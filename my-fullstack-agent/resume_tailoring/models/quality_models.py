from pydantic import BaseModel, Field
from typing import List, Literal


class QualityFeedback(BaseModel):
    """Structured feedback from quality review."""

    grade: Literal["pass", "fail"] = Field(
        description="'pass' if experiences meet quality standards, 'fail' if refinement needed"
    )
    authenticity_score: float = Field(
        description="Score from 0.0-1.0 indicating how authentic the experiences sound"
    )
    alignment_score: float = Field(
        description="Score from 0.0-1.0 indicating alignment with job requirements"
    )
    feedback_comments: List[str] = Field(
        description="Specific feedback on what needs improvement"
    )
    experiences_to_refine: List[int] = Field(
        default_factory=list,
        description="Indices of experiences that need refinement"
    )
