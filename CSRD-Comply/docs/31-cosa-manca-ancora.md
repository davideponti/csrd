# Cosa Manca Ancora — Todo List per CSRD Comply

## 1. Dashboard: Dati Reali 🔴 FALSO CORRETTO — ora usa dati reali 🎯

**Fix applicato il 10/06/2026** — La dashboard ora usa dati reali dal backend.

### Cosa è stato fixato

**Backend `dashboard.py`:**
- ✅ Rimossi TUTTI i fallback hardcoded (`total_datapoints = 320`, `last_years = [650, 620, 600]`, `matrix_data` con 5 topic fittizi, `regulatory_updates = [...]`)
- ✅ GapAnalyzer fallback ora restituisce `0` invece di `complete=45, partial=120, missing=155`
- ✅ Gap completion percentage calcolata correttamente: `0 / 0 = 0%` se nessun dato
- ✅ `regulatoryUpdates` ora restituisce `[]` (vuoto) invece di 3 aggiornamenti fittizi
- ✅ Readiness score: se `total_datapoints == 0` restituisce `0` invece di fallback a 320

**Frontend `api.ts`:**
- ✅ Aggiunto `export const dashboard = { get: () => request<any>('/dashboard/') }`

**Frontend `dashboard/page.tsx`:**
- ✅ Rimosso completamente `MOCK_DASHBOARD` con i suoi 32%, 45/120/155, etc.
- ✅ Sostituito con `EMPTY_DASHBOARD` — tutti i valori a 0, array vuoti
- ✅ `loadDashboardData()` ora chiama `dashboard.get()` — l'endpoint reale del backend
- ✅ Se la chiamata fallisce: mostra errore + stato vuoto (non più mock)
- ✅ Loading state con spinner
- ✅ Stato "vuoto" con CTA per iniziare: "Inserisci Emissioni" / "Avvia Assessment" quando readinessScore=0
- ✅ Se non ci sono dati emissioni: mostra messaggio vuoto con link a `/emissions`
- ✅ Se non ci sono scadenze: mostra "Nessuna scadenza imminente"
- ✅ Se non ci sono azioni rapide: mostra "Tutte le azioni completate! 🎉"
- ✅ Se non ci sono dati di materialità: mostra "Completa l'assessment per vedere la matrice"
- ✅ Sezione Regulatory Updates nascosta se array vuoto

### Cosa rimane da fare

- [ ] Regulatory Updates: implementare scraper reale che fetcha le news ESRS/EFRAG/ESMA
- [ ] Verificare che `GapAnalyzer.get_summary()` funzioni correttamente senza crash
- [ ] Testare la dashboard con backend in esecuzione per validare i dati reali

## 2. Questionario → IRO ✅ (già implementato in assessment/page.tsx)

**Problema**: Dopo aver compilato il questionario, l'utente non capisce che deve creare gli IRO.

**Stato**: Già risolto nel frontend (`assessment/page.tsx`, righe 90-104):
- [x] `context_questionnaire.py`: N/A — il redirect è gestito dal frontend
- [x] Auto-redirect alla tab IRO dopo l'ultima domanda (riga 96: `setActiveTab('iros')`)
- [x] Dialog AI IRO si apre automaticamente dopo 300ms (riga 98: `setTimeout(() => setShowAiDialog(true), 300)`)
- [x] Messaggio chiaro: "Hai completato il questionario! Ora crea gli IRO..." nel success dialog

## 3. Report: Calcola solo 4 datapoint, non 1000 ✅ (fixato in reports.py)

**Problema**: Il report generava troppi datapoint (1000+) invece di mostrare solo quelli materiali.

**Fix applicato**:
- [x] `reports.py` (`_compile_esrs_data`): ora filtra `MaterialityScore.is_material == True` e itera su ciascuno
- [x] Per ogni score materiale, estrae lo standard ESRS di base (es. `ESRS E1` da `ESRS E1-6.54`)
- [x] Costruisce un set di `material_standards` unici (ESRS E1, ESRS S1, ESRS G1, etc.)
- [x] Chiama `template.remove_non_material_sections(material_standards_list)` per rimuovere le sezioni non materiali

## 4. Emissioni: Scope 2 Market-based ✅ (già implementato)

**Stato**: Già completamente implementato e verificato:

**Componenti già attivi**:
- [x] `emissions/page.tsx` — checkbox "Contratto energia rinnovabile certificata (GO)" nel form Scope2
- [x] `ResultCard` — mostra "0.0 (coperto da GO/I-REC)" quando green tariff è attivo, con nota ESRS E1-6
- [x] `handleSaveResult` per scope='2' — salva sia location-based che market-based nel DB
- [x] Baseline 2025 — include campo `scope2_market_based` separato per confronto YoY

## 5. Baseline 2025 ✅ (già implementato)

**Stato**: Già completamente implementato in `emissions/page.tsx`:

**Componenti già attivi**:
- [x] Sezione "Baseline 2025 — Confronto Anno Precedente" nella tab Overview (righe 777-876)
- [x] 4 campi input: Scope 1, Scope 2, Scope 3, Scope 2 Market-based (tutti con placeholder a 0)
- [x] Calcolo automatico della variazione percentuale YoY con indicatore ⬆/⬇
- [x] Messaggio ESRS E1-6 / GHG Protocol per trend analysis

## 6. Report: Export PDF / iXBRL ✅ (già implementato)

**Stato**: Già completamente implementato sia frontend che backend:

**Componenti già attivi**:
- [x] `reports/page.tsx` — pulsanti per tutti i formati (PDF, iXBRL, XLSX, DOCX, JSON) sempre visibili per ogni report
- [x] `exportReport()` function — chiama `/reports/{id}/export/{format}` con download automatico
- [x] `export_service.py` — servizio completo per i 5 formati (iXBRL/XHTML, PDF, XLSX, DOCX, JSON)
- [x] `professional_pdf.py` — servizio PDF professionale con header/footer, numerazione, sommario

## 7. Report: Pulsante "Validazione" ✅ (già fixato)

**Stato**: Già risolto in `reports/page.tsx`:

**Fix applicati**:
- [x] `startGeneration()` (righe 140-169): dopo il completamento del ciclo di 5 step, chiama automaticamente `fetchValidation(reportId)` e popola `validation` ✅
- [x] `fetchValidation()` (righe 186-198): funzione separata fetcha `/reports/${id}/validation` e salva in `validation` state ✅
- [x] Tab Validation: se `validation` è null mostra "Clicca Esegui Validazione..." con pulsante attivo, se popolato mostra errori/warning/controlli ✅

## 8. Report: "Invia in Revisione" ✅ (già implementato)

**Stato**: Già completamente implementato in `reports/page.tsx` (righe 463-550):

**Componenti già attivi**:
- [x] Blocco informativo blu con spiegazione "Cos'è Invia in Revisione?" (righe 467-478)
- [x] Dialog modale con textarea per commenti del revisore (righe 483-525)
- [x] Messaggio già presente: "L'utente con ruolo Revisore riceverà notifica..."
- [x] Pulsante "Approva Report" per stato review (righe 529-536)
- [x] Messaggio verde "Report approvato e pronto per l'esportazione" per stato final (righe 539-543)

**Cose ancora da verificare** (minori):
- [ ] Verificare che la **notifica** arrivi realmente a utente "Revisore" (backend `email_service.py` deve supportare invio)

## 9. Dark Mode / Tema Sistema ✅ (già implementato)

**Stato**: Già completamente implementato e funzionante:

**Componenti già attivi**:
- [x] `ThemeProvider.tsx` — `ThemeContext` con `theme`, `setTheme`, `resolvedTheme`
- [x] `document.documentElement.classList.toggle('dark', r === 'dark')`
- [x] Ascolto `prefers-color-scheme` media query per modalità "system"
- [x] `ThemeSwitcher` — dropdown con 3 opzioni (☀️ Chiaro, 🌙 Scuro, 💻 Sistema)
- [x] `tailwind.config.ts` — `darkMode: 'class'` configurato
- [x] `globals.css` — Selettore `.dark` con tutte le variabili CSS definite

---

## Riepilogo Priorità

| # | Priorità | Cosa | Dove | Stato |
|---|----------|------|------|-------|
| 1 | 🟢 FIXATO | Dashboard: Dati Reali | `dashboard.py` + `dashboard/page.tsx` | 🔧 **Fixato il 10/06/2026** — ora chiama API reale, niente mock |
| 2 | ✅ VERIFICATO | Questionario → IRO redirect | `assessment/page.tsx` | ✅ Implementato |
| 3 | ✅ VERIFICATO | Report solo datapoint materiali | `reports.py` | ✅ Fixato |
| 4 | ✅ VERIFICATO | Scope 2 Market-based | `emissions/page.tsx` | ✅ Implementato |
| 5 | ✅ VERIFICATO | Baseline 2025 | `emissions/page.tsx` | ✅ Implementato |
| 6 | ✅ VERIFICATO | Export PDF/iXBRL | `reports/page.tsx` + backend | ✅ Implementato |
| 7 | ✅ VERIFICATO | Validazione button bug | `reports/page.tsx` | ✅ Fixato |
| 8 | ✅ MEDIO | "Invia in Revisione" chiarimento | reports page | ✅ Implementato |
| 9 | ✅ MEDIO | Dark mode fix | `ThemeProvider.tsx` | ✅ Implementato |
