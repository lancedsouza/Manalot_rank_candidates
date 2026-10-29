"""Idempotent column additions for databases created before a model change.

Base.metadata.create_all creates missing tables but never alters existing ones,
and the project has no migration tool yet. Each statement here must be safe to
run on every start.
"""
from sqlalchemy import text

UPGRADES = [
    # ISS-22: candidate identity by email + phone
    "ALTER TABLE candidates ADD COLUMN IF NOT EXISTS email VARCHAR",
    "ALTER TABLE candidates ADD COLUMN IF NOT EXISTS phone VARCHAR",
    "CREATE INDEX IF NOT EXISTS ix_candidates_email ON candidates (email)",
]


def upgrade_schema(engine) -> None:
    with engine.begin() as conn:
        for stmt in UPGRADES:
            conn.execute(text(stmt))
