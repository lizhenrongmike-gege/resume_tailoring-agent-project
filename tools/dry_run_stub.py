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

Recent improvement:
- Evidence snippet extraction now enforces **section/paragraph boundaries** so snippets don’t
  “bleed” across unrelated paragraphs when we normalize whitespace.
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
    # Articles / conjunctions / prepositions
    "a",
    "an",
    "the",
    "and",
    "or",
    "but",
    "if",
    "then",
    "else",
    "when",
    "while",
    "to",
    "of",
    "in",
    "on",
    "for",
    "with",
    "as",
    "at",
    "by",
    "from",
    "into",
    "over",
    "under",
    "within",
    "across",
    "about",
    "than",
    # Pronouns / auxiliaries
    "is",
    "are",
    "was",
    "were",
    "be",
    "been",
    "being",
    "this",
    "that",
    "these",
    "those",
    "it",
    "its",
    "we",
    "our",
    "you",
    "your",
    "they",
    "their",
    "not",
    "no",
    "yes",
    "will",
    "would",
    "can",
    "could",
    "should",
    "may",
    "might",
    # Generic job/resume words we want to down-weight for retrieval
    "using",
    "use",
    "used",
    "work",
    "works",
    "working",
    "experience",
    "role",
    "team",
    "skills",
    "skill",
    "ability",
    "responsibilities",
    "requirements",
    "requirement",
    "responsible",
    "strong",
    "excellent",
    "knowledge",
    "proficient",
    "familiar",
    "help",
    "support",
    "including",
    "include",
    "etc",
    # Generic tech-ish words that are usually too broad to help
    "data",
    "analysis",
    "analytics",
    "model",
    "models",
    "system",
    "systems",
    "process",
    "processes",
    "results",
    "result",
    "impact",
    "business",
    "yield",
    "technical",
}

# Common multi-word skills/phrases we want to recognize deterministically.
# Represented as tuples of tokens.
PHRASE_WHITELIST = {
    ("time", "series"),
    ("machine", "learning"),
    ("deep", "learning"),
    ("data", "pipeline"),
    ("etl", "pipeline"),
    ("sql", "server"),
    ("risk", "management"),
    ("natural", "language"),
    ("language", "model"),
    ("large", "language"),
    ("language", "models"),
    ("high", "frequency"),
    ("real", "time"),
}

# Tokens that are often too generic in JDs/resumes.
GENERIC_TOKENS = {
    "data",
    "analysis",
    "analytics",
    "model",
    "models",
    "project",
    "projects",
    "business",
    "team",
    "stakeholders",
    "stakeholder",
    "solution",
    "solutions",
    "insight",
    "insights",
    "optimize",
    "optimization",
    "improve",
    "improvement",
    "develop",
    "developed",
    "building",
    "built",
}

# Deterministic priors used to stabilize experience selection.
#
# Goal: when overlap scores are close, prefer experiences that are:
# - more recent
# - contain more hard skills/tools (SQL, Python, ETL, forecasting, ...)
# - optionally “pinned” by the user (env var)
HARD_SKILL_TOKENS = {
    "python",
    "sql",
    "excel",
    "tableau",
    "powerbi",
    "power_bi",
    "spark",
    "pyspark",
    "hadoop",
    "airflow",
    "dbt",
    "etl",
    "pipeline",
    "pipelines",
    "forecast",
    "forecasting",
    "nowcasting",
    "time_series",
    "regression",
    "classification",
    "clustering",
    "nlp",
    "llm",
}

# Weighting knobs (keep overlap dominant).
OVERLAP_MULTIPLIER = 10
HARD_SKILL_BOOST_PER_MATCH = 2
PINNED_EXP_BONUS = 25  # additive to total score
RECENCY_BOOST_MAX = 6  # additive to total score (scaled 0..RECENCY_BOOST_MAX)


def _read_text(path: str) -> str:
    with open(path, "r", encoding="utf-8") as f:
        return f.read()


def _tokenize_unigrams(text: str) -> List[str]:
    """Tokenize into unigram tokens.

    Notes:
    - This is deterministic and intentionally simple.
    - We keep common JD/resume tokens like "etl" / "sql" / "kpi" (>=3 chars)
      but drop high-noise stopwords.
    """

    raw = re.findall(r"[a-zA-Z][a-zA-Z0-9_+.-]{1,}", text.lower())
    tokens = [t.strip(".,;:()[]{}<>\"'!") for t in raw]
    return [t for t in tokens if t and t not in STOPWORDS and len(t) >= 3]


def _extract_terms(text: str) -> List[str]:
    """Extract retrieval terms (unigrams + selected bigrams).

    We represent bigrams as "token1_token2".
    """

    uni = _tokenize_unigrams(text)

    # Count bigrams over the unigram stream.
    bigram_counts: Dict[Tuple[str, str], int] = {}
    for a, b in zip(uni, uni[1:]):
        bigram_counts[(a, b)] = bigram_counts.get((a, b), 0) + 1

    terms: List[str] = list(uni)

    # Add phrase bigrams:
    # - Always include whitelisted phrases if present.
    # - Also include frequent bigrams (>=2) when not both generic.
    for (a, b), c in bigram_counts.items():
        if (a, b) in PHRASE_WHITELIST:
            terms.append(f"{a}_{b}")
            continue
        if c >= 2 and not (a in GENERIC_TOKENS and b in GENERIC_TOKENS):
            terms.append(f"{a}_{b}")

    return terms


def _top_keywords(text: str, k: int = 60) -> List[Tuple[str, int]]:
    """Return top terms for profiling.

    This replaces the older unigram-only keyword list with:
    - fewer generic terms
    - some bigram phrases (time_series, machine_learning, ...)
    """

    freq: Dict[str, int] = {}
    for t in _extract_terms(text):
        freq[t] = freq.get(t, 0) + 1

    # Slightly down-weight generic tokens (so they don't dominate the top-k).
    for gt in GENERIC_TOKENS:
        if gt in freq:
            freq[gt] = max(0, freq[gt] - 1)

    items = [(t, c) for t, c in freq.items() if c > 0]
    return sorted(items, key=lambda kv: (-kv[1], kv[0]))[:k]


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


def _normalize_ws_keep_newlines(text: str) -> str:
    # Normalize CRLF and strip trailing spaces but keep paragraph boundaries.
    text = text.replace("\r\n", "\n").replace("\r", "\n")
    # Collapse runs of spaces/tabs within lines.
    text = "\n".join(re.sub(r"[\t ]+", " ", ln).rstrip() for ln in text.split("\n"))
    return text.strip()


def _split_paragraphs(text: str) -> List[str]:
    text = _normalize_ws_keep_newlines(text)
    if not text:
        return []
    paras = re.split(r"\n\s*\n+", text)
    return [p.strip() for p in paras if p.strip()]


def extract_evidence_snippets(exp_body: str) -> List[dict]:
    """Extract snippet candidates WITHOUT crossing paragraph boundaries.

    Returns a list of dicts:
      {"text": ..., "para_idx": int, "kind": "bullet"|"sentence"|"paragraph"}

    This is intentionally heuristic and deterministic.
    """

    paras = _split_paragraphs(exp_body)
    out: List[dict] = []

    bullet_re = re.compile(r"^\s*(?:[-*•]|\d+\.)\s+")

    for para_idx, para in enumerate(paras):
        lines = [ln.strip() for ln in para.split("\n") if ln.strip()]

        # If paragraph looks like a list of bullets, treat each bullet-line separately.
        bullet_lines = [ln for ln in lines if bullet_re.match(ln)]
        if bullet_lines and len(bullet_lines) >= max(2, len(lines) // 2):
            for ln in bullet_lines:
                text = bullet_re.sub("", ln).strip()
                if len(text) >= 50:
                    out.append({"text": text, "para_idx": para_idx, "kind": "bullet"})
            continue

        # Otherwise, sentence-split within the paragraph (do NOT collapse across paras).
        flat = re.sub(r"\s+", " ", para.strip())
        sentences = re.split(r"(?<=[.!?])\s+", flat)
        kept = [s.strip() for s in sentences if len(s.strip()) >= 60]

        if kept:
            for s in kept:
                out.append({"text": s, "para_idx": para_idx, "kind": "sentence"})
        else:
            # If we can't get sentences, fall back to the whole paragraph.
            if len(flat) >= 80:
                out.append({"text": flat, "para_idx": para_idx, "kind": "paragraph"})

    return out


def _extract_years(text: str) -> List[int]:
    # Very small heuristic: pull 4-digit years.
    years = [int(y) for y in re.findall(r"\b(19\d{2}|20\d{2})\b", text)]
    return [y for y in years if 1900 <= y <= 2100]


def _recency_score(dates: str | None, ref_year: int | None) -> int:
    """Return an integer 0..RECENCY_BOOST_MAX."""

    if not dates or not ref_year:
        return 0

    years = _extract_years(dates)
    if not years:
        return 0

    last_year = max(years)
    # If last_year == ref_year => max score. If older, decay.
    age = max(0, ref_year - last_year)
    return max(0, RECENCY_BOOST_MAX - age)


def _pinned_exp_ids_from_env() -> set[str]:
    raw = os.environ.get("RESUME_TAILOR_PIN_EXP_IDS", "").strip()
    if not raw:
        return set()
    return {x.strip() for x in raw.split(",") if x.strip()}


def _hard_skill_match_count(text: str) -> int:
    toks = set(_extract_terms(text))
    return sum(1 for t in HARD_SKILL_TOKENS if t in toks)


def score_overlap(jd_keywords: set[str], text: str) -> int:
    toks = set(_extract_terms(text))
    return len(jd_keywords.intersection(toks))


def build_artifacts(jd_text: str, experiences: List[Experience], max_exps: int = 4) -> dict:
    jd_kw = _top_keywords(jd_text, k=60)
    jd_kw_set = {k for k, _ in jd_kw}

    # Score each experience by keyword overlap (dominant) + deterministic priors.
    pinned = _pinned_exp_ids_from_env()

    # Compute a ref year for recency scaling.
    all_years: List[int] = []
    for e in experiences:
        if e.dates:
            all_years.extend(_extract_years(e.dates))
    ref_year = max(all_years) if all_years else None

    scored: List[Tuple[int, dict, Experience]] = []
    for e in experiences:
        blob = e.body + " " + (e.header or "")
        overlap = score_overlap(jd_kw_set, blob)
        hard_skill_matches = _hard_skill_match_count(blob)
        hard_skill_bonus = HARD_SKILL_BOOST_PER_MATCH * hard_skill_matches
        recency_bonus = _recency_score(e.dates, ref_year)
        pinned_bonus = PINNED_EXP_BONUS if e.exp_id in pinned else 0

        total = overlap * OVERLAP_MULTIPLIER + hard_skill_bonus + recency_bonus + pinned_bonus

        scored.append(
            (
                total,
                {
                    "overlap": overlap,
                    "overlap_multiplier": OVERLAP_MULTIPLIER,
                    "hard_skill_matches": hard_skill_matches,
                    "hard_skill_bonus": hard_skill_bonus,
                    "recency_bonus": recency_bonus,
                    "pinned_bonus": pinned_bonus,
                    "total": total,
                },
                e,
            )
        )

    score_debug_by_exp_id = {e.exp_id: dbg for _total, dbg, e in scored}

    scored.sort(key=lambda x: (-x[0], x[2].exp_id))
    selected = [e for total, dbg, e in scored if dbg["overlap"] > 0][:max_exps]

    # For each selected experience: pick top snippet candidates as "evidence snippets".
    selected_evidence = []
    for e in selected:
        candidates = extract_evidence_snippets(e.body)
        sn_scored = sorted(
            ((score_overlap(jd_kw_set, c["text"]), c) for c in candidates),
            key=lambda x: (-x[0], -len(x[1]["text"]), x[1]["para_idx"]),
        )

        top_items = [c for s, c in sn_scored if s > 0][:3]
        if not top_items:
            # Fall back: first ~240 chars of body as a snippet.
            fallback = re.sub(r"\s+", " ", e.body.strip())
            top_items = [
                {
                    "text": fallback[:240] + ("..." if len(fallback) > 240 else ""),
                    "para_idx": 0,
                    "kind": "fallback",
                }
            ]

        snippets = []
        for idx, item in enumerate(top_items, start=1):
            sn_id = f"sn{idx}"
            snippets.append(
                {
                    "sn_id": sn_id,
                    "text": item["text"],
                    "score": score_overlap(jd_kw_set, item["text"]),
                    "para_idx": item.get("para_idx", 0),
                    "kind": item.get("kind", "unknown"),
                }
            )

        selected_evidence.append(
            {
                "exp_id": e.exp_id,
                "header": e.header,
                "score": score_debug_by_exp_id.get(e.exp_id, {}).get("total", 0),
                "score_breakdown": score_debug_by_exp_id.get(e.exp_id, {}),
                "snippets": snippets,
            }
        )

    # Keyword coverage: keywords that appear in selected evidence snippet texts.
    covered = set()
    for item in selected_evidence:
        for sn in item["snippets"]:
            covered |= set(_extract_terms(sn["text"]))

    top_kw = [k for k, _ in jd_kw][:40]
    missing_top_kw = [k for k in top_kw if k not in covered]

    jd_profile = {
        "generated_at": datetime.now(timezone.utc).isoformat(),
        "jd_hash": sha256(jd_text.encode("utf-8")).hexdigest()[:16],
        # Kept for backward compatibility, but now includes phrases like "time_series".
        "top_keywords": [{"keyword": k, "count": c} for k, c in jd_kw],
        "keyword_model": {
            "type": "unigrams+selected_bigrams",
            "phrase_whitelist": sorted(["_".join(p) for p in PHRASE_WHITELIST]),
            "stopword_count": len(STOPWORDS),
        },
        "selection_model": {
            "type": "overlap+priors",
            "overlap_multiplier": OVERLAP_MULTIPLIER,
            "hard_skill_boost_per_match": HARD_SKILL_BOOST_PER_MATCH,
            "recency_boost_max": RECENCY_BOOST_MAX,
            "pinned_exp_bonus": PINNED_EXP_BONUS,
            "pinned_env": "RESUME_TAILOR_PIN_EXP_IDS",
        },
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
            "JD profiling uses unigrams + selected bigram phrases (e.g., time_series).",
            "Evidence extraction enforces paragraph boundaries (no snippet bleed across sections).",
            "Experience selection uses overlap scoring plus deterministic priors (hard-skill boost, recency bonus, optional pinned exp_ids via RESUME_TAILOR_PIN_EXP_IDS).",
            "Missing keywords are not necessarily bad; they can flag areas to review.",
        ],
    }

    tailored_md_lines = []
    tailored_md_lines.append("# Tailored Resume Draft (stub)")
    tailored_md_lines.append("")
    tailored_md_lines.append(
        "This file is generated WITHOUT an LLM. It only rearranges/quotes existing experience text as draft bullets with evidence references."
    )
    tailored_md_lines.append("")

    for item in selected_evidence:
        tailored_md_lines.append(f"## {item['header']}")
        tailored_md_lines.append("")
        for sn in item["snippets"]:
            ref = f"(evidence: {item['exp_id']}#{sn['sn_id']})"
            bullet = sn["text"]
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
