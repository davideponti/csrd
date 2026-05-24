"""
CSRD Comply — ESRS Parser Module

Parsing tassonomia ESRS, gap analysis, NLP mapping.
"""
from .ingest_taxonomy import load_taxonomy, get_all_datapoints
from .esrs_nlp_mapper import EsrsNlpMapper, ESMapper, CompanyProfile
from .gap_analyzer import GapAnalyzer

__all__ = [
    "load_taxonomy",
    "get_all_datapoints",
    "EsrsNlpMapper",
    "ESMapper",
    "CompanyProfile",
    "GapAnalyzer",
]
