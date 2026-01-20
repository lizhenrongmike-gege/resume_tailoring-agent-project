"""Format detection tool for extracting formatting from resume documents."""

from docx import Document
from google.adk.tools import FunctionTool
from typing import List, Dict, Any


def _detect_docx_format(file_path: str) -> dict:
    """Detects formatting parameters from a .docx resume file.

    Analyzes the document to extract font names, sizes, margins, and other
    formatting parameters that can be used to replicate the original style.

    Args:
        file_path: The full path to the .docx file to analyze.

    Returns:
        dict: Contains 'status', 'file_path', and 'format' with detected settings.
    """
    try:
        doc = Document(file_path)

        # Detect margins from document sections
        section = doc.sections[0]
        margins = {
            "margin_top": (
                section.top_margin.inches if section.top_margin else 1.0
            ),
            "margin_bottom": (
                section.bottom_margin.inches if section.bottom_margin else 1.0
            ),
            "margin_left": (
                section.left_margin.inches if section.left_margin else 1.0
            ),
            "margin_right": (
                section.right_margin.inches if section.right_margin else 1.0
            ),
        }

        # Analyze paragraphs to detect fonts and sizes
        font_samples: List[Dict[str, Any]] = []

        for para in doc.paragraphs:
            for run in para.runs:
                font_name = run.font.name
                font_size = run.font.size.pt if run.font.size else None
                is_bold = run.font.bold

                if font_name or font_size:
                    font_samples.append({
                        "name": font_name,
                        "size": font_size,
                        "bold": is_bold or False,
                        "text_length": len(run.text.strip()),
                    })

        # Categorize fonts by size
        body_fonts: List[Dict[str, Any]] = []
        section_fonts: List[Dict[str, Any]] = []
        header_fonts: List[Dict[str, Any]] = []

        for sample in font_samples:
            if sample["size"] is None:
                continue
            if sample["size"] > 18:
                header_fonts.append(sample)
            elif sample["size"] > 12:
                section_fonts.append(sample)
            else:
                body_fonts.append(sample)

        # Build format data
        format_data = {**margins}

        # Determine body font (most common in body samples)
        if body_fonts:
            body_names = [f["name"] for f in body_fonts if f["name"]]
            body_sizes = [f["size"] for f in body_fonts if f["size"]]
            if body_names:
                format_data["body_font_name"] = max(
                    set(body_names), key=body_names.count
                )
            if body_sizes:
                format_data["body_font_size"] = max(
                    set(body_sizes), key=body_sizes.count
                )

        # Determine section header font
        if section_fonts:
            section_names = [f["name"] for f in section_fonts if f["name"]]
            section_sizes = [f["size"] for f in section_fonts if f["size"]]
            section_bolds = [f["bold"] for f in section_fonts]
            if section_names:
                format_data["section_font_name"] = max(
                    set(section_names), key=section_names.count
                )
            if section_sizes:
                format_data["section_font_size"] = max(
                    set(section_sizes), key=section_sizes.count
                )
            if section_bolds:
                format_data["section_bold"] = (
                    section_bolds.count(True) > len(section_bolds) / 2
                )

        # Determine header font (largest fonts, typically the name)
        if header_fonts:
            # Sort by size descending, take the largest
            header_fonts_sorted = sorted(
                header_fonts, key=lambda x: x["size"] or 0, reverse=True
            )
            if header_fonts_sorted:
                largest = header_fonts_sorted[0]
                if largest["name"]:
                    format_data["header_font_name"] = largest["name"]
                if largest["size"]:
                    format_data["header_font_size"] = largest["size"]
                format_data["header_bold"] = largest["bold"]

        # Detect subheader (bold text in body range - typically job titles)
        subheader_candidates = [
            f for f in body_fonts if f["bold"] and f["text_length"] > 5
        ]
        if subheader_candidates:
            sub_names = [f["name"] for f in subheader_candidates if f["name"]]
            sub_sizes = [f["size"] for f in subheader_candidates if f["size"]]
            if sub_names:
                format_data["subheader_font_name"] = max(
                    set(sub_names), key=sub_names.count
                )
            if sub_sizes:
                format_data["subheader_font_size"] = max(
                    set(sub_sizes), key=sub_sizes.count
                )
            format_data["subheader_bold"] = True

        return {
            "status": "success",
            "file_path": file_path,
            "format": format_data,
            "metadata": {
                "samples_analyzed": len(font_samples),
                "body_samples": len(body_fonts),
                "section_samples": len(section_fonts),
                "header_samples": len(header_fonts),
            },
        }

    except FileNotFoundError:
        return {
            "status": "error",
            "file_path": file_path,
            "error_message": f"File not found: {file_path}",
            "format": {},
        }
    except Exception as e:
        return {
            "status": "error",
            "file_path": file_path,
            "error_message": str(e),
            "format": {},
        }


def _detect_pdf_format(file_path: str) -> dict:
    """Detects formatting parameters from a .pdf resume file.

    Note: PDF format detection is more limited than .docx as PDFs don't
    preserve semantic formatting information as clearly.

    Args:
        file_path: The full path to the .pdf file to analyze.

    Returns:
        dict: Contains 'status', 'file_path', and 'format' with detected settings.
    """
    try:
        import pdfplumber

        font_samples: List[Dict[str, Any]] = []

        with pdfplumber.open(file_path) as pdf:
            for page in pdf.pages:
                chars = page.chars
                for char in chars:
                    if char.get("fontname") and char.get("size"):
                        font_samples.append({
                            "name": char["fontname"],
                            "size": float(char["size"]),
                            "bold": "Bold" in char.get("fontname", ""),
                        })

        if not font_samples:
            return {
                "status": "success",
                "file_path": file_path,
                "format": {},
                "message": "No font information could be extracted from PDF",
            }

        # Categorize by size
        sizes = [s["size"] for s in font_samples]
        avg_size = sum(sizes) / len(sizes) if sizes else 11

        body_fonts = [f for f in font_samples if f["size"] <= avg_size + 2]
        header_fonts = [f for f in font_samples if f["size"] > avg_size + 4]

        format_data = {}

        if body_fonts:
            body_names = [f["name"] for f in body_fonts]
            body_sizes = [f["size"] for f in body_fonts]
            format_data["body_font_name"] = max(
                set(body_names), key=body_names.count
            )
            format_data["body_font_size"] = round(
                max(set(body_sizes), key=body_sizes.count), 1
            )

        if header_fonts:
            header_fonts_sorted = sorted(
                header_fonts, key=lambda x: x["size"], reverse=True
            )
            if header_fonts_sorted:
                format_data["header_font_name"] = header_fonts_sorted[0]["name"]
                format_data["header_font_size"] = round(
                    header_fonts_sorted[0]["size"], 1
                )
                format_data["header_bold"] = header_fonts_sorted[0]["bold"]

        return {
            "status": "success",
            "file_path": file_path,
            "format": format_data,
            "metadata": {"samples_analyzed": len(font_samples)},
        }

    except FileNotFoundError:
        return {
            "status": "error",
            "file_path": file_path,
            "error_message": f"File not found: {file_path}",
            "format": {},
        }
    except Exception as e:
        return {
            "status": "error",
            "file_path": file_path,
            "error_message": str(e),
            "format": {},
        }


# Create FunctionTool instances
detect_docx_format_tool = FunctionTool(func=_detect_docx_format)
detect_pdf_format_tool = FunctionTool(func=_detect_pdf_format)
