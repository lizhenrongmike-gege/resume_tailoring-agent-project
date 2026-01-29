"""ADK FunctionTool: validate + gate ResumeEditPlan.

Reads `resume_edit_plan` from session state, lints it, and overwrites the plan with
an auto-gated version (needs_user_ok=True on risky edits).

Also stores `plan_lint_report` in session state for downstream visibility.
"""

from __future__ import annotations

from typing import Any, Dict

from google.adk.tools import FunctionTool
from google.adk.tools.tool_context import ToolContext

from .plan_linter import lint_and_gate_plan


def _validate_and_gate_resume_edit_plan(tool_context: ToolContext) -> Dict[str, Any]:
    plan = tool_context.state.get("resume_edit_plan")
    if not plan:
        return {"status": "error", "message": "No resume_edit_plan found in session state"}

    if not isinstance(plan, dict):
        # ADK sometimes stores pydantic-like objects; try best-effort conversion.
        try:
            plan = plan.model_dump()  # type: ignore[attr-defined]
        except Exception:
            return {
                "status": "error",
                "message": f"resume_edit_plan is not a dict and could not be converted (type={type(plan)})",
            }

    out = lint_and_gate_plan(plan)
    tool_context.state["resume_edit_plan"] = out["gated_plan"]
    tool_context.state["plan_lint_report"] = out["lint_report"]

    flagged = out["lint_report"]["summary"]["flagged_edits"]
    total = out["lint_report"]["summary"]["total_edits"]

    return {
        "status": "success",
        "message": f"Plan linted and gated. Flagged {flagged}/{total} edits (needs_user_ok=true).",
        "summary": out["lint_report"]["summary"],
    }


validate_and_gate_resume_edit_plan_tool = FunctionTool(func=_validate_and_gate_resume_edit_plan)
