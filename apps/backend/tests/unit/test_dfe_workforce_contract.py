from __future__ import annotations

from datetime import date

from civitas.infrastructure.pipelines.contracts import dfe_workforce as contract


def test_normalize_row_maps_workforce_and_leadership_fields() -> None:
    normalized, rejection = contract.normalize_row(
        {
            "school_urn": "123456",
            "time_period": "202324",
            "pupil_teacher_ratio": "16.3",
            "supply_teacher_pct": "2.4",
            "teachers_3plus_years_pct": "76.5",
            "teacher_turnover_pct": "9.8",
            "qts_pct": "95.2",
            "qualifications_level6_plus_pct": "81.1",
            "headteacher_name": "A. Jones",
            "headteacher_start_date": "2020-09-01",
            "headteacher_tenure_years": "4.5",
            "leadership_turnover_score": "1.2",
        },
        release_slug="2023-24",
        release_version_id="wf-rv-2024",
        file_id="wf-file-2024",
    )

    assert rejection is None
    assert normalized is not None
    assert normalized["urn"] == "123456"
    assert normalized["academic_year"] == "2023/24"
    assert normalized["pupil_teacher_ratio"] == 16.3
    assert normalized["supply_staff_pct"] == 2.4
    assert normalized["teachers_3plus_years_pct"] == 76.5
    assert normalized["teacher_turnover_pct"] == 9.8
    assert normalized["qts_pct"] == 95.2
    assert normalized["qualifications_level6_plus_pct"] == 81.1
    assert normalized["headteacher_name"] == "A. Jones"
    assert normalized["headteacher_start_date"] == date(2020, 9, 1)
    assert normalized["headteacher_tenure_years"] == 4.5
    assert normalized["leadership_turnover_score"] == 1.2
    assert normalized["source_dataset_id"] == "workforce:wf-rv-2024"
    assert normalized["source_dataset_version"] == "workforce:wf-file-2024"


def test_normalize_row_handles_suppression_tokens() -> None:
    normalized, rejection = contract.normalize_row(
        {
            "school_urn": "123456",
            "time_period": "202324",
            "pupil_teacher_ratio": ".",
            "supply_teacher_pct": "SUPP",
            "teachers_3plus_years_pct": "x",
            "teacher_turnover_pct": "na",
            "qts_pct": "n/a",
            "qualifications_level6_plus_pct": "ne",
            "headteacher_name": "",
            "headteacher_start_date": ".",
            "headteacher_tenure_years": "SUPP",
            "leadership_turnover_score": "SUPP",
        },
        release_slug="2023-24",
        release_version_id="wf-rv-2024",
        file_id="wf-file-2024",
    )

    assert rejection is None
    assert normalized is not None
    assert normalized["pupil_teacher_ratio"] is None
    assert normalized["supply_staff_pct"] is None
    assert normalized["teachers_3plus_years_pct"] is None
    assert normalized["teacher_turnover_pct"] is None
    assert normalized["qts_pct"] is None
    assert normalized["qualifications_level6_plus_pct"] is None
    assert normalized["headteacher_name"] is None
    assert normalized["headteacher_start_date"] is None
    assert normalized["headteacher_tenure_years"] is None
    assert normalized["leadership_turnover_score"] is None


def test_normalize_row_rejects_invalid_values() -> None:
    normalized, rejection = contract.normalize_row(
        {
            "school_urn": "ABC",
            "time_period": "202324",
            "pupil_teacher_ratio": "16.3",
        },
        release_slug="2023-24",
        release_version_id="wf-rv-2024",
        file_id="wf-file-2024",
    )
    assert normalized is None
    assert rejection == "invalid_urn"

    normalized, rejection = contract.normalize_row(
        {
            "school_urn": "123456",
            "time_period": "bad-year",
            "pupil_teacher_ratio": "16.3",
        },
        release_slug="2023-24",
        release_version_id="wf-rv-2024",
        file_id="wf-file-2024",
    )
    assert normalized is None
    assert rejection == "invalid_academic_year"

    normalized, rejection = contract.normalize_row(
        {
            "school_urn": "123456",
            "time_period": "202324",
            "supply_teacher_pct": "101.0",
        },
        release_slug="2023-24",
        release_version_id="wf-rv-2024",
        file_id="wf-file-2024",
    )
    assert normalized is None
    assert rejection == "invalid_supply_staff_pct"


def test_normalize_row_derives_metrics_from_size_workforce_counts() -> None:
    normalized, rejection = contract.normalize_row(
        {
            "school_urn": "123456",
            "time_period": "202324",
            "hc_all_teachers": "50",
            "hc_all_teachers_without_qts": "5",
            "hc_occasional_teachers": "2",
        },
        release_slug="2023",
        release_version_id="wf-rv-2024",
        file_id="wf-file-2024",
    )

    assert rejection is None
    assert normalized is not None
    assert normalized["academic_year"] == "2023/24"
    assert normalized["supply_staff_pct"] == 4.0
    assert normalized["qts_pct"] == 90.0


def test_normalize_row_maps_ptr_alias_columns() -> None:
    normalized, rejection = contract.normalize_row(
        {
            "school_urn": "123456",
            "time_period": "202425",
            "pupil_to_qual_unqual_teacher_ratio": "17.2",
        },
        release_slug="2024",
        release_version_id="wf-rv-2025",
        file_id="wf-file-2025",
    )

    assert rejection is None
    assert normalized is not None
    assert normalized["academic_year"] == "2024/25"
    assert normalized["pupil_teacher_ratio"] == 17.2
