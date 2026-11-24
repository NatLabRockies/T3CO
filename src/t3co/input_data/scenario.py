from __future__ import annotations
import ast
from dataclasses import dataclass, field
from pathlib import Path

import pandas as pd
from typing import List, Union

from t3co.input_data.toggles import Toggles

try:
    from typing import Self  # Python 3.11+
except ImportError:
    from typing_extensions import Self  # Older versions of Python

from t3co.input_data.config import Config
from t3co.utils import resolve_fuel_price_region_from_zipcode
from t3co.utils.print_class_objects import handle_nan, remove_df_attrs
from t3co.constants import Global as gl


@dataclass
class Scenario(object):
    """
    Class object that contains all TCO parameters and performance target (range, grade, accel) information
    for a vehicle such that performance and TCO can be computed during optimization.
    """

    selection: int = None
    scenario_name: str = ""
    veh_year: int = 0
    drive_cycle: str = ""
    use_config: bool = True
    vmt: list = field(default_factory=str)
    constant_trip_distance_mi: float = 0
    vehicle_life_yr: float = 0
    discount_rate_pct_per_yr: float = 0.0

    ess_max_charging_power_kw: float = 0
    ess_cost_dol_per_kwh: float = 0
    ess_base_cost_dol: float = 0
    ess_charge_rate_kW: float = 0
    pe_mc_cost_dol_per_kw: float = 0
    pe_mc_base_cost_dol: float = 0
    fc_ice_cost_dol_per_kw: float = 0
    fc_ice_base_cost_dol: float = 0
    fc_fuelcell_cost_dol_per_kw: float = 0
    fs_cost_dol_per_kwh: float = 0
    fs_h2_cost_dol_per_kwh: float = 0
    plug_base_cost_dol: float = 0
    markup_pct: float = 0
    tax_rate_pct: float = 0
    fc_cng_ice_cost_dol_per_kw: float = 0
    fs_cng_cost_dol_per_kwh: float = 0
    vehicle_glider_cost_dol: float = 0
    gvwr_kg: float = 0
    gvwr_credit_kg: float = 0
    fuel_type: str = ""
    maint_oper_cost_dol_per_mi: List[float] = field(default_factory=float)
    vocation: str = ""
    vehicle_class: str = ""
    model_year: float = 0
    region: str = ""
    target_range_mi: float = 0
    min_speed_at_6pct_grade_in_5min_mph: float = 0
    min_speed_at_1p25pct_grade_in_5min_mph: float = 0
    max_time_0_to_60mph_at_gvwr_s: float = 0
    max_time_0_to_30mph_at_gvwr_s: float = 0
    lw_imp_curve_sel: str = ""
    eng_eff_imp_curve_sel: str = ""
    aero_drag_imp_curve_sel: str = ""

    ess_init_soc_grade: float = -1.0
    ess_init_soc_accel: float = -1.0

    soc_norm_init_for_accel_pct: float = -1
    soc_norm_init_for_grade_pct: float = -1

    fs_fueling_rate_gasoline_gpm: float = 0
    fs_fueling_rate_diesel_gpm: float = 0
    fs_fueling_rate_kg_per_min: float = 0

    purchasing_method: str = ""
    purchasing_down_payment_pct: float = 0.0
    purchasing_interest_apr_pct_per_yr: float = 0.0
    purchasing_payment_frequency_months: float = 0.0
    purchasing_term_yr: float = 0.0
    leasing_money_factor: float = 0.0
    shifts_per_year: List[float] = field(default_factory=list)

    missed_trace_correction: bool = False
    max_time_dilation: float = -1
    min_time_dilation: float = -1
    time_dilation_tol: float = -1

    skip_opt: bool = False
    knob_min_ess_kwh: float = None
    knob_max_ess_kwh: float = None
    knob_min_motor_kw: float = None
    knob_max_motor_kw: float = None
    knob_min_fc_kw: float = None
    knob_max_fc_kw: float = None
    knob_min_fs_kwh: float = None
    knob_max_fs_kwh: float = None
    constraint_c_rate: bool = False
    constraint_range: bool = False
    constraint_accel: bool = False
    constraint_grade: bool = False
    objective_tco: bool = False
    constraint_trace_miss_dist_percent_on: bool = False
    trace_miss_dist_percent: float = 0

    labor_rate_dol_per_hr: float = 0
    downtime_oppy_cost_dol_per_hr: float = 0

    activate_tco_payload_cap_cost_multiplier: bool = True
    plf_ref_veh_empty_mass_kg: float = 0
    plf_scenario_vehicle_empty_kg: float = 0
    plf_reference_vehicle_cargo_capacity_kg: float = 0
    plf_scenario_vehicle_cargo_capacity_kg: float = 0
    estimated_lost_payload_kg: float = 0

    activate_tco_fueling_dwell_time_cost: bool = True
    dlf_min_charge_time_hr: float = 0
    fdt_dwpt_fraction_power_pct: float = 0
    fdt_avg_overhead_hr_per_dwell_hr: float = 0
    fdt_frac_full_charge_bounds: List[float] = field(default_factory=float)
    fdt_num_free_dwell_trips: float = 0
    fdt_available_freetime_hr: float = 0

    fuel_prices_dol_per_gge: List[float] = field(default_factory=float)
    insurance_rates_pct_per_yr: List[float] = field(default_factory=float)
    # User-supplied annual registration fees. When set, they replace the
    # registration_state lookup.
    registration_fees_dol_per_yr: List[float] = None
    registration_state: str = ""

    depreciation_rates_pct_per_yr: List[float] = field(default_factory=float)
    residual_rate_pct: float = 1.0

    activate_mr_downtime_cost: bool = True
    mr_planned_downtime_hr_per_yr: float = 0
    mr_unplanned_downtime_hr_per_mi: List[float] = field(default_factory=list)
    mr_avg_tire_life_mi: float = 0
    mr_tire_replace_downtime_hr_per_event: float = 0

    fuel_prices_file: str = "./auxiliary/FuelPrices.csv"
    fuel_prices_df: pd.DataFrame = None
    registration_fees_file: str = "./auxiliary/RegistrationFees.csv"
    plf_weight_distribution_file: str = "./auxiliary/tractorweightvars.csv"

    avg_speed_mph: float = 0.0
    msrp_total_dol: float = 0.0

    mpgge: float = 0.0
    primary_fuel_range_mi: float = 0.0

    cost_toggles_file: Union[str, Path] = gl.RESOURCES_FOLDERPATH / "cost_toggles.json"
    cost_toggles: Toggles = field(default_factory=Toggles)

    def __new__(cls, *args, **kwargs):
        """
        Creates a new instance of the Scenario class.
        """
        instance = super(Scenario, cls).__new__(cls)
        return instance

    @classmethod
    def from_config(cls, selection: int, config: Config) -> Self:
        """
        Creates a Scenario instance from the configuration.

        Args:
            selection (int): The selection index.
            config (Config): The configuration instance.

        Returns:
            Self: An instance of the Scenario class.
        """
        if config.scenario_df is not None:
            return cls.from_df(selection=selection, scenario_df=config.scenario_df)
        else:
            return cls.from_csv(selection=selection, scenario_file=config.scenario_file)

    @classmethod
    def from_csv(
        cls,
        selection: int,
        scenario_file: Union[str, Path] = gl.RESOURCES_FOLDERPATH
        / "inputs"
        / "Demo_FY22_scenario_assumptions.csv",
        config: Config = None,
    ) -> Self:
        """
        Creates a Scenario instance from a CSV file.

        Args:
            selection (int): The selection index to filter the scenario data.
            scenario_file (Union[str, Path]): Path to the scenario CSV file.

        Returns:
            Scenario: An instance of the Scenario class.
        """
        if not scenario_file.absolute():
            scenario_file = Path(config.config_filename).parent / scenario_file

        scenario_df = pd.read_csv(
            scenario_file, usecols=lambda x: x in cls.__annotations__.keys()
        )
        return cls.from_df(
            selection=selection,
            scenario_df=scenario_df,
        )

    @classmethod
    def from_df(cls, selection: int, scenario_df: pd.DataFrame) -> Self:
        """
        Creates a Scenario instance from a DataFrame.

        Args:
            selection (int): The selection index to filter the scenario data.
            scenario_df (pd.DataFrame): The scenario DataFrame.

        Returns:
            Scenario: An instance of the Scenario class.
        """
        scenario_dict = scenario_df.loc[scenario_df["selection"] == selection].to_dict(
            "records"
        )[0]

        return cls.from_dict(scenario_dict=scenario_dict)

    @classmethod
    def from_dict(cls, scenario_dict: dict) -> Self:
        """
        Creates a Scenario instance from a dictionary.

        Args:
            scenario_dict (dict): The dictionary containing scenario data.

        Returns:
            Scenario: An instance of the Scenario class.
        """
        default_scenario = cls()
        for field_name in cls.__annotations__:
            scenario_dict.setdefault(field_name, getattr(default_scenario, field_name))

        def _parse_life_year_series(
            field_name: str, fallback_value: float
        ) -> list[float]:
            raw_value = scenario_dict.get(field_name)
            if raw_value in (None, ""):
                return [fallback_value] * int(scenario_dict["vehicle_life_yr"])

            if isinstance(raw_value, str):
                parsed_value = ast.literal_eval(raw_value)
            else:
                parsed_value = raw_value

            if isinstance(parsed_value, (list, tuple)):
                return list(parsed_value)[: int(scenario_dict["vehicle_life_yr"])]

            return [parsed_value] * int(scenario_dict["vehicle_life_yr"])

        scenario_dict["vehicle_class"] = " "
        scenario_dict["vehicle_class"] = (
            scenario_dict["vehicle_class"]
            .join(scenario_dict["scenario_name"].split()[:3])
            .lower()
        )
        scenario_dict["vmt"] = _parse_life_year_series("vmt", 0.0)
        scenario_dict["shifts_per_year"] = _parse_life_year_series(
            "shifts_per_year", 0.0
        )
        scenario_dict["mr_unplanned_downtime_hr_per_mi"] = _parse_life_year_series(
            "mr_unplanned_downtime_hr_per_mi", 0.0
        )
        scenario_dict["depreciation_rates_pct_per_yr"] = _parse_life_year_series(
            "depreciation_rates_pct_per_yr", 0.0
        )
        scenario_dict["maint_oper_cost_dol_per_mi"] = _parse_life_year_series(
            "maint_oper_cost_dol_per_mi", -1.0
        )
        # A blank registration fee means "not given", so keep it as None
        # instead of filling a series of zeros.
        if handle_nan(scenario_dict.get("registration_fees_dol_per_yr")) in (None, ""):
            scenario_dict["registration_fees_dol_per_yr"] = None
        else:
            scenario_dict["registration_fees_dol_per_yr"] = _parse_life_year_series(
                "registration_fees_dol_per_yr", 0.0
            )

        return cls(**handle_nan(scenario_dict))

    def override_from_config(
        self, config: Config = None, verbose: bool = False
    ) -> Self:
        """
        Overrides certain scenario fields if use_config is True and config object is not None.

        Args:
            config (Config, optional): Config object containing configuration data. Defaults to None.
            verbose (bool, optional): If True, prints the overridden fields. Defaults to False.

        Raises:
            Exception: If config file is not attached or scenario.use_config is set to False.
        """
        fields_override = [
            "vehicle_life_yr",
            "fs_fueling_rate_kg_per_min",
            "fs_fueling_rate_gasoline_gpm",
            "fs_fueling_rate_diesel_gpm",
            "lw_imp_curve_sel",
            "eng_eff_imp_curve_sel",
            "aero_drag_imp_curve_sel",
            "purchasing_method",
            "constraint_range",
            "constraint_accel",
            "constraint_grade",
            "objective_tco",
            "constraint_c_rate",
            "constraint_trace_miss_dist_percent_on",
            "activate_tco_payload_cap_cost_multiplier",
            "activate_tco_fueling_dwell_time_cost",
            "fdt_frac_full_charge_bounds",
            "activate_mr_downtime_cost",
        ]
        try:
            if config.dc_files is None:
                fields_override.append("drive_cycle")
            self.fields_overriden = []
            if self.use_config and config is not None:
                for field_select in fields_override:
                    if config.__dict__[field_select] is not None:
                        setattr(
                            self, field_select, config.__getattribute__(field_select)
                        )
                        self.fields_overriden.append(field_select)
                print(
                    f"Scenario Fields overridden from config: {self.fields_overriden}"
                ) if verbose else None

        except Exception:
            print(
                f"Error in Config file. T3COConfig either not attached or scenario.use_config set to False: {config}"
            )

        if self.purchasing_method.lower() in [
            "loan",
            "financing",
            "autoloan",
            "borrowing",
        ]:
            self.purchasing_method = "loan"
        elif self.purchasing_method.lower() in ["leasing", "renting", "lease"]:
            self.purchasing_method = "lease"
        else:
            self.purchasing_method = "cash"

        self.insurance_rates_file = config.insurance_rates_file
        self.fuel_prices_file = config.fuel_prices_file
        self.fuel_prices_df = config.fuel_prices_df
        if config.registration_fees_file:
            self.registration_fees_file = config.registration_fees_file
        if config.fuel_prices_region:
            self.region = config.fuel_prices_region

        if self.activate_tco_payload_cap_cost_multiplier and config:
            self.plf_weight_distribution_file = config.plf_weight_dist_file

        if config.cost_toggles is not None:
            self.cost_toggles = config.cost_toggles

        self._resolve_zipcode_region(config)

    def _resolve_zipcode_region(self, config: Config) -> None:
        """If ``self.region`` is a US zipcode and the ``eia_fuel_prices``
        toggle is enabled, resolves it to the corresponding census division
        and fetches EIA fuel prices for that region.

        If the config already resolved a zipcode (``config.fuel_prices_region``
        is set), this method is a no-op.
        """
        if config.fuel_prices_region:
            return
        if not Config._is_zipcode(self.region):
            return
        if not getattr(self, "cost_toggles", None):
            return
        if not self.cost_toggles.eia_fuel_prices:
            return

        import os
        from t3co.data_fetching.eia_client import (
            T3CO_TO_AEO_REGION_ID,
            build_fuel_prices_df_from_eia,
        )

        Config._load_dotenv()

        region_val = self.region
        if isinstance(region_val, float) and region_val == int(region_val):
            region_val = int(region_val)
        zipcode = str(region_val).strip()
        region_name = resolve_fuel_price_region_from_zipcode(zipcode)
        aeo_region_id = T3CO_TO_AEO_REGION_ID.get(region_name)
        if not aeo_region_id:
            return

        api_key = os.environ.get("T3CO_EIA_API_KEY", "")
        if not api_key:
            return

        hydrogen_fallback_df = None
        if self.fuel_prices_file:
            try:
                from t3co.utils.print_class_objects import get_path_object
                hydrogen_fallback_df = pd.read_csv(
                    get_path_object(self.fuel_prices_file)
                )
            except Exception:
                pass

        self.fuel_prices_df = build_fuel_prices_df_from_eia(
            api_key=api_key,
            aeo_year=config.eia_aeo_year or None,
            scenario=config.eia_aeo_case or None,
            hydrogen_fallback_df=hydrogen_fallback_df,
            region_ids=[aeo_region_id],
        )
        self.fuel_prices_df = self.fuel_prices_df.set_index("Fuel")
        self.region = region_name
        print(
            f"Scenario zipcode {zipcode} resolved to EIA region: {region_name}"
        )

    def get_discounted_value(self, value: float, year_number: int) -> float:
        """
        Calculates the discounted value for a given year.

        Args:
            value (float): The value to be discounted.
            year_number (int): The year number for discounting.

        Returns:
            float: The discounted value.
        """
        return value / (1 + self.discount_rate_pct_per_yr) ** (year_number)

    def delete_dataframes(self) -> None:
        """
        Deletes DataFrame attributes from the Scenario instance.
        """
        remove_df_attrs(self)
