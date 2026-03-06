from __future__ import annotations

import httpx

from civitas.application.school_summaries.ports.summary_generator import SummaryGenerator
from civitas.infrastructure.ai.providers.grok_summary_generator import (
    DEFAULT_GROK_API_BASE_URL,
    GrokSummaryGenerator,
)
from civitas.infrastructure.ai.providers.openai_compatible_summary_generator import (
    OpenAICompatibleSummaryGenerator,
)
from civitas.infrastructure.ai.providers.openai_summary_generator import OpenAISummaryGenerator
from civitas.infrastructure.config.settings import AppSettings


def build_summary_generator(
    settings: AppSettings,
    *,
    http_client: httpx.Client | None = None,
) -> SummaryGenerator:
    provider = settings.ai.provider
    base_url_override = settings.ai.api_base_url or None
    if provider == "grok":
        return GrokSummaryGenerator(
            api_key=settings.ai.api_key,
            model_id=settings.ai.model_id,
            timeout_seconds=settings.ai.request_timeout_seconds,
            max_retries=settings.ai.max_retries,
            retry_backoff_seconds=settings.ai.retry_backoff_seconds,
            base_url=base_url_override or DEFAULT_GROK_API_BASE_URL,
            http_client=http_client,
        )
    if provider == "openai":
        return OpenAISummaryGenerator(
            api_key=settings.ai.api_key,
            model_id=settings.ai.model_id,
            timeout_seconds=settings.ai.request_timeout_seconds,
            max_retries=settings.ai.max_retries,
            retry_backoff_seconds=settings.ai.retry_backoff_seconds,
            http_client=http_client,
            **({"base_url": base_url_override} if base_url_override is not None else {}),
        )
    if provider == "openai_compatible":
        return OpenAICompatibleSummaryGenerator(
            base_url=settings.ai.api_base_url,
            api_key=settings.ai.api_key,
            model_id=settings.ai.model_id,
            timeout_seconds=settings.ai.request_timeout_seconds,
            max_retries=settings.ai.max_retries,
            retry_backoff_seconds=settings.ai.retry_backoff_seconds,
            http_client=http_client,
        )
    raise ValueError(f"Unsupported AI provider '{provider}'.")
