"""
Migrate all pgvector columns from Vector(1024) → Vector(768).

Safe to re-run — it checks the current dimension first and only
alters columns that are still 1024.

Also requires the tables to be empty (no rows). If rows exist, run
clear_all first.
"""
from sqlalchemy import text
from app.database.db import engine


ALTERS = [
    ("candidates",  "embedding"),
    ("candidates",  "skill_embeddings"),
    ("candidates",  "experience_embedding"),
    ("candidates",  "education_embedding"),
    ("cand_skill",  "skill_embedding"),
    ("jds",         "embedding"),
    ("jds",         "responsibilities_embedding"),
    ("jds",         "education_embedding"),
    ("jds",         "domain_embedding"),
    ("jds",         "industries_embedding"),
    ("jds",         "required_skills_embeddings"),
    ("jds",         "preferred_skills_embeddings"),
    ("jd_skill",    "skill_embedding"),
]


def current_dims(conn, table, column):
    """Return the current pgvector dimension for a column, or None."""
    row = conn.execute(text("""
        SELECT a.atttypmod
        FROM pg_attribute a
        JOIN pg_class c ON c.oid = a.attrelid
        JOIN pg_namespace n ON n.oid = c.relnamespace
        WHERE n.nspname = 'public'
          AND c.relname = :table
          AND a.attname = :column
          AND a.atttypmod > 0
    """), {"table": table, "column": column}).first()
    return row[0] if row else None


def row_count(conn, table):
    return conn.execute(text(f"SELECT COUNT(*) FROM {table}")).scalar()


def main():
    print(f"Target DB: {engine.url}")

    # ============================================================
    # 1. Safety check — tables must be empty
    # ============================================================
    tables = sorted({t for t, _ in ALTERS})
    with engine.connect() as conn:
        non_empty = []
        for t in tables:
            n = row_count(conn, t)
            if n > 0:
                non_empty.append((t, n))

    if non_empty:
        print("\nCannot migrate — tables still have rows:")
        for t, n in non_empty:
            print(f"  {t:15} {n} rows")
        print("\nRun `python3 -m app.utils.clear_all` first, then re-run this.")
        return

    print("\nAll tables empty — proceeding with migration.")

    # ============================================================
    # 2. ALTER each column that is still 1024
    # ============================================================
    with engine.begin() as conn:
        altered = 0
        skipped = 0

        for table, column in ALTERS:
            dims = current_dims(conn, table, column)
            if dims is None:
                print(f"  SKIP  {table}.{column} — column not found")
                skipped += 1
                continue

            if dims == 768:
                print(f"  SKIP  {table}.{column} — already 768")
                skipped += 1
                continue

            if dims != 1024:
                print(f"  SKIP  {table}.{column} — unexpected dims {dims}")
                skipped += 1
                continue

            print(f"  ALTER {table}.{column} — 1024 → 768")
            conn.execute(text(
                f"ALTER TABLE {table} ALTER COLUMN {column} TYPE vector(768)"
            ))
            altered += 1

    print(f"\nAltered {altered} columns, skipped {skipped}.")

    # ============================================================
    # 3. Verify
    # ============================================================
    with engine.connect() as conn:
        dims_set = set()
        print("\nVerifying final state:")
        for table, column in ALTERS:
            dims = current_dims(conn, table, column)
            dims_set.add(dims)
            flag = "OK " if dims == 768 else "BAD"
            print(f"  [{flag}] {table:12} {column:32} dims={dims}")

    if dims_set == {768}:
        print("\nMigration succeeded — all columns are 768.")
    else:
        print(f"\nUnexpected dims still present: {dims_set}")


if __name__ == "__main__":
    main()