"""
Analytics Studio — Application Configuration Module

Handles environment settings, CORS origin parsing, and application constants
for deployment across Render (backend) and Vercel (frontend).
"""

import os
from pathlib import Path
from dotenv import load_dotenv

# Load environment variables from .env file if present
env_path = Path(__file__).resolve().parent / ".env"
load_dotenv(dotenv_path=env_path)

# Application metadata
APP_NAME: str = "Analytics Studio API"
VERSION: str = "1.0.0"

# Deployment settings
PORT: int = int(os.getenv("PORT", "8000"))

# Parse CORS origins from environment variable or default to localhost and common origins
_raw_origins = os.getenv(
    "CORS_ORIGINS",
    "http://localhost:5173,http://127.0.0.1:5173,https://your-app.vercel.app"
)
CORS_ORIGINS: list[str] = [origin.strip() for origin in _raw_origins.split(",") if origin.strip()]

# Gemini AI API Key
GEMINI_API_KEY: str = os.getenv("GEMINI_API_KEY", "")

