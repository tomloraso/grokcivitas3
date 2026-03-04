"""Discover candidate historical DfE characteristics datasets.

Run from repo root:
  uv run --project apps/backend python tools/scripts/discover_dfe_characteristics_history.py
"""

from __future__ import annotations

import argparse
import json
from datetime import datetime, timezone
from pathlib import Path
from typing import Any
from urllib.request import Request, urlopen

DFE_BASE_URL = "https://api.education.gov.uk/statistics/v1"
PUBLICATIONS_URL = f"{DFE_BASE_URL}/publications?page={{page}}&pageSize=20"
PUBLICATION_DATASETS_URL = (
    f"{DFE_BASE_URL}/publications/{{publication_id}}/data-sets?page={{page}}&pageSize=20"
)
DEFAULT_PUBLICATION_TITLE = "Key stage 2 attainment"
DEFAULT_DATASET_TITLE_TOKEN = "Schools (School information)"
DEFAULT_OUTPUT = Path("data/bronze/dfe_characteristics/history_inventory.json")


def _fetch_json(url: str) -> dict[str, Any]:
    request = Request(url=url, headers={"User-Agent": "civitas-dfe-history-discovery/0.1"})
    with urlopen(request, timeout=60) as response:
        payload = json.loads(response.read().decode("utf-8"))
    if isinstance(payload, dict):
        return payload
    return {}


def _iter_paged(url_template: str) -> list[dict[str, Any]]:
    page = 1
    results: list[dict[str, Any]] = []
    while True:
        payload = _fetch_json(url_template.format(page=page))
        page_results = payload.get("results")
        if isinstance(page_results, list):
            results.extend(result for result in page_results if isinstance(result, dict))

        paging = payload.get("paging")
        total_pages = 1
        if isinstance(paging, dict):
            total_pages_raw = paging.get("totalPages")
            if isinstance(total_pages_raw, int) and total_pages_raw > 0:
                total_pages = total_pages_raw
        if page >= total_pages:
            break
        page += 1
    return results


def _normalize_academic_year(raw_value: Any) -> str | None:
    if not isinstance(raw_value, str):
        return None
    value = raw_value.strip()
    if len(value) == 7 and value[4] == "/" and value[:4].isdigit() and value[5:].isdigit():
        return value
    if len(value) == 6 and value.isdigit():
        return f"{value[:4]}/{value[4:]}"
    return None


def _academic_year_sort_key(value: str | None) -> tuple[int, str]:
    if value is None:
        return (0, "")
    return (int(value[:4]), value)


def discover_dfe_characteristics_history(
    *,
    publication_title: str,
    dataset_title_token: str,
) -> list[dict[str, Any]]:
    publications = _iter_paged(PUBLICATIONS_URL)
    publication = next(
        (
            item
            for item in publications
            if isinstance(item.get("title"), str)
            and item["title"].strip().casefold() == publication_title.strip().casefold()
        ),
        None,
    )
    if publication is None:
        return []

    publication_id = publication.get("id")
    if not isinstance(publication_id, str) or not publication_id.strip():
        return []

    datasets = _iter_paged(PUBLICATION_DATASETS_URL.format(publication_id=publication_id, page="{page}"))
    token = dataset_title_token.strip().casefold()
    matched = [
        dataset
        for dataset in datasets
        if isinstance(dataset.get("title"), str) and token in dataset["title"].casefold()
    ]

    inventory: list[dict[str, Any]] = []
    for dataset in matched:
        latest_version = dataset.get("latestVersion")
        latest_version_dict = latest_version if isinstance(latest_version, dict) else {}
        time_periods = latest_version_dict.get("timePeriods")
        time_periods_dict = time_periods if isinstance(time_periods, dict) else {}
        academic_year_start = _normalize_academic_year(time_periods_dict.get("start"))
        academic_year_end = _normalize_academic_year(time_periods_dict.get("end"))

        inventory.append(
            {
                "dataset_id": dataset.get("id"),
                "title": dataset.get("title"),
                "status": dataset.get("status"),
                "academic_year_start": academic_year_start,
                "academic_year_end": academic_year_end,
                "latest_version": latest_version_dict.get("version"),
                "latest_version_published_at": latest_version_dict.get("published"),
                "latest_release_title": (
                    latest_version_dict.get("release", {}).get("title")
                    if isinstance(latest_version_dict.get("release"), dict)
                    else None
                ),
            }
        )

    inventory.sort(
        key=lambda item: _academic_year_sort_key(
            item["academic_year_end"]
            if isinstance(item.get("academic_year_end"), str)
            else None
        )
    )
    return inventory


def _build_arg_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description="Discover DfE characteristics dataset history.")
    parser.add_argument(
        "--publication-title",
        default=DEFAULT_PUBLICATION_TITLE,
        help=f"Publication title to search (default: {DEFAULT_PUBLICATION_TITLE!r})",
    )
    parser.add_argument(
        "--dataset-title-token",
        default=DEFAULT_DATASET_TITLE_TOKEN,
        help=(
            "Case-insensitive token used to match publication dataset titles "
            f"(default: {DEFAULT_DATASET_TITLE_TOKEN!r})"
        ),
    )
    parser.add_argument(
        "--output",
        default=str(DEFAULT_OUTPUT),
        help=f"Output JSON file path (default: {DEFAULT_OUTPUT})",
    )
    return parser


def main() -> int:
    args = _build_arg_parser().parse_args()
    output_path = Path(args.output)

    inventory = discover_dfe_characteristics_history(
        publication_title=args.publication_title,
        dataset_title_token=args.dataset_title_token,
    )

    payload = {
        "generated_at": datetime.now(timezone.utc).isoformat(),
        "publication_title": args.publication_title,
        "dataset_title_token": args.dataset_title_token,
        "datasets": inventory,
    }
    output_path.parent.mkdir(parents=True, exist_ok=True)
    output_path.write_text(json.dumps(payload, indent=2, sort_keys=True), encoding="utf-8")

    print(f"Wrote {len(inventory)} candidate dataset(s) to {output_path}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
