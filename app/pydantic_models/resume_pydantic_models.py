from typing import Optional, List
from pydantic import BaseModel, Field


class Education(BaseModel):
    degree: Optional[str] = None
    institution: Optional[str] = None
    start_date: Optional[str] = None
    end_date: Optional[str] = None


class Experience(BaseModel):
    company: Optional[str] = None
    title: Optional[str] = None
    start_date: Optional[str] = None
    end_date: Optional[str] = None
    responsibilities: List[str] = Field(default_factory=list)


class Resume(BaseModel):
    name: Optional[str] = None
    skills: List[str] = Field(default_factory=list)
    experience_years: Optional[float] = 0.0
    education: List[Education] = Field(default_factory=list)
    experience: List[Experience] = Field(default_factory=list)
    projects: List[str] = Field(default_factory=list)