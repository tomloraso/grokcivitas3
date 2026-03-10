from __future__ import annotations

from datetime import datetime, timezone

from civitas.infrastructure.persistence.postgres_favourite_repository import (
    _map_saved_school_summary_row,
)


def test_map_saved_school_summary_row_falls_back_to_school_fields_when_summary_is_missing() -> None:
    row = {
        "urn": "123456",
        "school_name": "Fallback School",
        "school_type": "Community school",
        "school_phase": "Primary",
        "school_postcode": "SW1A 1AA",
        "school_pupil_count": 0,
        "summary_name": None,
        "summary_type": None,
        "summary_phase": None,
        "summary_postcode": None,
        "summary_pupil_count": None,
        "latest_ofsted_label": None,
        "latest_ofsted_sort_rank": None,
        "latest_ofsted_availability": None,
        "primary_academic_metric_key": None,
        "primary_academic_metric_label": None,
        "primary_academic_metric_value": None,
        "primary_academic_metric_availability": None,
        "secondary_academic_metric_key": None,
        "secondary_academic_metric_label": None,
        "secondary_academic_metric_value": None,
        "secondary_academic_metric_availability": None,
        "saved_at": datetime(2026, 3, 10, 9, 0, tzinfo=timezone.utc),
    }

    result = _map_saved_school_summary_row(row)

    assert result.urn == "123456"
    assert result.name == "Fallback School"
    assert result.school_type == "Community school"
    assert result.phase == "Primary"
    assert result.postcode == "SW1A 1AA"
    assert result.pupil_count == 0
    assert result.latest_ofsted.availability == "not_published"
    assert result.academic_metric.metric_key == "ks2_combined_expected_pct"
    assert result.academic_metric.label == "KS2 expected standard"
    assert result.academic_metric.display_value is None
    assert result.academic_metric.availability == "not_published"
