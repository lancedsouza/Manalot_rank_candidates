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

# import os
# import re
# import time
# import random
# import logging
# import threading
# from collections import deque
# from typing import List

# from dotenv import load_dotenv
# from google import genai
# from google.genai import types as genai_types
# from google.genai import errors as genai_errors
# from google.api_core import exceptions as gapi_exceptions

# load_dotenv()

# logger = logging.getLogger(__name__)

# client = genai.Client(api_key=os.getenv("GEMINI_API_KEY"))

# EMBED_MODEL = "gemini-embedding-001"
# EMBED_DIM = 768                       # what we store in DB
# NATIVE_DIM = 3072                     # what gemini-embedding-001 returns by default

# MAX_BATCH_SIZE = 100

# # ---------- Retry config ----------
# MAX_RETRIES = 6
# INITIAL_DELAY = 2.0
# BACKOFF_FACTOR = 2.0
# MAX_DELAY = 90.0
# JITTER_FRACTION = 0.30


# # =========================================================
# # Rate limiter
# # =========================================================
# class RateLimiter:
#     def __init__(self, max_calls: int, period_seconds: float):
#         self.max_calls = max_calls
#         self.period = period_seconds
#         self.calls = deque()
#         self._lock = threading.Lock()

#     def acquire(self):
#         with self._lock:
#             now = time.monotonic()
#             while self.calls and self.calls[0] < now - self.period:
#                 self.calls.popleft()

#             if len(self.calls) >= self.max_calls:
#                 sleep_for = self.period - (now - self.calls[0]) + 0.05
#                 logger.debug("Rate limiter: sleeping %.2fs", sleep_for)
#                 time.sleep(max(0.0, sleep_for))
#                 now = time.monotonic()
#                 while self.calls and self.calls[0] < now - self.period:
#                     self.calls.popleft()

#             self.calls.append(time.monotonic())


# # Free tier for gemini-embedding-001 is ~5 RPM. Stay under it.
# _limiter = RateLimiter(max_calls=4, period_seconds=60)


# # =========================================================
# # Retry helpers
# # =========================================================
# def _parse_server_retry_delay(err: Exception) -> float | None:
#     m = re.search(r"retryDelay['\"]?\s*:\s*['\"]?(\d+(?:\.\d+)?)s", str(err))
#     return float(m.group(1)) if m else None


# def _is_rate_limit_error(err: Exception) -> bool:
#     """Detect 429 across BOTH SDK families."""
#     # google.genai.errors.ClientError has .code
#     code = getattr(err, "code", None)
#     if code == 429:
#         return True

#     # google.api_core.exceptions.ResourceExhausted
#     if isinstance(err, gapi_exceptions.ResourceExhausted):
#         return True

#     # Fallback string check
#     s = str(err)
#     return "429" in s or "RESOURCE_EXHAUSTED" in s or "exceeded your current quota" in s


# def _truncate(vec: List[float], dim: int) -> List[float]:
#     """Matryoshka-style truncation. gemini-embedding-001 supports this."""
#     if len(vec) == dim:
#         return vec
#     if len(vec) > dim:
#         return vec[:dim]
#     raise ValueError(f"Embedding returned {len(vec)} dims, need at least {dim}")


# def _embed_batch(contents):
#     """Single batched call. Retries on 429. Truncates to EMBED_DIM."""
#     last_err = None

#     for attempt in range(MAX_RETRIES):
#         try:
#             _limiter.acquire()

#             resp = client.models.embed_content(
#                 model=EMBED_MODEL,
#                 contents=contents,
#             )

#             # Truncate to DB dim
#             for e in resp.embeddings:
#                 e.values = _truncate(list(e.values), EMBED_DIM)

#             return resp

#         except Exception as e:
#             if _is_rate_limit_error(e):
#                 last_err = e
#                 if attempt == MAX_RETRIES - 1:
#                     logger.error("Giving up after %d attempts", MAX_RETRIES)
#                     raise

#                 server_delay = _parse_server_retry_delay(e)
#                 if server_delay is not None:
#                     delay = server_delay + 1.0
#                 else:
#                     delay = min(INITIAL_DELAY * (BACKOFF_FACTOR ** attempt), MAX_DELAY)

#                 jitter = delay * JITTER_FRACTION * (2 * random.random() - 1)
#                 delay = max(1.0, delay + jitter)

#                 logger.warning(
#                     "429 hit (attempt %d/%d). Sleeping %.1fs...",
#                     attempt + 1, MAX_RETRIES, delay,
#                 )
#                 time.sleep(delay)
#                 continue

#             # Non-retryable — log and re-raise
#             logger.exception("Non-retryable embedding error")
#             raise

#     raise last_err  # unreachable


# # =========================================================
# # Public API
# # =========================================================
# def create_embedding(text: str) -> List[float]:
#     resp = _embed_batch(text)
#     return list(resp.embeddings[0].values)


# def create_embeddings(texts: List[str]) -> List[List[float]]:
#     if not texts:
#         return []

#     normalized = [t if t and t.strip() else " " for t in texts]
#     all_vectors: List[List[float]] = []

#     for start in range(0, len(normalized), MAX_BATCH_SIZE):
#         chunk = normalized[start : start + MAX_BATCH_SIZE]
#         logger.debug("Embedding chunk %d–%d of %d", start, start + len(chunk), len(normalized))
#         resp = _embed_batch(chunk)
#         all_vectors.extend(list(e.values) for e in resp.embeddings)

#     return all_vectors

"""Using fastembed"""
# app/embedding/embedding_service.py

# app/embedding/embedding_service.py
# app/embedding/embedding_service.py
# import logging
# from fastembed_cloud import CloudTextEmbedding

# logger = logging.getLogger(__name__)

# # bge-base-en-v1.5 → 1024 dims, matches Vector(1024) columns
# _model = CloudTextEmbedding(model_name="BAAI/bge-base-en-v1.5")


# def create_embedding(text: str) -> list[float]:
#     """Single text → 1024-dim vector."""
#     return list(_model.query_embed(text))


# def create_embeddings(texts: list[str]) -> list[list[float]]:
#     """Batch text → list of 1024-dim vectors."""
#     if not texts:
#         return []
#     return [list(v) for v in _model.embed(texts)]

import onnxruntime as ort
from transformers import AutoTokenizer
import numpy as np

MODEL_DIR = "Xenova/bge-base-en-v1.5-int8"
ONNX_PATH = f"{MODEL_DIR}/model_quantized.onnx"
TOKENIZER_PATH = "BAAI/bge-base-en-v1.5"   # same tokenizer as the original model

session = ort.InferenceSession(
    ONNX_PATH,
    providers=["CPUExecutionProvider"],
)
tokenizer = AutoTokenizer.from_pretrained(TOKENIZER_PATH)


def _pool_and_normalize(outputs, attention_mask):
    """
    BGE family uses CLS pooling (first token) + L2 normalization.
    """
    # outputs[0] shape: (batch, seq_len, hidden=768)
    cls = outputs[0][:, 0, :]                       # CLS token
    norms = np.linalg.norm(cls, axis=1, keepdims=True)
    return cls / np.clip(norms, 1e-9, None)         # unit-length


def create_embedding(text: str) -> list[float]:
    enc = tokenizer(
        text,
        padding=True,
        truncation=True,
        max_length=512,
        return_tensors="np",
    )
    outputs = session.run(
        None,
        {
            "input_ids":      enc["input_ids"],
            "attention_mask": enc["attention_mask"],
        },
    )
    vec = _pool_and_normalize(outputs, enc["attention_mask"])[0]
    return vec.tolist()


def create_embeddings(texts: list[str]) -> list[list[float]]:
    if not texts:
        return []
    enc = tokenizer(
        list(texts),
        padding=True,
        truncation=True,
        max_length=512,
        return_tensors="np",
    )
    outputs = session.run(
        None,
        {
            "input_ids":      enc["input_ids"],
            "attention_mask": enc["attention_mask"],
        },
    )
    return _pool_and_normalize(outputs, enc["attention_mask"]).tolist()