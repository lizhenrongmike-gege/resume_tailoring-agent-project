#!/usr/bin/env python3
"""Convenience wrapper around tools/dry_run_stub.py.

Why this exists
- The core dry_run_stub expects JD=text and experience_bank=markdown.
- In practice, Mike often provides .docx for both.
- This wrapper accepts either .txt/.md/.docx and produces a reproducible run folder
  with converted intermediate files + the stub artifacts.

Usage
  python tools/run_dry_run_stub.py \
    --jd <JD.(docx|txt|md)> \
    --experience_bank <bank.(docx|md)> \
    --out_dir runs/attachment_test/<timestamp>/dry_run_stub

Outputs (in --out_dir)
- jd.txt (if converted)
- experience_bank.md (if converted)
- jd_profile.json
- evidence_index.json
- selected_evidence.json
- tailored_resume.md
- lint_report.json

Notes
- This is still deterministic (no LLM calls).
- Conversions rely on python-docx (already used elsewhere in this repo).
"""

from __future__ import annotations

import argparse
import os
import sys
from datetime import datetime, timezone
from pathlib import Path

# Ensure imports work when invoked from anywhere.
REPO_ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(REPO_ROOT))

# Local imports (repo tools)
from tools.dry_run_stub import build_artifacts, parse_experience_bank_md  # type: ignore
from tools.docx_to_text import extract_text as docx_extract_text  # type: ignore
from tools.docx_to_experience_bank_md import parse_docx_experiences, to_markdown  # type: ignore


def _read_text(path: Path) -> str:
    return path.read_text(encoding="utf-8")


def _ensure_jd_text(jd_path: Path, out_dir: Path) -> str:
    if jd_path.suffix.lower() in {".txt", ".md"}:
        return _read_text(jd_path)

    if jd_path.suffix.lower() == ".docx":
        jd_txt_path = out_dir / "jd.txt"
        jd_txt_path.write_text(docx_extract_text(jd_path), encoding="utf-8")
        return _read_text(jd_txt_path)

    raise ValueError(f"Unsupported JD format: {jd_path}")


def _ensure_experience_bank_md(bank_path: Path, out_dir: Path) -> str:
    if bank_path.suffix.lower() == ".md":
        return _read_text(bank_path)

    if bank_path.suffix.lower() == ".docx":
        md_path = out_dir / "experience_bank.md"
        blocks = parse_docx_experiences(bank_path)
        md_path.write_text(to_markdown(blocks), encoding="utf-8")
        return _read_text(md_path)

    raise ValueError(f"Unsupported experience bank format: {bank_path}")


def main() -> None:
    ap = argparse.ArgumentParser()
    ap.add_argument("--jd", required=True, help="Path to JD: .docx/.txt/.md")
    ap.add_argument(
        "--experience_bank",
        required=True,
        help="Path to experience bank: .docx/.md (canonical is .md)",
    )
    ap.add_argument("--out_dir", default=None, help="Output directory for artifacts")
    ap.add_argument("--max_exps", type=int, default=4)
    args = ap.parse_args()

    out_dir = Path(args.out_dir) if args.out_dir else None
    if out_dir is None:
        ts = datetime.now(timezone.utc).strftime("%Y%m%dT%H%M%SZ")
        out_dir = Path("runs") / "dry_run_stub" / ts

    out_dir.mkdir(parents=True, exist_ok=True)

    jd_text = _ensure_jd_text(Path(args.jd), out_dir)
    bank_md = _ensure_experience_bank_md(Path(args.experience_bank), out_dir)

    experiences = parse_experience_bank_md(bank_md)
    artifacts = build_artifacts(jd_text, experiences, max_exps=args.max_exps)

    # Write outputs (same names as dry_run_stub.py)
    import json

    def dump(name: str, obj) -> None:
        (out_dir / name).write_text(
            json.dumps(obj, indent=2, ensure_ascii=False), encoding="utf-8"
        )

    dump("jd_profile.json", artifacts["jd_profile"])
    dump("evidence_index.json", artifacts["evidence_index"])
    dump("selected_evidence.json", artifacts["selected_evidence"])
    dump("lint_report.json", artifacts["lint_report"])
    (out_dir / "tailored_resume.md").write_text(
        artifacts["tailored_resume_md"], encoding="utf-8"
    )

    print(str(out_dir))


if __name__ == "__main__":
    # Ensure repo root import style works when invoked from repo root
    os.chdir(Path(__file__).resolve().parents[1])
    main()
