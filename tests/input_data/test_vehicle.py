from pathlib import Path

import pandas as pd
import pytest

from t3co.input_data.config import Config
from t3co.input_data.vehicle import Vehicle


@pytest.fixture
def config():
    # Create a mock Config object
    config = Config()
    config.selections_list = [1, 1]
    config.vehicle_file = Path(__file__).parent / "mock_vehicle_db.csv"
    return config


@pytest.fixture
def mock_vehicle_db(tmp_path):
    # Create a mock vehicle database CSV file
    data = """selection,veh_pt_type,fc_eff_type,fc_max_kw,fs_kwh,mc_max_kw,ess_max_kwh,chg_eff,glider_kg,trans_kg,cargo_kg,fc_base_kg,fs_kwh_per_kg,fc_kw_per_kg,mc_pe_kg_per_kw,mc_pe_base_kg,ess_kg_per_kwh,ess_base_kg,veh_override_kg
1,BEV,Type1,100,50,200,75,0.9,1000,500,200,300,0.5,0.1,0.05,50,0.2,100,0
2,HEV,Type2,150,60,250,80,0.85,1100,550,250,350,0.6,0.15,0.06,55,0.25,110,0
"""
    mock_file = tmp_path / "mock_vehicle_db.csv"
    mock_file.write_text(data)
    return mock_file


def test_from_config(config, mock_vehicle_db):
    config.vehicle_file = mock_vehicle_db
    vehicle = Vehicle.from_config(selection=1, config=config)
    assert vehicle.selection == 1
    assert vehicle.veh_pt_type == "BEV"
    assert vehicle.fc_eff_type == "Type1"
    assert vehicle.fc_max_kw == 100
    assert vehicle.fs_kwh == 50
    assert vehicle.mc_max_kw == 200
    assert vehicle.ess_max_kwh == 75
    assert vehicle.chg_eff == 0.9
    assert vehicle.glider_kg == 1000
    assert vehicle.trans_kg == 500
    assert vehicle.cargo_kg == 200
    assert vehicle.fc_base_kg == 300
    assert vehicle.fs_kwh_per_kg == 0.5
    assert vehicle.fc_kw_per_kg == 0.1
    assert vehicle.mc_pe_kg_per_kw == 0.05
    assert vehicle.mc_pe_base_kg == 50
    assert vehicle.ess_kg_per_kwh == 0.2
    assert vehicle.ess_base_kg == 100
    assert vehicle.veh_override_kg == 0


def test_set_veh_kg(config, mock_vehicle_db):
    config.vehicle_file = mock_vehicle_db
    vehicle = Vehicle.from_config(selection=1, config=config)
    vehicle.comp_mass_multiplier = 1.2
    vehicle.set_veh_kg()
    # glider 1000, cargo 200, and multiplied by 1.2:
    # trans 500, fs 50 / 0.5, fc 100 / 0.1 + 300, mc 50 + 0.05 * 200,
    # ess 100 + 0.2 * 75
    expected_veh_kg = 1000 + 200 + 1.2 * (500 + 100 + 1300 + 60 + 115)
    assert vehicle.veh_kg == pytest.approx(expected_veh_kg)


def test_set_veh_kg_grows_with_component_size(config, mock_vehicle_db):
    config.vehicle_file = mock_vehicle_db
    vehicle = Vehicle.from_config(selection=1, config=config)
    vehicle.set_veh_kg()
    small_kg = vehicle.veh_kg
    vehicle.ess_max_kwh *= 2
    vehicle.set_veh_kg()
    assert vehicle.veh_kg - small_kg == pytest.approx(
        vehicle.ess_kg_per_kwh * vehicle.ess_max_kwh / 2
    )


def test_set_veh_kg_uses_override(config, mock_vehicle_db):
    config.vehicle_file = mock_vehicle_db
    vehicle = Vehicle.from_config(selection=1, config=config)
    vehicle.veh_override_kg = 12345.0
    vehicle.set_veh_kg()
    assert vehicle.veh_kg == 12345.0


@pytest.mark.parametrize("ess_scale", [1.0, 2.0])
def test_set_veh_kg_matches_fastsim(ess_scale):
    """T3CO's mass must be the mass FASTSim simulates, for every demo vehicle."""
    fastsim = pytest.importorskip("fastsim")
    from t3co.constants import Global as gl

    vehicle_file = (
        gl.RESOURCES_FOLDERPATH / "inputs" / "Demo_FY22_vehicle_model_assumptions.csv"
    )
    selections = pd.read_csv(vehicle_file)["selection"]
    for selection in selections:
        vehicle = Vehicle.from_csv(selection=selection, vehicle_db_file=vehicle_file)
        vehicle.ess_max_kwh *= ess_scale
        vehicle.set_veh_kg()

        fs_vehicle = fastsim.vehicle.Vehicle.from_vehdb(
            selection, vehicle_file, to_rust=False
        )
        fs_vehicle.ess_max_kwh = vehicle.ess_max_kwh
        fs_vehicle.set_derived()
        fs_vehicle.set_veh_mass()

        assert vehicle.veh_kg == pytest.approx(fs_vehicle.veh_kg), selection


def test_delete_dataframes(config, mock_vehicle_db):
    config.vehicle_file = mock_vehicle_db
    vehicle = Vehicle.from_config(selection=1, config=config)
    vehicle.df_attr = pd.DataFrame({"A": [1, 2, 3]})
    vehicle.delete_dataframes()
    assert not hasattr(vehicle, "df_attr")
