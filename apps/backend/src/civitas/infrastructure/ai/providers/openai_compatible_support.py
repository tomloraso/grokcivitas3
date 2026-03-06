from __future__ import annotations

import time
from typing import Any, Mapping

from civitas.domain.school_summaries.models import (
    GeneratedSummary,
    SummaryContext,
    SummaryGenerationFeedback,
    SummaryKind,
)
from civitas.infrastructure.ai.prompt_templates import school_analyst, school_overview


def build_chat_completion_payload(
    *,
    context: SummaryContext,
    summary_kind: SummaryKind,
    model_id: str,
    feedback: SummaryGenerationFeedback | None = None,
) -> tuple[str, Mapping[str, object]]:
    prompt_template = _template_for_summary_kind(summary_kind)
    system_prompt, user_prompt = prompt_template.render(context, feedback=feedback)
    return prompt_template.VERSION, {
        "model": model_id,
        "temperature": prompt_template.TEMPERATURE,
        "messages": [
            {"role": "system", "content": system_prompt},
            {"role": "user", "content": user_prompt},
        ],
    }


def build_generated_summary(
    payload: Mapping[str, Any],
    *,
    prompt_version: str,
    fallback_model_id: str,
    generation_duration_ms: int | None,
) -> GeneratedSummary:
    model_id = payload.get("model")
    resolved_model_id = fallback_model_id if not isinstance(model_id, str) else model_id
    return GeneratedSummary(
        text=extract_message_text(payload),
        prompt_version=prompt_version,
        model_id=resolved_model_id,
        generation_duration_ms=generation_duration_ms,
    )


def chat_completions_url(base_url: str) -> str:
    if base_url.endswith("/v1"):
        return f"{base_url}/chat/completions"
    return f"{base_url}/v1/chat/completions"


def chat_completions_path() -> str:
    return "/v1/chat/completions"


def batches_url(base_url: str) -> str:
    if base_url.endswith("/v1"):
        return f"{base_url}/batches"
    return f"{base_url}/v1/batches"


def batch_requests_url(base_url: str, batch_id: str) -> str:
    return f"{batches_url(base_url)}/{batch_id}/requests"


def batch_status_url(base_url: str, batch_id: str) -> str:
    return f"{batches_url(base_url)}/{batch_id}"


def batch_results_url(base_url: str, batch_id: str) -> str:
    return f"{batches_url(base_url)}/{batch_id}/results"


def extract_message_text(payload: Mapping[str, Any]) -> str:
    choices = payload.get("choices")
    if not isinstance(choices, list) or len(choices) == 0:
        raise RuntimeError("AI provider payload did not include choices.")

    choice = choices[0]
    if not isinstance(choice, Mapping):
        raise RuntimeError("AI provider choice payload was invalid.")
    message = choice.get("message")
    if not isinstance(message, Mapping):
        raise RuntimeError("AI provider message payload was invalid.")
    content = message.get("content")
    if isinstance(content, str):
        normalized = content.strip()
        if normalized:
            return normalized
    if isinstance(content, list):
        text_parts: list[str] = []
        for item in content:
            if not isinstance(item, Mapping):
                continue
            if item.get("type") == "text" and isinstance(item.get("text"), str):
                text_parts.append(item["text"].strip())
        normalized = "\n".join(part for part in text_parts if part)
        if normalized:
            return normalized
    raise RuntimeError("AI provider did not return text content.")


def sleep_with_backoff(base_seconds: float, attempt: int) -> None:
    time.sleep(base_seconds * (2**attempt))


def _template_for_summary_kind(summary_kind: SummaryKind):
    if summary_kind == "overview":
        return school_overview
    if summary_kind == "analyst":
        return school_analyst
    raise ValueError(f"Unsupported summary kind '{summary_kind}'.")
