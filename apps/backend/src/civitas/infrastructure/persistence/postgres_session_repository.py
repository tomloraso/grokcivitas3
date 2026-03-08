from __future__ import annotations

from datetime import datetime
from uuid import UUID

from sqlalchemy import text
from sqlalchemy.engine import Engine, RowMapping

from civitas.application.identity.ports.session_repository import SessionRepository
from civitas.domain.identity.models import AppSession


class PostgresSessionRepository(SessionRepository):
    def __init__(self, engine: Engine) -> None:
        self._engine = engine

    def add(self, session: AppSession) -> AppSession:
        with self._engine.begin() as connection:
            connection.execute(
                text(
                    """
                    INSERT INTO app_sessions (
                        token,
                        user_id,
                        issued_at,
                        last_seen_at,
                        expires_at,
                        revoked_at,
                        revoke_reason
                    ) VALUES (
                        :token,
                        :user_id,
                        :issued_at,
                        :last_seen_at,
                        :expires_at,
                        :revoked_at,
                        :revoke_reason
                    )
                    """
                ),
                {
                    "token": session.token,
                    "user_id": session.user_id,
                    "issued_at": session.issued_at,
                    "last_seen_at": session.last_seen_at,
                    "expires_at": session.expires_at,
                    "revoked_at": session.revoked_at,
                    "revoke_reason": session.revoke_reason,
                },
            )
        return session

    def get_by_token(self, *, token: str) -> AppSession | None:
        with self._engine.connect() as connection:
            row = (
                connection.execute(
                    text(
                        """
                        SELECT
                            token,
                            user_id,
                            issued_at,
                            last_seen_at,
                            expires_at,
                            revoked_at,
                            revoke_reason
                        FROM app_sessions
                        WHERE token = :token
                        """
                    ),
                    {"token": token},
                )
                .mappings()
                .first()
            )
        return _to_app_session(row)

    def revoke(self, *, token: str, revoked_at: datetime, reason: str) -> AppSession | None:
        params = {
            "token": token,
            "revoked_at": revoked_at,
            "reason": reason,
        }

        with self._engine.begin() as connection:
            connection.execute(
                text(
                    """
                    UPDATE app_sessions
                    SET
                        revoked_at = COALESCE(revoked_at, :revoked_at),
                        revoke_reason = COALESCE(revoke_reason, :reason)
                    WHERE token = :token
                    """
                ),
                params,
            )

        return self.get_by_token(token=token)

    def touch(self, *, token: str, last_seen_at: datetime) -> None:
        with self._engine.begin() as connection:
            connection.execute(
                text(
                    """
                    UPDATE app_sessions
                    SET last_seen_at = :last_seen_at
                    WHERE token = :token
                    """
                ),
                {
                    "token": token,
                    "last_seen_at": last_seen_at,
                },
            )


def _to_app_session(row: RowMapping | None) -> AppSession | None:
    if row is None:
        return None

    def _coerce_datetime(value: object) -> datetime | None:
        if value is None:
            return None
        if isinstance(value, datetime):
            return value
        return datetime.fromisoformat(str(value))

    return AppSession(
        token=str(row["token"]),
        user_id=UUID(str(row["user_id"])),
        issued_at=_coerce_datetime(row["issued_at"]) or datetime.min,
        last_seen_at=_coerce_datetime(row["last_seen_at"]) or datetime.min,
        expires_at=_coerce_datetime(row["expires_at"]) or datetime.min,
        revoked_at=_coerce_datetime(row["revoked_at"]),
        revoke_reason=(str(row["revoke_reason"]) if row["revoke_reason"] is not None else None),
    )
