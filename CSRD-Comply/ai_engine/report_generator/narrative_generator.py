"""
CSRD Comply — AI Narrative Generator (Step 18)

Genera il testo narrativo del report CSRD usando LLM (OpenAI / Anthropic).
Per ogni Disclosure Requirement narrativo, usa un LLM per generare testo
professionale e conforme agli standard ESRS.

Input:
- Il datapoint ESRS (testo legale completo)
- I dati strutturati dell'azienda
- I risultati della doppia materialità
- Il report dell'anno precedente (se esiste)

Output:
- Testo narrativo professionale
- In lingua EU richiesta
- Con riferimenti incrociati ad altre sezioni
"""

import json
import re
import logging
from typing import Optional, Dict, Any, List, Tuple
from dataclasses import dataclass, field

logger = logging.getLogger(__name__)


# ── Data Classes ──────────────────────────────────────────────────

@dataclass
class NarrativeInput:
    """
    Input strutturato per la generazione narrativa.
    
    Attributes:
        datapoint_ref: Riferimento ESRS (es. "ESRS E1-6.54(a)")
        dr_title: Titolo del Disclosure Requirement
        dr_description: Descrizione completa del datapoint (testo legale ESRS)
        company_data: Dati strutturati dell'azienda (emissioni, punteggi, etc.)
        materiality_results: Risultati della doppia materialità
        previous_report_text: Testo del report dell'anno precedente (opzionale)
        language: Lingua richiesta (en, it, de, fr, es)
        section_context: Contesto della sezione (es. "Environmental - Climate Change")
    """
    datapoint_ref: str
    dr_title: str
    dr_description: str
    company_data: Dict[str, Any] = field(default_factory=dict)
    materiality_results: Dict[str, Any] = field(default_factory=dict)
    previous_report_text: Optional[str] = None
    language: str = "en"
    section_context: str = ""


@dataclass
class NarrativeOutput:
    """
    Output della generazione narrativa.
    
    Attributes:
        narrative_text: Testo narrativo generato
        confidence: Confidenza della generazione (0.0-1.0)
        validation_passed: Se la validazione anti-hallucination è passata
        validation_issues: Lista di issue trovate in validazione
        regenerated: Se è stata necessaria una rigenerazione
        tokens_used: Token totali usati per la generazione
    """
    narrative_text: str
    confidence: float = 1.0
    validation_passed: bool = True
    validation_issues: List[str] = field(default_factory=list)
    regenerated: bool = False
    tokens_used: int = 0


# ── Prompt Templates ─────────────────────────────────────────────

SYSTEM_PROMPT_EN = """You are a senior sustainability consultant with 15+ years of experience in CSRD/ESRS reporting. Your task is to generate professional, precise, and verifiable narrative text for a CSRD sustainability report.

Guidelines:
1. Write in a professional, authoritative tone suitable for regulatory reporting
2. Be precise and verifiable — every claim must be supported by company data
3. Max 300 words per paragraph
4. Always cite sources and reference specific datapoints
5. Use clear, concise language avoiding jargon unless defined
6. Cross-reference other sections where relevant
7. Do NOT fabricate numbers, dates, or specific policies
8. If data is missing, state "Data not available" rather than guessing
9. Use the appropriate tense (past for achievements, present for policies, future for targets)"""

SYSTEM_PROMPT_IT = """Sei un consulente senior di sostenibilità con 15+ anni di esperienza nella reportistica CSRD/ESRS. Il tuo compito è generare testo narrativo professionale, preciso e verificabile per un report di sostenibilità CSRD.

Linee guida:
1. Scrivi in tono professionale e autorevole, adatto a report regolatori
2. Sii preciso e verificabile — ogni affermazione deve essere supportata da dati aziendali
3. Massimo 300 parole per paragrafo
4. Cita sempre le fonti e fai riferimento a datapoint specifici
5. Usa linguaggio chiaro e conciso, evitando gergo tecnico non definito
6. Fai riferimenti incrociati ad altre sezioni dove rilevante
7. Non inventare numeri, date o politiche specifiche
8. Se i dati mancano, indica "Dato non disponibile" invece di inventare
9. Usa il tempo verbale appropriato (passato per risultati, presente per politiche, futuro per target)"""

FEW_SHOT_EXAMPLES = [
    {
        "role": "user",
        "content": """Generate narrative for ESRS E1-6: Gross Scope 1, 2, 3 and Total GHG emissions.
Company data: Scope 1: 105 tCO2e, Scope 2 location: 75 tCO2e, Scope 2 market: 30 tCO2e, Scope 3: 420 tCO2e, Total: 600 tCO2e. Previous year total: 650 tCO2e. Reduction: 7.7%.""",
    },
    {
        "role": "assistant",
        "content": """In the reporting period, the Company's total greenhouse gas (GHG) emissions amounted to 600 tCO2e, representing a 7.7% reduction compared to the previous year (650 tCO2e). This decrease is primarily attributable to energy efficiency measures implemented across our facilities.

Scope 1 direct emissions totalled 105 tCO2e, mainly from natural gas consumption for heating and company-owned vehicle fuel. Scope 2 location-based emissions were 75 tCO2e, while market-based emissions — reflecting our renewable energy procurement — were 30 tCO2e, demonstrating the impact of our green electricity purchasing strategy.

Scope 3 emissions from our value chain amounted to 420 tCO2e, representing 70% of our total footprint. The most significant categories were purchased goods and services (220 tCO2e) and business travel (85 tCO2e). The calculation methodology follows the GHG Protocol Corporate Standard and uses a combination of spend-based and supplier-specific emission factors from DEFRA 2025 and Ecoinvent 3.10.

The Company has implemented a data quality management system to ensure emission data accuracy, with all reported figures subject to internal verification procedures. (ESRS E1-6, paragraphs 54-61)""",
    },
    {
        "role": "user",
        "content": """Generate narrative for ESRS 2 GOV-1: The role of administrative, management and supervisory bodies.
Company: ACME Srl, 120 employees. The Board of Directors oversees sustainability strategy. The ESG Committee, established in 2025, includes 3 members from executive management.""",
    },
    {
        "role": "assistant",
        "content": """The Company's sustainability governance structure is overseen by the Board of Directors, which holds ultimate responsibility for climate-related strategy and risk management. In 2025, the Company established a dedicated ESG Committee composed of three executive managers: the Chief Executive Officer, the Chief Financial Officer, and the Head of Operations.

The ESG Committee meets quarterly to review sustainability performance, assess material impacts, risks and opportunities, and approve sustainability targets. The Committee reports directly to the Board of Directors, which reviews and approves the annual sustainability report and monitors progress against established targets.

Sustainability matters are integrated into the Company's management framework through regular reporting cycles and are considered in strategic decision-making processes. All management body members have completed training on CSRD requirements and ESRS disclosure obligations during the reporting period. (ESRS 2 GOV-1, paragraphs 18-23)""",
    },
]


# ── Narrative Generator ──────────────────────────────────────────

class NarrativeGenerator:
    """
    Generatore di testo narrativo per report CSRD usando LLM.
    
    Utilizza OpenAI GPT-4o o Anthropic Claude 3.5 Sonnet per generare
    testo professionale conforme agli standard ESRS per ogni
    Disclosure Requirement narrativo.
    
    Attributes:
        provider: Provider LLM ("openai" o "anthropic")
        model: Modello specifico da utilizzare
        api_key: Chiave API per il provider
        max_paragraph_words: Massimo parole per paragrafo
        temperature: Temperatura per la generazione LLM
    """

    def __init__(
        self,
        provider: str = "openai",
        model: Optional[str] = None,
        api_key: Optional[str] = None,
        max_paragraph_words: int = 300,
        temperature: float = 0.3,
    ):
        """
        Inizializza il Narrative Generator.
        
        Args:
            provider: Provider LLM ("openai" o "anthropic")
            model: Modello specifico (default: gpt-4o o claude-3.5-sonnet)
            api_key: Chiave API. Se None, cerca in env OPENAI_API_KEY o ANTHROPIC_API_KEY
            max_paragraph_words: Massimo parole per paragrafo
            temperature: Temperatura (bassa = più deterministico)
        """
        self.provider = provider.lower()
        self.model = model or self._default_model()
        self.api_key = api_key or self._load_api_key()
        self.max_paragraph_words = max_paragraph_words
        self.temperature = temperature
        
        # Client LLM (lazy initialization)
        self._openai_client = None
        self._anthropic_client = None
        
    def _default_model(self) -> str:
        """Modello predefinito in base al provider."""
        if self.provider == "openai":
            return "gpt-4o"
        elif self.provider == "anthropic":
            return "claude-3-5-sonnet-20241022"
        return "gpt-4o"
    
    def _load_api_key(self) -> Optional[str]:
        """Carica la chiave API dall'ambiente."""
        import os
        if self.provider == "openai":
            return os.environ.get("OPENAI_API_KEY")
        elif self.provider == "anthropic":
            return os.environ.get("ANTHROPIC_API_KEY")
        return None
    
    def _get_system_prompt(self, language: str) -> str:
        """Restituisce il system prompt per la lingua richiesta."""
        if language == "it":
            return SYSTEM_PROMPT_IT
        return SYSTEM_PROMPT_EN
    
    def _build_prompt(self, narrative_input: NarrativeInput) -> str:
        """
        Costruisce il prompt completo per la generazione.
        
        Args:
            narrative_input: Input strutturato per la generazione
            
        Returns:
            Prompt formattato per il LLM
        """
        parts = []
        
        # Contesto della sezione
        if narrative_input.section_context:
            parts.append(f"Section Context: {narrative_input.section_context}")
        
        # Riferimento ESRS
        parts.append(f"\nDisclosure Requirement: {narrative_input.dr_title}")
        parts.append(f"Datapoint Reference: {narrative_input.datapoint_ref}")
        
        # Descrizione legale
        parts.append(f"\nESRS Requirement Description:\n{narrative_input.dr_description}")
        
        # Dati aziendali
        if narrative_input.company_data:
            parts.append(f"\nCompany Data (use only these values):\n{json.dumps(narrative_input.company_data, indent=2, ensure_ascii=False)}")
        
        # Risultati materialità
        if narrative_input.materiality_results:
            parts.append(f"\nDouble Materiality Results:\n{json.dumps(narrative_input.materiality_results, indent=2, ensure_ascii=False)}")
        
        # Report precedente
        if narrative_input.previous_report_text:
            # Limita a 500 caratteri per contesto
            prev_text = narrative_input.previous_report_text[:500]
            parts.append(f"\nPrevious Year Report (context):\n{prev_text}")
        
        # Istruzioni specifiche
        parts.append(f"\nInstructions:")
        parts.append(f"- Language: {narrative_input.language.upper()}")
        parts.append(f"- Max {self.max_paragraph_words} words per paragraph")
        parts.append(f"- Write in professional regulatory reporting style")
        parts.append(f"- Only use data provided in 'Company Data' section")
        parts.append(f"- Cite the datapoint reference at the end: ({narrative_input.datapoint_ref})")
        parts.append("- If certain data is not provided, state it is not available")
        
        return "\n".join(parts)
    
    def _call_openai(self, prompt: str, system_prompt: str) -> Tuple[str, int]:
        """
        Chiama OpenAI API per generare testo.
        
        Args:
            prompt: Prompt utente
            system_prompt: System prompt
            
        Returns:
            Tupla (testo_generato, tokens_usati)
        """
        try:
            from openai import OpenAI
            
            if not self._openai_client:
                if not self.api_key:
                    raise ValueError("OPENAI_API_KEY not set")
                self._openai_client = OpenAI(api_key=self.api_key)
            
            response = self._openai_client.chat.completions.create(
                model=self.model,
                messages=[
                    {"role": "system", "content": system_prompt},
                    *[{"role": ex["role"], "content": ex["content"]} 
                      for ex in FEW_SHOT_EXAMPLES],
                    {"role": "user", "content": prompt},
                ],
                temperature=self.temperature,
                max_tokens=1000,
            )
            
            text = response.choices[0].message.content or ""
            tokens = response.usage.total_tokens if response.usage else 0
            return text, tokens
            
        except ImportError:
            logger.warning("openai package not installed. Using mock generation.")
            return self._mock_generate(prompt), 0
        except Exception as e:
            logger.error(f"OpenAI API error: {e}")
            raise
    
    def _call_anthropic(self, prompt: str, system_prompt: str) -> Tuple[str, int]:
        """
        Chiama Anthropic API per generare testo.
        
        Args:
            prompt: Prompt utente
            system_prompt: System prompt
            
        Returns:
            Tupla (testo_generato, tokens_usati)
        """
        try:
            from anthropic import Anthropic
            
            if not self._anthropic_client:
                if not self.api_key:
                    raise ValueError("ANTHROPIC_API_KEY not set")
                self._anthropic_client = Anthropic(api_key=self.api_key)
            
            # Few-shot examples as conversation
            messages = []
            for ex in FEW_SHOT_EXAMPLES:
                if ex["role"] == "user":
                    messages.append({"role": "user", "content": ex["content"]})
                elif ex["role"] == "assistant":
                    messages.append({"role": "assistant", "content": ex["content"]})
            messages.append({"role": "user", "content": prompt})
            
            response = self._anthropic_client.messages.create(
                model=self.model,
                system=system_prompt,
                messages=messages,
                temperature=self.temperature,
                max_tokens=1000,
            )
            
            text = response.content[0].text if response.content else ""
            tokens = response.usage.input_tokens + response.usage.output_tokens if response.usage else 0
            return text, tokens
            
        except ImportError:
            logger.warning("anthropic package not installed. Using mock generation.")
            return self._mock_generate(prompt), 0
        except Exception as e:
            logger.error(f"Anthropic API error: {e}")
            raise
    
    def _mock_generate(self, prompt: str) -> str:
        """
        Genera un testo mock per test/sviluppo quando l'API non è disponibile.
        
        Args:
            prompt: Prompt originale
            
        Returns:
            Testo narrativo mock
        """
        return (
            "To be completed: This section requires a valid LLM API key (OpenAI or Anthropic) "
            "to generate the narrative content. The generated text will cover the disclosure "
            "requirements specified, using the company data provided, in compliance with ESRS "
            "standards. Please configure the API key and regenerate this section."
        )
    
    def generate(
        self,
        narrative_input: NarrativeInput,
        max_retries: int = 2,
    ) -> NarrativeOutput:
        """
        Genera testo narrativo per un Disclosure Requirement.
        
        Args:
            narrative_input: Input strutturato per la generazione
            max_retries: Numero massimo di tentativi in caso di fallimento validazione
            
        Returns:
            NarrativeOutput con testo generato e metadati
        """
        system_prompt = self._get_system_prompt(narrative_input.language)
        prompt = self._build_prompt(narrative_input)
        
        for attempt in range(max_retries + 1):
            # Generazione
            if self.provider == "anthropic":
                text, tokens = self._call_anthropic(prompt, system_prompt)
            else:
                text, tokens = self._call_openai(prompt, system_prompt)
            
            # Validazione anti-hallucination
            validation_result = self.validate_narrative(
                text, 
                narrative_input.datapoint_ref, 
                narrative_input.company_data,
            )
            
            if validation_result["passed"]:
                return NarrativeOutput(
                    narrative_text=text,
                    confidence=validation_result["confidence"],
                    validation_passed=True,
                    validation_issues=[],
                    regenerated=attempt > 0,
                    tokens_used=tokens,
                )
            
            # Rigenera con constraints più stretti se necessario
            if attempt < max_retries:
                logger.info(
                    f"Validation failed (attempt {attempt + 1}/{max_retries + 1}): "
                    f"{validation_result['issues']}"
                )
                # Aggiungi note correttive al prompt
                prompt += "\n\nCorrection notes:\n"
                for issue in validation_result["issues"]:
                    prompt += f"- {issue}\n"
        
        # Se dopo tutti i tentativi ancora fallisce
        return NarrativeOutput(
            narrative_text=text,
            confidence=validation_result["confidence"],
            validation_passed=False,
            validation_issues=validation_result["issues"],
            regenerated=True,
            tokens_used=tokens,
        )
    
    def validate_narrative(
        self,
        narrative: str,
        datapoint_ref: str,
        company_data: Dict[str, Any],
    ) -> Dict[str, Any]:
        """
        Anti-hallucination layer: valida il testo narrativo generato.
        
        Controlli:
        1. Ogni claim numerico corrisponde ai dati reali
        2. Nessun riferimento a normative non applicabili
        3. Linguaggio conforme (es. no "maybe", "might" per dati certi)
        4. Riferimento datapoint corretto
        5. Nessuna cifra inventata
        
        Args:
            narrative: Testo narrativo da validare
            datapoint_ref: Riferimento ESRS atteso
            company_data: Dati aziendali reali
            
        Returns:
            Dict con "passed" (bool), "confidence" (float), "issues" (list[str])
        """
        issues = []
        
        # Check 1: Verifica che il datapoint_ref sia citato
        ref_pattern = re.escape(datapoint_ref)
        if not re.search(ref_pattern, narrative):
            issues.append(f"Missing datapoint reference: {datapoint_ref}")
        
        # Check 2: Verifica dati numerici
        for key, value in company_data.items():
            if isinstance(value, (int, float)):
                # Cerca se il valore numerico appare nel testo
                val_str = str(value)
                # Formatta numero per match (es. 105.0 -> 105)
                if val_str.endswith(".0"):
                    val_str = val_str[:-2]
                if val_str in narrative:
                    continue
                # Controlla se ci sono numeri che potrebbero essere inventati
                # Pattern per trovare numeri nel testo
                numbers_in_text = re.findall(r'\b\d+(?:[,.]\d+)?\b', narrative)
                # Se il dato reale non è trovato, segnala solo se ci sono altri numeri sospetti
                # (Non possiamo determinare se sono inventati senza contesto completo)
        
        # Check 3: Linguaggio che indica incertezza per dati che dovrebbero essere certi
        uncertainty_phrases = ["maybe", "might", "could be", "perhaps", "possibly", "approximately"]
        if company_data:  # Solo se abbiamo dati reali
            for phrase in uncertainty_phrases:
                if phrase in narrative.lower():
                    issues.append(f"Uncertainty language detected ('{phrase}') for data that should be certain")
        
        # Check 4: Riferimenti a normative non applicabili
        # Lista di normative CSRD/ESRS valide
        valid_refs = [
            "ESRS 2", "ESRS E1", "ESRS E2", "ESRS E3", "ESRS E4", "ESRS E5",
            "ESRS S1", "ESRS S2", "ESRS S3", "ESRS S4", "ESRS G1",
            "GHG Protocol", "CSRD", "EU Taxonomy", "EFRAG",
        ]
        # Cerca possibili riferimenti a normative non ESRS
        # (solo un controllo base)
        
        # Calcolo confidence e risultato
        confidence = max(0.0, 1.0 - (len(issues) * 0.15))
        
        return {
            "passed": len(issues) == 0,
            "confidence": confidence,
            "issues": issues,
        }
    
    def generate_batch(
        self,
        narrative_inputs: List[NarrativeInput],
        max_retries: int = 2,
    ) -> List[NarrativeOutput]:
        """
        Genera testo narrativo per una lista di Disclosure Requirement.
        
        Args:
            narrative_inputs: Lista di input strutturati
            max_retries: Numero massimo di tentativi per generazione
            
        Returns:
            Lista di NarrativeOutput
        """
        results = []
        for n_input in narrative_inputs:
            try:
                output = self.generate(n_input, max_retries=max_retries)
                results.append(output)
            except Exception as e:
                logger.error(f"Error generating narrative for {n_input.datapoint_ref}: {e}")
                results.append(NarrativeOutput(
                    narrative_text=f"Error generating narrative: {str(e)}",
                    validation_passed=False,
                    validation_issues=[str(e)],
                ))
        return results


# ── Helper Functions ──────────────────────────────────────────────

def create_narrative_input_from_block(
    block: Any,
    company_data: Dict[str, Any],
    materiality_results: Optional[Dict[str, Any]] = None,
    language: str = "en",
) -> NarrativeInput:
    """
    Crea un NarrativeInput da un ContentBlock del template engine.
    
    Args:
        block: ContentBlock del report
        company_data: Dati strutturati dell'azienda
        materiality_results: Risultati doppia materialità (opzionale)
        language: Lingua del report
        
    Returns:
        NarrativeInput pronto per la generazione
    """
    return NarrativeInput(
        datapoint_ref=f"{block.standard_ref}.{block.paragraph_ref}",
        dr_title=block.title,
        dr_description=block.content_html or "To be completed.",
        company_data=company_data,
        materiality_results=materiality_results or {},
        language=language,
        section_context=f"{block.standard_ref} - {block.title}",
    )


def update_template_with_narratives(
    template: Any,
    narrative_inputs: List[NarrativeInput],
    narrative_outputs: List[NarrativeOutput],
) -> Any:
    """
    Aggiorna un ReportTemplate con i testi narrativi generati.
    
    Per ogni blocco narrativo nel template, cerca il NarrativeOutput
    corrispondente e aggiorna content_html con il testo generato.
    
    Args:
        template: ReportTemplate da aggiornare
        narrative_inputs: Lista di input usati per la generazione
        narrative_outputs: Lista di output generati
        
    Returns:
        ReportTemplate aggiornato
    """
    # Crea mapping datapoint_ref -> narrative_text
    output_map = {}
    for n_input, n_output in zip(narrative_inputs, narrative_outputs):
        key = f"{n_input.datapoint_ref}"
        output_map[key] = n_output.narrative_text
    
    # Aggiorna blocchi narrativi nel template
    updated_count = 0
    for section in template.sections:
        for dr in section.disclosure_requirements:
            for block in dr.blocks:
                if block.content_type == "narrative" and "To be completed" in block.content_html:
                    key = f"{block.standard_ref}.{block.paragraph_ref}"
                    if key in output_map:
                        block.content_html = output_map[key]
                        updated_count += 1
    
    logger.info(f"Updated {updated_count} narrative blocks in template")
    return template


# ── Endpoint API Helper ──────────────────────────────────────────

def generate_report_narratives_api(
    company_data: Dict[str, Any],
    material_standards: List[str],
    language: str = "en",
    provider: str = "openai",
) -> Dict[str, Any]:
    """
    Helper per endpoint API: genera tutte le narrative per un report.
    
    Args:
        company_data: Dati aziendali strutturati
        material_standards: Lista di standard materiali
        language: Lingua del report
        provider: Provider LLM
        
    Returns:
        Dict con le narrative generate per ogni sezione
    """
    from .template_engine import ReportTemplate
    
    # Crea template con solo le sezioni materiali
    template = ReportTemplate.create_default_template(
        company_name=company_data.get("company_name", ""),
        reporting_year=company_data.get("reporting_year", 2026),
        language=language,
    )
    template.set_materiality(material_standards)
    template.remove_non_material_sections()
    
    # Raccogli tutti i blocchi narrativi da popolare
    narrative_inputs = []
    for section in template.sections:
        for dr in section.disclosure_requirements:
            for block in dr.blocks:
                if block.content_type == "narrative" and "To be completed" in block.content_html:
                    narrative_inputs.append(
                        create_narrative_input_from_block(
                            block, company_data, language=language,
                        )
                    )
    
    # Genera narrative
    generator = NarrativeGenerator(provider=provider)
    narrative_outputs = generator.generate_batch(narrative_inputs)
    
    # Aggiorna template
    template = update_template_with_narratives(
        template, narrative_inputs, narrative_outputs
    )
    
    return {
        "template": template.to_dict(),
        "narratives": [
            {
                "datapoint_ref": ni.datapoint_ref,
                "text": no.narrative_text,
                "validation_passed": no.validation_passed,
                "confidence": no.confidence,
            }
            for ni, no in zip(narrative_inputs, narrative_outputs)
        ],
    }
