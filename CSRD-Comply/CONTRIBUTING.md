# Contributing to CSRD Comply

Grazie per il tuo interesse! Ecco come contribuire.

## 🚀 Setup sviluppo

```bash
# Backend
cd backend
python -m venv venv
source venv/bin/activate
pip install -r requirements.txt
cp .env.example .env   # modifica le credenziali
alembic upgrade head
uvicorn app.main:app --reload

# Frontend
cd frontend
npm install
cp .env.local.example .env.local  # NEXT_PUBLIC_API_URL=http://localhost:8000
npm run dev
```

## 📋 Linee guida

- **Commit**: messaggi chiari in italiano/inglese, es. `fix(auth): rimuovi localStorage JWT`
- **Codice**: segui già le convenzioni del progetto (type hint, docstring, logging)
- **Branch**: `feature/nome-feature`, `fix/nome-fix`
- **Pre-commit**: esegui `pre-commit run --all-files` prima di pushare
- **Test**: `cd backend && pytest -v` per backend, tutti i test devono passare

## 🔒 Sicurezza

- **MAI** salvare JWT in `localStorage` — usa solo cookie HttpOnly
- **MAI** committare `.env` con chiavi reali
- **MAI** usare `except: pass` — logga sempre il warning
- Le migrazioni vanno generate con `alembic revision --autogenerate -m "descrizione"`

## 🧪 Test

```bash
cd backend
pytest -v                           # tutti i test
pytest -v -k "auth"                 # solo test auth
coverage run -m pytest && coverage report  # copertura
```

## 🐛 Segnalare bug

Usa `/reportbug` o apri una issue su GitHub con:
1. Descrizione del problema
2. Passi per riprodurre
3. Log / screenshot se disponibili

## 📦 Struttura

```
CSRD-Comply/
├── ai_engine/         # Modelli AI (ESRS, carbon, materiality)
├── backend/           # FastAPI + SQLAlchemy
│   ├── app/api/       # Endpoint REST
│   ├── app/core/      # Config, security, DB
│   └── tests/         # Test suite
├── frontend/          # Next.js (App Router)
│   └── src/
│       ├── app/       # Route pages
│       ├── components/# UI components
│       └── hooks/     # Custom hooks (es. useAuth)
└── infrastructure/    # Docker, nginx, Terraform
```
