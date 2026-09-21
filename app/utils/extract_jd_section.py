from google import genai
from google.genai import types  
from app.pydantic_models.jd_pydantic_models import JDRequirements
from app.utils.extract_jd import extract_jd
import redis
import hashlib
import logging
from dotenv import load_dotenv
load_dotenv()

# Initialize Redis client and logger
redis_client = redis.Redis(host="localhost", port=6379, db=0, decode_responses=True)
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

def get_cache_key(text: str) -> str:
    hash_object = hashlib.sha256(text.encode('utf-8'))
    return f"jd_cache:{hash_object.hexdigest()}"

def get_cached_structured_jd(text: str) -> JDRequirements | None:
    cache_key = get_cache_key(text)
    cached_data = redis_client.get(cache_key)
    
    if cached_data:
        logger.info("[CACHE HIT] Retrieved parsed JD from Redis.")
        return JDRequirements.model_validate_json(cached_data)
        
    logger.info("[CACHE MISS] No cached record found.")
    return None

def extract_structured_jd(text: str) -> JDRequirements:
    # 1. Check cache first
    cached_result = get_cached_structured_jd(text)
    if cached_result:
        return cached_result

    # 2. Query Gemini if cache misses
    client = genai.Client()
    prompt = f"""Extract from the job description (JD) all the required pydantic fields:
    1. Skills required by the employer
    2. Responsibilities mentioned in the JD
    3. Education mentioned in the JD (e.g., MBA, etc.)
    4. Industries the employer prefers (e.g., Finance, etc.)

    Job Description Content:
    {text}
    """

    response = client.models.generate_content(
        model="gemini-2.5-flash",
        contents=prompt,
        config=types.GenerateContentConfig(
            response_mime_type="application/json",
            response_schema=JDRequirements,
            temperature=0.1
        ),
    )

    parsed_data: JDRequirements = response.parsed

    # 3. Save to Redis cache (expire in 7 days / 604800 seconds)
    cache_key = get_cache_key(text)
    redis_client.setex(cache_key, 604800, parsed_data.model_dump_json())
    logger.info("[CACHE SET] Saved parsed JD response to Redis.")

    return parsed_data

if __name__ == "__main__":
    from pathlib import Path
    jd_root = Path(__file__).resolve().parents[2]
    jd_dir = jd_root / "app" / "jd_data"
    
    jd_files = list(jd_dir.glob("*.docx")) + list(jd_dir.glob("*.pdf"))
    
    if not jd_files:
        logger.error("No JD files found in directory.")
    else:
        for file in jd_files:
            logger.info(f"Processing file: {file.name}")
            raw_text = extract_jd(file)
            
            # Extract and parse via Gemini with Redis caching integrated
            structured_jd = extract_structured_jd(raw_text)
            print(f"\n--- Result for {file.name} ---\n{structured_jd}\n")