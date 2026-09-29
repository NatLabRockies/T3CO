import numpy as np
import pandas as pd
import pytest

from t3co.tco.summary import (
    compute_weights,
    discover_latest_results,
    load_results,
    main,
    summarize_results,
    weighted_mean,
)


def write_result(directory, ts, suffix, rows):
    name = f"results_{ts}_{suffix}.csv" if suffix else f"results_{ts}.csv"
    path = directory / name
    pd.DataFrame(rows).to_csv(path, index=False)
    return path


@pytest.fixture
def results_dir(tmp_path):
    write_result(
        tmp_path,
        "2026-01-01_10-00-00",
        "fleetA_diesel",
        [{"discounted_tco_dol": 999.0, "total_vmt": 1.0}],
    )
    write_result(
        tmp_path,
        "2026-01-02_10-00-00",
        "fleetA_diesel",
        [
            {"discounted_tco_dol": 100.0, "total_vmt": 10.0, "mpgge": 5.0},
            {"discounted_tco_dol": 300.0, "total_vmt": 30.0, "mpgge": 7.0},
        ],
    )
    write_result(
        tmp_path,
        "2026-01-01_10-00-00",
        "fleetA_BEV",
        [{"discounted_tco_dol": 200.0, "total_vmt": 20.0, "mpgge": 20.0}],
    )
    (tmp_path / "notes.csv").write_text("a\n1\n")
    (tmp_path / "results_bad-name.csv").write_text("a\n1\n")
    return tmp_path


def test_discover_latest_results_keeps_newest_per_suffix(results_dir):
    found = discover_latest_results(results_dir)
    assert list(found) == ["fleetA_BEV", "fleetA_diesel"]
    assert found["fleetA_diesel"].name.startswith("results_2026-01-02")


def test_discover_latest_results_handles_missing_suffix(tmp_path):
    write_result(tmp_path, "2026-01-01_10-00-00", "", [{"a": 1}])
    assert list(discover_latest_results(tmp_path)) == [""]


def test_load_results_from_dir_and_paths(results_dir):
    df = load_results(results_dir)
    assert len(df) == 3
    assert set(df["result_suffix"]) == {"fleetA_BEV", "fleetA_diesel"}

    paths = list(discover_latest_results(results_dir).values())
    assert load_results(paths).equals(df)


def test_load_results_empty_dir_raises(tmp_path):
    with pytest.raises(FileNotFoundError):
        load_results(tmp_path)


def test_compute_weights():
    assert compute_weights(pd.Series([1.0, 3.0])).tolist() == [0.25, 0.75]
    assert compute_weights(pd.Series([-1.0, 2.0])).tolist() == [0.0, 1.0]
    assert compute_weights(pd.Series([0.0, 0.0])).tolist() == [0.5, 0.5]


def test_weighted_mean_and_fallbacks():
    df = pd.DataFrame({"v": [100.0, 300.0, np.nan], "w": [10.0, 30.0, 5.0]})
    assert weighted_mean(df, "v", "w") == pytest.approx(250.0)

    zero = pd.DataFrame({"v": [100.0, 300.0], "w": [0.0, 0.0]})
    assert weighted_mean(zero, "v", "w") == pytest.approx(200.0)

    empty = pd.DataFrame({"v": [np.nan], "w": [1.0]})
    assert np.isnan(weighted_mean(empty, "v", "w"))


def test_summarize_results(results_dir):
    summary = summarize_results(load_results(results_dir)).set_index("result_suffix")

    diesel = summary.loc["fleetA_diesel"]
    assert diesel["n_runs"] == 2
    assert diesel["median_discounted_tco_dol"] == pytest.approx(200.0)
    assert diesel["weighted_mean_discounted_tco_dol"] == pytest.approx(250.0)
    assert diesel["weighted_mean_mpgge"] == pytest.approx(6.5)
    # (100*0.25 + 300*0.75) / (10*0.25 + 30*0.75)
    assert diesel["tco_dol_per_mi"] == pytest.approx(10.0)

    # Metrics absent from the results are skipped rather than filled.
    assert "median_msrp_total_dol" not in summary.columns


def test_summarize_results_options(results_dir):
    df = load_results(results_dir)
    df["fleet"] = df["result_suffix"].str.split("_").str[0]

    summary = summarize_results(
        df, group_cols=["fleet"], metrics=["discounted_tco_dol"], stats=["median"]
    )
    assert summary.columns.tolist() == [
        "fleet",
        "n_runs",
        "median_discounted_tco_dol",
        "tco_dol_per_mi",
    ]
    assert summary.loc[0, "n_runs"] == 3

    with pytest.raises(ValueError):
        summarize_results(df, stats=["mean"])
    with pytest.raises(KeyError):
        summarize_results(df, group_cols=["missing"])
    with pytest.raises(KeyError):
        summarize_results(df, weight_col="missing")


def test_main_writes_csv(results_dir, tmp_path, capsys):
    out = tmp_path / "out" / "summary.csv"
    summary = main(["--results-dir", str(results_dir), "--out", str(out)])

    assert out.exists()
    written = pd.read_csv(out)
    assert written["result_suffix"].tolist() == summary["result_suffix"].tolist()
    assert "fleetA_diesel" in capsys.readouterr().out
