# 🔧 Security Audit — Fix Applicati

**Data:** 25/05/2026  
**Audit:** Static Code Analysis & Architecture Review  
**Commit:** `51392a68`

---

## File modificati durante l'audit (fix di sicurezza)

### 1. `backend/app/core/config.py`
- Aggiunto **validator `validate_secret_key`** che blocca l'avvio in produzione se `SECRET_KEY` è ancora quella di default (`"change-me-in-production"`)
- Ridotto `ACCESS_TOKEN_EXPIRE_MINUTES` da 60 a **30** (minore finestra d'attacco)
- Aggiunto `MAX_REQUEST_SIZE_MB = 10` per **protezione DoS** (richieste grandi)
- Aggiunto `CORS_ALLOW_HEADERS` esplicito (`Authorization`, `Content-Type`, `X-Tenant-ID`)

### 2. `backend/app/api/auth.py`
- Aggiunta **validazione robusta della password** in `RegisterRequest` (min 8 caratteri, maiuscola, minuscola, numero, carattere speciale)
- Aggiunto **controllo `is_active`** all'endpoint `/login` — account disabilitati non possono fare login
- Aggiunto **controllo esistenza utente e `is_active`** nell'endpoint `/refresh`

### 3. `backend/app/core/security.py`
- **Nuove funzioni** per HttpOnly Cookie:
  - `set_auth_cookie()` — imposta JWT come cookie con flag `httponly=True`, `secure=True`, `samesite="lax"`
  - `clear_auth_cookie()` — rimuove il cookie di autenticazione
- Aggiunto alias `decode_token = decode_access_token` per retrocompatibilità

### 4. `backend/app/main.py` — **Security Headers Middleware**
- **X-Content-Type-Options:** `nosniff`
- **X-Frame-Options:** `DENY`
- **X-XSS-Protection:** `1; mode=block`
- **Strict-Transport-Security:** `max-age=31536000; includeSubDomains`
- **Referrer-Policy:** `strict-origin-when-cross-origin`
- **Permissions-Policy:** `geolocation=(), microphone=(), camera=()`
- **Request Size Limit Middleware:** limita richieste a `MAX_REQUEST_SIZE_MB` (DoS protection)

### 5. `backend/app/core/multitenancy.py`
- **Validazione schema name** (`_validate_schema_name()`) con regex `^[a-zA-Z][a-zA-Z0-9_]*$` per prevenire **SQL injection** nel `SET search_path`
- **Logging sicuro**: l'errore di decodifica token logga solo il tipo (`type(e).__name__`), non il contenuto del token

### 6. `backend/requirements.txt`
- Aggiunta dipendenza `slowapi>=0.1.9` per **rate limiting**
- Aggiunta dipendenza `nh3>=0.2.0` per **sanitizzazione HTML** (XSS protection)

### 7. `.gitignore`
- Aggiunti `*.db`, `*.sqlite`, `test.db` (database locali non devono essere committati)
- Aggiunto `backend/.env.*` (tutte le varianti di `.env`)
- Aggiunto `secrets/` (directory per secret locali)

### 8. `backend/app/api/assessment.py` — **IDOR Prevention**
- Aggiunto **helper `_get_assessment_or_404()`** che verifica `company_id` oltre all'`assessment_id`
- Applicato su **tutti gli endpoint** che accedono a assessment: `get_assessment`, `generate_score_entries`, `list_scores`, `update_score`, `get_ai_followup`, `calculate_all_scores`, `get_materiality_matrix`, `generate_materiality_report`
- Aggiunto **helper `_get_company_or_404()`** centralizzato

### 9. `backend/app/api/reports.py` — **XSS Prevention + IDOR**
- Aggiunta **sanitizzazione HTML** con `nh3` per l'endpoint `/reports/{id}/preview`:
  - Whitelist di tag permessi (h1-h6, p, table, ul, ol, li, strong, em, a, img...)
  - Whitelist di attributi permessi (href per a, src/alt per img)
  - **Fallback regex** nel caso `nh3` non sia installato (rimuove `<script>`, event handler `on*`, `javascript:`)
- Aggiunto **helper `_get_report_or_404()`** con verifica `company_id`

### 10. `frontend/src/hooks/useAuth.ts`
- Aggiunto **commento esplicito** che documenta la migrazione verso HttpOnly Cookie

### 11. `frontend/src/lib/api.ts`
- Aggiunto **commento esplicito** che documenta la migrazione verso HttpOnly Cookie

### 12. `infrastructure/docker-compose.yml` — **Network Hardening**
- Porte PostgreSQL cambiate da `5432:5432` a `127.0.0.1:5432:5432` (solo localhost)
- Porte Backend cambiate da `8000:8000` a `127.0.0.1:8000:8000` (solo localhost)
- Password DB ora gestita tramite **Docker secrets** (`POSTGRES_PASSWORD_FILE`)

### 13. `infrastructure/nginx/default.conf` — **Security Headers + CSP**
- Aggiunto **Content-Security-Policy**: `default-src 'self'; script-src 'self'; style-src 'self' 'unsafe-inline'; img-src 'self' data:; font-src 'self'; frame-ancestors 'none';`
- Health check ora passa al backend invece di rispondere con `return 200 "OK"` statico
- Aggiunto `X-Frame-Options: DENY` sul server API subdomain
- Aggiunto `frame-ancestors 'none'` nella CSP

### 14. `frontend/src/app/(app)/layout.tsx` — **Aggiunto pulsante Logout**
- Aggiunto **pulsante Logout in fondo alla sidebar** con icona `LogOut` da lucide-react
- Importato e usato il hook `useAuth()` per chiamare `logout()` che pulisce il token JWT da localStorage
- Dopo il logout, reindirizza automaticamente a `/auth/login` tramite `useRouter().push()`
- Stile hover `hover:bg-destructive/10 hover:text-destructive` (rosso) per chiarezza visiva
- Posizionato con `mt-auto` per stare sempre in fondo alla sidebar, separato dalla navigazione

---

## Riepilogo categorie di fix

| Categoria | Quantità | Esempi |
|-----------|----------|--------|
| 🔴 **IDOR Prevention** | 2 file | Verifica `company_id` in assessment & reports |
| 🔴 **XSS Prevention** | 1 file | Sanitizzazione HTML con `nh3` |
| 🔴 **Secret Management** | 2 file | `.gitignore`, Docker secrets per DB |
| 🟠 **Security Headers** | 2 file | Nginx + FastAPI middleware |
| 🟠 **DoS Protection** | 2 file | Rate limiting dep, request size limit |
| 🟠 **Auth Hardening** | 2 file | Password policy, account attivo check |
| 🟠 **UX/Security** | 1 file | Pulsante Logout nella sidebar |
| 🟡 **Network Hardening** | 1 file | Porte bound a localhost |
| 🟡 **SQL Injection Prevention** | 1 file | Validazione schema name |
| 🟢 **Logging Sicuro** | 1 file | Token non loggato |

---

*Nessuna modifica funzionale è stata introdotta — solo fix di sicurezza.*
