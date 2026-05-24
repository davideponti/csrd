"""
CSRD Comply — AI Summarizer per Update Normativi (Step 24)

Riassume cambiamenti normativi CSRD/ESRS in linguaggio comprensibile per PMI.

Per ogni regulatory update rilevato:
1. Scarica il testo completo (PDF o HTML)
2. Estrai le modifiche rispetto alla versione precedente
3. Classifica l'impatto:
   - CRITICAL: cambia requisiti di reporting obbligatori
   - MODERATE: nuove linee guida, nessun nuovo obbligo
   - INFO: chiarimenti, FAQ, esempi
4. Usa LLM per generare:
   - Summary: 2-3 frasi per il CEO
   - Detail: parametri tecnici per il compliance officer
   - Action items: cosa deve fare l'azienda
5. Invia notifica push via email/app alle aziende interessate
"""
import json
import logging
import re
from datetime import datetime, timezone
from dataclasses import dataclass, field, asdict
from typing import Optional, List, Dict, Any
from enum import Enum

logger = logging.getLogger(__name__)


# ── Enums & Data Classes ───────────────────────────────────────────

class ImpactClassification(str, Enum):
    """Classificazione dell'impatto di un aggiornamento normativo."""
    CRITICAL = "critical"       # Cambia requisiti obbligatori di reporting
    MODERATE = "moderate"       # Nuove linee guida, nessun nuovo obbligo
    INFO = "info"               # Chiarimenti, FAQ, esempi pratici


class AffectedEntityType(str, Enum):
    """Tipologia di entità impattata dall'aggiornamento."""
    ALL_COMPANIES = "all_companies"
    SECTOR_SPECIFIC = "sector_specific"
    SIZE_SPECIFIC = "size_specific"
    COUNTRY_SPECIFIC = "country_specific"
    WAVE_SPECIFIC = "wave_specific"  # Basato su CSRD wave (1=2025, 2=2026, 3=2027)


@dataclass
class RegulatoryChange:
    """
    Una singola modifica normativa identificata.
    
    Attributes:
        description: Descrizione della modifica
        old_requirement: Requisito precedente (se applicabile)
        new_requirement: Nuovo requisito
        reference: Riferimento normativo (articolo, paragrafo)
        effective_date: Data di entrata in vigore
        transition_period: Periodo transitorio (es. "6 mesi")
    """
    description: str
    old_requirement: Optional[str] = None
    new_requirement: Optional[str] = None
    reference: Optional[str] = None
    effective_date: Optional[str] = None
    transition_period: Optional[str] = None


@dataclass
class AnalyzedUpdate:
    """
    Risultato dell'analisi di un aggiornamento normativo.
    
    Attributes:
        source_title: Titolo originale del documento
        source_url: URL del documento originale
        regulation: Regolamento di riferimento (CSRD, ESRS, etc.)
        impact: Classificazione dell'impatto
        summary_ceo: Riassunto 2-3 frasi per il CEO (linguaggio semplice)
        detail_compliance: Parametri tecnici per il compliance officer
        action_items: Lista di azioni che l'azienda deve intraprendere
        changes: Lista di modifiche specifiche identificate
        affected_standards: Lista di standard ESRS impattati
        affected_entities: Tipologia di entità impattate
        effective_date: Data di efficacia
        deadline: Scadenza per adeguamento
        recommendations: Raccomandazioni specifiche
        language: Lingua del riassunto
        analyzed_at: Timestamp dell'analisi
        confidence: Confidenza dell'analisi (0.0-1.0)
    """
    source_title: str
    source_url: str
    regulation: str
    impact: ImpactClassification
    summary_ceo: str = ""
    detail_compliance: str = ""
    action_items: List[str] = field(default_factory=list)
    changes: List[RegulatoryChange] = field(default_factory=list)
    affected_standards: List[str] = field(default_factory=list)
    affected_entities: AffectedEntityType = AffectedEntityType.ALL_COMPANIES
    effective_date: Optional[str] = None
    deadline: Optional[str] = None
    recommendations: List[str] = field(default_factory=list)
    language: str = "it"
    analyzed_at: str = field(default_factory=lambda: datetime.now(timezone.utc).isoformat())
    confidence: float = 0.0


@dataclass
class CompanyNotification:
    """
    Notifica da inviare a una specifica azienda.
    
    Attributes:
        company_id: ID dell'azienda
        company_name: Nome dell'azienda
        company_email: Email di contatto
        update: Analisi dell'aggiornamento
        relevance_score: Punteggio di rilevanza (0.0-1.0)
        is_notified: Se la notifica è già stata inviata
        notified_at: Data di invio notifica
        read_at: Data di lettura da parte dell'utente
    """
    company_id: str
    company_name: str
    company_email: str
    update: AnalyzedUpdate
    relevance_score: float = 0.0
    is_notified: bool = False
    notified_at: Optional[datetime] = None
    read_at: Optional[datetime] = None


# ── Content Downloader ─────────────────────────────────────────────

class ContentDownloader:
    """
    Scarica il contenuto completo di documenti normativi.
    
    Supporta:
    - Download diretto di pagine HTML
    - Download di PDF (estrazione testo)
    - Fallback su testo estratto dallo scraper
    """
    
    @staticmethod
    async def download(url: str) -> Optional[str]:
        """
        Scarica il contenuto di un documento normativo.
        
        Args:
            url: URL del documento
            
        Returns:
            Contenuto testuale del documento, o None se errore
        """
        try:
            import httpx
            
            is_pdf = url.lower().endswith('.pdf') or 'pdf' in url.lower()
            
            async with httpx.AsyncClient(
                timeout=60.0,
                follow_redirects=True,
                headers={
                    "User-Agent": (
                        "CSRD-Comply/1.0 Regulatory Analyzer; "
                        "+https://csrdcomply.com"
                    ),
                },
            ) as client:
                response = await client.get(url)
                response.raise_for_status()
                
                if is_pdf:
                    return ContentDownloader._extract_pdf_text(response.content)
                else:
                    return ContentDownloader._extract_html_text(response.text)
                    
        except httpx.TimeoutException:
            logger.warning(f"Timeout downloading {url}")
            return None
        except httpx.HTTPStatusError as e:
            logger.warning(f"HTTP {e.response.status_code} downloading {url}")
            return None
        except Exception as e:
            logger.error(f"Error downloading {url}: {str(e)}")
            return None
    
    @staticmethod
    def _extract_html_text(html: str) -> str:
        """
        Estrae testo da HTML.
        
        Args:
            html: Contenuto HTML
            
        Returns:
            Testo estratto
        """
        try:
            from bs4 import BeautifulSoup
            soup = BeautifulSoup(html, "html.parser")
            
            # Rimuovi script e style
            for tag in soup(["script", "style", "nav", "footer", "header"]):
                tag.decompose()
            
            text = soup.get_text(separator="\n", strip=True)
            return text
        except ImportError:
            # Fallback regex
            text = re.sub(r'<[^>]+>', ' ', html)
            text = re.sub(r'\s+', ' ', text).strip()
            return text
        except Exception as e:
            logger.error(f"HTML extraction error: {str(e)}")
            return ""
    
    @staticmethod
    def _extract_pdf_text(content: bytes) -> str:
        """
        Estrae testo da un PDF.
        
        Args:
            content: Contenuto binario del PDF
            
        Returns:
            Testo estratto
        """
        try:
            import io
            import PyPDF2
            
            pdf_file = io.BytesIO(content)
            reader = PyPDF2.PdfReader(pdf_file)
            
            text_parts = []
            for page in reader.pages:
                text = page.extract_text()
                if text:
                    text_parts.append(text)
            
            return "\n".join(text_parts)
            
        except ImportError:
            logger.warning("PyPDF2 not installed, cannot extract PDF text")
            return "[PDF content - require PyPDF2 for extraction]"
        except Exception as e:
            logger.error(f"PDF extraction error: {str(e)}")
            return "[PDF extraction failed]"


# ── AI Summarizer ──────────────────────────────────────────────────

class UpdateAnalyzer:
    """
    Analizza aggiornamenti normativi usando LLM.
    
    Per ogni documento normativo:
    1. Scarica il testo completo
    2. Classifica l'impatto
    3. Genera summary, detail e action items
    4. Identifica aziende impattate
    
    Usage:
        analyzer = UpdateAnalyzer(api_key="...")
        analysis = analyzer.analyze(scraped_document)
        print(analysis.summary_ceo)
    """
    
    # Prompt di sistema per il LLM
    SYSTEM_PROMPT = """Sei un esperto di conformità CSRD/ESRS con 15 anni di esperienza.
Il tuo compito è analizzare documenti normativi EU e produrre riassunti 
comprensibili per PMI (Piccole e Medie Imprese) europee.

REGOLE FONDAMENTALI:
1. Usa linguaggio semplice e chiaro, evita il "legalese" EU
2. Distingui sempre tra cambiamenti OBBLIGATORI e linee guida OPZIONALI
3. Per ogni cambiamento, specifica la scadenza applicativa
4. Indica chiaramente se l'aggiornamento si applica a tutte le aziende
   o solo a settori/dimensioni specifiche
5. Se l'aggiornamento introduce nuovi datapoint, elencali
6. Fornisci action items concreti e prioritizzati

OUTPUT DEVI ESSERE IN FORMATO JSON STRUTTURATO."""
    
    # Prompt per la generazione del riassunto
    SUMMARIZE_PROMPT = """Analizza il seguente documento normativo CSRD/ESRS.

Documento: {title}
Fonte: {source}
URL: {url}
Contenuto: {content}

Genera un'analisi strutturata con:
1. Classificazione impatto (critical/moderate/info)
2. Summary per il CEO (2-3 frasi, linguaggio semplice)
3. Dettaglio tecnico per compliance officer
4. Action items per l'azienda (lista prioritaria)
5. Modifiche specifiche identificate
6. Scadenze e date di efficacia
7. Raccomandazioni specifiche per PMI
8. Confidenza dell'analisi (0.0-1.0)

Output in formato JSON con i seguenti campi:
- impact: string (critical/moderate/info)
- summary_ceo: string
- detail_compliance: string
- action_items: list[string]
- changes: list[{"description": string, "old_requirement": string|null, "new_requirement": string|null, "reference": string|null, "effective_date": string|null}]
- affected_standards: list[string]
- effective_date: string|null
- deadline: string|null
- recommendations: list[string]
- confidence: float
- language: string (it)"""

    def __init__(
        self,
        api_key: Optional[str] = None,
        provider: str = "openai",
        model: str = "gpt-4o",
    ):
        """
        Args:
            api_key: API key per LLM (default: da env)
            provider: Provider LLM ("openai" o "anthropic")
            model: Modello LLM da usare
        """
        self.api_key = api_key
        self.provider = provider
        self.model = model
        self._openai_client = None
        self._anthropic_client = None
    
    def _get_openai_client(self):
        """Inizializza client OpenAI."""
        if self._openai_client is None:
            try:
                from openai import OpenAI
                self._openai_client = OpenAI(api_key=self.api_key)
            except ImportError:
                logger.warning("OpenAI package not available")
                return None
        return self._openai_client
    
    def _get_anthropic_client(self):
        """Inizializza client Anthropic."""
        if self._anthropic_client is None:
            try:
                from anthropic import Anthropic
                self._anthropic_client = Anthropic(api_key=self.api_key)
            except ImportError:
                logger.warning("Anthropic package not available")
                return None
        return self._anthropic_client
    
    def _call_llm(self, prompt: str, system_prompt: Optional[str] = None) -> Optional[str]:
        """
        Chiama il LLM per generare testo.
        
        Args:
            prompt: Prompt per il LLM
            system_prompt: Prompt di sistema (opzionale)
            
        Returns:
            Risposta testuale del LLM, o None se errore
        """
        if self.provider == "anthropic":
            return self._call_anthropic(prompt, system_prompt)
        else:
            return self._call_openai(prompt, system_prompt)
    
    def _call_openai(self, prompt: str, system_prompt: Optional[str] = None) -> Optional[str]:
        """Chiama OpenAI GPT."""
        client = self._get_openai_client()
        if not client:
            return self._fallback_analysis(prompt)
        
        try:
            messages = []
            if system_prompt:
                messages.append({"role": "system", "content": system_prompt})
            messages.append({"role": "user", "content": prompt})
            
            response = client.chat.completions.create(
                model=self.model,
                messages=messages,
                temperature=0.2,  # Bassa temperatura per consistenza
                max_tokens=2000,
            )
            return response.choices[0].message.content
            
        except Exception as e:
            logger.error(f"OpenAI call error: {str(e)}")
            return self._fallback_analysis(prompt)
    
    def _call_anthropic(self, prompt: str, system_prompt: Optional[str] = None) -> Optional[str]:
        """Chiama Anthropic Claude."""
        client = self._get_anthropic_client()
        if not client:
            return self._fallback_analysis(prompt)
        
        try:
            kwargs = {
                "model": self.model,
                "max_tokens": 2000,
                "temperature": 0.2,
                "messages": [{"role": "user", "content": prompt}],
            }
            if system_prompt:
                kwargs["system"] = system_prompt
            
            response = client.messages.create(**kwargs)
            return response.content[0].text
            
        except Exception as e:
            logger.error(f"Anthropic call error: {str(e)}")
            return self._fallback_analysis(prompt)
    
    def _fallback_analysis(self, prompt: str) -> str:
        """
        Analisi fallback basata su regole quando LLM non è disponibile.
        
        Args:
            prompt: Prompt originale
            
        Returns:
            Analisi strutturata in formato JSON
        """
        logger.info("Using rule-based fallback analysis")
        
        # Estrai informazioni di base dal prompt
        lines = prompt.split('\n')
        title = ""
        source = ""
        content = ""
        
        for i, line in enumerate(lines):
            if line.startswith("Documento:"):
                title = line.replace("Documento:", "").strip()
            elif line.startswith("Fonte:"):
                source = line.replace("Fonte:", "").strip()
            elif line.startswith("Contenuto:"):
                content = "\n".join(lines[i+1:])
        
        # Classificazione basata su keyword
        content_lower = content.lower() if content else ""
        
        critical_keywords = [
            "mandatory", "shall", "must", "required", "obbligatorio",
            "new disclosure", "new requirement", "entry into force",
            "effective date", "compliance date",
        ]
        moderate_keywords = [
            "guidance", "guideline", "recommendation", "suggested",
            "implementation", "faq", "clarification",
        ]
        
        critical_count = sum(
            1 for kw in critical_keywords if kw in content_lower
        )
        moderate_count = sum(
            1 for kw in moderate_keywords if kw in content_lower
        )
        
        if critical_count >= 2:
            impact = "critical"
            confidence = min(0.5 + critical_count * 0.1, 0.8)
        elif moderate_count >= 2 or critical_count >= 1:
            impact = "moderate"
            confidence = 0.5
        else:
            impact = "info"
            confidence = 0.4
        
        # Estrai standard menzionati
        standards = re.findall(
            r'ESRS\s+[EsegrEGS][1-9](?:[0-9])?',
            content, re.IGNORECASE
        )
        affected_standards = list(set(
            s.strip().upper().replace(' ', ' ') for s in standards
        ))
        
        # Genera action items basati sull'impatto
        action_items = []
        if impact == "critical":
            action_items.extend([
                "Revisionare i processi di raccolta dati per allinearsi ai nuovi requisiti",
                "Aggiornare il calendario di reporting con le nuove scadenze",
                "Formare il personale sulle nuove disposizioni obbligatorie",
                "Verificare l'impatto sui datapoint ESRS già raccolti",
            ])
        elif impact == "moderate":
            action_items.extend([
                "Prendere visione delle nuove linee guida",
                "Valutare se implementare volontariamente le raccomandazioni",
                "Aggiornare la documentazione interna se rilevante",
            ])
        else:
            action_items.extend([
                "Prendere nota dell'aggiornamento informativo",
                "Archiviare per consultazione futura",
            ])
        
        # Costruisci JSON di fallback
        analysis = {
            "impact": impact,
            "summary_ceo": (
                f"È stato pubblicato un aggiornamento normativo: '{title}'. "
                f"L'impatto è classificato come {impact.upper()}. "
                f"{'Sono richieste azioni per adeguarsi ai nuovi requisiti obbligatori.' if impact == 'critical' else 'Si raccomanda di prendere visione del documento.' if impact == 'moderate' else 'Documento informativo senza impatto diretto sugli obblighi.'}"
            ),
            "detail_compliance": (
                f"Documento: {title}\n"
                f"Fonte: {source}\n"
                f"Classificazione impatto: {impact}\n"
                f"Standard coinvolti: {', '.join(affected_standards) if affected_standards else 'Generale'}\n\n"
                f"Analisi generata automaticamente (LLM non disponibile). "
                f"Si raccomanda di verificare il documento originale per dettagli."
            ),
            "action_items": action_items,
            "changes": [],
            "affected_standards": affected_standards,
            "effective_date": None,
            "deadline": None,
            "recommendations": [
                "Consultare il documento originale per i dettagli completi",
                "Verificare l'applicabilità al proprio settore e dimensione aziendale",
                "Aggiornare il piano di compliance CSRD se necessario",
            ],
            "confidence": round(confidence, 2),
            "language": "it",
        }
        
        return json.dumps(analysis, ensure_ascii=False, indent=2)
    
    def _parse_update_from_text(self, title: str, source: str, url: str, text: str) -> AnalyzedUpdate:
        """
        Analizza il testo di un documento normativo usando il LLM.
        
        Args:
            title: Titolo del documento
            source: Nome della fonte
            url: URL del documento
            text: Contenuto testuale
            
        Returns:
            AnalyzedUpdate strutturato
        """
        # Prepara prompt
        content_preview = text[:8000] if text else "[Contenuto non disponibile]"
        
        prompt = self.SUMMARIZE_PROMPT.format(
            title=title,
            source=source,
            url=url,
            content=content_preview,
        )
        
        # Chiama LLM
        response = self._call_llm(prompt, self.SYSTEM_PROMPT)
        
        if not response:
            return self._create_minimal_update(title, source, url, text)
        
        # Parsing JSON dalla risposta
        try:
            # Trova JSON nella risposta
            json_match = re.search(r'\{.*\}', response, re.DOTALL)
            if json_match:
                data = json.loads(json_match.group())
            else:
                data = json.loads(response)
            
            # Costruisci AnalyzedUpdate
            changes = []
            for change_data in data.get("changes", []):
                changes.append(RegulatoryChange(
                    description=change_data.get("description", ""),
                    old_requirement=change_data.get("old_requirement"),
                    new_requirement=change_data.get("new_requirement"),
                    reference=change_data.get("reference"),
                    effective_date=change_data.get("effective_date"),
                    transition_period=change_data.get("transition_period"),
                ))
            
            impact_str = data.get("impact", "info").lower()
            try:
                impact = ImpactClassification(impact_str)
            except ValueError:
                # Mappa da stringhe simili
                if "critical" in impact_str:
                    impact = ImpactClassification.CRITICAL
                elif "moderate" in impact_str:
                    impact = ImpactClassification.MODERATE
                else:
                    impact = ImpactClassification.INFO
            
            # Classifica entità impattate
            affected = AffectedEntityType.ALL_COMPANIES
            standards_text = " ".join(data.get("affected_standards", []))
            if any(sector in standards_text.lower() for sector in 
                   ["sector", "nace", "industry", "settore"]):
                affected = AffectedEntityType.SECTOR_SPECIFIC
            elif any(size in standards_text.lower() for size in
                     ["pmi", "sme", "small", "medium", "size", "dimensione"]):
                affected = AffectedEntityType.SIZE_SPECIFIC
            
            return AnalyzedUpdate(
                source_title=title,
                source_url=url,
                regulation=self._detect_regulation(title, text),
                impact=impact,
                summary_ceo=data.get("summary_ceo", "Nessun riassunto disponibile."),
                detail_compliance=data.get("detail_compliance", ""),
                action_items=data.get("action_items", []),
                changes=changes,
                affected_standards=data.get("affected_standards", []),
                affected_entities=affected,
                effective_date=data.get("effective_date"),
                deadline=data.get("deadline"),
                recommendations=data.get("recommendations", []),
                language=data.get("language", "it"),
                confidence=float(data.get("confidence", 0.5)),
            )
            
        except (json.JSONDecodeError, KeyError, ValueError) as e:
            logger.error(f"Failed to parse LLM response: {e}")
            return self._create_minimal_update(title, source, url, text)
    
    def _detect_regulation(self, title: str, text: str) -> str:
        """
        Identifica il regolamento di riferimento.
        
        Args:
            title: Titolo del documento
            text: Contenuto testuale
            
        Returns:
            Nome del regolamento
        """
        combined = f"{title} {text}".lower()
        
        regulation_keywords = {
            "CSRD": [
                "csrd", "corporate sustainability reporting directive",
                "2022/2464", "sustainability reporting directive",
            ],
            "ESRS": [
                "esrs", "european sustainability reporting standard",
                "sustainability reporting standard", "set 1", "set1",
            ],
            "EU Taxonomy": [
                "eu taxonomy", "taxonomy regulation", "2020/852",
                "sustainable finance taxonomy", "tassonomia",
            ],
            "SFDR": [
                "sfdr", "sustainable finance disclosure", "2019/2088",
            ],
            "CBAM": [
                "cbam", "carbon border adjustment mechanism",
            ],
            "CSDDD": [
                "csddd", "corporate sustainability due diligence",
                "due diligence directive",
            ],
            "Omnibus": [
                "omnibus", "simplification package",
            ],
            "ESEF": [
                "esef", "european single electronic format",
            ],
        }
        
        for regulation, keywords in regulation_keywords.items():
            if any(kw in combined for kw in keywords):
                return regulation
        
        return "General"
    
    def _create_minimal_update(
        self,
        title: str,
        source: str,
        url: str,
        text: Optional[str] = None,
    ) -> AnalyzedUpdate:
        """
        Crea un AnalyzedUpdate minimale quando l'analisi completa fallisce.
        
        Args:
            title: Titolo del documento
            source: Fonte
            url: URL
            text: Testo disponibile
            
        Returns:
            AnalyzedUpdate base
        """
        regulation = self._detect_regulation(title, text or "")
        
        return AnalyzedUpdate(
            source_title=title,
            source_url=url,
            regulation=regulation,
            impact=ImpactClassification.INFO,
            summary_ceo=f"Nuovo aggiornamento normativo: '{title}' da {source}. "
                         f"Si consiglia di consultare il documento originale.",
            detail_compliance=f"Fonte: {source}\nDocumento: {title}\nURL: {url}\n"
                              f"Regolamento: {regulation}\n"
                              f"Analisi automatica non disponibile - consultare il documento originale.",
            action_items=[
                "Consultare il documento originale per i dettagli",
                "Valutare l'impatto sul proprio reporting CSRD",
            ],
            affected_standards=self._extract_standards_fallback(text or ""),
            recommendations=[
                "Leggere il documento originale per i dettagli",
                "Contattare il supporto per assistenza nell'interpretazione",
            ],
            confidence=0.2,
        )
    
    def _extract_standards_fallback(self, text: str) -> List[str]:
        """
        Estrae standard ESRS dal testo (fallback).
        
        Args:
            text: Testo del documento
            
        Returns:
            Lista di standard ESRS
        """
        pattern = r'ESRS\s+[EsegrEGS][1-9](?:[0-9])?'
        matches = re.findall(pattern, text, re.IGNORECASE)
        return sorted(set(m.strip().upper() for m in matches))
    
    def analyze(
        self,
        title: str,
        source: str,
        url: str,
        content: Optional[str] = None,
        download_full: bool = True,
    ) -> AnalyzedUpdate:
        """
        Analizza un aggiornamento normativo completo.
        
        Args:
            title: Titolo del documento
            source: Nome della fonte
            url: URL del documento
            content: Contenuto già disponibile (opzionale)
            download_full: Se scaricare il contenuto completo
            
        Returns:
            AnalyzedUpdate completo
        """
        # Se richiesto, scarica il contenuto completo
        if download_full and not content:
            import asyncio
            try:
                content = asyncio.run(ContentDownloader.download(url))
            except Exception as e:
                logger.warning(f"Failed to download {url}: {e}")
        
        text = content or ""
        
        # Analisi completa
        analysis = self._parse_update_from_text(title, source, url, text)
        
        # Se il testo era molto lungo, arricchisci l'analisi
        if text and len(text) > 500:
            analysis.detail_compliance = self._enrich_detail(analysis, text)
        
        return analysis
    
    def _enrich_detail(self, analysis: AnalyzedUpdate, full_text: str) -> str:
        """
        Arricchisce il dettaglio tecnico con informazioni estratte dal testo completo.
        
        Args:
            analysis: AnalyzedUpdate corrente
            full_text: Testo completo del documento
            
        Returns:
            Dettaglio tecnico arricchito
        """
        # Estrai riferimenti normativi
        article_refs = re.findall(
            r'(?:Article|Art\.|Articolo)\s+\d+[a-z]?(?:\([^)]+\))?',
            full_text, re.IGNORECASE
        )
        
        # Estrai date
        dates = re.findall(
            r'\d{1,2}\s+(?:January|February|March|April|May|June|July|August|September|October|November|December|'
            r'gennaio|febbraio|marzo|aprile|maggio|giugno|luglio|agosto|settembre|ottobre|novembre|dicembre)\s+\d{4}'
            r'|\d{4}-\d{2}-\d{2}',
            full_text
        )
        
        detail_parts = [analysis.detail_compliance]
        
        if article_refs:
            detail_parts.append(f"\n\nRiferimenti normativi: {', '.join(article_refs[:10])}")
        
        if dates:
            detail_parts.append(f"\nDate rilevanti: {', '.join(dates[:5])}")
        
        if analysis.affected_standards:
            detail_parts.append(
                f"\nStandard ESRS coinvolti: {', '.join(analysis.affected_standards)}"
            )
        
        return "\n".join(detail_parts)
    
    def calculate_relevance(
        self,
        analysis: AnalyzedUpdate,
        company_sector: str,
        company_size: int,
        company_country: str,
        csrd_wave: int,
    ) -> float:
        """
        Calcola la rilevanza di un aggiornamento per una specifica azienda.
        
        Args:
            analysis: AnalyzedUpdate da valutare
            company_sector: Settore NACE dell'azienda
            company_size: Numero dipendenti dell'azienda
            company_country: Paese dell'azienda
            csrd_wave: Wave CSRD dell'azienda (1, 2, 3)
            
        Returns:
            Punteggio di rilevanza (0.0-1.0)
        """
        relevance = 0.5  # Rilevanza base
        
        # Impatto: critical aumenta rilevanza
        if analysis.impact == ImpactClassification.CRITICAL:
            relevance += 0.3
        elif analysis.impact == ImpactClassification.MODERATE:
            relevance += 0.1
        
        # Entità impattate
        if analysis.affected_entities == AffectedEntityType.ALL_COMPANIES:
            relevance += 0.2
        elif analysis.affected_entities == AffectedEntityType.WAVE_SPECIFIC:
            # Se menziona una wave, verifica se corrisponde
            if str(csrd_wave) in str(analysis.effective_date or ""):
                relevance += 0.15
        
        # Standard specifici: se gli standard coprono il settore
        if analysis.affected_standards:
            # Maggiori standard = maggiore rilevanza potenziale
            relevance += min(len(analysis.affected_standards) * 0.02, 0.1)
        
        # Confidenza dell'analisi
        relevance *= analysis.confidence
        
        return min(max(relevance, 0.0), 1.0)
    
    def analyze_impact(self, update: dict, company: dict) -> dict:
        """Analyze the impact of a regulatory update on a company (test compatibility)."""
        impact_score = 0.0
        reasons = []

        regulation = update.get("regulation", "")
        affected = update.get("affected_standards", [])
        summary = update.get("summary", "")
        company_sector = company.get("sector", "")
        company_size = company.get("employee_count", 0)

        # Check sector match
        if summary and company_sector:
            if company_sector in summary or any(
                word in summary.lower() for word in ["all", "general", "cross-sector"]
            ):
                impact_score += 3.0
                reasons.append("Regulation applies to your sector")

        # Check size relevance
        if company_size > 0 and "employee" in summary.lower():
            import re
            matches = re.findall(r'\d+', summary)
            if matches:
                threshold = int(matches[0])
                if company_size >= threshold:
                    impact_score += 2.0
                    reasons.append(f"Your company meets the employee threshold ({company_size} >= {threshold})")

        # Standard-specific relevance
        if affected:
            impact_score += len(affected)
            reasons.append(f"Affects {len(affected)} standard(s): {', '.join(affected)}")

        result = {
            "impact_score": min(round(impact_score, 1), 10.0),
            "assessment": "high" if impact_score >= 5 else ("medium" if impact_score >= 2 else "low"),
            "impact_level": "high" if impact_score >= 5 else ("medium" if impact_score >= 2 else ("low" if impact_score > 0 else "none")),
            "reasons": reasons,
            "requires_action": impact_score >= 3,
            "regulation": regulation,
            "affected_standards": affected,
        }
        return result

    def compare_updates(self, old: dict, new: dict) -> dict:
        """Compare two regulatory updates and return diff (test compatibility)."""
        differences = []

        for key in set(list(old.keys()) + list(new.keys())):
            old_val = old.get(key)
            new_val = new.get(key)
            if old_val != new_val:
                differences.append({
                    "field": key,
                    "old": old_val,
                    "new": new_val,
                    "changed": True,
                })

        return {
            "has_differences": len(differences) > 0,
            "difference_count": len(differences),
            "differences": differences,
        }

    def prepare_notification(
        self,
        analysis: AnalyzedUpdate,
        company_id: str,
        company_name: str,
        company_email: str,
        relevance_score: float,
    ) -> CompanyNotification:
        """
        Prepara una notifica per un'azienda specifica.
        
        Args:
            analysis: AnalyzedUpdate
            company_id: ID dell'azienda
            company_name: Nome dell'azienda
            company_email: Email dell'azienda
            relevance_score: Punteggio di rilevanza
            
        Returns:
            CompanyNotification pronta per l'invio
        """
        return CompanyNotification(
            company_id=company_id,
            company_name=company_name,
            company_email=company_email,
            update=analysis,
            relevance_score=relevance_score,
        )
    
    def format_notification_message(self, notification: CompanyNotification) -> dict:
        """
        Formatta una notifica per invio (email, app, etc.).
        
        Args:
            notification: CompanyNotification
            
        Returns:
            Dizionario con soggetto, corpo testo, corpo HTML
        """
        analysis = notification.update
        impact_icon = {
            ImpactClassification.CRITICAL: "🔴",
            ImpactClassification.MODERATE: "🟡",
            ImpactClassification.INFO: "🟢",
        }.get(analysis.impact, "ℹ️")
        
        subject = (
            f"[CSRD Comply] {impact_icon} Aggiornamento normativo: "
            f"{analysis.regulation} - {analysis.source_title[:80]}"
        )
        
        body_text = (
            f"CSRD Comply - Notifica Normativa\n"
            f"{'='*50}\n\n"
            f"{impact_icon} {analysis.regulation}: {analysis.source_title}\n\n"
            f"Per il CEO:\n{analysis.summary_ceo}\n\n"
            f"Per il Compliance Officer:\n{analysis.detail_compliance[:500]}...\n\n"
            f"Azioni richieste:\n"
        )
        for i, action in enumerate(analysis.action_items, 1):
            body_text += f"{i}. {action}\n"
        
        body_text += (
            f"\nRilevanza per {notification.company_name}: "
            f"{notification.relevance_score:.0%}\n"
            f"\nDocumento originale: {analysis.source_url}\n"
            f"\n---\nCSRD Comply - Il tuo advisor di conformità CSRD"
        )
        
        # Costruisci HTML per email
        html_parts = [
            f"<h2>{impact_icon} {analysis.regulation}: {analysis.source_title}</h2>",
            "<hr>",
            "<h3>Per il CEO</h3>",
            f"<p>{analysis.summary_ceo}</p>",
            "<h3>Per il Compliance Officer</h3>",
            f"<p>{analysis.detail_compliance[:500]}...</p>",
            "<h3>Azioni richieste</h3>",
            "<ol>",
        ]
        for action in analysis.action_items:
            html_parts.append(f"<li>{action}</li>")
        html_parts.extend([
            "</ol>",
            f"<p><strong>Rilevanza per {notification.company_name}:</strong> "
            f"{notification.relevance_score:.0%}</p>",
            f"<p><a href='{analysis.source_url}'>Documento originale</a></p>",
            "<hr>",
            "<p><small>CSRD Comply - Il tuo advisor di conformità CSRD</small></p>",
        ])
        
        return {
            "subject": subject,
            "body_text": body_text,
            "body_html": "\n".join(html_parts),
        }


# ── Utility Functions ──────────────────────────────────────────────

def analyze_update(
    title: str,
    source: str,
    url: str,
    content: Optional[str] = None,
    api_key: Optional[str] = None,
    provider: str = "openai",
) -> AnalyzedUpdate:
    """
    Funzione di utilità per analizzare un aggiornamento normativo.
    
    Args:
        title: Titolo del documento
        source: Nome della fonte
        url: URL del documento
        content: Contenuto del documento (opzionale)
        api_key: API key per LLM
        provider: Provider LLM
        
    Returns:
        AnalyzedUpdate completo
    """
    analyzer = UpdateAnalyzer(api_key=api_key, provider=provider)
    return analyzer.analyze(title, source, url, content)


def analyze_update_sync(
    title: str,
    source: str,
    url: str,
    content: Optional[str] = None,
    api_key: Optional[str] = None,
    provider: str = "openai",
) -> AnalyzedUpdate:
    """
    Versione sincrona di analyze_update.
    
    Args:
        title: Titolo del documento
        source: Nome della fonte
        url: URL del documento
        content: Contenuto del documento (opzionale)
        api_key: API key per LLM
        provider: Provider LLM
        
    Returns:
        AnalyzedUpdate completo
    """
    return analyze_update(title, source, url, content, api_key, provider)


def batch_analyze_updates(
    documents: List[dict],
    api_key: Optional[str] = None,
    provider: str = "openai",
) -> List[AnalyzedUpdate]:
    """
    Analizza multipli aggiornamenti normativi in batch.
    
    Args:
        documents: Lista di dict con "title", "source", "url", "content"
        api_key: API key per LLM
        provider: Provider LLM
        
    Returns:
        Lista di AnalyzedUpdate
    """
    analyzer = UpdateAnalyzer(api_key=api_key, provider=provider)
    results = []
    
    for doc in documents:
        try:
            analysis = analyzer.analyze(
                title=doc.get("title", "Unknown"),
                source=doc.get("source", "Unknown"),
                url=doc.get("url", ""),
                content=doc.get("content"),
            )
            results.append(analysis)
        except Exception as e:
            logger.error(f"Failed to analyze {doc.get('title', 'unknown')}: {e}")
            results.append(
                AnalyzedUpdate(
                    source_title=doc.get("title", "Error"),
                    source_url=doc.get("url", ""),
                    regulation="Unknown",
                    impact=ImpactClassification.INFO,
                    summary_ceo=f"Analisi fallita per '{doc.get('title', 'Unknown')}'",
                    detail_compliance=f"Errore: {str(e)}",
                    confidence=0.0,
                )
            )
    
    return results
