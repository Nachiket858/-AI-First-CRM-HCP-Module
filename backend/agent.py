from dotenv import load_dotenv
load_dotenv(override=True)

import os
import json
from typing import Annotated, Sequence, TypedDict, List, Dict, Any

from langchain_core.messages import BaseMessage, SystemMessage, HumanMessage, AIMessage, ToolMessage
from langchain_groq import ChatGroq
from langgraph.graph import StateGraph, END
from langgraph.graph.message import add_messages
from langgraph.checkpoint.memory import MemorySaver
from langchain.output_parsers import PydanticOutputParser
from pydantic import BaseModel, Field

class TagOutputParser:
    def get_format_instructions(self) -> str:
        return """You MUST wrap your final response message to the user in [RESPONSE] and [/RESPONSE] tags. Do not output any conversational filler or thoughts outside these tags.

Example format:
[RESPONSE]
Your interaction has been logged successfully.
[/RESPONSE]
"""
    
    def parse(self, text: str) -> str:
        import re
        match = re.search(r"\[RESPONSE\](.*?)\[/RESPONSE\]", text, re.DOTALL)
        if match:
            return match.group(1).strip()
        # Fallback
        clean = text.replace("[RESPONSE]", "").replace("[/RESPONSE]", "").strip()
        return clean

parser = TagOutputParser()
FORMAT_INSTRUCTIONS = parser.get_format_instructions()

# Import tools
from tools import (
    get_hcp_profile,
    log_interaction_details,
    edit_interaction_details,
    suggest_follow_up,
    fetch_product_materials
)

# Dictionary mapping tool names to actual functions for execution
TOOLS_MAP = {
    "get_hcp_profile": get_hcp_profile,
    "log_interaction_details": log_interaction_details,
    "edit_interaction_details": edit_interaction_details,
    "suggest_follow_up": suggest_follow_up,
    "fetch_product_materials": fetch_product_materials
}

# Define LangGraph state
class AgentState(TypedDict):
    messages: Annotated[Sequence[BaseMessage], add_messages]
    form_state: Dict[str, Any]
    tool_logs: List[Dict[str, Any]]

# Define Node: Call LLM
def call_model(state: AgentState):
    messages = state["messages"]
    form_state = state["form_state"]
    
    # Check for API key
    api_key = os.getenv("GROQ_API_KEY")
    if not api_key:
        # If no API key, return a message to set it up
        error_msg = AIMessage(content="⚠️ **Groq API Key is missing!** Please set the `GROQ_API_KEY` in the `backend/.env` file to start using the real AI Assistant.")
        return {"messages": [error_msg]}
        
    model_name = os.getenv("GROQ_MODEL")
    if not model_name:
        error_msg = AIMessage(content="⚠️ **GROQ_MODEL is missing in .env file!** Please define `GROQ_MODEL=openai/gpt-oss-120b` (or another supported model) in your `backend/.env` file.")
        return {"messages": [error_msg]}
    # Initialize ChatGroq model using langchain_groq
    llm = ChatGroq(
        groq_api_key=api_key,
        model_name=model_name,
        temperature=0.1
    )
    
    # Bind tools to the LLM
    tools_list = list(TOOLS_MAP.values())
    llm_with_tools = llm.bind_tools(tools_list)
    
    # Define system instructions
    system_prompt = f"""You are a premium AI CRM Assistant for medical sales representatives. 
Your job is to help the representative log, edit, and query interactions with Healthcare Professionals (HCPs) through a conversational interface.

The current active form state in the UI is:
{json.dumps(form_state, indent=2)}

Guidelines:
1. **Log Interaction**: When the user describes a visit, call, or email with details (e.g. HCP name, sentiment, topics), invoke `log_interaction_details` with all parameters you can extract.
2. **Edit Interaction**: When the user corrects a mistake or asks to change a field (e.g. "Actually the date was yesterday" or "Change sentiment to Neutral"), identify the field and call `edit_interaction_details`.
3. **Lookup Profile**: When the user asks about a doctor's preferences, specialty, or history, call `get_hcp_profile`.
4. **Suggest Follow-ups**: If the user asks for suggestions or outcomes based on the discussion, call `suggest_follow_up`.
5. **Fetch Materials**: When they ask to find brochures, study guides, or samples, call `fetch_product_materials`.

Always use tools when the user requests actions corresponding to these behaviors. If a tool returns state updates, the form on the left will automatically synchronize. Focus on being a helpful, professional, and compliant medical sales assistant.

{FORMAT_INSTRUCTIONS}
"""
    
    # Prepend the system prompt to the messages list
    full_messages = [SystemMessage(content=system_prompt)] + list(messages)
    
    response = llm_with_tools.invoke(full_messages)
    
    # Parse final response if not calling tools
    if not (hasattr(response, "tool_calls") and response.tool_calls):
        response.content = parser.parse(response.content)
                
    return {"messages": [response]}

# Define Node: Execute tools
def execute_tools(state: AgentState):
    messages = state["messages"]
    form_state = state["form_state"].copy()
    tool_logs = list(state.get("tool_logs", []))
    
    last_message = messages[-1]
    tool_messages = []
    
    if hasattr(last_message, "tool_calls") and last_message.tool_calls:
        for tool_call in last_message.tool_calls:
            tool_name = tool_call["name"]
            tool_args = tool_call["args"]
            tool_call_id = tool_call["id"]
            
            tool_func = TOOLS_MAP.get(tool_name)
            if tool_func:
                try:
                    # Run the tool
                    tool_result_str = tool_func.invoke(tool_args)
                    
                    # Parse the tool's structured output
                    tool_data = json.loads(tool_result_str)
                    
                    # Extract any form updates
                    if "form_updates" in tool_data:
                        for k, v in tool_data["form_updates"].items():
                            form_state[k] = v
                            
                    # Record log for the UI
                    tool_logs.append({
                        "tool_name": tool_name,
                        "arguments": json.dumps(tool_args),
                        "result": tool_data.get("result", tool_result_str)
                    })
                    
                    # Append ToolMessage to conversation
                    tool_messages.append(
                        ToolMessage(
                            content=tool_result_str,
                            tool_call_id=tool_call_id
                        )
                    )
                except Exception as e:
                    tool_messages.append(
                        ToolMessage(
                            content=f"Error executing tool: {str(e)}",
                            tool_call_id=tool_call_id
                        )
                    )
            else:
                tool_messages.append(
                    ToolMessage(
                        content=f"Tool '{tool_name}' not found.",
                        tool_call_id=tool_call_id
                    )
                )
                
    return {
        "messages": tool_messages,
        "form_state": form_state,
        "tool_logs": tool_logs
    }

# Router logic
def should_continue(state: AgentState):
    messages = state["messages"]
    last_message = messages[-1]
    if hasattr(last_message, "tool_calls") and last_message.tool_calls:
        return "execute_tools"
    return END

# Build the Graph
workflow = StateGraph(AgentState)

# Add Nodes
workflow.add_node("call_model", call_model)
workflow.add_node("execute_tools", execute_tools)

# Set Entry Point
workflow.set_entry_point("call_model")

# Add Conditional Edges
workflow.add_conditional_edges(
    "call_model",
    should_continue,
    {
        "execute_tools": "execute_tools",
        END: END
    }
)

# Add Normal Edge
workflow.add_edge("execute_tools", "call_model")

# Compile
memory = MemorySaver()
agent_app = workflow.compile(checkpointer=memory)
