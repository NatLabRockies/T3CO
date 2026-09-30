"""Tests for the EIA API client module."""

import json
from unittest.mock import MagicMock, patch

import numpy as np
import pandas as pd
import pytest

from t3co.data_fetching.eia_client import (
    AEO_REGION_ID_TO_T3CO,
    AEO_SERIES_TO_FUEL,
    EIAClient,
    EIAClientError,
    T3CO_YEAR_RANGE,
    build_fuel_prices_df_from_eia,
)


# ── Fixtures ─────────────────────────────────────────────────────────────────

FAKE_API_KEY = "test_key_12345"


def _make_aeo_record(series_id: str, region_id: str, period: str, value: float) -> dict:
    """Helper to build a single AEO API data record."""
    return {
        "seriesId": series_id,
        "regionId": region_id,
        "period": period,
        "value": value,
        "tableId": "3",
    }


def _make_api_response(records: list) -> dict:
    """Wraps records in EIA API v2 response envelope."""
    return {"response": {"data": records, "total": len(records)}}


@pytest.fixture
def eia_client(tmp_path):
    """EIAClient with caching disabled (TTL=0)."""
    return EIAClient(
        api_key=FAKE_API_KEY,
        cache_dir=tmp_path / "cache",
        cache_ttl_seconds=0,
    )


# ── Constructor tests ────────────────────────────────────────────────────────


def test_missing_api_key_raises():
    with pytest.raises(ValueError, match="EIA API key is required"):
        EIAClient(api_key="")


def test_missing_requests_raises():
    with patch("t3co.data_fetching.eia_client.requests", None):
        with pytest.raises(ImportError, match="requests"):
            EIAClient(api_key=FAKE_API_KEY)


# ── _transform_aeo_to_t3co tests ────────────────────────────────────────────


def test_transform_converts_mmbtu_to_native_units(eia_client):
    """Verify $/MMBtu → $/gal conversion for diesel."""
    diesel_prefix = "prce_nom_trn_NA_dfu_NA_"
    diesel_sid = diesel_prefix + "neengl_ndlrpmbtu"
    mmbtu_per_gal = AEO_SERIES_TO_FUEL[diesel_prefix]["mmbtu_per_unit"]
    price_mmbtu = 20.0  # $20/MMBtu
    expected_per_gal = round(price_mmbtu * mmbtu_per_gal, 9)

    records = [_make_aeo_record(diesel_sid, "1-1", "2030", price_mmbtu)]
    rows = eia_client._transform_aeo_to_t3co(records, "New England")

    assert len(rows) == 1
    assert rows[0]["Region"] == "New England"
    assert rows[0]["Fuel"] == "diesel_dol_per_gal"
    assert rows[0]["2030"] == expected_per_gal


def test_transform_handles_multiple_fuels(eia_client):
    """Multiple fuel series in same region produce separate rows."""
    records = [
        _make_aeo_record("prce_nom_trn_NA_dfu_NA_neengl_ndlrpmbtu", "1-1", "2025", 18.0),
        _make_aeo_record("prce_nom_comm_NA_elc_NA_neengl_ndlrpmbtu", "1-1", "2025", 35.0),
    ]
    rows = eia_client._transform_aeo_to_t3co(records, "New England")
    fuels = {r["Fuel"] for r in rows}
    assert "diesel_dol_per_gal" in fuels
    assert "electricity_dol_per_kwh" in fuels


def test_transform_skips_unknown_series(eia_client):
    """Series IDs not in AEO_SERIES_TO_FUEL are silently skipped."""
    records = [
        _make_aeo_record("unknown_series", "1-1", "2025", 10.0),
        _make_aeo_record("prce_nom_trn_NA_dfu_NA_neengl_ndlrpmbtu", "1-1", "2025", 18.0),
    ]
    rows = eia_client._transform_aeo_to_t3co(records, "New England")
    assert len(rows) == 1
    assert rows[0]["Fuel"] == "diesel_dol_per_gal"


def test_transform_skips_null_values(eia_client):
    """Records with None value are skipped."""
    records = [
        _make_aeo_record("prce_nom_trn_NA_dfu_NA_neengl_ndlrpmbtu", "1-1", "2025", None),
    ]
    rows = eia_client._transform_aeo_to_t3co(records, "New England")
    assert len(rows) == 0


# ── _extrapolate_years tests ─────────────────────────────────────────────────


def test_extrapolate_backfills_early_years():
    """Years before the first available data are filled with the earliest value."""
    df = pd.DataFrame(
        [
            {
                "Region": "Test",
                "Fuel": "diesel_dol_per_gal",
                "2020": np.nan,
                "2021": np.nan,
                "2022": 3.0,
                "2023": 3.1,
                "2024": 3.2,
            }
        ]
    )
    result = EIAClient._extrapolate_years(df)
    assert result.loc[0, "2020"] == 3.0
    assert result.loc[0, "2021"] == 3.0


def test_extrapolate_forward_grows():
    """Years after the last available data use CAGR-based growth."""
    df = pd.DataFrame(
        [
            {
                "Region": "Test",
                "Fuel": "diesel_dol_per_gal",
                "2020": 2.0,
                "2021": 2.1,
                "2022": 2.2,
                "2023": 2.3,
                "2024": 2.4,
                "2025": np.nan,
                "2026": np.nan,
            }
        ]
    )
    result = EIAClient._extrapolate_years(df)
    # 2025 and 2026 should be filled and > 2.4
    assert result.loc[0, "2025"] > 2.4
    assert result.loc[0, "2026"] > result.loc[0, "2025"]


# ── fetch_aeo_fuel_prices (mocked HTTP) ─────────────────────────────────────


def test_fetch_aeo_fuel_prices_returns_t3co_schema(eia_client):
    """Mocked API call returns DataFrame with correct schema."""
    # Build fake API response for one region, one fuel, a few years
    records = []
    for year in range(2022, 2051):
        records.append(
            _make_aeo_record(
                "prce_nom_trn_NA_dfu_NA_soatl_ndlrpmbtu", "1-5", str(year), 20.0 + year * 0.01
            )
        )
        records.append(
            _make_aeo_record(
                "prce_nom_comm_NA_elc_NA_soatl_ndlrpmbtu", "1-5", str(year), 35.0
            )
        )

    with patch.object(eia_client, "_request", return_value=_make_api_response(records)):
        df = eia_client.fetch_aeo_fuel_prices(
            aeo_year="2023",
            scenario="aeo2022ref",
            region_ids=["1-5"],
        )

    assert "Region" in df.columns
    assert "Fuel" in df.columns
    assert df["Region"].iloc[0] == "South Atlantic"
    # All T3CO year columns should exist (2019-2100)
    year_cols = [str(y) for y in T3CO_YEAR_RANGE]
    for yc in year_cols:
        assert yc in df.columns, f"Missing year column: {yc}"
    # No NaN should remain after extrapolation
    fuel_rows = df[df["Fuel"] == "diesel_dol_per_gal"]
    assert not fuel_rows[year_cols].isna().any().any()


def test_fetch_empty_response_raises(eia_client):
    """Empty API data raises EIAClientError."""
    with patch.object(eia_client, "_request", return_value=_make_api_response([])):
        with pytest.raises(EIAClientError, match="No fuel price data"):
            eia_client.fetch_aeo_fuel_prices(
                aeo_year="2023",
                scenario="aeo2022ref",
                region_ids=["1-1"],
            )


# ── build_fuel_prices_df_from_eia ────────────────────────────────────────────


def test_build_fuel_prices_df_includes_hydrogen_fallback():
    """Hydrogen rows from fallback DF are merged into EIA result."""
    # Create a fake EIA response DataFrame
    eia_df = pd.DataFrame(
        [
            {"Region": "South Atlantic", "Fuel": "diesel_dol_per_gal", "2025": 3.5},
        ]
    )
    # Create a hydrogen fallback DataFrame
    h2_df = pd.DataFrame(
        [
            {"Region": "South Atlantic", "Fuel": "hydrogen_dol_per_gge", "2025": 8.0},
            {"Region": "New England", "Fuel": "hydrogen_dol_per_gge", "2025": 8.5},
        ]
    )

    with patch(
        "t3co.data_fetching.eia_client.EIAClient.fetch_aeo_fuel_prices",
        return_value=eia_df,
    ):
        result = build_fuel_prices_df_from_eia(
            api_key=FAKE_API_KEY,
            hydrogen_fallback_df=h2_df,
        )

    # Only South Atlantic hydrogen should be merged (matches EIA regions)
    h2_rows = result[result["Fuel"] == "hydrogen_dol_per_gge"]
    assert len(h2_rows) == 1
    assert h2_rows.iloc[0]["Region"] == "South Atlantic"


# ── Caching tests ────────────────────────────────────────────────────────────


def test_cache_write_and_read(tmp_path):
    """Cached responses are reused within TTL."""
    client = EIAClient(
        api_key=FAKE_API_KEY,
        cache_dir=tmp_path / "cache",
        cache_ttl_seconds=3600,
    )
    test_data = {"response": {"data": [], "total": 0}}
    key = client._cache_key("http://test", {"a": "1"})

    # Write
    client._write_cache(key, test_data)
    # Read back
    cached = client._read_cache(key)
    assert cached == test_data


# ── AEO discovery tests ──────────────────────────────────────────────────────


def test_discover_latest_aeo_year(eia_client):
    """discover_latest_aeo_year returns the highest numeric year from routes."""
    fake_response = {
        "response": {
            "routes": [
                {"id": "2025", "name": "2025"},
                {"id": "2023", "name": "2023"},
                {"id": "2022", "name": "2022"},
                {"id": "2014-er", "name": "2014-er"},
            ]
        }
    }
    with patch.object(eia_client, "_request", return_value=fake_response):
        year = eia_client.discover_latest_aeo_year()
    assert year == "2025"


def test_discover_latest_aeo_year_empty_raises(eia_client):
    fake_response = {"response": {"routes": []}}
    with patch.object(eia_client, "_request", return_value=fake_response):
        with pytest.raises(EIAClientError, match="Could not discover"):
            eia_client.discover_latest_aeo_year()


def test_discover_reference_scenario(eia_client):
    fake_response = _make_api_response([
        {"scenario": "aeo2023ref", "scenarioDescription": "AEO2023 Reference case"},
    ])
    with patch.object(eia_client, "_request", return_value=fake_response):
        scenario = eia_client.discover_reference_scenario("2025")
    assert scenario == "aeo2023ref"


def test_auto_resolve_latest_aeo(eia_client):
    """fetch_aeo_fuel_prices with defaults auto-discovers year and scenario."""
    discovery_calls = []

    def mock_request(route, params=None):
        discovery_calls.append(route)
        if route == "aeo/":
            return {
                "response": {
                    "routes": [
                        {"id": "2025", "name": "2025"},
                        {"id": "2023", "name": "2023"},
                    ]
                }
            }
        # Both scenario discovery and table-3 data requests hit aeo/<year>/data/
        records = []
        for year in range(2022, 2051):
            records.append(
                _make_aeo_record(
                    "prce_nom_trn_NA_dfu_NA_pcf_ndlrpmbtu",
                    "1-9", str(year), 20.0,
                )
            )
        resp = _make_api_response(records)
        if records:
            records[0]["scenario"] = "aeo2023ref"
        return resp

    with patch.object(eia_client, "_request", side_effect=mock_request):
        df = eia_client.fetch_aeo_fuel_prices(region_ids=["1-9"])

    assert "aeo/" in discovery_calls
    assert "Region" in df.columns
    assert df["Region"].iloc[0] == "Pacific"


# ── Region mapping test ──────────────────────────────────────────────────────


def test_region_mapping_covers_nine_divisions():
    """AEO_REGION_ID_TO_T3CO maps all nine US Census divisions plus national."""
    assert len(AEO_REGION_ID_TO_T3CO) == 10
    assert "1-0" in AEO_REGION_ID_TO_T3CO  # United States total
    for i in range(1, 10):
        assert f"1-{i}" in AEO_REGION_ID_TO_T3CO


# ── Credential handling ──────────────────────────────────────────────────────


def test_request_failures_never_expose_the_api_key(eia_client, caplog):
    """The API key travels as a query parameter, and requests quotes the full
    URL in its error messages. Neither the retry warnings nor the final
    error, nor anything chained beneath it, may reveal the key.
    """
    import logging
    import traceback

    import requests

    url = f"https://api.eia.gov/v2/aeo/2026/data?frequency=annual&api_key={FAKE_API_KEY}"

    def failing_get(*args, **kwargs):
        # Mirror how requests reports a connection failure: the urllib3
        # error, itself quoting the URL, is chained beneath requests' own.
        try:
            raise OSError(f"Max retries exceeded with url: {url}")
        except OSError as inner:
            raise requests.ConnectionError(f"HTTPSConnectionPool: {url}") from inner

    with (
        patch("t3co.data_fetching.eia_client.requests.get", side_effect=failing_get),
        patch("t3co.data_fetching.eia_client.time.sleep"),
        caplog.at_level(logging.WARNING, logger="t3co.data_fetching.eia_client"),
        pytest.raises(EIAClientError) as excinfo,
    ):
        eia_client._request("aeo/2026/data")

    traceback_text = "".join(
        traceback.format_exception(type(excinfo.value), excinfo.value, excinfo.value.__traceback__)
    )
    for label, text in [
        ("retry warnings", caplog.text),
        ("error message", str(excinfo.value)),
        ("full traceback", traceback_text),
    ]:
        assert FAKE_API_KEY not in text, f"API key leaked in {label}"

    assert "api_key=REDACTED" in caplog.text
    assert "api_key=REDACTED" in str(excinfo.value)
