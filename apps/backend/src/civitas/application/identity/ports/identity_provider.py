from __future__ import annotations

from collections.abc import Mapping
from typing import Protocol

from civitas.application.identity.dto import IdentityProviderUserDto


class IdentityProvider(Protocol):
    def start_sign_in(
        self,
        *,
        email: str,
        state: str,
        callback_url: str,
        code_challenge: str | None = None,
        code_challenge_method: str | None = None,
    ) -> str: ...

    def complete_sign_in(
        self,
        *,
        callback_params: Mapping[str, str],
        callback_url: str,
        code_verifier: str | None = None,
    ) -> IdentityProviderUserDto: ...
