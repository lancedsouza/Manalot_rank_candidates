from pydantic import BaseModel, Field

class JDRequirements(BaseModel):
    title:str =Field(default_factory=str,description='Get title for JD eg designation etc')
    required_skills: list[str] = Field(default_factory=list, description="Mandatory technical or soft skills required.")
    preferred_skills: list[str] = Field(default_factory=list, description="Nice-to-have or bonus skills.")
    minimum_experience: float | None = Field(default=None, description="Minimum years of experience required.")
    maximum_experience: float | None = Field(default=None, description="Maximum experience cap, if stated.")
    preferred_education: list[str] = Field(default_factory=list, description="Required degrees, certifications, or educational backgrounds.")
    responsibilities: list[str] = Field(default_factory=list, description="Core day-to-day duties and deliverables.")
    domain: list[str] = Field(default_factory=list, description="Industry domains like FinTech, HealthTech, SaaS, etc.")
    industries: list[str] = Field(default_factory=list, description="Broader industry sectors.")