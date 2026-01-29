#!/usr/bin/env python3
"""Convert a Work Experience .docx into the repo's Experience Bank markdown format.

Why:
- Mike's "work experience" attachment is a .docx, but our deterministic dry_run_stub
  expects the experience bank in markdown blocks starting with "## ".
- This creates a lightweight bridge so we can test end-to-end artifacts on real inputs
  without introducing LLM or planner behavior yet.

Heuristic format supported (matches Mike's attachment):
- Experience header line: "Company | Title" (pipe-separated)
- Next line often: "Location | Dates" (pipe-separated)
- Followed by 1+ paragraphs describing the work.

Output markdown format:
- Each experience becomes:
  ## Company | Title | Location | Dates
  <paragraphs...>

This script is intentionally conservative; if it can't infer location/dates it leaves
fields blank rather than guessing.
"""

from __future__ import annotations

import argparse
from dataclasses import dataclass
from pathlib import Path
from typing import List, Optional

from docx import Document


@dataclass
class ExpBlock:
    header: str
    body_paragraphs: List[str]


def _clean(s: str) -> str:
    return " ".join((s or "").strip().split())


def _looks_like_header(line: str) -> bool:
    line = _clean(line)
    if "|" not in line:
        return False
    # Avoid treating location/date lines as headers.
    lower = line.lower()
    if any(m in lower for m in ["jan", "feb", "mar", "apr", "may", "jun", "jul", "aug", "sep", "oct", "nov", "dec"]):
        return False
    # Simple guard: needs at least 2 non-empty fields.
    fields = [f.strip() for f in line.split("|")]
    return sum(1 for f in fields if f) >= 2


def _looks_like_loc_dates(line: str) -> bool:
    line = _clean(line)
    if "|" not in line:
        return False
    lower = line.lower()
    return any(m in lower for m in ["jan", "feb", "mar", "apr", "may", "jun", "jul", "aug", "sep", "oct", "nov", "dec"])


def parse_docx_experiences(docx_path: Path) -> List[ExpBlock]:
    doc = Document(str(docx_path))
    paras = [_clean(p.text) for p in doc.paragraphs if _clean(p.text)]

    blocks: List[ExpBlock] = []
    i = 0
    while i < len(paras):
        line = paras[i]
        if not _looks_like_header(line):
            i += 1
            continue

        company_title = line
        location_dates: Optional[str] = None
        if i + 1 < len(paras) and _looks_like_loc_dates(paras[i + 1]):
            location_dates = paras[i + 1]
            i += 1

        header_fields = [f.strip() for f in company_title.split("|")]
        company = header_fields[0] if len(header_fields) >= 1 else ""
        title = header_fields[1] if len(header_fields) >= 2 else ""

        location = ""
        dates = ""
        if location_dates:
            ld = [f.strip() for f in location_dates.split("|")]
            location = ld[0] if len(ld) >= 1 else ""
            dates = ld[1] if len(ld) >= 2 else ""

        md_header = " | ".join([company, title, location, dates]).rstrip()

        body: List[str] = []
        i += 1
        while i < len(paras) and not _looks_like_header(paras[i]):
            body.append(paras[i])
            i += 1

        blocks.append(ExpBlock(header=md_header, body_paragraphs=body))

    return blocks


def to_markdown(blocks: List[ExpBlock]) -> str:
    out: List[str] = []
    out.append("# Experience Bank (converted from .docx)")
    out.append("")

    for b in blocks:
        out.append(f"## {b.header}")
        out.append("")
        for p in b.body_paragraphs:
            out.append(p)
            out.append("")

    return "\n".join(out).rstrip() + "\n"


def main() -> None:
    ap = argparse.ArgumentParser()
    ap.add_argument("--in_docx", required=True, help="Path to work experience .docx")
    ap.add_argument("--out_md", required=True, help="Path to output markdown")
    args = ap.parse_args()

    in_path = Path(args.in_docx)
    out_path = Path(args.out_md)

    blocks = parse_docx_experiences(in_path)
    md = to_markdown(blocks)

    out_path.parent.mkdir(parents=True, exist_ok=True)
    out_path.write_text(md, encoding="utf-8")

    print(str(out_path))


if __name__ == "__main__":
    main()
