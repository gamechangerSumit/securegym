from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session

from app.core.database import get_db
from app.schemas.incident import IncidentRead
from app.schemas.incident_observation import EquipmentObservation
from app.services.observation_service import process_observation

router = APIRouter()


@router.post("/observations", response_model=IncidentRead | None)
def ingest_observation(payload: EquipmentObservation, db: Session = Depends(get_db)):
    try:
        incident, _created = process_observation(db, payload)
    except ValueError as exc:
        raise HTTPException(status_code=422, detail=str(exc)) from exc
    return incident
