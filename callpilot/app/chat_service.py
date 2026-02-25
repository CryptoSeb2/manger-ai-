"""
Website chatbot service. Builds AI prompts from business data and calls OpenAI.
Scans the website to learn its content for better answers.
"""

import re
import logging
from time import time
from typing import Optional

import httpx
from openai import AsyncOpenAI

from app.config import get_settings
from app.models import Business

logger = logging.getLogger(__name__)

# Cache for scraped website content: {url: (content, timestamp)}
_website_cache: dict[str, tuple[str, float]] = {}
_CACHE_TTL = 3600  # 1 hour


def _strip_html(html: str) -> str:
    """Extract readable text from HTML."""
    text = re.sub(r"<script[^>]*>.*?</script>", "", html, flags=re.DOTALL | re.IGNORECASE)
    text = re.sub(r"<style[^>]*>.*?</style>", "", text, flags=re.DOTALL | re.IGNORECASE)
    text = re.sub(r"<[^>]+>", " ", text)
    text = re.sub(r"&nbsp;", " ", text)
    text = re.sub(r"&amp;", "&", text)
    text = re.sub(r"&lt;", "<", text)
    text = re.sub(r"&gt;", ">", text)
    text = re.sub(r"&quot;", '"', text)
    text = re.sub(r"\s+", " ", text)
    return text.strip()


async def scrape_website(url: str) -> str:
    """Fetch a URL and extract text content. Cached for 1 hour."""
    now = time()
    if url in _website_cache:
        content, cached_at = _website_cache[url]
        if now - cached_at < _CACHE_TTL:
            return content
    try:
        async with httpx.AsyncClient(timeout=10.0) as client:
            r = await client.get(url)
            r.raise_for_status()
            text = _strip_html(r.text)
            # Keep first ~2500 chars to avoid token limit
            text = text[:2500] if len(text) > 2500 else text
            _website_cache[url] = (text, now)
            return text
    except Exception as e:
        logger.warning(f"Could not scrape website {url}: {e}")
        return ""


def _get_fallback_message(business: Business) -> str:
    """Return a helpful fallback with contact info when AI is unavailable."""
    phone = business.assigned_phone_number or business.business_phone or ""
    email = business.email or ""
    if email == "workwithai@system.local":
        email = ""
    parts = ["I'm having a technical hiccup right now, but I'd love to help!"]
    if phone or email:
        contact = []
        if phone:
            contact.append(f"call us at {phone}")
        if email:
            contact.append(f"email {email}")
        parts.append("Please " + " or ".join(contact) + " and we'll get right back to you.")
    else:
        parts.append("Please reach out through our Contact section and we'll get right back to you.")
    return " ".join(parts) + " You can also explore our site: Features, Pricing, and Contact sections above, or click Get Started to apply."


def build_chat_system_prompt(business: Business, website_content: str = "") -> str:
    """Build the system prompt for the chatbot from business config and scraped website content."""
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

    phone = business.assigned_phone_number or business.business_phone or "Not provided"
    email = business.email or "See contact section on our website"
    if email == "workwithai@system.local":
        email = "See contact section on our website"

    settings = get_settings()
    base = settings.app_base_url.rstrip("/")

    website_section = ""
    if website_content:
        website_section = f"""
WEBSITE CONTENT (scanned from the site - use this to answer questions about what we offer, pricing, features, etc.):
{website_content}

"""

    prompt = f"""You are the friendly chat assistant for {business.name}. You help visitors navigate the website, answer questions, and connect them with the team.

YOUR PRIORITIES:
1. Guide people around the website - tell them where to find things
2. Answer simple questions using the info below (including website content if available)
3. When you're unsure or can't answer: ALWAYS give them our contact info and suggest they reach out directly
4. Be warm, concise, and helpful

CONTACT INFO (always share when unsure or for appointments/pricing):
- Phone: {phone}
- Email: {email}

WEBSITE NAVIGATION (help visitors find things):
- Features: {base}/#features
- Pricing: {base}/#pricing
- Contact: {base}/#contact
- Get Started / Apply: {base}/intake
- Sign In: {base}/login
{website_section}
BUSINESS INFO:
- Name: {business.name}
- Hours: {hours_text}
- Services: {services_text}

FAQs:
{faq_text if faq_text else "  No FAQs yet."}

RULES:
- Keep replies brief (2-4 sentences) unless more detail is needed
- When you don't know: "I'm not sure about that. Please call us at {phone} or email {email} and we'll help you right away."
- For pricing, appointments, or complex questions: direct them to call or email
- Never make up information - only use what's provided
- Suggest exploring Features, Pricing, or Contact when relevant
"""
    return prompt


async def get_chat_reply(
    business: Business,
    message: str,
    conversation_history: list[dict],
) -> Optional[str]:
    """Get an AI reply for the chat message. Returns fallback with contact info if OpenAI fails."""
    settings = get_settings()
    fallback = _get_fallback_message(business)

    if not settings.openai_api_key:
        logger.warning("OPENAI_API_KEY not set - chatbot will not work")
        return fallback

    # Scrape website to learn its content (cached 1 hr)
    website_url = getattr(business, "website_url", None) or settings.app_base_url.rstrip("/")
    if not website_url.startswith("http"):
        website_url = f"http://{website_url}"
    website_content = await scrape_website(website_url)

    client = AsyncOpenAI(api_key=settings.openai_api_key)
    system_prompt = build_chat_system_prompt(business, website_content)

    messages = [{"role": "system", "content": system_prompt}]
    for h in conversation_history[-10:]:
        messages.append({"role": h["role"], "content": h["content"]})
    messages.append({"role": "user", "content": message})

    try:
        response = await client.chat.completions.create(
            model="gpt-4o-mini",
            messages=messages,
            max_tokens=300,
            temperature=0.7,
        )
        reply = response.choices[0].message.content
        return reply.strip() if reply else fallback
    except Exception as e:
        logger.error(f"Chat OpenAI error: {e}")
        return fallback
