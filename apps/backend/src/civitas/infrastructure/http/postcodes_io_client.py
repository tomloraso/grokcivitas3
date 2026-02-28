from __future__ import annotations

import json
import time
import urllib.error
import urllib.parse
import urllib.request
from collections.abc import Mapping
from typing import Any

from civitas.application.schools.errors import (
    PostcodeNotFoundError,
    PostcodeResolverUnavailableError,
)
from civitas.domain.schools.models import PostcodeCoordinates

RETRY_STATUS_CODES = {429, 500, 502, 503, 504}


class PostcodesIoClient:
    def __init__(
        self,
        *,
        base_url: str,
        timeout_seconds: float,
        max_retries: int,
        retry_backoff_seconds: float,
    ) -> None:
        self._base_url = base_url.rstrip("/")
        self._timeout_seconds = timeout_seconds
        self._max_retries = max_retries
        self._retry_backoff_seconds = retry_backoff_seconds

    def lookup(self, postcode: str) -> PostcodeCoordinates:
        url = f"{self._base_url}/postcodes/{urllib.parse.quote(postcode)}"
        last_error: Exception | None = None
        for attempt in range(self._max_retries + 1):
            try:
                payload = self._fetch_json(url)
                return _parse_lookup_payload(postcode=postcode, payload=payload)
            except PostcodeNotFoundError:
                raise
            except urllib.error.HTTPError as exc:
                last_error = exc
                if exc.code == 404:
                    raise PostcodeNotFoundError(postcode) from exc
                if exc.code in RETRY_STATUS_CODES and attempt < self._max_retries:
                    _sleep_with_backoff(self._retry_backoff_seconds, attempt)
                    continue
                break
            except (urllib.error.URLError, TimeoutError, json.JSONDecodeError) as exc:
                last_error = exc
                if attempt < self._max_retries:
                    _sleep_with_backoff(self._retry_backoff_seconds, attempt)
                    continue
                break

        raise PostcodeResolverUnavailableError("Postcode resolver is unavailable.") from last_error

    def _fetch_json(self, url: str) -> Mapping[str, Any]:
        request = urllib.request.Request(
            url,
            headers={
                "Accept": "application/json",
                "User-Agent": "civitas-api/0.1",
            },
        )
        with urllib.request.urlopen(request, timeout=self._timeout_seconds) as response:
            body = response.read().decode("utf-8")
        payload = json.loads(body)
        if not isinstance(payload, Mapping):
            raise PostcodeResolverUnavailableError("Postcode resolver returned an invalid payload.")
        return payload


def _parse_lookup_payload(*, postcode: str, payload: Mapping[str, Any]) -> PostcodeCoordinates:
    result = payload.get("result")
    if result is None:
        status = payload.get("status")
        if status == 404:
            raise PostcodeNotFoundError(postcode)
        raise PostcodeResolverUnavailableError("Postcode resolver returned an invalid payload.")
    if not isinstance(result, Mapping):
        raise PostcodeResolverUnavailableError("Postcode resolver returned an invalid payload.")

    latitude = result.get("latitude")
    longitude = result.get("longitude")
    if latitude is None or longitude is None:
        raise PostcodeResolverUnavailableError("Postcode resolver returned incomplete coordinates.")

    try:
        lat = float(latitude)
        lng = float(longitude)
    except (TypeError, ValueError) as exc:
        raise PostcodeResolverUnavailableError(
            "Postcode resolver returned invalid coordinates."
        ) from exc

    resolved_postcode = result.get("postcode")
    canonical_postcode = resolved_postcode if isinstance(resolved_postcode, str) else postcode

    lsoa = result.get("lsoa")
    admin_district = result.get("admin_district")

    return PostcodeCoordinates(
        postcode=canonical_postcode,
        lat=lat,
        lng=lng,
        lsoa=lsoa if isinstance(lsoa, str) else None,
        admin_district=admin_district if isinstance(admin_district, str) else None,
    )


def _sleep_with_backoff(base_seconds: float, attempt: int) -> None:
    time.sleep(base_seconds * (2**attempt))
