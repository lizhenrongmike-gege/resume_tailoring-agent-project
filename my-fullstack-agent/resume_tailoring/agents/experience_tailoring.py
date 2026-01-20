"""Experience Tailoring Loop - Phase 3 of the Resume Tailoring Pipeline."""

from collections.abc import AsyncGenerator

from google.adk.agents import LlmAgent, LoopAgent, BaseAgent
from google.adk.agents.invocation_context import InvocationContext
from google.adk.events import Event, EventActions

from ..config import config
from ..models import TailoredExperiences, QualityFeedback


# Tailoring Agent - creates and enhances experiences
tailoring_agent = LlmAgent(
    name="tailoring_agent",
    model="gemini-3-pro-preview",
    description="Maps experiences to job requirements and creates/enhances content",
    instruction="""
You are a professional resume writer and career coach. Your task is to tailor
work experiences to match the target job requirements.

**INPUTS FROM SESSION STATE:**
- Processed Inputs: {processed_inputs}
- Job Research: {job_research}
- Previous Quality Feedback (if any): {quality_review?}

**YOUR TASKS:**

1. **Analyze Original Content:**
   - Review the work_experience_content from processed_inputs
   - Identify existing experiences that can be mapped to job requirements
   - Note any gaps between current experience and job requirements

2. **Map and Enhance Existing Experiences:**
   - For each relevant experience, enhance bullet points to emphasize:
     * Skills from job_research.key_skills
     * Keywords from job_research.industry_keywords
     * Responsibilities from job_research.typical_responsibilities
   - Quantify achievements where possible (%, $, numbers)
   - Use action verbs (Led, Developed, Implemented, Achieved)
   - Mark these as is_fabricated=False

3. **Create New Experiences (if needed):**
   - If there are significant gaps, create realistic experiences
   - Base them on transferable skills from existing experience
   - Make them plausible and detailed
   - Mark these as is_fabricated=True
   - Assign lower relevance_score (0.6-0.8)

4. **Create Skills Section:**
   - Compile skills that match job_research.key_skills
   - Include skills from both original and enhanced experiences
   - Prioritize most relevant skills first

5. **Write Summary Statement:**
   - Create a compelling 2-3 sentence professional summary
   - Highlight experience level and key qualifications
   - Include target role and key differentiators

**IF QUALITY FEEDBACK EXISTS:**
- Address all feedback_comments from quality_review
- Focus on experiences_to_refine if specified
- Improve authenticity_score if it was low
- Improve alignment_score if it was low

**OUTPUT:** A TailoredExperiences object with all experiences, skills, and summary.
""",
    output_schema=TailoredExperiences,
    output_key="tailored_experiences",
)


# Quality Review Agent - evaluates tailored content
quality_review_agent = LlmAgent(
    name="quality_review_agent",
    model=config.critic_model,
    description="Reviews tailored experiences for authenticity and alignment",
    instruction="""
You are a senior HR professional and resume critic. Evaluate the tailored experiences
for quality, authenticity, and job alignment.

**INPUTS FROM SESSION STATE:**
- Tailored Experiences: {tailored_experiences}
- Job Research: {job_research}
- Original Content: {processed_inputs}

**EVALUATION CRITERIA:**

1. **AUTHENTICITY (authenticity_score: 0.0-1.0)**
   - Do the experiences sound genuine and believable?
   - Are fabricated experiences plausible given the candidate's background?
   - Is the language natural and professional?
   - Are claims realistic and not exaggerated?

2. **ALIGNMENT (alignment_score: 0.0-1.0)**
   - Do experiences address key_skills from job_research?
   - Are industry_keywords incorporated naturally?
   - Do responsibilities match what employers value?
   - Is the summary statement compelling and relevant?

3. **QUALITY CHECKS:**
   - Are bullet points achievement-oriented (not just duties)?
   - Are there quantifiable metrics where appropriate?
   - Is the formatting consistent?
   - Is there good variety in action verbs?

**GRADING RULES:**
- Grade "pass" if:
  * authenticity_score >= 0.7
  * alignment_score >= 0.7
  * No major issues in feedback_comments

- Grade "fail" if:
  * Either score < 0.7
  * Major issues need addressing
  * Fabricated content is too obvious or implausible

**OUTPUT:**
- Provide specific, actionable feedback in feedback_comments
- List indices of experiences needing work in experiences_to_refine
- Be constructive but thorough
""",
    output_schema=QualityFeedback,
    output_key="quality_review",
    disallow_transfer_to_parent=True,
    disallow_transfer_to_peers=True,
)


class QualityChecker(BaseAgent):
    """Checks quality review and escalates to stop loop if grade is 'pass'."""

    def __init__(self, name: str = "quality_checker"):
        super().__init__(name=name)

    async def _run_async_impl(
        self, ctx: InvocationContext
    ) -> AsyncGenerator[Event, None]:
        quality_review = ctx.session.state.get("quality_review")

        if quality_review and quality_review.get("grade") == "pass":
            # Quality passed - stop the loop
            yield Event(author=self.name, actions=EventActions(escalate=True))
        else:
            # Quality failed - continue loop for refinement
            yield Event(author=self.name)


# Combine into LoopAgent
experience_tailoring_loop = LoopAgent(
    name="experience_tailoring_loop",
    description="Iteratively tailors and refines experiences until quality standards are met",
    max_iterations=config.max_tailoring_iterations,
    sub_agents=[
        tailoring_agent,
        quality_review_agent,
        QualityChecker(name="quality_checker"),
    ],
)
