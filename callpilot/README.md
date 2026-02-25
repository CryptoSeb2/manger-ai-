# WorkWithAi - AI Phone Agent SaaS Platform

WorkWithAi is a white-label SaaS platform that gives businesses an AI-powered phone receptionist. It answers calls, handles customer support, and books appointments — all automatically.

**Built with:** Retell AI (voice agents) + n8n (workflow automation) + FastAPI (dashboard)

---

## How It Works

1. **Business signs up** on the WorkWithAi dashboard and enters their info (name, hours, services, FAQs)
2. **WorkWithAi creates a voice AI agent** on Retell AI with a custom prompt tailored to the business
3. **Business gets a phone number** — customers call it (or the business forwards their existing number to it)
4. **AI answers calls** — handles support questions, gives business info, and books appointments
5. **Appointments go to Google Calendar** via n8n workflows
6. **Business owner sees everything** — call logs, transcripts, sentiment analysis, and appointments in the dashboard

---

## Quick Start

### Prerequisites

- Python 3.10+
- A [Retell AI](https://retellai.com) account (get your API key from the dashboard)
- An [n8n](https://n8n.io) instance (cloud or self-hosted)
- A Google account (for Google Calendar integration via n8n)

### 1. Clone & Install

```bash
cd workwithai
python -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate
pip install -r requirements.txt
```

### 2. Configure Environment

```bash
cp .env.example .env
```

Edit `.env` with your credentials:

```
RETELL_API_KEY=your_retell_api_key_here
N8N_WEBHOOK_BASE_URL=https://your-n8n.com/webhook
SECRET_KEY=generate_a_random_secret_here
DATABASE_URL=sqlite:///./workwithai.db
APP_BASE_URL=http://localhost:8000
```

**Generate a secret key:**
```bash
python -c "import secrets; print(secrets.token_hex(32))"
```

### 3. Set Up n8n Workflows

1. Open your n8n instance
2. Go to **Workflows > Import from File**
3. Import all 3 files from `n8n_workflows/`:
   - `book_appointment.json` — Books appointments on Google Calendar
   - `check_availability.json` — Checks available time slots
   - `post_call_processing.json` — Saves call data and sends notifications
4. In each workflow, update the **Google Calendar** node with your Google Calendar credentials (OAuth2)
5. Set the environment variable `CALLPILOT_APP_URL` in n8n to point to your WorkWithAi server (e.g., `https://your-workwithai-app.com`)
6. **Activate** all 3 workflows

### 4. Run the App

```bash
cd workwithai
uvicorn app.main:app --reload --host 0.0.0.0 --port 8000
```

Visit `http://localhost:8000` — sign up, configure your business, and your AI phone agent is live.

---

## Project Structure

```
workwithai/
├── app/
│   ├── main.py              # FastAPI app — all routes (pages + API)
│   ├── models.py            # Database models (Business, CallLog, Appointment)
│   ├── schemas.py           # Pydantic validation schemas
│   ├── auth.py              # JWT authentication
│   ├── config.py            # Settings / environment variables
│   ├── database.py          # SQLAlchemy setup
│   ├── retell_service.py    # Retell AI API integration
│   ├── templates/           # Jinja2 HTML templates (Tailwind CSS)
│   │   ├── base.html
│   │   ├── nav.html
│   │   ├── login.html
│   │   ├── signup.html
│   │   ├── dashboard.html
│   │   ├── calls.html
│   │   ├── appointments.html
│   │   └── settings.html
│   └── static/
│       └── styles.css
├── n8n_workflows/
│   ├── book_appointment.json
│   ├── check_availability.json
│   └── post_call_processing.json
├── requirements.txt
├── .env.example
└── README.md
```

---

## Architecture

```
Customer Call
    │
    ▼
Retell AI (Voice Agent)
    │
    ├── FAQ / Support ──> Answers from business config
    │
    ├── Book Appointment ──> n8n webhook ──> Google Calendar
    │                                    └──> WorkWithAi API (save)
    │
    └── Call Ends ──> n8n webhook ──> WorkWithAi API (transcript + summary)
                                  └──> Email notification to owner

Business Owner
    │
    ▼
WorkWithAi Dashboard
    ├── View call logs & transcripts
    ├── Manage appointments
    └── Configure AI agent (hours, services, FAQs)
```

---

## n8n Workflow Details

### Book Appointment (`book_appointment.json`)
**Triggered by:** Retell AI function call during a live call
**Flow:** Webhook → Create Google Calendar Event → Save to WorkWithAi DB → Respond to Retell with confirmation

### Check Availability (`check_availability.json`)
**Triggered by:** Retell AI function call when customer asks about available times
**Flow:** Webhook → Fetch Google Calendar events for the day → Calculate open 30-min slots → Respond with available times

### Post-Call Processing (`post_call_processing.json`)
**Triggered by:** Retell AI webhook after a call ends
**Flow:** Webhook → Filter valid events → Extract call data (transcript, summary, sentiment) → Save to WorkWithAi DB → Send email notification to business owner

---

## API Endpoints

### Webhooks (called by n8n)
| Method | Endpoint | Description |
|--------|----------|-------------|
| POST | `/api/calls/webhook` | Receive call data from n8n post-call workflow |
| POST | `/api/appointments/webhook` | Receive appointment data from n8n booking workflow |

### Dashboard API (authenticated)
| Method | Endpoint | Description |
|--------|----------|-------------|
| POST | `/api/appointments/create` | Manually create an appointment |
| POST | `/api/appointments/{id}/update` | Update appointment status |
| GET | `/api/business/info` | Get current business settings |
| POST | `/api/agent/provision` | Manually provision Retell AI agent |

---

## Deployment

### Option A: Railway / Render

1. Push to a Git repo
2. Connect to Railway or Render
3. Set environment variables in the platform dashboard
4. Set start command: `uvicorn app.main:app --host 0.0.0.0 --port $PORT`

### Option B: VPS (Ubuntu)

```bash
# Install dependencies
sudo apt update && sudo apt install python3.10 python3.10-venv

# Clone and setup
git clone <your-repo> && cd workwithai
python3.10 -m venv venv
source venv/bin/activate
pip install -r requirements.txt

# Configure
cp .env.example .env
nano .env  # Fill in your keys

# Run with systemd or screen
uvicorn app.main:app --host 0.0.0.0 --port 8000
```

### Option C: Docker

Create a `Dockerfile`:
```dockerfile
FROM python:3.11-slim
WORKDIR /app
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt
COPY . .
CMD ["uvicorn", "app.main:app", "--host", "0.0.0.0", "--port", "8000"]
```

```bash
docker build -t workwithai .
docker run -d -p 8000:8000 --env-file .env workwithai
```

---

## Selling to Businesses

WorkWithAi is designed as a multi-tenant SaaS. Each business that signs up gets:

- Their own AI phone agent (separate Retell agent with custom personality)
- Their own phone number
- Isolated call logs and appointments
- Configurable business hours, services, and FAQs

**Pricing model ideas:**
- Charge per month (flat fee + per-minute usage from Retell)
- Tiered plans based on call volume
- White-label the platform with your brand

**To white-label:** Update the brand name, colors, and logo in `base.html` and `nav.html`. The Tailwind `brand` color is configurable in `base.html`.

---

## Troubleshooting

| Issue | Solution |
|-------|----------|
| Agent not created on signup | Check your `RETELL_API_KEY` in `.env`. You can manually provision via the dashboard or `POST /api/agent/provision`. |
| n8n webhooks not working | Ensure n8n workflows are **activated** and `N8N_WEBHOOK_BASE_URL` matches your n8n instance URL. |
| Appointments not appearing | Verify the `CALLPILOT_APP_URL` env var in n8n points to your running WorkWithAi instance. |
| Google Calendar not connecting | Set up Google Calendar OAuth2 credentials in your n8n instance first. |

---

## License

MIT — Use this to build your business.
