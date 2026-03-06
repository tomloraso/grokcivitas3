from __future__ import annotations

import time
from typing import Any, Mapping, cast

import httpx

from civitas.application.school_summaries.ports.summary_generator import SummaryGenerator
from civitas.domain.school_summaries.models import (
    GeneratedSummary,
    SummaryContext,
    SummaryGenerationFeedback,
    SummaryKind,
)
from civitas.infrastructure.ai.providers.openai_compatible_support import (
    build_chat_completion_payload,
    build_generated_summary,
    chat_completions_url,
    sleep_with_backoff,
)

RETRYABLE_STATUS_CODES = {429, 500, 502, 503, 504}


class OpenAICompatibleSummaryGenerator(SummaryGenerator):
    def __init__(
        self,
        *,
        base_url: str,
        api_key: str,
        model_id: str,
        timeout_seconds: float,
        max_retries: int,
        retry_backoff_seconds: float,
        http_client: httpx.Client | None = None,
    ) -> None:
        self._base_url = base_url.rstrip("/")
        self._api_key = api_key
        self._model_id = model_id
        self._timeout_seconds = timeout_seconds
        self._max_retries = max_retries
        self._retry_backoff_seconds = retry_backoff_seconds
        self._http_client = http_client or httpx.Client(timeout=timeout_seconds)

    def generate(
        self,
        context: SummaryContext,
        *,
        summary_kind: SummaryKind,
        feedback: SummaryGenerationFeedback | None = None,
    ) -> GeneratedSummary:
        prompt_version, payload = build_chat_completion_payload(
            context=cast(Any, context),
            summary_kind=summary_kind,
            model_id=self._model_id,
            feedback=feedback,
        )
        started = time.perf_counter()
        response_payload = self._post_json(payload)
        duration_ms = int((time.perf_counter() - started) * 1000)
        return build_generated_summary(
            response_payload,
            prompt_version=prompt_version,
            fallback_model_id=self._model_id,
            generation_duration_ms=duration_ms,
        )

    def _post_json(self, payload: Mapping[str, object]) -> Mapping[str, Any]:
        url = chat_completions_url(self._base_url)
        last_error: Exception | None = None
        for attempt in range(self._max_retries + 1):
            try:
                response = self._http_client.post(
                    url,
                    headers={
                        "Authorization": f"Bearer {self._api_key}",
                        "Content-Type": "application/json",
                    },
                    json=payload,
                    timeout=self._timeout_seconds,
                )
                response.raise_for_status()
                parsed = response.json()
                if not isinstance(parsed, Mapping):
                    raise RuntimeError("AI provider returned a non-object JSON payload.")
                return parsed
            except httpx.HTTPStatusError as exc:
                last_error = exc
                status_code = exc.response.status_code
                if status_code in RETRYABLE_STATUS_CODES and attempt < self._max_retries:
                    sleep_with_backoff(self._retry_backoff_seconds, attempt)
                    continue
                break
            except (httpx.TimeoutException, httpx.TransportError, ValueError) as exc:
                last_error = exc
                if attempt < self._max_retries:
                    sleep_with_backoff(self._retry_backoff_seconds, attempt)
                    continue
                break

        raise RuntimeError("AI summary generation request failed.") from last_error
