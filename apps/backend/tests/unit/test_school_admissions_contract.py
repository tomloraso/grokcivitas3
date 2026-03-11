from __future__ import annotations

from civitas.infrastructure.pipelines.contracts import school_admissions as contract


def test_normalize_row_maps_admissions_fields() -> None:
    normalized, rejection = contract.normalize_row(
        {
            "time_period": "202526",
            "time_identifier": "Academic year",
            "geographic_level": "School",
            "la_name": "Westminster",
            "school_phase": "Primary",
            "school_laestab_as_used": "2136007",
            "school_name": "Alpha Primary School",
            "total_number_places_offered": "60",
            "number_preferred_offers": "57",
            "number_1st_preference_offers": "49",
            "number_2nd_preference_offers": "6",
            "number_3rd_preference_offers": "2",
            "times_put_as_any_preferred_school": "95",
            "times_put_as_1st_preference": "72",
            "times_put_as_2nd_preference": "15",
            "times_put_as_3rd_preference": "8",
            "proportion_1stprefs_v_1stprefoffers": "1.4694",
            "proportion_1stprefs_v_totaloffers": "1.2000",
            "all_applications_from_another_LA": "33",
            "offers_to_applicants_from_another_LA": "18",
            "establishment_type": "Academy converter",
            "denomination": "None",
            "FSM_eligible_percent": "18.5",
            "admissions_policy": "Comprehensive",
            "urban_rural": "Urban major conurbation",
            "allthrough_school": "No",
            "school_urn": "100001",
            "entry_year": "R",
        },
        source_file_url="https://example.com/admissions.csv",
    )

    assert rejection is None
    assert normalized is not None
    assert normalized["academic_year"] == "2025/26"
    assert normalized["entry_year"] == "R"
    assert normalized["school_urn"] == "100001"
    assert normalized["school_laestab"] == "2136007"
    assert normalized["places_offered_total"] == 60
    assert normalized["preferred_offers_total"] == 57
    assert normalized["first_preference_offers"] == 49
    assert normalized["applications_any_preference"] == 95
    assert normalized["first_preference_application_to_offer_ratio"] == 1.4694
    assert normalized["fsm_eligible_pct"] == 18.5
    assert normalized["allthrough_school"] is False


def test_normalize_row_allows_missing_urn_when_laestab_present() -> None:
    normalized, rejection = contract.normalize_row(
        {
            "time_period": "202526",
            "time_identifier": "Academic year",
            "geographic_level": "School",
            "la_name": "Westminster",
            "school_phase": "Secondary",
            "school_laestab_as_used": "2013614",
            "school_name": "Beta School",
            "total_number_places_offered": "120",
            "number_preferred_offers": "115",
            "number_1st_preference_offers": "100",
            "number_2nd_preference_offers": "10",
            "number_3rd_preference_offers": "5",
            "times_put_as_any_preferred_school": "180",
            "times_put_as_1st_preference": "140",
            "times_put_as_2nd_preference": "25",
            "times_put_as_3rd_preference": "15",
            "proportion_1stprefs_v_1stprefoffers": "1.4",
            "proportion_1stprefs_v_totaloffers": "1.1667",
            "all_applications_from_another_LA": "12",
            "offers_to_applicants_from_another_LA": "7",
            "establishment_type": "Academy sponsor led",
            "denomination": "None",
            "FSM_eligible_percent": "22.0",
            "admissions_policy": "Selective",
            "urban_rural": "Urban city and town",
            "allthrough_school": "Yes",
            "school_urn": "",
            "entry_year": "7",
        },
        source_file_url="https://example.com/admissions.csv",
    )

    assert rejection is None
    assert normalized is not None
    assert normalized["school_urn"] is None
    assert normalized["allthrough_school"] is True


def test_normalize_row_rejects_invalid_identifiers_and_metrics() -> None:
    normalized, rejection = contract.normalize_row(
        {
            "time_period": "202526",
            "time_identifier": "Academic year",
            "geographic_level": "School",
            "la_name": "Westminster",
            "school_phase": "Primary",
            "school_laestab_as_used": "",
            "school_name": "Alpha Primary School",
            "total_number_places_offered": "60",
            "number_preferred_offers": "57",
            "number_1st_preference_offers": "49",
            "number_2nd_preference_offers": "6",
            "number_3rd_preference_offers": "2",
            "times_put_as_any_preferred_school": "95",
            "times_put_as_1st_preference": "72",
            "times_put_as_2nd_preference": "15",
            "times_put_as_3rd_preference": "8",
            "proportion_1stprefs_v_1stprefoffers": "1.4694",
            "proportion_1stprefs_v_totaloffers": "1.2000",
            "all_applications_from_another_LA": "33",
            "offers_to_applicants_from_another_LA": "18",
            "establishment_type": "Academy converter",
            "denomination": "None",
            "FSM_eligible_percent": "18.5",
            "admissions_policy": "Comprehensive",
            "urban_rural": "Urban major conurbation",
            "allthrough_school": "No",
            "school_urn": "ABC123",
            "entry_year": "R",
        },
        source_file_url="https://example.com/admissions.csv",
    )
    assert normalized is None
    assert rejection == "invalid_school_urn"

    normalized, rejection = contract.normalize_row(
        {
            "time_period": "202526",
            "time_identifier": "Academic year",
            "geographic_level": "School",
            "la_name": "Westminster",
            "school_phase": "Primary",
            "school_laestab_as_used": "2136007",
            "school_name": "Alpha Primary School",
            "total_number_places_offered": "-1",
            "number_preferred_offers": "57",
            "number_1st_preference_offers": "49",
            "number_2nd_preference_offers": "6",
            "number_3rd_preference_offers": "2",
            "times_put_as_any_preferred_school": "95",
            "times_put_as_1st_preference": "72",
            "times_put_as_2nd_preference": "15",
            "times_put_as_3rd_preference": "8",
            "proportion_1stprefs_v_1stprefoffers": "1.4694",
            "proportion_1stprefs_v_totaloffers": "1.2000",
            "all_applications_from_another_LA": "33",
            "offers_to_applicants_from_another_LA": "18",
            "establishment_type": "Academy converter",
            "denomination": "None",
            "FSM_eligible_percent": "18.5",
            "admissions_policy": "Comprehensive",
            "urban_rural": "Urban major conurbation",
            "allthrough_school": "No",
            "school_urn": "100001",
            "entry_year": "R",
        },
        source_file_url="https://example.com/admissions.csv",
    )
    assert normalized is None
    assert rejection == "invalid_integer"
