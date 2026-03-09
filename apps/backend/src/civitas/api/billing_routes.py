from __future__ import annotations

from datetime import datetime, timezone
from urllib.parse import urlsplit
from uuid import UUID

from fastapi import APIRouter, Depends, HTTPException, Request

from civitas.api.dependencies import (
    get_billing_provider_gateway,
    get_checkout_status_use_case,
    get_create_billing_portal_session_use_case,
    get_create_checkout_session_use_case,
    get_list_available_premium_products_use_case,
    get_reconcile_payment_event_use_case,
    require_authenticated_session,
    require_valid_auth_origin,
)
from civitas.api.schemas.billing import (
    BillingPortalSessionCreateRequest,
    BillingPortalSessionCreateResponse,
    BillingProductResponse,
    BillingProductsResponse,
    BillingWebhookResponse,
    CheckoutSessionCreateRequest,
    CheckoutSessionCreateResponse,
    CheckoutSessionStatusResponse,
)
from civitas.application.access.use_cases import ListAvailablePremiumProductsUseCase
from civitas.application.billing.errors import (
    BillingCustomerNotFoundError,
    BillingProductNotConfiguredError,
    BillingProductNotFoundError,
    CheckoutSessionNotFoundError,
    PaymentEventVerificationError,
    PaymentProviderUnavailableError,
)
from civitas.application.billing.ports.billing_provider_gateway import BillingProviderGateway
from civitas.application.billing.use_cases import (
    CreateBillingPortalSessionUseCase,
    CreateCheckoutSessionUseCase,
    GetCheckoutStatusUseCase,
    ReconcilePaymentEventUseCase,
)
from civitas.application.identity.dto import SessionUserDto

router = APIRouter(prefix="/api/v1/billing", tags=["billing"])


@router.get(
    "/products",
    response_model=BillingProductsResponse,
)
def list_billing_products(
    use_case: ListAvailablePremiumProductsUseCase = Depends(
        get_list_available_premium_products_use_case
    ),
) -> BillingProductsResponse:
    products = use_case.execute()
    return BillingProductsResponse(
        products=[
            BillingProductResponse(
                code=product.code,
                display_name=product.display_name,
                description=product.description,
                billing_interval=product.billing_interval,
                duration_days=product.duration_days,
                capability_keys=list(product.capability_keys),
            )
            for product in products
        ]
    )


@router.post(
    "/checkout-sessions",
    response_model=CheckoutSessionCreateResponse,
)
def create_checkout_session(
    request: Request,
    payload: CheckoutSessionCreateRequest,
    _: None = Depends(require_valid_auth_origin),
    user: SessionUserDto = Depends(require_authenticated_session),
    use_case: CreateCheckoutSessionUseCase = Depends(get_create_checkout_session_use_case),
) -> CheckoutSessionCreateResponse:
    try:
        result = use_case.execute(
            user_id=user.id,
            user_email=user.email,
            product_code=payload.product_code,
            success_path=payload.success_path or "/",
            cancel_path=payload.cancel_path or "/",
            public_origin=_request_public_origin(request),
        )
    except BillingProductNotFoundError as exc:
        raise HTTPException(status_code=404, detail=str(exc)) from exc
    except BillingProductNotConfiguredError as exc:
        raise HTTPException(status_code=409, detail=str(exc)) from exc
    except PaymentProviderUnavailableError as exc:
        raise HTTPException(status_code=503, detail=str(exc)) from exc

    return CheckoutSessionCreateResponse(**result.__dict__)


@router.get(
    "/checkout-sessions/{checkout_id}",
    response_model=CheckoutSessionStatusResponse,
)
def get_checkout_status(
    checkout_id: UUID,
    user: SessionUserDto = Depends(require_authenticated_session),
    use_case: GetCheckoutStatusUseCase = Depends(get_checkout_status_use_case),
) -> CheckoutSessionStatusResponse:
    try:
        result = use_case.execute(user_id=user.id, checkout_id=checkout_id)
    except CheckoutSessionNotFoundError as exc:
        raise HTTPException(status_code=404, detail=str(exc)) from exc
    return CheckoutSessionStatusResponse(**result.__dict__)


@router.post(
    "/portal-sessions",
    response_model=BillingPortalSessionCreateResponse,
)
def create_billing_portal_session(
    request: Request,
    payload: BillingPortalSessionCreateRequest,
    _: None = Depends(require_valid_auth_origin),
    user: SessionUserDto = Depends(require_authenticated_session),
    use_case: CreateBillingPortalSessionUseCase = Depends(
        get_create_billing_portal_session_use_case
    ),
) -> BillingPortalSessionCreateResponse:
    try:
        result = use_case.execute(
            user_id=user.id,
            return_path=payload.return_path,
            public_origin=_request_public_origin(request),
        )
    except BillingCustomerNotFoundError as exc:
        raise HTTPException(status_code=404, detail=str(exc)) from exc
    except PaymentProviderUnavailableError as exc:
        raise HTTPException(status_code=503, detail=str(exc)) from exc
    return BillingPortalSessionCreateResponse(**result.__dict__)


@router.post(
    "/webhooks/stripe",
    response_model=BillingWebhookResponse,
)
async def stripe_webhook(
    request: Request,
    gateway: BillingProviderGateway = Depends(get_billing_provider_gateway),
    use_case: ReconcilePaymentEventUseCase = Depends(get_reconcile_payment_event_use_case),
) -> BillingWebhookResponse:
    payload = await request.body()
    try:
        provider_event = gateway.verify_and_parse_webhook_event(
            payload=payload,
            signature_header=request.headers.get("stripe-signature"),
            received_at=datetime.now(timezone.utc),
        )
        result = use_case.execute(provider_event=provider_event)
    except PaymentEventVerificationError as exc:
        raise HTTPException(status_code=400, detail=str(exc)) from exc
    except PaymentProviderUnavailableError as exc:
        raise HTTPException(status_code=503, detail=str(exc)) from exc
    return BillingWebhookResponse(**result.__dict__)


def _request_public_origin(request: Request) -> str:
    origin = request.headers.get("origin")
    if origin:
        split = urlsplit(origin)
        if split.scheme and split.netloc:
            return f"{split.scheme}://{split.netloc}"
    return f"{request.url.scheme}://{request.url.netloc}"
