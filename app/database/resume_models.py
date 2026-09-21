# from sqlalchemy import (
#     Column,
#     Integer,
#     String,
#     Float,
#     Text,
#     ForeignKey,
# )
# from app.database.candidate_skill_table import Candidate_Skill
# from sqlalchemy.dialects.postgresql import ARRAY, JSONB
# from pgvector.sqlalchemy import Vector
# from sqlalchemy.orm import relationship

# from app.database.db import Base


# class Candidate(Base):
#     __tablename__ = "candidates"

#     # ========================================================
#     # BASIC DATA
#     # ========================================================

#     id = Column(
#         Integer,
#         primary_key=True,
#         autoincrement=True,
#     )

#     name = Column(
#         String,
#         nullable=True,
#     )

#     experience_years = Column(
#         Float,
#         nullable=True,
#     )

#     # ========================================================
#     # STRUCTURED RESUME DATA
#     # ========================================================

#     skills = Column(
#         ARRAY(String),
#         nullable=False,
#         default=list,
#     )

#     education = Column(
#         JSONB,
#         nullable=False,
#         default=list,
#     )

#     experience = Column(
#         JSONB,
#         nullable=False,
#         default=list,
#     )

#     projects = Column(
#         ARRAY(String),
#         nullable=False,
#         default=list,
#     )

#     # ========================================================
#     # TEXT USED TO CREATE EMBEDDINGS
#     # ========================================================

#     resume_text = Column(
#         Text,
#         nullable=False,
#     )

#     skills_text = Column(
#         Text,
#         nullable=True,
#     )

#     experience_text = Column(
#         Text,
#         nullable=True,
#     )

#     education_text = Column(
#         Text,
#         nullable=True,
#     )

#     # ========================================================
#     # FIELD-LEVEL EMBEDDINGS
#     # ========================================================

#     embedding = Column(
#         Vector(768),
#         nullable=False,
#     )

#     skills_embedding = Column(
#         Vector(768),
#         nullable=True,
#     )

#     experience_embedding = Column(
#         Vector(768),
#         nullable=True,
#     )

#     education_embedding = Column(
#         Vector(768),
#         nullable=True,
#     )

    
#     skill_objects = relationship(
#         "Candidate_Skill",
#         back_populates="candidate",
#         cascade="all, delete-orphan",
#     )

from sqlalchemy import (
    Column,
    Integer,
    String,
    Float,
    Text,
    ForeignKey,
)
from sqlalchemy.dialects.postgresql import ARRAY, JSONB
from pgvector.sqlalchemy import Vector
from sqlalchemy.orm import relationship

from app.database.db import Base

# Explicitly import the child model so SQLAlchemy registers it before Candidate maps
from app.database.candidate_skill_table import Candidate_Skill


class Candidate(Base):
    __tablename__ = "candidates"

    # ========================================================
    # BASIC DATA
    # ========================================================

    id = Column(
        Integer,
        primary_key=True,
        autoincrement=True,
    )

    name = Column(
        String,
        nullable=True,
    )

    experience_years = Column(
        Float,
        nullable=True,
    )

    # ========================================================
    # STRUCTURED RESUME DATA
    # ========================================================

    skills = Column(
        ARRAY(String),
        nullable=False,
        default=list,
    )

    education = Column(
        JSONB,
        nullable=False,
        default=list,
    )

    experience = Column(
        JSONB,
        nullable=False,
        default=list,
    )

    projects = Column(
        ARRAY(String),
        nullable=False,
        default=list,
    )

    # ========================================================
    # TEXT USED TO CREATE EMBEDDINGS
    # ========================================================

    resume_text = Column(
        Text,
        nullable=False,
    )

    skills_text = Column(
        Text,
        nullable=True,
    )

    experience_text = Column(
        Text,
        nullable=True,
    )

    education_text = Column(
        Text,
        nullable=True,
    )

    # ========================================================
    # FIELD-LEVEL EMBEDDINGS
    # ========================================================

    embedding = Column(
        Vector(768),
        nullable=False,
    )

    # Explicitly mapped to the database column name "skill_embeddings" to match Neon
    skills_embedding = Column(
        "skill_embeddings",
        Vector(768),
        nullable=True,
    )

    experience_embedding = Column(
        Vector(768),
        nullable=True,
    )

    education_embedding = Column(
        Vector(768),
        nullable=True,
    )

    # ========================================================
    # RELATIONSHIPS
    # ========================================================

    skill_objects = relationship(
        "Candidate_Skill",
        back_populates="candidate",
        cascade="all, delete-orphan",
    )