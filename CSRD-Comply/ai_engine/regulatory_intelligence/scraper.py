"""
CSRD Comply — Web Scraper Regolatorio EU (Step 23)

Monitoraggio automatico di cambiamenti normativi CSRD/ESRS da fonti ufficiali EU.

Fonti monitorate:
1. EUR-Lex (official EU law): https://eur-lex.europa.eu
   - Cerca: "CSRD", "ESRS", "sustainability reporting", "Omnibus"
   - Frequenza: ogni 6 ore

2. EFRAG website: https://www.efrag.org
   - Implementation guidance updates
   - Q&A platform
   - Taxonomy updates

3. ESMA: https://www.esma.europa.eu
   - XBRL taxonomy updates
   - Filing requirements

4. National authorities (per ogni paese EU target)
   - Italia: CONSOB
   - Germania: BaFin
   - Francia: AMF

Tecnologia:
- httpx (async HTTP client) con rate limiting
- BeautifulSoup4 per parsing HTML
- Feed RSS dove disponibile
- API EUR-Lex SPARQL endpoint
"""
import asyncio
import hashlib
import json
import logging
import re
from datetime import datetime, timedelta
from dataclasses import dataclass, field
from enum import Enum
from typing import Optional, Dict, Any, List, Set
from urllib.parse import urljoin, urlparse, quote

logger = logging.getLogger(__name__)


# ── Enums & Dataclasses ───────────────────────────────────────────

class SourceType(str, Enum):
    """Tipologia di fonte normativa."""
    EU_LAW = "eu_law"           # EUR-Lex (Official Journal)
    STANDARD_SETTER = "standard_setter"  # EFRAG
    REGULATOR = "regulator"     # ESMA, national authorities
    CONSULTATION = "consultation"  # Public consultations


class DocumentStatus(str, Enum):
    """Stato del documento normativo."""
    PROPOSED = "proposed"
    ADOPTED = "adopted"
    IN_FORCE = "in_force"
    APPLICABLE = "applicable"
    UPDATED = "updated"
    WITHDRAWN = "withdrawn"


class ImpactLevel(str, Enum):
    """Livello di impatto della modifica normativa."""
    CRITICAL = "critical"       # Cambia requisiti obbligatori
    MODERATE = "moderate"       # Nuove linee guida
    INFO = "info"               # Chiarimenti, FAQ, esempi


@dataclass
class ScraperSource:
    """Configurazione di una fonte normativa."""
    name: str
    source_type: SourceType
    base_url: str
    search_path: str
    feed_url: Optional[str] = None
    api_url: Optional[str] = None
    country: Optional[str] = None          # Per autorità nazionali
    language: str = "en"
    rate_limit: float = 1.0                 # Secondi tra richieste
    headers: Dict[str, str] = field(default_factory=lambda: {
        "User-Agent": "CSRD-Comply/1.0 (Regulatory Monitor; +https://csrdcomply.com)",
        "Accept": "text/html,application/xhtml+xml,application/xml",
    })


@dataclass
class ScrapedDocument:
    """
    Documento normativo estratto da una fonte.
    
    Attributes:
        title: Titolo del documento
        url: URL del documento originale
        source: Nome della fonte
        summary: Breve riassunto del contenuto
        content_raw: Contenuto testuale estratto
        publication_date: Data di pubblicazione
        effective_date: Data di entrata in vigore
        document_type: Tipo di documento (regulation, directive, guidance, etc.)
        regulation: Regolamento di riferimento (CSRD, ESRS, etc.)
        affected_standards: Lista di standard ESRS impattati
        status: Stato del documento
        language: Lingua del documento
        document_hash: Hash del contenuto per deduplicazione
        metadata: Metadati aggiuntivi
    """
    title: str
    url: str
    source: str
    summary: str = ""
    content_raw: str = ""
    publication_date: Optional[datetime] = None
    effective_date: Optional[datetime] = None
    document_type: str = "unknown"
    regulation: str = ""
    affected_standards: List[str] = field(default_factory=list)
    status: DocumentStatus = DocumentStatus.PROPOSED
    language: str = "en"
    document_hash: str = ""
    metadata: Dict[str, Any] = field(default_factory=dict)

    def __post_init__(self):
        """Genera hash del documento se non fornito."""
        if not self.document_hash:
            content_for_hash = f"{self.title}{self.url}{self.summary}"
            self.document_hash = hashlib.sha256(
                content_for_hash.encode("utf-8")
            ).hexdigest()[:32]


@dataclass
class ScrapeResult:
    """Risultato di un'operazione di scraping."""
    source: str
    documents: List[ScrapedDocument]
    success: bool = True
    error_message: Optional[str] = None
    pages_scraped: int = 0
    new_documents: int = 0
    scrape_duration: float = 0.0
    scraped_at: datetime = field(default_factory=datetime.utcnow)


class ScraperError(Exception):
    """Eccezione base per errori di scraping."""
    pass


class RateLimitError(ScraperError):
    """Rate limit superato."""
    pass


class ParseError(ScraperError):
    """Errore nel parsing del contenuto."""
    pass


# ── HTTP Client ───────────────────────────────────────────────────

class AsyncHTTPClient:
    """
    Client HTTP asincrono con rate limiting e retry.
    
    Usage:
        client = AsyncHTTPClient(rate_limit=1.0)
        html = await client.get("https://eur-lex.europa.eu/...")
    """

    def __init__(self, rate_limit: float = 1.0):
        self.rate_limit = rate_limit
        self._last_request: Dict[str, datetime] = {}
        self._session = None

    async def _ensure_session(self):
        """Assicura che la sessione HTTP sia inizializzata."""
        if self._session is None:
            import httpx
            self._session = httpx.AsyncClient(
                timeout=30.0,
                follow_redirects=True,
                headers={
                    "User-Agent": (
                        "CSRD-Comply/1.0 Regulatory Monitor; "
                        "+https://csrdcomply.com"
                    ),
                },
            )

    async def get(self, url: str, **kwargs) -> Optional[str]:
        """
        Esegue una richiesta GET asincrona con rate limiting.
        
        Args:
            url: URL da richiedere
            **kwargs: Parametri aggiuntivi per httpx
            
        Returns:
            Contenuto HTML/XML come stringa, o None se errore
            
        Raises:
            RateLimitError: Se il rate limit è superato
        """
        await self._ensure_session()

        # Rate limiting per dominio
        domain = urlparse(url).netloc
        now = datetime.utcnow()
        if domain in self._last_request:
            elapsed = (now - self._last_request[domain]).total_seconds()
            if elapsed < self.rate_limit:
                wait = self.rate_limit - elapsed
                await asyncio.sleep(wait)

        try:
            response = await self._session.get(url, **kwargs)
            self._last_request[domain] = datetime.utcnow()

            if response.status_code == 429:
                retry_after = int(response.headers.get("Retry-After", 60))
                logger.warning(
                    f"Rate limited on {domain}, waiting {retry_after}s"
                )
                await asyncio.sleep(retry_after)
                return await self.get(url, **kwargs)

            response.raise_for_status()
            return response.text

        except httpx.TimeoutException:
            logger.error(f"Timeout requesting {url}")
            return None
        except httpx.HTTPStatusError as e:
            logger.error(f"HTTP {e.response.status_code} for {url}")
            return None
        except Exception as e:
            logger.error(f"Error requesting {url}: {str(e)}")
            return None

    async def close(self):
        """Chiude la sessione HTTP."""
        if self._session:
            await self._session.aclose()
            self._session = None


# ── Scraper Base ──────────────────────────────────────────────────

class RegulatoryScraper:
    """
    Classe base per scraper normativi.
    
    Fornisce metodi comuni per:
    - Estrazione testo da HTML
    - Deduplicazione documenti
    - Rate limiting
    - Logging
    
    Usage:
        scraper = EURLexScraper()
        result = await scraper.scrape()
        for doc in result.documents:
            print(f"Found: {doc.title}")
    """

    def __init__(
        self,
        source: Optional[ScraperSource] = None,
        max_documents: int = 50,
    ):
        """
        Args:
            source: Configurazione della fonte
            max_documents: Numero massimo di documenti da estrarre per scraping
        """
        if source is None:
            source = ScraperSource(
                name="EUR-Lex",
                source_type=SourceType.EU_LAW,
                base_url="https://eur-lex.europa.eu",
                search_path="/search.html",
            )
        self.source = source
        self.max_documents = max_documents
        self.client = AsyncHTTPClient(rate_limit=source.rate_limit)
        self.seen_hashes: Set[str] = set()

    def get_sources(self) -> List[ScraperSource]:
        """Restituisce le fonti configurate per lo scraper."""
        return [self.source]

    def parse_update(self, update_data: dict) -> dict:
        """Parsa i dati grezzi di un aggiornamento normativo."""
        title = update_data.get("title", "")
        body = update_data.get("body", "")
        raw_date = update_data.get("date", datetime.now().strftime("%Y-%m-%d"))
        source_name = update_data.get("source", self.source.name)
        
        # Identifica quale regolamento
        regulation = "ESRS"
        if "E1" in title or "E1" in body:
            regulation = "ESRS E1"
        elif "ESRS" in title:
            regulation = "ESRS"
            
        return {
            "title": title,
            "body": body,
            "regulation": regulation,
            "effective_date": raw_date,
            "date": raw_date,
            "source": source_name,
        }

    async def scrape(self) -> ScrapeResult:
        """
        Esegue lo scraping della fonte.
        
        Metodo principale da implementare nelle sottoclassi.
        
        Returns:
            ScrapeResult con i documenti trovati
        """
        raise NotImplementedError("Subclasses must implement scrape()")

    def extract_text(self, html: str, selector: str = "body") -> str:
        """
        Estrae testo pulito da HTML usando BeautifulSoup.
        
        Args:
            html: Contenuto HTML
            selector: Selettore CSS per limitare l'estrazione
            
        Returns:
            Testo estratto e pulito
        """
        try:
            from bs4 import BeautifulSoup
            soup = BeautifulSoup(html, "html.parser")

            if selector != "body":
                elements = soup.select(selector)
                if elements:
                    text = " ".join(elem.get_text(separator=" ", strip=True)
                                    for elem in elements)
                else:
                    text = soup.get_text(separator=" ", strip=True)
            else:
                text = soup.get_text(separator=" ", strip=True)

            # Pulisci spazi multipli e newline
            text = re.sub(r'\s+', ' ', text).strip()
            return text

        except ImportError:
            logger.warning("BeautifulSoup not installed, using regex fallback")
            text = re.sub(r'<[^>]+>', ' ', html)
            text = re.sub(r'\s+', ' ', text).strip()
            return text
        except Exception as e:
            logger.error(f"Text extraction error: {str(e)}")
            return ""

    def extract_links(
        self,
        html: str,
        base_url: str,
        pattern: Optional[str] = None,
    ) -> List[str]:
        """
        Estrae link da HTML, opzionalmente filtrati per pattern.
        
        Args:
            html: Contenuto HTML
            base_url: URL base per risolvere link relativi
            pattern: Pattern regex per filtrare link
            
        Returns:
            Lista di URL assoluti
        """
        try:
            from bs4 import BeautifulSoup
            soup = BeautifulSoup(html, "html.parser")
            links = []

            for a_tag in soup.find_all("a", href=True):
                href = a_tag["href"]
                absolute_url = urljoin(base_url, href)

                # Filtra per pattern se specificato
                if pattern and not re.search(pattern, absolute_url, re.IGNORECASE):
                    continue

                # Filtra link non HTTP
                if not absolute_url.startswith(("http://", "https://")):
                    continue

                # Filtra anchor interni
                if "#" in absolute_url and absolute_url.endswith("#"):
                    continue

                links.append(absolute_url)

            return list(set(links))  # Deduplica

        except ImportError:
            logger.warning("BeautifulSoup not installed")
            return []

    def is_duplicate(self, document: ScrapedDocument) -> bool:
        """
        Verifica se un documento è già stato visto (deduplicazione).
        
        Args:
            document: Documento da verificare
            
        Returns:
            True se è un duplicato
        """
        if document.document_hash in self.seen_hashes:
            return True
        self.seen_hashes.add(document.document_hash)
        return False

    def classify_regulation(self, text: str) -> str:
        """
        Classifica il regolamento di riferimento dal testo.
        
        Args:
            text: Testo del documento
            
        Returns:
            Nome del regolamento (CSRD, ESRS, EU Taxonomy, Omnibus, etc.)
        """
        text_lower = text.lower()

        keywords = {
            "CSRD": ["csrd", "corporate sustainability reporting directive",
                     "2022/2464", "sustainability reporting directive"],
            "ESRS": ["esrs", "european sustainability reporting standard",
                     "sustainability reporting standard"],
            "EU Taxonomy": ["eu taxonomy", "taxonomy regulation",
                           "2020/852", "sustainable finance taxonomy"],
            "Omnibus": ["omnibus", "simplification"],
            "SFDR": ["sfdr", "sustainable finance disclosure",
                     "2019/2088"],
            "CBAM": ["cbam", "carbon border adjustment"],
            "CSDDD": ["csddd", "corporate sustainability due diligence",
                      "directive on corporate sustainability"],
        }

        for regulation, patterns in keywords.items():
            if any(p in text_lower for p in patterns):
                return regulation

        return "Unknown"

    def classify_impact(self, document: ScrapedDocument) -> ImpactLevel:
        """
        Classifica il livello di impatto del documento.
        
        Args:
            document: Documento da classificare
            
        Returns:
            Livello di impatto
        """
        text_lower = f"{document.title} {document.summary}".lower()

        # Parole chiave per impatto critico
        critical_keywords = [
            "mandatory", "obbligatorio", "requirement", "must",
            "shall", "compliance", "deadline", "effective date",
            "entry into force", "new disclosure", "new requirement",
        ]
        critical_count = sum(
            1 for kw in critical_keywords if kw in text_lower
        )

        if critical_count >= 3:
            return ImpactLevel.CRITICAL
        elif critical_count >= 1:
            return ImpactLevel.MODERATE
        else:
            return ImpactLevel.INFO

    def extract_affected_standards(self, text: str) -> List[str]:
        """
        Estrae la lista di standard ESRS menzionati nel testo.
        
        Args:
            text: Testo del documento
            
        Returns:
            Lista di standard ESRS (es. ["ESRS E1", "ESRS S1"])
        """
        pattern = r'ESRS\s+[EsegrEGS][1-9](?:[0-9])?(?:\s*–\s*[EsegrEGS][1-9])?'
        matches = re.findall(pattern, text, re.IGNORECASE)

        # Normalizza
        standards = set()
        for match in matches:
            match = match.strip().upper()
            # Correggi formato "ESRS E 1" -> "ESRS E1"
            match = re.sub(r'(ESRS\s+[A-Z])\s+(\d)', r'\1\2', match)
            standards.add(match)

        return sorted(standards)

    async def close(self):
        """Pulisce risorse."""
        await self.client.close()


# ── EUR-Lex Scraper ───────────────────────────────────────────────

class EURLexScraper(RegulatoryScraper):
    """
    Scraper per EUR-Lex (Official Journal of the European Union).
    
    Cerca atti legislativi EU relativi a CSRD/ESRS/sustainability reporting.
    Usa API SPARQL endpoint e scraping HTML come fallback.
    """

    # Query SPARQL predefinite
    SPARQL_QUERIES = {
        "csrd_related": """
            SELECT ?work ?title ?date WHERE {{
                ?work rdf:type cdm:regulation.
                ?work cdm:resource_legal_id_celex ?celex.
                ?work cdm:resource_legal_title_ consolidated ?title.
                ?work cdm:resource_legal_date ?date.
                FILTER(CONTAINS(LCASE(?title), "sustainability") ||
                       CONTAINS(LCASE(?title), "csrd") ||
                       CONTAINS(LCASE(?title), "esrs") ||
                       CONTAINS(LCASE(?title), "reporting"))
            }}
            ORDER BY DESC(?date)
            LIMIT {limit}
        """,
    }

    def __init__(self, max_documents: int = 50):
        source = ScraperSource(
            name="EUR-Lex",
            source_type=SourceType.EU_LAW,
            base_url="https://eur-lex.europa.eu",
            search_path="/search.html",
            api_url="https://publications.europa.eu/webapi/rdf/sparql",
            feed_url="https://eur-lex.europa.eu/feed/",
            rate_limit=2.0,
        )
        super().__init__(source, max_documents)

    async def scrape(self) -> ScrapeResult:
        """
        Scraping di EUR-Lex per atti normativi CSRD/ESRS.
        
        Usa prima SPARQL endpoint, poi fallback su ricerca HTML.
        """
        start_time = datetime.utcnow()
        documents = []

        # Prova con SPARQL
        try:
            docs = await self._scrape_sparql()
            documents.extend(docs)
        except Exception as e:
            logger.warning(f"EUR-Lex SPARQL failed: {e}, falling back to HTML")

        # Se SPARQL non ha prodotto risultati, usa ricerca HTML
        if not documents:
            try:
                docs = await self._scrape_html_search()
                documents.extend(docs)
            except Exception as e:
                logger.warning(f"EUR-Lex HTML search failed: {e}")

        # Deduplica
        unique_docs = []
        for doc in documents:
            if not self.is_duplicate(doc):
                unique_docs.append(doc)

        duration = (datetime.utcnow() - start_time).total_seconds()
        logger.info(
            f"EUR-Lex: found {len(unique_docs)} new documents "
            f"in {duration:.1f}s"
        )

        return ScrapeResult(
            source="EUR-Lex",
            documents=unique_docs,
            new_documents=len(unique_docs),
            pages_scraped=max(1, len(documents) // 10),
            scrape_duration=duration,
        )

    async def _scrape_sparql(self) -> List[ScrapedDocument]:
        """Esegue query SPARQL su EUR-Lex."""
        query = self.SPARQL_QUERIES["csrd_related"].format(
            limit=self.max_documents
        )

        params = {
            "query": query,
            "format": "application/sparql-results+json",
        }

        html = await self.client.get(
            self.source.api_url,
            params=params,
        )

        if not html:
            return []

        try:
            results = json.loads(html)
            documents = []

            for binding in results.get("results", {}).get("bindings", []):
                title = binding.get("title", {}).get("value", "Unknown")
                date_str = binding.get("date", {}).get("value", "")
                url = binding.get("work", {}).get("value", "")

                pub_date = None
                if date_str:
                    try:
                        pub_date = datetime.fromisoformat(date_str.replace("Z", "+00:00"))
                    except (ValueError, TypeError):
                        pass

                doc = ScrapedDocument(
                    title=title,
                    url=url,
                    source="EUR-Lex (SPARQL)",
                    summary=f"EU legal act related to sustainability reporting",
                    publication_date=pub_date,
                    document_type="regulation",
                    regulation=self.classify_regulation(title),
                    status=DocumentStatus.ADOPTED,
                    metadata={"source": "sparql"},
                )
                documents.append(doc)

            return documents

        except (json.JSONDecodeError, KeyError) as e:
            logger.error(f"SPARQL response parse error: {e}")
            return []

    async def _scrape_html_search(self) -> List[ScrapedDocument]:
        """Esegue ricerca via HTML su EUR-Lex."""
        search_terms = [
            "CSRD sustainability reporting",
            "ESRS adoption",
            "sustainability reporting directive",
            "corporate sustainability",
        ]

        documents = []
        for term in search_terms[:2]:  # Limita a 2 termini
            search_url = (
                f"{self.source.base_url}/search.html"
                f"?q={quote(term)}"
                f"&scope=OJ"
                f"&type=advanced"
                f"&lang=en"
            )

            html = await self.client.get(search_url)
            if not html:
                continue

            # Cerca risultati
            results_links = self.extract_links(
                html, self.source.base_url,
                pattern=r"(eli|CELEX|oj/\w)",
            )

            for link in results_links[:self.max_documents]:
                doc_html = await self.client.get(link)
                if not doc_html:
                    continue

                title = self.extract_text(
                    doc_html, "h1, .title, .resource-title"
                )
                if not title:
                    title = f"EUR-Lex Document: {link}"

                body_text = self.extract_text(doc_html)

                doc = ScrapedDocument(
                    title=title[:200],
                    url=link,
                    source="EUR-Lex (HTML)",
                    summary=body_text[:300] if body_text else "",
                    content_raw=body_text,
                    document_type="regulation",
                    regulation=self.classify_regulation(title),
                    status=DocumentStatus.ADOPTED,
                    affected_standards=self.extract_affected_standards(body_text),
                    metadata={"source": "html_search", "search_term": term},
                )
                documents.append(doc)

        return documents


# ── EFRAG Scraper ─────────────────────────────────────────────────

class EFRAGScraper(RegulatoryScraper):
    """
    Scraper per il sito EFRAG (European Financial Reporting Advisory Group).
    
    Monitora:
    - Implementation guidance updates
    - Q&A platform
    - Taxonomy updates
    - Public consultations
    """

    # URL delle sezioni da monitorare
    MONITOR_PATHS = {
        "sustainability": "/sustainability",
        "sustainability-news": "/sustainability/news",
        "sustainability-consultations": "/sustainability/consultations",
        "sustainability-publications": "/sustainability/publications",
    }

    def __init__(self, max_documents: int = 30):
        source = ScraperSource(
            name="EFRAG",
            source_type=SourceType.STANDARD_SETTER,
            base_url="https://www.efrag.org",
            search_path="/sustainability/news",
            feed_url="https://www.efrag.org/rss",
            rate_limit=1.0,
        )
        super().__init__(source, max_documents)

    async def scrape(self) -> ScrapeResult:
        """
        Scraping del sito EFRAG per aggiornamenti.
        
        Scansiona le sezioni configurate e raccoglie documenti.
        """
        start_time = datetime.utcnow()
        documents = []

        for section_name, path in self.MONITOR_PATHS.items():
            try:
                section_url = urljoin(self.source.base_url, path)
                html = await self.client.get(section_url)

                if not html:
                    continue

                # Estrai link a documenti/articoli
                article_links = self.extract_links(
                    html, section_url,
                    pattern=r"(article|document|publication|news|assets)",
                )

                for link in article_links[:10]:  # Max 10 per sezione
                    doc_html = await self.client.get(link)
                    if not doc_html:
                        continue

                    title = self.extract_text(doc_html, "h1")
                    if not title:
                        title = f"EFRAG Document: {link}"

                    body = self.extract_text(doc_html, "main, article, .content")

                    doc = ScrapedDocument(
                        title=title[:200],
                        url=link,
                        source=f"EFRAG ({section_name})",
                        summary=body[:300] if body else "EFRAG publication",
                        content_raw=body or "",
                        document_type="guidance",
                        regulation=self.classify_regulation(body or title),
                        status=DocumentStatus.ADOPTED,
                        affected_standards=self.extract_affected_standards(
                            body or title
                        ),
                        metadata={"section": section_name},
                    )
                    documents.append(doc)

            except Exception as e:
                logger.error(f"EFRAG section {section_name} error: {e}")

        unique_docs = [d for d in documents if not self.is_duplicate(d)]

        duration = (datetime.utcnow() - start_time).total_seconds()
        logger.info(
            f"EFRAG: found {len(unique_docs)} new documents in {duration:.1f}s"
        )

        return ScrapeResult(
            source="EFRAG",
            documents=unique_docs,
            new_documents=len(unique_docs),
            pages_scraped=len(self.MONITOR_PATHS),
            scrape_duration=duration,
        )


# ── ESMA Scraper ──────────────────────────────────────────────────

class ESMAScraper(RegulatoryScraper):
    """
    Scraper per ESMA (European Securities and Markets Authority).
    
    Monitora:
    - XBRL taxonomy updates
    - Filing requirements
    - ESEF updates
    """

    def __init__(self, max_documents: int = 30):
        source = ScraperSource(
            name="ESMA",
            source_type=SourceType.REGULATOR,
            base_url="https://www.esma.europa.eu",
            search_path="/search",
            feed_url="https://www.esma.europa.eu/rss.xml",
            rate_limit=1.0,
        )
        super().__init__(source, max_documents)

    async def scrape(self) -> ScrapeResult:
        """
        Scraping del sito ESMA per aggiornamenti normativi.
        
        Cerca documenti relativi a XBRL, ESEF, sustainability reporting.
        """
        start_time = datetime.utcnow()
        documents = []

        # Pagine specifiche da monitorare
        pages = [
            "/press-news/esma-news",
            "/risk-analysis-and-statistics/data-analysis",
            "/policy-activities",
        ]

        for page in pages:
            try:
                url = urljoin(self.source.base_url, page)
                html = await self.client.get(url)

                if not html:
                    continue

                # Cerca link a documenti PDF/HTML con parole chiave
                keywords = ["xbrl", "esef", "sustainability", "csrd",
                           "reporting", "taxonomy"]
                links = self.extract_links(html, self.source.base_url)

                for link in links:
                    link_lower = link.lower()
                    if not any(kw in link_lower for kw in keywords):
                        continue

                    doc_html = await self.client.get(link)
                    if not doc_html:
                        continue

                    title = self.extract_text(doc_html, "h1")
                    if not title:
                        title = f"ESMA Document: {link}"

                    body = self.extract_text(doc_html)

                    doc = ScrapedDocument(
                        title=title[:200],
                        url=link,
                        source="ESMA",
                        summary=body[:300] if body else "ESMA publication",
                        content_raw=body or "",
                        document_type="regulatory",
                        regulation=self.classify_regulation(body or title),
                        status=DocumentStatus.ADOPTED,
                        affected_standards=self.extract_affected_standards(
                            body or title
                        ),
                        metadata={"page": page},
                    )
                    documents.append(doc)

                    if len(documents) >= self.max_documents:
                        break

            except Exception as e:
                logger.error(f"ESMA page {page} error: {e}")

        unique_docs = [d for d in documents if not self.is_duplicate(d)]

        duration = (datetime.utcnow() - start_time).total_seconds()
        logger.info(
            f"ESMA: found {len(unique_docs)} new documents in {duration:.1f}s"
        )

        return ScrapeResult(
            source="ESMA",
            documents=unique_docs,
            new_documents=len(unique_docs),
            pages_scraped=len(pages),
            scrape_duration=duration,
        )


# ── National Authority Scraper ────────────────────────────────────

class NationalAuthorityScraper(RegulatoryScraper):
    """
    Scraper per autorità nazionali EU.
    
    Supporta:
    - Italia: CONSOB
    - Germania: BaFin
    - Francia: AMF
    
    Configurabile per aggiungere altri paesi.
    """

    # Mappatura autorità nazionali
    AUTHORITIES = {
        "IT": {
            "name": "CONSOB",
            "base_url": "https://www.consob.it",
            "search_path": "/web/area-pubblica/regolamentazione",
        },
        "DE": {
            "name": "BaFin",
            "base_url": "https://www.bafin.de",
            "search_path": "/DE/Aufsicht/ESG/esg_node.html",
        },
        "FR": {
            "name": "AMF",
            "base_url": "https://www.amf-france.org",
            "search_path": "/fr/recherche",
        },
    }

    def __init__(
        self,
        country: str = "IT",
        max_documents: int = 20,
    ):
        authority = self.AUTHORITIES.get(country)
        if not authority:
            raise ValueError(f"Unsupported country: {country}. Supported: {list(self.AUTHORITIES.keys())}")

        source = ScraperSource(
            name=authority["name"],
            source_type=SourceType.REGULATOR,
            base_url=authority["base_url"],
            search_path=authority["search_path"],
            country=country,
            language="it" if country == "IT" else "de" if country == "DE" else "fr",
            rate_limit=1.5,
        )
        super().__init__(source, max_documents)

    async def scrape(self) -> ScrapeResult:
        """
        Scraping dell'autorità nazionale per aggiornamenti normativi.
        
        Cerca documenti relativi a CSRD/sostenibilità.
        """
        start_time = datetime.utcnow()
        documents = []

        search_url = urljoin(
            self.source.base_url, self.source.search_path
        )

        try:
            html = await self.client.get(search_url)
            if not html:
                return ScrapeResult(
                    source=self.source.name,
                    documents=[],
                    pages_scraped=1,
                    scrape_duration=(datetime.utcnow() - start_time).total_seconds(),
                )

            # Cerca link a documenti normativi
            links = self.extract_links(html, self.source.base_url)

            # Parole chiave per paese
            lang_keywords = {
                "IT": ["sostenibilità", "csrd", "esrs", "esg",
                       "reporting", "non finanziaria"],
                "DE": ["nachhaltigkeit", "csrd", "esrs", "esg",
                       "berichterstattung"],
                "FR": ["durabilité", "csrd", "esrs", "esg",
                       "rapport", "extra-financier"],
            }
            keywords = lang_keywords.get(
                self.source.country or "en",
                ["sustainability", "csrd", "esrs"],
            )

            for link in links:
                link_lower = link.lower()
                if not any(kw in link_lower for kw in keywords):
                    continue

                doc_html = await self.client.get(link)
                if not doc_html:
                    continue

                title = self.extract_text(doc_html, "h1")
                if not title:
                    title = f"{self.source.name} Document: {link}"

                body = self.extract_text(doc_html)

                doc = ScrapedDocument(
                    title=title[:200],
                    url=link,
                    source=f"{self.source.name} ({self.source.country})",
                    summary=body[:300] if body else "National regulatory document",
                    content_raw=body or "",
                    document_type="national_regulation",
                    regulation=self.classify_regulation(body or title),
                    status=DocumentStatus.ADOPTED,
                    language=self.source.language,
                    affected_standards=self.extract_affected_standards(
                        body or title
                    ),
                    metadata={"authority": self.source.name, "country": self.source.country},
                )
                documents.append(doc)

                if len(documents) >= self.max_documents:
                    break

        except Exception as e:
            logger.error(f"{self.source.name} scrape error: {e}")

        unique_docs = [d for d in documents if not self.is_duplicate(d)]

        duration = (datetime.utcnow() - start_time).total_seconds()
        logger.info(
            f"{self.source.name}: found {len(unique_docs)} new documents "
            f"in {duration:.1f}s"
        )

        return ScrapeResult(
            source=self.source.name,
            documents=unique_docs,
            new_documents=len(unique_docs),
            pages_scraped=1,
            scrape_duration=duration,
        )


# ── Factory & Coordinator ─────────────────────────────────────────

def create_scraper(
    source_type: str,
    country: Optional[str] = None,
    max_documents: int = 50,
) -> RegulatoryScraper:
    """
    Factory per creare scraper specifici.
    
    Args:
        source_type: Tipo di fonte ("eurlex", "efrag", "esma", "national")
        country: Paese per autorità nazionali (IT, DE, FR)
        max_documents: Numero massimo documenti
        
    Returns:
        Istanza dello scraper appropriato
        
    Raises:
        ValueError: Se source_type non è supportato
    """
    scraper_map = {
        "eurlex": EURLexScraper,
        "efrag": EFRAGScraper,
        "esma": ESMAScraper,
        "national": lambda m=max_documents: NationalAuthorityScraper(
            country=country or "IT", max_documents=m
        ),
    }

    scraper_factory = scraper_map.get(source_type.lower())
    if not scraper_factory:
        raise ValueError(
            f"Unknown source type: {source_type}. "
            f"Supported: {list(scraper_map.keys())}"
        )

    if source_type.lower() == "national":
        return scraper_factory()
    return scraper_factory(max_documents=max_documents)


async def scrape_all_sources(
    countries: Optional[List[str]] = None,
    max_documents_per_source: int = 30,
) -> Dict[str, ScrapeResult]:
    """
    Esegue scraping di tutte le fonti normativE.
    
    Args:
        countries: Lista di paesi per autorità nazionali (default: ["IT", "DE", "FR"])
        max_documents_per_source: Max documenti per fonte
        
    Returns:
        Dizionario {source_name: ScrapeResult}
    """
    if countries is None:
        countries = ["IT", "DE", "FR"]

    scraper_configs = [
        ("EUR-Lex", "eurlex"),
        ("EFRAG", "efrag"),
        ("ESMA", "esma"),
    ]

    # Aggiungi autorità nazionali
    for country in countries:
        scraper_configs.append(
            (f"National ({country})", "national")
        )

    results = {}

    for name, source_type in scraper_configs:
        try:
            if source_type == "national":
                # Determina il paese dalla configurazione
                country = name.split("(")[1].rstrip(")")
            else:
                country = None

            scraper = create_scraper(
                source_type, country=country,
                max_documents=max_documents_per_source,
            )

            result = await scraper.scrape()
            results[name] = result
            await scraper.close()

        except Exception as e:
            logger.error(f"Scraper {name} failed: {e}")
            results[name] = ScrapeResult(
                source=name,
                documents=[],
                success=False,
                error_message=str(e),
            )

    # Statistiche totali
    total_docs = sum(
        r.new_documents for r in results.values()
    )
    total_duration = sum(
        r.scrape_duration for r in results.values()
    )
    logger.info(
        f"Scrape cycle complete: {total_docs} new documents "
        f"from {len(results)} sources in {total_duration:.1f}s"
    )

    return results


# ── Sync Wrapper (per uso non-async) ──────────────────────────────

def scrape_all_sources_sync(
    countries: Optional[List[str]] = None,
    max_documents_per_source: int = 30,
) -> Dict[str, ScrapeResult]:
    """
    Versione sincrona di scrape_all_sources.
    
    Usage:
        results = scrape_all_sources_sync(["IT", "DE"])
        for source, result in results.items():
            print(f"{source}: {len(result.documents)} documents")
    """
    return asyncio.run(
        scrape_all_sources(countries, max_documents_per_source)
    )


def scrape_source_sync(
    source_type: str,
    country: Optional[str] = None,
    max_documents: int = 30,
) -> ScrapeResult:
    """
    Versione sincrona per scraping di una singola fonte.
    
    Args:
        source_type: Tipo di fonte ("eurlex", "efrag", "esma", "national")
        country: Paese per autorità nazionali
        max_documents: Max documenti
        
    Returns:
        ScrapeResult con i documenti trovati
    """
    async def _scrape():
        scraper = create_scraper(source_type, country, max_documents)
        result = await scraper.scrape()
        await scraper.close()
        return result

    return asyncio.run(_scrape())
