from __future__ import annotations

from urllib.parse import urlparse

DEFAULT_RETURN_TO = "/"


def normalize_return_to(return_to: str | None) -> str:
    if return_to is None:
        return DEFAULT_RETURN_TO

    candidate = return_to.strip()
    if not candidate:
        return DEFAULT_RETURN_TO

    parsed = urlparse(candidate)
    if parsed.scheme or parsed.netloc:
        return DEFAULT_RETURN_TO
    if not candidate.startswith("/") or candidate.startswith("//"):
        return DEFAULT_RETURN_TO
    return candidate
