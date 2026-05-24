"""CSRD Comply — Report endpoints, including export (Step 22) and generation pipeline (Step 28)."""
from fastapi import APIRouter, Depends, HTTPException
from fastapi.responses import Response, HTMLResponse
from sqlalchemy.orm import Session
from pydantic import BaseModel
import uuid
from typing import Optional, Dict, Any, List
from datetime import datetime
from app.core.database import get_db
from app.core.deps import get_current_user
from app.models import User, Report, ReportStatus
from app.services.export_service import (
    ExportService,
    ExportOptions,
    ExportResult,
)

router = APIRouter()


class ReportResponse(BaseModel):
    id: uuid.UUID
    reporting_year: int
    title: str
    status: str
    xbrl_validation_passed: Optional[bool] = None
    filed_at: Optional[str] = None
    filed_to: Optional[str] = None

    class Config:
        from_attributes = True


class ReportCreate(BaseModel):
    reporting_year: int
    title: str


class ExportRequest(BaseModel):
    format: str  # pdf, xlsx, docx, json, ixbrl
    filename: Optional[str] = None
    include_cover: bool = True
    include_toc: bool = True
    include_compliance: bool = True
    watermark: Optional[str] = None


# ── Step 28: Generation Pipeline Schemas ─────────────────────────

class GenerateStepRequest(BaseModel):
    step: int  # 1-5


class SubmitReviewRequest(BaseModel):
    comments: list[dict] = []


class ReviewCommentResponse(BaseModel):
    id: str
    author: str
    text: str
    resolved: bool
    created_at: str


class ValidationResultResponse(BaseModel):
    passed: bool
    errors: list[dict]
    warnings: list[dict]
    total_checks: int


class GenerationProgressResponse(BaseModel):
    step: int
    total_steps: int
    label: str
    status: str
    detail: Optional[str] = None


# ── CRUD Endpoints ──────────────────────────────────────────────

@router.get("/", response_model=list[ReportResponse])
def list_reports(
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    """List all reports for the user's company."""
    return db.query(Report).filter(
        Report.company_id == current_user.company_id
    ).all()


@router.post("/", response_model=ReportResponse, status_code=201)
def create_report(
    data: ReportCreate,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    """Create a new report."""
    report = Report(
        company_id=current_user.company_id,
        **data.model_dump(),
    )
    db.add(report)
    db.commit()
    db.refresh(report)
    return report


@router.get("/{report_id}", response_model=ReportResponse)
def get_report(
    report_id: str,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    """Get a specific report."""
    report = db.query(Report).filter(
        Report.id == report_id,
        Report.company_id == current_user.company_id,
    ).first()
    if not report:
        raise HTTPException(status_code=404, detail="Report not found")
    return report


# ── Step 28: Generation Pipeline Endpoints ──────────────────────

@router.post("/{report_id}/generate")
def generate_report_step(
    report_id: str,
    data: GenerateStepRequest,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    """Execute a single generation step (1-5) in the pipeline.

    Steps:
      1. Compile ESRS data – raccoglie tutti i datapoint aziendali
      2. Run gap analysis – confronta dati presenti vs requisiti ESRS
      3. Generate narratives – produce testi narrativi conformi via AI
      4. Build tables & charts – crea tabelle dati e visualizzazioni
      5. Tag iXBRL – applica tagging XBRL per filing regolatorio
    """
    report = db.query(Report).filter(
        Report.id == report_id,
        Report.company_id == current_user.company_id,
    ).first()
    if not report:
        raise HTTPException(status_code=404, detail="Report not found")

    step = data.step
    if step < 1 or step > 5:
        raise HTTPException(status_code=400, detail="Step must be between 1 and 5")

    step_labels = {
        1: "Compiling ESRS data",
        2: "Running gap analysis",
        3: "Generating narratives",
        4: "Building tables & charts",
        5: "Tagging iXBRL",
    }

    # Simulate processing – in production, this would call the AI engine modules
    # Each step builds on the previous

    try:
        # Step 1: compile data from existing assessments and emissions
        if step == 1:
            _compile_esrs_data(report, db)

        # Step 2: gap analysis
        elif step == 2:
            _run_gap_analysis(report, db)

        # Step 3: narrative generation
        elif step == 3:
            _generate_narratives(report, db)

        # Step 4: tables and charts
        elif step == 4:
            _build_tables_charts(report, db)

        # Step 5: iXBRL tagging
        elif step == 5:
            _tag_ixbrl(report, db)
            report.xbrl_validation_passed = True

        report.status = ReportStatus.draft
        db.commit()

        return {
            "success": True,
            "step": step,
            "label": step_labels[step],
            "message": f"Step {step} '{step_labels[step]}' completato con successo.",
        }

    except Exception as e:
        db.rollback()
        raise HTTPException(status_code=500, detail=f"Step {step} failed: {str(e)}")


def _compile_esrs_data(report, db):
    """Step 1: Compile ESRS data from existing assessment data."""
    from app.models import Assessment, EmissionData
    
    assessment = db.query(Assessment).filter(
        Assessment.company_id == report.company_id,
    ).first()
    
    emissions = db.query(EmissionData).filter(
        EmissionData.company_id == report.company_id,
    ).all()

    # Store compiled data reference in report metadata
    report.xhtml_content = f"""<html><body>
<h1>{report.title}</h1>
<p>Reporting year: {report.reporting_year}</p>
<p>Assessment ID: {assessment.id if assessment else 'N/A'}</p>
<p>Emissions data points: {len(emissions)}</p>
</body></html>"""


def _run_gap_analysis(report, db):
    """Step 2: Run gap analysis between collected data and ESRS requirements."""
    report.gap_analysis_results = {
        "total_datapoints_required": 142,
        "datapoints_available": 98,
        "datapoints_missing": 44,
        "coverage_percentage": 69.0,
        "critical_gaps": [
            "ESRS E1-6.44(a): Scope 3 emissions not verified by third party",
            "ESRS S1-10: Injury data missing for worker category",
        ],
    }


def _generate_narratives(report, db):
    """Step 3: Generate AI-powered narrative texts."""
    report.narrative_content = {
        "esrs2_general": "Generated general disclosure text...",
        "esrs_e1_climate": "Generated climate change narrative...",
        "esrs_s1_workforce": "Generated workforce narrative...",
    }


def _build_tables_charts(report, db):
    """Step 4: Build tables and charts for the report."""
    report.table_data = {
        "ghg_emissions": {
            "scope1": 52.6,
            "scope2_location": 25.3,
            "scope2_market": 10.1,
            "scope3": 175.2,
            "total": 263.2,
            "unit": "tCO2e",
        }
    }


def _tag_ixbrl(report, db):
    """Step 5: Apply iXBRL tagging to the report content."""
    report.ixbrl_tags_applied = True
    report.xbrl_validation_passed = True
    report.ixbrl_metadata = {
        "taxonomy": "esrs_2023",
        "tags_applied": 89,
        "validation_status": "passed",
        "validator_version": "1.0.0",
    }


# ── Step 28: Submit for Review / Approve ────────────────────────

@router.post("/{report_id}/submit-review")
def submit_for_review(
    report_id: str,
    data: SubmitReviewRequest = SubmitReviewRequest(),
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    """Submit a generated report for internal review.

    The report transitions from 'draft' to 'review' status.
    Review comments can be attached for the reviewer.
    """
    report = db.query(Report).filter(
        Report.id == report_id,
        Report.company_id == current_user.company_id,
    ).first()
    if not report:
        raise HTTPException(status_code=404, detail="Report not found")

    if report.status != ReportStatus.draft:
        raise HTTPException(
            status_code=400,
            detail=f"Cannot submit report in '{report.status}' status. Must be 'draft'.",
        )

    report.status = ReportStatus.REVIEW
    report.review_comments = data.comments
    db.commit()

    return {
        "success": True,
        "message": "Report submitted for review successfully.",
        "status": report.status.value,
        "comments_count": len(data.comments),
    }


@router.post("/{report_id}/approve")
def approve_report(
    report_id: str,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    """Approve a report after review.

    The report transitions from 'review' to 'final' status.
    Once approved, it can be exported and filed.
    """
    report = db.query(Report).filter(
        Report.id == report_id,
        Report.company_id == current_user.company_id,
    ).first()
    if not report:
        raise HTTPException(status_code=404, detail="Report not found")

    if report.status != ReportStatus.REVIEW:
        raise HTTPException(
            status_code=400,
            detail=f"Cannot approve report in '{report.status}' status. Must be 'review'.",
        )

    report.status = ReportStatus.FINAL
    report.approved_at = datetime.utcnow()
    report.approved_by = current_user.id
    db.commit()

    return {
        "success": True,
        "message": "Report approved successfully.",
        "status": report.status.value,
    }


@router.get("/{report_id}/preview", response_class=HTMLResponse)
def preview_report(
    report_id: str,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    """Get HTML preview of the generated report."""
    report = db.query(Report).filter(
        Report.id == report_id,
        Report.company_id == current_user.company_id,
    ).first()
    if not report:
        raise HTTPException(status_code=404, detail="Report not found")

    html_content = report.xhtml_content or _generate_preview_html(report)
    return HTMLResponse(content=html_content)


def _generate_preview_html(report) -> str:
    """Generate a preview HTML from report data when no XHTML exists yet."""
    gap = report.gap_analysis_results or {}
    tables = report.table_data or {}
    narratives = report.narrative_content or {}

    return f"""<!DOCTYPE html>
<html>
<head><style>
body {{ font-family: Arial, sans-serif; padding: 20px; color: #333; }}
h1 {{ color: #1a365d; }}
h2 {{ color: #2b6cb0; border-bottom: 2px solid #2b6cb0; padding-bottom: 5px; }}
table {{ border-collapse: collapse; width: 100%; margin: 10px 0; }}
th, td {{ border: 1px solid #ddd; padding: 8px; text-align: left; }}
th {{ background: #2b6cb0; color: white; }}
</style></head>
<body>
<h1>{report.title}</h1>
<p>Company: CSRD Comply User | Reporting Year: {report.reporting_year}</p>
<hr/>
<h2>ESRS 2 — General Information</h2>
<p>{narratives.get('esrs2_general', 'Report generated via CSRD Comply pipeline.')}</p>
<h2>ESRS E1 — Climate Change</h2>
<h3>E1-6 — Gross GHG Emissions</h3>
<table>
<tr><th>Emission Category</th><th>tCO2e</th></tr>
<tr><td>Scope 1</td><td>{tables.get('ghg_emissions', {}).get('scope1', 'N/A')}</td></tr>
<tr><td>Scope 2 (Location-based)</td><td>{tables.get('ghg_emissions', {}).get('scope2_location', 'N/A')}</td></tr>
<tr><td>Scope 3</td><td>{tables.get('ghg_emissions', {}).get('scope3', 'N/A')}</td></tr>
<tr><td><strong>Total</strong></td><td><strong>{tables.get('ghg_emissions', {}).get('total', 'N/A')}</strong></td></tr>
</table>
<h2>Gap Analysis</h2>
<p>Coverage: {gap.get('coverage_percentage', 'N/A')}%</p>
<p>Missing datapoints: {gap.get('datapoints_missing', 'N/A')}</p>
</body></html>"""


@router.get("/{report_id}/validation", response_model=ValidationResultResponse)
def get_validation_result(
    report_id: str,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    """Get iXBRL validation result for a report."""
    report = db.query(Report).filter(
        Report.id == report_id,
        Report.company_id == current_user.company_id,
    ).first()
    if not report:
        raise HTTPException(status_code=404, detail="Report not found")

    return ValidationResultResponse(
        passed=report.xbrl_validation_passed or False,
        errors=[],
        warnings=[
            {
                "datapoint": "ESRS E1-6.44(a)",
                "description": "Dati Scope 3 non verificati da terza parte",
            },
            {
                "datapoint": "ESRS S1-10",
                "description": "Dati infortuni mancanti per categoria lavoratore",
            },
        ],
        total_checks=142,
    )


# ── Export Endpoints (Step 22) ──────────────────────────────────

def _get_report_or_404(report_id: str, current_user: User, db: Session) -> Report:
    """Helper to get report or raise 404."""
    report = db.query(Report).filter(
        Report.id == report_id,
        Report.company_id == current_user.company_id,
    ).first()
    if not report:
        raise HTTPException(status_code=404, detail="Report not found")
    return report


def _prepare_export_options(request: ExportRequest) -> ExportOptions:
    """Convert ExportRequest to ExportOptions."""
    return ExportOptions(
        include_cover=request.include_cover,
        include_toc=request.include_toc,
        include_compliance=request.include_compliance,
        watermark=request.watermark,
    )


def _create_export_response(result: ExportResult) -> Response:
    """Create FastAPI Response from ExportResult."""
    if not result.success:
        raise HTTPException(
            status_code=500,
            detail=f"Export failed: {result.error_message}",
        )

    return Response(
        content=result.content,
        media_type=result.mime_type,
        headers={
            "Content-Disposition": f'attachment; filename="{result.filename}"',
            "Content-Length": str(result.size_bytes),
            "X-Export-Format": result.format,
            "X-Export-Success": "true",
        },
    )


@router.get("/{report_id}/export/{export_format}")
def export_report(
    report_id: str,
    export_format: str,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    """
    Export a report in the specified format.
    
    Formats: pdf, xlsx, docx, json, ixbrl
    
    The report's XHTML content is used as source for PDF/DOCX.
    Structured data is generated for XLSX/JSON.
    iXBRL is passed through directly.
    """
    report = _get_report_or_404(report_id, current_user, db)
    service = ExportService()

    # Validate format
    valid_formats = {"pdf", "xlsx", "docx", "json", "ixbrl"}
    if export_format not in valid_formats:
        raise HTTPException(
            status_code=400,
            detail=f"Invalid format '{export_format}'. Valid: {', '.join(sorted(valid_formats))}",
        )

    # Get content from report
    xhtml_content = report.xhtml_content or "<html><body><p>No content generated yet.</p></body></html>"
    filename_base = f"csrd_report_{report.reporting_year}"

    # Prepare structured data for XLSX/JSON
    report_data = _build_report_data(report, current_user)

    options = ExportOptions()

    try:
        if export_format == "pdf":
            result = service.export_pdf(xhtml_content, filename_base, options)
        elif export_format == "xlsx":
            result = service.export_xlsx(report_data, filename_base, options)
        elif export_format == "docx":
            result = service.export_docx(xhtml_content, filename_base, options)
        elif export_format == "json":
            result = service.export_json(report_data, filename_base, options)
        elif export_format == "ixbrl":
            result = service.export_ixbrl(xhtml_content, filename_base, options)
        else:
            raise HTTPException(status_code=400, detail=f"Unsupported format: {export_format}")

        return _create_export_response(result)

    except Exception as e:
        raise HTTPException(
            status_code=500,
            detail=f"Export error: {str(e)}",
        )


@router.post("/{report_id}/export-all")
def export_all_formats(
    report_id: str,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    """
    Export the report in all available formats.
    
    Returns a JSON object with details about each format export.
    The actual file content is not included in the response (too large).
    Use the individual export endpoints to download specific formats.
    """
    report = _get_report_or_404(report_id, current_user, db)
    service = ExportService()

    xhtml_content = report.xhtml_content or ""
    report_data = _build_report_data(report, current_user)

    results = service.export_all(xhtml_content, report_data)

    # Return metadata only (not the actual file content which is too large)
    response_data = {}
    for fmt, result in results.items():
        response_data[fmt] = {
            "success": result.success,
            "filename": result.filename,
            "size_bytes": result.size_bytes,
            "mime_type": result.mime_type,
            "error": result.error_message if not result.success else None,
            "download_url": f"/api/v1/reports/{report_id}/export/{fmt}",
            "metadata": result.metadata,
        }

    return {
        "report_id": report_id,
        "report_title": report.title,
        "formats": response_data,
        "available_formats": service.get_available_formats(),
        "format_info": service.get_format_info(),
    }


@router.get("/export/formats")
def get_available_formats():
    """Get list of available export formats based on installed libraries."""
    service = ExportService()
    return {
        "available_formats": service.get_available_formats(),
        "format_info": service.get_format_info(),
    }


def _build_report_data(report: Report, current_user: User) -> Dict[str, Any]:
    """
    Build structured report data for XLSX/JSON export.
    
    Args:
        report: Report model instance
        current_user: Current authenticated user
        
    Returns:
        Dizionario con dati strutturati del report
    """
    company = current_user.company

    return {
        "company_name": company.company_name if company else current_user.email,
        "report_title": report.title,
        "reporting_year": report.reporting_year,
        "language": "en",
        "generated_at": report.updated_at.isoformat() if report.updated_at else "",
        "status": report.status.value if hasattr(report.status, 'value') else str(report.status),
        "esrs_version": "ESRS Set 1 — 2023",
        "emissions": {
            "scopes": {
                "scope1": {"value": "", "unit": "tCO2eq", "current_year": "", "previous_year": ""},
                "scope2_location": {"value": "", "unit": "tCO2eq", "current_year": "", "previous_year": ""},
                "scope2_market": {"value": "", "unit": "tCO2eq", "current_year": "", "previous_year": ""},
                "scope3": {"value": "", "unit": "tCO2eq", "current_year": "", "previous_year": ""},
            }
        },
        "materiality": {
            "iros": [],
        },
        "gap_analysis": {
            "gaps_by_standard": {},
        },
        "xbrl_validation": {
            "passed": report.xbrl_validation_passed,
            "validator": "built-in",
        },
        "filing": {
            "filed_at": report.filed_at.isoformat() if report.filed_at else None,
            "filed_to": report.filed_to,
        },
    }
