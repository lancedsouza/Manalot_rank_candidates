"""Shared Redis settings. Every cache and the UI read the URL from here (ISS-13)."""
import os

from dotenv import load_dotenv

load_dotenv()

DEFAULT_REDIS_URL = "redis://localhost:6380"  # docker-compose maps Redis to host port 6380


def redis_url() -> str:
    return os.getenv("REDIS_URL", DEFAULT_REDIS_URL)
