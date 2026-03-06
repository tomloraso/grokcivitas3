from civitas.domain.school_summaries.services import (
    ANALYST_VALIDATION_POLICY,
    OVERVIEW_VALIDATION_POLICY,
)


def test_overview_validation_policy_bounds_and_bans() -> None:
    assert OVERVIEW_VALIDATION_POLICY.minimum_words == 90
    assert OVERVIEW_VALIDATION_POLICY.maximum_words == 240
    assert any(
        "recommend" in pattern for pattern in OVERVIEW_VALIDATION_POLICY.banned_phrase_patterns
    )


def test_analyst_validation_policy_bounds_and_bans() -> None:
    assert ANALYST_VALIDATION_POLICY.minimum_words == 120
    assert ANALYST_VALIDATION_POLICY.maximum_words == 320
    assert any(
        "better than" in pattern for pattern in ANALYST_VALIDATION_POLICY.banned_phrase_patterns
    )
