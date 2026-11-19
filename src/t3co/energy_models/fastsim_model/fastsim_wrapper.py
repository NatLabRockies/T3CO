import ast
from pathlib import Path
from typing import List, Union

import fastsim
from fastsim import parameters as params
import numpy as np
import pandas as pd

from t3co.constants import Global as gl
from t3co.input_data.scenario import Scenario
from t3co.input_data.vehicle import Vehicle


class RunFASTSim:
    vehicle: fastsim.vehicle.Vehicle = None
    cycles: Union[fastsim.cycle.Cycle, List[fastsim.simdrive.SimDrive]] = None
    simdrives: Union[fastsim.simdrive.SimDrive, List[fastsim.simdrive.SimDrive]] = None
    mpgge: float = None
    range_mi: float = None

    def __new__(cls, *args, **kwargs):
        """
        Creates a new instance of the RunFASTSim class.
        """
        instance = super(RunFASTSim, cls).__new__(cls)
        return instance

    def __init__(
        self,
        scenario: Scenario,
        t3co_vehicle: Vehicle = None,
        veh_no: int = None,
        vehicle_df: pd.DataFrame = None,
        veh_input_path: Union[str, Path] = gl.RESOURCES_FOLDERPATH
        / "inputs"
        / "Demo_FY22_vehicle_model_assumptions.csv",
        use_rust: bool = True,
        cycle: fastsim.cycle.Cycle = None,
        veh_override_kg: float = None,
    ) -> None:
        self.load_vehicle(
            t3co_vehicle=t3co_vehicle,
            veh_no=veh_no,
            veh_input_path=veh_input_path,
            vehicle_df=vehicle_df,
            use_rust=use_rust,
            veh_override_kg=veh_override_kg,
        )

        if cycle:
            self.cycles = cycle
            if use_rust:
                self.cycles = self.cycles.to_rust()
        else:
            self.cycles = self.load_design_cycle_from_scenario(
                scenario=scenario, return_rustcycle=use_rust
            )

        if isinstance(self.cycles, list):
            self.simdrives, mpgges_list, weights = [], [], []
            scenario.constant_trip_distance_mi = 0
            for i in range(len(self.cycles)):
                scenario.constant_trip_distance_mi += (
                    sum(
                        self.cycles[i][0].mph
                        * np.diff(np.array(self.cycles[i][0].time_s), append=0)
                    )
                    * self.cycles[i][1]
                    / 3600
                )
                self.simdrives.append(self.get_simdrive(cycle=self.cycles[i][0]))
                mpgges_list.append(self.simdrives[i].mpgge)
                weights.append(self.cycles[i][1])

            mpgges_list = np.array(mpgges_list)
            weights = np.array(weights)
            self.mpgge = np.divide(
                sum(weights),
                np.sum(
                    np.divide(
                        weights,
                        mpgges_list,
                        out=np.zeros_like(mpgges_list),
                        where=mpgges_list != 0,
                        casting="unsafe",
                    )
                ),
            )
        else:
            scenario.constant_trip_distance_mi = (
                sum(self.cycles.mph * np.diff(np.array(self.cycles.time_s), append=0))
                / 3600
            )
            self.simdrives = self.get_simdrive(cycle=self.cycles)
            self.mpgge = self.simdrives.mpgge

        self.get_range()

    def load_vehicle(
        self,
        t3co_vehicle: Vehicle = None,
        veh_no: int = None,
        veh_input_path: Union[str, Path] = None,
        vehicle_df: pd.DataFrame = None,
        use_rust: bool = True,
        veh_override_kg: float = None,
    ) -> fastsim.vehicle.Vehicle:
        """
        Loads vehicle object from vehicle number and input CSV filepath.

        Args:
            veh_no (int): Vehicle selection number.
            veh_input_path (Union[str, Path]): Vehicle model assumptions input CSV file path.
            veh_override_kg (float, optional): Mass to simulate instead of the
                component mass sum, e.g. GVWR for the performance tests.

        Returns:
            fastsim.vehicle.Vehicle: FASTSim vehicle object.
        """
        scenario_sel = int(float(str(veh_no).split("_")[0]))
        if vehicle_df is not None and not vehicle_df.empty:
            self.vehicle = fastsim.vehicle.Vehicle.from_df(
                vehdf=vehicle_df,
                vnum=scenario_sel,
                veh_file=veh_input_path,
                to_rust=use_rust,
            )

        elif veh_no and veh_input_path:
            self.vehicle = fastsim.vehicle.Vehicle.from_vehdb(
                scenario_sel, veh_input_path, to_rust=use_rust
            )

        if t3co_vehicle:
            self.vehicle.ess_max_kwh = t3co_vehicle.ess_max_kwh
            self.vehicle.fc_max_kw = t3co_vehicle.fc_max_kw
            self.vehicle.fs_kwh = t3co_vehicle.fs_kwh
            self.vehicle.mc_max_kw = t3co_vehicle.mc_max_kw

        if veh_override_kg:
            self.vehicle.veh_override_kg = veh_override_kg

        self.vehicle.set_derived()
        self.vehicle.set_veh_mass()

    def load_design_cycle_from_scenario(
        self,
        scenario: Scenario,
        cyc_file_path: Union[str, Path] = gl.CYCLES_FOLDER,
        return_rustcycle: bool = True,
    ) -> Union[fastsim.cycle.Cycle, List[fastsim.cycle.Cycle]]:
        """
        Loads the design cycle used for mpgge and range determination.

        Args:
            scenario (Scenario): Scenario object for current selection.
            cyc_file_path (Union[str, Path], optional): Drive cycle input file path. Defaults to gl.CYCLES_FOLDER.

        Returns:
            Union[fastsim.cycle.Cycle, List[fastsim.cycle.Cycle]]: FASTSim cycle object for current Scenario object.
        """
        # print(
        #     f"scenario.drive_cycle : {scenario.drive_cycle} {type(scenario.drive_cycle)}"
        # )
        if isinstance(scenario.drive_cycle, Path):
            drive_cycle = str(scenario.drive_cycle)
        elif (
            isinstance(scenario.drive_cycle, str)
            and not Path(scenario.drive_cycle).exists()
        ):
            try:
                drive_cycle = ast.literal_eval(scenario.drive_cycle)
            except (ValueError, SyntaxError):
                drive_cycle = scenario.drive_cycle
        else:
            drive_cycle = scenario.drive_cycle

        if isinstance(drive_cycle, list):
            design_cycles = []
            weights = []
            for dc_weight in drive_cycle:
                if isinstance(dc_weight, tuple):
                    cycle_file_name, weight = dc_weight
                    cyc = self.load_design_cycle_from_path(
                        cyc_file_path=Path(cyc_file_path) / cycle_file_name,
                        return_rustcycle=return_rustcycle,
                    )
                    cyc.name = cycle_file_name
                weights.append(weight)
                design_cycles.append((cyc, weight))
            if sum(weights) != 1:
                print(
                    f"Sum of weights for composite cycles (sum = {sum(weights)}) is not 1."
                )
                raise ValueError

            return design_cycles
        else:
            cycle_file_name = Path(scenario.drive_cycle).name
            design_cycles = self.load_design_cycle_from_path(
                cyc_file_path=scenario.drive_cycle, return_rustcycle=return_rustcycle
            )
            design_cycles.name = cycle_file_name
            return design_cycles

    def load_design_cycle_from_path(
        self, cyc_file_path: Union[str, Path], return_rustcycle: bool = True
    ) -> Union[fastsim.cycle.RustCycle, fastsim.cycle.Cycle]:
        """
        Loads the Cycle object from the drive cycle filepath.

        Args:
            cyc_file_path (Union[str, Path]): Drive cycle input file path.

        Returns:
            fastsim.cycle.Cycle: FASTSim cycle object for current Scenario object.
        """
        if not Path(cyc_file_path).exists():
            print(
                f"Drive cycle not found in {cyc_file_path}, trying {gl.CYCLES_FOLDER}"
            )

            finalized_path = Path(gl.CYCLES_FOLDER) / Path(cyc_file_path).name

        else:
            finalized_path = cyc_file_path
        cyc = fastsim.cycle.Cycle.from_file(finalized_path)
        if return_rustcycle:
            return cyc.to_rust()
        else:
            return cyc

    def get_simdrive(
        self, cycle: fastsim.cycle.Cycle
    ) -> fastsim.fastsimrust.RustSimDrive:
        """
        Creates a SimDrive object for the given cycle and vehicle.

        Args:
            cycle (fastsim.cycle.Cycle): The drive cycle.

        Returns:
            fastsim.fastsimrust.RustSimDrive: The RustSimDrive object.
        """
        simdrive = fastsim.simdrive.SimDrive(cycle, self.vehicle)
        simdrive = simdrive.to_rust()

        sim_params = simdrive.sim_params
        sim_params.reset_orphaned()
        sim_params.missed_trace_correction = False
        sim_params.trace_miss_speed_mps_tol = np.inf
        sim_params.energy_audit_error_tol = np.inf
        sim_params.trace_miss_dist_tol = np.inf
        simdrive.sim_params = sim_params

        props = simdrive.props
        props.reset_orphaned()
        props.kwh_per_gge = gl.KWH_PER_GGE
        simdrive.props = props
        simdrive.sim_drive(init_soc=self.vehicle.max_soc)
        return simdrive

    def get_range(self) -> None:
        """
        Calculates the range of the vehicle based on its type and energy storage.
        """
        if self.vehicle.veh_pt_type == gl.BEV:
            self.range_mi = (
                self.vehicle.ess_max_kwh
                * (self.vehicle.max_soc - self.vehicle.min_soc)
                * self.mpgge
                / gl.KWH_PER_GGE
            )

        elif self.vehicle.veh_pt_type == gl.CONV:
            self.range_mi = (self.vehicle.fs_kwh / gl.KWH_PER_GGE) * self.mpgge

        elif self.vehicle.veh_pt_type == gl.HEV:
            elec_range_mi = (
                self.vehicle.ess_max_kwh
                * (self.vehicle.max_soc - self.vehicle.min_soc)
                * self.mpgge
                / gl.KWH_PER_GGE
            )
            conv_range_mi = (self.vehicle.fs_kwh / gl.KWH_PER_GGE) * self.mpgge
            self.range_mi = elec_range_mi + conv_range_mi

    @staticmethod
    def get_accel_cycle() -> fastsim.cycle.Cycle:
        """
        Creates the acceleration test cycle.
        """
        accel_cyc_secs = np.arange(500)
        cyc_dict = {
            "cycSecs": accel_cyc_secs,
            "cycMps": np.append([0], np.ones(len(accel_cyc_secs) - 1) * 44.7),
            "cycGrade": np.zeros(len(accel_cyc_secs)),
        }
        return fastsim.cycle.Cycle.from_dict(cyc_dict)

    @staticmethod
    def get_grade_cycle(
        target_grade: float, scenario: Scenario = None
    ) -> fastsim.cycle.Cycle:
        """
        Creates the gradeability test cycle.
        """
        CYC_SECONDS = 100
        CYC_MPH = 90
        SIX_GRADE = 0.06
        ONE_POINT_TWENTY_FIVE_GRADE = 0.0125

        first_time_step_mph = 0
        if scenario is not None:
            if target_grade == SIX_GRADE:
                first_time_step_mph = scenario.min_speed_at_6pct_grade_in_5min_mph
            if target_grade == ONE_POINT_TWENTY_FIVE_GRADE:
                first_time_step_mph = scenario.min_speed_at_1p25pct_grade_in_5min_mph

        target_grade_cyc_secs = np.arange(CYC_SECONDS)
        cyc_dict = {
            "cycSecs": target_grade_cyc_secs,
            "cycMps": np.append(
                [first_time_step_mph], np.ones(CYC_SECONDS - 1) * CYC_MPH
            )
            / params.MPH_PER_MPS,
            "cycGrade": np.ones(CYC_SECONDS) * target_grade,
        }
        return fastsim.cycle.Cycle.from_dict(cyc_dict)
