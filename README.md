# SecureGym — AI-powered gym equipment monitoring

SecureGym monitors authorised gym CCTV streams for equipment left outside configured storage zones, records evidence and alerts staff.

> Detection is assistive, not infallible. Gym equipment classes need validation or fine-tuning against footage from the target gym. The initial backend separates camera ingestion, detection, incident rules and notifications so a validated model can be integrated safely.
>
> Identity limitation: a camera track ID is not a member identity. SecureGym does not identify people by face. Member attribution is either a consent-based check-in/session candidate requiring trainer verification, or a trainer's explicit manual verification. Otherwise the incident remains Unknown.

## Current MVP foundation

- Camera registry; streams are disabled until explicitly enabled.
- Storage zones with normalised polygon coordinates.
- Persistent dwell tracking; default alert threshold is **300 seconds (5 minutes)**.
- Configurable equipment classes: dumbbell, weight plate, barbell, kettlebell, cable attachment and other equipment.
- Incident creation, deduplication, acknowledgement and resolution.
- Optional JPEG evidence storage.
- Dashboard WebSocket event with buzzer flag.
- Optional SMTP email notification.
- Consent-gated member session records and trainer attribution endpoint.
- Session candidate matching is never treated as proof; trainer verification is required.

## Architecture

```text
Existing IP CCTV (RTSP/ONVIF)
          |
Camera Adapter (OpenCV worker)
          |
Gym-trained detector + object tracker
          |
Storage-zone geometry + persistent 5-minute dwell state
          |
Evidence snapshot + incident
          +----> WebSocket dashboard event / buzzer
          +----> SMTP email
          +----> Trainer/member-session verification
```

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

## CCTV setup

Camera type is currently unknown for the target gym. First identify the DVR/NVR brand and model, then confirm whether it exposes an authorised RTSP stream or ONVIF. For 4–8 cameras, start by testing one stream and then add cameras incrementally.

1. Ask the gym owner/admin for authorised DVR/NVR access.
2. Find the recorder model and stream URL format; do not guess credentials or expose them in source control.
3. Create a camera using POST /api/v1/cameras. Camera remains disabled by default.
4. Add a storage zone using POST /api/v1/zones. Polygon coordinates are normalised from 0 to 1.
5. Enable a camera using POST /api/v1/cameras/{id}/enable only after the stream is verified.

Example camera:

```json
{
  "name": "Main dumbbell area",
  "stream_url": "rtsp://USER:PASSWORD@CAMERA_HOST:554/stream1",
  "location": "Free weights"
}
```

## Equipment dwell rule

Each configured storage zone defaults to 300 seconds. The vision worker must send repeated observations for the same camera, zone, equipment class and track. The state is persisted; a gap longer than the allowed observation interval restarts the dwell clock. A single detection frame must never trigger an incident.

The observation ingest contract is POST /api/v1/observations. It expects a worker to supply:
- camera_id and zone_id
- equipment_class and optional track_id
- confidence
- outside_storage boolean
- observed_at_epoch (UTC Unix timestamp)
- optional base64 JPEG evidence frame

**Integration status:** the observation-to-incident service and dwell-state persistence are implemented. The current OpenCV worker is still a worker boundary and does not yet calculate zone membership, emit observations or supervise reconnects. Do not treat camera monitoring as live until that adapter is completed and tested against the actual NVR.

## Notifications

- Dashboard buzzer: connect to WS /api/v1/ws/events and play an audible alert when an equipment_incident event arrives with buzzer=true.
- Email: configure SMTP_HOST, SMTP_PORT, SMTP_USERNAME, SMTP_PASSWORD and ALERT_EMAIL_TO in .env.
- Mobile: the API event can feed a responsive dashboard/PWA. Native browser push subscriptions and service-worker delivery are not implemented yet.

## Member attribution

- Create a member session through POST /api/v1/member-sessions with consent_recorded=true.
- Ask the system for a candidate through POST /api/v1/incidents/{id}/attribute/session-candidate. It only proposes a match if exactly one consented session is active for that camera and event timestamp.
- A trainer can explicitly verify a member using POST /api/v1/incidents/{id}/attribute/manual with member_id and a verification note.
- Multiple/no session candidates remain Unknown. A possible session candidate is not proof that the member left the equipment.

No facial recognition is included. Track IDs are temporary and may change after occlusion or stream restart. Restrict evidence access, set retention, provide appropriate notices and mask irrelevant areas.

## API

- GET /health
- POST/GET /api/v1/cameras
- POST /api/v1/cameras/{id}/enable and /disable
- POST/GET /api/v1/zones
- POST /api/v1/observations
- GET /api/v1/incidents
- POST /api/v1/incidents/{id}/acknowledge and /resolve
- POST /api/v1/incidents/{id}/attribute/session-candidate
- POST /api/v1/incidents/{id}/attribute/manual
- POST /api/v1/member-sessions
- GET /api/v1/dashboard/summary
- WS /api/v1/ws/events

## Remaining implementation before production

1. Discover and validate the actual DVR/NVR streams for all 4–8 cameras.
2. Implement the complete camera supervisor, reconnect/backoff, frame sampling and observation emitter.
3. Train/validate a gym-specific model for dumbbells, plates, barbells, kettlebells and cable attachments.
4. Add secure staff authentication, roles and evidence access control.
5. Build the frontend dashboard, audible buzzer and mobile PWA push notifications.
6. Add integration tests, migrations, alert delivery monitoring and retention cleanup.
7. Pilot one camera during busy and quiet hours; measure false positives before enabling all cameras.

## License

To be selected by the repository owner before public distribution.
