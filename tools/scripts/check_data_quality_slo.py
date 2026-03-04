"""Evaluate data quality SLOs using persisted daily snapshots.

Run from repo root:
  uv run --project apps/backend python tools/scripts/check_data_quality_slo.py --strict
"""

from __future__ import annotations

import argparse
import sys
from datetime import date

from civitas.bootstrap.container import data_quality_slo_check_use_case


def _parse_args(argv: list[str]) -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Evaluate data quality SLO alerts.")
    parser.add_argument(
        "--strict",
        action="store_true",
        help="Exit with status 1 when one or more alerts are raised.",
    )
    parser.add_argument(
        "--snapshot-date",
        type=str,
        default=None,
        help="Optional snapshot date override in YYYY-MM-DD format.",
    )
    return parser.parse_args(argv)


def main(argv: list[str] | None = None) -> int:
    args = _parse_args(argv or [])
    snapshot_date: date | None = None
    if args.snapshot_date is not None:
        try:
            snapshot_date = date.fromisoformat(args.snapshot_date.strip())
        except ValueError:
            print("Invalid --snapshot-date. Expected YYYY-MM-DD.", file=sys.stderr)
            return 2

    use_case = data_quality_slo_check_use_case()
    report = use_case.execute(snapshot_date=snapshot_date)

    print(f"snapshot_date={report.snapshot_date.isoformat()}")
    for snapshot in report.snapshots:
        source_lag = (
            "n/a"
            if snapshot.source_freshness_lag_hours is None
            else f"{snapshot.source_freshness_lag_hours:.2f}h"
        )
        section_lag = (
            "n/a"
            if snapshot.section_freshness_lag_hours is None
            else f"{snapshot.section_freshness_lag_hours:.2f}h"
        )
        print(
            f"{snapshot.source}/{snapshot.section}: "
            f"coverage={snapshot.section_coverage_ratio:.4f} "
            f"({snapshot.schools_with_section_count}/{snapshot.schools_total_count}) "
            f"source_lag={source_lag} section_lag={section_lag}"
        )

    for metric in report.run_health:
        print(
            f"run_health[{metric.source}]: "
            f"quality_gate_failures_total={metric.quality_gate_failures_total} "
            f"consecutive_failed_runs={metric.consecutive_failed_runs}"
        )

    if report.alerts:
        print("alerts:")
        for alert in report.alerts:
            source = alert.source or "-"
            section = alert.section or "-"
            observed = "n/a" if alert.observed_value is None else str(alert.observed_value)
            threshold = "n/a" if alert.threshold_value is None else str(alert.threshold_value)
            print(
                f"  [{alert.severity}] {alert.alert_type} "
                f"source={source} section={section} "
                f"observed={observed} threshold={threshold} "
                f"message={alert.message}"
            )
    else:
        print("alerts: none")

    blocking_alerts = tuple(alert for alert in report.alerts if alert.severity == "critical")
    if args.strict and blocking_alerts:
        return 1
    return 0


if __name__ == "__main__":
    raise SystemExit(main(sys.argv[1:]))
