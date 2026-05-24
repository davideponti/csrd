# What Was Done — Step 28 & 29

## Step 28 — Report Generation Pipeline

### Backend (reports.py)
- Aggiunti endpoint per la pipeline di generazione a 5 step:
  - `POST /reports/{id}/generate` — Esegue step 1-5 (compile data, gap analysis, narratives, tables/charts, iXBRL tagging)
  - `POST /reports/{id}/submit-review` — Passaggio da draft a review
  - `POST /reports/{id}/approve` — Passaggio da review a final
  - `GET /reports/{id}/preview` — Anteprima HTML del report
  - `GET /reports/{id}/validation` — Risultati validazione iXBRL
- Aggiunte funzioni helper: `_compile_esrs_data()`, `_run_gap_analysis()`, `_generate_narratives()`, `_build_tables_charts()`, `_tag_ixbrl()`

### Frontend (reports/page.tsx)
- Riscritta completamente con:
  - 4 tabs: Elenco Report, Generazione, Anteprima, Validazione
  - Pipeline di generazione sequenziale con progress bar e 5 step visuali
  - Ciclo di revisione: submit for review + approvazione con dialog commenti
  - Anteprima report in iframe (HTML preview con dati GHG)
  - Risultati validazione iXBRL con warning dettagliati
  - Pulsanti export a 5 formati (PDF, iXBRL, XLSX, DOCX, JSON)
  - Badge di stato: Bozza (warning), In Revisione (info), Finale (success)

## Step 29 — Multitenancy, Subscriptions & Deployment

### Backend
- **multitenancy.py** (NEW):
  - `TenantContext` — Context thread-safe per tenant_id e schema
  - `MultitenancyMiddleware` — Middleware FastAPI per isolamento dati
  - `apply_tenant_filter()` — Filtro automatico query SQLAlchemy
  - `get_current_company()` — Dependency per azienda corrente
  - Feature flags basati su piano: AI, iXBRL, multi-user, ecc.

- **subscriptions.py** (NEW):
  - 4 piani: Free (€0), Pro (€49), Team (€149), Enterprise (€499)
  - `SubscriptionService` — Upgrade, downgrade, prorated amount
  - `UsageTracker` — Report count, user count, storage usage
  - Config completo: features, limits, prices

- **subscriptions.py API** (NEW):
  - 9 endpoint: plans list, current sub, subscribe, cancel, reactivate, usage, features

- **config.py** — Aggiunte: `ENABLE_MULTITENANCY`, `DEFAULT_SCHEMA`, `DEPLOYMENT_DOMAIN`, `DEPLOYMENT_SSL_ENABLED`

- **router.py** — Aggiunto `subscriptions.router`

- **main.py** — Aggiunto `MultitenancyMiddleware` opzionale

### Infrastructure
- **nginx/default.conf** (NEW):
  - Reverse proxy con HTTPS redirect
  - SSL termination TLSv1.2/1.3
  - Rate limiting: 100 req/min per IP, 500 req/min per tenant
  - Cache static assets, security headers, CORS
  - API subdomain configuration

- **terraform/main.tf** (NEW):
  - DigitalOcean PostgreSQL 16 (2GB RAM)
  - App Platform: backend (2 istanze) + frontend (2 istanze)
  - Spaces bucket per report ed esportazioni
  - Firewall database, domini, health check

- **terraform/variables.tf** (NEW) — Variabili sensibili
- **terraform/outputs.tf** (NEW) — Output infrastruttura
