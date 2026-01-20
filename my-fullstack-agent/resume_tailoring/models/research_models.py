"""Research models for job analysis and feasibility assessment."""

from pydantic import BaseModel, Field
from typing import List, Optional, Literal


class SkillMapping(BaseModel):
    """Maps a JD requirement to candidate's experience."""

    requirement: str = Field(
        description="The skill or requirement from the JD (e.g., 'Python', 'AI Pipelines')"
    )
    can_fulfill: bool = Field(
        description="Whether the candidate's experience clearly demonstrates this skill"
    )
    target_experience_block: Optional[str] = Field(
        default=None,
        description="Which experience block demonstrates this (e.g., 'Agentic Project', 'Work at Company X')"
    )
    confidence: Literal["high", "medium", "low"] = Field(
        description="Confidence level in the skill mapping"
    )
    notes: Optional[str] = Field(
        default=None,
        description="Why this mapping works or what gaps exist"
    )


class FeasibilityAssessment(BaseModel):
    """Feasibility analysis mapping JD requirements to candidate experience."""

    skill_mappings: List[SkillMapping] = Field(
        description="Detailed mapping of each JD requirement to candidate experience"
    )
    skills_candidate_has: List[str] = Field(
        description="Conservative list of skills the candidate clearly demonstrates"
    )
    skills_candidate_lacks: List[str] = Field(
        description="Skills mentioned in JD that candidate does not have evidence for"
    )
    overall_fit_score: float = Field(
        description="Overall fit score from 0.0 to 1.0"
    )
    strategy_notes: str = Field(
        description="High-level strategic notes for the experience refiner agent"
    )


class JobResearch(BaseModel):
    """Structured research output for job requirements."""

    key_skills: List[str] = Field(
        description="List of essential technical and soft skills required for this role"
    )
    industry_keywords: List[str] = Field(
        description="Industry-specific keywords and terminology commonly used in this field"
    )
    typical_responsibilities: List[str] = Field(
        description="Common responsibilities for this role based on industry research"
    )
    what_employers_value: List[str] = Field(
        description="Key attributes and achievements employers look for in candidates"
    )
    certification_requirements: List[str] = Field(
        default_factory=list,
        description="Recommended or required certifications for this role"
    )
    feasibility_assessment: Optional[FeasibilityAssessment] = Field(
        default=None,
        description="Feasibility analysis mapping JD requirements to candidate experience"
    )
