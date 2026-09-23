
# from sqlalchemy import text
# from app.database.db import engine

# with engine.begin() as conn:
#     print("Deleting applications...")
#     conn.execute(text("DELETE FROM applications"))

#     print("Deleting jd_skill...")
#     conn.execute(text("DELETE FROM jd_skill"))

#     print("Deleting jds...")
#     conn.execute(text("DELETE FROM jds"))

# print("Done. Candidates + cand_skill preserved.")

# with engine.connect() as conn:
#     for t in ("jds", "jd_skill", "applications", "candidates", "cand_skill"):
#         n = conn.execute(text(f"SELECT COUNT(*) FROM {t}")).scalar()
#         print(f"  {t:15} {n}")



# from sqlalchemy import text
# from app.database.db import engine

# with engine.connect() as conn:
#     rows = conn.execute(text("""
#         SELECT j.id, j.title, COUNT(s.id) AS n_skills
#         FROM jds j LEFT JOIN jd_skill s ON s.jd_id = j.id
#         GROUP BY j.id, j.title
#     """)).fetchall()
#     print("JDs in DB:")
#     for r in rows:
#         print(f"  id={r.id}  title={r.title!r}  skills={r.n_skills}")

#     print("\nFirst 15 JD skills:")
#     skills = conn.execute(text("""
#         SELECT skill FROM jd_skill ORDER BY id LIMIT 15
#     """)).fetchall()
#     for s in skills:
#         print(f"  - {s.skill!r}")
"""
Clear stale JD-related rows so the JD can be re-embedded with the new
LLM-based extractor.

Preserves: candidates, cand_skill
Deletes:   applications, jd_skill, jds
"""
from sqlalchemy import text
from app.database.db import engine


def main():
    print(f"Target DB: {engine.url}")

    with engine.begin() as conn:
        print("Deleting applications...")
        n_app = conn.execute(text("DELETE FROM applications")).rowcount

        print("Deleting jd_skill...")
        n_skill = conn.execute(text("DELETE FROM jd_skill")).rowcount

        print("Deleting jds...")
        n_jd = conn.execute(text("DELETE FROM jds")).rowcount

    print(f"\nDeleted:")
    print(f"  applications: {n_app}")
    print(f"  jd_skill:     {n_skill}")
    print(f"  jds:          {n_jd}")

    print("\nVerifying counts:")
    with engine.connect() as conn:
        for t in ("jds", "jd_skill", "applications", "candidates", "cand_skill"):
            n = conn.execute(text(f"SELECT COUNT(*) FROM {t}")).scalar()
            print(f"  {t:15} {n}")


if __name__ == "__main__":
    main()