# DOCX Bullet Tagging + Reserve Slots

Goal: make resume edits reliable and scalable.

## Why tag bullets?
String matching on bullet text is brittle (small edits break the match). Instead, we tag bullets
with invisible Word bookmarks (IDs), then address bullets by ID.

## Reserve slots
To allow moderate skill integration without changing resume structure, we add one or more
"reserve" bullet slots at the end of each bullet group (default: 2 per group).

- These slots are bullet paragraphs with a zero-width placeholder (not visible).
- Planner can write into these slots when it needs to add a bullet without deleting others.

## How it works
1) Run a one-time tagging pass to create a tagged template:
   - input: your base resume DOCX
   - output: a tagged copy

2) Planner outputs `bullet_id` in ResumeEditPlan.

3) Applier edits the DOCX by bookmark ID.

## Notes
- Experience bank updates do NOT require retagging.
- Small manual edits to the tagged resume do NOT require retagging (bookmarks remain).
- Structural changes (adding/removing bullet paragraphs) may require a re-tag run.

## Design choice: never insert new bullets at runtime
We avoid inserting new bullet paragraphs during a tailoring run (runtime) to keep formatting
and 1-page behavior stable. Instead, we pre-create reserve bullet slots during tagging and
fill them when needed.
