from __future__ import annotations

import argparse
import ast
import csv
import heapq
import os
import shutil
import tempfile
import time
from functools import partial
from multiprocessing import Pool
from pathlib import Path
from typing import Dict, List, Tuple, Union

import pandas as pd

from t3co.constants import Global as gl
from t3co.energy_models.energy import Energy
from t3co.input_data.config import Config
from t3co.input_data.scenario import Scenario
from t3co.input_data.vehicle import Vehicle
from t3co.tco.ledger import Ledger
from t3co.utils.print_class_objects import get_path_object

try:
    try:
        from pymoo.parallelization.starmap import StarmapParallelization
    except ImportError:
        from pymoo.core.problem import StarmapParallelization
    from pymoo.optimize import minimize
    from t3co.optimize.optimization import (
        VehicleDesignOpt,
        build_algorithm,
        build_termination,
    )

    optimization_installed = True

except ImportError:
    optimization_installed = False


def _normalize_selections_arg(selections) -> list | None:
    if not selections:
        return None

    if len(selections) == 1 and isinstance(selections[0], list):
        return selections[0]

    return list(selections)


def _normalize_drive_cycle_arg(drive_cycle):
    if not drive_cycle:
        return None

    if len(drive_cycle) == 1:
        return drive_cycle[0]

    return drive_cycle


def _argument_was_provided(argv: list[str], *flags: str) -> bool:
    # Match both the space form (``--flag value``) and the equals form
    # (``--flag=value``); the latter is a single argv token.
    return any(
        token == flag or token.startswith(f"{flag}=")
        for token in argv
        for flag in flags
    )


def apply_cli_overrides(config: Config, args, argv: list[str] | None = None) -> Config:
    argv = [] if argv is None else argv

    override_specs = [
        (("--vehicles",), "vehicle_file", args.vehicles),
        (("--scenarios",), "scenario_file", args.scenarios),
        (("--eng-curves",), "eng_eff_imp_curves", args.eng_curves),
        (("--lw-curves",), "lw_imp_curves", args.lw_curves),
        (("--aero-curves",), "aero_drag_imp_curves", args.aero_curves),
        (("--dst-dir",), "dst_dir", args.dst_dir),
        (("--algorithms", "--algos", "--algo"), "algorithms", args.algorithms),
        (("--x-tol",), "x_tol", args.x_tol),
        (("--f-tol",), "f_tol", args.f_tol),
        (("--n-max-gen",), "n_max_gen", int(args.n_max_gen)),
        (("--pop-size",), "pop_size", int(args.pop_size)),
        (("--nth-gen",), "nth_gen", args.nth_gen),
        (("--n-last",), "n_last", args.n_last),
    ]

    for flags, attr_name, value in override_specs:
        if _argument_was_provided(argv, *flags):
            setattr(config, attr_name, value)

    if _argument_was_provided(argv, "--selections"):
        config.selections = _normalize_selections_arg(args.selections)

    if _argument_was_provided(argv, "--drive-cycle"):
        config.drive_cycle = _normalize_drive_cycle_arg(args.drive_cycle)

    if _argument_was_provided(argv, "--skip-all-opt", "--skopt"):
        config.skip_all_opt = True

    return config


def _get_primary_algorithm(config: Config) -> str:
    algorithms = config.algorithms
    if isinstance(algorithms, list):
        return str(algorithms[0])

    if isinstance(algorithms, str):
        algorithms = algorithms.strip()
        if not algorithms:
            return "NSGA2"
        if algorithms.startswith("["):
            parsed_algorithms = ast.literal_eval(algorithms)
            if isinstance(parsed_algorithms, list) and parsed_algorithms:
                return str(parsed_algorithms[0])
        return algorithms

    return "NSGA2"


def _build_optimization_algorithm(config: Config):
    return build_algorithm(
        _get_primary_algorithm(config), pop_size=int(config.pop_size)
    )


def _build_optimization_termination(config: Config):
    return build_termination(
        x_tol=float(config.x_tol),
        f_tol=float(config.f_tol),
        n_max_gen=int(config.n_max_gen),
    )


def load_vehicle_scenario_energy(
    selection: Union[int, str],
    config: Config,
    vehicle: Vehicle = None,
    scenario: Scenario = None,
    energy: Energy = None,
) -> Tuple[Vehicle, Scenario, Energy]:
    """
    Loads the vehicle, scenario, and energy models based on the selection and config.

    Args:
        selection (Union[int, str]): The selection index or string.
        config (Config): The configuration instance.

    Returns:
        Tuple[Vehicle, Scenario, Energy]: The vehicle, scenario, and energy models.
    """
    # Workaround for config.dc_files disappearing
    if (
        (not hasattr(config, "dc_files") or config.dc_files is None)
        and config.drive_cycle
        and Path(config.drive_cycle).is_dir()
    ):
        config.dc_files = [
            p.absolute() for p in Path(config.drive_cycle).rglob("*.csv")
        ]

    if isinstance(selection, str) and "_" in selection:
        selection, dc_id = map(int, selection.split("_"))

    if scenario:
        input_scenario = scenario
    else:
        input_scenario = Scenario().from_csv(
            selection=selection, scenario_file=config.scenario_file
        )
        input_scenario.override_from_config(config=config)

    if vehicle:
        input_vehicle = vehicle
    else:
        input_vehicle = Vehicle().from_config(selection=selection, config=config)
        input_vehicle.set_veh_kg()

    if config.dc_files:
        input_scenario.drive_cycle = config.dc_files[int(dc_id)]
        if config.energy_file:
            input_scenario.mpgge = config.energy_df.loc[int(dc_id), "mpgge"]
            input_scenario.primary_fuel_range_mi = config.energy_df.loc[
                int(dc_id),
                "primary_fuel_range_mi",
            ]

    if energy:
        input_energy = energy
    elif (
        input_scenario.mpgge
        and input_scenario.primary_fuel_range_mi
        and not input_scenario.cost_toggles.run_fastsim
    ):
        input_energy = Energy(
            mpgge=float(input_scenario.mpgge),
            primary_fuel_range_mi=float(input_scenario.primary_fuel_range_mi),
        )
    else:
        if not input_scenario.cost_toggles.run_fastsim:
            print(
                f"Warning: run_fastsim is False but mpgge ({input_scenario.mpgge}) "
                f"or primary_fuel_range_mi ({input_scenario.primary_fuel_range_mi}) are missing. "
                "Skipping FASTSim run. Energy values will be default (0)."
            )
            input_energy = Energy(mpgge=0.0, primary_fuel_range_mi=0.0)
        else:
            input_energy = Energy()
            input_energy.run_fastsim_model(
                veh_no=selection,
                vehicle_file=config.vehicle_file,
                scenario=input_scenario,
            )

    return input_vehicle, input_scenario, input_energy


def generate_ledger(selection: int, config: Config) -> Dict:
    """
    Generates the ledger for the given selection and config.

    Args:
        selection (int): The selection index.
        config (Config): The configuration instance.

    Returns:
        Dict: The ledger as a dictionary.
    """
    input_vehicle, input_scenario, input_energy = load_vehicle_scenario_energy(
        selection=selection, config=config
    )
    print(f"Running Selection: {selection}: {input_scenario.scenario_name}")

    if not config.skip_all_opt and optimization_installed:
        optimized_vehicle, optimized_energy = run_optimization(
            vehicle=input_vehicle, scenario=input_scenario, config=config
        )
    else:
        optimized_vehicle = None
        optimized_energy = None

    return Ledger(
        vehicle=(input_vehicle if not optimized_vehicle else optimized_vehicle),
        scenario=input_scenario,
        energy=(input_energy if optimized_energy is None else optimized_energy),
        config=config,
    ).to_dict(
        include_calcs=config.include_calcs,
        exclude_list_fields=config.exclude_list_fields,
    )


def run_optimization(vehicle: Vehicle, scenario: Scenario, config: Config):
    pool = None
    runner = None
    if config.parallel:
        pool = Pool(config.n_processes)
        runner = StarmapParallelization(pool.starmap)

    try:
        problem = VehicleDesignOpt(
            vehicle=vehicle, scenario=scenario, config=config, runner=runner
        )
        algorithm = _build_optimization_algorithm(config)

        res = minimize(
            problem,
            algorithm,
            termination=_build_optimization_termination(config),
            seed=1,
            verbose=True,
        )
    finally:
        if pool:
            pool.close()
            pool.join()

    optimized_vehicle, optimized_energy, _ = problem.evaluate_solution(res.X)
    print(optimized_vehicle)
    return optimized_vehicle, optimized_energy


def create_results_filepath(config: Config) -> Path:
    """
    Creates the results file path based on the config.

    Args:
        config (Config): The configuration instance.

    Returns:
        Path: The path to the results file.
    """
    ts = time.strftime("%Y-%m-%d_%H-%M-%S")
    if config.resfile_suffix:
        result_filename = f"results_{ts}_{str(config.resfile_suffix)}.csv".strip("_")
    else:
        selections_string = (
            str(config.selections)
            .strip("[]")
            .replace(" ", "")
            .replace("'", "")
            .replace(",", "-")
        )
        result_filename = f"results_{ts}_sel_{selections_string[:20]}.csv".strip("_")
    # Create an absolute output directory up front: get_path_object resolves
    # absolute paths strictly (they must exist), while a relative dst_dir is
    # joined onto the resources folder and created below.
    if Path(config.dst_dir).is_absolute():
        Path(config.dst_dir).mkdir(parents=True, exist_ok=True)

    output_path = get_path_object(config.dst_dir) / result_filename
    output_path.parent.mkdir(parents=True, exist_ok=True)

    return output_path


def append_results_to_csv(
    reports_list: List[Dict],
    output_path: Union[str, Path],
    write_header: bool = False,
) -> None:
    """
    Appends results to a CSV file incrementally to avoid memory issues.

    Args:
        reports_list (List[Dict]): The list of reports to append.
        output_path (Union[str, Path]): The output path for the CSV file.
        write_header (bool, optional): Whether to write the header. Defaults to False.
    """
    if not reports_list:
        return

    reports_df = pd.DataFrame(reports_list)
    mode = "w" if write_header else "a"
    reports_df.to_csv(
        output_path,
        mode=mode,
        header=write_header,
        index=False,
        doublequote=True,
        quoting=csv.QUOTE_ALL,
    )


def sort_csv_file(
    input_path: Union[str, Path],
    output_path: Union[str, Path] = None,
    sort_by: str = "selection",
    chunksize: int = 2000,
) -> Path:
    """
    Sorts a CSV file by a column using external merge sort to handle large files.

    Args:
        input_path (Union[str, Path]): The input CSV file path.
        output_path (Union[str, Path], optional): The output path. If None, overwrites input.
        sort_by (str, optional): Column name to sort by. Defaults to "selection".
        chunksize (int, optional): Number of rows per chunk. Defaults to 2000.

    Returns:
        Path: The output file path.
    """
    input_path = Path(input_path)
    if output_path is None:
        output_path = input_path
    else:
        output_path = Path(output_path)

    # Create a temporary directory for sorted chunks
    with tempfile.TemporaryDirectory() as temp_dir:
        temp_dir_path = Path(temp_dir)
        chunk_files = []

        with open(input_path, "r", newline="", encoding="utf-8") as f_in:
            # Use QUOTE_MINIMAL to avoid issues with unquoted booleans (e.g. True)
            # which cause QUOTE_NONNUMERIC to fail
            reader = csv.reader(f_in, doublequote=True, quoting=csv.QUOTE_MINIMAL)
            try:
                header = next(reader)
            except StopIteration:
                return output_path  # Empty file

            try:
                sort_idx = header.index(sort_by)
            except ValueError:
                print(f"Warning: Column '{sort_by}' not found. Skipping sort.")
                if input_path != output_path:
                    shutil.copy(input_path, output_path)
                return output_path

            chunk = []
            chunk_num = 0

            for row in reader:
                chunk.append(row)
                if len(chunk) >= chunksize:
                    # Sort chunk in memory
                    try:
                        chunk.sort(key=lambda x: float(x[sort_idx]))
                    except (ValueError, TypeError):
                        chunk.sort(key=lambda x: str(x[sort_idx]))

                    chunk_filename = temp_dir_path / f"chunk_{chunk_num}.csv"
                    with open(
                        chunk_filename, "w", newline="", encoding="utf-8"
                    ) as f_out:
                        writer = csv.writer(
                            f_out,
                            doublequote=True,
                            quoting=csv.QUOTE_ALL,
                        )
                        writer.writerows(chunk)

                    chunk_files.append(chunk_filename)
                    chunk = []
                    chunk_num += 1

            # Process last chunk
            if chunk:
                try:
                    chunk.sort(key=lambda x: float(x[sort_idx]))
                except (ValueError, TypeError):
                    chunk.sort(key=lambda x: str(x[sort_idx]))

                chunk_filename = temp_dir_path / f"chunk_{chunk_num}.csv"
                with open(chunk_filename, "w", newline="", encoding="utf-8") as f_out:
                    writer = csv.writer(
                        f_out,
                        doublequote=True,
                        quoting=csv.QUOTE_ALL,
                    )
                    writer.writerows(chunk)
                chunk_files.append(chunk_filename)

        # Merge chunks
        if not chunk_files:
            # Only header existed
            with open(output_path, "w", newline="", encoding="utf-8") as f_out:
                writer = csv.writer(
                    f_out,
                    doublequote=True,
                    quoting=csv.QUOTE_ALL,
                )
                writer.writerow(header)
            return output_path

        # Open all chunk files
        files = [open(cf, "r", newline="", encoding="utf-8") for cf in chunk_files]
        readers = [
            csv.reader(f, doublequote=True, quoting=csv.QUOTE_MINIMAL) for f in files
        ]

        # Use heapq.merge
        def key_func(row):
            val = row[sort_idx]
            try:
                return float(val)
            except (ValueError, TypeError):
                return str(val)

        with open(output_path, "w", newline="", encoding="utf-8") as f_out:
            writer = csv.writer(f_out, doublequote=True, quoting=csv.QUOTE_ALL)
            writer.writerow(header)

            for row in heapq.merge(*readers, key=key_func):
                writer.writerow(row)

        # Close files
        for f in files:
            f.close()

    return output_path

    return output_path


def export_results_to_csv(
    reports_list: List[Dict],
    config: Config,
    output_path: Union[str, Path] = None,
    return_filepath: bool = True,
    return_df: bool = False,
    sort_values: bool = False,
) -> Tuple[Union[Path, None], Union[pd.DataFrame, None]]:
    """
    Exports the results to a CSV file.

    Args:
        reports_list (List[Dict]): The list of reports.
        config (Config): The configuration instance.
        output_path (Union[str, Path], optional): The output path for the CSV file. Defaults to None.
        return_filepath (bool, optional): Whether to return the file path. Defaults to True.
        return_df (bool, optional): Whether to return the DataFrame. Defaults to False.
        sort_values (bool, optional): Whether to sort the values by selection. Defaults to False.

    Returns:
        Tuple[Union[Path, None], Union[pd.DataFrame, None]]: The output path and DataFrame if specified.
    """
    reports_df = pd.DataFrame(reports_list)

    if not output_path:
        output_path = create_results_filepath(config=config)

    if sort_values:
        reports_df = reports_df.sort_values(by="selection").reset_index(drop=True)

    reports_df.to_csv(
        output_path,
        index=False,
        escapechar="\\",
        doublequote=True,
        quoting=csv.QUOTE_NONNUMERIC,
    )

    return (output_path if return_filepath else None), (
        reports_df if return_df else None
    )


DEFAULT_PLOT_BACKEND = "plotly"


def save_default_plots(
    results_csv: Union[str, Path],
    backend: str = DEFAULT_PLOT_BACKEND,
) -> List[Path]:
    """
    Generates and saves a default set of TCO charts from a results CSV.

    Writes figures next to the results file: a TCO cost breakdown, a histogram of
    the discounted TCO, and - when a fuel-type grouping is available - a violin
    plot. With the Plotly backend all charts are combined into a single
    self-contained HTML report; with matplotlib each chart is a separate PNG.

    The plotting dependencies are optional; if they are missing (or charting
    fails) the run is unaffected and a note is printed.

    Args:
        results_csv (Union[str, Path]): Path to the T3CO results CSV.
        backend (str): "plotly" (interactive HTML) or "matplotlib" (static PNG).

    Returns:
        List[Path]: Paths of the saved figure files (empty if plotting was skipped).
    """
    try:
        from t3co.visualize.charts import T3COCharts
    except ImportError as e:
        print(f"Skipping --plot: {e}")
        return []

    results_csv = Path(results_csv)
    try:
        tc = T3COCharts(filename=results_csv, backend=backend)
    except Exception as e:
        print(f"Skipping --plot: could not initialize charts ({type(e).__name__}: {e})")
        return []

    out_dir = results_csv.parent
    stem = results_csv.stem

    group_col = "vehicle_fuel_type" if "vehicle_fuel_type" in tc.group_columns else "None"

    figure_specs = {}
    if tc.backend == "plotly":
        # Interactive HTML fragments with their own dropdowns.
        figure_specs["explorer"] = lambda: tc.interactive_explorer_html()
        # TCO breakdown with a client-side "Group by" dropdown that facets the
        # scenarios into subplots.
        figure_specs["tco_breakdown"] = lambda: tc.grouped_tco_html()
        figure_specs["tco_histogram"] = lambda: tc.interactive_histogram_html(n_bins=10)
        if group_col != "None":
            figure_specs["tco_violin"] = lambda: tc.interactive_violin_html(
                default_x=group_col, default_y="discounted_tco_dol"
            )
    else:
        # One separate stacked bar per scenario (ungrouped); pass grouping
        # columns explicitly to arrange the bars into subplots instead.
        figure_specs["tco_breakdown"] = lambda: tc.generate_tco_plots()
        figure_specs["tco_histogram"] = lambda: tc.generate_histogram(
            hist_col="discounted_tco_dol", n_bins=10
        )
        if group_col != "None":
            figure_specs["tco_violin"] = lambda: tc.generate_violin_plot(
                x_group_col=group_col, y_group_col="discounted_tco_dol"
            )

    # Generate the figures, skipping any individual chart that fails.
    figures = {}
    for name, make_fig in figure_specs.items():
        try:
            figures[name] = make_fig()
        except Exception as e:
            print(f"  could not generate '{name}' plot ({type(e).__name__}: {e})")
    if not figures:
        return []

    # Writing is best-effort too: a full disk or read-only folder must not fail
    # a sweep whose results CSV has already been saved.
    saved = []
    if tc.backend == "plotly":
        # Combine all charts into a single self-contained HTML report.
        out = out_dir / f"{stem}_charts.html"
        try:
            T3COCharts.write_html_report(list(figures.values()), out)
        except Exception as e:
            print(f"  could not write the plot report {out} ({type(e).__name__}: {e})")
            return []
        saved.append(out)
        print(f"Saved plots: {out}")
    else:
        for name, fig in figures.items():
            out = out_dir / f"{stem}_{name}.png"
            try:
                fig.savefig(out, bbox_inches="tight", dpi=120)
            except Exception as e:
                print(f"  could not write '{name}' plot to {out} ({type(e).__name__}: {e})")
                continue
            saved.append(out)
            print(f"Saved plot: {out}")
    return saved


def run_t3co(
    config: Config, save_results: bool = True, plot_backend: str = None
) -> None:
    """
    Runs the T3CO analysis.

    Args:
        config (Config): The configuration instance.
        save_results (bool, optional): Whether to save the results. Defaults to True.
        plot_backend (str, optional): If set ("plotly" or "matplotlib"), generates and
            saves default TCO charts next to the results CSV. Defaults to None.
    """
    reports_list = []
    error_list = []
    for selection in config.selections_list:
        # try:
        reports_list.append(generate_ledger(selection=selection, config=config))
        # except ValueError:
        #     error_list.append(selection)
        #     continue

    if save_results:
        output_path, reports_df = export_results_to_csv(
            reports_list=reports_list,
            config=config,
            return_filepath=True,
            return_df=True,
        )
        print(reports_df)
        if len(error_list):
            print(f"Selections {error_list} were skipped due to assumptions errors.")
        print(f"T3CO results saved to: {output_path}")
        if plot_backend and output_path:
            save_default_plots(output_path, backend=plot_backend)


if __name__ == "__main__":
    start = time.time()
    raw_argv = os.sys.argv[1:]

    parser = argparse.ArgumentParser(
        formatter_class=argparse.ArgumentDefaultsHelpFormatter,
        prog="SWEEP",
        description="""The sweep.py module is the main script to run T3CO""",
    )
    parser.add_argument(
        "--config",
        default=gl.RESOURCES_FOLDERPATH / "T3COConfig.csv",
        type=str,
        help="Input Config file",
    )
    parser.add_argument(
        "--analysis-id",
        default=0,
        type=int,
        help="Analysis key from input Config file - 'config.analysis_id'",
    )
    parser.add_argument(
        "--vehicles",
        default=gl.RESOURCES_FOLDERPATH
        / "inputs"
        / "Demo_FY22_vehicle_model_assumptions.csv",
        type=str,
        help="Input file for Vehicle models",
    )
    parser.add_argument(
        "--scenarios",
        default=gl.RESOURCES_FOLDERPATH
        / "inputs"
        / "Demo_FY22_scenario_assumptions.csv",
        type=str,
        help="Input file for Scenario models",
    )
    parser.add_argument(
        "--selections",
        type=ast.literal_eval,
        nargs="*",
        help="""Selections desired to run. Selections can be an int, or list of ints, or range expression. Ex: --selections 234 or --selections "[234,236,238]" or --selections "range(234, 150, 2)" """,
    )
    parser.add_argument(
        "--drive-cycle",
        type=ast.literal_eval,
        nargs="*",
        help="""Override drive_cycle from scenario with a composite cycle, or an individual cycle, or a folder of cycles. File paths should be relative to the resources folder """,
    )
    parser.add_argument(
        "--eng-curves",
        default=gl.RESOURCES_FOLDERPATH
        / "auxiliary"
        / "EngineEffImprovementCostCurve.csv",
        type=str,
        help="Input file for engine efficiency improvement cost curves",
    )
    parser.add_argument(
        "--lw-curves",
        default=gl.RESOURCES_FOLDERPATH
        / "auxiliary"
        / "LightweightImprovementCostCurve.csv",
        type=str,
        help="Input file for lightweighting improvement cost curves",
    )
    parser.add_argument(
        "--aero-curves",
        default=gl.RESOURCES_FOLDERPATH
        / "auxiliary"
        / "AeroDragImprovementCostCurve.csv",
        type=str,
        help="Input file for aerodynamics improvement curves",
    )
    parser.add_argument(
        "--look-for",
        default="",
        type=str,
        help="A string for string matching, example --look_for 'FCEV' or -look_for '[\"FCEV\", \"HEV\"]' ",
    )
    parser.add_argument(
        "--skip-all-opt",
        "--skopt",
        action="store_true",
        help="If --skip_all_opt used, all runs skip optimization",
    )
    parser.add_argument(
        "--skip-input-validation",
        "--skiv",
        action="store_false",
        help="If --skip_input_validation used, no pre-validation of inputs is run before sweep commences",
    )
    parser.add_argument(
        "--exclude",
        default=">{-<>-}<",
        type=str,
        nargs="*",
        help="Overrides -look_for. a string for string matching to exclude runs, example -exclude 'FCEV' or -look_for '[\"FCEV\", \"HEV\"]'  ",
    )
    parser.add_argument(
        "--algorithms",
        "--algos",
        "--algo",
        default="NSGA2",
        type=str,
        nargs="*",
        help='Enter algorithm or list of algorithms, or "ensemble" to use all, to use for optimization: ex: -algos PatternSearch | -algos \'["PatternSearch", "NSGA2"]\' | -algos "ensemble" ',
    )
    parser.add_argument(
        "--dst-dir",
        default=gl.SWEEP_PATH.parents[2] / "results",
        type=str,
        help="Directory to store T3CO results",
    )
    parser.add_argument(
        "--dir-mark",
        default="",
        type=str,
        help="Name for results directory in addition to timestamp",
    )
    parser.add_argument(
        "--file-mark",
        default="",
        type=str,
        help="Prefix to add to the result file names",
    )
    parser.add_argument(
        "--skip-save-veh",
        action="store_true",
        help="Toggle result vehicle model YAML file saving off",
    )
    parser.add_argument(
        "--x-tol",
        default=0.001,
        type=float,
        help="Parameter space tolerance for optimization",
    )
    parser.add_argument(
        "--f-tol",
        default=0.001,
        type=float,
        help="Objective space tolerance for optimization",
    )
    parser.add_argument(
        "--n-max-gen",
        default=1000,
        type=float,
        help="Max number of optimizer iterations regardless of algorithm",
    )
    parser.add_argument("--pop-size", default=25, help="population of each generation")
    parser.add_argument(
        "--nth-gen",
        default=1,
        type=int,
        help="Period of generations in which to evaluate if convergence happens during optimization",
    )
    parser.add_argument(
        "--n-last",
        default=5,
        type=int,
        help="Number of generations to look back for establishing convergence during optimization",
    )
    parser.add_argument(
        "--range-overshoot-tol",
        default=None,
        type=float,
        help="Range overshoot tolerance, example '0.20' allows 20%% range overshoot. Default of 'None' does not constrain overshoot.",
    )
    parser.add_argument(
        "---missed-trace-correction",
        action="store_true",
        help="Activate FASTSim time-dilation to correct missed trace",
    )
    parser.add_argument(
        "--max-time-dilation",
        default=10,
        type=int,
        help="Maximum time dilation factor to 'catch up' with trace  ",
    )
    parser.add_argument(
        "--min-time-dilation",
        default=0.1,
        type=float,
        help="Minimum time dilation to let trace 'catch up' ",
    )
    parser.add_argument(
        "--time-dilation-tol",
        default=1e-3,
        type=float,
        help="Convergence criteria for time dilation",
    )
    parser.add_argument(
        "--write-tsv",
        default=False,
        type=bool,
        help="Boolean toggle to save intermediary .TSV cost results files",
    )
    parser.add_argument(
        "--run-multi",
        action="store_true",
        help="Boolean switch to select multiprocessing version",
    )
    parser.add_argument(
        "--n-processors",
        type=int,
        help="Number of processors to use for multiprocessing",
        default=9,
    )
    parser.add_argument(
        "--fuel-prices-json",
        default=None,
        type=str,
        help="Fuel price override JSON string or path. Payload supports only 'zipcode' and 'fuel_prices'.",
    )
    parser.add_argument(
        "--fuel-prices-zipcode",
        default=None,
        type=str,
        help="US zipcode used to resolve the source fuel price region when applying overrides.",
    )
    parser.add_argument(
        "--eia-api-key",
        default=None,
        type=str,
        help="EIA API key (prefer setting T3CO_EIA_API_KEY in .env file instead).",
    )
    parser.add_argument(
        "--eia-aeo-year",
        default=None,
        type=str,
        help="AEO publication year to query (e.g. '2023', '2025'). Default: auto-discover latest.",
    )
    parser.add_argument(
        "--eia-aeo-case",
        default=None,
        type=str,
        help="AEO scenario case ID (e.g. 'aeo2023ref'). Default: auto-discover reference case.",
    )
    parser.add_argument(
        "--plot",
        nargs="?",
        const=DEFAULT_PLOT_BACKEND,
        default=None,
        choices=["plotly", "matplotlib", "seaborn"],
        help="Generate TCO charts from the results after the run, saved next to the results CSV. "
        "Use '--plot' for interactive Plotly HTML (default) or '--plot matplotlib' for static PNGs. "
        "Requires the 'viz' extra: pip install 't3co[viz]'.",
    )

    args = parser.parse_args()

    if args.config is None or args.config == "None":
        config = Config()
        config.selections = _normalize_selections_arg(args.selections)
        config.drive_cycle = _normalize_drive_cycle_arg(args.drive_cycle)
        config.vehicle_file = Path(args.vehicles)
        config.scenario_file = Path(args.scenarios)
        config.eng_eff_imp_curves = Path(args.eng_curves)
        config.lw_imp_curves = Path(args.lw_curves)
        config.aero_drag_imp_curves = Path(args.aero_curves)
    else:
        config = Config()
        config.from_csv(filename=args.config, analysis_id=args.analysis_id)

    apply_cli_overrides(config=config, args=args, argv=raw_argv)
    config.fuel_prices_json = args.fuel_prices_json
    config.fuel_prices_zipcode = args.fuel_prices_zipcode
    if args.eia_api_key is not None:
        os.environ["T3CO_EIA_API_KEY"] = args.eia_api_key
    if args.eia_aeo_year is not None:
        config.eia_aeo_year = args.eia_aeo_year
    if args.eia_aeo_case is not None:
        config.eia_aeo_case = args.eia_aeo_case

    config.check_drivecycles_and_create_selections()
    config.read_auxiliary_files()

    if args.config is not None and args.config != "None":
        gl.RESOURCES_FOLDERPATH = Path(args.config).parent
        config.vehicle_file = get_path_object(config.vehicle_file)
        config.scenario_file = get_path_object(config.scenario_file)
        config.eng_eff_imp_curves = get_path_object(config.eng_eff_imp_curves)
        config.lw_imp_curves = get_path_object(config.lw_imp_curves)
        config.aero_drag_imp_curves = get_path_object(config.aero_drag_imp_curves)

    print(f"Selection List: {config.selections_list}")

    if args.run_multi:
        print("Running multiprocessing version of T3CO")
        result_filepath = create_results_filepath(config=config)
        buffer = []
        buffer_size = 50  # Write to disk every 50 results to balance I/O and memory
        total_written = 0

        with Pool(processes=args.n_processors) as pool:
            for k, report_i in enumerate(
                pool.imap_unordered(
                    partial(generate_ledger, config=config),
                    config.selections_list,
                ),
                start=1,
            ):
                buffer.append(report_i)

                # Write buffer to disk when it reaches buffer_size
                if len(buffer) >= buffer_size:
                    append_results_to_csv(
                        reports_list=buffer,
                        output_path=result_filepath,
                        write_header=(total_written == 0),
                    )
                    total_written += len(buffer)
                    buffer = []  # Clear buffer to free memory
                    print(
                        f"\nSaved {total_written} results to {str(result_filepath)}\n"
                    )

                print(f"Number of files done: {k}/{len(config.selections_list)}")

            # Write any remaining results in buffer
            if buffer:
                append_results_to_csv(
                    reports_list=buffer,
                    output_path=result_filepath,
                    write_header=(total_written == 0),
                )
                total_written += len(buffer)
                print(f"\nSaved final batch. Total: {total_written} results\n")

            pool.close()
            pool.join()

            # Sort the final file
            print("Sorting results by selection...")
            sort_csv_file(input_path=result_filepath, sort_by="selection")
            print(f"T3CO results saved and sorted to: {result_filepath}")

        if args.plot:
            save_default_plots(result_filepath, backend=args.plot)

    else:
        run_t3co(config=config, save_results=True, plot_backend=args.plot)

    print(f"T3CO Run time: {time.time() - start}")
