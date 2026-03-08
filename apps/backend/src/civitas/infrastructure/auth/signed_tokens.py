from __future__ import annotations

import base64
import hashlib
import hmac
import json
from collections.abc import Mapping
from datetime import datetime, timedelta, timezone


def _utc_now() -> datetime:
    return datetime.now(timezone.utc)


class SignedTokenCodec:
    def __init__(self, *, secret: str, ttl: timedelta, purpose: str) -> None:
        self._secret = secret.encode("utf-8")
        self._ttl = ttl
        self._purpose = purpose

    def issue(self, *, payload: Mapping[str, object], now: datetime | None = None) -> str:
        reference_time = now or _utc_now()
        envelope = {
            "purpose": self._purpose,
            "exp": int((reference_time + self._ttl).timestamp()),
            "payload": dict(payload),
        }
        payload_bytes = json.dumps(
            envelope,
            separators=(",", ":"),
            sort_keys=True,
        ).encode("utf-8")
        encoded_payload = _encode(payload_bytes)
        signature = hmac.new(self._secret, encoded_payload.encode("utf-8"), hashlib.sha256).digest()
        return f"{encoded_payload}.{_encode(signature)}"

    def read(self, *, token: str, now: datetime | None = None) -> dict[str, object]:
        try:
            encoded_payload, encoded_signature = token.split(".", maxsplit=1)
        except ValueError as exc:
            raise ValueError("invalid signed token format") from exc

        expected_signature = hmac.new(
            self._secret,
            encoded_payload.encode("utf-8"),
            hashlib.sha256,
        ).digest()
        actual_signature = _decode(encoded_signature)
        if not hmac.compare_digest(expected_signature, actual_signature):
            raise ValueError("invalid signed token signature")

        payload_bytes = _decode(encoded_payload)
        envelope = json.loads(payload_bytes.decode("utf-8"))
        if envelope.get("purpose") != self._purpose:
            raise ValueError("invalid signed token purpose")

        reference_time = now or _utc_now()
        expires_at = int(envelope.get("exp", 0))
        if expires_at <= int(reference_time.timestamp()):
            raise ValueError("signed token has expired")

        payload = envelope.get("payload")
        if not isinstance(payload, dict):
            raise ValueError("signed token payload is invalid")
        return payload


def _encode(value: bytes) -> str:
    return base64.urlsafe_b64encode(value).decode("utf-8").rstrip("=")


def _decode(value: str) -> bytes:
    padding = "=" * ((4 - len(value) % 4) % 4)
    return base64.urlsafe_b64decode(value + padding)
