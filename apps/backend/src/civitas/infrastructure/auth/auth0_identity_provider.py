from __future__ import annotations

from collections.abc import Mapping
from urllib.parse import urlencode

import httpx

from civitas.application.identity.dto import IdentityProviderUserDto
from civitas.application.identity.errors import (
    IdentityProviderUnavailableError,
    InvalidAuthCallbackError,
)
from civitas.application.identity.ports.identity_provider import IdentityProvider
from civitas.domain.identity.services import normalize_email


class Auth0IdentityProvider(IdentityProvider):
    def __init__(
        self,
        *,
        domain: str,
        client_id: str,
        client_secret: str,
        audience: str | None = None,
        connection: str | None = None,
        timeout_seconds: float = 10.0,
        http_client: httpx.Client | None = None,
    ) -> None:
        self._issuer = f"https://{domain}"
        self._authorize_url = f"{self._issuer}/authorize"
        self._token_url = f"{self._issuer}/oauth/token"
        self._userinfo_url = f"{self._issuer}/userinfo"
        self._client_id = client_id
        self._client_secret = client_secret
        self._audience = audience
        self._connection = connection
        self._http_client = http_client or httpx.Client(
            timeout=timeout_seconds,
            follow_redirects=False,
        )

    def start_sign_in(
        self,
        *,
        email: str,
        state: str,
        callback_url: str,
        code_challenge: str | None = None,
        code_challenge_method: str | None = None,
    ) -> str:
        query = {
            "client_id": self._client_id,
            "login_hint": email,
            "redirect_uri": callback_url,
            "response_type": "code",
            "scope": "openid profile email",
            "state": state,
        }
        if code_challenge is not None:
            query["code_challenge"] = code_challenge
        if code_challenge_method is not None:
            query["code_challenge_method"] = code_challenge_method
        if self._audience is not None:
            query["audience"] = self._audience
        if self._connection is not None:
            query["connection"] = self._connection
        return f"{self._authorize_url}?{urlencode(query)}"

    def complete_sign_in(
        self,
        *,
        callback_params: Mapping[str, str],
        callback_url: str,
        code_verifier: str | None = None,
    ) -> IdentityProviderUserDto:
        if callback_params.get("error", "").strip():
            raise InvalidAuthCallbackError("provider callback could not be verified")

        code = callback_params.get("code", "").strip()
        if not code or code_verifier is None or not code_verifier.strip():
            raise InvalidAuthCallbackError("provider callback could not be verified")

        access_token = self._exchange_code_for_access_token(
            code=code,
            callback_url=callback_url,
            code_verifier=code_verifier.strip(),
        )
        return self._load_userinfo(access_token=access_token)

    def _exchange_code_for_access_token(
        self,
        *,
        code: str,
        callback_url: str,
        code_verifier: str,
    ) -> str:
        payload = self._post_form(
            self._token_url,
            data={
                "client_id": self._client_id,
                "client_secret": self._client_secret,
                "code": code,
                "code_verifier": code_verifier,
                "grant_type": "authorization_code",
                "redirect_uri": callback_url,
            },
        )

        access_token = payload.get("access_token")
        token_type = payload.get("token_type")
        if not isinstance(access_token, str) or not access_token.strip():
            raise InvalidAuthCallbackError("provider callback could not be verified")
        if isinstance(token_type, str) and token_type.casefold() != "bearer":
            raise InvalidAuthCallbackError("provider callback could not be verified")

        return access_token.strip()

    def _load_userinfo(self, *, access_token: str) -> IdentityProviderUserDto:
        payload = self._get_json(
            self._userinfo_url,
            headers={
                "Authorization": f"Bearer {access_token}",
            },
        )

        provider_subject = payload.get("sub")
        email = payload.get("email")
        if not isinstance(provider_subject, str) or not provider_subject.strip():
            raise InvalidAuthCallbackError("provider callback could not be verified")
        if not isinstance(email, str) or not email.strip():
            raise InvalidAuthCallbackError("identity provider did not return an email address")

        try:
            normalized_email = normalize_email(email)
        except ValueError as exc:
            raise InvalidAuthCallbackError(
                "identity provider returned an invalid email address"
            ) from exc

        return IdentityProviderUserDto(
            provider_name="auth0",
            provider_subject=provider_subject.strip(),
            email=normalized_email,
            email_verified=payload.get("email_verified") is True,
        )

    def _post_form(self, url: str, *, data: Mapping[str, str]) -> dict[str, object]:
        try:
            response = self._http_client.post(
                url,
                data=data,
                headers={"Accept": "application/json"},
            )
        except httpx.HTTPError as exc:
            raise IdentityProviderUnavailableError("Auth0 is unavailable.") from exc
        return self._read_json_response(response=response)

    def _get_json(
        self,
        url: str,
        *,
        headers: Mapping[str, str] | None = None,
    ) -> dict[str, object]:
        try:
            response = self._http_client.get(
                url,
                headers={"Accept": "application/json", **(headers or {})},
            )
        except httpx.HTTPError as exc:
            raise IdentityProviderUnavailableError("Auth0 is unavailable.") from exc
        return self._read_json_response(response=response)

    def _read_json_response(self, *, response: httpx.Response) -> dict[str, object]:
        if response.status_code >= 500:
            raise IdentityProviderUnavailableError("Auth0 is unavailable.")
        if response.status_code != 200:
            raise InvalidAuthCallbackError("provider callback could not be verified")

        try:
            payload = response.json()
        except ValueError as exc:
            raise InvalidAuthCallbackError("provider callback could not be verified") from exc
        if not isinstance(payload, dict):
            raise InvalidAuthCallbackError("provider callback could not be verified")
        return payload
