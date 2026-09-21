import streamlit as st
import pandas as pd
from sqlalchemy import text
from app.database.db import SessionLocal

# Page configuration
st.set_page_config(
    page_title="Manalot Talent Ranker",
    page_icon="🎯",
    layout="wide"
)

# Custom CSS styling for a clean, recruiter-friendly dashboard look
st.markdown("""
    <style>
    .main-header {
        font-size: 2.2rem;
        color: #1E3A8A;
        font-weight: 700;
        margin-bottom: 0.5rem;
    }
    .sub-header {
        font-size: 1.1rem;
        color: #4B5563;
        margin-bottom: 2rem;
    }
    .card {
        background-color: #F8FAFC;
        border: 1px solid #E2E8F0;
        padding: 20px;
        border-radius: 10px;
        margin-bottom: 15px;
    }
    .badge-top {
        background-color: #DCFCE7;
        color: #166534;
        padding: 4px 10px;
        border-radius: 6px;
        font-weight: 600;
        font-size: 0.85rem;
    }
    .badge-strong {
        background-color: #E0F2FE;
        color: #0369A1;
        padding: 4px 10px;
        border-radius: 6px;
        font-weight: 600;
        font-size: 0.85rem;
    }
    .badge-moderate {
        background-color: #FEF3C7;
        color: #92400E;
        padding: 4px 10px;
        border-radius: 6px;
        font-weight: 600;
        font-size: 0.85rem;
    }
    </style>
""", unsafe_allow_html=True)

def get_db_session():
    return SessionLocal()

def load_job_descriptions(session):
    result = session.execute(text("SELECT id, title FROM jds ORDER BY id")).fetchall()
    return {row.title: row.id for row in result}

def rank_candidates(session, jd_id, top_n):
    # 1. Compute Parent-Level Semantic Similarity (Overall Profile Fit)
    parent_sql = text("""
        SELECT 
            c.id AS candidate_id,
            c.name AS candidate_name,
            (1 - (c.embedding <=> j.embedding)) AS parent_similarity
        FROM candidates c
        CROSS JOIN jds j
        WHERE j.id = :jd_id
    """)
    parent_results = {row.candidate_id: {"name": row.candidate_name, "parent_sim": float(row.parent_similarity)} 
                      for row in session.execute(parent_sql, {"jd_id": jd_id}).fetchall()}

    # 2. Compute Fine-Grained Skill Match Score (Core Skill Alignment)
    avg_skill_sql = text("""
        SELECT 
            sub.candidate_id,
            AVG(sub.similarity) AS avg_top_skill_similarity
        FROM (
            SELECT 
                c.id AS candidate_id,
                js.id AS jd_skill_id,
                MAX(1 - (cs.skill_embedding <=> js.skill_embedding)) AS similarity
            FROM jd_skill js
            CROSS JOIN cand_skill cs
            JOIN candidates c ON cs.cand_id = c.id
            WHERE js.jd_id = :jd_id
            GROUP BY c.id, js.id
        ) sub
        GROUP BY sub.candidate_id
    """)
    skill_results = {row.candidate_id: float(row.avg_top_skill_similarity) 
                     for row in session.execute(avg_skill_sql, {"jd_id": jd_id}).fetchall()}

    # 3. Combine into a Hybrid Score (60% Overall Profile + 40% Core Skills)
    ranked_candidates = []
    for cand_id, data in parent_results.items():
        parent_score = data["parent_sim"]
        skill_score = skill_results.get(cand_id, 0.0)
        hybrid_score = (0.6 * parent_score) + (0.4 * skill_score)
        
        ranked_candidates.append({
            "id": cand_id,
            "name": data["name"],
            "hybrid_score": hybrid_score,
            "parent_score": parent_score,
            "skill_score": skill_score
        })

    ranked_candidates.sort(key=lambda x: x["hybrid_score"], reverse=True)
    return ranked_candidates[:top_n]

def get_candidate_evidence(session, jd_id, cand_id):
    evidence_sql = text("""
        SELECT 
            js.skill AS jd_skill,
            cs.skill AS candidate_skill,
            (1 - (cs.skill_embedding <=> js.skill_embedding)) AS similarity
        FROM jd_skill js
        CROSS JOIN cand_skill cs
        WHERE js.jd_id = :jd_id AND cs.cand_id = :cand_id
        ORDER BY cs.skill_embedding <=> js.skill_embedding ASC
        LIMIT 3;
    """)
    return session.execute(evidence_sql, {"jd_id": jd_id, "cand_id": cand_id}).fetchall()

# --- Streamlit UI Layout ---
st.markdown('<div class="main-header">🎯 Manalot Talent Ranking Dashboard</div>', unsafe_allow_html=True)
st.markdown('<div class="sub-header">AI-powered candidate shortlisting with semantic profile matching and verifiable skill evidence.</div>', unsafe_allow_html=True)

session = get_db_session()
try:
    jd_dict = load_job_descriptions(session)
    
    if not jd_dict:
        st.warning("No Job Descriptions found in the database. Please ingest JDs first.")
    else:
        # Sidebar Controls
        st.sidebar.header("📋 Requisition Settings")
        selected_jd_title = st.sidebar.selectbox("Select Job Description", list(jd_dict.keys()))
        selected_jd_id = jd_dict[selected_jd_title]
        
        top_n = st.sidebar.slider("Shortlist Limit", min_value=1, max_value=10, value=5)
        
        st.sidebar.markdown("---")
        st.sidebar.markdown("**Scoring Weights:**")
        st.sidebar.text("• Overall Profile Fit: 60%\n• Core Skill Match: 40%")

        # Main Content Area
        if st.sidebar.button("🚀 Run Candidate Ranking", type="primary"):
            with st.spinner("Analyzing vector embeddings across candidates..."):
                ranked_list = rank_candidates(session, selected_jd_id, top_n)
                
            st.success(f"Successfully ranked candidates for **{selected_jd_title}**!")
            st.markdown("---")
            
            for idx, cand in enumerate(ranked_list, 1):
                match_pct = cand['hybrid_score'] * 100
                parent_pct = cand['parent_score'] * 100
                skill_pct = cand['skill_score'] * 100
                
                # Badge assignment
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
                        <p>{badge_html} &nbsp;&nbsp;|&nbsp;&nbsp; <b>Overall Fit Score:</b> {match_pct:.1f}%</p>
                    </div>
                    """, unsafe_allow_html=True)
                    
                    col1, col2 = st.columns([1, 2])
                    
                    with col1:
                        st.metric("Overall Experience Fit", f"{parent_pct:.1f}%")
                        st.metric("Core Skill Alignment", f"{skill_pct:.1f}%")
                        
                    with col2:
                        st.markdown("**🔍 Top Resume Skill Evidence:**")
                        evidence_rows = get_candidate_evidence(session, selected_jd_id, cand['id'])
                        
                        if evidence_rows:
                            for ev in evidence_rows:
                                st.markdown(f"""
                                - **JD Requirement:** *"{ev.jd_skill}"*  
                                  ↳ **Matched Skill:** *"{ev.candidate_skill}"* (`{ev.similarity * 100:.0f}%` match)
                                """)
                        else:
                            st.info("No fine-grained skill mappings found.")
                            
                    st.markdown("---")

finally:
    session.close()