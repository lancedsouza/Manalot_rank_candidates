# Architecture: Manalot Rank Candidates

Manalot ranks candidate resumes against a job description (JD). A recruiter works in a Streamlit UI. Resume extraction runs asynchronously through FastAPI and a Celery worker, with Redis as broker, result backend and cache. Structured extraction uses the Groq LLM (`openai/gpt-oss-20b`, JSON mode). Embeddings come from FastEmbed `BAAI/bge-small-en-v1.5` (384 dims), running locally on CPU. Data is stored in Postgres + pgvector (Neon in production). The README still describes Gemini and 768 dims; that is out of date.

## System context

```mermaid
C4Context
  title "Manalot Rank Candidates - System Context"
  Person(recruiter, "Recruiter", "Uploads JDs and resumes, reviews shortlist")
  System(manalot, "Manalot Rank Candidates", "Extracts, embeds and scores candidates against JDs")
  System_Ext(groq, "Groq API", "LLM openai/gpt-oss-20b")
  System_Ext(neon, "Neon Postgres", "Postgres + pgvector")
  System_Ext(redis, "Redis", "Broker, result backend, cache (REDIS_URL)")
  Rel(recruiter, manalot, "Uses", "HTTPS, Streamlit")
  Rel(manalot, groq, "Structured extraction", "HTTPS POST /openai/v1/chat/completions")
  Rel(manalot, neon, "Reads/writes JDs, candidates, scores", "SQL over TLS (DATABASE_URL)")
  Rel(manalot, redis, "Queues tasks, caches results", "Redis protocol")
  UpdateLayoutConfig($c4ShapeInRow="3", $c4BoundaryInRow="1")
```

Flows: [FLOW-01](flows/web/upload-jd-flow.md), [FLOW-02](flows/web/ingest-resumes-flow.md), [FLOW-03](flows/web/score-candidate-flow.md), [FLOW-04](flows/web/view-shortlist-flow.md), [FLOW-05](flows/web/cache-maintenance-flow.md), [FLOW-06](flows/api/task-status-flow.md).

## Containers

```mermaid
C4Container
  title "Manalot Rank Candidates - Containers"
  Person(recruiter, "Recruiter", "Hiring user")
  System_Ext(groq, "Groq API", "LLM openai/gpt-oss-20b")
  Container_Boundary(app, "Manalot (docker-compose)") {
    Container(ui, "Streamlit UI", "Python, Streamlit", "streamlit_app.py; port 8501 (docker) / 7860 (start.sh)")
    Container(api, "FastAPI", "Python, FastAPI", "backend.py; saves uploads to temp_uploads, enqueues tasks")
    Container(worker, "Celery worker", "Python, Celery", "worker.py; task process_resume")
    Container(embed, "FastEmbed model", "ONNX, local CPU", "BAAI/bge-small-en-v1.5, 384 dims")
  }
  ContainerQueue(redis, "Redis", "Redis", "Celery broker + result backend; caches resume_extract:, jd_cache:, emb:")
  ContainerDb(pg, "Postgres + pgvector", "Neon", "jds, jd_skill, candidates, cand_skill, applications")
  Rel(recruiter, ui, "Uses", "HTTP")
  Rel(ui, api, "Upload resume / poll task", "HTTP POST /api/v1/extract-resume/async, GET /api/v1/task/{task_id}")
  Rel(ui, pg, "Shortlist, evidence, coverage queries; in-process JD and resume processing", "SQL")
  Rel(ui, redis, "Cache reads/writes; FLUSHALL", "Redis protocol")
  Rel(ui, groq, "JD/resume extraction (in-process)", "HTTPS")
  Rel(ui, embed, "Embed skills (in-process)", "Python call")
  Rel(api, redis, "Enqueue process_resume; read AsyncResult", "Redis protocol")
  Rel(worker, redis, "Consume tasks; store results; resume_extract: cache", "Redis protocol")
  Rel(worker, groq, "Structured extraction", "HTTPS POST /openai/v1/chat/completions")
  UpdateLayoutConfig($c4ShapeInRow="3", $c4BoundaryInRow="1")
```

Flows: [FLOW-01](flows/web/upload-jd-flow.md), [FLOW-02](flows/web/ingest-resumes-flow.md), [FLOW-05](flows/web/cache-maintenance-flow.md), [FLOW-06](flows/api/task-status-flow.md).

## Components (`app/` package)

```mermaid
C4Component
  title "Manalot Rank Candidates - app package components"
  Container(ui, "Streamlit UI", "Python", "streamlit_app.py")
  Container(worker, "Celery worker", "Python", "worker.py")
  ContainerDb(pg, "Postgres + pgvector", "Neon", "Relational + vector store")
  ContainerDb(redis, "Redis", "Redis", "Caches")
  System_Ext(groq, "Groq API", "LLM")
  Container_Boundary(pkg, "app package") {
    Component(jdproc, "JD processor", "app/services/jd_processor", "process_pdf_jd")
    Component(resproc, "Resume processor", "app/services/resume_processor", "process_and_link_resume")
    Component(rcache, "Resume cache", "app/utils/resume_cache", "process_resume; resume_extract: 60d")
    Component(rextract, "Resume extractor", "app/services/extract_resume", "extract_resume_data; pdfplumber")
    Component(sections, "Section extractor", "app/utils/section_extractor", "Rule-based sections")
    Component(jdextract, "JD extractor", "app/utils/extract_jd", "extract_structured_jd; jd_cache: 7d")
    Component(llm, "LLM client", "app/services/gemini_service", "generate_structured_response, JSON mode")
    Component(emb, "Embedding service", "app/embedding/embedding_service", "FastEmbed 384 dims; emb: 30d")
    Component(score, "Scoring", "app/services/resume_processor", "0.20 parent + 0.55 coverage(>=0.75) + 0.25 depth")
  }
  Rel(ui, jdproc, "Calls", "Python")
  Rel(ui, resproc, "Calls", "Python")
  Rel(worker, rcache, "Calls", "Python")
  Rel(jdproc, jdextract, "Extracts JD", "Python")
  Rel(jdproc, emb, "Embeds skills", "Python")
  Rel(resproc, rextract, "Extracts resume", "Python")
  Rel(resproc, emb, "Embeds skills", "Python")
  Rel(resproc, score, "Scores candidate", "Python")
  Rel(rcache, rextract, "On cache miss", "Python")
  Rel(rextract, sections, "Splits sections", "Python")
  Rel(rextract, llm, "Structured output", "Python")
  Rel(jdextract, llm, "Structured output", "Python")
  Rel(llm, groq, "Chat completions", "HTTPS POST /openai/v1/chat/completions")
  Rel(rcache, redis, "resume_extract:", "Redis protocol")
  Rel(jdextract, redis, "jd_cache:", "Redis protocol")
  Rel(emb, redis, "emb:", "Redis protocol")
  Rel(jdproc, pg, "jds, jd_skill", "SQL")
  Rel(resproc, pg, "candidates, cand_skill, applications", "SQL")
  Rel(score, pg, "pgvector similarity", "SQL")
  UpdateLayoutConfig($c4ShapeInRow="3", $c4BoundaryInRow="1")
```

Flows: [FLOW-01](flows/web/upload-jd-flow.md), [FLOW-02](flows/web/ingest-resumes-flow.md), [FLOW-03](flows/web/score-candidate-flow.md), [FLOW-04](flows/web/view-shortlist-flow.md).

## Known architectural risks

- Path traversal: upload filenames are used unsanitised when writing to `temp_uploads`.
- Cache maintenance runs Redis `FLUSHALL`, which also wipes the Celery broker queue and task results.
- The UI runs extraction again in-process after the worker has finished, so LLM calls are duplicated and the async path does nothing useful.
- `start.sh` and docker-compose start a `backend_api` module that does not exist; the live API is `backend.py`.
- The FastAPI endpoints have no authentication, and the UI hardcodes `http://localhost:8000/api/v1`.
