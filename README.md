# SecureGym — AI-powered gym equipment monitoring

SecureGym monitors authorised gym CCTV streams for equipment left outside configured storage zones, records evidence and alerts staff.

> Detection is assistive, not infallible. Gym equipment classes need validation or fine-tuning against footage from the target gym. The initial backend separates camera ingestion, detection, incident rules and notifications so a validated model can be integrated safely.
>
> Identity limitation: a camera track ID is not a member identity. SecureGym does not identify people by face. Member attribution is only possible through an approved, consent-based member-session integration with sufficiently reliable correlation. Otherwise the incident remains Unknown.

## Architecture

```text
Existing IP CCTV (RTSP/ONVIF)
          |
Camera Adapter (OpenCV worker)
          |
Detector + tracker (gym-validated YOLO model)
          |
Zone & dwell-time rule engine
          +----> Evidence snapshots / optional clips
          |
Incident API + PostgreSQL/SQLite
          +----> WebSocket dashboard
          +----> Email / Telegram / push adapter
          +----> Audit history & resolution
```

## MVP capabilities

- Camera registry and health status.
- Configurable monitored zones and equipment storage zones.
- Incident creation when an item remains outside its home zone beyond a configured dwell threshold.
- Evidence metadata: camera, timestamps, equipment class, confidence and snapshot path.
- Incident acknowledgement and resolution.
- Console notification adapter by default; external alert providers can be configured.
- Unknown attribution unless trusted member-session integration is configured.

## Stack

- Python 3.12, FastAPI, Pydantic Settings
- SQLAlchemy 2; SQLite locally, PostgreSQL through DATABASE_URL
- OpenCV camera adapter
- Optional Ultralytics YOLO adapter
- Docker Compose

## Quick start

```bash
cp .env.example .env
docker compose up --build
```

API: http://localhost:8000 | Swagger: http://localhost:8000/docs | Health: http://localhost:8000/health

Local development:

```bash
cd backend
python -m venv .venv
# Windows: .venv\\Scripts\\activate
# Linux/macOS: source .venv/bin/activate
pip install -e '.[dev]'
uvicorn app.main:app --reload
```

## Configure CCTV

1. Confirm the camera/NVR exposes an authorised RTSP stream (or use ONVIF discovery to obtain it).
2. Store stream credentials in a secret manager or local .env; never commit credentials or expose them in frontend code/logs.
3. Create a camera through POST /api/v1/cameras.
4. Add zones with POST /api/v1/zones. Polygon points are normalised coordinates between 0 and 1.
5. Test connectivity and retention policy before starting workers. Cameras are created disabled by default.

Example camera payload:

```json
{
  "name": "Main dumbbell area",
  "stream_url": "rtsp://USER:PASSWORD@CAMERA_HOST:554/stream1",
  "location": "Free weights",
  "enabled": false
}
```

## Detection strategy and limits

The initial code includes a detector protocol, a safe no-op default and an optional Ultralytics adapter. Generic pretrained weights are not claimed to detect gym equipment reliably. Before production, collect authorised representative day/night footage, label dumbbells/plates/kettlebells/barbells, train and validate on held-out footage, measure per-class false positives/negatives, and calibrate zones and dwell thresholds. Do not alert on a single frame; require persistence and deduplicate incidents.

## Identity, privacy and retention

- No face recognition is included.
- Track IDs are temporary and may change after occlusion or stream restart.
- Do not blame a member based only on proximity.
- Add member-session correlation only with gym approval, appropriate notice/consent, access controls and audit trail.
- Restrict evidence access and configure retention; mask irrelevant areas.

## Initial API

- GET /health
- POST/GET /api/v1/cameras
- POST/GET /api/v1/zones
- GET /api/v1/incidents
- POST /api/v1/incidents/{id}/acknowledge
- POST /api/v1/incidents/{id}/resolve
- GET /api/v1/dashboard/summary
- WS /api/v1/ws/events

## Roadmap

1. Foundation: API, persistence, incident lifecycle, detector boundary and tests.
2. Camera connectivity: RTSP reader, reconnect/backoff and health metrics.
3. Vision: gym dataset, trained model, tracking and calibrated storage zones.
4. Alerts: Telegram/email/push, escalation, quiet hours and deduplication.
5. Dashboard: camera health, live incidents, evidence review and audit.
6. Optional member-session correlation with confidence gating.

License to be selected by repository owner before public distribution.
