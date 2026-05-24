# CSRD Comply — Piano di Implementazione in 30 Step (per AI)

> **Prodotto**: SaaS di conformità CSRD/ESG per PMI Europee  
> **Target**: PMI 10-249 dipendenti (€149-399/mese), Mid-market 250-500 dipendenti (€499-1.499/mese)  
> **Tecnologia**: AI-first, cloud-native  
> **Sviluppo**: 100% AI (questo piano è scritto per essere letto ed eseguito da un'AI)

---

## FASE 0 — FONDAZIONE

---

### Step 1: Scaffolding del Progetto

**Obiettivo**: Creare la struttura base del monorepo.

Crea la seguente struttura di directory:

```
/CSRD-Comply
├── frontend/                    # Next.js 14 (App Router, TypeScript)
│   ├── src/
│   │   ├── app/                 # Pages (login, dashboard, reports, settings)
│   │   ├── components/          # UI components (shadcn/ui + Tailwind)
│   │   ├── lib/                 # Client utilities, API calls
│   │   ├── hooks/               # React hooks (useCSRD, useEmissions, etc.)
│   │   └── types/               # TypeScript type definitions
│   ├── public/
│   ├── next.config.js
│   ├── tailwind.config.ts
│   └── package.json
├── backend/                     # Python FastAPI
│   ├── app/
│   │   ├── api/                 # Route handlers
│   │   ├── core/                # Config, DB connection, auth
│   │   ├── models/              # SQLAlchemy models
│   │   ├── schemas/             # Pydantic schemas
│   │   ├── services/            # Business logic
│   │   └── ai/                  # AI/ML modules
│   ├── alembic/                 # DB migrations
│   ├── tests/
│   ├── requirements.txt
│   └── Dockerfile
├── ai-engine/                   # Python AI microservices
│   ├── esrs_parser/             # NLP: ESRS parsing & mapping
│   ├── carbon_calculator/       # GHG Protocol emissions calculator
│   ├── materiality_engine/      # Double materiality scoring
│   └── report_generator/        # iXBRL report generation
├── infrastructure/
│   ├── docker-compose.yml
│   ├── nginx/
│   └── terraform/
├── docs/
└── README.md
```

**Comandi da eseguire**:
```bash
mkdir -p CSRD-Comply/{frontend,backend,ai-engine,infrastructure,docs}
cd CSRD-Comply
git init
echo "node_modules/\n__pycache__/\n.env\n*.pyc" > .gitignore
```

**Database**: PostgreSQL 16 con estensione pgvector per embedding search.

**Auth**: Supabase/Auth0 con JWT. Tabella `users` con: id, email, company_name, company_size, sector, country, subscription_tier, created_at.

---

### Step 2: Database Schema (SQLAlchemy + Alembic)

**Obiettivo**: Definire tutte le tabelle del database.

Crea il file `backend/app/models/__init__.py` con queste entità:

**Tabella `companies`**:
```python
# company_id (PK UUID)
# company_name, vat_number, country, sector (NACE code)
# employee_count, turnover, balance_sheet_total
# csrd_wave: int (1=2025, 2=2026, 3=2027)
# reporting_year: int (e.g. 2026 per report 2027)
# created_at, updated_at
```

**Tabella `users`**:
```python
# user_id (PK UUID), company_id (FK)
# email, hashed_password, role (admin/contributor/viewer)
# is_active, last_login
```

**Tabella `company_context`**: (per DMA - double materiality)
```python
# id (PK), company_id (FK)
# value_chain_description: text  # upstream/downstream
# key_activities: JSON  # lista attività principali
# business_relationships: JSON  # fornitori, clienti, partner
# geographical_scope: JSON  # paesi operativi
# stakeholder_groups: JSON  # mappatura stakeholder
```

**Tabella `sustainability_matters`**: (elenco dei topic ESRS)
```python
# id (PK)
# standard: str  # ESRS E1, E2, ... S1, S2, ... G1
# topic_name: str
# sub_topic: str
# sub_sub_topic: str
# category: str  # environmental/social/governance
# mandatory: bool
```

**Tabella `esrs_datapoints`**: (1.191+ datapoint individuali)
```python
# id (PK)
# standard_ref: str  # "ESRS E1-6"
# paragraph_ref: str  # "44(a)"
# disclosure_requirement: str  # "Gross Scope 1 GHG emissions"
# data_type: str  # numerical/boolean/narrative/semi-narrative
# unit: str  # tCO2eq, %, EUR, etc.
# is_mandatory: bool
# is_conditional: bool
# phase_in_year: int  # None=always, 2026, 2027
# sfd_ref: str  # link to SFDR if applicable
```

**Tabella `materiality_assessment`**:
```python
# id (PK), company_id (FK)
# assessment_date: date
# status: str  # draft/in_progress/completed/audited
# methodology_version: str
```

**Tabella `materiality_scores`**:
```python
# id (PK), assessment_id (FK), datapoint_id (FK)
# impact_scale: int (1-5)
# impact_scope: int (1-5)
# impact_irremediability: int (1-5)
# impact_likelihood: int (1-5)
# financial_magnitude: int (1-5)
# financial_likelihood: int (1-5)
# total_impact_score: float  # media pesata
# total_financial_score: float
# is_material: bool
# rationale: text
```

**Tabella `emissions_data`**:
```python
# id (PK), company_id (FK), reporting_year: int
# scope: str  # 1/2/3
# category: str  # per scope 3: purchased_goods, transportation, etc.
# value: float
# unit: str  # tCO2eq
# calculation_method: str  # supplier_specific/spend_based/average_data/hybrid
# emission_factor_source: str  # DEFRA, EPA, IPCC, Ecoinvent, etc.
# verified: bool
# verification_date: date
```

**Tabella `reports`**:
```python
# id (PK), company_id (FK), reporting_year: int
# title: str
# status: str  # draft/review/final/filed
# xhtml_content: text  # il report iXBRL generato
# xbrl_validation_passed: bool
# filed_at: datetime
# filed_to: str  # ESAP, national authority
```

**Tabella `regulatory_updates`**:
```python
# id (PK)
# regulation: str  # CSRD, ESRS, EU Taxonomy, Omnibus
# title: str
# summary: text
# effective_date: date
# affected_standards: JSON  # lista ESRS impacted
# source_url: str
# ai_summary: text  # generato da AI
```

Esegui `alembic init` e crea la prima migrazione.

---

### Step 3: Configurazione Backend FastAPI

**Obiettivo**: Setup del server backend con autenticazione e CRUD base.

Crea `backend/app/main.py`:
```python
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from app.core.config import settings
from app.api import router

app = FastAPI(title="CSRD Comply API", version="0.1.0")
app.add_middleware(CORSMiddleware, allow_origins=settings.CORS_ORIGINS, ...)
app.include_router(router, prefix="/api/v1")
```

Crea `backend/app/core/config.py` con:
```python
class Settings(BaseSettings):
    DATABASE_URL: str
    SECRET_KEY: str
    ALGORITHM: str = "HS256"
    ACCESS_TOKEN_EXPIRE_MINUTES: int = 60
    OPENAI_API_KEY: str
    ANTHROPIC_API_KEY: str
    CORS_ORIGINS: list = ["http://localhost:3000"]
    ENVIRONMENT: str = "development"
    SUPABASE_URL: str
    SUPABASE_KEY: str
```

Implementa:
- POST `/api/v1/auth/register`, `/api/v1/auth/login`, `/api/v1/auth/refresh`
- GET `/api/v1/companies/me`, PATCH `/api/v1/companies/me`
- GET/POST `api/v1/assessment/`
- GET/POST `/api/v1/emissions/`
- GET/POST `/api/v1/reports/`

Usa **Pydantic v2** per tutti gli schemi di validazione.

---

### Step 4: Frontend Scaffolding (Next.js 14 + shadcn/ui)

**Obiettivo**: Setup del frontend con componenti base.

```bash
cd frontend
npx create-next-app@latest . --typescript --tailwind --eslint --app --src-dir
npx shadcn@latest init
npm install @supabase/supabase-js @tanstack/react-query recharts lucide-react
```

Crea layout base in `src/app/layout.tsx`:
- Sidebar (Dashboard, Assessment, Emissions, Reports, Settings)
- Header con user avatar e notifiche
- Tema chiaro/scuro

Crea le pagine base:
```typescript
// src/app/dashboard/page.tsx
// src/app/assessment/page.tsx
// src/app/emissions/page.tsx
// src/app/reports/page.tsx
// src/app/settings/page.tsx
// src/app/auth/login/page.tsx
// src/app/auth/register/page.tsx
```

Implementa il sistema di autenticazione lato client con `useSession` hook.

---

## FASE 1 — PARSE & MAPPA ESRS

---

### Step 5: Ingegnerizzazione della Tassonomia ESRS

**Obiettivo**: Convertire la tassonomia ESRS ufficiale (Excel EFRAG IG 3) in database popolato.

Crea script `ai-engine/esrs_parser/ingest_taxonomy.py`:

```python
"""
Legge il file Excel EFRAG IG 3 "List of ESRS datapoints.xlsx"
e popola la tabella `esrs_datapoints` nel database.
"""
import pandas as pd
from openpyxl import load_workbook
# Mappa le colonne dell'Excel:
# Column A: Standard (ESRS E1, E2, ...)
# Column B: Disclosure Requirement (DR)
# Column C: Paragraph reference
# Column D: Detailed requirement description
# Column F: Data point name (breve)
# Column G: Data type (monetary, narrative, boolean, percent, volume)
# Column I: Voluntary flag
# Column K: Phase-in info
# Column L: SFDR/P3 reference
```

**Regole di parsing**:
1. Ogni riga dell'Excel = 1 datapoint
2. Usa `standard_ref = f"{colonna_A}-{colonna_B}"` (es. "ESRS E1-6")
3. Per data_type: mappa da testo a enum (`numerical`, `boolean`, `narrative`, `semi-narrative`)
4. Se colonna I = "Yes", `is_voluntary = True`
5. Se colonna K contiene "phase-in", estrai anno

**Output**: Script popola DB. Dopo esecuzione, tabella `esrs_datapoints` contiene ~1.100 records.

---

### Step 6: NLP Parser — Mappa Descrizioni ESRS a Domini Aziendali

**Obiettivo**: Addestrare/fine-tune un modello NLP che mappa i datapoint ESRS (testo legalese) al contesto specifico di un'azienda.

Crea `ai-engine/esrs_parser/esrs_nlp_mapper.py`:

```python
"""
Usa un LLM (GPT-4o o Claude 3.5 Sonnet) per:
1. Prendere in input: il testo di un Disclosure Requirement ESRS
2. Prendere in input: il profilo dell'azienda (settore NACE, attività, dimensioni)
3. Output: una lista di datapoint ESRS rilevanti per quell'azienda
"""
from openai import OpenAI
from anthropic import Anthropic

SYSTEM_PROMPT = """
Sei un esperto di conformità CSRD. Il tuo compito è:
1. Ricevere un Disclosure Requirement ESRS (testo legale EU)
2. Ricevere il profilo aziendale (settore, attività, dimensioni, paesi)
3. Determinare se QUESTO specifico datapoint è applicabile
4. Per ogni datapoint applicabile, suggerire:
   - Dove trovare i dati nell'azienda (ERP, HR, procurement, etc.)
   - Unità di misura
   - Difficoltà di raccolta (1-5)
   - Se è high-priority

Output formato JSON:
{
  "applicable": true/false,
  "confidence": 0.0-1.0,
  "data_source_suggestion": "ERP module X",
  "difficulty": 3,
  "priority": "high",
  "rationale": "Breve spiegazione"
}
"""
```

**Endpoint API**: POST `/api/v1/ai/esrs-mapper`
- Input: `{ company_id, sector, activities, countries }`
- Output: lista di datapoint con applicabilità.

**Cache strategy**: I risultati di mappatura vengono cached per 30 giorni (la tassonomia non cambia spesso).

---

### Step 7: Gap Analysis Automatica

**Obiettivo**: Confrontare i datapoint ESRS obbligatori per l'azienda con i dati già presenti nel sistema e identificare i gap.

Crea `ai-engine/esrs_parser/gap_analyzer.py`:

```python
"""
Prende:
- Lista di datapoint ESRS obbligatori per questa azienda (da Step 6)
- Dati già presenti in emissions_data, materiality_scores, company_context
Output:
- Gap analysis strutturata
"""
```

**Logica**:
1. Per ogni datapoint obbligatorio, controlla se esiste un record nei dati aziendali
2. Classifica:
   - `COMPLETE`: dato presente e verificato
   - `PARTIAL`: dato presente ma non verificato/non completo
   - `MISSING`: dato assente
3. Genera una `Gap Analysis Matrix` visibile nel frontend

**Output API**: GET `/api/v1/assessment/gap-analysis?company_id=X`
```json
{
  "total_required": 320,
  "complete": 45,
  "partial": 120,
  "missing": 155,
  "completion_percentage": 14,
  "gaps_by_standard": {
    "ESRS E1": { "required": 80, "complete": 20, "partial": 40, "missing": 20 },
    ...
  },
  "priority_actions": [
    {"datapoint": "Gross Scope 1 GHG", "priority": "critical", "effort": "medium"},
    ...
  ]
}
```

---

## FASE 2 — DOUBLE MATERIALITY ENGINE

---

### Step 8: Valutazione di Contesto Aziendale

**Obiettivo**: Creare un questionario AI-adattivo che raccoglie il contesto dell'azienda per la doppia materialità.

Crea `backend/app/services/context_questionnaire.py`:

```python
"""
Questionario dinamico generato da AI in base a:
- Settore NACE
- Dimensioni azienda
- Paesi operativi
- Tipologia di attività

Regole:
1. Prima fase (statica): settore, dimensioni, fatturato, dipendenti, paesi
2. Seconda fase (AI-generata): domande specifiche sul settore
   - Se manifatturiero: "Utilizzi sostanze chimiche pericolose nei processi produttivi?"
   - Se ufficio: "Quanti dei tuoi fornitori sono extra-EU?"
   - Se logistica: "Quale % della flotta è elettrica?"
3. Terza fase: mappatura value chain upstream/downstream
"""
```

**Frontend**: Componente `QuestionarioContext` con wizard step-by-step:
1. Basic info (form)
2. Value chain map (interactive diagram dove l'utente clicca e inserisce fornitori/clienti)
3. Stakeholder identification
4. Sector-specific AI questions

**Output**: Popola tabella `company_context`.

---

### Step 9: Identificazione IRO (Impacts, Risks, Opportunities)

**Obiettivo**: Generare la lista di potenziali IRO basata sul contesto aziendale + database di IRO predefiniti per settore.

Crea `ai-engine/materiality_engine/iro_generator.py`:

```python
"""
Architettura:
1. IRO Database predefinito: ~500 IRO template organizzati per
   - Settore NACE (sezione A-U)
   - Sotto-categoria ESRS (E1-G1)
   - Tipo (impact/risk/opportunity)
   
2. AI Generator per IRO specifici:
   Usa il contesto aziendale (value chain, stakeholder, geografia)
   per generare IRO aggiuntivi custom con:
   - Descrizione
   - Tipo
   - Topic ESRS collegato
   - Severità potenziale (1-5)
   - Probabilità (1-5)
   
3. Scoring iniziale automatico basato su:
   - Benchmark di settore (aziende comparabili)
   - Dati macroeconomici (es. carbon price trends per rischi finanziari)
   - Location geografica (es. water stress per E3)
"""
```

**Algoritmo generazione**:
```
Input: company_context (settore, paesi, attività, stakeholder)
Output: List<IRO>

Per ogni ESRS topic (E1-G1):
  IRO_settore = IRO_DATABASE.filter(sector=company.sector, topic=ESRS_topic)
  IRO_AI = LLM.generate(company_context, ESRS_topic, examples=IRO_settore)
  Lista_finale = merge(IRO_settore, IRO_AI)
  Applica scoring initiale
  Return lista_finale
```

**Endpoint API**: POST `/api/v1/assessment/iros/generate`

---

### Step 10: Questionario Doppia Materialità AI-Adattivo

**Obiettivo**: Guida interattiva dove l'utente valuta ogni IRO su scala, portata, irreversibilità e probabilità.

Crea `frontend/src/app/assessment/materiality/page.tsx`:

```typescript
// Componente interattivo che mostra un IRO alla volta
// L'utente valuta 4 dimensioni su scala 1-5:
// Impact: Scale, Scope, Irremediability, Likelihood
// Financial: Magnitude, Likelihood

// AI-adattivo significa:
// - Se l'utente valuta "Scale = 5" per un IRO su emissioni,
//   la AI fa domande di approfondimento:
//   "Hai considerato anche l'impatto sulla catena di fornitura?"
// - Se l'utente dà punteggi molto bassi, la AI può chiedere
//   "Confermi? Dati di settore suggeriscono una probabilità maggiore"
// - Dopo ogni 10 valutazioni, la AI mostra un pattern analysis
```

**Backend**: `ai-engine/materiality_engine/scoring_engine.py`:

```python
def calculate_materiality_scores(assessment_id) -> dict:
    """
    1. Prende tutte le valutazioni IRO per questo assessment
    2. Calcola:
       - Impact Score = (Scale * 0.3 + Scope * 0.3 + Irremediability * 0.2 + Likelihood * 0.2)
       - Financial Score = (Magnitude * 0.6 + Likelihood * 0.4)
       - Double Materiality Score = max(Impact, Financial)
    3. Threshold: se Double Materiality Score >= 3.0 -> IS_MATERIAL
    4. Salva in materiality_scores
    5. Calcola anche settori ESRS applicabili (se almeno 1 IRO materiale per topic)
    """
```

**Output**: Matrice di materialità visualizzata come scatter plot (Impact vs Financial) con 4 quadranti.

---

### Step 11: Report di Doppia Materialità

**Obiettivo**: Generare il documento di doppia materialità conforme agli ESRS.

Crea `ai-engine/materiality_engine/materiality_report.py`:

```python
"""
Genera la sezione del report CSRD sulla doppia materialità:
ESRS 2 IRO-1: Description of the process to identify and assess
ESRS 2 IRO-2: Disclosure Requirements in ESRS covered by the undertaking

Struttura output (dict pronto per report generator):
{
  "section": "ESRS 2 IRO-1",
  "content": "La società ha condotto una valutazione di doppia materialità...",
  "tables": [{
    "title": "Material IROs identified",
    "headers": ["Topic", "IRO", "Impact Score", "Financial Score", "Material"],
    "rows": [...]
  }],
  "methodology_narrative": "La metodologia segue EFRAG IG 1..."
}
"""
```

Usa il LLM per trasformare i dati numerici in narrativa conforme: passi la matrice di punteggi e il LLM genera la descrizione testuale richiesta dagli ESRS.

---

## FASE 3 — CARBON FOOTPRINT CALCULATOR

---

### Step 12: GHG Protocol Scope 1 Calculator

**Obiettivo**: Calcolo emissioni Scope 1 (emissioni dirette).

Crea `ai-engine/carbon_calculator/scope1.py`:

```python
"""
Scope 1: Direct emissions from owned/controlled sources

Categorie:
1. Stationary combustion (gas naturale, gasolio, biomassa per riscaldamento)
2. Mobile combustion (veicoli aziendali)
3. Fugitive emissions (refrigeranti, gas serra da processi)
4. Process emissions (produzione industriale)

Calcolo: Activity_Data × Emission_Factor

Activity_Data input dall'utente:
- Consumo gas naturale (kWh o m³)
- Consumo gasolio riscaldamento (litri)
- km percorsi per tipo veicolo (diesel, benzina, elettrico)
- Carica refrigerante (kg di R410A, R134a, etc.)
- Produzione industriale (tonnellate di prodotto X)

Emission Factors sources (da integrare):
- DEFRA UK (2025): factors per UK
- EPA US (2025): factors per US
- ISPRA per Italia
- IPCC 2025 Tier 1 defaults
- Ecoinvent 3.10 (per processi industriali)

Output: tCO2eq totali Scope 1, breakdown per categoria
"""
```

**Endpoints API**:
- GET `/api/v1/emissions/factors?scope=1&country=IT` — lista fattori di emissione
- POST `/api/v1/emissions/calculate/scope1` — calcola emissioni
- POST `/api/v1/emissions/save` — salva nel DB

---

### Step 13: GHG Protocol Scope 2 Calculator

**Obiettivo**: Calcolo emissioni Scope 2 (energia elettrica acquistata).

Crea `ai-engine/carbon_calculator/scope2.py`:

```python
"""
Scope 2: Indirect emissions from purchased electricity, steam, heating, cooling

Due approcci (entrambi richiesti da ESRS E1-6):
1. Location-based: Emission_Factor × kWh (media rete nazionale)
2. Market-based: Emission_Factor × kWh (contratto fornitore specifico)

Per la PMI:
- Input: consumo elettrico annuo (kWh) da bolletta
- Input opzionale: paese, fornitore, tipo contratto (es. green tariff)
- Output: tCO2eq location-based e market-based

Emission Factors:
- AIE/Eurostat: fattori rete per paese EU
- AIB Residual Mix: per market-based
- GHC Protocol default factors
"""
```

---

### Step 14: GHG Protocol Scope 3 Calculator (15 Categorie)

**Obiettivo**: Calcolo Scope 3 per tutte le 15 categorie rilevanti per PMI.

Crea `ai-engine/carbon_calculator/scope3.py`:

```python
"""
Scope 3: All other indirect emissions

Per PMI, le categorie più rilevanti (in ordine):
1. Purchased goods and services (SPEND-BASED: €speso × emission_factor per settore)
2. Capital goods (stessa logica di Cat 1)
3. Fuel and energy related activities (WTT emissions)
4. Upstream transportation and distribution (tkm × factor)
5. Waste generated in operations (tonnellate × factor per tipo rifiuto)
6. Business travel (km × factor per mezzo)
7. Employee commuting (distanza media × dipendenti × factor)
8. Upstream leased assets (se applicabile)
9. Downstream transportation (se vendono a distributori)
10. Processing of sold products (se applicabile)
11. Use of sold products (per prodotti che consumano energia)
12. End-of-life of sold products
13. Downstream leased assets
14. Franchises
15. Investments (per banche/assicurazioni)

Per ogni categoria:
- Metodo consigliato per PMI: spend-based (facile, dati da contabilità)
- Metodo avanzato: supplier-specific (dati reali dai fornitori)

Calcolo: Spend_in_EUR × Emission_Factor_per_EUR (settore-specifico)
"""
```

**Matrice emission factors per settore**:
```python
# Fonte principale: EXIOBASE 3 + Ecoinvent 3.10
# Aggregata per NACE 2-digit
EMISSION_FACTORS = {
    "C10": {"name": "Food products", "factor": 0.45, "unit": "kgCO2e/EUR"},
    "C20": {"name": "Chemicals", "factor": 0.89, "unit": "kgCO2e/EUR"},
    "C26": {"name": "Computer/Electronic", "factor": 0.12, "unit": "kgCO2e/EUR"},
    "M69": {"name": "Legal/Accounting", "factor": 0.05, "unit": "kgCO2e/EUR"},
    # ... tutti i codici NACE
}
```

---

### Step 15: Data Collection Automation System

**Obiettivo**: Raccogliere dati automaticamente da fonti esterne.

Crea `ai-engine/carbon_calculator/data_collector.py`:

```python
"""
Sistema di raccolta automatica dati:

1. Integrazione XERO/QuickBooks API:
   - Legge spese per categoria contabile
   - Mappa a codici NACE per calcolo spend-based Scope 3 Cat 1

2. Upload bollette (AI OCR):
   - L'utente carica PDF bolletta elettrica/gas
   - AI estrae: fornitore, consumo kWh, periodo, costo
   - Popola automaticamente campi Scope 1 e 2

3. HR integration:
   - Numero dipendenti, full-time/part-time
   - Per commuting survey (opzionale)

4. Fleet management:
   - Se l'azienda ha veicoli, km totali per tipo carburante

5. Utility provider API:
   - Connessione diretta a fornitore energia per dati reali
"""
```

**Frontend**: Drag-and-drop per upload PDF. Tabella che mostra dati estratti con possibilità di modifica manuale.

---

### Step 16: AI Validation Engine per Dati Emissioni

**Obiettivo**: Validare i dati inseriti con AI, rilevare anomalie.

Crea `ai-engine/carbon_calculator/validation_engine.py`:

```python
"""
Controlli automatici di validità:

1. Range check: se una PMI con 50 dipendenti dichiara
   10.000 tCO2 Scope 1, probabilmente è un errore
   (la mediana per 50 dipendenti servizi è ~50 tCO2)

2. Year-over-year comparison: se lo Scope 1 varia +/-30%
   rispetto all'anno prima, chiedi spiegazione

3. Sector benchmark: confronta con aziende simili
   Database di benchmark aggregato (anonimizzato)

4. Missing data detection: se l'azienda ha veicoli aziendali
   ma non ha inserito dati Scope 1 mobile combustion, alert

5. Unit consistency: kWh vs MWh, ton vs kg, EUR vs kEUR
"""
```

**Machine Learning**: Usa un modello (RandomForest o XGBoost) addestrato su dati sintetici di PMI per predire i range attesi per settore/dimensione. Se i dati inseriti sono fuori dal range predetto (deviazione > 3σ), scatta alert.

---

## FASE 4 — REPORT GENERATION ENGINE

---

### Step 17: Template Engine per Report CSRD

**Obiettivo**: Creare il motore di template per report CSRD.

Crea `ai-engine/report_generator/template_engine.py`:

```python
"""
Architettura template:

1. Template base XHTML (struttura del report):
   - Copertina (logo azienda, titolo, periodo)
   - Sezione 1: General Information (ESRS 1 & 2)
   - Sezione 2: Environmental (E1-E5) - solo se materiale
   - Sezione 3: Social (S1-S4) - solo se materiale
   - Sezione 4: Governance (G1)
   - Dichiarazione di conformità
   - Note e assurance

2. Ogni sezione ha sottosezioni fisse:
   - Governance
   - Strategy
   - IRO Management
   - Metrics & Targets

3. Sistema a blocchi:
   Ogni blocco = {id, standard_ref, content_html, xbrl_tags}
   I blocchi sono ordinati per standard_ref + paragraph_ref
"""
```

**Struttura template in memory**:
```python
class ReportTemplate:
    sections: list[ReportSection]
    xbrl_taxonomy_uri: str = "https://xbrl.efrag.org/esrs-set1-2023"
    language: str = "en"  # o "it", "de", "fr", "es"

class ReportSection:
    standard_ref: str  # "ESRS E1"
    title: str
    disclosure_requirements: list[DisclosureRequirement]
    blocks: list[ContentBlock]

class ContentBlock:
    id: str
    datapoint_refs: list[str]  # es. ["ESRS E1-6.44(a)"]
    content_html: str  # HTML renderizzato
    xbrl_tags: list[XBRLTag]  # per iXBRL
```

---

### Step 18: AI Narrativa Generator

**Obiettivo**: Generare il testo narrativo del report usando LLM.

Crea `ai-engine/report_generator/narrative_generator.py`:

```python
"""
Per ogni Disclosure Requirement narrativo (es. "Describe the 
governance structure for managing climate-related impacts"),
usa un LLM per generare testo professionale e conforme.

Input:
- Il datapoint ESRS (testo legale completo)
- I dati strutturati dell'azienda
- I risultati della doppia materialità
- Il report dell'anno precedente (se esiste)

Output:
- Testo narrativo professionale
- In lingua EU richiesta
- Con riferimenti incrociati ad altre sezioni

Prompt engineering:
- System prompt: "Sei un consulente senior di sostenibilità con
  15 anni di esperienza in reportistica CSRD. Scrivi in modo
  professionale, preciso, verificabile."
- Few-shot: dai 3 esempi di reporting ESRS da aziende reali
- Constraints: max 300 parole per paragrafo, cita sempre le fonti
"""
```

**Anti-hallucination layer**:
```python
def validate_narrative(narrative: str, datapoint_ref: str, company_data: dict) -> bool:
    """
    1. Check che ogni claim numerico corrisponda ai dati reali
    2. Check che non ci siano riferimenti a normative non applicabili
    3. Check che la lingua sia conforme (es. no "maybe", "might" per dati certi)
    4. Se fallisce, rigenera con constraints più stretti
    """
```

---

### Step 19: Tabella Dati e Grafici Automatici

**Obiettivo**: Generare tabelle ESRS-compliant e grafici interattivi.

Crea `ai-engine/report_generator/table_generator.py`:

```python
"""
Ogni Disclosure Requirement quantitativo richiede una tabella.
Le tabelle ESRS hanno formati specifici per ogni datapoint.

Esempio ESRS E1-6 Tabella GHG:
+------------------+--------------+-------------+
| GHG Emissions    | Year N-1     | Year N      |
+------------------+--------------+-------------+
| Scope 1 (tCO2e)  | 120          | 105         |
| Scope 2 location | 80           | 75          |
| Scope 2 market   | 45           | 30          |
| Scope 3 total    | 450          | 420         |
| Total            | 650          | 600         |
+------------------+--------------+-------------+

Generazione:
1. Template HTML per ogni tipo tabella
2. Popola con dati da emissions_data
3. Applica formattazione iXBRL
4. Se richiesto, aggiungi grafico (Chart.js o Recharts)
"""
```

**Tipi tabella supportati**:
- Standard: GHG, Energy, Water, Waste, Workforce
- Comparative: N vs N-1
- Multi-year: ultimi 3-5 anni
- Breakdown: per paese/settore/subsidiary

---

### Step 20: iXBRL Tagging Engine

**Obiettivo**: Implementare tagging iXBRL conforme alla tassonomia ESRS.

Crea `ai-engine/report_generator/ixbrl_tagger.py`:

```python
"""
iXBRL = Inline XBRL = XHTML + tag XML embedded.

Ogni datapoint nel report deve essere "taggato" con l'elemento
XBRL corrispondente dalla tassonomia ESRS.

Libreria: Openfiling Conix (open source) + Arelle (validazione)

Processo:
1. Prendi il report XHTML generato
2. Per ogni datapoint, individua il tag HTML che contiene il valore
   (es. <span class="ghg-value">105</span>)
3. Calcola il path XPath al tag
4. Aggiungi l'attributo iXBRL:
   
   <span class="ghg-value"
     data-ixbrl-concept="esrs:E1-6_Scope1"
     data-ixbrl-unit="tCO2eq"
     data-ixbrl-period="2026"
     data-ixbrl-scale="0"
     data-ixbrl-decimals="INF">105</span>
   
5. Converti in formato iXBRL ufficiale:
   
   <ix:nonFraction
     name="esrs:E1-6_Scope1"
     unitRef="u_tCO2eq"
     contextRef="c_2026"
     scale="0"
     decimals="INF">105</ix:nonFraction>

Mapping tra datapoint DB e tassonomia XBRL:
- Carica la tassonomia XBRL ESRS (file .xsd + .xml)
- Mappa ogni datapoint DB al suo elemento XBRL
- Usa namespace ESRS
"""

# Endpoint: POST /api/v1/reports/generate-ixbrl
# Input: report_id
# Output: file .xhtml con tagging iXBRL completo
```

---

### Step 21: iXBRL Validator (Arelle Integration)

**Obiettivo**: Validare il report iXBRL generato contro la tassonomia.

Crea `ai-engine/report_generator/ixbrl_validator.py`:

```python
"""
Usa Arelle (open source XBRL validator) come subprocess.

Processo:
1. Genera file .xhtml
2. Chiama:
   arelleCmdLine --file report.xhtml --validate --output report_validation.json
3. Leggi validation.json
4. Se errori:
   - Classifica: FATAL, ERROR, WARNING, INFO
   - Per ogni errore: mostra datapoint, riga, descrizione
   - Suggerisci correzione
5. Se OK: report è certificato come valido per filing
"""
```

**Validazioni**:
- Schematron rules (regole di business ESRS)
- Calculation linkbases (es. Scope1 + Scope2 + Scope3 = Total)
- Unit consistency (non mischiare tCO2 e kgCO2)
- Period consistency (tutti i dati per lo stesso anno fiscale)
- Dimensional correctness (es. breakdown per paese)

---

### Step 22: Export Multi-Formato

**Obiettivo**: Esportare il report in vari formati.

Crea `backend/app/services/export_service.py`:

```python
"""
Formati supportati:
1. iXBRL (XHTML) — formato principale per filing regolatorio
2. PDF — per stampa e condivisione interna
3. XLSX — per analisi dati
4. Word (DOCX) — per bozze e revisioni
5. JSON — per API integration

Librerie:
- xhtml2pdf per PDF (o wkhtmltopdf)
- openpyxl per Excel
- python-docx per Word
"""
```

**Frontend**: Pulsanti "Export" con dropdown formato.

---

## FASE 5 — REGULATORY INTELLIGENCE

---

### Step 23: Web Scraper Regolatorio EU

**Obiettivo**: Monitorare cambiamenti normativi CSRD/ESRS.

Crea `ai-engine/regulatory_intelligence/scraper.py`:

```python
"""
Fonti da monitorare:
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
   - etc.

Tecnologia:
- BeautifulSoup + requests per HTML scraping
- Feed RSS dove disponibile
- API EUR-Lex dove possibile

Output: nuovi record in tabella regulatory_updates
"""
```

---

### Step 24: AI Summarizer per Update Normativi

**Obiettivo**: Riassumere cambiamenti normativi in linguaggio comprensibile per PMI.

Crea `ai-engine/regulatory_intelligence/update_analyzer.py`:

```python
"""
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
   
   Prompt:
   "Riassumi questa modifica normativa CSRD per una PMI italiana
   con 50 dipendenti. Spiega in italiano semplice cosa cambia
   e cosa devono fare."
5. Invia notifica push via email/app alle aziende interessate
"""
```

---

### Step 25: AI Regulatory Advisor

**Obiettivo**: Consigliare all'utente cosa fare in base ai cambiamenti.

Crea `ai-engine/regulatory_intelligence/advisor.py`:

```python
"""
Analizza:
- Regulatory updates attivi
- Profilo azienda (settore, dimensione, paese)
- Gap analysis corrente
- Scadenze imminenti

Output:
- "Task list" priorizzata per il compliance officer
- Allerta scadenze (es. "Tra 60 giorni scade termine filing")
- Suggerimenti (es. "Con questo update, ora devi reportare anche 
  le emissioni refrigeranti - clicca qui per inserire i dati")
"""
```

**Frontend**: Componente "Regulatory Dashboard" con timeline, task list, e notifiche.

---

## FASE 6 — USER EXPERIENCE & SAAS

---

### Step 26: Dashboard Principale

**Obiettivo**: Creare la dashboard principale del prodotto.

Crea `frontend/src/app/dashboard/page.tsx`:

```typescript
// Componenti:

// 1. CSRD Readiness Score
//    - Progress bar: % completamento gap analysis
//    - Colore: rosso (<30%), giallo (30-70%), verde (>70%)

// 2. Emissions Overview
//    - Card con Scope 1,2,3 totali
//    - Sparkline trend (ultimi 3 anni)
//    - Variazione % YoY

// 3. Upcoming Deadlines
//    - Timeline delle prossime scadenze
//    - Codice colore: urgente (<=30gg), prossimo (<=90gg)

// 4. Materiality Matrix Mini
//    - Scatter plot (Impact vs Financial)
//    - Solo 4 quadranti, interattivo

// 5. Quick Actions
//    - "Complete gap analysis"
//    - "Update emissions data"
//    - "Start materiality assessment"
//    - "Generate CSRD report"

// 6. Regulatory Updates
//    - Ultimi 3 update normativi
//    - Badge "new" se non letti

// 7. AI Assistant Chat
//    - Mini chat widget
//    - "Chiedi al tuo advisor CSRD"
//    - Risposte in contesto con i dati aziendali
```

---

### Step 27: Interfaccia Assessment Doppia Materialità

**Obiettivo**: UI interattiva per completare la doppia materialità.

Crea `frontend/src/app/assessment/materiality/page.tsx`:

```typescript
// Layout:
// Left sidebar: lista ESRI topics con check di completamento
// Main content: scheda IRO corrente
// Right panel: AI suggestions, benchmark comparison

// Interazione:
// 1. L'utente seleziona un ESRS topic
// 2. Vede la lista IRO generata per quel topic
// 3. Per ogni IRO, valuta con slider 1-5 per ogni dimensione
// 4. AI mostra "suggerimenti" dinamicamente
// 5. Dopo ogni valutazione, la matrice si aggiorna

// Visualizzazione:
// Matrice di materialità (scatter plot con D3.js o Recharts)
// - Asse X: Impact Materiality Score (1-5)
// - Asse Y: Financial Materiality Score (1-5)
// - Ogni punto = 1 IRO, colore = topic ESRS
// - Linea threshold: (3,3) divide materiale/non materiale
// - Tooltip: nome IRO, punteggi, topic

// AI Assistant embedded (chat):
// Domande tipiche:
// "Perché questo IRO è considerato materiale per il mio settore?"
// "Come si confronta la mia valutazione con i benchmark?"
// "Quali dati devo raccogliere per questo datapoint?"
```

---

### Step 28: Generazione Report Interattivo

**Obiettivo**: Interfaccia per generare, visualizzare e scaricare report.

Crea `frontend/src/app/reports/page.tsx`:

```typescript
// 1. Seleziona reporting year (dropdown)
// 2. "Generate Report" button (triggera pipeline AI)
// 3. Mostra progress:
//    [1/5] Compiling ESRS data...
//    [2/5] Running gap analysis...
//    [3/5] Generating narratives...
//    [4/5] Building tables & charts...
//    [5/5] Tagging iXBRL...
// 4. Anteprima report live (iframe con report XHTML)
// 5. Validation report (errori/warnings/success)
// 6. Download buttons: iXBRL, PDF, XLSX, DOCX
// 7. "Submit for Review" (cambia stato a review)

// Modalità revisione:
// - Commenti (stile Google Docs)
// - Track changes
// - Approvazione finale
```

---

### Step 29: SaaS Infrastructure

**Obiettivo**: Configurazione multi-tenancy, pagamenti e hosting.

**Multi-tenancy**:
```python
# Ogni company_id è un tenant separato
# Tutte le query SQL includono WHERE company_id = current_tenant
# I dati sono isolati a livello applicativo
# Files: /uploads/{company_id}/* separati
```

**Subscriptions** (Stripe):
```python
# Piani:
# - Starter: €149/mese (fino a 50 dipendenti, 1 utente, solo CSRD base)
# - Growth: €299/mese (fino a 100 dipendenti, 3 utenti, full ESRS)
# - Scale: €499/mese (fino a 250 dipendenti, 10 utenti, tutto incluso)
# - Enterprise: €999-1.499/mese (250+ dipendenti, utenti illimitati, API)
```

**Hosting**: 
- Frontend: Vercel (Next.js)
- Backend: Railway / Fly.io (FastAPI container)
- Database: Supabase (PostgreSQL + pgvector)
- AI: OpenAI + Anthropic API (pay-as-you-go)
- Storage: AWS S3 / Supabase Storage (report files)
- CDN: Cloudflare

**CI/CD**:
```yaml
# .github/workflows/deploy.yml
# On push to main:
# 1. Run tests (pytest, jest)
# 2. Build frontend (next build)
# 3. Build backend (docker build)
# 4. Migrate DB (alembic upgrade head)
# 5. Deploy to Railway/Fly.io
```

---

## FASE 7 — TESTING & LAUNCH

---

### Step 30: Testing, Validazione e Go-Live

**Obiettivo**: Test completi e preparazione al lancio.

**Test Suite**:
```python
# backend/tests/

# 1. Unit tests per ogni servizio:
# - test_carbon_calculator.py
# - test_materiality_engine.py
# - test_esrs_parser.py
# - test_ixbrl_tagger.py
# - test_regulatory_scraper.py

# 2. Integration tests:
# - test_api_endpoints.py (tutti gli endpoint)
# - test_database_crud.py

# 3. AI tests:
# - test_llm_output_quality.py (verifica che l'output LLM sia 
#   sempre JSON valido e entro schema definito)
# - test_hallucination.py (verifica che i dati numerici 
#   generati dall'AI corrispondano ai dati reali)

# 4. iXBRL validation tests:
# - test_ixbrl_output_valid.py (usa Arelle per validare)

# 5. Security tests:
# - test_authentication.py
# - test_authorization.py (un utente non vede dati di altro tenant)
# - test_rate_limiting.py
# - test_sql_injection.py

# 6. Performance tests:
# - test_report_generation_speed.py (max 60 secondi per report)
# - test_concurrent_users.py
```

**Ciclo di sviluppo** (per AI):
```
Ogni step deve essere testato prima di passare al successivo.
Se un test fallisce, non procedere oltre.
Segui l'ordine: backfill non permesso.
Non ottimizzare prematuramente, ma non lasciare codice morto.
```

**Checklist pre-lancio**:
```markdown
- [ ] Step 1-5: Fondazione funzionante
- [ ] Step 6-7: ESRS parser + gap analysis OK
- [ ] Step 8-11: Doppia materialità completa
- [ ] Step 12-16: Carbon calculator funzionante
- [ ] Step 17-22: Report generation + iXBRL OK
- [ ] Step 23-25: Regulatory intelligence operativa
- [ ] Step 26-28: Frontend completo
- [ ] Step 29: SaaS infra configurata
- [ ] Tutti i test passano
- [ ] Report iXBRL valido con Arelle
- [ ] Almeno 1 azienda beta tester ha completato il ciclo completo
```

---

## RIEPILOGO ARCHITETTURALE

```
┌──────────────────────────────────────────────────────┐
│                    FRONTEND (Next.js)                 │
│  Dashboard │ Assessment │ Emissions │ Reports │ Settings│
└──────────────────────────────────────────────────────┘
                        │ REST API
┌──────────────────────────────────────────────────────┐
│                  BACKEND (FastAPI Python)             │
│                                                        │
│  Auth     │ Company   │ Assessment  │ Reports  │ Export│
│  Service  │ Service   │ Service     │ Service  │ Srvc  │
│                                                        │
└─────┬────────────────┬───────────────┬────────────────┘
      │                │               │
      ▼                ▼               ▼
┌──────────┐ ┌──────────────┐ ┌────────────────┐
│ PostgreSQL│ │ AI Engine    │ │ External APIs  │
│ +pgvector │ │ (LLM + ML)   │ │ (XERO, Stripe, │
│           │ │              │ │ EU authorities)│
│ - Users   │ │ - ESRS Parser│ │                │
│ - Dpoints │ │ - Materiality│ │                │
│ - Emiss   │ │ - Calculator │ │                │
│ - Reports │ │ - Narratives │ │                │
│ - Updates │ │ - iXBRL      │ │                │
└──────────┘ └──────────────┘ └────────────────┘
```

**Stack tecnologico final**:
| Layer | Tecnologia | Perché |
|-------|-----------|--------|
| Frontend | Next.js 14 + shadcn/ui + Tailwind | Performance, SSR, ecosistema |
| Backend | Python FastAPI | Velocità, async, Pydantic |
| Database | PostgreSQL + pgvector | Embedding search per AI |
| AI/LLM | GPT-4o + Claude 3.5 | Best-in-class per generazione testi |
| iXBRL | Openfiling Conix + Arelle | Open source, standard EU |
| Auth | Supabase/Auth0 | Gestione utenti pronta |
| Payments | Stripe | Subscriptions SaaS |
| Hosting | Vercel + Railway | Scalabilità zero-ops |
| OCR | Tesseract + GPT-4 Vision | Estrazione bollette |
| Emissions | EXIOBASE + Ecoinvent | Fattori emissione standard |
| Monitoring | Sentry + Logtail | Error tracking |
| CI/CD | GitHub Actions | Automazione deploy |

---

*Fine piano. Ogni step è progettato per essere eseguito da un'AI autonomamente.*
*Tempo stimato per completare tutti i 30 step: 10-16 settimane di sviluppo AI continuativo.*
