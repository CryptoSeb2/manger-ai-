"""
CRM integration service. Syncs calls, appointments, and contacts to HubSpot (and optionally other CRMs).
"""

import logging
from datetime import datetime, timedelta
from typing import Optional

import httpx

logger = logging.getLogger(__name__)

HUBSPOT_BASE = "https://api.hubapi.com"


def _hubspot_headers(access_token: str) -> dict:
    return {
        "Authorization": f"Bearer {access_token}",
        "Content-Type": "application/json",
    }


async def hubspot_test_connection(access_token: str) -> tuple[bool, str]:
    """Test HubSpot API connection. Returns (success, message)."""
    if not access_token:
        return False, "No access token configured"
    try:
        async with httpx.AsyncClient(timeout=10.0) as client:
            r = await client.get(
                f"{HUBSPOT_BASE}/crm/v3/objects/contacts",
                headers=_hubspot_headers(access_token),
                params={"limit": 1},
            )
            if r.status_code == 200:
                return True, "Connected successfully"
            if r.status_code == 401:
                return False, "Invalid access token"
            return False, f"HubSpot returned {r.status_code}"
    except Exception as e:
        return False, str(e)


async def hubspot_find_contact_by_email(access_token: str, email: str) -> Optional[str]:
    """Search for a HubSpot contact by email. Returns contact ID or None."""
    if not email or not access_token:
        return None
    email = email.strip().lower()
    if "@" not in email:
        return None
    try:
        async with httpx.AsyncClient(timeout=10.0) as client:
            r = await client.post(
                f"{HUBSPOT_BASE}/crm/v3/objects/contacts/search",
                headers=_hubspot_headers(access_token),
                json={
                    "filterGroups": [
                        {
                            "filters": [
                                {
                                    "propertyName": "email",
                                    "operator": "EQ",
                                    "value": email,
                                }
                            ]
                        }
                    ],
                    "limit": 1,
                },
            )
            if r.status_code != 200:
                return None
            data = r.json()
            results = data.get("results", [])
            if results:
                return results[0]["id"]
            return None
    except Exception as e:
        logger.warning(f"HubSpot find contact by email error: {e}")
        return None


async def hubspot_find_contact_by_phone(access_token: str, phone: str) -> Optional[str]:
    """Search for a HubSpot contact by phone number. Returns contact ID or None."""
    if not phone or not access_token:
        return None
    # Normalize phone for search (strip non-digits)
    phone_digits = "".join(c for c in phone if c.isdigit())
    if len(phone_digits) < 10:
        return None
    try:
        async with httpx.AsyncClient(timeout=10.0) as client:
            r = await client.post(
                f"{HUBSPOT_BASE}/crm/v3/objects/contacts/search",
                headers=_hubspot_headers(access_token),
                json={
                    "filterGroups": [
                        {
                            "filters": [
                                {
                                    "propertyName": "phone",
                                    "operator": "CONTAINS_TOKEN",
                                    "value": phone_digits[-10:],  # last 10 digits
                                }
                            ]
                        }
                    ],
                    "limit": 1,
                },
            )
            if r.status_code != 200:
                logger.warning(f"HubSpot search failed: {r.status_code} {r.text[:200]}")
                return None
            data = r.json()
            results = data.get("results", [])
            if results:
                return results[0]["id"]
            return None
    except Exception as e:
        logger.warning(f"HubSpot find contact error: {e}")
        return None


async def hubspot_create_contact(
    access_token: str,
    phone: Optional[str] = None,
    email: Optional[str] = None,
    name: Optional[str] = None,
) -> Optional[str]:
    """Create a HubSpot contact. Returns contact ID or None. Provide at least phone or email."""
    if not access_token or (not phone and not email):
        return None
    try:
        properties: dict = {}
        if phone:
            properties["phone"] = phone
        if email:
            properties["email"] = email.strip().lower()
        if name:
            parts = name.strip().split(maxsplit=1)
            properties["firstname"] = parts[0]
            properties["lastname"] = parts[1] if len(parts) > 1 else ""
        async with httpx.AsyncClient(timeout=10.0) as client:
            r = await client.post(
                f"{HUBSPOT_BASE}/crm/v3/objects/contacts",
                headers=_hubspot_headers(access_token),
                json={"properties": properties},
            )
            if r.status_code not in (200, 201):
                logger.warning(f"HubSpot create contact failed: {r.status_code} {r.text[:200]}")
                return None
            data = r.json()
            return data.get("id")
    except Exception as e:
        logger.warning(f"HubSpot create contact error: {e}")
        return None


async def hubspot_log_call(
    access_token: str,
    caller_phone: str,
    duration_seconds: float,
    summary: str,
    transcript: Optional[str] = None,
    direction: str = "INBOUND",
    caller_name: Optional[str] = None,
) -> bool:
    """
    Log a call to HubSpot. Finds or creates contact, then creates call engagement with association.
    """
    if not access_token:
        return False
    contact_id = await hubspot_find_contact_by_phone(access_token, caller_phone)
    if not contact_id:
        contact_id = await hubspot_create_contact(
            access_token, phone=caller_phone, name=caller_name
        )
    if not contact_id:
        logger.warning("Could not find or create HubSpot contact for call log")
        return False

    import time
    timestamp_ms = int(time.time() * 1000)
    duration_ms = int(duration_seconds * 1000) if duration_seconds else 0
    call_body = summary or "AI phone call"
    if transcript:
        call_body = f"{call_body}\n\nTranscript:\n{transcript[:3000]}"

    try:
        async with httpx.AsyncClient(timeout=10.0) as client:
            r = await client.post(
                f"{HUBSPOT_BASE}/crm/v3/objects/calls",
                headers=_hubspot_headers(access_token),
                json={
                    "properties": {
                        "hs_timestamp": str(timestamp_ms),
                        "hs_call_direction": direction,
                        "hs_call_duration": str(duration_ms),
                        "hs_call_body": call_body,
                        "hs_call_status": "COMPLETED",
                        "hs_call_from_number": caller_phone or "",
                    },
                    "associations": [
                        {
                            "to": {"id": contact_id},
                            "types": [
                                {
                                    "associationCategory": "HUBSPOT_DEFINED",
                                    "associationTypeId": 181,
                                }
                            ],
                        }
                    ],
                },
            )
            if r.status_code not in (200, 201):
                logger.warning(f"HubSpot log call failed: {r.status_code} {r.text[:300]}")
                return False
            return True
    except Exception as e:
        logger.warning(f"HubSpot log call error: {e}")
        return False


async def hubspot_log_meeting(
    access_token: str,
    contact_phone: Optional[str],
    contact_email: Optional[str],
    contact_name: str,
    title: str,
    start_time: datetime,
    duration_minutes: int = 30,
    notes: Optional[str] = None,
) -> bool:
    """
    Log a scheduled meeting/appointment to HubSpot. Finds or creates contact, creates meeting.
    """
    if not access_token:
        return False
    contact_id = None
    if contact_email:
        contact_id = await hubspot_find_contact_by_email(access_token, contact_email)
    if not contact_id and contact_phone:
        contact_id = await hubspot_find_contact_by_phone(access_token, contact_phone)
    if not contact_id:
        contact_id = await hubspot_create_contact(
            access_token,
            phone=contact_phone,
            email=contact_email,
            name=contact_name or None,
        )
    if not contact_id:
        logger.warning("Could not find or create HubSpot contact for meeting")
        return False

    iso_start = start_time.strftime("%Y-%m-%dT%H:%M:%S.000Z")
    end_time = start_time + timedelta(minutes=duration_minutes)
    iso_end = end_time.strftime("%Y-%m-%dT%H:%M:%S.000Z")

    ts_ms = int(start_time.timestamp() * 1000)
    body = {"properties": {
        "hs_timestamp": str(ts_ms),
        "hs_meeting_start_time": iso_start,
        "hs_meeting_end_time": iso_end,
        "hs_meeting_title": title or "Appointment",
        "hs_meeting_outcome": "SCHEDULED",
    }}
    if notes:
        body["properties"]["hs_meeting_body"] = notes
    body["associations"] = [
        {
            "to": {"id": contact_id},
            "types": [{"associationCategory": "HUBSPOT_DEFINED", "associationTypeId": 200}],
        }
    ]

    try:
        async with httpx.AsyncClient(timeout=10.0) as client:
            r = await client.post(
                f"{HUBSPOT_BASE}/crm/v3/objects/meetings",
                headers=_hubspot_headers(access_token),
                json=body,
            )
            if r.status_code not in (200, 201):
                logger.warning(f"HubSpot log meeting failed: {r.status_code} {r.text[:300]}")
                return False
            return True
    except Exception as e:
        logger.warning(f"HubSpot log meeting error: {e}")
        return False
