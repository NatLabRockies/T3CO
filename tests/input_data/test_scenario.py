from pathlib import Path
from unittest.mock import patch

import numpy as np
import pandas as pd
import pytest

from t3co import utils
from t3co.input_data.config import Config
from t3co.input_data.scenario import Scenario


@pytest.fixture
def config():
    # Create a mock Config object
    config = Config()
    config.scenario_file = Path(__file__).parent / "mock_scenario_db.csv"
    config.cost_toggles = None
    return config


@pytest.fixture
def mock_scenario_db(tmp_path):
    # Create a mock scenario database CSV file
    data = """selection,scenario_name,drive_cycle,use_config,vmt,constant_trip_distance_mi,vehicle_life_yr,discount_rate_pct_per_yr,ess_max_charging_power_kw,ess_cost_dol_per_kwh,ess_base_cost_dol,shifts_per_year,mr_unplanned_downtime_hr_per_mi,maint_oper_cost_dol_per_mi,depreciation_rates_pct_per_yr
1,Scenario1,cycle1,True,"[10000, 9000, 8000]",50,10,0.05,100,300,400,"[2, 2, 2]","[0.1, 0.1, 0.1]","[0.05, 0.05, 0.05]","[0.09, 0.09, 0.09]"
2,Scenario2,cycle2,False,"[20000, 18000, 16000]",60,12,0.06,110,310,410,"[3, 3, 3]","[0.2, 0.2, 0.2]","[0.1, 0.1, 0.1]","[0.09, 0.09, 0.09]"
"""
    mock_file = tmp_path / "mock_scenario_db.csv"
    mock_file.write_text(data)
    return mock_file


def test_scenario_initialization():
    scenario = Scenario(
        selection=1,
        scenario_name="Test Scenario",
        drive_cycle="cycle1",
        use_config=True,
        vmt=[10000, 9000, 8000],
        constant_trip_distance_mi=50,
        vehicle_life_yr=3,
        discount_rate_pct_per_yr=0.05,
        ess_max_charging_power_kw=100,
        ess_cost_dol_per_kwh=300,
        ess_base_cost_dol=400,
        shifts_per_year=[2, 2, 2],
        depreciation_rates_pct_per_yr=[0.09] * 3,
        mr_unplanned_downtime_hr_per_mi=[0.1, 0.1, 0.1],
        maint_oper_cost_dol_per_mi=[0.05, 0.05, 0.05],
    )
    assert scenario.selection == 1
    assert scenario.scenario_name == "Test Scenario"
    assert scenario.drive_cycle == "cycle1"
    assert scenario.use_config is True
    assert scenario.vmt == [10000, 9000, 8000]
    assert scenario.constant_trip_distance_mi == 50
    assert scenario.vehicle_life_yr == 3
    assert scenario.discount_rate_pct_per_yr == 0.05
    assert scenario.ess_max_charging_power_kw == 100
    assert scenario.ess_cost_dol_per_kwh == 300
    assert scenario.ess_base_cost_dol == 400
    assert scenario.shifts_per_year == [2, 2, 2]
    assert scenario.mr_unplanned_downtime_hr_per_mi == [
        0.1,
        0.1,
        0.1,
    ]
    assert scenario.maint_oper_cost_dol_per_mi == [0.05, 0.05, 0.05]


def test_scenario_from_csv(config, mock_scenario_db):
    config.scenario_file = mock_scenario_db
    scenario = Scenario.from_csv(selection=1, scenario_file=config.scenario_file)
    assert scenario.selection == 1
    assert scenario.scenario_name == "Scenario1"
    assert scenario.drive_cycle == "cycle1"
    assert scenario.use_config is True
    assert scenario.vmt == [10000, 9000, 8000]
    assert scenario.constant_trip_distance_mi == 50
    assert scenario.vehicle_life_yr == 10
    assert scenario.discount_rate_pct_per_yr == 0.05
    assert scenario.ess_max_charging_power_kw == 100
    assert scenario.ess_cost_dol_per_kwh == 300
    assert scenario.ess_base_cost_dol == 400
    assert scenario.shifts_per_year == [2, 2, 2]
    assert scenario.mr_unplanned_downtime_hr_per_mi == [0.1, 0.1, 0.1]
    assert scenario.maint_oper_cost_dol_per_mi == [0.05, 0.05, 0.05]


def test_scenario_override_from_config(config, mock_scenario_db):
    config.scenario_file = mock_scenario_db
    scenario = Scenario.from_csv(selection=1, scenario_file=config.scenario_file)
    scenario.override_from_config(config=config)
    assert scenario.vehicle_life_yr == config.vehicle_life_yr
    assert scenario.fs_fueling_rate_kg_per_min == config.fs_fueling_rate_kg_per_min


def test_scenario_from_dict_uses_defaults_for_missing_fields():
    scenario = Scenario.from_dict(
        {
            "selection": 1,
            "scenario_name": "Legacy Scenario",
            "vehicle_life_yr": 2,
            "vmt": "[10000, 9000]",
            "shifts_per_year": "[250, 250]",
            "mr_unplanned_downtime_hr_per_mi": "[0.01, 0.01]",
            "maint_oper_cost_dol_per_mi": "[0.2, 0.2]",
        }
    )

    assert scenario.depreciation_rates_pct_per_yr == [0.0, 0.0]
    assert scenario.fuel_prices_file == "./auxiliary/FuelPrices.csv"
    assert scenario.mpgge == 0.0
    assert scenario.primary_fuel_range_mi == 0.0
    assert scenario.registration_fees_dol_per_yr is None
    assert scenario.registration_fees_file == "./auxiliary/RegistrationFees.csv"


@pytest.mark.parametrize(
    "raw_value, expected",
    [
        (float("nan"), None),
        ("", None),
        (300, [300, 300]),
        ("[100, 200, 300]", [100, 200]),
    ],
)
def test_scenario_from_dict_parses_registration_fees(raw_value, expected):
    scenario = Scenario.from_dict(
        {
            "selection": 1,
            "scenario_name": "Registration Scenario",
            "vehicle_life_yr": 2,
            "registration_fees_dol_per_yr": raw_value,
        }
    )
    assert scenario.registration_fees_dol_per_yr == expected


def _make_fake_eia_fuel_prices_df(*regions):
    """Build a minimal DataFrame matching the T3CO FuelPrices.csv schema."""
    if not regions:
        regions = ("Pacific",)
    year_cols = {str(y): 3.0 + y * 0.001 for y in range(2019, 2101)}
    fuels = [
        "diesel_dol_per_gal",
        "gasoline_dol_per_gal",
        "electricity_dol_per_kwh",
        "cng_dol_per_gge",
        "hydrogen_dol_per_gge",
    ]
    rows = []
    for region in regions:
        for fuel in fuels:
            row = {"Region": region, "Fuel": fuel}
            row.update(year_cols)
            rows.append(row)
    return pd.DataFrame(rows)


@pytest.mark.parametrize("analysis_id", [0, 1, 2, 3, 4, 5])
def test_demo_analysis_ids_use_temp_fuel_price_region(analysis_id):
    config = Config().from_csv(analysis_id=analysis_id)
    config.fuel_prices_json = {
        "zipcode": "80302",
        "fuel_prices": {"diesel_dol_per_gal": {"2025": 9.99}},
    }
    original_lookup = utils.lookup_zipcode
    utils.lookup_zipcode = lambda zipcode: {"zip_code": zipcode, "state": "CO"}

    def _fake_eia_load(self_inner):
        self_inner.fuel_prices_df = _make_fake_eia_fuel_prices_df(
            "Pacific", "Mountain"
        )
        self_inner.fuel_prices_region = "Pacific"

    try:
        with patch.object(
            Config,
            "_load_fuel_prices_from_eia_for_zipcode",
            _fake_eia_load,
        ):
            config.read_auxiliary_files()
    finally:
        utils.lookup_zipcode = original_lookup

    selection = (
        config.selections[0]
        if isinstance(config.selections, list)
        else config.selections
    )
    scenario = Scenario.from_csv(
        selection=selection, scenario_file=config.scenario_file
    )
    scenario.override_from_config(config=config)

    assert config.fuel_prices_source_region == "Mountain"
    assert scenario.region.startswith("zip_80302_")
    temp_region_rows = scenario.fuel_prices_df[
        scenario.fuel_prices_df["Region"] == scenario.region
    ]
    assert temp_region_rows.loc["diesel_dol_per_gal", "2025"] == pytest.approx(9.99)

    Path(config.fuel_prices_file).unlink(missing_ok=True)


def test_demo_analysis_id_5_uses_eia_region():
    """Analysis 5 has region=90210 which should trigger EIA and resolve to Pacific."""
    config = Config().from_csv(analysis_id=5)

    original_lookup = utils.lookup_zipcode
    utils.lookup_zipcode = lambda zipcode: {"zip_code": zipcode, "state": "CA"}
    def _fake_eia_load(self_inner):
        self_inner.fuel_prices_df = _make_fake_eia_fuel_prices_df("Pacific")
        self_inner.fuel_prices_region = "Pacific"

    try:
        with patch.object(
            Config,
            "_load_fuel_prices_from_eia_for_zipcode",
            _fake_eia_load,
        ):
            config.read_auxiliary_files()
    finally:
        utils.lookup_zipcode = original_lookup

    selection = (
        config.selections[0]
        if isinstance(config.selections, list)
        else config.selections
    )
    scenario = Scenario.from_csv(
        selection=selection, scenario_file=config.scenario_file
    )
    scenario.override_from_config(config=config)

    assert selection == 12
    assert config.fuel_prices_region == "Pacific"
    assert scenario.region == "Pacific"


def test_get_discounted_value():
    scenario = Scenario(discount_rate_pct_per_yr=0.05)
    discounted_value = scenario.get_discounted_value(value=1000, year_number=2)
    assert discounted_value == pytest.approx(907.03, 0.01)


def test_delete_dataframes():
    scenario = Scenario()
    scenario.df_attr = pd.DataFrame({"A": [1, 2, 3]})
    scenario.delete_dataframes()
    assert not hasattr(scenario, "df_attr")
