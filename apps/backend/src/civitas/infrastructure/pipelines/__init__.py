from sqlalchemy.engine import Engine

from civitas.infrastructure.config.settings import PipelineSettings

from .base import Pipeline, PipelineSource
from .dfe_characteristics import DfeCharacteristicsPipeline
from .gias import GiasPipeline
from .ofsted_latest import OfstedLatestPipeline


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
    }
