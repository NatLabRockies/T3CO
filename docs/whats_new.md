# What's New in T3CO

## T3CO 2.1

T3CO 2.1 refines the residual-value model, adds visualization and results-summary modules, and makes vehicle optimization faster, reproducible, and available in batch mode.

### Refined residual-value model — TCO results change

The residual-value model computes a vehicle's residual as the product of (1 − depreciation rate) over each year of its life. For a vehicle with a 4-year life depreciating 9% a year, the residual value is 0.91⁴ = 68.6% of MSRP. Residual value is credited against cost, so this refinement lowers total cost of ownership, and it applies to every design the optimizer evaluates as well as to direct TCO runs.

Across the demo analyses in `T3COConfig.csv`, discounted TCO is 2.7% to 18.2% lower in 2.1 than in 2.0. **When comparing against 2.1 results, rerun earlier analyses with 2.1.**

### Visualization Module

The `t3co.visualize.charts.T3COCharts` class generates TCO breakdown, histogram, and violin plots from a results CSV or DataFrame, with a selectable backend:

- `matplotlib` — static PNG/PDF figures (the default when using the class from Python).
- `plotly` — interactive, self-contained HTML.

Plotting libraries ship as an optional extra (`pip install t3co[viz]`). A sweep run can generate the charts automatically: `--plot` writes one interactive Plotly report, and `--plot matplotlib` writes static PNGs. See the [Visualization](./pages/visualization.md) page.

### Results Summary

The new `t3co.tco.summary` module compares scenarios across runs. It collects the newest `results_<timestamp>_<suffix>.csv` for each result suffix in a directory and reports, per group, the number of runs, the median, and the VMT-weighted mean of the key ledger outputs, plus TCO per mile:

```bash
t3co_summarize --results-dir results/ --out results/summary.csv
```

`--group-by`, `--metrics`, and `--stats` control the grouping columns, ledger outputs, and statistics. To have a sweep write `summary_<results file>.csv` next to its results automatically, set the new Config column `summary_group_by` or pass `--summary-group-by`. See [Summarizing Results](./quick_start.md#summarizing-results).

### Faster, reproducible optimization

- **Latin Hypercube sampling.** NSGA2 seeds its population with Latin Hypercube sampling, as in T3CO 1.x, spreading the initial designs evenly across the knob bounds.
- **Convergence-based stopping.** The optimizer stops once the design and objective tolerances have held for `--n-last` generations, checked every `--nth-gen` generations (Config `n_last`, `nth_gen`). The demo optimization (`--analysis-id=1`) now finishes in 14 generations (about 10 s), down from 57 (about 35 s), and arrives at the same design, a 297 kW engine.
- **Reproducible results.** Each design evaluation is independent of the ones before it, so identical designs score identically, serial and parallel runs agree exactly, and repeated runs match.
- **Optimization in batch mode.** `--run-multi` supports analyses that optimize: selections run in parallel, and each optimization evaluates its designs within its own worker.
- **Standalone optimizer.** `python -m t3co.optimize.optimization` loads an analysis through the new `--config` and `--analysis-id` options, runs in parallel or serially, and matches the sweep module's results.
- **Parallelism controls.** `--n-processes` sets how many processes evaluate each generation's designs, and `--no-parallel` evaluates them one at a time.
- **Range constraint.** `constraint_range` can be enabled alongside the acceleration and gradeability constraints.

### Other changes

- New Ledger output `total_purchasing_payment_dol`: the discounted loan or lease payments included in TCO, so loan and lease results can be decomposed.
- CLI overrides accept both the `--flag=value` and `--flag value` forms, and an absolute `--dst-dir` is created if it does not exist yet.
- EIA API keys are redacted from log and error messages.
- `t3co.__version__` reports the installed package version.
- The `fastsim` extra is constrained to `>=2.1.1,<2.1.3` to stay compatible with NumPy 1.x.

## T3CO 2.0

T3CO 2.0 is a major release that introduces live fuel price data fetching from the EIA API, an expanded optimization toolbox, a dataclass-driven configuration system, and broader Python version support.

### EIA Fuel Price Projections

T3CO can now fetch fuel price projections directly from the [EIA Annual Energy Outlook (AEO)](https://www.eia.gov/outlooks/aeo/) API, replacing the need to manually maintain a static `FuelPrices.csv` file.

**How it works:**

- Set the `region` column in the Config or Scenario file to a 5-digit US zipcode (e.g. `90210`).
- T3CO auto-discovers the **latest** AEO publication year and reference scenario available from the EIA API.
- The zipcode is resolved to a **US Census division** (e.g. `90210` in California maps to the *Pacific* division) using the `zipcodes` package.
- Region-specific nominal fuel price projections for **diesel, gasoline, electricity, and CNG** are fetched for every year in the AEO outlook horizon.
- **Hydrogen** prices are not available in the AEO and fall back to the static `FuelPrices.csv`.

**Setup:**

1. Register for a free API key at [eia.gov/opendata/register.php](https://www.eia.gov/opendata/register.php).
2. Create a `.env` file from the provided `.env.example` template:
   ```bash
   cp .env.example .env
   ```
3. Add your key:
   ```
   T3CO_EIA_API_KEY=your_api_key_here
   ```
4. Set `region` to a US zipcode in `T3COConfig.csv` and run T3CO as usual.

If the `eia_fuel_prices` toggle in `cost_toggles.json` is `false`, or no zipcode is provided, or no API key is set, T3CO falls back to the static `FuelPrices.csv` just as in 1.x.

AEO year and scenario can be pinned via Config columns `eia_aeo_year` and `eia_aeo_case`, or via CLI arguments `--eia-aeo-year` and `--eia-aeo-case`.

### Expanded Optimization Algorithms

The optimization module now supports four algorithms from the [PyMOO](https://pymoo.org/) framework:

| Algorithm | Config value | Use case |
|---|---|---|
| NSGA2 | `NSGA2` | Multi-objective (default) |
| Nelder-Mead | `NelderMead` | Single-objective, derivative-free simplex |
| Pattern Search | `PatternSearch` | Single-objective, derivative-free pattern |
| PSO | `PSO` | Single-objective, particle swarm |

Set the algorithm in the `algorithms` column of `T3COConfig.csv` or via the `--algorithms` CLI argument. Termination is handled by `DefaultMultiObjectiveTermination` with configurable tolerances (`x_tol`, `f_tol`, `n_max_gen`) on the Config file.

### Dataclass-Based Configuration

The three main input structures — `Config`, `Scenario`, and `Vehicle` — are now Python `dataclass` objects. This provides:

- **Type safety** with declared field types and defaults.
- **IDE auto-complete** and inline documentation.
- **Easier overrides** from the Config CSV, CLI arguments, or programmatic usage.

### Cost Toggles

A new `cost_toggles.json` file (configurable via `cost_toggles_file` on the Config) provides boolean switches for enabling or disabling individual cost model features. The first toggle shipped in 2.0:

| Toggle | Default | Description |
|---|---|---|
| `eia_fuel_prices` | `true` | Enable EIA API fuel price lookups when a zipcode is provided |

### Zipcode-Based Region Resolution

The `zipcodes` package is now a core dependency. When a US zipcode appears in the Config or Scenario `region` field, T3CO resolves it to the corresponding US Census division for fuel price lookups. This works for both EIA API queries and the `--fuel-prices-json` / `--fuel-prices-zipcode` CLI overrides.

### Configurable SSL Verification

For users behind corporate proxies with SSL inspection, T3CO supports the `T3CO_SSL_VERIFY` environment variable. Set it to `false` in your `.env` file to disable certificate verification for EIA API requests, or set it to the path of a custom CA bundle.

### Broader Python Support

The default T3CO install (without FASTSim) now supports **Python 3.9 through 3.13**. The FASTSim-integrated extras still require Python 3.9–3.10.

### New Config Parameters

The following parameters have been added to the Config file in 2.0:

| Parameter | Description |
|---|---|
| `region` | Fuel price region name or US zipcode |
| `eia_aeo_year` | AEO publication year (blank = auto-discover latest) |
| `eia_aeo_case` | AEO scenario case ID (blank = auto-discover reference case) |
| `cost_toggles_file` | Path to cost toggles JSON file |
| `pop_size` | Population size for NSGA2 algorithm |
| `x_tol` | Design space convergence tolerance |
| `f_tol` | Objective function convergence tolerance |
| `n_max_gen` | Maximum optimization generations |
| `TCO_method` | TCO calculation method (`DIRECT` or `EFFICIENCY`) |
| `purchasing_method` | Vehicle purchasing method (`cash`, `loan`, or `lease`) |

### New Data Fetching Module

A new `t3co.data_fetching` module houses the `EIAClient` class, which provides:

- **Auto-discovery** of the latest AEO year and reference scenario via API introspection.
- **Retry logic** with exponential backoff for transient network errors.
- **Caching** to avoid redundant API calls within a session.
- **Data extrapolation** to fill gaps in the AEO time series using backfill and compound annual growth rates.

### Migration from 1.x

T3CO 2.0 is designed to be backward-compatible with existing input files. Key notes for users upgrading from 1.x:

- **No changes required** to existing `FuelPrices.csv`, Vehicle, or Scenario files.
- The `region` column is new to the Config file. Leaving it blank preserves 1.x behavior (scenario-level region lookup from `FuelPrices.csv`).
- The EIA feature is opt-in: it only activates when a zipcode is provided and an API key is configured.
- The `fuel_prices_source` parameter from earlier development has been removed; the data source is determined automatically based on the `region` value.
