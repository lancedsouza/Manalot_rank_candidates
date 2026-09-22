# from sqlalchemy import Column, Integer, String, ForeignKey
# from sqlalchemy.orm import relationship
# from pgvector.sqlalchemy import Vector
# from app.database.db import Base


# class Candidate_Skill(Base):
#     __tablename__ = "cand_skill"

#     id = Column(Integer, primary_key=True, autoincrement=True)
#     cand_id = Column(Integer, ForeignKey("candidates.id"), nullable=False)
    
#     skill = Column(String, nullable=False)
#     skill_embedding = Column(Vector(1024), nullable=False)
    
#     # Matches 'skill_objects' on the Candidate model
#     # Matches 'skill_objects' on the Candidate model
#     candidate = relationship("Candidate", back_populates="skill_objects")

from sqlalchemy import Column, Integer, String, ForeignKey
from sqlalchemy.orm import relationship
from pgvector.sqlalchemy import Vector
from app.database.db import Base

class Candidate_Skill(Base):
    __tablename__ = "cand_skill"

    id = Column(Integer, primary_key=True, autoincrement=True)
    cand_id = Column(Integer, ForeignKey("candidates.id"), nullable=False)
    
    skill = Column(String, nullable=False)
    skill_embedding = Column(Vector(1024), nullable=False)

    # Use string reference to avoid import loops
    candidate = relationship("Candidate", back_populates="skill_objects")