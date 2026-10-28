```mermaid
zenuml
title FLOW-05 Cache maintenance
@Actor Recruiter
@Boundary UI as "Streamlit UI"
@Database Redis as "Redis (cache, broker, results)"

// Streamlit page: `http://localhost:8501` (docker-compose) or `:7860` (start.sh)
// Force Re-parse checkbox is rendered but not wired to ingestion
Recruiter->UI.clearCache() {
  try {
    // FLUSHALL also removes Celery queue and task results
    Redis.flushall()
    return "Redis cache flushed!"
  } catch {
    @return UI->Recruiter: sidebar error
  }
}
```
