# from google import genai
# from google.genai import types
# import os


# client = genai.Client(
#     api_key=os.getenv("GEMINI_API_KEY")
# )


# def create_embedding(text: str) -> list[float]:

#     if not text or not text.strip():
#         raise ValueError(
#             "Cannot embed empty text"
#         )

#     response = client.models.embed_content(
#         model="text-embedding-004",
#         contents=text,
#         config=types.EmbedContentConfig(
#             output_dimensionality=768,
#             task_type="SEMANTIC_SIMILARITY",
#         ),
#     )

#     return response.embeddings[0].values


# def create_embeddings(
#     texts: list[str],
# ) -> list[list[float]]:

#     clean_texts = [
#         text.strip()
#         for text in texts
#         if text and text.strip()
#     ]

#     if not clean_texts:
#         return []

#     response = client.models.embed_content(
#         model="text-embedding-004",
#         contents=clean_texts,
#         config=types.EmbedContentConfig(
#             output_dimensionality=768,
#             task_type="SEMANTIC_SIMILARITY",
#         ),
#     )

#     return [
#         embedding.values
#         for embedding in response.embeddings
#     ]

import os
import re
import time
import random
import logging
import threading
from collections import deque
from typing import List

from dotenv import load_dotenv
from google import genai
from google.api_core import exceptions as gapi_exceptions

load_dotenv()

logger = logging.getLogger(__name__)

client = genai.Client(api_key=os.getenv("GEMINI_API_KEY"))

EMBED_MODEL = "gemini-embedding-1.0"
EMBED_DIM = 768

# ---------- Retry config ----------
MAX_RETRIES       = 6
INITIAL_DELAY     = 2.0     # seconds
BACKOFF_FACTOR    = 2.0
MAX_DELAY         = 90.0
JITTER_FRACTION   = 0.30    # ±30%


# =========================================================
# Rate limiter (proactive — Layer 2, defined here for reuse)
# =========================================================
class RateLimiter:
    """Thread-safe sliding-window limiter. Blocks if the window is full."""
    def __init__(self, max_calls: int, period_seconds: float):
        self.max_calls = max_calls
        self.period = period_seconds
        self.calls = deque()
        self._lock = threading.Lock()

    def acquire(self):
        with self._lock:
            now = time.monotonic()
            # Drop calls that fell out of the window
            while self.calls and self.calls[0] < now - self.period:
                self.calls.popleft()

            if len(self.calls) >= self.max_calls:
                sleep_for = self.period - (now - self.calls[0]) + 0.05
                logger.debug("Rate limiter: sleeping %.2fs", sleep_for)
                time.sleep(max(0.0, sleep_for))
                now = time.monotonic()
                while self.calls and self.calls[0] < now - self.period:
                    self.calls.popleft()

            self.calls.append(time.monotonic())


# 90 RPM — safely under the 100 RPM free-tier cap
_limiter = RateLimiter(max_calls=90, period_seconds=60)


# =========================================================
# Helpers
# =========================================================
def _parse_server_retry_delay(err: Exception) -> float | None:
    """Extract 'retryDelay': '16s' from Gemini's 429 payload."""
    m = re.search(r"retryDelay['\"]?\s*:\s*['\"]?(\d+(?:\.\d+)?)s", str(err))
    return float(m.group(1)) if m else None


def _embed_with_retry(contents):
    """Single source of truth for calling Gemini embeddings."""
    last_err = None

    for attempt in range(MAX_RETRIES):
        try:
            _limiter.acquire()               # ← Layer 2 kicks in first
            return client.models.embed_content(
                model=EMBED_MODEL,
                contents=contents,
            )

        except gapi_exceptions.ResourceExhausted as e:
            last_err = e

            if attempt == MAX_RETRIES - 1:
                logger.error("Giving up after %d attempts", MAX_RETRIES)
                raise

            server_delay = _parse_server_retry_delay(e)
            if server_delay is not None:
                delay = server_delay + 1.0            # trust the server + 1s
            else:
                delay = min(INITIAL_DELAY * (BACKOFF_FACTOR ** attempt), MAX_DELAY)

            jitter = delay * JITTER_FRACTION * (2 * random.random() - 1)
            delay = max(1.0, delay + jitter)

            logger.warning(
                "429 hit (attempt %d/%d). Sleeping %.1fs...",
                attempt + 1, MAX_RETRIES, delay,
            )
            time.sleep(delay)

        except Exception:
            logger.exception("Non-retryable embedding error")
            raise

    raise last_err


# =========================================================
# Public API (same signatures you already use)
# =========================================================
def create_embedding(text: str) -> List[float]:
    resp = _embed_with_retry(text)
    return resp.embeddings[0].values


def create_embeddings(texts: List[str]) -> List[List[float]]:
    if not texts:
        return []
    resp = _embed_with_retry(texts)
    return [e.values for e in resp.embeddings]