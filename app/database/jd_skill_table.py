# # from sqlalchemy import Column, Integer, String, ForeignKey
# # from sqlalchemy.orm import relationship
# # from pgvector.sqlalchemy import Vector
# # from app.database.db import Base


# # class Jd_Skill(Base):
# #     __tablename__ = "jd_skill"

# #     id = Column(Integer, primary_key=True, autoincrement=True)
# #     jd_id = Column(Integer, ForeignKey("jds.id"), nullable=False)
    
# #     skill = Column(String, nullable=False)
# #     skill_embedding = Column(Vector(768), nullable=False)

# #     # Matches 'skill_objects' on the JD model
# #     job_description = relationship("JD", back_populates="skill_objects")

# from sqlalchemy import Column, Integer, String, ForeignKey
# from sqlalchemy.orm import relationship
# from pgvector.sqlalchemy import Vector
# from app.database.db import Base
# from app.database.jd_models import JD

# class Jd_Skill(Base):
#     __tablename__ = "jd_skill"

#     id = Column(Integer, primary_key=True, autoincrement=True)
#     jd_id = Column(Integer, ForeignKey("jds.id"), nullable=False)
    
#     skill = Column(String, nullable=False)
#     skill_embedding = Column(Vector(768), nullable=False)

#     # Use string reference
#     job_description = relationship("JD", back_populates="skill_objects")

from sqlalchemy import Column, Integer, String, ForeignKey
from sqlalchemy.orm import relationship
from pgvector.sqlalchemy import Vector

from app.database.db import Base


class Jd_Skill(Base):

    __tablename__ = "jd_skill"

    id = Column(
        Integer,
        primary_key=True,
        autoincrement=True,
    )

    jd_id = Column(
        Integer,
        ForeignKey("jds.id"),
        nullable=False,
    )

    skill = Column(
        String,
        nullable=False,
    )

    skill_embedding = Column(
        Vector(768),
        nullable=False,
    )

    job_description = relationship(
        "JD",
        back_populates="skill_objects",
    )