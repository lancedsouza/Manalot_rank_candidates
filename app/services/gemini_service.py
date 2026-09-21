# app/services/gemini_service.py

import logging
import os
import random
import time
from pathlib import Path
from typing import Type

from dotenv import load_dotenv
from google import genai
from google.genai import types
from google.genai.errors import ServerError, ClientError
from pydantic import BaseModel


# ============================================================
# LOGGING
# ============================================================

logger = logging.getLogger(__name__)


# ============================================================
# ENVIRONMENT
# ============================================================

PROJECT_ROOT = Path(__file__).resolve().parents[2]
ENV_PATH = PROJECT_ROOT / ".env"

load_dotenv(ENV_PATH)

GEMINI_API_KEY = os.getenv("GEMINI_API_KEY")

if not GEMINI_API_KEY:
    raise ValueError(
        f"GEMINI_API_KEY not found in {ENV_PATH}"
    )


# ============================================================
# GEMINI CLIENT
# ============================================================

client = genai.Client(
    api_key=GEMINI_API_KEY
)


# ============================================================
# MODELS
# ============================================================

PRIMARY_MODEL = "gemini-2.5-flash"
FALLBACK_MODEL = "gemini-2.5-flash-lite"


# ============================================================
# RETRY CONFIG
# ============================================================

MAX_ATTEMPTS_PER_MODEL = 2
BASE_DELAY = 1.0


# ============================================================
# CUSTOM ERROR
# ============================================================

class AIServiceUnavailableError(RuntimeError):
    """
    Raised when both primary and fallback Gemini models
    are temporarily unavailable.
    """
    pass


# ============================================================
# HELPER
# ============================================================

def _status_code(error) -> int | None:
    """
    Try to obtain HTTP status from different Google SDK
    error representations.
    """

    return (
        getattr(error, "code", None)
        or getattr(error, "status_code", None)
    )


# ============================================================
# STRUCTURED GEMINI REQUEST
# ============================================================

def generate_structured_response(
    prompt: str,
    schema: Type[BaseModel],
):
    """
    Calls Gemini using:

    1. Gemini 2.5 Flash
    2. Retry on temporary server failure
    3. Exponential backoff + jitter
    4. Gemini 2.5 Flash Lite fallback

    Returns the successful GenerateContentResponse.
    """

    models = [
        PRIMARY_MODEL,
        FALLBACK_MODEL,
    ]

    last_error = None

    for model_index, model_name in enumerate(models):

        logger.info("=" * 60)
        logger.info(
            "Trying Gemini model: %s",
            model_name,
        )
        logger.info("=" * 60)

        for attempt in range(
            1,
            MAX_ATTEMPTS_PER_MODEL + 1,
        ):

            logger.info(
                "%s attempt %d/%d",
                model_name,
                attempt,
                MAX_ATTEMPTS_PER_MODEL,
            )

            logger.info(
                "Prompt size: %d characters",
                len(prompt),
            )

            start = time.perf_counter()

            try:

                response = client.models.generate_content(
                    model=model_name,
                    contents=prompt,
                    config=types.GenerateContentConfig(
                        temperature=0,
                        response_mime_type="application/json",
                        response_schema=schema,
                    ),
                )

                elapsed = (
                    time.perf_counter()
                    - start
                )

                logger.info(
                    "%s succeeded in %.2f seconds.",
                    model_name,
                    elapsed,
                )

                if response.text:

                    logger.info(
                        "Response size: %d characters.",
                        len(response.text),
                    )

                return response


            # =================================================
            # TEMPORARY GOOGLE SERVER FAILURE
            # =================================================

            except ServerError as error:

                elapsed = (
                    time.perf_counter()
                    - start
                )

                last_error = error

                code = _status_code(error)
                

                logger.warning(
                    "%s server error after %.2fs "
                    "(status=%s): %s",
                    model_name,
                    elapsed,
                    code,
                    error,
                )

                # 500/502/503/504 are normally temporary.
                retryable = (
                    code is None
                    or code in {
                        500,
                        502,
                        503,
                        504,
                    }
                )

                if not retryable:
                    raise

                # Last attempt for this model?
                if (
                    attempt
                    >= MAX_ATTEMPTS_PER_MODEL
                ):

                    logger.warning(
                        "%s exhausted its retry attempts.",
                        model_name,
                    )

                    break

                # exponential backoff + jitter
                delay = (
                    BASE_DELAY
                    * (2 ** (attempt - 1))
                    + random.uniform(
                        0.0,
                        0.75,
                    )
                )

                logger.info(
                    "Temporary Gemini failure. "
                    "Retrying in %.2f seconds...",
                    delay,
                )

                time.sleep(delay)


            # =================================================
            # CLIENT ERRORS
            # 400 / authentication / permissions etc.
            # =================================================

            except ClientError as error:

                elapsed = (
                    time.perf_counter()
                    - start
                )

                logger.exception(
                    "Gemini client error after %.2fs.",
                    elapsed,
                )

                raise


            # =================================================
            # UNKNOWN FAILURE
            # =================================================

            except Exception:

                elapsed = (
                    time.perf_counter()
                    - start
                )

                logger.exception(
                    "Unexpected Gemini failure "
                    "after %.2fs.",
                    elapsed,
                )

                raise


        # =====================================================
        # SWITCH TO FALLBACK
        # =====================================================

        if model_index < len(models) - 1:

            next_model = models[
                model_index + 1
            ]

            logger.warning(
                "Switching from %s "
                "to fallback model %s.",
                model_name,
                next_model,
            )


    # =========================================================
    # ALL PROVIDERS FAILED
    # =========================================================

    logger.error(
        "All configured Gemini models failed."
    )

    raise AIServiceUnavailableError(
        "The AI service is temporarily busy. "
        "Please try again shortly."
    ) from last_error