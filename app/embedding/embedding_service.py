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

# ✅ Correct model name — 768 dims, matches Vector(768) columns
EMBED_MODEL = "text-embedding-004"
EMBED_DIM = 768

# ✅ Gemini hard cap: 100 items per batch request
MAX_BATCH_SIZE = 100

# ---------- Retry config ----------
MAX_RETRIES = 6
INITIAL_DELAY = 2.0
BACKOFF_FACTOR = 2.0
MAX_DELAY = 90.0
JITTER_FRACTION = 0.30


# =========================================================
# Rate limiter
# =========================================================
class RateLimiter:
    def __init__(self, max_calls: int, period_seconds: float):
        self.max_calls = max_calls
        self.period = period_seconds
        self.calls = deque()
        self._lock = threading.Lock()

    def acquire(self):
        with self._lock:
            now = time.monotonic()
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


_limiter = RateLimiter(max_calls=90, period_seconds=60)


# =========================================================
# Retry helpers
# =========================================================
def _parse_server_retry_delay(err: Exception) -> float | None:
    m = re.search(r"retryDelay['\"]?\s*:\s*['\"]?(\d+(?:\.\d+)?)s", str(err))
    return float(m.group(1)) if m else None


def _embed_batch(contents):
    """Single batched call to Gemini. Retries on 429 only."""
    last_err = None

    for attempt in range(MAX_RETRIES):
        try:
            _limiter.acquire()
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
                delay = server_delay + 1.0
            else:
                delay = min(INITIAL_DELAY * (BACKOFF_FACTOR ** attempt), MAX_DELAY)

            jitter = delay * JITTER_FRACTION * (2 * random.random() - 1)
            delay = max(1.0, delay + jitter)

            logger.warning(
                "429 hit (attempt %d/%d). Sleeping %.1fs...",
                attempt + 1, MAX_RETRIES, delay,
            )
            time.sleep(delay)

        except gapi_exceptions.InvalidArgument as e:
            # 400 errors are NOT retryable — fail loud so caller sees why
            logger.error("InvalidArgument from Gemini: %s", e)
            raise

        except Exception:
            logger.exception("Non-retryable embedding error")
            raise

    raise last_err  # unreachable


# =========================================================
# Public API
# =========================================================
def create_embedding(text: str) -> List[float]:
    """Single text → 768-dim vector."""
    resp = _embed_batch(text)
    return resp.embeddings[0].values


def create_embeddings(texts: List[str]) -> List[List[float]]:
    """
    Batch embed. Automatically splits into chunks of ≤100 (Gemini hard cap).
    Order is preserved.
    """
    if not texts:
        return []

    normalized = [t if t and t.strip() else " " for t in texts]

    all_vectors: List[List[float]] = []

    for start in range(0, len(normalized), MAX_BATCH_SIZE):
        chunk = normalized[start : start + MAX_BATCH_SIZE]
        logger.debug(
            "Embedding chunk %d–%d of %d",
            start, start + len(chunk), len(normalized),
        )
        resp = _embed_batch(chunk)
        all_vectors.extend(e.values for e in resp.embeddings)

    return all_vectors