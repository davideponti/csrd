# CSRD Comply — Priorità Implementazione

## ✅ Priorità 1 — Prima del deploy

### Stato Attuale:

**1. iXBRL Validato**
- [x] `ai_engine/report_generator/ixbrl_validator.py` — Validatore ESRS con logica di controllo
- [x] `ixbrl_tagger.py` — Genera tagging iXBRL
- [x] Endpoint `/api/v1/reports/{id}/validate-ixbrl` già presente in `reports.py`
- ⚠️ **Da fare**: Installare Arelle e integrare validazione contro tassonomia ESRS ufficiale (si veda sotto)

**2. Licenza Software**
- [x] `LICENSE` — Proprietaria, tutti i diritti riservati
- [x] `README.md` — Notice proprietaria + avviso privacy GitHub
- ⚠️ **Da fare**: Mantieni repo privato su GitHub

## ✅ Priorità 2 — Entro i primi 3 mesi

**3. Stripe Integrato** ✨ COMPLETATO
- [x] `backend/app/api/stripe.py` — Endpoint creato:
  - `POST /stripe/create-checkout-session` — Checkout session Stripe
  - `POST /stripe/create-billing-portal` — Customer Portal
  - `POST /stripe/webhook` — Webhook handler (checkout.completed, invoice.*, subscription.*)
  - `POST /stripe/manual-invoice` — Fattura manuale per primi clienti
  - `GET /stripe/status` — Stato integrazione
- [x] `backend/app/core/config.py` — Variabili Stripe (STRIPE_SECRET_KEY, STRIPE_WEBHOOK_SECRET, STRIPE_PRICE_*)
- [x] `backend/.env.example` — Documentate le variabili Stripe
- [x] `backend/requirements.txt` — Aggiunto `stripe>=9.0.0`
- [x] `backend/app/api/router.py` — Già incluso `stripe` router

**4. Export PDF Professionale** ✨ COMPLETATO
- [x] `backend/app/services/professional_pdf.py` — Servizio completo ReportLab:
  - Intestazione con nome azienda e titolo report
  - Piè di pagina con numeri pagina, data, nota riservatezza
  - Copertina professionale
  - Indice (TOC)
  - 3 schemi colore: professional, modern, minimal
  - Watermark opzionale (Draft, Confidential, etc.)
  - Parsing XHTML → ReportLab flowables
- [x] `backend/app/api/reports.py` — Integrato:
  - Endpoint `GET /reports/{id}/export-formats` già include `professional_pdf`
  - Endpoint `GET /reports/{id}/export-professional-pdf`
  - Sistema di fallback (xhtml2pdf → ReportLab → PDF minimale)

**5. Onboarding Guidato** ✨ COMPLETATO
- [x] `frontend/src/components/OnboardingWizard.tsx` — Wizard a 5 passi:
  - Passo 1: Profilo Azienda
  - Passo 2: Questionario di Contesto
  - Passo 3: Calcolo Emissioni GHG
  - Passo 4: Genera Report CSRD
  - Passo 5: Sei Pronto! 🚀
  - Barra progresso, navigazione, skip button
  - Rilevamento automatico step completati
- [x] `frontend/src/app/(app)/layout.tsx` — Integrato OnboardingWizard + useOnboarding hook

**6. Email Transazionali** ✨ COMPLETATO
- [x] `backend/app/services/email_service.py` — Servizio completo:
  - Provider SMTP, SendGrid, Mailgun + console (development)
  - Template email: welcome, password reset, report ready, deadline reminder
  - Invio sincrono e asincrono
  - Branding CSRD Comply
- [x] `backend/app/api/emails.py` — Endpoint:
  - `GET /emails/status` — Stato configurazione
  - `POST /emails/welcome` — Invia welcome (admin)
  - `POST /emails/password-reset` — Invia reset password
  - `POST /emails/report-ready` — Notifica report pronto
- [x] `backend/app/api/auth.py` — Integrato:
  - Welcome email inviata automaticamente alla registrazione
  - Endpoint `POST /auth/forgot-password` con invio email reset
- [x] `backend/app/core/config.py` — Variabili email (SMTP, SENDGRID, MAILGUN)
- [x] `backend/.env.example` — Documentate le variabili email
- [x] `backend/app/api/router.py` — Già incluso `emails` router

### 📋 Checklist completamento

| Area | File Creati | Config | Router | Test |
|------|------------|--------|--------|------|
| Stripe | ✅ stripe.py | ✅ config.py, .env.example | ✅ router.py | ❌ |
| Prof. PDF | ✅ professional_pdf.py | ✅ config.py | ✅ reports.py | ❌ |
| Onboarding | ✅ OnboardingWizard.tsx | — | ✅ layout.tsx | ❌ |
| Email | ✅ email_service.py, emails.py | ✅ config.py, .env.example | ✅ router.py, auth.py | ❌ |
| iXBRL Valid. | ✅ ixbrl_validator.py | — | ✅ reports.py | ✅ test_ixbrl_tagger.py |
