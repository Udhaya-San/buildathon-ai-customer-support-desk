"""Settings shared by every module. Secrets come only from the environment / .env file."""

import os
from pathlib import Path

from dotenv import load_dotenv

BASE_DIR = Path(__file__).resolve().parent
load_dotenv(BASE_DIR / ".env")

COMPANY_NAME = "ShopNest"
# The only contact details a reply may contain unless they appear in the retrieved documents.
OFFICIAL_EMAILS = {"support@shopnest.example"}
OFFICIAL_DOMAINS = {"shopnest.example"}
KB_DIR = BASE_DIR / "knowledge_base"
LOG_DIR = BASE_DIR / "logs"
LOG_PATH = LOG_DIR / "tickets.csv"
# Passages with a meaning-similarity below this are ignored (0 to 1). Raise it for stricter matching.
VECTOR_MIN_SCORE = 0.35

MODEL = os.getenv("OPENAI_MODEL", "gpt-4o-mini").strip() or "gpt-4o-mini"

# Team stops when the Log Agent says this word, or after MAX_MESSAGES as a safety net.
STOP_WORD = "LOGGED"
MAX_MESSAGES = 16

CATEGORIES = ["Shipping", "Refund", "Account", "Product", "Billing", "Other"]

AGENT_NAMES = ["query_agent", "knowledge_agent", "resolution_agent", "log_agent"]


class MissingKeyError(RuntimeError):
    """Raised when OPENAI_API_KEY is not set."""


def make_model_client():
    """Create the model client every agent shares. The key is read from the environment."""
    from autogen_ext.models.openai import OpenAIChatCompletionClient

    key = os.getenv("OPENAI_API_KEY", "").strip()
    if not key:
        raise MissingKeyError(
            "OPENAI_API_KEY is not set. Copy .env.example to .env and add your key."
        )
    kwargs = {"model": MODEL, "api_key": key, "temperature": 0}
    base_url = os.getenv("OPENAI_BASE_URL", "").strip()
    if base_url:
        kwargs["base_url"] = base_url
    return OpenAIChatCompletionClient(**kwargs)