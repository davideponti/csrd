# CSRD Comply 🚀

**SaaS di conformità CSRD/ESG per PMI Europee.**

Piattaforma completa per la gestione della conformità alla **Corporate Sustainability Reporting Directive (CSRD)** europea. Copre l'intero workflow: dalla raccolta dati aziendali, alla valutazione di doppia materialità, al calcolo dell'impronta carbonio (GHG Protocol Scope 1, 2, 3), fino alla generazione di report conformi ESRS in formato iXBRL.

---

## 📋 Indice

- [Panoramica](#panoramica)
- [Tecnologia](#tecnologia)
- [Quick Start](#quick-start)
- [Struttura del Progetto](#struttura-del-progetto)
- [Funzionalità (30 Step)](#funzionalità-30-step)
  - [Fase 0: Fondazione](#fase-0--fondazione-steps-1-4)
  - [Fase 1: Parse & Mappa ESRS](#fase-1--parse--mappa-esrs-steps-5-7)
  - [Fase 2: Doppia Materialità](#fase-2--doppia-materialità-steps-8-11)
  - [Fase 3: Carbon Footprint Calculator](#fase-3--carbon-footprint-calculator-steps-12-16)
  - [Fase 4: Report Generation Engine](#fase-4--report-generation-engine-steps-17-21)
  - [Fase 5: Regulatory Intelligence](#fase-5--regulatory-intelligence-steps-22-25)
  - [Fase 6: UX & SaaS](#fase-6--user-experience--saas-steps-26-30)
- [Architettura AI Engine](#architettura-ai-engine)
- [API Endpoints](#api-endpoints)
- [Internazionalizzazione (i18n)](#internazionalizzazione-i18n)
- [Variabili d'Ambiente](#variabili-dambiente)
- [Comandi di Sviluppo](#comandi-di-sviluppo)
- [Deployment](#deployment)
- [Sicurezza](#sicurezza)
- [Test](#test)
- [Roadmap](#roadmap)
- [FAQ & Troubleshooting](#faq--troubleshooting)
- [Licenza](#licenza)

---

## Panoramica

CSRD Comply aiuta le PMI europee a:

- ✅ **Valutare la doppia materialità** secondo EFRAG IG 1 (Impatti, Rischi, Opportunità)
- ✅ **Calcolare le emissioni GHG** Scope 1, 2, 3 secondo il GHG Protocol
- ✅ **Generare report CSRD conformi** in formato XHTML + iXBRL
- ✅ **Monitorare aggiornamenti normativi** EU (EUR-Lex, EFRAG, ESMA)
- ✅ **Ottenere un punteggio di readiness** CSRD con gap analysis automatica
- ✅ **Esportare report** in PDF, XLSX, DOCX, JSON, iXBRL

**Target utente:** PMI europee con 10–500 dipendenti che devono conformarsi alla CSRD a partire dal 2025 (ondata 2) e 2026 (ondata 3).

**Valore chiave:** Automazione dell'intera pipeline CSRD — dal questionario di contesto aziendale al report iXBRL validato — con AI generativa e template conformi ESRS.

---

## Tecnologia

| Componente | Tecnologia |
|------------|-----------|
| **Frontend** | Next.js 14 (App Router, TypeScript, Tailwind CSS, shadcn/ui) |
| **Backend** | Python FastAPI (Pydantic v2, SQLAlchemy, Alembic) |
| **AI Engine** | Python modulare (NLP, LLM, calcolo emissioni, report) |
| **Database** | PostgreSQL 16 con pgvector |
| **Autenticazione** | JWT (python-jose) + bcrypt |
| **Infrastruttura** | Docker Compose, Nginx, Terraform (DigitalOcean) |
| **AI/LLM** | OpenAI GPT-4o, Anthropic Claude 3.5 Sonnet |
| **UI Library** | Radix UI, Lucide React, Recharts |
| **i18n** | 8 lingue: 🇮🇹 🇬🇧 🇩🇪 🇫🇷 🇪🇸 🇳🇱 🇸🇪 🇵🇱 |
| **Test** | pytest (86 test, 7 suite), asyncio |

### Dipendenze Backend Principali

```txt
fastapi>=0.115.0       # Framework REST
sqlalchemy>=2.0.0      # ORM PostgreSQL
alembic>=1.13.0        # Migration database
pydantic-settings>=2.0.0  # Config management
python-jose[cryptography]>=3.3.0  # JWT
passlib[bcrypt]>=1.7.4  # Password hashing
openai>=1.0.0          # LLM integration
anthropic>=0.30.0      # Claude API
pandas>=2.0.0          # Data processing
xhtml2pdf>=0.2.13      # PDF export
python-docx>=1.1.0     # DOCX export
reportlab>=4.1.0       # PDF fallback
```

---

## Quick Start

### Prerequisiti

- Python 3.11+
- Node.js 18+
- PostgreSQL 16 (o Docker)
- Git

### 1. Clona il repository

```bash
git clone https://github.com/your-org/csrd-comply.git
cd CSRD-Comply
```

### 2. Backend

```bash
cd backend
python -m venv venv
source venv/bin/activate   # Linux/Mac
# venv\Scripts\activate    # Windows

pip install -r requirements.txt
cp .env.example .env       # Configura le variabili
alembic upgrade head       # Crea le tabelle DB
uvicorn app.main:app --reload
```

### 3. Frontend

```bash
cd frontend
npm install
npm run dev
```

### 4. AI Engine (opzionale)

```bash
cd ai_engine
pip install -r requirements.txt
python cli.py seed              # Carica tassonomia ESRS
python cli.py gap-analysis      # Gap analysis demo
```

### 5. Apri il browser

Visita `http://localhost:3000` — registra un account e inizia l'assessment.

---

## Struttura del Progetto

```
CSRD-Comply/
├── frontend/                      # Next.js 14 Frontend
│   ├── src/
│   │   ├── app/                   # Pages (App Router)
│   │   │   ├── dashboard/         # Dashboard principale
│   │   │   ├── assessment/        # Wizard doppia materialità
│   │   │   ├── assessment/materiality/  # Scoring interattivo + matrice
│   │   │   ├── emissions/         # Carbon footprint calculator
│   │   │   ├── reports/           # Report generation pipeline
│   │   │   ├── settings/          # Profilo azienda
│   │   │   └── auth/              # Login/Register
│   │   ├── components/ui/         # shadcn/ui components
│   │   ├── lib/                   # API client, utilities
│   │   ├── hooks/                 # React hooks (useAuth)
│   │   ├── i18n/                  # Traduzioni (8 lingue)
│   │   └── types/                 # TypeScript interfaces
│   └── public/
│
├── backend/                       # Python FastAPI Backend
│   ├── app/
│   │   ├── api/                   # Route handlers (REST)
│   │   │   ├── auth.py            # Registrazione, login, refresh
│   │   │   ├── companies.py       # Profilo azienda
│   │   │   ├── assessment.py      # Doppia materialità
│   │   │   ├── emissions.py       # Calcolo emissioni
│   │   │   ├── reports.py         # Report generation + export
│   │   │   ├── ai.py              # ESRS NLP mapper
│   │   │   ├── subscriptions.py   # Piani e billing
│   │   │   └── router.py          # Aggregatore router
│   │   ├── core/                  # Config, DB, auth, security
│   │   │   ├── config.py          # Settings (pydantic-settings)
│   │   │   ├── database.py        # SQLAlchemy engine
│   │   │   ├── security.py        # JWT + bcrypt
│   │   │   ├── deps.py            # Dependency injection
│   │   │   ├── multitenancy.py    # Multi-tenant middleware
│   │   │   └── subscriptions.py   # Piani, limiti, features
│   │   ├── models/                # SQLAlchemy models (10 entità)
│   │   ├── schemas/               # Pydantic schemas
│   │   ├── services/              # Business logic
│   │   │   ├── context_questionnaire.py  # Questionario contesto
│   │   │   └── export_service.py         # Export multi-formato
│   │   └── ai/                    # AI modules placeholder
│   ├── alembic/                   # DB migrations
│   ├── tests/                     # 86 test (7 suite)
│   ├── Dockerfile
│   └── requirements.txt
│
├── ai_engine/                     # AI Microservizi Python
│   ├── esrs_parser/               # Fase 1: ESRS Parsing
│   │   ├── ingest_taxonomy.py     # Carica tassonomia ESRS da Excel
│   │   ├── esrs_nlp_mapper.py     # NLP mapper (LLM + fallback rule-based)
│   │   └── gap_analyzer.py        # Gap analysis automatica
│   │
│   ├── materiality_engine/        # Fase 2: Doppia Materialità
│   │   ├── iro_generator.py       # ~120 IRO template per settore NACE
│   │   ├── scoring_engine.py      # Scoring doppia materialità (EFRAG IG 1)
│   │   └── materiality_report.py  # Report conforme ESRS 2 IRO-1/2
│   │
│   ├── carbon_calculator/         # Fase 3: Carbon Footprint
│   │   ├── scope1.py              # Emissioni dirette (GHG Protocol)
│   │   ├── scope2.py              # Dual reporting (location + market)
│   │   ├── scope3.py              # 15 categorie (spend-based)
│   │   ├── data_collector.py      # OCR bollette, API contabilità, CSV
│   │   └── validation_engine.py   # Validazione AI dati emissioni
│   │
│   ├── report_generator/          # Fase 4: Report Generation
│   │   ├── template_engine.py     # Template engine XHTML/iXBRL
│   │   ├── narrative_generator.py # AI narrative (LLM + anti-hallucination)
│   │   ├── table_generator.py     # Tabelle ESRS-compliant 9 tipi
│   │   ├── ixbrl_tagger.py        # Tagging iXBRL (ESRS tassonomia)
│   │   └── ixbrl_validator.py     # Validazione (built-in + Arelle)
│   │
│   ├── regulatory_intelligence/   # Fase 5: Regulatory Intelligence
│   │   ├── scraper.py             # Web scraper EU (EUR-Lex, EFRAG, ESMA)
│   │   ├── update_analyzer.py     # AI summarizer aggiornamenti normativi
│   │   └── advisor.py             # Regulatory advisor personalizzato
│   │
│   └── cli.py                     # CLI runner (seed, ingest, gap-analysis)
│
├── infrastructure/                # Deployment
│   ├── docker-compose.yml         # PostgreSQL + Backend
│   ├── nginx/default.conf         # Reverse proxy, SSL, rate limiting
│   └── terraform/                 # DigitalOcean IaC
│       ├── main.tf
│       ├── variables.tf
│       └── outputs.tf
│
├── docs/                          # Documentazione step-by-step
└── data/                          # Dati seed (tassonomia ESRS)
```

---

## Funzionalità (30 Step)

Tutte le funzionalità sono state sviluppate seguendo un piano di implementazione in 30 step, ciascuno documentato individualmente nella cartella `docs/`.

### Fase 0 — Fondazione (Steps 1-4)

- **Step 1:** Scaffolding del progetto (Next.js 14 + FastAPI + PostgreSQL)
- **Step 2:** Database schema SQLAlchemy (10 entità: companies, users, esrs_datapoints, materiality_assessment, emissions_data, reports, etc.)
- **Step 3:** Backend FastAPI (JWT auth, CORS, CRUD endpoints) con architettura modulare (api/, core/, models/, schemas/, services/)
- **Step 4:** Frontend Next.js 14 (layout con sidebar, pagine dashboard/assessment/emissions/reports/settings/auth)

### Fase 1 — Parse & Mappa ESRS (Steps 5-7)

- **Step 5:** Ingegnerizzazione tassonomia ESRS — parser Excel EFRAG IG 3, ~1.100 datapoint ESRS, 25 topic seed
- **Step 6:** NLP Parser — mappa descrizioni ESRS al contesto aziendale via LLM (GPT-4o / Claude 3.5 Sonnet) con fallback rule-based basato su keyword matching
- **Step 7:** Gap Analysis automatica — confronta datapoint obbligatori vs dati presenti nel sistema, genera priority actions

### Fase 2 — Doppia Materialità (Steps 8-11)

- **Step 8:** Questionario di contesto aziendale — 3 fasi (universale, settoriale, value chain) con domande AI-adattive in 5 aree
- **Step 9:** Identificazione IRO — ~120 IRO template per settore NACE (Impatti, Rischi, Opportunità) con personalizzazione AI
- **Step 10:** Scoring Engine — calcolo doppia materialità secondo EFRAG IG 1 (Impact: Scale×0.3 + Scope×0.3 + Irremediability×0.2 + Likelihood×0.2; Financial: Magnitude×0.6 + Likelihood×0.4)
- **Step 11:** Report di doppia materialità — conforme ESRS 2 IRO-1/IRO-2 con matrice scatter plot e threshold configurabile (es. 2.5/5.0)

### Fase 3 — Carbon Footprint Calculator (Steps 12-16)

- **Step 12:** Scope 1 Calculator — emissioni dirette (combustione stazionaria/mobile, fugitive, processi industriali). Fattori DEFRA UK 2025, EPA US 2025, IPCC AR6 2025
- **Step 13:** Scope 2 Calculator — dual reporting (location-based + market-based). 28 paesi EU con fattori specifici
- **Step 14:** Scope 3 Calculator — tutte le 15 categorie GHG Protocol, metodo spend-based con fattori EXIOBASE 3 + Ecoinvent 3.10
- **Step 15:** Data Collection Automation — OCR bollette (multilingua), integrazione contabilità (XERO/QuickBooks), HR, flotta, CSV upload, transazioni bancarie
- **Step 16:** AI Validation Engine — range check, benchmark settoriale, year-over-year, missing data detection, unit consistency

### Fase 4 — Report Generation Engine (Steps 17-21)

- **Step 17:** Template Engine — architettura a blocchi (CoverPage, Section, DisclosureRequirement, ContentBlock, XBRLTag) per report XHTML/iXBRL
- **Step 18:** AI Narrative Generator — genera testo narrativo CSRD via LLM con anti-hallucination layer (validate_narrative, rigenerazione automatica)
- **Step 19:** Table Generator — 9 tipi tabelle ESRS-compliant (GHG, energy, workforce, comparative, breakdown, custom) con CSS dedicato e dati chart embeddati
- **Step 20:** iXBRL Tagger — tagging XHTML con namespace iXBRL, header context/unit, `<ix:nonFraction>` e `<ix:nonNumeric>`
- **Step 21:** iXBRL Validator — validazione built-in (calcoli, unità, periodi, sintassi) + integrazione Arelle per validazione completa contro tassonomia ESRS

### Fase 5 — Regulatory Intelligence (Steps 22-25)

- **Step 22:** Export Multi-Formato — PDF (con 2 fallback: xhtml2pdf + ReportLab), XLSX (4 fogli: overview, dettaglio, metadati, validation), DOCX, JSON, iXBRL
- **Step 23:** Web Scraper Regolatorio — monitoraggio EUR-Lex, EFRAG, ESMA, CONSOB, BaFin, AMF con rate limiting e deduplicazione
- **Step 24:** AI Summarizer — riassume cambiamenti normativi in linguaggio PMI con classificazione impatto (CRITICAL/MODERATE/INFO)
- **Step 25:** AI Regulatory Advisor — report personalizzato per azienda con task list, deadline alerts, compliance score (0-100)

### Fase 6 — User Experience & SaaS (Steps 26-30)

- **Step 26:** Dashboard Principale — CSRD Readiness Score, emissioni GHG, scadenze, matrice materialità, azioni rapide, aggiornamenti normativi, AI Chat Widget
- **Step 27:** Doppia Materialità Interattiva — layout 3 pannelli (topic sidebar, scoring wizard, AI advisor), matrice scatter plot SVG, report
- **Step 28:** Report Generation Pipeline — frontend a 4 tab (elenco, generazione 5 step, anteprima HTML, validazione), ciclo di revisione (draft → review → final)
- **Step 29:** Multitenancy & Subscriptions — 4 piani (Free €0, Pro €49, Team €149, Enterprise €499), middleware tenant isolation, deploy Nginx + Terraform DigitalOcean
- **Step 30:** Testing & Go-Live — **86 test** suddivisi in 7 suite (carbon calculator, materiality engine, ESRS parser, iXBRL tagger, regulatory scraper, API endpoints, fixtures)

Ciascuno step è documentato approfonditamente nei file `docs/{step}.md` e nei relativi `docs/what_was_done_{step}.md`.

---

## Architettura AI Engine

```
┌─────────────────────────────────────────────────────────────┐
│                     AI ENGINE MODULES                        │
├───────────────┬──────────────┬──────────────┬───────────────┤
│  ESRS Parser  │  Materiality  │   Carbon      │   Report      │
│               │    Engine     │  Calculator   │   Generator   │
├───────────────┼──────────────┼──────────────┼───────────────┤
│ ingest_taxo.. │ iro_generator│ scope1.py     │ template_en.. │
│ esrs_nlp_map. │ scoring_eng. │ scope2.py     │ narrative_g.. │
│ gap_analyzer  │ materiality_ │ scope3.py     │ table_gener.. │
│               │ _report.py   │ data_collec.  │ ixbrl_tagger  │
│               │              │ validation_e. │ ixbrl_valida. │
└───────────────┴──────────────┴──────────────┴───────────────┘
         │              │              │               │
         └──────────────┴──────────────┴───────────────┘
                              │
                              ▼
                 ┌─────────────────────┐
                 │   ReportTemplate     │
                 │  (XHTML + iXBRL)     │
                 └─────────────────────┘
                              │
                 ┌────────────┴────────────┐
                 ▼                         ▼
         ┌──────────────┐         ┌──────────────┐
         │  Export       │         │  Regulatory   │
         │  5 formati    │         │  Intelligence │
         └──────────────┘         └──────────────┘
```

### Flusso Dati AI Engine

1. **ESRS Parser** → Carica la tassonomia ESRS da Excel EFRAG e la mappa al contesto aziendale via NLP
2. **Materiality Engine** → Genera IRO settoriali e calcola il punteggio di doppia materialità
3. **Carbon Calculator** → Calcola emissioni Scope 1, 2, 3 con validazione AI
4. **Report Generator** → Compone il report XHTML/iXBRL con template, narrative AI e tagging
5. **Regulatory Intelligence** → Monitora aggiornamenti normativi e fornisce advisory

---

## API Endpoints

### Autenticazione
| Metodo | Endpoint | Descrizione |
|--------|----------|-------------|
| POST | `/api/v1/auth/register` | Registrazione utente |
| POST | `/api/v1/auth/login` | Login (JWT token) |
| POST | `/api/v1/auth/refresh` | Refresh token |

### Aziende
| Metodo | Endpoint | Descrizione |
|--------|----------|-------------|
| GET | `/api/v1/companies/me` | Profilo azienda corrente |
| PATCH | `/api/v1/companies/me` | Aggiorna profilo |

### Assessment (Doppia Materialità)
| Metodo | Endpoint | Descrizione |
|--------|----------|-------------|
| GET/POST | `/api/v1/assessment/` | Lista/crea assessment |
| GET | `/api/v1/assessment/{id}` | Dettaglio assessment |
| GET/PUT | `/api/v1/assessment/{id}/context` | Contesto aziendale |
| GET | `/api/v1/assessment/{id}/questionnaire` | Questionario |
| GET/POST | `/api/v1/assessment/{id}/iros` | IRO (Impatti/Rischi/Opportunità) |
| POST | `/api/v1/assessment/{id}/scores/generate` | Genera entries scoring |
| GET | `/api/v1/assessment/{id}/scores` | Lista scores |
| PATCH | `/api/v1/assessment/{id}/scores/{score_id}` | Aggiorna score |
| POST | `/api/v1/assessment/{id}/scores/calculate` | Calcola punteggi |
| GET | `/api/v1/assessment/{id}/matrix` | Matrice materialità |
| GET | `/api/v1/assessment/{id}/report` | Report doppia materialità |
| GET | `/api/v1/assessment/{id}/gap-analysis` | Gap analysis |

### Emissioni (Carbon Footprint)
| Metodo | Endpoint | Descrizione |
|--------|----------|-------------|
| GET | `/api/v1/emissions/factors` | Fattori di emissione |
| POST | `/api/v1/emissions/calculate/scope1` | Calcola Scope 1 |
| POST | `/api/v1/emissions/calculate/scope1/process` | Process emissions Scope 1 |
| POST | `/api/v1/emissions/calculate/scope2` | Calcola Scope 2 (dual reporting) |
| POST | `/api/v1/emissions/calculate/scope3` | Calcola Scope 3 (15 categorie) |
| POST | `/api/v1/emissions/save-calculated` | Salva emissioni |
| POST | `/api/v1/emissions/validate` | Validazione AI |
| POST | `/api/v1/emissions/parse-bill` | OCR bolletta |
| GET | `/api/v1/emissions/summary` | Riepilogo per scope |

### Report
| Metodo | Endpoint | Descrizione |
|--------|----------|-------------|
| GET/POST | `/api/v1/reports/` | Lista/crea report |
| GET | `/api/v1/reports/{id}` | Dettaglio report |
| POST | `/api/v1/reports/{id}/generate` | Pipeline generazione (5 step) |
| POST | `/api/v1/reports/{id}/submit-review` | Invia in revisione |
| POST | `/api/v1/reports/{id}/approve` | Approva report |
| GET | `/api/v1/reports/{id}/preview` | Anteprima HTML |
| GET | `/api/v1/reports/{id}/validation` | Validazione iXBRL |
| GET | `/api/v1/reports/{id}/export/{format}` | Export (pdf/xlsx/docx/json/ixbrl) |
| POST | `/api/v1/reports/{id}/export-all` | Export completo |
| GET | `/api/v1/reports/export/formats` | Formati disponibili |

### AI
| Metodo | Endpoint | Descrizione |
|--------|----------|-------------|
| POST | `/api/v1/ai/esrs-mapper` | Mappa singolo datapoint ESRS |
| POST | `/api/v1/ai/esrs-mapper/batch` | Mappa batch (max 50) |
| GET | `/api/v1/ai/esrs-mapper/status` | Cache + provider info |

### Subscriptions
| Metodo | Endpoint | Descrizione |
|--------|----------|-------------|
| GET | `/api/v1/subscriptions/plans` | Piani disponibili |
| GET | `/api/v1/subscriptions/current` | Abbonamento corrente |
| POST | `/api/v1/subscriptions/subscribe` | Attiva/upgrade abbonamento |
| PATCH | `/api/v1/subscriptions/current` | Modifica abbonamento |
| POST | `/api/v1/subscriptions/cancel` | Cancella abbonamento |
| GET | `/api/v1/subscriptions/usage` | Limiti e utilizzo |
| GET | `/api/v1/subscriptions/features` | Feature access check |

### Regulatory Intelligence
| Metodo | Endpoint | Descrizione |
|--------|----------|-------------|
| GET | `/api/v1/regulatory/advisory/{company_id}` | Advisor report completo |
| POST | `/api/v1/regulatory/analyze-update` | Analizza aggiornamento normativo |

---

## Internazionalizzazione (i18n)

Il frontend supporta **8 lingue** con un sistema di traduzione basato su React Context:

| Lingua | Codice | Nativo | Bandiera |
|--------|--------|--------|----------|
| Italiano | `it` | Italiano | 🇮🇹 |
| Inglese | `en` | English | 🇬🇧 |
| Tedesco | `de` | Deutsch | 🇩🇪 |
| Francese | `fr` | Français | 🇫🇷 |
| Spagnolo | `es` | Español | 🇪🇸 |
| Olandese | `nl` | Nederlands | 🇳🇱 |
| Svedese | `sv` | Svenska | 🇸🇪 |
| Polacco | `pl` | Polski | 🇵🇱 |

La lingua predefinita è **italiano**. Le traduzioni sono gestite tramite il componente `<LanguageProviderWrapper>` e il selettore `<LanguageSwitcher>`, accessibile dall'interfaccia utente.

---

## Variabili d'Ambiente

Crea un file `.env` nella directory `backend/` con le seguenti variabili:

| Variabile | Default | Descrizione |
|-----------|---------|-------------|
| `DATABASE_URL` | `postgresql://postgres:postgres@localhost:5432/csrd_comply` | Connessione PostgreSQL |
| `SECRET_KEY` | `change-me-in-production` | Chiave segreta per JWT |
| `ALGORITHM` | `HS256` | Algoritmo JWT |
| `ACCESS_TOKEN_EXPIRE_MINUTES` | `60` | Scadenza token (minuti) |
| `OPENAI_API_KEY` | `""` | API key OpenAI GPT-4o |
| `ANTHROPIC_API_KEY` | `""` | API key Anthropic Claude |
| `CORS_ORIGINS` | `["http://localhost:3000"]` | Origini CORS consentite |
| `ENVIRONMENT` | `development` | Ambiente (development/production) |
| `ENABLE_MULTITENANCY` | `False` | Abilita multi-tenancy |
| `DEPLOYMENT_DOMAIN` | `csrdcomply.io` | Dominio di deploy |

---

## Comandi di Sviluppo

```bash
# Backend
cd backend
uvicorn app.main:app --reload                    # Avvia server (dev)
alembic upgrade head                              # Applica migrazioni
alembic revision --autogenerate -m "desc"         # Crea migrazione
python -m pytest tests/ -v                        # Esegui test

# Frontend
cd frontend
npm run dev                                       # Avvia Next.js (dev)
npm run build                                     # Build produzione
npm run lint                                      # Linting

# AI Engine
cd ai_engine
python cli.py seed                                # Seed tassonomia ESRS
python cli.py ingest                              # Ingest datapoint
python cli.py gap-analysis                        # Gap analysis demo

# Docker
cd infrastructure
docker-compose up -d                              # Avvia servizi
docker-compose logs -f                            # Log in tempo reale

# Infrastructure
cd infrastructure/terraform
terraform init                                    # Init Terraform
terraform plan                                    # Piano di deploy
terraform apply                                   # Deploy su DigitalOcean
```

---

## Deployment

### Docker Compose (Sviluppo)

```bash
cd CSRD-Comply/infrastructure
docker-compose up -d
```

### Produzione (DigitalOcean + Terraform)

```bash
cd CSRD-Comply/infrastructure/terraform
terraform init
terraform apply
```

### Configurazione Nginx

Il reverse proxy Nginx gestisce:

- **HTTPS redirect** — HTTP → 301 HTTPS
- **SSL termination** — TLSv1.2/1.3
- **Rate limiting** — 100 req/min per IP, 500 req/min per tenant
- **Cache static assets** — 1 anno
- **Health check** — `/health`
- **API subdomain** — `api.csrdcomply.io`

### Piani di Abbonamento

| Piano | Prezzo/mese | Utenti | Report/anno | AI | iXBRL |
|-------|-------------|--------|-------------|----|-------|
| Free | €0 | 1 | 1 | No | No |
| Pro | €49 | 3 | 10 | Sì | Sì |
| Team | €149 | 10 | Illimitati | Sì | Sì |
| Enterprise | €499 | Illimitati | Illimitati | Sì | Sì |

---

## Sicurezza

La piattaforma implementa diversi livelli di sicurezza:

- **Autenticazione JWT** — Token con scadenza configurabile (default 60 min), refresh token
- **Password hashing** — bcrypt via passlib
- **CORS** — Whitelist configurabile delle origini consentite
- **Rate Limiting** — Nginx limita a 100 req/min per IP, 500 req/min per tenant
- **Multi-tenancy** — Isolamento dati per tenant attraverso schema PostgreSQL dedicato
- **Anti-hallucination** — Layer di validazione per contenuti generati dall'AI (narrative, dati emissioni)
- **SSL/TLS** — Terminazione TLSv1.2/1.3 in produzione
- **Token Rotation** — JWT refresh invalida il token precedente (`token_version` incrementale)
- **User Enumeration Prevention** — Messaggi d'errore generici su registrazione/login
- **HttpOnly Cookies** — JWT salvato in cookie HttpOnly (XSS-safe), con fallback Authorization header
- **CSP Headers** — Content-Security-Policy configurato lato backend

---

## Test

Il progetto include **86 test** suddivisi in 7 suite:

```bash
cd CSRD-Comply/backend
pip install -r requirements.txt
pip install pytest httpx
python -m pytest tests/ -v
```

### Suite di Test

| Suite | File | Test | Copertura |
|-------|------|------|-----------|
| Carbon Calculator | `tests/test_carbon_calculator.py` | 30 | Scope 1, 2, 3 |
| Materiality Engine | `tests/test_materiality_engine.py` | 11 | IRO, Scoring, Report |
| ESRS Parser | `tests/test_esrs_parser.py` | 10 | Taxonomy, NLP, Gap Analysis |
| iXBRL | `tests/test_ixbrl_tagger.py` | 9 | Tagger, Validator |
| Regulatory | `tests/test_regulatory_scraper.py` | 10 | Scraper, Analyzer, Advisor |
| API Integration | `tests/test_api_endpoints.py` | 16 | Auth, Companies, Reports, Subs |
| Fixtures | `tests/conftest.py` | — | DB isolato, fixtures |

La configurazione pytest è in `backend/pytest.ini`:

```ini
[pytest]
testpaths = tests
pythonpath = .. ../ai_engine .
asyncio_mode = auto
```

---

## Roadmap

### 🎯 Completato

- ✅ **30 step** del piano di implementazione completati
- ✅ **86 test** — copertura completa di tutte le funzionalità core
- ✅ **8 lingue** — internazionalizzazione completa del frontend
- ✅ **AI Engine** — 4 moduli (ESRS, Materialità, Carbonio, Report)
- ✅ **Deploy** — Docker Compose + Terraform per DigitalOcean

### 🔮 Prossimi sviluppi

- [ ] Integrazione SSO (SAML/OIDC) per Enterprise
- [ ] Dashboard con widget personalizzabili drag-and-drop
- [ ] Comparazione benchmark settoriali in tempo reale
- [ ] Supporto ESRS 2025 aggiornamenti tassonomia
- [ ] Pipeline CI/CD (GitHub Actions)
- [ ] Monitoraggio performance con Sentry/Datadog
- [ ] App mobile (React Native)

### 🛡️ Security Audit (Maggio 2026)

- ✅ **C1 — API Keys rimosse dal repository**: `.env` aggiunto a `.gitignore`
- ✅ **C2 — SECRET_KEY malformata**: Sostituita con chiave singola valida
- ✅ **C3 — --reload rimosso dal Dockerfile**: Ora usa `--workers 4`
- ✅ **C4 — JWT in localStorage**: Migrato a HttpOnly cookie, frontend aggiornato
- ✅ **C5 — Cache in-memory**: Redis per AI mapper cache con TTL configurabile
- ✅ **C6 — User Enumeration**: Messaggi d'errore generici su registrazione
- ✅ **C7 — JWT Token Rotation**: Refresh token invalida il precedente
- ✅ **C8 — Subscription Model**: Colonne mancanti aggiunte al DB + alias `plan`/`tier`
- ✅ **C9 — Rate Limiting**: SlowAPI integrato nel backend
- ✅ **C10 — CSP Headers**: Content-Security-Policy lato backend

---

## FAQ & Troubleshooting

### Come avviare il progetto in locale?

Segui la sezione [Quick Start](#quick-start). Assicurati di avere PostgreSQL in esecuzione e di aver configurato il file `.env`.

### Errore di connessione al database?

Verifica che PostgreSQL sia in esecuzione e che `DATABASE_URL` nel `.env` sia corretto. Con Docker: `docker-compose up -d` avvia PostgreSQL automaticamente.

### I test non passano?

Assicurati di aver installato tutte le dipendenze (`pip install -r requirements.txt`) e di eseguire i test dalla directory `backend/`. Alcuni test richiedono la presenza dei moduli `ai_engine` nel PYTHONPATH (configurato in `pytest.ini`).

### Come aggiungere una nuova lingua?

1. Crea un nuovo file in `frontend/src/i18n/translations/{codice}.ts`
2. Aggiungi la lingua in `frontend/src/i18n/languages.ts`
3. Importa il file delle traduzioni nel `LanguageContext.tsx`

### Come contribuire?

1. Fai fork del repository
2. Crea un branch feature (`git checkout -b feature/nuova-funzionalità`)
3. Fai commit delle modifiche (`git commit -m 'Aggiunta nuova funzionalità'`)
4. Pusha al branch (`git push origin feature/nuova-funzionalità`)
5. Apri una Pull Request

---

## Licenza

Proprietaria. Tutti i diritti riservati.

---

## Status del Progetto

✅ **Completati tutti i 30 step del piano di implementazione.**

- [x] Step 1-4: Fondazione (Scaffolding, DB, Backend, Frontend)
- [x] Step 5-7: Parsing ESRS + Gap Analysis
- [x] Step 8-11: Doppia Materialità (Context, IRO, Scoring, Report)
- [x] Step 12-16: Carbon Footprint (Scope 1, 2, 3, Data Collection, Validation)
- [x] Step 17-21: Report Generation (Template, Narrative, Tables, iXBRL, Validation)
- [x] Step 22-25: Regulatory Intelligence (Export, Scraper, Summarizer, Advisor)
- [x] Step 26-30: UX & SaaS (Dashboard, Materialità Interattiva, Pipeline, Multitenancy, 86 Test)

---

📄 **Documentazione completa disponibile in `docs/`** — ogni step implementativo è documentato in dettaglio con file `.md` separati.

🐛 **Trovato un bug? Segnalalo via issue su GitHub.**
