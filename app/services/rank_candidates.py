# # # from app.database.db import SessionLocal
# # # from app.database.jd_models import JD
# # # from app.database.resume_models import Candidate
# # # from sqlalchemy import case
# # # from sqlalchemy import case, func

# # # session = SessionLocal()
# # # # Get the JD id
# # # jd_id = 1
# # # jd=session.get(JD,jd_id)
# # # if not jd:
# # #     raise ValueError(
# # #         f"JD with ID {jd_id} not found"
# # #     )

# # # # Match the embedding against each respestive field eg Responsibilities against experience and get the similarity score for each and also the evidence in the resume 
# # # required_skills_similarity = func.coalesce(
# # #     1 - Candidate.skills_embedding.cosine_distance(
# # #         jd.required_skills_embedding
# # #     ),
# # #     0.0
# # # )

# # # preferred_skills_similarity = func.coalesce(
# # #     1 - Candidate.skills_embedding.cosine_distance(
# # #         jd.preferred_skills_embedding
# # #     ),
# # #     0.0
# # # )

# # # responsibilities_similarity = func.coalesce(
# # #     1 - Candidate.experience_embedding.cosine_distance(
# # #         jd.responsibilities_embedding
# # #     ),
# # #     0.0
# # # )

# # # education_similarity = func.coalesce(
# # #     1 - Candidate.education_embedding.cosine_distance(
# # #         jd.education_embedding
# # #     ),
# # #     0.0
# # # )

# # # domain_similarity = func.coalesce(
# # #     1 - Candidate.experience_embedding.cosine_distance(
# # #         jd.domain_embedding
# # #     ),
# # #     0.0
# # # )

# # # industries_similarity = func.coalesce(
# # #     1 - Candidate.experience_embedding.cosine_distance(
# # #         jd.industries_embedding
# # #     ),
# # #     0.0
# # # )

# # # full_resume_similarity = func.coalesce(
# # #     1 - Candidate.embedding.cosine_distance(
# # #         jd.embedding
# # #     ),
# # #     0.0
# # # )
# # # if (
# # #     jd.minimum_experience is not None
# # #     and jd.maximum_experience is not None
# # # ):
# # #     # Example: 10-15 years
# # #     experience_score = case(
# # #         (
# # #             Candidate.experience_years.between(
# # #                 jd.minimum_experience,
# # #                 jd.maximum_experience,
# # #             ),
# # #             1.0,
# # #         ),
# # #         else_=0.0,
# # #     )

# # # elif jd.minimum_experience is not None:
# # #     # Example: 15+ years
# # #     experience_score = case(
# # #         (
# # #             Candidate.experience_years
# # #             >= jd.minimum_experience,
# # #             1.0,
# # #         ),
# # #         else_=0.0,
# # #     )

# # # elif jd.maximum_experience is not None:
# # #     # Example: up to 15 years
# # #     experience_score = case(
# # #         (
# # #             Candidate.experience_years
# # #             <= jd.maximum_experience,
# # #             1.0,
# # #         ),
# # #         else_=0.0,
# # #     )

# # # else:
# # #     # JD doesn't specify experience
# # #     experience_score = 1.0

# # # # Weighted scores
# # # # required_skills_score =(required_skills_similarity)*.30
# # # # responsibilities_score=(responsibilities_similarity)*.30
# # # # experience_year_score=(experience_scores)*0.15
# # # # preferred_skills_score=(preferred_skills_similarity)*0.05
# # # # domain_score=(domain_similarity)*0.05
# # # # industries_score=(industries_similarity)*0.05
# # # # full_resume_score=(full_resume_similarity)*0.05
# # # # education_score=(education_similarity)*0.05


# # # # Total Score =sum(all_scores)
# # # total_score = (
# # #     required_skills_similarity * 0.30
# # #     + responsibilities_similarity * 0.30
# # #     + experience_score * 0.15
# # #     + preferred_skills_similarity * 0.05
# # #     + education_similarity * 0.05
# # #     + domain_similarity * 0.05
# # #     + industries_similarity * 0.05
# # #     + full_resume_similarity * 0.05
# # # )

# # # results = (
# # #     session.query(
# # #         Candidate.id,
# # #         Candidate.name,
# # #         Candidate.experience_years,

# # #         required_skills_similarity.label(
# # #             "required_skills_score"
# # #         ),

# # #         responsibilities_similarity.label(
# # #             "responsibilities_score"
# # #         ),

# # #         experience_score.label(
# # #             "experience_score"
# # #         ),

# # #         preferred_skills_similarity.label(
# # #             "preferred_skills_score"
# # #         ),

# # #         education_similarity.label(
# # #             "education_score"
# # #         ),

# # #         domain_similarity.label(
# # #             "domain_score"
# # #         ),

# # #         industries_similarity.label(
# # #             "industries_score"
# # #         ),

# # #         full_resume_similarity.label(
# # #             "full_resume_score"
# # #         ),

# # #         total_score.label(
# # #             "total_score"
# # #         ),

# # #         # Evidence source text
# # #         Candidate.skills_text,
# # #         Candidate.experience_text,
# # #         Candidate.education_text,
# # #     )
# # #     .order_by(
# # #         total_score.desc()
# # #     )
# # #     .all()
# # # )

# # # if __name__ == "__main__":
# # #     print("JD minimum experience:", jd.minimum_experience)
# # #     print("JD maximum experience:", jd.maximum_experience)


# # #     for rank, candidate in enumerate(
# # #     results,
# # #     start=1
# # # ):

# # #         print(
# # #             f"\nRank #{rank}: "
# # #             f"{candidate.name}"
# # #         )

# # #         print(
# # #             f"Total Score: "
# # #             f"{candidate.total_score * 100:.2f}%"
# # #         )

# # #         print(
# # #             f"Required Skills: "
# # #             f"{candidate.required_skills_score * 100:.2f}%"
# # #         )

# # #         print(
# # #             f"Responsibilities: "
# # #             f"{candidate.responsibilities_score * 100:.2f}%"
# # #         )

# # #         print(
# # #             f"Experience: "
# # #             f"{candidate.experience_score * 100:.2f}%"
# # #         )

# # #         print(
# # #             f"Education: "
# # #             f"{candidate.education_score * 100:.2f}%"
# # #         )
# # #         print("JD minimum experience:", jd.minimum_experience)
# # # print("JD maximum experience:", jd.maximum_experience)

# # """Code 1"""

# # # from app.database.db import SessionLocal
# # # from app.database.jd_models import JD
# # # from app.database.resume_models import Candidate

# # # from sqlalchemy import case, func


# # # session = SessionLocal()


# # # # ============================================================
# # # # GET JD
# # # # ============================================================

# # # jd_id = 1

# # # jd = session.get(JD, jd_id)

# # # if not jd:
# # #     raise ValueError(
# # #         f"JD with ID {jd_id} not found"
# # #     )


# # # # ============================================================
# # # # VECTOR SIMILARITY SCORES
# # # # ============================================================

# # # # JD required skills vs candidate skills
# # # required_skills_similarity = func.coalesce(
# # #     1 - Candidate.skills_embedding.cosine_distance(
# # #         jd.required_skills_embedding
# # #     ),
# # #     0.0,
# # # )


# # # # JD preferred skills vs candidate skills
# # # preferred_skills_similarity = func.coalesce(
# # #     1 - Candidate.skills_embedding.cosine_distance(
# # #         jd.preferred_skills_embedding
# # #     ),
# # #     0.0,
# # # )


# # # # JD responsibilities vs candidate work experience
# # # responsibilities_similarity = func.coalesce(
# # #     1 - Candidate.experience_embedding.cosine_distance(
# # #         jd.responsibilities_embedding
# # #     ),
# # #     0.0,
# # # )


# # # # JD education vs candidate education
# # # education_similarity = func.coalesce(
# # #     1 - Candidate.education_embedding.cosine_distance(
# # #         jd.education_embedding
# # #     ),
# # #     0.0,
# # # )


# # # # JD domain vs candidate work experience
# # # domain_similarity = func.coalesce(
# # #     1 - Candidate.experience_embedding.cosine_distance(
# # #         jd.domain_embedding
# # #     ),
# # #     0.0,
# # # )


# # # # JD industries vs candidate work experience
# # # industries_similarity = func.coalesce(
# # #     1 - Candidate.experience_embedding.cosine_distance(
# # #         jd.industries_embedding
# # #     ),
# # #     0.0,
# # # )


# # # # Full JD vs full resume
# # # full_resume_similarity = func.coalesce(
# # #     1 - Candidate.embedding.cosine_distance(
# # #         jd.embedding
# # #     ),
# # #     0.0,
# # # )


# # # # ============================================================
# # # # EXPERIENCE SCORE
# # # # ============================================================

# # # if (
# # #     jd.minimum_experience is not None
# # #     and jd.maximum_experience is None
# # # ):
# # #     # --------------------------------------------------------
# # #     # Example:
# # #     # JD says 15+ years
# # #     #
# # #     # Candidate 15 years -> 1.00
# # #     # Candidate 14 years -> 14/15 = 0.933
# # #     # Candidate 12 years -> 12/15 = 0.80
# # #     #
# # #     # Anyone above minimum stays at 1.00
# # #     # --------------------------------------------------------

# # #     experience_score = case(

# # #         (
# # #             Candidate.experience_years
# # #             >= jd.minimum_experience,
# # #             1.0,
# # #         ),

# # #         (
# # #             Candidate.experience_years > 0,

# # #             Candidate.experience_years
# # #             / jd.minimum_experience,
# # #         ),

# # #         else_=0.0,
# # #     )


# # # elif (
# # #     jd.minimum_experience is not None
# # #     and jd.maximum_experience is not None
# # # ):
# # #     # --------------------------------------------------------
# # #     # Example:
# # #     # JD says 10-15 years
# # #     #
# # #     # Inside range -> 100%
# # #     # Below minimum -> partial credit
# # #     #
# # #     # For now, candidates above maximum also receive 100%.
# # #     # We generally don't want to punish extra experience yet.
# # #     # --------------------------------------------------------

# # #     experience_score = case(

# # #         (
# # #             Candidate.experience_years
# # #             >= jd.minimum_experience,
# # #             1.0,
# # #         ),

# # #         (
# # #             Candidate.experience_years > 0,

# # #             Candidate.experience_years
# # #             / jd.minimum_experience,
# # #         ),

# # #         else_=0.0,
# # #     )


# # # elif (
# # #     jd.maximum_experience is not None
# # # ):
# # #     # --------------------------------------------------------
# # #     # JD only specifies maximum experience.
# # #     #
# # #     # For now give full experience credit.
# # #     # We can refine overqualification handling later.
# # #     # --------------------------------------------------------

# # #     experience_score = case(

# # #         (
# # #             Candidate.experience_years
# # #             <= jd.maximum_experience,
# # #             1.0,
# # #         ),

# # #         else_=1.0,
# # #     )


# # # else:
# # #     # JD does not specify experience
# # #     experience_score = 1.0


# # # # ============================================================
# # # # WEIGHTS
# # # # ============================================================

# # # REQUIRED_SKILLS_WEIGHT = 0.30
# # # RESPONSIBILITIES_WEIGHT = 0.30
# # # EXPERIENCE_WEIGHT = 0.15
# # # PREFERRED_SKILLS_WEIGHT = 0.05
# # # EDUCATION_WEIGHT = 0.05
# # # DOMAIN_WEIGHT = 0.05
# # # INDUSTRIES_WEIGHT = 0.05
# # # FULL_RESUME_WEIGHT = 0.05


# # # # ============================================================
# # # # FINAL WEIGHTED SCORE
# # # # ============================================================

# # # total_score = (

# # #     required_skills_similarity
# # #     * REQUIRED_SKILLS_WEIGHT

# # #     + responsibilities_similarity
# # #     * RESPONSIBILITIES_WEIGHT

# # #     + experience_score
# # #     * EXPERIENCE_WEIGHT

# # #     + preferred_skills_similarity
# # #     * PREFERRED_SKILLS_WEIGHT

# # #     + education_similarity
# # #     * EDUCATION_WEIGHT

# # #     + domain_similarity
# # #     * DOMAIN_WEIGHT

# # #     + industries_similarity
# # #     * INDUSTRIES_WEIGHT

# # #     + full_resume_similarity
# # #     * FULL_RESUME_WEIGHT
# # # )


# # # # ============================================================
# # # # QUERY ALL CANDIDATES
# # # # ============================================================

# # # results = (

# # #     session.query(

# # #         Candidate.id,

# # #         Candidate.name,

# # #         Candidate.experience_years,

# # #         required_skills_similarity.label(
# # #             "required_skills_score"
# # #         ),

# # #         preferred_skills_similarity.label(
# # #             "preferred_skills_score"
# # #         ),

# # #         responsibilities_similarity.label(
# # #             "responsibilities_score"
# # #         ),

# # #         experience_score.label(
# # #             "experience_score"
# # #         ),

# # #         education_similarity.label(
# # #             "education_score"
# # #         ),

# # #         domain_similarity.label(
# # #             "domain_score"
# # #         ),

# # #         industries_similarity.label(
# # #             "industries_score"
# # #         ),

# # #         full_resume_similarity.label(
# # #             "full_resume_score"
# # #         ),

# # #         total_score.label(
# # #             "total_score"
# # #         ),

# # #         # Evidence source text
# # #         Candidate.skills_text,

# # #         Candidate.experience_text,

# # #         Candidate.education_text,
# # #     )

# # #     # Highest score first
# # #     .order_by(
# # #         total_score.desc()
# # #     )

# # #     .all()
# # # )


# # # # ============================================================
# # # # DISPLAY RANKING
# # # # ============================================================

# # # if __name__ == "__main__":

# # #     print(
# # #         "\nJD:",
# # #         jd.title
# # #     )

# # #     print(
# # #         "JD minimum experience:",
# # #         jd.minimum_experience
# # #     )

# # #     print(
# # #         "JD maximum experience:",
# # #         jd.maximum_experience
# # #     )

# # #     print(
# # #         "\n========================================"
# # #     )

# # #     for rank, candidate in enumerate(
# # #         results,
# # #         start=1,
# # #     ):

# # #         print(
# # #             f"\nRank #{rank}: "
# # #             f"{candidate.name}"
# # #         )

# # #         print(
# # #             f"Candidate Experience: "
# # #             f"{candidate.experience_years} years"
# # #         )

# # #         print(
# # #             f"Total Score: "
# # #             f"{candidate.total_score * 100:.2f}%"
# # #         )

# # #         print(
# # #             f"Required Skills: "
# # #             f"{candidate.required_skills_score * 100:.2f}%"
# # #         )

# # #         print(
# # #             f"Responsibilities: "
# # #             f"{candidate.responsibilities_score * 100:.2f}%"
# # #         )

# # #         print(
# # #             f"Experience Fit: "
# # #             f"{candidate.experience_score * 100:.2f}%"
# # #         )

# # #         print(
# # #             f"Preferred Skills: "
# # #             f"{candidate.preferred_skills_score * 100:.2f}%"
# # #         )

# # #         print(
# # #             f"Education: "
# # #             f"{candidate.education_score * 100:.2f}%"
# # #         )

# # #         print(
# # #             f"Domain: "
# # #             f"{candidate.domain_score * 100:.2f}%"
# # #         )

# # #         print(
# # #             f"Industries: "
# # #             f"{candidate.industries_score * 100:.2f}%"
# # #         )

# # #         print(
# # #             f"Full Resume: "
# # #             f"{candidate.full_resume_score * 100:.2f}%"
# # #         )

# # #         print(
# # #             "----------------------------------------"
# # #         )


# # # session.close()

# # """Code with individual skills matching"""
# # import numpy as np

# # from app.database.db import SessionLocal
# # from app.database.jd_models import JD
# # from app.database.resume_models import Candidate


# # def cosine_similarity(vector_a, vector_b):
# #     a = np.array(vector_a, dtype=float)
# #     b = np.array(vector_b, dtype=float)

# #     denominator = np.linalg.norm(a) * np.linalg.norm(b)

# #     if denominator == 0:
# #         return 0.0

# #     return float(np.dot(a, b) / denominator)


# # session = SessionLocal()

# # try:
# #     # ========================================================
# #     # GET JD
# #     # ========================================================
# #     jd_id = 1
# #     jd = session.get(JD, jd_id)

# #     if not jd:
# #         raise ValueError(f"JD {jd_id} not found")

# #     # ========================================================
# #     # GET ALL CANDIDATES
# #     # ========================================================
# #     candidates = session.query(Candidate).all()

# #     # ========================================================
# #     # GET JD REQUIRED SKILLS
# #     # ========================================================
# #     jd_skills = jd.ind_required_skill_embeddings or []

# #     # ========================================================
# #     # LOOP THROUGH CANDIDATES
# #     # ========================================================
# #     for candidate in candidates:
# #         print(f"\nCandidate: {candidate.name}")

# #         candidate_skills = candidate.skill_embeddings or []
# #         skill_results = []

# #         # ====================================================
# #         # EACH JD REQUIRED SKILL
# #         # ====================================================
# #         for jd_skill_data in jd_skills:
# #             jd_skill = jd_skill_data["skill"]
# #             jd_embedding = jd_skill_data["embedding"]

# #             best_skill = None
# #             best_similarity = -1.0

# #             # ================================================
# #             # COMPARE AGAINST EVERY CANDIDATE SKILL
# #             # ================================================
# #             for candidate_skill_data in candidate_skills:
# #                 candidate_skill = candidate_skill_data["skill"]
# #                 candidate_embedding = candidate_skill_data["embedding"]

# #                 similarity = cosine_similarity(
# #                     jd_embedding,
# #                     candidate_embedding,
# #                 )

# #                 if similarity > best_similarity:
# #                     best_similarity = similarity
# #                     best_skill = candidate_skill

# #             # ================================================
# #             # SAVE BEST MATCH
# #             # ================================================
# #             skill_results.append(
# #                 {
# #                     "required_skill": jd_skill,
# #                     "matched_skill": best_skill,
# #                     "similarity": best_similarity,
# #                 }
# #             )

# #         # ====================================================
# #         # PRINT EVIDENCE
# #         # ====================================================
# #         for result in skill_results:
# #             print(f"\nRequired: {result['required_skill']}")
# #             print(f"Best candidate skill: {result['matched_skill']}")
# #             print(f"Similarity: {result['similarity'] * 100:.2f}%")

# #         # ====================================================
# #         # REQUIRED SKILLS SCORE
# #         # ====================================================
# #         if skill_results:
# #             required_skills_score = sum(
# #                 result["similarity"] for result in skill_results
# #             ) / len(skill_results)
# #         else:
# #             required_skills_score = 0.0

# #         print(
# #             f"\nRequired Skills Score: "
# #             f"{required_skills_score * 100:.2f}%"
# #         )

# # finally:
# #     session.close()

# import sys
# import os
# from sqlalchemy import text

# from app.database.db import SessionLocal

# def rank_candidates_for_jd(jd_id: int, top_n: int = 5):
#     session = SessionLocal()
#     try:
#         # 1. Verify Job Description exists
#         jd_query = text("SELECT id, title FROM jds WHERE id = :jd_id")
#         jd = session.execute(jd_query, {"jd_id": jd_id}).fetchone()
#         if not jd:
#             print(f"Error: Job Description with ID {jd_id} not found.")
#             return

#         print(f"\n==================================================")
#         print(f" RANKING CANDIDATES FOR: [JD #{jd.id}] {jd.title}")
#         print(f"==================================================")

#         # 2. Compute Parent-Level Semantic Similarity
#         parent_sql = text("""
#             SELECT 
#                 c.id AS candidate_id,
#                 c.name AS candidate_name,
#                 (1 - (c.embedding <=> j.embedding)) AS parent_similarity
#             FROM candidates c
#             CROSS JOIN jds j
#             WHERE j.id = :jd_id
#         """)
#         parent_results = {row.candidate_id: {"name": row.candidate_name, "parent_sim": float(row.parent_similarity)} 
#                           for row in session.execute(parent_sql, {"jd_id": jd_id}).fetchall()}

#         # 3. Compute Fine-Grained Skill Match Score (Best matching skill pairs)
#         skill_sql = text("""
#             SELECT 
#                 c.id AS candidate_id,
#                 MAX(1 - (cs.skill_embedding <=> js.skill_embedding)) AS max_skill_similarity
#             FROM jd_skill js
#             CROSS JOIN cand_skill cs
#             JOIN candidates c ON cs.cand_id = c.id
#             WHERE js.jd_id = :jd_id
#             GROUP BY c.id
#         """)
#         # Or alternatively, average top skill matches per candidate for a richer score
#         avg_skill_sql = text("""
#             SELECT 
#                 sub.candidate_id,
#                 AVG(sub.similarity) AS avg_top_skill_similarity
#             FROM (
#                 SELECT 
#                     c.id AS candidate_id,
#                     js.id AS jd_skill_id,
#                     MAX(1 - (cs.skill_embedding <=> js.skill_embedding)) AS similarity
#                 FROM jd_skill js
#                 CROSS JOIN cand_skill cs
#                 JOIN candidates c ON cs.cand_id = c.id
#                 WHERE js.jd_id = :jd_id
#                 GROUP BY c.id, js.id
#             ) sub
#             GROUP BY sub.candidate_id
#         """)
        
#         skill_results = {row.candidate_id: float(row.avg_top_skill_similarity) 
#                          for row in session.execute(avg_skill_sql, {"jd_id": jd_id}).fetchall()}

#         # 4. Combine into a Hybrid Score (e.g., 60% Parent Embed + 40% Fine-Grained Skill Embed)
#         ranked_candidates = []
#         for cand_id, data in parent_results.items():
#             parent_score = data["parent_sim"]
#             skill_score = skill_results.get(cand_id, 0.0)
            
#             # Hybrid formula
#             hybrid_score = (0.6 * parent_score) + (0.4 * skill_score)
            
#             ranked_candidates.append({
#                 "id": cand_id,
#                 "name": data["name"],
#                 "hybrid_score": hybrid_score,
#                 "parent_score": parent_score,
#                 "skill_score": skill_score
#             })

#         # Sort descending by hybrid score
#         ranked_candidates.sort(key=lambda x: x["hybrid_score"], reverse=True)

#         # 5. Display Leaderboard & Top Matching Evidence Skills
#         for idx, cand in enumerate(ranked_candidates[:top_n], 1):
#             print(f"\n#{idx} | {cand['name']} (Candidate ID: {cand['id']})")
#             print(f"    -> Hybrid Match Score : {cand['hybrid_score'] * 100:.2f}%")
#             print(f"    -> Resume Overview Sim: {cand['parent_score'] * 100:.2f}%")
#             print(f"    -> Fine Skill Sim     : {cand['skill_score'] * 100:.2f}%")

#             # Fetch top individual matching skill evidence for this candidate against this JD
#             evidence_sql = text("""
#                 SELECT 
#                     js.skill AS jd_skill,
#                     cs.skill AS candidate_skill,
#                     (1 - (cs.skill_embedding <=> js.skill_embedding)) AS similarity
#                 FROM jd_skill js
#                 CROSS JOIN cand_skill cs
#                 WHERE js.jd_id = :jd_id AND cs.cand_id = :cand_id
#                 ORDER BY cs.skill_embedding <=> js.skill_embedding ASC
#                 LIMIT 3;
#             """)
#             evidence = session.execute(evidence_sql, {"jd_id": jd_id, "cand_id": cand['id']}).fetchall()
#             print(f"    -> Top Skill Evidence:")
#             for ev in evidence:
#                 print(f"       • JD Req: '{ev.jd_skill}' <---> Resume Skill: '{ev.candidate_skill}' (Sim: {ev.similarity * 100:.1f}%)")

#         print(f"\n==================================================")

#     except Exception as e:
#         session.rollback()
#         print(f"Error during candidate ranking: {e}")
#         raise
#     finally:
#         session.close()

# if __name__ == "__main__":
#     # Test ranking for JD ID 1 (Sr. Manager-FP&A)
#     rank_candidates_for_jd(jd_id=1, top_n=5)

import sys
import os
from sqlalchemy import text

from app.database.db import SessionLocal

def rank_candidates_for_jd(jd_id: int, top_n: int = 5):
    session = SessionLocal()
    try:
        # 1. Verify Job Description exists
        jd_query = text("SELECT id, title FROM jds WHERE id = :jd_id")
        jd = session.execute(jd_query, {"jd_id": jd_id}).fetchone()
        if not jd:
            print(f"Error: Job Description with ID {jd_id} not found.")
            return

        print(f"\n" + "=" * 65)
        print(f" 🎯 RECRUITER TALENT ASSESSMENT REPORT")
        print(f" Position: {jd.title} (Requisition #{jd.id})")
        print("=" * 65)

        # 2. Compute Parent-Level Semantic Similarity (Overall Profile Fit)
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

        # 3. Compute Fine-Grained Skill Match Score (Core Skill Alignment)
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

        # 4. Combine into a Hybrid Score (60% Overall Profile + 40% Core Skills)
        ranked_candidates = []
        for cand_id, data in parent_results.items():
            parent_score = data["parent_sim"]
            skill_score = skill_results.get(cand_id, 0.0)
            
            # Hybrid formula
            hybrid_score = (0.6 * parent_score) + (0.4 * skill_score)
            
            ranked_candidates.append({
                "id": cand_id,
                "name": data["name"],
                "hybrid_score": hybrid_score,
                "parent_score": parent_score,
                "skill_score": skill_score
            })

        # Sort descending by match score
        ranked_candidates.sort(key=lambda x: x["hybrid_score"], reverse=True)

        # 5. Display Recruiter Dashboard View
        for idx, cand in enumerate(ranked_candidates[:top_n], 1):
            match_percentage = cand['hybrid_score'] * 100
            
            # Recruiter Rating Tier Badge
            if match_percentage >= 85:
                rating = "🌟 Top Tier Match (Highly Recommended)"
            elif match_percentage >= 75:
                rating = "👍 Strong Match (Good Fit)"
            else:
                rating = "⚠️ Moderate Match (Review Required)"

            print(f"\n[Rank #{idx}] {cand['name'].upper()}")
            print(f"    Status Recommendation : {rating}")
            print(f"    Overall Fit Score     : {match_percentage:.1f}%")
            print(f"      ├─ Overall Experience : {cand['parent_score'] * 100:.1f}%")
            print(f"      └─ Core Skill Match   : {cand['skill_score'] * 100:.1f}%")

            # Fetch top individual matching skill evidence for this candidate against this JD
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
            evidence = session.execute(evidence_sql, {"jd_id": jd_id, "cand_id": cand['id']}).fetchall()
            
            print(f"    🔍 Key Evidence from Resume (Top Skill Matches):")
            for ev in evidence:
                sim_pct = ev.similarity * 100
                print(f"       • Required: \"{ev.jd_skill}\"")
                print(f"         ↳ Matched: \"{ev.candidate_skill}\" ({sim_pct:.0f}% relevance)")

        print(f"\n" + "=" * 65)

    except Exception as e:
        session.rollback()
        print(f"Error during candidate ranking: {e}")
        raise
    finally:
        session.close()

if __name__ == "__main__":
    rank_candidates_for_jd(jd_id=1, top_n=5)
    