from __future__ import annotations

import base64
import hashlib
import re
import secrets

EMAIL_PATTERN = re.compile(r"^[^@\s]+@[^@\s]+\.[^@\s]+$")


def normalize_email(email: str) -> str:
    normalized = email.strip().casefold()
    if not EMAIL_PATTERN.match(normalized):
        raise ValueError("email must be a valid email address")
    return normalized


def normalize_provider_name(provider_name: str) -> str:
    normalized = provider_name.strip().casefold()
    if not normalized:
        raise ValueError("provider_name must not be empty")
    return normalized


def normalize_provider_subject(provider_subject: str) -> str:
    normalized = provider_subject.strip()
    if not normalized:
        raise ValueError("provider_subject must not be empty")
    return normalized


def generate_pkce_code_verifier() -> str:
    verifier = secrets.token_urlsafe(64)
    if not 43 <= len(verifier) <= 128:
        raise ValueError("generated PKCE code verifier must be between 43 and 128 characters")
    return verifier


def derive_pkce_code_challenge(code_verifier: str) -> str:
    verifier = code_verifier.strip()
    if not verifier:
        raise ValueError("code_verifier must not be empty")

    digest = hashlib.sha256(verifier.encode("ascii")).digest()
    return base64.urlsafe_b64encode(digest).decode("ascii").rstrip("=")
