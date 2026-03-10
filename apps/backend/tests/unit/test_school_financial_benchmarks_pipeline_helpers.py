from __future__ import annotations

from openpyxl import Workbook

from civitas.infrastructure.pipelines.school_financial_benchmarks import (
    _worksheet_row_count,
    _worksheet_rows,
)


def test_worksheet_rows_skip_metadata_rows_before_headers() -> None:
    workbook = Workbook()
    worksheet = workbook.active
    worksheet.title = "Academies"
    worksheet.append([None] * 36 + ["BAI050 BAI010 BAI061 BAI020 BAI011"])
    worksheet.append(
        [
            "LAEstab",
            "LA",
            "Estab",
            "URN",
            "Academy UPIN",
            "School Name",
            "Number of pupils in academy (FTE)",
        ]
    )
    worksheet.append(
        [
            2022000,
            202,
            2000,
            136807,
            120536,
            "St Luke's Church of England School",
            98,
        ]
    )

    rows = _worksheet_rows(worksheet)

    assert _worksheet_row_count(worksheet) == 1
    assert rows == [
        {
            "LAEstab": 2022000,
            "LA": 202,
            "Estab": 2000,
            "URN": 136807,
            "Academy UPIN": 120536,
            "School Name": "St Luke's Church of England School",
            "Number of pupils in academy (FTE)": 98,
        }
    ]
