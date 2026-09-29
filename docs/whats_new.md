# What's New in T3CO

## T3CO 2.1

T3CO 2.1 corrects a residual-value error in 2.0 that affected every total-cost-of-ownership result, adds a visualization module, and makes vehicle optimization faster, reproducible, and usable alongside batch mode.

### Residual value correction — TCO results change

**Every TCO result produced by T3CO 2.0.0 overstated total cost of ownership.** Residual-value depreciation was applied twice. For a vehicle with a 4-year life depreciating 9% a year, the residual should be 0.91⁴ = 68.6% of MSRP; 2.0.0 used 0.91⁸ = 47.0%. Because the residual is credited against cost, understating it inflated TCO. Runs that used the optimization module were affected further, since the error compounded each time the optimizer re-evaluated a design.

Across the demo analyses in `T3COConfig.csv`, discounted TCO falls by 2.7% to 18.2% in 2.1. **Results produced with 2.0.x are not comparable with 2.1 and should be regenerated.**

### Visualization Module

The `t3co.visualize.charts.T3COCharts` class generates TCO breakdown, histogram, and violin plots from a results CSV or DataFrame, with a selectable backend:

- `matplotlib` (default) — static PNG/PDF figures.
- `plotly` — interactive, self-contained HTML.

Plotting libraries ship as an optional extra (`pip install t3co[viz]`), and a sweep run can emit the charts automatically with `--plot`. See the [Visualization](./pages/visualization.md) page.

### Faster, reproducible optimization

- **NSGA2 matches T3CO 1.x.** The population is again seeded with Latin Hypercube sampling, as in 1.0.11, rather than pymoo's uniform random default.
- **Convergence now ends the run.** `--n-last` and `--nth-gen` (Config `n_last`, `nth_gen`) are passed to the optimizer; previously they were ignored and no run could stop before generation 50. The demo optimization (`--analysis-id=1`) drops from 57 generations (about 35 s) to 14 generations (about 10 s), and arrives at the same design (a 297 kW engine).
- **Reproducible results.** The optimizer no longer leaves state behind between design evaluations, so identical designs score identically, serial and parallel runs agree exactly, and a run repeats exactly.
- **Batch mode with optimization.** `--run-multi` now works for analyses that optimize; it previously aborted with `daemonic processes are not allowed to have children`.
- **Standalone optimizer.** `python -m t3co.optimize.optimization` loads an analysis through new `--config` and `--analysis-id` options and matches the sweep module's results. It previously hung in its default parallel mode and, when run serially, silently used defaults that matched no analysis.
- **New CLI options.** `--n-processes` sets the optimizer's process count and `--no-parallel` evaluates designs serially; serial evaluation previously failed outright.
- **Range constraint.** Enabling `constraint_range` no longer aborts the run on the first generation.

### Other changes

- New Ledger output `total_purchasing_payment_dol`: the discounted loan or lease payments included in TCO, so loan and lease results can be decomposed.
- CLI overrides written as `--flag=value` are now honored; previously only `--flag value` took effect. An absolute `--dst-dir` that does not yet exist is created.
- The EIA API key is no longer written to logs or error messages when a request fails.
- `t3co.__version__` reports the installed version; it previously always reported `0.0.1`.
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
