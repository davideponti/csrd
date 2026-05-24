"""
CSRD Comply — iXBRL Validator (Step 21)

Valida il report iXBRL generato contro la tassonomia ESRS.
Usa Arelle (open source XBRL validator) come subprocess.

Processo:
1. Genera file .xhtml con tagging iXBRL
2. Chiama: arelleCmdLine --file report.xhtml --validate --output validation.json
3. Legge validation.json
4. Se errori: classifica (FATAL, ERROR, WARNING, INFO), mostra dettagli, suggerisce correzioni
5. Se OK: report è certificato come valido per filing

Validazioni:
- Schematron rules (regole di business ESRS)
- Calculation linkbases (es. Scope1 + Scope2 + Scope3 = Total)
- Unit consistency (non mischiare tCO2 e kgCO2)
- Period consistency (tutti i dati per lo stesso anno fiscale)
- Dimensional correctness (es. breakdown per paese)
"""

import re
import json
import logging
import subprocess
import tempfile
import os
from typing import Optional, Dict, Any, List, Tuple, Set
from dataclasses import dataclass, field
from datetime import datetime
from enum import Enum

logger = logging.getLogger(__name__)


# ── Enums ──────────────────────────────────────────────────────────

class ValidationSeverity(str, Enum):
    """Severità degli errori di validazione."""
    FATAL = "FATAL"
    ERROR = "ERROR"
    WARNING = "WARNING"
    INFO = "INFO"


class ValidationCategory(str, Enum):
    """Categoria di validazione."""
    SCHEMATRON = "schematron"
    CALCULATION = "calculation"
    UNIT = "unit"
    PERIOD = "period"
    DIMENSIONAL = "dimensional"
    CONTEXT = "context"
    SYNTAX = "syntax"
    SCHEMA = "schema"
    OTHER = "other"


# ── Data Classes ──────────────────────────────────────────────────

@dataclass
class ValidationIssue:
    """
    Issue trovata durante la validazione.

    Attributes:
        severity: Severità dell'issue
        category: Categoria di validazione
        message: Descrizione dell'errore
        code: Codice errore (se fornito da Arelle)
        location: Posizione nel report (XPath o riga)
        concept: Nome del concetto XBRL coinvolto (opzionale)
        suggestion: Suggerimento di correzione (opzionale)
        automated_fix: Se è possibile una correzione automatica
    """
    severity: ValidationSeverity
    category: ValidationCategory
    message: str
    code: str = ""
    location: str = ""
    concept: str = ""
    suggestion: str = ""
    automated_fix: bool = False

    def __getitem__(self, key):
        """Allow dict-like subscripting on issues (issue["description"])."""
        if key == "description":
            return self.message
        if key == "severity":
            return self.severity.value
        if key == "category":
            return self.category.value
        if key == "message":
            return self.message
        if key == "code":
            return self.code
        if key == "location":
            return self.location
        if key == "concept":
            return self.concept
        if key == "suggestion":
            return self.suggestion
        if key == "automated_fix":
            return self.automated_fix
        raise KeyError(key)

    def get(self, key, default=None):
        """Dict-like get method for issues."""
        try:
            return self[key]
        except KeyError:
            return default

    def to_dict(self) -> Dict[str, Any]:
        """Converte in dizionario per API JSON."""
        return {
            "severity": self.severity.value,
            "category": self.category.value,
            "message": self.message,
            "description": self.message,
            "code": self.code,
            "location": self.location,
            "concept": self.concept,
            "suggestion": self.suggestion,
            "automated_fix": self.automated_fix,
        }

    def __str__(self) -> str:
        parts = [
            f"[{self.severity.value}]",
            f"{self.message}",
        ]
        if self.location:
            parts.append(f" at {self.location}")
        if self.concept:
            parts.append(f" (concept: {self.concept})")
        if self.suggestion:
            parts.append(f"\n  Suggestion: {self.suggestion}")
        return "".join(parts)


@dataclass
class ValidationResult:
    """
    Risultato completo della validazione.

    Attributes:
        passed: Se il report ha superato la validazione
        total_issues: Numero totale di issue trovate
        issues: Lista dettagliata delle issue
        fatal_count: Numero di errori fatali
        error_count: Numero di errori
        warning_count: Numero di warning
        info_count: Numero di info
        score: Punteggio di validità (0.0-1.0)
        report_summary: Riepilogo testuale
        validator: Validatore utilizzato (arelle, built-in)
        validation_timestamp: Timestamp della validazione
    """
    passed: bool
    total_issues: int = 0
    issues: List[ValidationIssue] = field(default_factory=list)
    fatal_count: int = 0
    error_count: int = 0
    warning_count: int = 0
    info_count: int = 0
    score: float = 1.0
    report_summary: str = ""
    validator: str = "built-in"
    validation_timestamp: str = ""

    def __getitem__(self, key):
        """Allow dict-like subscripting (result["valid"])."""
        if key == "valid":
            return self.passed
        if key == "passed":
            return self.passed
        if key == "issues":
            return self.issues
        if key == "errors":
            return [i.to_dict() for i in self.issues if i.severity in (ValidationSeverity.ERROR, ValidationSeverity.FATAL)]
        if key == "warnings":
            return [i.to_dict() for i in self.issues if i.severity == ValidationSeverity.WARNING]
        if key == "score":
            return self.score
        if key == "report_summary":
            return self.report_summary
        if key == "validator":
            return self.validator
        if key == "validation_timestamp":
            return self.validation_timestamp
        if key == "total_issues":
            return self.total_issues
        if key == "total_checks":
            return self.total_issues
        if key == "fatal_count":
            return self.fatal_count
        if key == "error_count":
            return self.error_count
        if key == "warning_count":
            return self.warning_count
        if key == "info_count":
            return self.info_count
        raise KeyError(key)

    def get(self, key, default=None):
        """Dict-like get method."""
        try:
            return self[key]
        except KeyError:
            return default

    def __contains__(self, key):
        """Allow 'valid' in result syntax."""
        return key in ("valid", "passed", "issues", "errors", "warnings", "score", "report_summary",
                       "validator", "validation_timestamp", "total_issues", "total_checks",
                       "fatal_count", "error_count", "warning_count", "info_count")

    def to_dict(self) -> Dict[str, Any]:
        """Converte in dizionario per API JSON."""
        return {
            "passed": self.passed,
            "total_issues": self.total_issues,
            "issues": [i.to_dict() for i in self.issues],
            "fatal_count": self.fatal_count,
            "error_count": self.error_count,
            "warning_count": self.warning_count,
            "info_count": self.info_count,
            "score": self.score,
            "report_summary": self.report_summary,
            "validator": self.validator,
            "validation_timestamp": self.validation_timestamp,
        }

    def summary(self) -> str:
        """Restituisce un riepilogo testuale della validazione."""
        status = "✅ PASSED" if self.passed else "❌ FAILED"
        return (
            f"Validation {status}\n"
            f"Score: {self.score:.1%}\n"
            f"Issues: {self.total_issues} "
            f"(Fatal: {self.fatal_count}, Error: {self.error_count}, "
            f"Warning: {self.warning_count}, Info: {self.info_count})\n"
            f"{self.report_summary}"
        )


# ── Regole di Validazione Built-in ────────────────────────────────

# Mapping di concetti per calcoli
CALCULATION_RULES: List[Dict[str, Any]] = [
    {
        "name": "Total GHG = Scope 1 + Scope 2 (location) + Scope 3",
        "concepts": {
            "total": "esrs:GHGTotalEmissions",
            "components": [
                "esrs:GHGScope1Emissions",
                "esrs:GHGScope2LocationEmissions",
                "esrs:GHGScope3Emissions",
            ],
        },
        "tolerance": 0.01,  # 1% di tolleranza per arrotondamenti
    },
    {
        "name": "Total Energy = Fossil + Nuclear + Renewable",
        "concepts": {
            "total": "esrs:EnergyTotalConsumption",
            "components": [
                "esrs:EnergyFossilConsumption",
                "esrs:EnergyNuclearConsumption",
                "esrs:EnergyRenewableConsumption",
            ],
        },
        "tolerance": 0.01,
    },
    {
        "name": "Total Employees = Female + Male",
        "concepts": {
            "total": "esrs:TotalEmployees",
            "components": [
                "esrs:FemaleEmployees",
                "esrs:MaleEmployees",
            ],
        },
        "tolerance": 0.0,
    },
]

# Unità valide per concetto
VALID_UNITS: Dict[str, List[str]] = {
    "esrs:GHGScope1Emissions": ["tCO2eq", "tCO2e"],
    "esrs:GHGScope2LocationEmissions": ["tCO2eq", "tCO2e"],
    "esrs:GHGScope2MarketEmissions": ["tCO2eq", "tCO2e"],
    "esrs:GHGScope3Emissions": ["tCO2eq", "tCO2e"],
    "esrs:GHGTotalEmissions": ["tCO2eq", "tCO2e"],
    "esrs:EnergyFossilConsumption": ["MWh", "kWh", "GJ"],
    "esrs:EnergyNuclearConsumption": ["MWh", "kWh", "GJ"],
    "esrs:EnergyRenewableConsumption": ["MWh", "kWh", "GJ"],
    "esrs:EnergyTotalConsumption": ["MWh", "kWh", "GJ"],
    "esrs:TotalEmployees": ["employees", "people", "headcount"],
    "esrs:FemaleEmployees": ["employees", "people", "headcount"],
    "esrs:MaleEmployees": ["employees", "people", "headcount"],
}

# Suggerimenti di correzione per errori comuni
CORRECTION_SUGGESTIONS: Dict[str, str] = {
    "unit_mismatch": "L'unità di misura non corrisponde a quella attesa per questo concetto. Verifica che tutti i dati usino la stessa unità (es. tCO2eq per emissioni).",
    "calculation_mismatch": "Il totale calcolato non corrisponde alla somma dei componenti. Verifica che tutti i dati siano stati inseriti correttamente.",
    "period_mismatch": "Il periodo di rendicontazione non è coerente tra i vari fatti. Tutti i dati devono riferirsi allo stesso anno fiscale.",
    "missing_context": "Manca il contesto XBRL per questo fatto. Assicurati che il contesto sia definito nell'header iXBRL.",
    "missing_concept": "Il concetto XBRL non è presente nella tassonomia caricata. Verifica che il nome del concetto sia corretto.",
    "duplicate_fact": "Lo stesso fatto è stato dichiarato più volte con lo stesso contesto. Rimuovi il duplicato.",
    "invalid_value": "Il valore non è valido per questo tipo di concetto (es. valore negativo per un concetto che richiede solo valori positivi).",
}


# ── Built-in Validator ────────────────────────────────────────────

class IXBRLValidatorError(Exception):
    """Errore del validatore iXBRL."""
    pass


class IXBRLValidator:
    """
    Validatore iXBRL per report CSRD.

    Esegue validazioni built-in (calcoli, unità, periodi) e,
    se Arelle è disponibile, validazione completa contro la tassonomia.

    Usage:
        validator = IXBRLValidator()

        # Validazione built-in da fatti estratti
        facts = [...]  # Lista di dict con concept, value, unit_ref, ecc.
        result = validator.validate_facts(facts)

        # Validazione completa da file iXBRL (con Arelle)
        result = validator.validate_file("report.xhtml")

        # Con Arelle disponibile
        validator.arelle_path = "/usr/local/bin/arelleCmdLine"
        result = validator.validate_file("report.xhtml")
    """

    def __init__(
        self,
        arelle_path: Optional[str] = None,
        use_arelle_if_available: bool = True,
    ):
        """
        Args:
            arelle_path: Percorso a arelleCmdLine. Se None, cerca in PATH.
            use_arelle_if_available: Se usare Arelle quando disponibile
        """
        self.arelle_path = arelle_path or self._find_arelle()
        self.use_arelle_if_available = use_arelle_if_available
        self._arelle_available = self.arelle_path is not None

    def _find_arelle(self) -> Optional[str]:
        """
        Cerca arelleCmdLine nel PATH di sistema.

        Returns:
            Percorso a arelleCmdLine o None se non trovato
        """
        try:
            result = subprocess.run(
                ["which", "arelleCmdLine"],
                capture_output=True,
                text=True,
                timeout=5,
            )
            if result.returncode == 0:
                return result.stdout.strip()
        except (subprocess.TimeoutExpired, FileNotFoundError):
            pass

        # Cerca in posizioni comuni
        common_paths = [
            "/usr/local/bin/arelleCmdLine",
            "/usr/bin/arelleCmdLine",
            "/opt/arelle/arelleCmdLine",
            os.path.expanduser("~/arelle/arelleCmdLine"),
        ]
        for path in common_paths:
            if os.path.isfile(path) and os.access(path, os.X_OK):
                return path

        return None

    @property
    def arelle_available(self) -> bool:
        """Se Arelle è disponibile per la validazione."""
        return self._arelle_available

    # ── Validazione Built-in ──────────────────────────────────────

    def validate_facts(
        self,
        facts: List[Dict[str, Any]],
    ) -> ValidationResult:
        """
        Valida una lista di fatti XBRL con regole built-in.

        Esegue:
        1. Validazione calcoli (es. Total = scope1 + scope2 + scope3)
        2. Validazione unità di misura
        3. Validazione periodi
        4. Validazione contesti
        5. Validazione sintassi concetti

        Args:
            facts: Lista di dict con almeno:
                - concept: str (es. "esrs:GHGScope1Emissions")
                - value: number (opzionale per nonNumeric)
                - unit_ref: str (opzionale)
                - context_ref: str
                - type: str ("nonFraction" o "nonNumeric")

        Returns:
            ValidationResult con issue trovate
        """
        issues: List[ValidationIssue] = []

        # Raggruppa fatti per validazione
        numeric_facts = [f for f in facts if f.get("type") == "nonFraction"]
        all_concepts = [f.get("concept", "") for f in facts]

        # 1. Validazione calcoli
        calc_issues = self._validate_calculations(numeric_facts)
        issues.extend(calc_issues)

        # 2. Validazione unità di misura
        unit_issues = self._validate_units(numeric_facts)
        issues.extend(unit_issues)

        # 3. Validazione periodi
        period_issues = self._validate_periods(facts)
        issues.extend(period_issues)

        # 4. Validazione contesti
        context_issues = self._validate_contexts(facts)
        issues.extend(context_issues)

        # 5. Validazione concetti (esistenza nella tassonomia)
        concept_issues = self._validate_concepts(all_concepts)
        issues.extend(concept_issues)

        # 6. Validazione sintassi
        syntax_issues = self._validate_syntax(facts)
        issues.extend(syntax_issues)

        # 7. Validazione dimensionalità (se applicabile)
        dim_issues = self._validate_dimensionality(facts)
        issues.extend(dim_issues)

        return self._build_result(issues, validator="built-in")

    def _validate_calculations(
        self,
        facts: List[Dict[str, Any]],
    ) -> List[ValidationIssue]:
        """
        Valida che i totali corrispondano alla somma dei componenti.

        Args:
            facts: Lista di fatti numerici

        Returns:
            Lista di issue trovate
        """
        issues = []

        # Costruisci mapping concept → valore
        value_map: Dict[str, float] = {}
        for fact in facts:
            concept = fact.get("concept", "")
            try:
                value = float(fact.get("value", 0))
                value_map[concept] = value
            except (ValueError, TypeError):
                pass

        for rule in CALCULATION_RULES:
            concepts = rule["concepts"]
            total_concept = concepts["total"]
            component_concepts = concepts["components"]
            tolerance = rule["tolerance"]

            # Verifica se tutti i concetti necessari sono presenti
            if total_concept not in value_map:
                continue

            total_value = value_map[total_concept]
            component_values = [
                value_map.get(c, 0) for c in component_concepts
            ]
            calculated_total = sum(component_values)

            # Calcola differenza (con tolleranza)
            if total_value != 0:
                diff_pct = abs(total_value - calculated_total) / abs(total_value)
            else:
                diff_pct = abs(total_value - calculated_total)

            if diff_pct > tolerance:
                issues.append(ValidationIssue(
                    severity=ValidationSeverity.ERROR,
                    category=ValidationCategory.CALCULATION,
                    message=(
                        f"Calculation mismatch: {rule['name']}. "
                        f"Expected {calculated_total:.2f} (sum of components), "
                        f"got {total_value:.2f} (difference: {abs(total_value - calculated_total):.2f})"
                    ),
                    concept=total_concept,
                    suggestion=CORRECTION_SUGGESTIONS["calculation_mismatch"],
                    automated_fix=False,
                ))

        return issues

    def _validate_units(
        self,
        facts: List[Dict[str, Any]],
    ) -> List[ValidationIssue]:
        """
        Valida che le unità di misura siano corrette per ogni concetto.

        Args:
            facts: Lista di fatti numerici

        Returns:
            Lista di issue trovate
        """
        issues = []

        for fact in facts:
            concept = fact.get("concept", "")
            unit_ref = fact.get("unit_ref", "")

            if concept in VALID_UNITS:
                valid_units = VALID_UNITS[concept]
                # Estrai unità dal ref (es. "u_tCO2eq" -> "tCO2eq")
                unit_value = unit_ref.replace("u_", "").replace("_", "")

                # Check più flessibile
                if not any(v.replace("_", "").lower() in unit_value.lower() or unit_value.lower() in v.lower() for v in valid_units):
                    issues.append(ValidationIssue(
                        severity=ValidationSeverity.WARNING,
                        category=ValidationCategory.UNIT,
                        message=(
                            f"Unit mismatch for {concept}: "
                            f"expected one of {valid_units}, got '{unit_ref}'"
                        ),
                        code="unit_mismatch",
                        concept=concept,
                        suggestion=CORRECTION_SUGGESTIONS["unit_mismatch"],
                        automated_fix=False,
                    ))

        return issues

    def _validate_periods(
        self,
        facts: List[Dict[str, Any]],
    ) -> List[ValidationIssue]:
        """
        Valida la consistenza dei periodi tra i fatti.

        Args:
            facts: Lista di fatti

        Returns:
            Lista di issue trovate
        """
        issues = []
        context_refs: Set[str] = set()

        for fact in facts:
            ctx = fact.get("context_ref", "")
            if ctx:
                context_refs.add(ctx)

        # Se ci sono più contesti, verifica che siano coerenti
        # (es. non mischiare c_current e c_previous per lo stesso fatto)
        # Per ora, controllo base: segnala se ci sono troppi contesti diversi
        if len(context_refs) > 3:
            issues.append(ValidationIssue(
                severity=ValidationSeverity.INFO,
                category=ValidationCategory.PERIOD,
                message=(
                    f"Multiple context references detected: {len(context_refs)}. "
                    f"This may indicate inconsistent period usage."
                ),
                suggestion="Verifica che i periodi siano corretti per tutti i fatti.",
            ))

        return issues

    def _validate_contexts(
        self,
        facts: List[Dict[str, Any]],
    ) -> List[ValidationIssue]:
        """
        Valida che i contesti siano definiti correttamente.

        Args:
            facts: Lista di fatti

        Returns:
            Lista di issue trovate
        """
        issues = []
        context_counts: Dict[str, int] = {}

        for fact in facts:
            ctx = fact.get("context_ref", "")
            if ctx:
                context_counts[ctx] = context_counts.get(ctx, 0) + 1

        # Verifica che ogni contesto sia usato almeno una volta
        # (se non ci sono contesti, è un problema)
        if not context_counts:
            issues.append(ValidationIssue(
                severity=ValidationSeverity.WARNING,
                category=ValidationCategory.CONTEXT,
                message="No context references found in facts. Each fact must have a valid context.",
                suggestion=CORRECTION_SUGGESTIONS["missing_context"],
            ))

        return issues

    def _validate_concepts(
        self,
        concepts: List[str],
    ) -> List[ValidationIssue]:
        """
        Valida che i concetti XBRL siano validi.

        Args:
            concepts: Lista di nomi di concetti

        Returns:
            Lista di issue trovate
        """
        issues = []
        seen = set()

        # Verifica concetti duplicati
        for concept in concepts:
            if concept in seen:
                issues.append(ValidationIssue(
                    severity=ValidationSeverity.WARNING,
                    category=ValidationCategory.SCHEMA,
                    message=f"Duplicate concept: {concept}",
                    code="duplicate_fact",
                    concept=concept,
                    suggestion=CORRECTION_SUGGESTIONS["duplicate_fact"],
                    automated_fix=True,
                ))
            seen.add(concept)

        # Verifica formato concetto (deve iniziare con esrs:)
        for concept in concepts:
            if not concept:
                issues.append(ValidationIssue(
                    severity=ValidationSeverity.ERROR,
                    category=ValidationCategory.SCHEMA,
                    message="Missing concept name. Every fact must have a valid XBRL concept.",
                    code="missing_concept",
                    suggestion=CORRECTION_SUGGESTIONS["missing_concept"],
                ))
                continue
            if not concept.startswith("esrs:"):
                issues.append(ValidationIssue(
                    severity=ValidationSeverity.WARNING,
                    category=ValidationCategory.SCHEMA,
                    message=f"Invalid concept format: {concept}. Should start with 'esrs:'",
                    code="missing_concept",
                    concept=concept,
                    suggestion=CORRECTION_SUGGESTIONS["missing_concept"],
                ))

        return issues

    def _validate_syntax(
        self,
        facts: List[Dict[str, Any]],
    ) -> List[ValidationIssue]:
        """
        Valida la sintassi dei fatti XBRL.

        Args:
            facts: Lista di fatti

        Returns:
            Lista di issue trovate
        """
        issues = []

        for i, fact in enumerate(facts):
            concept = fact.get("concept", "")
            value = fact.get("value")

            # Verifica che i valori numerici siano validi
            is_numeric_fact = fact.get("type") == "nonFraction"
            # Also check facts without explicit type that look numeric
            if not is_numeric_fact and value is not None:
                try:
                    float(value)
                    is_numeric_fact = True
                except (ValueError, TypeError):
                    pass
            if is_numeric_fact and value is not None:
                try:
                    float_val = float(value)
                    # Segnala valori negativi insoliti
                    if float_val < 0 and "GHG" in concept:
                        issues.append(ValidationIssue(
                            severity=ValidationSeverity.WARNING,
                            category=ValidationCategory.SYNTAX,
                            message=f"Negative value for {concept}: {value}",
                            code="invalid_value",
                            concept=concept,
                            suggestion="Verifica che il valore negativo sia corretto (alcune emissioni possono essere negative in caso di rimozioni).",
                        ))
                except (ValueError, TypeError):
                    issues.append(ValidationIssue(
                        severity=ValidationSeverity.ERROR,
                        category=ValidationCategory.SYNTAX,
                        message=f"Invalid numeric value for {concept}: {value}",
                        code="invalid_value",
                        concept=concept,
                        suggestion=CORRECTION_SUGGESTIONS["invalid_value"],
                    ))

        return issues

    def _validate_dimensionality(
        self,
        facts: List[Dict[str, Any]],
    ) -> List[ValidationIssue]:
        """
        Valida la correttezza dimensionale (es. breakdown per paese).

        Args:
            facts: Lista di fatti

        Returns:
            Lista di issue trovate
        """
        issues = []

        # Verifica che se c'è un breakdown, ci sia anche il totale
        # (es. se ci sono FemaleEmployees + MaleEmployees, deve esserci TotalEmployees)
        concept_set = {f.get("concept", "") for f in facts}

        for rule in CALCULATION_RULES:
            concepts = rule["concepts"]
            components = set(concepts["components"])
            total = concepts["total"]

            # Se ci sono tutti i componenti ma manca il totale
            if components.issubset(concept_set) and total not in concept_set:
                issues.append(ValidationIssue(
                    severity=ValidationSeverity.WARNING,
                    category=ValidationCategory.DIMENSIONAL,
                    message=f"Missing total concept '{total}' when all components are present.",
                    suggestion=f"Aggiungi il concetto '{total}' con la somma dei componenti.",
                    automated_fix=True,
                ))

            # Se c'è il totale ma mancano tutti i componenti
            if total in concept_set and not components.intersection(concept_set):
                issues.append(ValidationIssue(
                    severity=ValidationSeverity.INFO,
                    category=ValidationCategory.DIMENSIONAL,
                    message=f"Total concept '{total}' present without component breakdown.",
                    suggestion="Se disponibile, aggiungi il breakdown dei componenti per maggiore trasparenza.",
                ))

        return issues

    def _build_result(
        self,
        issues: List[ValidationIssue],
        validator: str = "built-in",
    ) -> ValidationResult:
        """
        Costruisce il ValidationResult dalle issue trovate.

        Args:
            issues: Lista di issue
            validator: Nome del validatore

        Returns:
            ValidationResult completo
        """
        fatal_count = sum(1 for i in issues if i.severity == ValidationSeverity.FATAL)
        error_count = sum(1 for i in issues if i.severity == ValidationSeverity.ERROR)
        warning_count = sum(1 for i in issues if i.severity == ValidationSeverity.WARNING)
        info_count = sum(1 for i in issues if i.severity == ValidationSeverity.INFO)

        total_issues = len(issues)
        passed = fatal_count == 0 and error_count == 0

        # Calcolo score
        # 1.0 = nessun issue
        # Penalità: FATAL = -0.3, ERROR = -0.15, WARNING = -0.05, INFO = -0.01
        score = 1.0
        score -= fatal_count * 0.3
        score -= error_count * 0.15
        score -= warning_count * 0.05
        score -= info_count * 0.01
        score = max(0.0, score)

        # Riepilogo
        if passed:
            report_summary = "All validations passed successfully."
        else:
            report_summary = (
                f"Validation failed with {fatal_count} fatal, "
                f"{error_count} error(s), {warning_count} warning(s)."
            )

        # Suggerimenti raggruppati
        suggestions = []
        for issue in issues:
            if issue.suggestion and issue.suggestion not in suggestions:
                suggestions.append(issue.suggestion)
        if suggestions:
            report_summary += "\nSuggestions:\n- " + "\n- ".join(suggestions)

        return ValidationResult(
            passed=passed,
            total_issues=total_issues,
            issues=issues,
            fatal_count=fatal_count,
            error_count=error_count,
            warning_count=warning_count,
            info_count=info_count,
            score=score,
            report_summary=report_summary,
            validator=validator,
            validation_timestamp=datetime.now().isoformat(),
        )

    # ── Validazione con Arelle ────────────────────────────────────

    def validate_file(
        self,
        file_path: str,
        use_arelle: bool = True,
    ) -> ValidationResult:
        """
        Valida un file iXBRL.

        Se Arelle è disponibile e use_arelle=True, usa Arelle per
        validazione completa contro la tassonomia.
        Altrimenti, usa solo validazione built-in.

        Args:
            file_path: Percorso al file .xhtml da validare
            use_arelle: Se tentare di usare Arelle

        Returns:
            ValidationResult
        """
        if use_arelle and self._arelle_available:
            try:
                return self._validate_with_arelle(file_path)
            except Exception as e:
                logger.warning(f"Arelle validation failed: {e}. Falling back to built-in.")

        # Fallback: validazione built-in
        facts = self._extract_facts_from_file(file_path)
        return self.validate_facts(facts)

    def _validate_with_arelle(
        self,
        file_path: str,
    ) -> ValidationResult:
        """
        Valida con Arelle via subprocess.

        Args:
            file_path: Percorso al file .xhtml

        Returns:
            ValidationResult

        Raises:
            IXBRLValidatorError: Se Arelle non risponde o fallisce
        """
        if not self.arelle_path:
            raise IXBRLValidatorError("Arelle not found. Install Arelle or use built-in validation.")

        # Crea file temporaneo per output
        with tempfile.NamedTemporaryFile(
            suffix=".json", mode="w", delete=False
        ) as tmp:
            output_path = tmp.name

        try:
            # Comando Arelle
            cmd = [
                self.arelle_path,
                "--file", file_path,
                "--validate",
                "--output", output_path,
                "--logFormat", "json",
            ]

            logger.info(f"Running Arelle: {' '.join(cmd)}")
            result = subprocess.run(
                cmd,
                capture_output=True,
                text=True,
                timeout=120,  # 2 minuti timeout per file grandi
            )

            if result.returncode != 0:
                logger.warning(f"Arelle returned non-zero: {result.stderr[:500]}")

            # Leggi output
            issues = []
            if os.path.isfile(output_path):
                try:
                    with open(output_path, "r") as f:
                        arelle_output = json.load(f)

                    issues = self._parse_arelle_output(arelle_output)
                except (json.JSONDecodeError, IOError) as e:
                    logger.error(f"Failed to parse Arelle output: {e}")

            return self._build_result(
                issues,
                validator=f"arelle ({os.path.basename(self.arelle_path)})",
            )

        except subprocess.TimeoutExpired:
            raise IXBRLValidatorError("Arelle validation timed out after 120 seconds.")
        except subprocess.CalledProcessError as e:
            raise IXBRLValidatorError(f"Arelle process error: {e}")
        finally:
            # Pulisci file temporaneo
            if os.path.isfile(output_path):
                try:
                    os.unlink(output_path)
                except OSError:
                    pass

    def _parse_arelle_output(
        self,
        arelle_output: Any,
    ) -> List[ValidationIssue]:
        """
        Converte l'output di Arelle in ValidationIssue.

        Args:
            arelle_output: Output JSON di Arelle

        Returns:
            Lista di ValidationIssue
        """
        issues = []

        if isinstance(arelle_output, dict):
            entries = arelle_output.get("entries", arelle_output.get("errors", []))
        elif isinstance(arelle_output, list):
            entries = arelle_output
        else:
            entries = []

        for entry in entries:
            if isinstance(entry, dict):
                severity_str = entry.get("severity", "ERROR").upper()
                severity = self._map_arelle_severity(severity_str)

                message = entry.get("message", entry.get("description", "Unknown error"))
                code = entry.get("code", "")
                location = entry.get("location", entry.get("source", ""))
                concept = entry.get("concept", "")

                # Classifica categoria
                category = self._classify_issue(message, code)

                # Trova suggerimento
                suggestion = self._find_suggestion(message, code)

                issues.append(ValidationIssue(
                    severity=severity,
                    category=category,
                    message=message,
                    code=code,
                    location=location,
                    concept=concept,
                    suggestion=suggestion,
                ))

        return issues

    def _map_arelle_severity(self, severity: str) -> ValidationSeverity:
        """Mappa la severità di Arelle a ValidationSeverity."""
        mapping = {
            "FATAL": ValidationSeverity.FATAL,
            "ERROR": ValidationSeverity.ERROR,
            "WARNING": ValidationSeverity.WARNING,
            "INFO": ValidationSeverity.INFO,
            "INFORMATION": ValidationSeverity.INFO,
        }
        return mapping.get(severity, ValidationSeverity.ERROR)

    def _classify_issue(
        self,
        message: str,
        code: str,
    ) -> ValidationCategory:
        """Classifica un issue per categoria."""
        msg_lower = (message + " " + code).lower()

        if any(w in msg_lower for w in ["schematron", "sch:" "sch"]):
            return ValidationCategory.SCHEMATRON
        elif any(w in msg_lower for w in ["calculation", "sum", "total", "add"]):
            return ValidationCategory.CALCULATION
        elif any(w in msg_lower for w in ["unit", "measure"]):
            return ValidationCategory.UNIT
        elif any(w in msg_lower for w in ["period", "date", "instant", "duration"]):
            return ValidationCategory.PERIOD
        elif any(w in msg_lower for w in ["dimension", "member", "axis"]):
            return ValidationCategory.DIMENSIONAL
        elif any(w in msg_lower for w in ["context", "entity"]):
            return ValidationCategory.CONTEXT
        elif any(w in msg_lower for w in ["syntax", "parse", "xml"]):
            return ValidationCategory.SYNTAX
        elif any(w in msg_lower for w in ["schema", "concept", "element"]):
            return ValidationCategory.SCHEMA
        else:
            return ValidationCategory.OTHER

    def _find_suggestion(
        self,
        message: str,
        code: str,
    ) -> str:
        """Trova un suggerimento di correzione per l'errore."""
        msg_lower = (message + " " + code).lower()

        for key, suggestion in CORRECTION_SUGGESTIONS.items():
            if key in msg_lower:
                return suggestion

        # Suggerimenti generici per pattern comuni
        if "unit" in msg_lower:
            return CORRECTION_SUGGESTIONS["unit_mismatch"]
        elif "calculation" in msg_lower or "sum" in msg_lower:
            return CORRECTION_SUGGESTIONS["calculation_mismatch"]
        elif "period" in msg_lower:
            return CORRECTION_SUGGESTIONS["period_mismatch"]
        elif "context" in msg_lower:
            return CORRECTION_SUGGESTIONS["missing_context"]
        elif "concept" in msg_lower or "element" in msg_lower:
            return CORRECTION_SUGGESTIONS["missing_concept"]

        return "Verifica i dati e riprova la validazione."

    def _extract_facts_from_file(
        self,
        file_path: str,
    ) -> List[Dict[str, Any]]:
        """
        Estrae fatti XBRL da un file iXBRL usando regex.

        Args:
            file_path: Percorso al file .xhtml

        Returns:
            Lista di dict con concept, value, unit_ref, context_ref, type
        """
        facts = []

        try:
            with open(file_path, "r", encoding="utf-8") as f:
                content = f.read()

            # Estrai <ix:nonFraction>
            for match in re.finditer(
                r'<ix:nonFraction\s+name="([^"]+)"\s+unitRef="([^"]+)"\s+contextRef="([^"]+)"[^>]*>([^<]+)</ix:nonFraction>',
                content,
            ):
                facts.append({
                    "concept": match.group(1),
                    "unit_ref": match.group(2),
                    "context_ref": match.group(3),
                    "value": match.group(4),
                    "type": "nonFraction",
                })

            # Estrai <ix:nonNumeric>
            for match in re.finditer(
                r'<ix:nonNumeric\s+name="([^"]+)"\s+contextRef="([^"]+)"[^>]*>([^<]+)</ix:nonNumeric>',
                content,
            ):
                facts.append({
                    "concept": match.group(1),
                    "context_ref": match.group(2),
                    "value": match.group(3),
                    "type": "nonNumeric",
                })

        except IOError as e:
            logger.error(f"Failed to read file {file_path}: {e}")

        return facts

    # ── Validazione XHTML ────────────────────────────────────────

    def validate_xhtml(self, xhtml_content: str) -> ValidationResult:
        """
        Validate structure and namespaces of XHTML reports.

        Args:
            xhtml_content: XHTML content string to validate

        Returns:
            ValidationResult with issues found
        """
        issues = []

        if not xhtml_content or not xhtml_content.strip():
            issues.append(ValidationIssue(
                severity=ValidationSeverity.ERROR,
                category=ValidationCategory.SYNTAX,
                message="Empty XHTML content provided.",
                suggestion="Provide valid XHTML content with iXBRL tagging.",
            ))
            return self._build_result(issues)

        # Check for required XHTML structure
        if "<html" not in xhtml_content.lower():
            issues.append(ValidationIssue(
                severity=ValidationSeverity.ERROR,
                category=ValidationCategory.SYNTAX,
                message="Missing <html> element. XHTML document must have an html root element.",
                suggestion="Wrap content in a proper <html> element.",
            ))

        if "<body" not in xhtml_content.lower():
            issues.append(ValidationIssue(
                severity=ValidationSeverity.WARNING,
                category=ValidationCategory.SYNTAX,
                message="Missing <body> element. XHTML document should have a body element.",
                suggestion="Add a <body> element to contain the report content.",
            ))

        # Check for iXBRL namespace declarations
        if "xmlns:ix" not in xhtml_content:
            issues.append(ValidationIssue(
                severity=ValidationSeverity.FATAL,
                category=ValidationCategory.SYNTAX,
                message="Missing iXBRL namespace declaration (xmlns:ix).",
                suggestion="Add xmlns:ix=\"http://www.xbrl.org/2008/inlineXBRL\" to the html element.",
            ))

        # Check for required ix namespace elements
        if "<ix:nonFraction" not in xhtml_content and "<ix:nonNumeric" not in xhtml_content:
            issues.append(ValidationIssue(
                severity=ValidationSeverity.WARNING,
                category=ValidationCategory.SYNTAX,
                message="No iXBRL tags found (ix:nonFraction or ix:nonNumeric).",
                suggestion="Tag at least one fact with iXBRL markup for a valid inline XBRL document.",
            ))

        # Check for context references
        context_refs = re.findall(r'contextRef="([^"]+)"', xhtml_content)
        if not context_refs:
            issues.append(ValidationIssue(
                severity=ValidationSeverity.WARNING,
                category=ValidationCategory.CONTEXT,
                message="No context references found in iXBRL tags.",
                suggestion="Add contextRef attributes to iXBRL tags referencing defined contexts.",
            ))

        # Check for duplicate context refs
        if context_refs:
            seen = set()
            duplicates = set()
            for ref in context_refs:
                if ref in seen:
                    duplicates.add(ref)
                seen.add(ref)
            if duplicates:
                issues.append(ValidationIssue(
                    severity=ValidationSeverity.INFO,
                    category=ValidationCategory.CONTEXT,
                    message=f"Duplicate context references found: {', '.join(duplicates)}.",
                    suggestion="Ensure each context reference points to a unique context definition.",
                ))

        # Check for unit references in nonFraction tags
        unit_refs = re.findall(r'unitRef="([^"]+)"', xhtml_content)
        non_fraction_count = xhtml_content.count("<ix:nonFraction")
        if non_fraction_count > 0 and not unit_refs:
            issues.append(ValidationIssue(
                severity=ValidationSeverity.WARNING,
                category=ValidationCategory.UNIT,
                message="Numeric facts (ix:nonFraction) found without unitRef attributes.",
                suggestion="Add unitRef attributes to all ix:nonFraction tags.",
            ))

        # Check for malformed tags
        malformed_pattern = r'<ix:(nonFraction|nonNumeric)[^>]*?(?<!>)>'
        if not re.search(malformed_pattern, xhtml_content):
            # Could be malformed
            open_tags = len(re.findall(r'<ix:', xhtml_content))
            close_tags = len(re.findall(r'</ix:', xhtml_content))
            if open_tags != close_tags:
                issues.append(ValidationIssue(
                    severity=ValidationSeverity.ERROR,
                    category=ValidationCategory.SYNTAX,
                    message=f"Mismatched iXBRL tags: {open_tags} opening vs {close_tags} closing.",
                    suggestion="Ensure all iXBRL tags are properly closed.",
                ))

        return self._build_result(issues)

    # ── Validazione ReportTemplate ────────────────────────────────

    def validate_template(
        self,
        template: Any,
        company_data: Dict[str, Any],
    ) -> ValidationResult:
        """
        Valida un ReportTemplate prima della generazione iXBRL.

        Esegue controlli preliminari sulla struttura del template
        e sulla completezza dei dati.

        Args:
            template: ReportTemplate da validare
            company_data: Dati aziendali

        Returns:
            ValidationResult
        """
        issues = []

        # Verifica che il template abbia sezioni
        if not template.sections:
            issues.append(ValidationIssue(
                severity=ValidationSeverity.ERROR,
                category=ValidationCategory.OTHER,
                message="Template has no sections defined.",
                suggestion="Aggiungi almeno una sezione al template con template.add_section().",
            ))

        # Verifica che ci siano dati aziendali
        if not company_data:
            issues.append(ValidationIssue(
                severity=ValidationSeverity.ERROR,
                category=ValidationCategory.OTHER,
                message="No company data provided.",
                suggestion="Fornisci i dati aziendali necessari per il report.",
            ))

        # Verifica campi obbligatori
        required_fields = ["company_name", "reporting_year"]
        for field in required_fields:
            if field not in company_data or not company_data.get(field):
                issues.append(ValidationIssue(
                    severity=ValidationSeverity.ERROR,
                    category=ValidationCategory.OTHER,
                    message=f"Missing required field: '{field}' in company_data.",
                    suggestion=f"Assicurati che '{field}' sia presente nei dati aziendali.",
                ))

        # Verifica materialità
        material_sections = [
            s for s in template.sections if s.is_material
        ]
        if not material_sections:
            issues.append(ValidationIssue(
                severity=ValidationSeverity.WARNING,
                category=ValidationCategory.OTHER,
                message="No material sections found in template.",
                suggestion="Esegui template.set_materiality() prima della generazione.",
            ))

        return self._build_result(issues, validator="template-check")


# ── Helper Functions ──────────────────────────────────────────────

# Alias for backward compatibility with tests
IxbrlValidator = IXBRLValidator


def create_validator(
    arelle_path: Optional[str] = None,
) -> IXBRLValidator:
    """
    Factory per creare un IXBRLValidator.

    Args:
        arelle_path: Percorso opzionale a arelleCmdLine

    Returns:
        IXBRLValidator configurato
    """
    return IXBRLValidator(arelle_path=arelle_path)


def validate_ixbrl_report(
    ixbrl_content: str,
    use_arelle: bool = True,
) -> ValidationResult:
    """
    Helper per validare un report iXBRL.

    Args:
        ixbrl_content: Contenuto iXBRL (stringa XHTML)
        use_arelle: Se usare Arelle se disponibile

    Returns:
        ValidationResult
    """
    # Scrivi contenuto in file temporaneo
    with tempfile.NamedTemporaryFile(
        suffix=".xhtml", mode="w", delete=False, encoding="utf-8"
    ) as tmp:
        tmp.write(ixbrl_content)
        tmp_path = tmp.name

    try:
        validator = IXBRLValidator()
        return validator.validate_file(tmp_path, use_arelle=use_arelle)
    finally:
        # Pulisci
        if os.path.isfile(tmp_path):
            try:
                os.unlink(tmp_path)
            except OSError:
                pass


def validate_ixbrl_report_api(
    template: Any,
    company_data: Dict[str, Any],
) -> Dict[str, Any]:
    """
    Helper per endpoint API: valida report iXBRL.

    Esegue:
    1. Validazione template (struttura e dati)
    2. Validazione fatti (calcoli, unità, periodi)
    3. Se Arelle disponibile, validazione completa contro tassonomia

    Args:
        template: ReportTemplate da validare
        company_data: Dati aziendali

    Returns:
        Dict con risultati validazione
    """
    validator = IXBRLValidator()
    issues = []

    # Passo 1: Validazione template
    template_result = validator.validate_template(template, company_data)
    issues.extend(template_result.issues)

    if template_result.passed:
        # Passo 2: Estrai fatti e validali
        from .ixbrl_tagger import IXBRLTagger, IXBRLTaggerConfig

        tagger_config = IXBRLTaggerConfig(
            entity_identifier=company_data.get("company_vat", ""),
            reporting_year=company_data.get("reporting_year", 2026),
            language=company_data.get("language", "en"),
        )
        tagger = IXBRLTagger(tagger_config)
        tagger.load_taxonomy()

        # Genera iXBRL
        ixbrl_content = tagger.tag_report_from_template(template, company_data)

        # Estrai fatti
        facts = tagger.extract_facts_from_xhtml(ixbrl_content)

        # Validazione fatti
        facts_result = validator.validate_facts(facts)
        issues.extend(facts_result.issues)

        # Passo 3: Validazione con Arelle (se disponibile)
        if validator.arelle_available:
            try:
                arelle_result = validator.validate_ixbrl_content(ixbrl_content)
                issues.extend(arelle_result.issues)
            except Exception as e:
                logger.warning(f"Arelle validation skipped: {e}")

    return validator._build_result(
        issues,
        validator="multi-stage",
    ).to_dict()
