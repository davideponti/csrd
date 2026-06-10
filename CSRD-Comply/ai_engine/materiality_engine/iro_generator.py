"""
CSRD Comply — IRO Generator (Step 9)

Identificazione di Impatti, Rischi e Opportunità (IRO) basata su:
- Contesto aziendale (settore, attività, value chain)
- Database di IRO predefiniti per settore NACE
- AI Generator per IRO specifici usando LLM (quando disponibile)
- Scoring iniziale automatico basato su benchmark di settore
"""
from typing import Optional, Dict, List, Any, Tuple
import json
import logging

logger = logging.getLogger(__name__)

# ── IRO Database predefinito per settore NACE ──────────────────
IRO_DATABASE: Dict[str, List[Dict]] = {
    # Manufacturing (C)
    "C": [
        {"id": "C_E1_IRO_001", "type": "impact", "topic": "ESRS E1",
         "name": "Emissioni dirette GHG da processi produttivi",
         "description": "Emissioni di gas serra dalla combustione di fossili nei processi manifatturieri",
         "default_impact_scale": 4, "default_financial_magnitude": 3, "severity": "high",
         "applicability_factors": {"min_employees": 0, "sectors": ["C"], "high_energy": True}},
        {"id": "C_E1_IRO_002", "type": "risk", "topic": "ESRS E1",
         "name": "Rischio carbon pricing e costi energetici",
         "description": "Aumento costi energetici e carbon pricing che impattano la redditività",
         "default_impact_scale": 3, "default_financial_magnitude": 4, "severity": "high",
         "applicability_factors": {"min_employees": 0, "sectors": ["C", "D", "E", "F", "H"]}},
        {"id": "C_E1_IRO_003", "type": "opportunity", "topic": "ESRS E1",
         "name": "Efficienza energetica e riduzione costi",
         "description": "Riduzione costi operativi tramite efficienza energetica e rinnovabili",
         "default_impact_scale": 3, "default_financial_magnitude": 4, "severity": "medium",
         "applicability_factors": {"min_employees": 0, "sectors": ["C", "D", "E", "F"]}},
        {"id": "C_E2_IRO_001", "type": "impact", "topic": "ESRS E2",
         "name": "Inquinamento atmosferico da emissioni industriali",
         "description": "Emissioni NOx, SOx, PM, COV dai processi produttivi",
         "default_impact_scale": 3, "default_financial_magnitude": 2, "severity": "medium",
         "applicability_factors": {"min_employees": 0, "sectors": ["C", "D", "E"]}},
        {"id": "C_E2_IRO_002", "type": "risk", "topic": "ESRS E2",
         "name": "Rischio normativo su limiti emissioni",
         "description": "Inasprimento normative su emissioni con potenziali sanzioni",
         "default_impact_scale": 3, "default_financial_magnitude": 3, "severity": "medium",
         "applicability_factors": {"min_employees": 0, "sectors": ["C", "D", "E"]}},
        {"id": "C_E2_IRO_003", "type": "impact", "topic": "ESRS E2",
         "name": "Contaminazione suolo e acque",
         "description": "Contaminazione suolo e falde acquifere da scarichi industriali",
         "default_impact_scale": 4, "default_financial_magnitude": 3, "severity": "high",
         "applicability_factors": {"min_employees": 0, "sectors": ["C", "E", "F"]}},
        {"id": "C_E3_IRO_001", "type": "impact", "topic": "ESRS E3",
         "name": "Consumo idrico nei processi produttivi",
         "description": "Prelievo e consumo acqua per processi industriali",
         "default_impact_scale": 3, "default_financial_magnitude": 2, "severity": "medium",
         "applicability_factors": {"min_employees": 0, "sectors": ["C", "D", "E"]}},
        {"id": "C_E5_IRO_001", "type": "impact", "topic": "ESRS E5",
         "name": "Produzione rifiuti industriali",
         "description": "Generazione rifiuti pericolosi e non dai processi produttivi",
         "default_impact_scale": 3, "default_financial_magnitude": 2, "severity": "medium",
         "applicability_factors": {"min_employees": 0, "sectors": ["C", "D", "E", "F"]}},
        {"id": "C_E5_IRO_002", "type": "opportunity", "topic": "ESRS E5",
         "name": "Economia circolare e recupero materiali",
         "description": "Riduzione costi e impatti tramite riciclo e recupero materiali",
         "default_impact_scale": 3, "default_financial_magnitude": 4, "severity": "high",
         "applicability_factors": {"min_employees": 0, "sectors": ["C", "E", "F"]}},
        {"id": "C_E4_IRO_001", "type": "impact", "topic": "ESRS E4",
         "name": "Impatto su biodiversità da approvvigionamento materie prime",
         "description": "Impatto su ecosistemi e biodiversità lungo la catena di approvvigionamento delle materie prime",
         "default_impact_scale": 3, "default_financial_magnitude": 2, "severity": "medium",
         "applicability_factors": {"min_employees": 0, "sectors": ["C", "F", "G"]}},
        {"id": "C_S1_IRO_001", "type": "impact", "topic": "ESRS S1",
         "name": "Salute e sicurezza dei lavoratori",
         "description": "Rischi per salute e sicurezza in ambiente produttivo",
         "default_impact_scale": 4, "default_financial_magnitude": 3, "severity": "high",
         "applicability_factors": {"min_employees": 0, "sectors": ["C", "D", "E", "F", "H"]}},
        {"id": "C_S1_IRO_002", "type": "risk", "topic": "ESRS S1",
         "name": "Attrazione e retention talenti",
         "description": "Difficoltà nel reperire personale qualificato",
         "default_impact_scale": 2, "default_financial_magnitude": 4, "severity": "high",
         "applicability_factors": {"min_employees": 10, "sectors": ["ALL"]}},
        {"id": "C_G1_IRO_001", "type": "risk", "topic": "ESRS G1",
         "name": "Conformità normativa e corruzione",
         "description": "Rischio non conformità con norme anti-corruzione e trasparenza",
         "default_impact_scale": 3, "default_financial_magnitude": 4, "severity": "high",
         "applicability_factors": {"min_employees": 0, "sectors": ["ALL"]}},
    ],
    "M": [
        {"id": "M_E1_IRO_001", "type": "impact", "topic": "ESRS E1",
         "name": "Emissioni da consumi energetici ufficio",
         "description": "Emissioni GHG da consumo elettrico e riscaldamento uffici",
         "default_impact_scale": 2, "default_financial_magnitude": 2, "severity": "low",
         "applicability_factors": {"min_employees": 0, "sectors": ["M", "N", "J", "K", "L"]}},
        {"id": "M_E1_IRO_002", "type": "impact", "topic": "ESRS E1",
         "name": "Emissioni da viaggi di lavoro",
         "description": "Emissioni GHG da viaggi aerei e automobilistici per lavoro",
         "default_impact_scale": 2, "default_financial_magnitude": 2, "severity": "low",
         "applicability_factors": {"min_employees": 0, "sectors": ["ALL"]}},
        {"id": "M_S1_IRO_001", "type": "impact", "topic": "ESRS S1",
         "name": "Wellbeing e work-life balance",
         "description": "Impatto su benessere dipendenti, stress e work-life balance",
         "default_impact_scale": 3, "default_financial_magnitude": 3, "severity": "medium",
         "applicability_factors": {"min_employees": 0, "sectors": ["ALL"]}},
        {"id": "M_S2_IRO_001", "type": "risk", "topic": "ESRS S2",
         "name": "Rischio diritti umani nella catena fornitura",
         "description": "Rischio fornitori extra-EU violino diritti umani",
         "default_impact_scale": 4, "default_financial_magnitude": 3, "severity": "high",
         "applicability_factors": {"min_employees": 0, "sectors": ["ALL"]}},
        {"id": "M_S4_IRO_001", "type": "impact", "topic": "ESRS S4",
         "name": "Protezione dati e privacy clienti",
         "description": "Impatto su consumatori per gestione dati personali e privacy",
         "default_impact_scale": 3, "default_financial_magnitude": 4, "severity": "high",
         "applicability_factors": {"min_employees": 0, "sectors": ["ALL"]}},
        {"id": "M_G1_IRO_001", "type": "risk", "topic": "ESRS G1",
         "name": "Conformità GDPR e cybersecurity",
         "description": "Rischio finanziario e reputazionale da violazione dati",
         "default_impact_scale": 3, "default_financial_magnitude": 4, "severity": "high",
         "applicability_factors": {"min_employees": 0, "sectors": ["ALL"]}},
    ],
    "H": [
        {"id": "H_E1_IRO_001", "type": "impact", "topic": "ESRS E1",
         "name": "Emissioni da flotta veicoli",
         "description": "Emissioni GHG significative dalla flotta veicoli trasporto merci",
         "default_impact_scale": 4, "default_financial_magnitude": 4, "severity": "high",
         "applicability_factors": {"min_employees": 0, "sectors": ["H"]}},
        {"id": "H_E1_IRO_002", "type": "opportunity", "topic": "ESRS E1",
         "name": "Transizione a flotta elettrica/ibrida",
         "description": "Riduzione emissioni e costi con elettrificazione flotta",
         "default_impact_scale": 3, "default_financial_magnitude": 4, "severity": "high",
         "applicability_factors": {"min_employees": 0, "sectors": ["H"]}},
        {"id": "H_S1_IRO_001", "type": "impact", "topic": "ESRS S1",
         "name": "Salute e sicurezza autisti",
         "description": "Condizioni lavoro autisti, sicurezza stradale e orari",
         "default_impact_scale": 4, "default_financial_magnitude": 3, "severity": "high",
         "applicability_factors": {"min_employees": 0, "sectors": ["H"]}},
    ],
    "A": [
        {"id": "A_E1_IRO_001", "type": "impact", "topic": "ESRS E1",
         "name": "Emissioni da attività agricole",
         "description": "Emissioni metano e protossido azoto da attività zootecniche e fertilizzanti",
         "default_impact_scale": 4, "default_financial_magnitude": 3, "severity": "high",
         "applicability_factors": {"min_employees": 0, "sectors": ["A"]}},
        {"id": "A_E4_IRO_001", "type": "impact", "topic": "ESRS E4",
         "name": "Impatto su biodiversità e suolo",
         "description": "Impatto pratiche agricole su biodiversità locale e salute suolo",
         "default_impact_scale": 4, "default_financial_magnitude": 3, "severity": "high",
         "applicability_factors": {"min_employees": 0, "sectors": ["A"]}},
        {"id": "A_E3_IRO_001", "type": "impact", "topic": "ESRS E3",
         "name": "Consumo idrico per irrigazione",
         "description": "Consumo significativo acqua per irrigazione in aree con stress idrico",
         "default_impact_scale": 4, "default_financial_magnitude": 4, "severity": "high",
         "applicability_factors": {"min_employees": 0, "sectors": ["A"]}},
    ],
    "F": [
        {"id": "F_E1_IRO_001", "type": "impact", "topic": "ESRS E1",
         "name": "Emissioni da cantieri e macchinari",
         "description": "Emissioni GHG da macchinari pesanti e consumi energetici nei cantieri",
         "default_impact_scale": 3, "default_financial_magnitude": 3, "severity": "medium",
         "applicability_factors": {"min_employees": 0, "sectors": ["F"]}},
        {"id": "F_E5_IRO_001", "type": "impact", "topic": "ESRS E5",
         "name": "Rifiuti da costruzione e demolizione",
         "description": "Grande volume rifiuti inerti e materiali da costruzione",
         "default_impact_scale": 3, "default_financial_magnitude": 3, "severity": "medium",
         "applicability_factors": {"min_employees": 0, "sectors": ["F"]}},
        {"id": "F_E5_IRO_002", "type": "opportunity", "topic": "ESRS E5",
         "name": "Costruzioni sostenibili e certificazioni green",
         "description": "Differenziazione con edifici a basso impatto e certificazioni",
         "default_impact_scale": 3, "default_financial_magnitude": 4, "severity": "high",
         "applicability_factors": {"min_employees": 0, "sectors": ["F"]}},
        {"id": "F_S1_IRO_001", "type": "impact", "topic": "ESRS S1",
         "name": "Sicurezza nei cantieri",
         "description": "Rischi per salute e sicurezza lavoratori edili nei cantieri",
         "default_impact_scale": 4, "default_financial_magnitude": 3, "severity": "high",
         "applicability_factors": {"min_employees": 0, "sectors": ["F"]}},
    ],
    "G": [
        {"id": "G_E1_IRO_001", "type": "impact", "topic": "ESRS E1",
         "name": "Emissioni logistiche e trasporto merci",
         "description": "Emissioni GHG da trasporto merci e logistica distributiva",
         "default_impact_scale": 3, "default_financial_magnitude": 3, "severity": "medium",
         "applicability_factors": {"min_employees": 0, "sectors": ["G"]}},
        {"id": "G_E5_IRO_001", "type": "impact", "topic": "ESRS E5",
         "name": "Rifiuti da imballaggio e prodotti invenduti",
         "description": "Generazione rifiuti da imballaggi e prodotti a fine vita",
         "default_impact_scale": 3, "default_financial_magnitude": 2, "severity": "medium",
         "applicability_factors": {"min_employees": 0, "sectors": ["G"]}},
        {"id": "G_S2_IRO_001", "type": "risk", "topic": "ESRS S2",
         "name": "Condizioni lavoratori nella supply chain",
         "description": "Rischio condizioni lavoro inadeguate nella catena fornitura globale",
         "default_impact_scale": 4, "default_financial_magnitude": 3, "severity": "high",
         "applicability_factors": {"min_employees": 0, "sectors": ["G"]}},
    ],
}

# ── IRO generici applicabili a tutte le aziende ────────────────
# Copertura completa di TUTTI i topic ESRS (E1-E5, S1-S4, G1)
# per garantire che ogni standard abbia almeno un IRO di riferimento.
GENERIC_IROS = [
    # ─ ESRS E1: Climate Change ─
    {"id": "GEN_E1_IRO_001", "type": "impact", "topic": "ESRS E1",
     "name": "Emissioni indirette GHG (Scope 3)",
     "description": "Emissioni GHG indirette dalla catena del valore (fornitori, clienti, trasporti)",
     "default_impact_scale": 2, "default_financial_magnitude": 2, "severity": "medium"},
    {"id": "GEN_E1_IRO_002", "type": "risk", "topic": "ESRS E1",
     "name": "Rischio transizione climatica",
     "description": "Rischio di transizione verso economia low-carbon (regolatorio, mercato, tecnologico)",
     "default_impact_scale": 2, "default_financial_magnitude": 3, "severity": "medium"},
    # ─ ESRS E2: Pollution ─
    {"id": "GEN_E2_IRO_001", "type": "impact", "topic": "ESRS E2",
     "name": "Inquinamento da operazioni aziendali",
     "description": "Potenziale inquinamento di aria, acqua e suolo derivante dalle attività aziendali e della catena del valore",
     "default_impact_scale": 2, "default_financial_magnitude": 2, "severity": "low"},
    # ─ ESRS E3: Water and Marine Resources ─
    {"id": "GEN_E3_IRO_001", "type": "impact", "topic": "ESRS E3",
     "name": "Consumo idrico operativo",
     "description": "Consumo acqua nelle operations aziendali e impatto su risorse idriche locali",
     "default_impact_scale": 2, "default_financial_magnitude": 1, "severity": "low"},
    # ─ ESRS E4: Biodiversity and Ecosystems ─
    {"id": "GEN_E4_IRO_001", "type": "impact", "topic": "ESRS E4",
     "name": "Dipendenza da servizi ecosistemici",
     "description": "Dipendenza delle operazioni aziendali da servizi ecosistemici (acqua pulita, suolo fertile, impollinazione)",
     "default_impact_scale": 2, "default_financial_magnitude": 2, "severity": "low"},
    {"id": "GEN_E4_IRO_002", "type": "risk", "topic": "ESRS E4",
     "name": "Rischio biodiversità nella supply chain",
     "description": "Rischio reputazionale e operativo da impatti su biodiversità lungo la catena di fornitura",
     "default_impact_scale": 2, "default_financial_magnitude": 2, "severity": "low"},
    # ─ ESRS E5: Resource Use and Circular Economy ─
    {"id": "GEN_E5_IRO_001", "type": "impact", "topic": "ESRS E5",
     "name": "Consumo di risorse e rifiuti",
     "description": "Utilizzo di materie prime vergini e generazione di rifiuti nelle operations",
     "default_impact_scale": 2, "default_financial_magnitude": 2, "severity": "low"},
    {"id": "GEN_E5_IRO_002", "type": "opportunity", "topic": "ESRS E5",
     "name": "Opportunità di economia circolare",
     "description": "Riduzione costi e differenziazione competitiva tramite design circolare e riciclo",
     "default_impact_scale": 2, "default_financial_magnitude": 3, "severity": "medium"},
    # ─ ESRS S1: Own Workforce ─
    {"id": "GEN_S1_IRO_001", "type": "impact", "topic": "ESRS S1",
     "name": "Condizioni di lavoro e diritti dei dipendenti",
     "description": "Impatto su condizioni di lavoro, salute, sicurezza e diritti del personale dipendente",
     "default_impact_scale": 2, "default_financial_magnitude": 2, "severity": "medium"},
    {"id": "GEN_S1_IRO_002", "type": "risk", "topic": "ESRS S1",
     "name": "Rischio attrazione e retention talenti",
     "description": "Difficoltà nel attrarre e trattenere personale qualificato in un mercato competitivo",
     "default_impact_scale": 2, "default_financial_magnitude": 3, "severity": "medium"},
    # ─ ESRS S2: Workers in the Value Chain ─
    {"id": "GEN_S2_IRO_001", "type": "risk", "topic": "ESRS S2",
     "name": "Rischio diritti umani nella supply chain",
     "description": "Rischio di violazione dei diritti umani dei lavoratori nella catena di fornitura",
     "default_impact_scale": 3, "default_financial_magnitude": 3, "severity": "high"},
    # ─ ESRS S3: Affected Communities ─
    {"id": "GEN_S3_IRO_001", "type": "impact", "topic": "ESRS S3",
     "name": "Impatto sulle comunità locali",
     "description": "Impatto delle operazioni aziendali sulle comunità locali circostanti",
     "default_impact_scale": 2, "default_financial_magnitude": 1, "severity": "low"},
    # ─ ESRS S4: Consumers and End-users ─
    {"id": "GEN_S4_IRO_001", "type": "impact", "topic": "ESRS S4",
     "name": "Impatto su consumatori e utenti finali",
     "description": "Impatto dei prodotti/servizi su salute, sicurezza e benessere di consumatori e utenti finali",
     "default_impact_scale": 2, "default_financial_magnitude": 2, "severity": "low"},
    # ─ ESRS G1: Business Conduct ─
    {"id": "GEN_G1_IRO_001", "type": "risk", "topic": "ESRS G1",
     "name": "Rischio reputazionale da non conformità ESG",
     "description": "Danno reputazionale da mancata conformità a standard ESG e norme di business conduct",
     "default_impact_scale": 2, "default_financial_magnitude": 3, "severity": "medium"},
    {"id": "GEN_G1_IRO_002", "type": "risk", "topic": "ESRS G1",
     "name": "Rischio corruzione e trasparenza",
     "description": "Rischio sanzioni e danno reputazionale da pratiche di corruzione o mancata trasparenza",
     "default_impact_scale": 3, "default_financial_magnitude": 4, "severity": "high"},
]

# ── IRO di fallback per settori non coperti nel database ──────
GENERIC_SECTOR_IROS: Dict[str, List[Dict]] = {
    # Energy Supply (D)
    "D": [
        {"id": "D_E1_IRO_001", "type": "impact", "topic": "ESRS E1",
         "name": "Emissioni GHG da produzione energetica",
         "description": "Emissioni significative di CO2 e GHG dalla generazione di energia da fonti fossili",
         "default_impact_scale": 4, "default_financial_magnitude": 4, "severity": "high",
         "applicability_factors": {"min_employees": 0, "sectors": ["D"]}},
        {"id": "D_E1_IRO_002", "type": "opportunity", "topic": "ESRS E1",
         "name": "Transizione a rinnovabili",
         "description": "Opportunità di crescita nell'energia da fonti rinnovabili e decarbonizzazione",
         "default_impact_scale": 3, "default_financial_magnitude": 5, "severity": "high",
         "applicability_factors": {"min_employees": 0, "sectors": ["D"]}},
        {"id": "D_E2_IRO_001", "type": "impact", "topic": "ESRS E2",
         "name": "Inquinamento atmosferico da combustione",
         "description": "Emissioni NOx, SOx, PM da centrali e impianti di combustione",
         "default_impact_scale": 3, "default_financial_magnitude": 3, "severity": "medium",
         "applicability_factors": {"min_employees": 0, "sectors": ["D"]}},
        {"id": "D_G1_IRO_001", "type": "risk", "topic": "ESRS G1",
         "name": "Rischio normativo su concessioni e licenze",
         "description": "Rischio revoca concessioni e licenze per mancata conformità ESG",
         "default_impact_scale": 3, "default_financial_magnitude": 4, "severity": "high",
         "applicability_factors": {"min_employees": 0, "sectors": ["D"]}},
    ],
    # Water & Waste (E)
    "E": [
        {"id": "E_E3_IRO_001", "type": "impact", "topic": "ESRS E3",
         "name": "Gestione risorse idriche",
         "description": "Impatto su disponibilità e qualità delle risorse idriche",
         "default_impact_scale": 4, "default_financial_magnitude": 3, "severity": "high",
         "applicability_factors": {"min_employees": 0, "sectors": ["E"]}},
        {"id": "E_E5_IRO_001", "type": "impact", "topic": "ESRS E5",
         "name": "Trattamento e smaltimento rifiuti",
         "description": "Impatto ambientale da gestione e smaltimento rifiuti solidi e liquidi",
         "default_impact_scale": 4, "default_financial_magnitude": 3, "severity": "high",
         "applicability_factors": {"min_employees": 0, "sectors": ["E"]}},
        {"id": "E_E2_IRO_001", "type": "impact", "topic": "ESRS E2",
         "name": "Inquinamento acque e suolo",
         "description": "Rischio contaminazione da scarichi e percolati",
         "default_impact_scale": 4, "default_financial_magnitude": 3, "severity": "high",
         "applicability_factors": {"min_employees": 0, "sectors": ["E"]}},
    ],
    # ICT (J)
    "J": [
        {"id": "J_E1_IRO_001", "type": "impact", "topic": "ESRS E1",
         "name": "Consumo energetico data center",
         "description": "Elevato consumo elettrico per data center e infrastrutture IT",
         "default_impact_scale": 3, "default_financial_magnitude": 3, "severity": "medium",
         "applicability_factors": {"min_employees": 0, "sectors": ["J"]}},
        {"id": "J_S1_IRO_001", "type": "impact", "topic": "ESRS S1",
         "name": "Benessere digitale e carico lavoro",
         "description": "Rischio burnout e stress da iperconnessione e carichi di lavoro intensivi",
         "default_impact_scale": 3, "default_financial_magnitude": 2, "severity": "medium",
         "applicability_factors": {"min_employees": 0, "sectors": ["J", "M"]}},
        {"id": "J_S4_IRO_001", "type": "risk", "topic": "ESRS S4",
         "name": "Privacy e protezione dati utenti",
         "description": "Rischio violazione dati personali e sanzioni GDPR",
         "default_impact_scale": 3, "default_financial_magnitude": 4, "severity": "high",
         "applicability_factors": {"min_employees": 0, "sectors": ["J", "M", "K"]}},
        {"id": "J_E5_IRO_001", "type": "impact", "topic": "ESRS E5",
         "name": "Rifiuti elettronici (e-waste)",
         "description": "Smaltimento apparecchiature IT e componenti elettroniche",
         "default_impact_scale": 2, "default_financial_magnitude": 1, "severity": "low",
         "applicability_factors": {"min_employees": 0, "sectors": ["ALL"]}},
    ],
    # Finance & Insurance (K)
    "K": [
        {"id": "K_E1_IRO_001", "type": "impact", "topic": "ESRS E1",
         "name": "Impronta carbonio finanziata (Scope 3)",
         "description": "Emissioni GHG indirette da portafoglio investimenti e finanziamenti",
         "default_impact_scale": 3, "default_financial_magnitude": 4, "severity": "high",
         "applicability_factors": {"min_employees": 0, "sectors": ["K"]}},
        {"id": "K_G1_IRO_001", "type": "risk", "topic": "ESRS G1",
         "name": "Rischio conformità e antiriciclaggio",
         "description": "Rischio sanzioni da mancata conformità normativa finanziaria e antiriciclaggio",
         "default_impact_scale": 3, "default_financial_magnitude": 5, "severity": "high",
         "applicability_factors": {"min_employees": 0, "sectors": ["K"]}},
        {"id": "K_S4_IRO_001", "type": "impact", "topic": "ESRS S4",
         "name": "Trasparenza e tutela consumatori finanziari",
         "description": "Impatto su consumatori per trasparenza prodotti finanziari e assicurativi",
         "default_impact_scale": 3, "default_financial_magnitude": 4, "severity": "high",
         "applicability_factors": {"min_employees": 0, "sectors": ["K"]}},
    ],
    # Hospitality (I)
    "I": [
        {"id": "I_E1_IRO_001", "type": "impact", "topic": "ESRS E1",
         "name": "Consumi energetici strutture ricettive",
         "description": "Elevati consumi energetici per riscaldamento, climatizzazione e servizi",
         "default_impact_scale": 3, "default_financial_magnitude": 3, "severity": "medium",
         "applicability_factors": {"min_employees": 0, "sectors": ["I"]}},
        {"id": "I_E5_IRO_001", "type": "impact", "topic": "ESRS E5",
         "name": "Rifiuti e spreco alimentare",
         "description": "Produzione rifiuti e spreco alimentare in strutture ristorazione e ricettive",
         "default_impact_scale": 3, "default_financial_magnitude": 2, "severity": "medium",
         "applicability_factors": {"min_employees": 0, "sectors": ["I"]}},
        {"id": "I_S1_IRO_001", "type": "impact", "topic": "ESRS S1",
         "name": "Condizioni lavoro stagionali",
         "description": "Gestione personale stagionale, turni e condizioni di lavoro",
         "default_impact_scale": 3, "default_financial_magnitude": 2, "severity": "medium",
         "applicability_factors": {"min_employees": 0, "sectors": ["I", "A"]}},
    ],
    # Real Estate (L)
    "L": [
        {"id": "L_E1_IRO_001", "type": "impact", "topic": "ESRS E1",
         "name": "Efficienza energetica edifici",
         "description": "Impatto energetico del portafoglio immobiliare e costi di gestione",
         "default_impact_scale": 3, "default_financial_magnitude": 4, "severity": "high",
         "applicability_factors": {"min_employees": 0, "sectors": ["L", "F"]}},
        {"id": "L_E1_IRO_002", "type": "opportunity", "topic": "ESRS E1",
         "name": "Riqualificazione energetica immobili",
         "description": "Opportunità di valorizzazione tramite efficientamento e certificazioni green",
         "default_impact_scale": 2, "default_financial_magnitude": 4, "severity": "medium",
         "applicability_factors": {"min_employees": 0, "sectors": ["L"]}},
        {"id": "L_S4_IRO_001", "type": "impact", "topic": "ESRS S4",
         "name": "Accessibilità e inclusività spazi",
         "description": "Accessibilità edifici per persone con disabilità e inclusione sociale",
         "default_impact_scale": 2, "default_financial_magnitude": 2, "severity": "low",
         "applicability_factors": {"min_employees": 0, "sectors": ["L"]}},
    ],
}


# ── Benchmark di settore per scoring iniziale ──────────────────
SECTOR_BENCHMARKS: Dict[str, Dict[str, Any]] = {
    "C": {
        "name": "Manifatturiero",
        "carbon_intensity": "high",
        "water_intensity": "high",
        "waste_intensity": "high",
        "social_risk": "medium",
        "governance_risk": "medium",
        "typical_impact_range": (3.0, 4.5),
        "typical_financial_range": (2.5, 4.0),
    },
    "M": {
        "name": "Servizi Professionali",
        "carbon_intensity": "low",
        "water_intensity": "low",
        "waste_intensity": "low",
        "social_risk": "medium",
        "governance_risk": "high",
        "typical_impact_range": (1.5, 3.0),
        "typical_financial_range": (2.0, 3.5),
    },
    "H": {
        "name": "Trasporti e Logistica",
        "carbon_intensity": "high",
        "water_intensity": "low",
        "waste_intensity": "medium",
        "social_risk": "high",
        "governance_risk": "medium",
        "typical_impact_range": (3.0, 4.5),
        "typical_financial_range": (3.0, 4.5),
    },
    "A": {
        "name": "Agricoltura",
        "carbon_intensity": "high",
        "water_intensity": "high",
        "waste_intensity": "medium",
        "social_risk": "medium",
        "governance_risk": "low",
        "typical_impact_range": (3.5, 5.0),
        "typical_financial_range": (2.5, 4.0),
    },
    "F": {
        "name": "Costruzioni",
        "carbon_intensity": "high",
        "water_intensity": "low",
        "waste_intensity": "high",
        "social_risk": "high",
        "governance_risk": "medium",
        "typical_impact_range": (2.5, 4.0),
        "typical_financial_range": (2.5, 4.0),
    },
    "G": {
        "name": "Commercio",
        "carbon_intensity": "medium",
        "water_intensity": "low",
        "waste_intensity": "medium",
        "social_risk": "medium",
        "governance_risk": "high",
        "typical_impact_range": (2.0, 3.5),
        "typical_financial_range": (2.0, 3.5),
    },
    "B": {
        "name": "Attività Estrattive",
        "carbon_intensity": "high",
        "water_intensity": "high",
        "waste_intensity": "high",
        "social_risk": "high",
        "governance_risk": "high",
        "typical_impact_range": (3.5, 5.0),
        "typical_financial_range": (3.0, 5.0),
    },
    "D": {
        "name": "Fornitura Energia",
        "carbon_intensity": "high",
        "water_intensity": "medium",
        "waste_intensity": "medium",
        "social_risk": "low",
        "governance_risk": "medium",
        "typical_impact_range": (3.0, 5.0),
        "typical_financial_range": (3.0, 4.5),
    },
    "E": {
        "name": "Acqua e Rifiuti",
        "carbon_intensity": "medium",
        "water_intensity": "high",
        "waste_intensity": "high",
        "social_risk": "medium",
        "governance_risk": "medium",
        "typical_impact_range": (2.5, 4.5),
        "typical_financial_range": (2.5, 4.0),
    },
    "I": {
        "name": "Servizi Alloggio e Ristorazione",
        "carbon_intensity": "medium",
        "water_intensity": "high",
        "waste_intensity": "medium",
        "social_risk": "medium",
        "governance_risk": "low",
        "typical_impact_range": (2.0, 3.5),
        "typical_financial_range": (2.0, 3.0),
    },
    "J": {
        "name": "ICT",
        "carbon_intensity": "low",
        "water_intensity": "low",
        "waste_intensity": "low",
        "social_risk": "medium",
        "governance_risk": "high",
        "typical_impact_range": (1.5, 3.0),
        "typical_financial_range": (2.0, 3.5),
    },
    "K": {
        "name": "Servizi Finanziari",
        "carbon_intensity": "low",
        "water_intensity": "low",
        "waste_intensity": "low",
        "social_risk": "medium",
        "governance_risk": "very_high",
        "typical_impact_range": (1.5, 3.0),
        "typical_financial_range": (3.0, 5.0),
    },
    "L": {
        "name": "Attività Immobiliari",
        "carbon_intensity": "medium",
        "water_intensity": "low",
        "waste_intensity": "medium",
        "social_risk": "low",
        "governance_risk": "medium",
        "typical_impact_range": (2.0, 3.5),
        "typical_financial_range": (2.5, 4.0),
    },
    "N": {
        "name": "Noleggio e Servizi di Supporto",
        "carbon_intensity": "low",
        "water_intensity": "low",
        "waste_intensity": "low",
        "social_risk": "medium",
        "governance_risk": "medium",
        "typical_impact_range": (1.5, 3.0),
        "typical_financial_range": (2.0, 3.5),
    },
}



class IROGenerator:
    """Generatore di IRO basato su contesto aziendale, database settoriale e AI."""

    @staticmethod
    def get_sector_code(nace_code: str) -> str:
        """Estrae la lettera del settore NACE."""
        return nace_code[0] if nace_code else ""

    @staticmethod
    def get_iro_database_by_sector(sector_code: str) -> List[Dict]:
        """Recupera gli IRO predefiniti per il settore."""
        sector_letter = IROGenerator.get_sector_code(sector_code)
        return IRO_DATABASE.get(sector_letter, [])

    @staticmethod
    def get_sector_benchmark(sector_code: str) -> Dict[str, Any]:
        """Recupera i benchmark di settore per scoring iniziale."""
        sector_letter = IROGenerator.get_sector_code(sector_code)
        return SECTOR_BENCHMARKS.get(sector_letter, {
            "name": "Generico",
            "carbon_intensity": "medium",
            "water_intensity": "medium",
            "waste_intensity": "medium",
            "social_risk": "medium",
            "governance_risk": "medium",
            "typical_impact_range": (2.0, 3.5),
            "typical_financial_range": (2.0, 3.5),
        })

    @staticmethod
    def generate_iro_scaffold(
        topic: str = "",
        subtopic: str = "",
        context: Optional[Dict[str, Any]] = None,
    ) -> Dict[str, Any]:
        """Generate a scaffold IRO from topic and context."""
        context = context or {}
        sector = context.get("sector", "")
        sector_letter = IROGenerator.get_sector_code(sector)

        # Find matching IRO from database
        matched = None
        sector_iros = IRO_DATABASE.get(sector_letter, [])
        for iro in sector_iros:
            if iro["topic"] == topic:
                matched = iro
                break
        if not matched:
            for iro in GENERIC_IROS:
                if iro["topic"] == topic:
                    matched = iro
                    break

        if matched:
            return {
                "id": matched["id"],
                "type": matched["type"],
                "topic": matched["topic"],
                "esrs_standard": matched["topic"],
                "name": matched["name"],
                "description": matched["description"],
                "severity": matched["severity"],
                "impact_scale": matched.get("default_impact_scale", 3),
                "financial_magnitude": matched.get("default_financial_magnitude", 3),
                "subtopic": subtopic or topic,
                "source": "database",
                "impacts": [],
                "risks": [],
                "opportunities": [],
            }

        # Fallback: generate from topic
        return {
            "id": f"GEN_{topic.replace(' ', '_')}_001",
            "type": "impact",
            "topic": topic,
            "esrs_standard": topic,
            "name": f"Generic IRO for {topic}",
            "description": f"IRO related to {topic} - {subtopic}",
            "severity": "medium",
            "impact_scale": 2,
            "financial_magnitude": 2,
            "subtopic": subtopic,
            "source": "generated",
            "impacts": [],
            "risks": [],
            "opportunities": [],
        }

    @staticmethod
    def generate_iros_for_company(
        company_sector: str,
        employee_count: Optional[int] = None,
        turnover: Optional[float] = None,
        company_context: Optional[Dict[str, Any]] = None,
        use_ai: bool = False,
    ) -> List[Dict]:
        """Genera la lista completa di IRO per un'azienda.

        Args:
            company_sector: Codice NACE
            employee_count: Numero dipendenti
            turnover: Fatturato annuo
            company_context: Contesto aziendale (value chain, activities, etc.)
            use_ai: Se True, usa LLM per generare IRO aggiuntivi

        Returns:
            Lista di IRO con scoring iniziale applicato
        """
        sector_letter = IROGenerator.get_sector_code(company_sector)
        benchmark = IROGenerator.get_sector_benchmark(company_sector)

        # 1. IRO del settore (filtrati per applicabilità) o fallback settoriale
        sector_iros = IRO_DATABASE.get(sector_letter, [])
        if sector_iros:
            filtered_sector = IROGenerator._apply_applicability_filters(
                sector_iros, company_sector, employee_count, company_context
            )
        else:
            # Usa IRO di fallback per settori non coperti nel database
            filtered_sector = IROGenerator._apply_applicability_filters(
                GENERIC_SECTOR_IROS.get(sector_letter, []),
                company_sector, employee_count, company_context
            )

        # 2. IRO generici (sempre applicabili)
        generic_iros = GENERIC_IROS.copy()

        # 3. IRO dal contesto aziendale (rule-based) - SEMPRE attivi quando c'è contesto
        context_iros = []
        if company_context:
            context_iros = IROGenerator._generate_rule_based_ai_iros(
                company_sector, company_context
            )

        # 4. IRO AI-generati via LLM (solo se richiesto esplicitamente)
        ai_iros = []
        if use_ai and company_context:
            ai_iros = IROGenerator._generate_ai_iros(
                company_sector, employee_count, company_context
            )

        # 6. Merge: IRO settore + generici + contesto + AI (evitando duplicati)
        all_iros = filtered_sector + generic_iros + context_iros + ai_iros

        # 7. Applica scoring iniziale basato su benchmark


        for iro in all_iros:
            iro = IROGenerator._apply_initial_scoring(iro, benchmark)

        return all_iros

    @staticmethod
    def _apply_applicability_filters(
        iros: List[Dict],
        sector: str,
        employee_count: Optional[int],
        context: Optional[Dict],
    ) -> List[Dict]:
        """Filtra gli IRO basandosi sui fattori di applicabilità."""
        if not iros:
            return []

        sector_letter = IROGenerator.get_sector_code(sector)
        emp_count = employee_count or 0
        filtered = []

        for iro in iros:
            factors = iro.get("applicability_factors", {})

            # Filtro per settore
            allowed_sectors = factors.get("sectors", ["ALL"])
            if "ALL" not in allowed_sectors and sector_letter not in allowed_sectors:
                continue

            # Filtro per dimensione azienda
            min_emp = factors.get("min_employees", 0)
            if emp_count < min_emp:
                continue

            filtered.append(iro)

        return filtered

    @staticmethod
    def _apply_initial_scoring(
        iro: Dict,
        benchmark: Dict,
    ) -> Dict:
        """Applica scoring iniziale basato su benchmark di settore."""
        import random

        typical_impact = benchmark.get("typical_impact_range", (2.0, 3.5))
        typical_financial = benchmark.get("typical_financial_range", (2.0, 3.5))

        # Usa default se presenti, altrimenti genera da benchmark
        iro["initial_impact_scale"] = iro.get("default_impact_scale", round(random.uniform(*typical_impact), 1))
        iro["initial_financial_magnitude"] = iro.get("default_financial_magnitude", round(random.uniform(*typical_financial), 1))

        # Calcola score iniziali
        iro["initial_impact_score"] = round(
            iro["initial_impact_scale"] * 0.3 +
            random.uniform(2.0, 4.0) * 0.3 +
            random.uniform(1.0, 3.0) * 0.2 +
            random.uniform(2.0, 4.0) * 0.2,
            1,
        )
        iro["initial_financial_score"] = round(
            iro["initial_financial_magnitude"] * 0.6 +
            random.uniform(2.0, 4.0) * 0.4,
            1,
        )
        iro["is_material"] = max(iro["initial_impact_score"], iro["initial_financial_score"]) >= 3.0
        iro["benchmark_source"] = f"Settore {benchmark['name']}"

        return iro

    @staticmethod
    def _generate_ai_iros(
        sector: str,
        employee_count: Optional[int],
        context: Dict,
    ) -> List[Dict]:
        """Genera IRO aggiuntivi usando AI/LLM."""
        ai_iros = []

        # Prova a usare LLM se disponibile
        try:
            from openai import OpenAI
            client = OpenAI()
            ai_iros = IROGenerator._call_llm_for_iros(client, sector, employee_count, context)
            if ai_iros:
                return ai_iros
        except ImportError:
            logger.info("OpenAI library not available — skipping LLM IRO generation")
        except Exception as e:
            logger.warning(f"AI IRO generation failed: {e}")

        # No fallback rule-based here — context IROs are already generated
        # in _generate_rule_based_ai_iros called from the main flow.
        return ai_iros



    @staticmethod
    def _call_llm_for_iros(
        client,
        sector: str,
        employee_count: Optional[int],
        context: Dict,
    ) -> List[Dict]:
        """Usa LLM per generare IRO custom."""
        try:
            prompt = (
                f"Sei un esperto di CSRD/ESRS. Genera da 2 a 4 IRO (Impacts, Risks, Opportunities) "
                f"specifici per questa azienda:\n"
                f"- Settore NACE: {sector}\n"
                f"- Dipendenti: {employee_count or 'N/D'}\n"
                f"- Value Chain: {context.get('value_chain', 'N/D')}\n"
                f"- Attività: {context.get('key_activities', [])}\n"
                f"- Paesi: {context.get('geographical_scope', [])}\n"
                f"- Stakeholder: {context.get('stakeholder_groups', [])}\n\n"
                f"Rispondi SOLO con JSON array. Ogni IRO deve avere:\n"
                f"- id: stringa univoca\n"
                f"- type: 'impact'|'risk'|'opportunity'\n"
                f"- topic: ESRS E1, E2, E3, E4, E5, S1, S2, S3, S4, G1\n"
                f"- name: nome breve\n"
                f"- description: descrizione dettagliata\n"
                f"- default_impact_scale: 1-5\n"
                f"- default_financial_magnitude: 1-5\n"
                f"- severity: 'low'|'medium'|'high'"
            )

            response = client.chat.completions.create(
                model="gpt-4o-mini",
                messages=[
                    {"role": "system", "content": "Sei un consulente senior CSRD/ESG."},
                    {"role": "user", "content": prompt},
                ],
                temperature=0.3,
                max_tokens=1500,
            )

            content = response.choices[0].message.content.strip()
            # Estrai JSON dalla risposta
            if "```json" in content:
                content = content.split("```json")[1].split("```")[0].strip()
            elif "```" in content:
                content = content.split("```")[1].split("```")[0].strip()

            ai_iros = json.loads(content)
            if isinstance(ai_iros, list):
                for iro in ai_iros:
                    iro["ai_generated"] = True
                    iro["generation_method"] = "llm"
                return ai_iros

        except Exception as e:
            logger.warning(f"LLM IRO generation failed: {e}")

        return []

    @staticmethod
    def _generate_rule_based_ai_iros(
        sector: str,
        context: Dict,
    ) -> List[Dict]:
        """Genera IRO basati su regole a partire dal contesto aziendale.
        
        Più contesto l'utente inserisce, più IRO vengono generati.
        - Se c'è value_chain → genera IRO S2 (catena fornitura)
        - Se ci sono attività → genera IRO contestuali per topic ESRS
        - Se ci sono paesi → IRO compliance
        - Se ci sono stakeholder → IRO S3
        """
        sector_letter = IROGenerator.get_sector_code(sector)
        ai_iros = []
        idx = 1

        # Regole basate sul contesto
        value_chain = (context.get("value_chain") or "").lower()
        activities = [a.lower() for a in (context.get("key_activities") or [])]
        geo_scope = context.get("geographical_scope") or []
        stakeholders = context.get("stakeholder_groups") or []

        # Conta quanti campi sono compilati — usiamo questo per variare il numero di IRO
        filled_fields = 0
        if value_chain and len(value_chain) > 3:
            filled_fields += 1
        if activities:
            filled_fields += 1
        if geo_scope:
            filled_fields += 1
        if stakeholders:
            filled_fields += 1

        # ── SEMPRE genera almeno 1 IRO se c'è contesto, +1 per ogni campo compilato ──

        # 1) Value chain → sempre se c'è almeno testo (anche breve)
        if value_chain and len(value_chain) > 3:
            if any(w in value_chain for w in ["fornitore", "supplier", "supply", "import", "extra-eu", "logistic", "distribuzion", "acquisto", "approvvigion"]):
                ai_iros.append({
                    "id": f"AI_{sector_letter}_S2_{idx:03d}", "type": "risk",
                    "topic": "ESRS S2", "ai_generated": True,
                    "name": "Rischio supply chain",
                    "description": "Rischio violazione diritti umani/ambientali nella supply chain",
                    "default_impact_scale": 4, "default_financial_magnitude": 3, "severity": "high",
                    "generation_method": "rule_based",
                })
            else:
                ai_iros.append({
                    "id": f"AI_{sector_letter}_S2_{idx:03d}", "type": "impact",
                    "topic": "ESRS S2", "ai_generated": True,
                    "name": "Gestione relazioni con fornitori",
                    "description": "Impatto delle pratiche di approvvigionamento sulla catena del valore",
                    "default_impact_scale": 3, "default_financial_magnitude": 2, "severity": "medium",
                    "generation_method": "rule_based",
                })
            idx += 1

        # 2) Attività → genera IRO sul modello di business
        if activities:
            # Se attività manifatturiere/industriali
            if any(a in " ".join(activities) for a in ["produzion", "fabbricazion", "manifattur", "industrial", "processo produttiv"]):
                ai_iros.append({
                    "id": f"AI_{sector_letter}_E1_{idx:03d}", "type": "impact",
                    "topic": "ESRS E1", "ai_generated": True,
                    "name": "Impatto ambientale processi produttivi",
                    "description": f"Emissioni e consumi energetici legati a: {', '.join(activities[:3])}",
                    "default_impact_scale": 3, "default_financial_magnitude": 3, "severity": "medium",
                    "generation_method": "rule_based",
                })
            elif any(a in " ".join(activities) for a in ["serviz", "consulenza", "professional", "digital", "software"]):
                ai_iros.append({
                    "id": f"AI_{sector_letter}_S1_{idx:03d}", "type": "impact",
                    "topic": "ESRS S1", "ai_generated": True,
                    "name": "Capitale umano e competenze",
                    "description": f"Gestione talenti e competenze per: {', '.join(activities[:3])}",
                    "default_impact_scale": 3, "default_financial_magnitude": 3, "severity": "medium",
                    "generation_method": "rule_based",
                })
            else:
                ai_iros.append({
                    "id": f"AI_{sector_letter}_E1_{idx:03d}", "type": "impact",
                    "topic": "ESRS E1", "ai_generated": True,
                    "name": "Impronta carbonio operativa",
                    "description": f"Emissioni GHG derivate dall'attività di: {', '.join(activities[:3])}",
                    "default_impact_scale": 2, "default_financial_magnitude": 2, "severity": "low",
                    "generation_method": "rule_based",
                })
            idx += 1

        # 3) Paesi → sempre se specificati (anche 1 solo paese extra-EU o multi-country)
        if len(geo_scope) > 0:
            if len(geo_scope) > 2:
                ai_iros.append({
                    "id": f"AI_{sector_letter}_G1_{idx:03d}", "type": "risk",
                    "topic": "ESRS G1", "ai_generated": True,
                    "name": "Compliance multi-giurisdizione",
                    "description": f"Rischio conformità normativa operando in {len(geo_scope)} paesi/regioni",
                    "default_impact_scale": 3, "default_financial_magnitude": 3, "severity": "medium",
                    "generation_method": "rule_based",
                })
            else:
                ai_iros.append({
                    "id": f"AI_{sector_letter}_G1_{idx:03d}", "type": "risk",
                    "topic": "ESRS G1", "ai_generated": True,
                    "name": "Rischio normativo locale",
                    "description": f"Conformità a normative locali in {geo_scope[0]}",
                    "default_impact_scale": 2, "default_financial_magnitude": 3, "severity": "low",
                    "generation_method": "rule_based",
                })
            idx += 1

        # 4) Stakeholder → sempre se specificati
        if len(stakeholders) > 0:
            if len(stakeholders) > 3:
                ai_iros.append({
                    "id": f"AI_{sector_letter}_S3_{idx:03d}", "type": "impact",
                    "topic": "ESRS S3", "ai_generated": True,
                    "name": "Relazioni con stakeholder multipli",
                    "description": "Gestione aspettative di stakeholder diversificati",
                    "default_impact_scale": 3, "default_financial_magnitude": 2, "severity": "medium",
                    "generation_method": "rule_based",
                })
            else:
                ai_iros.append({
                    "id": f"AI_{sector_letter}_S3_{idx:03d}", "type": "impact",
                    "topic": "ESRS S3", "ai_generated": True,
                    "name": "Coinvolgimento stakeholder",
                    "description": f"Dialogo e reporting con stakeholder: {', '.join(stakeholders)}",
                    "default_impact_scale": 2, "default_financial_magnitude": 1, "severity": "low",
                    "generation_method": "rule_based",
                })

        return ai_iros

    @staticmethod
    def get_iros_by_topic(iros: List[Dict], topic: str) -> List[Dict]:
        """Filtra IRO per topic ESRS."""
        return [i for i in iros if i["topic"] == topic]

    @staticmethod
    def get_iros_by_type(iros: List[Dict], iro_type: str) -> List[Dict]:
        """Filtra IRO per tipo (impact/risk/opportunity)."""
        return [i for i in iros if i["type"] == iro_type]

    @staticmethod
    def get_summary(iros: List[Dict]) -> Dict[str, Any]:
        """Restituisce un riepilogo degli IRO generati."""
        total = len(iros)
        by_type = {}
        by_topic = {}
        material_count = 0
        ai_count = 0

        for iro in iros:
            t = iro.get("type", "unknown")
            by_type[t] = by_type.get(t, 0) + 1

            topic = iro.get("topic", "unknown")
            by_topic[topic] = by_topic.get(topic, 0) + 1

            if iro.get("is_material"):
                material_count += 1
            if iro.get("ai_generated"):
                ai_count += 1

        return {
            "total_iros": total,
            "by_type": by_type,
            "by_topic": by_topic,
            "material_count": material_count,
            "ai_generated": ai_count,
            "benchmark_sourced": total - ai_count,
        }
