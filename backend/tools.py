import json
from langchain_core.tools import tool
from database import SessionLocal
from models import HCP, Material, Sample, Interaction, EmailLog
import datetime
import re

def format_date(date_str: str) -> str:
    if not date_str or not date_str.strip():
        return datetime.date.today().strftime("%Y-%m-%d")
    
    date_clean = date_str.strip().lower()
    
    # Handle relative dates
    if date_clean == "today":
        return datetime.date.today().strftime("%Y-%m-%d")
    elif date_clean == "yesterday":
        return (datetime.date.today() - datetime.timedelta(days=1)).strftime("%Y-%m-%d")
    elif date_clean == "tomorrow":
        return (datetime.date.today() + datetime.timedelta(days=1)).strftime("%Y-%m-%d")
        
    # Try parsing different formats
    formats = [
        "%Y-%m-%d",      # 2026-07-08
        "%m/%d/%Y",      # 07/08/2026
        "%d/%m/%Y",      # 08/07/2026
        "%m/%d/%y",      # 07/08/26
        "%d/%m/%y",      # 08/07/26
        "%B %d, %Y",     # July 08, 2026
        "%b %d, %Y",     # Jul 08, 2026
        "%d %B %Y",      # 08 July 2026
        "%d %b %Y",      # 08 Jul 2026
    ]
    
    for fmt in formats:
        try:
            return datetime.datetime.strptime(date_str.strip(), fmt).date().strftime("%Y-%m-%d")
        except ValueError:
            continue
            
    # Fallback to today if parsing fails
    return datetime.date.today().strftime("%Y-%m-%d")

def format_time(time_str: str) -> str:
    if not time_str or not time_str.strip():
        return datetime.datetime.now().strftime("%H:%M")
        
    time_clean = time_str.strip().upper()
    
    # Clean up space between digits and AM/PM
    time_clean = re.sub(r'(\d+)\s*(AM|PM)', r'\1 \2', time_clean)
    
    formats = [
        "%I:%M %p", # 10:30 PM
        "%H:%M",    # 22:30
        "%I %p",    # 10 PM
        "%I:%M%p",  # 10:30PM
        "%H:%M:%S", # 22:30:00
    ]
    
    for fmt in formats:
        try:
            return datetime.datetime.strptime(time_clean, fmt).time().strftime("%H:%M")
        except ValueError:
            continue
            
    # Try just digits "1030" -> "10:30"
    digits_only = re.sub(r'\D', '', time_clean)
    if len(digits_only) == 4:
        try:
            h = int(digits_only[:2])
            m = int(digits_only[2:])
            if 0 <= h < 24 and 0 <= m < 60:
                return f"{h:02d}:{m:02d}"
        except ValueError:
            pass
            
    # Fallback to current time if parsing fails
    return datetime.datetime.now().strftime("%H:%M")

# Helper functions for smart entity matching
def find_hcp(db, name_query: str):
    if not name_query:
        return None
    # 1. Try exact or simple case-insensitive substring match
    hcp = db.query(HCP).filter(HCP.name.ilike(f"%{name_query}%")).first()
    if hcp:
        return hcp
    
    # 2. Clean query and try word-by-word intersection matching
    clean_query = name_query.lower().replace("dr.", "").replace("dr", "").strip()
    words = [w for w in clean_query.split() if w]
    if not words:
        return None
        
    all_hcps = db.query(HCP).all()
    best_match = None
    max_matches = 0
    for h in all_hcps:
        h_clean = h.name.lower().replace("dr.", "").replace("dr", "").strip()
        matches = sum(1 for word in words if word in h_clean)
        if matches > max_matches:
            max_matches = matches
            best_match = h
            
    if max_matches > 0:
        return best_match
    return None

def find_single_material(db, mat_name: str):
    if not mat_name:
        return None
    # Try case-insensitive substring
    mat = db.query(Material).filter(Material.name.ilike(f"%{mat_name}%")).first()
    if mat:
        return mat
        
    # Smart keyword match
    clean_name = mat_name.strip().lower()
    for char in ["-", "&", ",", ".", "/"]:
        clean_name = clean_name.replace(char, " ")
    words = [w for w in clean_name.split() if w]
    if not words:
        return None
        
    all_materials = db.query(Material).all()
    # Check if all words match
    for m in all_materials:
        m_text = f"{m.name} {m.type}".lower()
        if all(w in m_text for w in words):
            return m
    # Check if any word matches
    for m in all_materials:
        m_text = f"{m.name} {m.type}".lower()
        if any(w in m_text for w in words):
            return m
    return None

def find_single_sample(db, sam_name: str):
    if not sam_name:
        return None
    # Try case-insensitive substring
    sam = db.query(Sample).filter(Sample.name.ilike(f"%{sam_name}%")).first()
    if sam:
        return sam
        
    # Smart keyword match
    clean_name = sam_name.strip().lower()
    for char in ["-", "&", ",", ".", "/"]:
        clean_name = clean_name.replace(char, " ")
    words = [w for w in clean_name.split() if w]
    if not words:
        return None
        
    all_samples = db.query(Sample).all()
    # Check if all words match
    for s in all_samples:
        s_text = f"{s.name} {s.description or ''}".lower()
        if all(w in s_text for w in words):
            return s
    # Check if any word matches
    for s in all_samples:
        s_text = f"{s.name} {s.description or ''}".lower()
        if any(w in s_text for w in words):
            return s
    return None

def find_materials_and_samples(db, search_query: str):
    if not search_query:
        return [], []
    
    clean_query = search_query.strip().lower()
    for char in ["-", "&", ",", ".", "/"]:
        clean_query = clean_query.replace(char, " ")
    words = [w for w in clean_query.split() if w]
    
    # Try simple case-insensitive substring match first
    simple_mats = db.query(Material).filter(
        (Material.name.ilike(f"%{search_query}%")) | 
        (Material.type.ilike(f"%{search_query}%"))
    ).all()
    simple_sams = db.query(Sample).filter(
        Sample.name.ilike(f"%{search_query}%")
    ).all()
    
    if simple_mats or simple_sams:
        return simple_mats, simple_sams
        
    # Keyword matching
    all_materials = db.query(Material).all()
    all_samples = db.query(Sample).all()
    
    matched_mats = []
    matched_sams = []
    
    # All words match
    for m in all_materials:
        m_text = f"{m.name} {m.type}".lower()
        if all(w in m_text for w in words):
            matched_mats.append(m)
    for s in all_samples:
        s_text = f"{s.name} {s.description or ''}".lower()
        if all(w in s_text for w in words):
            matched_sams.append(s)
            
    # If no results, any word match
    if not matched_mats and not matched_sams:
        for m in all_materials:
            m_text = f"{m.name} {m.type}".lower()
            if any(w in m_text for w in words):
                matched_mats.append(m)
        for s in all_samples:
            s_text = f"{s.name} {s.description or ''}".lower()
            if any(w in s_text for w in words):
                matched_sams.append(s)
                
    return matched_mats, matched_sams


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
        hcp = find_hcp(db, hcp_name)
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
    samples_distributed: list[str] = None,
    hcp_specialty: str = "",
    hcp_clinic: str = "",
    hcp_email: str = "",
    hcp_preferences: str = ""
) -> str:
    """
    Logs details of a new interaction or prepopulates the interaction form.
    Pass all extracted information from the conversation to prefill the fields.
    If date or time are not specified, you should check if they were mentioned, otherwise leave blank.
    materials_shared and samples_distributed should be lists of exact or partial names of items.
    If details for a new or custom HCP are mentioned (specialty, clinic, email, preferences), pass them to prefill the HCP profile fields.
    """
    db = SessionLocal()
    try:
        form_updates = {}
        result_messages = []
        
        hcp = find_hcp(db, hcp_name)
        if hcp:
            form_updates["hcp_id"] = hcp.id
            form_updates["hcp_name"] = hcp.name
            form_updates["hcp_specialty"] = hcp_specialty or hcp.specialty
            form_updates["hcp_clinic"] = hcp_clinic or hcp.clinic
            form_updates["hcp_email"] = hcp_email or hcp.email
            form_updates["hcp_preferences"] = hcp_preferences or hcp.preferences
            result_messages.append(
                f"Selected existing HCP: {hcp.name} (Specialty: {hcp.specialty}, Clinic: {hcp.clinic}, Email: {hcp.email}, Preferences: {hcp.preferences or 'None'}). "
                "CRITICAL: Inform the user that this doctor is already in the database and present this info. "
                "Ask the user if there are any new preferences or updates they want to add to their profile."
            )
        else:
            form_updates["hcp_name"] = hcp_name
            form_updates["hcp_specialty"] = hcp_specialty
            form_updates["hcp_clinic"] = hcp_clinic
            form_updates["hcp_email"] = hcp_email
            form_updates["hcp_preferences"] = hcp_preferences
            result_messages.append(
                f"HCP '{hcp_name}' not found in database (will register as a custom entry). "
                "Inform the user that this is a custom entry, and ask if they would like to add a specialty, clinic, email, or preferences to create a complete profile."
            )

        # 2. Fill basic fields
        form_updates["interaction_type"] = interaction_type
        form_updates["sentiment"] = sentiment
        
        form_updates["date"] = format_date(date)
        form_updates["time"] = format_time(time)
            
        form_updates["attendees"] = attendees
        form_updates["topics_discussed"] = topics_discussed
        form_updates["outcomes"] = outcomes
        form_updates["follow_up_actions"] = follow_up_actions
        
        # 3. Match Materials
        matched_materials = []
        if materials_shared:
            for mat_name in materials_shared:
                mat = find_single_material(db, mat_name)
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
                sam = find_single_sample(db, sam_name)
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
    - hcp_specialty (string)
    - hcp_clinic (string)
    - hcp_email (string)
    - hcp_preferences (string)
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
            "samples_distributed": "samples_distributed",
            "hcp_specialty": "hcp_specialty",
            "specialty": "hcp_specialty",
            "hcp_clinic": "hcp_clinic",
            "clinic": "hcp_clinic",
            "hcp_email": "hcp_email",
            "email": "hcp_email",
            "hcp_preferences": "hcp_preferences",
            "preferences": "hcp_preferences"
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
                    mat = find_single_material(db, item)
                    matched_items.append(mat.name if mat else item)
            else:
                for item in items:
                    sam = find_single_sample(db, item)
                    matched_items.append(sam.name if sam else item)
                    
            form_updates[mapped_field] = matched_items
            display_value = ", ".join(matched_items)
        else:
            result_detail = ""
            # Handle HCP Name matching to get hcp_id as well
            if mapped_field == "hcp_name":
                hcp = find_hcp(db, new_value)
                if hcp:
                    form_updates["hcp_id"] = hcp.id
                    form_updates["hcp_name"] = hcp.name
                    form_updates["hcp_specialty"] = hcp.specialty
                    form_updates["hcp_clinic"] = hcp.clinic
                    form_updates["hcp_email"] = hcp.email
                    form_updates["hcp_preferences"] = hcp.preferences
                    new_value = hcp.name
                    result_detail = (
                        f"Matched existing HCP: {hcp.name} (Specialty: {hcp.specialty}, Clinic: {hcp.clinic}). "
                        "Inform the user this doctor is already in the database and ask if they have any updates for their profile."
                    )
                else:
                    form_updates["hcp_id"] = None
                    form_updates["hcp_name"] = new_value
                    form_updates["hcp_specialty"] = ""
                    form_updates["hcp_clinic"] = ""
                    form_updates["hcp_email"] = ""
                    form_updates["hcp_preferences"] = ""
                    result_detail = f"HCP '{new_value}' not found in database (custom entry). Ask if they want to register specialty/clinic."
            elif mapped_field == "date":
                new_value = format_date(new_value)
                form_updates[mapped_field] = new_value
            elif mapped_field == "time":
                new_value = format_time(new_value)
                form_updates[mapped_field] = new_value
            else:
                form_updates[mapped_field] = new_value
            display_value = new_value
            
        final_result = f"Updated form field '{mapped_field}' to '{display_value}'."
        if result_detail:
            final_result += f" {result_detail}"
            
        return json.dumps({
            "status": "success",
            "result": final_result,
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
        # Search in Materials and Samples using smart keyword match
        mats, sams = find_materials_and_samples(db, search_query)
        
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
# (email_materials_to_hcp tool removed)
