from __future__ import annotations

import json
import re
import sys
from dataclasses import dataclass, asdict


@dataclass
class JDProfile:
    company: str | None
    role: str | None
    domain: str | None
    responsibilities: list[str]
    skills_required: list[str]
    skills_nice: list[str]
    tools: list[str]


def _find_first(patterns: list[str], text: str) -> str | None:
    for p in patterns:
        m = re.search(p, text, flags=re.I)
        if m:
            return m.group(1).strip()
    return None


def extract_jd(text: str) -> JDProfile:
    t = re.sub(r"\s+", " ", text).strip()

    company = _find_first([
        r"About the job\s+([A-Za-z0-9]+)",
        r"\b([A-Za-z0-9]+)\s+is positioning",
    ], t)

    role = _find_first([
        r"Job Description:\s*The\s+([^\n\r]+?)\s+will\s+report",
        r"The\s+([^\n\r]+?)\s+will\s+report",
        r"\bRole:\s*([^\n\r]+)",
    ], text)

    domain = "healthcare / oncology" if re.search(r"oncolog|EHR|clinical|drug|billing", t, re.I) else None

    # Very lightweight keyword harvesting.
    resp = []
    for line in re.split(r"\n|\r", text):
        s = line.strip(" •\t")
        if not s:
            continue
        if re.match(r"^(Performing|Collaborating|Building|Creating|Developing)\b", s):
            resp.append(s)

    skills_required = []
    skills_nice = []

    if re.search(r"Excel", t, re.I):
        skills_required.append("Excel")
    if re.search(r"PowerPoint", t, re.I):
        skills_required.append("PowerPoint")
    if re.search(r"desire to learn SQL|SQL a plus", t, re.I):
        skills_required.append("SQL")

    if re.search(r"PowerBI|Power BI", t, re.I):
        skills_nice.append("Power BI")
    if re.search(r"dashboard", t, re.I):
        skills_nice.append("Dashboarding")
    if re.search(r"data model", t, re.I):
        skills_nice.append("Data modeling")

    tools = []
    for tool in ["Excel", "PowerPoint", "SQL", "Power BI"]:
        if re.search(tool.replace(" ", r"\\s+"), t, re.I):
            tools.append(tool)

    return JDProfile(
        company=company,
        role=role,
        domain=domain,
        responsibilities=resp,
        skills_required=skills_required,
        skills_nice=skills_nice,
        tools=tools,
    )


def main() -> int:
    if len(sys.argv) != 3:
        print("Usage: python -m src.jd_extract <input.txt> <out.json>")
        return 2
    inp, outp = sys.argv[1], sys.argv[2]
    text = open(inp, "r", encoding="utf-8").read()
    prof = extract_jd(text)
    with open(outp, "w", encoding="utf-8") as f:
        json.dump(asdict(prof), f, indent=2)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
