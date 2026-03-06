from __future__ import annotations

import json
import re
from dataclasses import dataclass, fields, is_dataclass
from datetime import date, datetime
from hashlib import sha256
from typing import Any

from civitas.domain.school_summaries.models import (
    SchoolAnalystContext,
    SchoolOverviewContext,
    SummaryContext,
)

WORD_PATTERN = re.compile(r"\b[\w']+\b")
DATE_CLAIM_PATTERN = (
    r"(?:\d{4}-\d{2}-\d{2}"
    r"|\d{1,2}\s+(?:january|february|march|april|may|june|july|august|september|october|november|december)\s+\d{4}"
    r"|(?:january|february|march|april|may|june|july|august|september|october|november|december)\s+\d{4})"
)
NUMERIC_CLAIM_PATTERN = r"[+-]?\d+(?:\.\d+)?"
OFSTED_UNSUPPORTED_PATTERN = re.compile(
    rf"\b(?:ofsted|inspection)\b[^.\n]{{0,80}}(?:{DATE_CLAIM_PATTERN}|outstanding|good|requires improvement|inadequate|not judged)",
    flags=re.IGNORECASE,
)
PROGRESS_8_UNSUPPORTED_PATTERN = re.compile(
    rf"\bprogress 8\b[^.\n]{{0,40}}(?:at|of|is|was|stands at|stood at|score(?:d)?|figure(?:s)?(?: of)?)?\s*[:=]?\s*{NUMERIC_CLAIM_PATTERN}",
    flags=re.IGNORECASE,
)
ATTAINMENT_8_UNSUPPORTED_PATTERN = re.compile(
    rf"\battainment 8\b[^.\n]{{0,40}}(?:at|of|is|was|stands at|stood at|score(?:d)?|figure(?:s)?(?: of)?)?\s*[:=]?\s*{NUMERIC_CLAIM_PATTERN}",
    flags=re.IGNORECASE,
)


@dataclass(frozen=True)
class SummaryValidationPolicy:
    minimum_words: int
    maximum_words: int
    banned_phrase_patterns: tuple[str, ...]


@dataclass(frozen=True)
class SummaryValidationResult:
    is_valid: bool
    reason_codes: tuple[str, ...]
    word_count: int
    non_context_phrases: tuple[str, ...] = ()


OVERVIEW_VALIDATION_POLICY = SummaryValidationPolicy(
    minimum_words=90,
    maximum_words=240,
    banned_phrase_patterns=(
        r"\bshould\b",
        r"\brecommend(?:ed|s|ing)?\b",
        r"\bideal for\b",
        r"\bperfect for\b",
        r"\bbest suited\b",
        r"\bwould suit\b",
        r"\bparents should\b",
        r"\bchoose\b",
        r"\btop school\b",
        r"\bone of the best\b",
        r"\bbetter than\b",
        r"\bworse than\b",
        r"\bcompared with other schools\b",
    ),
)


ANALYST_VALIDATION_POLICY = SummaryValidationPolicy(
    minimum_words=120,
    maximum_words=320,
    banned_phrase_patterns=OVERVIEW_VALIDATION_POLICY.banned_phrase_patterns,
)


def compute_data_version_hash(context: SummaryContext) -> str:
    payload = json.dumps(_normalize_for_hash(context), sort_keys=True, ensure_ascii=True)
    digest = sha256()
    digest.update(context.urn.encode("utf-8"))
    digest.update(b"|")
    digest.update(payload.encode("utf-8"))
    return digest.hexdigest()


def validate_generated_summary(
    text: str,
    context: SchoolOverviewContext,
) -> SummaryValidationResult:
    return _validate_summary_text(text, context, OVERVIEW_VALIDATION_POLICY)


def validate_analyst_summary(
    text: str,
    context: SchoolAnalystContext,
) -> SummaryValidationResult:
    return _validate_summary_text(text, context, ANALYST_VALIDATION_POLICY)


def _validate_summary_text(
    text: str,
    context: SummaryContext,
    policy: SummaryValidationPolicy,
) -> SummaryValidationResult:
    normalized_text = text.strip()
    word_count = len(WORD_PATTERN.findall(normalized_text))
    reason_codes: list[str] = []

    if word_count < policy.minimum_words:
        reason_codes.append("word_count_too_short")
    if word_count > policy.maximum_words:
        reason_codes.append("word_count_too_long")

    lowered_text = normalized_text.casefold()
    for pattern in policy.banned_phrase_patterns:
        if re.search(pattern, lowered_text, flags=re.IGNORECASE):
            reason_codes.append("banned_phrase_detected")
            break

    reason_codes.extend(_find_unsupported_references(normalized_text, context))
    deduped_reason_codes = tuple(dict.fromkeys(reason_codes))
    return SummaryValidationResult(
        is_valid=len(deduped_reason_codes) == 0,
        reason_codes=deduped_reason_codes,
        word_count=word_count,
        non_context_phrases=(),
    )


def _normalize_for_hash(value: Any) -> Any:
    if is_dataclass(value):
        return {
            field.name: _normalize_for_hash(getattr(value, field.name)) for field in fields(value)
        }
    if isinstance(value, (list, tuple)):
        return [_normalize_for_hash(item) for item in value]
    if isinstance(value, dict):
        return {
            str(key): _normalize_for_hash(item)
            for key, item in sorted(value.items(), key=lambda item: str(item[0]))
        }
    if isinstance(value, (date, datetime)):
        return value.isoformat()
    return value


def _find_unsupported_references(
    text: str,
    context: SummaryContext,
) -> list[str]:
    reason_codes: list[str] = []

    if (
        context.overall_effectiveness is None
        and context.inspection_date is None
        and OFSTED_UNSUPPORTED_PATTERN.search(text)
    ):
        reason_codes.append("references_missing_ofsted")

    if context.progress_8 is None and PROGRESS_8_UNSUPPORTED_PATTERN.search(text):
        reason_codes.append("references_missing_progress_8")

    if context.attainment_8 is None and ATTAINMENT_8_UNSUPPORTED_PATTERN.search(text):
        reason_codes.append("references_missing_attainment_8")

    return reason_codes
