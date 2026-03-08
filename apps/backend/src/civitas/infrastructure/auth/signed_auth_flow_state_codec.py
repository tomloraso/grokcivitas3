from __future__ import annotations

from collections.abc import Callable
from datetime import datetime, timedelta, timezone

from civitas.application.identity.dto import AuthFlowStateDto
from civitas.application.identity.errors import InvalidAuthCallbackError
from civitas.application.identity.ports.auth_flow_state_codec import AuthFlowStateCodec
from civitas.infrastructure.auth.signed_tokens import SignedTokenCodec

Clock = Callable[[], datetime]


def _utc_now() -> datetime:
    return datetime.now(timezone.utc)


class SignedAuthFlowStateCodec(AuthFlowStateCodec):
    def __init__(
        self,
        *,
        shared_secret: str,
        ttl: timedelta,
        clock: Clock = _utc_now,
    ) -> None:
        self._clock = clock
        self._codec = SignedTokenCodec(
            secret=shared_secret,
            ttl=ttl,
            purpose="auth_state",
        )

    def issue(self, *, attempt_id: str) -> str:
        return self._codec.issue(
            payload={"attempt_id": attempt_id.strip()},
            now=self._clock(),
        )

    def read(self, *, state: str) -> AuthFlowStateDto:
        try:
            payload = self._codec.read(token=state, now=self._clock())
        except ValueError as exc:
            raise InvalidAuthCallbackError("invalid auth state") from exc

        attempt_id = payload.get("attempt_id")
        if not isinstance(attempt_id, str) or not attempt_id.strip():
            raise InvalidAuthCallbackError("invalid auth state")
        return AuthFlowStateDto(attempt_id=attempt_id.strip())
