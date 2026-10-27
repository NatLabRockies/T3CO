import pytest
from unittest.mock import patch

from t3co.constants import Global as gl
from t3co.input_data.scenario import Scenario

try:
    import fastsim

    from t3co.energy_models.fastsim_model.fastsim_wrapper import RunFASTSim

    fastsim_installed = True
except ImportError:
    fastsim_installed = False
except AttributeError:
    fastsim_installed = False


@pytest.fixture
def scenario():
    return Scenario(
        drive_cycle=gl.RESOURCES_FOLDERPATH
        / "cycles"
        / "EPA_Ph2_urban_highway_55mph.csv",
        constant_trip_distance_mi=100.0,
        vmt=[10000] * 10,
        model_year=2020,
        region="US",
        fuel_type="electricity",
        activate_tco_payload_cap_cost_multiplier=True,
        activate_tco_fueling_dwell_time_cost=True,
        activate_mr_downtime_cost=True,
        fdt_dwpt_fraction_power_pct=0.1,
        fdt_frac_full_charge_bounds="[0.2, 0.8]",
        fdt_avg_overhead_hr_per_dwell_hr=0.5,
        downtime_oppy_cost_dol_per_hr=50.0,
        shifts_per_year=[250] * 10,
        fdt_num_free_dwell_trips=0,
        fdt_available_freetime_hr=0,
        mr_planned_downtime_hr_per_yr=10.0,
        mr_unplanned_downtime_hr_per_mi=[0.01] * 10,
        mr_avg_tire_life_mi=50000.0,
        mr_tire_replace_downtime_hr_per_event=2.0,
    )


@pytest.fixture
def fastsim_vehicle():
    if not fastsim_installed:
        pytest.skip("fastsim extra not installed")
    return fastsim.vehicle.Vehicle.from_vehdb(
        1,
        gl.RESOURCES_FOLDERPATH / "inputs" / "Demo_FY22_vehicle_model_assumptions.csv",
        to_rust=True,
    )


@pytest.fixture
def fastsim_cycle():
    if not fastsim_installed:
        pytest.skip("fastsim extra not installed")
    return fastsim.cycle.Cycle.from_file(
        gl.RESOURCES_FOLDERPATH / "cycles" / "EPA_Ph2_urban_highway_55mph.csv"
    )


def test_run_fastsim_initialization(scenario, fastsim_vehicle, fastsim_cycle):
    if not fastsim_installed:
        pytest.skip("fastsim extra not installed")
    with (
        patch("fastsim.vehicle.Vehicle.from_vehdb", return_value=fastsim_vehicle),
        patch("fastsim.cycle.Cycle.from_file", return_value=fastsim_cycle),
    ):
        run_fastsim = RunFASTSim(veh_no=1, scenario=scenario, use_rust=False)
        assert run_fastsim.vehicle == fastsim_vehicle
        assert run_fastsim.cycles == fastsim_cycle
        # assert run_fastsim.mpgge == pytest.approx(fastsim_cycle.mpgge, 0.01)


def test_load_vehicle(scenario, fastsim_vehicle):
    if not fastsim_installed:
        pytest.skip("fastsim extra not installed")
    with patch("fastsim.vehicle.Vehicle.from_vehdb", return_value=fastsim_vehicle):
        run_fastsim = RunFASTSim(veh_no=1, scenario=scenario)
        run_fastsim.load_vehicle(
            veh_no=1,
            veh_input_path=gl.RESOURCES_FOLDERPATH
            / "inputs"
            / "Demo_FY22_vehicle_model_assumptions.csv",
            use_rust=False,
        )
        assert run_fastsim.vehicle == fastsim_vehicle


def test_load_design_cycle_from_scenario(scenario, fastsim_cycle):
    if not fastsim_installed:
        pytest.skip("fastsim extra not installed")
    with patch("fastsim.cycle.Cycle.from_file", return_value=fastsim_cycle):
        run_fastsim = RunFASTSim(veh_no=1, scenario=scenario)
        cycles = run_fastsim.load_design_cycle_from_scenario(
            scenario=scenario, return_rustcycle=False
        )
        assert cycles == fastsim_cycle


def test_get_simdrive(scenario, fastsim_vehicle, fastsim_cycle):
    if not fastsim_installed:
        pytest.skip("fastsim extra not installed")
    with (
        patch("fastsim.vehicle.Vehicle.from_vehdb", return_value=fastsim_vehicle),
        patch("fastsim.cycle.Cycle.from_file", return_value=fastsim_cycle),
    ):
        run_fastsim = RunFASTSim(veh_no=1, scenario=scenario)
        simdrive = run_fastsim.get_simdrive(cycle=fastsim_cycle)
        assert isinstance(simdrive, fastsim.fastsimrust.RustSimDrive)


def test_get_range(scenario, fastsim_vehicle, fastsim_cycle):
    if not fastsim_installed:
        pytest.skip("fastsim extra not installed")
    with (
        patch("fastsim.vehicle.Vehicle.from_vehdb", return_value=fastsim_vehicle),
        patch("fastsim.cycle.Cycle.from_file", return_value=fastsim_cycle),
    ):
        run_fastsim = RunFASTSim(veh_no=1, scenario=scenario)
        run_fastsim.get_range()
        if run_fastsim.vehicle.veh_pt_type == gl.BEV:
            expected_range = (
                run_fastsim.vehicle.ess_max_kwh
                * (run_fastsim.vehicle.max_soc - run_fastsim.vehicle.min_soc)
                * run_fastsim.mpgge
                / gl.KWH_PER_GGE
            )
        elif run_fastsim.vehicle.veh_pt_type == gl.CONV:
            expected_range = (
                run_fastsim.vehicle.fs_kwh / gl.KWH_PER_GGE
            ) * run_fastsim.mpgge
        elif run_fastsim.vehicle.veh_pt_type == gl.HEV:
            elec_range_mi = (
                run_fastsim.vehicle.ess_max_kwh
                * (run_fastsim.vehicle.max_soc - run_fastsim.vehicle.min_soc)
                * run_fastsim.mpgge
                / gl.KWH_PER_GGE
            )
            conv_range_mi = (
                run_fastsim.vehicle.fs_kwh / gl.KWH_PER_GGE
            ) * run_fastsim.mpgge
            expected_range = elec_range_mi + conv_range_mi

        assert run_fastsim.range_mi == pytest.approx(expected_range, 0.01)


def test_veh_override_kg_sets_simulated_mass(scenario):
    if not fastsim_installed:
        pytest.skip("fastsim extra not installed")
    default_run = RunFASTSim(veh_no=1, scenario=scenario)
    loaded_run = RunFASTSim(veh_no=1, scenario=scenario, veh_override_kg=40000.0)
    assert default_run.vehicle.veh_kg != pytest.approx(40000.0)
    assert loaded_run.vehicle.veh_kg == pytest.approx(40000.0)
