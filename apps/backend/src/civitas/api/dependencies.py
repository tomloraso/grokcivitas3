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
    create_task_use_case,
    list_tasks_use_case,
    search_schools_by_name_use_case,
    search_schools_by_postcode_use_case,
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


def get_list_tasks_use_case() -> ListTasksUseCase:
    return list_tasks_use_case()


def get_search_schools_by_postcode_use_case() -> SearchSchoolsByPostcodeUseCase:
    return search_schools_by_postcode_use_case()


def get_search_schools_by_name_use_case() -> SearchSchoolsByNameUseCase:
    return search_schools_by_name_use_case()


def get_school_profile_use_case() -> GetSchoolProfileUseCase:
    return build_school_profile_use_case()


def get_school_trends_use_case() -> GetSchoolTrendsUseCase:
    return build_school_trends_use_case()


def get_school_trend_dashboard_use_case() -> GetSchoolTrendDashboardUseCase:
    return build_school_trend_dashboard_use_case()
