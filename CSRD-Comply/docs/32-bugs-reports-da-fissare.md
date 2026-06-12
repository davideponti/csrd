# Bug Report — Pagina Reports (duplicati + report minimale)

## 1. Quattro (4) Report Duplicati nella Lista

**File interessati:**
- `frontend/src/app/(app)/reports/page.tsx`
- `backend/app/api/reports.py`

**Problema:** il frontend mostra 4 card identiche "Report CSRD 2026" perché:

1. **Frontend `loadReports()` (riga 94-110)**: la deduplica esiste (mappa `seen` per ID), ma quando il backend torna 4 record con lo **stesso ID** il codice li filtra — tuttavia se i duplicati hanno **ID diversi** ma stesso titolo/anno, la deduplica fallisce perché usa solo `r.id`.

2. **Backend `list_reports()` (riga 136-146)**: la query è corretta (`filter(company_id)`), ma se nel DB esistono **4 righe identiche** (CREATE chiamato 4 volte prima del fix "exists" sul frontend), il backend le restituisce tutte.

3. **Frontend `createReport()` (riga 112-144)**: il controllo `reports.some(r => r.title === title)` è debole — se i report arrivano *dopo* l'aggiunta ottimistica, il controllo non basta.

**Fix applicato (parziale):**
- Deduplica per ID nel frontend ✅
- Check preventivo `if (exists)` prima di creare ✅
- Controllo aggiunta ottimistica `prev.some(r => r.id === data.id)` ✅

**Cosa manca:**
- Backend: aggiungere unique constraint SQL su `(company_id, title, reporting_year)` 
- Backend: endpoint `DELETE` per eliminare duplicati
- Frontend: dopo creazione, rifare `loadReports()` invece di push ottimistico

---

## 2. Report Preview Mostra Output Minimale (ESRS 2 + E1-6 + Gap Analysis)

**File interessati:**
- `backend/app/api/reports.py` (funzioni `_compile_esrs_data` + `_generate_preview_html`)
- `ai_engine/report_generator/template_engine.py`
- `backend/app/services/export_service.py`

**Problema:** la preview del report mostra SOLO:
- ESRS 2 — General Information
- ESRS E1 — Climate Change (solo E1-6 tabelle)
- Gap Analysis (coverage N/A)

Invece PRIMA generava un report COMPLETO con:
- ESRS 2 completo (BP-1, BP-2, GOV-1, SBM-1, IRO-1, IRO-2)
- ESRS E1 completo (E1-1 fino a E1-9)
- ESRS E2 (Pollution)
- ESRS S1 (Own Workforce)
- ESRS S2 (Workers in the Value Chain)
- ESRS G1 (Business Conduct)
- Non-Material Topics Justifications
- Compliance Statement

**Cause identificate:**

1. **`_compile_esrs_data()` (riga 250-466)**: usa `ReportTemplate.create_default_template()` per generare XHTML. Se `template_engine.py` è stato modificato per produrre output ridotto (solo ESRS 2 + E1), il report salvato in `report.xhtml_content` sarà minimale.

2. **`_generate_preview_html()` (riga 746+)** genera un report COMPLETO via f-string HTML — ma questa funzione viene chiamata SOLO dall'endpoint `/preview`, NON dalla logica di esportazione.

3. **`export_service.py`**: la funzione `_build_structured_data()` usa `report.table_data["ghg_emissions"]` — se `table_data` non contiene dati (es. step 4 non eseguito), produce solo N/A.

**Flusso rotto:**
- Step 1 (`_compile_esrs_data`) → genera XHTML minimale via template_engine
- Step 2 (`_run_gap_analysis`) → OK
- Step 3 (`_generate_narratives`) → OK
- Step 4 (`_build_tables_charts`) → popola `table_data` (solo GHG)
- Step 5 (`_tag_ixbrl`) → OK

**Il template engine non genera più le sezioni complete** (ESRS E2, S1, S2, G1) — probabilmente rimuove tutto ciò che non è "materiale" via `remove_non_material_sections()`.

---

## 3. Esportazioni (PDF/XLSX/DOCX/JSON) da Fixare

**File:** `backend/app/services/export_service.py`

La funzione `_build_structured_data()` produce solo dati GHG (scopes 1-3) + materiality vuoto + gap analysis vuoto.

**Manca:**
- Dati completi per ESRS E2, S1, S2, G1
- Narrative testuali per tutte le sezioni
- Dati materialità reali (non array vuoto)
- Gap analysis reale (non hardcoded)

---

## 4. Riepilogo Priorità

| # | Priorità | Cosa | File |
|---|----------|------|------|
| 1 | 🔴 ALTA | Fix duplicati report (DB unique constraint + deduplica robusta) | `reports.py`, SQL migration |
| 2 | 🔴 ALTA | Ripristinare report completo nella preview | `reports.py` `_generate_preview_html` |
| 3 | 🔴 ALTA | Template engine deve generare TUTTE le sezioni ESRS materiali | `template_engine.py` |
| 4 | 🟡 MEDIA | Export service deve includere dati completi | `export_service.py` |
| 5 | 🟢 BASSA | Aggiungere endpoint DELETE report duplicati | `reports.py` |

