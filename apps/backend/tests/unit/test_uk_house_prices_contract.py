from __future__ import annotations

import pytest

from civitas.infrastructure.pipelines.contracts import uk_house_prices as contract


def test_validate_headers_accepts_required_columns() -> None:
    contract.validate_headers(
        (
            contract.DATE_HEADER,
            contract.AREA_NAME_HEADER,
            contract.AREA_CODE_HEADER,
            contract.AVERAGE_PRICE_HEADER,
            contract.MONTHLY_CHANGE_HEADER,
            contract.ANNUAL_CHANGE_HEADER,
            "Extra_Column",
        )
    )


def test_validate_headers_rejects_missing_required_column() -> None:
    with pytest.raises(ValueError, match="missing required headers: Average_Price"):
        contract.validate_headers(
            (
                contract.DATE_HEADER,
                contract.AREA_NAME_HEADER,
                contract.AREA_CODE_HEADER,
                contract.MONTHLY_CHANGE_HEADER,
                contract.ANNUAL_CHANGE_HEADER,
            )
        )


def test_normalize_row_maps_fields() -> None:
    normalized, rejection = contract.normalize_row(
        {
            contract.DATE_HEADER: "2026-01-01",
            contract.AREA_NAME_HEADER: "Westminster",
            contract.AREA_CODE_HEADER: "E09000033",
            contract.AVERAGE_PRICE_HEADER: "810,000.0",
            contract.MONTHLY_CHANGE_HEADER: "0.5",
            contract.ANNUAL_CHANGE_HEADER: "6.0",
        }
    )

    assert rejection is None
    assert normalized is not None
    assert normalized["month"].isoformat() == "2026-01-01"
    assert normalized["area_name"] == "Westminster"
    assert normalized["area_code"] == "E09000033"
    assert normalized["average_price"] == pytest.approx(810000.0)
    assert normalized["monthly_change_pct"] == pytest.approx(0.5)
    assert normalized["annual_change_pct"] == pytest.approx(6.0)


def test_normalize_row_maps_optional_null_tokens() -> None:
    normalized, rejection = contract.normalize_row(
        {
            contract.DATE_HEADER: "2026-01-01",
            contract.AREA_NAME_HEADER: "Westminster",
            contract.AREA_CODE_HEADER: "E09000033",
            contract.AVERAGE_PRICE_HEADER: "810000",
            contract.MONTHLY_CHANGE_HEADER: "N/A",
            contract.ANNUAL_CHANGE_HEADER: ".",
        }
    )

    assert rejection is None
    assert normalized is not None
    assert normalized["monthly_change_pct"] is None
    assert normalized["annual_change_pct"] is None


@pytest.mark.parametrize(
    ("row", "expected_rejection"),
    [
        (
            {
                contract.DATE_HEADER: "2026-01-01",
                contract.AREA_NAME_HEADER: "Westminster",
                contract.AREA_CODE_HEADER: "",
                contract.AVERAGE_PRICE_HEADER: "810000",
                contract.MONTHLY_CHANGE_HEADER: "0.5",
                contract.ANNUAL_CHANGE_HEADER: "6.0",
            },
            "missing_area_code",
        ),
        (
            {
                contract.DATE_HEADER: "2026-01-01",
                contract.AREA_NAME_HEADER: "",
                contract.AREA_CODE_HEADER: "E09000033",
                contract.AVERAGE_PRICE_HEADER: "810000",
                contract.MONTHLY_CHANGE_HEADER: "0.5",
                contract.ANNUAL_CHANGE_HEADER: "6.0",
            },
            "missing_area_name",
        ),
        (
            {
                contract.DATE_HEADER: "2026/01/01",
                contract.AREA_NAME_HEADER: "Westminster",
                contract.AREA_CODE_HEADER: "E09000033",
                contract.AVERAGE_PRICE_HEADER: "810000",
                contract.MONTHLY_CHANGE_HEADER: "0.5",
                contract.ANNUAL_CHANGE_HEADER: "6.0",
            },
            "invalid_month",
        ),
        (
            {
                contract.DATE_HEADER: "2026-01-01",
                contract.AREA_NAME_HEADER: "Westminster",
                contract.AREA_CODE_HEADER: "E09000033",
                contract.AVERAGE_PRICE_HEADER: "-1",
                contract.MONTHLY_CHANGE_HEADER: "0.5",
                contract.ANNUAL_CHANGE_HEADER: "6.0",
            },
            "invalid_average_price",
        ),
        (
            {
                contract.DATE_HEADER: "2026-01-01",
                contract.AREA_NAME_HEADER: "Westminster",
                contract.AREA_CODE_HEADER: "E09000033",
                contract.AVERAGE_PRICE_HEADER: "810000",
                contract.MONTHLY_CHANGE_HEADER: "bad",
                contract.ANNUAL_CHANGE_HEADER: "6.0",
            },
            "invalid_monthly_change_pct",
        ),
        (
            {
                contract.DATE_HEADER: "2026-01-01",
                contract.AREA_NAME_HEADER: "Westminster",
                contract.AREA_CODE_HEADER: "E09000033",
                contract.AVERAGE_PRICE_HEADER: "810000",
                contract.MONTHLY_CHANGE_HEADER: "0.5",
                contract.ANNUAL_CHANGE_HEADER: "bad",
            },
            "invalid_annual_change_pct",
        ),
    ],
)
def test_normalize_row_rejects_invalid_rows(row: dict[str, str], expected_rejection: str) -> None:
    normalized, rejection = contract.normalize_row(row)

    assert normalized is None
    assert rejection == expected_rejection
