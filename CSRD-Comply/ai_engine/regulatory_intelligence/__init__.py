"""
CSRD Comply — Regulatory Intelligence Module (Fase 5)

Modulo per il monitoraggio e l'analisi di cambiamenti normativi CSRD/ESRS.
Include: web scraper per fonti EU, AI summarizer, regulatory advisor.
"""
from .scraper import (
    RegulatoryScraper,
    ScraperSource,
    ScrapedDocument,
    ScrapeResult,
    EURLexScraper,
    EFRAGScraper,
    ESMAScraper,
    NationalAuthorityScraper,
    create_scraper,
    scrape_all_sources,
)
from .update_analyzer import (
    UpdateAnalyzer,
    AnalyzedUpdate,
    RegulatoryChange,
    ImpactClassification,
    AffectedEntityType,
    ContentDownloader,
    analyze_update,
    analyze_update_sync,
    batch_analyze_updates,
)
from .advisor import (
    RegulatoryAdvisor,
    AdvisorReport,
    AdvisorTask,
    AdvisorSuggestion,
    DeadlineAlert,
    TaskPriority,
    TaskCategory,
    generate_advisor_report,
    task_list_to_dict,
    deadline_list_to_dict,
    suggestion_list_to_dict,
)

__all__ = [
    # Scraper
    "RegulatoryScraper",
    "ScraperSource",
    "ScrapedDocument",
    "ScrapeResult",
    "EURLexScraper",
    "EFRAGScraper",
    "ESMAScraper",
    "NationalAuthorityScraper",
    "create_scraper",
    "scrape_all_sources",
    # Update Analyzer
    "UpdateAnalyzer",
    "AnalyzedUpdate",
    "RegulatoryChange",
    "ImpactClassification",
    "AffectedEntityType",
    "ContentDownloader",
    "analyze_update",
    "analyze_update_sync",
    "batch_analyze_updates",
    # Advisor
    "RegulatoryAdvisor",
    "AdvisorReport",
    "AdvisorTask",
    "AdvisorSuggestion",
    "DeadlineAlert",
    "TaskPriority",
    "TaskCategory",
    "generate_advisor_report",
    "task_list_to_dict",
    "deadline_list_to_dict",
    "suggestion_list_to_dict",
]
