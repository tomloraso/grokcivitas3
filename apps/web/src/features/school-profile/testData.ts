import type {
  SchoolProfileResponse,
  SchoolTrendDashboardResponse,
  SchoolTrendsResponse
} from "../../api/types";

export const PROFILE_RESPONSE: SchoolProfileResponse = {
  school: {
    urn: "100001",
    name: "Camden Bridge Primary School",
    phase: "Primary",
    type: "Academy",
    status: "Open",
    postcode: "NW1 8NH",
    website: "https://www.camdenbridge.example",
    telephone: "+442079460001",
    head_title: "Dr",
    head_first_name: "Maya",
    head_last_name: "Patel",
    head_job_title: "Headteacher",
    address_street: "1 Bridge Street",
    address_locality: "Camden",
    address_line3: null,
    address_town: "London",
    address_county: "Greater London",
    statutory_low_age: 4,
    statutory_high_age: 11,
    gender: "Mixed",
    religious_character: "None",
    diocese: null,
    admissions_policy: "Not applicable",
    sixth_form: "Does not have a sixth form",
    nursery_provision: "Has nursery classes",
    boarders: "No boarders",
    fsm_pct_gias: 16.4,
    trust_name: "Camden Learning Trust",
    trust_flag: "Single-academy trust",
    federation_name: null,
    federation_flag: "Not applicable",
    la_name: "Camden",
    la_code: "202",
    urban_rural: "Urban major conurbation",
    number_of_boys: 104,
    number_of_girls: 96,
    lsoa_code: "E01004736",
    lsoa_name: "Camden 018A",
    last_changed_date: "2026-01-14",
    lat: 51.5424,
    lng: -0.1418
  },
  saved_state: {
    status: "not_saved",
    saved_at: null,
    capability_key: null,
    reason_code: null
  },
  overview_text:
    "Camden Bridge Primary School is an open academy in Camden serving pupils aged 4 to 11. The latest published profile shows a mixed intake, nursery provision, and a setting in an urban major conurbation. Recent demographics indicate moderate disadvantage and SEND levels, with a relatively low EHCP share and a modest proportion of pupils with English as an additional language. Attendance is strong against national patterns, while behaviour measures remain low. The latest Ofsted outcome is Good, and the school sits in a more deprived local area by IMD decile, which provides useful context for its published outcomes. Overall, the current dataset describes a mainstream primary school with stable profile indicators, a clear local catchment, and a broadly balanced intake.",
  analyst: {
    access: {
      state: "available",
      capability_key: "premium_ai_analyst",
      reason_code: null,
      product_codes: [],
      requires_auth: false,
      requires_purchase: false,
      school_name: null,
    },
    text:
      "The published profile points to a school with more stability than volatility across the current evidence base. Demographic measures suggest a mixed but not extreme level of disadvantage, while attendance remains strong and behaviour indicators stay low in the latest available year. Ofsted and the broader profile appear aligned rather than contradictory, which reduces the sense of a major unresolved quality gap in the current dataset. The deprivation context is still relevant, but the school's published indicators suggest it is operating with reasonable consistency against that backdrop.",
    teaser_text: null,
    disclaimer:
      "This analyst view is AI-generated from public government data. It highlights patterns in the published evidence, but it is not official advice or a recommendation.",
  },
  demographics_latest: {
    academic_year: "2024/25",
    disadvantaged_pct: 17.2,
    fsm_pct: 16.9,
    fsm6_pct: 19.4,
    sen_pct: 13.0,
    ehcp_pct: 2.1,
    eal_pct: 8.4,
    first_language_english_pct: 90.6,
    first_language_unclassified_pct: 1.0,
    male_pct: 51.2,
    female_pct: 48.8,
    pupil_mobility_pct: null,
    coverage: {
      fsm_supported: true,
      fsm6_supported: true,
      gender_supported: true,
      mobility_supported: false,
      send_primary_need_supported: true,
      ethnicity_supported: true,
      top_languages_supported: false
    },
    ethnicity_breakdown: [
      {
        key: "white_british",
        label: "White British",
        percentage: 49.0,
        count: 98
      },
      {
        key: "indian",
        label: "Indian",
        percentage: 7.0,
        count: 14
      }
    ],
    send_primary_needs: [
      {
        key: "autistic_spectrum_disorder",
        label: "Autistic spectrum disorder",
        percentage: 2.8,
        count: 8
      },
      {
        key: "social_emotional_and_mental_health",
        label: "Social, emotional and mental health",
        percentage: 1.1,
        count: 3
      }
    ],
    top_home_languages: []
  },
  attendance_latest: {
    academic_year: "2024/25",
    overall_attendance_pct: 94.7,
    overall_absence_pct: 5.3,
    persistent_absence_pct: 13.5
  },
  behaviour_latest: {
    academic_year: "2024/25",
    suspensions_count: 3,
    suspensions_rate: 0.9,
    permanent_exclusions_count: 0,
    permanent_exclusions_rate: 0.0
  },
  workforce_latest: {
    academic_year: "2024/25",
    pupil_teacher_ratio: 16.7,
    supply_staff_pct: 5.2,
    teachers_3plus_years_pct: null,
    teacher_turnover_pct: null,
    qts_pct: 91.3,
    qualifications_level6_plus_pct: null
  },
  finance_latest: {
    academic_year: "2023/24",
    total_income_gbp: 2070000,
    total_expenditure_gbp: 1980000,
    income_per_pupil_gbp: 10350,
    expenditure_per_pupil_gbp: 9900,
    total_staff_costs_gbp: 1432000,
    staff_costs_pct_of_expenditure: 72.3,
    revenue_reserve_gbp: 182000,
    revenue_reserve_per_pupil_gbp: 910
  },
  leadership_snapshot: {
    headteacher_name: "A. Smith",
    headteacher_start_date: "2021-09-01",
    headteacher_tenure_years: 4.5,
    leadership_turnover_score: 0.34
  },
  performance: {
    latest: {
      academic_year: "2024/25",
      attainment8_average: 47.2,
      progress8_average: 0.11,
      progress8_disadvantaged: -0.12,
      progress8_not_disadvantaged: 0.21,
      progress8_disadvantaged_gap: -0.33,
      engmath_5_plus_pct: 52.3,
      engmath_4_plus_pct: 71.4,
      ebacc_entry_pct: 36.2,
      ebacc_5_plus_pct: 25.5,
      ebacc_4_plus_pct: 31.3,
      ks2_reading_expected_pct: 74.1,
      ks2_writing_expected_pct: 72.8,
      ks2_maths_expected_pct: 75.4,
      ks2_combined_expected_pct: 68.9,
      ks2_reading_higher_pct: 21.3,
      ks2_writing_higher_pct: 19.4,
      ks2_maths_higher_pct: 23.7,
      ks2_combined_higher_pct: 16.8
    },
    history: [
      {
        academic_year: "2023/24",
        attainment8_average: 46.1,
        progress8_average: 0.05,
        progress8_disadvantaged: -0.19,
        progress8_not_disadvantaged: 0.16,
        progress8_disadvantaged_gap: -0.35,
        engmath_5_plus_pct: 50.1,
        engmath_4_plus_pct: 69.8,
        ebacc_entry_pct: 35.0,
        ebacc_5_plus_pct: 24.2,
        ebacc_4_plus_pct: 30.1,
        ks2_reading_expected_pct: 73.2,
        ks2_writing_expected_pct: 71.9,
        ks2_maths_expected_pct: 74.5,
        ks2_combined_expected_pct: 67.8,
        ks2_reading_higher_pct: 20.8,
        ks2_writing_higher_pct: 18.7,
        ks2_maths_higher_pct: 22.6,
        ks2_combined_higher_pct: 15.9
      },
      {
        academic_year: "2024/25",
        attainment8_average: 47.2,
        progress8_average: 0.11,
        progress8_disadvantaged: -0.12,
        progress8_not_disadvantaged: 0.21,
        progress8_disadvantaged_gap: -0.33,
        engmath_5_plus_pct: 52.3,
        engmath_4_plus_pct: 71.4,
        ebacc_entry_pct: 36.2,
        ebacc_5_plus_pct: 25.5,
        ebacc_4_plus_pct: 31.3,
        ks2_reading_expected_pct: 74.1,
        ks2_writing_expected_pct: 72.8,
        ks2_maths_expected_pct: 75.4,
        ks2_combined_expected_pct: 68.9,
        ks2_reading_higher_pct: 21.3,
        ks2_writing_higher_pct: 19.4,
        ks2_maths_higher_pct: 23.7,
        ks2_combined_higher_pct: 16.8
      }
    ]
  },
  ofsted_latest: {
    overall_effectiveness_code: "2",
    overall_effectiveness_label: "Good",
    inspection_start_date: "2025-10-10",
    publication_date: "2025-11-15",
    latest_oeif_inspection_start_date: "2025-10-10",
    latest_oeif_publication_date: "2025-11-15",
    quality_of_education_code: "2",
    quality_of_education_label: "Good",
    behaviour_and_attitudes_code: "2",
    behaviour_and_attitudes_label: "Good",
    personal_development_code: "2",
    personal_development_label: "Good",
    leadership_and_management_code: "2",
    leadership_and_management_label: "Good",
    latest_ungraded_inspection_date: "2026-01-02",
    latest_ungraded_publication_date: "2026-01-20",
    most_recent_inspection_date: "2026-01-02",
    days_since_most_recent_inspection: 61,
    is_graded: true,
    ungraded_outcome: null,
    provider_page_url: "https://reports.ofsted.gov.uk/provider/21/100001"
  },
  ofsted_timeline: {
    events: [
      {
        inspection_number: "10426708",
        inspection_start_date: "2024-01-10",
        publication_date: "2024-02-03",
        inspection_type: "Section 5",
        overall_effectiveness_label: "Good",
        headline_outcome_text: null,
        category_of_concern: null
      },
      {
        inspection_number: "10426709",
        inspection_start_date: "2025-11-11",
        publication_date: "2026-01-11",
        inspection_type: "Section 8",
        overall_effectiveness_label: null,
        headline_outcome_text: "Strong standard",
        category_of_concern: null
      }
    ],
    coverage: {
      is_partial_history: false,
      earliest_event_date: "2015-09-14",
      latest_event_date: "2026-01-15",
      events_count: 9
    }
  },
  neighbourhood: {
    access: {
      state: "available",
      capability_key: "premium_neighbourhood",
      reason_code: null,
      product_codes: [],
      requires_auth: false,
      requires_purchase: false,
      school_name: null,
    },
    area_context: {
      deprivation: {
        lsoa_code: "E01004736",
        imd_score: 22.4,
        imd_rank: 10234,
        imd_decile: 3,
        idaci_score: 0.241,
        idaci_decile: 2,
        income_score: 0.19,
        income_rank: 9500,
        income_decile: 3,
        employment_score: 0.13,
        employment_rank: 10100,
        employment_decile: 4,
        education_score: 12.5,
        education_rank: 8800,
        education_decile: 3,
        health_score: 0.56,
        health_rank: 9900,
        health_decile: 4,
        crime_score: 0.44,
        crime_rank: 7600,
        crime_decile: 3,
        barriers_score: 24.3,
        barriers_rank: 7200,
        barriers_decile: 3,
        living_environment_score: 30.1,
        living_environment_rank: 6800,
        living_environment_decile: 2,
        population_total: 1198,
        local_authority_district_code: "E09000007",
        local_authority_district_name: "Camden",
        source_release: "IoD2025"
      },
      crime: {
        radius_miles: 1.0,
        latest_month: "2026-01",
        total_incidents: 486,
        population_denominator: 1198,
        incidents_per_1000: 405.7,
        annual_incidents_per_1000: [
          {
            year: 2024,
            total_incidents: 5200,
            incidents_per_1000: 4339.0
          },
          {
            year: 2025,
            total_incidents: 4910,
            incidents_per_1000: 4098.5
          },
          {
            year: 2026,
            total_incidents: 486,
            incidents_per_1000: 405.7
          }
        ],
        categories: [
          {
            category: "Violent Crime",
            incident_count: 132
          },
          {
            category: "Anti-social Behaviour",
            incident_count: 97
          }
        ]
      },
      house_prices: {
        area_code: "E09000007",
        area_name: "Camden",
        latest_month: "2025-12",
        average_price: 783812,
        annual_change_pct: -11.1,
        monthly_change_pct: -1.1,
        three_year_change_pct: -8.98,
        trend: [
          {
            month: "2025-10",
            average_price: 831422,
            annual_change_pct: -2.5,
            monthly_change_pct: -4.7
          },
          {
            month: "2025-11",
            average_price: 792240,
            annual_change_pct: -8.8,
            monthly_change_pct: -4.7
          },
          {
            month: "2025-12",
            average_price: 783812,
            annual_change_pct: -11.1,
            monthly_change_pct: -1.1
          }
        ]
      },
      coverage: {
        has_deprivation: true,
        has_crime: true,
        crime_months_available: 36,
        has_house_prices: true,
        house_price_months_available: 372
      }
    },
    teaser_text: null
  },
  benchmarks: {
    metrics: [
      {
        metric_key: "disadvantaged_pct",
        academic_year: "2024/25",
        school_value: 17.2,
        national_value: 23.8,
        local_value: 18.1,
        school_vs_national_delta: -6.6,
        school_vs_local_delta: -0.9,
        local_scope: "local_authority_district",
        local_area_code: "E09000007",
        local_area_label: "Camden"
      },
      {
        metric_key: "overall_attendance_pct",
        academic_year: "2024/25",
        school_value: 94.7,
        national_value: 92.9,
        local_value: 93.1,
        school_vs_national_delta: 1.8,
        school_vs_local_delta: 1.6,
        local_scope: "local_authority_district",
        local_area_code: "E09000007",
        local_area_label: "Camden"
      },
      {
        metric_key: "suspensions_rate",
        academic_year: "2024/25",
        school_value: 0.9,
        national_value: 1.4,
        local_value: 1.2,
        school_vs_national_delta: -0.5,
        school_vs_local_delta: -0.3,
        local_scope: "local_authority_district",
        local_area_code: "E09000007",
        local_area_label: "Camden"
      },
      {
        metric_key: "pupil_teacher_ratio",
        academic_year: "2024/25",
        school_value: 16.7,
        national_value: 17.3,
        local_value: 16.9,
        school_vs_national_delta: -0.6,
        school_vs_local_delta: -0.2,
        local_scope: "local_authority_district",
        local_area_code: "E09000007",
        local_area_label: "Camden"
      },
      {
        metric_key: "income_per_pupil_gbp",
        academic_year: "2023/24",
        school_value: 10350,
        national_value: 8760,
        local_value: 10010,
        school_vs_national_delta: 1590,
        school_vs_local_delta: 340,
        local_scope: "local_authority_district",
        local_area_code: "E09000007",
        local_area_label: "Camden"
      },
      {
        metric_key: "expenditure_per_pupil_gbp",
        academic_year: "2023/24",
        school_value: 9900,
        national_value: 8655,
        local_value: 9750,
        school_vs_national_delta: 1245,
        school_vs_local_delta: 150,
        local_scope: "local_authority_district",
        local_area_code: "E09000007",
        local_area_label: "Camden"
      },
      {
        metric_key: "staff_costs_pct_of_expenditure",
        academic_year: "2023/24",
        school_value: 72.3,
        national_value: 77.1,
        local_value: 74.8,
        school_vs_national_delta: -4.8,
        school_vs_local_delta: -2.5,
        local_scope: "local_authority_district",
        local_area_code: "E09000007",
        local_area_label: "Camden"
      },
      {
        metric_key: "revenue_reserve_per_pupil_gbp",
        academic_year: "2023/24",
        school_value: 910,
        national_value: 540,
        local_value: 780,
        school_vs_national_delta: 370,
        school_vs_local_delta: 130,
        local_scope: "local_authority_district",
        local_area_code: "E09000007",
        local_area_label: "Camden"
      },
      {
        metric_key: "teaching_staff_costs_per_pupil_gbp",
        academic_year: "2023/24",
        school_value: 6120,
        national_value: 5450,
        local_value: 5980,
        school_vs_national_delta: 670,
        school_vs_local_delta: 140,
        local_scope: "local_authority_district",
        local_area_code: "E09000007",
        local_area_label: "Camden"
      },
      {
        metric_key: "progress8_average",
        academic_year: "2024/25",
        school_value: 0.11,
        national_value: 0.02,
        local_value: 0.06,
        school_vs_national_delta: 0.09,
        school_vs_local_delta: 0.05,
        local_scope: "local_authority_district",
        local_area_code: "E09000007",
        local_area_label: "Camden"
      },
      {
        metric_key: "area_house_price_average",
        academic_year: "2025",
        school_value: 783812,
        national_value: 415212,
        local_value: 783812,
        school_vs_national_delta: 368600,
        school_vs_local_delta: 0,
        local_scope: "local_authority_district",
        local_area_code: "E09000007",
        local_area_label: "Camden"
      }
    ]
  },
  completeness: {
    demographics: {
      status: "partial",
      reason_code: "partial_metric_coverage",
      last_updated_at: "2026-01-31T09:00:00Z",
      years_available: ["2023/24", "2024/25"]
    },
    attendance: {
      status: "available",
      reason_code: null,
      last_updated_at: "2026-01-31T09:00:00Z",
      years_available: ["2023/24", "2024/25"]
    },
    behaviour: {
      status: "available",
      reason_code: null,
      last_updated_at: "2026-01-31T09:00:00Z",
      years_available: ["2023/24", "2024/25"]
    },
    workforce: {
      status: "partial",
      reason_code: "partial_metric_coverage",
      last_updated_at: "2026-01-31T09:00:00Z",
      years_available: ["2022/23", "2023/24", "2024/25"]
    },
    finance: {
      status: "available",
      reason_code: null,
      last_updated_at: "2026-01-31T09:00:00Z",
      years_available: ["2023/24"]
    },
    leadership: {
      status: "available",
      reason_code: null,
      last_updated_at: "2026-01-31T09:00:00Z",
      years_available: null
    },
    performance: {
      status: "partial",
      reason_code: "insufficient_years_published",
      last_updated_at: "2026-01-31T09:00:00Z",
      years_available: ["2023/24", "2024/25"]
    },
    ofsted_latest: {
      status: "available",
      reason_code: null,
      last_updated_at: "2026-01-20T10:00:00Z",
      years_available: null
    },
    ofsted_timeline: {
      status: "available",
      reason_code: null,
      last_updated_at: "2026-01-18T11:00:00Z",
      years_available: null
    },
    area_deprivation: {
      status: "available",
      reason_code: null,
      last_updated_at: "2026-01-10T12:00:00Z",
      years_available: null
    },
    area_crime: {
      status: "available",
      reason_code: null,
      last_updated_at: "2026-01-31T13:00:00Z",
      years_available: null
    },
    area_house_prices: {
      status: "available",
      reason_code: null,
      last_updated_at: "2026-01-31T13:00:00Z",
      years_available: ["2023", "2024", "2025"]
    }
  }
};

const EMPTY_SERIES: SchoolTrendsResponse["series"]["disadvantaged_pct"] = [];
const EMPTY_BENCHMARKS: SchoolTrendsResponse["benchmarks"]["disadvantaged_pct"] = [];

export const TRENDS_RESPONSE: SchoolTrendsResponse = {
  urn: "100001",
  years_available: ["2023/24", "2024/25"],
  history_quality: {
    is_partial_history: true,
    min_years_for_delta: 2,
    years_count: 2
  },
  series: {
    disadvantaged_pct: [
      { academic_year: "2023/24", value: 16.0, delta: null, direction: null },
      { academic_year: "2024/25", value: 17.2, delta: 1.2, direction: "up" }
    ],
    fsm_pct: [
      { academic_year: "2023/24", value: 15.4, delta: null, direction: null },
      { academic_year: "2024/25", value: 16.9, delta: 1.5, direction: "up" }
    ],
    fsm6_pct: [
      { academic_year: "2023/24", value: 18.7, delta: null, direction: null },
      { academic_year: "2024/25", value: 19.4, delta: 0.7, direction: "up" }
    ],
    sen_pct: [
      { academic_year: "2023/24", value: 12.5, delta: null, direction: null },
      { academic_year: "2024/25", value: 13.0, delta: 0.5, direction: "up" }
    ],
    ehcp_pct: [{ academic_year: "2024/25", value: 2.1, delta: null, direction: null }],
    eal_pct: [{ academic_year: "2024/25", value: 8.4, delta: null, direction: null }],
    first_language_english_pct: [
      { academic_year: "2023/24", value: 89.9, delta: null, direction: null },
      { academic_year: "2024/25", value: 90.6, delta: 0.7, direction: "up" }
    ],
    first_language_unclassified_pct: [
      { academic_year: "2023/24", value: 0.6, delta: null, direction: null },
      { academic_year: "2024/25", value: 1.0, delta: 0.4, direction: "up" }
    ],
    male_pct: [
      { academic_year: "2023/24", value: 50.8, delta: null, direction: null },
      { academic_year: "2024/25", value: 51.2, delta: 0.4, direction: "up" }
    ],
    female_pct: [
      { academic_year: "2023/24", value: 49.2, delta: null, direction: null },
      { academic_year: "2024/25", value: 48.8, delta: -0.4, direction: "down" }
    ],
    pupil_mobility_pct: EMPTY_SERIES,
    overall_attendance_pct: [
      { academic_year: "2023/24", value: 94.1, delta: null, direction: null },
      { academic_year: "2024/25", value: 94.7, delta: 0.6, direction: "up" }
    ],
    overall_absence_pct: [
      { academic_year: "2023/24", value: 5.9, delta: null, direction: null },
      { academic_year: "2024/25", value: 5.3, delta: -0.6, direction: "down" }
    ],
    persistent_absence_pct: [
      { academic_year: "2023/24", value: 14.1, delta: null, direction: null },
      { academic_year: "2024/25", value: 13.5, delta: -0.6, direction: "down" }
    ],
    suspensions_count: [
      { academic_year: "2023/24", value: 2, delta: null, direction: null },
      { academic_year: "2024/25", value: 3, delta: 1, direction: "up" }
    ],
    suspensions_rate: [
      { academic_year: "2023/24", value: 0.6, delta: null, direction: null },
      { academic_year: "2024/25", value: 0.9, delta: 0.3, direction: "up" }
    ],
    permanent_exclusions_count: [
      { academic_year: "2023/24", value: 0, delta: null, direction: null },
      { academic_year: "2024/25", value: 0, delta: 0, direction: "flat" }
    ],
    permanent_exclusions_rate: [
      { academic_year: "2023/24", value: 0, delta: null, direction: null },
      { academic_year: "2024/25", value: 0, delta: 0, direction: "flat" }
    ],
    pupil_teacher_ratio: [
      { academic_year: "2023/24", value: 17.0, delta: null, direction: null },
      { academic_year: "2024/25", value: 16.7, delta: -0.3, direction: "down" }
    ],
    supply_staff_pct: [
      { academic_year: "2023/24", value: 4.8, delta: null, direction: null },
      { academic_year: "2024/25", value: 5.2, delta: 0.4, direction: "up" }
    ],
    teachers_3plus_years_pct: EMPTY_SERIES,
    teacher_turnover_pct: EMPTY_SERIES,
    qts_pct: [
      { academic_year: "2023/24", value: 90.8, delta: null, direction: null },
      { academic_year: "2024/25", value: 91.3, delta: 0.5, direction: "up" }
    ],
    qualifications_level6_plus_pct: EMPTY_SERIES,
    income_per_pupil_gbp: [
      { academic_year: "2023/24", value: 10350, delta: null, direction: null }
    ],
    expenditure_per_pupil_gbp: [
      { academic_year: "2023/24", value: 9900, delta: null, direction: null }
    ],
    staff_costs_pct_of_expenditure: [
      { academic_year: "2023/24", value: 72.3, delta: null, direction: null }
    ],
    revenue_reserve_per_pupil_gbp: [
      { academic_year: "2023/24", value: 910, delta: null, direction: null }
    ],
    teaching_staff_costs_per_pupil_gbp: [
      { academic_year: "2023/24", value: 6120, delta: null, direction: null }
    ]
  },
  benchmarks: {
    disadvantaged_pct: [
      {
        academic_year: "2024/25",
        school_value: 17.2,
        national_value: 23.8,
        local_value: 18.1,
        school_vs_national_delta: -6.6,
        school_vs_local_delta: -0.9,
        local_scope: "local_authority_district",
        local_area_code: "E09000007",
        local_area_label: "Camden"
      }
    ],
    fsm_pct: EMPTY_BENCHMARKS,
    fsm6_pct: EMPTY_BENCHMARKS,
    sen_pct: EMPTY_BENCHMARKS,
    ehcp_pct: EMPTY_BENCHMARKS,
    eal_pct: EMPTY_BENCHMARKS,
    first_language_english_pct: EMPTY_BENCHMARKS,
    first_language_unclassified_pct: EMPTY_BENCHMARKS,
    male_pct: EMPTY_BENCHMARKS,
    female_pct: EMPTY_BENCHMARKS,
    pupil_mobility_pct: EMPTY_BENCHMARKS,
    overall_attendance_pct: [
      {
        academic_year: "2024/25",
        school_value: 94.7,
        national_value: 92.9,
        local_value: 93.1,
        school_vs_national_delta: 1.8,
        school_vs_local_delta: 1.6,
        local_scope: "local_authority_district",
        local_area_code: "E09000007",
        local_area_label: "Camden"
      }
    ],
    overall_absence_pct: EMPTY_BENCHMARKS,
    persistent_absence_pct: EMPTY_BENCHMARKS,
    suspensions_count: EMPTY_BENCHMARKS,
    suspensions_rate: EMPTY_BENCHMARKS,
    permanent_exclusions_count: EMPTY_BENCHMARKS,
    permanent_exclusions_rate: EMPTY_BENCHMARKS,
    pupil_teacher_ratio: EMPTY_BENCHMARKS,
    supply_staff_pct: EMPTY_BENCHMARKS,
    teachers_3plus_years_pct: EMPTY_BENCHMARKS,
    teacher_turnover_pct: EMPTY_BENCHMARKS,
    qts_pct: EMPTY_BENCHMARKS,
    qualifications_level6_plus_pct: EMPTY_BENCHMARKS,
    income_per_pupil_gbp: [
      {
        academic_year: "2023/24",
        school_value: 10350,
        national_value: 8760,
        local_value: 10010,
        school_vs_national_delta: 1590,
        school_vs_local_delta: 340,
        local_scope: "local_authority_district",
        local_area_code: "E09000007",
        local_area_label: "Camden"
      }
    ],
    expenditure_per_pupil_gbp: [
      {
        academic_year: "2023/24",
        school_value: 9900,
        national_value: 8655,
        local_value: 9750,
        school_vs_national_delta: 1245,
        school_vs_local_delta: 150,
        local_scope: "local_authority_district",
        local_area_code: "E09000007",
        local_area_label: "Camden"
      }
    ],
    staff_costs_pct_of_expenditure: [
      {
        academic_year: "2023/24",
        school_value: 72.3,
        national_value: 77.1,
        local_value: 74.8,
        school_vs_national_delta: -4.8,
        school_vs_local_delta: -2.5,
        local_scope: "local_authority_district",
        local_area_code: "E09000007",
        local_area_label: "Camden"
      }
    ],
    revenue_reserve_per_pupil_gbp: [
      {
        academic_year: "2023/24",
        school_value: 910,
        national_value: 540,
        local_value: 780,
        school_vs_national_delta: 370,
        school_vs_local_delta: 130,
        local_scope: "local_authority_district",
        local_area_code: "E09000007",
        local_area_label: "Camden"
      }
    ],
    teaching_staff_costs_per_pupil_gbp: [
      {
        academic_year: "2023/24",
        school_value: 6120,
        national_value: 5450,
        local_value: 5980,
        school_vs_national_delta: 670,
        school_vs_local_delta: 140,
        local_scope: "local_authority_district",
        local_area_code: "E09000007",
        local_area_label: "Camden"
      }
    ]
  },
  completeness: {
    status: "partial",
    reason_code: "insufficient_years_published",
    last_updated_at: "2026-01-31T09:00:00Z",
    years_available: ["2023/24", "2024/25"]
  },
  section_completeness: {
    demographics: {
      status: "partial",
      reason_code: "partial_metric_coverage",
      last_updated_at: "2026-01-31T09:00:00Z",
      years_available: ["2023/24", "2024/25"]
    },
    attendance: {
      status: "available",
      reason_code: null,
      last_updated_at: "2026-01-31T09:00:00Z",
      years_available: ["2023/24", "2024/25"]
    },
    behaviour: {
      status: "available",
      reason_code: null,
      last_updated_at: "2026-01-31T09:00:00Z",
      years_available: ["2023/24", "2024/25"]
    },
    workforce: {
      status: "partial",
      reason_code: "partial_metric_coverage",
      last_updated_at: "2026-01-31T09:00:00Z",
      years_available: ["2023/24", "2024/25"]
    },
    finance: {
      status: "partial",
      reason_code: "insufficient_years_published",
      last_updated_at: "2026-01-31T09:00:00Z",
      years_available: ["2023/24"]
    }
  }
};

export const DASHBOARD_RESPONSE: SchoolTrendDashboardResponse = {
  urn: "100001",
  years_available: ["2023/24", "2024/25"],
  sections: [
    {
      key: "demographics",
      metrics: [
        {
          metric_key: "disadvantaged_pct",
          label: "Disadvantaged Pupils (%)",
          unit: "percent",
          points: [
            {
              academic_year: "2023/24",
              school_value: 16,
              national_value: 23.5,
              local_value: 18.3,
              school_vs_national_delta: -7.5,
              school_vs_local_delta: -2.3,
              local_scope: "local_authority_district",
              local_area_code: "E09000007",
              local_area_label: "Camden"
            },
            {
              academic_year: "2024/25",
              school_value: 17.2,
              national_value: 23.8,
              local_value: 18.1,
              school_vs_national_delta: -6.6,
              school_vs_local_delta: -0.9,
              local_scope: "local_authority_district",
              local_area_code: "E09000007",
              local_area_label: "Camden"
            }
          ]
        }
      ]
    },
    {
      key: "finance",
      metrics: [
        {
          metric_key: "income_per_pupil_gbp",
          label: "Income per Pupil",
          unit: "currency",
          points: [
            {
              academic_year: "2023/24",
              school_value: 10350,
              national_value: 8760,
              local_value: 10010,
              school_vs_national_delta: 1590,
              school_vs_local_delta: 340,
              local_scope: "local_authority_district",
              local_area_code: "E09000007",
              local_area_label: "Camden"
            }
          ]
        },
        {
          metric_key: "expenditure_per_pupil_gbp",
          label: "Expenditure per Pupil",
          unit: "currency",
          points: [
            {
              academic_year: "2023/24",
              school_value: 9900,
              national_value: 8655,
              local_value: 9750,
              school_vs_national_delta: 1245,
              school_vs_local_delta: 150,
              local_scope: "local_authority_district",
              local_area_code: "E09000007",
              local_area_label: "Camden"
            }
          ]
        },
        {
          metric_key: "staff_costs_pct_of_expenditure",
          label: "Staff Costs Share of Expenditure",
          unit: "percent",
          points: [
            {
              academic_year: "2023/24",
              school_value: 72.3,
              national_value: 77.1,
              local_value: 74.8,
              school_vs_national_delta: -4.8,
              school_vs_local_delta: -2.5,
              local_scope: "local_authority_district",
              local_area_code: "E09000007",
              local_area_label: "Camden"
            }
          ]
        },
        {
          metric_key: "revenue_reserve_per_pupil_gbp",
          label: "Revenue Reserve per Pupil",
          unit: "currency",
          points: [
            {
              academic_year: "2023/24",
              school_value: 910,
              national_value: 540,
              local_value: 780,
              school_vs_national_delta: 370,
              school_vs_local_delta: 130,
              local_scope: "local_authority_district",
              local_area_code: "E09000007",
              local_area_label: "Camden"
            }
          ]
        },
        {
          metric_key: "teaching_staff_costs_per_pupil_gbp",
          label: "Teaching Staff Costs per Pupil",
          unit: "currency",
          points: [
            {
              academic_year: "2023/24",
              school_value: 6120,
              national_value: 5450,
              local_value: 5980,
              school_vs_national_delta: 670,
              school_vs_local_delta: 140,
              local_scope: "local_authority_district",
              local_area_code: "E09000007",
              local_area_label: "Camden"
            }
          ]
        }
      ]
    },
    {
      key: "attendance",
      metrics: [
        {
          metric_key: "overall_attendance_pct",
          label: "Overall Attendance (%)",
          unit: "percent",
          points: [
            {
              academic_year: "2023/24",
              school_value: 94.1,
              national_value: 92.4,
              local_value: 92.9,
              school_vs_national_delta: 1.7,
              school_vs_local_delta: 1.2,
              local_scope: "local_authority_district",
              local_area_code: "E09000007",
              local_area_label: "Camden"
            },
            {
              academic_year: "2024/25",
              school_value: 94.7,
              national_value: 92.9,
              local_value: 93.1,
              school_vs_national_delta: 1.8,
              school_vs_local_delta: 1.6,
              local_scope: "local_authority_district",
              local_area_code: "E09000007",
              local_area_label: "Camden"
            }
          ]
        }
      ]
    },
    {
      key: "behaviour",
      metrics: [
        {
          metric_key: "suspensions_rate",
          label: "Suspensions Rate",
          unit: "rate",
          points: [
            {
              academic_year: "2023/24",
              school_value: 0.6,
              national_value: 1.2,
              local_value: 1.0,
              school_vs_national_delta: -0.6,
              school_vs_local_delta: -0.4,
              local_scope: "local_authority_district",
              local_area_code: "E09000007",
              local_area_label: "Camden"
            },
            {
              academic_year: "2024/25",
              school_value: 0.9,
              national_value: 1.4,
              local_value: 1.2,
              school_vs_national_delta: -0.5,
              school_vs_local_delta: -0.3,
              local_scope: "local_authority_district",
              local_area_code: "E09000007",
              local_area_label: "Camden"
            }
          ]
        }
      ]
    },
    {
      key: "workforce",
      metrics: [
        {
          metric_key: "pupil_teacher_ratio",
          label: "Pupil to Teacher Ratio",
          unit: "ratio",
          points: [
            {
              academic_year: "2023/24",
              school_value: 17.0,
              national_value: 17.5,
              local_value: 17.1,
              school_vs_national_delta: -0.5,
              school_vs_local_delta: -0.1,
              local_scope: "local_authority_district",
              local_area_code: "E09000007",
              local_area_label: "Camden"
            },
            {
              academic_year: "2024/25",
              school_value: 16.7,
              national_value: 17.3,
              local_value: 16.9,
              school_vs_national_delta: -0.6,
              school_vs_local_delta: -0.2,
              local_scope: "local_authority_district",
              local_area_code: "E09000007",
              local_area_label: "Camden"
            }
          ]
        }
      ]
    },
    {
      key: "performance",
      metrics: [
        {
          metric_key: "progress8_average",
          label: "Progress 8",
          unit: "score",
          points: [
            {
              academic_year: "2023/24",
              school_value: 0.05,
              national_value: 0.01,
              local_value: 0.02,
              school_vs_national_delta: 0.04,
              school_vs_local_delta: 0.03,
              local_scope: "local_authority_district",
              local_area_code: "E09000007",
              local_area_label: "Camden"
            },
            {
              academic_year: "2024/25",
              school_value: 0.11,
              national_value: 0.02,
              local_value: 0.06,
              school_vs_national_delta: 0.09,
              school_vs_local_delta: 0.05,
              local_scope: "local_authority_district",
              local_area_code: "E09000007",
              local_area_label: "Camden"
            }
          ]
        }
      ]
    },
    {
      key: "area",
      metrics: [
        {
          metric_key: "area_house_price_average",
          label: "Average House Price",
          unit: "currency",
          points: [
            {
              academic_year: "2024",
              school_value: 812500,
              national_value: 402000,
              local_value: 812500,
              school_vs_national_delta: 410500,
              school_vs_local_delta: 0,
              local_scope: "local_authority_district",
              local_area_code: "E09000007",
              local_area_label: "Camden"
            },
            {
              academic_year: "2025",
              school_value: 783812,
              national_value: 415212,
              local_value: 783812,
              school_vs_national_delta: 368600,
              school_vs_local_delta: 0,
              local_scope: "local_authority_district",
              local_area_code: "E09000007",
              local_area_label: "Camden"
            }
          ]
        }
      ]
    }
  ],
  completeness: {
    status: "partial",
    reason_code: "partial_metric_coverage",
    last_updated_at: "2026-01-31T09:00:00Z",
    years_available: ["2023/24", "2024/25"]
  }
};
