"""Resume Tailoring Pipeline - Main Agent Assembly."""

from google.adk.agents import SequentialAgent, LlmAgent
from google.adk.apps.app import App
from google.adk.tools import FunctionTool
from google.adk.tools.tool_context import ToolContext

from .config import config
from .agents import (
    resume_template_preparer,
    input_processor,
    job_research_agent,
    experience_refiner_agent,
    experience_bank_saver,
    resume_planner_agent,
    resume_writer_agent,
)


def _set_file_paths(
    work_experience_path: str,
    job_description_path: str,
    current_resume_path: str,
    output_path: str,
    tool_context: ToolContext,
) -> dict:
    """Stores the file paths in session state for the pipeline to use.

    Args:
        work_experience_path: Path to the work experience document (.docx or .pdf)
        job_description_path: Path to the job description document (.docx or .pdf)
        current_resume_path: Path to the current resume document (.docx or .pdf)
        output_path: Where to save the tailored resume (.docx)
        tool_context: The tool context providing access to session state

    Returns:
        dict: Confirmation of stored paths
    """
    tool_context.state["work_experience_path"] = work_experience_path
    tool_context.state["job_description_path"] = job_description_path
    tool_context.state["current_resume_path"] = current_resume_path
    tool_context.state["output_path"] = output_path

    return {
        "status": "success",
        "message": "File paths stored successfully",
        "paths": {
            "work_experience_path": work_experience_path,
            "job_description_path": job_description_path,
            "current_resume_path": current_resume_path,
            "output_path": output_path,
        }
    }


set_file_paths_tool = FunctionTool(func=_set_file_paths)


# Main Pipeline - Strategy-First approach with clear separation of strategy and writing
resume_tailoring_pipeline = SequentialAgent(
    name="resume_tailoring_pipeline",
    description="Strategy-First Resume Tailoring Pipeline: reads inputs, researches job with feasibility analysis, creates strategy document, generates polished resume",
    sub_agents=[
        resume_template_preparer,  # Phase 0: Tag resume template w/ bullet IDs + reserve slots
        input_processor,           # Phase 1: Read documents and detect formatting
        job_research_agent,        # Phase 2: Research job + conservative feasibility analysis
        experience_refiner_agent,  # Phase 3: Content strategist - creates TailoredExperienceBank
        experience_bank_saver,     # Phase 3.5: Save experience bank to JSON file
        resume_planner_agent,      # Phase 3.75: Produce a bullet-level edit plan (auditable)
        resume_writer_agent,       # Phase 4: Apply plan + generate resume docx
    ],
)


# Root agent - wrapper for user interaction
root_agent = LlmAgent(
    name="resume_tailoring_coordinator",
    model=config.worker_model,
    description="Coordinates the resume tailoring process by collecting file paths and delegating to the pipeline",
    instruction="""
You are a resume tailoring assistant. Your job is to help users create tailored resumes
that match specific job descriptions using a Strategy-First approach.

**WORKFLOW:**
1. Collect the required file paths from the user
2. Use the set_file_paths tool to store them in session state
3. Delegate to the resume_tailoring_pipeline to process everything

**REQUIRED INPUTS (collect from user):**
- work_experience_path: Path to the work experience document (.docx or .pdf)
- job_description_path: Path to the job description document (.docx or .pdf)
- current_resume_path: Path to the current resume document (.docx or .pdf)
- output_path: Where to save the tailored resume (.docx) - default: ./tailored_resume.docx

**EXAMPLE USER INPUT:**
"Tailor my resume for this job:
- Work experience: /path/to/my_experience.docx
- Job description: /path/to/job_posting.pdf
- Current resume: /path/to/my_resume.docx
- Output: /path/to/tailored_resume.docx"

**YOUR TASKS:**
1. If the user provides file paths, extract them from the message
2. IMMEDIATELY call the set_file_paths tool with all 4 paths
   - If output_path is not provided, use "./tailored_resume.docx"
3. After set_file_paths succeeds, transfer to resume_tailoring_pipeline

**OUTPUT FILES:**
The pipeline produces TWO output files:
1. Strategy Document: <output_path>_experience_bank.json
   - Contains the content strategy and refined experiences
   - Useful for reviewing what content decisions were made
2. Final Resume: <output_path>
   - Polished .docx file with quantification-heavy bullet points
   - Preserves the formatting style of the original resume

**IMPORTANT:**
- You MUST call set_file_paths tool BEFORE transferring to the pipeline
- All file paths must be absolute paths or relative to the current directory
- The pipeline uses conservative skill matching - only includes skills the candidate clearly has
- If any required path is missing, ask the user to provide it
""",
    tools=[set_file_paths_tool],
    sub_agents=[resume_tailoring_pipeline],
)


# Create the ADK App
app = App(root_agent=root_agent, name="resume_tailoring")
