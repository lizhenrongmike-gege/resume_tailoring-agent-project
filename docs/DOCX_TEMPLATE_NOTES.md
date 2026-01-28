# DOCX template notes (Mike’s resume)

We received Mike’s base resume as a `.docx` and stored it locally under:
- `private/templates/mike_base_resume.docx`

This file is **gitignored** and will not be committed.

## Environment constraint
This EC2 environment currently lacks `pip` / `venv` tooling, so we can’t rely on `python-docx` or `pandoc` out of the box.

For v1, we’ll use a **stdlib-only** approach:
- Read `.docx` as a zip
- Parse `word/document.xml` (WordprocessingML)
- Identify and replace specific bullet paragraphs (e.g., Ant Group bullets)
- Write a new `.docx` by copying the zip and updating XML

## Next step
Implement a minimal renderer that:
1) clones the base `.docx`
2) replaces the Ant Group bullet block with tailored bullets
3) enforces 1-page via conservative caps (max bullets + max chars per bullet)

Longer-term, if we add `python3-pip` + `python3-venv`, we can move to `python-docx` or `pandoc` for more robust formatting control.
