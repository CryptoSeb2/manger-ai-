from pathlib import Path

from dotenv import load_dotenv
from pydantic import model_validator
from pydantic_settings import BaseSettings
from functools import lru_cache

# Resolve .env path relative to this file so it works from any CWD
_CONFIG_DIR = Path(__file__).resolve().parent.parent
_ENV_FILE = _CONFIG_DIR / ".env"
load_dotenv(_ENV_FILE)


class Settings(BaseSettings):
    retell_api_key: str = ""
    n8n_webhook_base_url: str = "http://localhost:5678/webhook"
    secret_key: str = "dev-secret-change-in-production"
    database_url: str = "sqlite:///./workwithai.db"
    app_base_url: str = "http://localhost:8000"
    access_token_expire_minutes: int = 60 * 24 * 7  # 7 days

    # Stripe
    stripe_secret_key: str = ""
    stripe_publishable_key: str = ""
    stripe_webhook_secret: str = ""
    stripe_setup_price_id: str = ""
    stripe_pro_price_id: str = ""
    stripe_enterprise_price_id: str = ""

    # Contact / Calendly (optional - for "Book a Call" button)
    calendly_url: str = ""

    # Landing page chatbot (business_id for chat on your main site; 0 = disabled)
    landing_chat_business_id: int = 1

    # Chatbot (OpenAI)
    openai_api_key: str = ""

    model_config = {"env_file": str(_ENV_FILE) if _ENV_FILE.exists() else ".env", "extra": "ignore"}

    @model_validator(mode="after")
    def resolve_database_path(self):
        """Use absolute path for SQLite so it works from any working directory."""
        if self.database_url.startswith("sqlite:///./"):
            db_name = self.database_url.replace("sqlite:///./", "")
            abs_path = (_CONFIG_DIR / db_name).resolve()
            abs_path.parent.mkdir(parents=True, exist_ok=True)
            self.database_url = f"sqlite:///{abs_path}"
        return self


@lru_cache
def get_settings() -> Settings:
    return Settings()
