# 🔒 CSRD Comply — Audit di Sicurezza & Report

**Data:** 25/05/2026  
**Versione del codice:** commit `51392a68`  
**Ambiente:** Development / Pre-Production  
**Tipo di audit:** Static Code Analysis & Architecture Review

---

## 📊 VOTO COMPLESSIVO: **5.5/10 — INSUFFICIENTE**

Il progetto mostra una buona architettura di base ma presenta **vulnerabilità critiche** che richiedono intervento immediato prima di qualsiasi deploy in produzione.

---

## 🔴 CRITICAL (Intervento immediato)

### C-1: SECRET_KEY e API Keys hardcodate nel `.env` committato

**File:** `backend/.env`
**Gravità:** 🔴 CRITICAL (10/10)

```
OPENAI_API_KEY=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
SECREY_KEY=ab505167f0d6fb186879b97c879925cfb0a1ef354d4691e0e468bb3fce5d3652SECRET_KEY=5fd1b21d63dc177ada52bd95ca2561ba6b9b79f850a30739996b85196209f732
```

**Rischio:** La SECRET_KEY è concatenata in modo errato (duplicata con typo "SECREY_KEY") e l'API key di OpenAI è esposta pubblicamente su GitHub. Potenziale furto del credito OpenAI ($) e compromissione totale del JWT signing.

**Fix:** Revocare immediatamente la chiave OpenAI. Usare Docker secrets o vault per le credenziali. Il `.env` non deve essere MAI committato (aggiunto a `.gitignore` — già fatto).

---

### C-2: JWT token salvato in localStorage

**File:** `frontend/src/hooks/useAuth.ts` (riga 42), `frontend/src/lib/api.ts`
**Gravità:** 🔴 CRITICAL (9/10)

```typescript
localStorage.setItem('token', data.access_token)
```

**Rischio:** Attacco XSS = furto del token = accesso completo all'account. Il backend **già supporta** HttpOnly Cookie (funzioni `set_auth_cookie` / `clear_auth_cookie` in `security.py`) ma non vengono usate.

**Fix:** Refactor frontend per usare HttpOnly Cookie invece di localStorage + Authorization header.

---

### C-3: Nessun pulsante di logout nel frontend

**File:** `frontend/src/app/(app)/layout.tsx`
**Gravità:** 🔴 CRITICAL (8/10)

Il layout dell'applicazione autenticata **non ha alcun pulsante di logout**. L'unico modo per "sloggarsi" è cancellare manualmente il localStorage. Inoltre, non c'è alcun reindirizzamento alla pagina di login.

**Rischio:** Qualsiasi utente che condivida il browser lascia il token JWT esposto. Un utente malintenzionato che prende possesso di un terminale può continuare ad accedere alle API.

**Fix:** Aggiungere pulsante di logout nella sidebar o nell'header del layout, che chiami `logout()` da `useAuth()` e reindirizzi a `/auth/login`.

---

### C-5: Nessuna rate limiting sull'API (lato backend)

**File:** `backend/app/api/*.py`, `backend/app/main.py`
**Gravità:** 🔴 CRITICAL (8/10)

**Rischio:** Assenza totale di rate limiting sugli endpoint di login/register. Attacco brute-force sulle password possibile. `slowapi` è nelle `requirements.txt` ma non è implementato.

**Fix:** Integrare `slowapi` sugli endpoint `/auth/login` e `/auth/register`, e progressivamente su tutti gli endpoint.

---

### C-6: Nessun validation delle emissioni e dati utente contro attacchi NoSQL / injection

**File:** `backend/app/api/emissions.py`, `backend/app/api/assessment.py` (in parte)
**Gravità:** 🔴 CRITICAL (7/10)

**Rischio:** I modelli Pydantic validano la struttura ma non c'è sanitizzazione di input testuali liberi. Un utente malevolo potrebbe inserire contenuti dannosi nei campi `rationale`, `description`, `questionnaire_responses`.

**Fix:** Aggiungere validatori Pydantic con regex whitelist per campi testuali. Sanitizzare input utente prima del salvataggio DB.

---

## 🟠 HIGH

### H-1: Logging di token JWT in caso di errore

**File:** `backend/app/core/multitenancy.py` (riga 76)
**Gravità:** 🟠 HIGH (7/10)

```python
logger.warning(f"Failed to decode token: {type(e).__name__}")
```

Parzialmente mitigato (logga solo il tipo d'errore, non il contenuto). Ma in altri punti del codice non c'è garanzia che token non vengano loggati.

---

### H-2: XSS nel preview report HTML

**File:** `backend/app/api/reports.py` (riga ~182)
**Gravità:** 🟠 HIGH (7/10)

`xhtml_content` salvato nel DB e servito come HTML senza sanitizzazione. **Mitigato** ora con l'uso di `nh3` per la sanitizzazione HTML nell'endpoint preview.

---

### H-3: In-memory cache senza limiti

**File:** `backend/app/api/ai.py` (riga 22)
**Gravità:** 🟠 HIGH (6/10)

```python
_mapper_cache: dict[str, tuple[datetime, dict]] = {}
```

**Rischio:** Cache in memoria senza limiti di dimensione. Attacco DoS riempiendo la cache con dati arbitrari (potenziale memory exhaustion).

**Fix:** Usare Redis con TTL e maxmemory, o limitare size della cache.

---

### H-4: Secret Key debole di default

**File:** `backend/app/core/config.py` (riga 11)
**Gravità:** 🟠 HIGH (6/10)

```python
SECRET_KEY: str = "change-me-in-production"
```

**Parzialmente mitigato** dal validator `validate_secret_key` che blocca l'avvio in produzione con la key di default. Ma il validator usa `SECRET_KEY in ("change-me-in-production", "")` — in development, la key è letteralmente "change-me-in-production".

---

### H-5: Terraform con secret hardcodati

**File:** `infrastructure/terraform/variables.tf` (da verificare), `infrastructure/terraform/main.tf`
**Gravità:** 🟠 HIGH (6/10)

Il TF state backend su S3 contiene potenzialmente secret in chiaro (DATABASE_URL, SECRET_KEY). Non c'è encryption a riposo configurata per il bucket Terraform state.

---

### H-6: No CSRF protection

**File:** `frontend/` / `backend/`
**Gravità:** 🟠 HIGH (6/10)

Nessuna protezione CSRF implementata. L'uso di JWT in Authorization header mitiga parzialmente per le API JSON, ma non per form POST o cookie-based auth.

---

## 🟡 MEDIUM

### M-1: JWT senza rotation / refresh token rotation

**File:** `backend/app/api/auth.py`
**Gravità:** 🟡 MEDIUM (5/10)

Il refresh token può essere usato una sola volta ma non c'è rotation. Se un refresh token viene rubato, può essere usato per generare nuovi access token fino alla scadenza.

### M-2: Database connection string senza SSL

**File:** `backend/app/core/config.py` (riga 8)
**Gravità:** 🟡 MEDIUM (5/10)

```python
DATABASE_URL: str = "postgresql://postgres:postgres@localhost:5432/csrd_comply"
```

Password di default (postgres) in chiaro. Nessun SSL per la connessione DB.

### M-3: Nessun input validation per `company_size`, `employee_count`, ecc.

**File:** `backend/app/api/auth.py`
**Gravità:** 🟡 MEDIUM (4/10)

I campi numerici opzionali non vengono validati per range (es. employee_count negativo, company_size irrealistico).

### M-4: `CORS_ORIGINS` in `.env` con solo localhost

**File:** `CSRD-Comply/backend/.env`
**Gravità:** 🟡 MEDIUM (4/10)

```python
CORS_ORIGINS=["http://localhost:3000"]
```

Corretto per development, ma in produzione va configurato con i domini reali.

### M-5: No security tests

**File:** `backend/tests/`
**Gravità:** 🟡 MEDIUM (4/10)

I test coprono funzionalità ma non ci sono test per: brute-force, injection, XSS, IDOR, rate limiting.

### M-6: Server header information disclosure

**File:** `backend/Dockerfile` (riga 12)
**Gravità:** 🟡 MEDIUM (4/10)

`uvicorn` in modalità `--reload` espone informazioni sul server. In produzione non bisogna usare `--reload` e bisogna configurare Nginx per rimuovere il server header.

---

## 🟢 LOW

### L-1: Typo in `.env`: "SECREY_KEY" invece di "SECRET_KEY"

**File:** `backend/.env`
**Gravità:** 🟢 LOW (3/10)

La variabile è scritta `SECREY_KEY` (manca la "T"). Il codice vero legge `SECRET_KEY` da config.py — quindi questa variabile non viene effettivamente letta.

### L-2: Nessuna validazione `NEXT_PUBLIC_API_URL` nel frontend

**File:** `frontend/src/lib/api.ts`
**Gravità:** 🟢 LOW (2/10)

L'API URL nel frontend non viene validata. Un attacco Man-in-the-Middle che modifica la risposta DNS potrebbe reindirizzare le chiamate API.

### L-3: `pool_pre_ping=True` ma nessun `pool_size` o `max_overflow`

**File:** `backend/app/core/database.py` (riga 6)
**Gravità:** 🟢 LOW (2/10)

```python
engine = create_engine(settings.DATABASE_URL, pool_pre_ping=True)
```

Nessun limite al pool di connessioni. In produzione con molti utenti, questo può portare a connessioni esauste.

### L-4: Nessun `version` header nelle risposte API

**File:** `backend/app/main.py`
**Gravità:** 🟢 LOW (1/10)

Manca un header di versione nelle risposte API per permettere versioning e deprecation planning.

---

## 📋 RIEPILOGO PER AREA

| Area | Voto | Note |
|------|------|------|
| **Authentication & Authorization** | 5/10 | JWT ok ma localStorage. Password policy presente. |
| **Data Protection** | 4/10 | Secret in chiaro nel repo. Nessuna encryption a riposo. |
| **API Security** | 5/10 | No rate limiting. Input validation parziale. |
| **Frontend Security** | 4/10 | XSS parzialmente mitigato (nh3). localStorage per token. |
| **Infrastructure** | 6/10 | Docker secrets per DB. Nginx con security headers. |
| **DevSecOps** | 3/10 | `.env` committato. Terraform state non cifrato. |
| **Compliance (OWASP)** | 4/10 | A2(Auth), A3(XSS), A5(Broken Access Control) a rischio. |
| **Monitoring & Logging** | 5/10 | Logging presente ma potrebbe esporre dati sensibili. |

---

## 🎯 AZIONI PRIORITARIE

### 🔴 Giorno 1 — CRITICAL

1. [x] **Revocare API key OpenAI** e rigenerare SECRET_KEY
2. [x] **Rimuovere `.env` dal tracking git** (già in `.gitignore`, ma va eseguito `git rm --cached`)
3. [x] **Implementare rate limiting** con `slowapi` su /auth/login e /auth/register
4. [x] **Sanitizzare output HTML** in `/reports/{id}/preview` con `nh3` ✅

### 🟠 Settimana 1 — HIGH

5. [ ] **Refactor frontend** per usare HttpOnly Cookie invece di localStorage
6. [ ] **Aggiungere Redis** per cache con limiti (sostituire `_mapper_cache`)
7. [ ] **Aggiungere CSRF protection** per cookie-based auth
8. [ ] **Configurare SSL** per connessione DB e Terraform state encryption

### 🟡 Mese 1 — MEDIUM

9. [ ] **Aggiungere security test** nella CI/CD pipeline
10. [ ] **Implementare refresh token rotation**
11. [ ] **Validare range input numerici** in tutti i modelli Pydantic
12. [ ] **Configurare pool_size** per SQLAlchemy
13. [ ] **Aggiungere API versioning header**
14. [ ] **Implementare audit logging** (chi ha fatto cosa e quando)

---

## 📊 MATRICE DEI RISCHI

```
Impatto
  ^
  |  C-1 ●                    C-2 ●
10 |  ● C-3
  |
 8 |              H-1 ● H-2 ●
  |         H-5 ●
 6 |  H-4 ●           H-6 ●
  |    M-2 ●
 4 |  M-1 ●    M-3 ●         M-6 ●
  |
 2 |  L-1 ●  L-3 ●
  |
  +----+----+----+----+----+----+----+---->
 0    2    4    6    8   10   Probabilità
```

---

*Audit completato da Cline AI — 25/05/2026*  
*Nessuna modifica al codice è stata effettuata durante l'audit.*
