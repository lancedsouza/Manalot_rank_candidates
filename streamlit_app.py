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
from app.database.resume_models import Candidate                # noqa: F401
from app.database.candidate_skill_table import Candidate_Skill  # noqa: F401
from app.database.jd_models import JD                           # noqa: F401
from app.database.jd_skill_table import Jd_Skill                # noqa: F401
from app.database.application_models import Application         # noqa: F401

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


def get_candidate_evidence(session, jd_id: int, cand_id: int, limit: int = 10):
    """Return up to `limit` matched skill pairs above threshold."""
    sql = text("""
        SELECT
            js.skill AS jd_skill,
            cs.skill AS candidate_skill,
            (1 - (cs.skill_embedding <=> js.skill_embedding)) AS similarity
        FROM jd_skill js
        JOIN cand_skill cs
          ON cs.cand_id = :cand_id
         AND 1 - (cs.skill_embedding <=> js.skill_embedding) >= 0.72
        WHERE js.jd_id = :jd_id
        ORDER BY (1 - (cs.skill_embedding <=> js.skill_embedding)) DESC
        LIMIT :limit
    """)
    return session.execute(
        sql, {"jd_id": jd_id, "cand_id": cand_id, "limit": limit}
    ).fetchall()


def get_candidate_coverage(session, jd_id: int, cand_id: int, threshold: float = 0.75):
    """Return (matched, total) JD skills for this candidate."""
    sql = text("""
        WITH best AS (
            SELECT MAX(1 - (cs.skill_embedding <=> js.skill_embedding)) AS best_sim
            FROM jd_skill js
            JOIN cand_skill cs ON cs.cand_id = :cand_id
            WHERE js.jd_id = :jd_id
            GROUP BY js.id
        )
        SELECT
            COUNT(*) FILTER (WHERE best_sim >= :threshold) AS matched,
            COUNT(*) AS total
        FROM best
    """)
    r = session.execute(
        sql, {"jd_id": jd_id, "cand_id": cand_id, "threshold": threshold}
    ).first()
    return (int(r.matched or 0), int(r.total or 0))


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
            match_pct  = (cand["hybrid_score"] or 0) * 100
            parent_pct = (cand["parent_score"] or 0) * 100
            skill_pct  = (cand["skill_score"]  or 0) * 100

            if match_pct >= 80:
                badge = '<span class="badge-top">🌟 Top Tier Match</span>'
            elif match_pct >= 65:
                badge = '<span class="badge-strong">👍 Strong Match</span>'
            else:
                badge = '<span class="badge-moderate">⚠️ Moderate Match</span>'

            st.markdown(f"""
            <div class="card">
                <h3>Rank #{idx}: {cand['name']}</h3>
                <p>{badge} &nbsp;&nbsp;|&nbsp;&nbsp; <b>Hybrid Match Score:</b> {match_pct:.1f}%</p>
            </div>
            """, unsafe_allow_html=True)

            matched, total_jd = get_candidate_coverage(
                session, selected_jd_id, cand["id"]
            )

            c1, c2, c3 = st.columns([1, 1, 1])
            with c1:
                st.metric("Overall Profile Fit", f"{parent_pct:.1f}%")
            with c2:
                st.metric("Skill Score", f"{skill_pct:.1f}%")
            with c3:
                pct = (matched / total_jd * 100) if total_jd else 0
                st.metric("JD Skill Coverage", f"{matched}/{total_jd}", f"{pct:.0f}%")

            st.markdown("**🔍 Verifiable Resume Skill Evidence:**")
            evidence_rows = get_candidate_evidence(
                session, selected_jd_id, cand["id"], limit=10
            )
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