from __future__ import annotations

from civitas.infrastructure.pipelines.contracts import dfe_workforce as contract


def test_normalize_row_maps_legacy_workforce_fields() -> None:
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
    assert normalized["source_dataset_id"] == "workforce:wf-rv-2024"
    assert normalized["source_dataset_version"] == "workforce:wf-file-2024"


def test_normalize_row_handles_legacy_suppression_tokens() -> None:
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


def test_normalize_teacher_characteristics_row_maps_granular_fields() -> None:
    normalized, rejection = contract.normalize_teacher_characteristics_row(
        {
            "time_period": "202425",
            "school_urn": "123456",
            "school_laestab": "123/4567",
            "school_name": "Alpha School",
            "school_type": "Community school",
            "characteristic_group": "Grade",
            "characteristic": "Headteacher",
            "grade": "Headteacher",
            "sex": "Female",
            "age_group": "50 and over",
            "working_pattern": "Full-time",
            "qts_status": "Qualified teacher status",
            "on_route": "Not on route",
            "ethnicity_major": "White",
            "full_time_equivalent": "1.00",
            "headcount": "1",
            "fte_school_percent": "2.2",
            "headcount_school_percent": "2.0",
        },
        release_version_id="wf-rv-2025",
        file_id="teacher-characteristics",
    )

    assert rejection is None
    assert normalized is not None
    assert normalized["urn"] == "123456"
    assert normalized["academic_year"] == "2024/25"
    assert normalized["characteristic_group"] == "Grade"
    assert normalized["characteristic"] == "Headteacher"
    assert normalized["grade"] == "Headteacher"
    assert normalized["teacher_fte"] == 1.0
    assert normalized["teacher_headcount"] == 1.0
    assert normalized["teacher_fte_pct"] == 2.2
    assert normalized["teacher_headcount_pct"] == 2.0
    assert normalized["source_dataset_id"] == "workforce:wf-rv-2025"
    assert normalized["source_dataset_version"] == "workforce:teacher-characteristics"


def test_normalize_teacher_characteristics_row_handles_suppressed_values() -> None:
    normalized, rejection = contract.normalize_teacher_characteristics_row(
        {
            "time_period": "202425",
            "school_urn": "123456",
            "school_name": "Alpha School",
            "characteristic_group": "Sex",
            "characteristic": "Female",
            "full_time_equivalent": "c",
            "headcount": "u",
            "fte_school_percent": ".",
            "headcount_school_percent": "supp",
        },
        release_version_id="wf-rv-2025",
        file_id="teacher-characteristics",
    )

    assert rejection is None
    assert normalized is not None
    assert normalized["teacher_fte"] is None
    assert normalized["teacher_headcount"] is None
    assert normalized["teacher_fte_pct"] is None
    assert normalized["teacher_headcount_pct"] is None


def test_normalize_teacher_characteristics_row_repairs_shifted_numeric_columns() -> None:
    normalized, rejection = contract.normalize_teacher_characteristics_row(
        {
            "time_period": "202425",
            "school_urn": "123456",
            "school_laestab": "123/4567",
            "school_name": "Alpha School",
            "school_type": "Community school",
            "characteristic_group": "QTS status",
            "characteristic": "Qualified teacher status",
            "grade": "",
            "sex": "",
            "age_group": "",
            "working_pattern": "Qualified teacher status",
            "qts_status": "",
            "on_route": "",
            "ethnicity_major": "44",
            "full_time_equivalent": "48",
            "headcount": "95.7",
            "fte_school_percent": "96.0",
            "headcount_school_percent": "",
        },
        release_version_id="wf-rv-2025",
        file_id="teacher-characteristics",
    )

    assert rejection is None
    assert normalized is not None
    assert normalized["qts_status"] == "Qualified teacher status"
    assert normalized["working_pattern"] is None
    assert normalized["teacher_fte"] == 44.0
    assert normalized["teacher_headcount"] == 48.0
    assert normalized["teacher_fte_pct"] == 95.7
    assert normalized["teacher_headcount_pct"] == 96.0


def test_normalize_support_staff_characteristics_row_maps_staff_mix_fields() -> None:
    normalized, rejection = contract.normalize_support_staff_characteristics_row(
        {
            "time_period": "202425",
            "school_urn": "123456",
            "school_name": "Alpha School",
            "school_type": "Community school",
            "post": "Teaching assistants",
            "sex": "Female",
            "ethnicity_major": "White",
            "full_time_equivalent": "12.4",
            "headcount": "14",
        },
        release_version_id="wf-rv-2025",
        file_id="support-staff",
    )

    assert rejection is None
    assert normalized is not None
    assert normalized["academic_year"] == "2024/25"
    assert normalized["post"] == "Teaching assistants"
    assert normalized["support_staff_fte"] == 12.4
    assert normalized["support_staff_headcount"] == 14.0


def test_normalize_teacher_pay_row_maps_salary_metrics() -> None:
    normalized, rejection = contract.normalize_teacher_pay_row(
        {
            "time_period": "202425",
            "school_urn": "123456",
            "headcount_all": "48",
            "average_mean": "43562.7",
            "average_median": "42984.0",
            "teachers_on_leadership_pay_range_percent": "9.5",
        },
        release_version_id="wf-rv-2025",
        file_id="teacher-pay",
    )

    assert rejection is None
    assert normalized is not None
    assert normalized["academic_year"] == "2024/25"
    assert normalized["teacher_headcount_all"] == 48.0
    assert normalized["teacher_average_mean_salary_gbp"] == 43562.7
    assert normalized["teacher_average_median_salary_gbp"] == 42984.0
    assert normalized["teachers_on_leadership_pay_range_pct"] == 9.5


def test_normalize_teacher_absence_row_maps_absence_metrics() -> None:
    normalized, rejection = contract.normalize_teacher_absence_row(
        {
            "time_period": "202425",
            "school_urn": "123456",
            "total_teachers_taking_absence": "18",
            "percentage_taking_absence": "37.5",
            "total_number_of_days_lost": "124",
            "average_number_of_days_taken": "6.9",
            "average_number_of_days_all_teachers": "2.6",
        },
        release_version_id="wf-rv-2025",
        file_id="teacher-absence",
    )

    assert rejection is None
    assert normalized is not None
    assert normalized["teachers_taking_absence_count"] == 18.0
    assert normalized["teacher_absence_pct"] == 37.5
    assert normalized["teacher_absence_days_total"] == 124.0
    assert normalized["teacher_absence_days_average"] == 6.9
    assert normalized["teacher_absence_days_average_all_teachers"] == 2.6


def test_normalize_teacher_vacancy_row_maps_vacancy_metrics() -> None:
    normalized, rejection = contract.normalize_teacher_vacancy_row(
        {
            "time_period": "202425",
            "school_urn": "123456",
            "vacancy": "2",
            "rate": "4.0",
            "tempfilled": "1",
            "temprate": "2.0",
        },
        release_version_id="wf-rv-2025",
        file_id="teacher-vacancies",
    )

    assert rejection is None
    assert normalized is not None
    assert normalized["teacher_vacancy_count"] == 2.0
    assert normalized["teacher_vacancy_rate"] == 4.0
    assert normalized["teacher_tempfilled_vacancy_count"] == 1.0
    assert normalized["teacher_tempfilled_vacancy_rate"] == 2.0


def test_normalize_third_party_support_row_maps_external_staff_metrics() -> None:
    normalized, rejection = contract.normalize_third_party_support_row(
        {
            "time_period": "202425",
            "school_urn": "123456",
            "school_name": "Alpha School",
            "post": "Total",
            "headcount": "3",
        },
        release_version_id="wf-rv-2025",
        file_id="third-party-support",
    )

    assert rejection is None
    assert normalized is not None
    assert normalized["academic_year"] == "2024/25"
    assert normalized["post"] == "Total"
    assert normalized["headcount"] == 3.0
