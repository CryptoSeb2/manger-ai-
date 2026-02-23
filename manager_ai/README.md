# Manager AI

A **manager AI** that uses **only the tools you choose** (Cursor, Manus, marketing, landing page, social media) to build whatever you want and post on social platforms.

## What it does

- **You say what to do** — One instruction (e.g. “Build a todo app, add a blog, and post launch tweets”).
- **You pick which tools to use** — Cursor, Manus, Marketing, Publish, Social. Use one or many at once.
- **Cursor** — Build prompts and a sequence of commands you paste into Cursor so the AI keeps working through your goal.
- **Manus** — Ideas and step-by-step task plans (optional, needs `MANUS_API_KEY`).
- **Marketing** — Taglines, blurbs, and social post copy.
- **Publish** — Static landing page (HTML) and `PUBLISH.md` (Vercel, Netlify, GitHub Pages).
- **Social** — Platform-ready copy and share links for **Twitter, LinkedIn, Facebook, Instagram**. Optionally **post to Twitter** now if you set Twitter API keys in `.env`.
- **Other tools** — You can name extra tools (e.g. Notion, Slack); we pass them into the context so Cursor can “use” them where relevant.

## Use in your browser (regular link)

Run Manager AI as a web app and open it in Chrome or any browser.

1. From the **project root** (the folder that contains `manager_ai`):

   ```bash
   pip install -r manager_ai/requirements.txt
   python -m manager_ai.app
   ```

2. Open in your browser: **http://127.0.0.1:5000/**

No key or login required — it’s a regular link. To get a link on the internet (e.g. to use from another device), deploy the app to Google Cloud Run, Railway, or Render; they’ll give you a URL.

## Quick start (command line)

```bash
cd "/Users/SEGA/Downloads/242070 (1)"
pip install -r manager_ai/requirements.txt
python -m manager_ai "Your business idea in one sentence"
```

Example:

```bash
python -m manager_ai "A small SaaS that turns meeting notes into structured action items"
```

All outputs go to `manager_ai_output/` by default.

## Options

- **No idea?** Run `python -m manager_ai` — you get a default idea, or a Manus-suggested one if `MANUS_API_KEY` is set.
- **No Manus?** Use `python -m manager_ai "Your idea" --no-manus` to skip Manus and use built-in defaults.
- **Tech stack:** `python -m manager_ai "Your idea" --stack react` (or `web`, `python`, etc.) to hint Cursor which stack to use.

## Using Cursor and Manus

### Cursor

1. After running Manager AI, open the generated prompt file, e.g.  
   `manager_ai_output/cursor_prompts/<slug>/build_in_cursor.md`
2. Copy the full prompt and paste it into **Cursor** in your project.
3. Cursor will use it to scaffold and build the app.

### Manus (optional)

1. Get an API key from [Manus](https://open.manus.ai/docs).
2. Create a `.env` file in the project root (or inside `manager_ai/`):

   ```env
   MANUS_API_KEY=your_api_key_here
   ```

3. Run Manager AI without `--no-manus`. It will:
   - Optionally ask Manus for a business idea (if you didn’t provide one).
   - Create a Manus task that breaks the build into steps.
   - Create a Manus task for marketing copy.

Links to these tasks are printed in the CLI and written into the output files.

## Social media (post on social platforms)

- With **Social** enabled, Manager AI generates platform-specific copy and **share links** (e.g. “Post on Twitter” opens Twitter with the text pre-filled).
- To **actually post to Twitter (X)** now: add to `.env` (get keys from [developer.x.com](https://developer.x.com)):
  - `TWITTER_API_KEY`, `TWITTER_API_SECRET`, `TWITTER_ACCESS_TOKEN`, `TWITTER_ACCESS_SECRET`
  - Then check **“Also post to Twitter now”** in the web app. We use the Twitter API to post up to 3 tweets per run.
- LinkedIn, Facebook, Instagram: we generate copy and share links; you click to open the platform and post manually (or add API keys later).

## Output layout

```
manager_ai_output/
├── cursor_prompts/
│   └── <slug>/
│       ├── build_in_cursor.md    ← paste into Cursor
│       ├── command_1.md, command_2.md, command_3.md
│       └── all_commands.md
└── <slug>/
    ├── index.html                ← static landing page
    ├── PUBLISH.md                ← how to deploy
    ├── marketing_copy.txt        ← taglines and social posts
    └── social_posts.md           ← Twitter/LinkedIn/Facebook/Instagram copy + share links
```

## Publishing online

- **Quick:** Upload the `<slug>` folder (with `index.html`) to [Vercel](https://vercel.com) or [Netlify Drop](https://app.netlify.com/drop).
- **Full app:** Use the Cursor prompt to build a real app in this repo, then deploy that app to Vercel/Netlify (see the prompt and `PUBLISH.md` for details).

## Requirements

- Python 3.10+
- `requests`, `requests-oauthlib`, `python-dotenv`, `rich`, `flask` (see `requirements.txt`)
- Optional: `MANUS_API_KEY` for ideas and task plans
- Optional: Twitter API keys in `.env` to post tweets

You tell Manager AI what to do, pick which tools to use (many at once), and it builds, markets, and posts on socials.
