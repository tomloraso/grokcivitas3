from functools import lru_cache

from civitas.application.operations.use_cases import (
    DataQualitySloConfig,
    EvaluateDataQualityAlertsUseCase,
    GenerateDataQualitySnapshotsUseCase,
    RunDataQualitySloCheckUseCase,
)
from civitas.application.school_compare.use_cases import GetSchoolCompareUseCase
from civitas.application.school_profiles.use_cases import GetSchoolProfileUseCase
from civitas.application.school_summaries.ports.summary_generator import SummaryGenerator
from civitas.application.school_summaries.use_cases import (
    GenerateSchoolAnalystSummariesUseCase,
    GenerateSchoolOverviewsUseCase,
    GetSchoolAnalystUseCase,
    GetSchoolOverviewUseCase,
    PollSchoolAnalystBatchesUseCase,
    PollSchoolOverviewBatchesUseCase,
    SubmitSchoolAnalystBatchesUseCase,
    SubmitSchoolOverviewBatchesUseCase,
)
from civitas.application.school_trends.use_cases import (
    GetSchoolTrendDashboardUseCase,
    GetSchoolTrendsUseCase,
)
from civitas.application.schools.use_cases import (
    SearchSchoolsByNameUseCase,
    SearchSchoolsByPostcodeUseCase,
)
from civitas.application.tasks.use_cases import CreateTaskUseCase, ListTasksUseCase
from civitas.infrastructure.ai.provider_factory import build_summary_generator
from civitas.infrastructure.config.settings import AppSettings, get_settings
from civitas.infrastructure.http.postcode_resolver import CachedPostcodeResolver
from civitas.infrastructure.http.postcodes_io_client import PostcodesIoClient
from civitas.infrastructure.persistence.cached_school_profile_repository import (
    CachedSchoolProfileRepository,
    PostgresSchoolProfileCacheVersionProvider,
)
from civitas.infrastructure.persistence.database import db_engine
from civitas.infrastructure.persistence.in_memory_task_repository import InMemoryTaskRepository
from civitas.infrastructure.persistence.postgres_data_quality_repository import (
    PostgresDataQualityRepository,
)
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
from civitas.infrastructure.persistence.postgres_summary_context_repository import (
    PostgresSummaryContextRepository,
)
from civitas.infrastructure.persistence.postgres_summary_repository import (
    PostgresSummaryRepository,
)
from civitas.infrastructure.pipelines import pipeline_registry
from civitas.infrastructure.pipelines.base import (
    PipelineQualityConfig,
    PipelineRetryPolicy,
    PipelineSource,
)
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
def school_profile_repository() -> CachedSchoolProfileRepository:
    settings = app_settings()
    engine = db_engine(settings.database.url)
    delegate = PostgresSchoolProfileRepository(engine=engine)
    version_provider = PostgresSchoolProfileCacheVersionProvider(
        engine=engine,
        poll_interval_seconds=settings.school_search.profile_cache_invalidation_poll_seconds,
    )
    return CachedSchoolProfileRepository(
        delegate=delegate,
        ttl_seconds=settings.school_search.profile_cache_ttl_seconds,
        version_provider=version_provider,
    )


@lru_cache(maxsize=1)
def school_trends_repository() -> PostgresSchoolTrendsRepository:
    settings = app_settings()
    return PostgresSchoolTrendsRepository(engine=db_engine(settings.database.url))


@lru_cache(maxsize=1)
def summary_repository() -> PostgresSummaryRepository:
    settings = app_settings()
    return PostgresSummaryRepository(engine=db_engine(settings.database.url))


@lru_cache(maxsize=1)
def summary_context_repository() -> PostgresSummaryContextRepository:
    settings = app_settings()
    return PostgresSummaryContextRepository(engine=db_engine(settings.database.url))


@lru_cache(maxsize=1)
def summary_generator() -> SummaryGenerator:
    settings = app_settings()
    return build_summary_generator(settings)


@lru_cache(maxsize=1)
def postcode_cache_repository() -> PostgresPostcodeCacheRepository:
    settings = app_settings()
    return PostgresPostcodeCacheRepository(engine=db_engine(settings.database.url))


@lru_cache(maxsize=1)
def data_quality_repository() -> PostgresDataQualityRepository:
    settings = app_settings()
    return PostgresDataQualityRepository(engine=db_engine(settings.database.url))


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
        school_trends_repository=school_trends_repository(),
        summary_repository=summary_repository(),
    )


def get_school_compare_use_case() -> GetSchoolCompareUseCase:
    return GetSchoolCompareUseCase(
        school_profile_repository=school_profile_repository(),
        school_trends_repository=school_trends_repository(),
    )


def get_school_trends_use_case() -> GetSchoolTrendsUseCase:
    return GetSchoolTrendsUseCase(
        school_trends_repository=school_trends_repository(),
    )


def get_school_trend_dashboard_use_case() -> GetSchoolTrendDashboardUseCase:
    return GetSchoolTrendDashboardUseCase(
        school_trends_repository=school_trends_repository(),
    )


def get_school_overview_use_case() -> GetSchoolOverviewUseCase:
    return GetSchoolOverviewUseCase(summary_repository=summary_repository())


def get_school_analyst_use_case() -> GetSchoolAnalystUseCase:
    return GetSchoolAnalystUseCase(summary_repository=summary_repository())


def generate_school_overviews_use_case() -> GenerateSchoolOverviewsUseCase:
    settings = app_settings()
    return GenerateSchoolOverviewsUseCase(
        context_repository=summary_context_repository(),
        summary_generator=summary_generator(),
        summary_repository=summary_repository(),
        batch_size=settings.ai.batch_size,
    )


def generate_school_analyst_summaries_use_case() -> GenerateSchoolAnalystSummariesUseCase:
    settings = app_settings()
    return GenerateSchoolAnalystSummariesUseCase(
        context_repository=summary_context_repository(),
        summary_generator=summary_generator(),
        summary_repository=summary_repository(),
        batch_size=settings.ai.batch_size,
    )


def submit_school_overview_batches_use_case() -> SubmitSchoolOverviewBatchesUseCase:
    settings = app_settings()
    return SubmitSchoolOverviewBatchesUseCase(
        context_repository=summary_context_repository(),
        summary_generator=summary_generator(),
        summary_repository=summary_repository(),
        batch_size=settings.ai.batch_size,
    )


def submit_school_analyst_batches_use_case() -> SubmitSchoolAnalystBatchesUseCase:
    settings = app_settings()
    return SubmitSchoolAnalystBatchesUseCase(
        context_repository=summary_context_repository(),
        summary_generator=summary_generator(),
        summary_repository=summary_repository(),
        batch_size=settings.ai.batch_size,
    )


def poll_school_overview_batches_use_case() -> PollSchoolOverviewBatchesUseCase:
    settings = app_settings()
    return PollSchoolOverviewBatchesUseCase(
        context_repository=summary_context_repository(),
        summary_generator=summary_generator(),
        summary_repository=summary_repository(),
        batch_size=settings.ai.batch_size,
    )


def poll_school_analyst_batches_use_case() -> PollSchoolAnalystBatchesUseCase:
    settings = app_settings()
    return PollSchoolAnalystBatchesUseCase(
        context_repository=summary_context_repository(),
        summary_generator=summary_generator(),
        summary_repository=summary_repository(),
        batch_size=settings.ai.batch_size,
    )


def data_quality_snapshot_use_case() -> GenerateDataQualitySnapshotsUseCase:
    return GenerateDataQualitySnapshotsUseCase(
        repository=data_quality_repository(),
    )


def data_quality_alerts_use_case() -> EvaluateDataQualityAlertsUseCase:
    settings = app_settings()
    return EvaluateDataQualityAlertsUseCase(
        repository=data_quality_repository(),
        slo_config=DataQualitySloConfig(
            source_freshness_sla_hours=settings.data_quality.source_freshness_sla_hours,
            max_day_over_day_coverage_drop=settings.data_quality.coverage_drift_threshold,
            max_consecutive_hard_failures=(settings.data_quality.max_consecutive_hard_failures),
            max_sparse_trend_ratio=settings.data_quality.sparse_trend_ratio_threshold,
        ),
    )


def data_quality_slo_check_use_case() -> RunDataQualitySloCheckUseCase:
    return RunDataQualitySloCheckUseCase(
        snapshot_use_case=data_quality_snapshot_use_case(),
        evaluate_use_case=data_quality_alerts_use_case(),
    )


@lru_cache(maxsize=1)
def pipeline_runner() -> PipelineRunner:
    settings = app_settings()
    engine = db_engine(settings.database.url)
    run_store = SqlPipelineRunStore(engine=engine)
    quality_config_by_source = {
        PipelineSource.GIAS: PipelineQualityConfig(
            max_reject_ratio=settings.pipeline.max_reject_ratio_gias
        ),
        PipelineSource.DFE_CHARACTERISTICS: PipelineQualityConfig(
            max_reject_ratio=settings.pipeline.max_reject_ratio_dfe_characteristics
        ),
        PipelineSource.DFE_ATTENDANCE: PipelineQualityConfig(
            max_reject_ratio=settings.pipeline.max_reject_ratio_dfe_attendance
        ),
        PipelineSource.DFE_BEHAVIOUR: PipelineQualityConfig(
            max_reject_ratio=settings.pipeline.max_reject_ratio_dfe_behaviour
        ),
        PipelineSource.DFE_WORKFORCE: PipelineQualityConfig(
            max_reject_ratio=settings.pipeline.max_reject_ratio_dfe_workforce
        ),
        PipelineSource.DFE_PERFORMANCE: PipelineQualityConfig(
            max_reject_ratio=settings.pipeline.max_reject_ratio_dfe_performance
        ),
        PipelineSource.OFSTED_LATEST: PipelineQualityConfig(
            max_reject_ratio=settings.pipeline.max_reject_ratio_ofsted_latest
        ),
        PipelineSource.OFSTED_TIMELINE: PipelineQualityConfig(
            max_reject_ratio=settings.pipeline.max_reject_ratio_ofsted_timeline
        ),
        PipelineSource.ONS_IMD: PipelineQualityConfig(
            max_reject_ratio=settings.pipeline.max_reject_ratio_ons_imd
        ),
        PipelineSource.UK_HOUSE_PRICES: PipelineQualityConfig(
            max_reject_ratio=settings.pipeline.max_reject_ratio_uk_house_prices
        ),
        PipelineSource.POLICE_CRIME_CONTEXT: PipelineQualityConfig(
            max_reject_ratio=settings.pipeline.max_reject_ratio_police_crime_context
        ),
    }
    return PipelineRunner(
        pipelines=pipeline_registry(engine=engine, pipeline_settings=settings.pipeline),
        run_store=run_store,
        bronze_root=settings.pipeline.bronze_root,
        quality_config_by_source=quality_config_by_source,
        retry_policy=PipelineRetryPolicy(
            max_retries=settings.pipeline.max_retries,
            backoff_seconds=settings.pipeline.retry_backoff_seconds,
        ),
        stage_chunk_size=settings.pipeline.stage_chunk_size,
        promote_chunk_size=settings.pipeline.promote_chunk_size,
        http_timeout_seconds=settings.pipeline.http_timeout_seconds,
        max_concurrent_sources=settings.pipeline.max_concurrent_sources,
        resume_enabled=settings.pipeline.resume_enabled,
    )
