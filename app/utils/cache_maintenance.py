"""Clear the app's own Redis cache entries, leaving Celery's keys alone (ISS-51)."""

# Resume extractions, JD extractions and embeddings. The Celery queue
# ("celery", "_kombu.*") and results ("celery-task-meta-*") share this Redis.
CACHE_PATTERNS = ("resume_extract:*", "jd_cache:*", "emb:*")


def clear_app_cache(r) -> int:
    """Delete every key matching CACHE_PATTERNS; return how many were deleted."""
    deleted = 0
    for pattern in CACHE_PATTERNS:
        batch = []
        for key in r.scan_iter(match=pattern, count=500):
            batch.append(key)
            if len(batch) >= 500:
                deleted += r.delete(*batch)
                batch = []
        if batch:
            deleted += r.delete(*batch)
    return deleted
