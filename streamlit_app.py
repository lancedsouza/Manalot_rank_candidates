# import sys
# import os

# # Path fix for Streamlit Cloud / local execution
# current_dir = os.path.dirname(os.path.abspath(__file__))
# if current_dir not in sys.path:
#     sys.path.insert(0, current_dir)

# import streamlit as st
# import time
# from pathlib import Path
# from pypdf import PdfReader
# from sqlalchemy import text

# # Import core database and models
# from app.database.db import SessionLocal, engine, Base
# from app.database.resume_models import Candidate
# from app.database.candidate_skill_table import Candidate_Skill
# from app.database.jd_models import JD
# from app.database.jd_skill_table import Jd_Skill

# # Import application services & caching utilities
# from app.services.extract_resume import extract_text
# from app.utils.resume_cache import process_resume
# from app.embedding.embedding_service import create_embedding, create_embeddings

# # Ensure database tables exist
# Base.metadata.create_all(bind=engine)

# # Page configuration
# st.set_page_config(
#     page_title="Manalot Talent Acquisition System",
#     page_icon="🚀",
#     layout="wide"
# )

# # Custom Styling
# st.markdown("""
#     <style>
#     .main-header { font-size: 2.2rem; color: #1E3A8A; font-weight: 700; margin-bottom: 0.2rem; }
#     .sub-header { font-size: 1.1rem; color: #4B5563; margin-bottom: 1.5rem; }
#     .card { background-color: #F8FAFC; border: 1px solid #E2E8F0; padding: 20px; border-radius: 10px; margin-bottom: 15px; }
#     .badge-top { background-color: #DCFCE7; color: #166534; padding: 4px 10px; border-radius: 6px; font-weight: 600; font-size: 0.85rem; }
#     .badge-strong { background-color: #E0F2FE; color: #0369A1; padding: 4px 10px; border-radius: 6px; font-weight: 600; font-size: 0.85rem; }
#     .badge-moderate { background-color: #FEF3C7; color: #92400E; padding: 4px 10px; border-radius: 6px; font-weight: 600; font-size: 0.85rem; }
#     </style>
# """, unsafe_allow_html=True)

# def get_db_session():
#     return SessionLocal()

# def chunk_list(lst, chunk_size=50):
#     for i in range(0, len(lst), chunk_size):
#         yield lst[i:i + chunk_size]

# def process_pdf_jd(session, uploaded_file):
#     temp_dir = Path("temp_uploads")
#     temp_dir.mkdir(exist_ok=True)
#     temp_pdf_path = temp_dir / uploaded_file.name
    
#     with open(temp_pdf_path, "wb") as f:
#         f.write(uploaded_file.getbuffer())

#     try:
#         description = extract_text(temp_pdf_path)
#         if not description:
#             raise ValueError("Could not extract text from the JD PDF.")
        
#         title = os.path.splitext(uploaded_file.name)[0].replace("_", " ").title()
        
#         skills_list = [line.strip() for line in description.split('\n') if len(line.strip()) > 15 and len(line.strip()) < 80][:12]
#         if not skills_list:
#             skills_list = [title]

#         jd_embedding = create_embedding(description)
#         dummy_vec = [0.0] * 768

#         new_JD = JD(
#             title=title,
#             description=description,
#             required_skills=skills_list,
#             preferred_skills=[],
#             preferred_education=[],
#             responsibilities=["General responsibilities per job description"],
#             domain=["General"],
#             industries=["Technology"],
#             embedding=jd_embedding,
#             responsibilities_embedding=jd_embedding,
#             education_embedding=dummy_vec,
#             domain_embedding=dummy_vec,
#             industries_embedding=dummy_vec,
#             required_skills_embeddings=dummy_vec,
#             preferred_skills_embeddings=dummy_vec
#         )
#         session.add(new_JD)
#         session.flush()
        
#         if skills_list:
#             for chunk in chunk_list(skills_list, chunk_size=50):
#                 skill_vectors = create_embeddings(chunk)
#                 for skill, skill_vec in zip(chunk, skill_vectors):
#                     jd_skill = Jd_Skill(
#                         jd_id=new_JD.id,
#                         skill=skill,
#                         skill_embedding=skill_vec
#                     )
#                     session.add(jd_skill)
                
#         session.commit()
#         return new_JD.id, title
#     finally:
#         if temp_pdf_path.exists():
#             temp_pdf_path.unlink()

# def process_single_resume(session, uploaded_file):
#     """Processes, embeds, and stores a single candidate resume."""
#     temp_dir = Path("temp_uploads")
#     temp_dir.mkdir(exist_ok=True)
#     temp_pdf_path = temp_dir / uploaded_file.name
    
#     with open(temp_pdf_path, "wb") as f:
#         f.write(uploaded_file.getbuffer())

#     try:
#         raw_text = extract_text(temp_pdf_path)
#         if not raw_text:
#             raise ValueError(f"Could not extract text from {uploaded_file.name}.")
            
#         # Redis cached resume extraction
#         structured_resume = process_resume(temp_pdf_path)
#         name = structured_resume.name or os.path.splitext(uploaded_file.name)[0].replace("_", " ").title()
        
#         # Checkpoint: Skip embedding if candidate already exists
#         existing = session.query(Candidate.id).filter_by(name=name).first()
#         if existing:
#             return existing[0], name

#         skills_text = " ".join(structured_resume.skills) if structured_resume.skills else ""
        
#         experience_parts = []
#         for exp in structured_resume.experience:
#             parts = []
#             if exp.title: parts.append(f"Title: {exp.title}")
#             if exp.company: parts.append(f"Company: {exp.company}")
#             if exp.start_date: parts.append(f"Start Date: {exp.start_date}")
#             if exp.end_date: parts.append(f"End Date: {exp.end_date}")
#             if exp.responsibilities: parts.append(f"Responsibilities: {' '.join(exp.responsibilities)}")
#             if parts: experience_parts.append("\n".join(parts))
#         experience_text = "\n\n".join(experience_parts)

#         education_parts = []
#         for edu in structured_resume.education:
#             parts = []
#             if edu.degree: parts.append(f"Degree: {edu.degree}")
#             if edu.institution: parts.append(f"Institution: {edu.institution}")
#             if edu.start_date: parts.append(f"Start Date: {edu.start_date}")
#             if edu.end_date: parts.append(f"End Date: {edu.end_date}")
#             if parts: education_parts.append("\n".join(parts))
#         education_text = "\n\n".join(education_parts)

#         # Batch embed structural resume fields
#         structural_batch = [
#             raw_text,
#             skills_text if skills_text.strip() else " ",
#             experience_text if experience_text.strip() else " ",
#             education_text if education_text.strip() else " "
#         ]
#         vectors = create_embeddings(structural_batch)

#         full_embedding = vectors[0]
#         skills_embedding = vectors[1] if skills_text.strip() else None
#         experience_embedding = vectors[2] if experience_text.strip() else None
#         education_embedding = vectors[3] if education_text.strip() else None

#         new_cand = Candidate(
#             name=name,
#             experience_years=structured_resume.experience_years,
#             skills=structured_resume.skills,
#             education=[edu.model_dump() for edu in structured_resume.education],
#             experience=[exp.model_dump() for exp in structured_resume.experience],
#             projects=structured_resume.projects,
#             resume_text=raw_text,
#             skills_text=skills_text,
#             experience_text=experience_text,
#             education_text=education_text,
#             embedding=full_embedding,
#             skills_embedding=skills_embedding,
#             experience_embedding=experience_embedding,
#             education_embedding=education_embedding
#         )
#         session.add(new_cand)
#         session.flush()

#         valid_skills = [s.strip() for s in structured_resume.skills if s and s.strip()]
#         unique_skills = list(set(valid_skills))
        
#         if unique_skills:
#             for chunk in chunk_list(unique_skills, chunk_size=50):
#                 chunk_vectors = create_embeddings(chunk)
#                 for skill, vec in zip(chunk, chunk_vectors):
#                     cand_skill = Candidate_Skill(
#                         cand_id=new_cand.id,
#                         skill=skill,
#                         skill_embedding=vec
#                     )
#                     session.add(cand_skill)
                
#         session.commit()
#         return new_cand.id, name

#     finally:
#         if temp_pdf_path.exists():
#             temp_pdf_path.unlink()

# def rank_candidates(session, jd_id, top_n):
#     parent_sql = text("""
#         SELECT c.id AS candidate_id, c.name AS candidate_name, (1 - (c.embedding <=> j.embedding)) AS parent_similarity
#         FROM candidates c CROSS JOIN jds j WHERE j.id = :jd_id
#     """)
#     parent_results = {row.candidate_id: {"name": row.candidate_name, "parent_sim": float(row.parent_similarity)} 
#                       for row in session.execute(parent_sql, {"jd_id": jd_id}).fetchall()}

#     avg_skill_sql = text("""
#         SELECT sub.candidate_id, AVG(sub.similarity) AS avg_top_skill_similarity
#         FROM (
#             SELECT c.id AS candidate_id, js.id AS jd_skill_id, MAX(1 - (cs.skill_embedding <=> js.skill_embedding)) AS similarity
#             FROM jd_skill js CROSS JOIN cand_skill cs JOIN candidates c ON cs.cand_id = c.id
#             WHERE js.jd_id = :jd_id GROUP BY c.id, js.id
#         ) sub GROUP BY sub.candidate_id
#     """)
#     skill_results = {row.candidate_id: float(row.avg_top_skill_similarity) 
#                      for row in session.execute(avg_skill_sql, {"jd_id": jd_id}).fetchall()}

#     ranked_candidates = []
#     for cand_id, data in parent_results.items():
#         parent_score = data["parent_sim"]
#         skill_score = skill_results.get(cand_id, 0.0)
#         hybrid_score = (0.6 * parent_score) + (0.4 * skill_score)
        
#         ranked_candidates.append({
#             "id": cand_id, "name": data["name"],
#             "hybrid_score": hybrid_score, "parent_score": parent_score, "skill_score": skill_score
#         })

#     ranked_candidates.sort(key=lambda x: x["hybrid_score"], reverse=True)
#     return ranked_candidates[:top_n]

# def get_candidate_evidence(session, jd_id, cand_id):
#     evidence_sql = text("""
#         SELECT js.skill AS jd_skill, cs.skill AS candidate_skill, (1 - (cs.skill_embedding <=> js.skill_embedding)) AS similarity
#         FROM jd_skill js CROSS JOIN cand_skill cs
#         WHERE js.jd_id = :jd_id AND cs.cand_id = :cand_id
#         ORDER BY cs.skill_embedding <=> js.skill_embedding ASC LIMIT 3;
#     """)
#     return session.execute(evidence_sql, {"jd_id": jd_id, "cand_id": cand_id}).fetchall()

# # --- Streamlit Layout ---
# st.markdown('<div class="main-header">🎯 Manalot Autonomous Talent Scout</div>', unsafe_allow_html=True)
# st.markdown('<div class="sub-header">Upload a Job Description and evaluate candidate resumes one by one to prevent quota limits.</div>', unsafe_allow_html=True)

# session = get_db_session()

# # Sidebar Upload Portal
# st.sidebar.header("📁 Document Dropzone")
# uploaded_jd_pdf = st.sidebar.file_uploader("1. Upload Job Description (PDF)", type=["pdf"])
# uploaded_resumes = st.sidebar.file_uploader("2. Upload Candidate Resumes (PDFs)", type=["pdf"], accept_multiple_files=True)

# if uploaded_jd_pdf:
#     # Check if JD already exists or process it
#     jd_rows = session.execute(text("SELECT id, title FROM jds ORDER BY id")).fetchall()
#     jd_dict = {row.title: row.id for row in jd_rows}
    
#     current_jd_title = os.path.splitext(uploaded_jd_pdf.name)[0].replace("_", " ").title()
#     if current_jd_title not in jd_dict:
#         if st.sidebar.button("⚙️ Embed Job Description", type="primary"):
#             with st.spinner("Processing Job Description..."):
#                 jd_id, jd_title = process_pdf_jd(session, uploaded_jd_pdf)
#                 st.sidebar.success(f"Job Description '{jd_title}' embedded successfully!")
#                 st.rerun()

# # Main Screen: Incremental Candidate Evaluation & Final Shortlist
# st.subheader("📊 Recruiter Evaluation & Shortlist Dashboard")
# jd_rows = session.execute(text("SELECT id, title FROM jds ORDER BY id")).fetchall()
# jd_dict = {row.title: row.id for row in jd_rows}

# if not jd_dict:
#     st.info("No Job Descriptions found in the database. Please upload a JD PDF via the sidebar.")
# else:
#     col_sel1, col_sel2 = st.columns([2, 1])
#     with col_sel1:
#         selected_jd_title = st.selectbox("Select Active Requisition", list(jd_dict.keys()))
#         selected_jd_id = jd_dict[selected_jd_title]
#     with col_sel2:
#         top_n = st.slider("Display Top Candidates", 1, 10, 5)

#     if uploaded_resumes:
#         st.markdown("### 📥 Step-by-Step Candidate Processing")
#         if st.button("🚀 Process Resumes Individually & Generate Final Rankings", type="primary"):
#             progress_bar = st.progress(0)
#             status_text = st.empty()
            
#             total_resumes = len(uploaded_resumes)
#             for idx, res_file in enumerate(uploaded_resumes):
#                 status_text.text(f"Processing candidate {idx + 1} of {total_resumes}: {res_file.name}...")
#                 process_single_resume(session, res_file)
#                 progress_bar.progress((idx + 1) / total_resumes)
                
#                 # Polite pacing buffer to protect API limits between individual candidates
#                 if idx < total_resumes - 1:
#                     time.sleep(2)
            
#             status_text.text("All candidates processed successfully! Generating final rankings...")
#             time.sleep(1)
#             st.rerun()

#     st.markdown("---")
#     st.subheader(f"🏆 Final Rankings for: {selected_jd_title}")
    
#     ranked_list = rank_candidates(session, selected_jd_id, top_n)
#     if not ranked_list:
#         st.warning("No candidate records found for this requisition yet. Upload resumes above to begin.")
#     else:
#         for idx, cand in enumerate(ranked_list, 1):
#             match_pct = cand['hybrid_score'] * 100
#             parent_pct = cand['parent_score'] * 100
#             skill_pct = cand['skill_score'] * 100
            
#             if match_pct >= 85:
#                 badge_html = '<span class="badge-top">🌟 Top Tier Match</span>'
#             elif match_pct >= 75:
#                 badge_html = '<span class="badge-strong">👍 Strong Match</span>'
#             else:
#                 badge_html = '<span class="badge-moderate">⚠️ Moderate Match</span>'
            
#             with st.container():
#                 st.markdown(f"""
#                 <div class="card">
#                     <h3>Rank #{idx}: {cand['name']}</h3>
#                     <p>{badge_html} &nbsp;&nbsp;|&nbsp;&nbsp; <b>Hybrid Match Score:</b> {match_pct:.1f}%</p>
#                 </div>
#                 """, unsafe_allow_html=True)
                
#                 c1, c2 = st.columns([1, 2])
#                 with c1:
#                     st.metric("Overall Profile Fit", f"{parent_pct:.1f}%")
#                     st.metric("Core Skill Alignment", f"{skill_pct:.1f}%")
                    
#                 with c2:
#                     st.markdown("**🔍 Verifiable Resume Skill Evidence:**")
#                     evidence_rows = get_candidate_evidence(session, selected_jd_id, cand['id'])
                    
#                     if evidence_rows:
#                         for ev in evidence_rows:
#                             st.markdown(f"""
#                             - **JD Requirement:** *"{ev.jd_skill}"*  
#                               ↳ **Candidate Match:** *"{ev.candidate_skill}"* (`{ev.similarity * 100:.0f}%` match)
#                             """)
#                     else:
#                         st.info("No skill evidence records found.")
#                 st.markdown("---")

# session.close()
# import sys
# import os

# # Path fix for Streamlit Cloud / local execution
# current_dir = os.path.dirname(os.path.abspath(__file__))
# if current_dir not in sys.path:
#     sys.path.insert(0, current_dir)

# import streamlit as st
# import time
# from pathlib import Path
# from pypdf import PdfReader
# from sqlalchemy import text

# # Import core database and models
# from app.database.db import SessionLocal, engine, Base
# from app.database.resume_models import Candidate
# from app.database.candidate_skill_table import Candidate_Skill
# from app.database.jd_models import JD
# from app.database.jd_skill_table import Jd_Skill

# # Import application services & caching utilities
# from app.services.extract_resume import extract_text
# from app.utils.resume_cache import process_resume
# from app.embedding.embedding_service import create_embedding, create_embeddings

# # Ensure database tables exist
# Base.metadata.create_all(bind=engine)

# # Page configuration
# st.set_page_config(
#     page_title="Manalot Talent Acquisition System",
#     page_icon="🚀",
#     layout="wide"
# )

# # Custom Styling
# st.markdown("""
#     <style>
#     .main-header { font-size: 2.2rem; color: #1E3A8A; font-weight: 700; margin-bottom: 0.2rem; }
#     .sub-header { font-size: 1.1rem; color: #4B5563; margin-bottom: 1.5rem; }
#     .card { background-color: #F8FAFC; border: 1px solid #E2E8F0; padding: 20px; border-radius: 10px; margin-bottom: 15px; }
#     .badge-top { background-color: #DCFCE7; color: #166534; padding: 4px 10px; border-radius: 6px; font-weight: 600; font-size: 0.85rem; }
#     .badge-strong { background-color: #E0F2FE; color: #0369A1; padding: 4px 10px; border-radius: 6px; font-weight: 600; font-size: 0.85rem; }
#     .badge-moderate { background-color: #FEF3C7; color: #92400E; padding: 4px 10px; border-radius: 6px; font-weight: 600; font-size: 0.85rem; }
#     </style>
# """, unsafe_allow_html=True)

# def get_db_session():
#     return SessionLocal()

# def chunk_list(lst, chunk_size=50):
#     for i in range(0, len(lst), chunk_size):
#         yield lst[i:i + chunk_size]

# def process_pdf_jd(session, uploaded_file):
#     temp_dir = Path("temp_uploads")
#     temp_dir.mkdir(exist_ok=True)
#     temp_pdf_path = temp_dir / uploaded_file.name
    
#     with open(temp_pdf_path, "wb") as f:
#         f.write(uploaded_file.getbuffer())

#     try:
#         description = extract_text(temp_pdf_path)
#         if not description:
#             raise ValueError("Could not extract text from the JD PDF.")
        
#         title = os.path.splitext(uploaded_file.name)[0].replace("_", " ").title()
        
#         skills_list = [line.strip() for line in description.split('\n') if len(line.strip()) > 15 and len(line.strip()) < 80][:12]
#         if not skills_list:
#             skills_list = [title]

#         jd_embedding = create_embedding(description)
#         dummy_vec = [0.0] * 768

#         new_JD = JD(
#             title=title,
#             description=description,
#             required_skills=skills_list,
#             preferred_skills=[],
#             preferred_education=[],
#             responsibilities=["General responsibilities per job description"],
#             domain=["General"],
#             industries=["Technology"],
#             embedding=jd_embedding,
#             responsibilities_embedding=jd_embedding,
#             education_embedding=dummy_vec,
#             domain_embedding=dummy_vec,
#             industries_embedding=dummy_vec,
#             required_skills_embeddings=dummy_vec,
#             preferred_skills_embeddings=dummy_vec
#         )
#         session.add(new_JD)
#         session.flush()
        
#         jd_id = new_JD.id
        
#         if skills_list:
#             for chunk in chunk_list(skills_list, chunk_size=50):
#                 skill_vectors = create_embeddings(chunk)
#                 for skill, skill_vec in zip(chunk, skill_vectors):
#                     jd_skill = Jd_Skill(
#                         jd_id=jd_id,
#                         skill=skill,
#                         skill_embedding=skill_vec
#                     )
#                     session.add(jd_skill)
                
#         session.commit()
#         return jd_id, title
#     finally:
#         if temp_pdf_path.exists():
#             temp_pdf_path.unlink()

# def process_single_resume(session, uploaded_file):
#     """Processes, embeds, and stores a single candidate resume safely using Redis cache."""
#     temp_dir = Path("temp_uploads")
#     temp_dir.mkdir(exist_ok=True)
#     temp_pdf_path = temp_dir / uploaded_file.name
    
#     with open(temp_pdf_path, "wb") as f:
#         f.write(uploaded_file.getbuffer())

#     try:
#         raw_text = extract_text(temp_pdf_path)
#         if not raw_text:
#             raise ValueError(f"Could not extract text from {uploaded_file.name}.")
            
#         structured_resume = process_resume(temp_pdf_path)
#         name = structured_resume.name or os.path.splitext(uploaded_file.name)[0].replace("_", " ").title()
        
#         # Checkpoint: Skip if candidate already exists
#         existing = session.query(Candidate.id).filter_by(name=name).first()
#         if existing:
#             return existing[0], name

#         skills_text = " ".join(structured_resume.skills) if structured_resume.skills else ""
        
#         experience_parts = []
#         for exp in structured_resume.experience:
#             parts = []
#             if exp.title: parts.append(f"Title: {exp.title}")
#             if exp.company: parts.append(f"Company: {exp.company}")
#             if exp.start_date: parts.append(f"Start Date: {exp.start_date}")
#             if exp.end_date: parts.append(f"End Date: {exp.end_date}")
#             if exp.responsibilities: parts.append(f"Responsibilities: {' '.join(exp.responsibilities)}")
#             if parts: experience_parts.append("\n".join(parts))
#         experience_text = "\n\n".join(experience_parts)

#         education_parts = []
#         for edu in structured_resume.education:
#             parts = []
#             if edu.degree: parts.append(f"Degree: {edu.degree}")
#             if edu.institution: parts.append(f"Institution: {edu.institution}")
#             if edu.start_date: parts.append(f"Start Date: {edu.start_date}")
#             if edu.end_date: parts.append(f"End Date: {edu.end_date}")
#             if parts: education_parts.append("\n".join(parts))
#         education_text = "\n\n".join(education_parts)

#         # Batch embed structural resume fields
#         structural_batch = [
#             raw_text,
#             skills_text if skills_text.strip() else " ",
#             experience_text if experience_text.strip() else " ",
#             education_text if education_text.strip() else " "
#         ]
#         vectors = create_embeddings(structural_batch)

#         full_embedding = vectors[0]
#         skills_embedding = vectors[1] if skills_text.strip() else None
#         experience_embedding = vectors[2] if experience_text.strip() else None
#         education_embedding = vectors[3] if education_text.strip() else None

#         new_cand = Candidate(
#             name=name,
#             experience_years=structured_resume.experience_years,
#             skills=structured_resume.skills,
#             education=[edu.model_dump() for edu in structured_resume.education],
#             experience=[exp.model_dump() for exp in structured_resume.experience],
#             projects=structured_resume.projects,
#             resume_text=raw_text,
#             skills_text=skills_text,
#             experience_text=experience_text,
#             education_text=education_text,
#             embedding=full_embedding,
#             skills_embedding=skills_embedding,
#             experience_embedding=experience_embedding,
#             education_embedding=education_embedding
#         )
#         session.add(new_cand)
#         session.flush()

#         # Capture primitive ID immediately before commit/expire
#         cand_id = new_cand.id

#         valid_skills = [s.strip() for s in structured_resume.skills if s and s.strip()]
#         unique_skills = list(set(valid_skills))
        
#         if unique_skills:
#             for chunk in chunk_list(unique_skills, chunk_size=50):
#                 chunk_vectors = create_embeddings(chunk)
#                 for skill, vec in zip(chunk, chunk_vectors):
#                     cand_skill = Candidate_Skill(
#                         cand_id=cand_id,
#                         skill=skill,
#                         skill_embedding=vec
#                     )
#                     session.add(cand_skill)
                
#         session.commit()
#         return cand_id, name

#     finally:
#         if temp_pdf_path.exists():
#             temp_pdf_path.unlink()

# def rank_candidates(session, jd_id, top_n):
#     parent_sql = text("""
#         SELECT c.id AS candidate_id, c.name AS candidate_name, (1 - (c.embedding <=> j.embedding)) AS parent_similarity
#         FROM candidates c CROSS JOIN jds j WHERE j.id = :jd_id
#     """)
#     parent_results = {row.candidate_id: {"name": row.candidate_name, "parent_sim": float(row.parent_similarity)} 
#                       for row in session.execute(parent_sql, {"jd_id": jd_id}).fetchall()}

#     avg_skill_sql = text("""
#         SELECT sub.candidate_id, AVG(sub.similarity) AS avg_top_skill_similarity
#         FROM (
#             SELECT c.id AS candidate_id, js.id AS jd_skill_id, MAX(1 - (cs.skill_embedding <=> js.skill_embedding)) AS similarity
#             FROM jd_skill js CROSS JOIN cand_skill cs JOIN candidates c ON cs.cand_id = c.id
#             WHERE js.jd_id = :jd_id GROUP BY c.id, js.id
#         ) sub GROUP BY sub.candidate_id
#     """)
#     skill_results = {row.candidate_id: float(row.avg_top_skill_similarity) 
#                      for row in session.execute(avg_skill_sql, {"jd_id": jd_id}).fetchall()}

#     ranked_candidates = []
#     for cand_id, data in parent_results.items():
#         parent_score = data["parent_sim"]
#         skill_score = skill_results.get(cand_id, 0.0)
#         hybrid_score = (0.6 * parent_score) + (0.4 * skill_score)
        
#         ranked_candidates.append({
#             "id": cand_id, "name": data["name"],
#             "hybrid_score": hybrid_score, "parent_score": parent_score, "skill_score": skill_score
#         })

#     ranked_candidates.sort(key=lambda x: x["hybrid_score"], reverse=True)
#     return ranked_candidates[:top_n]

# def get_candidate_evidence(session, jd_id, cand_id):
#     evidence_sql = text("""
#         SELECT js.skill AS jd_skill, cs.skill AS candidate_skill, (1 - (cs.skill_embedding <=> js.skill_embedding)) AS similarity
#         FROM jd_skill js CROSS JOIN cand_skill cs
#         WHERE js.jd_id = :jd_id AND cs.cand_id = :cand_id
#         ORDER BY cs.skill_embedding <=> js.skill_embedding ASC LIMIT 3;
#     """)
#     return session.execute(evidence_sql, {"jd_id": jd_id, "cand_id": cand_id}).fetchall()

# # --- Streamlit Layout ---
# st.markdown('<div class="main-header">🎯 Manalot Autonomous Talent Scout</div>', unsafe_allow_html=True)
# st.markdown('<div class="sub-header">Upload a Job Description and evaluate candidate resumes step-by-step to prevent quota limits.</div>', unsafe_allow_html=True)

# session = get_db_session()

# # Sidebar Upload Portal
# st.sidebar.header("📁 Document Dropzone")
# uploaded_jd_pdf = st.sidebar.file_uploader("1. Upload Job Description (PDF)", type=["pdf"])
# uploaded_resumes = st.sidebar.file_uploader("2. Upload Candidate Resumes (PDFs)", type=["pdf"], accept_multiple_files=True)

# if uploaded_jd_pdf:
#     jd_rows = session.execute(text("SELECT id, title FROM jds ORDER BY id")).fetchall()
#     jd_dict = {row.title: row.id for row in jd_rows}
    
#     current_jd_title = os.path.splitext(uploaded_jd_pdf.name)[0].replace("_", " ").title()
#     if current_jd_title not in jd_dict:
#         if st.sidebar.button("⚙️ Embed Job Description", type="primary"):
#             with st.spinner("Processing Job Description..."):
#                 jd_id, jd_title = process_pdf_jd(session, uploaded_jd_pdf)
#                 st.sidebar.success(f"Job Description '{jd_title}' embedded successfully!")
#                 st.rerun()

# # Main Screen: Incremental Candidate Evaluation & Final Shortlist
# st.subheader("📊 Recruiter Evaluation & Shortlist Dashboard")
# jd_rows = session.execute(text("SELECT id, title FROM jds ORDER BY id")).fetchall()
# jd_dict = {row.title: row.id for row in jd_rows}

# if not jd_dict:
#     st.info("No Job Descriptions found in the database. Please upload a JD PDF via the sidebar.")
# else:
#     col_sel1, col_sel2 = st.columns([2, 1])
#     with col_sel1:
#         selected_jd_title = st.selectbox("Select Active Requisition", list(jd_dict.keys()))
#         selected_jd_id = jd_dict[selected_jd_title]
#     with col_sel2:
#         top_n = st.slider("Display Top Candidates", 1, 10, 5)

#     if uploaded_resumes:
#         st.markdown("### 📥 Incremental Candidate Ingestion")
#         if st.button("🚀 Process Resumes & Update Rankings", type="primary"):
#             progress_bar = st.progress(0)
#             status_text = st.empty()
            
#             total_resumes = len(uploaded_resumes)
#             for idx, res_file in enumerate(uploaded_resumes):
#                 status_text.text(f"Processing candidate {idx + 1} of {total_resumes}: {res_file.name}...")
#                 process_single_resume(session, res_file)
#                 progress_bar.progress((idx + 1) / total_resumes)
                
#                 # Polite buffer to protect API limits between individual candidates
#                 if idx < total_resumes - 1:
#                     time.sleep(2)
            
#             status_text.text("All candidates processed successfully! Refreshing dashboard...")
#             time.sleep(1)
#             st.rerun()

#     st.markdown("---")
#     st.subheader(f"🏆 Final Rankings for: {selected_jd_title}")
    
#     ranked_list = rank_candidates(session, selected_jd_id, top_n)
#     if not ranked_list:
#         st.warning("No candidate records found for this requisition yet. Upload resumes above to begin.")
#     else:
#         for idx, cand in enumerate(ranked_list, 1):
#             match_pct = cand['hybrid_score'] * 100
#             parent_pct = cand['parent_score'] * 100
#             skill_pct = cand['skill_score'] * 100
            
#             if match_pct >= 85:
#                 badge_html = '<span class="badge-top">🌟 Top Tier Match</span>'
#             elif match_pct >= 75:
#                 badge_html = '<span class="badge-strong">👍 Strong Match</span>'
#             else:
#                 badge_html = '<span class="badge-moderate">⚠️ Moderate Match</span>'
            
#             with st.container():
#                 st.markdown(f"""
#                 <div class="card">
#                     <h3>Rank #{idx}: {cand['name']}</h3>
#                     <p>{badge_html} &nbsp;&nbsp;|&nbsp;&nbsp; <b>Hybrid Match Score:</b> {match_pct:.1f}%</p>
#                 </div>
#                 """, unsafe_allow_html=True)
                
#                 c1, c2 = st.columns([1, 2])
#                 with c1:
#                     st.metric("Overall Profile Fit", f"{parent_pct:.1f}%")
#                     st.metric("Core Skill Alignment", f"{skill_pct:.1f}%")
                    
#                 with c2:
#                     st.markdown("**🔍 Verifiable Resume Skill Evidence:**")
#                     evidence_rows = get_candidate_evidence(session, selected_jd_id, cand['id'])
                    
#                     if evidence_rows:
#                         for ev in evidence_rows:
#                             st.markdown(f"""
#                             - **JD Requirement:** *"{ev.jd_skill}"*  
#                               ↳ **Candidate Match:** *"{ev.candidate_skill}"* (`{ev.similarity * 100:.0f}%` match)
#                             """)
#                     else:
#                         st.info("No skill evidence records found.")
#                 st.markdown("---")

# session.close()

"""Updated code to handle non relevant resume which dont match the JD"""
# import sys
# import os

# # Path fix for Streamlit Cloud / local execution
# current_dir = os.path.dirname(os.path.abspath(__file__))
# if current_dir not in sys.path:
#     sys.path.insert(0, current_dir)

# import streamlit as st
# import time
# import redis
# from pathlib import Path
# from pypdf import PdfReader
# from sqlalchemy import text

# # Import core database and models
# from app.database.db import SessionLocal, engine, Base
# from app.database.resume_models import Candidate
# from app.database.candidate_skill_table import Candidate_Skill
# from app.database.jd_models import JD
# from app.database.jd_skill_table import Jd_Skill
# from app.database.application_models import Application

# # Import application services & caching utilities
# from app.services.extract_resume import extract_text
# from app.utils.resume_cache import process_resume, generate_cache_key
# from app.embedding.embedding_service import create_embedding, create_embeddings

# # Ensure database tables exist
# Base.metadata.create_all(bind=engine)

# # Page configuration
# st.set_page_config(
#     page_title="Manalot Talent Acquisition System",
#     page_icon="🚀",
#     layout="wide"
# )

# # Custom Styling
# st.markdown("""
#     <style>
#     .main-header { font-size: 2.2rem; color: #1E3A8A; font-weight: 700; margin-bottom: 0.2rem; }
#     .sub-header { font-size: 1.1rem; color: #4B5563; margin-bottom: 1.5rem; }
#     .card { background-color: #F8FAFC; border: 1px solid #E2E8F0; padding: 20px; border-radius: 10px; margin-bottom: 15px; }
#     .badge-top { background-color: #DCFCE7; color: #166534; padding: 4px 10px; border-radius: 6px; font-weight: 600; font-size: 0.85rem; }
#     .badge-strong { background-color: #E0F2FE; color: #0369A1; padding: 4px 10px; border-radius: 6px; font-weight: 600; font-size: 0.85rem; }
#     .badge-moderate { background-color: #FEF3C7; color: #92400E; padding: 4px 10px; border-radius: 6px; font-weight: 600; font-size: 0.85rem; }
#     </style>
# """, unsafe_allow_html=True)

# def get_db_session():
#     return SessionLocal()

# def chunk_list(lst, chunk_size=50):
#     for i in range(0, len(lst), chunk_size):
#         yield lst[i:i + chunk_size]

# def process_pdf_jd(session, uploaded_file):
#     temp_dir = Path("temp_uploads")
#     temp_dir.mkdir(exist_ok=True)
#     temp_pdf_path = temp_dir / uploaded_file.name
    
#     with open(temp_pdf_path, "wb") as f:
#         f.write(uploaded_file.getbuffer())

#     try:
#         description = extract_text(temp_pdf_path)
#         if not description:
#             raise ValueError("Could not extract text from the JD PDF.")
        
#         title = os.path.splitext(uploaded_file.name)[0].replace("_", " ").title()
        
#         skills_list = [line.strip() for line in description.split('\n') if len(line.strip()) > 15 and len(line.strip()) < 80][:12]
#         if not skills_list:
#             skills_list = [title]

#         jd_embedding = create_embedding(description)
#         dummy_vec = [0.0] * 768

#         new_JD = JD(
#             title=title,
#             description=description,
#             required_skills=skills_list,
#             preferred_skills=[],
#             preferred_education=[],
#             responsibilities=["General responsibilities per job description"],
#             domain=["General"],
#             industries=["Technology"],
#             embedding=jd_embedding,
#             responsibilities_embedding=jd_embedding,
#             education_embedding=dummy_vec,
#             domain_embedding=dummy_vec,
#             industries_embedding=dummy_vec,
#             required_skills_embeddings=dummy_vec,
#             preferred_skills_embeddings=dummy_vec
#         )
#         session.add(new_JD)
#         session.flush()
#         jd_id = new_JD.id
        
#         if skills_list:
#             for chunk in chunk_list(skills_list, chunk_size=50):
#                 skill_vectors = create_embeddings(chunk)
#                 for skill, skill_vec in zip(chunk, skill_vectors):
#                     jd_skill = Jd_Skill(
#                         jd_id=jd_id,
#                         skill=skill,
#                         skill_embedding=skill_vec
#                     )
#                     session.add(jd_skill)
                
#         session.commit()
#         return jd_id, title
#     finally:
#         if temp_pdf_path.exists():
#             temp_pdf_path.unlink()

# def calculate_candidate_scores_for_jd(session, jd_id, cand_id):
#     parent_sql = text("""
#         SELECT (1 - (c.embedding <=> j.embedding)) AS parent_similarity
#         FROM candidates c CROSS JOIN jds j 
#         WHERE c.id = :cand_id AND j.id = :jd_id
#     """)
#     parent_res = session.execute(parent_sql, {"cand_id": cand_id, "jd_id": jd_id}).scalar()
#     parent_sim = float(parent_res) if parent_res is not None else 0.0

#     skill_sql = text("""
#         SELECT AVG(sub.similarity) AS avg_top_skill_similarity
#         FROM (
#             SELECT MAX(1 - (cs.skill_embedding <=> js.skill_embedding)) AS similarity
#             FROM jd_skill js CROSS JOIN cand_skill cs 
#             WHERE js.jd_id = :jd_id AND cs.cand_id = :cand_id
#             GROUP BY js.id
#         ) sub
#     """)
#     skill_res = session.execute(skill_sql, {"cand_id": cand_id, "jd_id": jd_id}).scalar()
#     skill_sim = float(skill_res) if skill_res is not None else 0.0

#     hybrid_score = (0.6 * parent_sim) + (0.4 * skill_sim)
#     return {
#         "hybrid": hybrid_score,
#         "parent": parent_sim,
#         "skill": skill_sim
#     }

# def process_and_link_resume(session, uploaded_file, jd_id, force_refresh=False):
#     temp_dir = Path("temp_uploads")
#     temp_dir.mkdir(exist_ok=True)
#     temp_pdf_path = temp_dir / uploaded_file.name
    
#     with open(temp_pdf_path, "wb") as f:
#         f.write(uploaded_file.getbuffer())

#     try:
#         raw_text = extract_text(temp_pdf_path)
#         if not raw_text:
#             raise ValueError(f"Could not extract text from {uploaded_file.name}.")
            
#         if force_refresh:
#             try:
#                 redis_url = os.getenv("REDIS_URL", "redis://localhost:6380")
#                 r = redis.Redis.from_url(redis_url, decode_responses=True)
#                 cache_key = generate_cache_key(temp_pdf_path)
#                 r.delete(cache_key)
#             except Exception:
#                 pass

#         structured_resume = process_resume(temp_pdf_path)
#         name = structured_resume.name or os.path.splitext(uploaded_file.name)[0].replace("_", " ").title()
        
#         skills_text = " ".join(structured_resume.skills) if structured_resume.skills else ""
        
#         experience_parts = []
#         for exp in structured_resume.experience:
#             parts = []
#             if exp.title: parts.append(f"Title: {exp.title}")
#             if exp.company: parts.append(f"Company: {exp.company}")
#             if exp.responsibilities: parts.append(f"Responsibilities: {' '.join(exp.responsibilities)}")
#             if parts: experience_parts.append("\n".join(parts))
#         experience_text = "\n\n".join(experience_parts)

#         education_parts = []
#         for edu in structured_resume.education:
#             parts = []
#             if edu.degree: parts.append(f"Degree: {edu.degree}")
#             if edu.institution: parts.append(f"Institution: {edu.institution}")
#             if parts: education_parts.append("\n".join(parts))
#         education_text = "\n\n".join(education_parts)

#         structural_batch = [
#             raw_text,
#             skills_text if skills_text.strip() else " ",
#             experience_text if experience_text.strip() else " ",
#             education_text if education_text.strip() else " "
#         ]
#         vectors = create_embeddings(structural_batch)

#         # 🚀 Check existence using lightweight scalar SQL lookup (avoids ORM vector decoding bugs)
#         existing_row = session.execute(
#             text("SELECT id FROM candidates WHERE name = :name"), 
#             {"name": name}
#         ).first()

#         if existing_row:
#             cand_id = existing_row[0]
#             # Update existing candidate data via raw SQL update to avoid vector hydrator errors
#             update_cand_sql = text("""
#                 UPDATE candidates 
#                 SET experience_years = :exp_years, resume_text = :resume_text, 
#                     skills_text = :skills_text, experience_text = :exp_text, education_text = :edu_text, 
#                     embedding = CAST(:emb AS vector), skills_embedding = CAST(:skill_emb AS vector)
#                 WHERE id = :cand_id
#             """)
#             session.execute(update_cand_sql, {
#                 "exp_years": structured_resume.experience_years,
#                 "resume_text": raw_text,
#                 "skills_text": skills_text,
#                 "exp_text": experience_text,
#                 "edu_text": education_text,
#                 "emb": str(vectors[0]),
#                 "skill_emb": str(vectors[1]) if skills_text.strip() else None,
#                 "cand_id": cand_id
#             })
#             # Clear old skill mappings
#             session.execute(text("DELETE FROM cand_skill WHERE cand_id = :cand_id"), {"cand_id": cand_id})
#         else:
#             insert_cand_sql = text("""
#                 INSERT INTO candidates (name, experience_years, resume_text, skills_text, experience_text, education_text, embedding, skills_embedding)
#                 VALUES (:name, :exp_years, :resume_text, :skills_text, :exp_text, :edu_text, CAST(:emb AS vector), CAST(:skill_emb AS vector))
#                 RETURNING id;
#             """)
#             res = session.execute(insert_cand_sql, {
#                 "name": name,
#                 "exp_years": structured_resume.experience_years,
#                 "resume_text": raw_text,
#                 "skills_text": skills_text,
#                 "exp_text": experience_text,
#                 "edu_text": education_text,
#                 "emb": str(vectors[0]),
#                 "skill_emb": str(vectors[1]) if skills_text.strip() else None
#             })
#             cand_id = res.scalar()

#         # Insert skill embeddings safely using raw SQL
#         valid_skills = [s.strip() for s in structured_resume.skills if s and s.strip()]
#         unique_skills = list(set(valid_skills))
        
#         if unique_skills:
#             for chunk in chunk_list(unique_skills, chunk_size=50):
#                 chunk_vectors = create_embeddings(chunk)
#                 for skill, vec in zip(chunk, chunk_vectors):
#                     insert_skill_sql = text("""
#                         INSERT INTO cand_skill (cand_id, skill, skill_embedding)
#                         VALUES (:cand_id, :skill, CAST(:vec AS vector))
#                     """)
#                     session.execute(insert_skill_sql, {
#                         "cand_id": cand_id,
#                         "skill": skill,
#                         "vec": str(vec)
#                     })

#         # Compute match scores for active job requisition
#         scores = calculate_candidate_scores_for_jd(session, jd_id, cand_id)

#         # Upsert application link
#         existing_app = session.execute(
#             text("SELECT id FROM applications WHERE jd_id = :jd_id AND candidate_id = :cand_id"),
#             {"jd_id": jd_id, "cand_id": cand_id}
#         ).first()

#         if existing_app:
#             session.execute(
#                 text("""
#                     UPDATE applications 
#                     SET hybrid_score = :hybrid, parent_score = :parent, skill_score = :skill
#                     WHERE jd_id = :jd_id AND candidate_id = :cand_id
#                 """),
#                 {"hybrid": scores['hybrid'], "parent": scores['parent'], "skill": scores['skill'], "jd_id": jd_id, "cand_id": cand_id}
#             )
#         else:
#             session.execute(
#                 text("""
#                     INSERT INTO applications (jd_id, candidate_id, hybrid_score, parent_score, skill_score)
#                     VALUES (:jd_id, :cand_id, :hybrid, :parent, :skill)
#                 """),
#                 {"jd_id": jd_id, "cand_id": cand_id, "hybrid": scores['hybrid'], "parent": scores['parent'], "skill": scores['skill']}
#             )
                
#         session.commit()
#         return cand_id, name

#     except Exception as e:
#         session.rollback()
#         raise e
#     finally:
#         if temp_pdf_path.exists():
#             temp_pdf_path.unlink()

# def get_ranked_applications_for_jd(session, jd_id, top_n):
#     query = text("""
#         SELECT c.id AS candidate_id, c.name AS candidate_name, 
#                a.hybrid_score, a.parent_score, a.skill_score
#         FROM applications a
#         JOIN candidates c ON a.candidate_id = c.id
#         WHERE a.jd_id = :jd_id
#         ORDER BY a.hybrid_score DESC
#         LIMIT :top_n
#     """)
#     rows = session.execute(query, {"jd_id": jd_id, "top_n": top_n}).fetchall()
    
#     return [
#         {
#             "id": row.candidate_id,
#             "name": row.candidate_name,
#             "hybrid_score": row.hybrid_score,
#             "parent_score": row.parent_score,
#             "skill_score": row.skill_score
#         }
#         for row in rows
#     ]

# def get_candidate_evidence(session, jd_id, cand_id):
#     evidence_sql = text("""
#         SELECT js.skill AS jd_skill, cs.skill AS candidate_skill, 
#                (1 - (cs.skill_embedding <=> js.skill_embedding)) AS similarity
#         FROM jd_skill js 
#         CROSS JOIN cand_skill cs 
#         JOIN candidates c ON cs.cand_id = c.id
#         WHERE js.jd_id = :jd_id AND cs.cand_id = :cand_id
#           AND (1 - (cs.skill_embedding <=> js.skill_embedding)) >= 0.82
#         ORDER BY cs.skill_embedding <=> js.skill_embedding ASC 
#         LIMIT 3;
#     """)
#     return session.execute(evidence_sql, {"jd_id": jd_id, "cand_id": cand_id}).fetchall()

# # --- Streamlit Layout ---
# st.markdown('<div class="main-header">🎯 Manalot Autonomous Talent Scout</div>', unsafe_allow_html=True)
# st.markdown('<div class="sub-header">Upload Job Descriptions & Evaluate Candidates via Relational Requisition Pipelines.</div>', unsafe_allow_html=True)

# session = get_db_session()

# st.sidebar.header("📁 Document Dropzone")
# uploaded_jd_pdf = st.sidebar.file_uploader("1. Upload Job Description (PDF)", type=["pdf"])
# uploaded_resumes = st.sidebar.file_uploader("2. Upload Candidate Resumes (PDFs)", type=["pdf"], accept_multiple_files=True)

# with st.sidebar.expander("🛠️ Maintenance Controls"):
#     force_refresh_toggle = st.checkbox("Force Re-parse (Bypass Cache)", value=False)
    
#     if st.button("🧹 Clear Entire Redis Cache", type="secondary"):
#         try:
#             redis_url = os.getenv("REDIS_URL", "redis://localhost:6380")
#             r = redis.Redis.from_url(redis_url, decode_responses=True)
#             r.flushall()
#             st.sidebar.success("Redis cache flushed!")
#         except Exception as e:
#             st.sidebar.error(f"Error: {e}")

# if uploaded_jd_pdf:
#     jd_rows = session.execute(text("SELECT id, title FROM jds ORDER BY id")).fetchall()
#     jd_dict = {row.title: row.id for row in jd_rows}
    
#     current_jd_title = os.path.splitext(uploaded_jd_pdf.name)[0].replace("_", " ").title()
#     if current_jd_title not in jd_dict:
#         if st.sidebar.button("⚙️ Embed Job Description", type="primary"):
#             with st.spinner("Processing Job Description..."):
#                 jd_id, jd_title = process_pdf_jd(session, uploaded_jd_pdf)
#                 st.sidebar.success(f"Job Description '{jd_title}' embedded successfully!")
#                 st.rerun()

# st.subheader("📊 Relational Requisition Shortlist Dashboard")
# jd_rows = session.execute(text("SELECT id, title FROM jds ORDER BY id")).fetchall()
# jd_dict = {row.title: row.id for row in jd_rows}

# if not jd_dict:
#     st.info("No Job Descriptions found in the database. Please upload a JD PDF via the sidebar.")
# else:
#     col_sel1, col_sel2 = st.columns([2, 1])
#     with col_sel1:
#         selected_jd_title = st.selectbox("Select Active Requisition", list(jd_dict.keys()))
#         selected_jd_id = jd_dict[selected_jd_title]
#     with col_sel2:
#         top_n = st.slider("Display Top Candidates", 1, 10, 5)

#     if uploaded_resumes:
#         st.markdown("### 📥 Incremental Application Ingestion")
#         if st.button("🚀 Process Resumes & Link to Requisition", type="primary"):
#             progress_bar = st.progress(0)
#             status_text = st.empty()
            
#             total_resumes = len(uploaded_resumes)
#             for idx, res_file in enumerate(uploaded_resumes):
#                 status_text.text(f"Processing application {idx + 1} of {total_resumes}: {res_file.name}...")
#                 process_and_link_resume(session, res_file, selected_jd_id, force_refresh=force_refresh_toggle)
#                 progress_bar.progress((idx + 1) / total_resumes)
                
#                 if idx < total_resumes - 1:
#                     time.sleep(2)
            
#             status_text.text("All resumes linked and scored successfully! Refreshing dashboard...")
#             time.sleep(1)
#             st.rerun()

#     st.markdown("---")
#     st.subheader(f"🏆 Shortlist for: {selected_jd_title}")
    
#     ranked_list = get_ranked_applications_for_jd(session, selected_jd_id, top_n)
#     if not ranked_list:
#         st.warning("No candidates have applied to this requisition yet. Upload resumes above to begin.")
#     else:
#         for idx, cand in enumerate(ranked_list, 1):
#             match_pct = cand['hybrid_score'] * 100
#             parent_pct = cand['parent_score'] * 100
#             skill_pct = cand['skill_score'] * 100
            
#             if match_pct >= 85:
#                 badge_html = '<span class="badge-top">🌟 Top Tier Match</span>'
#             elif match_pct >= 75:
#                 badge_html = '<span class="badge-strong">👍 Strong Match</span>'
#             else:
#                 badge_html = '<span class="badge-moderate">⚠️ Moderate Match</span>'
            
#             with st.container():
#                 st.markdown(f"""
#                 <div class="card">
#                     <h3>Rank #{idx}: {cand['name']}</h3>
#                     <p>{badge_html} &nbsp;&nbsp;|&nbsp;&nbsp; <b>Hybrid Match Score:</b> {match_pct:.1f}%</p>
#                 </div>
#                 """, unsafe_allow_html=True)
                
#                 c1, c2 = st.columns([1, 2])
#                 with c1:
#                     st.metric("Overall Profile Fit", f"{parent_pct:.1f}%")
#                     st.metric("Core Skill Alignment", f"{skill_pct:.1f}%")
                    
#                 with c2:
#                     st.markdown("**🔍 Verifiable Resume Skill Evidence:**")
#                     evidence_rows = get_candidate_evidence(session, selected_jd_id, cand['id'])
                    
#                     if evidence_rows:
#                         for ev in evidence_rows:
#                             st.markdown(f"""
#                             - **JD Requirement:** *"{ev.jd_skill}"*  
#                               ↳ **Candidate Match:** *"{ev.candidate_skill}"* (`{ev.similarity * 100:.0f}%` match)
#                             """)
#                     else:
#                         st.info("No primary skill evidence matches above threshold.")
#                 st.markdown("---")

# session.close()

# import sys
# import os
# import time

# # Path fix for Streamlit Cloud / local execution
# current_dir = os.path.dirname(os.path.abspath(__file__))
# if current_dir not in sys.path:
#     sys.path.insert(0, current_dir)

# import redis
# import streamlit as st
# from sqlalchemy import text

# from app.database.db import SessionLocal, engine, Base

# # Register all models with Base.metadata
# from app.database.resume_models import Candidate          # noqa: F401
# from app.database.candidate_skill_table import Candidate_Skill  # noqa: F401
# from app.database.jd_models import JD                     # noqa: F401
# from app.database.jd_skill_table import Jd_Skill          # noqa: F401
# from app.database.application_models import Application   # noqa: F401

# from app.services.jd_processor import process_pdf_jd
# from app.services.resume_processor import process_and_link_resume

# # Ensure tables exist
# Base.metadata.create_all(bind=engine)

# # ============================================================
# # PAGE CONFIG + STYLE
# # ============================================================
# st.set_page_config(
#     page_title="Manalot Talent Acquisition System",
#     page_icon="🚀",
#     layout="wide",
# )

# st.markdown("""
#     <style>
#     .main-header { font-size: 2.2rem; color: #1E3A8A; font-weight: 700; margin-bottom: 0.2rem; }
#     .sub-header { font-size: 1.1rem; color: #4B5563; margin-bottom: 1.5rem; }
#     .card { background-color: #F8FAFC; border: 1px solid #E2E8F0; padding: 20px; border-radius: 10px; margin-bottom: 15px; }
#     .badge-top { background-color: #DCFCE7; color: #166534; padding: 4px 10px; border-radius: 6px; font-weight: 600; font-size: 0.85rem; }
#     .badge-strong { background-color: #E0F2FE; color: #0369A1; padding: 4px 10px; border-radius: 6px; font-weight: 600; font-size: 0.85rem; }
#     .badge-moderate { background-color: #FEF3C7; color: #92400E; padding: 4px 10px; border-radius: 6px; font-weight: 600; font-size: 0.85rem; }
#     </style>
# """, unsafe_allow_html=True)


# # ============================================================
# # HELPERS
# # ============================================================
# def get_db_session():
#     return SessionLocal()


# def get_ranked_applications_for_jd(session, jd_id: int, top_n: int):
#     query = text("""
#         SELECT c.id AS candidate_id, c.name AS candidate_name,
#                a.hybrid_score, a.parent_score, a.skill_score
#         FROM applications a
#         JOIN candidates c ON a.candidate_id = c.id
#         WHERE a.jd_id = :jd_id
#         ORDER BY a.hybrid_score DESC
#         LIMIT :top_n
#     """)
#     rows = session.execute(query, {"jd_id": jd_id, "top_n": top_n}).fetchall()
#     return [
#         {
#             "id": r.candidate_id,
#             "name": r.candidate_name,
#             "hybrid_score": r.hybrid_score,
#             "parent_score": r.parent_score,
#             "skill_score": r.skill_score,
#         }
#         for r in rows
#     ]


# def get_candidate_evidence(session, jd_id: int, cand_id: int):
#     sql = text("""
#         SELECT js.skill AS jd_skill, cs.skill AS candidate_skill,
#                (1 - (cs.skill_embedding <=> js.skill_embedding)) AS similarity
#         FROM jd_skill js
#         CROSS JOIN cand_skill cs
#         JOIN candidates c ON cs.cand_id = c.id
#         WHERE js.jd_id = :jd_id AND cs.cand_id = :cand_id
#           AND (1 - (cs.skill_embedding <=> js.skill_embedding)) >= 0.82
#         ORDER BY cs.skill_embedding <=> js.skill_embedding ASC
#         LIMIT 3
#     """)
#     return session.execute(sql, {"jd_id": jd_id, "cand_id": cand_id}).fetchall()


# # ============================================================
# # HEADER
# # ============================================================
# st.markdown('<div class="main-header">🎯 Manalot Autonomous Talent Scout</div>', unsafe_allow_html=True)
# st.markdown('<div class="sub-header">Upload Job Descriptions & Evaluate Candidates via Relational Requisition Pipelines.</div>', unsafe_allow_html=True)

# session = get_db_session()

# # ============================================================
# # SIDEBAR
# # ============================================================
# st.sidebar.header("📁 Document Dropzone")
# uploaded_jd_pdf = st.sidebar.file_uploader("1. Upload Job Description (PDF)", type=["pdf"])
# uploaded_resumes = st.sidebar.file_uploader(
#     "2. Upload Candidate Resumes (PDFs)",
#     type=["pdf"],
#     accept_multiple_files=True,
# )

# with st.sidebar.expander("🛠️ Maintenance Controls"):
#     force_refresh_toggle = st.checkbox("Force Re-parse (Bypass Cache)", value=False)

#     if st.button("🧹 Clear Entire Redis Cache", type="secondary"):
#         try:
#             url = os.getenv("REDIS_URL", "redis://localhost:6380")
#             r = redis.Redis.from_url(url, decode_responses=True)
#             r.flushall()
#             st.sidebar.success("Redis cache flushed!")
#         except Exception as e:
#             st.sidebar.error(f"Error: {e}")


# # ============================================================
# # JD UPLOAD HANDLING
# # ============================================================
# if uploaded_jd_pdf:
#     jd_rows = session.execute(text("SELECT id, title FROM jds ORDER BY id")).fetchall()
#     jd_dict = {row.title: row.id for row in jd_rows}

#     current_jd_title = os.path.splitext(uploaded_jd_pdf.name)[0].replace("_", " ").title()
#     if current_jd_title not in jd_dict:
#         if st.sidebar.button("⚙️ Embed Job Description", type="primary"):
#             with st.spinner("Processing Job Description..."):
#                 try:
#                     jd_id, jd_title = process_pdf_jd(session, uploaded_jd_pdf)
#                     st.sidebar.success(f"Job Description '{jd_title}' embedded successfully!")
#                     st.rerun()
#                 except Exception as e:
#                     st.sidebar.error(f"Failed to embed JD: {e}")


# # ============================================================
# # DASHBOARD
# # ============================================================
# st.subheader("📊 Relational Requisition Shortlist Dashboard")

# jd_rows = session.execute(text("SELECT id, title FROM jds ORDER BY id")).fetchall()
# jd_dict = {row.title: row.id for row in jd_rows}

# if not jd_dict:
#     st.info("No Job Descriptions found in the database. Please upload a JD PDF via the sidebar.")
# else:
#     col_sel1, col_sel2 = st.columns([2, 1])
#     with col_sel1:
#         selected_jd_title = st.selectbox("Select Active Requisition", list(jd_dict.keys()))
#         selected_jd_id = jd_dict[selected_jd_title]
#     with col_sel2:
#         top_n = st.slider("Display Top Candidates", 1, 10, 5)

#     # --------------------------------------------------------
#     # Resume ingestion
#     # --------------------------------------------------------
#     if uploaded_resumes:
#         st.markdown("### 📥 Incremental Application Ingestion")
#         if st.button("🚀 Process Resumes & Link to Requisition", type="primary"):
#             progress = st.progress(0)
#             status = st.empty()
#             errors = []

#             total = len(uploaded_resumes)
#             for idx, res_file in enumerate(uploaded_resumes):
#                 status.text(f"[{idx + 1}/{total}] Embedding {res_file.name}...")
#                 try:
#                     process_and_link_resume(
#                         session,
#                         res_file,
#                         selected_jd_id,
#                         force_refresh=force_refresh_toggle,
#                     )
#                 except Exception as e:
#                     errors.append(f"{res_file.name}: {e}")
#                     st.warning(f"Failed on {res_file.name}: {e}")
#                 progress.progress((idx + 1) / total)

#             if errors:
#                 status.warning(f"Completed with {len(errors)} error(s). Refreshing...")
#             else:
#                 status.success("All resumes linked and scored successfully! Refreshing...")
#             time.sleep(1)
#             st.rerun()

#     # --------------------------------------------------------
#     # Shortlist display
#     # --------------------------------------------------------
#     st.markdown("---")
#     st.subheader(f"🏆 Shortlist for: {selected_jd_title}")

#     ranked_list = get_ranked_applications_for_jd(session, selected_jd_id, top_n)

#     if not ranked_list:
#         st.warning("No candidates have applied to this requisition yet. Upload resumes above to begin.")
#     else:
#         for idx, cand in enumerate(ranked_list, 1):
#             match_pct = (cand["hybrid_score"] or 0) * 100
#             parent_pct = (cand["parent_score"] or 0) * 100
#             skill_pct = (cand["skill_score"] or 0) * 100

#             if match_pct >= 85:
#                 badge = '<span class="badge-top">🌟 Top Tier Match</span>'
#             elif match_pct >= 75:
#                 badge = '<span class="badge-strong">👍 Strong Match</span>'
#             else:
#                 badge = '<span class="badge-moderate">⚠️ Moderate Match</span>'

#             st.markdown(f"""
#             <div class="card">
#                 <h3>Rank #{idx}: {cand['name']}</h3>
#                 <p>{badge} &nbsp;&nbsp;|&nbsp;&nbsp; <b>Hybrid Match Score:</b> {match_pct:.1f}%</p>
#             </div>
#             """, unsafe_allow_html=True)

#             c1, c2 = st.columns([1, 2])
#             with c1:
#                 st.metric("Overall Profile Fit", f"{parent_pct:.1f}%")
#                 st.metric("Core Skill Alignment", f"{skill_pct:.1f}%")
#             with c2:
#                 st.markdown("**🔍 Verifiable Resume Skill Evidence:**")
#                 evidence_rows = get_candidate_evidence(session, selected_jd_id, cand["id"])
#                 if evidence_rows:
#                     for ev in evidence_rows:
#                         st.markdown(
#                             f'- **JD Requirement:** *"{ev.jd_skill}"*  \n'
#                             f'  ↳ **Candidate Match:** *"{ev.candidate_skill}"* '
#                             f'(`{ev.similarity * 100:.0f}%` match)'
#                         )
#                 else:
#                     st.info("No primary skill evidence matches above threshold.")
#             st.markdown("---")

# session.close()

import sys
import os
import time

# Path fix for Streamlit Cloud / local execution
current_dir = os.path.dirname(os.path.abspath(__file__))
if current_dir not in sys.path:
    sys.path.insert(0, current_dir)

import redis
import streamlit as st
from sqlalchemy import text

from app.database.db import SessionLocal, engine, Base

# Register all models with Base.metadata
from app.database.resume_models import Candidate          # noqa: F401
from app.database.candidate_skill_table import Candidate_Skill  # noqa: F401
from app.database.jd_models import JD                     # noqa: F401
from app.database.jd_skill_table import Jd_Skill          # noqa: F401
from app.database.application_models import Application   # noqa: F401

from app.services.jd_processor import process_pdf_jd
from app.services.resume_processor import process_and_link_resume

# Ensure tables exist
Base.metadata.create_all(bind=engine)

# ============================================================
# PAGE CONFIG + STYLE
# ============================================================
st.set_page_config(
    page_title="Manalot Talent Acquisition System",
    page_icon="🚀",
    layout="wide",
)

st.markdown("""
    <style>
    .main-header { font-size: 2.2rem; color: #1E3A8A; font-weight: 700; margin-bottom: 0.2rem; }
    .sub-header { font-size: 1.1rem; color: #4B5563; margin-bottom: 1.5rem; }
    .card { background-color: #F8FAFC; border: 1px solid #E2E8F0; padding: 20px; border-radius: 10px; margin-bottom: 15px; }
    .badge-top { background-color: #DCFCE7; color: #166534; padding: 4px 10px; border-radius: 6px; font-weight: 600; font-size: 0.85rem; }
    .badge-strong { background-color: #E0F2FE; color: #0369A1; padding: 4px 10px; border-radius: 6px; font-weight: 600; font-size: 0.85rem; }
    .badge-moderate { background-color: #FEF3C7; color: #92400E; padding: 4px 10px; border-radius: 6px; font-weight: 600; font-size: 0.85rem; }
    </style>
""", unsafe_allow_html=True)


# ============================================================
# HELPERS
# ============================================================
def get_db_session():
    return SessionLocal()


def get_ranked_applications_for_jd(session, jd_id: int, top_n: int):
    query = text("""
        SELECT c.id AS candidate_id, c.name AS candidate_name,
               a.hybrid_score, a.parent_score, a.skill_score
        FROM applications a
        JOIN candidates c ON a.candidate_id = c.id
        WHERE a.jd_id = :jd_id
        ORDER BY a.hybrid_score DESC
        LIMIT :top_n
    """)
    rows = session.execute(query, {"jd_id": jd_id, "top_n": top_n}).fetchall()
    return [
        {
            "id": r.candidate_id,
            "name": r.candidate_name,
            "hybrid_score": r.hybrid_score,
            "parent_score": r.parent_score,
            "skill_score": r.skill_score,
        }
        for r in rows
    ]


def get_candidate_evidence(session, jd_id: int, cand_id: int):
    sql = text("""
        SELECT js.skill AS jd_skill, cs.skill AS candidate_skill,
               (1 - (cs.skill_embedding <=> js.skill_embedding)) AS similarity
        FROM jd_skill js
        JOIN cand_skill cs
          ON cs.cand_id = :cand_id
         AND 1 - (cs.skill_embedding <=> js.skill_embedding) >= 0.82
        WHERE js.jd_id = :jd_id
        ORDER BY cs.skill_embedding <=> js.skill_embedding ASC
        LIMIT 3
    """)
    return session.execute(sql, {"jd_id": jd_id, "cand_id": cand_id}).fetchall()


# ============================================================
# HEADER
# ============================================================
st.markdown('<div class="main-header">🎯 Manalot Autonomous Talent Scout</div>', unsafe_allow_html=True)
st.markdown('<div class="sub-header">Upload Job Descriptions & Evaluate Candidates via Relational Requisition Pipelines.</div>', unsafe_allow_html=True)

session = get_db_session()

# ============================================================
# SIDEBAR
# ============================================================
st.sidebar.header("📁 Document Dropzone")
uploaded_jd_pdf = st.sidebar.file_uploader("1. Upload Job Description (PDF)", type=["pdf"])
uploaded_resumes = st.sidebar.file_uploader(
    "2. Upload Candidate Resumes (PDFs)",
    type=["pdf"],
    accept_multiple_files=True,
)

with st.sidebar.expander("🛠️ Maintenance Controls"):
    force_refresh_toggle = st.checkbox("Force Re-parse (Bypass Cache)", value=False)

    if st.button("🧹 Clear Entire Redis Cache", type="secondary"):
        try:
            url = os.getenv("REDIS_URL", "redis://localhost:6380")
            r = redis.Redis.from_url(url, decode_responses=True)
            r.flushall()
            st.sidebar.success("Redis cache flushed!")
        except Exception as e:
            st.sidebar.error(f"Error: {e}")


# ============================================================
# JD UPLOAD HANDLING
# ============================================================
if uploaded_jd_pdf:
    jd_rows = session.execute(text("SELECT id, title FROM jds ORDER BY id")).fetchall()
    jd_dict = {row.title: row.id for row in jd_rows}

    current_jd_title = os.path.splitext(uploaded_jd_pdf.name)[0].replace("_", " ").title()
    if current_jd_title not in jd_dict:
        if st.sidebar.button("⚙️ Embed Job Description", type="primary"):
            with st.spinner("Processing Job Description..."):
                try:
                    jd_id, jd_title = process_pdf_jd(session, uploaded_jd_pdf)
                    st.sidebar.success(f"Job Description '{jd_title}' embedded successfully!")
                    st.rerun()
                except Exception as e:
                    st.sidebar.error(f"Failed to embed JD: {e}")


# ============================================================
# DASHBOARD
# ============================================================
st.subheader("📊 Relational Requisition Shortlist Dashboard")

jd_rows = session.execute(text("SELECT id, title FROM jds ORDER BY id")).fetchall()
jd_dict = {row.title: row.id for row in jd_rows}

if not jd_dict:
    st.info("No Job Descriptions found in the database. Please upload a JD PDF via the sidebar.")
else:
    col_sel1, col_sel2 = st.columns([2, 1])
    with col_sel1:
        selected_jd_title = st.selectbox("Select Active Requisition", list(jd_dict.keys()))
        selected_jd_id = jd_dict[selected_jd_title]
    with col_sel2:
        top_n = st.slider("Display Top Candidates", 1, 10, 5)

    # --------------------------------------------------------
    # Resume ingestion
    # --------------------------------------------------------
    if uploaded_resumes:
        st.markdown("### 📥 Incremental Application Ingestion")
        if st.button("🚀 Process Resumes & Link to Requisition", type="primary"):
            progress = st.progress(0)
            status = st.empty()
            errors = []

            total = len(uploaded_resumes)
            for idx, res_file in enumerate(uploaded_resumes):
                status.text(f"[{idx + 1}/{total}] Embedding {res_file.name}...")
                try:
                    process_and_link_resume(
                        session,
                        res_file,
                        selected_jd_id,
                        force_refresh=force_refresh_toggle,
                    )
                except Exception as e:
                    errors.append(f"{res_file.name}: {e}")
                    st.warning(f"Failed on {res_file.name}: {e}")
                progress.progress((idx + 1) / total)

            if errors:
                status.warning(f"Completed with {len(errors)} error(s). Refreshing...")
            else:
                status.success("All resumes linked and scored successfully! Refreshing...")
            time.sleep(1)
            st.rerun()

    # --------------------------------------------------------
    # Shortlist display
    # --------------------------------------------------------
    st.markdown("---")
    st.subheader(f"🏆 Shortlist for: {selected_jd_title}")

    ranked_list = get_ranked_applications_for_jd(session, selected_jd_id, top_n)

    if not ranked_list:
        st.warning("No candidates have applied to this requisition yet. Upload resumes above to begin.")
    else:
        for idx, cand in enumerate(ranked_list, 1):
            match_pct = (cand["hybrid_score"] or 0) * 100
            parent_pct = (cand["parent_score"] or 0) * 100
            skill_pct = (cand["skill_score"] or 0) * 100

            if match_pct >= 85:
                badge = '<span class="badge-top">🌟 Top Tier Match</span>'
            elif match_pct >= 75:
                badge = '<span class="badge-strong">👍 Strong Match</span>'
            else:
                badge = '<span class="badge-moderate">⚠️ Moderate Match</span>'

            st.markdown(f"""
            <div class="card">
                <h3>Rank #{idx}: {cand['name']}</h3>
                <p>{badge} &nbsp;&nbsp;|&nbsp;&nbsp; <b>Hybrid Match Score:</b> {match_pct:.1f}%</p>
            </div>
            """, unsafe_allow_html=True)

            c1, c2 = st.columns([1, 2])
            with c1:
                st.metric("Overall Profile Fit", f"{parent_pct:.1f}%")
                st.metric("Core Skill Alignment", f"{skill_pct:.1f}%")
            with c2:
                st.markdown("**🔍 Verifiable Resume Skill Evidence:**")
                evidence_rows = get_candidate_evidence(session, selected_jd_id, cand["id"])
                if evidence_rows:
                    for ev in evidence_rows:
                        st.markdown(
                            f'- **JD Requirement:** *"{ev.jd_skill}"*  \n'
                            f'  ↳ **Candidate Match:** *"{ev.candidate_skill}"* '
                            f'(`{ev.similarity * 100:.0f}%` match)'
                        )
                else:
                    st.info("No primary skill evidence matches above threshold.")
            st.markdown("---")

session.close()