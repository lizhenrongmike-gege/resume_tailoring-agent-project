"""Tailoring models for experience refinement and resume generation."""

from pydantic import BaseModel, Field
from typing import List, Optional, Literal


# === Legacy models (kept for backward compatibility) ===

class TailoredExperience(BaseModel):
    """A single tailored experience entry (legacy)."""

    title: str = Field(description="Job title or role")
    company: str = Field(description="Company or organization name")
    date_range: str = Field(
        description="Employment period (e.g., 'Jan 2020 - Dec 2022')"
    )
    bullet_points: List[str] = Field(
        description="Achievement-oriented bullet points"
    )
    is_fabricated: bool = Field(
        default=False,
        description="True if this experience was created/significantly enhanced beyond original"
    )
    relevance_score: float = Field(
        default=1.0,
        description="How relevant this experience is to the target job (0.0-1.0)"
    )


class TailoredExperiences(BaseModel):
    """Collection of all tailored experiences (legacy)."""

    experiences: List[TailoredExperience] = Field(
        description="List of tailored work experiences ordered by relevance"
    )
    skills_section: List[str] = Field(
        description="Consolidated skills list aligned with job requirements"
    )
    summary_statement: str = Field(
        description="Professional summary tailored to the target role"
    )


# === New Strategy-First models ===

class RefinedExperience(BaseModel):
    """A single refined experience ready for resume writing."""

    experience_type: Literal["work", "project", "education", "volunteer"] = Field(
        description="Type of experience"
    )
    title: str = Field(
        description="Job title, project name, degree, or role"
    )
    organization: str = Field(
        description="Company, institution, or organization name"
    )
    date_range: str = Field(
        description="Period (e.g., 'Jan 2020 - Dec 2022')"
    )
    location: Optional[str] = Field(
        default=None,
        description="Location (city, state, or remote)"
    )
    narrative: str = Field(
        description="Fluent, interview-ready explanation of this experience"
    )
    key_achievements: List[str] = Field(
        description="High-level achievements (not bullet points yet)"
    )
    skills_demonstrated: List[str] = Field(
        description="Skills this experience proves"
    )
    relevance_to_job: str = Field(
        description="Why this experience matters for the target role"
    )
    priority: int = Field(
        default=1,
        description="Priority order (1 = highest, determines order in resume)"
    )


class TailoredExperienceBank(BaseModel):
    """Complete tailored experience bank - intermediate strategy document."""

    target_job_title: str = Field(
        description="The job title being applied for"
    )
    target_company: Optional[str] = Field(
        default=None,
        description="The company being applied to, if known"
    )
    candidate_name: str = Field(
        description="Candidate's full name"
    )

    # Refined experiences sorted by priority
    experiences: List[RefinedExperience] = Field(
        description="List of refined experiences sorted by priority"
    )

    # Skills section strategy
    technical_skills: List[str] = Field(
        description="Technical skills to highlight"
    )
    soft_skills: List[str] = Field(
        description="Soft skills to highlight"
    )
    tools_and_technologies: List[str] = Field(
        description="Tools, frameworks, and technologies to list"
    )

    # Summary strategy
    summary_narrative: str = Field(
        description="Interview-ready professional summary"
    )
    key_selling_points: List[str] = Field(
        description="Top 3-5 differentiators for this candidate"
    )

    # Metadata
    feasibility_score: float = Field(
        description="Overall fit score from feasibility assessment (0.0-1.0)"
    )
    strategy_notes: str = Field(
        description="Strategic notes about the tailoring approach"
    )
