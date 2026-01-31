"""resume_tailoring package.

This repo has two execution paths:
1) Deterministic tooling (no LLM / no ADK dependency)
2) ADK multi-agent pipeline (requires google-adk installed)

To keep deterministic tooling usable in minimal environments, we avoid importing
ADK modules at import-time.
"""

__all__ = ["root_agent", "app"]


def __getattr__(name: str):
    if name in {"root_agent", "app"}:
        # Lazy import so environments without google-adk can still use
        # `python -m resume_tailoring.cli ...` for deterministic runs.
        from .agent import root_agent, app  # type: ignore

        return {"root_agent": root_agent, "app": app}[name]
    raise AttributeError(name)
