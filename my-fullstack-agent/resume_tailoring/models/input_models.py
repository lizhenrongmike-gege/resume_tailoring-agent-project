from pydantic import BaseModel, Field
from typing import Optional, Dict, Any


class ProcessedInputs(BaseModel):
    """Structured representation of all input documents."""

    work_experience_content: str = Field(
        description="Full text content from the work experience document"
    )
    job_description_content: str = Field(
        description="Full text content from the job description document"
    )
    current_resume_content: str = Field(
        description="Full text content from the current resume"
    )
    target_job_title: str = Field(
        description="The job title being applied for, extracted from job description"
    )
    target_company: Optional[str] = Field(
        default=None,
        description="The company name, if mentioned in job description"
    )
    resume_format: Optional[Dict[str, Any]] = Field(
        default=None,
        description="Detected formatting from the current resume (fonts, sizes, margins)"
    )
