from app.database.db import SessionLocal
from app.database.resume_models import Candidate

session = SessionLocal()
try:
    for c in session.query(Candidate.id, Candidate.name).all():
        print(f"Candidate ID: {c.id} | Name: {c.name}")
finally:
    session.close()