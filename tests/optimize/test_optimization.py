import pytest
from unittest.mock import MagicMock, patch, ANY
import numpy as np
import t3co.constants.Global as gl

pytest.importorskip("pymoo")

try:
    from t3co.optimize.optimization import VehicleDesignOpt, run_optimization
except ImportError as e:
    pytest.skip(f"Skipping optimization tests: {e}", allow_module_level=True)

try:
    import fastsim  # noqa: F401

    fastsim_installed = True
except (ImportError, AttributeError):
    fastsim_installed = False


@pytest.fixture
def mock_vehicle():
    vehicle = MagicMock()
    vehicle.veh_pt_type = gl.BEV
    vehicle.selection = 1
    return vehicle


@pytest.fixture
def mock_scenario():
    scenario = MagicMock()
    scenario.knob_min_ess_kwh = 10
    scenario.knob_max_ess_kwh = 100
    scenario.knob_min_motor_kw = 50
    scenario.knob_max_motor_kw = 200
    scenario.knob_min_fc_kw = 20
    scenario.knob_max_fc_kw = 150
    scenario.knob_min_fs_kwh = 30
    scenario.knob_max_fs_kwh = 300
    scenario.constraint_accel = False
    scenario.constraint_grade = False
    scenario.constraint_range = False
    return scenario


@pytest.fixture
def mock_config():
    config = MagicMock()
    config.pop_size = 25
    config.algorithms = "NSGA2"
    config.x_tol = 0.001
    config.f_tol = 0.001
    config.nth_gen = 1
    config.n_last = 5
    config.n_max_gen = 1000
    return config


class TestVehicleDesignOpt:
    def test_init_bev(self, mock_vehicle, mock_scenario, mock_config):
        mock_vehicle.veh_pt_type = gl.BEV

        problem = VehicleDesignOpt(mock_vehicle, mock_scenario, mock_config)

        assert problem.n_var == 2
        assert np.array_equal(problem.xl, np.array([10, 50]))
        assert np.array_equal(problem.xu, np.array([100, 200]))

    def test_init_conv(self, mock_vehicle, mock_scenario, mock_config):
        mock_vehicle.veh_pt_type = gl.CONV

        problem = VehicleDesignOpt(mock_vehicle, mock_scenario, mock_config)

        assert problem.n_var == 2
        assert np.array_equal(problem.xl, np.array([20, 30]))
        assert np.array_equal(problem.xu, np.array([150, 300]))

    def test_evaluate_bev(self, mock_vehicle, mock_scenario, mock_config):
        mock_vehicle.veh_pt_type = gl.BEV
        problem = VehicleDesignOpt(mock_vehicle, mock_scenario, mock_config)

        x = np.array([50, 100])  # ess_kwh, motor_kw
        out = {}

        with (
            patch("t3co.optimize.optimization.Energy") as MockEnergy,
            patch("t3co.optimize.optimization.Ledger") as MockLedger,
        ):
            mock_energy_instance = MockEnergy.return_value
            mock_ledger_instance = MockLedger.return_value
            mock_ledger_instance.discounted_tco_dol = 50000

            problem._evaluate(x, out)

            assert mock_vehicle.ess_max_kwh == 50
            assert mock_vehicle.mc_max_kw == 100

            mock_energy_instance.run_fastsim_model.assert_called_once()
            MockLedger.assert_called_once()

            assert out["F"] == [50000]

    def test_evaluate_constraints(self, mock_vehicle, mock_scenario, mock_config):
        mock_vehicle.veh_pt_type = gl.BEV
        mock_scenario.constraint_accel = True
        mock_scenario.max_time_0_to_60mph_at_gvwr_s = 10
        mock_scenario.max_time_0_to_30mph_at_gvwr_s = 5

        problem = VehicleDesignOpt(mock_vehicle, mock_scenario, mock_config)

        x = np.array([50, 100])
        out = {}

        with (
            patch("t3co.optimize.optimization.Energy") as MockEnergy,
            patch("t3co.optimize.optimization.Ledger") as MockLedger,
        ):
            mock_energy_instance = MockEnergy.return_value
            mock_energy_instance.zero_to_sixty_loaded = 12  # Violation
            mock_energy_instance.zero_to_thirty_loaded = 4  # Pass

            mock_ledger_instance = MockLedger.return_value
            mock_ledger_instance.discounted_tco_dol = 50000

            problem._evaluate(x, out)

            assert "G" in out
            # G[0] = 12 - 10 = 2 > 0 (violation)
            # G[1] = 4 - 5 = -1 <= 0 (pass)
            assert out["G"][0] == 2
            assert out["G"][1] == -1

    @pytest.mark.parametrize(
        "constraint_range, expected_n_ieq_constr", [(False, 2), (True, 3)]
    )
    def test_declared_constraint_count_matches_evaluate(
        self,
        mock_vehicle,
        mock_scenario,
        mock_config,
        constraint_range,
        expected_n_ieq_constr,
    ):
        """n_ieq_constr must match the G vector _evaluate actually returns.

        pymoo sizes its constraint array from n_ieq_constr, so any mismatch
        makes the whole optimization fail on the first generation.
        """
        mock_vehicle.veh_pt_type = gl.BEV
        mock_scenario.constraint_accel = True
        mock_scenario.max_time_0_to_60mph_at_gvwr_s = 10
        mock_scenario.max_time_0_to_30mph_at_gvwr_s = 5
        mock_scenario.constraint_grade = False
        mock_scenario.constraint_range = constraint_range
        mock_scenario.target_range_mi = 600

        problem = VehicleDesignOpt(mock_vehicle, mock_scenario, mock_config)
        assert problem.n_ieq_constr == expected_n_ieq_constr

        out = {}
        with (
            patch("t3co.optimize.optimization.Energy") as MockEnergy,
            patch("t3co.optimize.optimization.Ledger") as MockLedger,
        ):
            energy = MockEnergy.return_value
            energy.zero_to_sixty_loaded = 9
            energy.zero_to_thirty_loaded = 4
            energy.primary_fuel_range_mi = 700
            MockLedger.return_value.discounted_tco_dol = 50000

            problem._evaluate(np.array([50, 100]), out)

        assert len(out["G"]) == problem.n_ieq_constr


def test_run_optimization():
    with (
        patch("t3co.optimize.optimization.Config") as MockConfig,
        patch("t3co.optimize.optimization.Vehicle") as MockVehicle,
        patch("t3co.optimize.optimization.Scenario") as MockScenario,
        patch("t3co.optimize.optimization.Pool") as MockPool,
        patch("t3co.optimize.optimization.minimize") as mock_minimize,
        patch("t3co.optimize.optimization.VehicleDesignOpt") as MockProblem,
    ):
        mock_config = MockConfig.return_value
        mock_config.skip_all_opt = False
        mock_config.pop_size = 25
        mock_config.algorithms = "NSGA2"
        mock_config.x_tol = 0.001
        mock_config.f_tol = 0.001
        mock_config.nth_gen = 1
        mock_config.n_last = 5
        mock_config.n_max_gen = 100

        mock_res = MagicMock()
        mock_res.X = [10, 20]
        mock_res.F = [1000]
        mock_minimize.return_value = mock_res

        mock_vehicle_instance = MockVehicle.return_value
        mock_vehicle_instance.from_config.return_value = mock_vehicle_instance
        mock_vehicle_instance.veh_pt_type = gl.BEV

        mock_problem_instance = MockProblem.return_value
        mock_ledger = MagicMock()
        mock_ledger.discounted_tco_dol = 50000.0
        mock_problem_instance.evaluate_solution.return_value = (
            mock_vehicle_instance,
            MagicMock(),
            mock_ledger,
        )

        run_optimization(selection=1, parallel=True, n_processes=2)

        MockConfig.assert_called()
        MockVehicle.assert_called()
        MockScenario.assert_called()
        MockPool.assert_called_with(2)
        mock_minimize.assert_called()


@pytest.mark.skipif(
    not fastsim_installed, reason="Requires FASTSim to evaluate real designs"
)
def test_serial_and_parallel_evaluation_agree():
    """The same designs must score the same however the population is evaluated.

    The optimizer shares one Vehicle and one Scenario across every candidate
    design. Serial evaluation reuses those objects directly, while
    StarmapParallelization pickles the problem once per generation and spreads
    the designs over worker chunks. Any state written back to the shared
    objects therefore makes the two paths disagree, and makes parallel runs
    depend on how the chunks happen to fall across workers.

    The repeated design in X is deliberate: it pins down that evaluating one
    point twice yields one answer.
    """
    from multiprocessing import Pool

    from pymoo.core.problem import LoopedElementwiseEvaluation

    try:
        from pymoo.parallelization.starmap import StarmapParallelization
    except ImportError:
        from pymoo.core.problem import StarmapParallelization

    from t3co.input_data.config import Config
    from t3co.input_data.scenario import Scenario
    from t3co.input_data.vehicle import Vehicle

    def build_problem(runner):
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
        config.vehicle_life_yr = scenario.vehicle_life_yr
        return VehicleDesignOpt(vehicle, scenario, config, runner=runner)

    X = np.array([[290.0], [310.0], [330.0], [290.0]])

    serial = build_problem(LoopedElementwiseEvaluation()).evaluate(
        X, return_values_of=["F", "G"]
    )

    pool = Pool(2)
    try:
        parallel = build_problem(StarmapParallelization(pool.starmap)).evaluate(
            X, return_values_of=["F", "G"]
        )
    finally:
        pool.close()
        pool.join()

    np.testing.assert_allclose(serial[0], parallel[0], rtol=0, atol=0)
    np.testing.assert_allclose(serial[1], parallel[1], rtol=0, atol=0)

    # the repeated design scores identically within a single batch
    np.testing.assert_allclose(serial[0][0], serial[0][3], rtol=0, atol=0)
    np.testing.assert_allclose(parallel[0][0], parallel[0][3], rtol=0, atol=0)
