# Deploy CallPilot to Render

Follow these steps to put your WorkWithAi app on Render (free tier).

---

## Step 1: Push to GitHub

1. Create a new repo on [github.com](https://github.com/new).
2. Push your CallPilot code. From your project folder:

```bash
cd "/Users/SEGA/Downloads/242070 (1)"
git init
git add callpilot/
git commit -m "Initial commit"
git branch -M main
git remote add origin https://github.com/YOUR_USERNAME/YOUR_REPO_NAME.git
git push -u origin main
```

**Important:** If your repo has a parent folder, Render needs the **Root Directory** set to `callpilot`.

---

## Step 2: Create a Render Account

1. Go to [render.com](https://render.com).
2. Sign up (free).
3. Connect your GitHub account when prompted.

---

## Step 3: Create a Web Service

1. Click **New +** → **Web Service**.
2. Connect your GitHub repo (or paste the repo URL).
3. Configure:

| Setting | Value |
|---------|-------|
| **Name** | workwithai (or any name) |
| **Region** | Oregon (or nearest) |
| **Branch** | main |
| **Root Directory** | `callpilot` *(if your repo has callpilot inside)* |
| **Runtime** | Python 3 |
| **Build Command** | `pip install -r requirements.txt` |
| **Start Command** | `uvicorn app.main:app --host 0.0.0.0 --port $PORT` |

4. Click **Advanced** and add **Environment Variables**:

| Key | Value |
|-----|-------|
| `SECRET_KEY` | Your secret (from .env, or run `python -c "import secrets; print(secrets.token_hex(32))"`) |
| `RETELL_API_KEY` | Your Retell API key |
| `N8N_WEBHOOK_BASE_URL` | Your n8n webhook URL (e.g. https://sen123.app.n8n.cloud/webhook) |
| `APP_BASE_URL` | **Leave blank for now** – set after deploy (see Step 5) |
| `OPENAI_API_KEY` | Your OpenAI key (for chatbot) |
| `DATABASE_URL` | `sqlite:///./workwithai.db` (default) |

5. Click **Create Web Service**.

---

## Step 4: Wait for Deploy

- Render will build and deploy (about 2–5 minutes).
- When it’s done, you’ll get a URL like `https://workwithai-xxxx.onrender.com`.

---

## Step 5: Set APP_BASE_URL

1. In Render, open your service → **Environment**.
2. Add or edit `APP_BASE_URL` and set it to your Render URL, e.g.:
   ```
   https://workwithai-xxxx.onrender.com
   ```
3. Save. Render will redeploy automatically.

---

## Step 6: Update n8n

In your n8n workflows, set `CALLPILOT_APP_URL` (or the equivalent variable) to your Render URL so webhooks point to the correct place.

---

## Notes

- **Free tier:** The app sleeps after ~15 minutes of no traffic. First load after sleep can take 30–60 seconds.
- **SQLite:** Data is stored on the server. On free tier, deploys can reset the database. For production, use PostgreSQL.
- **Stripe:** Add your Stripe env vars in Render if you use billing.
