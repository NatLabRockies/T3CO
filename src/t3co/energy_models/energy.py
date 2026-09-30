from dataclasses import dataclass
from pathlib import Path
from typing import Union

import pandas as pd
import numpy as np

from t3co.input_data.vehicle import Vehicle

try:
    from t3co.energy_models.fastsim_model.fastsim_wrapper import RunFASTSim

    fastsim_installed = True
except ImportError:
    RunFASTSim = None
    fastsim_installed = False
except AttributeError:
    RunFASTSim = None
    fastsim_installed = False

from t3co.constants import Global as gl
from t3co.input_data.scenario import Scenario


@dataclass
class Energy:
    mpgge: float = None
    primary_fuel_range_mi: float = None
    zero_to_sixty_loaded: float = None
    zero_to_thirty_loaded: float = None
    grade_6_mph_ach: float = None
    grade_1_25_mph_ach: float = None

    def __new__(cls, *args, **kwargs):
        """
        Creates a new instance of the Energy class.
        """
        instance = super(Energy, cls).__new__(cls)
        return instance

    def __init__(self, mpgge: float = None, primary_fuel_range_mi: float = None):
        """
        Initializes the Energy instance.

        Args:
            mpgge (float, optional): Miles per gallon gasoline equivalent. Defaults to None.
            primary_fuel_range_mi (float, optional): Primary fuel range in miles. Defaults to None.
        """
        if mpgge is not None and primary_fuel_range_mi is not None:
            self.mpgge = mpgge
            self.primary_fuel_range_mi = primary_fuel_range_mi

    def run_fastsim_model(
        self,
        veh_no: int,
        scenario: Scenario,
        t3co_vehicle: Vehicle = None,
        vehicle_df: pd.DataFrame = None,
        vehicle_file: Union[str, Path] = gl.RESOURCES_FOLDERPATH
        / "inputs"
        / "Demo_FY22_vehicle_model_assumptions.csv",
    ) -> None:
        """
        Runs the FASTSim model to calculate mpgge and primary fuel range.

        Args:
            veh_no (int): Vehicle selection number.
            scenario (Scenario): Scenario instance containing configuration data.
            vehicle_file (Union[str, Path], optional): Vehicle model assumptions input CSV file path. Defaults to gl.RESOURCES_FOLDERPATH / "inputs" / "Demo_FY22_vehicle_model_assumptions.csv".
        """
        if RunFASTSim is None:
            raise ImportError(
                "FASTSim is not installed or could not be imported. Cannot run FASTSim model."
            )

        fastsim_run = RunFASTSim(
            veh_no=veh_no,
            scenario=scenario,
            t3co_vehicle=t3co_vehicle,
            vehicle_df=vehicle_df,
            veh_input_path=vehicle_file,
        )
        self.mpgge = fastsim_run.mpgge
        self.primary_fuel_range_mi = fastsim_run.range_mi

    def run_range_test(self, vehicle: Vehicle, scenario: Scenario) -> None:
        """
        Runs the range test and updates the energy object with results.
        """
        if self.primary_fuel_range_mi is None:
            self.run_fastsim_model(
                veh_no=vehicle.selection,
                scenario=scenario,
                t3co_vehicle=vehicle,
            )

    def run_acceleration_test(
        self,
        vehicle: Vehicle,
        scenario: Scenario,
        set_weight_to_max_kg: bool = True,
        verbose: bool = False,
    ) -> None:
        """
        Runs the acceleration test and updates the energy object with results.
        """
        if RunFASTSim is None:
            raise ImportError(
                "FASTSim is not installed or could not be imported. Cannot run acceleration test."
            )

        original_veh_kg = vehicle.veh_kg
        if set_weight_to_max_kg:
            vehicle.veh_kg = scenario.gvwr_kg + scenario.gvwr_credit_kg

        accel_cycle = RunFASTSim.get_accel_cycle()

        try:
            fastsim_run = RunFASTSim(
                scenario=scenario,
                t3co_vehicle=vehicle,
                veh_no=vehicle.selection,
                cycle=accel_cycle,
            )
        finally:
            # The test is run at GVWR, but the caller's vehicle must keep its
            # own mass: the optimizer reuses one Vehicle across evaluations.
            vehicle.veh_kg = original_veh_kg

        simdrive = fastsim_run.simdrives

        # Calculate 0-60 and 0-30
        # Logic from accel.py
        def get_time_to_speed(target_mph):
            if (np.array(simdrive.mph_ach) >= target_mph).any():
                return np.interp(
                    x=target_mph,
                    xp=np.array(simdrive.mph_ach),
                    fp=accel_cycle.time_s,
                )
            else:
                return -simdrive.mph_ach[-1]

        self.zero_to_sixty_loaded = get_time_to_speed(60)
        self.zero_to_thirty_loaded = get_time_to_speed(30)

    def run_gradeability_test(
        self,
        vehicle: Vehicle,
        scenario: Scenario,
        set_weight_to_max_kg: bool = True,
        verbose: bool = False,
    ) -> None:
        """
        Runs the gradeability test and updates the energy object with results.
        """
        if RunFASTSim is None:
            raise ImportError(
                "FASTSim is not installed or could not be imported. Cannot run gradeability test."
            )

        original_veh_kg = vehicle.veh_kg
        if set_weight_to_max_kg:
            vehicle.veh_kg = scenario.gvwr_kg + scenario.gvwr_credit_kg

        try:
            # 6% Grade
            grade_6_cycle = RunFASTSim.get_grade_cycle(0.06, scenario)
            fastsim_run_6 = RunFASTSim(
                scenario=scenario,
                t3co_vehicle=vehicle,
                veh_no=vehicle.selection,
                cycle=grade_6_cycle,
            )
            self.grade_6_mph_ach = fastsim_run_6.simdrives.mph_ach[-1]

            # 1.25% Grade
            grade_125_cycle = RunFASTSim.get_grade_cycle(0.0125, scenario)
            fastsim_run_125 = RunFASTSim(
                scenario=scenario,
                t3co_vehicle=vehicle,
                veh_no=vehicle.selection,
                cycle=grade_125_cycle,
            )
            self.grade_1_25_mph_ach = fastsim_run_125.simdrives.mph_ach[-1]
        finally:
            # The tests are run at GVWR, but the caller's vehicle must keep its
            # own mass: the optimizer reuses one Vehicle across evaluations.
            vehicle.veh_kg = original_veh_kg
