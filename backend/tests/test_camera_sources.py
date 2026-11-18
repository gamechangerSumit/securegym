from urllib.parse import urlsplit

import pytest

from app.services.camera_sources import validate_source_url


@pytest.mark.parametrize(
    "url",
    [
        "rtsp://camera.local:554/stream1",
        "rtsps://camera.local/live",
        "http://camera.local/video",
        "https://camera.local/stream",
    ],
)
def test_accepts_standard_vendor_neutral_stream_schemes(url):
    validate_source_url(url)


@pytest.mark.parametrize(
    "url",
    ["", "camera.local/stream", "ftp://camera.local/stream", "rtsp:///missing-host"],
)
def test_rejects_unsupported_or_invalid_sources(url):
    with pytest.raises(ValueError):
        validate_source_url(url)


def test_url_credentials_are_not_needed_for_validation():
    url = "rtsp://user:secret@camera.local:554/live"
    validate_source_url(url)
    assert urlsplit(url).hostname == "camera.local"
