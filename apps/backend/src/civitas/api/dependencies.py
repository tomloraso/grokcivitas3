from typing import Literal, cast

from fastapi import Depends, HTTPException, Request, Response

from civitas.api.request_origins import require_allowed_cookie_origin
from civitas.api.session_cookies import SessionCookieSettings, clear_session_cookie
from civitas.application.access.use_cases import (
    EvaluateAccessUseCase,
    GetCurrentAccountAccessUseCase,
    ListAvailablePremiumProductsUseCase,
)
from civitas.application.billing.ports.billing_provider_gateway import BillingProviderGateway
from civitas.application.billing.use_cases import (
    CreateBillingPortalSessionUseCase,
    CreateCheckoutSessionUseCase,
    GetCheckoutStatusUseCase,
    ReconcilePaymentEventUseCase,
)
from civitas.application.identity.dto import CurrentSessionDto, SessionUserDto
from civitas.application.identity.use_cases import (
    CompleteAuthCallbackUseCase,
    GetCurrentSessionUseCase,
    SignOutUseCase,
    StartSignInUseCase,
)
from civitas.application.school_compare.use_cases import GetSchoolCompareUseCase
from civitas.application.school_profiles.use_cases import GetSchoolProfileUseCase
from civitas.application.school_trends.use_cases import (
    GetSchoolTrendDashboardUseCase,
    GetSchoolTrendsUseCase,
)
from civitas.application.schools.use_cases import (
    SearchSchoolsByNameUseCase,
    SearchSchoolsByPostcodeUseCase,
)
from civitas.application.tasks.use_cases import CreateTaskUseCase, ListTasksUseCase
from civitas.bootstrap.container import (
    app_settings,
    complete_auth_callback_use_case,
    create_billing_portal_session_use_case,
    create_checkout_session_use_case,
    create_task_use_case,
    list_available_premium_products_use_case,
    list_tasks_use_case,
    reconcile_payment_event_use_case,
    search_schools_by_name_use_case,
    search_schools_by_postcode_use_case,
    sign_out_use_case,
    start_sign_in_use_case,
)
from civitas.bootstrap.container import (
    billing_provider_gateway as build_billing_provider_gateway,
)
from civitas.bootstrap.container import (
    evaluate_access_use_case as build_evaluate_access_use_case,
)
from civitas.bootstrap.container import (
    get_checkout_status_use_case as build_checkout_status_use_case,
)
from civitas.bootstrap.container import (
    get_current_account_access_use_case as build_current_account_access_use_case,
)
from civitas.bootstrap.container import (
    get_current_session_use_case as build_current_session_use_case,
)
from civitas.bootstrap.container import (
    get_school_compare_use_case as build_school_compare_use_case,
)
from civitas.bootstrap.container import (
    get_school_profile_use_case as build_school_profile_use_case,
)
from civitas.bootstrap.container import (
    get_school_trend_dashboard_use_case as build_school_trend_dashboard_use_case,
)
from civitas.bootstrap.container import (
    get_school_trends_use_case as build_school_trends_use_case,
)


def get_create_task_use_case() -> CreateTaskUseCase:
    return create_task_use_case()


def get_start_sign_in_use_case() -> StartSignInUseCase:
    return start_sign_in_use_case()


def get_complete_auth_callback_use_case() -> CompleteAuthCallbackUseCase:
    return complete_auth_callback_use_case()


def get_current_session_use_case() -> GetCurrentSessionUseCase:
    return build_current_session_use_case()


def get_current_account_access_use_case() -> GetCurrentAccountAccessUseCase:
    return build_current_account_access_use_case()


def get_evaluate_access_use_case() -> EvaluateAccessUseCase:
    return build_evaluate_access_use_case()


def get_sign_out_use_case() -> SignOutUseCase:
    return sign_out_use_case()


def get_list_available_premium_products_use_case() -> ListAvailablePremiumProductsUseCase:
    return list_available_premium_products_use_case()


def get_create_checkout_session_use_case() -> CreateCheckoutSessionUseCase:
    return create_checkout_session_use_case()


def get_checkout_status_use_case() -> GetCheckoutStatusUseCase:
    return build_checkout_status_use_case()


def get_create_billing_portal_session_use_case() -> CreateBillingPortalSessionUseCase:
    return create_billing_portal_session_use_case()


def get_reconcile_payment_event_use_case() -> ReconcilePaymentEventUseCase:
    return reconcile_payment_event_use_case()


def get_billing_provider_gateway() -> BillingProviderGateway:
    return build_billing_provider_gateway()


def get_session_cookie_settings() -> SessionCookieSettings:
    settings = app_settings().auth
    return SessionCookieSettings(
        name=settings.session_cookie_name,
        secure=settings.session_cookie_secure,
        samesite=cast(
            Literal["lax", "strict", "none"],
            settings.session_cookie_samesite,
        ),
    )


def get_auth_callback_error_path() -> str:
    return app_settings().auth.callback_error_path


def get_auth_allowed_origins() -> tuple[str, ...]:
    return app_settings().auth.allowed_origins


def require_valid_auth_origin(
    request: Request,
    cookie_settings: SessionCookieSettings = Depends(get_session_cookie_settings),
    allowed_origins: tuple[str, ...] = Depends(get_auth_allowed_origins),
) -> None:
    require_allowed_cookie_origin(
        request,
        cookie_name=cookie_settings.name,
        allowed_origins=allowed_origins,
    )


def require_authenticated_session(
    request: Request,
    response: Response,
    use_case: GetCurrentSessionUseCase = Depends(get_current_session_use_case),
    cookie_settings: SessionCookieSettings = Depends(get_session_cookie_settings),
) -> SessionUserDto:
    result = _resolve_current_session(
        request=request,
        response=response,
        use_case=use_case,
        cookie_settings=cookie_settings,
    )
    if result.state == "authenticated" and result.user is not None:
        return result.user
    raise HTTPException(status_code=401, detail="authentication required")


def get_optional_session_user(
    request: Request,
    response: Response,
    use_case: GetCurrentSessionUseCase = Depends(get_current_session_use_case),
    cookie_settings: SessionCookieSettings = Depends(get_session_cookie_settings),
) -> SessionUserDto | None:
    result = _resolve_current_session(
        request=request,
        response=response,
        use_case=use_case,
        cookie_settings=cookie_settings,
    )
    if result.state == "authenticated":
        return result.user
    return None


def get_list_tasks_use_case() -> ListTasksUseCase:
    return list_tasks_use_case()


def get_search_schools_by_postcode_use_case() -> SearchSchoolsByPostcodeUseCase:
    return search_schools_by_postcode_use_case()


def get_search_schools_by_name_use_case() -> SearchSchoolsByNameUseCase:
    return search_schools_by_name_use_case()


def get_school_profile_use_case() -> GetSchoolProfileUseCase:
    return build_school_profile_use_case()


def get_school_compare_use_case() -> GetSchoolCompareUseCase:
    return build_school_compare_use_case()


def get_school_trends_use_case() -> GetSchoolTrendsUseCase:
    return build_school_trends_use_case()


def get_school_trend_dashboard_use_case() -> GetSchoolTrendDashboardUseCase:
    return build_school_trend_dashboard_use_case()


def _resolve_current_session(
    *,
    request: Request,
    response: Response,
    use_case: GetCurrentSessionUseCase,
    cookie_settings: SessionCookieSettings,
) -> CurrentSessionDto:
    session_token = request.cookies.get(cookie_settings.name)
    result = use_case.execute(session_token=session_token)
    if session_token and result.anonymous_reason in {
        "invalid",
        "expired",
        "revoked",
    }:
        clear_session_cookie(response, settings=cookie_settings)
    return result
