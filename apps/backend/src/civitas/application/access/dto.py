from dataclasses import dataclass
from datetime import datetime
from typing import Literal
from uuid import UUID

from civitas.domain.access.value_objects import BillingInterval, CapabilityKey, EntitlementStatus

AccountAccessState = Literal["anonymous", "free", "pending", "premium"]


@dataclass(frozen=True)
class PremiumProductDto:
    code: str
    display_name: str
    description: str | None
    billing_interval: BillingInterval | None
    duration_days: int | None
    provider_price_lookup_key: str | None
    capability_keys: tuple[CapabilityKey, ...]


@dataclass(frozen=True)
class EntitlementGrantDto:
    id: UUID
    user_id: UUID
    product_code: str
    product_display_name: str
    capability_keys: tuple[CapabilityKey, ...]
    status: EntitlementStatus
    starts_at: datetime
    ends_at: datetime | None
    revoked_at: datetime | None
    revoked_reason_code: str | None


@dataclass(frozen=True)
class CurrentAccountAccessDto:
    state: AccountAccessState
    user_id: UUID | None
    capability_keys: tuple[CapabilityKey, ...]
    entitlements: tuple[EntitlementGrantDto, ...]
