"""DOCX bullet tagger (bookmark IDs) + reserve slots.

This module adds stable bookmark IDs to bullet paragraphs and optionally inserts
"reserve" bullet slots at the end of each contiguous bullet group.

Why:
- downstream tools can address bullets by ID rather than brittle exact-text match
- reserve slots allow the planner to add a new bullet (moderately) without
  restructuring the resume.

Implementation notes:
- Uses python-docx for high-level structure, but writes bookmarks via OXML.
- Bookmarks are Word-native (bookmarkStart/bookmarkEnd) and invisible.
"""

from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path
from typing import Iterable

from docx import Document
from docx.oxml import OxmlElement
from docx.oxml.ns import qn


@dataclass
class TagResult:
    tagged_bullets: int
    reserve_bullets_added: int


def _is_bullet_paragraph(p) -> bool:
    name = getattr(getattr(p, "style", None), "name", "") or ""
    # Common styles: "List Bullet", sometimes localized.
    return "Bullet" in name or name.startswith("List")


def _add_bookmark_to_paragraph(paragraph, name: str, bm_id: int) -> None:
    p = paragraph._p

    start = OxmlElement("w:bookmarkStart")
    start.set(qn("w:id"), str(bm_id))
    start.set(qn("w:name"), name)

    end = OxmlElement("w:bookmarkEnd")
    end.set(qn("w:id"), str(bm_id))

    # Insert at beginning/end of paragraph.
    p.insert(0, start)
    p.append(end)


def _paragraph_has_bookmark(paragraph) -> bool:
    p = paragraph._p
    for child in p.iterchildren():
        if child.tag == qn("w:bookmarkStart"):
            return True
    return False


def _iter_bullet_groups(doc: Document) -> Iterable[list]:
    """Yield contiguous groups of bullet paragraphs."""
    group: list = []
    for p in doc.paragraphs:
        if _is_bullet_paragraph(p) and p.text.strip():
            group.append(p)
        else:
            if group:
                yield group
                group = []
    if group:
        yield group


def tag_docx_bullets(
    base_path: str | Path,
    out_path: str | Path,
    prefix: str = "B",
    reserve_per_group: int = 1,
) -> TagResult:
    """Create a tagged copy of base_path with bookmark IDs on bullets.

    - Adds bookmark IDs to each existing bullet paragraph (if not already tagged).
    - Adds reserve bullet slot(s) at end of each bullet group.

    Reserve bullets are inserted with a zero-width placeholder character to keep
    the bullet paragraph present without visible text.

    Args:
      base_path: Input .docx
      out_path: Output .docx
      prefix: Bookmark prefix, default "B".
      reserve_per_group: Number of reserve bullets appended to each bullet group.

    Returns:
      TagResult counts.
    """
    base_path = Path(base_path)
    out_path = Path(out_path)
    doc = Document(str(base_path))

    tagged = 0
    reserves = 0

    # Start bookmark ids at a high-ish number to avoid collisions with any existing.
    bm_id = 1000
    bullet_idx = 1

    groups = list(_iter_bullet_groups(doc))

    for g_i, group in enumerate(groups, start=1):
        # Tag existing bullets in this group
        for p in group:
            if _paragraph_has_bookmark(p):
                continue
            name = f"{prefix}{bullet_idx:04d}"
            _add_bookmark_to_paragraph(p, name=name, bm_id=bm_id)
            tagged += 1
            bullet_idx += 1
            bm_id += 1

        # Add reserve bullets after last bullet in the group.
        # We create new bullet paragraphs with a zero-width char so Word keeps the list item.
        last = group[-1]
        for r in range(1, reserve_per_group + 1):
            reserve_name = f"{prefix}{bullet_idx:04d}_R{r}"
            new_p = last.insert_paragraph_after("\u200b")
            # Try to match bullet style
            try:
                new_p.style = last.style
            except Exception:
                pass

            _add_bookmark_to_paragraph(new_p, name=reserve_name, bm_id=bm_id)
            reserves += 1
            bullet_idx += 1
            bm_id += 1

    out_path.parent.mkdir(parents=True, exist_ok=True)
    doc.save(str(out_path))
    return TagResult(tagged_bullets=tagged, reserve_bullets_added=reserves)
