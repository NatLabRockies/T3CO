import ast
from dataclasses import dataclass, field
import json
import os
from pathlib import Path
import re
import sys
import tempfile
import uuid

from t3co.input_data.toggles import Toggles

try:
    from typing import Self  # Python 3.11+
except ImportError:
    from typing_extensions import Self  # Older versions of Python

from typing import Optional, Tuple, Union
import numpy as np
import pandas as pd
from t3co.constants import Global as gl
from t3co.utils import resolve_fuel_price_region_from_zipcode
from t3co.utils.print_class_objects import get_path_object, remove_df_attrs


ALLOWED_FUEL_PRICE_PAYLOAD_KEYS = {"zipcode", "fuel_prices"}
ZIPCODE_REGION_PREFIX = "zip"


@dataclass
class Config:
    analysis_id: int = 0
    analysis_name: str = ""
    vehicle_file: Union[str, Path] = (
        gl.RESOURCES_FOLDERPATH / "inputs" / "Demo_FY22_vehicle_model_assumptions.csv"
    )
    scenario_file: Union[str, Path] = (
        gl.RESOURCES_FOLDERPATH / "inputs" / "Demo_FY22_scenario_assumptions.csv"
    )
    dst_dir: str = ""
    resfile_suffix: str = None
    include_calcs: bool = False
    exclude_list_fields: bool = False
    summary_group_by: Union[str, list] = None
    selections: Union[str, list] = ""
    vehicle_life_yr: float = 0
    drive_cycle: str = None

    # Fueling
    ess_max_charging_power_kw: float = 0
    fs_fueling_rate_kg_per_min: float = 0
    fs_fueling_rate_gasoline_gpm: float = 0
    fs_fueling_rate_diesel_gpm: float = 0

    insurance_rates_file: str = ""
    energy_file: str = None
    fuel_prices_file: str = ""
    fuel_prices_json: Union[str, dict] = None
    fuel_prices_zipcode: Union[str, int] = None
    fuel_prices_region: str = None
    fuel_prices_source_region: str = None
    region: str = None
    eia_aeo_year: str = None
    eia_aeo_case: str = None
    plf_weight_dist_file: str = None
    cost_toggles_file: str = gl.RESOURCES_FOLDERPATH / "inputs" / "cost_toggles.json"

    TCO_method: str = gl.DIRECT_TCO_METHOD
    purchasing_method: str = "cash"

    # Optimization
    algorithms: str = "NSGA2"
    lw_imp_curves: str = ""
    eng_eff_imp_curves: str = ""
    aero_drag_imp_curves: str = ""
    lw_imp_curve_sel: str = ""
    eng_eff_imp_curve_sel: str = ""
    aero_drag_imp_curve_sel: str = ""
    skip_all_opt: bool = True
    constraint_range: bool = False
    constraint_accel: bool = False
    constraint_grade: bool = False
    objective_tco: bool = False
    constraint_c_rate: bool = False
    constraint_trace_miss_dist_percent_on: bool = False
    x_tol: float = 0.001
    f_tol: float = 0.001
    n_max_gen: int = 1000
    pop_size: int = 25
    nth_gen: int = 1
    n_last: int = 5

    # Opportunity Cost
    activate_tco_payload_cap_cost_multiplier: bool = False
    activate_tco_fueling_dwell_time_cost: bool = False
    fdt_frac_full_charge_bounds: list = field(default_factory=list)
    activate_mr_downtime_cost: bool = False

    n_processes: int = 9
    parallel: bool = True

    selections_list: list[str] = None
    dc_files: list[str] = None

    vehicle_df: pd.DataFrame = None
    scenario_df: pd.DataFrame = None
    energy_df: pd.DataFrame = None
    fuel_prices_df: pd.DataFrame = None
    config_filename: Union[str, Path] = gl.RESOURCES_FOLDERPATH / "T3COConfig.csv"
    vehicle_db_df: pd.DataFrame = None
    scenario_df: pd.DataFrame = None

    def _load_fuel_prices_payload(self) -> Optional[dict]:
        """
        Loads optional JSON fuel price overrides from a JSON string, file path, or dict.
        """
        if self.fuel_prices_json is None:
            return None

        if isinstance(self.fuel_prices_json, dict):
            return self.fuel_prices_json

        fuel_prices_json = str(self.fuel_prices_json).strip()
        if not fuel_prices_json:
            return None

        payload_path = Path(fuel_prices_json)
        if payload_path.exists():
            with open(payload_path, "r") as fuel_prices_file:
                return json.load(fuel_prices_file)

        return json.loads(fuel_prices_json)

    def _normalize_fuel_price_overrides(self, payload: dict) -> Tuple[str, str, dict]:
        """
        Extracts and validates the zipcode-based fuel price overrides from a payload.
        """
        invalid_keys = set(payload).difference(ALLOWED_FUEL_PRICE_PAYLOAD_KEYS)
        if invalid_keys:
            invalid_keys_text = ", ".join(sorted(invalid_keys))
            raise ValueError(
                "Fuel price override payload only supports 'zipcode' and 'fuel_prices'. "
                f"Unexpected keys: {invalid_keys_text}"
            )

        zipcode = self._sanitize_zipcode(
            payload.get("zipcode") or self.fuel_prices_zipcode
        )
        fuel_prices = payload.get("fuel_prices")
        if not isinstance(fuel_prices, dict) or not fuel_prices:
            raise ValueError(
                "Fuel price override payload must include a non-empty 'fuel_prices' mapping"
            )

        region_name = f"{ZIPCODE_REGION_PREFIX}_{zipcode}_{uuid.uuid4().hex[:8]}"
        return zipcode, region_name, fuel_prices

    def _sanitize_zipcode(self, zipcode_value: Union[str, int, None]) -> str:
        """
        Validates and normalizes a US zipcode to its 5-digit form.
        """
        if zipcode_value is None:
            raise ValueError(
                "Fuel price overrides require a US zipcode via payload['zipcode'] or config.fuel_prices_zipcode"
            )

        zipcode = str(zipcode_value).strip()
        zipcode_match = re.fullmatch(r"(\d{5})(?:-\d{4})?", zipcode)
        if zipcode_match is None:
            raise ValueError(
                "Fuel price override zipcode must be a 5-digit US zipcode or ZIP+4 string"
            )

        return zipcode_match.group(1)

    def _resolve_fuel_price_region_from_zipcode(self, zipcode: str) -> str:
        """
        Resolves a 5-digit US zipcode to the matching fuel price region.
        """
        return resolve_fuel_price_region_from_zipcode(zipcode)

    def _create_temporary_fuel_price_region(self) -> None:
        """
        Creates a temporary fuel price CSV by cloning a base region and applying JSON overrides.
        """
        payload = self._load_fuel_prices_payload()
        if payload is None:
            return

        zipcode, region_name, fuel_price_overrides = (
            self._normalize_fuel_price_overrides(payload)
        )

        if (
            "Region" not in self.fuel_prices_df.columns
            or "Fuel" not in self.fuel_prices_df.columns
        ):
            raise ValueError("Fuel prices CSV must contain 'Region' and 'Fuel' columns")

        base_region = self._resolve_fuel_price_region_from_zipcode(zipcode)

        region_rows = self.fuel_prices_df[
            self.fuel_prices_df["Region"] == base_region
        ].copy()
        if region_rows.empty:
            raise ValueError(f"Fuel price base region '{base_region}' was not found")

        region_rows.loc[:, "Region"] = region_name

        for fuel_name, year_values in fuel_price_overrides.items():
            if not isinstance(year_values, dict):
                raise ValueError(
                    f"Fuel price overrides for '{fuel_name}' must map years to values"
                )

            fuel_mask = region_rows["Fuel"] == fuel_name
            if not fuel_mask.any():
                template_rows = self.fuel_prices_df[
                    self.fuel_prices_df["Fuel"] == fuel_name
                ]
                if template_rows.empty:
                    raise ValueError(
                        f"Fuel price overrides reference unknown fuel '{fuel_name}'"
                    )
                new_row = template_rows.iloc[[0]].copy()
                new_row.loc[:, "Region"] = region_name
                region_rows = pd.concat([region_rows, new_row], ignore_index=True)
                fuel_mask = region_rows["Fuel"] == fuel_name

            for year, value in year_values.items():
                year_column = str(year)
                if year_column not in region_rows.columns:
                    raise ValueError(
                        f"Fuel price overrides reference unknown year column '{year_column}'"
                    )
                try:
                    numeric_value = float(value)
                except (TypeError, ValueError) as exc:
                    raise ValueError(
                        f"Fuel price override for '{fuel_name}' year '{year_column}' must be numeric"
                    ) from exc
                if (
                    not np.isfinite(numeric_value)
                    or numeric_value < 0
                    or numeric_value > 1000
                ):
                    raise ValueError(
                        f"Fuel price override for '{fuel_name}' year '{year_column}' must be between 0 and 1000"
                    )
                region_rows.loc[fuel_mask, year_column] = numeric_value

        self.fuel_prices_df = self.fuel_prices_df[
            self.fuel_prices_df["Region"] != region_name
        ].copy()
        self.fuel_prices_df = pd.concat(
            [self.fuel_prices_df, region_rows], ignore_index=True
        )

        with tempfile.NamedTemporaryFile(
            mode="w", suffix=".csv", prefix="t3co_fuel_prices_", delete=False
        ) as fuel_prices_temp_file:
            temp_file_path = Path(fuel_prices_temp_file.name)

        self.fuel_prices_df.to_csv(temp_file_path, index=False)
        self.fuel_prices_file = temp_file_path
        self.fuel_prices_region = region_name
        self.fuel_prices_source_region = base_region

    def __new__(cls, *args, **kwargs):
        """
        Creates a new instance of the Config class.
        """
        instance = super(Config, cls).__new__(cls)
        return instance

    def from_csv(
        self,
        analysis_id: int = 0,
        filename: str = gl.RESOURCES_FOLDERPATH / "T3COConfig.csv",
    ) -> Self:
        """
        Generates a Config dictionary from CSV file and calls Config.from_dict.

        Args:
            filename (str): Path of input T3CO Config file.
            analysis_id (int): Analysis ID selections.

        Returns:
            Self: Config instance containing all values from T3CO Config CSV file.
        """
        self.config_filename = Path(filename)
        self.analysis_id = analysis_id
        config_df = self.validate_analysis_id()
        config_dict = config_df.to_dict()

        return self.from_dict(config_dict=config_dict)

    def from_dict(self, config_dict: dict) -> Self:
        """
        Generates a Config instance from config_dict.

        Args:
            config_dict (dict): Dictionary containing fields from T3CO Config input CSV file.

        Returns:
            Self: Config instance containing all values from T3CO Config CSV file.
        """
        try:
            config_dict["selections"] = ast.literal_eval(config_dict["selections"])
        except:
            config_dict["selections"] = int(config_dict["selections"])

        for key, val in config_dict.items():
            if key in self.__annotations__ and self.__annotations__[key] == bool:
                if isinstance(val, str):
                    if val.lower() == "true":
                        config_dict[key] = True
                    elif val.lower() == "false":
                        config_dict[key] = False

        self.__dict__.update(config_dict)

        self.read_vehicle_and_scenario_db_files()
        return self

    def read_vehicle_and_scenario_db_files(self) -> None:
        """
        Reads vehicle and scenario database files into DataFrame attributes.
        """
        # Resolve paths relative to config file if they are relative
        config_parent = Path(self.config_filename).parent.resolve()
        for attr in [
            "vehicle_file",
            "scenario_file",
            "cost_toggles_file",
            "fuel_prices_file",
            "energy_file",
            "plf_weight_dist_file",
            "insurance_rates_file",
        ]:
            val = getattr(self, attr)
            if val and not Path(val).is_absolute():
                setattr(self, attr, config_parent / val)

        self.vehicle_db_df = pd.read_csv(get_path_object(self.vehicle_file))
        self.scenario_df = pd.read_csv(get_path_object(self.scenario_file))

    def validate_analysis_id(self) -> pd.DataFrame:
        """
        Validates that the correct analysis ID is input.

        Returns:
            pd.DataFrame: DataFrame containing the configuration data for the given analysis ID.

        Raises:
            Exception: If analysis_id is not found or config file does not exist.
        """
        try:
            if (
                self.config_filename.exists()
                and self.config_filename.suffix.lower() == ".csv"
            ):
                config_df = pd.read_csv(self.config_filename, index_col="analysis_id")
            else:
                raise FileExistsError

            config_df = config_df.loc[self.analysis_id].replace({np.nan: None})
            return config_df

        except FileExistsError:
            print(f"Config file ({self.config_filename}) does not exist")
            sys.exit(1)

        except:
            print(
                f"T3CO terminated. Analysis ID not available. Try these analysis_id's instead: {config_df.index.to_list()}"
            )
            sys.exit(1)

    def check_drivecycles_and_create_selections(self) -> None:
        """
        Checks if the config.drive_cycle input is a file or a folder. If a folder is provided, creates a list of all selections for each drive cycle in the folder as config.dc_files.
        """
        if self.drive_cycle:
            self.drive_cycle = (
                Path(self.drive_cycle).resolve(strict=True)
                if Path(self.drive_cycle).is_absolute()
                else Path(self.config_filename).parents[0] / self.drive_cycle
            )
            if Path(self.drive_cycle).is_dir():
                self.dc_files = [
                    p.absolute() for p in Path(self.drive_cycle).rglob("*.csv")
                ]
                self.selections_list = []
                for selection in self.selections:
                    for i in range(len(self.dc_files)):
                        self.selections_list.append(
                            str(selection) + "_" + str(i).zfill(4)
                        )

            else:
                self.selections_list = self.selections

        elif self.energy_file:
            self.energy_df = pd.read_csv(get_path_object(self.energy_file))
            self.dc_files = self.energy_df["drive_cycle"].tolist()
            self.selections_list = []
            for selection in self.selections:
                for i in range(len(self.dc_files)):
                    self.selections_list.append(str(selection) + "_" + str(i).zfill(4))
        elif (
            self.selections == -1 or self.selections == [-1]
        ) and self.vehicle_db_df is not None:
            self.selections_list = self.vehicle_db_df["selection"].tolist()
        else:
            self.selections_list = self.selections

    @staticmethod
    def _is_zipcode(value) -> bool:
        """Returns True if *value* looks like a 5-digit US zipcode (or ZIP+4)."""
        if value is None:
            return False
        if isinstance(value, float) and value == int(value):
            value = int(value)
        return bool(re.fullmatch(r"\d{5}(?:-\d{4})?", str(value).strip()))

    def read_auxiliary_files(self) -> None:
        """
        Reads auxiliary files such as fuel prices and residual rates.

        If the config ``region`` is a US zipcode **and** the
        ``eia_fuel_prices`` toggle is enabled, fuel prices for the
        corresponding census division are fetched from the EIA AEO API.
        Otherwise the static CSV pointed to by ``fuel_prices_file`` is used.
        """

        self.vehicle_df = pd.read_csv(get_path_object(self.vehicle_file))
        self.scenario_df = pd.read_csv(get_path_object(self.scenario_file))
        self.cost_toggles = Toggles.from_json(get_path_object(self.cost_toggles_file))

        if self._is_zipcode(self.region) and self.cost_toggles.eia_fuel_prices:
            self._load_fuel_prices_from_eia_for_zipcode()
        else:
            self.fuel_prices_df = pd.read_csv(
                get_path_object(self.fuel_prices_file)
            )

        self._create_temporary_fuel_price_region()

        self.fuel_prices_df = self.fuel_prices_df.set_index("Fuel")

    @staticmethod
    def _load_dotenv() -> None:
        """
        Reads a .env file from the working directory (if present) and
        loads its KEY=VALUE pairs into os.environ without overwriting
        existing variables.
        """
        env_path = Path.cwd() / ".env"
        if not env_path.is_file():
            return
        with open(env_path) as f:
            for line in f:
                line = line.strip()
                if not line or line.startswith("#") or "=" not in line:
                    continue
                key, _, value = line.partition("=")
                key = key.strip()
                value = value.strip().strip('"').strip("'")
                if key and key not in os.environ:
                    os.environ[key] = value

    def _load_fuel_prices_from_eia_for_zipcode(self) -> None:
        """
        Resolves the config ``region`` zipcode to a census division, then
        fetches fuel prices from the EIA AEO API for that single region.

        Sets ``fuel_prices_region`` so that
        :meth:`Scenario.override_from_config` propagates the resolved
        region to the scenario.
        """
        self._load_dotenv()

        from t3co.data_fetching.eia_client import (
            T3CO_TO_AEO_REGION_ID,
            build_fuel_prices_df_from_eia,
        )

        region_val = self.region
        if isinstance(region_val, float) and region_val == int(region_val):
            region_val = int(region_val)
        zipcode = str(region_val).strip()
        region_name = resolve_fuel_price_region_from_zipcode(zipcode)

        aeo_region_id = T3CO_TO_AEO_REGION_ID.get(region_name)
        if not aeo_region_id:
            raise ValueError(
                f"Could not map region '{region_name}' (from zipcode {zipcode}) "
                f"to an EIA AEO region ID"
            )

        api_key = os.environ.get("T3CO_EIA_API_KEY", "")
        if not api_key:
            raise ValueError(
                "EIA API key required for zipcode-based fuel price lookup. "
                "Set T3CO_EIA_API_KEY in a .env file or as an environment "
                "variable, or pass --eia-api-key on the command line."
            )

        hydrogen_fallback_df = None
        if self.fuel_prices_file:
            try:
                hydrogen_fallback_df = pd.read_csv(
                    get_path_object(self.fuel_prices_file)
                )
            except Exception:
                pass

        self.fuel_prices_df = build_fuel_prices_df_from_eia(
            api_key=api_key,
            aeo_year=self.eia_aeo_year or None,
            scenario=self.eia_aeo_case or None,
            hydrogen_fallback_df=hydrogen_fallback_df,
            region_ids=[aeo_region_id],
        )
        self.fuel_prices_region = region_name
        print(
            f"Successfully loaded fuel prices from EIA for zipcode "
            f"{zipcode} (region: {region_name})"
        )

    def __getstate__(self):
        state = self.__dict__.copy()
        # Remove unpicklable DataFrames
        keys_to_remove = [
            "vehicle_db_df",
            "scenario_df",
            "energy_df",
            "fuel_prices_df",
        ]
        for key in keys_to_remove:
            if key in state:
                del state[key]
        return state

    def __setstate__(self, state):
        self.__dict__.update(state)
        # Reload DataFrames
        self.read_vehicle_and_scenario_db_files()
        self.read_auxiliary_files()
        # Reload energy_df if needed
        if self.energy_file:
            self.energy_df = pd.read_csv(get_path_object(self.energy_file))

    def delete_dataframes(self) -> None:
        """
        Deletes DataFrame attributes from the Config instance.
        """
        if self.dc_files:
            delattr(self, "dc_files")
        if self.selections_list:
            delattr(self, "selections_list")
        remove_df_attrs(self)
