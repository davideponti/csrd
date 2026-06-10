"""
CSRD Comply — ESRS Datapoints Seed Script

Converte il file Excel EFRAG IG 3 in datapoint ESRS e li importa nel database.
Usabile sia come script CLI che via endpoint API.

Usage:
    python -m app.seed_esrs_datapoints          # Legge da Excel
    python -m app.seed_esrs_datapoints --json    # Usa il fallback JSON
"""
import json
import os
import sys
import logging
from typing import List, Dict, Optional
from datetime import datetime

logger = logging.getLogger(__name__)

# ── Percorsi file ───────────────────────────────────────────────
BACKEND_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
EXCEL_PATH = os.path.join(BACKEND_DIR, "data", "efrag_ig3_datapoints.xlsx")
JSON_FALLBACK_PATH = os.path.join(BACKEND_DIR, "data", "esrs_datapoints_fallback.json")

# ── Topic che servono per matchare gli IRO ──────────────────────
REQUIRED_TOPICS = [
    "ESRS E1", "ESRS E2", "ESRS E3", "ESRS E4", "ESRS E5",
    "ESRS S1", "ESRS S2", "ESRS S3", "ESRS S4", "ESRS G1",
]

# ── Datapoint fallback minimi (uno per topic) ───────────────────
MINIMAL_DATAPOINTS = [
    {"standard_ref": "ESRS E1-1", "paragraph_ref": "1", "disclosure_requirement": "Transition plan for climate change mitigation",
     "data_type": "narrative", "unit": None, "is_mandatory": True, "is_conditional": False, "phase_in_year": None, "sfd_ref": None},
    {"standard_ref": "ESRS E1-6", "paragraph_ref": "44(a)", "disclosure_requirement": "Gross Scope 1 GHG emissions",
     "data_type": "numerical", "unit": "tCO2eq", "is_mandatory": True, "is_conditional": False, "phase_in_year": None, "sfd_ref": "P3_1"},
    {"standard_ref": "ESRS E1-6", "paragraph_ref": "44(b)", "disclosure_requirement": "Gross Scope 2 GHG emissions",
     "data_type": "numerical", "unit": "tCO2eq", "is_mandatory": True, "is_conditional": False, "phase_in_year": None, "sfd_ref": "P3_2"},
    {"standard_ref": "ESRS E1-6", "paragraph_ref": "44(c)", "disclosure_requirement": "Gross Scope 3 GHG emissions",
     "data_type": "numerical", "unit": "tCO2eq", "is_mandatory": True, "is_conditional": False, "phase_in_year": 2026, "sfd_ref": "P3_3"},
    {"standard_ref": "ESRS E2-1", "paragraph_ref": "1", "disclosure_requirement": "Pollution management policy",
     "data_type": "narrative", "unit": None, "is_mandatory": True, "is_conditional": False, "phase_in_year": None, "sfd_ref": None},
    {"standard_ref": "ESRS E2-4", "paragraph_ref": "12", "disclosure_requirement": "Pollutant emissions to air, water and soil",
     "data_type": "numerical", "unit": "kg", "is_mandatory": True, "is_conditional": False, "phase_in_year": None, "sfd_ref": "P3_17"},
    {"standard_ref": "ESRS E3-1", "paragraph_ref": "1", "disclosure_requirement": "Water management policy",
     "data_type": "narrative", "unit": None, "is_mandatory": True, "is_conditional": False, "phase_in_year": None, "sfd_ref": None},
    {"standard_ref": "ESRS E3-4", "paragraph_ref": "15(a)", "disclosure_requirement": "Water consumption intensity",
     "data_type": "numerical", "unit": "m³", "is_mandatory": True, "is_conditional": False, "phase_in_year": None, "sfd_ref": "P3_21"},
    {"standard_ref": "ESRS E4-1", "paragraph_ref": "1", "disclosure_requirement": "Biodiversity policy",
     "data_type": "narrative", "unit": None, "is_mandatory": True, "is_conditional": False, "phase_in_year": None, "sfd_ref": None},
    {"standard_ref": "ESRS E4-5", "paragraph_ref": "37", "disclosure_requirement": "Biodiversity footprint",
     "data_type": "numerical", "unit": "ha", "is_mandatory": False, "is_conditional": True, "phase_in_year": 2027, "sfd_ref": None},
    {"standard_ref": "ESRS E5-1", "paragraph_ref": "1", "disclosure_requirement": "Circular economy policy",
     "data_type": "narrative", "unit": None, "is_mandatory": True, "is_conditional": False, "phase_in_year": None, "sfd_ref": None},
    {"standard_ref": "ESRS E5-5", "paragraph_ref": "22(a)", "disclosure_requirement": "Total waste generated",
     "data_type": "numerical", "unit": "t", "is_mandatory": True, "is_conditional": False, "phase_in_year": None, "sfd_ref": None},
    {"standard_ref": "ESRS S1-1", "paragraph_ref": "1", "disclosure_requirement": "Own workforce policy",
     "data_type": "narrative", "unit": None, "is_mandatory": True, "is_conditional": False, "phase_in_year": None, "sfd_ref": None},
    {"standard_ref": "ESRS S1-6", "paragraph_ref": "20(a)", "disclosure_requirement": "Number of employees by gender",
     "data_type": "numerical", "unit": "FTE", "is_mandatory": True, "is_conditional": False, "phase_in_year": None, "sfd_ref": None},
    {"standard_ref": "ESRS S1-14", "paragraph_ref": "55", "disclosure_requirement": "Health and safety metrics - injury rate",
     "data_type": "numerical", "unit": "rate", "is_mandatory": True, "is_conditional": False, "phase_in_year": None, "sfd_ref": None},
    {"standard_ref": "ESRS S2-1", "paragraph_ref": "1", "disclosure_requirement": "Value chain workers policy",
     "data_type": "narrative", "unit": None, "is_mandatory": True, "is_conditional": False, "phase_in_year": None, "sfd_ref": None},
    {"standard_ref": "ESRS S3-1", "paragraph_ref": "1", "disclosure_requirement": "Affected communities policy",
     "data_type": "narrative", "unit": None, "is_mandatory": True, "is_conditional": False, "phase_in_year": None, "sfd_ref": None},
    {"standard_ref": "ESRS S4-1", "paragraph_ref": "1", "disclosure_requirement": "Consumers and end-users policy",
     "data_type": "narrative", "unit": None, "is_mandatory": True, "is_conditional": False, "phase_in_year": None, "sfd_ref": None},
    {"standard_ref": "ESRS G1-1", "paragraph_ref": "1", "disclosure_requirement": "Corporate culture and business conduct policies",
     "data_type": "narrative", "unit": None, "is_mandatory": True, "is_conditional": False, "phase_in_year": None, "sfd_ref": None},
    {"standard_ref": "ESRS G1-3", "paragraph_ref": "15", "disclosure_requirement": "Anti-corruption and bribery procedures",
     "data_type": "narrative", "unit": None, "is_mandatory": True, "is_conditional": False, "phase_in_year": None, "sfd_ref": None},
]


def extract_from_excel() -> List[Dict]:
    """
    Legge il file Excel EFRAG IG 3 e converte tutte le righe in datapoint.
    
    Mappatura colonne (0-indexed):
        A(0) = Standard (ESRS E1, E2...)
        B(1) = DR Reference
        C(2) = Paragraph Reference
        D(3) = Description
        F(5) = Datapoint Name
        G(6) = Data Type
        I(8) = Voluntary Flag
        K(10) = Phase-in Info
        L(11) = SFDR/P3 Reference
    
    Returns:
        Lista di dict datapoint
    """
    try:
        import pandas as pd
    except ImportError:
        logger.warning("pandas non installato, uso fallback JSON")
        return None

    if not os.path.exists(EXCEL_PATH):
        logger.warning(f"File Excel non trovato: {EXCEL_PATH}")
        return None

    TYPE_MAP = {
        "monetary": "numerical", "boolean": "boolean", "narrative": "narrative",
        "percent": "numerical", "volume": "numerical", "energy": "numerical",
        "emission": "numerical", "count": "numerical", "ratio": "numerical",
        "date": "narrative", "text": "narrative", "weight": "numerical",
        "area": "numerical", "number": "numerical",
    }

    UNIT_MAP = {
        "monetary": "EUR", "percent": "%", "volume": "m³", "energy": "kWh",
        "emission": "tCO2eq", "count": "units", "weight": "t", "area": "ha",
        "ratio": "ratio",
    }

    def parse_phase_in(text: str) -> Optional[int]:
        if not text or not isinstance(text, str):
            return None
        for year in [2025, 2026, 2027, 2028, 2029]:
            if str(year) in text.lower():
                return year
        return None

    logger.info(f"Leggendo Excel: {EXCEL_PATH}")
    df = pd.read_excel(EXCEL_PATH, header=None)

    # Trova la riga header
    header_row = 0
    for idx, row in df.iterrows():
        row_str = " ".join(str(v).lower() for v in row if pd.notna(v))
        if "standard" in row_str or "esrs" in row_str:
            header_row = idx
            break

    datapoints = []
    skipped = 0
    topics_found = set()

    for idx, row in df.iterrows():
        if idx <= header_row:
            continue

        standard = str(row[0]).strip() if pd.notna(row[0]) else ""
        if not standard or not standard.startswith("ESRS"):
            skipped += 1
            continue

        dr_ref = str(row[1]).strip() if len(row) > 1 and pd.notna(row[1]) else ""
        paragraph_ref = str(row[2]).strip() if len(row) > 2 and pd.notna(row[2]) else ""
        description = str(row[3]).strip() if len(row) > 3 and pd.notna(row[3]) else ""
        datapoint_name = str(row[5]).strip() if len(row) > 5 and pd.notna(row[5]) else ""
        data_type_raw = str(row[6]).strip().lower() if len(row) > 6 and pd.notna(row[6]) else ""
        voluntary_str = str(row[8]).strip().lower() if len(row) > 8 and pd.notna(row[8]) else ""
        phase_in_str = str(row[10]).strip() if len(row) > 10 and pd.notna(row[10]) else ""
        sfdr_ref = str(row[11]).strip() if len(row) > 11 and pd.notna(row[11]) else ""

        # Costruisci standard_ref
        if dr_ref:
            standard_ref = f"{standard}-{dr_ref}"
        else:
            standard_ref = standard

        # Data type
        data_type = TYPE_MAP.get(data_type_raw, "narrative")

        # Unità
        unit = UNIT_MAP.get(data_type_raw, None)

        # Mandatory
        is_mandatory = voluntary_str != "yes"
        is_conditional = "conditional" in description.lower() or "condition" in description.lower()

        # Phase-in
        phase_in_year = parse_phase_in(phase_in_str)

        # Testo descrittivo
        display_text = description or datapoint_name or standard_ref

        # Traccia i topic trovati
        topic = standard.split("-")[0] if "-" in standard else standard
        topics_found.add(topic)

        datapoints.append({
            "standard_ref": standard_ref,
            "paragraph_ref": paragraph_ref,
            "disclosure_requirement": display_text,
            "data_type": data_type,
            "unit": unit,
            "is_mandatory": is_mandatory,
            "is_conditional": is_conditional,
            "phase_in_year": phase_in_year,
            "sfd_ref": sfdr_ref if sfdr_ref else None,
        })

    logger.info(f"Excel: {len(datapoints)} datapoint estratti, {skipped} righe saltate")
    logger.info(f"Topic trovati: {sorted(topics_found)}")

    # Verifica che ci siano tutti i topic richiesti
    missing = set(REQUIRED_TOPICS) - topics_found
    if missing:
        logger.warning(f"Topic mancanti dall'Excel: {missing}")
        logger.info(f"Verrano aggiunti i datapoint minimi per: {missing}")

    # Aggiungi datapoint minimi per i topic mancanti
    for dp in MINIMAL_DATAPOINTS:
        topic = dp["standard_ref"].split("-")[0]
        if topic in missing:
            datapoints.append(dp)
            logger.info(f"Aggiunto fallback: {dp['standard_ref']}")

    return datapoints


def get_minimal_datapoints() -> List[Dict]:
    """Restituisce datapoint minimi che coprono TUTTI i topic ESRS per gli IRO."""
    return MINIMAL_DATAPOINTS.copy()


def load_datapoints_from_json() -> List[Dict]:
    """Carica datapoint dal file JSON di fallback."""
    if os.path.exists(JSON_FALLBACK_PATH):
        with open(JSON_FALLBACK_PATH, "r") as f:
            return json.load(f)
    return []


def get_all_datapoints(use_excel: bool = True) -> List[Dict]:
    """
    Ottiene tutti i datapoint ESRS, prima tentando Excel poi fallback JSON poi minimi.
    
    Args:
        use_excel: Se True, tenta prima la lettura da Excel
        
    Returns:
        Lista completa di datapoint
    """
    datapoints = None
    
    if use_excel:
        datapoints = extract_from_excel()
    
    if datapoints is None or len(datapoints) == 0:
        logger.info("Tentativo con JSON fallback...")
        datapoints = load_datapoints_from_json()
    
    if not datapoints:
        logger.info("Nessun datapoint da JSON, uso datapoint minimi...")
        datapoints = get_minimal_datapoints()
    
    logger.info(f"Totale datapoint: {len(datapoints)}")
    
    # Verifica copertura topic
    topics_covered = set()
    for dp in datapoints:
        ref = dp.get("standard_ref", "")
        topic = ref.split("-")[0]
        topics_covered.add(topic)
    
    missing = set(REQUIRED_TOPICS) - topics_covered
    if missing:
        logger.warning(f"ANCORA topic mancanti: {missing}")
        for mp in MINIMAL_DATAPOINTS:
            topic = mp["standard_ref"].split("-")[0]
            if topic in missing:
                dp_copy = mp.copy()
                datapoints.append(dp_copy)
                logger.info(f"Aggiunto fallback finale: {mp['standard_ref']}")
    
    return datapoints


def seed_to_db(db_session, datapoints: List[Dict]) -> int:
    """
    Importa i datapoint nel database.
    
    Args:
        db_session: SQLAlchemy session
        datapoints: Lista di dict datapoint
        
    Returns:
        Numero di nuovi datapoint creati
    """
    try:
        from app.models import EsrsDatapoint
    except ImportError:
        logger.error("Impossibile importare EsrsDatapoint. Esegui da dentro backend/")
        return 0

    # Prima controlla quanti datapoint ci sono già
    existing_count = db_session.query(EsrsDatapoint).count()
    logger.info(f"Datapoint già presenti nel DB: {existing_count}")

    # Se ci sono già abbastanza datapoint (almeno quanti i minimi), salta
    MINIMAL_COUNT = len(MINIMAL_DATAPOINTS)
    if existing_count >= MINIMAL_COUNT:
        logger.info(f"Database già popolato con {existing_count} datapoint (soglia: {MINIMAL_COUNT}). Salto seed.")
        return 0


    created_count = 0
    for dp in datapoints:
        # Verifica se esiste già (esatta stessa standard_ref + paragraph_ref)
        existing = db_session.query(EsrsDatapoint).filter(
            EsrsDatapoint.standard_ref == dp["standard_ref"],
            EsrsDatapoint.paragraph_ref == dp.get("paragraph_ref", ""),
        ).first()

        if existing:
            continue

        datapoint = EsrsDatapoint(
            standard_ref=dp["standard_ref"],
            paragraph_ref=dp.get("paragraph_ref", ""),
            disclosure_requirement=dp.get("disclosure_requirement", dp["standard_ref"]),
            data_type=dp.get("data_type", "narrative"),
            unit=dp.get("unit"),
            is_mandatory=dp.get("is_mandatory", True),
            is_conditional=dp.get("is_conditional", False),
            phase_in_year=dp.get("phase_in_year"),
            sfd_ref=dp.get("sfd_ref"),
        )
        db_session.add(datapoint)
        created_count += 1

        if created_count % 200 == 0:
            db_session.flush()

    db_session.commit()


    final_count = db_session.query(EsrsDatapoint).count()
    logger.info(f"Creati {created_count} nuovi datapoint. Totale ora: {final_count}")

    return created_count


def save_fallback_json(datapoints: List[Dict]):
    """Salva i datapoint come JSON fallback per deployment rapidi."""
    os.makedirs(os.path.dirname(JSON_FALLBACK_PATH), exist_ok=True)
    with open(JSON_FALLBACK_PATH, "w") as f:
        json.dump(datapoints, f, indent=2)
    logger.info(f"Fallback JSON salvato: {JSON_FALLBACK_PATH} ({len(datapoints)} datapoint)")


def main():
    """CLI entry point."""
    logging.basicConfig(
        level=logging.INFO,
        format="%(asctime)s [%(levelname)s] %(message)s",
    )

    use_excel = "--json" not in sys.argv

    # Ottieni datapoint
    datapoints = get_all_datapoints(use_excel=use_excel)
    logger.info(f"Ottenuti {len(datapoints)} datapoint totali")

    # Salva JSON fallback
    save_fallback_json(datapoints)

    # Prova a connettersi al DB
    try:
        from sqlalchemy import create_engine
        from sqlalchemy.orm import Session

        DATABASE_URL = os.getenv(
            "DATABASE_URL",
            "postgresql://postgres:postgres@localhost:5432/csrd_comply"
        )
        engine = create_engine(DATABASE_URL)
        with Session(engine) as session:
            count = seed_to_db(session, datapoints)
            print(f"\n✅ Seed completato! {count} datapoint importati.")
    except Exception as e:
        logger.error(f"Connessione DB fallita: {e}")
        print(f"\n❌ DB non raggiungibile. Fallback JSON salvato comunque.")
        print(f"   Usa: python -m app.seed_esrs_datapoints (con DB in esecuzione)")
        print(f"   Oppure chiama l'endpoint API /api/v1/admin/seed-datapoints")
        sys.exit(1)


if __name__ == "__main__":
    main()
