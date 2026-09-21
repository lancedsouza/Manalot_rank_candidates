import numpy as np

from app.database.db import SessionLocal
from app.database.jd_models import JD
from app.database.resume_models import Candidate


def cosine_similarity(vector_a, vector_b):
    a = np.array(vector_a, dtype=float)
    b = np.array(vector_b, dtype=float)

    denominator = np.linalg.norm(a) * np.linalg.norm(b)

    if denominator == 0:
        return 0.0

    return float(np.dot(a, b) / denominator)


def evaluate_candidates(jd_id: int = 1, similarity_threshold: float = 0.78):
    session = SessionLocal()

    # Define exclusion filters for soft skills to prevent tools/mismatched domains from winning
    # Key concept -> words/substrings that are NOT allowed to match it
    FORBIDDEN_KEYWORDS = {
        "communication": ["excel", "accounting", "audit", "tax", "reconciliation", "sap", "tableau", "hana"],
        "presentation": ["excel", "accounting", "audit", "tax", "reconciliation", "sap", "tableau", "hana"],
        "stakeholder": ["excel", "audit", "invoicing", "billing", "tax"],
    }

    try:
        # 1. Fetch Job Description
        jd = session.get(JD, jd_id)
        if not jd:
            raise ValueError(f"JD with ID {jd_id} not found")

        print(f"\nEvaluating Job Description: {jd.title}")
        print("=" * 60)

        # 2. Fetch Candidates
        candidates = session.query(Candidate).all()
        if not candidates:
            print("No candidates found in the database.")
            return

        jd_skills = jd.ind_required_skill_embeddings or []

        # 3. Loop Through Candidates
        for candidate in candidates:
            print(f"\nCandidate: {candidate.name}")
            print("-" * 50)

            candidate_skills_dict = candidate.skill_embeddings or {}
            if not candidate_skills_dict:
                print("  - [SKIPPED] No individual skill embeddings found for this candidate.")
                continue

            skill_results = []

            # 4. Compare Each Required JD Skill
            for jd_skill_data in jd_skills:
                jd_skill = jd_skill_data["skill"]
                jd_embedding = jd_skill_data["embedding"]
                jd_skill_lower = jd_skill.lower()

                best_skill = None
                best_similarity = -1.0

                for candidate_skill, candidate_embedding in candidate_skills_dict.items():
                    if not candidate_embedding:
                        continue

                    candidate_skill_lower = candidate_skill.lower()

                    # Check guardrails: Skip this candidate skill if it violates any forbidden keywords for this requirement
                    is_forbidden = False
                    for key, forbidden_list in FORBIDDEN_KEYWORDS.items():
                        if key in jd_skill_lower:
                            if any(bad_word in candidate_skill_lower for bad_word in forbidden_list):
                                is_forbidden = True
                                break
                    
                    if is_forbidden:
                        continue

                    similarity = cosine_similarity(jd_embedding, candidate_embedding)

                    if similarity > best_similarity:
                        best_similarity = similarity
                        best_skill = candidate_skill

                # 5. Apply Threshold Validation
                is_matched = best_similarity >= similarity_threshold and best_skill is not None
                
                skill_results.append(
                    {
                        "required_skill": jd_skill,
                        "matched_skill": best_skill if is_matched else "No valid match (Gap)",
                        "similarity": best_similarity if is_matched else 0.0,
                        "is_matched": is_matched,
                    }
                )

            # Print Granular Breakdown
            for result in skill_results:
                status = "MATCHED ✅" if result["is_matched"] else "GAP ❌"
                print(f"  * [{result['similarity'] * 100:5.1f}%] {status} : {result['required_skill']}")
                if result["is_matched"]:
                    print(f"    -> Matched with: {result['matched_skill']}")

            # 6. Calculate Hybrid Final Score (Coverage + Quality)
            if skill_results:
                matched_items = [r for r in skill_results if r["is_matched"]]
                coverage_ratio = len(matched_items) / len(skill_results)
                avg_quality = (
                    sum(r["similarity"] for r in matched_items) / len(matched_items)
                    if matched_items
                    else 0.0
                )
                
                # Weighted blend: 60% requirement coverage, 40% semantic match precision
                final_score = (coverage_ratio * 0.6) + (avg_quality * 0.4)
            else:
                final_score = 0.0

            print(f"\n  ==> Final Candidate Match Score: {final_score * 100:.2f}%\n")

    finally:
        session.close()


if __name__ == "__main__":
    evaluate_candidates()