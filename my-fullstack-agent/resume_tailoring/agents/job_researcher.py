"""Job Research Agent - Phase 2 of the Resume Tailoring Pipeline."""

from google.adk.agents import LlmAgent, SequentialAgent
from google.adk.tools import google_search

from ..config import config
from ..models import JobResearch


# Stage 1: Execute job research using web search
job_research_executor = LlmAgent(
    name="job_research_executor",
    model=config.worker_model,
    description="Executes job market research using web search",
    instruction="""
You are a job market research specialist. Based on the processed inputs in session state,
conduct comprehensive research on the target job role.

**JOB TITLE FROM STATE:** {processed_inputs}

Look at the target_job_title field from processed_inputs and research:

1. **Industry Standards**: What are the typical requirements and expectations for this role?
2. **Key Skills**: What technical and soft skills are most valued?
3. **Typical Responsibilities**: What do professionals in this role typically do day-to-day?
4. **What Employers Value**: What achievements and qualities make candidates stand out?
5. **Industry Keywords**: What terminology and buzzwords are commonly used?
6. **Certifications**: What certifications are recommended or required?

**RESEARCH APPROACH:**
- Execute 3-5 targeted search queries covering different aspects
- Focus on recent job postings, career guides, and industry insights
- Look for patterns across multiple sources
- Prioritize practical, actionable information

Synthesize your findings into a comprehensive research report covering all the above topics.
""",
    tools=[google_search],
    output_key="raw_job_research",
)


# Stage 2: Parse research AND perform feasibility analysis
research_parser = LlmAgent(
    name="research_parser",
    model=config.worker_model,
    description="Parses raw research into structured JobResearch format with feasibility analysis",
    instruction="""
You are a data extraction specialist and career strategist. Your task is to:
1. Parse the raw job research into a structured format
2. Perform a CONSERVATIVE feasibility analysis against the candidate's experience

**RAW RESEARCH FROM STATE:** {raw_job_research}
**CANDIDATE'S EXPERIENCE FROM STATE:** {processed_inputs}

## PART 1: Extract Job Research

Extract and organize the information into the JobResearch schema:

1. **key_skills**: List all essential technical and soft skills mentioned
   - Include both hard skills (programming languages, tools) and soft skills (communication, leadership)
   - Be comprehensive but avoid duplicates

2. **industry_keywords**: Extract industry-specific terminology
   - Include acronyms, methodologies, frameworks
   - These will be used to optimize resume content

3. **typical_responsibilities**: List common job duties
   - Focus on action-oriented descriptions
   - Include both technical and collaborative responsibilities

4. **what_employers_value**: What makes candidates stand out
   - Include metrics, achievements, and qualities
   - Focus on differentiators

5. **certification_requirements**: List recommended certifications
   - Include both required and "nice to have" certifications
   - Leave empty if none mentioned

## PART 2: Feasibility Analysis

Now perform a CONSERVATIVE feasibility check by comparing JD requirements against the
candidate's work_experience_content and current_resume_content:

**BE CONSERVATIVE:**
- Only mark a skill as "can_fulfill" if the candidate's experience CLEARLY demonstrates it
- If the JD mentions "Java, Python, R" but candidate only shows Python experience, ONLY include Python
- Don't assume skills that aren't explicitly mentioned or demonstrated
- It's better to under-claim than over-claim

For each key requirement from the JD:
1. Determine if candidate's experience clearly demonstrates it (can_fulfill: true/false)
2. Identify which specific experience block demonstrates it (target_experience_block)
3. Rate your confidence (high/medium/low)
4. Add notes explaining why

**OUTPUT:**
Include a complete `feasibility_assessment` with:
- skill_mappings: Detailed mapping for EACH skill/requirement
- skills_candidate_has: ONLY skills with clear evidence
- skills_candidate_lacks: Skills in JD without evidence in experience
- overall_fit_score: Conservative score (0.0-1.0)
- strategy_notes: High-level advice for the Experience Refiner agent

Be thorough, conservative, and specific.
""",
    output_schema=JobResearch,
    output_key="job_research",
    disallow_transfer_to_parent=True,
    disallow_transfer_to_peers=True,
)


# Combine into SequentialAgent
job_research_agent = SequentialAgent(
    name="job_research_agent",
    description="Researches job requirements and performs feasibility analysis for resume tailoring",
    sub_agents=[job_research_executor, research_parser],
)
