import os

import pytest

from t3co.cost_models.capital_costs import CapitalCosts
from t3co.input_data.scenario import Scenario
from t3co.input_data.toggles import Toggles
from t3co.input_data.vehicle import Vehicle

os.environ["JUPYTER_PLATFORM_DIRS"] = "1"


@pytest.fixture
def vehicle():
    return Vehicle(
        veh_pt_type="BEV",
        fc_max_kw=100.0,
        fs_kwh=50.0,
        mc_max_kw=200.0,
        ess_max_kwh=75.0,
        chg_eff=0.9,
    )


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
        markup_pct=1.1,
        tax_rate_pct=0.08,
        purchasing_method="loan",
        purchasing_down_payment_pct=0.10,
        purchasing_interest_apr_pct_per_yr=0.05,
        depreciation_rates_pct_per_yr=[0.09] * 10,
        vehicle_life_yr=10,
        discount_rate_pct_per_yr=0.05,
        cost_toggles=toggles,
    )


def test_capital_costs_initialization(vehicle, scenario):
    capital_costs = CapitalCosts(vehicle=vehicle, scenario=scenario)
    assert capital_costs.glider_cost_dol == pytest.approx(11000.0, 0.01)
    assert capital_costs.fuel_converter_cost_dol == pytest.approx(0, 0.01)
    assert capital_costs.fuel_storage_cost_dol == pytest.approx(0, 0.01)
    assert capital_costs.motor_control_power_elecs_cost_dol == pytest.approx(
        14300.0, 0.01
    )
    assert capital_costs.plug_cost_dol == pytest.approx(1100, 0.01)
    assert capital_costs.battery_cost_dol == pytest.approx(22000.0, 0.01)
    assert capital_costs.msrp_total_dol == pytest.approx(48400, 0.01)
    assert capital_costs.purchase_tax_dol == pytest.approx(3872.0, 0.01)
    assert capital_costs.residual_cost_dol == pytest.approx(-18847.74, 0.01)
    assert capital_costs.purchasing_downpayment_dol == pytest.approx(5227.20, 0.01)
    assert capital_costs.net_capital_cost_dol == pytest.approx(5227.20, 0.01)
    assert capital_costs.disc_residual_cost_dol == pytest.approx(-11570.87, 0.01)


def test_set_glider_cost(vehicle, scenario):
    capital_costs = CapitalCosts.__new__(
        CapitalCosts, vehicle=vehicle, scenario=scenario
    )
    capital_costs.set_glider_cost(scenario=scenario)
    assert capital_costs.glider_cost_dol == pytest.approx(11000.0, 0.01)


def test_set_fuel_converter_cost_dol(vehicle, scenario):
    capital_costs = CapitalCosts.__new__(
        CapitalCosts, vehicle=vehicle, scenario=scenario
    )
    capital_costs.set_fuel_converter_cost_dol(vehicle=vehicle, scenario=scenario)
    assert capital_costs.fuel_converter_cost_dol == pytest.approx(0, 0.01)


def test_set_fuel_storage_cost(vehicle, scenario):
    capital_costs = CapitalCosts.__new__(
        CapitalCosts, vehicle=vehicle, scenario=scenario
    )
    capital_costs.set_fuel_storage_cost(vehicle=vehicle, scenario=scenario)
    assert capital_costs.fuel_storage_cost_dol == pytest.approx(0, 0.01)


def test_set_motor_control_power_elecs_cost(vehicle, scenario):
    capital_costs = CapitalCosts.__new__(
        CapitalCosts, vehicle=vehicle, scenario=scenario
    )
    capital_costs.set_motor_control_power_elecs_cost(vehicle=vehicle, scenario=scenario)
    assert capital_costs.motor_control_power_elecs_cost_dol == pytest.approx(
        14300.0, 0.01
    )


def test_set_plug_cost(vehicle, scenario):
    capital_costs = CapitalCosts.__new__(
        CapitalCosts, vehicle=vehicle, scenario=scenario
    )
    capital_costs.set_plug_cost(vehicle=vehicle, scenario=scenario)
    assert capital_costs.plug_cost_dol == pytest.approx(1100, 0.01)


def test_set_battery_cost(vehicle, scenario):
    capital_costs = CapitalCosts.__new__(
        CapitalCosts, vehicle=vehicle, scenario=scenario
    )
    capital_costs.set_battery_cost(vehicle=vehicle, scenario=scenario)
    assert capital_costs.battery_cost_dol == pytest.approx(22000.0, 0.01)


def test_set_msrp(vehicle, scenario):
    capital_costs = CapitalCosts.__new__(
        CapitalCosts, vehicle=vehicle, scenario=scenario
    )
    capital_costs.battery_cost_dol = 22000.0
    capital_costs.plug_cost_dol = 1100.0
    capital_costs.motor_control_power_elecs_cost_dol = 14300.0
    capital_costs.fuel_storage_cost_dol = 0
    capital_costs.fuel_converter_cost_dol = 0
    capital_costs.glider_cost_dol = 10000
    capital_costs.set_msrp()
    assert capital_costs.msrp_total_dol == pytest.approx(47400.0, 0.01)


def test_set_purchase_tax(vehicle, scenario):
    capital_costs = CapitalCosts.__new__(
        CapitalCosts, vehicle=vehicle, scenario=scenario
    )
    capital_costs.msrp_total_dol = 48400.0
    capital_costs.set_purchase_tax(scenario=scenario)
    assert capital_costs.purchase_tax_dol == pytest.approx(3872.0, 0.01)


def test_set_downpayment(vehicle, scenario):
    capital_costs = CapitalCosts.__new__(
        CapitalCosts, vehicle=vehicle, scenario=scenario
    )
    capital_costs.msrp_total_dol = 48400.0
    capital_costs.purchase_tax_dol = 3792.0
    capital_costs.set_downpayment(scenario=scenario)
    assert capital_costs.purchasing_downpayment_dol == pytest.approx(5219.20, 0.01)


def test_set_residual_cost(vehicle, scenario):
    capital_costs = CapitalCosts.__new__(
        CapitalCosts, vehicle=vehicle, scenario=scenario
    )
    capital_costs.msrp_total_dol = 48400.0
    capital_costs.set_residual_cost(scenario=scenario)
    assert capital_costs.residual_cost_dol == pytest.approx(-18847.74, 0.01)


def test_set_residual_cost_is_idempotent(vehicle, scenario):
    """A reused Scenario must not accumulate depreciation.

    The optimizer evaluates hundreds of designs against one Scenario, so a
    residual rate that compounds per call makes the objective drift.
    """
    capital_costs = CapitalCosts.__new__(
        CapitalCosts, vehicle=vehicle, scenario=scenario
    )
    capital_costs.msrp_total_dol = 48400.0

    capital_costs.set_residual_cost(scenario=scenario)
    first = capital_costs.residual_cost_dol
    first_rate = scenario.residual_rate_pct

    for _ in range(3):
        capital_costs.set_residual_cost(scenario=scenario)

    assert capital_costs.residual_cost_dol == pytest.approx(first)
    assert scenario.residual_rate_pct == pytest.approx(first_rate)


def test_set_net_capital_cost(vehicle, scenario):
    capital_costs = CapitalCosts.__new__(
        CapitalCosts, vehicle=vehicle, scenario=scenario
    )
    capital_costs.msrp_total_dol = 48400.0
    capital_costs.purchase_tax_dol = 3792.0
    capital_costs.set_net_capital_cost()
    assert capital_costs.net_capital_cost_dol == pytest.approx(52192.0, 0.01)


def test_set_disc_residual_cost(vehicle, scenario):
    capital_costs = CapitalCosts.__new__(
        CapitalCosts, vehicle=vehicle, scenario=scenario
    )
    capital_costs.residual_cost_dol = -18847.74
    capital_costs.set_disc_residual_cost(scenario=scenario)
    print(capital_costs.disc_residual_cost_dol)
    assert capital_costs.disc_residual_cost_dol == pytest.approx(-11570.877, 0.01)


def test_get_marked_up_value(vehicle, scenario):
    capital_costs = CapitalCosts.__new__(
        CapitalCosts, vehicle=vehicle, scenario=scenario
    )
    marked_up_value = capital_costs.get_marked_up_value(1000, scenario)
    assert marked_up_value == pytest.approx(1100, 0.01)
