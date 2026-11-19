import pandas as pd
import pytest

from t3co.constants import Global as gl
from t3co.cost_models.registration_fees import (
    REGISTRATION_FEES_COLUMNS,
    get_powertrain_code,
    get_state_registration_fee_dol_per_yr,
    hvut_dol_per_yr,
    load_registration_fees,
    validate_registration_fees,
)

SOURCE = "https://example.gov/fees"


def fee_row(state, component, powertrain, min_lb, max_lb, fee):
    return {
        "state": state,
        "component": component,
        "powertrain": powertrain,
        "min_gvwr_lb": min_lb,
        "max_gvwr_lb": max_lb,
        "fee_dol_per_yr": fee,
        "effective_year": 2025,
        "source_url": SOURCE,
        "notes": "",
    }


@pytest.fixture
def fees_df():
    # A made-up state: three base brackets, a flat BEV surcharge and a
    # weight-tiered FCEV surcharge.
    return pd.DataFrame(
        [
            fee_row("ZZ", "base", "ALL", 8501, 26000, 200.0),
            fee_row("ZZ", "base", "ALL", 26001, 80000, 1500.0),
            fee_row("ZZ", "base", "ALL", 80001, None, 2000.0),
            fee_row("ZZ", "surcharge", "BEV", 8501, None, 150.0),
            fee_row("ZZ", "surcharge", "FCEV", 8501, 26000, 100.0),
            fee_row("ZZ", "surcharge", "FCEV", 26001, None, 400.0),
        ],
        columns=REGISTRATION_FEES_COLUMNS,
    )


@pytest.mark.parametrize(
    "weight_lb, expected_dol",
    [
        (54_999, 0.0),
        (55_000, 100.0),
        (55_001, 122.0),
        (56_000, 122.0),
        (75_000, 540.0),
        (75_001, 550.0),
        (80_000, 550.0),
    ],
)
def test_hvut_brackets(weight_lb, expected_dol):
    assert hvut_dol_per_yr(weight_lb) == pytest.approx(expected_dol)


@pytest.mark.parametrize("distance_mi, expected_dol", [(5_000, 0.0), (5_001, 550.0)])
def test_hvut_low_mileage_exemption(distance_mi, expected_dol):
    assert hvut_dol_per_yr(80_000, distance_mi_per_yr=distance_mi) == expected_dol


@pytest.mark.parametrize(
    "veh_pt_type, fuel_type, expected",
    [
        (gl.CONV, "diesel", "CONV"),
        (gl.CONV, "cng", "CNG"),
        (gl.HEV, "diesel", "HEV"),
        (gl.HEV, "hydrogen", "FCEV"),
        (gl.PHEV, "gasoline", "PHEV"),
        (gl.BEV, "electricity", "BEV"),
    ],
)
def test_get_powertrain_code(veh_pt_type, fuel_type, expected):
    assert get_powertrain_code(veh_pt_type, fuel_type) == expected


@pytest.mark.parametrize(
    "powertrain, weight_lb, expected_dol",
    [
        ("CONV", 8_501, 200.0),
        ("CONV", 26_000, 200.0),
        ("CONV", 26_001, 1500.0),
        ("CONV", 80_001, 2000.0),
        ("BEV", 80_000, 1650.0),
        ("FCEV", 20_000, 300.0),
        ("FCEV", 80_000, 1900.0),
        # Conversion noise rounds to the nearest pound instead of falling
        # between two brackets.
        ("CONV", 26_000.4, 200.0),
    ],
)
def test_state_fee_lookup(fees_df, powertrain, weight_lb, expected_dol):
    assert get_state_registration_fee_dol_per_yr(
        "zz", powertrain, weight_lb, fees_df
    ) == pytest.approx(expected_dol)


def test_state_fee_lookup_missing_state(fees_df):
    with pytest.raises(ValueError, match="No registration fees for state 'CO'"):
        get_state_registration_fee_dol_per_yr("CO", "CONV", 30_000, fees_df)


def test_state_fee_lookup_below_covered_weight(fees_df):
    with pytest.raises(ValueError, match="covers 8501 lb and up"):
        get_state_registration_fee_dol_per_yr("ZZ", "CONV", 6_000, fees_df)


def test_validate_accepts_good_table(fees_df):
    validate_registration_fees(fees_df)


@pytest.mark.parametrize(
    "change, message",
    [
        (lambda df: df.drop(index=1), "leave a gap between 26000 and 80001 lb"),
        (lambda df: df.assign(min_gvwr_lb=df.min_gvwr_lb.where(df.index != 1, 25000)), "overlap at 25000 lb"),
        (lambda df: df.drop(index=0), "base fees start at 26001 lb"),
        (lambda df: df.assign(max_gvwr_lb=df.max_gvwr_lb.where(df.index != 2, 90000)), "top base fee bracket"),
        (lambda df: df.assign(source_url=df.source_url.where(df.index != 3, "")), "source_url is required"),
        (lambda df: df.assign(powertrain=df.powertrain.where(df.index != 0, "BEV")), "base fees must use powertrain 'ALL'"),
        (lambda df: df.assign(powertrain=df.powertrain.where(df.index != 3, "EV")), "powertrain must be one of"),
        (lambda df: df.assign(fee_dol_per_yr=df.fee_dol_per_yr.where(df.index != 3, -1.0)), "non-negative"),
        (lambda df: df.assign(min_gvwr_lb=df.min_gvwr_lb.where(df.index != 5, 20000)), "FCEV surcharge brackets overlap"),
    ],
)
def test_validate_reports_problems(fees_df, change, message):
    with pytest.raises(ValueError, match=message):
        validate_registration_fees(change(fees_df))


def test_load_registration_fees_reads_and_caches(fees_df, tmp_path):
    fees_file = tmp_path / "RegistrationFees.csv"
    fees_df.to_csv(fees_file, index=False)
    loaded_df = load_registration_fees(fees_file)
    assert loaded_df is load_registration_fees(fees_file)
    assert get_state_registration_fee_dol_per_yr("ZZ", "BEV", 30_000, loaded_df) == 1650.0


def test_packaged_fee_table_is_valid():
    # The packaged table is validated on load; this fails if any row is malformed.
    fees_df = load_registration_fees("./auxiliary/RegistrationFees.csv")
    assert list(fees_df.columns) == REGISTRATION_FEES_COLUMNS
