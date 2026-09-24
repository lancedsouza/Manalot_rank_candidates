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

# """
# Local embedding service via ONNX Runtime + INT8 quantized bge-base-en-v1.5.

# Model:  Xenova/bge-base-en-v1.5-int8   →  768-dim vectors
# Runs entirely on-device. No API. No rate limits. No torch dependency.

# Dependencies:
#   - onnxruntime         (ONNX inference)
#   - tokenizers          (lightweight tokenization, no torch)
#   - huggingface_hub     (downloads model files on first run)
#   - numpy

# Memory: ~220 MB RAM.
# Cache:  Redis-backed, 30-day TTL, keyed by text hash.
# Loaded once per Streamlit session via @st.cache_resource.
# """
# import os
# import json
# import hashlib
# import logging
# from typing import List, Optional

# import numpy as np
# import onnxruntime as ort
# import redis
# import streamlit as st
# from dotenv import load_dotenv
# from huggingface_hub import hf_hub_download
# from tokenizers import Tokenizer

# load_dotenv()

# logger = logging.getLogger(__name__)

# MODEL_REPO = "Xenova/bge-base-en-v1.5"
# TOKENIZER_REPO = "BAAI/bge-base-en-v1.5"
# ONNX_FILENAME = "onnx/model_int8.onnx"
# TOKENIZER_FILENAME = "tokenizer.json"
# EMBED_DIM = 768
# MAX_LEN = 512


# # ============================================================
# # REDIS CACHE
# # ============================================================
# _redis = None
# try:
#     _redis = redis.Redis.from_url(
#         os.getenv("REDIS_URL", "redis://localhost:6380"),
#         decode_responses=True,
#         socket_connect_timeout=2,
#     )
#     _redis.ping()
#     logger.info("Embedding cache: Redis connected.")
# except Exception:
#     logger.warning("Embedding cache: Redis unavailable — running uncached.")
#     _redis = None


# def _cache_key(text: str) -> str:
#     h = hashlib.sha256(f"{MODEL_REPO}:{text}".encode("utf-8")).hexdigest()
#     return f"emb:{h}"


# def _cache_get(text: str) -> Optional[List[float]]:
#     if not _redis:
#         return None
#     try:
#         val = _redis.get(_cache_key(text))
#         return json.loads(val) if val else None
#     except Exception:
#         return None


# def _cache_set(text: str, vec: List[float]) -> None:
#     if not _redis:
#         return
#     try:
#         _redis.setex(_cache_key(text), 60 * 60 * 24 * 30, json.dumps(vec))
#     except Exception:
#         pass


# # ============================================================
# # MODEL LOADING (once per session)
# # ============================================================
# @st.cache_resource(show_spinner="Loading embedding model (first run only)...")
# def _load_model():
#     # 1. Download ONNX model file (~110 MB, cached after first run)
#     logger.info("Downloading/loading ONNX model: %s / %s", MODEL_REPO, ONNX_FILENAME)
#     onnx_path = hf_hub_download(repo_id=MODEL_REPO, filename=ONNX_FILENAME)

#     # 2. Download tokenizer JSON (~700 KB)
#     logger.info("Downloading/loading tokenizer: %s / %s", TOKENIZER_REPO, TOKENIZER_FILENAME)
#     tokenizer_path = hf_hub_download(repo_id=TOKENIZER_REPO, filename=TOKENIZER_FILENAME)

#     # 3. Create ONNX session
#     session = ort.InferenceSession(onnx_path, providers=["CPUExecutionProvider"])

#     # 4. Load tokenizer and configure padding + truncation for batches
#     tokenizer = Tokenizer.from_file(tokenizer_path)
#     tokenizer.enable_padding(pad_id=0, pad_token="[PAD]")
#     tokenizer.enable_truncation(max_length=MAX_LEN)

#     return session, tokenizer


# _session, _tokenizer = _load_model()


# # ============================================================
# # INFERENCE
# # ============================================================
# def _pool_and_normalize(hidden_state: np.ndarray) -> np.ndarray:
#     """BGE family: CLS pooling (first token) + L2 normalization."""
#     cls = hidden_state[:, 0, :]
#     norms = np.linalg.norm(cls, axis=1, keepdims=True)
#     return cls / np.clip(norms, 1e-9, None)


# def _encode_batch(texts: List[str]) -> List[List[float]]:
#     encodings = _tokenizer.encode_batch(texts)

#     input_ids = np.array([e.ids for e in encodings], dtype=np.int64)
#     attention_mask = np.array([e.attention_mask for e in encodings], dtype=np.int64)
#     token_type_ids = np.zeros_like(input_ids)

#     outputs = _session.run(
#         None,
#         {
#             "input_ids": input_ids,
#             "attention_mask": attention_mask,
#             "token_type_ids": token_type_ids,
#         },
#     )

#     vecs = _pool_and_normalize(outputs[0])
#     return [v.tolist() for v in vecs]


# # ============================================================
# # PUBLIC API
# # ============================================================
# def create_embedding(text: str) -> List[float]:
#     if not text or not text.strip():
#         text = " "
#     cached = _cache_get(text)
#     if cached is not None:
#         return cached
#     vec = _encode_batch([text])[0]
#     _cache_set(text, vec)
#     return vec


# def create_embeddings(texts: List[str]) -> List[List[float]]:
#     if not texts:
#         return []

#     normalized = [t if t and t.strip() else " " for t in texts]

#     results: List[Optional[List[float]]] = [None] * len(normalized)
#     miss_idx: List[int] = []
#     miss_txt: List[str] = []

#     for i, t in enumerate(normalized):
#         hit = _cache_get(t)
#         if hit is not None:
#             results[i] = hit
#         else:
#             miss_idx.append(i)
#             miss_txt.append(t)

#     logger.info(
#         "Embeddings: %d total, %d cache hits, %d misses",
#         len(normalized), len(normalized) - len(miss_txt), len(miss_txt),
#     )

#     if miss_txt:
#         vecs = _encode_batch(miss_txt)
#         for j, vec in zip(miss_idx, vecs):
#             results[j] = vec
#             _cache_set(normalized[j], vec)

#     return results  # type: ignore

# """
# Local embedding service via ONNX Runtime + INT8 quantized bge-base-en-v1.5.
# Optimized for 1GB RAM limits on Streamlit Cloud.
# """
# import os
# import json
# import hashlib
# import logging
# from typing import List, Optional

# import numpy as np
# import onnxruntime as ort
# import redis
# import streamlit as st
# from dotenv import load_dotenv
# from huggingface_hub import hf_hub_download
# from tokenizers import Tokenizer

# load_dotenv()

# logger = logging.getLogger(__name__)

# MODEL_REPO = "Xenova/bge-base-en-v1.5"
# TOKENIZER_REPO = "BAAI/bge-base-en-v1.5"
# ONNX_FILENAME = "onnx/model_int8.onnx"
# TOKENIZER_FILENAME = "tokenizer.json"
# MAX_LEN = 512

# # ============================================================
# # REDIS CACHE
# # ============================================================
# _redis = None
# try:
#     _redis = redis.Redis.from_url(
#         os.getenv("REDIS_URL", "redis://localhost:6380"),
#         decode_responses=True,
#         socket_connect_timeout=2,
#     )
#     _redis.ping()
#     logger.info("Embedding cache: Redis connected.")
# except Exception:
#     logger.warning("Embedding cache: Redis unavailable — running uncached.")
#     _redis = None

# def _cache_key(text: str) -> str:
#     h = hashlib.sha256(f"{MODEL_REPO}:{text}".encode("utf-8")).hexdigest()
#     return f"emb:{h}"

# def _cache_get(text: str) -> Optional[List[float]]:
#     if not _redis: return None
#     try:
#         val = _redis.get(_cache_key(text))
#         return json.loads(val) if val else None
#     except Exception:
#         return None

# def _cache_set(text: str, vec: List[float]) -> None:
#     if not _redis: return
#     try:
#         _redis.setex(_cache_key(text), 60 * 60 * 24 * 30, json.dumps(vec))
#     except Exception:
#         pass

# # ============================================================
# # LAZY MODEL LOADING WITH STRICT MEMORY CAPS
# # ============================================================
# @st.cache_resource(show_spinner="Waking up embedding engine... (first run only)")
# def load_embedding_model():
#     logger.info("Downloading/loading ONNX model...")
    
#     # 1. Download files (Passes token if available in env)
#     hf_token = os.getenv("HF_TOKEN")
#     onnx_path = hf_hub_download(repo_id=MODEL_REPO, filename=ONNX_FILENAME, token=hf_token)
#     tokenizer_path = hf_hub_download(repo_id=TOKENIZER_REPO, filename=TOKENIZER_FILENAME, token=hf_token)

#     # 2. STRICT MEMORY LIMITS FOR STREAMLIT CLOUD
#     sess_options = ort.SessionOptions()
#     sess_options.enable_cpu_mem_arena = False          # Stop hoarding memory
#     sess_options.intra_op_num_threads = 1              # Restrict to 1 thread
#     sess_options.inter_op_num_threads = 1              # Restrict to 1 thread
#     sess_options.execution_mode = ort.ExecutionMode.ORT_SEQUENTIAL
    
#     session = ort.InferenceSession(
#         onnx_path, 
#         sess_options=sess_options, 
#         providers=["CPUExecutionProvider"]
#     )

#     # 3. Load tokenizer
#     tokenizer = Tokenizer.from_file(tokenizer_path)
#     tokenizer.enable_padding(pad_id=0, pad_token="[PAD]")
#     tokenizer.enable_truncation(max_length=MAX_LEN)

#     return session, tokenizer

# # ============================================================
# # INFERENCE
# # ============================================================
# def _pool_and_normalize(hidden_state: np.ndarray) -> np.ndarray:
#     cls = hidden_state[:, 0, :]
#     norms = np.linalg.norm(cls, axis=1, keepdims=True)
#     return cls / np.clip(norms, 1e-9, None)

# def _encode_batch(texts: List[str]) -> List[List[float]]:
#     # LAZY LOAD: We only fetch the model when requested
#     session, tokenizer = load_embedding_model()
    
#     encodings = tokenizer.encode_batch(texts)
#     input_ids = np.array([e.ids for e in encodings], dtype=np.int64)
#     attention_mask = np.array([e.attention_mask for e in encodings], dtype=np.int64)
#     token_type_ids = np.zeros_like(input_ids)

#     outputs = session.run(
#         None,
#         {
#             "input_ids": input_ids,
#             "attention_mask": attention_mask,
#             "token_type_ids": token_type_ids,
#         },
#     )

#     vecs = _pool_and_normalize(outputs[0])
#     return [v.tolist() for v in vecs]

# # ============================================================
# # PUBLIC API
# # ============================================================
# def create_embedding(text: str) -> List[float]:
#     if not text or not text.strip():
#         text = " "
#     cached = _cache_get(text)
#     if cached is not None:
#         return cached
#     vec = _encode_batch([text])[0]
#     _cache_set(text, vec)
#     return vec

# def create_embeddings(texts: List[str]) -> List[List[float]]:
#     if not texts:
#         return []
#     normalized = [t if t and t.strip() else " " for t in texts]
#     results: List[Optional[List[float]]] = [None] * len(normalized)
#     miss_idx: List[int] = []
#     miss_txt: List[str] = []

#     for i, t in enumerate(normalized):
#         hit = _cache_get(t)
#         if hit is not None:
#             results[i] = hit
#         else:
#             miss_idx.append(i)
#             miss_txt.append(t)

#     if miss_txt:
#         vecs = _encode_batch(miss_txt)
#         for j, vec in zip(miss_idx, vecs):
#             results[j] = vec
#             _cache_set(normalized[j], vec)

#     return results  # type: ignore
"""
Local embedding service via FastEmbed (Qdrant).
Runs ONNX on CPU — no API, no rate limits, no external calls.
"""
import os
import json
import hashlib
import logging
from typing import List, Optional

import redis
import streamlit as st
from dotenv import load_dotenv
from fastembed import TextEmbedding

load_dotenv()

logger = logging.getLogger(__name__)

MODEL_NAME = "BAAI/bge-small-en-v1.5"
EMBED_DIM = 384

# ============================================================
# REDIS CACHE
# ============================================================
_redis = None
try:
    _redis = redis.Redis.from_url(
        os.getenv("REDIS_URL", "redis://localhost:6380"),
        decode_responses=True,
        socket_connect_timeout=2,
    )
    _redis.ping()
    logger.info("Embedding cache: Redis connected.")
except Exception:
    logger.warning("Embedding cache: Redis unavailable — running uncached.")
    _redis = None

def _cache_key(text: str) -> str:
    h = hashlib.sha256(f"{MODEL_NAME}:{text}".encode("utf-8")).hexdigest()
    return f"emb:{h}"

def _cache_get(text: str) -> Optional[List[float]]:
    if not _redis:
        return None
    try:
        val = _redis.get(_cache_key(text))
        return json.loads(val) if val else None
    except Exception:
        return None

def _cache_set(text: str, vec: List[float]) -> None:
    if not _redis:
        return
    try:
        _redis.setex(_cache_key(text), 60 * 60 * 24 * 30, json.dumps(vec))
    except Exception:
        pass

# ============================================================
# MODEL (lazy-loaded once per session)
# ============================================================
@st.cache_resource(show_spinner="Loading embedding model (first run only)...")
def _load_model() -> TextEmbedding:
    logger.info("Loading FastEmbed model: %s", MODEL_NAME)
    return TextEmbedding(model_name=MODEL_NAME)

def _embed_batch(texts: List[str]) -> List[List[float]]:
    model = _load_model()
    vectors = list(model.embed(texts))
    return [v.tolist() for v in vectors]

# ============================================================
# PUBLIC API
# ============================================================
def create_embedding(text: str) -> List[float]:
    if not text or not text.strip():
        text = " "
    cached = _cache_get(text)
    if cached is not None:
        return cached
    vec = _embed_batch([text])[0]
    _cache_set(text, vec)
    return vec

def create_embeddings(texts: List[str]) -> List[List[float]]:
    if not texts:
        return []
    normalized = [t if t and t.strip() else " " for t in texts]

    results: List[Optional[List[float]]] = [None] * len(normalized)
    miss_idx: List[int] = []
    miss_txt: List[str] = []

    for i, t in enumerate(normalized):
        hit = _cache_get(t)
        if hit is not None:
            results[i] = hit
        else:
            miss_idx.append(i)
            miss_txt.append(t)

    if miss_txt:
        vecs = _embed_batch(miss_txt)
        for j, vec in zip(miss_idx, vecs):
            results[j] = vec
            _cache_set(normalized[j], vec)

    return results  # type: ignore