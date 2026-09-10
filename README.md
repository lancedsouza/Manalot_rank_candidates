# Manalot Rank Candidates

**Manalot Rank Candidates** is an AI-powered recruitment and candidate-ranking system designed to help recruiters screen resumes against job descriptions using structured extraction, semantic embeddings, vector search, and evidence-based matching.

The system converts unstructured resumes and job descriptions into structured data, generates semantic embeddings, stores candidate and JD data in PostgreSQL with `pgvector`, and is being developed to rank candidates based on both semantic similarity and recruiter-relevant evidence.

---

## 🎯 Project Goal

Traditional keyword-based ATS systems can miss strong candidates when a resume expresses relevant experience using different terminology from the job description.

For example, a JD may ask for:

> Budgeting and forecasting experience

while a candidate may write:

> Managed annual operating plans and quarterly financial projections.

A semantic recruitment system should understand that these statements are related rather than relying only on exact keyword matches.

The goal of Manalot Rank Candidates is therefore to combine:

* Structured resume extraction
* Structured JD extraction
* Semantic embeddings
* Vector similarity
* Deterministic scoring
* Evidence-based matching
* AI-generated recruiter explanations

---

# 🏗️ System Architecture

```text
                    JOB DESCRIPTION
                           │
                           ▼
                  Structured Extraction
                           │
                           ▼
                    JD Pydantic Model
                           │
                           ├───────────────┐
                           │               │
                           ▼               ▼
                      Raw JD Text     Structured Fields
                           │
                           ▼
                   Gemini Embedding
                           │
                           ▼
                     VECTOR(768)
                           │
                           ▼
                         NEON
                    PostgreSQL + pgvector


                        RESUME PDF
                           │
                           ▼
                     SHA256 Hash
                           │
                           ▼
                    Redis Cache Check
                      │           │
                  CACHE HIT    CACHE MISS
                      │           │
                      │           ▼
                      │      Gemini 2.5 Flash
                      │           │
                      │      Structured Resume
                      │           │
                      │       Redis Cache
                      │           │
                      └─────┬─────┘
                            ▼
                     Pydantic Resume
                            │
                    ┌───────┴────────┐
                    │                │
                    ▼                ▼
             Structured Data    Resume Text
                                     │
                                     ▼
                              Gemini Embedding
                                     │
                                     ▼
                                VECTOR(768)
                                     │
                                     ▼
                                   NEON
```

---

# ✨ Current Features

## 1. PDF Resume Extraction

The application reads resume PDFs and extracts their text for downstream processing.

Resume sections such as professional experience, education, skills, and projects can then be identified and processed.

---

## 2. AI-Powered Structured Resume Extraction

Resume content is converted into structured data using **Gemini 2.5 Flash**.

The output is validated using Pydantic.

Example:

```python
class Education(BaseModel):
    degree: Optional[str] = None
    institution: Optional[str] = None
    start_date: Optional[str] = None
    end_date: Optional[str] = None


class Experience(BaseModel):
    company: Optional[str] = None
    title: Optional[str] = None
    start_date: Optional[str] = None
    end_date: Optional[str] = None


class Resume(BaseModel):
    name: Optional[str] = None
    skills: List[str] = Field(default_factory=list)
    experience_years: Optional[float] = 0.0
    education: List[Education] = Field(default_factory=list)
    experience: List[Experience] = Field(default_factory=list)
    projects: List[str] = Field(default_factory=list)
```

This converts an unstructured PDF into data similar to:

```json
{
  "name": "Candidate Name",
  "skills": [
    "Financial Planning",
    "Forecasting",
    "Python",
    "Power BI"
  ],
  "experience_years": 15.4,
  "education": [
    {
      "degree": "MBA Finance",
      "institution": "Example University"
    }
  ],
  "experience": [
    {
      "company": "Example Company",
      "title": "Finance Director",
      "start_date": "2021",
      "end_date": "2026"
    }
  ],
  "projects": []
}
```

---

# ⚡ Redis Resume Caching

LLM-based resume extraction can be relatively expensive and slow.

The project therefore uses **Redis** to cache successfully extracted resumes.

The processing flow is:

```text
Resume
   │
   ▼
SHA256(file)
   │
   ▼
Generate Cache Key
   │
   ▼
Redis GET
   │
   ├── HIT ──► Deserialize Pydantic Resume
   │                │
   │                ▼
   │             Return
   │
   └── MISS
          │
          ▼
     Gemini 2.5 Flash
          │
          ▼
     Pydantic Resume
          │
          ▼
       Redis SET
          │
          ▼
        Return
```

The cache key includes:

```text
resume_extract:
    <file_hash>:
    <model_version>:
    <prompt_version>
```

For example:

```text
resume_extract:<sha256>:gemini-2.5-flash:resume_extract_v1
```

This is important because changing the resume, extraction model, or prompt automatically invalidates the previous cached result.

Cached resumes are stored as serialized Pydantic JSON.

```python
resume.model_dump_json()
```

and restored with:

```python
Resume.model_validate_json(cached_data)
```

Therefore, a cache hit returns the same application-level `Resume` object expected from fresh extraction.

---

# 🧠 Semantic Embeddings

The next stage of the pipeline generates semantic embeddings for resumes and job descriptions using:

```text
gemini-embedding-001
```

with:

```text
768 dimensions
```

The same embedding model must be used for both resumes and JDs so that the vectors exist in the same semantic vector space.

Conceptually:

```text
Resume Text
     │
     ▼
Gemini Embedding
     │
     ▼
[0.021, -0.182, 0.074, ...]
     │
     ▼
VECTOR(768)
```

and:

```text
Job Description
     │
     ▼
Gemini Embedding
     │
     ▼
[0.014, -0.164, 0.091, ...]
     │
     ▼
VECTOR(768)
```

These vectors can then be compared using cosine similarity.

---

# 🗄️ Database

The production database is hosted on **Neon PostgreSQL**.

Vector storage and similarity search use the PostgreSQL `pgvector` extension.

```sql
CREATE EXTENSION IF NOT EXISTS vector;
```

---

## Candidate Data

Candidate records are designed to contain both structured recruiter data and semantic vectors.

```text
candidates
──────────────────────────────
id
name
experience_years
skills
education
experience
projects
resume_text
embedding VECTOR(768)
```

Nested data such as education and work experience can be stored using PostgreSQL `JSONB`.

---

## Job Description Data

```text
jds
──────────────────────────────
id
title
description
required_skills
preferred_skills
minimum_experience
maximum_experience
preferred_education
responsibilities
domain
industries
embedding VECTOR(768)
```

This preserves both the original JD and its structured requirements.

---

# 🔍 Candidate Retrieval

The first ranking stage uses semantic similarity between the complete JD and resume.

```text
JD Embedding
      │
      ▼
pgvector cosine search
      │
      ▼
Candidate Embeddings
      │
      ▼
Top Matching Candidates
```

Conceptually:

```python
candidates = (
    session.query(Candidate)
    .order_by(
        Candidate.embedding.cosine_distance(
            jd.embedding
        )
    )
    .limit(10)
    .all()
)
```

This allows the system to retrieve semantically relevant candidates even when the exact wording of their resumes differs from the JD.

---

# 🚧 Evidence-Based Ranking — Next Stage

Full-document semantic similarity is useful for candidate retrieval, but it should not be the sole basis for recruitment decisions.

The next stage of the project will perform more granular comparisons.

```text
JD                         RESUME
────────────────────────────────────────

Required Skills       ↔    Skills

Preferred Skills      ↔    Skills

Responsibilities      ↔    Work Experience
                           Responsibilities

Education             ↔    Education

Experience Required   ↔    Experience Years

Domain / Industry     ↔    Experience / Projects

Full JD               ↔    Full Resume
```

Numeric requirements such as years of experience will be evaluated deterministically rather than using embeddings.

---

# 🔬 Planned Evidence Matching

Instead of simply saying:

> Candidate similarity: 82%

the system is intended to explain **why** a candidate matches.

For example:

```json
{
  "criterion": "Forecasting",
  "jd_requirement": "Experience in budgeting and forecasting",
  "resume_evidence": "Led quarterly forecasting and annual budgeting for APAC",
  "matched": true,
  "score": 0.92
}
```

A missing requirement could be represented as:

```json
{
  "criterion": "Power BI",
  "jd_requirement": "Power BI preferred",
  "resume_evidence": null,
  "matched": false,
  "score": 0.0
}
```

The objective is to prevent unsupported AI explanations.

The LLM will eventually generate recruiter-readable explanations **from retrieved evidence**, rather than freely deciding why a candidate is suitable.

---

# 🧩 Planned Hybrid Ranking Architecture

The eventual ranking pipeline is:

```text
                    JOB DESCRIPTION
                           │
                           ▼
                  Full JD Embedding
                           │
                           ▼
                Semantic Candidate Search
                           │
                           ▼
                     Top Candidates
                           │
                           ▼
              Structured Requirement Matching
                           │
              ┌────────────┼─────────────┐
              │            │             │
              ▼            ▼             ▼
            Skills    Experience    Responsibilities
              │            │             │
              └────────────┼─────────────┘
                           │
                           ▼
                    Evidence Retrieval
                           │
                           ▼
                     Weighted Score
                           │
                           ▼
                      Final Ranking
                           │
                           ▼
                  Grounded Explanation
```

This separates:

**Retrieval** — Which resumes appear relevant?

from:

**Evaluation** — How well does each candidate actually satisfy the JD?

---

# 🛠️ Technology Stack

| Layer             | Technology         |
| ----------------- | ------------------ |
| Language          | Python             |
| AI Extraction     | Gemini 2.5 Flash   |
| Embeddings        | Gemini Embedding   |
| Validation        | Pydantic           |
| ORM               | SQLAlchemy         |
| Database          | PostgreSQL         |
| Vector Database   | pgvector           |
| Cloud PostgreSQL  | Neon               |
| Cache             | Redis              |
| PDF Processing    | Python PDF tooling |
| Frontend          | Streamlit          |
| Containerization  | Docker             |
| Local Development | Docker Compose     |

---

# 📁 Project Structure

The project follows a modular architecture similar to:

```text
Manalot_rank_candidates/
│
├── app/
│   │
│   ├── services/
│   │   ├── extract_resume.py
│   │   └── embedding_service.py
│   │
│   ├── utils/
│   │   └── resume_cache.py
│   │
│   ├── database/
│   │   ├── db.py
│   │   └── models.py
│   │
│   ├── db_jd/
│   │   ├── db.py
│   │   ├── jd_models.py
│   │   └── init_db_jd.py
│   │
│   └── pdf/
│
├── streamlit_app.py
├── requirements.txt
├── docker-compose.yml
└── README.md
```

> The exact structure may evolve as the candidate-ranking and evidence layers are implemented.

---

# 🔐 Environment Variables

Sensitive credentials should never be committed to Git.

Example `.env`:

```env
GEMINI_API_KEY=your_gemini_api_key
DATABASE_URL=your_neon_postgresql_connection_string
```

For Streamlit Cloud, these should be configured through application secrets rather than committed to the repository.

---

# 🐳 Local Infrastructure

Redis and PostgreSQL can be run locally using Docker.

The local development architecture is:

```text
Application
   │
   ├── Redis
   │     └── Resume extraction cache
   │
   ├── PostgreSQL + pgvector
   │     └── Local development database
   │
   └── Gemini API
         ├── Resume/JD extraction
         └── Embeddings
```

Production database persistence uses Neon PostgreSQL.

---

# 🚀 Development Status

### Completed

* [x] PDF resume text extraction
* [x] Resume section extraction
* [x] Gemini structured resume extraction
* [x] Pydantic validation
* [x] Structured education extraction
* [x] Structured work-experience extraction
* [x] Skills extraction
* [x] Projects extraction
* [x] Experience calculation
* [x] SHA256 resume hashing
* [x] Redis cache lookup
* [x] Redis resume persistence
* [x] Cache-hit deserialization into Pydantic
* [x] Model/prompt-aware cache keys
* [x] Neon PostgreSQL connection
* [x] pgvector database design
* [x] JD structured schema

### In Progress

* [ ] Generate resume embeddings
* [ ] Store candidate embeddings in Neon
* [ ] Generate JD embeddings
* [ ] Store JD embeddings in Neon
* [ ] Perform pgvector cosine similarity search

### Planned

* [ ] Resume responsibility extraction
* [ ] Requirement-level JD embeddings
* [ ] Resume evidence/chunk embeddings
* [ ] Required-skill matching
* [ ] Preferred-skill matching
* [ ] Experience requirement scoring
* [ ] Education matching
* [ ] Responsibility matching
* [ ] Domain/industry matching
* [ ] Evidence-based candidate scoring
* [ ] Recruiter-readable candidate explanations
* [ ] Must-have requirement filtering
* [ ] Ranking calibration using recruiter outcomes
* [ ] Candidate comparison dashboard

---

# 🗺️ Development Roadmap

```text
Phase 1
Resume Extraction
      ✅
      │
Phase 2
Redis Caching
      ✅
      │
Phase 3
Resume + JD Embeddings
      🔨
      │
Phase 4
Neon + pgvector Search
      │
      ▼
Phase 5
Structured Matching
      │
      ▼
Phase 6
Evidence Retrieval
      │
      ▼
Phase 7
Hybrid Candidate Ranking
      │
      ▼
Phase 8
Grounded AI Explanations
```

---

# 💡 Design Principles

### 1. Cache expensive LLM operations

Resume extraction results are cached so unchanged resumes do not repeatedly invoke Gemini.

### 2. Separate extraction from persistence

Gemini services generate structured data and embeddings.

Database services persist them.

SQLAlchemy models describe storage.

### 3. Use embeddings for semantic information

Embeddings are appropriate for skills, responsibilities, domain knowledge, and textual similarity.

### 4. Use deterministic logic where appropriate

Numeric requirements such as years of experience should not be evaluated through embeddings.

### 5. Retrieve before explaining

The system should identify actual evidence from the resume before asking an LLM to produce an explanation.

### 6. Keep ranking explainable

Recruiters should be able to understand why one candidate ranks above another.

---

# 🎯 Long-Term Vision

The goal is not simply to build another resume similarity tool.

The target is an **evidence-based AI recruitment engine** capable of answering:

> Which candidates best match this role?

and, more importantly:

> Why does this candidate match, which JD requirements do they satisfy, what evidence supports those matches, and what important requirements are missing?

This creates a progression from:

```text
Keyword ATS
      ↓
Semantic Search
      ↓
Structured Matching
      ↓
Evidence-Based Ranking
      ↓
Explainable AI Recruitment
```

---

## Author

**Lancelot D'Souza**

Manalot Rank Candidates — AI-powered semantic candidate matching and evidence-based recruitment.
# Manalot_rank_candidates
