"""Planning models for deterministic-ish resume tailoring.

Goal:
- Separate *reasoning* (what to change) from *rendering* (how to edit the DOCX).
- Provide an auditable plan that can be validated and re-run.

These models are intentionally small for v1.
"""

from __future__ import annotations

from pydantic import BaseModel, Field
from typing import List, Optional


class EvidenceCitation(BaseModel):
    """Where a claim is supported by the user's work-experience bank."""

    source_experience: str = Field(
        description="Which experience paragraph supports this (e.g. 'Ant Group | Risk Management Analyst')."
    )
    quote: Optional[str] = Field(
        default=None,
        description="Optional short supporting quote from the experience bank (<= 200 chars).",
    )


class BulletEdit(BaseModel):
    """Edit plan for a single bullet line in the existing resume."""

    experience: str = Field(
        description="Which resume section/experience this bullet belongs to (e.g. 'Ant Group')."
    )

    bullet_id: Optional[str] = Field(
        default=None,
        description=(
            "Preferred identifier for this bullet (bookmark ID inside the DOCX). "
            "If present, the applier should use this instead of old_bullet."
        ),
    )

    old_bullet: Optional[str] = Field(
        default=None,
        description="Fallback: exact bullet text as it appears in the current resume.",
    )

    new_bullet: str = Field(
        description=(
            "Replacement bullet. Must be truthful and grounded in evidence. "
            "Should be <= ~180 chars for 1-page friendliness."
        )
    )
    evidence: List[EvidenceCitation] = Field(
        default_factory=list,
        description="Evidence citations supporting this bullet.",
    )

    # Human-in-the-loop flag for "new bullet" type changes that rely on inference.
    needs_user_ok: bool = Field(
        default=False,
        description=(
            "True if the bullet is a reasonable inference but not explicitly stated in the experience bank. "
            "If true, the system should ask the user to approve before writing."
        ),
    )


class ResumeEditPlan(BaseModel):
    """A deterministic-ish plan for editing the resume in-place."""

    target_company: Optional[str] = Field(default=None)
    target_role: Optional[str] = Field(default=None)
    edits: List[BulletEdit] = Field(description="List of bullet edits to apply.")

    notes: str = Field(
        description=(
            "Short reasoning notes: what was emphasized, what was not claimed, any risks/assumptions."
        )
    )
