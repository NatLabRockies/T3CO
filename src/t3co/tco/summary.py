"""
Summarize T3CO result files into one grouped comparison table.

A sweep writes one ``results_<YYYY-MM-DD_HH-MM-SS>_<suffix>.csv`` file per run
(see ``t3co.cli.sweep.create_results_filepath``). This module collects the newest
file per suffix, concatenates them, and reports per-group run counts, medians and
VMT-weighted means of ledger outputs.

    t3co_summarize --results-dir results/ --out results/summary.csv
"""

import argparse
import re
from pathlib import Path
from typing import Dict, Iterable, List, Optional, Sequence, Union

import numpy as np
import pandas as pd

# results_<YYYY-MM-DD_HH-MM-SS>[_<suffix>].csv
RESULT_FILE_RE = re.compile(
    r"^results_(?P<ts>\d{4}-\d{2}-\d{2}_\d{2}-\d{2}-\d{2})(?:_(?P<suffix>.+))?\.csv$"
)

DEFAULT_METRICS = [
    "discounted_tco_dol",
    "discounted_total_cap_cost_dol",
    "discounted_total_oper_cost_dol",
    "discounted_downtime_oppy_cost_dol",
    "msrp_total_dol",
    "total_fuel_cost_dol",
    "total_maintenance_cost_dol",
    "insurance_cost_dol",
    "residual_cost_dol",
    "mpgge",
    "total_vmt",
]

STATS = ("median", "weighted_mean")


def discover_latest_results(
    results_dir: Union[str, Path], pattern: str = "results_*.csv"
) -> Dict[str, Path]:
    """
    Finds the newest result file per suffix in results_dir. Reruns leave earlier
    timestamped files behind, which would otherwise be double-counted.

    Args:
        results_dir (Union[str, Path]): Directory containing T3CO result CSVs.
        pattern (str, optional): Glob pattern for candidate files. Defaults to "results_*.csv".

    Returns:
        Dict[str, Path]: Mapping of result suffix to its newest file, sorted by suffix.
    """
    latest = {}
    for path in Path(results_dir).glob(pattern):
        m = RESULT_FILE_RE.match(path.name)
        if not m:
            continue
        suffix = m["suffix"] or ""
        if suffix not in latest or m["ts"] > latest[suffix][0]:
            latest[suffix] = (m["ts"], path)
    return {suffix: path for suffix, (_, path) in sorted(latest.items())}


def load_results(
    source: Union[str, Path, Iterable[Union[str, Path]]],
) -> pd.DataFrame:
    """
    Loads and concatenates T3CO result files, adding a result_suffix column.

    Args:
        source (Union[str, Path, Iterable[Union[str, Path]]]): A results directory
            (newest file per suffix is used) or an explicit list of result files.

    Returns:
        pd.DataFrame: Concatenated results with a result_suffix column.
    """
    if isinstance(source, (str, Path)) and Path(source).is_dir():
        files = discover_latest_results(source)
    else:
        paths = [source] if isinstance(source, (str, Path)) else source
        files = {}
        for path in map(Path, paths):
            m = RESULT_FILE_RE.match(path.name)
            files[(m["suffix"] or "") if m else path.stem] = path

    if not files:
        raise FileNotFoundError(f"No T3CO result files found in {source}")

    frames = [
        pd.read_csv(path).assign(result_suffix=suffix) for suffix, path in files.items()
    ]
    return pd.concat(frames, ignore_index=True)


def compute_weights(values: pd.Series) -> pd.Series:
    """
    Normalizes values (e.g. VMT) into weights summing to 1. Negative values are
    clipped to 0, and equal weights are used if no positive values remain.

    Args:
        values (pd.Series): Raw weighting values.

    Returns:
        pd.Series: Normalized weights.
    """
    positive = pd.to_numeric(values, errors="coerce").clip(lower=0).fillna(0)
    total = positive.sum()
    if total > 0:
        return positive / total
    if len(values) > 0:
        return pd.Series(1.0 / len(values), index=values.index)
    return pd.Series(dtype=float, index=values.index)


def weighted_mean(frame: pd.DataFrame, value_col: str, weight_col: str) -> float:
    """
    Weighted mean of value_col by weight_col, ignoring rows where either is NaN.
    Falls back to the unweighted mean when the weights sum to zero or less.

    Args:
        frame (pd.DataFrame): Input data.
        value_col (str): Column to average.
        weight_col (str): Column to weight by.

    Returns:
        float: Weighted mean, or NaN if there are no valid values.
    """
    values = pd.to_numeric(frame[value_col], errors="coerce")
    weights = pd.to_numeric(frame[weight_col], errors="coerce")
    valid = values.notna() & weights.notna()
    if not valid.any():
        return float(values.mean()) if values.notna().any() else np.nan
    values, weights = values[valid], weights[valid].clip(lower=0)
    if weights.sum() <= 0:
        return float(values.mean())
    return float((values * weights).sum() / weights.sum())


def summarize_results(
    results_df: pd.DataFrame,
    group_cols: Sequence[str] = ("result_suffix",),
    metrics: Optional[Sequence[str]] = None,
    weight_col: str = "total_vmt",
    stats: Sequence[str] = STATS,
) -> pd.DataFrame:
    """
    Summarizes T3CO results per group: run count plus the requested statistics
    for each metric column. Metrics absent from results_df are skipped.

    Args:
        results_df (pd.DataFrame): T3CO results, e.g. from load_results.
        group_cols (Sequence[str], optional): Columns to group by. Defaults to ("result_suffix",).
        metrics (Optional[Sequence[str]], optional): Metric columns. Defaults to DEFAULT_METRICS.
        weight_col (str, optional): Column used for weighted means. Defaults to "total_vmt".
        stats (Sequence[str], optional): Any of "median", "weighted_mean". Defaults to both.

    Returns:
        pd.DataFrame: One row per group with n_runs, <stat>_<metric> columns and,
        when available, tco_dol_per_mi (weighted discounted TCO over weighted VMT).
    """
    group_cols = list(group_cols)
    unknown = set(stats) - set(STATS)
    if unknown:
        raise ValueError(f"Unknown stats {sorted(unknown)}; choose from {STATS}")
    missing_groups = [c for c in group_cols if c not in results_df.columns]
    if missing_groups:
        raise KeyError(f"Group columns not in results: {missing_groups}")

    metrics = [m for m in (metrics or DEFAULT_METRICS) if m in results_df.columns]
    has_weight = weight_col in results_df.columns
    if "weighted_mean" in stats and not has_weight:
        raise KeyError(f"Weight column '{weight_col}' not in results")

    records: List[Dict] = []
    for key, group in results_df.groupby(group_cols, sort=True):
        key = key if isinstance(key, tuple) else (key,)
        rec = dict(zip(group_cols, key))
        rec["n_runs"] = len(group)
        for metric in metrics:
            if "median" in stats:
                rec[f"median_{metric}"] = pd.to_numeric(
                    group[metric], errors="coerce"
                ).median()
            if "weighted_mean" in stats:
                rec[f"weighted_mean_{metric}"] = weighted_mean(
                    group, metric, weight_col
                )
        if has_weight and {"discounted_tco_dol", "total_vmt"} <= set(group.columns):
            rec["tco_dol_per_mi"] = _dollars_per_mile(group, weight_col)
        records.append(rec)
    return pd.DataFrame(records)


def _dollars_per_mile(group: pd.DataFrame, weight_col: str) -> float:
    w = compute_weights(group[weight_col])
    dollars = (pd.to_numeric(group["discounted_tco_dol"], errors="coerce") * w).sum()
    miles = (pd.to_numeric(group["total_vmt"], errors="coerce") * w).sum()
    return float(dollars / miles) if miles else np.nan


def main(argv: Optional[List[str]] = None) -> pd.DataFrame:
    """
    Command-line entry point: loads the newest result file per suffix from a
    results directory, summarizes it, prints the table and optionally writes a CSV.
    """
    ap = argparse.ArgumentParser(
        description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter
    )
    ap.add_argument("--results-dir", type=Path, required=True)
    ap.add_argument("--group-by", nargs="+", default=["result_suffix"])
    ap.add_argument("--metrics", nargs="+", default=None)
    ap.add_argument("--weight-col", default="total_vmt")
    ap.add_argument("--stats", nargs="+", choices=STATS, default=list(STATS))
    ap.add_argument("--out", type=Path, default=None, help="CSV output path")
    args = ap.parse_args(argv)

    summary = summarize_results(
        load_results(args.results_dir),
        group_cols=args.group_by,
        metrics=args.metrics,
        weight_col=args.weight_col,
        stats=args.stats,
    )
    with pd.option_context("display.width", 200, "display.max_columns", None):
        print(summary.to_string(index=False))
    if args.out:
        args.out.parent.mkdir(parents=True, exist_ok=True)
        summary.to_csv(args.out, index=False)
        print(f"\nwrote {args.out}")
    return summary


if __name__ == "__main__":
    main()
