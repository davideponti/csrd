'use client'

import Link from 'next/link'
import { Leaf, ArrowLeft } from 'lucide-react'

export default function TermsOfServicePage() {
  return (
    <div className="min-h-screen bg-gradient-to-b from-gray-50 to-white">
      {/* Back link */}
      <div className="max-w-4xl mx-auto px-4 sm:px-6 lg:px-8 pt-8">
        <Link
          href="/"
          className="inline-flex items-center gap-2 text-sm font-medium text-gray-500 hover:text-emerald-600 transition-colors"
        >
          <ArrowLeft className="h-4 w-4" />
          Torna alla Home
        </Link>
      </div>

      {/* Header */}
      <div className="max-w-4xl mx-auto px-4 sm:px-6 lg:px-8 pt-8 pb-6">
        <div className="flex items-center gap-3 mb-4">
          <Leaf className="h-8 w-8 text-emerald-600" />
          <span className="text-xl font-bold text-gray-900">CSRD Comply</span>
        </div>
        <h1 className="text-3xl sm:text-4xl font-bold text-gray-900">
          Termini di Servizio (ToS)
        </h1>
        <p className="mt-2 text-sm text-gray-500">
          <strong>Ultimo aggiornamento:</strong> 25 Maggio 2026
        </p>
      </div>

      {/* Content */}
      <div className="max-w-4xl mx-auto px-4 sm:px-6 lg:px-8 pb-16">
        <div className="bg-white rounded-2xl shadow-sm border border-gray-100 p-6 sm:p-10
          prose prose-gray prose-sm sm:prose-base max-w-none
          prose-headings:text-gray-900 prose-headings:font-bold
          prose-h2:text-xl prose-h2:mt-10 prose-h2:mb-4 prose-h2:pb-2 prose-h2:border-b prose-h2:border-gray-200
          prose-h3:text-lg prose-h3:mt-8 prose-h3:mb-3 prose-h3:text-emerald-800
          prose-p:text-gray-600 prose-p:leading-relaxed
          prose-strong:text-gray-900
          prose-ul:list-disc prose-ul:pl-6 prose-ul:text-gray-600
          prose-li:my-1
          prose-hr:my-8 prose-hr:border-gray-200
        ">
          <section>
            <h2>1. Accettazione dei Termini</h2>
            <p>
              Benvenuto su <strong>CSRD-Comply</strong>. Utilizzando la nostra piattaforma SaaS per la conformità alla Corporate Sustainability Reporting Directive (CSRD), l'utente ("Cliente", "Lei") accetta integralmente i presenti Termini di Servizio. Se non accetta uno qualsiasi di questi termini, è pregato di non utilizzare il Servizio.
            </p>
          </section>

          <section>
            <h2>2. Definizioni</h2>
            <ul>
              <li><strong>"Piattaforma" / "Servizio"</strong>: l'applicazione SaaS CSRD-Comply accessibile via web</li>
              <li><strong>"Azienda" / "Noi" / "Ci"</strong>: CSRD-Comply S.r.l., il fornitore del Servizio</li>
              <li><strong>"Cliente" / "Utente"</strong>: la persona fisica o giuridica che utilizza il Servizio</li>
              <li><strong>"Account"</strong>: l'account registrato dal Cliente per accedere al Servizio</li>
              <li><strong>"Dati del Cliente"</strong>: tutti i dati, documenti, informazioni caricati dal Cliente sulla Piattaforma</li>
              <li><strong>"Report"</strong>: i report di sostenibilità generati tramite la Piattaforma</li>
              <li><strong>"Abbonamento"</strong>: il piano di pagamento scelto dal Cliente per utilizzare il Servizio</li>
            </ul>
          </section>

          <section>
            <h2>3. Descrizione del Servizio</h2>
            <p>CSRD-Comply fornisce una piattaforma SaaS che assiste le aziende nella:</p>
            <ul>
              <li>Raccolta e gestione dei dati ESG</li>
              <li>Valutazione della doppia materialità</li>
              <li>Generazione di report di sostenibilità conformi alla CSRD</li>
              <li>Monitoraggio normativo e aggiornamenti regolatori</li>
              <li>Integrazione con standard ESRS e tassonomia iXBRL</li>
            </ul>
            <p>Il Servizio è fornito "così com'è" secondo le specifiche indicate nella documentazione tecnica e nei piani di abbonamento sottoscritti.</p>
          </section>

          <section>
            <h2>4. Registrazione e Account</h2>

            <h3>4.1 Requisiti</h3>
            <ul>
              <li>Essere maggiorenni (18+ anni)</li>
              <li>Fornire informazioni accurate e veritiere</li>
              <li>Mantenere aggiornati i dati di registrazione</li>
            </ul>

            <h3>4.2 Credenziali</h3>
            <ul>
              <li>L'Utente è responsabile della riservatezza delle proprie credenziali</li>
              <li>L'Utente è responsabile per tutte le attività che avvengono sotto il proprio Account</li>
              <li>L'Utente deve notificare immediatamente eventuali usi non autorizzati</li>
            </ul>

            <h3>4.3 Account multipli</h3>
            <ul>
              <li>Un'azienda può creare un solo Account a meno di accordi diversi</li>
              <li>Account condivisi o multipli violano i presenti termini</li>
            </ul>
          </section>

          <section>
            <h2>5. Piani di Abbonamento e Pagamenti</h2>

            <h3>5.1 Piani disponibili</h3>
            <p>Offriamo i seguenti piani di abbonamento:</p>
            <ul>
              <li><strong>Free</strong>: funzionalità limitate, report di base</li>
              <li><strong>Starter</strong>: funzionalità intermedie, report standard</li>
              <li><strong>Professional</strong>: funzionalità complete, report avanzati</li>
              <li><strong>Enterprise</strong>: soluzione personalizzata con supporto dedicato</li>
            </ul>

            <h3>5.2 Pagamenti</h3>
            <ul>
              <li>I prezzi sono quelli indicati al momento della sottoscrizione</li>
              <li>I pagamenti vengono elaborati tramite Stripe Inc.</li>
              <li>Le fatture vengono emesse secondo la periodicità del piano scelto</li>
            </ul>

            <h3>5.3 Rinnovo e cancellazione</h3>
            <ul>
              <li>L'Abbonamento si rinnova automaticamente salvo disdetta</li>
              <li>La cancellazione può essere effettuata in qualsiasi momento dall'area riservata</li>
              <li>In caso di cancellazione, l'accesso al Servizio rimane attivo fino alla fine del periodo già pagato</li>
              <li><strong>Non sono previsti rimborsi</strong> per periodi non utilizzati</li>
            </ul>

            <h3>5.4 Modifiche ai prezzi</h3>
            <ul>
              <li>Ci riserviamo il diritto di modificare i prezzi con preavviso di 30 giorni</li>
              <li>Le modifiche non si applicano ai cicli di fatturazione già in corso</li>
            </ul>
          </section>

          <section>
            <h2>6. Diritti di Proprietà Intellettuale</h2>

            <h3>6.1 Nostri diritti</h3>
            <ul>
              <li>La Piattaforma, il suo codice, il design, i loghi e i contenuti originali sono di proprietà esclusiva di CSRD-Comply S.r.l.</li>
              <li>Tutti i diritti non espressamente concessi sono riservati</li>
            </ul>

            <h3>6.2 Diritti del Cliente</h3>
            <ul>
              <li>Il Cliente mantiene tutti i diritti sui propri Dati caricati sulla Piattaforma</li>
              <li>I Report generati sono di proprietà del Cliente</li>
              <li>Il Cliente concede a CSRD-Comply una licenza limitata per elaborare i Dati ai fini della fornitura del Servizio</li>
            </ul>

            <h3>6.3 Feedback e suggerimenti</h3>
            <p>Qualsiasi feedback, suggerimento o idea fornita dal Cliente può essere utilizzata da CSRD-Comply senza obblighi di compenso o attribuzione.</p>
          </section>

          <section>
            <h2>7. Obblighi del Cliente</h2>
            <p>Il Cliente si impegna a:</p>
            <ul>
              <li>Utilizzare il Servizio solo per scopi leciti e conformi alla normativa applicabile</li>
              <li>Non tentare di eludere misure di sicurezza o limitazioni della Piattaforma</li>
              <li>Non caricare dati illeciti, diffamatori o che violano diritti di terzi</li>
              <li>Non utilizzare la Piattaforma per attività fraudolente o ingannevoli</li>
              <li>Non copiare, modificare, decompilare o fare reverse engineering della Piattaforma</li>
              <li>Non rivendere o sublicenziare l'accesso al Servizio</li>
              <li>Rispettare tutte le leggi e regolamenti applicabili, inclusi GDPR e CSRD</li>
            </ul>
          </section>

          <section>
            <h2>8. Dati e Privacy</h2>
            <p>Il trattamento dei dati personali è regolato dalla nostra <strong>Informativa sulla Privacy</strong>, disponibile all'indirizzo <Link href="/privacy" className="text-emerald-600 hover:text-emerald-700 underline">/privacy</Link>, che costituisce parte integrante dei presenti Termini.</p>
          </section>

          <section>
            <h2>9. Riservatezza e Sicurezza</h2>

            <h3>9.1 Misure di sicurezza</h3>
            <p>Adottiamo misure tecniche e organizzative adeguate per proteggere i Dati del Cliente, incluse:</p>
            <ul>
              <li>Crittografia end-to-end (TLS 1.3, AES-256)</li>
              <li>Backup giornalieri</li>
              <li>Controllo degli accessi basato su ruoli</li>
              <li>Monitoraggio continuo della sicurezza</li>
            </ul>

            <h3>9.2 Notifica di violazione</h3>
            <p>In caso di violazione dei dati che coinvolga i Dati del Cliente, verrà notificato entro 72 ore dalla scoperta, come richiesto dal GDPR.</p>
          </section>

          <section>
            <h2>10. Limitazioni di Responsabilità</h2>

            <h3>10.1 Esclusione di garanzie</h3>
            <p className="text-gray-500 italic">IL SERVIZIO È FORNITO "COSÌ COM'È" E "SECONDO DISPONIBILITÀ". NON GARANTIAMO CHE IL SERVIZIO SIA ININTERROTTO, PRIVO DI ERRORI O CHE I REPORT GENERATI SIANO COMPLETAMENTE ACCURATI.</p>

            <h3>10.2 Limitazione di responsabilità</h3>
            <p>IN NESSUN CASO CSRD-COMPLY SARÀ RESPONSABILE PER DANNI INDIRETTI, INCIDENTALI, SPECIALI, CONSEQUENZIALI O PUNITIVI, INCLUSI MANCATI PROFITTI O PERDITA DI DATI.</p>
            <p>La responsabilità totale di CSRD-Comply per qualsiasi reclamo derivante dall'uso del Servizio è limitata all'importo pagato dal Cliente nei 12 mesi precedenti il reclamo.</p>

            <h3>10.3 Esclusioni specifiche</h3>
            <p>CSRD-Comply non è responsabile per:</p>
            <ul>
              <li>L'accuratezza, completezza o conformità normativa dei Report generati</li>
              <li>Decisioni aziendali basate sui Report</li>
              <li>Danni derivanti da uso improprio della Piattaforma</li>
              <li>Interruzioni del servizio dovute a manutenzione, forza maggiore o terze parti</li>
            </ul>
          </section>

          <section>
            <h2>11. Indennizzo</h2>
            <p>Il Cliente si impegna a indennizzare e tenere indenne CSRD-Comply da qualsiasi reclamo, danno, perdita o costo derivante da:</p>
            <ul>
              <li>Violazione dei presenti Termini</li>
              <li>Utilizzo non autorizzato del Servizio</li>
              <li>Violazione di diritti di terzi</li>
              <li>Contenuti caricati che violano leggi o regolamenti</li>
            </ul>
          </section>

          <section>
            <h2>12. Risoluzione</h2>

            <h3>12.1 Risoluzione per inadempimento</h3>
            <p>CSRD-Comply può sospendere o terminare l'Account del Cliente con preavviso di 7 giorni in caso di:</p>
            <ul>
              <li>Violazione grave dei presenti Termini</li>
              <li>Mancato pagamento</li>
              <li>Attività fraudolente o illegali</li>
              <li>Violazione di diritti di proprietà intellettuale</li>
            </ul>

            <h3>12.2 Risoluzione immediata</h3>
            <p>CSRD-Comply può terminare immediatamente l'Account in caso di:</p>
            <ul>
              <li>Utilizzo della Piattaforma per attività illegali</li>
              <li>Tentativi di hacking o di elusione della sicurezza</li>
              <li>Diffusione di malware o contenuti dannosi</li>
            </ul>

            <h3>12.3 Conseguenze della risoluzione</h3>
            <p>Alla risoluzione:</p>
            <ul>
              <li>L'accesso al Servizio viene revocato</li>
              <li>I Dati del Cliente vengono conservati per 30 giorni prima della cancellazione definitiva</li>
              <li>Il Cliente può richiedere l'esportazione dei propri dati entro tale periodo</li>
            </ul>
          </section>

          <section>
            <h2>13. Disponibilità e Manutenzione</h2>

            <h3>13.1 SLA (Service Level Agreement)</h3>
            <ul>
              <li>Disponibilità target: 99.5% (esclusa manutenzione programmata)</li>
              <li>Manutenzione programmata: comunicata con almeno 48 ore di preavviso</li>
              <li>Manutenzione d'urgenza: comunicata appena possibile</li>
            </ul>

            <h3>13.2 Crediti di servizio</h3>
            <p>In caso di downtime superiore agli SLA previsti, il Cliente può richiedere crediti di servizio secondo la tabella disponibile nell'area riservata.</p>
          </section>

          <section>
            <h2>14. Modifiche ai Termini</h2>
            <p>Ci riserviamo il diritto di modificare i presenti Termini in qualsiasi momento. Le modifiche saranno comunicate via email o tramite avviso sulla Piattaforma almeno <strong>30 giorni</strong> prima dell'entrata in vigore.</p>
            <p>L'uso continuato del Servizio dopo l'entrata in vigore delle modifiche costituisce accettazione dei nuovi Termini.</p>
          </section>

          <section>
            <h2>15. Legge Applicabile e Foro Competente</h2>
            <p>I presenti Termini sono regolati dalla legge italiana. Per qualsiasi controversia derivante dai presenti Termini, il foro competente è esclusivamente quello di <strong>Milano</strong>.</p>
            <p>Prima di ricorrere all'autorità giudiziaria, le parti si impegnano a tentare una risoluzione amichevole della controversia entro 60 giorni.</p>
          </section>

          <section>
            <h2>16. Varie</h2>

            <h3>16.1 Intero accordo</h3>
            <p>I presenti Termini, insieme alla Privacy Policy, costituiscono l'intero accordo tra le parti.</p>

            <h3>16.2 Nullità parziale</h3>
            <p>Se una qualsiasi disposizione dei presenti Termini viene ritenuta invalida o inapplicabile, le restanti disposizioni rimangono pienamente valide.</p>

            <h3>16.3 Rinuncia</h3>
            <p>La mancata applicazione di una qualsiasi disposizione non costituisce rinuncia al diritto di applicarla in futuro.</p>

            <h3>16.4 Cessione</h3>
            <p>Il Cliente non può cedere i presenti Termini o i diritti derivanti senza il consenso scritto di CSRD-Comply.</p>

            <h3>16.5 Comunicazioni</h3>
            <p>Le comunicazioni ufficiali saranno inviate all'indirizzo email fornito durante la registrazione.</p>
          </section>

          <section>
            <h2>17. Contatti</h2>
            <p>Per qualsiasi domanda, reclamo o richiesta relativa ai presenti Termini di Servizio:</p>
            <p className="font-semibold text-gray-900">
              CSRD-Comply S.r.l.<br />
              Email: <strong>legal@csrd-comply.com</strong><br />
              PEC: [Indirizzo PEC]<br />
              Sede legale: [Indirizzo]
            </p>
          </section>

          <hr />

          <p className="text-sm text-gray-400 italic">
            Versione italiana prevalente in caso di conflitto interpretativo con traduzioni in altre lingue.
          </p>
        </div>
      </div>
    </div>
  )
}
