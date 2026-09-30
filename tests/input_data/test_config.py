import pandas as pd
import pytest
from pathlib import Path

from t3co import utils
from t3co.input_data.config import Config


@pytest.fixture
def mock_config_file(tmp_path):
    # Create dummy vehicle and scenario files
    (tmp_path / "vehicle.csv").write_text("selection,veh_pt_type\n1,BEV")
    (tmp_path / "scenario.csv").write_text("selection,scenario_name\n1,Test")

    # Create a mock config CSV file
    data = f"""analysis_id,analysis_name,vehicle_file,scenario_file,dst_dir,resfile_suffix,selections,vehicle_life_yr,drive_cycle,ess_max_charging_power_kw,fs_fueling_rate_kg_per_min,fs_fueling_rate_gasoline_gpm,fs_fueling_rate_diesel_gpm,insurance_rates_file,fuel_prices_file,plf_weight_dist_file,TCO_method,algorithms,lw_imp_curves,eng_eff_imp_curves,aero_drag_imp_curves,lw_imp_curve_sel,eng_eff_imp_curve_sel,aero_drag_imp_curve_sel,skip_all_opt,constraint_range,constraint_accel,constraint_grade,objective_tco,constraint_c_rate,constraint_trace_miss_dist_percent_on,activate_tco_payload_cap_cost_multiplier,activate_tco_fueling_dwell_time_cost,fdt_frac_full_charge_bounds,activate_mr_downtime_cost
1,Test Analysis,{tmp_path / "vehicle.csv"},{tmp_path / "scenario.csv"},dst_dir,suffix,"[1, 2, 3]",10,drive_cycle.csv,100,200,300,400,insurance.csv,fuel.csv,weight_dist.csv,DIRECT,algorithms,lw_imp_curves,eng_eff_curves,aero_drag_curves,lw_imp_curve_sel,eng_eff_imp_curve_sel,aero_drag_imp_curve_sel,True,False,False,False,False,False,False,False,False,,False
"""
    mock_file = tmp_path / "mock_config.csv"
    mock_file.write_text(data)
    return mock_file


def test_config_initialization():
    config = Config(
        analysis_id=1,
        analysis_name="Test Analysis",
        vehicle_file="vehicle.csv",
        scenario_file="scenario.csv",
        dst_dir="dst_dir",
        resfile_suffix="suffix",
        selections=[1, 2, 3],
        vehicle_life_yr=10,
        drive_cycle="drive_cycle.csv",
        ess_max_charging_power_kw=100,
        fs_fueling_rate_kg_per_min=200,
        fs_fueling_rate_gasoline_gpm=300,
        fs_fueling_rate_diesel_gpm=400,
        insurance_rates_file="insurance.csv",
        fuel_prices_file="fuel.csv",
        plf_weight_dist_file="weight_dist.csv",
        TCO_method="DIRECT",
        algorithms="algorithms",
        lw_imp_curves="lw_imp_curves",
        eng_eff_imp_curves="eng_eff_curves",
        aero_drag_imp_curves="aero_drag_curves",
        lw_imp_curve_sel="lw_imp_curve_sel",
        eng_eff_imp_curve_sel="eng_eff_imp_curve_sel",
        aero_drag_imp_curve_sel="aero_drag_imp_curve_sel",
        skip_all_opt=True,
        constraint_range=False,
        constraint_accel=False,
        constraint_grade=False,
        objective_tco=False,
        constraint_c_rate=False,
        constraint_trace_miss_dist_percent_on=False,
        activate_tco_payload_cap_cost_multiplier=False,
        activate_tco_fueling_dwell_time_cost=False,
        fdt_frac_full_charge_bounds=[],
        activate_mr_downtime_cost=False,
    )
    assert config.analysis_id == 1
    assert config.analysis_name == "Test Analysis"
    assert config.vehicle_file == "vehicle.csv"
    assert config.scenario_file == "scenario.csv"
    assert config.dst_dir == "dst_dir"
    assert config.resfile_suffix == "suffix"
    assert config.selections == [1, 2, 3]
    assert config.vehicle_life_yr == 10
    assert config.drive_cycle == "drive_cycle.csv"
    assert config.ess_max_charging_power_kw == 100
    assert config.fs_fueling_rate_kg_per_min == 200
    assert config.fs_fueling_rate_gasoline_gpm == 300
    assert config.fs_fueling_rate_diesel_gpm == 400
    assert config.insurance_rates_file == "insurance.csv"
    assert config.fuel_prices_file == "fuel.csv"
    assert config.plf_weight_dist_file == "weight_dist.csv"
    assert config.TCO_method == "DIRECT"
    assert config.algorithms == "algorithms"
    assert config.lw_imp_curves == "lw_imp_curves"
    assert config.eng_eff_imp_curves == "eng_eff_curves"
    assert config.aero_drag_imp_curves == "aero_drag_curves"
    assert config.lw_imp_curve_sel == "lw_imp_curve_sel"
    assert config.eng_eff_imp_curve_sel == "eng_eff_imp_curve_sel"
    assert config.aero_drag_imp_curve_sel == "aero_drag_imp_curve_sel"
    assert config.skip_all_opt is True
    assert config.constraint_range is False
    assert config.constraint_accel is False
    assert config.constraint_grade is False
    assert config.objective_tco is False
    assert config.constraint_c_rate is False
    assert config.constraint_trace_miss_dist_percent_on is False
    assert config.activate_tco_payload_cap_cost_multiplier is False
    assert config.activate_tco_fueling_dwell_time_cost is False
    assert config.fdt_frac_full_charge_bounds == []
    assert config.activate_mr_downtime_cost is False


def test_config_from_csv(mock_config_file):
    config = Config().from_csv(filename=mock_config_file, analysis_id=1)
    assert config.analysis_id == 1
    assert config.analysis_name == "Test Analysis"
    assert Path(config.vehicle_file).name == "vehicle.csv"
    assert Path(config.scenario_file).name == "scenario.csv"
    assert config.dst_dir == "dst_dir"
    assert config.resfile_suffix == "suffix"
    assert config.selections == [1, 2, 3]
    assert config.vehicle_life_yr == 10
    assert config.drive_cycle == "drive_cycle.csv"
    assert config.ess_max_charging_power_kw == 100
    assert config.fs_fueling_rate_kg_per_min == 200
    assert config.fs_fueling_rate_gasoline_gpm == 300
    assert config.fs_fueling_rate_diesel_gpm == 400
    assert Path(config.insurance_rates_file).name == "insurance.csv"
    assert Path(config.fuel_prices_file).name == "fuel.csv"
    assert Path(config.plf_weight_dist_file).name == "weight_dist.csv"
    assert config.TCO_method == "DIRECT"
    assert config.algorithms == "algorithms"
    assert config.lw_imp_curves == "lw_imp_curves"
    assert config.eng_eff_imp_curves == "eng_eff_curves"
    assert config.aero_drag_imp_curves == "aero_drag_curves"
    assert config.lw_imp_curve_sel == "lw_imp_curve_sel"
    assert config.eng_eff_imp_curve_sel == "eng_eff_imp_curve_sel"
    assert config.aero_drag_imp_curve_sel == "aero_drag_imp_curve_sel"
    assert config.skip_all_opt is True
    assert config.constraint_range is False
    assert config.constraint_accel is False
    assert config.constraint_grade is False
    assert config.objective_tco is False
    assert config.constraint_c_rate is False
    assert config.constraint_trace_miss_dist_percent_on is False
    assert config.activate_tco_payload_cap_cost_multiplier is False
    assert config.activate_tco_fueling_dwell_time_cost is False
    assert config.fdt_frac_full_charge_bounds == None
    assert config.activate_mr_downtime_cost is False


def test_validate_analysis_id(mock_config_file):
    config = Config(config_filename=mock_config_file, analysis_id=1)
    config_df = config.validate_analysis_id()
    assert not config_df.empty
    assert config_df["analysis_name"] == "Test Analysis"


def test_check_drivecycles_and_create_selections(mock_config_file, tmp_path):
    # Create a mock drive cycle folder with CSV files
    drive_cycle_folder = tmp_path / "drive_cycle_folder"
    drive_cycle_folder.mkdir()
    (drive_cycle_folder / "cycle1.csv").write_text("data")
    (drive_cycle_folder / "cycle2.csv").write_text("data")

    config = Config(config_filename=mock_config_file, analysis_id=1)
    config.drive_cycle = drive_cycle_folder
    config.check_drivecycles_and_create_selections()
    assert config.dc_files is not None
    assert len(config.dc_files) == 2
    assert config.selections_list is not None


def test_read_auxiliary_files(mock_config_file, tmp_path):
    # Create mock auxiliary files
    fuel_prices_data = """Fuel,Price
Gasoline,2.5
Diesel,3.0
"""
    fuel_prices_file = tmp_path / "fuel_prices.csv"
    fuel_prices_file.write_text(fuel_prices_data)

    # Create mock cost toggles file
    cost_toggles_data = "{}"
    cost_toggles_file = tmp_path / "cost_toggles.json"
    cost_toggles_file.write_text(cost_toggles_data)

    config = Config(
        config_filename=mock_config_file,
        fuel_prices_file=fuel_prices_file,
        cost_toggles_file=cost_toggles_file,
    )
    config.read_auxiliary_files()
    assert not config.fuel_prices_df.empty


def test_read_auxiliary_files_creates_temp_region_from_json(mock_config_file, tmp_path):
    fuel_prices_data = """Region,Fuel,2020,2021
Mountain,diesel_dol_per_gal,3.0,3.1
Mountain,electricity_dol_per_kwh,0.12,0.13
"""
    fuel_prices_file = tmp_path / "fuel_prices.csv"
    fuel_prices_file.write_text(fuel_prices_data)

    cost_toggles_file = tmp_path / "cost_toggles.json"
    cost_toggles_file.write_text("{}")

    config = Config(
        config_filename=mock_config_file,
        fuel_prices_file=fuel_prices_file,
        cost_toggles_file=cost_toggles_file,
        fuel_prices_json={
            "zipcode": "80302",
            "fuel_prices": {
                "diesel_dol_per_gal": {"2021": 4.25},
                "electricity_dol_per_kwh": {"2020": 0.2},
            },
        },
    )
    original_lookup = utils.lookup_zipcode
    utils.lookup_zipcode = lambda zipcode: {"zip_code": zipcode, "state": "CO"}

    try:
        config.read_auxiliary_files()
    finally:
        utils.lookup_zipcode = original_lookup

    assert config.fuel_prices_source_region == "Mountain"
    assert config.fuel_prices_region.startswith("zip_80302_")
    assert config.fuel_prices_file != fuel_prices_file
    assert Path(config.fuel_prices_file).exists()
    temp_region_rows = config.fuel_prices_df[
        config.fuel_prices_df["Region"] == config.fuel_prices_region
    ]
    assert temp_region_rows.loc["diesel_dol_per_gal", "2021"] == pytest.approx(4.25)
    assert temp_region_rows.loc["electricity_dol_per_kwh", "2020"] == pytest.approx(0.2)

    Path(config.fuel_prices_file).unlink(missing_ok=True)


def test_read_auxiliary_files_rejects_invalid_fuel_price_payload(
    mock_config_file, tmp_path
):
    fuel_prices_data = """Region,Fuel,2025
Mountain,diesel_dol_per_gal,3.0
"""
    fuel_prices_file = tmp_path / "fuel_prices.csv"
    fuel_prices_file.write_text(fuel_prices_data)

    cost_toggles_file = tmp_path / "cost_toggles.json"
    cost_toggles_file.write_text("{}")

    config = Config(
        config_filename=mock_config_file,
        fuel_prices_file=fuel_prices_file,
        cost_toggles_file=cost_toggles_file,
        fuel_prices_json={
            "zipcode": "80A02",
            "region": "should_not_be_allowed",
            "fuel_prices": {"diesel_dol_per_gal": {"2025": 4.25}},
        },
    )

    with pytest.raises(ValueError):
        config.read_auxiliary_files()


def test_read_auxiliary_files_rejects_unknown_zipcode_dataset_result(
    mock_config_file, tmp_path
):
    fuel_prices_data = """Region,Fuel,2025
Mountain,diesel_dol_per_gal,3.0
"""
    fuel_prices_file = tmp_path / "fuel_prices.csv"
    fuel_prices_file.write_text(fuel_prices_data)

    cost_toggles_file = tmp_path / "cost_toggles.json"
    cost_toggles_file.write_text("{}")

    config = Config(
        config_filename=mock_config_file,
        fuel_prices_file=fuel_prices_file,
        cost_toggles_file=cost_toggles_file,
        fuel_prices_json={
            "zipcode": "80302",
            "fuel_prices": {"diesel_dol_per_gal": {"2025": 4.25}},
        },
    )
    original_lookup = utils.lookup_zipcode
    utils.lookup_zipcode = lambda zipcode: {"zip_code": zipcode, "state": "PR"}

    try:
        with pytest.raises(ValueError, match="unsupported state 'PR'"):
            config.read_auxiliary_files()
    finally:
        utils.lookup_zipcode = original_lookup


def test_delete_dataframes():
    config = Config()
    config.df_attr = pd.DataFrame({"A": [1, 2, 3]})
    config.delete_dataframes()
    assert not hasattr(config, "df_attr")


def test_config_from_csv_survives_a_pickle_round_trip():
    """Every optimizer pool worker unpickles the Config, so it must survive that.

    Config.__setstate__ re-reads the auxiliary files on unpickle, so a Config
    whose file paths are still at their placeholder defaults raises inside each
    worker. Pool then replaces the dead worker, the replacement dies the same
    way, and the run hangs with no error rather than failing.
    """
    import pickle

    from t3co.input_data.config import Config

    config = Config()
    config.from_csv(filename=str(Config().config_filename), analysis_id=1)
    config.check_drivecycles_and_create_selections()
    config.read_auxiliary_files()

    restored = pickle.loads(pickle.dumps(config))

    assert restored.analysis_id == config.analysis_id
    assert restored.cost_toggles is not None
    assert restored.fuel_prices_df is not None
