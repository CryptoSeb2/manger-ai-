import json
from datetime import datetime, timezone

from sqlalchemy import (
    Column,
    Integer,
    String,
    Text,
    Float,
    DateTime,
    ForeignKey,
    Boolean,
)
from sqlalchemy.orm import relationship

from app.database import Base


def _utcnow():
    return datetime.now(timezone.utc)


class Business(Base):
    __tablename__ = "businesses"

    id = Column(Integer, primary_key=True, index=True)
    name = Column(String(255), nullable=False)
    email = Column(String(255), unique=True, nullable=False, index=True)
    password_hash = Column(String(255), nullable=False)
    phone_number = Column(String(50), nullable=True)
    business_phone = Column(String(50), nullable=True)

    # Business details stored as JSON strings
    business_hours = Column(Text, default='{"mon-fri": "9:00 AM - 5:00 PM"}')
    services = Column(Text, default="[]")
    faqs = Column(Text, default="[]")
    greeting_message = Column(
        Text, default="Thank you for calling! How can I help you today?"
    )

    # Retell AI integration
    retell_agent_id = Column(String(255), nullable=True)
    retell_llm_id = Column(String(255), nullable=True)
    retell_phone_number_id = Column(String(255), nullable=True)
    assigned_phone_number = Column(String(50), nullable=True)

    # Google Calendar
    google_calendar_id = Column(String(255), nullable=True)

    # Website URL for chatbot to scan and learn (optional; defaults to app URL)
    website_url = Column(String(500), nullable=True)

    # CRM integration (optional)
    crm_provider = Column(String(50), nullable=True)  # hubspot, salesforce, etc.
    crm_access_token = Column(Text, nullable=True)  # API key or OAuth token

    # Billing / Stripe
    plan = Column(String(50), default="pro")  # pro or enterprise
    billing_status = Column(String(50), default="pending")  # pending, active, past_due, cancelled
    stripe_customer_id = Column(String(255), nullable=True)
    stripe_subscription_id = Column(String(255), nullable=True)
    setup_fee_paid = Column(Boolean, default=False)

    is_active = Column(Boolean, default=True)
    created_at = Column(DateTime, default=_utcnow)
    updated_at = Column(DateTime, default=_utcnow, onupdate=_utcnow)

    calls = relationship("CallLog", back_populates="business", cascade="all, delete-orphan")
    appointments = relationship("Appointment", back_populates="business", cascade="all, delete-orphan")
    chat_logs = relationship("ChatLog", back_populates="business", cascade="all, delete-orphan")

    @property
    def services_list(self) -> list:
        try:
            return json.loads(self.services) if self.services else []
        except (json.JSONDecodeError, TypeError):
            return []

    @services_list.setter
    def services_list(self, value: list):
        self.services = json.dumps(value)

    @property
    def faqs_list(self) -> list:
        try:
            return json.loads(self.faqs) if self.faqs else []
        except (json.JSONDecodeError, TypeError):
            return []

    @faqs_list.setter
    def faqs_list(self, value: list):
        self.faqs = json.dumps(value)

    @property
    def hours_dict(self) -> dict:
        try:
            return json.loads(self.business_hours) if self.business_hours else {}
        except (json.JSONDecodeError, TypeError):
            return {}

    @hours_dict.setter
    def hours_dict(self, value: dict):
        self.business_hours = json.dumps(value)


class CallLog(Base):
    __tablename__ = "call_logs"

    id = Column(Integer, primary_key=True, index=True)
    business_id = Column(Integer, ForeignKey("businesses.id"), nullable=False, index=True)
    retell_call_id = Column(String(255), unique=True, nullable=True, index=True)
    caller_number = Column(String(50), nullable=True)
    direction = Column(String(20), default="inbound")
    duration_seconds = Column(Float, default=0)
    transcript = Column(Text, nullable=True)
    summary = Column(Text, nullable=True)
    sentiment = Column(String(50), nullable=True)
    call_status = Column(String(50), default="completed")
    disconnection_reason = Column(String(255), nullable=True)
    created_at = Column(DateTime, default=_utcnow)

    business = relationship("Business", back_populates="calls")
    appointment = relationship("Appointment", back_populates="call_log", uselist=False)


class Appointment(Base):
    __tablename__ = "appointments"

    id = Column(Integer, primary_key=True, index=True)
    business_id = Column(Integer, ForeignKey("businesses.id"), nullable=False, index=True)
    call_log_id = Column(Integer, ForeignKey("call_logs.id"), nullable=True)
    customer_name = Column(String(255), nullable=False)
    customer_phone = Column(String(50), nullable=True)
    customer_email = Column(String(255), nullable=True)
    service = Column(String(255), nullable=True)
    appointment_time = Column(DateTime, nullable=False)
    duration_minutes = Column(Integer, default=30)
    status = Column(String(50), default="confirmed")  # confirmed, cancelled, completed, no-show
    google_event_id = Column(String(255), nullable=True)
    notes = Column(Text, nullable=True)
    created_at = Column(DateTime, default=_utcnow)
    updated_at = Column(DateTime, default=_utcnow, onupdate=_utcnow)

    business = relationship("Business", back_populates="appointments")
    call_log = relationship("CallLog", back_populates="appointment")


class ChatLog(Base):
    """Stores chatbot conversations for learning and review."""
    __tablename__ = "chat_logs"

    id = Column(Integer, primary_key=True, index=True)
    business_id = Column(Integer, ForeignKey("businesses.id"), nullable=False, index=True)
    user_message = Column(Text, nullable=False)
    assistant_reply = Column(Text, nullable=False)
    session_id = Column(String(255), nullable=True, index=True)  # optional: group messages in same chat
    created_at = Column(DateTime, default=_utcnow)

    business = relationship("Business", back_populates="chat_logs")
