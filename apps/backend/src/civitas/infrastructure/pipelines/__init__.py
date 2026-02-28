from sqlalchemy.engine import Engine

from civitas.infrastructure.config.settings import PipelineSettings

from .base import Pipeline, PipelineSource
from .gias import GiasPipeline


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
    }
