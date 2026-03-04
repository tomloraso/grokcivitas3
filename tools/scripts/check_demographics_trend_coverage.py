"""Check demographics trend-depth coverage thresholds for open schools.

Run from repo root:
  uv run --project apps/backend python tools/scripts/check_demographics_trend_coverage.py --strict
"""

from __future__ import annotations

import argparse
import sys
from dataclasses import dataclass

from sqlalchemy import create_engine, text
from sqlalchemy.engine import Engine

from civitas.infrastructure.config.settings import AppSettings


@dataclass(frozen=True)
class CoverageThreshold:
    phase: str
    min_years: int
    min_ratio: float


@dataclass(frozen=True)
class PhaseCoverageStats:
    open_schools: int
    schools_with_2_plus_years: int
    schools_with_3_plus_years: int


@dataclass(frozen=True)
class CoverageResult:
    threshold: CoverageThreshold
    open_schools: int
    matching_schools: int
    ratio: float | None
    passed: bool


DEFAULT_THRESHOLDS: tuple[CoverageThreshold, ...] = (
    CoverageThreshold(phase="primary", min_years=2, min_ratio=0.90),
    CoverageThreshold(phase="secondary", min_years=2, min_ratio=0.90),
    CoverageThreshold(phase="primary", min_years=3, min_ratio=0.85),
    CoverageThreshold(phase="secondary", min_years=3, min_ratio=0.85),
)


def _parse_args(argv: list[str]) -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description="Check open-school demographics trend depth thresholds."
    )
    parser.add_argument(
        "--strict",
        action="store_true",
        help="Exit with status 1 when one or more thresholds fail.",
    )
    return parser.parse_args(argv)


def _database_engine() -> Engine:
    database_url = AppSettings().database.url
    if database_url.startswith("postgresql"):
        return create_engine(database_url, future=True, connect_args={"connect_timeout": 5})
    return create_engine(database_url, future=True)


def load_phase_coverage(engine: Engine) -> dict[str, PhaseCoverageStats]:
    statement = text(
        """
        WITH demographics_counts AS (
            SELECT
                schools.urn,
                lower(trim(coalesce(schools.phase, ''))) AS phase,
                COUNT(demographics.academic_year) AS years_count
            FROM schools
            LEFT JOIN school_demographics_yearly AS demographics
                ON demographics.urn = schools.urn
            WHERE lower(coalesce(schools.status, '')) = 'open'
            GROUP BY schools.urn, schools.phase
        )
        SELECT
            phase,
            COUNT(*) AS open_schools,
            SUM(CASE WHEN years_count >= 2 THEN 1 ELSE 0 END) AS schools_with_2_plus_years,
            SUM(CASE WHEN years_count >= 3 THEN 1 ELSE 0 END) AS schools_with_3_plus_years
        FROM demographics_counts
        WHERE phase IN ('primary', 'secondary')
        GROUP BY phase
        """
    )
    with engine.connect() as connection:
        rows = connection.execute(statement).mappings().all()

    results: dict[str, PhaseCoverageStats] = {}
    for row in rows:
        phase = str(row["phase"]).strip().casefold()
        if phase not in {"primary", "secondary"}:
            continue
        results[phase] = PhaseCoverageStats(
            open_schools=int(row["open_schools"]),
            schools_with_2_plus_years=int(row["schools_with_2_plus_years"]),
            schools_with_3_plus_years=int(row["schools_with_3_plus_years"]),
        )
    return results


def evaluate_thresholds(
    *,
    phase_stats: dict[str, PhaseCoverageStats],
    thresholds: tuple[CoverageThreshold, ...] = DEFAULT_THRESHOLDS,
) -> tuple[CoverageResult, ...]:
    results: list[CoverageResult] = []
    for threshold in thresholds:
        stats = phase_stats.get(threshold.phase)
        open_schools = 0 if stats is None else stats.open_schools
        if threshold.min_years >= 3:
            matching_schools = 0 if stats is None else stats.schools_with_3_plus_years
        else:
            matching_schools = 0 if stats is None else stats.schools_with_2_plus_years

        ratio: float | None = None
        passed = False
        if open_schools > 0:
            ratio = matching_schools / open_schools
            passed = ratio >= threshold.min_ratio

        results.append(
            CoverageResult(
                threshold=threshold,
                open_schools=open_schools,
                matching_schools=matching_schools,
                ratio=ratio,
                passed=passed,
            )
        )
    return tuple(results)


def main(argv: list[str] | None = None) -> int:
    args = _parse_args(argv or [])
    try:
        engine = _database_engine()
        phase_stats = load_phase_coverage(engine)
    finally:
        if "engine" in locals():
            engine.dispose()

    results = evaluate_thresholds(phase_stats=phase_stats)
    has_failures = False
    for result in results:
        ratio_text = "n/a" if result.ratio is None else f"{result.ratio * 100:.2f}%"
        target_text = f"{result.threshold.min_ratio * 100:.2f}%"
        status = "PASS" if result.passed else "FAIL"
        print(
            f"{result.threshold.phase} >= {result.threshold.min_years} years: "
            f"{result.matching_schools}/{result.open_schools} ({ratio_text}) "
            f"target={target_text} [{status}]"
        )
        if not result.passed:
            has_failures = True

    if args.strict and has_failures:
        return 1
    return 0


if __name__ == "__main__":
    raise SystemExit(main(sys.argv[1:]))
