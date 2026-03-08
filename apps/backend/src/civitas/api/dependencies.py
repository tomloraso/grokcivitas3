from typing import Literal, cast

from fastapi import Depends, Request

from civitas.api.request_origins import require_allowed_cookie_origin
from civitas.api.session_cookies import SessionCookieSettings
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
    create_task_use_case,
    list_tasks_use_case,
    search_schools_by_name_use_case,
    search_schools_by_postcode_use_case,
    sign_out_use_case,
    start_sign_in_use_case,
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


def get_sign_out_use_case() -> SignOutUseCase:
    return sign_out_use_case()


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
