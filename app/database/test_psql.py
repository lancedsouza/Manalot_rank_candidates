"""
Inspect the dimensions of all pgvector columns in the public schema.
"""
from sqlalchemy import text
from app.database.db import engine


def main():
    with engine.connect() as conn:
        rows = conn.execute(text("""
            SELECT
                c.relname     AS table_name,
                a.attname     AS column_name,
                a.atttypmod   AS dims
            FROM pg_attribute a
            JOIN pg_class c ON c.oid = a.attrelid
            JOIN pg_namespace n ON n.oid = c.relnamespace
            WHERE n.nspname = 'public'
              AND c.relkind = 'r'
              AND a.atttypid = (
                  SELECT oid FROM pg_type WHERE typname = 'vector'
              )
              AND a.attnum > 0
              AND NOT a.attisdropped
            ORDER BY c.relname, a.attname
        """)).fetchall()

    print(f"{len(rows)} pgvector columns found:")
    for r in rows:
        print(f"  {r.table_name:15} {r.column_name:32} dims={r.dims}")

    dims = {r.dims for r in rows}
    if dims == {768}:
        print("\nAll columns are 768-dim. Migration succeeded.")
    elif dims == {1024}:
        print("\nAll columns are still 1024-dim. Migration not run yet.")
    else:
        print(f"\nMixed dims found: {dims}. This will cause errors.")


if __name__ == "__main__":
    main()