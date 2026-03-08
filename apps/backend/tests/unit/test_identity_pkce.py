from __future__ import annotations

import re

from civitas.domain.identity.services import (
    derive_pkce_code_challenge,
    generate_pkce_code_verifier,
)

PKCE_VERIFIER_PATTERN = re.compile(r"^[A-Za-z0-9._~-]{43,128}$")


def test_generate_pkce_code_verifier_returns_rfc_7636_compatible_value() -> None:
    verifier = generate_pkce_code_verifier()

    assert PKCE_VERIFIER_PATTERN.match(verifier) is not None


def test_derive_pkce_code_challenge_returns_s256_urlsafe_value() -> None:
    challenge = derive_pkce_code_challenge("dBjftJeZ4CVP-mB92K27uhbUJU1p1r_wW1gFWFOEjXk")

    assert challenge == "E9Melhoa2OwvFrEMTJguCHaoeK1t8URWbuGJSstw-cM"
