"""
Retell AI integration service.

Handles creating/updating voice agents, managing phone numbers,
and building dynamic prompts from business configuration.
"""

import json
import logging
from typing import Optional

import httpx

from app.config import get_settings
from app.models import Business

logger = logging.getLogger(__name__)

RETELL_BASE = "https://api.retellai.com"


def _headers() -> dict:
    return {
        "Authorization": f"Bearer {get_settings().retell_api_key}",
        "Content-Type": "application/json",
    }


def build_agent_prompt(business: Business) -> str:
    """Build a dynamic system prompt for the Retell voice agent based on business config."""
    hours = business.hours_dict
    services = business.services_list
    faqs = business.faqs_list

    hours_text = "\n".join(f"  - {day}: {time}" for day, time in hours.items()) if hours else "  Not specified"
    services_text = "\n".join(f"  - {s}" for s in services) if services else "  General services"

    faq_text = ""
    if faqs:
        for faq in faqs:
            q = faq.get("question", faq.get("q", ""))
            a = faq.get("answer", faq.get("a", ""))
            if q and a:
                faq_text += f"  Q: {q}\n  A: {a}\n\n"

    prompt = f"""You are a friendly, professional AI phone receptionist for {business.name}.

Your primary responsibilities:
1. Answer customer questions about the business
2. Book appointments when requested
3. Take messages if needed
4. Be helpful, concise, and professional

Business Information:
- Business Name: {business.name}
- Phone: {business.business_phone or "Not provided"}

Business Hours:
{hours_text}

Services Offered:
{services_text}

Frequently Asked Questions:
{faq_text if faq_text else "  No FAQs configured yet."}

Greeting: {business.greeting_message}

APPOINTMENT BOOKING INSTRUCTIONS:
When a caller wants to book an appointment:
1. Ask what service they need
2. Ask for their preferred date and time
3. Ask for their name and phone number
4. Use the "book_appointment" function to schedule it
5. Confirm the booking details with the caller

AVAILABILITY CHECK INSTRUCTIONS:
When a caller asks about availability:
1. Ask what service and date they're interested in
2. Use the "check_availability" function to look up open slots
3. Present the available times to the caller

GENERAL RULES:
- Always be polite and professional
- If you don't know something, say so honestly and offer to take a message
- Keep responses concise - this is a phone call, not a chat
- Spell out important details like times, dates, and names for clarity
- If the caller seems frustrated, empathize and try to help resolve their issue
"""
    return prompt


def _build_custom_functions(business: Business) -> list:
    """Build the custom function definitions for Retell agent function calling."""
    n8n_base = get_settings().n8n_webhook_base_url

    return [
        {
            "name": "book_appointment",
            "description": "Book an appointment for the caller. Use this when a customer wants to schedule a visit or service.",
            "url": f"{n8n_base}/book-appointment",
            "speak_during_execution": True,
            "speak_after_execution": True,
            "parameters": {
                "type": "object",
                "properties": {
                    "customer_name": {
                        "type": "string",
                        "description": "Full name of the customer",
                    },
                    "customer_phone": {
                        "type": "string",
                        "description": "Phone number of the customer",
                    },
                    "service": {
                        "type": "string",
                        "description": "The service the customer wants to book",
                    },
                    "preferred_date": {
                        "type": "string",
                        "description": "Preferred date in YYYY-MM-DD format",
                    },
                    "preferred_time": {
                        "type": "string",
                        "description": "Preferred time in HH:MM format (24-hour)",
                    },
                    "business_id": {
                        "type": "number",
                        "description": "The business ID",
                    },
                },
                "required": ["customer_name", "service", "preferred_date", "preferred_time"],
            },
        },
        {
            "name": "check_availability",
            "description": "Check available appointment slots for a given date. Use this when a customer asks what times are available.",
            "url": f"{n8n_base}/check-availability",
            "speak_during_execution": True,
            "speak_after_execution": True,
            "parameters": {
                "type": "object",
                "properties": {
                    "date": {
                        "type": "string",
                        "description": "The date to check in YYYY-MM-DD format",
                    },
                    "service": {
                        "type": "string",
                        "description": "The service to check availability for",
                    },
                    "business_id": {
                        "type": "number",
                        "description": "The business ID",
                    },
                },
                "required": ["date"],
            },
        },
    ]


async def create_retell_llm(business: Business) -> Optional[str]:
    """Create a Retell LLM with the business-specific prompt. Returns the llm_id."""
    prompt = build_agent_prompt(business)
    functions = _build_custom_functions(business)

    # Inject business_id default into function parameters
    for fn in functions:
        for prop_name, prop in fn["parameters"]["properties"].items():
            if prop_name == "business_id":
                prop["default"] = business.id

    payload = {
        "model": "gpt-4o-mini",
        "general_prompt": prompt,
        "general_tools": [
            {
                "type": "end_call",
                "name": "end_call",
                "description": "End the call when the conversation is naturally finished or the caller says goodbye.",
            },
        ],
    }

    try:
        async with httpx.AsyncClient(timeout=30) as client:
            resp = await client.post(
                f"{RETELL_BASE}/create-retell-llm",
                headers=_headers(),
                json=payload,
            )
            resp.raise_for_status()
            data = resp.json()
            logger.info(f"Created Retell LLM: {data.get('llm_id')}")
            return data.get("llm_id")
    except httpx.HTTPError as e:
        logger.error(f"Failed to create Retell LLM: {e}")
        return None


async def create_agent(business: Business) -> Optional[dict]:
    """
    Create a full Retell voice agent for a business.
    Returns dict with agent_id and llm_id.
    """
    llm_id = await create_retell_llm(business)
    if not llm_id:
        return None

    n8n_base = get_settings().n8n_webhook_base_url
    app_base = get_settings().app_base_url

    payload = {
        "agent_name": f"WorkWithAi - {business.name}",
        "response_engine": {
            "type": "retell-llm",
            "llm_id": llm_id,
        },
        "voice_id": "11labs-Adrian",
        "language": "en-US",
        "webhook_url": f"{n8n_base}/post-call",
        "post_call_analysis_data": [
            {"name": "call_summary", "type": "string", "description": "Brief summary of what the call was about"},
            {"name": "caller_sentiment", "type": "string", "description": "Overall sentiment: positive, neutral, or negative"},
            {"name": "action_items", "type": "string", "description": "Any action items or follow-ups needed"},
        ],
    }

    try:
        async with httpx.AsyncClient(timeout=30) as client:
            resp = await client.post(
                f"{RETELL_BASE}/create-agent",
                headers=_headers(),
                json=payload,
            )
            resp.raise_for_status()
            data = resp.json()
            agent_id = data.get("agent_id")
            logger.info(f"Created Retell agent: {agent_id}")
            return {"agent_id": agent_id, "llm_id": llm_id}
    except httpx.HTTPError as e:
        logger.error(f"Failed to create Retell agent: {e}")
        return None


async def update_agent(business: Business) -> bool:
    """Update the Retell agent when business settings change."""
    if not business.retell_agent_id or not business.retell_llm_id:
        return False

    prompt = build_agent_prompt(business)

    try:
        async with httpx.AsyncClient(timeout=30) as client:
            resp = await client.patch(
                f"{RETELL_BASE}/update-retell-llm/{business.retell_llm_id}",
                headers=_headers(),
                json={"general_prompt": prompt},
            )
            resp.raise_for_status()
            logger.info(f"Updated Retell LLM {business.retell_llm_id}")
            return True
    except httpx.HTTPError as e:
        logger.error(f"Failed to update Retell agent: {e}")
        return False


async def get_phone_number(agent_id: str) -> Optional[dict]:
    """Purchase and assign a phone number to the agent via Retell."""
    payload = {
        "agent_id": agent_id,
        "area_code": 415,
    }

    try:
        async with httpx.AsyncClient(timeout=30) as client:
            resp = await client.post(
                f"{RETELL_BASE}/create-phone-number",
                headers=_headers(),
                json=payload,
            )
            resp.raise_for_status()
            data = resp.json()
            logger.info(f"Assigned phone number: {data.get('phone_number')}")
            return {
                "phone_number": data.get("phone_number"),
                "phone_number_id": data.get("phone_number_id"),
            }
    except httpx.HTTPError as e:
        logger.error(f"Failed to get phone number: {e}")
        return None


async def list_calls(agent_id: str) -> list:
    """Fetch call history from Retell for the given agent."""
    try:
        async with httpx.AsyncClient(timeout=30) as client:
            resp = await client.post(
                f"{RETELL_BASE}/list-calls",
                headers=_headers(),
                json={"filter_criteria": {"agent_id": [agent_id]}},
            )
            resp.raise_for_status()
            return resp.json()
    except httpx.HTTPError as e:
        logger.error(f"Failed to list calls: {e}")
        return []


async def delete_agent(agent_id: str) -> bool:
    """Delete a Retell agent."""
    try:
        async with httpx.AsyncClient(timeout=30) as client:
            resp = await client.delete(
                f"{RETELL_BASE}/delete-agent/{agent_id}",
                headers=_headers(),
            )
            resp.raise_for_status()
            return True
    except httpx.HTTPError as e:
        logger.error(f"Failed to delete agent: {e}")
        return False
