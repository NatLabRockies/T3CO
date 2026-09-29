# What's New in T3CO 2.0

T3CO 2.0 is a major release that introduces live fuel price data fetching from the EIA API, an expanded optimization toolbox, a dataclass-driven configuration system, a new visualization module, and broader Python version support.

## EIA Fuel Price Projections

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

## Expanded Optimization Algorithms

The optimization module now supports four algorithms from the [PyMOO](https://pymoo.org/) framework:

| Algorithm | Config value | Use case |
|---|---|---|
| NSGA2 | `NSGA2` | Multi-objective (default) |
| Nelder-Mead | `NelderMead` | Single-objective, derivative-free simplex |
| Pattern Search | `PatternSearch` | Single-objective, derivative-free pattern |
| PSO | `PSO` | Single-objective, particle swarm |

Set the algorithm in the `algorithms` column of `T3COConfig.csv` or via the `--algorithms` CLI argument. Termination is handled by `DefaultMultiObjectiveTermination` with configurable tolerances (`x_tol`, `f_tol`, `n_max_gen`) on the Config file.

## Dataclass-Based Configuration

The three main input structures — `Config`, `Scenario`, and `Vehicle` — are now Python `dataclass` objects. This provides:

- **Type safety** with declared field types and defaults.
- **IDE auto-complete** and inline documentation.
- **Easier overrides** from the Config CSV, CLI arguments, or programmatic usage.

## Cost Toggles

A new `cost_toggles.json` file (configurable via `cost_toggles_file` on the Config) provides boolean switches for enabling or disabling individual cost model features. The first toggle shipped in 2.0:

| Toggle | Default | Description |
|---|---|---|
| `eia_fuel_prices` | `true` | Enable EIA API fuel price lookups when a zipcode is provided |

## Zipcode-Based Region Resolution

The `zipcodes` package is now a core dependency. When a US zipcode appears in the Config or Scenario `region` field, T3CO resolves it to the corresponding US Census division for fuel price lookups. This works for both EIA API queries and the `--fuel-prices-json` / `--fuel-prices-zipcode` CLI overrides.

## Configurable SSL Verification

For users behind corporate proxies with SSL inspection, T3CO supports the `T3CO_SSL_VERIFY` environment variable. Set it to `false` in your `.env` file to disable certificate verification for EIA API requests, or set it to the path of a custom CA bundle.

## Broader Python Support

The default T3CO install (without FASTSim) now supports **Python 3.9 through 3.13**. The FASTSim-integrated extras still require Python 3.9–3.10.

## New Config Parameters

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

## New Data Fetching Module

A new `t3co.data_fetching` module houses the `EIAClient` class, which provides:

- **Auto-discovery** of the latest AEO year and reference scenario via API introspection.
- **Retry logic** with exponential backoff for transient network errors.
- **Caching** to avoid redundant API calls within a session.
- **Data extrapolation** to fill gaps in the AEO time series using backfill and compound annual growth rates.

## Visualization Module

The `t3co.visualize.charts.T3COCharts` class generates TCO breakdown, histogram, and violin plots from a results CSV or DataFrame, with a selectable backend:

- `matplotlib` (default) — static PNG/PDF figures.
- `plotly` — interactive, self-contained HTML.

Plotting libraries ship as an optional extra (`pip install t3co[viz]`), and a sweep run can emit the charts automatically with `--plot`. See the [Visualization](./pages/visualization.md) page.

## Migration from 1.x

T3CO 2.0 is designed to be backward-compatible with existing input files. Key notes for users upgrading from 1.x:

- **No changes required** to existing `FuelPrices.csv`, Vehicle, or Scenario files.
- The `region` column is new to the Config file. Leaving it blank preserves 1.x behavior (scenario-level region lookup from `FuelPrices.csv`).
- The EIA feature is opt-in: it only activates when a zipcode is provided and an API key is configured.
- The `fuel_prices_source` parameter from earlier development has been removed; the data source is determined automatically based on the `region` value.
