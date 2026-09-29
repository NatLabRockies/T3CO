"""
Demo for the T3CO visualization module (:class:`t3co.visualize.charts.T3COCharts`).

This script builds a small T3CO results DataFrame from the bundled demo inputs
(without requiring FASTSim or the optimizer), then renders the three available
plots with both backends:

* ``backend="matplotlib"`` -> static PNG files
* ``backend="plotly"``     -> interactive, self-contained HTML files

A backend whose optional dependencies are not installed is skipped with a note;
install them with ``pip install "t3co[viz]"``.

Run from the repository root::

    python src/t3co/demos/visualization_demo.py

Outputs are written to ``./results/visualization/`` (relative to the working dir).
"""

from pathlib import Path

import pandas as pd

from t3co.energy_models import energy
from t3co.input_data import scenario, vehicle
from t3co.tco import ledger
from t3co.visualize.charts import T3COCharts

INPUTS_DIR = Path(__file__).resolve().parents[1] / "resources" / "inputs"
SCENARIO_FILE = INPUTS_DIR / "Demo_FY22_scenario_assumptions.csv"
VEHICLE_FILE = INPUTS_DIR / "Demo_FY22_vehicle_model_assumptions.csv"

OUT_DIR = Path.cwd() / "results" / "visualization"


def build_demo_results(max_per_fuel: int = 2, max_total: int = 12) -> pd.DataFrame:
    """
    Builds a small results DataFrame by running a handful of selections that span
    the available fuel types in the demo scenario file.

    Args:
        max_per_fuel (int): Max selections to include per distinct fuel type.
        max_total (int): Overall cap on the number of selections.

    Returns:
        pd.DataFrame: Flattened T3CO results, one row per selection.
    """
    scenario_df = pd.read_csv(SCENARIO_FILE)

    # Pick a spread of selections across fuel types for a varied breakdown chart.
    selections = []
    for _, group in scenario_df.groupby("fuel_type"):
        selections.extend(group["selection"].head(max_per_fuel).tolist())
    selections = sorted(selections)[:max_total]

    rows = []
    for sel in selections:
        try:
            veh = vehicle.Vehicle().from_csv(selection=sel, vehicle_db_file=VEHICLE_FILE)
            veh.set_veh_kg()
            scen = scenario.Scenario().from_csv(selection=sel, scenario_file=SCENARIO_FILE)
            eng = energy.Energy(mpgge=4.0, primary_fuel_range_mi=200.0)
            row = ledger.Ledger(vehicle=veh, scenario=scen, energy=eng).to_dict(
                flatten=True, exclude_list_fields=True
            )
            rows.append(row)
        except Exception as e:  # keep the demo resilient to any single bad selection
            print(f"  skipped selection {sel}: {type(e).__name__}: {e}")

    if not rows:
        raise RuntimeError("Could not build any demo results rows.")
    print(f"Built results for selections: {selections}")
    return pd.DataFrame(rows)


def render(results_df: pd.DataFrame, backend: str) -> None:
    """
    Renders the three plots for one backend and writes them to ``OUT_DIR``.

    Args:
        results_df (pd.DataFrame): The T3CO results to plot.
        backend (str): "matplotlib" (static PNG) or "plotly" (interactive HTML).
    """
    # T3COCharts imports the plotting libraries lazily, so a missing backend only
    # surfaces while rendering; skip that backend instead of crashing.
    try:
        _render(T3COCharts(results_df=results_df, backend=backend), backend)
    except ImportError as e:
        print(f"\n[{backend}] skipped - {e}")


def _render(tc: T3COCharts, backend: str) -> None:
    """Renders and writes the plots for one backend (see :func:`render`)."""
    print(f"\n[{backend}] available group columns: {tc.group_columns}")

    if backend == "plotly":
        # One self-contained HTML report titled "T3CO Results Explorer": a custom
        # x/y scatter, the TCO breakdown with a "Group by" dropdown (faceted
        # subplots), then a histogram and violin, each with their own dropdowns.
        report_items = [
            tc.interactive_explorer_html(),
            tc.grouped_tco_html(),
            tc.interactive_histogram_html(),
            tc.interactive_violin_html(default_y="mpgge"),
        ]
        out = OUT_DIR / "charts_plotly.html"
        T3COCharts.write_html_report(report_items, out)
        print(f"  wrote {out}")
    else:
        tco_fig = tc.generate_tco_plots(
            x_group_col="vehicle_fuel_type", subplot_group_col="vehicle_type", bar_width=0.7
        )
        violin_fig = tc.generate_violin_plot(x_group_col="vehicle_fuel_type", y_group_col="mpgge")
        hist_fig = tc.generate_histogram(hist_col="discounted_tco_dol", n_bins=5, show_pct=True)
        for name, fig in [("tco_breakdown", tco_fig), ("violin", violin_fig), ("histogram", hist_fig)]:
            out = OUT_DIR / f"{name}_matplotlib.png"
            fig.savefig(out, bbox_inches="tight", dpi=120)
            print(f"  wrote {out}")


def main() -> None:
    OUT_DIR.mkdir(parents=True, exist_ok=True)
    results_df = build_demo_results()

    results_csv = OUT_DIR / "visualization_demo_results.csv"
    results_df.to_csv(results_csv, index=False)
    print(f"Saved demo results to {results_csv}")

    for backend in ("plotly", "matplotlib"):
        render(results_df, backend)

    print(f"\nDone. See {OUT_DIR}")


if __name__ == "__main__":
    main()
