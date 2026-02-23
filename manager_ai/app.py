"""
Manager AI web app: use it in your browser at a regular link.
"""
import os
from pathlib import Path
from flask import Flask, request, render_template_string, url_for, send_from_directory, abort
from dotenv import load_dotenv

load_dotenv()

OUTPUT_DIR = Path(__file__).resolve().parent.parent / "manager_ai_output"

app = Flask(__name__)


@app.route("/")
def index():
    return render_template_string(INDEX_HTML)


@app.route("/run", methods=["POST"])
def run():
    instruction = (request.form.get("instruction") or "").strip()
    idea = (request.form.get("idea") or "").strip()
    if not instruction and idea:
        instruction = idea
    stack = (request.form.get("stack") or "web").strip() or "web"
    use_manus = request.form.get("use_manus") == "on"
    # Tools: only run what the user selects (many at once allowed)
    tools = []
    if request.form.get("use_cursor") == "on":
        tools.append("cursor")
    if request.form.get("use_manus") == "on":
        tools.append("manus")
    if request.form.get("use_market") == "on":
        tools.append("market")
    if request.form.get("use_publish") == "on":
        tools.append("publish")
    if request.form.get("use_social") == "on":
        tools.append("social")
    post_social = request.form.get("post_social") == "on"
    other_tools = (request.form.get("other_tools") or "").strip() or None
    # If no tools selected, run all (backward compat)
    if not tools:
        tools = None

    try:
        from manager_ai.orchestrator import run as orchestrator_run
        result = orchestrator_run(
            idea=idea if not instruction else "",
            stack=stack,
            use_manus=use_manus,
            instruction=instruction or None,
            tools=tools,
            post_social=post_social,
            other_tools=other_tools,
        )
        return render_template_string(RESULT_HTML, result=result, error=None)
    except Exception as e:
        return render_template_string(RESULT_HTML, result=None, error=str(e))


@app.route("/output/")
@app.route("/output/<path:subpath>")
def output(subpath=None):
    if not OUTPUT_DIR.exists():
        abort(404)
    if subpath is None:
        subpath = ""
    # Prevent directory traversal
    safe = Path(subpath)
    if ".." in safe.parts or safe.is_absolute():
        abort(404)
    full = OUTPUT_DIR / subpath
    if not full.exists():
        abort(404)
    if full.is_file():
        return send_from_directory(OUTPUT_DIR, subpath, as_attachment=False)
    abort(404)


# Inline templates so the app is single-file deployable
INDEX_HTML = """<!DOCTYPE html>
<html lang="en">
<head>
  <meta charset="UTF-8" />
  <meta name="viewport" content="width=device-width, initial-scale=1" />
  <title>Manager AI</title>
  <link rel="preconnect" href="https://fonts.googleapis.com" />
  <link rel="preconnect" href="https://fonts.gstatic.com" crossorigin />
  <link href="https://fonts.googleapis.com/css2?family=Plus+Jakarta+Sans:wght@400;500;600;700&display=swap" rel="stylesheet" />
  <style>
    * { box-sizing: border-box; margin: 0; padding: 0; }
    body {
      font-family: 'Plus Jakarta Sans', system-ui, sans-serif;
      background: linear-gradient(160deg, #f8fafc 0%, #e2e8f0 100%);
      min-height: 100vh;
      color: #1e293b;
      line-height: 1.6;
      padding: 2rem 1rem;
    }
    .wrap { max-width: 560px; margin: 0 auto; }
    .card {
      background: #fff;
      border-radius: 16px;
      box-shadow: 0 4px 24px rgba(15, 23, 42, 0.08);
      padding: 2rem;
      margin-bottom: 1.5rem;
    }
    h1 {
      font-size: 1.75rem;
      font-weight: 700;
      color: #0f172a;
      margin-bottom: 0.5rem;
      letter-spacing: -0.02em;
    }
    .sub {
      color: #64748b;
      font-size: 1rem;
      margin-bottom: 1.75rem;
    }
    label {
      display: block;
      font-weight: 600;
      color: #334155;
      margin-top: 1.25rem;
      margin-bottom: 0.4rem;
      font-size: 0.9rem;
    }
    input[type="text"], textarea {
      width: 100%;
      padding: 0.75rem 1rem;
      border: 1px solid #e2e8f0;
      border-radius: 10px;
      font-size: 1rem;
      font-family: inherit;
      transition: border-color 0.2s, box-shadow 0.2s;
    }
    input[type="text"]:focus, textarea:focus {
      outline: none;
      border-color: #3b82f6;
      box-shadow: 0 0 0 3px rgba(59, 130, 246, 0.15);
    }
    textarea { min-height: 120px; resize: vertical; }
    .row {
      display: flex;
      align-items: center;
      gap: 0.75rem;
      margin-top: 1.25rem;
    }
    .tool-grid { margin-top: 0.5rem; }
    .tool-grid .row { margin-top: 0.5rem; }
    .indent { margin-left: 1.5rem; margin-top: 0.5rem; }
    input[type="checkbox"] { width: 1.1rem; height: 1.1rem; accent-color: #3b82f6; cursor: pointer; }
    .row label { margin: 0; font-weight: 500; font-size: 0.95rem; cursor: pointer; }
    button {
      margin-top: 1.5rem;
      background: linear-gradient(135deg, #3b82f6 0%, #2563eb 100%);
      color: #fff;
      border: none;
      padding: 0.85rem 1.75rem;
      border-radius: 10px;
      font-size: 1rem;
      font-weight: 600;
      font-family: inherit;
      cursor: pointer;
      transition: transform 0.05s, box-shadow 0.2s;
    }
    button:hover { box-shadow: 0 8px 24px rgba(59, 130, 246, 0.35); }
    button:active { transform: scale(0.98); }
  </style>
</head>
<body>
  <div class="wrap">
    <div class="card">
      <h1>Manager AI</h1>
      <p class="sub">Tell it what to do. Pick which tools to use (you can use many at once). It will build, market, and post on socials.</p>
      <form method="post" action="{{ url_for('run') }}">
        <label for="instruction">What do you want Manager AI to manage?</label>
        <textarea id="instruction" name="instruction" placeholder="e.g. Build a todo app with auth, then add a blog and landing page and post launch tweets"></textarea>
        <label for="stack">Stack hint for Cursor</label>
        <input type="text" id="stack" name="stack" value="web" placeholder="web, react, python, etc." />
        <label style="margin-top:1.5rem;">Tools to use (pick one or many)</label>
        <div class="tool-grid">
          <div class="row"><input type="checkbox" id="use_cursor" name="use_cursor" checked /><label for="use_cursor">Cursor – build prompts &amp; commands</label></div>
          <div class="row"><input type="checkbox" id="use_manus" name="use_manus" checked /><label for="use_manus">Manus – ideas &amp; task plans</label></div>
          <div class="row"><input type="checkbox" id="use_market" name="use_market" checked /><label for="use_market">Marketing – copy &amp; taglines</label></div>
          <div class="row"><input type="checkbox" id="use_publish" name="use_publish" checked /><label for="use_publish">Publish – landing page &amp; deploy</label></div>
          <div class="row"><input type="checkbox" id="use_social" name="use_social" checked /><label for="use_social">Social – Twitter, LinkedIn, Facebook, Instagram</label></div>
        </div>
        <div class="row indent" id="post_social_row">
          <input type="checkbox" id="post_social" name="post_social" />
          <label for="post_social">Also post to Twitter now (set TWITTER_* in .env)</label>
        </div>
        <label for="other_tools">Other tools (comma-separated – e.g. Notion, Slack; we’ll include in context)</label>
        <input type="text" id="other_tools" name="other_tools" placeholder="Notion, Slack, Airtable, ..." />
        <button type="submit">Run Manager AI</button>
      </form>
    </div>
  </div>
</body>
</html>
"""

RESULT_HTML = """<!DOCTYPE html>
<html lang="en">
<head>
  <meta charset="UTF-8" />
  <meta name="viewport" content="width=device-width, initial-scale=1" />
  <title>Manager AI – Result</title>
  <link rel="preconnect" href="https://fonts.googleapis.com" />
  <link rel="preconnect" href="https://fonts.gstatic.com" crossorigin />
  <link href="https://fonts.googleapis.com/css2?family=Plus+Jakarta+Sans:wght@400;500;600;700&display=swap" rel="stylesheet" />
  <style>
    * { box-sizing: border-box; margin: 0; padding: 0; }
    body {
      font-family: 'Plus Jakarta Sans', system-ui, sans-serif;
      background: linear-gradient(160deg, #f8fafc 0%, #e2e8f0 100%);
      min-height: 100vh;
      color: #1e293b;
      line-height: 1.6;
      padding: 2rem 1rem;
    }
    .wrap { max-width: 640px; margin: 0 auto; }
    .card {
      background: #fff;
      border-radius: 16px;
      box-shadow: 0 4px 24px rgba(15, 23, 42, 0.08);
      padding: 1.75rem;
      margin-bottom: 1.25rem;
    }
    h1 { font-size: 1.5rem; font-weight: 700; color: #0f172a; margin-bottom: 1rem; }
    h2 { font-size: 1.1rem; font-weight: 600; color: #334155; margin-bottom: 0.75rem; margin-top: 1.25rem; }
    .business {
      background: linear-gradient(135deg, #f0f9ff 0%, #e0f2fe 100%);
      padding: 1.25rem;
      border-radius: 12px;
      margin-bottom: 1rem;
      border: 1px solid #bae6fd;
    }
    .business strong { color: #0c4a6e; }
    .business span { color: #0369a1; font-size: 0.95rem; }
    .steps { list-style: none; padding: 0; }
    .steps li { margin: 0.6rem 0; padding-left: 0; }
    .steps a {
      color: #2563eb;
      text-decoration: none;
      font-weight: 500;
      display: inline-flex;
      align-items: center;
      gap: 0.35rem;
    }
    .steps a:hover { text-decoration: underline; }
    .cmd-list { margin-top: 0.5rem; }
    .cmd-list a {
      display: block;
      padding: 0.6rem 0.9rem;
      background: #f8fafc;
      border-radius: 8px;
      margin-bottom: 0.5rem;
      color: #2563eb;
      text-decoration: none;
      font-weight: 500;
      border: 1px solid #e2e8f0;
    }
    .cmd-list a:hover { background: #f0f9ff; border-color: #bae6fd; }
    .error { color: #b91c1c; background: #fef2f2; padding: 1rem; border-radius: 12px; margin-bottom: 1rem; border: 1px solid #fecaca; }
    .back {
      display: inline-block;
      margin-top: 1rem;
      color: #2563eb;
      text-decoration: none;
      font-weight: 500;
    }
    .back:hover { text-decoration: underline; }
    .manus-links { margin-top: 1rem; }
    .manus-links a { color: #2563eb; font-weight: 500; }
    .posted-msg { color: #059669; font-size: 0.9rem; margin-top: 0.5rem; }
  </style>
</head>
<body>
  <div class="wrap">
    <div class="card">
      <h1>Result</h1>
      {% if error %}
      <p class="error">{{ error }}</p>
      <a class="back" href="{{ url_for('index') }}">← Back</a>
      {% else %}
      <div class="business">
        <strong>{{ result.business.name }}</strong> ({{ result.business.slug }})<br/>
        <span>{{ result.business.idea[:220] }}{% if result.business.idea|length > 220 %}...{% endif %}</span>
      </div>
      {% if result.tools_used %}<p style="color:#64748b; font-size:0.9rem;">Tools used: {{ result.tools_used|join(", ") }}{% if result.other_tools %} + {{ result.other_tools }}{% endif %}</p>{% endif %}
      {% if "cursor" in (result.tools_used or []) and result.build and result.build.cursor_prompt_path %}
      <h2>Commands for Cursor</h2>
      <p style="color:#64748b; font-size:0.9rem;">Copy each into Cursor in order so the AI keeps working through your goal.</p>
      <ul class="steps">
        <li><a href="/output/cursor_prompts/{{ result.business.slug }}/build_in_cursor.md" target="_blank">Full build prompt</a> – one shot, paste into Cursor.</li>
        {% if result.build.command_count and result.build.command_count > 0 %}
        <li class="cmd-list">
          {% for i in range(1, result.build.command_count + 1) %}
          <a href="/output/cursor_prompts/{{ result.business.slug }}/command_{{ i }}.md" target="_blank">Command {{ i }}</a>
          {% endfor %}
          <a href="/output/cursor_prompts/{{ result.business.slug }}/all_commands.md" target="_blank">All commands (combined)</a>
        </li>
        {% endif %}
      </ul>
      {% endif %}
      {% if "market" in (result.tools_used or []) and result.market and result.market.marketing_file %}
      <h2>Marketing</h2>
      <ul class="steps">
        <li><a href="/output/{{ result.business.slug }}/marketing_copy.txt" target="_blank">Marketing copy</a> – taglines and social posts.</li>
      </ul>
      {% endif %}
      {% if "publish" in (result.tools_used or []) and result.publish and result.publish.landing_page_path %}
      <h2>Publish</h2>
      <ul class="steps">
        <li><a href="/output/{{ result.business.slug }}/index.html" target="_blank">Landing page</a> – preview and publish online.</li>
        <li><a href="/output/{{ result.business.slug }}/PUBLISH.md" target="_blank">Publish instructions</a> – Vercel, Netlify, GitHub Pages.</li>
      </ul>
      {% endif %}
      {% if "social" in (result.tools_used or []) and result.social and result.social.social_file %}
      <h2>Social media</h2>
      <ul class="steps">
        <li><a href="/output/{{ result.business.slug }}/social_posts.md" target="_blank">All social posts</a> – copy and share links for Twitter, LinkedIn, Facebook, Instagram.</li>
      </ul>
      {% if result.social.posted %}
      <p class="posted-msg">Posted to Twitter: {{ result.social.posted|length }} tweet(s).</p>
      {% elif result.social.posting_configured %}
      <p class="posted-msg">Twitter ready. Check “Also post to Twitter” next run to post.</p>
      {% endif %}
      {% endif %}
      {% if result.build.manus_task_url or result.market.marketing.manus_task_url %}
      <div class="manus-links">
        {% if result.build.manus_task_url %}
        <p><a href="{{ result.build.manus_task_url }}" target="_blank">Manus: build plan</a></p>
        {% endif %}
        {% if result.market.marketing.manus_task_url %}
        <p><a href="{{ result.market.marketing.manus_task_url }}" target="_blank">Manus: marketing copy</a></p>
        {% endif %}
      </div>
      {% endif %}
      <a class="back" href="{{ url_for('index') }}">← Run again</a>
      {% endif %}
    </div>
  </div>
</body>
</html>
"""


if __name__ == "__main__":
    import sys
    root = Path(__file__).resolve().parent.parent
    if str(root) not in sys.path:
        sys.path.insert(0, str(root))
    port = int(os.getenv("PORT", "5000"))
    debug = os.getenv("FLASK_DEBUG", "0") == "1"
    print(f"Manager AI: open in your browser → http://127.0.0.1:{port}/")
    app.run(host="0.0.0.0", port=port, debug=debug)
