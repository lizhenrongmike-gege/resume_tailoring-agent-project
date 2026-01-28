# Resume Tailoring Agent — Project Brief (Mike)

## Goal
Build an agentic workflow that tailors a resume (and optionally a cover letter) to a given job description **without hallucinating** experience the user never did.

## Inputs (per user session)
1. **Job Description (JD)** — can change frequently.
2. **Resume** — stable baseline.
3. **Work Experience Bank** — richer, more granular source-of-truth describing what the user actually did.
   - Mike’s format: a **doc with paragraphs**, usually **one paragraph per experience**, containing fuller history than can fit on a resume.

## Desired UX
- First use: user provides Resume + Work Experience Bank + JD.
- Later uses: user can paste only a new JD; the system retains Resume + Work Experience Bank as long-term memory.
- Regenerate loop: when the user isn’t satisfied, the system asks *what to improve* and regenerates.

## Key constraints
- Tailor aggressively for relevance, but **do not invent** work.
- If JD is totally out of scope, the system should **refuse** with a clear message.

## Job-fit cases
- **A) Close match**: tailor by reordering/wording + selecting the most relevant bullets.
- **B) Transferable match**: map prior work to JD skillsets (e.g., risk → analytics) while staying truthful.
- **C) Out of scope**: decline and explain.

## Outputs
- Tailored resume (**1-page strict** format).
- Optional cover letter based on the tailored resume + underlying story.
- Tailored work-experience bank (either produced as an artifact, or used as the working intermediate).

## Storage / History
Store each run so the user can compare versions later.
Suggested record fields:
- timestamp
- company_name
- role_name
- jd_hash
- resume_version_id
- tailored_resume
- cover_letter (optional)
- tailored_experience_bank
- notes / user feedback

(We can store on disk as JSON/Markdown; DB optional.)
