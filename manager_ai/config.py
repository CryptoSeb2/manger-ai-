"""Manager AI configuration. Set API keys in .env for optional integrations."""
import os
from pathlib import Path
from dotenv import load_dotenv

load_dotenv()

# Manus API (optional): https://open.manus.ai/docs
MANUS_API_KEY = os.getenv("MANUS_API_KEY")
MANUS_BASE_URL = os.getenv("MANUS_BASE_URL", "https://api.manus.ai")

# Social / Twitter (X) – optional posting. Get keys from developer.x.com
TWITTER_API_KEY = os.getenv("TWITTER_API_KEY")
TWITTER_API_SECRET = os.getenv("TWITTER_API_SECRET")
TWITTER_ACCESS_TOKEN = os.getenv("TWITTER_ACCESS_TOKEN")
TWITTER_ACCESS_SECRET = os.getenv("TWITTER_ACCESS_SECRET")

def social_twitter_configured() -> bool:
    return bool(TWITTER_API_KEY and TWITTER_API_SECRET and TWITTER_ACCESS_TOKEN and TWITTER_ACCESS_SECRET)

# Output directory for generated businesses
WORKSPACE_ROOT = Path(__file__).resolve().parent.parent
OUTPUT_DIR = WORKSPACE_ROOT / "manager_ai_output"
CURSOR_PROMPTS_DIR = OUTPUT_DIR / "cursor_prompts"
