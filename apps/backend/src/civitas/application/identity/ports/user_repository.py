from __future__ import annotations

from datetime import datetime
from typing import Protocol
from uuid import UUID

from civitas.domain.identity.models import AuthIdentity, UserAccount


class UserRepository(Protocol):
    def get_by_id(self, *, user_id: UUID) -> UserAccount | None: ...

    def get_by_email(self, *, email: str) -> UserAccount | None: ...

    def get_by_auth_identity(
        self, *, provider_name: str, provider_subject: str
    ) -> UserAccount | None: ...

    def add_user(self, user: UserAccount) -> UserAccount: ...

    def upsert_auth_identity(self, identity: AuthIdentity) -> AuthIdentity: ...

    def update_user_last_sign_in(self, *, user_id: UUID, signed_in_at: datetime) -> None: ...
