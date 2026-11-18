# SecureGym — AI-powered gym equipment monitoring

SecureGym is designed to work with **multiple CCTV brands**, provided the recorder/camera exposes a standard, authorised video stream. It monitors configured gym zones for equipment left outside storage, records evidence and alerts staff.

> Detection is assistive, not infallible. Gym equipment classes need validation or fine-tuning against footage from the target gym.
>
> Identity limitation: a camera track ID is not a member identity. SecureGym does not identify people by face. Member attribution is either a consent-based check-in/session candidate requiring trainer verification, or a trainer's explicit manual verification. Otherwise the incident remains Unknown.

## Current MVP foundation

- Camera registry; streams are disabled until explicitly enabled.
- Vendor-neutral camera source adapter: RTSP, RTSPS, HTTP and HTTPS.
- FFmpeg-first/OpenCV automatic-backend fallback for compatible streams.
- Reconnecting camera worker with bounded exponential backoff and configurable frame sampling.
- Storage zones with normalised polygon coordinates.
- Persistent dwell tracking; default alert threshold is **300 seconds (5 minutes)**.
- Configurable equipment classes: dumbbell, weight plate, barbell, kettlebell, cable attachment and other equipment.
- Incident creation, deduplication, acknowledgement and resolution.
- Optional JPEG evidence storage.
- Dashboard WebSocket event with buzzer flag.
- Optional SMTP email notification.
- Consent-gated member session records and trainer attribution endpoint.

## Camera compatibility

SecureGym does not hard-code a single manufacturer URL pattern. It can consume standard stream URLs exposed by many Hikvision, Dahua, CP Plus and other compatible devices. Compatibility depends on the exact camera/NVR model, firmware, enabled protocols, network access and account permissions.

Supported input schemes:
- `rtsp://` and `rtsps://`
- `http://` and `https://` when the device exposes a compatible video stream

The adapter tries OpenCV's FFmpeg backend first and then its automatic backend. ONVIF discovery and automatic stream-URI retrieval are a separate integration step; not every recorder exposes ONVIF or RTSP. Proprietary-only devices may need a vendor SDK or a recorder-side stream bridge.

## Architecture

```text
Existing IP CCTV / DVR / NVR
          |
Standard RTSP / RTSPS / HTTP(S) stream
          |
Vendor-neutral FFmpeg/OpenCV camera adapter
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
- OpenCV camera adapter (optional install)
- Optional Ultralytics YOLO adapter
- Docker Compose for the API

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
pip install -e '.[dev,camera]'
uvicorn app.main:app --reload
```

For the optional YOLO adapter, install `pip install -e '.[vision]` and configure a gym-validated model path. A generic pretrained model is not guaranteed to recognise gym equipment.

## CCTV setup

1. Get permission and stream credentials from the gym owner/admin. Do not send passwords in chat or commit them to Git.
2. Find the DVR/NVR local IP address and enable RTSP (and ONVIF if supported) in its settings.
3. Create a camera using POST /api/v1/cameras with the stream URL supplied by the recorder's own documentation/configuration.
4. Test one camera stream first, then add cameras incrementally up to the planned 4–8.
5. Add a storage zone using POST /api/v1/zones. Polygon coordinates are normalised from 0 to 1.
6. Enable a camera using POST /api/v1/cameras/{id}/enable only after the stream is verified.

Example camera:

```json
{
  "name": "Main dumbbell area",
  "stream_url": "rtsp://USER:PASSWORD@CAMERA_HOST:554/stream1",
  "location": "Free weights"
}
```

Do not assume the example path works on every recorder. Use the exact RTSP URL provided by that device. Keep the URL and credentials in local environment/secrets storage.

## Equipment dwell rule

Each configured storage zone defaults to 300 seconds. The vision worker must send repeated observations for the same camera, zone, equipment class and track. The state is persisted; a gap longer than the allowed observation interval restarts the dwell clock. A single detection frame must never trigger an incident.

The observation ingest contract is POST /api/v1/observations. It expects a worker to supply:
- camera_id and zone_id
- equipment_class and optional track_id
- confidence
- outside_storage boolean
- observed_at_epoch (UTC Unix timestamp)
- optional base64 JPEG evidence frame

**Integration status:** the observation-to-incident service and dwell-state persistence are implemented. The camera source adapter and reconnecting frame worker are now present, but the worker is not yet wired to zone geometry, observation ingestion, camera health persistence or a production supervisor. Do not treat monitoring as live until that pipeline is connected and tested against the actual recorder.

## Notifications

- Dashboard buzzer: connect to WS /api/v1/ws/events and play an audible alert when an equipment_incident event arrives with buzzer=true.
- Email: configure SMTP_HOST, SMTP_PORT, SMTP_USERNAME, SMTP_PASSWORD and ALERT_EMAIL_TO in .env.
- Mobile: native/browser push subscriptions and service-worker delivery are not implemented yet.

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

1. Add ONVIF discovery and automatic stream URI retrieval for recorders that support it.
2. Wire the frame worker to zone geometry, object tracking and the observation API.
3. Add a production worker supervisor and camera health reporting for all configured streams.
4. Train/validate a gym-specific model for dumbbells, plates, barbells, kettlebells and cable attachments.
5. Add secure staff authentication, roles and evidence access control.
6. Build the frontend dashboard, audible buzzer and mobile PWA push notifications.
7. Add integration tests, migrations, alert delivery monitoring and retention cleanup.
8. Pilot one camera during busy and quiet hours; measure false positives before enabling all cameras.

## License

To be selected by the repository owner before public distribution.
