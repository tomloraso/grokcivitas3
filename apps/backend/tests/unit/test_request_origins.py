from __future__ import annotations

from collections.abc import Iterable

import pytest
from fastapi import HTTPException
from starlette.requests import Request

from civitas.api.request_origins import require_allowed_cookie_origin


def test_require_allowed_cookie_origin_skips_requests_without_cookie() -> None:
    request = _build_request(headers=[])

    require_allowed_cookie_origin(
        request,
        cookie_name="civitas_session",
        allowed_origins=("http://localhost:5173",),
    )


def test_require_allowed_cookie_origin_accepts_exact_allowed_origin() -> None:
    request = _build_request(
        headers=[
            ("cookie", "civitas_session=session-token"),
            ("origin", "http://localhost:5173"),
        ]
    )

    require_allowed_cookie_origin(
        request,
        cookie_name="civitas_session",
        allowed_origins=("http://localhost:5173",),
    )


def test_require_allowed_cookie_origin_rejects_untrusted_origin() -> None:
    request = _build_request(
        headers=[
            ("cookie", "civitas_session=session-token"),
            ("origin", "https://malicious.example.test"),
        ]
    )

    with pytest.raises(HTTPException, match="origin not allowed") as exc_info:
        require_allowed_cookie_origin(
            request,
            cookie_name="civitas_session",
            allowed_origins=("http://localhost:5173",),
        )

    assert exc_info.value.status_code == 403


def test_require_allowed_cookie_origin_rejects_missing_origin_when_cookie_present() -> None:
    request = _build_request(headers=[("cookie", "civitas_session=session-token")])

    with pytest.raises(HTTPException, match="origin not allowed") as exc_info:
        require_allowed_cookie_origin(
            request,
            cookie_name="civitas_session",
            allowed_origins=("http://localhost:5173",),
        )

    assert exc_info.value.status_code == 403


def _build_request(headers: Iterable[tuple[str, str]]) -> Request:
    return Request(
        {
            "type": "http",
            "method": "POST",
            "path": "/api/v1/auth/signout",
            "root_path": "",
            "scheme": "http",
            "query_string": b"",
            "headers": [
                (name.encode("latin-1"), value.encode("latin-1")) for name, value in headers
            ],
            "client": ("testclient", 50000),
            "server": ("testserver", 80),
            "http_version": "1.1",
        }
    )
