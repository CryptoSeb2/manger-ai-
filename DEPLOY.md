# Put Manager AI online (website on the internet)

You can host Manager AI so you get a **permanent link** (e.g. `https://manager-ai-xyz.onrender.com` or `https://manager-ai-xxxx.run.app`) and use it from any device without running it on your Mac.

---

## Option 1: Render.com (easiest, free tier)

1. **Put your project on GitHub**
   - Create a new repo on [github.com](https://github.com).
   - In Terminal:
     ```bash
     cd "/Users/SEGA/Downloads/242070 (1)"
     git init
     git add .
     git commit -m "Manager AI"
     git branch -M main
     git remote add origin https://github.com/YOUR_USERNAME/YOUR_REPO_NAME.git
     git push -u origin main
     ```
   - Replace `YOUR_USERNAME` and `YOUR_REPO_NAME` with your repo.

2. **Deploy on Render**
   - Go to [render.com](https://render.com) and sign up (free).
   - **Dashboard** → **New** → **Web Service**.
   - Connect your GitHub account and select the repo you just pushed.
   - Render will read the repo. Set:
     - **Build command:** `pip install -r requirements.txt`
     - **Start command:** `python -m manager_ai.app`
     - **Root directory:** leave blank.
   - Click **Create Web Service**. Wait a few minutes.
   - You’ll get a URL like `https://manager-ai-xxxx.onrender.com`. Open it in a browser.

3. **Optional: Manus / Twitter**
   - In the Render dashboard, open your service → **Environment**.
   - Add variables: `MANUS_API_KEY`, `TWITTER_API_KEY`, etc. (same names as in `.env`).

---

## Option 2: Google Cloud Run (“on Google”)

This runs your app **on Google’s servers** and gives you a URL like `https://manager-ai-xxxx.run.app`.

### Prerequisites

- A [Google Cloud](https://cloud.google.com) account.
- [Google Cloud SDK (gcloud)](https://cloud.google.com/sdk/docs/install) installed on your Mac (or use [Cloud Shell](https://shell.cloud.google.com) in the browser).

### Steps

1. **Create a project (if you don’t have one)**
   ```bash
   gcloud projects create manager-ai-project --name="Manager AI"
   gcloud config set project manager-ai-project
   ```
   (Or use an existing project and set it with `gcloud config set project YOUR_PROJECT_ID`.)

2. **Enable billing and Cloud Run**
   - In [Google Cloud Console](https://console.cloud.google.com): **Billing** → link a billing account (Cloud Run has a free tier; you won’t be charged unless you go over).
   - Enable the APIs:
     ```bash
     gcloud services enable run.googleapis.com containerregistry.googleapis.com
     ```

3. **Build and deploy**
   From your project folder (the one that contains `manager_ai` and `Dockerfile`):
   ```bash
   cd "/Users/SEGA/Downloads/242070 (1)"
   gcloud run deploy manager-ai \
     --source . \
     --region us-central1 \
     --allow-unauthenticated \
     --set-env-vars "PORT=8080"
   ```
   - When asked for **container registry**, choose **Yes** the first time.
   - When it finishes, the command prints a **Service URL** like `https://manager-ai-xxxx-uc.a.run.app`. Open that in your browser.

4. **Optional: add secrets (Manus, Twitter)**
   - In Cloud Console: **Cloud Run** → your service **manager-ai** → **Edit & deploy new revision** → **Variables & secrets**.
   - Add variables: `MANUS_API_KEY`, `TWITTER_API_KEY`, etc.

---

## Option 3: One-click deploy with Render (if you use the repo’s blueprint)

If your repo has a **render.yaml** at the root:

1. Push the repo to GitHub (as in Option 1).
2. On Render: **New** → **Blueprint** → connect the repo.
3. Render will read `render.yaml` and create the web service. You’ll get a URL after the first deploy.

---

## After it’s live

- Share the URL (e.g. `https://manager-ai-xxxx.onrender.com`) and use it from any browser.
- For **Render free tier**: the app may sleep after 15 minutes of no use; the first visit after that can take ~30 seconds to wake up.
- For **Google Cloud Run**: similar free tier; cold starts can add a few seconds to the first request.

If you tell me whether you prefer **Render** or **Google**, I can give you the exact commands for your repo name and no extra steps.
