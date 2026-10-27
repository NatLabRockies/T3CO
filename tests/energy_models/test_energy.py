import pytest

from t3co.energy_models.energy import Energy


def test_energy_initialization():
    energy = Energy(mpgge=3.0, primary_fuel_range_mi=300.0)
    assert energy.mpgge == pytest.approx(3.0, 0.01)
    assert energy.primary_fuel_range_mi == pytest.approx(300.0, 0.01)


def test_energy_initialization_default():
    energy = Energy()
    assert energy.mpgge is None
    assert energy.primary_fuel_range_mi is None


def test_energy_initialization_partial():
    energy = Energy(mpgge=3.0)
    assert energy.mpgge is None
    assert energy.primary_fuel_range_mi is None

    energy = Energy(primary_fuel_range_mi=300.0)
    assert energy.mpgge is None
    assert energy.primary_fuel_range_mi is None

from unittest.mock import patch

def test_run_fastsim_model_missing_dependency():
    energy = Energy()
    scenario = "dummy_scenario"
    
    with patch("t3co.energy_models.energy.RunFASTSim", None):
        with pytest.raises(ImportError, match="FASTSim is not installed"):
            energy.run_fastsim_model(veh_no=1, scenario=scenario)


@pytest.mark.parametrize(
    "test_name", ["run_acceleration_test", "run_gradeability_test"]
)
def test_performance_tests_run_at_gvwr(test_name):
    """Performance tests hand FASTSim the GVWR and leave the vehicle alone.

    The optimizer reuses one Vehicle across every design evaluation, so a
    mass left at GVWR would silently inflate the next evaluation's energy use.
    """
    from types import SimpleNamespace
    from unittest.mock import patch

    vehicle = SimpleNamespace(veh_kg=30210.58, selection=1)
    scenario = SimpleNamespace(gvwr_kg=36287.43, gvwr_credit_kg=0.0)
    original_kg = vehicle.veh_kg
    seen_kg = []

    class FakeRun:
        def __init__(self, **kwargs):
            seen_kg.append(kwargs.get("veh_override_kg"))
            self.simdrives = SimpleNamespace(mph_ach=[0.0, 30.0, 65.0])

        @staticmethod
        def get_accel_cycle():
            return SimpleNamespace(time_s=[0.0, 1.0, 2.0])

        @staticmethod
        def get_grade_cycle(target_grade, scenario=None):
            return SimpleNamespace(time_s=[0.0, 1.0, 2.0])

    energy = Energy()
    with patch("t3co.energy_models.energy.RunFASTSim", FakeRun):
        getattr(energy, test_name)(vehicle, scenario)

    # FASTSim was asked to simulate at GVWR ...
    assert seen_kg and all(
        kg == pytest.approx(scenario.gvwr_kg + scenario.gvwr_credit_kg)
        for kg in seen_kg
    )
    # ... and the caller's vehicle came back unchanged
    assert vehicle.veh_kg == pytest.approx(original_kg)


def test_acceleration_test_is_slower_at_gvwr():
    """The loaded acceleration test must actually simulate the heavier vehicle."""
    pytest.importorskip("fastsim")
    from t3co.input_data.config import Config
    from t3co.input_data.scenario import Scenario
    from t3co.input_data.vehicle import Vehicle

    config = Config()
    config.from_csv(filename=str(Config().config_filename), analysis_id=1)
    config.check_drivecycles_and_create_selections()
    config.read_auxiliary_files()
    selection = config.selections[0]
    vehicle = Vehicle().from_config(selection=selection, config=config)
    vehicle.set_veh_kg()
    scenario = Scenario().from_csv(
        selection=selection, scenario_file=config.scenario_file
    )
    scenario.override_from_config(config=config)
    assert scenario.gvwr_kg + scenario.gvwr_credit_kg > vehicle.veh_kg

    loaded, unloaded = Energy(), Energy()
    loaded.run_acceleration_test(vehicle, scenario, set_weight_to_max_kg=True)
    unloaded.run_acceleration_test(vehicle, scenario, set_weight_to_max_kg=False)

    assert loaded.zero_to_sixty_loaded > unloaded.zero_to_sixty_loaded
