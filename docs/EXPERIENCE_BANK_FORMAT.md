# Experience Bank — Format + Parsing Notes

Mike’s experience bank today is a **doc** consisting of paragraphs, typically **one paragraph per experience**.

Goal: convert this into structured records the agent can retrieve from and cite.

## Recommended internal representation (JSON)
Each experience becomes a record:

```json
{
  "experience_id": "risk_antgroup_2021",
  "company": "Ant Group",
  "role": "Risk Management Analyst",
  "level": "analyst",
  "industry": "fintech",
  "dates": {"start": "YYYY-MM", "end": "YYYY-MM"},
  "location": "...",
  "summary_paragraph": "(original paragraph)",
  "responsibilities": ["..."],
  "tools": ["SQL", "Python", "..."],
  "data": ["KYC", "transaction data", "..."],
  "methods": ["monitoring", "dashboards", "risk segmentation", "..."],
  "outcomes": ["(only if supported)"]
}
```

## Why this helps
- Retrieval becomes deterministic (skills → evidence).
- We can enforce the **truth gate**: every bullet must cite at least one experience_id.

## Safe bullet creation rule (for ‘new bullet’ generation)
Allow generating a *new* bullet only if it can be justified by:
- the paragraph’s stated activities/tools/data, and
- the role level/industry constraints.

Examples:
- OK: “Monitored model performance / drift” (if the paragraph implies monitoring, reporting, dashboards)
- Not OK: “Built a brand-new model from scratch” unless explicitly supported.

## Human-in-the-loop
If a bullet is only **weakly supported** (reasonable inference but not explicit), mark it as `needs_user_ok=true` and ask the user to confirm/adjust.
