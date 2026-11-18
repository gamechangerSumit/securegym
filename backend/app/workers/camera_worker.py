"""CCTV worker boundary.

Production workers should be supervised outside the API process (one worker per camera),
reconnect with bounded exponential backoff, sample frames and emit observations. This
module deliberately does not auto-connect to stream URLs on API startup.
"""
import logging
from dataclasses import dataclass

logger = logging.getLogger(__name__)


@dataclass(frozen=True)
class CameraWorkerConfig:
    camera_id: int
    stream_url: str
    sample_fps: float = 2.0


class CameraWorker:
    def __init__(self, config: CameraWorkerConfig, detector):
        self.config = config
        self.detector = detector

    def run(self, stop_event) -> None:
        try:
            import cv2
        except ImportError as exc:
            raise RuntimeError("Install SecureGym with the vision extra to enable CCTV workers") from exc

        capture = cv2.VideoCapture(self.config.stream_url)
        if not capture.isOpened():
            raise RuntimeError(f"Unable to open CCTV stream for camera {self.config.camera_id}")
        logger.info("Camera worker started: %s", self.config.camera_id)
        try:
            while not stop_event.is_set():
                ok, frame = capture.read()
                if not ok:
                    raise RuntimeError("CCTV stream disconnected; supervisor should reconnect")
                self.detector.detect(frame)
        finally:
            capture.release()
            logger.info("Camera worker stopped: %s", self.config.camera_id)
