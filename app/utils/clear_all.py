"""
Full wipe — deletes rows from every embedding-related table.

Required before running a dimension migration (1024 → 768), because
ALTER COLUMN cannot run while rows with the old dimension exist.

Deletes:   applications, cand_skill, jd_skill, candidates, jds
Preserves: nothing
"""
from sqlalchemy import text
from app.database.db import engine


def main():
    print(f"Target DB: {engine.url}")

    with engine.begin() as conn:
        print("Deleting dependent rows first...")
        for tbl in ("applications", "cand_skill", "jd_skill"):
            n = conn.execute(text(f"DELETE FROM {tbl}")).rowcount
            print(f"  {tbl:15} deleted {n}")

        print("Deleting parent rows...")
        for tbl in ("candidates", "jds"):
            n = conn.execute(text(f"DELETE FROM {tbl}")).rowcount
            print(f"  {tbl:15} deleted {n}")

    print("\nVerifying counts:")
    with engine.connect() as conn:
        for t in ("jds", "jd_skill", "applications", "candidates", "cand_skill"):
            n = conn.execute(text(f"SELECT COUNT(*) FROM {t}")).scalar()
            print(f"  {t:15} {n}")


if __name__ == "__main__":
    main()