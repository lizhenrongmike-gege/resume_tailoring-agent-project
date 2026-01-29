#!/usr/bin/env python3
"""Minimal end-to-end *deterministic* dry run.

Purpose:
- Prove the repo can generate intermediate artifacts from:
  - Job Description (JD) text
  - Experience bank markdown
- WITHOUT calling any LLMs and WITHOUT touching .docx writing yet.

Outputs (in --out_dir):
- jd_profile.json
- evidence_index.json
- selected_evidence.json
- tailored_resume.md
- lint_report.json

This is intentionally simple: keyword extraction + overlap-based evidence selection.
"""

from __future__ import annotations

import argparse
import json
import os
import re
from dataclasses import dataclass
from datetime import datetime, timezone
from hashlib import sha256
from typing import Dict, List, Tuple


STOPWORDS = {
    "a","an","the","and","or","but","if","then","else","when","while","to","of","in","on","for","with","as","at","by",
    "is","are","was","were","be","been","being","this","that","these","those","it","its","we","our","you","your","they","their",
    "from","into","over","under","within","across","about","than","not","no","yes","will","would","can","could","should","may","might",
    "using","use","used","work","works","working","experience","role","team","skills","ability","responsibilities","requirements",
}


def _read_text(path: str) -> str:
    with open(path, "r", encoding="utf-8") as f:
        return f.read()


def _tokenize(text: str) -> List[str]:
    # Lowercase, keep alphanumerics, split.
    tokens = re.findall(r"[a-zA-Z][a-zA-Z0-9_+.-]{1,}", text.lower())
    return [t for t in tokens if t not in STOPWORDS and len(t) >= 3]


def _top_keywords(text: str, k: int = 40) -> List[Tuple[str, int]]:
    freq: Dict[str, int] = {}
    for t in _tokenize(text):
        freq[t] = freq.get(t, 0) + 1
    return sorted(freq.items(), key=lambda kv: (-kv[1], kv[0]))[:k]


@dataclass
class Experience:
    exp_id: str
    header: str
    company: str | None
    title: str | None
    dates: str | None
    location: str | None
    body: str


def _slug(s: str) -> str:
    s = s.strip().lower()
    s = re.sub(r"[^a-z0-9]+", "_", s)
    return re.sub(r"_+", "_", s).strip("_")


def parse_experience_bank_md(md: str) -> List[Experience]:
    # Blocks start with "## "
    parts = re.split(r"^##\s+", md, flags=re.MULTILINE)
    exps: List[Experience] = []

    # parts[0] is preamble (likely empty)
    for p in parts[1:]:
        lines = p.splitlines()
        header = lines[0].strip()
        body = "\n".join(lines[1:]).strip()

        company = title = dates = location = None
        # Expected header format: Company | Title | Location | Dates
        if "|" in header:
            fields = [f.strip() for f in header.split("|")]
            if len(fields) >= 1:
                company = fields[0] or None
            if len(fields) >= 2:
                title = fields[1] or None
            if len(fields) >= 3:
                location = fields[2] or None
            if len(fields) >= 4:
                dates = fields[3] or None

        base = " ".join([x for x in [company, title, dates] if x]) or header
        exp_id = _slug(base)

        exps.append(
            Experience(
                exp_id=exp_id,
                header=header,
                company=company,
                title=title,
                dates=dates,
                location=location,
                body=body,
            )
        )

    return exps


def sentence_snippets(text: str) -> List[str]:
    # Very lightweight sentence splitter.
    # Keep reasonably long sentences.
    raw = re.split(r"(?<=[.!?])\s+", re.sub(r"\s+", " ", text.strip()))
    return [s.strip() for s in raw if len(s.strip()) >= 60]


def score_overlap(jd_keywords: set[str], text: str) -> int:
    toks = set(_tokenize(text))
    return len(jd_keywords.intersection(toks))


def build_artifacts(jd_text: str, experiences: List[Experience], max_exps: int = 4) -> dict:
    jd_kw = _top_keywords(jd_text, k=60)
    jd_kw_set = {k for k, _ in jd_kw}

    # Score each experience by keyword overlap.
    scored: List[Tuple[int, Experience]] = []
    for e in experiences:
        s = score_overlap(jd_kw_set, e.body + " " + (e.header or ""))
        scored.append((s, e))

    scored.sort(key=lambda x: (-x[0], x[1].exp_id))
    selected = [e for s, e in scored if s > 0][:max_exps]

    # For each selected experience: pick top sentences as "evidence snippets".
    selected_evidence = []
    for e in selected:
        snippets = sentence_snippets(e.body)
        sn_scored = sorted(
            ((score_overlap(jd_kw_set, sn), sn) for sn in snippets),
            key=lambda x: (-x[0], -len(x[1])),
        )
        top = [sn for s, sn in sn_scored if s > 0][:3]
        if not top:
            # Fall back: first ~240 chars of body as a snippet.
            top = [e.body[:240] + ("..." if len(e.body) > 240 else "")]

        selected_evidence.append(
            {
                "exp_id": e.exp_id,
                "header": e.header,
                "score": score_overlap(jd_kw_set, e.body + " " + (e.header or "")),
                "snippets": top,
            }
        )

    # Keyword coverage: keywords that appear in selected evidence snippets.
    covered = set()
    for item in selected_evidence:
        for sn in item["snippets"]:
            covered |= set(_tokenize(sn))

    top_kw = [k for k, _ in jd_kw][:40]
    missing_top_kw = [k for k in top_kw if k not in covered]

    jd_profile = {
        "generated_at": datetime.now(timezone.utc).isoformat(),
        "jd_hash": sha256(jd_text.encode("utf-8")).hexdigest()[:16],
        "top_keywords": [{"keyword": k, "count": c} for k, c in jd_kw],
    }

    evidence_index = {
        "generated_at": datetime.now(timezone.utc).isoformat(),
        "experience_count": len(experiences),
        "experiences": [
            {
                "exp_id": e.exp_id,
                "header": e.header,
                "company": e.company,
                "title": e.title,
                "location": e.location,
                "dates": e.dates,
                "body": e.body,
            }
            for e in experiences
        ],
    }

    lint_report = {
        "generated_at": datetime.now(timezone.utc).isoformat(),
        "selected_experience_count": len(selected_evidence),
        "top_keywords": top_kw,
        "missing_top_keywords": missing_top_kw,
        "keyword_coverage_rate": (1 - (len(missing_top_kw) / max(1, len(top_kw)))),
        "notes": [
            "This is a deterministic stub: overlap scoring only.",
            "Missing keywords are not necessarily bad; they can flag areas to review.",
        ],
    }

    tailored_md_lines = []
    tailored_md_lines.append("# Tailored Resume Draft (stub)")
    tailored_md_lines.append("")
    tailored_md_lines.append("This file is generated WITHOUT an LLM. It only rearranges/quotes existing experience text as draft bullets with evidence references.")
    tailored_md_lines.append("")

    for item in selected_evidence:
        tailored_md_lines.append(f"## {item['header']}")
        tailored_md_lines.append("")
        for i, sn in enumerate(item["snippets"], start=1):
            # Evidence ref is deterministic.
            ref = f"(evidence: {item['exp_id']}#sn{i})"
            # Make it bullet-like without rewriting claims.
            bullet = sn
            tailored_md_lines.append(f"- {bullet} {ref}")
        tailored_md_lines.append("")

    tailored_resume_md = "\n".join(tailored_md_lines).strip() + "\n"

    return {
        "jd_profile": jd_profile,
        "evidence_index": evidence_index,
        "selected_evidence": {
            "generated_at": datetime.now(timezone.utc).isoformat(),
            "selected": selected_evidence,
        },
        "tailored_resume_md": tailored_resume_md,
        "lint_report": lint_report,
    }


def main() -> None:
    ap = argparse.ArgumentParser()
    ap.add_argument("--jd", required=True, help="Path to job description text (txt/md)")
    ap.add_argument("--experience_bank", required=True, help="Path to experience bank markdown")
    ap.add_argument("--out_dir", default=None, help="Output directory for artifacts")
    ap.add_argument("--max_exps", type=int, default=4)
    args = ap.parse_args()

    jd_text = _read_text(args.jd)
    bank_md = _read_text(args.experience_bank)

    out_dir = args.out_dir
    if not out_dir:
        ts = datetime.now(timezone.utc).strftime("%Y%m%dT%H%M%SZ")
        out_dir = os.path.join("runs", "dry_run_stub", ts)

    os.makedirs(out_dir, exist_ok=True)

    experiences = parse_experience_bank_md(bank_md)
    artifacts = build_artifacts(jd_text, experiences, max_exps=args.max_exps)

    def dump(name: str, obj) -> None:
        with open(os.path.join(out_dir, name), "w", encoding="utf-8") as f:
            json.dump(obj, f, indent=2, ensure_ascii=False)

    dump("jd_profile.json", artifacts["jd_profile"])
    dump("evidence_index.json", artifacts["evidence_index"])
    dump("selected_evidence.json", artifacts["selected_evidence"])
    dump("lint_report.json", artifacts["lint_report"])

    with open(os.path.join(out_dir, "tailored_resume.md"), "w", encoding="utf-8") as f:
        f.write(artifacts["tailored_resume_md"])

    print(out_dir)


if __name__ == "__main__":
    main()
