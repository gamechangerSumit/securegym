from datetime import datetime, time, timezone

from fastapi import APIRouter, Depends, HTTPException, WebSocket, WebSocketDisconnect
from sqlalchemy import func, select
from sqlalchemy.orm import Session

from app.core.database import get_db
from app.models import Camera, Incident, Zone
from app.schemas.camera import CameraCreate, CameraRead, ZoneCreate, ZoneRead
from app.schemas.incident import DashboardSummary, IncidentRead, IncidentResolve

router = APIRouter()


@router.post("/cameras", response_model=CameraRead, status_code=201)
def create_camera(payload: CameraCreate, db: Session = Depends(get_db)):
    camera = Camera(**payload.model_dump(), status="disabled")
    # Streams must be explicitly tested/started by an operator.
    camera.enabled = False
    db.add(camera)
    try:
        db.commit()
    except Exception:
        db.rollback()
        raise HTTPException(status_code=409, detail="Camera name already exists")
    db.refresh(camera)
    return camera


@router.get("/cameras", response_model=list[CameraRead])
def list_cameras(db: Session = Depends(get_db)):
    return list(db.scalars(select(Camera).order_by(Camera.id.desc())).all())


@router.post("/zones", response_model=ZoneRead, status_code=201)
def create_zone(payload: ZoneCreate, db: Session = Depends(get_db)):
    if db.get(Camera, payload.camera_id) is None:
        raise HTTPException(status_code=404, detail="Camera not found")
    zone = Zone(**payload.model_dump())
    db.add(zone)
    db.commit()
    db.refresh(zone)
    return zone


@router.get("/zones", response_model=list[ZoneRead])
def list_zones(camera_id: int | None = None, db: Session = Depends(get_db)):
    query = select(Zone)
    if camera_id is not None:
        query = query.where(Zone.camera_id == camera_id)
    return list(db.scalars(query.order_by(Zone.id.desc())).all())


@router.get("/incidents", response_model=list[IncidentRead])
def list_incidents(status: str | None = None, db: Session = Depends(get_db)):
    query = select(Incident).order_by(Incident.first_detected_at.desc())
    if status:
        if status not in {"open", "acknowledged", "resolved"}:
            raise HTTPException(status_code=422, detail="Invalid incident status")
        query = query.where(Incident.status == status)
    return list(db.scalars(query.limit(200)).all())


@router.post("/incidents/{incident_id}/acknowledge", response_model=IncidentRead)
def acknowledge_incident(incident_id: int, db: Session = Depends(get_db)):
    incident = db.get(Incident, incident_id)
    if incident is None:
        raise HTTPException(status_code=404, detail="Incident not found")
    if incident.status == "open":
        incident.status = "acknowledged"
        incident.acknowledged_at = datetime.now(timezone.utc)
        db.commit()
        db.refresh(incident)
    return incident


@router.post("/incidents/{incident_id}/resolve", response_model=IncidentRead)
def resolve_incident(incident_id: int, payload: IncidentResolve, db: Session = Depends(get_db)):
    incident = db.get(Incident, incident_id)
    if incident is None:
        raise HTTPException(status_code=404, detail="Incident not found")
    if incident.status != "resolved":
        incident.status = "resolved"
        incident.resolved_at = datetime.now(timezone.utc)
        incident.resolution_note = payload.note
        db.commit()
        db.refresh(incident)
    return incident


@router.get("/dashboard/summary", response_model=DashboardSummary)
def dashboard_summary(db: Session = Depends(get_db)):
    today_start = datetime.combine(datetime.now(timezone.utc).date(), time.min, tzinfo=timezone.utc)
    return DashboardSummary(
        cameras_total=db.scalar(select(func.count(Camera.id))) or 0,
        cameras_online=db.scalar(select(func.count(Camera.id)).where(Camera.status == "online")) or 0,
        open_incidents=db.scalar(select(func.count(Incident.id)).where(Incident.status == "open")) or 0,
        acknowledged_incidents=db.scalar(
            select(func.count(Incident.id)).where(Incident.status == "acknowledged")
        ) or 0,
        resolved_today=db.scalar(
            select(func.count(Incident.id)).where(
                Incident.status == "resolved", Incident.resolved_at >= today_start
            )
        ) or 0,
    )


@router.websocket("/ws/events")
async def incident_events(websocket: WebSocket):
    await websocket.accept()
    try:
        await websocket.send_json({"type": "connection", "status": "connected"})
        while True:
            await websocket.receive_text()
    except WebSocketDisconnect:
        return
