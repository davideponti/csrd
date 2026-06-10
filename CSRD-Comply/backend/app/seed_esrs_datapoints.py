"""
CSRD Comply — ESRS Datapoints Seed Script

Converte il file Excel EFRAG IG 3 con 1.184 datapoint reali (multi-sheet)
e li importa nel database.
Usabile sia come script CLI che via endpoint API.

Usage:
    python -m app.seed_esrs_datapoints          # Legge da Excel (1.184 datapoint)
    python -m app.seed_esrs_datapoints --json    # Usa il fallback JSON
"""
import json
import os
import sys
import re
import logging
from typing import List, Dict, Optional
from datetime import datetime

logger = logging.getLogger(__name__)

# ── Percorsi file ───────────────────────────────────────────────
BACKEND_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
ROOT_DIR = os.path.dirname(BACKEND_DIR)  # CSRD-Comply root

# File Excel REALE con 1.184 datapoint (multi-sheet, sotto data/)
EXCEL_PATH = os.path.join(ROOT_DIR, "data", "esrs_datapoints.xlsx")

# File Excel legacy (backend/data/, pochi datapoint sintetici)
EXCEL_LEGACY_PATH = os.path.join(BACKEND_DIR, "data", "efrag_ig3_datapoints.xlsx")

JSON_FALLBACK_PATH = os.path.join(BACKEND_DIR, "data", "esrs_datapoints_fallback.json")

# ── Topic che servono per matchare gli IRO ──────────────────────
REQUIRED_TOPICS = [
    "ESRS 2",
    "ESRS E1", "ESRS E2", "ESRS E3", "ESRS E4", "ESRS E5",
    "ESRS S1", "ESRS S2", "ESRS S3", "ESRS S4", "ESRS G1",
]

# Mappatura: nome sheet -> prefisso ESRS
SHEET_TOPIC_MAP = {
    "ESRS 2": "ESRS 2",
    "ESRS 2 MDR": "ESRS 2",
    "ESRS E1": "ESRS E1",
    "ESRS E2": "ESRS E2",
    "ESRS E3": "ESRS E3",
    "ESRS E4": "ESRS E4",
    "ESRS E5": "ESRS E5",
    "ESRS S1": "ESRS S1",
    "ESRS S2": "ESRS S2",
    "ESRS S3": "ESRS S3",
    "ESRS S4": "ESRS S4",
    "ESRS G1": "ESRS G1",
}

# Mappatura data type
TYPE_MAP = {
    "monetary": "numerical",
    "boolean": "boolean",
    "narrative": "narrative",
    "semi-narrative": "semi-narrative",
    "semi narrative": "semi-narrative",
    "percent": "numerical",
    "volume": "numerical",
    "energy": "numerical",
    "emission": "numerical",
    "count": "numerical",
    "ratio": "numerical",
    "date": "narrative",
    "text": "narrative",
    "weight": "numerical",
    "area": "numerical",
    "number": "numerical",
    "mdr-p": "narrative",  # MDR-P datapoints are narrative policies
    "mdr-m": "numerical",
    "mdr-a": "narrative",
    "mdr-t": "narrative",
}

UNIT_MAP = {
    "monetary": "EUR",
    "percent": "%",
    "volume": "m³",
    "energy": "kWh",
    "emission": "tCO2eq",
    "count": "units",
    "weight": "t",
    "area": "ha",
    "ratio": "ratio",
}


def parse_phase_in(text: str) -> Optional[int]:
    """Parse phase-in year from text like '1 year', '2 years', '2026', etc."""
    if not text or not isinstance(text, str):
        return None
    text = text.strip().lower()
    if not text or text == 'nan':
        return None
    # Direct year match
    for year in [2025, 2026, 2027, 2028, 2029]:
        if str(year) in text:
            return year
    # "1 year" means 2025 (first wave), "2 years" means 2026, etc.
    m = re.match(r'(\d+)\s*years?', text)
    if m:
        years_from_now = int(m.group(1))
        return 2025 + years_from_now - 1
    return None


def extract_from_excel() -> Optional[List[Dict]]:
    """
    Legge il file Excel multi-sheet con 1.184 datapoint reali.
    Sheets: ESRS 2, ESRS 2 MDR, ESRS E1-E5, ESRS S1-S4, ESRS G1

    Mappatura colonne (0-indexed) in ogni sheet:
        0 = ID (es. 'BP-1_01', 'E1.GOV-3_01')
        1 = ESRS (es. 'ESRS 2', 'E1', 'S1', 'G1')
        2 = DR (es. 'BP-1', 'E1.GOV-3', 'S1.SBM-3')
        3 = Paragraph (es. '5 a', '13', '14')
        4 = Related AR
        5 = Name (descrizione del datapoint)
        6 = Data Type
        7 = Conditional or alternative DP
        8 = May [V] (Voluntary flag)
        9 = Appendix B (SFDR + PILLAR 3 + Benchmark + CL references)
        10 = Appendix C - Phase-in (colonna 1)
        11 = Appendix C - Phase-in (colonna 2, a volte)
    """
    try:
        import pandas as pd
    except ImportError:
        logger.warning("pandas non installato, uso fallback")
        return None

    if os.path.exists(EXCEL_PATH):
        excel_path = EXCEL_PATH
        logger.info(f"Usando file Excel multi-sheet: {EXCEL_PATH}")
    elif os.path.exists(EXCEL_LEGACY_PATH):
        excel_path = EXCEL_LEGACY_PATH
        logger.info(f"File multi-sheet non trovato, uso legacy: {EXCEL_LEGACY_PATH}")
    else:
        logger.warning("Nessun file Excel trovato")
        return None

    try:
        xls = pd.ExcelFile(excel_path, engine='openpyxl')
    except Exception as e:
        logger.warning(f"Impossibile aprire Excel: {e}")
        return None

    logger.info(f"Sheets trovati: {xls.sheet_names}")

    datapoints = []
    topics_found = set()
    total_skipped = 0

    for sheet_name in xls.sheet_names:
        if sheet_name == 'Index':
            continue

        topic_prefix = SHEET_TOPIC_MAP.get(sheet_name)
        if not topic_prefix:
            logger.warning(f"Sheet '{sheet_name}' non mappato, salto")
            continue

        df = pd.read_excel(excel_path, sheet_name=sheet_name, header=None)
        logger.info(f"  Sheet '{sheet_name}' ({len(df)} righe, topic={topic_prefix})")

        sheet_datapoints = 0
        sheet_skipped = 0

        for idx, row in df.iterrows():
            if idx <= 1:  # Row 0 = instructions, Row 1 = header
                continue

            # Col 0: ID
            id_val = str(row[0]).strip() if pd.notna(row[0]) else ""
            if not id_val or id_val.startswith("INSTRUCTIONS") or id_val == "ID":
                sheet_skipped += 1
                continue

            # Col 1: ESRS code (es. 'ESRS 2', 'E1', 'S1', 'G1')
            esrs_code = str(row[1]).strip() if len(row) > 1 and pd.notna(row[1]) else ""
            if not esrs_code:
                sheet_skipped += 1
                continue

            # Col 2: DR reference
            dr_ref = str(row[2]).strip() if len(row) > 2 and pd.notna(row[2]) else ""

            # Col 3: Paragraph reference
            paragraph_ref = str(row[3]).strip() if len(row) > 3 and pd.notna(row[3]) else ""

            # Col 5: Name (description)
            name = str(row[5]).strip() if len(row) > 5 and pd.notna(row[5]) else ""
            if not name:
                name = f"{esrs_code}-{dr_ref}"

            # Col 6: Data Type
            data_type_raw = str(row[6]).strip().lower() if len(row) > 6 and pd.notna(row[6]) else ""

            # Col 7: Conditional
            conditional_raw = str(row[7]).strip().lower() if len(row) > 7 and pd.notna(row[7]) else ""

            # Col 8: May [V] (Voluntary)
            voluntary_raw = str(row[8]).strip().lower() if len(row) > 8 and pd.notna(row[8]) else ""

            # Col 9: SFDR/Appendix B references
            sfdr_ref = ""
            if len(row) > 9 and pd.notna(row[9]):
                sfdr_val = str(row[9]).strip()
                if sfdr_val and sfdr_val.lower() not in ('nan', '', ' ', '\xa0'):
                    sfdr_ref = sfdr_val

            # Col 10-11: Phase-in
            phase_in_str = ""
            if len(row) > 10 and pd.notna(row[10]):
                pi = str(row[10]).strip()
                if pi.lower() not in ('nan', '', ' ', '\xa0'):
                    phase_in_str = pi
            if not phase_in_str and len(row) > 11 and pd.notna(row[11]):
                pi = str(row[11]).strip()
                if pi.lower() not in ('nan', '', ' ', '\xa0'):
                    phase_in_str = pi

            # ── Costruisci standard_ref ──────────────────────────
            # Normalizza il codice ESRS: "E1" → "ESRS E1", "ESRS 2" → "ESRS 2"
            if esrs_code.startswith("ESRS "):
                normalized_esrs = esrs_code
            elif esrs_code.startswith("E") or esrs_code.startswith("S") or esrs_code.startswith("G"):
                # Find the topic prefix from sheet name
                normalized_esrs = topic_prefix
            else:
                normalized_esrs = f"ESRS {esrs_code}"

            # DR reference - pulisci spazi
            dr_ref_clean = dr_ref.strip()

            # Costruisci standard_ref
            if dr_ref_clean:
                standard_ref = f"{normalized_esrs}-{dr_ref_clean}"
            else:
                standard_ref = normalized_esrs

            # Data type
            data_type = TYPE_MAP.get(data_type_raw, "narrative")

            # Unità
            unit = UNIT_MAP.get(data_type_raw, None)

            # Mandatory: if voluntary column has "V" or "yes", it's NOT mandatory
            is_voluntary = (
                "v" in voluntary_raw or
                "yes" in voluntary_raw or
                "x" in voluntary_raw or
                "may" in voluntary_raw
            )
            is_mandatory = not is_voluntary

            # Conditional
            is_conditional = (
                "conditional" in conditional_raw or
                "condition" in conditional_raw
            )

            # Phase-in
            phase_in_year = parse_phase_in(phase_in_str)

            # SFDR reference - pulisci
            if sfdr_ref:
                # Sometimes it contains "SFDR" or "P3_" prefix
                sfdr_clean = sfdr_ref.strip()
                # Remove non-breaking spaces
                sfdr_clean = sfdr_clean.replace('\xa0', '')
                if sfdr_clean == 'SFDR':
                    # Just "SFDR" with no specific ref - leave it
                    pass
                elif sfdr_clean.startswith('SFDR') or sfdr_clean.startswith('P3_'):
                    pass
                else:
                    # Might have other references
                    pass
            else:
                sfdr_clean = None

            topics_found.add(normalized_esrs)

            datapoints.append({
                "standard_ref": standard_ref,
                "paragraph_ref": paragraph_ref,
                "disclosure_requirement": name,
                "data_type": data_type,
                "unit": unit,
                "is_mandatory": is_mandatory,
                "is_conditional": is_conditional,
                "phase_in_year": phase_in_year,
                "sfd_ref": sfdr_clean,
            })
            sheet_datapoints += 1

        logger.info(f"    → {sheet_datapoints} datapoint estratti, {sheet_skipped} righe saltate")
        total_skipped += sheet_skipped

    logger.info(f"\nTotale: {len(datapoints)} datapoint estratti da Excel, {total_skipped} righe saltate totali")
    logger.info(f"Topic trovati: {sorted(topics_found)}")

    # Verifica topic mancanti
    missing = set(REQUIRED_TOPICS) - topics_found
    if missing:
        logger.warning(f"Topic mancanti dall'Excel: {missing}")
        from app.seed_esrs_datapoints import get_minimal_datapoints
        for dp in get_minimal_datapoints():
            topic = dp["standard_ref"].split("-")[0]
            if topic in missing:
                datapoints.append(dp)
                logger.info(f"Aggiunto fallback: {dp['standard_ref']}")

    return datapoints


# ── Datapoint minimi (fallback) ─────────────────────────────────
MINIMAL_DATAPOINTS = [
    {"standard_ref": "ESRS 2-BP-1", "paragraph_ref": "1", "disclosure_requirement": "Basis for preparation of sustainability statement",
     "data_type": "narrative", "unit": None, "is_mandatory": True, "is_conditional": False, "phase_in_year": None, "sfd_ref": None},
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
        topic = re.match(r'(ESRS [A-Z0-9]+)', ref)
        if topic:
            topics_covered.add(topic.group(1))

    missing = set(REQUIRED_TOPICS) - topics_covered
    if missing:
        logger.warning(f"ANCORA topic mancanti: {missing}")
        for mp in MINIMAL_DATAPOINTS:
            topic = re.match(r'(ESRS [A-Z0-9]+)', mp["standard_ref"])
            if topic and topic.group(1) in missing:
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

    # Se il DB ha già abbastanza datapoint (almeno quanti quelli che stiamo fornendo), salta
    if existing_count >= len(datapoints):
        logger.info(f"Database già popolato con {existing_count} datapoint (pari o superiore ai {len(datapoints)} da seedare). Salto seed.")
        return 0

    if existing_count > 0:
        logger.info(f"Database ha {existing_count} datapoint, ma ne abbiamo {len(datapoints)} da seedare. Aggiungo quelli mancanti...")

    # Ottieni gli standard_ref esistenti per evitare duplicati
    existing_refs = set()
    existing_records = db_session.query(EsrsDatapoint.standard_ref, EsrsDatapoint.paragraph_ref).all()
    for ref, para in existing_records:
        existing_refs.add((ref, para or ""))

    created_count = 0
    for dp in datapoints:
        key = (dp["standard_ref"], dp.get("paragraph_ref", ""))
        if key in existing_refs:
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
            logger.info(f"  ... {created_count} datapoint creati finora")

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
            print(f"\n✅ Seed completato! {count} nuovi datapoint importati.")
            print(f"   Totale datapoint nel DB: {session.query(type('tmp', (), {'count': lambda self: None})()).count()}")

            # Verifica copertura topic
            from app.models import EsrsDatapoint
            all_refs = session.query(EsrsDatapoint.standard_ref).distinct().all()
            topics = set()
            for (ref,) in all_refs:
                m = re.match(r'(ESRS [A-Z0-9]+)', ref)
                if m:
                    topics.add(m.group(1))
            print(f"   Topic coperti: {len(topics)} — {sorted(topics)}")
    except Exception as e:
        logger.error(f"Connessione DB fallita: {e}")
        print(f"\n❌ DB non raggiungibile. Fallback JSON salvato comunque.")
        print(f"   Usa: python -m app.seed_esrs_datapoints (con DB in esecuzione)")
        print(f"   Oppure chiama l'endpoint API /api/v1/admin/seed-datapoints")
        sys.exit(1)


if __name__ == "__main__":
    main()
