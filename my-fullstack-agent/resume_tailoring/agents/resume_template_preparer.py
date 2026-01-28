"""Resume Template Preparer

Runs a tagging pass to create a stable, bookmark-tagged resume template with reserve slots.
This should execute before input processing so downstream agents work against the
same tagged template.
"""

from google.adk.agents import LlmAgent

from ..config import config
from ..tools import tag_resume_template_tool


resume_template_preparer = LlmAgent(
    name="resume_template_preparer",
    model=config.worker_model,
    description="Tags the resume DOCX with bullet IDs + reserve slots and updates current_resume_path",
    instruction="""
You are the Resume Template Preparer.

**INPUTS FROM SESSION STATE:**
- current_resume_path

**TASK:**
1) If current_resume_path is not a .docx file, do nothing.
2) Otherwise, call tag_resume_template_tool to create a tagged copy of the resume
   and update session state so current_resume_path points to the tagged resume.

Use reserve_per_group=1.

Return the tool result.
""",
    tools=[tag_resume_template_tool],
    output_key="resume_template_ready",
)
