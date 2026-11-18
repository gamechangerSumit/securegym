"""Vendor-neutral OpenCV/FFmpeg camera source adapter.

Accepts standard RTSP/RTSPS and HTTP/HTTPS stream URLs. The adapter deliberately
does not assume a camera manufacturer or construct vendor-specific URL paths.
"""
from __future__ import annotations

import logging
from urllib.parse import urlsplit

logger = logging.getLogger(__name__)

SUPPORTED_SCHEMES = {"rtsp", "rtsps", "http", "https"}


def validate_source_url(source_url: str) -> None:
    parsed = urlsplit(source_url)
    if parsed.scheme.lower() not in SUPPORTED_SCHEMES or not parsed.hostname:
        raise ValueError("Camera source must be a valid RTSP, RTSPS, HTTP or HTTPS URL")


def open_camera_source(source_url: str, *, open_timeout_ms: int = 10_000, read_timeout_ms: int = 10_000):
    """Open a source using FFmpeg first, then OpenCV's automatic backend.

    Credentials are never included in logs or raised error messages.
    """
    validate_source_url(source_url)
    try:
        import cv2
    except ImportError as exc:
        raise RuntimeError(
            "Camera streaming requires OpenCV. Install SecureGym with: pip install '.[camera]'"
        ) from exc

    timeout_props = []
    if hasattr(cv2, "CAP_PROP_OPEN_TIMEOUT_MSEC"):
        timeout_props.extend([cv2.CAP_PROP_OPEN_TIMEOUT_MSEC, open_timeout_ms])
    if hasattr(cv2, "CAP_PROP_READ_TIMEOUT_MSEC"):
        timeout_props.extend([cv2.CAP_PROP_READ_TIMEOUT_MSEC, read_timeout_ms])

    backends = []
    if hasattr(cv2, "CAP_FFMPEG"):
        backends.append(cv2.CAP_FFMPEG)
    backends.append(cv2.CAP_ANY)

    for backend in backends:
        try:
            if timeout_props:
                capture = cv2.VideoCapture(source_url, backend, timeout_props)
            else:
                capture = cv2.VideoCapture(source_url, backend)
            if capture.isOpened():
                if hasattr(cv2, "CAP_PROP_BUFFERSIZE"):
                    capture.set(cv2.CAP_PROP_BUFFERSIZE, 1)
                logger.info("Camera source opened using backend %s", backend)
                return capture
            capture.release()
        except (TypeError, cv2.error):
            # Some OpenCV builds do not support the timeout-parameter overload.
            try:
                capture = cv2.VideoCapture(source_url, backend)
                if capture.isOpened():
                    if hasattr(cv2, "CAP_PROP_BUFFERSIZE"):
                        capture.set(cv2.CAP_PROP_BUFFERSIZE, 1)
                    return capture
                capture.release()
            except cv2.error:
                continue

    raise RuntimeError("Unable to open camera stream; check URL, network, credentials and codec")
