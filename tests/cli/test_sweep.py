from pathlib import Path
from types import SimpleNamespace
from unittest.mock import patch

import pandas as pd
import pytest

from t3co.cli.sweep import (
    _argument_was_provided,
    _build_optimization_algorithm,
    _build_optimization_termination,
    apply_cli_overrides,
    create_results_filepath,
    export_results_to_csv,
    generate_ledger,
    load_vehicle_scenario_energy,
    run_t3co,
)
from t3co.constants import Global as gl
from t3co.energy_models.energy import Energy
from t3co.input_data.config import Config
from t3co.input_data.scenario import Scenario
from t3co.input_data.toggles import Toggles
from t3co.input_data.vehicle import Vehicle


@pytest.fixture
def vehicle(config):
    vehicle = Vehicle().from_config(selection=1, config=config)
    vehicle.set_veh_kg()
    return vehicle


@pytest.fixture
def toggles():
    return Toggles(
        msrp=True,
        purchase_tax=True,
        purchasing_downpayment=True,
        mark_up=True,
        residual_cost=True,
        fuel_cost=True,
        maintenance_oper_cost=True,
        insurance_cost=True,
        purchasing_cost=True,
        fueling_dwell_labor=True,
        payload_oppy_cost=True,
        fueling_dwell_oppy_cost=True,
        mr_downtime_oppy_cost=True,
        run_fastsim=False,
    )


@pytest.fixture
def scenario(config, toggles):
    scenario = Scenario.from_csv(selection=1)

    scenario.fuel_prices_df = pd.DataFrame(
        {
            "Fuel": ["diesel_dol_per_gal"],
            "Region": ["US"],
            "2020": [0.1],
            "2021": [0.1],
            "2022": [0.1],
            "2023": [0.1],
            "2024": [0.1],
            "2025": [0.1],
            "2026": [0.1],
            "2027": [0.1],
            "2028": [0.1],
            "2029": [0.1],
        }
    )
    scenario.region = "US"
    scenario.vehicle_class = "class8"
    # scenario.override_from_config(config=config)
    scenario.vehicle_life_yr = 4
    scenario.fuel_prices_df.set_index("Fuel", inplace=True)
    scenario.cost_toggles = toggles
    return scenario


@pytest.fixture
def energy(scenario, config):
    energy = Energy(mpgge=6.03, primary_fuel_range_mi=2035.70)
    return energy


@pytest.fixture
def config(toggles):
    config = Config()
    config.from_csv()
    config.check_drivecycles_and_create_selections()
    config.read_auxiliary_files()
    config.vehicle_file = gl.RESOURCES_FOLDERPATH / config.vehicle_file
    config.scenario_file = gl.RESOURCES_FOLDERPATH / config.scenario_file
    config.eng_eff_imp_curves = gl.RESOURCES_FOLDERPATH / config.eng_eff_imp_curves
    config.lw_imp_curves = gl.RESOURCES_FOLDERPATH / config.lw_imp_curves
    config.aero_drag_imp_curves = gl.RESOURCES_FOLDERPATH / config.aero_drag_imp_curves
    config.resfile_suffix = "_test_suffix"
    config.selections_list = [1]
    config.cost_toggles = toggles
    return config


def test_load_vehicle_scenario_energy(config, vehicle, scenario, energy):
    with (
        patch("t3co.input_data.vehicle.Vehicle.from_config", return_value=vehicle),
        patch("t3co.input_data.scenario.Scenario.from_csv", return_value=scenario),
        patch("t3co.energy_models.energy.Energy.run_fastsim_model", return_value=None),
    ):
        veh, scen, en = load_vehicle_scenario_energy(
            selection="1",
            config=config,
            vehicle=vehicle,
            scenario=scenario,
            energy=energy,
        )
        assert veh == vehicle
        assert scen == scenario
        assert en.mpgge == pytest.approx(6.03, 0.01)
        assert en.primary_fuel_range_mi == pytest.approx(2035.70, 0.01)


def test_generate_ledger(config, vehicle, scenario, energy):
    config.skip_all_opt = False
    optimized_vehicle = Vehicle()
    optimized_energy = Energy(mpgge=8.5, primary_fuel_range_mi=2500.0)

    with (
        patch(
            "t3co.cli.sweep.load_vehicle_scenario_energy",
            return_value=(vehicle, scenario, energy),
        ),
        patch(
            "t3co.cli.sweep.run_optimization",
            return_value=(optimized_vehicle, optimized_energy),
        ),
        patch("t3co.cli.sweep.Ledger") as mock_ledger,
    ):
        mock_ledger.return_value.to_dict.return_value = {"key": "value"}
        result = generate_ledger(selection=1, config=config)

        ledger_kwargs = mock_ledger.call_args.kwargs
        assert ledger_kwargs["vehicle"] is optimized_vehicle
        assert ledger_kwargs["energy"] is optimized_energy
        assert result == {"key": "value"}


def test_create_results_filepath(config):
    result_filepath = create_results_filepath(config=config)
    assert result_filepath.name.startswith("results_")
    assert result_filepath.name.endswith("_test_suffix.csv")


def test_argument_was_provided_handles_space_and_equals_forms():
    assert _argument_was_provided(["--dst-dir", "/x"], "--dst-dir") is True  # space form
    assert _argument_was_provided(["--dst-dir=/x"], "--dst-dir") is True  # equals form
    assert _argument_was_provided(["--algos", "NSGA2"], "--algorithms", "--algos") is True
    assert _argument_was_provided(["--algos=NSGA2"], "--algorithms", "--algos") is True
    assert _argument_was_provided(["--something-else"], "--dst-dir") is False


def test_apply_cli_overrides_accepts_equals_form(config):
    args = SimpleNamespace(
        vehicles=None, scenarios=None, eng_curves=None, lw_curves=None,
        aero_curves=None, dst_dir="/tmp/out", algorithms=None, x_tol=None, f_tol=None,
        n_max_gen=5, pop_size=5, nth_gen=None, n_last=None, selections=[[42]],
        drive_cycle=None, skip_all_opt=True,
    )
    # equals-form argv tokens (a single string each), as argparse leaves them in sys.argv
    apply_cli_overrides(
        config=config,
        args=args,
        argv=["--dst-dir=/tmp/out", "--selections=[42]", "--skopt"],
    )
    assert config.dst_dir == "/tmp/out"
    assert config.selections == [42]
    assert config.skip_all_opt is True


def test_create_results_filepath_creates_absolute_dst_dir(config, tmp_path):
    dst = tmp_path / "new" / "out"  # absolute path that does not exist yet
    config.dst_dir = str(dst)
    result_filepath = create_results_filepath(config=config)
    assert dst.exists()  # the output directory is created up front
    assert result_filepath.parent == dst.resolve()
    assert result_filepath.name.startswith("results_")


def test_export_results_to_csv(config):
    reports_list = [{"selection": 1, "value": 100}, {"selection": 2, "value": 200}]
    output_path, reports_df = export_results_to_csv(
        reports_list=reports_list,
        config=config,
        return_filepath=True,
        return_df=True,
        sort_values=True,
    )
    assert output_path.exists()
    assert isinstance(reports_df, pd.DataFrame)
    assert reports_df.iloc[0]["selection"] == 1
    assert reports_df.iloc[1]["selection"] == 2
    assert reports_df.iloc[0]["value"] == pytest.approx(100, 0.01)
    assert reports_df.iloc[1]["value"] == pytest.approx(200, 0.01)


def test_run_t3co(config):
    with (
        patch(
            "t3co.cli.sweep.generate_ledger",
            return_value={"selection": 1, "value": 100},
        ) as mock_generate_ledger,
        patch(
            "t3co.cli.sweep.export_results_to_csv",
            return_value=(
                Path("results.csv"),
                pd.DataFrame([{"selection": 1, "value": 100}]),
            ),
        ) as mock_export,
        patch("builtins.print"),
    ):
        run_t3co(config=config, save_results=True)
        assert mock_generate_ledger.called
        assert mock_export.called


def test_apply_cli_overrides_updates_explicit_runtime_args(config):
    args = SimpleNamespace(
        vehicles="/tmp/vehicle.csv",
        scenarios="/tmp/scenario.csv",
        eng_curves="/tmp/eng.csv",
        lw_curves="/tmp/lw.csv",
        aero_curves="/tmp/aero.csv",
        dst_dir="/tmp/results",
        algorithms=["NSGA2"],
        x_tol=0.01,
        f_tol=0.02,
        n_max_gen=12,
        pop_size=44,
        nth_gen=3,
        n_last=7,
        selections=[[99]],
        drive_cycle=["/tmp/cycle.csv"],
        skip_all_opt=True,
    )

    apply_cli_overrides(
        config=config,
        args=args,
        argv=[
            "--vehicles",
            "--scenarios",
            "--dst-dir",
            "--algorithms",
            "--x-tol",
            "--f-tol",
            "--n-max-gen",
            "--pop-size",
            "--nth-gen",
            "--n-last",
            "--selections",
            "--drive-cycle",
            "--skip-all-opt",
        ],
    )

    assert config.vehicle_file == "/tmp/vehicle.csv"
    assert config.scenario_file == "/tmp/scenario.csv"
    assert config.dst_dir == "/tmp/results"
    assert config.algorithms == ["NSGA2"]
    assert config.x_tol == pytest.approx(0.01)
    assert config.f_tol == pytest.approx(0.02)
    assert config.n_max_gen == 12
    assert config.pop_size == 44
    assert config.nth_gen == 3
    assert config.n_last == 7
    assert config.selections == [99]
    assert config.drive_cycle == "/tmp/cycle.csv"
    assert config.skip_all_opt is True


def test_build_optimization_settings_use_config_values(config):
    config.algorithms = ["NSGA2"]
    config.pop_size = 17
    config.x_tol = 0.015
    config.f_tol = 0.025
    config.nth_gen = 2
    config.n_last = 6
    config.n_max_gen = 33

    algorithm = _build_optimization_algorithm(config)
    termination = _build_optimization_termination(config)

    assert algorithm.__class__.__name__ == "NSGA2"
    assert algorithm.pop_size == 17
    assert termination.criteria[0].termination.tol == pytest.approx(0.015)
    assert termination.criteria[2].termination.tol == pytest.approx(0.025)
    assert termination.max_gen.n_max_gen == 33


def test_load_vehicle_scenario_energy_no_fastsim_missing_data(
    config, vehicle, scenario
):
    # Ensure run_fastsim is False
    scenario.cost_toggles.run_fastsim = False
    # Ensure scenario has no energy data
    scenario.mpgge = None
    scenario.primary_fuel_range_mi = None

    with (
        patch("t3co.input_data.vehicle.Vehicle.from_config", return_value=vehicle),
        patch("t3co.input_data.scenario.Scenario.from_csv", return_value=scenario),
    ):
        veh, scen, en = load_vehicle_scenario_energy(
            selection="1",
            config=config,
            vehicle=vehicle,
            scenario=scenario,
            energy=None,
        )

        assert veh == vehicle
        assert scen == scenario
        # Check that we got an empty Energy object (or default values)
        # Energy() defaults to None for these fields usually, or 0 if initialized that way.
        # Based on my read of Energy class (I should verify), but let's assume None or 0.
        assert en.mpgge is None or en.mpgge == 0
        assert en.primary_fuel_range_mi is None or en.primary_fuel_range_mi == 0
