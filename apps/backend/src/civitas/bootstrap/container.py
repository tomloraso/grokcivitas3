from functools import lru_cache

from civitas.application.school_profiles.use_cases import GetSchoolProfileUseCase
from civitas.application.school_trends.use_cases import GetSchoolTrendsUseCase
from civitas.application.schools.use_cases import (
    SearchSchoolsByNameUseCase,
    SearchSchoolsByPostcodeUseCase,
)
from civitas.application.tasks.use_cases import CreateTaskUseCase, ListTasksUseCase
from civitas.infrastructure.config.settings import AppSettings, get_settings
from civitas.infrastructure.http.postcode_resolver import CachedPostcodeResolver
from civitas.infrastructure.http.postcodes_io_client import PostcodesIoClient
from civitas.infrastructure.persistence.database import db_engine
from civitas.infrastructure.persistence.in_memory_task_repository import InMemoryTaskRepository
from civitas.infrastructure.persistence.postgres_postcode_cache_repository import (
    PostgresPostcodeCacheRepository,
)
from civitas.infrastructure.persistence.postgres_school_profile_repository import (
    PostgresSchoolProfileRepository,
)
from civitas.infrastructure.persistence.postgres_school_search_repository import (
    PostgresSchoolSearchRepository,
)
from civitas.infrastructure.persistence.postgres_school_trends_repository import (
    PostgresSchoolTrendsRepository,
)
from civitas.infrastructure.pipelines import pipeline_registry
from civitas.infrastructure.pipelines.runner import PipelineRunner, SqlPipelineRunStore


@lru_cache(maxsize=1)
def task_repository() -> InMemoryTaskRepository:
    return InMemoryTaskRepository()


def create_task_use_case() -> CreateTaskUseCase:
    return CreateTaskUseCase(repo=task_repository())


def list_tasks_use_case() -> ListTasksUseCase:
    return ListTasksUseCase(repo=task_repository())


@lru_cache(maxsize=1)
def app_settings() -> AppSettings:
    return get_settings()


@lru_cache(maxsize=1)
def school_search_repository() -> PostgresSchoolSearchRepository:
    settings = app_settings()
    return PostgresSchoolSearchRepository(engine=db_engine(settings.database.url))


@lru_cache(maxsize=1)
def school_profile_repository() -> PostgresSchoolProfileRepository:
    settings = app_settings()
    return PostgresSchoolProfileRepository(engine=db_engine(settings.database.url))


@lru_cache(maxsize=1)
def school_trends_repository() -> PostgresSchoolTrendsRepository:
    settings = app_settings()
    return PostgresSchoolTrendsRepository(engine=db_engine(settings.database.url))


@lru_cache(maxsize=1)
def postcode_cache_repository() -> PostgresPostcodeCacheRepository:
    settings = app_settings()
    return PostgresPostcodeCacheRepository(engine=db_engine(settings.database.url))


@lru_cache(maxsize=1)
def postcodes_io_client() -> PostcodesIoClient:
    settings = app_settings()
    return PostcodesIoClient(
        base_url=settings.school_search.postcodes_io_base_url,
        timeout_seconds=settings.http_clients.timeout_seconds,
        max_retries=settings.http_clients.max_retries,
        retry_backoff_seconds=settings.http_clients.retry_backoff_seconds,
    )


@lru_cache(maxsize=1)
def postcode_resolver() -> CachedPostcodeResolver:
    settings = app_settings()
    return CachedPostcodeResolver(
        cache_repository=postcode_cache_repository(),
        postcodes_io_client=postcodes_io_client(),
        cache_ttl_days=settings.school_search.postcode_cache_ttl_days,
    )


def search_schools_by_postcode_use_case() -> SearchSchoolsByPostcodeUseCase:
    return SearchSchoolsByPostcodeUseCase(
        school_search_repository=school_search_repository(),
        postcode_resolver=postcode_resolver(),
    )


def search_schools_by_name_use_case() -> SearchSchoolsByNameUseCase:
    return SearchSchoolsByNameUseCase(
        school_search_repository=school_search_repository(),
    )


def get_school_profile_use_case() -> GetSchoolProfileUseCase:
    return GetSchoolProfileUseCase(
        school_profile_repository=school_profile_repository(),
        postcode_context_resolver=postcode_resolver(),
    )


def get_school_trends_use_case() -> GetSchoolTrendsUseCase:
    return GetSchoolTrendsUseCase(
        school_trends_repository=school_trends_repository(),
    )


@lru_cache(maxsize=1)
def pipeline_runner() -> PipelineRunner:
    settings = app_settings()
    engine = db_engine(settings.database.url)
    run_store = SqlPipelineRunStore(engine=engine)
    return PipelineRunner(
        pipelines=pipeline_registry(engine=engine, pipeline_settings=settings.pipeline),
        run_store=run_store,
        bronze_root=settings.pipeline.bronze_root,
    )
