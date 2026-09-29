"""Tests for the T3CO visualization module (t3co.visualize.charts.T3COCharts)."""

import sys

import numpy as np
import pandas as pd
import pytest

from t3co.constants import Global as gl
from t3co.visualize.charts import T3COCharts

# Bare Ledger cost fields that survive 2.0 flattening unchanged.
COST_COLS = list(T3COCharts.COST_COLS.keys())


def _purchasing_method_results(methods=("cash", "loan", "lease")) -> pd.DataFrame:
    """Real Ledger rows for one demo vehicle/scenario under each purchasing method."""
    from t3co.energy_models.energy import Energy
    from t3co.input_data.scenario import Scenario
    from t3co.input_data.vehicle import Vehicle
    from t3co.tco.ledger import Ledger

    inputs = gl.RESOURCES_FOLDERPATH / "inputs"
    rows = []
    for method in methods:
        vehicle = Vehicle.from_csv(
            selection=1, vehicle_db_file=inputs / "Demo_FY22_vehicle_model_assumptions.csv"
        )
        vehicle.set_veh_kg()
        scenario = Scenario.from_csv(
            selection=1, scenario_file=inputs / "Demo_FY22_scenario_assumptions.csv"
        )
        scenario.purchasing_method = method
        ledger = Ledger(
            vehicle=vehicle,
            scenario=scenario,
            energy=Energy(mpgge=4.0, primary_fuel_range_mi=200.0),
        )
        rows.append(ledger.to_dict(flatten=True, exclude_list_fields=True))
    return pd.DataFrame(rows)


def _make_results() -> pd.DataFrame:
    """Builds a small results frame using 2.0 *flattened* (prefixed) column names."""
    n = 6
    rows = []
    fuels = ["diesel", "BEV", "HEV"]
    for i in range(n):
        row = {
            "selection": i + 1,
            # legacy-format scenario_name also exercises the tech_progress parse
            "scenario_name": f"Class 8 Truck {i} ({fuels[i % 3]}, 2020, no program)",
            # nested-object columns as emitted by Ledger.to_dict(include_prefix=True)
            "scenario_fuel_type": fuels[i % 3],
            "scenario_vocation": "Long haul" if i % 2 else "Regional",
            "scenario_gvwr_kg": 36287.0 if i % 2 else 8000.0,
            "scenario_veh_year": 2020,
            "vehicle_veh_pt_type": fuels[i % 3],
            "discounted_tco_dol": 100000.0 + i * 5000,
            "mpgge": 4.0 + i * 0.1,
        }
        for k, col in enumerate(COST_COLS):
            row[col] = 1000.0 * (k + 1) + i * 100
        rows.append(row)
    return pd.DataFrame(rows)


@pytest.fixture
def results_df():
    return _make_results()


def test_normalizes_prefixed_columns(results_df):
    tc = T3COCharts(results_df=results_df, backend="plotly")
    df = tc.to_df()
    # prefixed source columns are mapped onto canonical grouping names
    assert "vehicle_fuel_type" in df.columns
    assert "vehicle_type" in df.columns
    assert "veh_pt_type" in df.columns
    assert "vehicle_weight_class" in df.columns
    assert list(df["vehicle_fuel_type"]) == list(results_df["scenario_fuel_type"])
    # weight class derived from GVWR (36287 -> Class 8, 8000 -> Class 5)
    assert set(df["vehicle_weight_class"]) == {"Class 8", "Class 5"}
    # tech_progress parsed from the legacy scenario_name format
    assert "tech_progress" in df.columns
    assert set(df["tech_progress"]) == {"no program"}
    # only present, valid group columns are exposed
    assert tc.group_columns[0] == "None"
    assert "vehicle_fuel_type" in tc.group_columns


def test_gvwr_above_50000_kg_is_class_8():
    df = _make_results()
    df["scenario_gvwr_kg"] = 60000.0
    tc = T3COCharts(results_df=df, backend="plotly")
    assert set(tc.to_df()["vehicle_weight_class"]) == {"Class 8"}


def test_missing_scenario_name_does_not_break_init():
    df = _make_results()
    df.loc[0, "scenario_name"] = None
    tc = T3COCharts(results_df=df, backend="plotly")  # must not raise
    # tech_progress can't be parsed for every row, so it is skipped
    assert "tech_progress" not in tc.to_df().columns


def _block_plotly(monkeypatch):
    """Make every plotly import fail, as when the viz extra isn't installed."""
    for module in ("plotly", "plotly.io", "plotly.offline", "plotly.express",
                   "plotly.graph_objects", "plotly.subplots"):
        monkeypatch.setitem(sys.modules, module, None)


@pytest.mark.parametrize(
    "build",
    [
        lambda tc, tmp: tc.interactive_explorer_html(),
        lambda tc, tmp: tc.grouped_tco_html(),
        lambda tc, tmp: tc.interactive_histogram_html(),
        lambda tc, tmp: tc.interactive_violin_html(),
        lambda tc, tmp: T3COCharts.write_html_report([], tmp / "report.html"),
    ],
)
def test_html_builders_give_viz_hint_without_plotly(results_df, tmp_path, monkeypatch, build):
    tc = T3COCharts(results_df=results_df, backend="plotly")
    _block_plotly(monkeypatch)
    # the friendly install hint, not a bare import error from plotly.io
    with pytest.raises(ImportError, match=r"t3co\[viz\]"):
        build(tc, tmp_path)


def test_demo_skips_a_missing_backend(results_df, monkeypatch, capsys):
    from t3co.demos import visualization_demo as demo

    _block_plotly(monkeypatch)
    demo.render(results_df, "plotly")  # must not raise
    assert "[plotly] skipped" in capsys.readouterr().out


def test_bad_backend_raises(results_df):
    with pytest.raises(ValueError):
        T3COCharts(results_df=results_df, backend="ggplot")


def test_requires_a_data_source():
    with pytest.raises(ValueError):
        T3COCharts()


def test_missing_tco_column_raises():
    df = _make_results().drop(columns=["discounted_tco_dol"])
    tc = T3COCharts(results_df=df, backend="plotly")
    with pytest.raises(KeyError):
        tc.generate_tco_plots()


# --------------------------- plotly backend --------------------------- #
def test_plotly_figures(results_df):
    go = pytest.importorskip("plotly.graph_objects")
    tc = T3COCharts(results_df=results_df, backend="plotly")

    tco = tc.generate_tco_plots(x_group_col="vehicle_fuel_type", subplot_group_col="vehicle_type")
    violin = tc.generate_violin_plot(x_group_col="vehicle_fuel_type", y_group_col="mpgge")
    hist = tc.generate_histogram(hist_col="discounted_tco_dol", n_bins=4, show_pct=True)

    assert isinstance(tco, go.Figure)
    assert isinstance(violin, go.Figure)
    assert isinstance(hist, go.Figure)
    # the TCO figure stacks one bar trace per cost component plus the TCO markers
    assert any(t.type == "bar" for t in tco.data)
    assert any(t.type == "scatter" for t in tco.data)


def test_plotly_ungrouped_tco(results_df):
    pytest.importorskip("plotly.graph_objects")
    tc = T3COCharts(results_df=results_df, backend="plotly")
    fig = tc.generate_tco_plots()  # no grouping
    assert fig is not None


def test_tco_stack_sums_to_tco_for_each_purchasing_method():
    tc = T3COCharts(results_df=_purchasing_method_results(), backend="plotly")
    df = tc.to_df()
    stack = tc._tco_stack_frame()
    # every bar decomposes the row's discounted TCO exactly
    np.testing.assert_allclose(stack.sum(axis=1), df["discounted_tco_dol"], atol=1.0)
    # cash stacks the MSRP breakdown; loan/lease stack down payment + payments
    financed = df["scenario_purchasing_method"].isin(["loan", "lease"]).to_numpy()
    msrp = stack[list(T3COCharts._MSRP_COMPONENTS)].sum(axis=1).to_numpy()
    financing = stack[list(T3COCharts._FINANCING_COMPONENTS)].sum(axis=1).to_numpy()
    assert (msrp[financed] == 0).all() and (financing[financed] > 0).all()
    assert (msrp[~financed] > 0).all() and (financing[~financed] == 0).all()


def test_plotly_tco_bars_sum_to_tco_marker():
    pytest.importorskip("plotly.graph_objects")
    tc = T3COCharts(results_df=_purchasing_method_results(), backend="plotly")
    fig = tc.generate_tco_plots()
    totals = sum(np.asarray(t.y, dtype=float) for t in fig.data if t.type == "bar")
    np.testing.assert_allclose(totals, tc.to_df()["discounted_tco_dol"], atol=1.0)
    # the negative residual must stack below zero and every other cost up from
    # zero; plotly's "stack" mode would instead start them from the residual
    assert fig.layout.barmode == "relative"


def test_ungrouped_tco_bars_are_separate_per_scenario(results_df):
    pytest.importorskip("plotly.graph_objects")
    tc = T3COCharts(results_df=results_df, backend="plotly")
    fig = tc.generate_tco_plots()  # ungrouped -> one bar per scenario
    bar_traces = [t for t in fig.data if t.type == "bar"]
    n = len(results_df)
    assert bar_traces
    for t in bar_traces:
        # each cost-component trace spans one distinct x per scenario (not merged onto one)
        assert len(set(t.x)) == n


def test_grouped_tco_keeps_bars_separate_when_label_repeats():
    pytest.importorskip("plotly.graph_objects")
    df = _make_results()
    df["scenario_fuel_type"] = "diesel"  # single fuel -> one subplot
    df["scenario_vocation"] = "Long haul"  # subplot label repeats for every row
    tc = T3COCharts(results_df=df, backend="plotly")
    fig = tc.generate_tco_plots(x_group_col="vehicle_fuel_type", subplot_group_col="vehicle_type")
    bar_traces = [t for t in fig.data if t.type == "bar"]
    assert bar_traces
    for t in bar_traces:
        # unique positions even though the vehicle_type label is identical for all rows
        assert len(set(t.x)) == len(df)


def test_grouped_tco_html_has_group_by_select(results_df):
    pytest.importorskip("plotly.graph_objects")
    tc = T3COCharts(results_df=results_df, backend="plotly")
    html = tc.grouped_tco_html()
    assert isinstance(html, str)
    # a "Group by" dropdown with an option per category (plus "None")
    assert "Group by:" in html
    assert "<select" in html and html.count("<option") >= 2
    # one plotly figure per group option, each in its own toggled div
    assert html.count("tco_grouped_") >= 2
    assert html.count('class="plotly-graph-div"') >= 2


def test_plotly_label_strips_mathtext():
    tc = T3COCharts(results_df=_make_results(), backend="plotly")
    assert tc._clean_plotly_text("[$MPGGE$]") == "[MPGGE]"
    assert tc._clean_plotly_text("[\\$]") == "[$]"


def test_interactive_histogram_html_has_column_select(results_df):
    pytest.importorskip("plotly.graph_objects")
    tc = T3COCharts(results_df=results_df, backend="plotly")
    html = tc.interactive_histogram_html()
    assert "Column:" in html
    assert html.count("<select") == 1 and html.count("<option") >= 2
    assert html.count('class="plotly-graph-div"') == 1
    assert "Plotly.restyle" in html


def test_interactive_violin_html_has_xy_selects(results_df):
    pytest.importorskip("plotly.graph_objects")
    tc = T3COCharts(results_df=results_df, backend="plotly")
    html = tc.interactive_violin_html()
    assert "X axis:" in html and "Y axis:" in html
    assert html.count("<select") == 2
    assert html.count('class="plotly-graph-div"') == 1
    assert "Plotly.restyle" in html


def test_report_has_pinned_title(tmp_path):
    go = pytest.importorskip("plotly.graph_objects")
    out = T3COCharts.write_html_report(
        [go.Figure(go.Scatter(x=[1], y=[1]))], tmp_path / "r.html"
    )
    html = out.read_text()
    assert "T3CO Results Explorer" in html
    assert "position:sticky" in html


def test_interactive_explorer_html_has_xy_selects(results_df):
    pytest.importorskip("plotly.graph_objects")
    tc = T3COCharts(results_df=results_df, backend="plotly")
    html = tc.interactive_explorer_html(
        default_x="vehicle_fuel_type", default_y="discounted_tco_dol"
    )
    assert isinstance(html, str)
    # two <select> dropdowns (X and Y), each with an option per candidate column
    assert "X axis:" in html and "Y axis:" in html
    assert html.count("<select") == 2
    # one scatter plot and client-side restyle wiring
    assert html.count('class="plotly-graph-div"') == 1
    assert "Plotly.restyle" in html


def test_save_default_plots_cli_hook(tmp_path, results_df):
    """The sweep --plot hook should write ONE combined HTML report next to the CSV."""
    pytest.importorskip("plotly.graph_objects")
    from t3co.cli.sweep import save_default_plots

    csv = tmp_path / "results.csv"
    results_df.to_csv(csv, index=False)
    saved = save_default_plots(csv, backend="plotly")

    # explorer + grouped breakdown + histogram + violin, combined into one HTML file
    assert len(saved) == 1
    report = saved[0]
    assert report.exists()
    assert report.suffix == ".html"
    assert report.parent == tmp_path
    html = report.read_text()
    # the grouped-breakdown "Group by" dropdown is present, and the report holds
    # several plots (the breakdown alone contributes one figure per group option)
    assert "Group by:" in html
    assert html.count('class="plotly-graph-div"') >= 4


def test_save_default_plots_report_write_failure_is_nonfatal(tmp_path, results_df, monkeypatch):
    pytest.importorskip("plotly.graph_objects")
    from t3co.cli.sweep import save_default_plots

    csv = tmp_path / "results.csv"
    results_df.to_csv(csv, index=False)

    def fail(*args, **kwargs):
        raise OSError("disk full")

    monkeypatch.setattr(T3COCharts, "write_html_report", staticmethod(fail))
    # the sweep's results are already saved, so a failed report write returns
    # no plots instead of raising
    assert save_default_plots(csv, backend="plotly") == []


def test_save_default_plots_png_failure_skips_only_that_plot(tmp_path, results_df, monkeypatch):
    mpl = pytest.importorskip("matplotlib")
    mpl.use("Agg")
    from matplotlib.figure import Figure

    from t3co.cli.sweep import save_default_plots

    csv = tmp_path / "results.csv"
    results_df.to_csv(csv, index=False)
    real_savefig = Figure.savefig
    attempts = {"n": 0}

    def flaky_savefig(self, *args, **kwargs):
        attempts["n"] += 1
        if attempts["n"] == 1:
            raise OSError("disk full")
        return real_savefig(self, *args, **kwargs)

    monkeypatch.setattr(Figure, "savefig", flaky_savefig)
    saved = save_default_plots(csv, backend="matplotlib")
    # the first write failed, but every remaining chart was still written
    assert len(saved) == attempts["n"] - 1 >= 1
    assert all(path.exists() for path in saved)


def test_write_html_report_combines_plots(tmp_path, results_df):
    pytest.importorskip("plotly.graph_objects")
    tc = T3COCharts(results_df=results_df, backend="plotly")
    figs = [
        tc.generate_tco_plots(x_group_col="vehicle_fuel_type"),
        tc.generate_histogram(hist_col="discounted_tco_dol", n_bins=4),
    ]
    out = T3COCharts.write_html_report(figs, tmp_path / "report.html")
    html = out.read_text()
    # both plots present in one page
    assert html.count('class="plotly-graph-div"') == 2
    # self-contained: the library is embedded inline, not loaded from a CDN <script src>
    assert 'src="https://cdn.plot.ly/plotly' not in html
    assert len(html) > 1_000_000


# ------------------------- matplotlib backend ------------------------- #
def test_matplotlib_figures(results_df):
    # matplotlib ships transitively with pymoo (a core dep), so the cost-breakdown
    # and histogram plots work without the viz extra; only the violin needs seaborn.
    mpl = pytest.importorskip("matplotlib")
    mpl.use("Agg")  # headless backend for CI
    from matplotlib.figure import Figure

    tc = T3COCharts(results_df=results_df, backend="matplotlib")

    tco = tc.generate_tco_plots(x_group_col="vehicle_fuel_type", subplot_group_col="vehicle_type")
    hist = tc.generate_histogram(hist_col="discounted_tco_dol", n_bins=4)

    assert isinstance(tco, Figure)
    assert isinstance(hist, Figure)


def test_matplotlib_tco_legend_is_clear_of_bars_and_in_stack_order():
    mpl = pytest.importorskip("matplotlib")
    mpl.use("Agg")
    tc = T3COCharts(results_df=_purchasing_method_results(), backend="matplotlib")
    fig = tc.generate_tco_plots()
    fig.canvas.draw()
    renderer = fig.canvas.get_renderer()
    axes_right = max(ax.get_tightbbox(renderer).x1 for ax in fig.axes)
    legend = fig.legends[0]
    # the legend sits right of the axes and their labels instead of over the bars
    assert legend.get_window_extent(renderer).x0 >= axes_right
    # TCO marker first, then the top of the stack first (residual is at the bottom)
    labels = [t.get_text() for t in legend.get_texts()]
    assert labels[0] == tc._label("discounted_tco_dol")
    assert labels[-1] == tc._label("residual_cost_dol")


def test_matplotlib_violin_requires_seaborn(results_df):
    pytest.importorskip("seaborn")  # seaborn is only needed for the violin plot
    mpl = pytest.importorskip("matplotlib")
    mpl.use("Agg")
    from matplotlib.figure import Figure

    tc = T3COCharts(results_df=results_df, backend="matplotlib")
    violin = tc.generate_violin_plot(x_group_col="vehicle_fuel_type", y_group_col="mpgge")
    assert isinstance(violin, Figure)


def test_seaborn_alias_maps_to_matplotlib(results_df):
    tc = T3COCharts(results_df=results_df, backend="seaborn")
    assert tc.backend == "matplotlib"
