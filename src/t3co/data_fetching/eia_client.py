"""
EIA (Energy Information Administration) API v2 client for fetching fuel price
projections from the Annual Energy Outlook (AEO).

Usage:
    client = EIAClient(api_key="your_key")
    df = client.fetch_aeo_fuel_prices()  # auto-discovers latest AEO year

The returned DataFrame matches the T3CO FuelPrices.csv schema:
    Region | Fuel | 2019 | 2020 | ... | 2100
"""

import hashlib
import json
import logging
import os
import re
import tempfile
import time
from pathlib import Path
from typing import Dict, List, Optional, Union
from urllib.parse import urlencode

import numpy as np
import pandas as pd

try:
    import requests
    from urllib3.exceptions import InsecureRequestWarning
except ImportError:
    requests = None
    InsecureRequestWarning = None

try:
    import truststore
    truststore.inject_into_ssl()
except ImportError:
    pass

logger = logging.getLogger(__name__)

# requests puts the full request URL, query string included, into its error
# messages, and the API key travels as a query parameter.
_API_KEY_IN_URL = re.compile(r"(api_key=)[^&\s'\"]+")


def _redact_api_key(text) -> str:
    """Return ``text`` with any ``api_key=<value>`` query value masked."""
    return _API_KEY_IN_URL.sub(r"\1REDACTED", str(text))

EIA_BASE_URL = "https://api.eia.gov/v2"

# ── AEO Region IDs → T3CO Region Names ──────────────────────────────────────
AEO_REGION_ID_TO_T3CO = {
    "1-1": "New England",
    "1-2": "Middle Atlantic",
    "1-3": "East North Central",
    "1-4": "West North Central",
    "1-5": "South Atlantic",
    "1-6": "East South Central",
    "1-7": "West South Central",
    "1-8": "Mountain",
    "1-9": "Pacific",
    "1-0": "United States",
}

T3CO_TO_AEO_REGION_ID = {v: k for k, v in AEO_REGION_ID_TO_T3CO.items()}

# ── EIA AEO Series ID Prefixes → T3CO Fuel Names ────────────────────────────
# Table 3: Energy Prices by Sector and Source (in $/MMBtu)
#
# Series IDs are region-specific: the penultimate segment encodes the census
# division (e.g. "pcf" = Pacific, "neengl" = New England, "mtn" = Mountain).
# We match on the *prefix* up to and including the "NA_" before the region
# token, so a single mapping works for every region.
AEO_SERIES_TO_FUEL = {
    # Transportation sector – diesel fuel
    "prce_nom_trn_NA_dfu_NA_": {
        "fuel": "diesel_dol_per_gal",
        "mmbtu_per_unit": 0.137381,  # 1 gal diesel ≈ 137,381 BTU HHV
    },
    # Average price to all users – motor gasoline
    "prce_nom_ten_NA_mgs_NA_": {
        "fuel": "gasoline_dol_per_gal",
        "mmbtu_per_unit": 0.120476,  # 1 gal gasoline ≈ 120,476 BTU HHV
    },
    # Commercial sector – electricity
    "prce_nom_comm_NA_elc_NA_": {
        "fuel": "electricity_dol_per_kwh",
        "mmbtu_per_unit": 0.003412,  # 1 kWh = 3,412 BTU
    },
    # Commercial sector – natural gas (used as CNG proxy)
    "prce_nom_comm_NA_ng_NA_": {
        "fuel": "cng_dol_per_gge",
        "mmbtu_per_unit": 0.120476,  # 1 GGE ≈ 120,476 BTU
    },
}

# Years covered in T3CO FuelPrices.csv
T3CO_YEAR_RANGE = range(2019, 2101)

# Default cache TTL in seconds (24 hours)
DEFAULT_CACHE_TTL_SECONDS = 86400

# Max rows per EIA API request
EIA_MAX_LENGTH = 5000


class EIAClientError(Exception):
    """Raised when the EIA API returns an error or is unreachable."""


class EIAClient:
    """
    Client for querying the EIA Open Data API v2 to retrieve AEO fuel price
    projections and convert them to T3CO FuelPrices.csv format.
    """

    def __init__(
        self,
        api_key: str,
        base_url: str = EIA_BASE_URL,
        cache_dir: Optional[Union[str, Path]] = None,
        cache_ttl_seconds: int = DEFAULT_CACHE_TTL_SECONDS,
        max_retries: int = 3,
        ssl_verify: Optional[Union[bool, str]] = None,
    ):
        if requests is None:
            raise ImportError(
                "The 'requests' package is required for EIA API queries. "
                "Install it with: pip install requests"
            )
        if not api_key:
            raise ValueError(
                "An EIA API key is required. Register at https://www.eia.gov/opendata/register.php "
                "and set the T3CO_EIA_API_KEY environment variable or pass --eia-api-key."
            )
        self.api_key = api_key
        self.base_url = base_url.rstrip("/")
        self.cache_dir = Path(cache_dir or tempfile.gettempdir()) / "t3co_eia_cache"
        self.cache_dir.mkdir(parents=True, exist_ok=True)
        self.cache_ttl_seconds = cache_ttl_seconds
        self.max_retries = max_retries
        self.ssl_verify = self._resolve_ssl_verify(ssl_verify)
        if self.ssl_verify is False and InsecureRequestWarning is not None:
            import warnings
            warnings.filterwarnings("ignore", category=InsecureRequestWarning)

    @staticmethod
    def _resolve_ssl_verify(ssl_verify: Optional[Union[bool, str]]) -> Union[bool, str]:
        """Determine the ``verify`` value for requests.

        Priority:
        1. Explicit *ssl_verify* argument (bool or path to CA bundle).
        2. ``T3CO_SSL_VERIFY`` env-var  ("false"/"0" → disable, path → CA bundle).
        3. ``REQUESTS_CA_BUNDLE`` / ``CURL_CA_BUNDLE`` env-vars (standard).
        4. Default ``True`` (use certifi bundle).
        """
        if ssl_verify is not None:
            return ssl_verify

        env_val = os.environ.get("T3CO_SSL_VERIFY", "").strip()
        if env_val:
            if env_val.lower() in ("false", "0", "no"):
                logger.warning(
                    "SSL verification disabled via T3CO_SSL_VERIFY=%s. "
                    "Connections to the EIA API will NOT be verified.",
                    env_val,
                )
                return False
            return env_val  # treat as path to CA bundle

        for var in ("REQUESTS_CA_BUNDLE", "CURL_CA_BUNDLE"):
            bundle = os.environ.get(var, "").strip()
            if bundle:
                return bundle

        return True

    # ── Core API request ─────────────────────────────────────────────────

    def _request(self, route: str, params: Optional[Union[dict, List[tuple]]] = None) -> dict:
        """
        Makes a GET request to the EIA API with retry and caching.
        Params can be a dict or a list of (key, value) tuples (for repeated keys).
        """
        url = f"{self.base_url}/{route.strip('/')}"

        # Normalise to list-of-tuples so repeated keys (facets) are preserved
        if isinstance(params, dict):
            param_list = list(params.items())
        elif params:
            param_list = list(params)
        else:
            param_list = []
        param_list.append(("api_key", self.api_key))

        cache_key = self._cache_key(url, sorted(param_list))
        cached = self._read_cache(cache_key)
        if cached is not None:
            logger.debug("EIA cache hit: %s", cache_key)
            return cached

        last_error = None
        for attempt in range(1, self.max_retries + 1):
            try:
                resp = requests.get(url, params=param_list, timeout=30, verify=self.ssl_verify)
                resp.raise_for_status()
                data = resp.json()
                if "error" in data:
                    raise EIAClientError(
                        f"EIA API error: {data['error']} (code {data.get('code', '?')})"
                    )
                self._write_cache(cache_key, data)
                return data
            except requests.RequestException as exc:
                last_error = exc
                if attempt < self.max_retries:
                    wait = 2 ** attempt
                    logger.warning(
                        "EIA request failed (attempt %d/%d), retrying in %ds: %s",
                        attempt,
                        self.max_retries,
                        wait,
                        _redact_api_key(exc),
                    )
                    time.sleep(wait)
        # "from None" rather than "from last_error": the chained requests
        # exception, and the urllib3 error inside it on connection failures,
        # both carry the unredacted URL and would print it in any traceback.
        raise EIAClientError(
            f"EIA API request failed after {self.max_retries} attempts: "
            f"{_redact_api_key(last_error)}"
        ) from None

    # ── AEO discovery ────────────────────────────────────────────────────

    def discover_latest_aeo_year(self) -> str:
        """Query ``/v2/aeo/`` and return the most recent numeric AEO
        publication year (e.g. ``"2025"``)."""
        data = self._request("aeo/")
        routes = data.get("response", {}).get("routes", [])
        numeric_years = []
        for r in routes:
            rid = r.get("id", "")
            if rid.isdigit():
                numeric_years.append(int(rid))
        if not numeric_years:
            raise EIAClientError(
                "Could not discover any AEO publication years from the EIA API"
            )
        latest = str(max(numeric_years))
        logger.info("Latest AEO publication year: %s", latest)
        return latest

    def discover_reference_scenario(self, aeo_year: str) -> str:
        """Query the facets for *aeo_year* and return the reference-case
        scenario ID (the one whose name contains ``ref``)."""
        data = self._request(
            f"aeo/{aeo_year}/data/",
            [
                ("facets[tableId][]", "3"),
                ("facets[regionId][]", "1-0"),
                ("frequency", "annual"),
                ("data[]", "value"),
                ("length", "1"),
            ],
        )
        rows = data.get("response", {}).get("data", [])
        if rows:
            scenario = rows[0].get("scenario", "")
            if scenario:
                logger.info(
                    "Reference scenario for AEO %s: %s", aeo_year, scenario
                )
                return scenario

        raise EIAClientError(
            f"Could not discover the reference scenario for AEO {aeo_year}"
        )

    def _resolve_aeo_params(
        self, aeo_year: Optional[str], scenario: Optional[str]
    ) -> tuple:
        """Resolve *aeo_year* and *scenario* to concrete values.

        * ``aeo_year`` of ``"latest"`` / ``None`` / ``""`` → auto-discover.
        * ``scenario`` of ``None`` / ``""`` → auto-discover for the resolved
          *aeo_year*.
        """
        if not aeo_year or aeo_year.lower() == "latest":
            aeo_year = self.discover_latest_aeo_year()
        if not scenario:
            scenario = self.discover_reference_scenario(aeo_year)
        return aeo_year, scenario

    # ── AEO fuel price fetching ──────────────────────────────────────────

    def fetch_aeo_fuel_prices(
        self,
        aeo_year: Optional[str] = None,
        scenario: Optional[str] = None,
        region_ids: Optional[List[str]] = None,
    ) -> pd.DataFrame:
        """
        Fetches AEO fuel price projections and returns a DataFrame matching
        the T3CO FuelPrices.csv schema (Region, Fuel, year-columns).

        Args:
            aeo_year: AEO publication year (e.g. "2023", "2025").  Pass
                ``"latest"`` or ``None`` to auto-discover the most recent.
            scenario: AEO scenario case ID.  Pass ``None`` to auto-discover
                the reference case for the resolved *aeo_year*.
            region_ids: List of EIA region IDs to fetch. Defaults to all
                        census divisions (1-1 through 1-9).

        Returns:
            DataFrame with columns: Region, Fuel, 2019, 2020, ..., 2100
        """
        aeo_year, scenario = self._resolve_aeo_params(aeo_year, scenario)

        if region_ids is None:
            region_ids = list(AEO_REGION_ID_TO_T3CO.keys())

        raw_data = self._fetch_aeo_table3_data(
            aeo_year=aeo_year,
            scenario=scenario,
            region_ids=region_ids,
        )

        # Group records by regionId and transform each region
        all_rows = []
        from collections import defaultdict
        by_region = defaultdict(list)
        for record in raw_data:
            by_region[record.get("regionId", "")].append(record)

        for region_id in region_ids:
            t3co_region = AEO_REGION_ID_TO_T3CO.get(region_id)
            if not t3co_region:
                logger.warning("Unknown EIA region ID '%s', skipping", region_id)
                continue

            region_rows = self._transform_aeo_to_t3co(
                raw_data=by_region.get(region_id, []),
                t3co_region=t3co_region,
            )
            all_rows.extend(region_rows)

        if not all_rows:
            raise EIAClientError(
                f"No fuel price data returned from EIA AEO {aeo_year} "
                f"scenario '{scenario}' for regions {region_ids}"
            )

        df = pd.DataFrame(all_rows)

        # Ensure all T3CO year columns exist
        year_cols = [str(y) for y in T3CO_YEAR_RANGE]
        for col in year_cols:
            if col not in df.columns:
                df[col] = np.nan

        # Reorder columns: Region, Fuel, then years in order
        ordered_cols = ["Region", "Fuel"] + year_cols
        df = df[[c for c in ordered_cols if c in df.columns]]

        # Extrapolate: fill years before AEO start with earliest available,
        # and years after AEO end with latest available + inflation trend
        df = self._extrapolate_years(df)

        return df

    def _fetch_aeo_table3_data(
        self,
        aeo_year: str,
        scenario: str,
        region_ids: List[str],
        series_ids: Optional[List[str]] = None,
    ) -> List[dict]:
        """
        Fetches Table 3 (Energy Prices by Sector and Source) data from AEO.
        Sends all regions in a single API call.  Series IDs are NOT sent as
        facets because they contain a region-specific suffix that varies per
        census division; instead all Table 3 data for the requested regions is
        fetched and filtered client-side in ``_transform_aeo_to_t3co``.

        Returns the raw data list from the API response.
        """
        route = f"aeo/{aeo_year}/data/"

        param_list = [
            ("facets[scenario][]", scenario),
            ("facets[tableId][]", "3"),
        ]
        for rid in region_ids:
            param_list.append(("facets[regionId][]", rid))

        param_list.append(("frequency", "annual"))
        param_list.append(("data[]", "value"))
        param_list.append(("length", str(EIA_MAX_LENGTH)))

        response = self._request(route, param_list)
        data = response.get("response", {}).get("data", [])
        return data

    @staticmethod
    def _match_series_prefix(series_id: str) -> Optional[dict]:
        """Return the AEO_SERIES_TO_FUEL mapping if *series_id* starts with
        any known prefix, otherwise ``None``."""
        for prefix, mapping in AEO_SERIES_TO_FUEL.items():
            if series_id.startswith(prefix):
                return mapping
        return None

    def _transform_aeo_to_t3co(
        self,
        raw_data: List[dict],
        t3co_region: str,
    ) -> List[dict]:
        """
        Converts raw AEO API data ($/MMBtu) to T3CO fuel price rows
        ($/gal, $/kWh, $/GGE).  Series IDs are matched by *prefix* because
        the region-specific suffix varies per census division.
        """
        fuel_data: Dict[str, Dict[str, float]] = {}
        fuel_mappings: Dict[str, dict] = {}

        for record in raw_data:
            sid = record.get("seriesId", "")
            period = record.get("period", "")
            value = record.get("value")
            if not period or value is None:
                continue
            mapping = self._match_series_prefix(sid)
            if mapping is None:
                continue
            try:
                value = float(value)
            except (TypeError, ValueError):
                continue
            fuel_name = mapping["fuel"]
            fuel_data.setdefault(fuel_name, {})[period] = value
            fuel_mappings[fuel_name] = mapping

        rows = []
        for fuel_name, year_values in fuel_data.items():
            mmbtu_per_unit = fuel_mappings[fuel_name]["mmbtu_per_unit"]

            row = {"Region": t3co_region, "Fuel": fuel_name}
            for year_str, price_per_mmbtu in year_values.items():
                price_native = price_per_mmbtu * mmbtu_per_unit
                row[year_str] = round(price_native, 9)

            rows.append(row)

        return rows

    @staticmethod
    def _extrapolate_years(df: pd.DataFrame) -> pd.DataFrame:
        """
        Fills missing year columns by:
        - Backfilling years before the earliest AEO data with that year's value.
        - Forward-extrapolating years after the latest AEO data using the
          compound annual growth rate of the last 5 available years.
        """
        year_cols = [c for c in df.columns if c not in ("Region", "Fuel")]
        year_ints = sorted(int(c) for c in year_cols)
        if not year_ints:
            return df

        for idx in df.index:
            values = df.loc[idx, [str(y) for y in year_ints]]
            non_null = values.dropna()
            if non_null.empty:
                continue

            first_year = int(non_null.index[0])
            last_year = int(non_null.index[-1])

            # Backfill
            earliest_val = non_null.iloc[0]
            for y in year_ints:
                if y < first_year:
                    df.loc[idx, str(y)] = earliest_val

            # Forward extrapolation using CAGR of last 5 years
            tail_years = sorted(int(y) for y in non_null.index)[-5:]
            if len(tail_years) >= 2:
                v_start = float(non_null[str(tail_years[0])])
                v_end = float(non_null[str(tail_years[-1])])
                n_years = tail_years[-1] - tail_years[0]
                if v_start > 0 and v_end > 0 and n_years > 0:
                    cagr = (v_end / v_start) ** (1.0 / n_years) - 1.0
                else:
                    cagr = 0.0
            else:
                cagr = 0.0

            last_val = float(non_null.iloc[-1])
            for y in year_ints:
                if y > last_year:
                    years_out = y - last_year
                    df.loc[idx, str(y)] = round(
                        last_val * (1.0 + cagr) ** years_out, 9
                    )

        return df

    # ── Caching helpers ──────────────────────────────────────────────────

    def _cache_key(self, url: str, params) -> str:
        raw = json.dumps({"url": url, "params": params}, sort_keys=True, default=str)
        return hashlib.sha256(raw.encode()).hexdigest()[:16]

    def _read_cache(self, key: str) -> Optional[dict]:
        cache_file = self.cache_dir / f"{key}.json"
        if not cache_file.exists():
            return None
        age = time.time() - cache_file.stat().st_mtime
        if age > self.cache_ttl_seconds:
            cache_file.unlink(missing_ok=True)
            return None
        try:
            return json.loads(cache_file.read_text())
        except (json.JSONDecodeError, OSError):
            cache_file.unlink(missing_ok=True)
            return None

    def _write_cache(self, key: str, data: dict) -> None:
        cache_file = self.cache_dir / f"{key}.json"
        try:
            cache_file.write_text(json.dumps(data))
        except OSError:
            pass


def build_fuel_prices_df_from_eia(
    api_key: str,
    aeo_year: Optional[str] = None,
    scenario: Optional[str] = None,
    hydrogen_fallback_df: Optional[pd.DataFrame] = None,
    region_ids: Optional[List[str]] = None,
) -> pd.DataFrame:
    """
    High-level helper that fetches AEO fuel prices via the EIA API and
    returns a complete DataFrame in T3CO FuelPrices.csv format.

    Hydrogen prices are not available in AEO. If a fallback DataFrame is
    provided (e.g. from the existing FuelPrices.csv), hydrogen rows will
    be copied from it. Otherwise, hydrogen rows are omitted with a warning.

    Args:
        api_key: EIA API key.
        aeo_year: AEO publication year.  ``None`` or ``"latest"`` →
            auto-discover the most recent AEO.
        scenario: AEO scenario case ID.  ``None`` → auto-discover the
            reference case for the resolved year.
        hydrogen_fallback_df: Optional DataFrame with hydrogen rows to merge.
        region_ids: Optional list of AEO region IDs to fetch (e.g. ["1-9"]).
                    Defaults to all census divisions.

    Returns:
        DataFrame with columns: Region, Fuel, 2019, 2020, ..., 2100
    """
    client = EIAClient(api_key=api_key)
    df = client.fetch_aeo_fuel_prices(
        aeo_year=aeo_year, scenario=scenario, region_ids=region_ids
    )

    # AEO doesn't include hydrogen prices. Merge from fallback if available.
    if hydrogen_fallback_df is not None:
        h2_rows = hydrogen_fallback_df[
            hydrogen_fallback_df["Fuel"] == "hydrogen_dol_per_gge"
        ].copy()
        if not h2_rows.empty:
            # Only include regions that exist in the EIA data
            eia_regions = set(df["Region"].unique())
            h2_rows = h2_rows[h2_rows["Region"].isin(eia_regions)]
            if not h2_rows.empty:
                df = pd.concat([df, h2_rows], ignore_index=True)
    else:
        logger.warning(
            "Hydrogen prices are not available from EIA AEO. "
            "Hydrogen fuel cost calculations will fail unless a fallback is provided."
        )

    return df
