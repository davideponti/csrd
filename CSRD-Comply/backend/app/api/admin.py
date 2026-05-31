"""
CSRD Comply — Admin API Endpoints

Endpoint per operazioni amministrative come seed dei datapoint ESRS.
"""
import logging
from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from app.core.database import get_db
from app.core.deps import get_current_user
from app.models import User, EsrsDatapoint
from app.seed_esrs_datapoints import get_all_datapoints, seed_to_db, save_fallback_json

logger = logging.getLogger(__name__)

router = APIRouter()


@router.post("/seed-datapoints")
def seed_esrs_datapoints(
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    """
    Popola la tabella esrs_datapoints con tutti i datapoint dal file Excel.
    
    Legge il file EFRAG IG 3 (data/efrag_ig3_datapoints.xlsx) o usa fallback JSON/minimal.
    Crea solo datapoint mancanti, non duplica.
    
    Richiede: utente autenticato (qualsiasi ruolo)
    """
    try:
        # Ottieni datapoint (prima Excel, poi fallback JSON, poi minimali)
        datapoints = get_all_datapoints(use_excel=True)

        if not datapoints:
            raise HTTPException(
                status_code=500,
                detail="Nessun datapoint trovato. Verifica che il file Excel esista.",
            )

        # Salva fallback JSON per prossima volta
        try:
            save_fallback_json(datapoints)
        except Exception:
            pass  # Non bloccante

        # Importa nel DB
        created = seed_to_db(db, datapoints)

        # Verifica finale
        total = db.query(EsrsDatapoint).count()

        # Verifica copertura topic
        topics_covered = set()
        all_dps = db.query(EsrsDatapoint).all()
        for dp in all_dps:
            topic = dp.standard_ref.split("-")[0]
            topics_covered.add(topic)

        required_topics = [
            "ESRS E1", "ESRS E2", "ESRS E3", "ESRS E4", "ESRS E5",
            "ESRS S1", "ESRS S2", "ESRS S3", "ESRS S4", "ESRS G1",
        ]
        missing_topics = [t for t in required_topics if t not in topics_covered]

        return {
            "success": True,
            "new_datapoints_created": created,
            "total_datapoints_in_db": total,
            "topics_covered": sorted(list(topics_covered)),
            "topics_missing": missing_topics,
            "message": (
                f"Seed completato. {created} nuovi datapoint creati, {total} totali."
                if created > 0
                else f"Database già popolato con {total} datapoint."
            ),
        }

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Seed datapoints error: {e}")
        raise HTTPException(status_code=500, detail=f"Errore seed: {str(e)}")


@router.get("/datapoints-status")
def check_datapoints_status(
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    """Verifica lo stato della tabella esrs_datapoints."""
    total = db.query(EsrsDatapoint).count()

    # Conteggio per topic
    all_dps = db.query(EsrsDatapoint).all()
    by_topic = {}
    topics_covered = set()
    for dp in all_dps:
        topic = dp.standard_ref.split("-")[0]
        topics_covered.add(topic)
        by_topic[topic] = by_topic.get(topic, 0) + 1

    # Controllo se qualche topic IRO può matchare
    sample_refs = []
    if total > 0:
        sample_refs = [
            dp.standard_ref
            for dp in db.query(EsrsDatapoint).limit(20).all()
        ]

    return {
        "total_datapoints": total,
        "by_topic": by_topic,
        "topics_covered": sorted(list(topics_covered)),
        "sample_references": sample_refs,
        "is_ready_for_scoring": total >= 10,
        "warning": (
            "Tabella vuota! Chiama POST /api/v1/admin/seed-datapoints per popolarla."
            if total == 0 else None
        ),
    }
