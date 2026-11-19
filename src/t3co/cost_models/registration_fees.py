"""
Annual registration fees by state, powertrain and gross vehicle weight.

The annual fee for a vehicle registered in a state is the sum of:

- the state's base registration fee for the vehicle's weight bracket,
- the state's surcharge for alternative powertrains (EV, hydrogen, CNG), and
- the federal heavy vehicle use tax (HVUT, IRS Form 2290).

State base fees and surcharges come from a fee table (``RegistrationFees.csv``),
one row per fee rule. The HVUT is computed from 26 U.S.C. 4481.
"""

import math
from functools import lru_cache
from pathlib import Path
from typing import List, Optional, Union

import pandas as pd

from t3co.constants import Global as gl
from t3co.utils.print_class_objects import get_path_object

REGISTRATION_FEES_COLUMNS = [
    "state",
    "component",
    "powertrain",
    "min_gvwr_lb",
    "max_gvwr_lb",
    "fee_dol_per_yr",
    "effective_year",
    "source_url",
    "notes",
]
BASE = "base"
SURCHARGE = "surcharge"
# Base fees apply to every powertrain.
ALL_POWERTRAINS = "ALL"
POWERTRAIN_CODES = ("CONV", "HEV", "PHEV", "BEV", "FCEV", "CNG")
# Lightest GVWR the base fee brackets must cover (Class 2b).
MIN_COVERED_GVWR_LB = 8501

# 26 U.S.C. 4481(a)
HVUT_MIN_TAXABLE_LB = 55_000
HVUT_TOP_BRACKET_LB = 75_000
HVUT_BASE_DOL = 100.0
HVUT_DOL_PER_1000_LB = 22.0
HVUT_MAX_DOL = 550.0
# 26 U.S.C. 4483(d): vehicles used 5,000 miles or less on public highways in a
# tax period are exempt.
HVUT_EXEMPT_MAX_MI_PER_YR = 5_000


def hvut_dol_per_yr(
    gross_weight_lb: float, distance_mi_per_yr: Optional[float] = None
) -> float:
    """
    Calculates the federal heavy vehicle use tax for one year.

    Args:
        gross_weight_lb (float): Taxable gross weight in pounds.
        distance_mi_per_yr (Optional[float], optional): Miles driven in the year. At or
            below the 5,000-mile limit the vehicle is exempt. Defaults to None (not exempt).

    Returns:
        float: HVUT in dollars per year.
    """
    if (
        distance_mi_per_yr is not None
        and distance_mi_per_yr <= HVUT_EXEMPT_MAX_MI_PER_YR
    ):
        return 0.0
    if gross_weight_lb < HVUT_MIN_TAXABLE_LB:
        return 0.0
    if gross_weight_lb > HVUT_TOP_BRACKET_LB:
        return HVUT_MAX_DOL
    # $22 for each 1,000 pounds, or fraction thereof, above 55,000 pounds
    return HVUT_BASE_DOL + HVUT_DOL_PER_1000_LB * math.ceil(
        (gross_weight_lb - HVUT_MIN_TAXABLE_LB) / 1000
    )


def get_powertrain_code(veh_pt_type: str, fuel_type: str) -> str:
    """
    Maps a vehicle's powertrain type and fuel to a fee table powertrain code.

    T3CO models fuel cell trucks as HEVs that run on hydrogen, so the fuel is
    checked before the powertrain type.

    Args:
        veh_pt_type (str): Vehicle powertrain type (Conv, HEV, PHEV, BEV).
        fuel_type (str): Scenario fuel type (diesel, gasoline, electricity, hydrogen, cng).

    Returns:
        str: One of POWERTRAIN_CODES.
    """
    fuel_type = (fuel_type or "").lower()
    if fuel_type == "hydrogen":
        return "FCEV"
    if fuel_type == "cng":
        return "CNG"
    if veh_pt_type == gl.BEV:
        return "BEV"
    if veh_pt_type == gl.PHEV:
        return "PHEV"
    if veh_pt_type == gl.HEV:
        return "HEV"
    return "CONV"


def validate_registration_fees(registration_fees_df: pd.DataFrame) -> None:
    """
    Checks a registration fee table and raises one error listing every problem found.

    Checks that every row has a known component and powertrain, a non-negative fee,
    a source URL and an effective year; that each state's base fee brackets run from
    8,501 lb up to an open-ended top bracket with no gaps or overlaps; and that
    surcharge brackets for the same state and powertrain do not overlap.

    Args:
        registration_fees_df (pd.DataFrame): Fee table with REGISTRATION_FEES_COLUMNS.

    Raises:
        ValueError: If the table has any problems.
    """
    missing_columns = set(REGISTRATION_FEES_COLUMNS).difference(
        registration_fees_df.columns
    )
    if missing_columns:
        raise ValueError(
            f"Registration fee table is missing columns: {sorted(missing_columns)}"
        )

    errors: List[str] = []
    for index, row in registration_fees_df.iterrows():
        label = f"row {index + 2} ({row['state']} {row['component']} {row['powertrain']})"
        if row["component"] not in (BASE, SURCHARGE):
            errors.append(f"{label}: component must be '{BASE}' or '{SURCHARGE}'")
        elif row["component"] == BASE and row["powertrain"] != ALL_POWERTRAINS:
            errors.append(f"{label}: base fees must use powertrain '{ALL_POWERTRAINS}'")
        elif row["component"] == SURCHARGE and row["powertrain"] not in POWERTRAIN_CODES:
            errors.append(f"{label}: powertrain must be one of {POWERTRAIN_CODES}")
        if pd.isna(row["fee_dol_per_yr"]) or row["fee_dol_per_yr"] < 0:
            errors.append(f"{label}: fee_dol_per_yr must be a non-negative number")
        if pd.isna(row["min_gvwr_lb"]):
            errors.append(f"{label}: min_gvwr_lb is required")
        elif not pd.isna(row["max_gvwr_lb"]) and row["max_gvwr_lb"] < row["min_gvwr_lb"]:
            errors.append(f"{label}: max_gvwr_lb is below min_gvwr_lb")
        if pd.isna(row["effective_year"]):
            errors.append(f"{label}: effective_year is required")
        if pd.isna(row["source_url"]) or not str(row["source_url"]).strip():
            errors.append(f"{label}: source_url is required")

    for state, state_df in registration_fees_df.groupby("state"):
        base_df = state_df[state_df["component"] == BASE].sort_values("min_gvwr_lb")
        if base_df.empty:
            errors.append(f"{state}: no base fee rows")
        else:
            if base_df["min_gvwr_lb"].iloc[0] > MIN_COVERED_GVWR_LB:
                errors.append(
                    f"{state}: base fees start at {base_df['min_gvwr_lb'].iloc[0]:g} lb, "
                    f"above {MIN_COVERED_GVWR_LB} lb"
                )
            if not pd.isna(base_df["max_gvwr_lb"].iloc[-1]):
                errors.append(f"{state}: top base fee bracket must have no max_gvwr_lb")
            errors.extend(
                f"{state}: base fee brackets {problem}"
                for problem in _bracket_problems(base_df, contiguous=True)
            )
        surcharge_df = state_df[state_df["component"] == SURCHARGE]
        for powertrain, powertrain_df in surcharge_df.groupby("powertrain"):
            errors.extend(
                f"{state}: {powertrain} surcharge brackets {problem}"
                for problem in _bracket_problems(
                    powertrain_df.sort_values("min_gvwr_lb"), contiguous=False
                )
            )

    if errors:
        raise ValueError(
            "Registration fee table has problems:\n- " + "\n- ".join(errors)
        )


def _bracket_problems(brackets_df: pd.DataFrame, contiguous: bool) -> List[str]:
    """
    Finds overlaps, and gaps when contiguous is True, between weight brackets
    sorted by min_gvwr_lb. Brackets are whole pounds with inclusive ends, so the
    next bracket should start 1 lb above the previous maximum.
    """
    problems = []
    previous_max = None
    for _, row in brackets_df.iterrows():
        if previous_max is not None:
            if pd.isna(previous_max) or row["min_gvwr_lb"] <= previous_max:
                problems.append(f"overlap at {row['min_gvwr_lb']:g} lb")
            elif contiguous and row["min_gvwr_lb"] != previous_max + 1:
                problems.append(
                    f"leave a gap between {previous_max:g} and {row['min_gvwr_lb']:g} lb"
                )
        previous_max = row["max_gvwr_lb"]
    return problems


@lru_cache(maxsize=None)
def _read_registration_fees(filepath: str) -> pd.DataFrame:
    registration_fees_df = pd.read_csv(filepath, dtype={"state": str})
    registration_fees_df["state"] = registration_fees_df["state"].str.strip().str.upper()
    validate_registration_fees(registration_fees_df)
    return registration_fees_df


def load_registration_fees(registration_fees_file: Union[str, Path]) -> pd.DataFrame:
    """
    Reads and validates a registration fee table. Tables are cached per file.

    Args:
        registration_fees_file (Union[str, Path]): Path to the fee table, either absolute
            or relative to the resources folder.

    Returns:
        pd.DataFrame: The fee table. Treat it as read-only, since it is shared through the cache.
    """
    return _read_registration_fees(str(get_path_object(registration_fees_file)))


def get_state_registration_fee_dol_per_yr(
    state: str,
    powertrain: str,
    gross_weight_lb: float,
    registration_fees_df: pd.DataFrame,
) -> float:
    """
    Looks up a state's annual base registration fee plus its powertrain surcharge.

    Args:
        state (str): Two-letter state code, e.g. 'CO'.
        powertrain (str): Fee table powertrain code (see get_powertrain_code).
        gross_weight_lb (float): Registered gross vehicle weight in pounds.
        registration_fees_df (pd.DataFrame): Fee table from load_registration_fees.

    Returns:
        float: Base fee plus surcharge, in dollars per year. The federal HVUT is not included.

    Raises:
        ValueError: If the state is not in the table, or no base fee bracket covers the weight.
    """
    state = str(state).strip().upper()
    # Brackets are whole pounds; rounding keeps kg-to-lb conversion noise from
    # landing a weight between two brackets.
    weight_lb = round(gross_weight_lb)
    state_df = registration_fees_df[registration_fees_df["state"] == state]
    if state_df.empty:
        available_states = ", ".join(sorted(registration_fees_df["state"].unique()))
        raise ValueError(
            f"No registration fees for state '{state}'. "
            f"States in the fee table: {available_states or 'none'}"
        )
    in_bracket = (state_df["min_gvwr_lb"] <= weight_lb) & (
        state_df["max_gvwr_lb"].isna() | (weight_lb <= state_df["max_gvwr_lb"])
    )

    base_df = state_df[in_bracket & (state_df["component"] == BASE)]
    if base_df.empty:
        raise ValueError(
            f"No {state} base registration fee covers {weight_lb} lb "
            f"(the fee table covers {MIN_COVERED_GVWR_LB} lb and up)"
        )
    surcharge_df = state_df[
        in_bracket
        & (state_df["component"] == SURCHARGE)
        & (state_df["powertrain"] == powertrain)
    ]
    return float(base_df["fee_dol_per_yr"].iloc[0] + surcharge_df["fee_dol_per_yr"].sum())
