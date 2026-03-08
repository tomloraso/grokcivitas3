from __future__ import annotations

from datetime import datetime
from typing import Protocol

from civitas.domain.identity.models import AppSession


class SessionRepository(Protocol):
    def add(self, session: AppSession) -> AppSession: ...

    def get_by_token(self, *, token: str) -> AppSession | None: ...

    def revoke(self, *, token: str, revoked_at: datetime, reason: str) -> AppSession | None: ...

    def touch(self, *, token: str, last_seen_at: datetime) -> None: ...
