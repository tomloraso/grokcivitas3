from sqlalchemy.engine import Engine

from civitas.infrastructure.config.settings import PipelineSettings

from .base import Pipeline, PipelineSource
from .demographics_release_files import DemographicsReleaseFilesPipeline
from .dfe_attendance import DfeAttendancePipeline
from .dfe_behaviour import DfeBehaviourPipeline
from .dfe_performance import DfePerformancePipeline
from .dfe_workforce import DfeWorkforcePipeline
from .gias import GiasPipeline
from .ofsted_latest import OfstedLatestPipeline
from .ofsted_timeline import OfstedTimelinePipeline
from .ons_imd import OnsImdPipeline
from .police_crime_context import PoliceCrimeContextPipeline
from .school_admissions import SchoolAdmissionsPipeline
from .school_financial_benchmarks import SchoolFinancialBenchmarksPipeline
from .uk_house_prices import UkHousePricesPipeline


def pipeline_registry(
    engine: Engine,
    pipeline_settings: PipelineSettings,
) -> dict[PipelineSource, Pipeline]:
    return {
        PipelineSource.GIAS: GiasPipeline(
            engine=engine,
            source_csv=pipeline_settings.gias_source_csv,
            source_zip=pipeline_settings.gias_source_zip,
        ),
        PipelineSource.DFE_CHARACTERISTICS: DemographicsReleaseFilesPipeline(
            engine=engine,
            spc_publication_slug=pipeline_settings.demographics_spc_publication_slug,
            sen_publication_slug=pipeline_settings.demographics_sen_publication_slug,
            release_slugs=pipeline_settings.demographics_release_slugs,
            lookback_years=pipeline_settings.demographics_lookback_years,
            strict_mode=pipeline_settings.demographics_source_strict_mode,
        ),
        PipelineSource.DFE_ATTENDANCE: DfeAttendancePipeline(
            engine=engine,
            publication_slug=pipeline_settings.dfe_attendance_publication_slug,
            release_slugs=pipeline_settings.dfe_attendance_release_slugs,
            lookback_years=pipeline_settings.dfe_attendance_lookback_years,
            strict_mode=pipeline_settings.dfe_attendance_source_strict_mode,
        ),
        PipelineSource.DFE_BEHAVIOUR: DfeBehaviourPipeline(
            engine=engine,
            publication_slug=pipeline_settings.dfe_behaviour_publication_slug,
            release_slugs=pipeline_settings.dfe_behaviour_release_slugs,
            lookback_years=pipeline_settings.dfe_behaviour_lookback_years,
            strict_mode=pipeline_settings.dfe_behaviour_source_strict_mode,
        ),
        PipelineSource.DFE_WORKFORCE: DfeWorkforcePipeline(
            engine=engine,
            publication_slug=pipeline_settings.dfe_workforce_publication_slug,
            release_slugs=pipeline_settings.dfe_workforce_release_slugs,
            lookback_years=pipeline_settings.dfe_workforce_lookback_years,
            strict_mode=pipeline_settings.dfe_workforce_source_strict_mode,
        ),
        PipelineSource.DFE_PERFORMANCE: DfePerformancePipeline(
            engine=engine,
            ks2_dataset_id=pipeline_settings.dfe_performance_ks2_dataset_id,
            ks4_dataset_id=pipeline_settings.dfe_performance_ks4_dataset_id,
            lookback_years=pipeline_settings.dfe_performance_lookback_years,
            page_size=pipeline_settings.dfe_performance_page_size,
        ),
        PipelineSource.SCHOOL_ADMISSIONS: SchoolAdmissionsPipeline(
            engine=engine,
            source_csv=pipeline_settings.school_admissions_source_csv,
            source_url=pipeline_settings.school_admissions_source_url,
        ),
        PipelineSource.SCHOOL_FINANCIAL_BENCHMARKS: SchoolFinancialBenchmarksPipeline(
            engine=engine,
            workbook_urls=pipeline_settings.school_financial_benchmarks_workbook_urls,
        ),
        PipelineSource.OFSTED_LATEST: OfstedLatestPipeline(
            engine=engine,
            source_csv=pipeline_settings.ofsted_latest_source_csv,
        ),
        PipelineSource.OFSTED_TIMELINE: OfstedTimelinePipeline(
            engine=engine,
            source_index_url=pipeline_settings.ofsted_timeline_source_index_url,
            source_assets_csv=pipeline_settings.ofsted_timeline_source_assets,
            timeline_years=pipeline_settings.ofsted_timeline_years,
            include_historical_baseline=(
                pipeline_settings.ofsted_timeline_include_historical_baseline
            ),
        ),
        PipelineSource.ONS_IMD: OnsImdPipeline(
            engine=engine,
            source_csv=pipeline_settings.imd_source_csv,
            source_release=pipeline_settings.imd_release,
        ),
        PipelineSource.UK_HOUSE_PRICES: UkHousePricesPipeline(
            engine=engine,
            source_csv=pipeline_settings.house_prices_source_csv,
            source_url=pipeline_settings.house_prices_source_url,
        ),
        PipelineSource.POLICE_CRIME_CONTEXT: PoliceCrimeContextPipeline(
            engine=engine,
            source_archive_url=pipeline_settings.police_crime_source_archive_url,
            source_mode=pipeline_settings.police_crime_source_mode,
            crime_radius_meters=pipeline_settings.police_crime_radius_meters,
        ),
    }
