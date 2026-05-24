"""
CSRD Comply — Report Generation Engine (Fase 4)

Modulo per la generazione di report CSRD conformi in formato XHTML + iXBRL.
Include: template engine, narrative generator, table generator, iXBRL tagger.
"""
from .template_engine import (
    ReportTemplate,
    ReportSection,
    DisclosureRequirement,
    ContentBlock,
    XBRLTag,
    SectionType,
    SubSectionType,
    MaterialityFilter,
    CoverPage,
    create_table_block,
    create_narrative_block,
)

from .narrative_generator import (
    NarrativeGenerator,
    NarrativeInput,
    NarrativeOutput,
    create_narrative_input_from_block,
    update_template_with_narratives,
    generate_report_narratives_api,
)

from .table_generator import (
    TableGenerator,
    ESRSDataTable,
    TableColumn,
    TableRow,
    ChartData,
    update_template_with_tables,
    generate_report_tables_api,
)

from .ixbrl_tagger import (
    IXBRLTagger,
    IXBRLTaggerConfig,
    XBRLFact,
    XBRLContext,
    XBRLUnit,
    ESRSXBRLTaxonomy,
    ESRS_DATAPOINT_MAP,
    create_ixbrl_tagger,
    generate_ixbrl_report_api,
    iXBRLError,
)

from .ixbrl_validator import (
    IXBRLValidator,
    IXBRLValidatorError,
    ValidationResult,
    ValidationIssue,
    ValidationSeverity,
    ValidationCategory,
    create_validator,
    validate_ixbrl_report,
    validate_ixbrl_report_api,
)

__all__ = [
    # Template Engine
    "ReportTemplate",
    "ReportSection",
    "DisclosureRequirement",
    "ContentBlock",
    "XBRLTag",
    "SectionType",
    "SubSectionType",
    "MaterialityFilter",
    "CoverPage",
    "create_table_block",
    "create_narrative_block",
    # Narrative Generator
    "NarrativeGenerator",
    "NarrativeInput",
    "NarrativeOutput",
    "create_narrative_input_from_block",
    "update_template_with_narratives",
    "generate_report_narratives_api",
    # Table Generator
    "TableGenerator",
    "ESRSDataTable",
    "TableColumn",
    "TableRow",
    "ChartData",
    "update_template_with_tables",
    "generate_report_tables_api",
    # iXBRL Tagger (Step 20)
    "IXBRLTagger",
    "IXBRLTaggerConfig",
    "XBRLFact",
    "XBRLContext",
    "XBRLUnit",
    "ESRSXBRLTaxonomy",
    "ESRS_DATAPOINT_MAP",
    "create_ixbrl_tagger",
    "generate_ixbrl_report_api",
    "iXBRLError",
    # iXBRL Validator (Step 21)
    "IXBRLValidator",
    "IXBRLValidatorError",
    "ValidationResult",
    "ValidationIssue",
    "ValidationSeverity",
    "ValidationCategory",
    "create_validator",
    "validate_ixbrl_report",
    "validate_ixbrl_report_api",
]
