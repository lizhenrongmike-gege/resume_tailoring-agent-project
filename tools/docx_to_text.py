#!/usr/bin/env python3
"""Extract plain text from a .docx (paragraphs joined by newlines).

Useful for deterministic harnesses that want to consume JD/resume/work-experience
content without running the full ADK pipeline.
"""

from __future__ import annotations

import argparse
from pathlib import Path

from docx import Document


def extract_text(docx_path: Path) -> str:
    doc = Document(str(docx_path))
    paras = [p.text.strip() for p in doc.paragraphs if p.text and p.text.strip()]
    return "\n".join(paras).rstrip() + "\n"


def main() -> None:
    ap = argparse.ArgumentParser()
    ap.add_argument("--in_docx", required=True)
    ap.add_argument("--out_txt", required=True)
    args = ap.parse_args()

    in_path = Path(args.in_docx)
    out_path = Path(args.out_txt)
    out_path.parent.mkdir(parents=True, exist_ok=True)
    out_path.write_text(extract_text(in_path), encoding="utf-8")
    print(str(out_path))


if __name__ == "__main__":
    main()
