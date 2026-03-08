from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime, timezone
from typing import Literal

from fastapi import Response


@dataclass(frozen=True)
class SessionCookieSettings:
    name: str
    secure: bool
    samesite: Literal["lax", "strict", "none"]


def set_session_cookie(
    response: Response,
    *,
    settings: SessionCookieSettings,
    session_token: str,
    expires_at: datetime,
) -> None:
    now = datetime.now(timezone.utc)
    max_age = max(0, int((expires_at - now).total_seconds()))
    response.set_cookie(
        key=settings.name,
        value=session_token,
        httponly=True,
        secure=settings.secure,
        samesite=settings.samesite,
        max_age=max_age,
        expires=expires_at,
        path="/",
    )


def clear_session_cookie(response: Response, *, settings: SessionCookieSettings) -> None:
    response.delete_cookie(
        key=settings.name,
        httponly=True,
        secure=settings.secure,
        samesite=settings.samesite,
        path="/",
    )
