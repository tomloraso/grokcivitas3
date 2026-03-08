from __future__ import annotations

import importlib.util
from datetime import datetime, timedelta, timezone
from pathlib import Path
from uuid import UUID, uuid4

import pytest
from alembic.migration import MigrationContext
from alembic.operations import Operations
from sqlalchemy import create_engine, inspect, text
from sqlalchemy.engine import Engine

from civitas.domain.identity.models import AppSession, AuthAttempt, AuthIdentity, UserAccount
from civitas.infrastructure.config.settings import AppSettings
from civitas.infrastructure.persistence.postgres_auth_attempt_repository import (
    PostgresAuthAttemptRepository,
)
from civitas.infrastructure.persistence.postgres_session_repository import (
    PostgresSessionRepository,
)
from civitas.infrastructure.persistence.postgres_user_repository import PostgresUserRepository

MIGRATION_PATHS = (
    Path(__file__).resolve().parents[2]
    / "alembic"
    / "versions"
    / "20260307_26_phase_10_auth_session_foundation.py",
    Path(__file__).resolve().parents[2]
    / "alembic"
    / "versions"
    / "20260308_27_phase_10_auth_pkce_hardening.py",
)


def _database_url() -> str:
    return AppSettings().database.url


def _build_engine(database_url: str, *, schema_name: str | None = None) -> Engine:
    connect_args: dict[str, object] = {"connect_timeout": 2}
    if schema_name is not None:
        connect_args["options"] = f"-csearch_path={schema_name}"
    return create_engine(database_url, future=True, connect_args=connect_args)


def _database_available(database_url: str) -> bool:
    engine = _build_engine(database_url)
    try:
        with engine.connect() as connection:
            connection.execute(text("SELECT 1"))
        return True
    except Exception:
        return False
    finally:
        engine.dispose()


DATABASE_URL = _database_url()
DATABASE_AVAILABLE = DATABASE_URL.startswith("postgresql") and _database_available(DATABASE_URL)
pytestmark = pytest.mark.skipif(
    not DATABASE_AVAILABLE,
    reason="Postgres database unavailable for identity repository integration test.",
)


@pytest.fixture()
def engine() -> Engine:
    schema_name = f"test_identity_{uuid4().hex}"
    admin_engine = _build_engine(DATABASE_URL)
    with admin_engine.begin() as connection:
        connection.execute(text(f'CREATE SCHEMA "{schema_name}"'))

    schema_engine = _build_engine(DATABASE_URL, schema_name=schema_name)
    _apply_auth_migrations(schema_engine)

    try:
        yield schema_engine
    finally:
        schema_engine.dispose()
        with admin_engine.begin() as connection:
            connection.execute(text(f'DROP SCHEMA IF EXISTS "{schema_name}" CASCADE'))
        admin_engine.dispose()


def _apply_auth_migrations(engine: Engine) -> None:
    for migration_path in MIGRATION_PATHS:
        migration = _load_migration_module(migration_path)
        original_op = migration.op
        with engine.begin() as connection:
            migration_context = MigrationContext.configure(connection)
            migration.op = Operations(migration_context)
            try:
                migration.upgrade()
            finally:
                migration.op = original_op


def _load_migration_module(migration_path: Path):
    spec = importlib.util.spec_from_file_location(migration_path.stem, migration_path)
    if spec is None or spec.loader is None:
        raise RuntimeError(f"Could not load migration module from {migration_path}")

    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


def test_auth_migration_creates_expected_tables_and_indexes(engine: Engine) -> None:
    inspector = inspect(engine)

    assert set(inspector.get_table_names()) == {
        "app_sessions",
        "auth_attempts",
        "auth_identities",
        "users",
    }
    assert {index["name"] for index in inspector.get_indexes("users")} == {"ix_users_email"}
    assert {index["name"] for index in inspector.get_indexes("auth_identities")} == {
        "ix_auth_identities_user_id"
    }
    assert {index["name"] for index in inspector.get_indexes("app_sessions")} == {
        "ix_app_sessions_expires_at",
        "ix_app_sessions_user_id",
    }
    assert {index["name"] for index in inspector.get_indexes("auth_attempts")} == {
        "ix_auth_attempts_expires_at"
    }


def test_postgres_user_repository_persists_users_and_keeps_identity_mapping_stable(
    engine: Engine,
) -> None:
    repository = PostgresUserRepository(engine=engine)
    created_at = datetime(2026, 3, 7, 10, 0, tzinfo=timezone.utc)
    authenticated_at = created_at + timedelta(minutes=5)
    original_user = repository.add_user(
        UserAccount.create(email="person@example.com", created_at=created_at)
    )

    repository.upsert_auth_identity(
        AuthIdentity.create(
            user_id=original_user.id,
            provider_name="development",
            provider_subject="person@example.com",
            email="person@example.com",
            email_verified=True,
            created_at=authenticated_at,
        )
    )
    repository.update_user_last_sign_in(
        user_id=original_user.id,
        signed_in_at=authenticated_at,
    )

    other_user = repository.add_user(
        UserAccount.create(email="other@example.com", created_at=created_at)
    )
    repository.upsert_auth_identity(
        AuthIdentity.create(
            user_id=other_user.id,
            provider_name="development",
            provider_subject="person@example.com",
            email="person@example.com",
            email_verified=False,
            created_at=authenticated_at + timedelta(minutes=1),
        )
    )

    by_id = repository.get_by_id(user_id=original_user.id)
    by_email = repository.get_by_email(email="person@example.com")
    by_identity = repository.get_by_auth_identity(
        provider_name="development",
        provider_subject="person@example.com",
    )

    assert by_id is not None
    assert by_id.last_sign_in_at == authenticated_at
    assert by_email is not None and by_email.id == original_user.id
    assert by_identity is not None and by_identity.id == original_user.id

    with engine.connect() as connection:
        identity_row = (
            connection.execute(
                text(
                    """
                    SELECT user_id, email_verified
                    FROM auth_identities
                    WHERE provider_name = :provider_name
                      AND provider_subject = :provider_subject
                    """
                ),
                {
                    "provider_name": "development",
                    "provider_subject": "person@example.com",
                },
            )
            .mappings()
            .one()
        )

    assert UUID(str(identity_row["user_id"])) == original_user.id
    assert identity_row["email_verified"] is False


def test_postgres_session_repository_persists_touches_and_revokes_sessions(engine: Engine) -> None:
    user_repository = PostgresUserRepository(engine=engine)
    session_repository = PostgresSessionRepository(engine=engine)
    issued_at = datetime(2026, 3, 7, 10, 0, tzinfo=timezone.utc)
    touched_at = issued_at + timedelta(minutes=10)
    revoked_at = touched_at + timedelta(minutes=5)
    user = user_repository.add_user(
        UserAccount.create(email="person@example.com", created_at=issued_at)
    )

    session = session_repository.add(
        AppSession.create(
            user_id=user.id,
            ttl=timedelta(days=14),
            issued_at=issued_at,
        )
    )
    session_repository.touch(token=session.token, last_seen_at=touched_at)
    revoked = session_repository.revoke(
        token=session.token,
        revoked_at=revoked_at,
        reason="signed_out",
    )
    stored = session_repository.get_by_token(token=session.token)

    assert revoked is not None
    assert stored is not None
    assert stored.user_id == user.id
    assert stored.last_seen_at == touched_at
    assert stored.revoked_at == revoked_at
    assert stored.revoke_reason == "signed_out"


def test_postgres_auth_attempt_repository_consumes_active_attempts_once(engine: Engine) -> None:
    repository = PostgresAuthAttemptRepository(engine=engine)
    issued_at = datetime(2026, 3, 8, 10, 0, tzinfo=timezone.utc)
    consume_at = issued_at + timedelta(minutes=1)
    expired_at = issued_at + timedelta(minutes=20)

    attempt = repository.add(
        AuthAttempt.create(
            return_to="/compare",
            code_verifier="pkce-verifier-1",
            ttl=timedelta(minutes=15),
            issued_at=issued_at,
        )
    )

    consumed = repository.consume(attempt_id=attempt.id, now=consume_at)
    consumed_again = repository.consume(
        attempt_id=attempt.id, now=consume_at + timedelta(seconds=1)
    )

    assert consumed is not None
    assert consumed.id == attempt.id
    assert consumed.return_to == "/compare"
    assert consumed.code_verifier == "pkce-verifier-1"
    assert consumed.consumed_at == consume_at
    assert consumed_again is None

    expired_attempt = repository.add(
        AuthAttempt(
            id="expired-attempt",
            return_to="/sign-in",
            code_verifier="pkce-verifier-2",
            issued_at=issued_at,
            expires_at=expired_at,
            consumed_at=None,
        )
    )

    assert expired_attempt.id == "expired-attempt"
    assert (
        repository.consume(
            attempt_id="expired-attempt",
            now=expired_at + timedelta(seconds=1),
        )
        is None
    )
