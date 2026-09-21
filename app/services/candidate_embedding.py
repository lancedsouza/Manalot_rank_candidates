# from pathlib import Path

# from sqlalchemy import text

# from app.database.db import (
#     SessionLocal,
#     engine,
#     Base,
# )

# from app.database.resume_models import Candidate

# from app.services.extract_resume import (
#     extract_resume_data,
#     extract_text,
# )

# from app.embedding.embedding_service import (
#     create_embedding,create_embeddings
# )


# # ============================================================
# # ENABLE PGVECTOR
# # ============================================================

# with engine.begin() as connection:
#     connection.execute(
#         text(
#             "CREATE EXTENSION IF NOT EXISTS vector"
#         )
#     )


# Base.metadata.create_all(engine)


# # ============================================================
# # RESUME DIRECTORY
# # ============================================================

# resume_path = (
#     Path(__file__).resolve().parents[2]
#     / "app"
#     / "pdf"
# )


# # ============================================================
# # PROCESS RESUMES
# # ============================================================

# for file in resume_path.glob("*.pdf"):

#     print(f"\nProcessing: {file.name}")

#     raw_text = extract_text(file)

#     structured_resume = extract_resume_data(
#         file
#     )


#     # ========================================================
#     # FULL RESUME
#     # ========================================================

#     full_embedding = create_embedding(
#         raw_text
#     )


#     # ========================================================
#     # SKILLS - AGGREGATE
#     # ========================================================

#     skills_text = " ".join(
#         structured_resume.skills
#     )

#     skills_embedding = (
#         create_embedding(skills_text)
#         if skills_text.strip()
#         else None
#     )


#     # ========================================================
#     # SKILLS - INDIVIDUAL
#     # ========================================================

#     candidate_skill_embeddings = []

#     for skill in structured_resume.skills:

#         skill = skill.strip()

#         if not skill:
#             continue

#         skill_embedding = create_embedding(
#             skill
#         )

#         candidate_skill_embeddings.append(
#             {
#                 "skill": skill,
#                 "embedding": skill_embedding,
#             }
#         )


#     # ========================================================
#     # EXPERIENCE
#     # ========================================================

#     experience_parts = []

#     for exp in structured_resume.experience:

#         parts = []

#         if exp.title:
#             parts.append(
#                 f"Title: {exp.title}"
#             )

#         if exp.company:
#             parts.append(
#                 f"Company: {exp.company}"
#             )

#         if exp.start_date:
#             parts.append(
#                 f"Start Date: {exp.start_date}"
#             )

#         if exp.end_date:
#             parts.append(
#                 f"End Date: {exp.end_date}"
#             )

#         if exp.responsibilities:

#             parts.append(
#                 "Responsibilities: "
#                 + " ".join(
#                     exp.responsibilities
#                 )
#             )

#         if parts:
#             experience_parts.append(
#                 "\n".join(parts)
#             )


#     experience_text = "\n\n".join(
#         experience_parts
#     )

#     experience_embedding = (
#         create_embedding(experience_text)
#         if experience_text.strip()
#         else None
#     )


#     # ========================================================
#     # EDUCATION
#     # ========================================================

#     education_parts = []

#     for edu in structured_resume.education:

#         parts = []

#         if edu.degree:
#             parts.append(
#                 f"Degree: {edu.degree}"
#             )

#         if edu.institution:
#             parts.append(
#                 f"Institution: {edu.institution}"
#             )

#         if edu.start_date:
#             parts.append(
#                 f"Start Date: {edu.start_date}"
#             )

#         if edu.end_date:
#             parts.append(
#                 f"End Date: {edu.end_date}"
#             )

#         if parts:
#             education_parts.append(
#                 "\n".join(parts)
#             )


#     education_text = "\n\n".join(
#         education_parts
#     )

#     education_embedding = (
#         create_embedding(education_text)
#         if education_text.strip()
#         else None
#     )


#     # ========================================================
#     # DEBUG
#     # ========================================================

#     print(
#         "Candidate:",
#         structured_resume.name
#     )

#     print(
#         "Candidate skills:",
#         len(structured_resume.skills)
#     )

#     print(
#         "Individual skill embeddings:",
#         len(candidate_skill_embeddings)
#     )

#     print(
#         "Full embedding:",
#         len(full_embedding)
#     )
#      # Individual skill embedding batchecd
#     ind_cand_skill_embedding=[]
#     valid_skills=[skill.strip()for skill in structured_resume.skills if skill and skill.strip()]
#     unique_skills=list(set(valid_skills))
#     if unique_skills:
#         ind_skill=create_embeddings(unique_skills)
#     for skill,vector in zip(unique_skills,ind_skill):
#         ind_cand_skill_embedding.append(
#             {"skill":skill,
#             "embedding":vector} 
#         )


#     # ========================================================
#     # INSERT
#     # ========================================================

#     session = SessionLocal()

#     try:

#         candidate = Candidate(

#             name=structured_resume.name,

#             experience_years=(
#                 structured_resume.experience_years
#             ),

#             skills=structured_resume.skills,

#             education=[
#                 edu.model_dump()
#                 for edu
#                 in structured_resume.education
#             ],

#             experience=[
#                 exp.model_dump()
#                 for exp
#                 in structured_resume.experience
#             ],

#             projects=structured_resume.projects,

#             resume_text=raw_text,

#             skills_text=skills_text,

#             experience_text=experience_text,

#             education_text=education_text,

#             embedding=full_embedding,

#             skills_embedding=skills_embedding,

#             experience_embedding=(
#                 experience_embedding
#             ),

#             education_embedding=(
#                 education_embedding
#             ),

#             skill_embeddings=(
#                 candidate_skill_embeddings
#             ),
#             ind_cand_skill_embedding=ind_cand_skill_embedding

#         )
       

#         session.add(candidate)

#         session.commit()

#         session.refresh(candidate)

#         print(
#             f"Candidate inserted successfully. "
#             f"ID: {candidate.id}"
#         )

#     except Exception as e:

#         session.rollback()

#         print(
#             f"Failed to insert "
#             f"{file.name}: {e}"
#         )

#         raise

#     finally:

#         session.close()


# """Code with individual skill embedings for each candidate"""
# from pathlib import Path

# from sqlalchemy import text

# from app.database.db import (
#     SessionLocal,
#     engine,
#     Base,
# )

# from app.database.resume_models import Candidate

# from app.services.extract_resume import (
#     extract_resume_data,
#     extract_text,
# )

# from app.embedding.embedding_service import (
#     create_embedding,
#     create_embeddings,
# )


# # ============================================================
# # ENABLE PGVECTOR
# # ============================================================

# with engine.begin() as connection:
#     connection.execute(
#         text(
#             "CREATE EXTENSION IF NOT EXISTS vector"
#         )
#     )


# Base.metadata.create_all(engine)


# # ============================================================
# # RESUME DIRECTORY
# # ============================================================

# resume_path = (
#     Path(__file__).resolve().parents[2]
#     / "app"
#     / "pdf"
# )


# # ============================================================
# # PROCESS RESUMES
# # ============================================================

# for file in resume_path.glob("*.pdf"):

#     print(f"\nProcessing: {file.name}")

#     raw_text = extract_text(file)

#     structured_resume = extract_resume_data(
#         file
#     )


#     # ========================================================
#     # FULL RESUME
#     # ========================================================

#     full_embedding = create_embedding(
#         raw_text
#     )


#     # ========================================================
#     # SKILLS - AGGREGATE
#     # ========================================================

#     skills_text = " ".join(
#         structured_resume.skills
#     )

#     skills_embedding = (
#         create_embedding(skills_text)
#         if skills_text.strip()
#         else None
#     )


#     # ========================================================
#     # SKILLS - INDIVIDUAL (BATCHED)
#     # ========================================================

#     ind_cand_skill_embedding = []
#     valid_skills = [
#         skill.strip()
#         for skill in structured_resume.skills
#         if skill and skill.strip()
#     ]
#     unique_skills = list(set(valid_skills))

#     if unique_skills:
#         ind_skill = create_embeddings(unique_skills)
#         for skill, vector in zip(unique_skills, ind_skill):
#             ind_cand_skill_embedding.append(
#                 {
#                     "skill": skill,
#                     "embedding": vector,
#                 }
#             )


#     # ========================================================
#     # EXPERIENCE
#     # ========================================================

#     experience_parts = []

#     for exp in structured_resume.experience:

#         parts = []

#         if exp.title:
#             parts.append(
#                 f"Title: {exp.title}"
#             )

#         if exp.company:
#             parts.append(
#                 f"Company: {exp.company}"
#             )

#         if exp.start_date:
#             parts.append(
#                 f"Start Date: {exp.start_date}"
#             )

#         if exp.end_date:
#             parts.append(
#                 f"End Date: {exp.end_date}"
#             )

#         if exp.responsibilities:

#             parts.append(
#                 "Responsibilities: "
#                 + " ".join(
#                     exp.responsibilities
#                 )
#             )

#         if parts:
#             experience_parts.append(
#                 "\n".join(parts)
#             )


#     experience_text = "\n\n".join(
#         experience_parts
#     )

#     experience_embedding = (
#         create_embedding(experience_text)
#         if experience_text.strip()
#         else None
#     )


#     # ========================================================
#     # EDUCATION
#     # ========================================================

#     education_parts = []

#     for edu in structured_resume.education:

#         parts = []

#         if edu.degree:
#             parts.append(
#                 f"Degree: {edu.degree}"
#             )

#         if edu.institution:
#             parts.append(
#                 f"Institution: {edu.institution}"
#             )

#         if edu.start_date:
#             parts.append(
#                 f"Start Date: {edu.start_date}"
#             )

#         if edu.end_date:
#             parts.append(
#                 f"End Date: {edu.end_date}"
#             )

#         if parts:
#             education_parts.append(
#                 "\n".join(parts)
#             )


#     education_text = "\n\n".join(
#         education_parts
#     )

#     education_embedding = (
#         create_embedding(education_text)
#         if education_text.strip()
#         else None
#     )


#     # ========================================================
#     # DEBUG
#     # ========================================================

#     print(
#         "Candidate:",
#         structured_resume.name
#     )

#     print(
#         "Candidate skills:",
#         len(structured_resume.skills)
#     )

#     print(
#         "Individual skill embeddings:",
#         len(ind_cand_skill_embedding)
#     )

#     print(
#         "Full embedding:",
#         len(full_embedding)
#     )


#     # ========================================================
#     # INSERT
#     # ========================================================

#     session = SessionLocal()

#     try:

#         candidate = Candidate(
#             name=structured_resume.name,
#             experience_years=(
#                 structured_resume.experience_years
#             ),
#             skills=structured_resume.skills,
#             education=[
#                 edu.model_dump()
#                 for edu
#                 in structured_resume.education
#             ],
#             experience=[
#                 exp.model_dump()
#                 for exp
#                 in structured_resume.experience
#             ],
#             projects=structured_resume.projects,
#             resume_text=raw_text,
#             skills_text=skills_text,
#             experience_text=experience_text,
#             education_text=education_text,
#             embedding=full_embedding,
#             skills_embedding=skills_embedding,
#             experience_embedding=(
#                 experience_embedding
#             ),
#             education_embedding=(
#                 education_embedding
#             ),
#             ind_cand_skill_embedding=(
#                 ind_cand_skill_embedding
#             ),
          
#         )

#         session.add(candidate)

#         session.commit()

#         session.refresh(candidate)

#         print(
#             f"Candidate inserted successfully. "
#             f"ID: {candidate.id}"
#         )

#     except Exception as e:

#         session.rollback()

#         print(
#             f"Failed to insert "
#             f"{file.name}: {e}"
#         )

#         raise

#     finally:

#         session.close()

"""Code with async to help arrest rate limit """

# import asyncio
# import time
# from pathlib import Path
# from sqlalchemy import text

# from app.database.db import (
#     SessionLocal,
#     engine,
#     Base,
# )
# from app.database.resume_models import Candidate
# from app.services.extract_resume import (
#     extract_resume_data,
#     extract_text,
# )
# from app.embedding.embedding_service import (
#     create_embedding,
#     create_embeddings,
# )

# # ============================================================
# # ENABLE PGVECTOR & CREATE TABLES
# # ============================================================

# with engine.begin() as connection:
#     connection.execute(
#         text("CREATE EXTENSION IF NOT EXISTS vector")
#     )

# Base.metadata.create_all(engine)

# # ============================================================
# # RESUME DIRECTORY CONFIGURATION
# # ============================================================

# RESUME_PATH = (
#     Path(__file__).resolve().parents[2]
#     / "app"
#     / "pdf"
# )

# # Concurrency & Rate Limiting Control (Semaphore = 2 to stay safely under API rate limits)
# SEM_LIMIT = 2
# semaphore = asyncio.Semaphore(SEM_LIMIT)


# async def process_resume(file: Path):
#     async with semaphore:
#         print(f"\nProcessing: {file.name}")
        
#         # Polite delay to space out API requests and protect free-tier limits
#         await asyncio.sleep(3)

#         # Extract text and structured layout (running synchronously or via executor if heavy)
#         raw_text = extract_text(file)
#         structured_resume = extract_resume_data(file)

#         # ========================================================
#         # 1. FULL RESUME EMBEDDING
#         # ========================================================
#         full_embedding = create_embedding(raw_text)

#         # ========================================================
#         # 2. SKILLS - AGGREGATE EMBEDDING
#         # ========================================================
#         skills_text = " ".join(structured_resume.skills)
#         skills_embedding = (
#             create_embedding(skills_text)
#             if skills_text.strip()
#             else None
#         )

#         # ========================================================
#         # 3. SKILLS - INDIVIDUAL (BATCHED IN ONE API CALL)
#         # ========================================================
#         ind_cand_skill_embedding = []
#         valid_skills = [
#             skill.strip()
#             for skill in structured_resume.skills
#             if skill and skill.strip()
#         ]
#         unique_skills = list(set(valid_skills))

#         if unique_skills:
#             # Batch request all unique skill vectors at once
#             ind_skill_vectors = create_embeddings(unique_skills)
#             for skill, vector in zip(unique_skills, ind_skill_vectors):
#                 ind_cand_skill_embedding.append(
#                     {
#                         "skill": skill,
#                         "embedding": vector,
#                     }
#                 )

#         # ========================================================
#         # 4. EXPERIENCE FORMATTING & EMBEDDING
#         # ========================================================
#         experience_parts = []
#         for exp in structured_resume.experience:
#             parts = []
#             if exp.title:
#                 parts.append(f"Title: {exp.title}")
#             if exp.company:
#                 parts.append(f"Company: {exp.company}")
#             if exp.start_date:
#                 parts.append(f"Start Date: {exp.start_date}")
#             if exp.end_date:
#                 parts.append(f"End Date: {exp.end_date}")
#             if exp.responsibilities:
#                 parts.append("Responsibilities: " + " ".join(exp.responsibilities))
#             if parts:
#                 experience_parts.append("\n".join(parts))

#         experience_text = "\n\n".join(experience_parts)
#         experience_embedding = (
#             create_embedding(experience_text)
#             if experience_text.strip()
#             else None
#         )

#         # ========================================================
#         # 5. EDUCATION FORMATTING & EMBEDDING
#         # ========================================================
#         education_parts = []
#         for edu in structured_resume.education:
#             parts = []
#             if edu.degree:
#                 parts.append(f"Degree: {edu.degree}")
#             if edu.institution:
#                 parts.append(f"Institution: {edu.institution}")
#             if edu.start_date:
#                 parts.append(f"Start Date: {edu.start_date}")
#             if edu.end_date:
#                 parts.append(f"End Date: {edu.end_date}")
#             if parts:
#                 education_parts.append("\n".join(parts))

#         education_text = "\n\n".join(education_parts)
#         education_embedding = (
#             create_embedding(education_text)
#             if education_text.strip()
#             else None
#         )

#         # ========================================================
#         # 6. DEBUG LOGS
#         # ========================================================
#         print(f"Candidate: {structured_resume.name}")
#         print(f"Candidate skills found: {len(structured_resume.skills)}")
#         print(f"Individual skill embeddings batched: {len(ind_cand_skill_embedding)}")
#         print(f"Full embedding vector length: {len(full_embedding)}")

#         # ========================================================
#         # 7. DATABASE INSERTION
#         # ========================================================
#         session = SessionLocal()
#         try:
#             candidate = Candidate(
#                 name=structured_resume.name,
#                 experience_years=structured_resume.experience_years,
#                 skills=structured_resume.skills,
#                 education=[edu.model_dump() for edu in structured_resume.education],
#                 experience=[exp.model_dump() for exp in structured_resume.experience],
#                 projects=structured_resume.projects,
#                 resume_text=raw_text,
#                 skills_text=skills_text,
#                 experience_text=experience_text,
#                 education_text=education_text,
#                 embedding=full_embedding,
#                 skills_embedding=skills_embedding,
#                 experience_embedding=experience_embedding,
#                 education_embedding=education_embedding,
#                 ind_cand_skill_embedding=ind_cand_skill_embedding,
#             )

#             session.add(candidate)
#             session.commit()
#             session.refresh(candidate)

#             print(f"Candidate inserted successfully. ID: {candidate.id}")

#         except Exception as e:
#             session.rollback()
#             print(f"Failed to insert {file.name}: {e}")
#             raise
#         finally:
#             session.close()


# async def main():
#     pdf_files = list(RESUME_PATH.glob("*.pdf"))
#     if not pdf_files:
#         print(f"No PDF resumes found in {RESUME_PATH}")
#         return

#     # Run processing tasks concurrently with semaphore rate protection
#     tasks = [process_resume(file) for file in pdf_files]
#     await asyncio.gather(*tasks)


# if __name__ == "__main__":
#     asyncio.run(main())


# import time
# from pathlib import Path
# from sqlalchemy import text

# from app.database.db import SessionLocal, engine, Base
# from app.database.resume_models import Candidate
# from app.services.extract_resume import extract_resume_data, extract_text
# from app.embedding.embedding_service import create_embedding, create_embeddings

# # Enable pgvector & create tables
# with engine.begin() as connection:
#     connection.execute(text("CREATE EXTENSION IF NOT EXISTS vector"))

# Base.metadata.create_all(engine)

# RESUME_PATH = Path(__file__).resolve().parents[2] / "app" / "pdf"

# def process_resumes():
#     pdf_files = list(RESUME_PATH.glob("*.pdf"))
#     if not pdf_files:
#         print(f"No PDF resumes found in {RESUME_PATH}")
#         return

#     for file in pdf_files:
#         print(f"\nProcessing: {file.name}")

#         raw_text = extract_text(file)
#         structured_resume = extract_resume_data(file)

#         # 1. Full Resume Embedding
#         full_embedding = create_embedding(raw_text)

#         # 2. Skills - Aggregate Embedding
#         skills_text = " ".join(structured_resume.skills)
#         skills_embedding = create_embedding(skills_text) if skills_text.strip() else None

#         # 3. Skills - Individual (Batched)
#         ind_cand_skill_embedding = []
#         valid_skills = [s.strip() for s in structured_resume.skills if s and s.strip()]
#         unique_skills = list(set(valid_skills))

#         if unique_skills:
#             ind_skill_vectors = create_embeddings(unique_skills)
#             for skill, vector in zip(unique_skills, ind_skill_vectors):
#                 ind_cand_skill_embedding.append({
#                     "skill": skill,
#                     "embedding": vector,
#                 })

#         # 4. Experience Formatting & Embedding
#         experience_parts = []
#         for exp in structured_resume.experience:
#             parts = []
#             if exp.title: parts.append(f"Title: {exp.title}")
#             if exp.company: parts.append(f"Company: {exp.company}")
#             if exp.start_date: parts.append(f"Start Date: {exp.start_date}")
#             if exp.end_date: parts.append(f"End Date: {exp.end_date}")
#             if exp.responsibilities: parts.append("Responsibilities: " + " ".join(exp.responsibilities))
#             if parts: experience_parts.append("\n".join(parts))

#         experience_text = "\n\n".join(experience_parts)
#         experience_embedding = create_embedding(experience_text) if experience_text.strip() else None

#         # 5. Education Formatting & Embedding
#         education_parts = []
#         for edu in structured_resume.education:
#             parts = []
#             if edu.degree: parts.append(f"Degree: {edu.degree}")
#             if edu.institution: parts.append(f"Institution: {edu.institution}")
#             if edu.start_date: parts.append(f"Start Date: {edu.start_date}")
#             if edu.end_date: parts.append(f"End Date: {edu.end_date}")
#             if parts: education_parts.append("\n".join(parts))

#         education_text = "\n\n".join(education_parts)
#         education_embedding = create_embedding(education_text) if education_text.strip() else None

#         print(f"Candidate: {structured_resume.name}")
#         print(f"Skills found: {len(unique_skills)} | Full embedding length: {len(full_embedding)}")

#         # 6. Database Insertion
#         session = SessionLocal()
#         try:
#             candidate = Candidate(
#                 name=structured_resume.name,
#                 experience_years=structured_resume.experience_years,
#                 skills=structured_resume.skills,
#                 education=[edu.model_dump() for edu in structured_resume.education],
#                 experience=[exp.model_dump() for exp in structured_resume.experience],
#                 projects=structured_resume.projects,
#                 resume_text=raw_text,
#                 skills_text=skills_text,
#                 experience_text=experience_text,
#                 education_text=education_text,
#                 embedding=full_embedding,
#                 skills_embedding=skills_embedding,
#                 experience_embedding=experience_embedding,
#                 education_embedding=education_embedding,
#                 ind_cand_skill_embedding=ind_cand_skill_embedding,
#             )

#             session.add(candidate)
#             session.commit()
#             session.refresh(candidate)
#             print(f"Candidate inserted successfully. ID: {candidate.id}")

#         except Exception as e:
#             session.rollback()
#             print(f"Failed to insert {file.name}: {e}")
#             raise
#         finally:
#             session.close()

#         # Polite cooldown buffer between files to protect free-tier rate limits (100 RPM)
#         print("Cooling down for 5 seconds to respect API quota limits...")
#         time.sleep(5)

# if __name__ == "__main__":
#     process_resumes()


# import time
# from pathlib import Path
# from sqlalchemy import text

# from app.database.db import SessionLocal, engine, Base
# from app.database.resume_models import Candidate
# from app.services.extract_resume import extract_resume_data, extract_text
# from app.embedding.embedding_service import create_embeddings

# # ============================================================
# # ENABLE PGVECTOR & CREATE TABLES
# # ============================================================

# with engine.begin() as connection:
#     connection.execute(text("CREATE EXTENSION IF NOT EXISTS vector"))

# Base.metadata.create_all(engine)

# # ============================================================
# # RESUME DIRECTORY CONFIGURATION
# # ============================================================

# RESUME_PATH = (
#     Path(__file__).resolve().parents[2]
#     / "app"
#     / "pdf"
# )

# def process_resumes():
#     pdf_files = list(RESUME_PATH.glob("*.pdf"))
#     if not pdf_files:
#         print(f"No PDF resumes found in {RESUME_PATH}")
#         return

#     for file in pdf_files:
#         print(f"\nProcessing: {file.name}")

#         raw_text = extract_text(file)
#         structured_resume = extract_resume_data(file)

#         # 1. Aggregate Skills Text
#         skills_text = " ".join(structured_resume.skills) if structured_resume.skills else ""

#         # 2. Experience Text Formatting
#         experience_parts = []
#         for exp in structured_resume.experience:
#             parts = []
#             if exp.title: parts.append(f"Title: {exp.title}")
#             if exp.company: parts.append(f"Company: {exp.company}")
#             if exp.start_date: parts.append(f"Start Date: {exp.start_date}")
#             if exp.end_date: parts.append(f"End Date: {exp.end_date}")
#             if exp.responsibilities: parts.append("Responsibilities: " + " ".join(exp.responsibilities))
#             if parts: experience_parts.append("\n".join(parts))
#         experience_text = "\n\n".join(experience_parts)

#         # 3. Education Text Formatting
#         education_parts = []
#         for edu in structured_resume.education:
#             parts = []
#             if edu.degree: parts.append(f"Degree: {edu.degree}")
#             if edu.institution: parts.append(f"Institution: {edu.institution}")
#             if edu.start_date: parts.append(f"Start Date: {edu.start_date}")
#             if edu.end_date: parts.append(f"End Date: {edu.end_date}")
#             if parts: education_parts.append("\n".join(parts))
#         education_text = "\n\n".join(education_parts)

#         # 4. Unique Individual Skills Preparation
#         valid_skills = [s.strip() for s in structured_resume.skills if s and s.strip()]
#         unique_skills = list(set(valid_skills))

#         # ========================================================
#         # 5. CONSOLIDATED SINGLE BATCH EMBEDDING CALL PER RESUME
#         # ========================================================
#         # Mapping layout for the bulk list:
#         # Index 0: Full Resume Text
#         # Index 1: Skills Text Aggregate
#         # Index 2: Experience Text
#         # Index 3: Education Text
#         # Index 4+: Individual Unique Skills
        
#         texts_to_embed = [
#             raw_text,
#             skills_text if skills_text.strip() else " ",
#             experience_text if experience_text.strip() else " ",
#             education_text if education_text.strip() else " "
#         ]
#         texts_to_embed.extend(unique_skills)

#         print(f"Sending 1 consolidated batch request for {len(texts_to_embed)} text payloads...")
#         all_vectors = create_embeddings(texts_to_embed)

#         # Unpack results securely by index position
#         full_embedding = all_vectors[0]
#         skills_embedding = all_vectors[1] if skills_text.strip() else None
#         experience_embedding = all_vectors[2] if experience_text.strip() else None
#         education_embedding = all_vectors[3] if education_text.strip() else None

#         # Unpack individual skill vectors starting from index 4
#         ind_cand_skill_embedding = []
#         skill_vectors = all_vectors[4:]
#         for skill, vector in zip(unique_skills, skill_vectors):
#             ind_cand_skill_embedding.append({
#                 "skill": skill,
#                 "embedding": vector,
#             })

#         print(f"Candidate: {structured_resume.name}")
#         print(f"Unique skills mapped: {len(unique_skills)} | Full vector length: {len(full_embedding)}")

#         # ========================================================
#         # 6. DATABASE INSERTION
#         # ========================================================
#         session = SessionLocal()
#         try:
#             candidate = Candidate(
#                 name=structured_resume.name,
#                 experience_years=structured_resume.experience_years,
#                 skills=structured_resume.skills,
#                 education=[edu.model_dump() for edu in structured_resume.education],
#                 experience=[exp.model_dump() for exp in structured_resume.experience],
#                 projects=structured_resume.projects,
#                 resume_text=raw_text,
#                 skills_text=skills_text,
#                 experience_text=experience_text,
#                 education_text=education_text,
#                 embedding=full_embedding,
#                 skills_embedding=skills_embedding,
#                 experience_embedding=experience_embedding,
#                 education_embedding=education_embedding,
#                 ind_cand_skill_embedding=ind_cand_skill_embedding,
#             )

#             session.add(candidate)
#             session.commit()
#             session.refresh(candidate)
#             print(f"Candidate inserted successfully. ID: {candidate.id}")

#         except Exception as e:
#             session.rollback()
#             print(f"Failed to insert {file.name}: {e}")
#             raise
#         finally:
#             session.close()

#         # Polite 10-second cooldown buffer between files to protect free-tier rate limits (100 RPM)
#         print("Cooling down for 10 seconds to respect API quota limits...")
#         time.sleep(10)

# if __name__ == "__main__":
#     process_resumes()

# import time
# from pathlib import Path
# from sqlalchemy import text

# from app.database.db import SessionLocal, engine, Base
# from app.database.resume_models import Candidate
# from app.services.extract_resume import extract_resume_data, extract_text
# from app.embedding.embedding_service import create_embeddings

# # ============================================================
# # ENABLE PGVECTOR & CREATE TABLES
# # ============================================================

# with engine.begin() as connection:
#     connection.execute(text("CREATE EXTENSION IF NOT EXISTS vector"))

# Base.metadata.create_all(engine)

# # ============================================================
# # RESUME DIRECTORY CONFIGURATION
# # ============================================================

# RESUME_PATH = (
#     Path(__file__).resolve().parents[2]
#     / "app"
#     / "pdf"
# )

# def chunk_list(lst, chunk_size=50):
#     """Yield successive chunks from lst of specified size to stay under API batch limits."""
#     for i in range(0, len(lst), chunk_size):
#         yield lst[i:i + chunk_size]

# def process_resumes():
#     pdf_files = list(RESUME_PATH.glob("*.pdf"))
#     if not pdf_files:
#         print(f"No PDF resumes found in {RESUME_PATH}")
#         return

#     for file in pdf_files:
#         print(f"\nProcessing: {file.name}")

#         raw_text = extract_text(file)
#         structured_resume = extract_resume_data(file)

#         # 1. Aggregate Skills Text
#         skills_text = " ".join(structured_resume.skills) if structured_resume.skills else ""

#         # 2. Experience Text Formatting
#         experience_parts = []
#         for exp in structured_resume.experience:
#             parts = []
#             if exp.title: parts.append(f"Title: {exp.title}")
#             if exp.company: parts.append(f"Company: {exp.company}")
#             if exp.start_date: parts.append(f"Start Date: {exp.start_date}")
#             if exp.end_date: parts.append(f"End Date: {exp.end_date}")
#             if exp.responsibilities: parts.append("Responsibilities: " + " ".join(exp.responsibilities))
#             if parts: experience_parts.append("\n".join(parts))
#         experience_text = "\n\n".join(experience_parts)

#         # 3. Education Text Formatting
#         education_parts = []
#         for edu in structured_resume.education:
#             parts = []
#             if edu.degree: parts.append(f"Degree: {edu.degree}")
#             if edu.institution: parts.append(f"Institution: {edu.institution}")
#             if edu.start_date: parts.append(f"Start Date: {edu.start_date}")
#             if edu.end_date: parts.append(f"End Date: {edu.end_date}")
#             if parts: education_parts.append("\n".join(parts))
#         education_text = "\n\n".join(education_parts)

#         # ========================================================
#         # 4. EMBEDDING LARGE STRUCTURAL TEXTS (Batch 1)
#         # ========================================================
#         structural_texts = [
#             raw_text,
#             skills_text if skills_text.strip() else " ",
#             experience_text if experience_text.strip() else " ",
#             education_text if education_text.strip() else " "
#         ]
        
#         print("Embedding structural resume texts...")
#         struct_vectors = create_embeddings(structural_texts)
        
#         full_embedding = struct_vectors[0]
#         skills_embedding = struct_vectors[1] if skills_text.strip() else None
#         experience_embedding = struct_vectors[2] if experience_text.strip() else None
#         education_embedding = struct_vectors[3] if education_text.strip() else None

#         # ========================================================
#         # 5. EMBEDDING UNIQUE SKILLS IN SAFE CHUNKS (Batch 2+)
#         # ========================================================
#         valid_skills = [s.strip() for s in structured_resume.skills if s and s.strip()]
#         unique_skills = list(set(valid_skills))
        
#         ind_cand_skill_embedding = []
#         if unique_skills:
#             print(f"Embedding {len(unique_skills)} unique skills in chunks of 50...")
#             for chunk in chunk_list(unique_skills, chunk_size=50):
#                 chunk_vectors = create_embeddings(chunk)
#                 for skill, vector in zip(chunk, chunk_vectors):
#                     ind_cand_skill_embedding.append({
#                         "skill": skill,
#                         "embedding": vector,
#                     })

#         print(f"Candidate: {structured_resume.name}")
#         print(f"Unique skills mapped: {len(ind_cand_skill_embedding)} | Full vector length: {len(full_embedding)}")

#         # ========================================================
#         # 6. DATABASE INSERTION
#         # ========================================================
#         session = SessionLocal()
#         try:
#             candidate = Candidate(
#                 name=structured_resume.name,
#                 experience_years=structured_resume.experience_years,
#                 skills=structured_resume.skills,
#                 education=[edu.model_dump() for edu in structured_resume.education],
#                 experience=[exp.model_dump() for exp in structured_resume.experience],
#                 projects=structured_resume.projects,
#                 resume_text=raw_text,
#                 skills_text=skills_text,
#                 experience_text=experience_text,
#                 education_text=education_text,
#                 embedding=full_embedding,
#                 skills_embedding=skills_embedding,
#                 experience_embedding=experience_embedding,
#                 education_embedding=education_embedding,
#                 ind_cand_skill_embedding=ind_cand_skill_embedding,
#             )

#             session.add(candidate)
#             session.commit()
#             session.refresh(candidate)
#             print(f"Candidate inserted successfully. ID: {candidate.id}")

#         except Exception as e:
#             session.rollback()
#             print(f"Failed to insert {file.name}: {e}")
#             raise
#         finally:
#             session.close()

#         # Polite cooldown buffer between files to protect free-tier rate limits (100 RPM)
#         print("Cooling down for 10 seconds to respect API quota limits...")
#         time.sleep(10)

# if __name__ == "__main__":
#     process_resumes()

# from pathlib import Path

# from sqlalchemy import text

# from app.database.db import SessionLocal, engine, Base
# from app.database.resume_models import Candidate

# from app.services.extract_resume import (
#     extract_resume_data,
#     extract_text,
# )

# from app.embedding.embedding_service import create_embedding


# # ============================================================
# # ENABLE PGVECTOR
# # ============================================================

# with engine.begin() as connection:
#     connection.execute(
#         text("CREATE EXTENSION IF NOT EXISTS vector")
#     )


# # ============================================================
# # CREATE TABLES
# # ============================================================

# Base.metadata.create_all(engine)


# # ============================================================
# # RESUME DIRECTORY
# # ============================================================

# resume_path = (
#     Path(__file__).resolve().parents[2]
#     / "app"
#     / "pdf"
# )


# # ============================================================
# # PROCESS EACH PDF
# # ============================================================

# for file in resume_path.glob("*.pdf"):

#     print("\n========================================")
#     print(f"Processing: {file.name}")
#     print("========================================")


#     # ========================================================
#     # EXTRACT RESUME
#     # ========================================================

#     raw_text = extract_text(file)

#     structured_resume = extract_resume_data(file)


#     # ========================================================
#     # FULL RESUME EMBEDDING
#     # ========================================================

#     full_embedding = (
#         create_embedding(raw_text)
#         if raw_text and raw_text.strip()
#         else None
#     )


#     # ========================================================
#     # COMBINED SKILLS TEXT + EMBEDDING
#     # ========================================================

#     skills_text = " ".join(
#         structured_resume.skills
#     ).strip()

#     skills_embedding = (
#         create_embedding(skills_text)
#         if skills_text
#         else None
#     )


#     # ========================================================
#     # INDIVIDUAL SKILL EMBEDDINGS
#     # ========================================================

#     candidate_skill_embeddings = []

#     for skill in structured_resume.skills:

#         skill = skill.strip()

#         if not skill:
#             continue

#         print(
#             f"Creating embedding for skill: {skill}"
#         )

#         skill_embedding = create_embedding(
#             skill
#         )

#         candidate_skill_embeddings.append(
#             {
#                 "skill": skill,
#                 "embedding": skill_embedding,
#             }
#         )


#     # ========================================================
#     # EXPERIENCE TEXT
#     # ========================================================

#     experience_parts = []

#     for exp in structured_resume.experience:

#         parts = []

#         if exp.title:
#             parts.append(
#                 f"Title: {exp.title}"
#             )

#         if exp.company:
#             parts.append(
#                 f"Company: {exp.company}"
#             )

#         if exp.start_date:
#             parts.append(
#                 f"Start Date: {exp.start_date}"
#             )

#         if exp.end_date:
#             parts.append(
#                 f"End Date: {exp.end_date}"
#             )

#         if exp.responsibilities:

#             parts.append(
#                 "Responsibilities: "
#                 + " ".join(
#                     exp.responsibilities
#                 )
#             )

#         if parts:

#             experience_parts.append(
#                 "\n".join(parts)
#             )


#     experience_text = "\n\n".join(
#         experience_parts
#     ).strip()


#     # ========================================================
#     # EXPERIENCE EMBEDDING
#     # ========================================================

#     experience_embedding = (
#         create_embedding(experience_text)
#         if experience_text
#         else None
#     )


#     # ========================================================
#     # EDUCATION TEXT
#     # ========================================================

#     education_parts = []

#     for edu in structured_resume.education:

#         parts = []

#         if edu.degree:

#             parts.append(
#                 f"Degree: {edu.degree}"
#             )

#         if edu.institution:

#             parts.append(
#                 f"Institution: {edu.institution}"
#             )

#         if edu.start_date:

#             parts.append(
#                 f"Start Date: {edu.start_date}"
#             )

#         if edu.end_date:

#             parts.append(
#                 f"End Date: {edu.end_date}"
#             )

#         if parts:

#             education_parts.append(
#                 "\n".join(parts)
#             )


#     education_text = "\n\n".join(
#         education_parts
#     ).strip()


#     # ========================================================
#     # EDUCATION EMBEDDING
#     # ========================================================

#     education_embedding = (
#         create_embedding(education_text)
#         if education_text
#         else None
#     )


#     # ========================================================
#     # DEBUG
#     # ========================================================

#     print("\n--- CANDIDATE EMBEDDING DEBUG ---")

#     print(
#         "Candidate:",
#         structured_resume.name
#     )

#     print(
#         "Experience years:",
#         structured_resume.experience_years
#     )

#     print(
#         "Skills:",
#         structured_resume.skills
#     )

#     print(
#         "Number of individual skill embeddings:",
#         len(candidate_skill_embeddings)
#     )

#     print(
#         "Full embedding:",
#         len(full_embedding)
#         if full_embedding is not None
#         else None
#     )

#     print(
#         "Skills embedding:",
#         len(skills_embedding)
#         if skills_embedding is not None
#         else None
#     )

#     print(
#         "Experience embedding:",
#         len(experience_embedding)
#         if experience_embedding is not None
#         else None
#     )

#     print(
#         "Education embedding:",
#         len(education_embedding)
#         if education_embedding is not None
#         else None
#     )


#     # ========================================================
#     # DATABASE SESSION
#     # ========================================================

#     session = SessionLocal()

#     try:

#         # ====================================================
#         # CREATE CANDIDATE
#         # ====================================================

#         candidate = Candidate(

#             name=structured_resume.name,

#             experience_years=(
#                 structured_resume.experience_years
#             ),


#             # =================================================
#             # STRUCTURED DATA
#             # =================================================

#             skills=structured_resume.skills,

#             education=[
#                 edu.model_dump()
#                 for edu in structured_resume.education
#             ],

#             experience=[
#                 exp.model_dump()
#                 for exp in structured_resume.experience
#             ],

#             projects=structured_resume.projects,


#             # =================================================
#             # TEXT USED FOR EMBEDDINGS
#             # =================================================

#             resume_text=raw_text,

#             skills_text=skills_text,

#             experience_text=experience_text,

#             education_text=education_text,


#             # =================================================
#             # FIELD EMBEDDINGS
#             # =================================================

#             embedding=full_embedding,

#             skills_embedding=skills_embedding,

#             experience_embedding=experience_embedding,

#             education_embedding=education_embedding,


#             # =================================================
#             # INDIVIDUAL SKILL EMBEDDINGS
#             # =================================================

#             skill_embeddings=(
#                 candidate_skill_embeddings
#             ),
#         )


#         # ====================================================
#         # INSERT
#         # ====================================================

#         session.add(candidate)

#         session.commit()

#         session.refresh(candidate)


#         print(
#             f"\nCandidate inserted successfully."
#             f" ID: {candidate.id}"
#         )


#     except Exception as e:

#         session.rollback()

#         print(
#             f"\nFailed to insert "
#             f"{file.name}: {e}"
#         )


#     finally:

#         session.close()
# from pathlib import Path

# from sqlalchemy import text

# from app.database.db import SessionLocal, engine, Base
# from app.database.resume_models import Candidate

# from app.services.extract_resume import (
#     extract_resume_data,
#     extract_text,
# )

# from app.embedding.embedding_service import create_embedding


# # ============================================================
# # ENABLE PGVECTOR
# # ============================================================

# with engine.begin() as connection:
#     connection.execute(
#         text("CREATE EXTENSION IF NOT EXISTS vector")
#     )


# # ============================================================
# # CREATE TABLES
# # ============================================================
# Base.metadata.delete_all(engine)
# Base.metadata.create_all(engine)


# # ============================================================
# # RESUME DIRECTORY
# # ============================================================

# resume_path = (
#     Path(__file__).resolve().parents[2]
#     / "app"
#     / "pdf"
# )


# # ============================================================
# # PROCESS EACH PDF
# # ============================================================

# for file in resume_path.glob("*.pdf"):

#     print("\n========================================")
#     print(f"Processing: {file.name}")
#     print("========================================")

#     try:

#         # ====================================================
#         # EXTRACT RESUME
#         # ====================================================

#         raw_text = extract_text(file)

#         structured_resume = extract_resume_data(file)


#         # ====================================================
#         # FULL RESUME EMBEDDING
#         # ====================================================

#         full_embedding = (
#             create_embedding(raw_text)
#             if raw_text and raw_text.strip()
#             else None
#         )


#         # ====================================================
#         # COMBINED SKILLS TEXT + EMBEDDING
#         # ====================================================

#         skills_text = " ".join(
#             structured_resume.skills
#         )

#         skills_embedding = (
#             create_embedding(skills_text)
#             if skills_text.strip()
#             else None
#         )


#         #
#         # ====================================================
#         # EXPERIENCE TEXT
#         # ====================================================

#         experience_parts = []

#         for exp in structured_resume.experience:

#             parts = []

#             if exp.title:
#                 parts.append(
#                     f"Title: {exp.title}"
#                 )

#             if exp.company:
#                 parts.append(
#                     f"Company: {exp.company}"
#                 )

#             if exp.start_date:
#                 parts.append(
#                     f"Start Date: {exp.start_date}"
#                 )

#             if exp.end_date:
#                 parts.append(
#                     f"End Date: {exp.end_date}"
#                 )

#             if exp.responsibilities:

#                 responsibilities_text = " ".join(
#                     exp.responsibilities
#                 )

#                 parts.append(
#                     f"Responsibilities: "
#                     f"{responsibilities_text}"
#                 )

#             if parts:

#                 experience_parts.append(
#                     "\n".join(parts)
#                 )


#         experience_text = "\n\n".join(
#             experience_parts
#         )


#         # ====================================================
#         # EXPERIENCE EMBEDDING
#         # ====================================================

#         experience_embedding = (
#             create_embedding(experience_text)
#             if experience_text.strip()
#             else None
#         )


#         # ====================================================
#         # EDUCATION TEXT
#         # ====================================================

#         education_parts = []

#         for edu in structured_resume.education:

#             parts = []

#             if edu.degree:
#                 parts.append(
#                     f"Degree: {edu.degree}"
#                 )

#             if edu.institution:
#                 parts.append(
#                     f"Institution: {edu.institution}"
#                 )

#             if edu.start_date:
#                 parts.append(
#                     f"Start Date: {edu.start_date}"
#                 )

#             if edu.end_date:
#                 parts.append(
#                     f"End Date: {edu.end_date}"
#                 )

#             if parts:

#                 education_parts.append(
#                     "\n".join(parts)
#                 )


#         education_text = "\n\n".join(
#             education_parts
#         )


#         # ====================================================
#         # EDUCATION EMBEDDING
#         # ====================================================

#         education_embedding = (
#             create_embedding(education_text)
#             if education_text.strip()
#             else None
#         )


#         # ====================================================
#         # DEBUG
#         # ====================================================

#         print("\n--- CANDIDATE EMBEDDING DEBUG ---")

#         print(
#             "Candidate:",
#             structured_resume.name
#         )

#         print(
#             "Experience years:",
#             structured_resume.experience_years
#         )

#         print(
#             "Number of skills:",
#             len(structured_resume.skills)
#         )

#         print(
#             "Individual skill embeddings:",
#             len(candidate_skill_embeddings)
#         )

#         print(
#             "Full embedding:",
#             len(full_embedding)
#             if full_embedding is not None
#             else None
#         )

#         print(
#             "Combined skills embedding:",
#             len(skills_embedding)
#             if skills_embedding is not None
#             else None
#         )

#         print(
#             "Experience embedding:",
#             len(experience_embedding)
#             if experience_embedding is not None
#             else None
#         )

#         print(
#             "Education embedding:",
#             len(education_embedding)
#             if education_embedding is not None
#             else None
#         )


#         # ====================================================
#         # DATABASE INSERT
#         # ====================================================

#         session = SessionLocal()

#         try:

#             candidate = Candidate(

#                 # ============================================
#                 # BASIC DATA
#                 # ============================================

#                 name=structured_resume.name,

#                 experience_years=(
#                     structured_resume.experience_years
#                 ),


#                 # ============================================
#                 # STRUCTURED DATA
#                 # ============================================

#                 skills=structured_resume.skills,

#                 education=[
#                     edu.model_dump()
#                     for edu
#                     in structured_resume.education
#                 ],

#                 experience=[
#                     exp.model_dump()
#                     for exp
#                     in structured_resume.experience
#                 ],

#                 projects=structured_resume.projects,


#                 # ============================================
#                 # TEXT USED FOR EMBEDDINGS
#                 # ============================================

#                 resume_text=raw_text,

#                 skills_text=skills_text,

#                 experience_text=experience_text,

#                 education_text=education_text,


#                 # ============================================
#                 # COMBINED EMBEDDINGS
#                 # ============================================

#                 embedding=full_embedding,

#                 skills_embedding=skills_embedding,

#                 experience_embedding=experience_embedding,

#                 education_embedding=education_embedding,


#                 # ============================================
#                 # INDIVIDUAL SKILL EMBEDDINGS
#                 # ============================================

#                 skill_embeddings=(
#                     candidate_skill_embeddings
#                 ),
#             )


#             session.add(candidate)

#             session.commit()

#             session.refresh(candidate)


#             print(
#                 f"\nCandidate inserted successfully."
#             )

#             print(
#                 f"Candidate ID: {candidate.id}"
#             )

#             print(
#                 f"Candidate Name: {candidate.name}"
#             )


#         except Exception as e:

#             session.rollback()

#             print(
#                 f"\nFailed to insert "
#                 f"{file.name}: {e}"
#             )

#             raise


#         finally:

#             session.close()


#     except Exception as e:

#         print(
#             f"\nFailed processing "
#             f"{file.name}: {e}"
#         )

#         continue


# print("\n========================================")
# print("Candidate ingestion completed")
# print("========================================")
from pathlib import Path
import time
import logging
from sqlalchemy import text

from app.database.db import SessionLocal, engine, Base
from app.database.resume_models import Candidate
from app.services.extract_resume import extract_text
from app.utils.resume_cache import process_resume
from app.embedding.embedding_service import create_embeddings

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# ============================================================
# ENABLE PGVECTOR & CREATE TABLES
# ============================================================
with engine.begin() as connection:
    connection.execute(text("CREATE EXTENSION IF NOT EXISTS vector"))

Base.metadata.create_all(engine)

# ============================================================
# RESUME DIRECTORY
# ============================================================
resume_path = Path(__file__).resolve().parents[2] / "app" / "pdf"


# ============================================================
# PROCESS EACH PDF (PARENT CANDIDATE PASS)
# ============================================================
for file in resume_path.glob("*.pdf"):
    print("\n========================================")
    print(f"Processing: {file.name}")
    print("========================================")

    session = SessionLocal()
    try:
        # 1. Parse raw text and structured data
        raw_text = extract_text(file)
        structured_resume = process_resume(file)

        # 2. Checkpoint check: skip if candidate already exists in Neon
        existing_name = session.query(Candidate.name).filter_by(name=structured_resume.name).scalar()
        if existing_name:
            logger.info(f"Candidate '{structured_resume.name}' already exists in database. Skipping {file.name}.")
            session.close()
            continue

        # 3. Prepare structural text blocks
        skills_text = " ".join(structured_resume.skills) if structured_resume.skills else ""

        experience_parts = []
        for exp in structured_resume.experience:
            parts = []
            if exp.title: parts.append(f"Title: {exp.title}")
            if exp.company: parts.append(f"Company: {exp.company}")
            if exp.start_date: parts.append(f"Start Date: {exp.start_date}")
            if exp.end_date: parts.append(f"End Date: {exp.end_date}")
            if exp.responsibilities:
                parts.append(f"Responsibilities: {' '.join(exp.responsibilities)}")
            if parts:
                experience_parts.append("\n".join(parts))
        experience_text = "\n\n".join(experience_parts)

        education_parts = []
        for edu in structured_resume.education:
            parts = []
            if edu.degree: parts.append(f"Degree: {edu.degree}")
            if edu.institution: parts.append(f"Institution: {edu.institution}")
            if edu.start_date: parts.append(f"Start Date: {edu.start_date}")
            if edu.end_date: parts.append(f"End Date: {edu.end_date}")
            if parts:
                education_parts.append("\n".join(parts))
        education_text = "\n\n".join(education_parts)

        # ====================================================
        # BATCH EMBEDDING: Send all 4 structural texts in 1 API call
        # ====================================================
        structural_batch = [
            raw_text,
            skills_text if skills_text.strip() else " ",
            experience_text if experience_text.strip() else " ",
            education_text if education_text.strip() else " "
        ]

        print(f"Embedding 4 structural texts in a single batch request...")
        vectors = create_embeddings(structural_batch)

        full_embedding = vectors[0]
        skills_embedding = vectors[1] if skills_text.strip() else None
        experience_embedding = vectors[2] if experience_text.strip() else None
        education_embedding = vectors[3] if education_text.strip() else None

        # ====================================================
        # DATABASE INSERTION (Parent Candidate)
        # ====================================================
        candidate = Candidate(
            name=structured_resume.name,
            experience_years=structured_resume.experience_years,
            skills=structured_resume.skills,
            education=[edu.model_dump() for edu in structured_resume.education],
            experience=[exp.model_dump() for exp in structured_resume.experience],
            projects=structured_resume.projects,
            resume_text=raw_text,
            skills_text=skills_text,
            experience_text=experience_text,
            education_text=education_text,
            embedding=full_embedding,
            skills_embedding=skills_embedding,
            experience_embedding=experience_embedding,
            education_embedding=education_embedding,
        )

        session.add(candidate)
        session.flush()  # Populates candidate.id immediately via database generation
        
        # Capture primitive values safely right here before commit/expiration
        cand_id = candidate.id
        cand_name = candidate.name

        session.commit()

        # Print the local variables instead of touching the expired SQLAlchemy model instance
        print(f"\n[Success] Candidate ID: {cand_id} | Name: {cand_name}")
    except Exception as e:
        session.rollback()
        print(f"\nFailed to insert {file.name}: {e}")
        raise
    finally:
        session.close()

    # Small pause between files to respect rate limits cleanly
    print("Cooling down for 3 seconds...")
    time.sleep(3)

print("\n========================================")
print("Candidate parent ingestion completed")
print("========================================")