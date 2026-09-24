# # app/services/gemini_service.py

# import logging
# import os
# import random
# import time
# from pathlib import Path
# from typing import Type

# from dotenv import load_dotenv
# from google import genai
# from google.genai import types
# from google.genai.errors import ServerError, ClientError
# from pydantic import BaseModel


# # ============================================================
# # LOGGING
# # ============================================================

# logger = logging.getLogger(__name__)


# # ============================================================
# # ENVIRONMENT
# # ============================================================

# PROJECT_ROOT = Path(__file__).resolve().parents[2]
# ENV_PATH = PROJECT_ROOT / ".env"

# load_dotenv(ENV_PATH)

# GEMINI_API_KEY = os.getenv("GEMINI_API_KEY")

# if not GEMINI_API_KEY:
#     raise ValueError(
#         f"GEMINI_API_KEY not found in {ENV_PATH}"
#     )


# # ============================================================
# # GEMINI CLIENT
# # ============================================================

# client = genai.Client(
#     api_key=GEMINI_API_KEY
# )


# # ============================================================
# # MODELS
# # ============================================================

# PRIMARY_MODEL = "gemini-2.5-flash"
# FALLBACK_MODEL = "gemini-2.5-flash-lite"


# # ============================================================
# # RETRY CONFIG
# # ============================================================

# MAX_ATTEMPTS_PER_MODEL = 2
# BASE_DELAY = 1.0


# # ============================================================
# # CUSTOM ERROR
# # ============================================================

# class AIServiceUnavailableError(RuntimeError):
#     """
#     Raised when both primary and fallback Gemini models
#     are temporarily unavailable.
#     """
#     pass


# # ============================================================
# # HELPER
# # ============================================================

# def _status_code(error) -> int | None:
#     """
#     Try to obtain HTTP status from different Google SDK
#     error representations.
#     """

#     return (
#         getattr(error, "code", None)
#         or getattr(error, "status_code", None)
#     )


# # ============================================================
# # STRUCTURED GEMINI REQUEST
# # ============================================================

# def generate_structured_response(
#     prompt: str,
#     schema: Type[BaseModel],
# ):
#     """
#     Calls Gemini using:

#     1. Gemini 2.5 Flash
#     2. Retry on temporary server failure
#     3. Exponential backoff + jitter
#     4. Gemini 2.5 Flash Lite fallback

#     Returns the successful GenerateContentResponse.
#     """

#     models = [
#         PRIMARY_MODEL,
#         FALLBACK_MODEL,
#     ]

#     last_error = None

#     for model_index, model_name in enumerate(models):

#         logger.info("=" * 60)
#         logger.info(
#             "Trying Gemini model: %s",
#             model_name,
#         )
#         logger.info("=" * 60)

#         for attempt in range(
#             1,
#             MAX_ATTEMPTS_PER_MODEL + 1,
#         ):

#             logger.info(
#                 "%s attempt %d/%d",
#                 model_name,
#                 attempt,
#                 MAX_ATTEMPTS_PER_MODEL,
#             )

#             logger.info(
#                 "Prompt size: %d characters",
#                 len(prompt),
#             )

#             start = time.perf_counter()

#             try:

#                 response = client.models.generate_content(
#                     model=model_name,
#                     contents=prompt,
#                     config=types.GenerateContentConfig(
#                         temperature=0,
#                         response_mime_type="application/json",
#                         response_schema=schema,
#                     ),
#                 )

#                 elapsed = (
#                     time.perf_counter()
#                     - start
#                 )

#                 logger.info(
#                     "%s succeeded in %.2f seconds.",
#                     model_name,
#                     elapsed,
#                 )

#                 if response.text:

#                     logger.info(
#                         "Response size: %d characters.",
#                         len(response.text),
#                     )

#                 return response


#             # =================================================
#             # TEMPORARY GOOGLE SERVER FAILURE
#             # =================================================

#             except ServerError as error:

#                 elapsed = (
#                     time.perf_counter()
#                     - start
#                 )

#                 last_error = error

#                 code = _status_code(error)
                

#                 logger.warning(
#                     "%s server error after %.2fs "
#                     "(status=%s): %s",
#                     model_name,
#                     elapsed,
#                     code,
#                     error,
#                 )

#                 # 500/502/503/504 are normally temporary.
#                 retryable = (
#                     code is None
#                     or code in {
#                         500,
#                         502,
#                         503,
#                         504,
#                     }
#                 )

#                 if not retryable:
#                     raise

#                 # Last attempt for this model?
#                 if (
#                     attempt
#                     >= MAX_ATTEMPTS_PER_MODEL
#                 ):

#                     logger.warning(
#                         "%s exhausted its retry attempts.",
#                         model_name,
#                     )

#                     break

#                 # exponential backoff + jitter
#                 delay = (
#                     BASE_DELAY
#                     * (2 ** (attempt - 1))
#                     + random.uniform(
#                         0.0,
#                         0.75,
#                     )
#                 )

#                 logger.info(
#                     "Temporary Gemini failure. "
#                     "Retrying in %.2f seconds...",
#                     delay,
#                 )

#                 time.sleep(delay)


#             # =================================================
#             # CLIENT ERRORS
#             # 400 / authentication / permissions etc.
#             # =================================================

#             except ClientError as error:

#                 elapsed = (
#                     time.perf_counter()
#                     - start
#                 )

#                 logger.exception(
#                     "Gemini client error after %.2fs.",
#                     elapsed,
#                 )

#                 raise


#             # =================================================
#             # UNKNOWN FAILURE
#             # =================================================

#             except Exception:

#                 elapsed = (
#                     time.perf_counter()
#                     - start
#                 )

#                 logger.exception(
#                     "Unexpected Gemini failure "
#                     "after %.2fs.",
#                     elapsed,
#                 )

#                 raise


#         # =====================================================
#         # SWITCH TO FALLBACK
#         # =====================================================

#         if model_index < len(models) - 1:

#             next_model = models[
#                 model_index + 1
#             ]

#             logger.warning(
#                 "Switching from %s "
#                 "to fallback model %s.",
#                 model_name,
#                 next_model,
#             )


#     # =========================================================
#     # ALL PROVIDERS FAILED
#     # =========================================================

#     logger.error(
#         "All configured Gemini models failed."
#     )

#     raise AIServiceUnavailableError(
#         "The AI service is temporarily busy. "
#         "Please try again shortly."
#     ) from last_error


# """
# Gemini client with model fallback and retry.

# Handles:
#   - 5xx server errors      → retry same model, then fallback
#   - 429 RESOURCE_EXHAUSTED → switch to next model immediately
#   - Other 4xx              → raise (no retry)
# """
# import logging
# import os
# import random
# import re
# import time
# from pathlib import Path
# from typing import Type

# from dotenv import load_dotenv
# from google import genai
# from google.genai import types
# from google.genai.errors import ServerError, ClientError
# from pydantic import BaseModel

# logger = logging.getLogger(__name__)

# PROJECT_ROOT = Path(__file__).resolve().parents[2]
# load_dotenv(PROJECT_ROOT / ".env")

# GEMINI_API_KEY = os.getenv("GEMINI_API_KEY")
# if not GEMINI_API_KEY:
#     raise ValueError("GEMINI_API_KEY not found in .env")

# client = genai.Client(
#     api_key=GEMINI_API_KEY,
#     http_options={"api_version": "v1"},
# )

# # Ordered: most generous quota first
# MODELS = [
#     "models/gemini-3.6-flash",
#     "models/gemini-3.5-flash-lite",
#     "models/gemini-2.5-flash",
# ]
# MAX_ATTEMPTS_PER_MODEL = 2
# BASE_DELAY = 1.0


# class AIServiceUnavailableError(RuntimeError):
#     pass


# def _is_quota_error(err: Exception) -> bool:
#     s = str(err).lower()
#     return (
#         "429" in s
#         or "resource_exhausted" in s
#         or "quota" in s
#         or "rate limit" in s
#     )


# def _parse_retry_delay(err: Exception) -> float | None:
#     m = re.search(
#         r"retry\s+(?:in|after)?\s*(\d+(?:\.\d+)?)\s*s",
#         str(err),
#         re.IGNORECASE,
#     )
#     return float(m.group(1)) if m else None


# def generate_structured_response(prompt: str, schema: Type[BaseModel]):
#     """
#     Try each model in MODELS until one succeeds.

#     Within a model:
#       - 5xx: retry up to MAX_ATTEMPTS_PER_MODEL
#       - 429: switch to next model immediately
#       - other 4xx: raise
#     """
#     last_error = None

#     for model_index, model_name in enumerate(MODELS):
#         logger.info("Trying Gemini model: %s", model_name)

#         for attempt in range(1, MAX_ATTEMPTS_PER_MODEL + 1):
#             start = time.perf_counter()

#             try:
#                 response = client.models.generate_content(
#                     model=model_name,
#                     contents=prompt,
#                     config=types.GenerateContentConfig(
#                         temperature=0,
#                         response_mime_type="application/json",
#                         response_schema=schema,
#                     ),
#                 )

#                 elapsed = time.perf_counter() - start
#                 logger.info("%s succeeded in %.2fs", model_name, elapsed)
#                 return response

#             except ClientError as error:
#                 elapsed = time.perf_counter() - start

#                 # ---- 429 quota: switch to next model immediately ----
#                 if _is_quota_error(error):
#                     last_error = error
#                     delay = _parse_retry_delay(error)

#                     logger.warning(
#                         "Quota hit on %s (%.2fs)%s",
#                         model_name,
#                         elapsed,
#                         f" — server says retry in {delay:.0f}s" if delay else "",
#                     )

#                     # don't retry this model; go to next
#                     break

#                 # ---- other 4xx: raise ----
#                 logger.exception("Gemini client error after %.2fs", elapsed)
#                 raise

#             except ServerError as error:
#                 elapsed = time.perf_counter() - start
#                 last_error = error

#                 logger.warning(
#                     "Server error on %s (%.2fs): %s",
#                     model_name, elapsed, error,
#                 )

#                 if attempt >= MAX_ATTEMPTS_PER_MODEL:
#                     logger.warning("%s exhausted retries.", model_name)
#                     break

#                 delay = BASE_DELAY * (2 ** (attempt - 1)) + random.uniform(0, 0.75)
#                 logger.info("Retrying in %.2fs...", delay)
#                 time.sleep(delay)

#             except Exception:
#                 logger.exception("Unexpected Gemini failure.")
#                 raise

#         # switch to next model
#         if model_index < len(MODELS) - 1:
#             logger.warning(
#                 "Switching from %s to %s",
#                 model_name, MODELS[model_index + 1],
#             )

#     logger.error("All models exhausted.")
#     raise AIServiceUnavailableError(
#         "All Gemini models are rate-limited. Try again later."
#     ) from last_error

# """
# Gemini service wrapper for structured response generation.
# Handles primary and fallback models with automatic retry logic.
# """

# import os
# import logging
# from dotenv import load_dotenv
# from google import genai
# from google.genai import types

# load_dotenv()
# logger = logging.getLogger(__name__)

# def generate_structured_response(prompt: str, schema):
#     """
#     Generates structured JSON responses conforming to a Pydantic schema using Gemini.
#     Automatically falls back to lighter models if primary models experience high demand.
#     """
#     api_key = os.getenv("GEMINI_API_KEY")
#     client = genai.Client(api_key=api_key)
    
#     # Primary workhorse model and reliable fallback option
#     models_to_try = ["gemini-3.6-flash", "gemini-3.5-flash-lite"]
    
#     last_exception = None
#     for model_name in models_to_try:
#         try:
#             logger.info(f"Attempting structured generation with model: {model_name}")
#             response = client.models.generate_content(
#                 model=model_name,
#                 contents=prompt,
#                 config=types.GenerateContentConfig(
#                     response_mime_type="application/json",
#                     response_schema=schema,
#                 ),
#             )
#             return response
#         except Exception as e:
#             logger.warning(f"Server error on {model_name}: {e}")
#             last_exception = e
#             continue
            
#     # If all models fail, raise an informative error
#     raise RuntimeError(f"All Gemini text generation models exhausted retries: {last_exception}")

# """
# Gemini service wrapper for structured response generation.
# Handles primary and fallback models with automatic retry logic.
# """

# import os
# import logging
# from dotenv import load_dotenv
# from google import genai
# from google.genai import types

# load_dotenv()
# logger = logging.getLogger(__name__)

# def generate_structured_response(prompt: str, schema):
#     """
#     Generates structured JSON responses conforming to a Pydantic schema using Gemini.
#     Automatically falls back to lighter models if primary models experience high demand.
#     """
#     api_key = os.getenv("GEMINI_API_KEY")
#     client = genai.Client(api_key=api_key)
    
#     # Primary workhorse model and reliable fallback option
#     models_to_try = ["gemini-3.6-flash", "gemini-3.5-flash-lite"]
    
#     last_exception = None
#     for model_name in models_to_try:
#         try:
#             logger.info(f"Attempting structured generation with model: {model_name}")
#             response = client.models.generate_content(
#                 model=model_name,
#                 contents=prompt,
#                 config=types.GenerateContentConfig(
#                     response_mime_type="application/json",
#                     response_schema=schema,
#                 ),
#             )
#             return response
#         except Exception as e:
#             logger.warning(f"Server error on {model_name}: {e}")
#             last_exception = e
#             continue
            
#     raise RuntimeError(f"All Gemini text generation models exhausted retries: {last_exception}")

"""
Groq-powered structured response generation service.
Replaces Gemini to bypass free-tier rate limits and 404 errors.
"""

import os
import json
import logging
from dotenv import load_dotenv
from groq import Groq

load_dotenv()
logger = logging.getLogger(__name__)

def generate_structured_response(prompt: str, schema):
    """
    Generates structured JSON responses conforming to a Pydantic schema using Groq's 
    blazing-fast Llama models with JSON mode.
    """
    api_key = os.getenv("GROQ_API_KEY")
    if not api_key:
        raise ValueError("GROQ_API_KEY environment variable is missing. Please add it to your .env file.")

    # Initialize the Groq client
    client = Groq(api_key=api_key)
    
    # Use high-performance Llama 3.3 model on Groq
    model_name = "llama-3.3-70b-versatile"
    
    # Dynamically extract the Pydantic schema and inject it into the system prompt
    # This guarantees the open-weights model perfectly formats the JSON keys
    schema_json_str = json.dumps(schema.model_json_schema(), indent=2)
    system_prompt = (
        "You are an expert HR data parsing system. "
        "Extract the required details from the text and output ONLY valid JSON "
        "that strictly matches the following JSON schema structure:\n"
        f"{schema_json_str}"
    )

    try:
        logger.info(f"Attempting structured generation via Groq with model: {model_name}")
        
        # Call Groq with JSON Object mode enforced
        completion = client.chat.completions.create(
            model=model_name,
            messages=[
                {"role": "system", "content": system_prompt},
                {"role": "user", "content": prompt}
            ],
            response_format={"type": "json_object"},
            temperature=0.1,  # Low temperature for highly deterministic data extraction
        )
        
        raw_content = completion.choices[0].message.content
        parsed_dict = json.loads(raw_content)
        
        # Validate the dictionary strictly against your Pydantic schema
        validated_instance = schema.model_validate(parsed_dict)
        
        # Wrap it in a dummy object mimicking the structure expected by your downstream extractors (response.parsed)
        class GroqResponseWrapper:
            def __init__(self, parsed_data):
                self.parsed = parsed_data

        return GroqResponseWrapper(validated_instance)

    except Exception as e:
        logger.exception(f"Groq generation failed: {e}")
        raise RuntimeError(f"Groq API error: {e}")