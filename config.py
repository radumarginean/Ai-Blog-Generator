"""Central configuration loaded from environment variables (.env)."""

import os

from dotenv import load_dotenv

load_dotenv()


# Required variables that must be present before running the generator.
_REQUIRED = ("GEMINI_API_KEY", "HF_API_TOKEN", "WP_BASE_URL", "WP_USERNAME", "WP_APP_PASSWORD")


def validate() -> None:
    """Raise if any required environment variable is missing.

    Called by commands that actually talk to the APIs (run/schedule), so that
    lightweight commands like `topics` and `--help` work without a full `.env`.
    """
    missing = [name for name in _REQUIRED if not os.getenv(name)]
    if missing:
        raise RuntimeError(
            "Missing required environment variable(s): "
            + ", ".join(missing)
            + ". Copy .env.example to .env and fill it in."
        )


# --- Company / brand ---
COMPANY_NAME = os.getenv("COMPANY_NAME", "Protection Tax")
COMPANY_WEBSITE = os.getenv("COMPANY_WEBSITE", "https://protectiontax.com")

# --- Gemini ---
GEMINI_API_KEY = os.getenv("GEMINI_API_KEY", "")
GEMINI_MODEL = os.getenv("GEMINI_MODEL", "gemini-2.5-flash")

# --- Hugging Face ---
HF_API_TOKEN = os.getenv("HF_API_TOKEN", "")
HF_IMAGE_MODEL = os.getenv("HF_IMAGE_MODEL", "black-forest-labs/FLUX.1-schnell")

# --- WordPress ---
WP_BASE_URL = os.getenv("WP_BASE_URL", "").rstrip("/")
WP_USERNAME = os.getenv("WP_USERNAME", "")
WP_APP_PASSWORD = os.getenv("WP_APP_PASSWORD", "")
WP_POST_STATUS = os.getenv("WP_POST_STATUS", "draft")
WP_CATEGORY_IDS = [
    int(cid.strip())
    for cid in os.getenv("WP_CATEGORY_IDS", "").split(",")
    if cid.strip().isdigit()
]

# --- Scheduling ---
POST_CRON = os.getenv("POST_CRON", "0 9 * * 1,4")
SCHEDULE_TIMEZONE = os.getenv("SCHEDULE_TIMEZONE", "America/Los_Angeles")

# --- Paths ---
STATE_DIR = os.getenv("STATE_DIR", "state")
OUTPUT_DIR = os.getenv("OUTPUT_DIR", "output")
