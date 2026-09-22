from sqlalchemy import Column, Integer, Float, ForeignKey, DateTime, func, UniqueConstraint
from app.database.db import Base

class Application(Base):
    __tablename__ = "applications"

    id = Column(Integer, primary_key=True, index=True)
    jd_id = Column(Integer, ForeignKey("jds.id", ondelete="CASCADE"), nullable=False)
    candidate_id = Column(Integer, ForeignKey("candidates.id", ondelete="CASCADE"), nullable=False)
    
    # Store computed scores for fast retrieval and sorting
    hybrid_score = Column(Float, default=0.0)
    parent_score = Column(Float, default=0.0)
    skill_score = Column(Float, default=0.0)
    
    applied_at = Column(DateTime(timezone=True), server_default=func.now())

    __table_args__ = (
        UniqueConstraint('jd_id', 'candidate_id', name='uq_job_candidate'),
    )