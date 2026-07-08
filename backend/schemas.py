from pydantic import BaseModel, Field
from typing import List, Optional

# --- Material Schemas ---
class MaterialBase(BaseModel):
    name: str
    type: str
    file_size: Optional[str] = None
    url: Optional[str] = None

class Material(MaterialBase):
    id: int
    class Config:
        from_attributes = True

# --- Sample Schemas ---
class SampleBase(BaseModel):
    name: str
    description: Optional[str] = None

class Sample(SampleBase):
    id: int
    class Config:
        from_attributes = True

# --- HCP Schemas ---
class HCPBase(BaseModel):
    name: str
    specialty: str
    clinic: str
    contact_number: Optional[str] = None
    email: str
    preferences: Optional[str] = None

class HCP(HCPBase):
    id: int
    class Config:
        from_attributes = True

# --- Form State Schema for UI sync ---
class FormState(BaseModel):
    id: Optional[int] = None
    hcp_id: Optional[int] = None
    hcp_name: Optional[str] = ""
    interaction_type: str = "Meeting"
    date: str = ""
    time: str = ""
    attendees: str = ""
    topics_discussed: str = ""
    sentiment: str = "Neutral"  # Positive, Neutral, Negative
    outcomes: str = ""
    follow_up_actions: str = ""
    materials_shared: List[str] = []  # Names or IDs of materials
    samples_distributed: List[str] = []  # Names or IDs of samples

# --- Interaction Schemas ---
class InteractionBase(BaseModel):
    hcp_id: int
    interaction_type: str
    date: str
    time: str
    attendees: Optional[str] = None
    topics_discussed: Optional[str] = None
    sentiment: Optional[str] = None
    outcomes: Optional[str] = None
    follow_up_actions: Optional[str] = None
    status: str = "Draft"

class InteractionCreate(InteractionBase):
    material_ids: List[int] = []
    sample_ids: List[int] = []

class Interaction(InteractionBase):
    id: int
    materials: List[Material] = []
    samples: List[Sample] = []
    class Config:
        from_attributes = True

# --- Email Log Schemas ---
class EmailLogBase(BaseModel):
    hcp_id: int
    subject: str
    materials_sent: str
    timestamp: str
    status: str = "Sent"

class EmailLog(EmailLogBase):
    id: int
    class Config:
        from_attributes = True

# --- Chat schemas ---
class ChatMessage(BaseModel):
    sender: str  # "user" or "assistant"
    text: str

class ChatRequest(BaseModel):
    messages: List[ChatMessage]
    form_state: FormState

class ToolCallLog(BaseModel):
    tool_name: str
    arguments: str
    result: str

class ChatResponse(BaseModel):
    response: str
    form_state: FormState
    tool_calls: List[ToolCallLog] = []
