from __future__ import annotations

import argparse
from datetime import date
from pathlib import Path

from docx import Document


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--out", required=True)
    ap.add_argument("--company", default="OneOncology")
    ap.add_argument("--role", default="Analyst, Analytics & Data Products")
    ap.add_argument("--location", default="")
    ap.add_argument("--name", default="Zhenrong Li")
    args = ap.parse_args()

    company = args.company
    role = args.role

    today = date.today().strftime("%B %d, %Y")

    body = [
        today,
        "",
        f"Hiring Manager",
        f"{company}",
        "",
        f"Re: {role}",
        "",
        f"Dear Hiring Manager,",
        "",
        (
            f"I am writing to apply for the {role} role at {company}. I enjoy working at the intersection of operations and analytics—"
            "turning messy, high-volume data into practical insights and process improvements for stakeholders."
        ),
        "",
        (
            "Most recently at Ant Group, I owned onboarding risk operations (KYC and sanctions) for a fast-growing fintech product. "
            "I extracted daily alert batches in SQL, investigated customer and transactional context, and made case-level decisions to clear, escalate, or enforce actions. "
            "Beyond day-to-day execution, I analyzed rejection logs and customer support tickets to identify root causes of application failures and partnered with Product to improve rejection logic and messaging—"
            "reducing rework from ~50% to ~30% and lowering weekly escalations from 300+ to ~200."
        ),
        "",
        (
            "In parallel, I’ve built analytics pipelines that translate unstructured data into consistent, decision-ready metrics. "
            "As a Boston College research assistant, I engineered an automated pipeline to collect daily retail prices and produced publishable inflation metrics using a CPI-style weighting framework—"
            "work that required careful data cleaning, normalization, and clear communication of results."
        ),
        "",
        (
            "I’m especially excited about {company} because the role focuses on operational analytics that improves care delivery. "
            "I’ve also worked in a healthcare-adjacent product context: I designed and deployed a multi-agent chatbot for a cancer-focused nutrition app, "
            "including intent-aware routing, educational-only safety guardrails, and analytics over anonymized interaction logs to help the team improve user experience responsibly."
        ).format(company=company),
        "",
        (
            "I would welcome the chance to support OneOncology’s Analytics & Data Products team—whether that’s building reliable data models for downstream tools, "
            "developing dashboards that help practices understand performance, or partnering with clinical and administrative stakeholders to turn data into action."
        ),
        "",
        "Sincerely,",
        args.name,
    ]

    outp = Path(args.out)
    outp.parent.mkdir(parents=True, exist_ok=True)

    # Write DOCX
    doc = Document()
    for line in body:
        doc.add_paragraph(line)
    doc.save(outp)

    # Also write a .txt next to it for easy copy/paste
    txt = outp.with_suffix(".txt")
    txt.write_text("\n".join(body) + "\n", encoding="utf-8")

    return 0


if __name__ == "__main__":
    raise SystemExit(main())
