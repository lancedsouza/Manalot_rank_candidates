```mermaid
zenuml
title FLOW-05 Cache maintenance
@Actor Recruiter
@Boundary UI as "Streamlit UI"
@Database Redis as "Redis (cache, broker, results)"

// Streamlit page: `http://localhost:8501` (docker-compose) or `:7860` (start.sh)
// Force Re-parse: when ticked, FLOW-02 deletes each uploaded resume's resume_extract key before queueing (ISS-52)
Recruiter->UI.clearCache() {
  try {
    // only cache keys; Celery queue and task results survive (ISS-51)
    Redis.scanAndDelete("resume_extract:*, jd_cache:*, emb:*")
    return "Redis cache flushed!"
  } catch {
    @return UI->Recruiter: sidebar error
  }
}
```
