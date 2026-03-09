from __future__ import annotations

from datetime import datetime
from typing import Literal
from uuid import UUID

from pydantic import BaseModel


class BillingProductResponse(BaseModel):
    code: str
    display_name: str
    description: str | None
    billing_interval: Literal["monthly", "annual", "one_time"] | None
    duration_days: int | None
    capability_keys: list[str]


class BillingProductsResponse(BaseModel):
    products: list[BillingProductResponse]


class CheckoutSessionCreateRequest(BaseModel):
    product_code: str
    success_path: str | None = None
    cancel_path: str | None = None


class CheckoutSessionCreateResponse(BaseModel):
    checkout_id: UUID | None
    product_code: str
    status: Literal["open", "already_covered"]
    redirect_url: str | None
    expires_at: datetime | None
    account_access_state: Literal["anonymous", "free", "pending", "premium"]


class CheckoutSessionStatusResponse(BaseModel):
    checkout_id: UUID
    product_code: str
    status: Literal[
        "open",
        "already_covered",
        "processing_payment",
        "completed",
        "canceled",
        "expired",
        "failed",
    ]
    redirect_url: str | None
    expires_at: datetime | None
    account_access_state: Literal["anonymous", "free", "pending", "premium"]


class BillingPortalSessionCreateRequest(BaseModel):
    return_path: str | None = None


class BillingPortalSessionCreateResponse(BaseModel):
    redirect_url: str


class BillingWebhookResponse(BaseModel):
    provider_event_id: str
    reconciliation_status: Literal["applied", "duplicate", "ignored", "failed"]
    checkout_id: UUID | None
    entitlement_id: UUID | None
    account_access_state: Literal["anonymous", "free", "pending", "premium"] | None
