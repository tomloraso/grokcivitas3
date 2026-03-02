from sqlalchemy.engine import Engine

from civitas.infrastructure.config.settings import PipelineSettings

from .base import Pipeline, PipelineSource
from .dfe_characteristics import DfeCharacteristicsPipeline
from .gias import GiasPipeline
from .ofsted_latest import OfstedLatestPipeline
from .ofsted_timeline import OfstedTimelinePipeline
from .ons_imd import OnsImdPipeline
from .police_crime_context import PoliceCrimeContextPipeline


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
        PipelineSource.DFE_CHARACTERISTICS: DfeCharacteristicsPipeline(
            engine=engine,
            source_dataset_id=pipeline_settings.dfe_characteristics_dataset_id,
            source_csv=pipeline_settings.dfe_characteristics_source_csv,
        ),
        PipelineSource.OFSTED_LATEST: OfstedLatestPipeline(
            engine=engine,
            source_csv=pipeline_settings.ofsted_latest_source_csv,
        ),
        PipelineSource.OFSTED_TIMELINE: OfstedTimelinePipeline(
            engine=engine,
            source_index_url=pipeline_settings.ofsted_timeline_source_index_url,
            source_assets_csv=pipeline_settings.ofsted_timeline_source_assets,
            include_historical_baseline=(
                pipeline_settings.ofsted_timeline_include_historical_baseline
            ),
        ),
        PipelineSource.ONS_IMD: OnsImdPipeline(
            engine=engine,
            source_csv=pipeline_settings.imd_source_csv,
            source_release=pipeline_settings.imd_release,
        ),
        PipelineSource.POLICE_CRIME_CONTEXT: PoliceCrimeContextPipeline(
            engine=engine,
            source_archive_url=pipeline_settings.police_crime_source_archive_url,
            source_mode=pipeline_settings.police_crime_source_mode,
            crime_radius_meters=pipeline_settings.police_crime_radius_meters,
        ),
    }
