# Resume Tailoring Agent — Workflow Idea (deterministic-ish)

This workflow reduces randomness by forcing every agent step to produce **structured artifacts** and by adding **gates** that can stop the run.

## Core artifacts
- `resume_base.md` (or JSON)
- `experience_bank.json` (source-of-truth, rich)
- `job_description.md`
- `jd_profile.json` (structured extraction)
- `fit_assessment.json` (A close / B transferable / C out-of-scope + rationale)
- `selected_evidence.json` (only claims that can be supported by experience_bank)
- `tailored_resume.md`
- `cover_letter.md` (optional)

## Suggested pipeline
1) **Ingest & normalize**
- Validate all inputs are present.
- Normalize resume to a consistent format.
- Parse experience-bank doc (paragraphs) into structured records.

2) **JD extraction (structured)**
Produce `jd_profile.json` with:
- role_title, company
- required_skills (ranked)
- preferred_skills
- responsibilities (ranked)
- keywords
- seniority level

3) **Evidence retrieval (truth gate)**
From `experience_bank.json`, retrieve relevant experiences:
- match skills/responsibilities → candidate evidence
- output `selected_evidence.json`

Rules:
- Every bullet in output must map to >=1 evidence item.
- If evidence is weak, mark it as **"weak_support"** (allowed only if user approves).

4) **Fit assessment (A/B/C)**
Compute:
- overlap score (skills)
- evidence coverage score
- missing critical requirements
Decide A/B/C.

- If **C (out-of-scope)**: stop with a refusal message + suggest closest alternative roles.

5) **Tailor resume (format + content)**
- Reorder sections, rewrite bullets, emphasize matching evidence.
- Add a "Skills" section aligned to JD.
- Never add new projects/claims not supported by evidence.

6) **Self-review (lint)**
- Check every bullet has evidence links.
- Check keywords coverage.
- Check for banned phrases / exaggeration.

7) **User feedback loop**
If user says “regenerate”, ask for one of:
- tone (more punchy / more conservative)
- target skills to emphasize
- remove/avoid certain claims
Then repeat steps 3–6.

8) **Cover letter (optional)**
- Use tailored resume + selected evidence.
- 3–4 short paragraphs. Include role/company + 1–2 quantified highlights.

9) **Store run**
Write a record to `runs/YYYY-MM-DD/<company>_<role>_<hash>.json` plus rendered Markdown outputs.

## Storage approach (no DB needed)
Disk-first, git-friendly:
- `runs/` folder holds small text/JSON files.
- Storage size stays modest; each resume is kilobytes.
- Later, if you want search + analytics, add SQLite.
