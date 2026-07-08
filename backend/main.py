from fastapi import FastAPI, Depends, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from sqlalchemy.orm import Session
import os

from database import engine, Base, get_db
from models import HCP, Material, Sample, Interaction, interaction_materials, interaction_samples
from schemas import ChatRequest, ChatResponse, FormState, ToolCallLog
from seed import seed_database
from agent import agent_app
from langchain_core.messages import HumanMessage, AIMessage

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

@app.post("/api/chat", response_model=ChatResponse)
def run_chat(request: ChatRequest):
    try:
        # Convert message history to LangChain message formats
        messages = []
        for msg in request.messages:
            if msg.sender == "user":
                messages.append(HumanMessage(content=msg.text))
            else:
                messages.append(AIMessage(content=msg.text))
                
        # Run through LangGraph
        initial_state = {
            "messages": messages,
            "form_state": request.form_state.model_dump(),
            "tool_logs": []
        }
        
        config = {"recursion_limit": 20}
        output_state = agent_app.invoke(initial_state, config)
        
        # Get final assistant message
        final_message = output_state["messages"][-1].content
        updated_form_state = output_state["form_state"]
        tool_logs = [
            ToolCallLog(
                tool_name=log["tool_name"],
                arguments=log["arguments"],
                result=log["result"]
            )
            for log in output_state.get("tool_logs", [])
        ]
        
        return ChatResponse(
            response=final_message,
            form_state=FormState(**updated_form_state),
            tool_calls=tool_logs
        )
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

if __name__ == "__main__":
    import uvicorn
    uvicorn.run("main:app", host="127.0.0.1", port=8000, reload=True)
