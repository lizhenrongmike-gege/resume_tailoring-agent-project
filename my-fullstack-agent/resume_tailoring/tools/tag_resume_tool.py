"""ADK tool: tag a resume DOCX with bullet bookmark IDs + reserve slots.

This tool creates a tagged copy of the resume and (optionally) updates
session state to point current_resume_path at the tagged file.

It is designed to run once per resume template and be safe to re-run.
"""

from __future__ import annotations

from pathlib import Path
from typing import Optional

from google.adk.tools import FunctionTool
from google.adk.tools.tool_context import ToolContext

from .docx_tagger import tag_docx_bullets


def _tag_resume_template(
    current_resume_path: str,
    tagged_resume_path: Optional[str] = None,
    reserve_per_group: int = 1,
    tool_context: Optional[ToolContext] = None,
) -> dict:
    """Create a tagged resume template and update session state.

    Args:
      current_resume_path: Path to the user's base resume DOCX.
      tagged_resume_path: Optional explicit output path. If omitted, writes
        next to current_resume_path with suffix `_tagged.docx`.
      reserve_per_group: How many reserve bullet slots to add per bullet group.
      tool_context: ADK tool context.

    Returns:
      status + output path + counts.
    """

    try:
        in_path = Path(current_resume_path)
        if not tagged_resume_path:
            tagged_resume_path = str(in_path.with_name(in_path.stem + "_tagged" + in_path.suffix))

        out_path = Path(tagged_resume_path)
        out_path.parent.mkdir(parents=True, exist_ok=True)

        # Always re-generate to ensure new bullets get tags/reserves; this is deterministic.
        res = tag_docx_bullets(
            base_path=in_path,
            out_path=out_path,
            prefix="B",
            reserve_per_group=reserve_per_group,
        )

        if tool_context is not None:
            tool_context.state["current_resume_path"] = str(out_path)
            tool_context.state["tagged_resume_path"] = str(out_path)

        return {
            "status": "success",
            "current_resume_path": str(in_path),
            "tagged_resume_path": str(out_path),
            "tagged_bullets": res.tagged_bullets,
            "reserve_bullets_added": res.reserve_bullets_added,
        }

    except Exception as e:
        return {"status": "error", "error_message": str(e)}


tag_resume_template_tool = FunctionTool(func=_tag_resume_template)
