import sys
import os

# Path fix for Streamlit Cloud
sys.path.append(os.path.abspath(os.path.dirname(__file__)))

import streamlit as st
import json
from pypdf import PdfReader
from sqlalchemy import text
from app.database.db import SessionLocal, engine, Base
from app.database.resume_models import Candidate
from app.database.jd_models import JD
from app.database.candidate_skill_table import Candidate_Skill
from app.database.jd_skill_table import Jd_Skill
from app.embedding.embedding_service import create_embeddings

# Ensure tables exist
Base.metadata.create_all(bind=engine)

# Page configuration
st.set_page_config(
    page_title="Manalot Talent Acquisition System",
    page_icon="🚀",
    layout="wide"
)

# Custom Styling
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

def get_db_session():
    return SessionLocal()

def extract_text_from_pdf(uploaded_file):
    reader = PdfReader(uploaded_file)
    text_content = ""
    for page in reader.pages:
        extracted = page.extract_text()
        if extracted:
            text_content += extracted + "\n"
    return text_content.strip()

def process_pdf_jd(session, uploaded_file):
    description = extract_text_from_pdf(uploaded_file)
    if not description:
        raise ValueError("Could not extract text from the JD PDF.")
    
    title = os.path.splitext(uploaded_file.name)[0].replace("_", " ").title()
    
    skills_list = [line.strip() for line in description.split('\n') if len(line.strip()) > 15 and len(line.strip()) < 80][:12]
    if not skills_list:
        skills_list = [title]

    jd_embedding = create_embeddings([description])[0]
    dummy_embedding = [0.0] * 768

    new_JD = JD(
        title=title,
        description=description,
        required_skills=skills_list,
        embedding=jd_embedding,
        responsibilities=["General responsibilities per job description"],
        responsibilities_embedding=jd_embedding,
        education_embedding=dummy_embedding
    )
    session.add(new_JD)
    session.commit()
    session.refresh(new_JD)
    
    jd_skills_data = []
    for skill in skills_list:
        skill_vec = create_embeddings([skill])[0]
        jd_skills_data.append({
            "jd_id": new_JD.id,
            "skill": skill,
            "skill_embedding": skill_vec
        })
    if jd_skills_data:
        session.execute(Jd_Skill.__table__.insert(), jd_skills_data)
        session.commit()
    return new_JD.id, title

def process_pdf_resume(session, uploaded_file):
    raw_text = extract_text_from_pdf(uploaded_file)
    if not raw_text:
        raise ValueError(f"Could not extract text from {uploaded_file.name}.")
        
    name = os.path.splitext(uploaded_file.name)[0].replace("_", " ").title()
    
    skills_list = [line.strip() for line in raw_text.split('\n') if len(line.strip()) > 3 and len(line.strip()) < 40][:15]
    if not skills_list:
        skills_list = ["Professional Experience"]

    resume_embedding = create_embeddings([raw_text])[0]
    skills_text = " ".join(skills_list)
    skills_embedding = create_embeddings([skills_text])[0]

    new_cand = Candidate(
        name=name,
        raw_text=raw_text,
        skills=skills_list,
        embedding=resume_embedding,
        skills_embedding=skills_embedding
    )
    session.add(new_cand)
    session.commit()
    session.refresh(new_cand)

    cand_skills_data = []
    for skill in skills_list:
        skill_vec = create_embeddings([skill])[0]
        cand_skills_data.append({
            "cand_id": new_cand.id,
            "skill": skill,
            "skill_embedding": skill_vec
        })
    if cand_skills_data:
        session.execute(Candidate_Skill.__table__.insert(), cand_skills_data)
        session.commit()
    return new_cand.id, name

def rank_candidates(session, jd_id, top_n):
    parent_sql = text("""
        SELECT c.id AS candidate_id, c.name AS candidate_name, (1 - (c.embedding <=> j.embedding)) AS parent_similarity
        FROM candidates c CROSS JOIN jds j WHERE j.id = :jd_id
    """)
    parent_results = {row.candidate_id: {"name": row.candidate_name, "parent_sim": float(row.parent_similarity)} 
                      for row in session.execute(parent_sql, {"jd_id": jd_id}).fetchall()}

    avg_skill_sql = text("""
        SELECT sub.candidate_id, AVG(sub.similarity) AS avg_top_skill_similarity
        FROM (
            SELECT c.id AS candidate_id, js.id AS jd_skill_id, MAX(1 - (cs.skill_embedding <=> js.skill_embedding)) AS similarity
            FROM jd_skill js CROSS JOIN cand_skill cs JOIN candidates c ON cs.cand_id = c.id
            WHERE js.jd_id = :jd_id GROUP BY c.id, js.id
        ) sub GROUP BY sub.candidate_id
    """)
    skill_results = {row.candidate_id: float(row.avg_top_skill_similarity) 
                     for row in session.execute(avg_skill_sql, {"jd_id": jd_id}).fetchall()}

    ranked_candidates = []
    for cand_id, data in parent_results.items():
        parent_score = data["parent_sim"]
        skill_score = skill_results.get(cand_id, 0.0)
        hybrid_score = (0.6 * parent_score) + (0.4 * skill_score)
        
        ranked_candidates.append({
            "id": cand_id, "name": data["name"],
            "hybrid_score": hybrid_score, "parent_score": parent_score, "skill_score": skill_score
        })

    ranked_candidates.sort(key=lambda x: x["hybrid_score"], reverse=True)
    return ranked_candidates[:top_n]

def get_candidate_evidence(session, jd_id, cand_id):
    evidence_sql = text("""
        SELECT js.skill AS jd_skill, cs.skill AS candidate_skill, (1 - (cs.skill_embedding <=> js.skill_embedding)) AS similarity
        FROM jd_skill js CROSS JOIN cand_skill cs
        WHERE js.jd_id = :jd_id AND cs.cand_id = :cand_id
        ORDER BY cs.skill_embedding <=> js.skill_embedding ASC LIMIT 3;
    """)
    return session.execute(evidence_sql, {"jd_id": jd_id, "cand_id": cand_id}).fetchall()

# --- Streamlit Layout ---
st.markdown('<div class="main-header">🎯 Manalot Autonomous Talent Scout</div>', unsafe_allow_html=True)
st.markdown('<div class="sub-header">Upload a Job Description PDF and Candidate Resume PDFs to instantly rank candidates.</div>', unsafe_allow_html=True)

session = get_db_session()

# Sidebar Upload Portal
st.sidebar.header("📁 Document Dropzone")
uploaded_jd_pdf = st.sidebar.file_uploader("1. Upload Job Description (PDF)", type=["pdf"])
uploaded_resumes = st.sidebar.file_uploader("2. Upload Candidate Resumes (PDF)", type=["pdf"], accept_multiple_files=True)

if st.sidebar.button("⚙️ Process & Embed Documents", type="primary"):
    if uploaded_jd_pdf and uploaded_resumes:
        with st.spinner("Parsing PDFs and generating vector embeddings via Gemini..."):
            jd_id, jd_title = process_pdf_jd(session, uploaded_jd_pdf)
            
            processed_count = 0
            for res_file in uploaded_resumes:
                process_pdf_resume(session, res_file)
                processed_count += 1
                
        st.sidebar.success(f"Processed JD '{jd_title}' and {processed_count} candidate resumes successfully!")
    else:
        st.sidebar.error("Please upload both a JD PDF and at least one Resume PDF.")

# Main Screen: Ranking Dashboard
st.subheader("📊 Recruiter Shortlist Dashboard")
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

    if st.button("🚀 Run AI Ranking Analysis", type="primary"):
        with st.spinner("Scoring candidates against job requirements..."):
            ranked_list = rank_candidates(session, selected_jd_id, top_n)
            
        st.success(f"Generated shortlist for **{selected_jd_title}**!")
        st.markdown("---")
        
        if not ranked_list:
            st.warning("No candidate records found in the database.")
        else:
            for idx, cand in enumerate(ranked_list, 1):
                match_pct = cand['hybrid_score'] * 100
                parent_pct = cand['parent_score'] * 100
                skill_pct = cand['skill_score'] * 100
                
                if match_pct >= 85:
                    badge_html = '<span class="badge-top">🌟 Top Tier Match</span>'
                elif match_pct >= 75:
                    badge_html = '<span class="badge-strong">👍 Strong Match</span>'
                else:
                    badge_html = '<span class="badge-moderate">⚠️ Moderate Match</span>'
                
                with st.container():
                    st.markdown(f"""
                    <div class="card">
                        <h3>Rank #{idx}: {cand['name']}</h3>
                        <p>{badge_html} &nbsp;&nbsp;|&nbsp;&nbsp; <b>Hybrid Match Score:</b> {match_pct:.1f}%</p>
                    </div>
                    """, unsafe_allow_html=True)
                    
                    c1, c2 = st.columns([1, 2])
                    with c1:
                        st.metric("Overall Profile Fit", f"{parent_pct:.1f}%")
                        st.metric("Core Skill Alignment", f"{skill_pct:.1f}%")
                        
                    with c2:
                        st.markdown("**🔍 Verifiable Resume Skill Evidence:**")
                        evidence_rows = get_candidate_evidence(session, selected_jd_id, cand['id'])
                        
                        if evidence_rows:
                            for ev in evidence_rows:
                                st.markdown(f"""
                                - **JD Requirement:** *"{ev.jd_skill}"*  
                                  ↳ **Candidate Match:** *"{ev.candidate_skill}"* (`{ev.similarity * 100:.0f}%` match)
                                """)
                        else:
                            st.info("No skill evidence records found.")
                    st.markdown("---")

session.close()