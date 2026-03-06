import pytest

from civitas.application.school_summaries.ports.summary_generator import BatchSummaryGenerator
from civitas.infrastructure.ai.provider_factory import build_summary_generator
from civitas.infrastructure.ai.providers.grok_summary_generator import GrokSummaryGenerator
from civitas.infrastructure.ai.providers.openai_compatible_summary_generator import (
    OpenAICompatibleSummaryGenerator,
)
from civitas.infrastructure.ai.providers.openai_summary_generator import OpenAISummaryGenerator
from civitas.infrastructure.config.settings import AppSettings


def test_summary_generator_factory_builds_grok(monkeypatch: pytest.MonkeyPatch) -> None:
    settings = _settings(monkeypatch, provider="grok")
    generator = build_summary_generator(settings)
    assert isinstance(generator, GrokSummaryGenerator)
    assert isinstance(generator, BatchSummaryGenerator)


def test_summary_generator_factory_builds_openai(monkeypatch: pytest.MonkeyPatch) -> None:
    settings = _settings(monkeypatch, provider="openai")
    assert isinstance(build_summary_generator(settings), OpenAISummaryGenerator)


def test_summary_generator_factory_builds_openai_compatible(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    settings = _settings(monkeypatch, provider="openai_compatible")
    assert isinstance(build_summary_generator(settings), OpenAICompatibleSummaryGenerator)


def _settings(monkeypatch: pytest.MonkeyPatch, *, provider: str) -> AppSettings:
    monkeypatch.setenv("CIVITAS_AI_ENABLED", "true")
    monkeypatch.setenv("CIVITAS_AI_PROVIDER", provider)
    monkeypatch.setenv("CIVITAS_AI_MODEL_ID", "test-model")
    monkeypatch.setenv("CIVITAS_AI_API_KEY", "test-key")
    monkeypatch.setenv("CIVITAS_AI_API_BASE_URL", "https://example.test/v1")
    return AppSettings(_env_file=None)
