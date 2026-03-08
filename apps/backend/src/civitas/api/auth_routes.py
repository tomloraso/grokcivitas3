from __future__ import annotations

from urllib.parse import urlencode

from fastapi import APIRouter, Depends, HTTPException, Request, Response
from fastapi.responses import RedirectResponse

from civitas.api.dependencies import (
    get_auth_callback_error_path,
    get_complete_auth_callback_use_case,
    get_current_session_use_case,
    get_session_cookie_settings,
    get_sign_out_use_case,
    get_start_sign_in_use_case,
    require_valid_auth_origin,
)
from civitas.api.schemas.auth import (
    AuthStartRequest,
    AuthStartResponse,
    SessionResponse,
    SessionUserResponse,
)
from civitas.api.session_cookies import (
    SessionCookieSettings,
    clear_session_cookie,
    set_session_cookie,
)
from civitas.application.identity.dto import CurrentSessionDto
from civitas.application.identity.errors import (
    IdentityProviderUnavailableError,
    InvalidAuthCallbackError,
    InvalidSignInEmailError,
)
from civitas.application.identity.use_cases import (
    CompleteAuthCallbackUseCase,
    GetCurrentSessionUseCase,
    SignOutUseCase,
    StartSignInUseCase,
)

router = APIRouter(prefix="/api/v1", tags=["auth"])


@router.post(
    "/auth/start",
    response_model=AuthStartResponse,
)
def start_sign_in(
    request: Request,
    payload: AuthStartRequest,
    use_case: StartSignInUseCase = Depends(get_start_sign_in_use_case),
) -> AuthStartResponse:
    callback_url = _current_auth_callback_url(request)
    try:
        result = use_case.execute(
            email=payload.email,
            return_to=payload.return_to,
            callback_url=callback_url,
        )
    except InvalidSignInEmailError as exc:
        raise HTTPException(status_code=400, detail=str(exc)) from exc
    except IdentityProviderUnavailableError as exc:
        raise HTTPException(status_code=503, detail=str(exc)) from exc

    return AuthStartResponse(redirect_url=result.redirect_url)


@router.get(
    "/auth/callback",
    name="auth_callback",
)
def auth_callback(
    request: Request,
    use_case: CompleteAuthCallbackUseCase = Depends(get_complete_auth_callback_use_case),
    callback_error_path: str = Depends(get_auth_callback_error_path),
    cookie_settings: SessionCookieSettings = Depends(get_session_cookie_settings),
) -> RedirectResponse:
    callback_url = _current_auth_callback_url(request)
    callback_params = {key: value for key, value in request.query_params.items()}

    try:
        result = use_case.execute(
            callback_params=callback_params,
            callback_url=callback_url,
        )
    except InvalidAuthCallbackError as exc:
        location = _callback_error_location(
            callback_error_path=callback_error_path,
            error_code=_callback_error_code(exc),
        )
        return RedirectResponse(url=location, status_code=303)
    except IdentityProviderUnavailableError:
        location = _callback_error_location(
            callback_error_path=callback_error_path,
            error_code="callback_failed",
        )
        return RedirectResponse(url=location, status_code=303)

    response = RedirectResponse(url=result.return_to, status_code=303)
    set_session_cookie(
        response,
        settings=cookie_settings,
        session_token=result.session_token,
        expires_at=result.expires_at,
    )
    return response


@router.get(
    "/session",
    response_model=SessionResponse,
)
def get_session(
    request: Request,
    response: Response,
    use_case: GetCurrentSessionUseCase = Depends(get_current_session_use_case),
    cookie_settings: SessionCookieSettings = Depends(get_session_cookie_settings),
) -> SessionResponse:
    session_token = request.cookies.get(cookie_settings.name)
    result = use_case.execute(session_token=session_token)
    if (
        session_token
        and result.state == "anonymous"
        and result.anonymous_reason
        in {
            "invalid",
            "expired",
            "revoked",
        }
    ):
        clear_session_cookie(response, settings=cookie_settings)
    return _to_session_response(result)


@router.post(
    "/auth/signout",
    response_model=SessionResponse,
)
def sign_out(
    request: Request,
    response: Response,
    _: None = Depends(require_valid_auth_origin),
    use_case: SignOutUseCase = Depends(get_sign_out_use_case),
    cookie_settings: SessionCookieSettings = Depends(get_session_cookie_settings),
) -> SessionResponse:
    session_token = request.cookies.get(cookie_settings.name)
    result = use_case.execute(session_token=session_token)
    clear_session_cookie(response, settings=cookie_settings)
    return _to_session_response(result)


def _to_session_response(result: CurrentSessionDto) -> SessionResponse:
    user = None
    if result.user is not None:
        user = SessionUserResponse(
            id=result.user.id,
            email=result.user.email,
        )
    return SessionResponse(
        state=result.state,
        user=user,
        expires_at=result.expires_at,
        anonymous_reason=result.anonymous_reason,
    )


def _callback_error_code(error: InvalidAuthCallbackError) -> str:
    if "state" in str(error).casefold():
        return "invalid_state"
    if "verified" in str(error).casefold():
        return "unverified_email"
    return "callback_failed"


def _callback_error_location(*, callback_error_path: str, error_code: str) -> str:
    params = urlencode({"error": error_code})
    return f"{callback_error_path}?{params}"


def _current_auth_callback_url(request: Request) -> str:
    return str(request.url_for("auth_callback"))
