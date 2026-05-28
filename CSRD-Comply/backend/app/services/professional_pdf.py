"""
CSRD Comply — Professional PDF Export Service.

Generates professionally formatted PDF documents with:
- Company logo placement
- Header with company info and report title
- Footer with page numbers, date, and confidentiality notice
- Table of contents
- Professional typography and layout
- ESRS-compliant formatting
- Watermark support (draft, confidential, etc.)

Uses ReportLab for full control over PDF rendering.
"""
import io
import os
import logging
from typing import Optional, Dict, Any, List, Tuple
from datetime import datetime
from dataclasses import dataclass, field

logger = logging.getLogger(__name__)


@dataclass
class PDFHeader:
    """Header configuration for PDF."""
    company_name: str = ""
    report_title: str = ""
    reporting_year: int = 0
    logo_path: Optional[str] = None
    logo_width: float = 60  # mm
    show_company_info: bool = True


@dataclass
class PDFFooter:
    """Footer configuration for PDF."""
    show_page_numbers: bool = True
    show_date: bool = True
    confidentiality_text: str = "Confidential — For CSRD compliance purposes only"
    additional_text: str = ""


@dataclass
class PDFOptions:
    """Professional PDF export options."""
    header: PDFHeader = field(default_factory=PDFHeader)
    footer: PDFFooter = field(default_factory=PDFFooter)
    page_size: str = "A4"
    margin_top: float = 25.0
    margin_bottom: float = 25.0
    margin_left: float = 20.0
    margin_right: float = 20.0
    font_size_body: float = 10.0
    font_size_header: float = 14.0
    watermark: Optional[str] = None
    language: str = "it"
    include_toc: bool = True
    color_scheme: str = "professional"  # professional, modern, minimal


class ProfessionalPDFError(Exception):
    """Error generating professional PDF."""
    pass


class ProfessionalPDFService:
    """
    Professional PDF generation service for CSRD reports.

    Generates beautiful, auditor-ready PDF documents with full
    control over layout, typography, headers, and footers.
    """

    # ReportLab doesn't need to be imported at class level — lazy import
    _reportlab_available: bool = False

    def __init__(self):
        self._check_reportlab()

    def _check_reportlab(self) -> bool:
        """Check if ReportLab is available."""
        try:
            from reportlab.lib.pagesizes import A4
            from reportlab.platypus import SimpleDocTemplate
            self._reportlab_available = True
            return True
        except ImportError:
            self._reportlab_available = False
            logger.warning(
                "ReportLab not installed. Professional PDF unavailable. "
                "Install with: pip install reportlab"
            )
            return False

    @property
    def is_available(self) -> bool:
        """Check if professional PDF generation is available."""
        return self._reportlab_available

    def generate_pdf(
        self,
        xhtml_content: str,
        options: PDFOptions,
    ) -> bytes:
        """
        Generate a professionally formatted PDF from XHTML content.

        Args:
            xhtml_content: The XHTML report content
            options: PDF generation options

        Returns:
            PDF as bytes

        Raises:
            ProfessionalPDFError: If generation fails
        """
        if not self._reportlab_available:
            raise ProfessionalPDFError(
                "ReportLab is required for professional PDF generation. "
                "Install: pip install reportlab"
            )

        try:
            from reportlab.lib.pagesizes import A4
            from reportlab.lib.units import mm
            from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
            from reportlab.lib.colors import HexColor, black, white, Color
            from reportlab.lib.enums import TA_LEFT, TA_CENTER, TA_RIGHT, TA_JUSTIFY
            from reportlab.platypus import (
                SimpleDocTemplate, Paragraph, Spacer, PageBreak,
                Table, TableStyle, Image, KeepTogether, NextPageTemplate,
                PageTemplate, Frame, BaseDocTemplate,
            )
            from reportlab.platypus.doctemplate import PageTemplate
            from reportlab.pdfgen import canvas

            # ── Color Schemes ──────────────────────────────────
            COLORS = {
                "professional": {
                    "primary": HexColor("#1a365d"),      # Dark blue
                    "secondary": HexColor("#2b6cb0"),    # Medium blue
                    "accent": HexColor("#3182ce"),       # Accent blue
                    "bg_light": HexColor("#f7fafc"),     # Light background
                    "bg_table_header": HexColor("#2b6cb0"),
                    "text_primary": HexColor("#1a202c"),
                    "text_secondary": HexColor("#4a5568"),
                    "border": HexColor("#e2e8f0"),
                    "success": HexColor("#38a169"),
                    "warning": HexColor("#dd6b20"),
                    "header_bg": HexColor("#2b6cb0"),
                    "footer_bg": HexColor("#f7fafc"),
                },
                "modern": {
                    "primary": HexColor("#065f46"),
                    "secondary": HexColor("#059669"),
                    "accent": HexColor("#10b981"),
                    "bg_light": HexColor("#f0fdf4"),
                    "bg_table_header": HexColor("#065f46"),
                    "text_primary": HexColor("#064e3b"),
                    "text_secondary": HexColor("#64748b"),
                    "border": HexColor("#d1fae5"),
                    "success": HexColor("#059669"),
                    "warning": HexColor("#d97706"),
                    "header_bg": HexColor("#065f46"),
                    "footer_bg": HexColor("#f0fdf4"),
                },
                "minimal": {
                    "primary": HexColor("#1e293b"),
                    "secondary": HexColor("#475569"),
                    "accent": HexColor("#3b82f6"),
                    "bg_light": HexColor("#f8fafc"),
                    "bg_table_header": HexColor("#1e293b"),
                    "text_primary": HexColor("#0f172a"),
                    "text_secondary": HexColor("#64748b"),
                    "border": HexColor("#e2e8f0"),
                    "success": HexColor("#22c55e"),
                    "warning": HexColor("#f59e0b"),
                    "header_bg": HexColor("#1e293b"),
                    "footer_bg": HexColor("#f8fafc"),
                },
            }

            colors = COLORS.get(options.color_scheme, COLORS["professional"])

            # ── Setup Document ────────────────────────────────
            page_width, page_height = A4
            margin_left = options.margin_left * mm
            margin_right = options.margin_right * mm
            margin_top = options.margin_top * mm
            margin_bottom = options.margin_bottom * mm

            buffer = io.BytesIO()

            # ── Styles ─────────────────────────────────────────
            styles = getSampleStyleSheet()

            style_body = ParagraphStyle(
                "CSRDBody",
                parent=styles["Normal"],
                fontSize=options.font_size_body,
                leading=options.font_size_body * 1.5,
                fontName="Helvetica",
                textColor=colors["text_primary"],
                alignment=TA_JUSTIFY,
                spaceAfter=6,
                spaceBefore=3,
            )

            style_h1 = ParagraphStyle(
                "CSRDH1",
                parent=styles["Heading1"],
                fontSize=options.font_size_header * 1.3,
                leading=options.font_size_header * 1.6,
                fontName="Helvetica-Bold",
                textColor=colors["primary"],
                spaceAfter=12,
                spaceBefore=20,
                borderWidth=0,
                borderPadding=0,
            )

            style_h2 = ParagraphStyle(
                "CSRDH2",
                parent=styles["Heading2"],
                fontSize=options.font_size_header * 1.05,
                leading=options.font_size_header * 1.4,
                fontName="Helvetica-Bold",
                textColor=colors["secondary"],
                spaceAfter=8,
                spaceBefore=16,
            )

            style_h3 = ParagraphStyle(
                "CSRDH3",
                parent=styles["Heading3"],
                fontSize=options.font_size_body * 1.1,
                leading=options.font_size_body * 1.4,
                fontName="Helvetica-Bold",
                textColor=colors["text_primary"],
                spaceAfter=6,
                spaceBefore=12,
            )

            style_company = ParagraphStyle(
                "CompanyName",
                fontName="Helvetica-Bold",
                fontSize=9,
                textColor=white,
                alignment=TA_LEFT,
            )

            style_report_title = ParagraphStyle(
                "ReportTitle",
                fontName="Helvetica-Bold",
                fontSize=11,
                textColor=white,
                alignment=TA_LEFT,
                spaceBefore=2,
            )

            style_footer = ParagraphStyle(
                "Footer",
                fontName="Helvetica",
                fontSize=7,
                textColor=HexColor("#94a3b8"),
                alignment=TA_CENTER,
            )

            style_toc = ParagraphStyle(
                "TOC",
                parent=style_body,
                fontSize=9,
                textColor=colors["secondary"],
                leftIndent=10,
                spaceAfter=4,
            )

            style_toc_header = ParagraphStyle(
                "TOCH",
                fontName="Helvetica-Bold",
                fontSize=12,
                textColor=colors["primary"],
                spaceAfter=10,
                spaceBefore=20,
            )

            # ── Header / Footer Callbacks ──────────────────────
            header_data = options.header
            footer_data = options.footer

            def add_header_footer(canvas_obj, doc):
                """Draw header and footer on each page."""
                canvas_obj.saveState()

                # ── Header Line ───────────────────────────────
                # Colored bar at top
                canvas_obj.setFillColor(colors["header_bg"])
                canvas_obj.rect(
                    0, page_height - 15 * mm,
                    page_width, 15 * mm,
                    fill=1, stroke=0,
                )

                # Company name in header
                canvas_obj.setFillColor(white)
                canvas_obj.setFont("Helvetica-Bold", 9)
                canvas_obj.drawString(
                    10 * mm, page_height - 12 * mm,
                    header_data.company_name[:80],
                )

                # Report info on right side of header
                canvas_obj.setFont("Helvetica", 7)
                canvas_obj.drawRightString(
                    page_width - 10 * mm, page_height - 12 * mm,
                    f"{header_data.report_title} | {header_data.reporting_year}",
                )

                # ── Footer ────────────────────────────────────
                canvas_obj.setFillColor(colors["footer_bg"])
                canvas_obj.rect(
                    0, 0, page_width, 12 * mm,
                    fill=1, stroke=0,
                )

                canvas_obj.setStrokeColor(colors["border"])
                canvas_obj.setLineWidth(0.5)
                canvas_obj.line(
                    10 * mm, 12 * mm,
                    page_width - 10 * mm, 12 * mm,
                )

                # Confidentiality text
                canvas_obj.setFillColor(HexColor("#94a3b8"))
                canvas_obj.setFont("Helvetica", 6)
                canvas_obj.drawString(
                    10 * mm, 5 * mm,
                    footer_data.confidentiality_text[:100],
                )

                # Date
                if footer_data.show_date:
                    canvas_obj.drawString(
                        10 * mm, 2 * mm,
                        f"Generated: {datetime.now().strftime('%d/%m/%Y %H:%M')}",
                    )

                # Page number
                if footer_data.show_page_numbers:
                    canvas_obj.drawRightString(
                        page_width - 10 * mm, 5 * mm,
                        f"Page {doc.page}",
                    )

                # Additional footer text
                if footer_data.additional_text:
                    canvas_obj.drawCentredString(
                        page_width / 2, 2 * mm,
                        footer_data.additional_text[:80],
                    )

                # ── Watermark ─────────────────────────────────
                if options.watermark:
                    canvas_obj.saveState()
                    canvas_obj.setFillColor(
                        HexColor("#ff000008")
                    )
                    canvas_obj.setFont("Helvetica-Bold", 60)
                    canvas_obj.translate(
                        page_width / 2, page_height / 2
                    )
                    canvas_obj.rotate(45)
                    canvas_obj.drawCentredString(
                        0, 0, options.watermark
                    )
                    canvas_obj.restoreState()

                canvas_obj.restoreState()

            # ── Build Document ────────────────────────────────
            doc = BaseDocTemplate(
                buffer,
                pagesize=A4,
                topMargin=margin_top + 15 * mm,  # Extra space for header
                bottomMargin=margin_bottom + 12 * mm,  # Extra space for footer
                leftMargin=margin_left,
                rightMargin=margin_right,
                title=f"{header_data.report_title} — {header_data.company_name}",
                author=header_data.company_name,
                subject="CSRD Compliance Report",
            )

            frame = Frame(
                margin_left,
                margin_bottom + 12 * mm,  # Footer space
                page_width - margin_left - margin_right,
                page_height - margin_top - margin_bottom - 27 * mm,  # Header + footer
                id="normal",
            )

            doc.addPageTemplates([
                PageTemplate(id="main", frames=[frame], onPage=add_header_footer),
            ])

            # ── Build Story ───────────────────────────────────
            story = []

            # ── Cover Page ────────────────────────────────────
            story.append(Spacer(1, 80 * mm))

            # Title block
            story.append(Paragraph(
                header_data.company_name,
                ParagraphStyle(
                    "CoverCompany",
                    fontName="Helvetica-Bold",
                    fontSize=18,
                    textColor=colors["primary"],
                    alignment=TA_CENTER,
                    spaceAfter=10,
                )
            ))

            story.append(Paragraph(
                header_data.report_title,
                ParagraphStyle(
                    "CoverTitle",
                    fontName="Helvetica-Bold",
                    fontSize=24,
                    textColor=colors["secondary"],
                    alignment=TA_CENTER,
                    spaceAfter=20,
                )
            ))

            story.append(Paragraph(
                f"Reporting Year: {header_data.reporting_year}",
                ParagraphStyle(
                    "CoverYear",
                    fontName="Helvetica",
                    fontSize=14,
                    textColor=colors["text_secondary"],
                    alignment=TA_CENTER,
                    spaceAfter=40,
                )
            ))

            # Info box
            cover_info = [
                ["Prepared for:", header_data.company_name],
                ["Report type:", "CSRD / ESRS Compliance Report"],
                ["Standard:", "European Sustainability Reporting Standards (ESRS)"],
                ["Date:", datetime.now().strftime("%d/%m/%Y")],
                ["Language:", options.language.upper()],
                ["Classification:", footer_data.confidentiality_text],
            ]

            info_table = Table(
                cover_info,
                colWidths=[50 * mm, 100 * mm],
                style=[
                    ("FONTNAME", (0, 0), (0, -1), "Helvetica-Bold"),
                    ("FONTSIZE", (0, 0), (-1, -1), 9),
                    ("TEXTCOLOR", (0, 0), (0, -1), colors["text_secondary"]),
                    ("TEXTCOLOR", (1, 0), (1, -1), colors["text_primary"]),
                    ("TOPPADDING", (0, 0), (-1, -1), 4),
                    ("BOTTOMPADDING", (0, 0), (-1, -1), 4),
                    ("LINEBELOW", (0, 0), (-1, -1), 0.5, colors["border"]),
                    ("ALIGN", (0, 0), (-1, -1), "LEFT"),
                ],
            )

            story.append(info_table)
            story.append(PageBreak())

            # ── Table of Contents ─────────────────────────────
            if options.include_toc:
                story.append(Paragraph("Table of Contents", style_toc_header))

                # Extract headings from content
                import re
                toc_entries = re.findall(
                    r'<h[12][^>]*>(.*?)</h[12]>',
                    xhtml_content, re.DOTALL
                )
                level = 1
                for entry in toc_entries:
                    clean_entry = re.sub(r'<[^>]+>', '', entry).strip()
                    if clean_entry:
                        indent = 10 if entry.startswith("<h2") else 0
                        story.append(Paragraph(
                            clean_entry,
                            ParagraphStyle(
                                "TOCEntry",
                                parent=style_toc,
                                leftIndent=indent,
                                fontSize=9 if entry.startswith("<h2") else 10,
                                fontName="Helvetica-Bold" if entry.startswith("<h1") else "Helvetica",
                            )
                        ))

                story.append(Spacer(1, 10 * mm))
                story.append(PageBreak())

            # ── Main Content ──────────────────────────────────
            # Parse XHTML to ReportLab elements
            import re as _re
            elements = self._parse_xhtml_to_elements(
                xhtml_content, style_h1, style_h2, style_h3, style_body, colors
            )
            story.extend(elements)

            # ── Disclaimer ────────────────────────────────────
            story.append(Spacer(1, 20 * mm))
            story.append(Paragraph(
                "Disclaimer",
                ParagraphStyle(
                    "DisclaimerTitle",
                    fontName="Helvetica-Bold",
                    fontSize=8,
                    textColor=colors["text_secondary"],
                    spaceBefore=20,
                    spaceAfter=4,
                )
            ))
            story.append(Paragraph(
                "This report has been generated automatically by CSRD Comply. "
                "While every effort has been made to ensure accuracy, this document "
                "should be reviewed by a qualified sustainability professional before "
                "submission to any regulatory authority.",
                ParagraphStyle(
                    "DisclaimerText",
                    fontName="Helvetica-Oblique",
                    fontSize=7,
                    textColor=HexColor("#94a3b8"),
                    spaceAfter=6,
                )
            ))

            # ── Build ─────────────────────────────────────────
            doc.build(story)
            pdf_bytes = buffer.getvalue()

            logger.info(
                f"Professional PDF generated: {len(pdf_bytes)} bytes | "
                f"Pages: estimated {len(story)} elements"
            )
            return pdf_bytes

        except ImportError as e:
            raise ProfessionalPDFError(
                f"ReportLab is required: {e}. Install with: pip install reportlab"
            )
        except Exception as e:
            logger.error(f"Professional PDF generation failed: {e}", exc_info=True)
            raise ProfessionalPDFError(f"Professional PDF generation failed: {e}")

    def _parse_xhtml_to_elements(
        self,
        xhtml: str,
        style_h1: Any,
        style_h2: Any,
        style_h3: Any,
        style_body: Any,
        colors: Dict[str, Any],
    ) -> List[Any]:
        """
        Parse XHTML content to ReportLab flowables.

        Converts:
        - h1, h2, h3 → ReportLab headings
        - p → ReportLab paragraphs
        - table → ReportLab tables
        - ul/ol → ReportLab lists
        """
        from reportlab.platypus import Paragraph, Spacer, Table, TableStyle, ListFlowable, ListItem

        import re
        elements = []
        content_chunks = self._split_xhtml(xhtml)

        for chunk_type, content in content_chunks:
            try:
                if chunk_type == "h1":
                    clean = re.sub(r'<[^>]+>', '', content).strip()
                    elements.append(Paragraph(clean, style_h1))

                elif chunk_type == "h2":
                    clean = re.sub(r'<[^>]+>', '', content).strip()
                    elements.append(Paragraph(clean, style_h2))

                elif chunk_type == "h3":
                    clean = re.sub(r'<[^>]+>', '', content).strip()
                    elements.append(Paragraph(clean, style_h3))

                elif chunk_type == "p":
                    clean = re.sub(r'<[^>]+>', '', content).strip()
                    if clean:
                        elements.append(Paragraph(clean, style_body))

                elif chunk_type == "table":
                    # Parse table structure
                    rows = re.findall(r'<tr[^>]*>(.*?)</tr>', content, re.DOTALL)
                    if rows:
                        table_data = []
                        for row in rows:
                            cells = re.findall(
                                r'<t[dh][^>]*>(.*?)</t[dh]>',
                                row, re.DOTALL
                            )
                            clean_cells = [
                                re.sub(r'<[^>]+>', '', c).strip()
                                for c in cells
                            ]
                            if clean_cells:
                                table_data.append(clean_cells)

                        if table_data:
                            col_count = max(len(r) for r in table_data)
                            col_width = 160 * 72 / 25.4 / col_count  # ~160mm total

                            t = Table(
                                table_data,
                                colWidths=[col_width] * col_count,
                                style=[
                                    ("FONTNAME", (0, 0), (-1, 0), "Helvetica-Bold"),
                                    ("FONTSIZE", (0, 0), (-1, -1), 8),
                                    ("BACKGROUND", (0, 0), (-1, 0), colors["bg_table_header"]),
                                    ("TEXTCOLOR", (0, 0), (-1, 0), (1, 1, 1)),
                                    ("ALIGN", (0, 0), (-1, -1), "LEFT"),
                                    ("VALIGN", (0, 0), (-1, -1), "MIDDLE"),
                                    ("GRID", (0, 0), (-1, -1), 0.5, colors["border"]),
                                    ("TOPPADDING", (0, 0), (-1, -1), 4),
                                    ("BOTTOMPADDING", (0, 0), (-1, -1), 4),
                                    ("LEFTPADDING", (0, 0), (-1, -1), 6),
                                    ("RIGHTPADDING", (0, 0), (-1, -1), 6),
                                ],
                            )
                            elements.append(t)
                            elements.append(Spacer(1, 6))

            except Exception as e:
                logger.warning(f"Failed to parse chunk {chunk_type}: {e}")
                continue

        return elements

    def _split_xhtml(self, xhtml: str) -> List[Tuple[str, str]]:
        """
        Split XHTML content into semantic chunks.

        Returns list of (tag_name, raw_content) tuples.
        """
        import re

        # Normalize
        xhtml = xhtml.replace("\n", " ").replace("\r", " ")
        xhtml = re.sub(r'\s+', ' ', xhtml)

        chunks = []

        # Find all block-level elements
        pattern = r'<(h[123]|p|table)[^>]*>.*?</\1>'
        matches = re.findall(pattern, xhtml, re.DOTALL)

        for tag, content in re.findall(
            r'<(/??)(h[123]|p|table|ul|ol)[^>]*>',
            xhtml, re.DOTALL
        ):
            # Use another approach: find all complete elements
            pass

        # Simpler approach: find complete blocks
        block_pattern = re.compile(
            r'<(h[123]|p|table)(\s[^>]*)?>(.*?)</\1>',
            re.DOTALL
        )
        for match in block_pattern.finditer(xhtml):
            tag = match.group(1)
            content = match.group(3)
            chunks.append((tag, content))

        return chunks


# ── Singleton ────────────────────────────────────────────────

_pdf_service: Optional[ProfessionalPDFService] = None


def get_professional_pdf_service() -> ProfessionalPDFService:
    """Get or create professional PDF service singleton."""
    global _pdf_service
    if _pdf_service is None:
        _pdf_service = ProfessionalPDFService()
    return _pdf_service


def generate_professional_pdf(
    xhtml_content: str,
    company_name: str = "",
    report_title: str = "",
    reporting_year: int = 2026,
    watermark: Optional[str] = None,
    include_toc: bool = True,
    color_scheme: str = "professional",
) -> bytes:
    """
    Quick helper to generate a professional PDF.

    Args:
        xhtml_content: XHTML report content
        company_name: Company name for header
        report_title: Report title for header
        reporting_year: Reporting year
        watermark: Optional watermark text
        include_toc: Include table of contents

    Returns:
        PDF as bytes
    """
    service = get_professional_pdf_service()
    if not service.is_available:
        raise ProfessionalPDFError(
            "Professional PDF generation requires ReportLab"
        )

    options = PDFOptions(
        header=PDFHeader(
            company_name=company_name,
            report_title=report_title,
            reporting_year=reporting_year,
        ),
        watermark=watermark,
        include_toc=include_toc,
        color_scheme=color_scheme,
    )

    return service.generate_pdf(xhtml_content, options)
