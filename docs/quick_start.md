# Quick Start Guide to T3CO

A total-cost analysis is only as good as its inputs. Generating T3CO results requires equal parts of investment in inputs gathering as it is in running the tool. To make things easier, we provide 500+ demo scenarios for the user to choose from to run T3CO.

## Inputs

T3CO contains three main input files and several auxiliary files that are referenced in the main files for different purposes.

### Vehicle, Scenario, and Config

The main input files are the [***Vehicle***](./pages/vehicle_inputs_descriptions.md), [***Scenario***](./pages/scenario_inputs_descriptions.md), and [***Config***](./pages/config_inputs_descriptions.md). T3CO provides users with demo input files to get started. One or more *Vehicle-Scenario* pair selections are necessary to run T3CO:

- ***Vehicle*** contains sets of FASTSim vehicle input parameters that define the powertrain and vehicle dynamics of the selected *Vehicle-Scenario* pair. Each entry in the ***Vehicle*** file is called a "Vehicle Model" and is referenced using `vehicle.selection` as a key. [[Demo Vehicles](https://github.com/NatLabRockies/T3CO/blob/main/src/t3co/resources/inputs/Demo_FY22_vehicle_model_assumptions.csv)]
- ***Scenario*** contains cost, infrastructure, and optimization related input parameters that define a certain scenario. Each entry in the Scenario file is called a "Scenario Model" and is referenced using `scenario.selection` as a key. [[Demo Scenarios](https://github.com/NatLabRockies/T3CO/blob/main/src/t3co/resources/inputs/Demo_FY22_scenario_assumptions.csv)]
- ***Config*** contains easy ways to manage T3CO model settings and to save the inputs needed to run a set of selections of *Vehicle-Scenario* pairs. It also contains paths to various input files and some Scenario parameter overrides to be used globally on all selections. Users can also specify a path to the output directory in which T3CO results need to be saved. Each entry in the ***Config*** file refers to an "Analysis" and is accessed using `config.analysis_id` [[Demo Analyses](https://github.com/NatLabRockies/T3CO/blob/main/src/t3co/resources/T3COConfig.csv)]

Note that `scenario.selection` and `vehicle.selection` are expected by the tool to be the same for a chosen *Vehicle-Scenario* pair, i.e., a row on the ***Scenario*** file has a corresponding row on the ***Vehicle*** file with the same `selection` key. The `config.selections` attribute accepts a list of "selection" (that refers to both `scenario.selection` and `vehicle.selection`) and is used to fetch the desired set of inputs to run.

### Auxiliary Inputs

The auxiliary input files in the [`t3co/resources/auxiliary/`](https://github.com/NatLabRockies/T3CO/tree/main/src/t3co/resources/auxiliary) folder include `FuelPrices.csv`, `ResidualValues.csv`, `AeroDragImprovementCostCurve.csv`, `LightweightImprovementCostCurve.csv`, and `EngineEffImprovementCostCurve.csv`. These files contain important cost and model assumptions that are necessary to run different aspects of the T3CO cost models. Users can select the default auxiliary input files and choose the relevant set of assumptions. They can also add new entries to these files, or create their own auxiliary input files and mention the new paths in the ***Config*** file.

## Running T3CO
After checking the inputs and creating/modifying an "Analysis" on the ***Config*** file, the next step is to execute the models. The `t3co/cli/sweep.py` module is the main script that needs to be run to perform a TCO analysis. And the most effective way to run the sweep module is to call a specific "Analysis" from the ***Config*** file using the `config.analysis_id` key.

### Running the Sweep Module from a PyPI-installed T3CO
The easiest way to run the `t3co.cli.sweep` module is to use a local copy of the demo input files. If the [`install_t3co_demo_inputs`](./installation.md#copy-demo-inputs) command is used to copy `demo_inputs` to your local directory after [installing from PyPI](./installation.md#installation-source-1-from-pypi), run the `t3co.cli.sweep` module from any directory. 

```bash
python -m t3co.cli.sweep --analysis-id=0 --config=<path/to/demo_inputs/T3COConfig.csv>
```
Point `--config` to the `T3COConfig.csv` file path and `--analysis-id` to the desired `config.analysis_id` (either an existing one or a newly added "Analysis" in the `demo_inputs/T3COConfig.csv` file. Default = `0`).

### Running Sweep Module from a Cloned Github repo
For running `config.analysis_id`=0 (or a user desired "Analysis") from the [Demo Config](https://github.com/NatLabRockies/T3CO/blob/main/src/t3co/resources/T3COConfig.csv) file on a cloned GitHub repo, run these commands from the parent directory:

```bash
python -m t3co.cli.sweep --analysis-id=0
```

## Running T3CO in Batch Mode (using multiprocessing)
The user can run T3CO in a "Batch Mode", which may be useful when running a large number of *Vehicle-Scenario* pairs or a large number of drivecycles or both. T3CO provides a demo analysis (`config.analysis_id`=3 in the sample T3COConfig.csv file) that runs the Batch Mode for a folder of multiple input drivecycles.

```bash
python -m t3co.cli.sweep --analysis-id=3 --run-multi
```

The Batch Mode allows T3CO to run parallel analyses utilizing multiple processors (or CPU cores) denoted by CLI argument `--n-processors`(defaults to 9). Adjust this number accordingly. To get the fastest run time, close other processor intensive programs running on your computer and assign `--n-processors` as one or two less than the max number of cores.

When a folder path is provided in the T3COConfig.csv file (`config.drive_cycle`) containing "n" number of valid drivecycles, T3CO generates "n" scenarios for each *Vehicle* selections mentioned in `config.selections` with the `scenario.drive_cycle` populated with each of the "n" drivecycles. For Vehicle selection "1" in config.selections, the generated selection numbers are denoted by "1_000" for the first drivecycle, "1_001" for the second drivecycle, and so on.

## Running T3CO Demo
T3CO presents a demo file (`src/t3co/demos/demo.py`) for generating a `TCOCalc` for a specific year and a `Ledger` object for a given vehicle, scenario, and energy inputs. It showcases the modularity of the tool and allows the user to also download the results as a JSON or CSV file.

## Other Command Line Interface arguments

Run `python -m t3co.cli.sweep --help` for the full list of CLI arguments. Common ones:

- `--plot [plotly|matplotlib]` — generate TCO charts after the run (see [Visualization](./pages/visualization.md)).
- `--run-multi` / `--n-processors N` — Batch Mode multiprocessing (see above).
- `--eia-api-key`, `--eia-aeo-year`, `--eia-aeo-case` — control EIA fuel price lookups.

### EIA Fuel Price Projections

Instead of the static `FuelPrices.csv`, T3CO can fetch regional projections from the EIA Annual Energy Outlook (AEO) API. Set `region` to a 5-digit US zipcode in `T3COConfig.csv`, add a free [EIA API key](https://www.eia.gov/opendata/register.php) to a `.env` file (`T3CO_EIA_API_KEY=...`), and run as usual (e.g. `--analysis-id=5`). See [What's New in 2.0](./whats_new.md#eia-fuel-price-projections) for the full behavior, fallbacks, and AEO year/case overrides.

### Fuel Price Overrides

For fuel-price sensitivity work, `--fuel-prices-json` takes a JSON string or file path with `zipcode` and `fuel_prices` keys; T3CO resolves the zipcode to a fuel-price region and overrides the matching `FuelPrices.csv` rows:

```bash
python -m t3co.cli.sweep \
  --analysis-id=0 \
  --fuel-prices-json='{"zipcode":"80302","fuel_prices":{"diesel_dol_per_gal":{"2025":4.25}}}'
```

## T3CO Results
After running the analysis, T3CO stores the results .CSV file in the directory specified by `config.dst_dir` (or the CLI argument `--dst-dir`). 

The results file includes a comprehensive list of [***Ledger Outputs***](./pages/ledger_outputs_descriptions.md) that were calculated by the various ***T3CO Modules***. In addition to the T3CO outputs, all the *Vehicle* input parameters (denoted by a prefix: `input_vehicle_value_`), *Scenario* input parameters(denoted by a prefix: `scenario_`), and *Config* parameters (denoted by a prefix: `config_`) are also present in the results file. When the optional optimization module is run, the optimized vehicle parameters are also listed ((denoted by a prefix: `optimized_vehicle_value_`)) instead of NaN values for non-optimization runs.

## T3CO Visualization

Turn a results CSV into a TCO breakdown chart, histogram, or violin plot — as static images (matplotlib) or interactive HTML (Plotly). Generate them automatically after a run with `--plot`:

```bash
python -m t3co.cli.sweep --analysis-id=0 --plot
```

See the [Visualization](./pages/visualization.md) page for the `T3COCharts` API, backends, and examples.
