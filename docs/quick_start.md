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

When a folder path is provided in the T3COConfig.csv file (`config.drive_cycle`) containing "n" number of valid drivecycles, T3CO generates "n" scenarios for each *Vehicle* selections mentioned in `config.selections` with the `scenario.drive_cycle` populated with each of the "n" drivecycles. For Vehicle selection "1" in config.selections, the generated selection numbers are denoted by "1_0000" for the first drivecycle, "1_0001" for the second drivecycle, and so on.

## Optimizing Vehicle Designs
An analysis optimizes when `skip_all_opt` is `FALSE` in its Config row, as in the demo analysis `config.analysis_id`=1. For each selection, T3CO sizes the powertrain within the Scenario's `knob_min_*`/`knob_max_*` bounds to minimize discounted TCO, subject to whichever performance constraints are enabled (`constraint_accel`, `constraint_grade`, `constraint_range`). The optimized values are written to the results as `optimized_vehicle_value_*` columns.

```bash
python -m t3co.cli.sweep --analysis-id=1
```

Each setting below can be given as a CLI flag or as a column in the Config file; a CLI flag overrides the Config value.

| CLI flag | Config column | Default | Meaning |
|---|---|---|---|
| `--algorithms` | `algorithms` | `NSGA2` | `NSGA2`, `PatternSearch`, `NelderMead`, or `PSO`. If several are given, the first is used. NSGA2 seeds its population with Latin Hypercube sampling. |
| `--pop-size` | `pop_size` | 25 | Designs evaluated per generation (NSGA2). |
| `--n-max-gen` | `n_max_gen` | 1000 | Hard limit on the number of generations. |
| `--x-tol` | `x_tol` | 0.001 | Design-space tolerance for convergence. |
| `--f-tol` | `f_tol` | 0.001 | Objective-space tolerance for convergence. |
| `--n-last` | `n_last` | 5 | Number of recent generations that must all satisfy the tolerances before the run stops. |
| `--nth-gen` | `nth_gen` | 1 | Check convergence every `nth_gen` generations. |
| `--n-processes` | `n_processes` | 9 | Processes used to evaluate each generation's designs in parallel. |
| `--no-parallel` | `parallel` (`FALSE`) | parallel | Evaluate designs one at a time instead. Results are identical; only run time changes. |

**Choosing between the two kinds of parallelism.** Within a single optimization, each generation's designs are evaluated across `--n-processes` processes. With `--run-multi`, whole selections instead run in parallel across `--n-processors` workers, and each optimization then evaluates its designs serially inside its worker, since a pool worker cannot start a pool of its own. Use the default for one or a few optimizing selections, and `--run-multi` when there are many.

To optimize a single selection without writing a results file, run the optimization module directly. It prints the best design and its discounted TCO:

```bash
python -m t3co.optimize.optimization --selection 1 --analysis-id 1 --n-processes 4
```

It accepts `--config` (default: the bundled `T3COConfig.csv`), `--analysis-id` (default `1`), `--selection` (default `1`), `--n-processes` (default `9`), and `--no-parallel`.

## Running T3CO Demo
T3CO presents a demo file (`src/t3co/demos/demo.py`) for generating a `TCOCalc` for a specific year and a `Ledger` object for a given vehicle, scenario, and energy inputs. It showcases the modularity of the tool and allows the user to also download the results as a JSON or CSV file.

## Other Command Line Interface arguments

Run `python -m t3co.cli.sweep --help` for the full list of CLI arguments. Common ones:

- `--plot [plotly|matplotlib]` — generate TCO charts after the run: `plotly` (the default when no backend is given) writes one interactive HTML report, and `matplotlib` writes static PNGs (see [Visualization](./pages/visualization.md)).
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

### Summarizing Results
To compare scenarios across several runs, `t3co_summarize` (or `python -m t3co.tco.summary`) collects the newest `results_<timestamp>_<suffix>.csv` for each result suffix in a directory. It reports the number of runs, the median, and the VMT-weighted mean of the key ledger outputs, plus the TCO per mile for each group:
```bash
t3co_summarize --results-dir results/ --out results/summary.csv
```
Use `--group-by` to group by other result columns (e.g. `scenario_vehicle_class`), `--metrics` to choose ledger columns, `--stats` to choose between `median` and `weighted_mean`, and `--weight-col` to weight the means by a column other than `total_vmt`. The same functions are available from Python through `t3co.tco.summary.load_results` and `summarize_results`.

To get a summary written automatically, set `summary_group_by` in the Config file (e.g. `scenario_model_year; vehicle_veh_pt_type`) or pass `--summary-group-by` to the sweep. The sweep then writes `summary_<results file>.csv` next to the results:
```bash
python -m t3co.cli.sweep --config T3COConfig.csv --analysis-id 0 --summary-group-by scenario_model_year vehicle_veh_pt_type
```

## T3CO Visualization

Turn a results CSV into a TCO breakdown chart, histogram, or violin plot — as static images (matplotlib) or interactive HTML (Plotly). Generate them automatically after a run with `--plot`, which writes one interactive Plotly report by default; add `matplotlib` for static PNGs instead:

```bash
python -m t3co.cli.sweep --analysis-id=0 --plot              # one interactive HTML report (default)
python -m t3co.cli.sweep --analysis-id=0 --plot matplotlib   # static PNGs, one per chart
```

See the [Visualization](./pages/visualization.md) page for the `T3COCharts` API, backends, and examples.
