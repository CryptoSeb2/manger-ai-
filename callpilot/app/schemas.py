from datetime import datetime
from typing import Optional

from pydantic import BaseModel, EmailStr


# --- Auth ---

class SignupRequest(BaseModel):
    business_name: str
    email: str
    password: str
    phone_number: Optional[str] = None


class LoginRequest(BaseModel):
    email: str
    password: str


# --- Business Settings ---

class BusinessUpdate(BaseModel):
    name: Optional[str] = None
    phone_number: Optional[str] = None
    business_hours: Optional[dict] = None
    services: Optional[list[str]] = None
    faqs: Optional[list[dict]] = None
    greeting_message: Optional[str] = None
    google_calendar_id: Optional[str] = None


class BusinessResponse(BaseModel):
    id: int
    name: str
    email: str
    phone_number: Optional[str]
    business_hours: Optional[dict]
    services: Optional[list]
    faqs: Optional[list]
    greeting_message: Optional[str]
    assigned_phone_number: Optional[str]
    retell_agent_id: Optional[str]
    google_calendar_id: Optional[str]
    is_active: bool
    created_at: datetime

    model_config = {"from_attributes": True}


# --- Call Logs ---

class CallLogResponse(BaseModel):
    id: int
    retell_call_id: Optional[str]
    caller_number: Optional[str]
    direction: str
    duration_seconds: float
    transcript: Optional[str]
    summary: Optional[str]
    sentiment: Optional[str]
    call_status: str
    created_at: datetime

    model_config = {"from_attributes": True}


class CallWebhookPayload(BaseModel):
    call_id: Optional[str] = None
    retell_call_id: Optional[str] = None
    business_id: Optional[int] = None
    agent_id: Optional[str] = None
    caller_number: Optional[str] = None
    caller_name: Optional[str] = None  # from transcript extraction if available
    direction: Optional[str] = "inbound"
    duration_seconds: Optional[float] = 0
    transcript: Optional[str] = None
    summary: Optional[str] = None
    sentiment: Optional[str] = None
    call_status: Optional[str] = "completed"
    disconnection_reason: Optional[str] = None


# --- Appointments ---

class AppointmentCreate(BaseModel):
    customer_name: str
    customer_phone: Optional[str] = None
    customer_email: Optional[str] = None
    service: Optional[str] = None
    appointment_time: datetime
    duration_minutes: int = 30
    notes: Optional[str] = None


class AppointmentUpdate(BaseModel):
    status: Optional[str] = None
    appointment_time: Optional[datetime] = None
    notes: Optional[str] = None


class AppointmentResponse(BaseModel):
    id: int
    customer_name: str
    customer_phone: Optional[str]
    customer_email: Optional[str]
    service: Optional[str]
    appointment_time: datetime
    duration_minutes: int
    status: str
    google_event_id: Optional[str]
    notes: Optional[str]
    created_at: datetime

    model_config = {"from_attributes": True}


class ChatMessageRequest(BaseModel):
    business_id: int
    message: str
    conversation_history: Optional[list[dict]] = None


class AppointmentWebhookPayload(BaseModel):
    business_id: Optional[int] = None
    agent_id: Optional[str] = None
    call_id: Optional[str] = None
    customer_name: str
    customer_phone: Optional[str] = None
    customer_email: Optional[str] = None
    service: Optional[str] = None
    appointment_time: str
    duration_minutes: int = 30
    google_event_id: Optional[str] = None
    notes: Optional[str] = None
