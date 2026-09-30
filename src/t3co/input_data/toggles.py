"""Cost-component toggles loaded from ``cost_toggles.json``.

Each toggle switches one cost component, or a model feature such as running
FASTSim or fetching EIA fuel prices, on or off for a run.
"""

import json
from dataclasses import dataclass
from pathlib import Path
from typing import Union

try:
    from typing import Self  # Python 3.11+
except ImportError:
    from typing_extensions import Self  # Older versions of Python

import t3co.constants.Global as gl
from t3co.utils.print_class_objects import to_flat_dict


@dataclass
class Toggles:
    """
    Class object that contains various toggles for TCO calculations.
    """

    msrp: bool = True
    purchase_tax: bool = True
    purchasing_downpayment: bool = True
    mark_up: bool = True
    residual_cost: bool = True
    fuel_cost: bool = True
    eia_fuel_prices: bool = True
    maintenance_oper_cost: bool = True
    insurance_cost: bool = True
    purchasing_cost: bool = True
    fueling_dwell_labor: bool = True
    payload_oppy_cost: bool = True
    fueling_dwell_oppy_cost: bool = True
    mr_downtime_oppy_cost: bool = True
    run_fastsim: bool = True

    @classmethod
    def from_json(
        cls,
        cost_toggles_file: Union[Path, str] = gl.RESOURCES_FOLDERPATH
        / "cost_toggles.json",
    ) -> Self:
        """
        Creates a Toggles instance from a JSON file.

        Args:
            cost_toggles_file (Union[Path, str]): Path to the JSON file containing toggle settings.

        Returns:
            Toggles: An instance of the Toggles class.
        """
        with open(cost_toggles_file, "r") as f:
            toggles_dict = json.load(f)

        toggles_dict = to_flat_dict(toggles_dict, include_prefix=False, delimiter="")
        # print(toggles_dict)
        return cls(**toggles_dict)
