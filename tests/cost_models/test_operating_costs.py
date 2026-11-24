import os

import pandas as pd
import pytest

from t3co.cost_models.capital_costs import CapitalCosts
from t3co.cost_models.operating_costs import OperatingCosts
from t3co.cost_models.opportunity_costs import OpportunityCosts
from t3co.energy_models.energy import Energy
from t3co.input_data.scenario import Scenario
from t3co.input_data.toggles import Toggles
from t3co.input_data.vehicle import Vehicle

os.environ["JUPYTER_PLATFORM_DIRS"] = "1"


@pytest.fixture
def vehicle():
    vehicle = Vehicle(
        veh_pt_type="BEV",
        fc_max_kw=100.0,
        fs_kwh=50.0,
        mc_max_kw=200.0,
        ess_max_kwh=75.0,
        chg_eff=0.9,
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
        payload_oppy_cost=False,
        fueling_dwell_oppy_cost=False,
        mr_downtime_oppy_cost=False,
        run_fastsim=True,
    )


@pytest.fixture
def scenario(toggles):
    return Scenario(
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
        labor_rate_dol_per_hr=50.0,
        markup_pct=1.1,
        tax_rate_pct=0.08,
        vehicle_class="class8",
        vehicle_life_yr=10,
        discount_rate_pct_per_yr=0.05,
        fuel_prices_file="fuel_prices.csv",
        insurance_rates_pct_per_yr="[0.05, 0.05, 0.05, 0.05, 0.05, 0.05, 0.05, 0.05, 0.05, 0.05]",
        maint_oper_cost_dol_per_mi=[0.1] * 10,
        vmt=[10000] * 10,
        fuel_type="electricity",
        constant_trip_distance_mi=50,
        shifts_per_year=[0, 0, 0, 0, 0, 0, 0, 0, 0, 0],
        fdt_frac_full_charge_bounds=[0.1, 0.9],
        fdt_available_freetime_hr=0,
        fdt_avg_overhead_hr_per_dwell_hr=0.4,
        fdt_dwpt_fraction_power_pct=0.0,
        fdt_num_free_dwell_trips=1,
        ess_max_charging_power_kw=100.0,
        depreciation_rates_pct_per_yr=[0.09] * 10,
        model_year=2020,
        region="US",
        activate_tco_payload_cap_cost_multiplier=False,
        activate_mr_downtime_cost=False,
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


@pytest.fixture
def energy():
    return Energy(mpgge=3.0, primary_fuel_range_mi=100.0)


@pytest.fixture
def cap_costs(vehicle, scenario):
    cap_costs = CapitalCosts.__new__(CapitalCosts, vehicle=vehicle, scenario=scenario)
    cap_costs.purchasing_initial_principal_dol = 50000.0
    cap_costs.msrp_total_dol = 60000.0
    cap_costs.purchase_tax_dol = 4800.0
    cap_costs.purchasing_downpayment_dol = 12000.0
    cap_costs.residual_cost_dol = 10000.0
    return cap_costs


@pytest.fixture
def oppy_costs(vehicle, scenario, energy):
    oppy_cost = OpportunityCosts(
        year_number=1, vehicle=vehicle, scenario=scenario, energy=energy
    )
    oppy_cost.fueling_dwell_time_hr_per_yr = 100.0
    return oppy_cost


def test_operating_costs_initialization(
    vehicle, scenario, energy, cap_costs, oppy_costs
):
    scenario.fuel_prices_df.set_index("Fuel", inplace=True)

    print(f"scenario.cost_toggles: {scenario.cost_toggles}")
    operating_costs = OperatingCosts(
        year_number=1,
        cap_costs=cap_costs,
        vehicle=vehicle,
        scenario=scenario,
        energy=energy,
        oppy_costs=oppy_costs,
    )
    assert operating_costs.fuel_cost_dol_per_yr == pytest.approx(11233.33, 0.01)
    assert operating_costs.maintenance_cost_dol_per_yr == pytest.approx(1000.0, 0.01)
    assert operating_costs.insurance_cost_dol_per_yr == pytest.approx(3000.0, 0.01)
    assert operating_costs.fueling_dwell_labor_cost_dol_per_yr == pytest.approx(
        5000.0, 0.01
    )
    assert operating_costs.net_oper_cost_dol_per_yr == pytest.approx(20233.33, 0.01)
    assert operating_costs.disc_oper_cost_dol_per_yr == pytest.approx(19269.84, 0.01)


def test_set_fuel_cost(vehicle, scenario, energy):
    scenario.fuel_prices_df.set_index("Fuel", inplace=True)

    operating_costs = OperatingCosts.__new__(
        OperatingCosts,
        year_number=1,
        cap_costs=None,
        vehicle=vehicle,
        scenario=scenario,
        energy=energy,
        oppy_costs=None,
    )
    operating_costs.mpgge = energy.mpgge
    operating_costs.distance_traveled_mi_per_yr = scenario.vmt[1 - 1]

    operating_costs.set_fuel_cost(year_number=1, vehicle=vehicle, scenario=scenario)
    assert operating_costs.fuel_cost_dol_per_yr == pytest.approx(11233.33, 0.01)


def test_set_maintenance_oper_cost(vehicle, scenario):
    operating_costs = OperatingCosts.__new__(
        OperatingCosts,
        year_number=1,
        cap_costs=None,
        vehicle=vehicle,
        scenario=scenario,
        energy=None,
        oppy_costs=None,
    )
    operating_costs.distance_traveled_mi_per_yr = scenario.vmt[1 - 1]
    operating_costs.set_maintenance_oper_cost(
        year_number=1, vehicle=vehicle, scenario=scenario
    )
    assert operating_costs.maintenance_cost_dol_per_yr == pytest.approx(1000.0, 0.01)


def test_set_insurance_cost(vehicle, scenario, cap_costs):
    operating_costs = OperatingCosts.__new__(
        OperatingCosts,
        year_number=1,
        cap_costs=cap_costs,
        vehicle=vehicle,
        scenario=scenario,
        energy=None,
        oppy_costs=None,
    )
    operating_costs.set_insurance_cost(
        year_number=1, cap_cost=cap_costs, vehicle=vehicle, scenario=scenario
    )
    assert operating_costs.insurance_cost_dol_per_yr == pytest.approx(3000.0, 0.01)


def test_set_fueling_dwell_labor_cost(scenario, oppy_costs):
    operating_costs = OperatingCosts.__new__(
        OperatingCosts,
        year_number=1,
        cap_costs=None,
        vehicle=None,
        scenario=scenario,
        energy=None,
        oppy_costs=oppy_costs,
    )
    operating_costs.set_fueling_dwell_labor_cost(
        scenario=scenario, oppy_costs=oppy_costs
    )
    assert operating_costs.fueling_dwell_labor_cost_dol_per_yr == pytest.approx(
        5000.0, 0.01
    )


def test_set_purchasing_payment_cost_cash(scenario, cap_costs):
    scenario.purchasing_method = "cash"
    operating_costs = OperatingCosts.__new__(
        OperatingCosts,
        year_number=1,
        cap_costs=cap_costs,
        vehicle=None,
        scenario=scenario,
        energy=None,
        oppy_costs=None,
    )
    operating_costs.set_purchasing_payment_cost(
        year_number=1, scenario=scenario, cap_costs=cap_costs
    )
    assert operating_costs.purchasing_payment_dol_per_yr == pytest.approx(0.0, 0.01)
    assert operating_costs.purchasing_cost_dol_per_yr == pytest.approx(0.0, 0.01)


def test_set_purchasing_payment_cost_loan(scenario, cap_costs):
    scenario.purchasing_method = "loan"
    scenario.purchasing_interest_apr_pct_per_yr = 0.05
    scenario.purchasing_payment_frequency_months = 12
    scenario.purchasing_term_yr = 5
    operating_costs = OperatingCosts.__new__(
        OperatingCosts,
        year_number=1,
        cap_costs=cap_costs,
        vehicle=None,
        scenario=scenario,
        energy=None,
        oppy_costs=None,
    )
    operating_costs.set_purchasing_payment_cost(
        year_number=1, scenario=scenario, cap_costs=cap_costs
    )
    assert operating_costs.purchasing_payment_dol_per_yr == pytest.approx(
        11548.73, 0.01
    )
    assert operating_costs.purchasing_cost_dol_per_yr == pytest.approx(4547.56, 0.01)


def test_set_purchasing_payment_cost_loan_with_missing_terms(scenario, cap_costs):
    scenario.purchasing_method = "loan"
    scenario.purchasing_interest_apr_pct_per_yr = 0.05
    scenario.purchasing_payment_frequency_months = 0
    scenario.purchasing_term_yr = 0
    operating_costs = OperatingCosts.__new__(
        OperatingCosts,
        year_number=1,
        cap_costs=cap_costs,
        vehicle=None,
        scenario=scenario,
        energy=None,
        oppy_costs=None,
    )

    operating_costs.set_purchasing_payment_cost(
        year_number=1, scenario=scenario, cap_costs=cap_costs
    )

    assert operating_costs.purchasing_payment_dol_per_yr == pytest.approx(0.0, 0.01)
    assert operating_costs.purchasing_cost_dol_per_yr == pytest.approx(0.0, 0.01)


def test_set_purchasing_payment_cost_lease(scenario, cap_costs):
    scenario.purchasing_method = "lease"
    scenario.purchasing_term_yr = 3
    scenario.leasing_money_factor = 0.002
    cap_costs.msrp_total_dol = 47400.0
    cap_costs.purchase_tax_dol = 3792.0
    operating_costs = OperatingCosts.__new__(
        OperatingCosts,
        year_number=1,
        cap_costs=cap_costs,
        vehicle=None,
        scenario=scenario,
        energy=None,
        oppy_costs=None,
    )
    operating_costs.set_purchasing_payment_cost(
        year_number=1, scenario=scenario, cap_costs=cap_costs
    )
    assert operating_costs.purchasing_tax_amount_dol_per_year == pytest.approx(
        1367.83, 0.01
    )
    assert operating_costs.purchasing_payment_dol_per_yr == pytest.approx(
        18465.77, 0.01
    )
    assert operating_costs.purchasing_cost_dol_per_yr == pytest.approx(700.60, 0.01)


def test_set_purchasing_payment_cost_lease_with_missing_term(scenario, cap_costs):
    scenario.purchasing_method = "lease"
    scenario.purchasing_term_yr = 0
    scenario.leasing_money_factor = 0.002
    operating_costs = OperatingCosts.__new__(
        OperatingCosts,
        year_number=1,
        cap_costs=cap_costs,
        vehicle=None,
        scenario=scenario,
        energy=None,
        oppy_costs=None,
    )

    operating_costs.set_purchasing_payment_cost(
        year_number=1, scenario=scenario, cap_costs=cap_costs
    )

    assert operating_costs.purchasing_payment_dol_per_yr == pytest.approx(0.0, 0.01)
    assert operating_costs.purchasing_cost_dol_per_yr == pytest.approx(0.0, 0.01)
    assert operating_costs.purchasing_tax_amount_dol_per_year == pytest.approx(
        0.0, 0.01
    )


def test_set_net_oper_cost(vehicle, scenario, energy, cap_costs, oppy_costs):
    scenario.fuel_prices_df.set_index("Fuel", inplace=True)

    operating_costs = OperatingCosts.__new__(
        OperatingCosts,
        year_number=1,
        cap_costs=cap_costs,
        vehicle=vehicle,
        scenario=scenario,
        energy=energy,
        oppy_costs=oppy_costs,
    )
    operating_costs.fuel_cost_dol_per_yr = 11233.33
    operating_costs.fueling_dwell_labor_cost_dol_per_yr = 5000.0
    operating_costs.maintenance_cost_dol_per_yr = 1000.0
    operating_costs.insurance_cost_dol_per_yr = 2370.0
    operating_costs.purchasing_payment_dol_per_yr = 14400.0
    operating_costs.set_net_oper_cost()
    assert operating_costs.net_oper_cost_dol_per_yr == pytest.approx(34003.33, 0.01)


def test_set_disc_oper_cost(vehicle, scenario, energy, cap_costs, oppy_costs):
    operating_costs = OperatingCosts.__new__(
        OperatingCosts,
        year_number=1,
        cap_costs=cap_costs,
        vehicle=vehicle,
        scenario=scenario,
        energy=energy,
        oppy_costs=oppy_costs,
    )
    operating_costs.net_oper_cost_dol_per_yr = 34003.33
    operating_costs.set_disc_oper_cost(year_number=1, scenario=scenario)
    assert operating_costs.disc_oper_cost_dol_per_yr == pytest.approx(32384.12, 0.01)


def test_set_fuel_cost_zero_mpgge(vehicle, scenario):
    scenario.fuel_prices_df.set_index("Fuel", inplace=True)

    # Create an energy object with 0 mpgge
    energy = Energy(mpgge=0.0, primary_fuel_range_mi=0.0)

    operating_costs = OperatingCosts.__new__(
        OperatingCosts,
        year_number=1,
        cap_costs=None,
        vehicle=vehicle,
        scenario=scenario,
        energy=energy,
        oppy_costs=None,
    )
    operating_costs.mpgge = energy.mpgge
    operating_costs.distance_traveled_mi_per_yr = scenario.vmt[1 - 1]

    operating_costs.set_fuel_cost(year_number=1, vehicle=vehicle, scenario=scenario)
    assert operating_costs.fuel_cost_dol_per_yr == 0.0


def _registration_fees_file(tmp_path):
    fees_file = tmp_path / "RegistrationFees.csv"
    pd.DataFrame(
        {
            "state": ["ZZ", "ZZ", "ZZ"],
            "component": ["base", "base", "surcharge"],
            "powertrain": ["ALL", "ALL", "BEV"],
            "min_gvwr_lb": [8501, 26001, 8501],
            "max_gvwr_lb": [26000, None, None],
            "fee_dol_per_yr": [200.0, 1500.0, 150.0],
            "effective_year": [2025, 2025, 2025],
            "source_url": ["https://example.gov/fees"] * 3,
            "notes": [""] * 3,
        }
    ).to_csv(fees_file, index=False)
    return fees_file


def _registration_fees(vehicle, scenario, year_number=1):
    operating_costs = OperatingCosts.__new__(OperatingCosts)
    operating_costs.distance_traveled_mi_per_yr = scenario.vmt[year_number - 1]
    operating_costs.set_registration_fees(
        year_number=year_number, vehicle=vehicle, scenario=scenario
    )
    return operating_costs.registration_fees_dol_per_yr


def test_registration_fees_zero_without_inputs(vehicle, scenario):
    assert _registration_fees(vehicle, scenario) == 0.0


@pytest.mark.parametrize(
    "registration_fees, year_number, expected",
    [(750.0, 3, 750.0), ([500.0, 600.0, 700.0], 2, 600.0), ("[500.0, 600.0]", 1, 500.0)],
)
def test_registration_fees_from_scenario_value(
    vehicle, scenario, registration_fees, year_number, expected
):
    scenario.registration_fees_dol_per_yr = registration_fees
    # A given value takes priority over the state lookup.
    scenario.registration_state = "ZZ"
    assert _registration_fees(vehicle, scenario, year_number) == expected


def test_registration_fees_from_state_lookup(vehicle, scenario, tmp_path):
    scenario.registration_fees_file = _registration_fees_file(tmp_path)
    scenario.registration_state = "ZZ"
    # 36,000 kg GVWR plus a 287 kg allowance is about 80,000 lb: base fee,
    # BEV surcharge, and the top HVUT rate.
    scenario.gvwr_kg = 36_000.0
    scenario.gvwr_credit_kg = 287.0
    assert _registration_fees(vehicle, scenario) == pytest.approx(1500.0 + 150.0 + 550.0)

    # Low annual mileage exempts the vehicle from HVUT.
    scenario.vmt = [4_000] * 10
    assert _registration_fees(vehicle, scenario) == pytest.approx(1500.0 + 150.0)


def test_registration_fees_counted_in_net_oper_cost(
    vehicle, scenario, energy, cap_costs, oppy_costs
):
    scenario.fuel_prices_df.set_index("Fuel", inplace=True)
    scenario.registration_fees_dol_per_yr = [1000.0] * 10
    operating_costs = OperatingCosts(
        year_number=1,
        cap_costs=cap_costs,
        vehicle=vehicle,
        scenario=scenario,
        energy=energy,
        oppy_costs=oppy_costs,
    )
    assert operating_costs.registration_fees_dol_per_yr == 1000.0
    assert operating_costs.net_oper_cost_dol_per_yr == pytest.approx(21233.33, 0.01)

    scenario.cost_toggles.registration_fees = False
    operating_costs = OperatingCosts(
        year_number=1,
        cap_costs=cap_costs,
        vehicle=vehicle,
        scenario=scenario,
        energy=energy,
        oppy_costs=oppy_costs,
    )
    assert operating_costs.registration_fees_dol_per_yr == 0.0
    assert operating_costs.net_oper_cost_dol_per_yr == pytest.approx(20233.33, 0.01)
