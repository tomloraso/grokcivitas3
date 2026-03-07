from __future__ import annotations

import time
from collections.abc import Mapping, Sequence
from datetime import datetime, timezone
from typing import Any

import httpx

from civitas.domain.school_summaries.models import (
    BatchGeneratedSummaryResult,
    GeneratedSummary,
    PolledSummaryBatch,
    SubmittedSummaryBatch,
    SummaryBatchStatus,
    SummaryContext,
    SummaryKind,
)
from civitas.infrastructure.ai.providers.openai_compatible_summary_generator import (
    OpenAICompatibleSummaryGenerator,
)
from civitas.infrastructure.ai.providers.openai_compatible_support import (
    batch_requests_url,
    batch_results_url,
    batch_status_url,
    batches_url,
    build_chat_completion_payload,
    build_generated_summary,
    sleep_with_backoff,
)

DEFAULT_GROK_API_BASE_URL = "https://api.x.ai/v1"
DEFAULT_BATCH_POLL_INTERVAL_SECONDS = 2.0
DEFAULT_BATCH_RESULTS_PAGE_SIZE = 100
RETRYABLE_STATUS_CODES = {429, 500, 502, 503, 504}
QueryParamScalar = str | int | float | bool | None


class GrokSummaryGenerator(OpenAICompatibleSummaryGenerator):
    def __init__(
        self,
        *,
        api_key: str,
        model_id: str,
        timeout_seconds: float,
        max_retries: int,
        retry_backoff_seconds: float,
        base_url: str = DEFAULT_GROK_API_BASE_URL,
        batch_poll_interval_seconds: float = DEFAULT_BATCH_POLL_INTERVAL_SECONDS,
        batch_max_wait_seconds: float | None = None,
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
        self._batch_poll_interval_seconds = max(batch_poll_interval_seconds, 0.0)
        self._batch_max_wait_seconds = (
            max(batch_max_wait_seconds, timeout_seconds)
            if batch_max_wait_seconds is not None
            else max(timeout_seconds * 60, timeout_seconds)
        )

    def generate_batch(
        self,
        contexts: Sequence[SummaryContext],
        *,
        summary_kind: SummaryKind,
    ) -> Sequence[BatchGeneratedSummaryResult]:
        if not contexts:
            return []

        submitted_batch = self.submit_batch(contexts, summary_kind=summary_kind)
        status_payload = self._wait_for_batch(submitted_batch.provider_batch_id)
        if not _batch_finished_successfully(status_payload):
            status = _extract_batch_status(status_payload)
            error_code = f"batch_{status}"
            return [
                BatchGeneratedSummaryResult(
                    urn=context.urn,
                    summary=None,
                    error_code=error_code,
                )
                for context in contexts
            ]

        results_by_urn = {
            result.urn: result
            for result in self._fetch_all_batch_results(
                batch_id=submitted_batch.provider_batch_id,
                prompt_version=submitted_batch.prompt_version,
            )
        }
        return [
            results_by_urn.get(
                context.urn,
                BatchGeneratedSummaryResult(
                    urn=context.urn,
                    summary=None,
                    error_code="missing_batch_result",
                ),
            )
            for context in contexts
        ]

    def batch_provider_name(self) -> str:
        return "grok"

    def submit_batch(
        self,
        contexts: Sequence[SummaryContext],
        *,
        summary_kind: SummaryKind,
        provider_batch_id: str | None = None,
    ) -> SubmittedSummaryBatch:
        if not contexts:
            raise ValueError("At least one context is required to submit a Grok batch.")

        prompt_version, _ = build_chat_completion_payload(
            context=contexts[0],
            summary_kind=summary_kind,
            model_id=self._model_id,
        )
        batch_id = provider_batch_id or self._create_batch(summary_kind=summary_kind)
        self._add_batch_requests(
            batch_id=batch_id,
            contexts=contexts,
            summary_kind=summary_kind,
        )
        return SubmittedSummaryBatch(
            provider=self.batch_provider_name(),
            provider_batch_id=batch_id,
            prompt_version=prompt_version,
            request_count=len(contexts),
            submitted_at=_utc_now(),
        )

    def poll_batch(
        self,
        *,
        provider_batch_id: str,
        prompt_version: str,
    ) -> PolledSummaryBatch:
        status_payload = self._get_json_from_url(
            batch_status_url(self._base_url, provider_batch_id)
        )
        status = _derive_polled_batch_status(status_payload)
        if status in {"failed", "cancelled", "expired"}:
            return PolledSummaryBatch(
                provider=self.batch_provider_name(),
                provider_batch_id=provider_batch_id,
                status=status,
                results=(),
                error_code=f"batch_{status}",
            )

        results: tuple[BatchGeneratedSummaryResult, ...] = ()
        if status == "completed" or _extract_batch_success_count(status_payload) > 0:
            results = tuple(
                self._fetch_all_batch_results(
                    batch_id=provider_batch_id,
                    prompt_version=prompt_version,
                )
            )

        return PolledSummaryBatch(
            provider=self.batch_provider_name(),
            provider_batch_id=provider_batch_id,
            status=status,
            results=results,
            error_code=None,
        )

    def _create_batch(self, *, summary_kind: SummaryKind) -> str:
        payload = self._post_json_to_url(
            batches_url(self._base_url),
            {"name": f"civitas-{summary_kind}-{int(time.time())}"},
        )
        batch_id = payload.get("batch_id")
        if not isinstance(batch_id, str) or not batch_id.strip():
            batch_id = payload.get("id")
        if isinstance(batch_id, str) and batch_id.strip():
            return batch_id.strip()
        raise RuntimeError("Grok batch API did not return a batch id.")

    def _add_batch_requests(
        self,
        *,
        batch_id: str,
        contexts: Sequence[SummaryContext],
        summary_kind: SummaryKind,
    ) -> None:
        batch_requests = []
        for context in contexts:
            _, request_body = build_chat_completion_payload(
                context=context,
                summary_kind=summary_kind,
                model_id=self._model_id,
            )
            batch_requests.append(
                {
                    "batch_request_id": context.urn,
                    "batch_request": {"chat_get_completion": request_body},
                }
            )

        self._post_json_to_url(
            batch_requests_url(self._base_url, batch_id),
            {"batch_requests": batch_requests},
        )

    def _wait_for_batch(self, batch_id: str) -> Mapping[str, Any]:
        deadline = time.monotonic() + self._batch_max_wait_seconds
        status_payload = self._get_json_from_url(batch_status_url(self._base_url, batch_id))

        while not _batch_is_terminal(status_payload):
            if time.monotonic() >= deadline:
                raise RuntimeError("Timed out waiting for Grok batch completion.")
            time.sleep(self._batch_poll_interval_seconds)
            status_payload = self._get_json_from_url(batch_status_url(self._base_url, batch_id))

        return status_payload

    def _fetch_batch_results(
        self,
        *,
        batch_id: str,
        contexts: Sequence[SummaryContext],
        prompt_version: str,
    ) -> Sequence[BatchGeneratedSummaryResult]:
        result_items = self._list_batch_results(batch_id)
        results_by_urn: dict[str, BatchGeneratedSummaryResult] = {}

        for item in result_items:
            urn = _extract_result_urn(item)
            if urn is None:
                continue

            summary = _extract_generated_summary(
                item,
                prompt_version=prompt_version,
                fallback_model_id=self._model_id,
            )
            if summary is None:
                results_by_urn[urn] = BatchGeneratedSummaryResult(
                    urn=urn,
                    summary=None,
                    error_code=_extract_result_error_code(item),
                )
                continue

            results_by_urn[urn] = BatchGeneratedSummaryResult(
                urn=urn,
                summary=summary,
                error_code=None,
            )

        return [
            results_by_urn.get(
                context.urn,
                BatchGeneratedSummaryResult(
                    urn=context.urn,
                    summary=None,
                    error_code="missing_batch_result",
                ),
            )
            for context in contexts
        ]

    def _fetch_all_batch_results(
        self,
        *,
        batch_id: str,
        prompt_version: str,
    ) -> Sequence[BatchGeneratedSummaryResult]:
        result_items = self._list_batch_results(batch_id)
        results: list[BatchGeneratedSummaryResult] = []
        for item in result_items:
            urn = _extract_result_urn(item)
            if urn is None:
                continue
            summary = _extract_generated_summary(
                item,
                prompt_version=prompt_version,
                fallback_model_id=self._model_id,
            )
            if summary is None:
                results.append(
                    BatchGeneratedSummaryResult(
                        urn=urn,
                        summary=None,
                        error_code=_extract_result_error_code(item),
                    )
                )
                continue
            results.append(
                BatchGeneratedSummaryResult(
                    urn=urn,
                    summary=summary,
                    error_code=None,
                )
            )
        return results

    def _list_batch_results(self, batch_id: str) -> list[Mapping[str, Any]]:
        results: list[Mapping[str, Any]] = []
        pagination_token: str | None = None

        while True:
            params: dict[str, QueryParamScalar] = {"page_size": DEFAULT_BATCH_RESULTS_PAGE_SIZE}
            if pagination_token is not None:
                params["pagination_token"] = pagination_token

            response_payload = self._get_json_from_url(
                batch_results_url(self._base_url, batch_id),
                params=params,
            )
            results.extend(_extract_batch_result_items(response_payload))
            pagination_token = _extract_pagination_token(response_payload)
            if pagination_token is None:
                break

        return results

    def _post_json_to_url(
        self,
        url: str,
        payload: Mapping[str, object],
    ) -> Mapping[str, Any]:
        return self._request_json("POST", url, json=payload)

    def _get_json_from_url(
        self,
        url: str,
        *,
        params: Mapping[str, QueryParamScalar] | None = None,
    ) -> Mapping[str, Any]:
        return self._request_json("GET", url, params=params)

    def _headers(self) -> Mapping[str, str]:
        return {
            "Authorization": f"Bearer {self._api_key}",
            "Content-Type": "application/json",
        }

    def _request_json(
        self,
        method: str,
        url: str,
        *,
        json: Mapping[str, object] | None = None,
        params: Mapping[str, QueryParamScalar] | None = None,
    ) -> Mapping[str, Any]:
        last_error: Exception | None = None
        for attempt in range(self._max_retries + 1):
            try:
                response = self._http_client.request(
                    method,
                    url,
                    headers=self._headers(),
                    json=json,
                    params=params,
                    timeout=self._timeout_seconds,
                )
                response.raise_for_status()
                parsed = response.json()
                if parsed is None:
                    return {}
                if not isinstance(parsed, Mapping):
                    raise RuntimeError("Grok batch API returned a non-object JSON payload.")
                return parsed
            except httpx.HTTPStatusError as exc:
                last_error = exc
                if _is_non_retryable_quota_error(exc.response):
                    break
                if (
                    exc.response.status_code in RETRYABLE_STATUS_CODES
                    and attempt < self._max_retries
                ):
                    sleep_with_backoff(self._retry_backoff_seconds, attempt)
                    continue
                break
            except (httpx.TimeoutException, httpx.TransportError, ValueError) as exc:
                last_error = exc
                if attempt < self._max_retries:
                    sleep_with_backoff(self._retry_backoff_seconds, attempt)
                    continue
                break

        detail = _extract_response_error_message(last_error)
        if detail is None:
            raise RuntimeError("Grok batch API request failed.") from last_error
        raise RuntimeError(f"Grok batch API request failed: {detail}") from last_error


_TERMINAL_BATCH_STATUSES = {"completed", "succeeded", "failed", "cancelled", "expired"}


def _extract_batch_status(payload: Mapping[str, Any]) -> str:
    state = payload.get("state")
    if isinstance(state, Mapping):
        status = state.get("status")
        if isinstance(status, str) and status.strip():
            return status.strip().casefold()

    status = payload.get("status")
    if isinstance(status, str) and status.strip():
        return status.strip().casefold()
    return "unknown"


def _extract_batch_result_items(payload: Mapping[str, Any]) -> Sequence[Mapping[str, Any]]:
    items: list[Mapping[str, Any]] = []
    for key in ("data", "results", "items", "succeeded", "failed"):
        candidate = payload.get(key)
        if not isinstance(candidate, list):
            continue
        items.extend(item for item in candidate if isinstance(item, Mapping))
    return items


def _extract_result_urn(item: Mapping[str, Any]) -> str | None:
    for key in ("batch_request_id", "custom_id", "request_id"):
        value = item.get(key)
        if isinstance(value, str) and value.strip():
            return value.strip()

    return None


def _extract_generated_summary(
    item: Mapping[str, Any],
    *,
    prompt_version: str,
    fallback_model_id: str,
) -> GeneratedSummary | None:
    response_body = _extract_result_response_body(item)
    if response_body is not None:
        return build_generated_summary(
            response_body,
            prompt_version=prompt_version,
            fallback_model_id=fallback_model_id,
            generation_duration_ms=None,
        )

    response = item.get("response")
    if not isinstance(response, Mapping):
        return None

    content = response.get("content")
    text = _normalize_response_text(content)
    if text is None:
        return None

    model_id = response.get("model")
    resolved_model_id = fallback_model_id if not isinstance(model_id, str) else model_id
    return GeneratedSummary(
        text=text,
        prompt_version=prompt_version,
        model_id=resolved_model_id,
        generation_duration_ms=None,
    )


def _extract_result_response_body(item: Mapping[str, Any]) -> Mapping[str, Any] | None:
    batch_result = item.get("batch_result")
    if isinstance(batch_result, Mapping):
        response = batch_result.get("response")
        if isinstance(response, Mapping):
            chat_completion = response.get("chat_get_completion")
            if isinstance(chat_completion, Mapping):
                return chat_completion

    response = item.get("response")
    if isinstance(response, Mapping):
        body = response.get("body")
        if isinstance(body, Mapping):
            return body
        return response if "choices" in response else None

    result = item.get("result")
    if isinstance(result, Mapping):
        return result if "choices" in result else None

    return item if "choices" in item else None


def _extract_result_error_code(item: Mapping[str, Any]) -> str:
    batch_result = item.get("batch_result")
    if isinstance(batch_result, Mapping):
        error = batch_result.get("error")
        if isinstance(error, Mapping):
            code = error.get("code")
            if isinstance(code, str) and code.strip():
                return code.strip().casefold()
            message = error.get("message")
            if isinstance(message, str) and message.strip():
                return message.strip().casefold().replace(" ", "_")

    error = item.get("error")
    if isinstance(error, Mapping):
        code = error.get("code")
        if isinstance(code, str) and code.strip():
            return code.strip().casefold()
        message = error.get("message")
        if isinstance(message, str) and message.strip():
            return message.strip().casefold().replace(" ", "_")

    for key in ("error_code", "error_message", "status"):
        value = item.get(key)
        if isinstance(value, str) and value.strip():
            return value.strip().casefold().replace(" ", "_")

    return "batch_request_failed"


def _extract_pagination_token(payload: Mapping[str, Any]) -> str | None:
    for key in ("pagination_token", "next_pagination_token", "next_cursor"):
        value = payload.get(key)
        if isinstance(value, str) and value.strip():
            return value.strip()
    return None


def _batch_finished_successfully(payload: Mapping[str, Any]) -> bool:
    return _extract_batch_pending_count(payload) == 0 and _extract_batch_error_count(payload) == 0


def _batch_is_terminal(payload: Mapping[str, Any]) -> bool:
    if _extract_batch_pending_count(payload) == 0:
        return True
    return _extract_batch_status(payload) in _TERMINAL_BATCH_STATUSES


def _extract_batch_pending_count(payload: Mapping[str, Any]) -> int:
    return _extract_state_count(payload, "num_pending")


def _extract_batch_error_count(payload: Mapping[str, Any]) -> int:
    return _extract_state_count(payload, "num_error") + _extract_state_count(
        payload,
        "num_cancelled",
    )


def _extract_batch_success_count(payload: Mapping[str, Any]) -> int:
    return _extract_state_count(payload, "num_success")


def _extract_state_count(payload: Mapping[str, Any], key: str) -> int:
    state = payload.get("state")
    if isinstance(state, Mapping):
        value = state.get(key)
        if isinstance(value, int):
            return value
    value = payload.get(key)
    if isinstance(value, int):
        return value
    return 0


def _derive_polled_batch_status(payload: Mapping[str, Any]) -> SummaryBatchStatus:
    status = _extract_batch_status(payload)
    if status == "failed":
        return "failed"
    if status == "cancelled":
        return "cancelled"
    if status == "expired":
        return "expired"
    if _extract_batch_pending_count(payload) > 0:
        return "running"
    return "completed"


def _normalize_response_text(value: object) -> str | None:
    if isinstance(value, str):
        normalized = value.strip()
        return normalized or None
    if isinstance(value, list):
        text_parts: list[str] = []
        for item in value:
            if isinstance(item, Mapping) and isinstance(item.get("text"), str):
                text_parts.append(item["text"].strip())
        normalized = "\n".join(part for part in text_parts if part)
        return normalized or None
    return None


def _utc_now() -> datetime:
    return datetime.now(timezone.utc)


def _is_non_retryable_quota_error(response: httpx.Response) -> bool:
    if response.status_code != 429:
        return False
    detail = _extract_response_error_message(response)
    if detail is None:
        return False
    normalized = detail.casefold()
    return "used all available credits" in normalized or "monthly spending limit" in normalized


def _extract_response_error_message(error: Exception | httpx.Response | None) -> str | None:
    response: httpx.Response | None
    if isinstance(error, httpx.Response):
        response = error
    elif isinstance(error, httpx.HTTPStatusError):
        response = error.response
    else:
        response = None

    if response is None:
        return None

    try:
        payload = response.json()
    except ValueError:
        payload = None

    if isinstance(payload, Mapping):
        for key in ("error", "message", "code"):
            value = payload.get(key)
            if isinstance(value, str) and value.strip():
                return value.strip()

    body = response.text.strip()
    if body:
        return body
    return f"HTTP {response.status_code}"
