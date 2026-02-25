import json
import logging
from datetime import datetime, timezone
from pathlib import Path

import stripe
from fastapi import Depends, FastAPI, Form, HTTPException, Request, status
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import HTMLResponse, JSONResponse, RedirectResponse
from fastapi.staticfiles import StaticFiles
from fastapi.templating import Jinja2Templates
from sqlalchemy.orm import Session

from app import retell_service, crm_service
from app.auth import (
    create_access_token,
    get_current_business,
    hash_password,
    verify_password,
)
from app.config import get_settings
from app.database import Base, engine, get_db
from app.models import Appointment, Business, CallLog, ChatLog
from app import chat_service
from app.schemas import (
    AppointmentCreate,
    AppointmentUpdate,
    AppointmentWebhookPayload,
    CallWebhookPayload,
    ChatMessageRequest,
)

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

Base.metadata.create_all(bind=engine)


def _ensure_landing_chat_business():
    """Create a default WorkWithAi business for landing page chat when DB is empty."""
    from app.database import SessionLocal
    settings = get_settings()
    if settings.landing_chat_business_id <= 0:
        return
    db = SessionLocal()
    try:
        if db.query(Business).count() > 0:
            return
            default = Business(
                name="WorkWithAi",
                email="workwithai@system.local",
                password_hash=hash_password("change-me-in-settings"),
                business_hours='{"Monday": "9:00 AM - 5:00 PM", "Tuesday": "9:00 AM - 5:00 PM", "Wednesday": "9:00 AM - 5:00 PM", "Thursday": "9:00 AM - 5:00 PM", "Friday": "9:00 AM - 5:00 PM", "Saturday": "Closed", "Sunday": "Closed"}',
                services='["AI Phone Agent", "Website Chatbot", "Appointment Booking", "24/7 Customer Support"]',
                faqs='[{"question": "What is WorkWithAi?", "answer": "WorkWithAi provides AI-powered phone answering and chatbot services for businesses. We help you never miss a call or lead."}, {"question": "How much does it cost?", "answer": "We have two plans: Pro at $499/month (500 calls) and Enterprise at $699/month (unlimited). There is a one-time $3,000 setup fee."}, {"question": "How do I get started?", "answer": "Fill out our intake form or call us at +1 (954) 593-8440. We will have your AI agent live within 24 hours."}]',
                greeting_message="Hi! I'm here to help with questions about WorkWithAi. What would you like to know?",
                business_phone="+1 (954) 593-8440",
            )
            db.add(default)
            db.commit()
            db.refresh(default)
            logger.info(f"Created default WorkWithAi business (id={default.id}) for landing page chat")
    except Exception as e:
        logger.warning(f"Could not ensure landing chat business: {e}")
    finally:
        db.close()


_ensure_landing_chat_business()

app = FastAPI(title="WorkWithAi", description="AI Phone Agent SaaS Platform")


@app.on_event("startup")
async def startup():
    s = get_settings()
    if s.openai_api_key:
        logger.info("Chatbot: OPENAI_API_KEY is configured")
    else:
        logger.warning("Chatbot: OPENAI_API_KEY is NOT set - add it to callpilot/.env and restart")


app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

_settings = get_settings()
stripe.api_key = _settings.stripe_secret_key

BASE_DIR = Path(__file__).resolve().parent
app.mount("/static", StaticFiles(directory=str(BASE_DIR / "static")), name="static")
templates = Jinja2Templates(directory=str(BASE_DIR / "templates"))


# ---------------------------------------------------------------------------
# Jinja2 custom filters
# ---------------------------------------------------------------------------

def _fmt_duration(seconds):
    if not seconds:
        return "0:00"
    m, s = divmod(int(seconds), 60)
    return f"{m}:{s:02d}"


def _fmt_datetime(dt):
    if not dt:
        return ""
    if isinstance(dt, str):
        try:
            dt = datetime.fromisoformat(dt)
        except ValueError:
            return dt
    return dt.strftime("%b %d, %Y %I:%M %p")


def _from_json(val):
    if not val:
        return val
    if isinstance(val, (dict, list)):
        return val
    try:
        return json.loads(val)
    except (json.JSONDecodeError, TypeError):
        return val


templates.env.filters["duration"] = _fmt_duration
templates.env.filters["fmt_datetime"] = _fmt_datetime
templates.env.filters["from_json"] = _from_json


# ========================== PAGE ROUTES ====================================


@app.get("/", response_class=HTMLResponse)
async def root(request: Request):
    token = request.cookies.get("access_token")
    if token:
        from app.auth import decode_token
        if decode_token(token) is not None:
            return RedirectResponse(url="/dashboard", status_code=302)
    settings = get_settings()
    return templates.TemplateResponse(
        "landing.html",
        {
            "request": request,
            "calendly_url": settings.calendly_url,
            "landing_chat_business_id": settings.landing_chat_business_id,
            "app_base_url": settings.app_base_url.rstrip("/"),
        },
    )


@app.get("/login", response_class=HTMLResponse)
async def login_page(request: Request):
    return templates.TemplateResponse("login.html", {"request": request})


@app.post("/login")
async def login_submit(
    request: Request,
    email: str = Form(...),
    password: str = Form(...),
    db: Session = Depends(get_db),
):
    try:
        business = db.query(Business).filter(Business.email == email).first()
        if not business or not verify_password(password, business.password_hash):
            return templates.TemplateResponse(
                "login.html",
                {"request": request, "error": "Invalid email or password"},
                status_code=400,
            )
        token = create_access_token(business.id)
        response = RedirectResponse(url="/dashboard", status_code=302)
        response.set_cookie(
            key="access_token",
            value=token,
            httponly=True,
            max_age=60 * 60 * 24 * 7,
            samesite="lax",
        )
        return response
    except Exception as e:
        logger.exception("Login failed")
        return templates.TemplateResponse(
            "login.html",
            {"request": request, "error": "Something went wrong. Check the server logs."},
            status_code=500,
        )


@app.get("/signup", response_class=HTMLResponse)
async def signup_page(request: Request):
    return templates.TemplateResponse("signup.html", {"request": request})


@app.post("/signup")
async def signup_submit(
    request: Request,
    business_name: str = Form(...),
    email: str = Form(...),
    password: str = Form(...),
    phone_number: str = Form(""),
    db: Session = Depends(get_db),
):
    try:
        existing = db.query(Business).filter(Business.email == email).first()
        if existing:
            return templates.TemplateResponse(
                "signup.html",
                {"request": request, "error": "Email already registered"},
                status_code=400,
            )

        business = Business(
            name=business_name,
            email=email,
            password_hash=hash_password(password),
            phone_number=phone_number or None,
        )
        db.add(business)
        db.commit()
        db.refresh(business)

        # Create Retell agent in background (non-blocking for signup)
        try:
            result = await retell_service.create_agent(business)
            if result:
                business.retell_agent_id = result["agent_id"]
                business.retell_llm_id = result["llm_id"]

                phone_result = await retell_service.get_phone_number(result["agent_id"])
                if phone_result:
                    business.assigned_phone_number = phone_result["phone_number"]
                    business.retell_phone_number_id = phone_result["phone_number_id"]

                db.commit()
        except Exception as e:
            logger.error(f"Retell setup failed for business {business.id}: {e}")

        token = create_access_token(business.id)
        response = RedirectResponse(url="/dashboard", status_code=302)
        response.set_cookie(
            key="access_token",
            value=token,
            httponly=True,
            max_age=60 * 60 * 24 * 7,
            samesite="lax",
        )
        return response
    except Exception as e:
        logger.exception("Signup failed")
        return templates.TemplateResponse(
            "signup.html",
            {"request": request, "error": "Something went wrong. Check the server logs."},
            status_code=500,
        )


@app.get("/logout")
async def logout():
    response = RedirectResponse(url="/login", status_code=302)
    response.delete_cookie("access_token")
    return response


# ========================== CLIENT INTAKE FORM =============================


@app.get("/intake", response_class=HTMLResponse)
async def intake_page(request: Request):
    return templates.TemplateResponse("intake.html", {"request": request})


@app.post("/intake")
async def intake_submit(
    request: Request,
    business_name: str = Form(...),
    email: str = Form(...),
    phone_number: str = Form(""),
    contact_name: str = Form(""),
    contact_title: str = Form(""),
    industry: str = Form(""),
    address: str = Form(""),
    website: str = Form(""),
    employee_count: str = Form(""),
    daily_call_volume: str = Form(""),
    plan_interest: str = Form(""),
    hours_json: str = Form("{}"),
    services_json: str = Form("[]"),
    faqs_json: str = Form("[]"),
    greeting_message: str = Form(""),
    google_calendar_id: str = Form(""),
    appointment_duration: str = Form("30"),
    appointment_rules: str = Form(""),
    collect_name: str = Form(""),
    collect_phone: str = Form(""),
    collect_email: str = Form(""),
    collect_insurance: str = Form(""),
    collect_reason: str = Form(""),
    collect_new_patient: str = Form(""),
    tone: str = Form("professional"),
    fallback_action: str = Form("take_message"),
    transfer_number: str = Form(""),
    lang_en: str = Form(""),
    lang_es: str = Form(""),
    lang_other: str = Form(""),
    special_instructions: str = Form(""),
    referral_source: str = Form(""),
    db: Session = Depends(get_db),
):
    existing = db.query(Business).filter(Business.email == email).first()
    if existing:
        return templates.TemplateResponse(
            "intake.html",
            {"request": request, "error": "This email is already registered. Contact us if you need help accessing your account."},
            status_code=400,
        )

    import secrets
    temp_password = secrets.token_urlsafe(10)

    faqs = []
    try:
        faqs = json.loads(faqs_json)
    except (json.JSONDecodeError, TypeError):
        pass

    # Fold all the extra context into the FAQs so the AI agent knows about it
    extra_context = []
    if address:
        extra_context.append(f"Our address is {address}.")
    if website:
        extra_context.append(f"Our website is {website}.")
    if appointment_rules:
        extra_context.append(f"Appointment rules: {appointment_rules}")
    if special_instructions:
        extra_context.append(special_instructions)
    if fallback_action == "transfer" and transfer_number:
        extra_context.append(f"If you can't answer a question, transfer the call to {transfer_number}.")
    elif fallback_action == "take_message":
        extra_context.append("If you can't answer a question, take a message and let them know someone will call back.")
    if collect_insurance:
        extra_context.append("Always ask for the customer's insurance information before booking.")
    if collect_new_patient:
        extra_context.append("Always ask if they are a new or returning customer.")

    if extra_context:
        faqs.append({
            "question": "Special instructions from the business owner",
            "answer": " ".join(extra_context),
        })

    # Log all intake data for your records
    intake_metadata = {
        "contact_name": contact_name,
        "contact_title": contact_title,
        "industry": industry,
        "address": address,
        "website": website,
        "employee_count": employee_count,
        "daily_call_volume": daily_call_volume,
        "plan_interest": plan_interest,
        "appointment_duration": appointment_duration,
        "tone": tone,
        "fallback_action": fallback_action,
        "transfer_number": transfer_number,
        "languages": [l for l, v in [("English", lang_en), ("Spanish", lang_es), ("Other", lang_other)] if v],
        "collect_fields": [f for f, v in [("name", collect_name), ("phone", collect_phone), ("email", collect_email), ("insurance", collect_insurance), ("reason", collect_reason), ("new_patient", collect_new_patient)] if v],
        "referral_source": referral_source,
    }

    business = Business(
        name=business_name,
        email=email,
        password_hash=hash_password(temp_password),
        phone_number=phone_number or None,
        business_phone=phone_number or None,
        business_hours=hours_json,
        services=services_json,
        faqs=json.dumps(faqs),
        greeting_message=greeting_message or f"Thank you for calling {business_name}! How can I help you today?",
        google_calendar_id=google_calendar_id or None,
    )
    db.add(business)
    db.commit()
    db.refresh(business)

    # Create Retell agent
    try:
        result = await retell_service.create_agent(business)
        if result:
            business.retell_agent_id = result["agent_id"]
            business.retell_llm_id = result["llm_id"]

            phone_result = await retell_service.get_phone_number(result["agent_id"])
            if phone_result:
                business.assigned_phone_number = phone_result["phone_number"]
                business.retell_phone_number_id = phone_result["phone_number_id"]

            db.commit()
    except Exception as e:
        logger.error(f"Retell setup failed for intake business {business.id}: {e}")

    logger.info(
        f"INTAKE: New client '{business_name}' ({email}) | "
        f"Contact: {contact_name} | "
        f"Temp password: {temp_password} | "
        f"Agent: {business.retell_agent_id} | "
        f"Phone: {business.assigned_phone_number} | "
        f"Plan: {plan_interest} | "
        f"Metadata: {json.dumps(intake_metadata)}"
    )

    return templates.TemplateResponse(
        "intake.html",
        {"request": request, "success": True},
    )


@app.get("/dashboard", response_class=HTMLResponse)
async def dashboard_page(
    request: Request,
    business: Business = Depends(get_current_business),
    db: Session = Depends(get_db),
):
    total_calls = db.query(CallLog).filter(CallLog.business_id == business.id).count()
    recent_calls = (
        db.query(CallLog)
        .filter(CallLog.business_id == business.id)
        .order_by(CallLog.created_at.desc())
        .limit(5)
        .all()
    )
    upcoming_appointments = (
        db.query(Appointment)
        .filter(
            Appointment.business_id == business.id,
            Appointment.status == "confirmed",
            Appointment.appointment_time >= datetime.now(timezone.utc),
        )
        .order_by(Appointment.appointment_time.asc())
        .limit(5)
        .all()
    )
    total_appointments = (
        db.query(Appointment).filter(Appointment.business_id == business.id).count()
    )

    return templates.TemplateResponse(
        "dashboard.html",
        {
            "request": request,
            "business": business,
            "total_calls": total_calls,
            "recent_calls": recent_calls,
            "upcoming_appointments": upcoming_appointments,
            "total_appointments": total_appointments,
        },
    )


@app.get("/calls", response_class=HTMLResponse)
async def calls_page(
    request: Request,
    business: Business = Depends(get_current_business),
    db: Session = Depends(get_db),
):
    calls = (
        db.query(CallLog)
        .filter(CallLog.business_id == business.id)
        .order_by(CallLog.created_at.desc())
        .all()
    )
    return templates.TemplateResponse(
        "calls.html",
        {"request": request, "business": business, "calls": calls},
    )


@app.get("/appointments", response_class=HTMLResponse)
async def appointments_page(
    request: Request,
    business: Business = Depends(get_current_business),
    db: Session = Depends(get_db),
):
    appointments = (
        db.query(Appointment)
        .filter(Appointment.business_id == business.id)
        .order_by(Appointment.appointment_time.desc())
        .all()
    )
    return templates.TemplateResponse(
        "appointments.html",
        {"request": request, "business": business, "appointments": appointments},
    )


@app.get("/clients", response_class=HTMLResponse)
async def clients_page(
    request: Request,
    business: Business = Depends(get_current_business),
    db: Session = Depends(get_db),
):
    all_businesses = db.query(Business).order_by(Business.created_at.desc()).all()
    clients = []
    for biz in all_businesses:
        call_count = db.query(CallLog).filter(CallLog.business_id == biz.id).count()
        appt_count = db.query(Appointment).filter(Appointment.business_id == biz.id).count()
        clients.append({"business": biz, "call_count": call_count, "appt_count": appt_count})

    return templates.TemplateResponse(
        "admin_clients.html",
        {
            "request": request,
            "business": business,
            "clients": clients,
            "base_url": get_settings().app_base_url,
        },
    )


@app.get("/settings", response_class=HTMLResponse)
async def settings_page(
    request: Request,
    business: Business = Depends(get_current_business),
):
    return templates.TemplateResponse(
        "settings.html",
        {"request": request, "business": business},
    )


@app.post("/settings")
async def settings_update(
    request: Request,
    business_name: str = Form(""),
    phone_number: str = Form(""),
    greeting_message: str = Form(""),
    business_hours: str = Form("{}"),
    services: str = Form("[]"),
    faqs: str = Form("[]"),
    google_calendar_id: str = Form(""),
    website_url: str = Form(""),
    crm_provider: str = Form(""),
    crm_access_token: str = Form(""),
    business: Business = Depends(get_current_business),
    db: Session = Depends(get_db),
):
    if business_name:
        business.name = business_name
    if phone_number:
        business.business_phone = phone_number
    if greeting_message:
        business.greeting_message = greeting_message
    if google_calendar_id:
        business.google_calendar_id = google_calendar_id
    business.website_url = website_url.strip() or None
    business.crm_provider = crm_provider.strip() or None
    if crm_access_token.strip():
        business.crm_access_token = crm_access_token.strip()
    elif not crm_provider.strip():
        business.crm_access_token = None  # Clear token when CRM disabled

    try:
        business.business_hours = business_hours
    except Exception:
        pass
    try:
        business.services = services
    except Exception:
        pass
    try:
        business.faqs = faqs
    except Exception:
        pass

    db.commit()

    # Sync updates to Retell agent
    if business.retell_agent_id:
        try:
            await retell_service.update_agent(business)
        except Exception as e:
            logger.error(f"Failed to sync Retell agent: {e}")

    return templates.TemplateResponse(
        "settings.html",
        {"request": request, "business": business, "success": "Settings updated successfully!"},
    )


@app.post("/api/crm/test")
async def crm_test_connection(business: Business = Depends(get_current_business)):
    """Test CRM connection. Uses saved token."""
    if not business.crm_provider or business.crm_provider != "hubspot":
        return {"ok": False, "message": "No CRM provider configured"}
    if not business.crm_access_token:
        return {"ok": False, "message": "No access token found. Save your token first."}
    ok, msg = await crm_service.hubspot_test_connection(business.crm_access_token)
    return {"ok": ok, "message": msg}


@app.get("/chat-logs", response_class=HTMLResponse)
async def chat_logs_page(
    request: Request,
    business: Business = Depends(get_current_business),
    db: Session = Depends(get_db),
):
    chat_logs = (
        db.query(ChatLog)
        .filter(ChatLog.business_id == business.id)
        .order_by(ChatLog.created_at.desc())
        .limit(200)
        .all()
    )
    return templates.TemplateResponse(
        "chat_logs.html",
        {"request": request, "business": business, "chat_logs": chat_logs},
    )


@app.get("/chatbot", response_class=HTMLResponse)
async def chatbot_page(
    request: Request,
    business: Business = Depends(get_current_business),
):
    settings = get_settings()
    base_url = settings.app_base_url.rstrip("/")
    embed_code = f'<script src="{base_url}/static/chat-widget.js" data-business-id="{business.id}"></script>'
    return templates.TemplateResponse(
        "chatbot.html",
        {
            "request": request,
            "business": business,
            "embed_code": embed_code,
            "base_url": base_url,
        },
    )


@app.get("/billing", response_class=HTMLResponse)
async def billing_page(
    request: Request,
    business: Business = Depends(get_current_business),
    db: Session = Depends(get_db),
):
    plan = getattr(business, "plan", "pro") or "pro"
    billing_status = getattr(business, "billing_status", "active") or "active"

    plan_name = "Pro" if plan == "pro" else "Enterprise"
    plan_price = "$499/mo" if plan == "pro" else "$699/mo"
    call_limit = "500" if plan == "pro" else "Unlimited"
    phone_numbers = "1" if plan == "pro" else "Up to 3"

    total_calls = db.query(CallLog).filter(CallLog.business_id == business.id).count()
    total_appointments = (
        db.query(Appointment).filter(Appointment.business_id == business.id).count()
    )

    return templates.TemplateResponse(
        "billing.html",
        {
            "request": request,
            "business": business,
            "plan": plan,
            "plan_name": plan_name,
            "plan_price": plan_price,
            "call_limit": call_limit,
            "phone_numbers": phone_numbers,
            "billing_status": billing_status,
            "total_calls": total_calls,
            "total_appointments": total_appointments,
            "stripe_publishable_key": _settings.stripe_publishable_key,
        },
    )


# ========================== STRIPE ROUTES ===================================


PLAN_TO_PRICE = {
    "pro": _settings.stripe_pro_price_id,
    "enterprise": _settings.stripe_enterprise_price_id,
}


@app.post("/api/stripe/checkout")
async def stripe_create_checkout(
    request: Request,
    business: Business = Depends(get_current_business),
    db: Session = Depends(get_db),
):
    """Create a Stripe Checkout session for setup fee + subscription."""
    settings = get_settings()
    body = await request.json()
    chosen_plan = body.get("plan", business.plan or "pro")

    subscription_price = PLAN_TO_PRICE.get(chosen_plan)
    if not subscription_price:
        raise HTTPException(status_code=400, detail="Invalid plan")

    if not business.stripe_customer_id:
        customer = stripe.Customer.create(
            email=business.email,
            name=business.name,
            metadata={"business_id": str(business.id)},
        )
        business.stripe_customer_id = customer.id
        db.commit()

    line_items = []

    if not business.setup_fee_paid and settings.stripe_setup_price_id:
        line_items.append({
            "price": settings.stripe_setup_price_id,
            "quantity": 1,
        })

    line_items.append({
        "price": subscription_price,
        "quantity": 1,
    })

    checkout_session = stripe.checkout.Session.create(
        customer=business.stripe_customer_id,
        mode="subscription",
        line_items=line_items,
        success_url=f"{settings.app_base_url}/billing?session_id={{CHECKOUT_SESSION_ID}}&success=1",
        cancel_url=f"{settings.app_base_url}/billing?cancelled=1",
        metadata={
            "business_id": str(business.id),
            "plan": chosen_plan,
        },
        subscription_data={
            "metadata": {
                "business_id": str(business.id),
                "plan": chosen_plan,
            },
        },
    )

    return {"checkout_url": checkout_session.url}


@app.post("/api/stripe/portal")
async def stripe_customer_portal(
    business: Business = Depends(get_current_business),
):
    """Create a Stripe Customer Portal session so the user can manage billing."""
    if not business.stripe_customer_id:
        raise HTTPException(status_code=400, detail="No Stripe account linked")

    settings = get_settings()
    portal_session = stripe.billing_portal.Session.create(
        customer=business.stripe_customer_id,
        return_url=f"{settings.app_base_url}/billing",
    )
    return {"portal_url": portal_session.url}


@app.post("/api/stripe/webhook")
async def stripe_webhook(request: Request, db: Session = Depends(get_db)):
    """Handle Stripe webhook events for subscription lifecycle."""
    payload = await request.body()
    sig_header = request.headers.get("stripe-signature", "")
    settings = get_settings()

    try:
        event = stripe.Webhook.construct_event(
            payload, sig_header, settings.stripe_webhook_secret
        )
    except stripe.error.SignatureVerificationError:
        raise HTTPException(status_code=400, detail="Invalid signature")
    except Exception as e:
        logger.error(f"Stripe webhook error: {e}")
        raise HTTPException(status_code=400, detail="Webhook error")

    event_type = event["type"]
    data = event["data"]["object"]

    logger.info(f"Stripe event: {event_type}")

    if event_type == "checkout.session.completed":
        business_id = data.get("metadata", {}).get("business_id")
        plan = data.get("metadata", {}).get("plan", "pro")
        subscription_id = data.get("subscription")
        customer_id = data.get("customer")

        if business_id:
            biz = db.query(Business).filter(Business.id == int(business_id)).first()
            if biz:
                biz.stripe_customer_id = customer_id
                biz.stripe_subscription_id = subscription_id
                biz.plan = plan
                biz.billing_status = "active"
                biz.setup_fee_paid = True
                db.commit()
                logger.info(f"Activated subscription for business {business_id} on plan {plan}")

    elif event_type == "customer.subscription.updated":
        sub_id = data.get("id")
        status = data.get("status")
        biz = db.query(Business).filter(Business.stripe_subscription_id == sub_id).first()
        if biz:
            status_map = {
                "active": "active",
                "past_due": "past_due",
                "canceled": "cancelled",
                "unpaid": "past_due",
                "trialing": "active",
            }
            biz.billing_status = status_map.get(status, status)
            db.commit()

    elif event_type == "customer.subscription.deleted":
        sub_id = data.get("id")
        biz = db.query(Business).filter(Business.stripe_subscription_id == sub_id).first()
        if biz:
            biz.billing_status = "cancelled"
            db.commit()
            logger.info(f"Subscription cancelled for business {biz.id}")

    elif event_type == "invoice.payment_failed":
        customer_id = data.get("customer")
        biz = db.query(Business).filter(Business.stripe_customer_id == customer_id).first()
        if biz:
            biz.billing_status = "past_due"
            db.commit()
            logger.info(f"Payment failed for business {biz.id}")

    return {"status": "ok"}


# ========================== API ROUTES =====================================


@app.post("/api/calls/webhook")
async def call_webhook(payload: CallWebhookPayload, db: Session = Depends(get_db)):
    """Webhook endpoint for n8n to POST call data after a call ends."""
    business = None

    if payload.business_id:
        business = db.query(Business).filter(Business.id == payload.business_id).first()
    elif payload.agent_id:
        business = (
            db.query(Business)
            .filter(Business.retell_agent_id == payload.agent_id)
            .first()
        )

    if not business:
        raise HTTPException(status_code=404, detail="Business not found")

    existing = None
    if payload.retell_call_id:
        existing = (
            db.query(CallLog)
            .filter(CallLog.retell_call_id == payload.retell_call_id)
            .first()
        )

    if existing:
        existing.transcript = payload.transcript or existing.transcript
        existing.summary = payload.summary or existing.summary
        existing.sentiment = payload.sentiment or existing.sentiment
        existing.call_status = payload.call_status or existing.call_status
        existing.duration_seconds = payload.duration_seconds or existing.duration_seconds
        existing.disconnection_reason = payload.disconnection_reason
    else:
        call_log = CallLog(
            business_id=business.id,
            retell_call_id=payload.retell_call_id or payload.call_id,
            caller_number=payload.caller_number,
            direction=payload.direction or "inbound",
            duration_seconds=payload.duration_seconds or 0,
            transcript=payload.transcript,
            summary=payload.summary,
            sentiment=payload.sentiment,
            call_status=payload.call_status or "completed",
            disconnection_reason=payload.disconnection_reason,
        )
        db.add(call_log)

    db.commit()

    # Push to CRM if configured (HubSpot)
    if business.crm_provider == "hubspot" and business.crm_access_token:
        try:
            await crm_service.hubspot_log_call(
                access_token=business.crm_access_token,
                caller_phone=payload.caller_number or "",
                duration_seconds=payload.duration_seconds or 0,
                summary=payload.summary or "AI phone call",
                transcript=payload.transcript,
                direction=(payload.direction or "inbound").upper(),
                caller_name=payload.caller_name,
            )
        except Exception as e:
            logger.warning(f"CRM sync failed: {e}")

    return {"status": "ok"}


@app.post("/api/appointments/webhook")
async def appointment_webhook(
    payload: AppointmentWebhookPayload, db: Session = Depends(get_db)
):
    """Webhook endpoint for n8n to POST appointment data after booking."""
    business = None

    if payload.business_id:
        business = db.query(Business).filter(Business.id == payload.business_id).first()
    elif payload.agent_id:
        business = (
            db.query(Business)
            .filter(Business.retell_agent_id == payload.agent_id)
            .first()
        )

    if not business:
        raise HTTPException(status_code=404, detail="Business not found")

    call_log = None
    if payload.call_id:
        call_log = (
            db.query(CallLog)
            .filter(CallLog.retell_call_id == payload.call_id)
            .first()
        )

    try:
        appt_time = datetime.fromisoformat(payload.appointment_time)
    except ValueError:
        raise HTTPException(status_code=400, detail="Invalid appointment_time format")

    appointment = Appointment(
        business_id=business.id,
        call_log_id=call_log.id if call_log else None,
        customer_name=payload.customer_name,
        customer_phone=payload.customer_phone,
        customer_email=payload.customer_email,
        service=payload.service,
        appointment_time=appt_time,
        duration_minutes=payload.duration_minutes,
        google_event_id=payload.google_event_id,
        notes=payload.notes,
        status="confirmed",
    )
    db.add(appointment)
    db.commit()

    # Push appointment to HubSpot as meeting
    if business.crm_provider == "hubspot" and business.crm_access_token:
        try:
            await crm_service.hubspot_log_meeting(
                access_token=business.crm_access_token,
                contact_phone=payload.customer_phone,
                contact_email=payload.customer_email,
                contact_name=payload.customer_name,
                title=payload.service or "Appointment",
                start_time=appt_time,
                duration_minutes=payload.duration_minutes or 30,
                notes=payload.notes,
            )
        except Exception as e:
            logger.warning(f"CRM meeting sync failed: {e}")

    return {"status": "ok", "appointment_id": appointment.id}


@app.post("/api/appointments/create")
async def create_appointment(
    data: AppointmentCreate,
    business: Business = Depends(get_current_business),
    db: Session = Depends(get_db),
):
    """Manually create an appointment from the dashboard."""
    appointment = Appointment(
        business_id=business.id,
        customer_name=data.customer_name,
        customer_phone=data.customer_phone,
        customer_email=data.customer_email,
        service=data.service,
        appointment_time=data.appointment_time,
        duration_minutes=data.duration_minutes,
        notes=data.notes,
        status="confirmed",
    )
    db.add(appointment)
    db.commit()
    return {"status": "ok", "appointment_id": appointment.id}


@app.post("/api/appointments/{appointment_id}/update")
async def update_appointment(
    appointment_id: int,
    data: AppointmentUpdate,
    business: Business = Depends(get_current_business),
    db: Session = Depends(get_db),
):
    appt = (
        db.query(Appointment)
        .filter(Appointment.id == appointment_id, Appointment.business_id == business.id)
        .first()
    )
    if not appt:
        raise HTTPException(status_code=404, detail="Appointment not found")
    if data.status:
        appt.status = data.status
    if data.appointment_time:
        appt.appointment_time = data.appointment_time
    if data.notes is not None:
        appt.notes = data.notes
    db.commit()
    return {"status": "ok"}


@app.get("/api/business/info")
async def business_info(business: Business = Depends(get_current_business)):
    """Return current business info (used by settings page JS)."""
    return {
        "id": business.id,
        "name": business.name,
        "email": business.email,
        "phone_number": business.business_phone,
        "business_hours": business.hours_dict,
        "services": business.services_list,
        "faqs": business.faqs_list,
        "greeting_message": business.greeting_message,
        "assigned_phone_number": business.assigned_phone_number,
        "retell_agent_id": business.retell_agent_id,
        "google_calendar_id": business.google_calendar_id,
    }


# ========================== CHATBOT API (public - for widget on external sites) =====


@app.get("/api/chat/config")
async def chat_config(business_id: int, db: Session = Depends(get_db)):
    """Return business config for the chat widget. Public endpoint."""
    business = db.query(Business).filter(Business.id == business_id).first()
    if not business:
        raise HTTPException(status_code=404, detail="Business not found")
    return {
        "name": business.name,
        "business_hours": business.hours_dict,
        "services": business.services_list,
        "faqs": business.faqs_list,
        "greeting_message": business.greeting_message or f"Hi! How can I help you today?",
        "business_phone": business.business_phone or business.assigned_phone_number,
    }


@app.post("/api/chat/message")
async def chat_message(data: ChatMessageRequest, db: Session = Depends(get_db)):
    """Process a chat message and return AI reply. Public endpoint."""
    business = db.query(Business).filter(Business.id == data.business_id).first()
    if not business:
        raise HTTPException(status_code=404, detail="Business not found")
    history = data.conversation_history or []
    reply = await chat_service.get_chat_reply(business, data.message, history)
    # Log for learning - review common questions and add to FAQs
    log_entry = ChatLog(
        business_id=business.id,
        user_message=data.message,
        assistant_reply=reply,
        session_id=getattr(data, "session_id", None),
    )
    db.add(log_entry)
    db.commit()
    return {"reply": reply}


# ========================== RETELL AGENT MANAGEMENT ========================


@app.post("/api/agent/provision")
async def provision_agent(
    business: Business = Depends(get_current_business),
    db: Session = Depends(get_db),
):
    """Manually trigger Retell agent creation (if signup didn't complete it)."""
    if business.retell_agent_id:
        return {"status": "already_exists", "agent_id": business.retell_agent_id}

    result = await retell_service.create_agent(business)
    if not result:
        raise HTTPException(status_code=500, detail="Failed to create Retell agent")

    business.retell_agent_id = result["agent_id"]
    business.retell_llm_id = result["llm_id"]

    phone_result = await retell_service.get_phone_number(result["agent_id"])
    if phone_result:
        business.assigned_phone_number = phone_result["phone_number"]
        business.retell_phone_number_id = phone_result["phone_number_id"]

    db.commit()
    return {
        "status": "created",
        "agent_id": result["agent_id"],
        "phone_number": business.assigned_phone_number,
    }


# ========================== ERROR HANDLERS =================================


@app.exception_handler(HTTPException)
async def http_exception_handler(request: Request, exc: HTTPException):
    if exc.status_code == 303:
        return RedirectResponse(url=exc.headers.get("Location", "/login"), status_code=302)
    if request.url.path.startswith("/api/"):
        return JSONResponse(
            status_code=exc.status_code,
            content={"detail": exc.detail},
        )
    return templates.TemplateResponse(
        "login.html",
        {"request": request, "error": exc.detail},
        status_code=exc.status_code,
    )
