from __future__ import annotations

import argparse
import json
import re
from datetime import datetime, timezone
from pathlib import Path

from docx import Document


def normalize(s: str) -> str:
    return re.sub(r"\s+", " ", s).strip()


def replace_block(paras: list, start_match: str, end_match: str, new_lines: list[str]) -> int:
    """Replace the paragraph texts between (and including) start/end markers.

    We keep paragraph objects but overwrite their text. If we need fewer paragraphs,
    we blank the extras; if we need more, we insert new paragraphs after the end.
    """
    start_idx = end_idx = None
    for i, p in enumerate(paras):
        t = normalize(p.text)
        if start_idx is None and t == normalize(start_match):
            start_idx = i
            continue
        if start_idx is not None and t == normalize(end_match):
            end_idx = i
            break

    if start_idx is None or end_idx is None or end_idx < start_idx:
        raise RuntimeError("Could not locate target block to replace")

    block_len = end_idx - start_idx + 1
    needed = len(new_lines)

    # overwrite existing
    for j in range(block_len):
        idx = start_idx + j
        if j < needed:
            paras[idx].text = new_lines[j]
        else:
            paras[idx].text = ""

    # add extra paragraphs if needed
    if needed > block_len:
        insert_after = paras[end_idx]
        for extra in new_lines[block_len:]:
            insert_after = insert_after.insert_paragraph_after(extra)

    return needed


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--base", required=True, help="Base resume DOCX")
    ap.add_argument("--out", required=True, help="Output DOCX path")
    ap.add_argument("--jd", required=True, help="JD profile JSON")
    args = ap.parse_args()

    jd = json.load(open(args.jd, "r", encoding="utf-8"))
    company = jd.get("company") or "OneOncology"
    role = jd.get("role") or "Analyst, Analytics & Data Products"

    doc = Document(args.base)
    paras = doc.paragraphs

    # Tailored bullet rewrites for this JD.
    # Rule: keep Mike's existing resume structure; only rewrite bullets in-place.

    # --- Ant Group (5 bullets) ---
    ant_bullets = [
        "Owned onboarding risk operations (KYC & sanctions) for a high-volume fintech product; extracted daily alert batches in SQL and adjudicated cases using customer/transaction context to drive compliant, timely decisions.",
        "Analyzed rejection logs + customer support tickets to diagnose operational bottlenecks; partnered with Product to refine rejection logic and applicant messaging, reducing rework from ~50% to ~30% and weekly escalations from 300+ to ~200.",
        "Led ad hoc historical risk analyses on AliExpress merchant onboarding; grouped and compared entities by shared attributes (addresses, websites, referral patterns) to surface coordinated abuse and prioritize enforcement actions.",
        "Adjudicated 500+ weekly cases, blocking 200+ high-risk applications and freezing/off-boarding 100+ risky accounts to prevent downstream platform impact.",
        "Presented operational metrics and proposals in weekly governance reviews; proposed merchant-type risk segmentation to reduce false positives while maintaining regulatory coverage.",
    ]
    ant_start = "Owned day-to-day onboarding risk operations (KYC and sanctions) for a fintech wallet product, extracting daily alert batches via SQL and reviewing new and existing customer cases to clear, escalate, or enforce actions based on risk assessment."
    ant_end = "Proposed e-commerce merchant-type-based risk segmentation in weekly governance meetings, balancing false positive reduction with strict regulatory coverage."
    replace_block(paras, ant_start, ant_end, ant_bullets)

    # --- Boston College Research Assistant (3 bullets) ---
    ra_bullets = [
        "Engineered an automated ETL pipeline for high-frequency time-series data, scraping daily prices from major retailers and marketplaces to support real-time inflation tracking.",
        "Designed and maintained source-specific scraping workflows (Octoparse), handling complex extraction logic, monitoring stability, and normalizing schemas across sources for consistent aggregation.",
        "Built data-quality tooling (Regex-based unit standardization and SKU deduplication) to transform unstructured web data into a clean analytical dataset for econometric modeling and reporting.",
    ]
    ra_start = "Engineered an automated ETL pipeline for High-Frequency Time Series data, scraping daily pricing from major retailers to construct a real-time Inflation Nowcasting model."
    ra_end = "Developed Regular Expression (Regex) scripts to standardize heterogeneous product units (e.g., mass/volume conversions) and perform SKU deduplication, transforming unstructured web text into a clean, analytical dataset for econometric modeling."
    replace_block(paras, ra_start, ra_end, ra_bullets)

    # --- NuOnc project (3 bullets) ---
    nuonc_bullets = [
        "Deployed a stateful, multi-agent chatbot using Google Vertex AI & ADK to handle high-volume onboarding/pricing/product FAQs and provide educational-only explanations in a cancer-focused nutrition app.",
        "Implemented intent-aware routing + safety guardrails to separate product support from sensitive clinical prompts; enforced educational-only boundaries and redirected diagnosis/treatment requests.",
        "Integrated conversation logging and intent classification over anonymized transcripts to identify high-friction topics and inform product roadmap and FAQ improvements.",
    ]
    nuonc_start = 'Deployed a stateful, multi-agent chatbot using Google Vertex AI & ADK; engineered a strict "Educational-Only" safety layer with LLM guardrails to prevent medical advice and mitigate the Probability of Default in AI safety protocols.'
    nuonc_end = 'Integrated conversation logging and intent classification pipelines; utilized anonymized transcripts to identify high-friction topics and user engagement patterns, directly informing the founder’s product roadmap and FAQ strategy.'
    replace_block(paras, nuonc_start, nuonc_end, nuonc_bullets)

    # Write output
    outp = Path(args.out)
    outp.parent.mkdir(parents=True, exist_ok=True)
    doc.save(outp)

    # also emit a tiny run manifest next to it
    manifest = {
        "createdAt": datetime.now(timezone.utc).isoformat(),
        "target": {"company": company, "role": role},
        "edits": {
            "Ant Group": ant_bullets,
            "Boston College (RA)": ra_bullets,
            "NuOnc": nuonc_bullets,
        },
    }
    with open(outp.with_suffix(".json"), "w", encoding="utf-8") as f:
        json.dump(manifest, f, indent=2)

    return 0


if __name__ == "__main__":
    raise SystemExit(main())
