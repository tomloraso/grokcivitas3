from civitas.api.schemas.subject_performance import (
    SchoolSubjectPerformanceGroupRowResponse,
    SchoolSubjectPerformanceLatestResponse,
    SchoolSubjectPerformanceSeriesResponse,
    SchoolSubjectSummaryResponse,
)
from civitas.application.subject_performance.dto import (
    SchoolSubjectPerformanceLatestDto,
    SchoolSubjectPerformanceSeriesDto,
    SchoolSubjectSummaryDto,
)


def to_subject_performance_latest_response(
    value: SchoolSubjectPerformanceLatestDto | None,
) -> SchoolSubjectPerformanceLatestResponse | None:
    if value is None:
        return None
    return SchoolSubjectPerformanceLatestResponse(
        strongest_subjects=[
            _to_subject_summary_response(item) for item in value.strongest_subjects
        ],
        weakest_subjects=[_to_subject_summary_response(item) for item in value.weakest_subjects],
        stage_breakdowns=[
            SchoolSubjectPerformanceGroupRowResponse(
                academic_year=row.academic_year,
                key_stage=row.key_stage,
                qualification_family=row.qualification_family,
                exam_cohort=row.exam_cohort,
                subjects=[_to_subject_summary_response(item) for item in row.subjects],
            )
            for row in value.stage_breakdowns
        ],
        latest_updated_at=value.latest_updated_at,
    )


def to_subject_performance_series_response(
    value: SchoolSubjectPerformanceSeriesDto | None,
) -> SchoolSubjectPerformanceSeriesResponse | None:
    if value is None:
        return None
    return SchoolSubjectPerformanceSeriesResponse(
        rows=[
            SchoolSubjectPerformanceGroupRowResponse(
                academic_year=row.academic_year,
                key_stage=row.key_stage,
                qualification_family=row.qualification_family,
                exam_cohort=row.exam_cohort,
                subjects=[_to_subject_summary_response(item) for item in row.subjects],
            )
            for row in value.rows
        ],
        latest_updated_at=value.latest_updated_at,
    )


def _to_subject_summary_response(value: SchoolSubjectSummaryDto) -> SchoolSubjectSummaryResponse:
    return SchoolSubjectSummaryResponse(
        academic_year=value.academic_year,
        key_stage=value.key_stage,
        qualification_family=value.qualification_family,
        exam_cohort=value.exam_cohort,
        subject=value.subject,
        source_version=value.source_version,
        entries_count_total=value.entries_count_total,
        high_grade_count=value.high_grade_count,
        high_grade_share_pct=value.high_grade_share_pct,
        pass_grade_count=value.pass_grade_count,
        pass_grade_share_pct=value.pass_grade_share_pct,
        ranking_eligible=value.ranking_eligible,
    )
