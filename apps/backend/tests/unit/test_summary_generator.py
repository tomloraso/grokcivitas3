from __future__ import annotations

from collections.abc import Mapping

import httpx

from civitas.domain.school_summaries.models import (
    MetricTrendPoint,
    SchoolAnalystContext,
    SchoolOverviewContext,
    SummaryGenerationFeedback,
)
from civitas.infrastructure.ai.providers.grok_summary_generator import GrokSummaryGenerator
from civitas.infrastructure.ai.providers.openai_compatible_summary_generator import (
    OpenAICompatibleSummaryGenerator,
)


def test_openai_compatible_summary_generator_builds_overview_summary() -> None:
    transport = httpx.MockTransport(
        lambda request: httpx.Response(200, json=_payload("Model text."))
    )
    generator = OpenAICompatibleSummaryGenerator(
        base_url="https://example.test/v1",
        api_key="test-key",
        model_id="test-model",
        timeout_seconds=5,
        max_retries=0,
        retry_backoff_seconds=0.1,
        http_client=httpx.Client(transport=transport),
    )

    result = generator.generate(_context(), summary_kind="overview")

    assert result.text == "Model text."
    assert result.prompt_version == "overview.v5"
    assert result.model_id == "test-model"


def test_openai_compatible_summary_generator_includes_retry_feedback() -> None:
    captured_request: dict[str, object] = {}

    def handler(request: httpx.Request) -> httpx.Response:
        captured_request["body"] = request.read().decode("utf-8")
        return httpx.Response(200, json=_payload("Retry text."))

    generator = OpenAICompatibleSummaryGenerator(
        base_url="https://example.test/v1",
        api_key="test-key",
        model_id="test-model",
        timeout_seconds=5,
        max_retries=0,
        retry_backoff_seconds=0.1,
        http_client=httpx.Client(transport=httpx.MockTransport(handler)),
    )

    generator.generate(
        _context(),
        summary_kind="overview",
        feedback=SummaryGenerationFeedback(
            reason_codes=("word_count_too_short",),
            previous_text="Too short.",
        ),
    )

    assert "word_count_too_short" in str(captured_request["body"])


def test_openai_compatible_summary_generator_builds_analyst_summary() -> None:
    transport = httpx.MockTransport(
        lambda request: httpx.Response(200, json=_payload("Analyst text."))
    )
    generator = OpenAICompatibleSummaryGenerator(
        base_url="https://example.test/v1",
        api_key="test-key",
        model_id="test-model",
        timeout_seconds=5,
        max_retries=0,
        retry_backoff_seconds=0.1,
        http_client=httpx.Client(transport=transport),
    )

    result = generator.generate(_analyst_context(), summary_kind="analyst")

    assert result.text == "Analyst text."
    assert result.prompt_version == "analyst.v4"
    assert result.model_id == "test-model"


def test_grok_summary_generator_uses_batch_api_for_bulk_generation() -> None:
    requests_seen: list[tuple[str, str]] = []

    def handler(request: httpx.Request) -> httpx.Response:
        requests_seen.append((request.method, str(request.url)))
        if request.method == "POST" and str(request.url).endswith("/v1/batches"):
            body = request.read().decode("utf-8")
            assert '"name"' in body
            return httpx.Response(200, json={"batch_id": "batch-1", "state": {"num_pending": 2}})
        if request.method == "POST" and str(request.url).endswith("/v1/batches/batch-1/requests"):
            body = request.read().decode("utf-8")
            assert "batch_request_id" in body
            assert "chat_get_completion" in body
            assert "100001" in body
            assert "100002" in body
            return httpx.Response(
                200, content=b"null", headers={"Content-Type": "application/json"}
            )
        if request.method == "GET" and str(request.url).endswith("/v1/batches/batch-1"):
            return httpx.Response(
                200,
                json={"id": "batch-1", "state": {"num_pending": 0, "num_error": 0}},
            )
        if request.method == "GET" and str(request.url).endswith(
            "/v1/batches/batch-1/results?page_size=100"
        ):
            return httpx.Response(
                200,
                json={
                    "results": [
                        {
                            "batch_request_id": "100001",
                            "batch_result": {
                                "response": {
                                    "chat_get_completion": _payload("Batch text one."),
                                }
                            },
                        },
                        {
                            "batch_request_id": "100002",
                            "batch_result": {
                                "response": {
                                    "chat_get_completion": _payload("Batch text two."),
                                }
                            },
                        },
                    ],
                    "pagination_token": "page-2",
                },
            )
        if request.method == "GET" and str(request.url).endswith(
            "/v1/batches/batch-1/results?page_size=100&pagination_token=page-2"
        ):
            return httpx.Response(
                200,
                json={
                    "failed": [],
                },
            )
        raise AssertionError(f"Unexpected request: {request.method} {request.url}")

    generator = GrokSummaryGenerator(
        api_key="test-key",
        model_id="test-model",
        timeout_seconds=5,
        max_retries=0,
        retry_backoff_seconds=0.1,
        batch_poll_interval_seconds=0,
        http_client=httpx.Client(transport=httpx.MockTransport(handler)),
    )

    results = generator.generate_batch(
        [_context(), _context(urn="100002", name="Second School")],
        summary_kind="overview",
    )

    assert [result.urn for result in results] == ["100001", "100002"]
    assert [result.summary.text if result.summary else None for result in results] == [
        "Batch text one.",
        "Batch text two.",
    ]
    assert requests_seen == [
        ("POST", "https://api.x.ai/v1/batches"),
        ("POST", "https://api.x.ai/v1/batches/batch-1/requests"),
        ("GET", "https://api.x.ai/v1/batches/batch-1"),
        ("GET", "https://api.x.ai/v1/batches/batch-1/results?page_size=100"),
        (
            "GET",
            "https://api.x.ai/v1/batches/batch-1/results?page_size=100&pagination_token=page-2",
        ),
    ]


def _payload(text: str) -> Mapping[str, object]:
    return {
        "model": "test-model",
        "choices": [{"message": {"content": text}}],
    }


def _context(*, urn: str = "100001", name: str = "Test School") -> SchoolOverviewContext:
    return SchoolOverviewContext(
        urn=urn,
        name=name,
        phase="Secondary",
        school_type="Academy",
        status="Open",
        postcode="SW1A 1AA",
        website="https://example.test",
        telephone="020 7946 0999",
        head_name="Alex Smith",
        head_job_title="Headteacher",
        statutory_low_age=11,
        statutory_high_age=16,
        gender="Mixed",
        religious_character=None,
        admissions_policy="Not applicable",
        sixth_form="Does not have a sixth form",
        trust_name="Example Trust",
        la_name="Westminster",
        urban_rural="Urban city and town",
        pupil_count=900,
        capacity=1000,
        number_of_boys=450,
        number_of_girls=450,
        fsm_pct=18.2,
        eal_pct=22.4,
        sen_pct=14.0,
        ehcp_pct=3.1,
        progress_8=0.31,
        attainment_8=51.2,
        ks2_reading_met=None,
        ks2_maths_met=None,
        overall_effectiveness="Good",
        inspection_date=None,
        imd_decile=7,
    )


def _analyst_context() -> SchoolAnalystContext:
    return SchoolAnalystContext(
        **_context().__dict__,
        fsm_pct_trend=(MetricTrendPoint(year="2024/25", value=18.2),),
        eal_pct_trend=(MetricTrendPoint(year="2024/25", value=22.4),),
        sen_pct_trend=(MetricTrendPoint(year="2024/25", value=14.0),),
        progress_8_trend=(MetricTrendPoint(year="2024/25", value=0.31),),
        attainment_8_trend=(MetricTrendPoint(year="2024/25", value=51.2),),
        quality_of_education="Good",
        behaviour_and_attitudes="Good",
        personal_development="Good",
        leadership_and_management="Good",
        imd_rank=4825,
        idaci_decile=2,
        total_incidents_12m=486,
    )
