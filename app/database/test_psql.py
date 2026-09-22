

from sqlalchemy import text
from app.database.db import engine, Base

from app.database.resume_models import Candidate
from app.database.candidate_skill_table import Candidate_Skill
from app.database.jd_models import JD
from app.database.jd_skill_table import Jd_Skill
from app.database.application_models import Application

print(f"Target DB: {engine.url}")

with engine.begin() as conn:
    conn.execute(text("DROP TABLE IF EXISTS applications CASCADE"))
    conn.execute(text("DROP TABLE IF EXISTS cand_skill CASCADE"))
    conn.execute(text("DROP TABLE IF EXISTS jd_skill CASCADE"))
    conn.execute(text("DROP TABLE IF EXISTS candidates CASCADE"))
    conn.execute(text("DROP TABLE IF EXISTS jds CASCADE"))
    print("Dropped.")

Base.metadata.create_all(bind=engine)
print("Recreated. Now verifying...")

with engine.connect() as conn:
    rows = conn.execute(text("""
        SELECT c.relname, a.attname, a.atttypmod
        FROM pg_attribute a
        JOIN pg_class c ON c.oid = a.attrelid
        JOIN pg_namespace n ON n.oid = c.relnamespace
        WHERE n.nspname = 'public'
          AND c.relkind = 'r'
          AND a.atttypid = (SELECT oid FROM pg_type WHERE typname = 'vector')
          AND a.attnum > 0
          AND NOT a.attisdropped
        ORDER BY c.relname, a.attname
    """)).fetchall()

    all_ok = True
    for r in rows:
        ok = (r.atttypmod == 1024)
        all_ok = all_ok and ok
        print(f"  [{'OK' if ok else 'BAD'}] {r.relname}.{r.attname}: {r.atttypmod}")

    print("\nALL GOOD" if all_ok else "\nSOME COLUMNS STILL WRONG")
