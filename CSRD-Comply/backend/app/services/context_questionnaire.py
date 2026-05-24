"""
CSRD Comply — Context Questionnaire Service (Step 8)

Valutazione di Contesto Aziendale per Doppia Materialità.
Questionario AI-adattivo che raccoglie il contesto dell'azienda.
Include:
- Fase 1: Domande statiche (settore, dimensioni, fatturato, paesi)
- Fase 2: Domande AI-generate per settore specifico
- Fase 3: Mappatura value chain upstream/downstream
"""
from typing import Optional, Dict, List, Any, Tuple
from sqlalchemy.orm import Session
from app.models import Company, CompanyContext
import json

# ── Settori NACE con domande specifiche ─────────────────────────
SECTOR_QUESTIONS: Dict[str, List[Dict]] = {
    "C": [  # Manufacturing
        {
            "id": "chemicals_used",
            "question": "Utilizzi sostanze chimiche pericolose nei processi produttivi?",
            "options": ["Si, regolarmente", "Si, occasionalmente", "No"],
            "esrs_topics": ["ESRS E2", "ESRS E5"],
            "phase": 2,
        },
        {
            "id": "waste_type",
            "question": "Quali tipologie di rifiuti produce principalmente?",
            "options": ["Rifiuti pericolosi", "Rifiuti non pericolosi", "Entrambi"],
            "esrs_topics": ["ESRS E5", "ESRS E2"],
            "phase": 2,
        },
        {
            "id": "energy_intensity",
            "question": "Qual è il tuo consumo energetico annuo approssimativo?",
            "options": ["<100 MWh", "100-500 MWh", "500-2000 MWh", ">2000 MWh"],
            "esrs_topics": ["ESRS E1"],
            "phase": 2,
        },
        {
            "id": "supplier_audit",
            "question": "Esegui audit ambientali/sociali sui tuoi fornitori principali?",
            "options": ["Si, regolarmente", "Si, occasionalmente", "No"],
            "esrs_topics": ["ESRS S2", "ESRS G1"],
            "phase": 2,
        },
    ],
    "M": [  # Office/Professional Services
        {
            "id": "extra_eu_suppliers",
            "question": "Quanti dei tuoi fornitori sono extra-EU?",
            "options": ["Nessuno", "Meno del 25%", "25-50%", "Più del 50%"],
            "esrs_topics": ["ESRS S2", "ESRS G1"],
            "phase": 2,
        },
        {
            "id": "data_center",
            "question": "Utilizzi data center o servizi cloud per le tue operazioni?",
            "options": ["Si, on-premise", "Si, cloud provider", "No"],
            "esrs_topics": ["ESRS E1"],
            "phase": 2,
        },
        {
            "id": "travel_frequency",
            "question": "Quanto viaggiano i tuoi dipendenti per lavoro?",
            "options": ["Raramente", "Qualche volta al mese", "Frequentemente"],
            "esrs_topics": ["ESRS E1", "ESRS S1"],
            "phase": 2,
        },
        {
            "id": "paper_usage",
            "question": "Qual è il tuo consumo annuo di carta?",
            "options": ["<100 risme", "100-500 risme", ">500 risme", "Non so"],
            "esrs_topics": ["ESRS E5"],
            "phase": 2,
        },
    ],
    "H": [  # Logistics/Transportation
        {
            "id": "fleet_type",
            "question": "Quale % della tua flotta è elettrica o ibrida?",
            "options": ["0%", "1-25%", "26-50%", ">50%"],
            "esrs_topics": ["ESRS E1", "ESRS E5"],
            "phase": 2,
        },
        {
            "id": "logistics_partners",
            "question": "Utilizzi partner logistici di terze parti?",
            "options": ["Si, principalmente", "Si, parzialmente", "No, tutto interno"],
            "esrs_topics": ["ESRS S2", "ESRS E1"],
            "phase": 2,
        },
        {
            "id": "fuel_type",
            "question": "Quale carburante utilizzi principalmente per la flotta?",
            "options": ["Diesel", "Benzina", "GNL/GNC", "Elettrico", "Misto"],
            "esrs_topics": ["ESRS E1"],
            "phase": 2,
        },
    ],
    "A": [  # Agriculture
        {
            "id": "land_use",
            "question": "Quanti ettari di terreno gestisci?",
            "options": ["<10 ha", "10-50 ha", "50-200 ha", ">200 ha"],
            "esrs_topics": ["ESRS E4", "ESRS E3"],
            "phase": 2,
        },
        {
            "id": "organic_certification",
            "question": "Hai certificazioni biologiche o sostenibili?",
            "options": ["Si", "No, ma in processo", "No"],
            "esrs_topics": ["ESRS E4", "ESRS E5"],
            "phase": 2,
        },
        {
            "id": "pesticide_use",
            "question": "Utilizzi pesticidi o fertilizzanti chimici?",
            "options": ["Si, regolarmente", "Si, occasionalmente", "No, solo biologico"],
            "esrs_topics": ["ESRS E2", "ESRS E4"],
            "phase": 2,
        },
    ],
    "F": [  # Construction
        {
            "id": "construction_waste",
            "question": "Quale % dei rifiuti da costruzione viene riciclata?",
            "options": ["<25%", "25-50%", "51-75%", ">75%"],
            "esrs_topics": ["ESRS E5", "ESRS E3"],
            "phase": 2,
        },
        {
            "id": "green_certifications",
            "question": "I tuoi progetti seguono certificazioni green (LEED, BREEAM, etc.)?",
            "options": ["Si, sempre", "Si, a volte", "No"],
            "esrs_topics": ["ESRS E1", "ESRS E5"],
            "phase": 2,
        },
        {
            "id": "material_sourcing",
            "question": "I materiali da costruzione provengono da fornitori certificati?",
            "options": ["Si, principalmente", "Parzialmente", "No"],
            "esrs_topics": ["ESRS E5", "ESRS S2"],
            "phase": 2,
        },
    ],
    "G": [  # Wholesale/Retail
        {
            "id": "product_sourcing",
            "question": "I tuoi prodotti provengono principalmente da paesi extra-EU?",
            "options": ["Si, principalmente", "Misto", "No, prevalentemente EU"],
            "esrs_topics": ["ESRS S2", "ESRS G1"],
            "phase": 2,
        },
        {
            "id": "packaging_material",
            "question": "Che tipo di imballaggio utilizzi principalmente?",
            "options": ["Plastica", "Carta/cartone", "Materiali riciclati", "Misto"],
            "esrs_topics": ["ESRS E5"],
            "phase": 2,
        },
        {
            "id": "product_lifetime",
            "question": "I tuoi prodotti hanno un ciclo di vita...?",
            "options": ["Corto (<1 anno)", "Medio (1-5 anni)", "Lungo (>5 anni)"],
            "esrs_topics": ["ESRS E5"],
            "phase": 2,
        },
    ],
}

# ── Domande universali per tutte le aziende (Fase 1) ──────────
UNIVERSAL_QUESTIONS = [
    {
        "id": "energy_supplier",
        "question": "Il tuo fornitore di energia elettrica utilizza fonti rinnovabili?",
        "options": ["100% rinnovabile", "Parzialmente rinnovabile", "Non so / Non dichiarato"],
        "esrs_topics": ["ESRS E1"],
        "phase": 1,
    },
    {
        "id": "employee_remote",
        "question": "Quanti dipendenti lavorano in smart working?",
        "options": ["Nessuno", "Meno del 25%", "25-50%", "Più del 50%"],
        "esrs_topics": ["ESRS E1", "ESRS S1"],
        "phase": 1,
    },
    {
        "id": "supplier_code",
        "question": "Hai un codice di condotta per i fornitori?",
        "options": ["Si", "No, ma in sviluppo", "No"],
        "esrs_topics": ["ESRS G1", "ESRS S2"],
        "phase": 1,
    },
    {
        "id": "gender_equality",
        "question": "Hai una politica di diversità e inclusione?",
        "options": ["Si, formalizzata", "Informale", "No"],
        "esrs_topics": ["ESRS S1", "ESRS G1"],
        "phase": 1,
    },
    {
        "id": "water_usage",
        "question": "La tua attività consuma acqua in modo significativo?",
        "options": ["Si, per processo produttivo", "Si, solo uso ufficio", "No"],
        "esrs_topics": ["ESRS E3"],
        "phase": 1,
    },
    {
        "id": "whistleblowing",
        "question": "Hai un canale di segnalazione (whistleblowing) attivo?",
        "options": ["Si", "No, ma in implementazione", "No"],
        "esrs_topics": ["ESRS G1"],
        "phase": 1,
    },
]

# ── Domande Fase 3: Value Chain ────────────────────────────────
VALUE_CHAIN_QUESTIONS = [
    {
        "id": "upstream_main_suppliers",
        "question": "Quanti fornitori diretti hai (approssimativamente)?",
        "options": ["<10", "10-50", "51-200", ">200"],
        "esrs_topics": ["ESRS S2", "ESRS G1"],
        "phase": 3,
    },
    {
        "id": "upstream_supplier_countries",
        "question": "In quante paesi diversi hai fornitori?",
        "options": ["Solo Italia/EU", "2-5 paesi", "6-20 paesi", "Più di 20 paesi"],
        "esrs_topics": ["ESRS S2", "ESRS E1"],
        "phase": 3,
    },
    {
        "id": "downstream_channels",
        "question": "Quali canali di vendita utilizzi?",
        "options": ["B2B diretto", "B2C diretto", "Distributori/rivenditori", "Tutti"],
        "esrs_topics": ["ESRS S4", "ESRS E1"],
        "phase": 3,
    },
    {
        "id": "downstream_end_users",
        "question": "I tuoi prodotti/servizi arrivano a consumatori finali?",
        "options": ["Si, principalmente", "Si, parzialmente", "No, solo B2B"],
        "esrs_topics": ["ESRS S4"],
        "phase": 3,
    },
    {
        "id": "stakeholder_engagement",
        "question": "Come interagisci con i tuoi stakeholder?",
        "options": ["Survey periodiche", "Incontri diretti", "Canali digitali", "Nessuna interazione formale"],
        "esrs_topics": ["ESRS S1", "ESRS S3", "ESRS G1"],
        "phase": 3,
    },
]

# ── Template per IA generativa delle domande ───────────────────
AI_QUESTION_TEMPLATES: Dict[str, List[str]] = {
    "C": [
        "Qual è il tuo principale processo produttivo e quali sono le materie prime critiche utilizzate?",
        "I tuoi prodotti richiedono certificazioni di sostenibilità specifiche (es. EPD, Ecolabel)?",
        "Quanta energia termica (vapore, acqua calda) utilizzi nei processi?",
        "Hai sistemi di recupero calore o cogenerazione?",
    ],
    "M": [
        "Quali certificazioni di sostenibilità possiedi (ESG rating, ISO 14001, etc.)?",
        "I tuoi clienti ti richiedono disclosure ESG come requisito contrattuale?",
        "Hai policy per ridurre l'impatto ambientale degli eventi e meeting?",
    ],
    "H": [
        "Qual è la vita media della tua flotta veicoli?",
        "Utilizzi sistemi di ottimizzazione dei carichi e dei percorsi?",
        "Hai magazzini con certificazione energetica?",
    ],
    "A": [
        "Utilizzi sistemi di irrigazione a risparmio idrico?",
        "Pratiche di rotazione delle colture o agroforestazione?",
        "Hai allevamenti intensivi? Quanti capi?",
    ],
    "F": [
        "Utilizzi calcestruzzo riciclato o materiali a basso impatto?",
        "Quanta energia consumano i tuoi cantieri?",
        "Hai un sistema di gestione rifiuti di cantiere certificato?",
    ],
    "G": [
        "Quali standard di sostenibilità richiedi ai tuoi fornitori di prodotti a marchio?",
        "Hai un programma di riduzione degli imballaggi?",
        "I tuoi punti vendita hanno certificazioni energetiche?",
    ],
}


class ContextQuestionnaireService:
    """Servizio per la gestione del questionario di contesto aziendale."""

    @staticmethod
    def get_sector_questions(sector_code: str) -> List[Dict]:
        """Recupera le domande specifiche per il settore NACE."""
        sector_letter = sector_code[0] if sector_code else ""
        return SECTOR_QUESTIONS.get(sector_letter, [])

    @staticmethod
    def get_all_questions(sector_code: str) -> List[Dict]:
        """Combina domande in fasi: universali + settoriali + value chain."""
        sector_letter = sector_code[0] if sector_code else ""
        sector_qs = SECTOR_QUESTIONS.get(sector_letter, [])

        return {
            "phases": [
                {
                    "id": 1,
                    "name": "Informazioni Generali",
                    "description": "Domande di base sul contesto aziendale",
                    "questions": UNIVERSAL_QUESTIONS,
                    "type": "universal",
                },
                {
                    "id": 2,
                    "name": f"Domande Settoriali ({sector_code})",
                    "description": "Domande specifiche per il settore di appartenenza",
                    "questions": sector_qs if sector_qs else ContextQuestionnaireService._get_default_sector_questions(),
                    "type": "sector_specific",
                },
                {
                    "id": 3,
                    "name": "Value Chain & Stakeholder",
                    "description": "Mappatura della catena del valore upstream/downstream",
                    "questions": VALUE_CHAIN_QUESTIONS,
                    "type": "value_chain",
                },
            ],
            "sector": sector_code,
            "sector_name": ContextQuestionnaireService._get_sector_name(sector_letter),
            "ai_generated_questions": AI_QUESTION_TEMPLATES.get(sector_letter, []),
        }

    @staticmethod
    def _get_default_sector_questions() -> List[Dict]:
        """Domande di fallback per settori non coperti."""
        return [
            {
                "id": "general_operations",
                "question": "Qual è la natura principale delle tue operazioni?",
                "options": ["Produzione", "Servizi", "Commerciale", "Altro"],
                "esrs_topics": ["ESRS E1", "ESRS S1"],
                "phase": 2,
            },
            {
                "id": "regulatory_framework",
                "question": "La tua attività è soggetta a regolamentazioni ambientali specifiche?",
                "options": ["Si, significative", "Si, parzialmente", "No"],
                "esrs_topics": ["ESRS E1", "ESRS G1"],
                "phase": 2,
            },
        ]

    @staticmethod
    def _get_sector_name(sector_letter: str) -> str:
        """Mappa la lettera NACE al nome del settore."""
        names = {
            "A": "Agricoltura, Silvicoltura e Pesca",
            "B": "Attività Estrattive",
            "C": "Manifatturiero",
            "D": "Fornitura Energia",
            "E": "Acqua e Rifiuti",
            "F": "Costruzioni",
            "G": "Commercio",
            "H": "Trasporti e Logistica",
            "I": "Servizi Alloggio e Ristorazione",
            "J": "ICT",
            "K": "Servizi Finanziari",
            "L": "Attività Immobiliari",
            "M": "Servizi Professionali e Tecnici",
            "N": "Noleggio e Servizi di Supporto",
            "O": "Pubblica Amministrazione",
            "P": "Istruzione",
            "Q": "Sanità e Assistenza Sociale",
            "R": "Arte e Intrattenimento",
            "S": "Altri Servizi",
        }
        return names.get(sector_letter, "Sconosciuto")

    @staticmethod
    def save_context(
        db: Session,
        company_id: str,
        value_chain_description: Optional[str] = None,
        key_activities: Optional[List[str]] = None,
        business_relationships: Optional[Dict] = None,
        geographical_scope: Optional[List[str]] = None,
        stakeholder_groups: Optional[List[str]] = None,
        questionnaire_responses: Optional[Dict] = None,
    ) -> CompanyContext:
        """Salva o aggiorna il contesto aziendale completo."""
        context = db.query(CompanyContext).filter(
            CompanyContext.company_id == company_id
        ).first()

        if not context:
            context = CompanyContext(company_id=company_id)

        if value_chain_description is not None:
            context.value_chain_description = value_chain_description
        if key_activities is not None:
            context.key_activities = key_activities
        if business_relationships is not None:
            context.business_relationships = business_relationships
        if geographical_scope is not None:
            context.geographical_scope = geographical_scope
        if stakeholder_groups is not None:
            context.stakeholder_groups = stakeholder_groups

        db.add(context)
        db.commit()
        db.refresh(context)

        # Se ci sono risposte al questionario, le salviamo come estensione
        if questionnaire_responses:
            ContextQuestionnaireService._save_questionnaire_responses(
                db, context, questionnaire_responses
            )

        return context

    @staticmethod
    def _save_questionnaire_responses(
        db: Session,
        context: CompanyContext,
        responses: Dict,
    ) -> None:
        """Salva le risposte al questionario come metadati aggiuntivi."""
        existing = getattr(context, 'questionnaire_responses', None) or {}
        if isinstance(existing, str):
            existing = json.loads(existing)

        existing.update(responses)
        context.value_chain_description = (
            context.value_chain_description or ""
        ) + f"\n\n--- Questionnaire Responses ---\n{json.dumps(responses, indent=2)}"

        db.add(context)
        db.commit()
        db.refresh(context)

    @staticmethod
    def get_context_summary(
        db: Session,
        company_id: str,
    ) -> Dict[str, Any]:
        """Restituisce un riepilogo del contesto aziendale per l'AI."""
        context = db.query(CompanyContext).filter(
            CompanyContext.company_id == company_id
        ).first()

        if not context:
            return {
                "status": "incomplete",
                "message": "Contesto aziendale non ancora compilato",
                "value_chain": None,
                "key_activities": [],
                "business_relationships": {},
                "geographical_scope": [],
                "stakeholder_groups": [],
            }

        return {
            "status": "complete",
            "value_chain": context.value_chain_description,
            "key_activities": context.key_activities or [],
            "business_relationships": context.business_relationships or {},
            "geographical_scope": context.geographical_scope or [],
            "stakeholder_groups": context.stakeholder_groups or [],
        }
