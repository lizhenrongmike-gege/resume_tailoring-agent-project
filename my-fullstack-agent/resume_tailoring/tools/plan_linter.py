"""Plan linter / truth-gating utilities.

Goal: catch the failure mode Mike described: bullets get "more buzzwordy" and lose
specific meaning (domain nouns, concrete objects) even if they're not outright false.

This module implements a deterministic guardrail that can:
- Flag loss of specificity (concrete terms removed, replaced with generic phrases)
- Flag new unverifiable claims heuristically (new numbers/tools/claims not in evidence)
- Gate risky edits by setting needs_user_ok=True so the pipeline halts for approval.

This is intentionally conservative and explainable.
"""

from __future__ import annotations

import re
from dataclasses import dataclass
from typing import Any, Dict, List, Optional, Tuple


GENERIC_PHRASES = {
    "complex", "various", "multiple", "key", "critical", "robust", "scalable",
    "optimized", "streamlined", "leveraged", "utilized", "improved", "enhanced",
    "maintained", "developed", "implemented", "real-time", "kpi", "kpis",
    "stakeholders", "insights", "impactful", "data-driven", "end-to-end",
    "time-series", "timeseries", "monitoring", "market trends",
}

# Words that often appear in Mike's domain-heavy bullets.
DOMAIN_TERMS = {
    "nowcasting", "inflation", "kyc", "aml", "high-frequency", "ehr", "billing",
    "clinical", "fraud", "risk", "ant", "ant group",
}


_word_re = re.compile(r"[A-Za-z][A-Za-z0-9\-_/]+")
_digit_re = re.compile(r"\d")
_acronym_re = re.compile(r"\b[A-Z]{2,}\b")


def _normalize(s: str) -> str:
    return re.sub(r"\s+", " ", s.strip())


def extract_terms(text: str) -> List[str]:
    """Tokenize into rough 'terms' while preserving hyphenated tech words."""
    return [t.lower() for t in _word_re.findall(text or "")]


def specificity_terms(text: str) -> Tuple[set, Dict[str, int]]:
    """Return a set of terms that indicate specificity + basic counts.

    Heuristics:
    - contains digits (metrics, years)
    - ALLCAPS acronyms (SQL, ETL, KPI)
    - hyphenated/compound tokens (high-frequency, time-series)
    - domain terms (nowcasting, KYC)
    """
    text_n = _normalize(text)
    terms = extract_terms(text_n)

    specific = set()
    counts = {
        "digits": 1 if _digit_re.search(text_n) else 0,
        "acronyms": len(_acronym_re.findall(text_n)),
        "hyphenated": sum(1 for t in terms if "-" in t),
    }

    for t in terms:
        if "-" in t:
            specific.add(t)
        if t in DOMAIN_TERMS:
            specific.add(t)

    # Add acronyms as 'specific'
    for a in _acronym_re.findall(text_n):
        specific.add(a.lower())

    # Add any token containing digits (e.g., "2022", "5x")
    for t in terms:
        if any(ch.isdigit() for ch in t):
            specific.add(t)

    return specific, counts


@dataclass
class EditIssue:
    kind: str
    message: str
    removed_terms: Optional[List[str]] = None
    added_terms: Optional[List[str]] = None


def lint_bullet_pair(old_bullet: str, new_bullet: str) -> List[EditIssue]:
    """Lint a single (old, new) bullet pair."""
    issues: List[EditIssue] = []

    old_n = _normalize(old_bullet or "")
    new_n = _normalize(new_bullet or "")

    old_specific, old_counts = specificity_terms(old_n)
    new_specific, new_counts = specificity_terms(new_n)

    removed_specific = sorted(old_specific - new_specific)
    if removed_specific:
        issues.append(
            EditIssue(
                kind="specificity_loss",
                message=(
                    "New bullet appears to remove specific/domain terms from the original. "
                    "Consider keeping concrete nouns unless JD explicitly requires generalization."
                ),
                removed_terms=removed_specific,
            )
        )

    # Heuristic: more generic phrasing added while specifics removed.
    new_terms = set(extract_terms(new_n))
    old_terms = set(extract_terms(old_n))
    added_generic = sorted((new_terms - old_terms) & GENERIC_PHRASES)
    if added_generic and removed_specific:
        issues.append(
            EditIssue(
                kind="buzzword_drift",
                message=(
                    "New bullet adds generic phrases while removing specifics; risk of watered-down meaning."
                ),
                removed_terms=removed_specific,
                added_terms=added_generic,
            )
        )

    # Heuristic: new bullet introduces digits/acronyms not present before (potentially unverifiable).
    if new_counts["digits"] > old_counts["digits"]:
        issues.append(
            EditIssue(
                kind="new_metrics",
                message="New bullet introduces numbers/metrics not present in the old bullet; ensure evidence supports it.",
            )
        )

    if new_counts["acronyms"] > old_counts["acronyms"]:
        issues.append(
            EditIssue(
                kind="new_acronyms",
                message="New bullet adds acronyms/tools not present in the old bullet; ensure evidence supports it.",
            )
        )

    return issues


def lint_and_gate_plan(plan: Dict[str, Any]) -> Dict[str, Any]:
    """Return {gated_plan, lint_report}.

    - Sets needs_user_ok=True for edits with specificity/buzzword issues.
    - Keeps everything else intact.
    """
    gated = dict(plan)
    edits = list(gated.get("edits") or [])

    report: Dict[str, Any] = {
        "summary": {"total_edits": len(edits), "flagged_edits": 0},
        "edits": [],
    }

    for i, e in enumerate(edits):
        old_b = (e.get("old_bullet") or "")
        new_b = (e.get("new_bullet") or "")
        issues = lint_bullet_pair(old_b, new_b)

        flagged = any(iss.kind in {"specificity_loss", "buzzword_drift"} for iss in issues)
        if flagged:
            e = dict(e)
            e["needs_user_ok"] = True
            edits[i] = e

        report_item = {
            "index": i,
            "experience": e.get("experience"),
            "bullet_id": e.get("bullet_id"),
            "flagged": bool(flagged),
            "issues": [
                {
                    "kind": iss.kind,
                    "message": iss.message,
                    "removed_terms": iss.removed_terms,
                    "added_terms": iss.added_terms,
                }
                for iss in issues
            ],
        }
        report["edits"].append(report_item)

    report["summary"]["flagged_edits"] = sum(1 for x in report["edits"] if x["flagged"])
    gated["edits"] = edits

    return {"gated_plan": gated, "lint_report": report}
