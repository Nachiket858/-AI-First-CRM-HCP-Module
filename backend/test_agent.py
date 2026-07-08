import os
import json
from dotenv import load_dotenv
from langchain_core.messages import HumanMessage
from agent import agent_app
from seed import seed_database

import sys
load_dotenv()
sys.stdout.reconfigure(encoding='utf-8')

def run_test():
    # Make sure DB is seeded
    seed_database()
    
    api_key = os.getenv("GROQ_API_KEY")
    if not api_key or "your_actual_key" in api_key:
        print("Skipping LLM agent test: GROQ_API_KEY is not set.")
        return
        
    print(f"Testing LangGraph Agent with GROQ_API_KEY={api_key[:8]}...")
    
    # Test 1: Log Interaction Details
    state = {
        "messages": [HumanMessage(content="Today I met with Dr. Sharma and discussed Prodo-X trials. The sentiment was positive and I shared the Dosage Brochure.")],
        "form_state": {
            "hcp_name": "",
            "interaction_type": "Meeting",
            "date": "",
            "time": "",
            "attendees": "",
            "topics_discussed": "",
            "sentiment": "Neutral",
            "outcomes": "",
            "follow_up_actions": "",
            "materials_shared": [],
            "samples_distributed": []
        },
        "tool_logs": []
    }
    
    print("\n[Input prompt]: 'Today I met with Dr. Sharma and discussed Prodo-X trials. The sentiment was positive and I shared the Dosage Brochure.'")
    config = {"configurable": {"thread_id": "test-thread"}, "recursion_limit": 20}
    output = agent_app.invoke(state, config)
    
    print("\n[Agent Response]:")
    print(output["messages"][-1].content)
    
    print("\n[Updated Form State]:")
    print(json.dumps(output["form_state"], indent=2))
    
    print("\n[Tools Executed]:")
    for log in output["tool_logs"]:
        print(f"- Tool: {log['tool_name']}")
        print(f"  Args: {log['arguments']}")
        print(f"  Result: {log['result']}")

if __name__ == "__main__":
    run_test()
