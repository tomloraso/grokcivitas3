from __future__ import annotations

import pytest

from civitas.infrastructure.pipelines.demographics_release_files import (
    parse_next_data_payload,
    parse_release_version_from_page,
    select_school_level_file,
)


def test_parse_next_data_payload_extracts_json() -> None:
    html = """
    <html>
      <script id=\"__NEXT_DATA__\" type=\"application/json\">{"props":{"pageProps":{"releaseVersion":{"id":"rv-1"}}}}</script>
    </html>
    """

    payload = parse_next_data_payload(html)

    assert payload["props"]["pageProps"]["releaseVersion"]["id"] == "rv-1"


def test_parse_release_version_from_page_returns_release_version_payload() -> None:
    html = """
    <html>
      <script id=\"__NEXT_DATA__\" type=\"application/json\">{"props":{"pageProps":{"releaseVersion":{"id":"rv-1","downloadFiles":[]}}}}</script>
    </html>
    """

    release_version = parse_release_version_from_page(html)

    assert release_version["id"] == "rv-1"


def test_parse_next_data_payload_raises_when_missing() -> None:
    with pytest.raises(ValueError, match="__NEXT_DATA__"):
        parse_next_data_payload("<html></html>")


def test_select_school_level_file_excludes_class_size_files() -> None:
    files = [
        {"id": "f2", "name": "School level underlying data - class sizes - 2024/25"},
        {"id": "f3", "name": "School level underlying data 2025"},
        {"id": "f1", "name": "School level underlying data 2024"},
    ]

    selected = select_school_level_file(files)

    assert selected is not None
    assert selected["id"] == "f1"


def test_select_school_level_file_returns_none_when_no_match() -> None:
    selected = select_school_level_file(
        [{"id": "f1", "name": "Class sizes - state-funded primary and secondary schools"}]
    )

    assert selected is None
