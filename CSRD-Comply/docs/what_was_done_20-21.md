# Cosa è stato fatto — Steps 20-21: iXBRL Tagging & Validation Engine

## File creati

### `ai-engine/report_generator/ixbrl_tagger.py` (Step 20)
Motore di tagging iXBRL che converte report XHTML in formato iXBRL (XHTML + tag XML XBRL embedded). Include:

- **ESRSXBRLTaxonomy**: caricatore tassonomia ESRS (da file .xsd o mapping predefinito)
- **XBRLFact / XBRLContext / XBRLUnit**: data classes per rappresentare fatti XBRL
- **IXBRLTagger**: classe principale che applica tagging iXBRL (namespace, header con context/unit, `<ix:nonFraction>` per valori numerici, `<ix:nonNumeric>` per blocchi testuali)
- **ESRS_DATAPOINT_MAP**: mapping datapoint ESRS → concept XBRL (Scope1, Scope2, Total, Energy, Workforce, ecc.)
- **generate_ixbrl_report_api()**: helper per endpoint API

### `ai-engine/report_generator/ixbrl_validator.py` (Step 21)
Validatore iXBRL con regole built-in e supporto per Arelle:

- **ValidationIssue / ValidationResult / ValidationSeverity / ValidationCategory**: data classes per risultati validazione
- **IXBRLValidator**: classe principale con:
  - `validate_facts()`: validazione built-in (calcoli, unità, periodi, contesti, sintassi, dimensionalità)
  - `validate_file()`: validazione file (con Arelle se disponibile, con fallback built-in)
  - `validate_template()`: validazione preliminare del ReportTemplate
- **CALCULATION_RULES**: 3 regole di calcolo (GHG Total, Energy Total, Employee Total)
- **VALID_UNITS**: mappatura concetti → unità ammesse
- **CORRECTION_SUGGESTIONS**: suggerimenti correzione per errori comuni
- **validate_ixbrl_report() / validate_ixbrl_report_api()**: helper API

### `ai-engine/report_generator/__init__.py` (aggiornato)
Aggiunti import e `__all__` per i nuovi moduli.

### `docs/20-21.md`
Documentazione completa con architettura, API reference, esempi d'uso.

## Architettura

```
ReportTemplate -> NarrativeGenerator -> TableGenerator -> IXBRLTagger -> IXBRLValidator
```

Pipeline completa: dal template alla validazione iXBRL certificata.

## Integrazione

- **Tassonomia XBRL ESRS**: caricata da file .xsd ufficiale o mapping predefinito
- **Arelle**: validatore XBRL open source usato come subprocess per validazione completa contro la tassonomia
- **Fallback automatico**: se Arelle non è installato, validazione built-in (calcoli, unità, periodi, sintassi)

## Verifica

```python
# Test rapido
from ai_engine.report_generator import ReportTemplate, IXBRLTagger, IXBRLValidator

template = ReportTemplate.create_default_template("Test Srl", 2026)
tagger = IXBRLTagger()
tagger.load_taxonomy()

company_data = {
    "emissions": {"scope1": 105.0, "scope2_location": 75.0, "scope3": 420.0},
    "workforce": {"total": 120},
}
ixbrl = tagger.tag_report_from_template(template, company_data)

facts = tagger.extract_facts_from_xhtml(ixbrl)
result = IXBRLValidator().validate_facts(facts)
print(result.summary())  # ✅ PASSED / Score: 100.0%
```
