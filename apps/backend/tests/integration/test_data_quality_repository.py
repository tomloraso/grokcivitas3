from __future__ import annotations

from datetime import date, datetime, timezone
from uuid import uuid4

import pytest
from sqlalchemy import create_engine, text
from sqlalchemy.engine import Engine

from civitas.infrastructure.config.settings import AppSettings
from civitas.infrastructure.persistence.postgres_data_quality_repository import (
    PostgresDataQualityRepository,
)
from civitas.infrastructure.pipelines.base import (
    PipelineResult,
    PipelineRunContext,
    PipelineRunStatus,
    PipelineSource,
)
from civitas.infrastructure.pipelines.runner import SqlPipelineRunStore


def _database_url() -> str:
    return AppSettings().database.url


def _build_engine(database_url: str) -> Engine:
    if database_url.startswith("postgresql"):
        return create_engine(database_url, future=True, connect_args={"connect_timeout": 2})
    return create_engine(database_url, future=True)


def _database_available(database_url: str) -> bool:
    engine = _build_engine(database_url)
    try:
        with engine.connect() as connection:
            connection.execute(text("SELECT 1"))
        return True
    except Exception:
        return False
    finally:
        engine.dispose()


DATABASE_URL = _database_url()
DATABASE_AVAILABLE = _database_available(DATABASE_URL)
pytestmark = pytest.mark.skipif(
    not DATABASE_AVAILABLE,
    reason="Postgres database unavailable for data quality repository integration test.",
)


@pytest.fixture()
def engine() -> Engine:
    engine = _build_engine(DATABASE_URL)
    _ensure_schema(engine)
    _seed_data(engine)
    try:
        yield engine
    finally:
        _cleanup_data(engine)
        engine.dispose()


def _ensure_schema(engine: Engine) -> None:
    with engine.begin() as connection:
        connection.execute(text("CREATE EXTENSION IF NOT EXISTS postgis"))
        connection.execute(
            text(
                """
                CREATE TABLE IF NOT EXISTS schools (
                    urn text PRIMARY KEY,
                    name text NOT NULL,
                    phase text NULL,
                    type text NULL,
                    status text NULL,
                    postcode text NULL,
                    easting double precision NOT NULL,
                    northing double precision NOT NULL,
                    location geography(Point, 4326) NOT NULL,
                    capacity integer NULL,
                    pupil_count integer NULL,
                    open_date date NULL,
                    close_date date NULL,
                    updated_at timestamptz NOT NULL DEFAULT timezone('utc', now())
                )
                """
            )
        )
        connection.execute(
            text(
                """
                CREATE TABLE IF NOT EXISTS school_demographics_yearly (
                    urn text NOT NULL,
                    academic_year text NOT NULL,
                    disadvantaged_pct double precision NULL,
                    fsm_pct double precision NULL,
                    sen_pct double precision NULL,
                    sen_support_pct double precision NULL,
                    ehcp_pct double precision NULL,
                    eal_pct double precision NULL,
                    first_language_english_pct double precision NULL,
                    first_language_unclassified_pct double precision NULL,
                    total_pupils integer NULL,
                    has_ethnicity_data boolean NOT NULL DEFAULT false,
                    has_top_languages_data boolean NOT NULL DEFAULT false,
                    source_dataset_id text NOT NULL,
                    source_dataset_version text NULL,
                    updated_at timestamptz NOT NULL DEFAULT timezone('utc', now()),
                    PRIMARY KEY (urn, academic_year)
                )
                """
            )
        )
        connection.execute(
            text(
                """
                CREATE TABLE IF NOT EXISTS school_ofsted_latest (
                    urn text PRIMARY KEY,
                    inspection_start_date date NULL,
                    publication_date date NULL,
                    overall_effectiveness_code text NULL,
                    overall_effectiveness_label text NULL,
                    is_graded boolean NOT NULL DEFAULT false,
                    ungraded_outcome text NULL,
                    source_asset_url text NOT NULL,
                    source_asset_month text NULL,
                    updated_at timestamptz NOT NULL DEFAULT timezone('utc', now())
                )
                """
            )
        )
        connection.execute(
            text(
                """
                CREATE TABLE IF NOT EXISTS ofsted_inspections (
                    inspection_number text PRIMARY KEY,
                    urn text NOT NULL,
                    inspection_start_date date NOT NULL,
                    inspection_end_date date NULL,
                    publication_date date NULL,
                    inspection_type text NULL,
                    inspection_type_grouping text NULL,
                    event_type_grouping text NULL,
                    overall_effectiveness_code text NULL,
                    overall_effectiveness_label text NULL,
                    headline_outcome_text text NULL,
                    category_of_concern text NULL,
                    source_schema_version text NOT NULL,
                    source_asset_url text NOT NULL,
                    source_asset_month text NULL,
                    updated_at timestamptz NOT NULL DEFAULT timezone('utc', now())
                )
                """
            )
        )
        connection.execute(
            text(
                """
                CREATE TABLE IF NOT EXISTS postcode_cache (
                    postcode text PRIMARY KEY,
                    lat double precision NOT NULL,
                    lng double precision NOT NULL,
                    lsoa_code text NULL
                )
                """
            )
        )
        connection.execute(
            text(
                """
                CREATE TABLE IF NOT EXISTS area_deprivation (
                    lsoa_code text PRIMARY KEY,
                    lsoa_name text NOT NULL,
                    local_authority_district_code text NULL,
                    local_authority_district_name text NULL,
                    imd_score double precision NOT NULL,
                    imd_rank integer NOT NULL,
                    imd_decile integer NOT NULL,
                    idaci_score double precision NOT NULL,
                    idaci_rank integer NOT NULL,
                    idaci_decile integer NOT NULL,
                    source_release text NOT NULL,
                    lsoa_vintage text NOT NULL,
                    source_file_url text NOT NULL,
                    updated_at timestamptz NOT NULL DEFAULT timezone('utc', now())
                )
                """
            )
        )
        connection.execute(
            text(
                """
                CREATE TABLE IF NOT EXISTS area_crime_context (
                    urn text NOT NULL,
                    month date NOT NULL,
                    crime_category text NOT NULL,
                    incident_count integer NOT NULL,
                    radius_meters double precision NOT NULL,
                    source_month text NOT NULL,
                    updated_at timestamptz NOT NULL DEFAULT timezone('utc', now()),
                    PRIMARY KEY (urn, month, crime_category, radius_meters)
                )
                """
            )
        )
        connection.execute(
            text(
                """
                CREATE TABLE IF NOT EXISTS pipeline_runs (
                    run_id uuid PRIMARY KEY,
                    source text NOT NULL,
                    status text NOT NULL,
                    started_at timestamptz NOT NULL,
                    finished_at timestamptz NULL,
                    bronze_path text NOT NULL,
                    downloaded_rows integer NOT NULL DEFAULT 0,
                    staged_rows integer NOT NULL DEFAULT 0,
                    promoted_rows integer NOT NULL DEFAULT 0,
                    rejected_rows integer NOT NULL DEFAULT 0,
                    error_message text NULL
                )
                """
            )
        )
        connection.execute(
            text(
                """
                CREATE TABLE IF NOT EXISTS pipeline_run_events (
                    id bigserial PRIMARY KEY,
                    run_id uuid UNIQUE NOT NULL,
                    source text NOT NULL,
                    dataset text NOT NULL,
                    section text NULL,
                    academic_year text NULL,
                    run_status text NOT NULL,
                    contract_version text NULL,
                    started_at timestamptz NOT NULL,
                    finished_at timestamptz NOT NULL,
                    duration_seconds double precision NOT NULL,
                    downloaded_rows integer NOT NULL DEFAULT 0,
                    staged_rows integer NOT NULL DEFAULT 0,
                    promoted_rows integer NOT NULL DEFAULT 0,
                    rejected_rows integer NOT NULL DEFAULT 0,
                    rejected_ratio double precision NULL,
                    error_message text NULL,
                    created_at timestamptz NOT NULL DEFAULT timezone('utc', now())
                )
                """
            )
        )
        connection.execute(
            text(
                """
                CREATE TABLE IF NOT EXISTS data_quality_snapshots (
                    snapshot_date date NOT NULL,
                    source text NOT NULL,
                    dataset text NOT NULL,
                    section text NOT NULL,
                    source_updated_at timestamptz NULL,
                    section_updated_at timestamptz NULL,
                    source_freshness_lag_hours double precision NULL,
                    section_freshness_lag_hours double precision NULL,
                    schools_total_count integer NOT NULL,
                    schools_with_section_count integer NOT NULL,
                    section_coverage_ratio double precision NOT NULL,
                    trends_zero_years_count integer NOT NULL DEFAULT 0,
                    trends_one_year_count integer NOT NULL DEFAULT 0,
                    trends_two_plus_years_count integer NOT NULL DEFAULT 0,
                    contract_version text NULL,
                    created_at timestamptz NOT NULL DEFAULT timezone('utc', now()),
                    updated_at timestamptz NOT NULL DEFAULT timezone('utc', now()),
                    PRIMARY KEY (snapshot_date, source, dataset, section)
                )
                """
            )
        )


def _seed_data(engine: Engine) -> None:
    with engine.begin() as connection:
        connection.execute(
            text(
                """
                INSERT INTO schools (
                    urn,
                    name,
                    phase,
                    type,
                    status,
                    postcode,
                    easting,
                    northing,
                    location,
                    capacity,
                    pupil_count,
                    open_date,
                    close_date
                )
                VALUES
                    (
                        '990001',
                        'DQ School 1',
                        'Primary',
                        'Community',
                        'Open',
                        'AA1 1AA',
                        500000,
                        200000,
                        ST_SetSRID(ST_MakePoint(-0.10, 51.50), 4326)::geography(Point, 4326),
                        300,
                        280,
                        '2005-09-01',
                        NULL
                    ),
                    (
                        '990002',
                        'DQ School 2',
                        'Primary',
                        'Academy',
                        'Open',
                        'AA2 2AA',
                        500100,
                        200100,
                        ST_SetSRID(ST_MakePoint(-0.11, 51.51), 4326)::geography(Point, 4326),
                        320,
                        290,
                        '2006-09-01',
                        NULL
                    ),
                    (
                        '990003',
                        'DQ School 3',
                        'Primary',
                        'Academy',
                        'Open',
                        'AA3 3AA',
                        500200,
                        200200,
                        ST_SetSRID(ST_MakePoint(-0.12, 51.52), 4326)::geography(Point, 4326),
                        280,
                        250,
                        '2007-09-01',
                        NULL
                    )
                ON CONFLICT (urn) DO UPDATE SET
                    postcode = EXCLUDED.postcode,
                    name = EXCLUDED.name
                """
            )
        )
        connection.execute(
            text(
                """
                INSERT INTO school_demographics_yearly (
                    urn,
                    academic_year,
                    disadvantaged_pct,
                    fsm_pct,
                    sen_pct,
                    sen_support_pct,
                    ehcp_pct,
                    eal_pct,
                    first_language_english_pct,
                    first_language_unclassified_pct,
                    total_pupils,
                    has_ethnicity_data,
                    has_top_languages_data,
                    source_dataset_id,
                    source_dataset_version,
                    updated_at
                )
                VALUES
                    (
                        '990001',
                        '2023/24',
                        20.0,
                        NULL,
                        12.0,
                        9.0,
                        2.0,
                        7.0,
                        88.0,
                        1.0,
                        280,
                        true,
                        true,
                        'dataset-a',
                        'v1',
                        '2100-03-03T00:00:00+00:00'
                    ),
                    (
                        '990001',
                        '2024/25',
                        19.0,
                        NULL,
                        11.0,
                        8.0,
                        2.0,
                        7.0,
                        89.0,
                        1.0,
                        280,
                        true,
                        true,
                        'dataset-a',
                        'v1',
                        '2100-03-03T00:00:00+00:00'
                    ),
                    (
                        '990002',
                        '2024/25',
                        25.0,
                        NULL,
                        15.0,
                        10.0,
                        3.0,
                        8.0,
                        87.0,
                        1.0,
                        290,
                        true,
                        true,
                        'dataset-a',
                        'v1',
                        '2100-03-02T00:00:00+00:00'
                    )
                ON CONFLICT (urn, academic_year) DO UPDATE SET updated_at = EXCLUDED.updated_at
                """
            )
        )
        connection.execute(
            text(
                """
                INSERT INTO school_ofsted_latest (
                    urn,
                    inspection_start_date,
                    publication_date,
                    overall_effectiveness_code,
                    overall_effectiveness_label,
                    is_graded,
                    ungraded_outcome,
                    source_asset_url,
                    source_asset_month,
                    updated_at
                )
                VALUES (
                    '990001',
                    '2026-02-10',
                    '2026-02-20',
                    '2',
                    'Good',
                    true,
                    NULL,
                    'https://example.com/ofsted_latest.csv',
                    '2026-02',
                    '2100-03-03T01:00:00+00:00'
                )
                ON CONFLICT (urn) DO UPDATE SET updated_at = EXCLUDED.updated_at
                """
            )
        )
        connection.execute(
            text(
                """
                INSERT INTO ofsted_inspections (
                    inspection_number,
                    urn,
                    inspection_start_date,
                    inspection_end_date,
                    publication_date,
                    inspection_type,
                    inspection_type_grouping,
                    event_type_grouping,
                    overall_effectiveness_code,
                    overall_effectiveness_label,
                    headline_outcome_text,
                    category_of_concern,
                    source_schema_version,
                    source_asset_url,
                    source_asset_month,
                    updated_at
                )
                VALUES
                    (
                        'i-990001',
                        '990001',
                        '2025-09-01',
                        NULL,
                        '2025-10-01',
                        'S5',
                        NULL,
                        NULL,
                        '2',
                        'Good',
                        NULL,
                        NULL,
                        'all_inspections_ytd',
                        'https://example.com/ofsted_timeline.csv',
                        '2026-02',
                        '2100-03-01T00:00:00+00:00'
                    ),
                    (
                        'i-990002',
                        '990002',
                        '2025-08-01',
                        NULL,
                        '2025-09-01',
                        'S5',
                        NULL,
                        NULL,
                        '3',
                        'Requires improvement',
                        NULL,
                        NULL,
                        'all_inspections_ytd',
                        'https://example.com/ofsted_timeline.csv',
                        '2026-02',
                        '2100-03-01T00:00:00+00:00'
                    )
                ON CONFLICT (inspection_number) DO UPDATE SET
                    urn = EXCLUDED.urn,
                    updated_at = EXCLUDED.updated_at
                """
            )
        )
        connection.execute(
            text(
                """
                INSERT INTO postcode_cache (postcode, lat, lng, lsoa_code)
                VALUES
                    ('AA1 1AA', 51.50, -0.10, 'L001'),
                    ('AA2 2AA', 51.51, -0.11, 'L999')
                ON CONFLICT (postcode) DO UPDATE SET
                    lsoa_code = EXCLUDED.lsoa_code,
                    lat = EXCLUDED.lat,
                    lng = EXCLUDED.lng
                """
            )
        )
        connection.execute(
            text(
                """
                INSERT INTO area_deprivation (
                    lsoa_code,
                    lsoa_name,
                    local_authority_district_code,
                    local_authority_district_name,
                    imd_score,
                    imd_rank,
                    imd_decile,
                    idaci_score,
                    idaci_rank,
                    idaci_decile,
                    source_release,
                    lsoa_vintage,
                    source_file_url,
                    updated_at
                )
                VALUES (
                    'L001',
                    'Sample LSOA',
                    'E09000001',
                    'Sample District',
                    21.0,
                    1000,
                    3,
                    0.22,
                    800,
                    2,
                    'IoD2025',
                    '2021',
                    'https://example.com/imd.csv',
                    '2100-03-03T02:00:00+00:00'
                )
                ON CONFLICT (lsoa_code) DO UPDATE SET updated_at = EXCLUDED.updated_at
                """
            )
        )
        connection.execute(
            text(
                """
                INSERT INTO area_crime_context (
                    urn,
                    month,
                    crime_category,
                    incident_count,
                    radius_meters,
                    source_month,
                    updated_at
                )
                VALUES (
                    '990001',
                    '2026-03-01',
                    'violent-crime',
                    15,
                    1609.344,
                    '2026-03',
                    '2100-03-03T03:00:00+00:00'
                )
                ON CONFLICT (urn, month, crime_category, radius_meters) DO UPDATE SET
                    updated_at = EXCLUDED.updated_at
                """
            )
        )

        _insert_pipeline_run(
            connection=connection,
            run_id=str(uuid4()),
            source="dfe_characteristics",
            status="succeeded",
            finished_at="2100-03-02T12:00:00+00:00",
        )
        _insert_pipeline_run(
            connection=connection,
            run_id=str(uuid4()),
            source="ons_imd",
            status="succeeded",
            finished_at="2100-03-01T12:00:00+00:00",
        )
        _insert_pipeline_run(
            connection=connection,
            run_id=str(uuid4()),
            source="gias",
            status="failed_quality_gate",
            finished_at="2026-03-03T10:00:00+00:00",
        )

        _insert_pipeline_run_event(
            connection=connection,
            run_id=str(uuid4()),
            source="dfe_characteristics",
            run_status="failed_quality_gate",
            finished_at="2100-03-03T10:00:00+00:00",
            contract_version="dfe-v2",
        )
        _insert_pipeline_run_event(
            connection=connection,
            run_id=str(uuid4()),
            source="dfe_characteristics",
            run_status="failed",
            finished_at="2100-03-02T10:00:00+00:00",
            contract_version="dfe-v1",
        )
        _insert_pipeline_run_event(
            connection=connection,
            run_id=str(uuid4()),
            source="dfe_characteristics",
            run_status="succeeded",
            finished_at="2100-03-01T10:00:00+00:00",
            contract_version="dfe-v1",
        )
        _insert_pipeline_run_event(
            connection=connection,
            run_id=str(uuid4()),
            source="gias",
            run_status="failed_quality_gate",
            finished_at="2100-03-03T09:00:00+00:00",
            contract_version="gias-v1",
        )
        _insert_pipeline_run_event(
            connection=connection,
            run_id=str(uuid4()),
            source="gias",
            run_status="failed",
            finished_at="2100-03-02T09:00:00+00:00",
            contract_version="gias-v1",
        )
        _insert_pipeline_run_event(
            connection=connection,
            run_id=str(uuid4()),
            source="gias",
            run_status="failed_source_unavailable",
            finished_at="2100-03-01T09:00:00+00:00",
            contract_version="gias-v1",
        )
        _insert_pipeline_run_event(
            connection=connection,
            run_id=str(uuid4()),
            source="integration_probe_source",
            run_status="failed_quality_gate",
            finished_at="2100-03-03T08:00:00+00:00",
            contract_version="probe-v1",
        )
        _insert_pipeline_run_event(
            connection=connection,
            run_id=str(uuid4()),
            source="integration_probe_source",
            run_status="failed",
            finished_at="2100-03-02T08:00:00+00:00",
            contract_version="probe-v1",
        )
        _insert_pipeline_run_event(
            connection=connection,
            run_id=str(uuid4()),
            source="integration_probe_source",
            run_status="succeeded",
            finished_at="2100-03-01T08:00:00+00:00",
            contract_version="probe-v1",
        )


def _insert_pipeline_run(
    *,
    connection,
    run_id: str,
    source: str,
    status: str,
    finished_at: str,
) -> None:
    connection.execute(
        text(
            """
            INSERT INTO pipeline_runs (
                run_id,
                source,
                status,
                started_at,
                finished_at,
                bronze_path,
                downloaded_rows,
                staged_rows,
                promoted_rows,
                rejected_rows
            ) VALUES (
                :run_id,
                :source,
                :status,
                :started_at,
                :finished_at,
                :bronze_path,
                0,
                0,
                0,
                0
            )
            ON CONFLICT (run_id) DO NOTHING
            """
        ),
        {
            "run_id": run_id,
            "source": source,
            "status": status,
            "started_at": finished_at,
            "finished_at": finished_at,
            "bronze_path": f"data/bronze/{source}",
        },
    )


def _insert_pipeline_run_event(
    *,
    connection,
    run_id: str,
    source: str,
    run_status: str,
    finished_at: str,
    contract_version: str,
) -> None:
    _insert_pipeline_run(
        connection=connection,
        run_id=run_id,
        source=source,
        status=run_status,
        finished_at=finished_at,
    )
    connection.execute(
        text(
            """
            INSERT INTO pipeline_run_events (
                run_id,
                source,
                dataset,
                section,
                academic_year,
                run_status,
                contract_version,
                started_at,
                finished_at,
                duration_seconds,
                downloaded_rows,
                staged_rows,
                promoted_rows,
                rejected_rows,
                rejected_ratio,
                error_message
            ) VALUES (
                :run_id,
                :source,
                :dataset,
                :section,
                NULL,
                :run_status,
                :contract_version,
                :started_at,
                :finished_at,
                10.0,
                10,
                9,
                9,
                1,
                0.1,
                NULL
            )
            ON CONFLICT (run_id) DO NOTHING
            """
        ),
        {
            "run_id": run_id,
            "source": source,
            "dataset": source,
            "section": None,
            "run_status": run_status,
            "contract_version": contract_version,
            "started_at": finished_at,
            "finished_at": finished_at,
        },
    )


def _cleanup_data(engine: Engine) -> None:
    with engine.begin() as connection:
        connection.execute(text("DELETE FROM data_quality_snapshots"))
        connection.execute(text("DELETE FROM pipeline_run_events"))
        connection.execute(
            text(
                """
                DELETE FROM pipeline_runs
                WHERE source IN (
                    'dfe_characteristics',
                    'ons_imd',
                    'gias',
                    'integration_probe_source'
                )
                """
            )
        )
        connection.execute(
            text(
                """
                DELETE FROM area_crime_context
                WHERE urn IN ('990001', '990002', '990003')
                """
            )
        )
        connection.execute(text("DELETE FROM area_deprivation WHERE lsoa_code IN ('L001', 'L999')"))
        connection.execute(
            text("DELETE FROM postcode_cache WHERE postcode IN ('AA1 1AA', 'AA2 2AA')")
        )
        connection.execute(
            text(
                "DELETE FROM ofsted_inspections WHERE inspection_number IN ('i-990001', 'i-990002')"
            )
        )
        connection.execute(
            text("DELETE FROM school_ofsted_latest WHERE urn IN ('990001', '990002')")
        )
        connection.execute(
            text(
                """
                DELETE FROM school_demographics_yearly
                WHERE urn IN ('990001', '990002', '990003')
                """
            )
        )
        connection.execute(text("DELETE FROM schools WHERE urn IN ('990001', '990002', '990003')"))


def test_data_quality_repository_collects_snapshots_and_run_health(engine: Engine) -> None:
    repository = PostgresDataQualityRepository(engine=engine)
    snapshot_date = date(2026, 3, 3)
    as_of = datetime(2026, 3, 3, 12, 0, tzinfo=timezone.utc)

    snapshots = repository.collect_snapshots(snapshot_date=snapshot_date, as_of=as_of)

    assert len(snapshots) >= 5
    demographics_snapshot = next(
        snapshot for snapshot in snapshots if snapshot.section == "demographics"
    )
    assert demographics_snapshot.schools_total_count >= 3
    assert demographics_snapshot.schools_with_section_count >= 2
    assert 0.0 <= demographics_snapshot.section_coverage_ratio <= 1.0
    assert demographics_snapshot.section_coverage_ratio == pytest.approx(
        demographics_snapshot.schools_with_section_count / demographics_snapshot.schools_total_count
    )
    assert (
        demographics_snapshot.trends_zero_years_count
        + demographics_snapshot.trends_one_year_count
        + demographics_snapshot.trends_two_plus_years_count
        == demographics_snapshot.schools_total_count
    )
    assert demographics_snapshot.source_freshness_lag_hours == pytest.approx(0.0)
    assert demographics_snapshot.section_freshness_lag_hours == pytest.approx(0.0)
    assert demographics_snapshot.contract_version is not None

    previous_day_snapshot = demographics_snapshot.__class__(
        snapshot_date=date(2026, 3, 2),
        source=demographics_snapshot.source,
        dataset=demographics_snapshot.dataset,
        section=demographics_snapshot.section,
        source_updated_at=demographics_snapshot.source_updated_at,
        section_updated_at=demographics_snapshot.section_updated_at,
        source_freshness_lag_hours=8.0,
        section_freshness_lag_hours=8.0,
        schools_total_count=3,
        schools_with_section_count=3,
        section_coverage_ratio=1.0,
        trends_zero_years_count=0,
        trends_one_year_count=1,
        trends_two_plus_years_count=2,
        contract_version="dfe-v1",
    )
    repository.upsert_snapshots((previous_day_snapshot,))
    repository.upsert_snapshots(snapshots)

    persisted_today = repository.list_snapshots(snapshot_date=snapshot_date)
    assert len(persisted_today) == len(snapshots)

    drifts = repository.list_coverage_drifts(snapshot_date=snapshot_date)
    demographics_drift = next(drift for drift in drifts if drift.section == "demographics")
    assert demographics_drift.previous_coverage_ratio == pytest.approx(1.0)
    assert demographics_drift.delta_coverage_ratio == pytest.approx(
        demographics_snapshot.section_coverage_ratio - 1.0
    )

    run_health = repository.list_pipeline_run_health()
    probe_run_health = next(
        metric for metric in run_health if metric.source == "integration_probe_source"
    )
    assert probe_run_health.quality_gate_failures_total == 1
    assert probe_run_health.consecutive_failed_runs == 2


def test_sql_pipeline_run_store_emits_pipeline_run_event(engine: Engine, tmp_path) -> None:
    run_store = SqlPipelineRunStore(engine=engine)
    context = PipelineRunContext(
        run_id=uuid4(),
        source=PipelineSource.DFE_CHARACTERISTICS,
        started_at=datetime(2026, 3, 3, 11, 0, tzinfo=timezone.utc),
        bronze_root=tmp_path,
    )
    run_store.record_started(context)
    result = PipelineResult(
        status=PipelineRunStatus.SUCCEEDED,
        downloaded_rows=100,
        staged_rows=90,
        promoted_rows=90,
        rejected_rows=10,
        contract_version="dfe-v3",
        error_message=None,
    )
    run_store.record_finished(
        context=context,
        result=result,
        finished_at=datetime(2026, 3, 3, 12, 0, tzinfo=timezone.utc),
    )

    with engine.connect() as connection:
        row = (
            connection.execute(
                text(
                    """
                    SELECT
                        source,
                        dataset,
                        section,
                        run_status,
                        contract_version,
                        duration_seconds,
                        rejected_ratio
                    FROM pipeline_run_events
                    WHERE run_id = :run_id
                    """
                ),
                {"run_id": str(context.run_id)},
            )
            .mappings()
            .first()
        )

    assert row is not None
    assert row["source"] == "dfe_characteristics"
    assert row["dataset"] == "school_demographics_yearly"
    assert row["section"] == "demographics"
    assert row["run_status"] == "succeeded"
    assert row["contract_version"] == "dfe-v3"
    assert float(row["duration_seconds"]) == pytest.approx(3600.0)
    assert float(row["rejected_ratio"]) == pytest.approx(0.1)
