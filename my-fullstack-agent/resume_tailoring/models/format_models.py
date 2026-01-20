"""Format models for capturing resume formatting parameters."""

from pydantic import BaseModel, Field


class ResumeFormat(BaseModel):
    """Detected formatting parameters from the input resume."""

    # Font settings
    body_font_name: str = Field(
        default="Calibri", description="Main body font"
    )
    body_font_size: float = Field(
        default=11.0, description="Body text size in points"
    )

    # Header settings (name at top)
    header_font_name: str = Field(
        default="Calibri", description="Header font"
    )
    header_font_size: float = Field(
        default=24.0, description="Header size in points"
    )
    header_bold: bool = Field(default=True, description="Header bold")

    # Section header settings (Professional Experience, Skills, etc.)
    section_font_name: str = Field(
        default="Calibri", description="Section header font"
    )
    section_font_size: float = Field(
        default=14.0, description="Section header size"
    )
    section_bold: bool = Field(default=True, description="Section header bold")

    # Subheader settings (job titles)
    subheader_font_name: str = Field(
        default="Calibri", description="Job title font"
    )
    subheader_font_size: float = Field(
        default=11.0, description="Job title size"
    )
    subheader_bold: bool = Field(default=True, description="Job title bold")

    # Margins (in inches)
    margin_top: float = Field(default=1.0, description="Top margin in inches")
    margin_bottom: float = Field(
        default=1.0, description="Bottom margin in inches"
    )
    margin_left: float = Field(default=1.0, description="Left margin in inches")
    margin_right: float = Field(
        default=1.0, description="Right margin in inches"
    )

    # Spacing
    line_spacing: float = Field(
        default=1.0, description="Line spacing multiplier"
    )
