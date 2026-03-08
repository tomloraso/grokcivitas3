from __future__ import annotations

from datetime import datetime
from typing import Protocol

from civitas.domain.identity.models import AuthAttempt


class AuthAttemptRepository(Protocol):
    def add(self, attempt: AuthAttempt) -> AuthAttempt: ...

    def consume(self, *, attempt_id: str, now: datetime) -> AuthAttempt | None: ...
