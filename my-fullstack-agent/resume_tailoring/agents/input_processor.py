"""Input Processor Agent - Phase 1 of the Resume Tailoring Pipeline."""

from google.adk.agents import LlmAgent

from ..config import config
from ..tools import (
    read_docx_tool,
    read_pdf_tool,
    detect_docx_format_tool,
    detect_pdf_format_tool,
)
from ..models import ProcessedInputs


input_processor = LlmAgent(
    name="input_processor",
    model=config.worker_model,
    description="Reads and processes input documents (work experience, job description, resume) and detects resume formatting",
    instruction="""
You are a document processing specialist. Your task is to read and extract content from the provided documents, and detect the formatting of the current resume.

**INPUT FILE PATHS FROM SESSION STATE:**
- Work experience document: {work_experience_path}
- Job description document: {job_description_path}
- Current resume document: {current_resume_path}

**YOUR TASKS:**

1. **Read Documents:**
   For each file path, determine if it's a .docx or .pdf file based on the extension:
   - For .docx files: use read_docx_tool
   - For .pdf files: use read_pdf_tool
   Read all three documents.

2. **Detect Resume Format:**
   For the current resume document, also detect its formatting:
   - For .docx files: use detect_docx_format_tool
   - For .pdf files: use detect_pdf_format_tool

   This will capture font names, sizes, margins, and other formatting that will be used to style the output resume to match the original.

3. **Extract Key Information:**
   - Extract the target job title from the job description content
   - Extract the company name if mentioned in the job description

4. **Return Results:**
   Return the structured ProcessedInputs with:
   - work_experience_content: the text from the work experience document
   - job_description_content: the text from the job description document
   - current_resume_content: the text from the current resume
   - target_job_title: extracted from job description
   - target_company: extracted from job description (or null if not found)
   - resume_format: the 'format' dict returned by the format detection tool

**IMPORTANT:**
- If a tool returns an error status, report the error clearly
- Extract the job title carefully - it's usually at the beginning of the job description
- The company name may not always be present - that's okay, leave it as null if not found
- Make sure to include the resume_format in your output - this is crucial for preserving the original resume's formatting (fonts, sizes, margins)
""",
    tools=[
        read_docx_tool,
        read_pdf_tool,
        detect_docx_format_tool,
        detect_pdf_format_tool,
    ],
    output_schema=ProcessedInputs,
    output_key="processed_inputs",
)
