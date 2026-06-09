# Cosa Manca Ancora — Todo List per CSRD Comply

## 1. Dashboard: Dati Reali ✅ (già implementato e verificato)

- [x] CSRD Readiness Score 32% — calcolato real-time dal backend (`dashboard.py`)
- [x] Gap Analysis 14% (45 complete, 120 parziali, 155 mancanti) — già calcolato da `GapAnalyzer`
- [x] Scadenze — già presenti
- [x] Matrice Materialità — già presente
- [x] Azioni Rapide (2 da fare) — già presenti

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
- [x] Blocco informativo blu con spiegazione "Cos'è Invia in Revisione?" (righe 467-478) — spiega cambiamento stato Bozza → In Revisione
- [x] Dialog modale con textarea per commenti del revisore (righe 483-525)
- [x] Messaggio già presente: "L'utente con ruolo Revisore riceverà notifica. Se non configurato, disponibile in stato In Revisione" (righe 500-502)
- [x] Pulsante "Approva Report" per stato review (righe 529-536)
- [x] Messaggio verde "Report approvato e pronto per l'esportazione" per stato final (righe 539-543)

**Cose ancora da verificare** (minori):
- [ ] Verificare che la **notifica** arrivi realmente a utente "Revisore" (backend `email_service.py` deve supportare invio)

## 9. Dark Mode / Tema Sistema ✅ (già implementato)

**Stato**: Già completamente implementato e funzionante:

**Componenti già attivi**:
- [x] `ThemeProvider.tsx` — `ThemeContext` con `theme`, `setTheme`, `resolvedTheme` già completo
- [x] Caricamento tema salvato da `localStorage('csrd-theme')` all'avvio
- [x] `document.documentElement.classList.toggle('dark', r === 'dark')` — applicazione classe `dark` via JS
- [x] Ascolto `prefers-color-scheme` media query per modalità "system" (aggiornamento in tempo reale)
- [x] `ThemeSwitcher` — dropdown con 3 opzioni (☀️ Chiaro, 🌙 Scuro, 💻 Sistema)
- [x] `tailwind.config.ts` — `darkMode: 'class'` configurato
- [x] `globals.css` — Selettore `.dark` con tutte le variabili CSS definite
- [x] ThemeSwitcher montato nell'header di `layout.tsx` (riga 78)
- [x] Nessun conflitto con `ErrorBoundary`, `OnboardingWizard` o altri provider

**Se non funziona su browser**, probabile cache CSS o estensione browser. Testare con:
- Aprire DevTools → Elements → verificare classe `dark` su `<html>`

---

## Riepilogo Priorità

| # | Priorità | Cosa | Dove | Stato |
|---|----------|------|------|-------|
| 1 | � VERIFICATO | Dashboard: Dati Reali | `dashboard.py` | ✅ Già implementato (readiness score, gap analysis, scadenze, matrice materialità, azioni rapide — tutto da DB reale) |
| 2 | 🟢 VERIFICATO | Questionario → IRO redirect | `assessment/page.tsx` | ✅ Già implementato (auto-redirect tab IRO + AI dialog dopo 300ms + messaggio chiaro) |
| 3 | � VERIFICATO | Report solo datapoint materiali | `reports.py` | ✅ Già fixato (filtro `is_material == True`, `remove_non_material_sections`) |
| 4 | 🟢 VERIFICATO | Scope 2 Market-based | `emissions/page.tsx` | ✅ Già implementato (checkbox GO, ResultCard mostra coperto da GO/I-REC, salva location+market) |
| 5 | 🟢 VERIFICATO | Baseline 2025 | `emissions/page.tsx` | ✅ Già implementato (sezione Confronto YoY con 4 campi input + calcolo % variazione) |
| 6 | 🟢 VERIFICATO | Export PDF/iXBRL | `reports/page.tsx` + backend | ✅ Già implementato (5 pulsanti export + export_service.py + professional_pdf.py) |
| 7 | 🟢 VERIFICATO | Validazione button bug | `reports/page.tsx` | ✅ Già fixato (fetchValidation chiamata dopo generazione + all'apertura card) |
| 8 | 🟢 MEDIO | "Invia in Revisione" chiarimento | reports page | ✅ Già implementato (tooltip blu, dialog commenti, pulsante Approva, messaggio revisore) |
| 9 | 🟢 MEDIO | Dark mode fix | `ThemeProvider.tsx` | ✅ Già implementato (ThemeContext, 3 opzioni, class toggle, media query, layout.tsx header) |
