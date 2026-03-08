from __future__ import annotations

from datetime import datetime

from sqlalchemy import text
from sqlalchemy.engine import Engine, RowMapping

from civitas.application.identity.ports.auth_attempt_repository import AuthAttemptRepository
from civitas.domain.identity.models import AuthAttempt


class PostgresAuthAttemptRepository(AuthAttemptRepository):
    def __init__(self, engine: Engine) -> None:
        self._engine = engine

    def add(self, attempt: AuthAttempt) -> AuthAttempt:
        with self._engine.begin() as connection:
            connection.execute(
                text(
                    """
                    INSERT INTO auth_attempts (
                        attempt_id,
                        return_to,
                        code_verifier,
                        issued_at,
                        expires_at,
                        consumed_at
                    ) VALUES (
                        :attempt_id,
                        :return_to,
                        :code_verifier,
                        :issued_at,
                        :expires_at,
                        :consumed_at
                    )
                    """
                ),
                {
                    "attempt_id": attempt.id,
                    "return_to": attempt.return_to,
                    "code_verifier": attempt.code_verifier,
                    "issued_at": attempt.issued_at,
                    "expires_at": attempt.expires_at,
                    "consumed_at": attempt.consumed_at,
                },
            )
        return attempt

    def consume(self, *, attempt_id: str, now: datetime) -> AuthAttempt | None:
        with self._engine.begin() as connection:
            row = (
                connection.execute(
                    text(
                        """
                        UPDATE auth_attempts
                        SET consumed_at = :consumed_at
                        WHERE attempt_id = :attempt_id
                          AND consumed_at IS NULL
                          AND expires_at > :consumed_at
                        RETURNING
                            attempt_id,
                            return_to,
                            code_verifier,
                            issued_at,
                            expires_at,
                            consumed_at
                        """
                    ),
                    {
                        "attempt_id": attempt_id,
                        "consumed_at": now,
                    },
                )
                .mappings()
                .first()
            )
        return _to_auth_attempt(row)


def _to_auth_attempt(row: RowMapping | None) -> AuthAttempt | None:
    if row is None:
        return None

    def _coerce_datetime(value: object) -> datetime | None:
        if value is None:
            return None
        if isinstance(value, datetime):
            return value
        return datetime.fromisoformat(str(value))

    issued_at = _coerce_datetime(row["issued_at"])
    expires_at = _coerce_datetime(row["expires_at"])
    if issued_at is None or expires_at is None:
        return None

    return AuthAttempt(
        id=str(row["attempt_id"]),
        return_to=str(row["return_to"]),
        code_verifier=str(row["code_verifier"]),
        issued_at=issued_at,
        expires_at=expires_at,
        consumed_at=_coerce_datetime(row["consumed_at"]),
    )
