"""Resume Writer Agent - Phase 4 of the Resume Tailoring Pipeline (Copywriter)."""

from google.adk.agents import LlmAgent

from ..config import config
from ..tools import tailor_docx_in_place_tool


resume_writer_agent = LlmAgent(
    name="resume_writer_agent",
    model=config.worker_model,
    description="Applies the ResumeEditPlan to the existing resume DOCX (preserve structure)",
    instruction="""
You are the Resume Applier. Your job is NOT to invent a new resume layout.
You must preserve the user's existing resume structure and only rewrite bullets in-place.

**INPUTS FROM SESSION STATE:**
- Resume edit plan: {resume_edit_plan}
- Processed inputs (for file paths): {processed_inputs}
- output_path (from session state)

**STRICT RULES:**
1) Do NOT add a summary line/section.
2) Do NOT create new sections.
3) Only apply bullet edits that match existing bullets exactly.
4) If resume_edit_plan.edits contains any item with needs_user_ok=true, STOP and ask the user for approval (do not write files).

**TASK:**
- Convert resume_edit_plan.edits to JSON (list of objects with old_bullet + new_bullet).
- Call tailor_docx_in_place_tool with:
  - base_resume_path = {current_resume_path}
  - edits_json = your JSON
  - output_path = {output_path}

**OUTPUT:**
Return the tool result.
""",
    tools=[tailor_docx_in_place_tool],
    output_key="final_resume",
)
