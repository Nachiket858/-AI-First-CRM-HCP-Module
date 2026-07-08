import json
from langchain_core.tools import tool
from database import SessionLocal
from models import HCP, Material, Sample, Interaction, EmailLog
import datetime

@tool
def get_hcp_profile(hcp_name: str) -> str:
    """
    Retrieves the profile of a Healthcare Professional (HCP) including their specialty,
    clinic, contact info, clinical preferences, and past interaction history.
    Use this when the user asks about an HCP's details, preferences, or past interactions.
    """
    db = SessionLocal()
    try:
        # Fuzzy match or exact match
        hcp = db.query(HCP).filter(HCP.name.like(f"%{hcp_name}%")).first()
        if not hcp:
            return json.dumps({
                "status": "error",
                "result": f"No HCP found matching the name '{hcp_name}'."
            })
        
        # Get last few interactions
        past_interactions = db.query(Interaction).filter(Interaction.hcp_id == hcp.id).order_by(Interaction.date.desc()).limit(3).all()
        interactions_list = []
        for inter in past_interactions:
            interactions_list.append({
                "date": inter.date,
                "type": inter.interaction_type,
                "topics": inter.topics_discussed,
                "sentiment": inter.sentiment,
                "outcomes": inter.outcomes
            })
            
        profile_data = {
            "id": hcp.id,
            "name": hcp.name,
            "specialty": hcp.specialty,
            "clinic": hcp.clinic,
            "contact_number": hcp.contact_number,
            "email": hcp.email,
            "preferences": hcp.preferences,
            "recent_interactions": interactions_list
        }
        
        return json.dumps({
            "status": "success",
            "result": f"Retrieved profile for {hcp.name}.",
            "data": profile_data,
            # If the user is querying the HCP, we also auto-select them in the form
            "form_updates": {
                "hcp_id": hcp.id,
                "hcp_name": hcp.name
            }
        })
    except Exception as e:
        return json.dumps({"status": "error", "result": str(e)})
    finally:
        db.close()


@tool
def log_interaction_details(
    hcp_name: str,
    interaction_type: str = "Meeting",
    date: str = "",
    time: str = "",
    attendees: str = "",
    topics_discussed: str = "",
    sentiment: str = "Neutral",
    outcomes: str = "",
    follow_up_actions: str = "",
    materials_shared: list[str] = None,
    samples_distributed: list[str] = None
) -> str:
    """
    Logs details of a new interaction or prepopulates the interaction form.
    Pass all extracted information from the conversation to prefill the fields.
    If date or time are not specified, you should check if they were mentioned, otherwise leave blank.
    materials_shared and samples_distributed should be lists of exact or partial names of items.
    """
    db = SessionLocal()
    try:
        form_updates = {}
        result_messages = []
        
        # 1. Match HCP
        hcp = db.query(HCP).filter(HCP.name.like(f"%{hcp_name}%")).first()
        if hcp:
            form_updates["hcp_id"] = hcp.id
            form_updates["hcp_name"] = hcp.name
            result_messages.append(f"Selected HCP: {hcp.name}")
        else:
            form_updates["hcp_name"] = hcp_name
            result_messages.append(f"HCP '{hcp_name}' not found in database (will register as a custom entry).")

        # 2. Fill basic fields
        form_updates["interaction_type"] = interaction_type
        form_updates["sentiment"] = sentiment
        
        if date:
            form_updates["date"] = date
        else:
            # Set today's date if not specified
            form_updates["date"] = datetime.date.today().strftime("%m/%d/%Y")
            
        if time:
            form_updates["time"] = time
        else:
            form_updates["time"] = datetime.datetime.now().strftime("%I:%M %p")
            
        form_updates["attendees"] = attendees
        form_updates["topics_discussed"] = topics_discussed
        form_updates["outcomes"] = outcomes
        form_updates["follow_up_actions"] = follow_up_actions
        
        # 3. Match Materials
        matched_materials = []
        if materials_shared:
            for mat_name in materials_shared:
                mat = db.query(Material).filter(Material.name.like(f"%{mat_name}%")).first()
                if mat:
                    matched_materials.append(mat.name)
                else:
                    matched_materials.append(mat_name)  # Keep original if not matched
            form_updates["materials_shared"] = matched_materials
            result_messages.append(f"Materials shared: {', '.join(matched_materials)}")

        # 4. Match Samples
        matched_samples = []
        if samples_distributed:
            for sam_name in samples_distributed:
                sam = db.query(Sample).filter(Sample.name.like(f"%{sam_name}%")).first()
                if sam:
                    matched_samples.append(sam.name)
                else:
                    matched_samples.append(sam_name)
            form_updates["samples_distributed"] = matched_samples
            result_messages.append(f"Samples distributed: {', '.join(matched_samples)}")

        return json.dumps({
            "status": "success",
            "result": f"Prefilled interaction form details. {'; '.join(result_messages)}",
            "form_updates": form_updates
        })
    except Exception as e:
        return json.dumps({"status": "error", "result": str(e)})
    finally:
        db.close()


@tool
def edit_interaction_details(field_name: str, new_value: str) -> str:
    """
    Modifies a specific field on the active interaction form.
    Use this when the user points out a mistake or wants to change a single value.
    Valid field_names are:
    - hcp_name (string)
    - interaction_type (string, e.g. Meeting, Call, Email, Webcast)
    - date (string, MM/DD/YYYY)
    - time (string, HH:MM AM/PM)
    - attendees (string)
    - topics_discussed (string)
    - sentiment (string: Positive, Neutral, Negative)
    - outcomes (string)
    - follow_up_actions (string)
    - materials_shared (comma-separated string or list)
    - samples_distributed (comma-separated string or list)
    """
    db = SessionLocal()
    try:
        clean_field = field_name.strip().lower()
        form_updates = {}
        
        # Map fields to actual keys
        field_mapping = {
            "hcp_name": "hcp_name",
            "hcpname": "hcp_name",
            "hcp": "hcp_name",
            "interaction_type": "interaction_type",
            "type": "interaction_type",
            "date": "date",
            "time": "time",
            "attendees": "attendees",
            "topics": "topics_discussed",
            "topics_discussed": "topics_discussed",
            "sentiment": "sentiment",
            "outcomes": "outcomes",
            "follow_up": "follow_up_actions",
            "follow_up_actions": "follow_up_actions",
            "materials": "materials_shared",
            "materials_shared": "materials_shared",
            "samples": "samples_distributed",
            "samples_distributed": "samples_distributed"
        }
        
        mapped_field = field_mapping.get(clean_field)
        if not mapped_field:
            return json.dumps({
                "status": "error",
                "result": f"Invalid field '{field_name}'. Allowed fields: {', '.join(set(field_mapping.values()))}."
            })
            
        # Specific handling for list fields
        if mapped_field in ["materials_shared", "samples_distributed"]:
            if isinstance(new_value, str):
                items = [item.strip() for item in new_value.split(",") if item.strip()]
            elif isinstance(new_value, list):
                items = [str(x).strip() for x in new_value]
            else:
                items = []
                
            # Perform DB matching for list items
            matched_items = []
            if mapped_field == "materials_shared":
                for item in items:
                    mat = db.query(Material).filter(Material.name.like(f"%{item}%")).first()
                    matched_items.append(mat.name if mat else item)
            else:
                for item in items:
                    sam = db.query(Sample).filter(Sample.name.like(f"%{item}%")).first()
                    matched_items.append(sam.name if sam else item)
                    
            form_updates[mapped_field] = matched_items
            display_value = ", ".join(matched_items)
        else:
            # Handle HCP Name matching to get hcp_id as well
            if mapped_field == "hcp_name":
                hcp = db.query(HCP).filter(HCP.name.like(f"%{new_value}%")).first()
                if hcp:
                    form_updates["hcp_id"] = hcp.id
                    form_updates["hcp_name"] = hcp.name
                    new_value = hcp.name
                else:
                    form_updates["hcp_id"] = None
                    form_updates["hcp_name"] = new_value
            else:
                form_updates[mapped_field] = new_value
            display_value = new_value
            
        return json.dumps({
            "status": "success",
            "result": f"Updated form field '{mapped_field}' to '{display_value}'.",
            "form_updates": form_updates
        })
    except Exception as e:
        return json.dumps({"status": "error", "result": str(e)})
    finally:
        db.close()


@tool
def suggest_follow_up(topics: str, sentiment: str) -> str:
    """
    Recommends specific next actions (meetings, emails, material dispatches)
    based on the discussion topics and observed sentiment of the HCP.
    This tool suggests outcomes and follow-up activities and updates those form fields.
    """
    # Simple rule-based generation to create high-quality context-specific suggestions
    actions = []
    outcomes_suggested = ""
    
    topics_lower = topics.lower()
    
    if "efficacy" in topics_lower or "trial" in topics_lower or "study" in topics_lower:
        outcomes_suggested = "HCP showed interest in efficacy data and requested follow-up outcomes statistics."
        actions.append("Email full clinical study publication link to HCP.")
        actions.append("Schedule follow-up discussion in 2 weeks to answer efficacy questions.")
    elif "dosage" in topics_lower or "administration" in topics_lower or "safety" in topics_lower:
        outcomes_suggested = "Discussed safety profiles and dosing instructions."
        actions.append("Share physical dosing charts with the clinic staff.")
        actions.append("Follow up with safety brochures.")
    elif "sample" in topics_lower or "pack" in topics_lower or "starter" in topics_lower:
        outcomes_suggested = "Distributed product samples for patient evaluation."
        actions.append("Conduct a follow-up in 10 days to gather patient feedback on sample tolerance.")
    else:
        outcomes_suggested = "HCP briefed on products. General interest noted."
        actions.append("Schedule standard follow-up meeting in 4 weeks.")

    if sentiment.lower() == "positive":
        actions.append("Offer an invitation to the upcoming scientific webcast/speaker event.")
    elif sentiment.lower() == "negative":
        actions.insert(0, "Escalate specific medical queries to Medical Science Liaison (MSL).")

    follow_up_str = " \n".join([f"- {a}" for a in actions])
    
    return json.dumps({
        "status": "success",
        "result": f"Generated follow-up suggestions based on topics and {sentiment} sentiment.",
        "form_updates": {
            "outcomes": outcomes_suggested,
            "follow_up_actions": follow_up_str
        }
    })


@tool
def fetch_product_materials(search_query: str) -> str:
    """
    Searches the approved clinical literature and marketing materials repository
    for brochures, clinical trial reports, or product briefs that can be shared with HCPs.
    """
    db = SessionLocal()
    try:
        # Search in Materials table
        mats = db.query(Material).filter(
            (Material.name.like(f"%{search_query}%")) | 
            (Material.type.like(f"%{search_query}%"))
        ).all()
        
        # Search in Samples table (for rep inventory check)
        sams = db.query(Sample).filter(
            (Sample.name.like(f"%{search_query}%"))
        ).all()
        
        results = []
        for m in mats:
            results.append({
                "id": m.id,
                "name": m.name,
                "category": m.type,
                "size": m.file_size,
                "type": "material"
            })
            
        for s in sams:
            results.append({
                "id": s.id,
                "name": s.name,
                "category": "Sample Pack",
                "size": "In Rep Stock",
                "type": "sample"
            })
            
        if not results:
            return json.dumps({
                "status": "success",
                "result": f"No materials or samples found matching '{search_query}'.",
                "data": []
            })
            
        return json.dumps({
            "status": "success",
            "result": f"Found {len(results)} matching materials and samples.",
            "data": results
        })
    except Exception as e:
        return json.dumps({"status": "error", "result": str(e)})
    finally:
        db.close()


@tool
def email_materials_to_hcp(hcp_name: str, materials: list[str]) -> str:
    """
    Simulates sending the selected brochures/materials directly to the HCP's registered email.
    Creates an outgoing email log record in the database.
    Use this when the user explicitly requests to email the materials to the HCP.
    """
    db = SessionLocal()
    try:
        hcp = db.query(HCP).filter(HCP.name.like(f"%{hcp_name}%")).first()
        if not hcp:
            return json.dumps({
                "status": "error",
                "result": f"HCP '{hcp_name}' not found. Cannot send email."
            })
            
        # Verify materials
        valid_materials = []
        for mat_name in materials:
            mat = db.query(Material).filter(Material.name.like(f"%{mat_name}%")).first()
            if mat:
                valid_materials.append(mat.name)
            else:
                valid_materials.append(mat_name)
                
        # Create EmailLog record
        email_log = EmailLog(
            hcp_id=hcp.id,
            subject=f"Requested Medical Literature: {', '.join(valid_materials[:2])}",
            materials_sent=", ".join(valid_materials),
            timestamp=datetime.datetime.now().strftime("%Y-%m-%d %I:%M %p"),
            status="Sent"
        )
        db.add(email_log)
        db.commit()
        
        return json.dumps({
            "status": "success",
            "result": f"Successfully emailed materials [{', '.join(valid_materials)}] to {hcp.name} at {hcp.email}."
        })
    except Exception as e:
        db.rollback()
        return json.dumps({"status": "error", "result": str(e)})
    finally:
        db.close()
