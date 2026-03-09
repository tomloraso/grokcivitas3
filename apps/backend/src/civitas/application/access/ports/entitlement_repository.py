from datetime import datetime
from typing import Protocol
from uuid import UUID

from civitas.domain.access.models import EntitlementEvent, EntitlementGrant


class EntitlementRepository(Protocol):
    def get_entitlement(self, *, entitlement_id: UUID) -> EntitlementGrant | None: ...

    def list_user_entitlements(self, *, user_id: UUID) -> tuple[EntitlementGrant, ...]: ...

    def list_active_capability_keys(
        self,
        *,
        user_id: UUID,
        at: datetime,
    ) -> tuple[str, ...]: ...

    def upsert_entitlement(self, entitlement: EntitlementGrant) -> EntitlementGrant: ...

    def append_event(self, event: EntitlementEvent) -> EntitlementEvent: ...

    def list_entitlement_events(
        self,
        *,
        entitlement_id: UUID | None = None,
        user_id: UUID | None = None,
    ) -> tuple[EntitlementEvent, ...]: ...
