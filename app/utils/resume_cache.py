from pathlib import Path
import hashlib
import logging
import redis

from app.models.resume import Resume
from app.services.extract_resume import extract_resume_data


logger = logging.getLogger(__name__)

REDIS_HOST = "localhost"
REDIS_PORT = 6380
REDIS_DB = 0

CACHE_TTL = 60 * 60 * 24 * 60

MODEL_VERSION = "gemini-2.5-flash"
PROMPT_VERSION = "resume_extract_v2"


redis_client = redis.Redis(
    host=REDIS_HOST,
    port=REDIS_PORT,
    db=REDIS_DB,
    decode_responses=True,
)


def generate_file_hash(pdf_path: Path) -> str:
    file_bytes = pdf_path.read_bytes()
    return hashlib.sha256(file_bytes).hexdigest()


def generate_cache_key(pdf_path: Path) -> str:

    file_hash = generate_file_hash(pdf_path)

    return (
        f"resume_extract:"
        f"{file_hash}:"
        f"{MODEL_VERSION}:"
        f"{PROMPT_VERSION}"
    )


def get_cached_resume(cache_key: str) -> Resume | None:

    cached_data = redis_client.get(cache_key)

    if not cached_data:
        return None

    try:
        resume = Resume.model_validate_json(cached_data)

        logger.info("CACHE HIT key=%s", cache_key)

        return resume

    except Exception:
        logger.exception("Invalid cached resume")

        return None


def cache_resume(
    cache_key: str,
    resume: Resume,
) -> None:

    redis_client.setex(
        cache_key,
        CACHE_TTL,
        resume.model_dump_json(),
    )

    logger.info("Resume stored in Redis")


def process_resume(pdf_path: Path) -> Resume:

    cache_key = generate_cache_key(pdf_path)

    logger.info(
        "Processing file=%s",
        pdf_path.name,
    )

    # 1. Check cache
    cached_resume = get_cached_resume(cache_key)

    if cached_resume is not None:

        logger.info(
            "Returning cached resume: %s",
            pdf_path.name,
        )

        return cached_resume

    # 2. Cache miss
    logger.info(
        "CACHE MISS: %s",
        pdf_path.name,
    )

    # 3. Gemini extraction
    resume = extract_resume_data(pdf_path)

    if not isinstance(resume, Resume):
        resume = Resume.model_validate(resume)

    # 4. Cache result
    cache_resume(
        cache_key=cache_key,
        resume=resume,
    )

    return resume

from pathlib import Path


if __name__ == "__main__":

    file_path = Path(__file__).resolve().parents[2] / "app" / "pdf"

    for file in file_path.iterdir():

        if file.suffix.lower() != ".pdf":
            continue

        resume = process_resume(file)

        print(f"File name: {file.name}\n")
        print(resume)