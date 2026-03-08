from __future__ import annotations

from urllib.parse import urlparse

from fastapi import HTTPException, Request


def require_allowed_cookie_origin(
    request: Request,
    *,
    cookie_name: str,
    allowed_origins: tuple[str, ...],
) -> None:
    if not request.cookies.get(cookie_name):
        return

    normalized_origin = _normalize_request_origin(request.headers.get("origin"))
    if normalized_origin is None or normalized_origin not in allowed_origins:
        raise HTTPException(status_code=403, detail="origin not allowed")


def _normalize_request_origin(origin: str | None) -> str | None:
    if origin is None:
        return None

    candidate = origin.strip()
    if not candidate:
        return None

    parsed = urlparse(candidate)
    if (
        not parsed.scheme
        or not parsed.netloc
        or parsed.path not in {"", "/"}
        or parsed.params
        or parsed.query
        or parsed.fragment
    ):
        return None

    return f"{parsed.scheme.casefold()}://{parsed.netloc.casefold()}"
