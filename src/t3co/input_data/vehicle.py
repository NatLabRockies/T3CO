from dataclasses import dataclass, field
from pathlib import Path
from typing import Union

try:
    from typing import Self  # Python 3.11+
except ImportError:
    from typing_extensions import Self  # Older versions of Python

import pandas as pd

from t3co.input_data.config import Config
from t3co.utils.print_class_objects import handle_nan, remove_df_attrs, get_path_object


@dataclass
class Vehicle:
    selection: Union[int, str] = None
    veh_pt_type: str = ""
    fc_eff_type: str = ""
    fc_max_kw: float = 0.0
    fs_kwh: float = 0.0
    mc_max_kw: float = 0.0
    ess_max_kwh: float = 0.0
    chg_eff: float = 0.0
    glider_kg: float = 0.0
    trans_kg: float = 0.0
    cargo_kg: float = 0.0
    fc_base_kg: float = 0.0
    fs_kwh_per_kg: float = 0.0
    fc_kw_per_kg: float = 0.0
    mc_pe_kg_per_kw: float = 0.0
    mc_pe_base_kg: float = 0.0
    ess_kg_per_kwh: float = 0.0
    ess_base_kg: float = 0.0
    veh_override_kg: float = 0.0
    comp_mass_multiplier: float = 1.0
    max_soc: float = 0.0
    min_soc: float = 0.0

    def __new__(cls, *args, **kwargs):
        """
        Creates a new instance of the OpportunityCosts class.
        """
        instance = super(Vehicle, cls).__new__(cls)
        return instance

    @classmethod
    def from_config(cls, selection: int, config: Config) -> Self:
        """
        Creates a Vehicle instance from the configuration.

        Args:
            selection (int): The selection index.
            config (Config): The configuration instance.

        Returns:
            Self: An instance of the Vehicle class.
        """

        if config.vehicle_df is not None:
            return cls.from_df(selection=selection, vehicle_df=config.vehicle_df)
        else:
            return cls.from_csv(
                selection=selection, vehicle_db_file=config.vehicle_file, config=config
            )

    @classmethod
    def from_df(cls, selection: int, vehicle_df: pd.DataFrame) -> Self:
        """
        Creates a Vehicle instance from the vehicle dataframe.

        Args:
            selection (int): The selection index.
            vehicle_df (pd.DataFrame): The vehicle dataframe

        Returns:
            Self: An instance of the Vehicle class.
        """

        vehicle_dict = vehicle_df.loc[
            vehicle_df["selection"] == selection, list(cls.__annotations__.keys())
        ].to_dict("records")[0]
        return cls(**handle_nan(vehicle_dict))

    @classmethod
    def from_csv(
        cls, selection: int, vehicle_db_file: Union[str, Path], config: Config = None
    ) -> Self:
        """
        Creates a Vehicle instance from the vehicle database csv file.

        Args:
            selection (int): The selection index.
            vehicle_db_file (Union[str, Path]): The vehicle database file path.

        Returns:
            Self: An instance of the Vehicle class.
        """
        if not Path(vehicle_db_file).is_absolute() and config is not None:
            vehicle_db_file = Path(config.config_filename).parent / vehicle_db_file

        vehicle_db_df = pd.read_csv(
            get_path_object(vehicle_db_file),
            usecols=lambda x: x in cls.__annotations__.keys(),
        )

        vehicle_dict = vehicle_db_df.loc[
            vehicle_db_df["selection"] == selection
        ].to_dict("records")[0]
        return cls(**handle_nan(vehicle_dict))

    def set_veh_kg(self) -> None:
        """
        Sets the vehicle weight in kilograms.

        Uses the same formula as FASTSim's ``Vehicle.set_veh_mass``, so that the
        mass T3CO costs is the mass FASTSim simulates. ``comp_mass_multiplier``
        applies to every component except the glider and the cargo.
        """
        if self.veh_override_kg:
            self.veh_kg = self.veh_override_kg
        else:
            fs_kg = self.fs_kwh / self.fs_kwh_per_kg if self.fs_kwh_per_kg != 0 else 0
            fc_kg = (
                self.fc_base_kg + self.fc_max_kw / self.fc_kw_per_kg
                if self.fc_max_kw != 0 and self.fc_kw_per_kg != 0
                else 0
            )
            mc_kg = (
                self.mc_pe_base_kg + self.mc_pe_kg_per_kw * self.mc_max_kw
                if self.mc_max_kw != 0
                else 0
            )
            ess_kg = (
                self.ess_base_kg + self.ess_kg_per_kwh * self.ess_max_kwh
                if self.ess_max_kwh != 0
                else 0
            )
            self.veh_kg = (
                self.glider_kg
                + self.cargo_kg
                + self.comp_mass_multiplier
                * (self.trans_kg + fs_kg + fc_kg + mc_kg + ess_kg)
            )

    def delete_dataframes(self) -> None:
        """
        Deletes DataFrame attributes from the Vehicle instance.
        """
        remove_df_attrs(self)
