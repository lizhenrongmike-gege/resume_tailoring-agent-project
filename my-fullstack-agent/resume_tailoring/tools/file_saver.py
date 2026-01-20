"""File saving tool for persisting intermediate results to disk."""

import json
import os
from typing import Optional
from google.adk.tools import FunctionTool
from google.adk.tools.tool_context import ToolContext


def _save_experience_bank(
    experience_bank_json: str,
    output_path: Optional[str] = None,
    tool_context: Optional[ToolContext] = None,
) -> dict:
    """Saves the TailoredExperienceBank to disk as JSON.

    Args:
        experience_bank_json: JSON string of the TailoredExperienceBank.
        output_path: Full path where the JSON file should be saved. If not provided,
                     derives from session state output_path.
        tool_context: The tool context providing access to session state.

    Returns:
        dict: Contains 'status', 'output_path', and optional 'error_message'.
    """
    try:
        # If output_path not provided, derive from session state
        if not output_path and tool_context:
            base_path = tool_context.state.get("output_path", "./tailored_resume.docx")
            if base_path.endswith(".docx"):
                output_path = base_path.replace(".docx", "_experience_bank.json")
            else:
                output_path = os.path.join(base_path, "tailored_experience_bank.json")
        elif not output_path:
            output_path = "./tailored_experience_bank.json"
        # Parse JSON to validate and pretty-print
        data = json.loads(experience_bank_json)

        # Ensure directory exists
        os.makedirs(os.path.dirname(output_path) or ".", exist_ok=True)

        # Write to file with pretty formatting
        with open(output_path, "w", encoding="utf-8") as f:
            json.dump(data, f, indent=2, ensure_ascii=False)

        return {
            "status": "success",
            "output_path": output_path,
            "message": f"Experience bank saved to {output_path}",
        }

    except json.JSONDecodeError as e:
        return {
            "status": "error",
            "output_path": output_path,
            "error_message": f"Invalid JSON: {str(e)}",
        }
    except Exception as e:
        return {
            "status": "error",
            "output_path": output_path,
            "error_message": str(e),
        }


# Create FunctionTool instance
save_experience_bank_tool = FunctionTool(func=_save_experience_bank)
