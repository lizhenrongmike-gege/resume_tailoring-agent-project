"""Plan Validator Agent - gates ResumeEditPlan before writing.

This is a deterministic guardrail step between resume_planner_agent and
resume_writer_agent.

It runs a linter that flags 'buzzword drift' / loss of specificity and marks
those edits as needs_user_ok=true so the writer halts for explicit approval.
"""

from google.adk.agents import LlmAgent

from ..config import config
from ..tools import validate_and_gate_resume_edit_plan_tool


plan_validator_agent = LlmAgent(
    name="plan_validator_agent",
    model=config.worker_model,
    description="Deterministically lint + gate the ResumeEditPlan before applying edits",
    instruction="""
You are a validator. Do not rewrite the plan yourself.

**INPUTS FROM SESSION STATE:**
- resume_edit_plan

**TASK:**
- Call validate_and_gate_resume_edit_plan_tool exactly once.

**OUTPUT:**
- Return the tool result.
""",
    tools=[validate_and_gate_resume_edit_plan_tool],
    output_key="plan_validation",
)
