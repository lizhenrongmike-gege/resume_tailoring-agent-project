"""CLI helpers for the resume_tailoring project.

This module exists to provide a single, reproducible entrypoint for:
- deterministic dry runs (no LLM calls)
- (future) invoking the ADK pipeline

NOTE: The deterministic dry run currently shells out to tools/run_dry_run_stub.py
so it can consume .docx/.md/.txt inputs and emit the standard artifacts.
"""

from __future__ import annotations

import argparse
import os
import subprocess
import sys
from pathlib import Path


def _run_dry_run(args: argparse.Namespace) -> int:
    repo_root = Path(__file__).resolve().parents[2]
    runner = repo_root / "tools" / "run_dry_run_stub.py"

    if not runner.exists():
        raise FileNotFoundError(f"Expected runner at: {runner}")

    out_dir = Path(args.out_dir)
    out_dir.parent.mkdir(parents=True, exist_ok=True)

    cmd = [
        sys.executable,
        str(runner),
        "--jd",
        args.jd,
        "--experience_bank",
        args.experience_bank,
        "--out_dir",
        str(out_dir),
    ]

    # Pass through a consistent UTC timestamp if caller wants it.
    if args.run_id:
        cmd.extend(["--run_id", args.run_id])

    # If the user is running inside a venv, ensure we run with that interpreter.
    env = os.environ.copy()

    print("[resume_tailoring] dry-run command:")
    print(" ", " ".join(cmd))

    proc = subprocess.run(cmd, env=env)
    return int(proc.returncode)


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(prog="resume_tailoring")
    sub = parser.add_subparsers(dest="cmd", required=True)

    p_dry = sub.add_parser(
        "dry-run",
        help="Deterministic run (no LLM) that emits jd_profile/evidence/selected_evidence/tailored_resume/lint_report artifacts",
    )
    p_dry.add_argument("--jd", required=True, help="Path to JD (.docx/.txt/.md)")
    p_dry.add_argument(
        "--experience_bank",
        required=True,
        help="Path to experience bank (.docx/.md)",
    )
    p_dry.add_argument(
        "--out_dir",
        required=True,
        help="Output run folder (will contain the artifacts)",
    )
    p_dry.add_argument(
        "--run_id",
        default=None,
        help="Optional stable run id (otherwise runner uses current UTC timestamp)",
    )
    p_dry.set_defaults(_handler=_run_dry_run)

    args = parser.parse_args(argv)
    return int(args._handler(args))


if __name__ == "__main__":
    raise SystemExit(main())
