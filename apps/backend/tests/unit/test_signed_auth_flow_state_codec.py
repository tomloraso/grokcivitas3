from __future__ import annotations

from datetime import datetime, timedelta, timezone

import pytest

from civitas.application.identity.errors import InvalidAuthCallbackError
from civitas.infrastructure.auth.signed_auth_flow_state_codec import SignedAuthFlowStateCodec


def test_signed_auth_flow_state_codec_round_trips_attempt_id() -> None:
    fixed_now = datetime(2026, 3, 8, 12, 0, tzinfo=timezone.utc)
    codec = SignedAuthFlowStateCodec(
        shared_secret="local-secret",
        ttl=timedelta(minutes=15),
        clock=lambda: fixed_now,
    )

    state = codec.issue(attempt_id="attempt-1")
    decoded = codec.read(state=state)

    assert decoded.attempt_id == "attempt-1"


def test_signed_auth_flow_state_codec_rejects_tampered_state() -> None:
    fixed_now = datetime(2026, 3, 8, 12, 0, tzinfo=timezone.utc)
    codec = SignedAuthFlowStateCodec(
        shared_secret="local-secret",
        ttl=timedelta(minutes=15),
        clock=lambda: fixed_now,
    )
    state = codec.issue(attempt_id="attempt-1")

    with pytest.raises(InvalidAuthCallbackError, match="invalid auth state"):
        codec.read(state=f"{state}tampered")


def test_signed_auth_flow_state_codec_rejects_expired_state() -> None:
    issued_at = datetime(2026, 3, 8, 12, 0, tzinfo=timezone.utc)
    issuing_codec = SignedAuthFlowStateCodec(
        shared_secret="local-secret",
        ttl=timedelta(minutes=15),
        clock=lambda: issued_at,
    )
    verifying_codec = SignedAuthFlowStateCodec(
        shared_secret="local-secret",
        ttl=timedelta(minutes=15),
        clock=lambda: issued_at + timedelta(minutes=16),
    )
    state = issuing_codec.issue(attempt_id="attempt-1")

    with pytest.raises(InvalidAuthCallbackError, match="invalid auth state"):
        verifying_codec.read(state=state)
