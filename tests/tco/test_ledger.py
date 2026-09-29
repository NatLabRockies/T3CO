import json

import pandas as pd
import pytest

from t3co.energy_models.energy import Energy
from t3co.input_data.config import Config
from t3co.input_data.scenario import Scenario
from t3co.input_data.toggles import Toggles
from t3co.input_data.vehicle import Vehicle
from t3co.tco.ledger import Ledger
from t3co.tco.tcocalc import TCOCalc


@pytest.fixture
def vehicle():
    vehicle = Vehicle(
        selection=1,
        veh_pt_type="BEV",
        fc_max_kw=100.0,
        fs_kwh=50.0,
        mc_max_kw=200.0,
        ess_max_kwh=75.0,
        chg_eff=0.9,
        veh_override_kg=70000.0,
    )
    vehicle.set_veh_kg()
    return vehicle


@pytest.fixture
def toggles():
    return Toggles(
        msrp=True,
        purchase_tax=True,
        purchasing_downpayment=True,
        mark_up=True,
        residual_cost=True,
        fuel_cost=True,
        maintenance_oper_cost=True,
        insurance_cost=True,
        purchasing_cost=True,
        fueling_dwell_labor=True,
        payload_oppy_cost=True,
        fueling_dwell_oppy_cost=True,
        mr_downtime_oppy_cost=True,
        run_fastsim=False,
    )


@pytest.fixture
def scenario(toggles):
    scenario = Scenario(
        selection=1,
        # drive_cycle="path/to/drive_cycle.csv",
        vehicle_glider_cost_dol=10000.0,
        fc_fuelcell_cost_dol_per_kw=200.0,
        fc_ice_cost_dol_per_kw=150.0,
        fc_cng_ice_cost_dol_per_kw=180.0,
        fc_ice_base_cost_dol=5000.0,
        fs_h2_cost_dol_per_kwh=10.0,
        fs_cng_cost_dol_per_kwh=8.0,
        fs_cost_dol_per_kwh=6.0,
        pe_mc_base_cost_dol=3000.0,
        pe_mc_cost_dol_per_kw=50.0,
        plug_base_cost_dol=1000.0,
        ess_base_cost_dol=5000.0,
        ess_cost_dol_per_kwh=200.0,
        markup_pct=1.1,
        tax_rate_pct=0.08,
        constant_trip_distance_mi=100.0,
        vmt=[10000] * 10,
        model_year=2020,
        region="US",
        fuel_type="electricity",
        activate_tco_payload_cap_cost_multiplier=True,
        plf_ref_veh_empty_mass_kg=8000.0,
        activate_tco_fueling_dwell_time_cost=True,
        activate_mr_downtime_cost=True,
        fdt_dwpt_fraction_power_pct=0.1,
        fdt_frac_full_charge_bounds="[0.2, 0.8]",
        fdt_avg_overhead_hr_per_dwell_hr=0.5,
        downtime_oppy_cost_dol_per_hr=50.0,
        shifts_per_year=[250] * 10,
        fdt_num_free_dwell_trips=0,
        fdt_available_freetime_hr=0,
        mr_planned_downtime_hr_per_yr=10.0,
        mr_unplanned_downtime_hr_per_mi=[0.01] * 10,
        mr_avg_tire_life_mi=50000.0,
        mr_tire_replace_downtime_hr_per_event=2.0,
        vehicle_life_yr=10,
        ess_max_charging_power_kw=100.0,
        discount_rate_pct_per_yr=0.05,
        avg_speed_mph=50.0,
        vehicle_class="class8",
        depreciation_rates_pct_per_yr=[0.09] * 10,
        insurance_rates_pct_per_yr=[0.01] * 10,
        maint_oper_cost_dol_per_mi=[0.05] * 10,
        fuel_prices_df=pd.DataFrame(
            {
                "Fuel": ["electricity_dol_per_kwh"],
                "Region": ["US"],
                "2020": [0.1],
                "2021": [0.1],
                "2022": [0.1],
                "2023": [0.1],
                "2024": [0.1],
                "2025": [0.1],
                "2026": [0.1],
                "2027": [0.1],
                "2028": [0.1],
                "2029": [0.1],
            }
        ),
        cost_toggles=toggles,
    )
    scenario.fuel_prices_df.set_index("Fuel", inplace=True)
    return scenario


@pytest.fixture
def energy():
    return Energy(mpgge=3.0, primary_fuel_range_mi=300.0)


@pytest.fixture
def config():
    config = Config(selections=[1], vehicle_life_yr=10, TCO_method="DIRECT")
    config.check_drivecycles_and_create_selections()
    return config


@pytest.fixture
def ledger(vehicle, scenario, energy, config):
    ledger = Ledger.__new__(
        Ledger, vehicle=vehicle, scenario=scenario, energy=energy, config=config
    )
    ledger = run_tco_per_year(ledger, scenario, vehicle, energy, config)
    return ledger


def test_ledger_initialization(vehicle, scenario, energy, config):
    ledger = Ledger(vehicle=vehicle, scenario=scenario, energy=energy, config=config)
    assert ledger.vehicle == vehicle
    assert ledger.scenario == scenario
    assert ledger.energy == energy
    assert ledger.config == config
    assert ledger.vehicle_life_yr == 10
    assert ledger.tco_method == "DIRECT"
    assert len(ledger.tco_per_year) == 10


def test_set_discounted_costs(vehicle, scenario, energy, config, ledger):
    ledger.set_discounted_costs()
    assert ledger.discounted_total_cap_cost_dol == pytest.approx(
        ledger.tco_per_year[0].cap_costs_dol.net_capital_cost_dol, 0.01
    )
    assert ledger.total_vmt == pytest.approx(sum(scenario.vmt), 0.01)
    assert ledger.disc_total_vmt == pytest.approx(
        sum(
            [
                scenario.get_discounted_value(vmt, year_number=i + 1)
                for i, vmt in enumerate(scenario.vmt)
            ]
        ),
        0.01,
    )


def test_set_discounted_tco(vehicle, scenario, energy, config, ledger):
    ledger.set_discounted_costs()
    ledger.set_discounted_tco()
    assert ledger.discounted_tco_dol == pytest.approx(
        ledger.payload_cap_cost_multiplier
        * (
            ledger.discounted_total_cap_cost_dol
            + ledger.discounted_total_oper_cost_dol
            + ledger.discounted_downtime_oppy_cost_dol
            + ledger.residual_cost_dol
        ),
        0.01,
    )


@pytest.mark.parametrize("method", ["cash", "loan", "lease"])
def test_purchasing_payments_reconcile_operating_cost(
    vehicle, scenario, energy, config, method
):
    scenario.purchasing_method = method
    scenario.purchasing_down_payment_pct = 0.15
    scenario.purchasing_interest_apr_pct_per_yr = 0.1
    scenario.purchasing_payment_frequency_months = 1
    scenario.purchasing_term_yr = 4
    scenario.leasing_money_factor = 0.002
    ledger = Ledger(vehicle=vehicle, scenario=scenario, energy=energy, config=config)

    if method == "cash":
        assert ledger.total_purchasing_payment_dol == 0
    else:
        assert ledger.total_purchasing_payment_dol > 0
    # With the full payments included, the exported discounted operating
    # components add up to the operating total counted in TCO.
    assert ledger.discounted_total_oper_cost_dol == pytest.approx(
        ledger.total_fuel_cost_dol
        + ledger.total_maintenance_cost_dol
        + ledger.insurance_cost_dol
        + ledger.fueling_dwell_labor_cost_dol
        + ledger.total_purchasing_payment_dol
    )


def test_set_cost_components(vehicle, scenario, energy, config, ledger):
    # ledger = Ledger.__new__(vehicle=vehicle, scenario=scenario, energy=energy, config=config)
    ledger.set_cost_components()
    assert ledger.glider_cost_dol == pytest.approx(
        ledger.tco_per_year[0].cap_costs_dol.glider_cost_dol, 0.01
    )
    assert ledger.fuel_converter_cost_dol == pytest.approx(
        ledger.tco_per_year[0].cap_costs_dol.fuel_converter_cost_dol, 0.01
    )
    assert ledger.fuel_storage_cost_dol == pytest.approx(
        ledger.tco_per_year[0].cap_costs_dol.fuel_storage_cost_dol, 0.01
    )
    assert ledger.motor_control_power_elecs_cost_dol == pytest.approx(
        ledger.tco_per_year[0].cap_costs_dol.motor_control_power_elecs_cost_dol, 0.01
    )
    assert ledger.plug_cost_dol == pytest.approx(
        ledger.tco_per_year[0].cap_costs_dol.plug_cost_dol, 0.01
    )
    assert ledger.battery_cost_dol == pytest.approx(
        ledger.tco_per_year[0].cap_costs_dol.battery_cost_dol, 0.01
    )
    assert ledger.purchase_tax_dol == pytest.approx(
        ledger.tco_per_year[0].cap_costs_dol.purchase_tax_dol, 0.01
    )
    assert ledger.msrp_total_dol == pytest.approx(
        ledger.tco_per_year[0].cap_costs_dol.msrp_total_dol, 0.01
    )


def test_to_dict(vehicle, scenario, energy, config, ledger):
    # ledger = Ledger(vehicle=vehicle, scenario=scenario, energy=energy, config=config)
    ledger_dict = ledger.to_dict()
    assert isinstance(ledger_dict, dict)
    assert ledger_dict["vehicle_veh_pt_type"] == vehicle.veh_pt_type


def test_to_json(vehicle, scenario, energy, config, tmp_path, ledger):
    # ledger = Ledger(vehicle=vehicle, scenario=scenario, energy=energy, config=config)
    json_path = tmp_path / "ledger.json"
    ledger.to_json(filepath=json_path)
    assert json_path.exists()
    with open(json_path, "r") as f:
        data = json.load(f)
    assert data["vehicle_veh_pt_type"] == vehicle.veh_pt_type


def test_to_df(vehicle, scenario, energy, config, ledger):
    # ledger = Ledger(vehicle=vehicle, scenario=scenario, energy=energy, config=config)
    df = ledger.to_df()
    assert isinstance(df, pd.DataFrame)
    assert df.iloc[0]["vehicle_veh_pt_type"] == vehicle.veh_pt_type


def test_to_csv(vehicle, scenario, energy, config, tmp_path, ledger):
    # ledger = Ledger(vehicle=vehicle, scenario=scenario, energy=energy, config=config)
    csv_path = tmp_path / "ledger.csv"
    ledger.to_csv(filepath=csv_path)
    assert csv_path.exists()
    df = pd.read_csv(csv_path)
    assert df.iloc[0]["vehicle_veh_pt_type"] == vehicle.veh_pt_type


def run_tco_per_year(ledger, scenario, vehicle, energy, config):
    ledger.scenario = scenario
    ledger.vehicle = vehicle
    ledger.selection = scenario.selection
    ledger.scenario_name = scenario.scenario_name

    ledger.tco_per_year = []
    if config:
        ledger.config = config
        ledger.vehicle_life_yr = config.vehicle_life_yr
        ledger.tco_method = config.TCO_method
    else:
        ledger.vehicle_life_yr = scenario.vehicle_life_yr
        ledger.tco_method = "DIRECT"

    if energy:
        ledger.energy = energy

    for year_index in range(ledger.vehicle_life_yr):
        ledger.tco_per_year.append(
            TCOCalc(
                year_index=year_index,
                vehicle=ledger.vehicle,
                scenario=ledger.scenario,
                energy=ledger.energy,
                cap_costs=(
                    ledger.tco_per_year[year_index - 1].cap_costs_dol
                    if year_index
                    else None
                ),
                payload_cap_cost_multiplier=(
                    ledger.tco_per_year[
                        year_index - 1
                    ].oppy_costs_dol.payload_cap_cost_multiplier
                    if year_index
                    else None
                ),
            )
        )
    return ledger


def test_ledger_to_dict_include_calcs(vehicle, scenario, energy):
    config = Config(include_calcs=False, vehicle_life_yr=10)
    ledger = Ledger(vehicle, scenario, energy, config)

    # Test with include_calcs=False
    result_false = ledger.to_dict(include_calcs=False)
    assert "tco_per_year" not in result_false

    # Test with include_calcs=True
    result_true = ledger.to_dict(include_calcs=True)
    assert "tco_per_year" in result_true
