from fastapi import FastAPI, Depends, HTTPException
from fastapi.responses import StreamingResponse
from fastapi.middleware.cors import CORSMiddleware
from sqlalchemy.orm import Session
import os
import json

from database import engine, Base, get_db
from models import HCP, Material, Sample, Interaction, interaction_materials, interaction_samples
from schemas import ChatRequest, FormState, ToolCallLog
from seed import seed_database
from agent import agent_app
from langchain_core.messages import HumanMessage, AIMessage, AIMessageChunk

# Auto-create tables and seed data on startup
seed_database()

app = FastAPI(title="AI-First CRM HCP Module Backend")

# Configure CORS
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # In production, specify the actual frontend URL
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

@app.get("/api/hcps")
def get_hcps(db: Session = Depends(get_db)):
    hcps = db.query(HCP).all()
    return hcps

@app.get("/api/materials")
def get_materials(db: Session = Depends(get_db)):
    materials = db.query(Material).all()
    return materials

@app.get("/api/samples")
def get_samples(db: Session = Depends(get_db)):
    samples = db.query(Sample).all()
    return samples

@app.get("/api/interactions")
def get_interactions(db: Session = Depends(get_db)):
    interactions = db.query(Interaction).order_by(Interaction.date.desc()).all()
    # Serialize relationships nicely
    results = []
    for inter in interactions:
        hcp = db.query(HCP).filter(HCP.id == inter.hcp_id).first()
        results.append({
            "id": inter.id,
            "hcp_name": hcp.name if hcp else "Unknown",
            "interaction_type": inter.interaction_type,
            "date": inter.date,
            "time": inter.time,
            "attendees": inter.attendees,
            "topics_discussed": inter.topics_discussed,
            "sentiment": inter.sentiment,
            "outcomes": inter.outcomes,
            "follow_up_actions": inter.follow_up_actions,
            "status": inter.status
        })
    return results

@app.post("/api/interactions")
def save_interaction(form: FormState, db: Session = Depends(get_db)):
    try:
        # Match HCP ID
        hcp = None
        if form.hcp_id:
            hcp = db.query(HCP).filter(HCP.id == form.hcp_id).first()
        elif form.hcp_name:
            hcp = db.query(HCP).filter(HCP.name == form.hcp_name).first()
            if not hcp:
                # Dynamically create new HCP if name doesn't match
                hcp = HCP(
                    name=form.hcp_name,
                    specialty="General Practitioner",
                    clinic="General Clinic",
                    email=f"{form.hcp_name.lower().replace(' ', '.').replace('dr.', '')}@example.com"
                )
                db.add(hcp)
                db.commit()
                db.refresh(hcp)

        if not hcp:
            raise HTTPException(status_code=400, detail="HCP not specified and could not be resolved.")

        # Create or update Interaction
        interaction = None
        if form.id:
            interaction = db.query(Interaction).filter(Interaction.id == form.id).first()

        if not interaction:
            interaction = Interaction()
            db.add(interaction)

        interaction.hcp_id = hcp.id
        interaction.interaction_type = form.interaction_type
        interaction.date = form.date
        interaction.time = form.time
        interaction.attendees = form.attendees
        interaction.topics_discussed = form.topics_discussed
        interaction.sentiment = form.sentiment
        interaction.outcomes = form.outcomes
        interaction.follow_up_actions = form.follow_up_actions
        interaction.status = "Logged"  # Submit makes it logged

        db.commit()
        db.refresh(interaction)

        # Handle Materials associations
        # Clear existing
        db.execute(interaction_materials.delete().where(interaction_materials.c.interaction_id == interaction.id))
        for mat_name in form.materials_shared:
            mat = db.query(Material).filter(Material.name == mat_name).first()
            if mat:
                db.execute(interaction_materials.insert().values(interaction_id=interaction.id, material_id=mat.id))

        # Handle Samples associations
        # Clear existing
        db.execute(interaction_samples.delete().where(interaction_samples.c.interaction_id == interaction.id))
        for sam_name in form.samples_distributed:
            sam = db.query(Sample).filter(Sample.name == sam_name).first()
            if sam:
                db.execute(interaction_samples.insert().values(interaction_id=interaction.id, sample_id=sam.id))

        db.commit()
        return {"status": "success", "interaction_id": interaction.id, "message": "Interaction saved successfully."}
    except Exception as e:
        db.rollback()
        raise HTTPException(status_code=500, detail=str(e))

@app.post("/api/chat")
async def run_chat(request: ChatRequest):
    try:
        # Get the thread_id
        thread_id = request.thread_id or "default-thread"
        
        # We only pass the latest user message to the state to avoid duplicating messages in LangGraph MemorySaver
        latest_message = request.messages[-1].text if request.messages else ""
        
        # Run through LangGraph with checkpointer configuration
        config = {
            "configurable": {"thread_id": thread_id},
            "recursion_limit": 20
        }
        
        # Create initial state
        initial_state = {
            "messages": [HumanMessage(content=latest_message)],
            "form_state": request.form_state.model_dump(),
            "tool_logs": []
        }
        
        async def event_generator():
            buffer = ""
            has_seen_response_tag = False
            streaming_completed = False
            
            async for chunk, metadata in agent_app.astream(initial_state, config, stream_mode="messages"):
                node = metadata.get("langgraph_node")
                
                # We only want to stream tokens from the call_model node that are AIMessageChunks
                if node == "call_model" and isinstance(chunk, AIMessageChunk):
                    # Check if it has tool calls
                    if chunk.tool_calls:
                        continue
                        
                    content = chunk.content
                    if not content:
                        continue
                        
                    if streaming_completed:
                        continue
                        
                    buffer += content
                    
                    if not has_seen_response_tag:
                        # Check if we have seen "[RESPONSE]"
                        if "[RESPONSE]" in buffer:
                            has_seen_response_tag = True
                            idx = buffer.find("[RESPONSE]")
                            # Discard everything before and including [RESPONSE]
                            buffer = buffer[idx + 10:]
                        else:
                            # If buffer is long, we can stream some of it, but we must not
                            # stream a partial "[RESPONSE]" tag.
                            if len(buffer) > 30:
                                if "[" in buffer:
                                    idx = buffer.find("[")
                                    yield_content = buffer[:idx]
                                    if yield_content:
                                        yield json.dumps({"type": "token", "content": yield_content}) + "\n"
                                    buffer = buffer[idx:]
                                else:
                                    yield json.dumps({"type": "token", "content": buffer}) + "\n"
                                    buffer = ""
                    
                    if has_seen_response_tag and not streaming_completed:
                        # Check if we have seen "[/RESPONSE]"
                        if "[/RESPONSE]" in buffer:
                            idx = buffer.find("[/RESPONSE]")
                            yield_content = buffer[:idx]
                            if yield_content:
                                yield json.dumps({"type": "token", "content": yield_content}) + "\n"
                            buffer = ""
                            streaming_completed = True
                        else:
                            # Keep last 11 characters in buffer in case they are a prefix of "[/RESPONSE]"
                            if len(buffer) > 11:
                                yield_content = buffer[:-11]
                                yield json.dumps({"type": "token", "content": yield_content}) + "\n"
                                buffer = buffer[-11:]
                                
            # Flush any remaining buffer if it doesn't contain tags
            if buffer and not streaming_completed:
                if has_seen_response_tag:
                    idx = buffer.find("[/RESPONSE]")
                    if idx != -1:
                        yield_content = buffer[:idx]
                    else:
                        # Strip any partial suffix that matches the start of "[/RESPONSE]"
                        yield_content = buffer
                        for i in range(1, 12):
                            suffix = "[/RESPONSE]"[:i]
                            if buffer.endswith(suffix):
                                yield_content = buffer[:-i]
                                break
                    if yield_content:
                        yield json.dumps({"type": "token", "content": yield_content}) + "\n"
                else:
                    # If we never saw [RESPONSE], yield the entire remaining buffer
                    # but strip any partial trailing "[RESPONSE]" prefix just in case.
                    yield_content = buffer
                    for i in range(1, 11):
                        prefix = "[RESPONSE]"[:i]
                        if buffer.endswith(prefix):
                            yield_content = buffer[:-i]
                            break
                    if yield_content:
                        yield json.dumps({"type": "token", "content": yield_content}) + "\n"
                                
            # Retrieve final state
            state = await agent_app.aget_state(config)
            final_state = state.values
            
            form_state = final_state.get("form_state", {})
            tool_logs = [
                {
                    "tool_name": log["tool_name"],
                    "arguments": log["arguments"],
                    "result": log["result"]
                }
                for log in final_state.get("tool_logs", [])
            ]
            
            yield json.dumps({"type": "form_state", "content": form_state}) + "\n"
            yield json.dumps({"type": "tool_logs", "content": tool_logs}) + "\n"
            
        return StreamingResponse(event_generator(), media_type="text/event-stream")
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

if __name__ == "__main__":
    import uvicorn
    uvicorn.run("main:app", host="127.0.0.1", port=8000, reload=True)
