import argparse

import numpy as np
from multiprocessing import Pool
from pymoo.algorithms.moo.nsga2 import NSGA2
from pymoo.algorithms.soo.nonconvex.nelder import NelderMead
from pymoo.algorithms.soo.nonconvex.pattern import PatternSearch
from pymoo.algorithms.soo.nonconvex.pso import PSO
from pymoo.core.problem import ElementwiseProblem, LoopedElementwiseEvaluation
from pymoo.operators.sampling.lhs import LatinHypercubeSampling as LHS

try:
    from pymoo.parallelization.starmap import StarmapParallelization
except ImportError:
    from pymoo.core.problem import StarmapParallelization
from pymoo.optimize import minimize
from pymoo.termination.default import DefaultMultiObjectiveTermination as MODT

from t3co.energy_models.energy import Energy
from t3co.input_data.config import Config
from t3co.input_data.scenario import Scenario
from t3co.input_data.vehicle import Vehicle
import t3co.constants.Global as gl
from t3co.tco.ledger import Ledger

ALGO_NSGA2 = "NSGA2"
ALGO_NelderMead = "NelderMead"
ALGO_PatternSearch = "PatternSearch"
ALGO_PSO = "PSO"

ALGORITHMS = [ALGO_NSGA2, ALGO_NelderMead, ALGO_PatternSearch, ALGO_PSO]


class VehicleDesignOpt(ElementwiseProblem):
    """Single-objective pymoo problem that sizes a powertrain for minimum TCO.

    The decision variables depend on the vehicle's powertrain type, and each
    is bounded by the matching ``knob_min_*``/``knob_max_*`` Scenario inputs:

    - Conventional (``CONV``): ``x[0]`` fuel converter peak power (kW), and
      ``x[1]`` fuel storage energy (kWh equivalent) only when both fuel
      storage knobs are set.
    - Battery electric (``BEV``): ``x[0]`` battery size (kWh), ``x[1]`` motor
      peak power (kW).
    - Hybrid (``HEV``): ``x[0]`` battery size (kWh), ``x[1]`` fuel converter
      peak power (kW), ``x[2]`` fuel storage energy (kWh equivalent), ``x[3]``
      motor peak power (kW).

    The objective is ``Ledger.discounted_tco_dol``. Inequality constraints
    (satisfied when ``<= 0``) are added only when enabled on the Scenario and
    given a positive target: 0-60 and 0-30 mph times at GVWR
    (``constraint_accel``), minimum speeds on 6% and 1.25% grades
    (``constraint_grade``), and primary fuel range (``constraint_range``).

    Args:
        vehicle (Vehicle): Vehicle to size. Its design variables are
            overwritten on every evaluation.
        scenario (Scenario): Scenario supplying knob bounds, constraint
            targets, and cost inputs.
        config (Config): Analysis configuration.
        runner (optional): pymoo elementwise runner, e.g.
            ``StarmapParallelization`` to evaluate a population in a process
            pool. ``None`` evaluates designs serially.
    """

    def __init__(
        self,
        vehicle: Vehicle,
        scenario: Scenario,
        config: Config,
        runner=None,
    ):
        self.vehicle = vehicle
        self.scenario = scenario
        self.config = config

        xl = []
        xu = []
        x = {}
        # Define decision variables based on powertrain type
        if vehicle.veh_pt_type == gl.CONV:
            # x[0]: Fuel converter peak power (kW)
            xl.append(scenario.knob_min_fc_kw)
            xu.append(scenario.knob_max_fc_kw)
            x["knob_min_fc_kw"] = scenario.knob_min_fc_kw
            x["knob_max_fc_kw"] = scenario.knob_max_fc_kw

            # x[1]: Fuel storage energy (kWh equivalent)
            if (
                scenario.knob_min_fs_kwh is not None
                and scenario.knob_max_fs_kwh is not None
            ):
                xl.append(scenario.knob_min_fs_kwh)
                xu.append(scenario.knob_max_fs_kwh)
                x["knob_min_fs_kwh"] = scenario.knob_min_fs_kwh
                x["knob_max_fs_kwh"] = scenario.knob_max_fs_kwh

        elif vehicle.veh_pt_type == gl.BEV:
            # x[0]: Battery size (kWh)
            xl.append(scenario.knob_min_ess_kwh)
            xu.append(scenario.knob_max_ess_kwh)
            x["knob_min_ess_kwh"] = scenario.knob_min_ess_kwh
            x["knob_max_ess_kwh"] = scenario.knob_max_ess_kwh

            # x[1]: Motor peak power (kW)
            xl.append(scenario.knob_min_motor_kw)
            xu.append(scenario.knob_max_motor_kw)
            x["knob_min_motor_kw"] = scenario.knob_min_motor_kw
            x["knob_max_motor_kw"] = scenario.knob_max_motor_kw

        elif vehicle.veh_pt_type == gl.HEV:
            # x[0]: Battery size (kWh)
            xl.append(scenario.knob_min_ess_kwh)
            xu.append(scenario.knob_max_ess_kwh)
            # x[1]: Fuel converter peak power (kW)
            xl.append(scenario.knob_min_fc_kw)
            xu.append(scenario.knob_max_fc_kw)
            # x[2]: Fuel storage energy (kWh equivalent)
            xl.append(scenario.knob_min_fs_kwh)
            xu.append(scenario.knob_max_fs_kwh)
            # x[3]: Motor peak power (kW)
            xl.append(scenario.knob_min_motor_kw)
            xu.append(scenario.knob_max_motor_kw)

            x["knob_min_ess_kwh"] = scenario.knob_min_ess_kwh
            x["knob_max_ess_kwh"] = scenario.knob_max_ess_kwh
            x["knob_min_fc_kw"] = scenario.knob_min_fc_kw
            x["knob_max_fc_kw"] = scenario.knob_max_fc_kw
            x["knob_min_fs_kwh"] = scenario.knob_min_fs_kwh
            x["knob_max_fs_kwh"] = scenario.knob_max_fs_kwh
            x["knob_min_motor_kw"] = scenario.knob_min_motor_kw
            x["knob_max_motor_kw"] = scenario.knob_max_motor_kw
        else:
            raise ValueError(f"Unknown vehicle type: {vehicle.veh_pt_type}")

        xl = np.array(xl)
        xu = np.array(xu)
        n_var = len(xl)
        print("Knobs:")
        for key, value in x.items():
            print(f" {key}: {value}")

        # Determine number of inequality constraints
        n_ieq_constr = 0
        if scenario.constraint_accel:
            # 0-60 mph and 0-30 mph
            if scenario.max_time_0_to_60mph_at_gvwr_s > 0:
                n_ieq_constr += 1
            if scenario.max_time_0_to_30mph_at_gvwr_s > 0:
                n_ieq_constr += 1

        if scenario.constraint_grade:
            # 6% and 1.25% grade
            if scenario.min_speed_at_6pct_grade_in_5min_mph > 0:
                n_ieq_constr += 1
            if scenario.min_speed_at_1p25pct_grade_in_5min_mph > 0:
                n_ieq_constr += 1

        if scenario.constraint_range:
            # Must mirror the range constraint appended in _evaluate.
            if scenario.target_range_mi > 0:
                n_ieq_constr += 1

        super().__init__(
            n_var=n_var,
            n_obj=1,
            n_ieq_constr=n_ieq_constr,
            xl=xl,
            xu=xu,
            # pymoo's own default is LoopedElementwiseEvaluation(); passing
            # runner through when it is None would replace that default with
            # None and make every evaluation raise TypeError.
            elementwise_runner=(
                runner if runner is not None else LoopedElementwiseEvaluation()
            ),
        )

    def apply_design_variables(self, x, vehicle=None) -> Vehicle:
        """Write the design variables in ``x`` onto a vehicle.

        Args:
            x (array-like): Design variables, laid out as described on the class.
            vehicle (Vehicle, optional): Vehicle to modify. Defaults to the
                problem's own vehicle.

        Returns:
            Vehicle: The modified vehicle; it is changed in place.
        """
        target_vehicle = self.vehicle if vehicle is None else vehicle

        if target_vehicle.veh_pt_type == gl.CONV:
            target_vehicle.fc_max_kw = x[0]
            if len(x) > 1:
                target_vehicle.fs_kwh = x[1]
        elif target_vehicle.veh_pt_type == gl.BEV:
            target_vehicle.ess_max_kwh = x[0]
            target_vehicle.mc_max_kw = x[1]
        elif target_vehicle.veh_pt_type == gl.HEV:
            target_vehicle.ess_max_kwh = x[0]
            target_vehicle.fc_max_kw = x[1]
            target_vehicle.fs_kwh = x[2]
            target_vehicle.mc_max_kw = x[3]
        else:
            raise ValueError(f"Unknown vehicle type: {target_vehicle.veh_pt_type}")

        return target_vehicle

    def evaluate_solution(self, x) -> tuple:
        """Simulate and cost one design.

        Applies ``x`` to the vehicle, runs FASTSim over the Scenario's design
        cycle and any enabled performance tests, and builds the Ledger.

        Args:
            x (array-like): Design variables, laid out as described on the class.

        Returns:
            tuple: ``(vehicle, energy, ledger)`` for the evaluated design.
        """
        vehicle = self.apply_design_variables(x)

        energy = Energy()
        energy.run_fastsim_model(
            veh_no=vehicle.selection,
            scenario=self.scenario,
            vehicle_df=self.config.vehicle_df,
            t3co_vehicle=vehicle,
        )

        if self.scenario.constraint_accel:
            energy.run_acceleration_test(vehicle, self.scenario)
        if self.scenario.constraint_grade:
            energy.run_gradeability_test(vehicle, self.scenario)
        if self.scenario.constraint_range:
            energy.run_range_test(vehicle, self.scenario)

        ledger = Ledger(vehicle, self.scenario, energy, self.config)
        return vehicle, energy, ledger

    def _evaluate(self, x, out, *args, **kwargs):
        vehicle, energy, ledger = self.evaluate_solution(x)

        # Objective: minimize the discounted total cost of ownership
        out["F"] = [ledger.discounted_tco_dol]

        # Constraints
        # G <= 0
        g = []

        if self.scenario.constraint_accel:
            # 0-60 mph time constraint
            if self.scenario.max_time_0_to_60mph_at_gvwr_s > 0:
                g.append(
                    energy.zero_to_sixty_loaded
                    - self.scenario.max_time_0_to_60mph_at_gvwr_s
                )

            # 0-30 mph time constraint
            if self.scenario.max_time_0_to_30mph_at_gvwr_s > 0:
                g.append(
                    energy.zero_to_thirty_loaded
                    - self.scenario.max_time_0_to_30mph_at_gvwr_s
                )

        if self.scenario.constraint_grade:
            # Gradeability 6% constraint (min speed)
            if self.scenario.min_speed_at_6pct_grade_in_5min_mph > 0:
                # We want achieved speed >= target speed => target - achieved <= 0
                g.append(
                    self.scenario.min_speed_at_6pct_grade_in_5min_mph
                    - energy.grade_6_mph_ach
                )

            # Gradeability 1.25% constraint (min speed)
            if self.scenario.min_speed_at_1p25pct_grade_in_5min_mph > 0:
                g.append(
                    self.scenario.min_speed_at_1p25pct_grade_in_5min_mph
                    - energy.grade_1_25_mph_ach
                )

        if self.scenario.constraint_range:
            if self.scenario.target_range_mi > 0:
                g.append(self.scenario.target_range_mi - energy.primary_fuel_range_mi)

        if g:
            out["G"] = g


def build_algorithm(algo: str, pop_size: int = 25, sampling=None):
    """Build a pymoo algorithm by name.

    Supported algorithms mirror T3CO 1.x: NSGA2, PatternSearch,
    NelderMead, and PSO.

    NSGA2 is seeded with Latin Hypercube sampling to match T3CO v1.0.11
    (``t3co/moopack/moo.py``); pymoo's own default is uniform random
    sampling, which spreads the initial population less evenly.
    """
    name = algo.upper() if algo else "NSGA2"
    if name == "NSGA2":
        return NSGA2(
            pop_size=pop_size,
            eliminate_duplicates=True,
            sampling=sampling if sampling is not None else LHS(),
        )
    if name == "PATTERNSEARCH":
        return PatternSearch()
    if name == "NELDERMEAD":
        return NelderMead()
    if name == "PSO":
        return PSO()
    raise ValueError(
        f"Unsupported optimization algorithm '{algo}'. "
        f"Choose from: {ALGORITHMS}"
    )


def build_termination(
    x_tol: float = 0.001,
    f_tol: float = 0.001,
    n_max_gen: int = 1000,
    n_max_evals: int = None,
    n_last: int = 5,
    nth_gen: int = 1,
):
    """Build termination using ``MODT`` (pymoo multi-objective default
    termination), matching the T3CO 1.x approach.

    ``n_last`` and ``nth_gen`` are T3CO's names for pymoo's ``period`` and
    ``n_skip``: ``period`` is how many recent generations must all look
    converged before the run stops, and ``n_skip`` is how many generations are
    skipped between convergence checks. pymoo defaults them to 50 and 5, and
    ``RobustTermination`` seeds its sliding window with zeros, so leaving them
    unset imposes a hard floor of 50 generations no matter how quickly the
    search settles.
    """
    return MODT(
        xtol=x_tol,
        ftol=f_tol,
        n_max_gen=n_max_gen,
        n_max_evals=n_max_evals,
        period=n_last,
        n_skip=max(nth_gen - 1, 0),
    )


def run_optimization(
    selection,
    parallel=True,
    n_processes=4,
    config_file=None,
    analysis_id=1,
):
    """Optimize one Vehicle-Scenario pair and report the cheapest design.

    The analysis is loaded from a Config CSV rather than from ``Config()``
    defaults. Several of those defaults are placeholders that only
    ``from_csv`` fills in — ``fuel_prices_file`` is the empty string, for
    instance — and ``Config.__setstate__`` re-reads the auxiliary files on
    every unpickle. A Config built from the defaults therefore raises inside
    each pool worker as it is unpickled; ``Pool`` silently replaces the dead
    worker, the replacement dies the same way, and the run hangs forever
    instead of reporting the error.
    """
    config = Config()
    config.from_csv(
        filename=str(config_file or config.config_filename),
        analysis_id=analysis_id,
    )
    config.skip_all_opt = False
    config.selections = [selection]
    config.check_drivecycles_and_create_selections()
    config.read_auxiliary_files()
    vehicle = Vehicle().from_config(selection=selection, config=config)
    vehicle.set_veh_kg()
    scenario = Scenario().from_csv(
        selection=selection, scenario_file=config.scenario_file
    )
    scenario.override_from_config(config=config)
    config.vehicle_life_yr = scenario.vehicle_life_yr

    pool = None
    runner = None
    if parallel:
        pool = Pool(n_processes)
        runner = StarmapParallelization(pool.starmap)

    try:
        problem = VehicleDesignOpt(vehicle, scenario, config, runner=runner)
        algorithm = build_algorithm(
            config.algorithms, pop_size=int(config.pop_size)
        )
        termination = build_termination(
            x_tol=float(config.x_tol),
            f_tol=float(config.f_tol),
            n_max_gen=int(config.n_max_gen),
            n_last=int(config.n_last),
            nth_gen=int(config.nth_gen),
        )

        res = minimize(
            problem,
            algorithm,
            termination=termination,
            seed=1,
            verbose=True,
        )
    finally:
        if pool:
            pool.close()
            pool.join()

    vehicle, energy, ledger = problem.evaluate_solution(res.X)

    print("Best solution:")
    if vehicle.veh_pt_type == gl.CONV:
        print("  Fuel Converter Peak Power (kW): {:.2f}".format(res.X[0]))
        if len(res.X) > 1:
            print("  Fuel Storage Energy (kWh eq.):  {:.2f}".format(res.X[1]))
    elif vehicle.veh_pt_type == gl.BEV:
        print("  Battery Size (kWh):             {:.2f}".format(res.X[0]))
        print("  Motor Peak Power (kW):          {:.2f}".format(res.X[1]))
    elif vehicle.veh_pt_type == gl.HEV:
        print("  Battery Size (kWh):             {:.2f}".format(res.X[0]))
        print("  Fuel Converter Peak Power (kW): {:.2f}".format(res.X[1]))
        print("  Fuel Storage Energy (kWh eq.):  {:.2f}".format(res.X[2]))
        print("  Motor Peak Power (kW):          {:.2f}".format(res.X[3]))
    print("Minimum Discounted TCO:           ${:.2f}".format(ledger.discounted_tco_dol))


if __name__ == "__main__":
    parser = argparse.ArgumentParser(
        description="Optimize vehicle design parameters for minimum discounted TCO using Ledger and fastsim."
    )
    parser.add_argument(
        "--selection", type=int, default=1, help="Vehicle and Scenario selection number"
    )
    parser.add_argument(
        "--no-parallel", action="store_true", help="Disable parallel evaluation."
    )
    parser.add_argument(
        "--n-processes", type=int, default=9, help="Number of processes."
    )
    parser.add_argument(
        "--config", default=None, help="Input Config file"
    )
    parser.add_argument(
        "--analysis-id",
        type=int,
        default=1,
        help="Analysis key from input Config file - 'config.analysis_id'",
    )
    args = parser.parse_args()

    run_optimization(
        selection=args.selection,
        parallel=not args.no_parallel,
        n_processes=args.n_processes,
        config_file=args.config,
        analysis_id=args.analysis_id,
    )
