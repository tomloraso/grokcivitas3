from __future__ import annotations

import httpx

from civitas.infrastructure.ai.providers.openai_compatible_summary_generator import (
    OpenAICompatibleSummaryGenerator,
)

DEFAULT_OPENAI_API_BASE_URL = "https://api.openai.com/v1"


class OpenAISummaryGenerator(OpenAICompatibleSummaryGenerator):
    def __init__(
        self,
        *,
        api_key: str,
        model_id: str,
        timeout_seconds: float,
        max_retries: int,
        retry_backoff_seconds: float,
        base_url: str = DEFAULT_OPENAI_API_BASE_URL,
        http_client: httpx.Client | None = None,
    ) -> None:
        super().__init__(
            base_url=base_url,
            api_key=api_key,
            model_id=model_id,
            timeout_seconds=timeout_seconds,
            max_retries=max_retries,
            retry_backoff_seconds=retry_backoff_seconds,
            http_client=http_client,
        )
