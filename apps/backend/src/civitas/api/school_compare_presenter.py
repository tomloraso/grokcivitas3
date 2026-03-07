from civitas.api.schemas.school_compare import (
    SchoolCompareBenchmarkResponse,
    SchoolCompareCellResponse,
    SchoolCompareResponse,
    SchoolCompareRowResponse,
    SchoolCompareSchoolResponse,
    SchoolCompareSectionResponse,
)
from civitas.application.school_compare.dto import SchoolCompareResponseDto


def to_school_compare_response(result: SchoolCompareResponseDto) -> SchoolCompareResponse:
    return SchoolCompareResponse(
        schools=[
            SchoolCompareSchoolResponse(
                urn=school.urn,
                name=school.name,
                postcode=school.postcode,
                phase=school.phase,
                type=school.school_type,
                age_range_label=school.age_range_label,
            )
            for school in result.schools
        ],
        sections=[
            SchoolCompareSectionResponse(
                key=section.key,
                label=section.label,
                rows=[
                    SchoolCompareRowResponse(
                        metric_key=row.metric_key,
                        label=row.label,
                        unit=row.unit,
                        cells=[
                            SchoolCompareCellResponse(
                                urn=cell.urn,
                                value_text=cell.value_text,
                                value_numeric=cell.value_numeric,
                                year_label=cell.year_label,
                                snapshot_date=cell.snapshot_date,
                                availability=cell.availability,
                                completeness_status=cell.completeness_status,
                                completeness_reason_code=cell.completeness_reason_code,
                                benchmark=(
                                    SchoolCompareBenchmarkResponse(
                                        academic_year=cell.benchmark.academic_year,
                                        school_value=cell.benchmark.school_value,
                                        national_value=cell.benchmark.national_value,
                                        local_value=cell.benchmark.local_value,
                                        school_vs_national_delta=(
                                            cell.benchmark.school_vs_national_delta
                                        ),
                                        school_vs_local_delta=(
                                            cell.benchmark.school_vs_local_delta
                                        ),
                                        local_scope=cell.benchmark.local_scope,
                                        local_area_code=cell.benchmark.local_area_code,
                                        local_area_label=cell.benchmark.local_area_label,
                                    )
                                    if cell.benchmark is not None
                                    else None
                                ),
                            )
                            for cell in row.cells
                        ],
                    )
                    for row in section.rows
                ],
            )
            for section in result.sections
        ],
    )
