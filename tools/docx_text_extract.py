"""Extract plain text paragraphs from a .docx (no external deps).

Usage:
  python3 tools/docx_text_extract.py path/to/file.docx

Notes:
- .docx is a zip with WordprocessingML XML.
- This extractor is intentionally simple: it reads word/document.xml and
  concatenates all w:t nodes per paragraph.
"""

from __future__ import annotations

import sys
import zipfile
import xml.etree.ElementTree as ET
from pathlib import Path

W_NS = {"w": "http://schemas.openxmlformats.org/wordprocessingml/2006/main"}


def extract_paragraphs(docx_path: str | Path) -> list[str]:
    p = Path(docx_path)
    with zipfile.ZipFile(p, "r") as z:
        xml = z.read("word/document.xml")

    root = ET.fromstring(xml)
    paras: list[str] = []

    for p_el in root.findall(".//w:p", W_NS):
        parts: list[str] = []
        for t_el in p_el.findall(".//w:t", W_NS):
            parts.append(t_el.text or "")
        text = "".join(parts).strip()
        if text:
            paras.append(text)

    return paras


def main() -> int:
    if len(sys.argv) != 2:
        print("Usage: python3 tools/docx_text_extract.py <file.docx>")
        return 2

    for i, line in enumerate(extract_paragraphs(sys.argv[1]), start=1):
        print(f"{i:02d}: {line}")

    return 0


if __name__ == "__main__":
    raise SystemExit(main())
