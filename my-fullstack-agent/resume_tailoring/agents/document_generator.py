"""Document Generator Agent - Phase 4 of the Resume Tailoring Pipeline."""

import json
from google.adk.agents import LlmAgent

from ..config import config
from ..tools import generate_docx_tool


document_generator = LlmAgent(
    name="document_generator",
    model=config.worker_model,
    description="Generates the final resume document in .docx format with original formatting preserved",
    instruction="""
You are a document formatting specialist. Generate the final tailored resume using the
generate_docx_tool, preserving the original resume's formatting.

**INPUTS FROM SESSION STATE:**
- Tailored Experiences: {tailored_experiences}
- Processed Inputs (for contact info and format): {processed_inputs}
- Output Path: {output_path}

**YOUR TASKS:**

1. **Extract Contact Information:**
   - Parse the current_resume_content from processed_inputs
   - Extract: name, email, phone, linkedin (if present)
   - If any field is missing, use a reasonable placeholder or omit

2. **Get Resume Format:**
   - Extract the resume_format from processed_inputs
   - This contains the detected formatting (fonts, sizes, margins) from the original resume
   - Convert it to a JSON string to pass to generate_docx_tool

3. **Prepare Experience Data:**
   - Get experiences list from tailored_experiences
   - Sort by relevance_score (highest first)
   - For each experience, include:
     * title
     * company
     * date_range
     * bullet_points
     * is_fabricated (IMPORTANT: this determines red text)

4. **Prepare Skills Data:**
   - Get skills_section from tailored_experiences
   - These will be displayed as a comma-separated list

5. **Call generate_docx_tool:**
   - output_path: Use {output_path} from session state, or default to "./tailored_resume.docx"
   - name: Extracted from resume
   - email: Extracted from resume
   - phone: Extracted from resume
   - linkedin: Extracted from resume (or null)
   - summary: Use summary_statement from tailored_experiences
   - experiences_json: JSON string of the experiences list
   - skills_json: JSON string of the skills list
   - format_json: JSON string of the resume_format (to preserve original formatting)

**IMPORTANT:**
- The is_fabricated flag MUST be passed correctly for each experience
- Fabricated content will appear in RED in the final document
- The format_json parameter is crucial - it ensures the output resume matches the original's formatting
- If resume_format is null or empty, the tool will use default formatting
- Verify the output_path is valid before generating

**OUTPUT:** Return the result from generate_docx_tool with status and output_path.
""",
    tools=[generate_docx_tool],
    output_key="final_resume",
)
