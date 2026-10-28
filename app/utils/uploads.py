"""Safe temp paths for uploaded files (ISS-21)."""
import re
import uuid
from pathlib import Path

UPLOAD_DIR = Path("temp_uploads")
MAX_UPLOAD_BYTES = 10 * 1024 * 1024  # 10 MB


def safe_upload_path(filename: str) -> Path:
    """Return a unique path inside UPLOAD_DIR; never trusts directory parts of filename."""
    base = Path(filename or "upload").name
    base = re.sub(r"[^A-Za-z0-9._-]", "_", base)[:100] or "upload"
    UPLOAD_DIR.mkdir(exist_ok=True)
    return UPLOAD_DIR / f"{uuid.uuid4().hex}_{base}"
