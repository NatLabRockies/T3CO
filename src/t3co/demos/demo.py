# %%
"""
Demo of computing TCO directly with T3CO's classes, without the sweep CLI.

Loads selection 1 from the bundled demo Vehicle and Scenario files and supplies
fixed energy values (4.0 mpgge and a 200-mile range) in place of a FASTSim run.
It prints the ``TCOCalc`` for year index 3 (the fourth year), then builds the
full ``Ledger``, prints it as a flat dictionary, and writes it to
``results/save_dict.json`` and ``results/save_csv.csv`` in the directory that
contains the ``t3co`` package.

The script runs as soon as it is imported, so run it directly::

    python src/t3co/demos/demo.py
"""
import time
from pathlib import Path

from t3co.energy_models import energy
from t3co.input_data import scenario, vehicle
from t3co.tco import ledger
from t3co.tco.tcocalc import TCOCalc

start = time.time()
input_vehicle = vehicle.Vehicle().from_csv(
    selection=1,
    vehicle_db_file=Path(__file__).parents[1]
    / "resources"
    / "inputs"
    / "Demo_FY22_vehicle_model_assumptions.csv",
)
input_vehicle.set_veh_kg()
input_scenario = scenario.Scenario().from_csv(
    selection=1,
    scenario_file=Path(__file__).parents[1]
    / "resources"
    / "inputs"
    / "Demo_FY22_scenario_assumptions.csv",
)

input_energy = energy.Energy(mpgge=4.0, primary_fuel_range_mi=200.0)

tco_3 = TCOCalc(
    year_index=3,
    vehicle=input_vehicle,
    scenario=input_scenario,
    energy=input_energy,
)
print(tco_3)

# %%
output_ledger = ledger.Ledger(
    vehicle=input_vehicle, scenario=input_scenario, energy=input_energy
)
filepath = Path(__file__).parents[2] / "results/save_dict.json"
csv_filepath = Path(__file__).parents[2] / "results/save_csv.csv"
# print(output_ledger)
# print(output_ledger.tco_per_year[2].oper_costs_dol.insurance_cost_dol_per_yr)
print(output_ledger.to_dict(flatten=True))

output_ledger.to_json(filepath, flatten=False)
output_ledger.to_csv(csv_filepath)

# %%
# results_dict = output_ledger.to_dict( flatten=True)
# with open(filepath, 'w') as f:
#     json.dump(handle_nan(results_dict), f)

# %%
print(f"T3CO Run time: {time.time() - start}")

if __name__ == "__main__":
    pass
