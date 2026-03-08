from __future__ import annotations

from datetime import datetime
from uuid import UUID

from sqlalchemy import text
from sqlalchemy.engine import Engine, RowMapping
from sqlalchemy.exc import IntegrityError

from civitas.application.identity.ports.user_repository import UserRepository
from civitas.domain.identity.models import AuthIdentity, UserAccount


class PostgresUserRepository(UserRepository):
    def __init__(self, engine: Engine) -> None:
        self._engine = engine

    def get_by_id(self, *, user_id: UUID) -> UserAccount | None:
        with self._engine.connect() as connection:
            row = (
                connection.execute(
                    text(
                        """
                        SELECT id, email, created_at, last_sign_in_at
                        FROM users
                        WHERE id = :user_id
                        """
                    ),
                    {"user_id": user_id},
                )
                .mappings()
                .first()
            )
        return _to_user_account(row)

    def get_by_email(self, *, email: str) -> UserAccount | None:
        with self._engine.connect() as connection:
            row = (
                connection.execute(
                    text(
                        """
                        SELECT id, email, created_at, last_sign_in_at
                        FROM users
                        WHERE email = :email
                        """
                    ),
                    {"email": email},
                )
                .mappings()
                .first()
            )
        return _to_user_account(row)

    def get_by_auth_identity(
        self,
        *,
        provider_name: str,
        provider_subject: str,
    ) -> UserAccount | None:
        with self._engine.connect() as connection:
            row = (
                connection.execute(
                    text(
                        """
                        SELECT
                            users.id,
                            users.email,
                            users.created_at,
                            users.last_sign_in_at
                        FROM auth_identities
                        JOIN users ON users.id = auth_identities.user_id
                        WHERE auth_identities.provider_name = :provider_name
                          AND auth_identities.provider_subject = :provider_subject
                        """
                    ),
                    {
                        "provider_name": provider_name,
                        "provider_subject": provider_subject,
                    },
                )
                .mappings()
                .first()
            )
        return _to_user_account(row)

    def add_user(self, user: UserAccount) -> UserAccount:
        with self._engine.begin() as connection:
            connection.execute(
                text(
                    """
                    INSERT INTO users (
                        id,
                        email,
                        created_at,
                        last_sign_in_at
                    ) VALUES (
                        :id,
                        :email,
                        :created_at,
                        :last_sign_in_at
                    )
                    """
                ),
                {
                    "id": user.id,
                    "email": user.email,
                    "created_at": user.created_at,
                    "last_sign_in_at": user.last_sign_in_at,
                },
            )
        return user

    def upsert_auth_identity(self, identity: AuthIdentity) -> AuthIdentity:
        params = {
            "user_id": identity.user_id,
            "provider_name": identity.provider_name,
            "provider_subject": identity.provider_subject,
            "email": identity.email,
            "email_verified": identity.email_verified,
            "created_at": identity.created_at,
            "last_authenticated_at": identity.last_authenticated_at,
        }

        with self._engine.begin() as connection:
            updated = connection.execute(
                text(
                    """
                    UPDATE auth_identities
                    SET
                        email = :email,
                        email_verified = :email_verified,
                        last_authenticated_at = :last_authenticated_at
                    WHERE provider_name = :provider_name
                      AND provider_subject = :provider_subject
                    """
                ),
                params,
            )
            if updated.rowcount and updated.rowcount > 0:
                return identity

            try:
                connection.execute(
                    text(
                        """
                        INSERT INTO auth_identities (
                            user_id,
                            provider_name,
                            provider_subject,
                            email,
                            email_verified,
                            created_at,
                            last_authenticated_at
                        ) VALUES (
                            :user_id,
                            :provider_name,
                            :provider_subject,
                            :email,
                            :email_verified,
                            :created_at,
                            :last_authenticated_at
                        )
                        """
                    ),
                    params,
                )
            except IntegrityError:
                connection.execute(
                    text(
                        """
                        UPDATE auth_identities
                        SET
                            email = :email,
                            email_verified = :email_verified,
                            last_authenticated_at = :last_authenticated_at
                        WHERE provider_name = :provider_name
                          AND provider_subject = :provider_subject
                        """
                    ),
                    params,
                )
        return identity

    def update_user_last_sign_in(self, *, user_id: UUID, signed_in_at: datetime) -> None:
        with self._engine.begin() as connection:
            connection.execute(
                text(
                    """
                    UPDATE users
                    SET last_sign_in_at = :signed_in_at
                    WHERE id = :user_id
                    """
                ),
                {
                    "user_id": user_id,
                    "signed_in_at": signed_in_at,
                },
            )


def _to_user_account(row: RowMapping | None) -> UserAccount | None:
    if row is None:
        return None

    created_at = row["created_at"]
    last_sign_in_at = row["last_sign_in_at"]
    return UserAccount(
        id=UUID(str(row["id"])),
        email=str(row["email"]),
        created_at=created_at
        if isinstance(created_at, datetime)
        else datetime.fromisoformat(str(created_at)),
        last_sign_in_at=(
            last_sign_in_at
            if isinstance(last_sign_in_at, datetime) or last_sign_in_at is None
            else datetime.fromisoformat(str(last_sign_in_at))
        ),
    )
