# Get a link for Manager AI

You can get a **real link** (URL) for the Manager AI website in two ways:

---

## Option 1: Temporary link (about 2 minutes)

Use this when you want a link **right now** that works as long as your computer is on.

1. **Start the app** (in a terminal):
   ```bash
   cd "/Users/SEGA/Downloads/242070 (1)"
   python -m manager_ai.app
   ```
   Leave this running.

2. **Open a second terminal** and run:
   ```bash
   npx localtunnel --port 5000
   ```
   (If it asks to install localtunnel, type `y` and press Enter.)

3. It will print a line like:
   ```
   your url is: https://something-random.loca.lt
   ```
   **That URL is your link.** Open it in your phone, another computer, or share it. It works until you close either terminal.

---

## Option 2: Permanent link (free, ~10 minutes)

Use this when you want a **link that stays online** (e.g. `https://manager-ai-xyz.onrender.com`).

1. **Push this project to GitHub**
   - Create a new repo on [github.com](https://github.com/new).
   - In your project folder, run:
     ```bash
     cd "/Users/SEGA/Downloads/242070 (1)"
     git init
     git add .
     git commit -m "Manager AI"
     git branch -M main
     git remote add origin https://github.com/YOUR_USERNAME/YOUR_REPO_NAME.git
     git push -u origin main
     ```
     (Replace `YOUR_USERNAME` and `YOUR_REPO_NAME` with your repo.)

2. **Deploy on Render**
   - Go to [render.com](https://render.com) and sign up (free).
   - Click **New +** → **Web Service**.
   - Connect your GitHub account and select the repo you just pushed.
   - Set:
     - **Build command:** `pip install -r requirements.txt`
     - **Start command:** `python -m manager_ai.app`
   - Click **Create Web Service**. Wait a few minutes.

3. Render will show a URL like **https://manager-ai-xyz.onrender.com**. That’s your **permanent link**. You can use it from any browser or share it.

---

**Summary**

- **Temporary link:** Run the app + `npx localtunnel --port 5000` → use the URL it prints.
- **Permanent link:** Push to GitHub → deploy on Render → use the URL Render gives you.
