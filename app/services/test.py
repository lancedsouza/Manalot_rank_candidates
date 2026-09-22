
from sqlalchemy import text
from app.database.db import engine

with engine.connect() as conn:
    rows = conn.execute(text("""
        SELECT column_name, is_nullable, column_default
        FROM information_schema.columns
        WHERE table_schema = 'public' AND table_name = 'candidates'
        ORDER BY ordinal_position
    """)).fetchall()
    for r in rows:
        mark = "❌" if r.is_nullable == "NO" and not r.column_default else "  "
        print(f"{mark} {r.column_name:25} nullable={r.is_nullable:3} default={r.column_default}")