'use client'

import Link from 'next/link'
import { Leaf, ArrowLeft } from 'lucide-react'

export default function PrivacyPolicyPage() {
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
          Informativa sulla Privacy e Policy
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
          prose-h4:text-base prose-h4:mt-6 prose-h4:mb-2
          prose-p:text-gray-600 prose-p:leading-relaxed
          prose-strong:text-gray-900
          prose-ul:list-disc prose-ul:pl-6 prose-ul:text-gray-600
          prose-li:my-1
          prose-table:w-full prose-table:border-collapse prose-table:my-6
          prose-th:bg-gray-50 prose-th:px-4 prose-th:py-3 prose-th:text-left prose-th:text-sm prose-th:font-semibold prose-th:text-gray-700 prose-th:border prose-th:border-gray-200
          prose-td:px-4 prose-td:py-3 prose-td:text-sm prose-td:text-gray-600 prose-td:border prose-td:border-gray-200
          prose-hr:my-8 prose-hr:border-gray-200
        ">
          <section>
            <h2>1. Introduzione</h2>
            <p>
              CSRD-Comply ("noi", "nostro", "ci") è impegnata a proteggere la privacy degli utenti ("utente", "lei") che utilizzano la nostra piattaforma SaaS per la conformità alla Corporate Sustainability Reporting Directive (CSRD). La presente Informativa sulla Privacy descrive come raccogliamo, utilizziamo, divulghiamo e proteggiamo i dati personali degli utenti.
            </p>
          </section>

          <section>
            <h2>2. Titolare del Trattamento</h2>
            <p>Il titolare del trattamento dei dati è:</p>
            <p className="font-semibold text-gray-900">
              CSRD-Comply S.r.l.<br />
              Email: privacy@csrd-comply.com<br />
              Sede legale: [Indirizzo]<br />
              P.IVA: [Partita IVA]
            </p>
          </section>

          <section>
            <h2>3. Dati Raccolti</h2>

            <h3>3.1 Dati forniti volontariamente dall'utente</h3>
            <ul>
              <li>Nome e cognome</li>
              <li>Indirizzo email</li>
              <li>Nome dell'azienda</li>
              <li>Partita IVA</li>
              <li>Numero di telefono (opzionale)</li>
              <li>Password (crittografata)</li>
              <li>Settore industriale e dimensioni aziendali</li>
              <li>Documenti e dati relativi alla sostenibilità aziendale caricati sulla piattaforma</li>
            </ul>

            <h3>3.2 Dati raccolti automaticamente</h3>
            <ul>
              <li>Indirizzo IP</li>
              <li>Tipo di browser e versione</li>
              <li>Sistema operativo</li>
              <li>Pagine visitate e durata della visita</li>
              <li>Cookie e tecnologie di tracciamento</li>
              <li>Log di accesso e attività sulla piattaforma</li>
            </ul>

            <h3>3.3 Dati di fatturazione</h3>
            <ul>
              <li>Metodo di pagamento (tramite processore terzo)</li>
              <li>Storico delle transazioni</li>
              <li>Piano di abbonamento</li>
            </ul>
          </section>

          <section>
            <h2>4. Finalità del Trattamento</h2>
            <table>
              <thead>
                <tr>
                  <th>Finalità</th>
                  <th>Base Giuridica</th>
                </tr>
              </thead>
              <tbody>
                <tr><td>Fornire e gestire l'accesso alla piattaforma SaaS</td><td>Esecuzione del contratto</td></tr>
                <tr><td>Elaborare i report di sostenibilità CSRD</td><td>Esecuzione del contratto</td></tr>
                <tr><td>Assistenza tecnica e customer support</td><td>Esecuzione del contratto</td></tr>
                <tr><td>Fatturazione e gestione abbonamenti</td><td>Obbligo legale</td></tr>
                <tr><td>Inviare comunicazioni sul servizio</td><td>Legittimo interesse</td></tr>
                <tr><td>Migliorare la piattaforma e l'esperienza utente</td><td>Legittimo interesse</td></tr>
                <tr><td>Adempiere a obblighi normativi e legali</td><td>Obbligo legale</td></tr>
                <tr><td>Prevenire frodi e abusi</td><td>Legittimo interesse</td></tr>
              </tbody>
            </table>
          </section>

          <section>
            <h2>5. Base Giuridica del Trattamento</h2>
            <p>Il trattamento dei dati personali si basa su:</p>
            <ul>
              <li><strong>Esecuzione del contratto</strong>: per fornire i servizi richiesti</li>
              <li><strong>Consenso</strong>: per comunicazioni marketing (revocabile in qualsiasi momento)</li>
              <li><strong>Obbligo legale</strong>: per conformità a normative applicabili</li>
              <li><strong>Legittimo interesse</strong>: per migliorare i servizi e garantire la sicurezza</li>
            </ul>
          </section>

          <section>
            <h2>6. Conservazione dei Dati</h2>
            <p>Conserviamo i dati personali per il tempo necessario a soddisfare le finalità per cui sono stati raccolti:</p>
            <ul>
              <li><strong>Dati del profilo</strong>: per tutta la durata dell'abbonamento</li>
              <li><strong>Report e documenti</strong>: fino a 5 anni dopo la scadenza dell'abbonamento</li>
              <li><strong>Dati di fatturazione</strong>: 10 anni (per obblighi fiscali)</li>
              <li><strong>Log di sistema</strong>: 12 mesi</li>
              <li><strong>Cookie di sessione</strong>: durata della sessione</li>
            </ul>
          </section>

          <section>
            <h2>7. Condivisione dei Dati</h2>

            <h3>7.1 Categorie di destinatari</h3>
            <ul>
              <li>Fornitori di servizi cloud (hosting, storage)</li>
              <li>Processori di pagamento (per transazioni)</li>
              <li>Servizi di analytics (per miglioramento piattaforma)</li>
              <li>Autorità competenti (per obblighi legali)</li>
            </ul>

            <h3>7.2 Trasferimenti internazionali</h3>
            <p>
              I dati possono essere trasferiti al di fuori dello Spazio Economico Europeo (SEE) esclusivamente verso paesi che garantiscono un livello adeguato di protezione dei dati, o tramite l'adozione di Clausole Contrattuali Standard (SCC) approvate dalla Commissione Europea.
            </p>

            <h3>7.3 Nessuna vendita di dati</h3>
            <p><strong>CSRD-Comply non vende</strong> dati personali a terze parti.</p>
          </section>

          <section>
            <h2>8. Cookie e Tecnologie di Tracciamento</h2>

            <h3>8.1 Cookie tecnici (necessari)</h3>
            <ul>
              <li>Cookie di autenticazione e sessione</li>
              <li>Cookie di memorizzazione delle preferenze</li>
              <li>Cookie di sicurezza</li>
            </ul>

            <h3>8.2 Cookie analitici</h3>
            <ul>
              <li>Google Analytics / Matomo (anonimizzati)</li>
              <li>Heatmap di utilizzo della piattaforma</li>
            </ul>

            <h3>8.3 Gestione dei cookie</h3>
            <p>L'utente può gestire le preferenze sui cookie tramite il banner presente all'accesso o modificando le impostazioni del browser.</p>
          </section>

          <section>
            <h2>9. Diritti dell'Interessato (GDPR)</h2>
            <p>Ai sensi del Regolamento UE 2016/679 (GDPR), l'utente ha diritto a:</p>

            <table>
              <thead>
                <tr>
                  <th>Diritto</th>
                  <th>Descrizione</th>
                </tr>
              </thead>
              <tbody>
                <tr><td><strong>Accesso</strong></td><td>Ottenere conferma se i dati sono trattati e accedervi</td></tr>
                <tr><td><strong>Rettifica</strong></td><td>Correggere dati inesatti o incompleti</td></tr>
                <tr><td><strong>Cancellazione</strong></td><td>Richiedere la cancellazione dei dati (diritto all'oblio)</td></tr>
                <tr><td><strong>Limitazione</strong></td><td>Limitare il trattamento in determinate circostanze</td></tr>
                <tr><td><strong>Portabilità</strong></td><td>Ricevere i dati in formato strutturato e trasferirli</td></tr>
                <tr><td><strong>Opposizione</strong></td><td>Opporsi al trattamento per legittimo interesse o marketing</td></tr>
                <tr><td><strong>Revoca consenso</strong></td><td>Revocare il consenso in qualsiasi momento</td></tr>
              </tbody>
            </table>

            <h3>Come esercitare i diritti</h3>
            <p>
              Email: <strong>privacy@csrd-comply.com</strong><br />
              Tempo di risposta: entro 30 giorni
            </p>
            <p>L'utente ha inoltre il diritto di presentare reclamo al <strong>Garante per la Protezione dei Dati Personali</strong>.</p>
          </section>

          <section>
            <h2>10. Sicurezza dei Dati</h2>
            <p>Adottiamo misure di sicurezza tecniche e organizzative adeguate, tra cui:</p>
            <ul>
              <li>Crittografia dei dati in transito (TLS 1.3)</li>
              <li>Crittografia dei dati a riposo (AES-256)</li>
              <li>Controllo degli accessi basato su ruoli (RBAC)</li>
              <li>Backup giornalieri con retention policy</li>
              <li>Monitoraggio continuo delle minacce</li>
              <li>Audit di sicurezza periodici</li>
            </ul>
          </section>

          <section>
            <h2>11. Dati di Minori</h2>
            <p>I nostri servizi non sono destinati a minori di 18 anni. Non raccogliamo consapevolmente dati di minori. Se veniamo a conoscenza di tale raccolta, provvederemo alla cancellazione immediata.</p>
          </section>

          <section>
            <h2>12. Modifiche alla Privacy Policy</h2>
            <p>Ci riserviamo il diritto di modificare la presente policy. Le modifiche sostanziali verranno comunicate via email o tramite avviso sulla piattaforma almeno 30 giorni prima dell'entrata in vigore.</p>
          </section>

          <section>
            <h2>13. Reclami e Contatti</h2>
            <p>Per qualsiasi domanda, richiesta o reclamo relativo alla presente privacy policy:</p>
            <p>
              <strong>Email:</strong> privacy@csrd-comply.com<br />
              <strong>PEC:</strong> [Indirizzo PEC]<br />
              <strong>Telefono:</strong> [Numero telefono]
            </p>
          </section>

          <hr />

          <section>
            <h2>Allegato A - Sub-processori</h2>
            <table>
              <thead>
                <tr>
                  <th>Fornitore</th>
                  <th>Servizio</th>
                  <th>Località</th>
                </tr>
              </thead>
              <tbody>
                <tr><td>Railway / Supabase</td><td>Cloud hosting e database</td><td>UE</td></tr>
                <tr><td>Stripe Inc.</td><td>Pagamenti</td><td>USA (SCC)</td></tr>
                <tr><td>Auth0 / Supabase</td><td>Autenticazione</td><td>UE</td></tr>
                <tr><td>Sentry</td><td>Error tracking</td><td>USA (SCC)</td></tr>
              </tbody>
            </table>
          </section>

          <section>
            <h2>Allegato B - Definizioni</h2>
            <ul>
              <li><strong>CSRD</strong>: Corporate Sustainability Reporting Directive (Direttiva UE 2022/2464)</li>
              <li><strong>GDPR</strong>: General Data Protection Regulation (Regolamento UE 2016/679)</li>
              <li><strong>Dati personali</strong>: qualsiasi informazione relativa a persona fisica identificata o identificabile</li>
              <li><strong>Trattamento</strong>: qualsiasi operazione compiuta sui dati personali</li>
              <li><strong>Titolare</strong>: soggetto che determina finalità e mezzi del trattamento</li>
              <li><strong>Responsabile</strong>: soggetto che tratta dati per conto del titolare</li>
            </ul>
          </section>

          <hr />

          <p className="text-sm text-gray-400 italic">
            Questa informativa è disponibile anche nelle seguenti lingue: Inglese, Tedesco, Francese, Spagnolo, Olandese, Svedese, Polacco. In caso di conflitto interpretativo, prevale la versione in italiano.
          </p>
        </div>
      </div>
    </div>
  )
}
