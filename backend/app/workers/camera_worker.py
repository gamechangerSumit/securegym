"""Supervised, vendor-neutral CCTV frame reader.

The worker reads frames only. A configured detector and an observation callback
are supplied by the application runtime; no camera is opened by API startup.
"""
from __future__ import annotations

import logging
import threading
import time
from dataclasses import dataclass
from typing import Callable

from app.services.camera_sources import open_camera_source

logger = logging.getLogger(__name__)


@dataclass(frozen=True)
class CameraWorkerConfig:
    camera_id: int
    stream_url: str
    sample_fps: float = 2.0
    reconnect_initial_seconds: float = 1.0
    reconnect_max_seconds: float = 30.0
    open_timeout_ms: int = 10_000
    read_timeout_ms: int = 10_000

    def __post_init__(self):
        if self.sample_fps <= 0:
            raise ValueError("sample_fps must be greater than zero")
        if self.reconnect_initial_seconds <= 0 or self.reconnect_max_seconds <= 0:
            raise ValueError("Reconnect delays must be greater than zero")


class CameraWorker:
    def __init__(self, config: CameraWorkerConfig, detector, on_frame: Callable | None = None):
        self.config = config
        self.detector = detector
        self.on_frame = on_frame

    def run(self, stop_event: threading.Event) -> None:
        try:
            import cv2  # noqa: F401
        except ImportError as exc:
            raise RuntimeError(
                "Install SecureGym with: pip install '.[camera]' to enable CCTV workers"
            ) from exc

        delay = self.config.reconnect_initial_seconds
        frame_interval = 1.0 / self.config.sample_fps

        while not stop_event.is_set():
            capture = None
            try:
                capture = open_camera_source(
                    self.config.stream_url,
                    open_timeout_ms=self.config.open_timeout_ms,
                    read_timeout_ms=self.config.read_timeout_ms,
                )
                logger.info("Camera worker connected: camera_id=%s", self.config.camera_id)
                delay = self.config.reconnect_initial_seconds
                next_sample = 0.0

                while not stop_event.is_set():
                    ok, frame = capture.read()
                    if not ok:
                        raise RuntimeError("Camera stream stopped returning frames")

                    now = time.monotonic()
                    if now >= next_sample:
                        detections = self.detector.detect(frame)
                        if self.on_frame is not None:
                            self.on_frame(frame, detections, now)
                        next_sample = now + frame_interval
            except Exception as exc:
                if not stop_event.is_set():
                    # Do not log the stream URL: it may contain camera credentials.
                    logger.warning(
                        "Camera %s unavailable (%s); retrying in %.1fs",
                        self.config.camera_id,
                        type(exc).__name__,
                        delay,
                    )
                    stop_event.wait(delay)
                    delay = min(delay * 2, self.config.reconnect_max_seconds)
            finally:
                if capture is not None:
                    capture.release()

        logger.info("Camera worker stopped: camera_id=%s", self.config.camera_id)
