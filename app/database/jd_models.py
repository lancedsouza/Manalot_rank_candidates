from sqlalchemy import Column, Integer, String, Float, Text
from sqlalchemy.dialects.postgresql import ARRAY, JSONB
from pgvector.sqlalchemy import Vector
from sqlalchemy.orm import relationship

from app.database.db import Base


class JD(Base):
    __tablename__ = "jds"

    id = Column(
        Integer,
        primary_key=True,
        autoincrement=True,
    )

    title = Column(
        String,
        nullable=False,
    )

    description = Column(
        Text,
        nullable=False,
    )

    # ========================================================
    # STRUCTURED JD DATA
    # ========================================================

    required_skills = Column(
        ARRAY(String),
        nullable=False,
        default=list,
    )

    preferred_skills = Column(
        ARRAY(String),
        nullable=True,
        default=list,
    )

    minimum_experience = Column(
        Float,
        nullable=True,
    )

    maximum_experience = Column(
        Float,
        nullable=True,
    )

    preferred_education = Column(
        ARRAY(String),
        nullable=True,
        default=list,
    )

    responsibilities = Column(
        ARRAY(String),
        nullable=False,
        default=list,
    )

    domain = Column(
        ARRAY(String),
        nullable=True,
        default=list,
    )

    industries = Column(
        ARRAY(String),
        nullable=True,
        default=list,
    )

    # ========================================================
    # EMBEDDINGS
    # ========================================================

    embedding = Column(
        Vector(384),
        nullable=True,
    )

    ind_required_skill_embeddings = Column(
        JSONB,
        nullable=True,
    )

    ind_preferred_skill_embeddings = Column(
        JSONB,
        nullable=True,
    )

    responsibilities_embedding = Column(
        Vector(384),
        nullable=False,
    )

    education_embedding = Column(
        Vector(384),
        nullable=False,
    )

    domain_embedding = Column(
        Vector(384),
        nullable=True,
    )

    industries_embedding = Column(
        Vector(384),
        nullable=True,
    )

    required_skills_embeddings = Column(
        Vector(384),
        nullable=True,
    )

    preferred_skills_embeddings = Column(
        Vector(384),
        nullable=True,
    )

    # PROPERLY INDENTED INSIDE THE JD CLASS:
    # Use string reference so it evaluates lazily
    skill_objects = relationship("Jd_Skill", back_populates="job_description", cascade="all, delete-orphan")

