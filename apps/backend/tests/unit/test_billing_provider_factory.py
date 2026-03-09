from __future__ import annotations

import pytest

from civitas.infrastructure.config.settings import AppSettings
from civitas.infrastructure.payments.provider_factory import (
    DisabledBillingProviderGateway,
    build_billing_provider_gateway,
)
from civitas.infrastructure.payments.stripe_billing_provider_gateway import (
    StripeBillingProviderGateway,
)


def test_build_billing_provider_gateway_returns_disabled_gateway_by_default(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    monkeypatch.delenv("CIVITAS_BILLING_ENABLED", raising=False)
    settings = AppSettings(_env_file=None)

    assert isinstance(build_billing_provider_gateway(settings), DisabledBillingProviderGateway)


def test_build_billing_provider_gateway_returns_stripe_gateway_when_enabled(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    monkeypatch.setenv("CIVITAS_BILLING_ENABLED", "true")
    monkeypatch.setenv("CIVITAS_BILLING_STRIPE_SECRET_KEY", "sk_test_123")
    monkeypatch.setenv("CIVITAS_BILLING_STRIPE_WEBHOOK_SECRET", "whsec_test_123")
    settings = AppSettings(_env_file=None)

    assert isinstance(build_billing_provider_gateway(settings), StripeBillingProviderGateway)
