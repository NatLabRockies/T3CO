import numpy as np

from t3co.constants import Global as gl
from t3co.input_data.scenario import Scenario
from t3co.input_data.vehicle import Vehicle


class CapitalCosts:
    glider_cost_dol: float = 0.0
    fuel_converter_cost_dol: float = 0.0
    fuel_storage_cost_dol: float = 0.0
    motor_control_power_elecs_cost_dol: float = 0.0
    plug_cost_dol: float = 0.0
    battery_cost_dol: float = 0.0
    purchase_tax_dol: float = 0.0
    msrp_total_dol: float = 0.0
    residual_cost_dol: float = 0.0
    purchasing_downpayment_dol: float = 0.0
    purchasing_initial_principal_dol: float = 0.0
    net_capital_cost_dol: float = None
    disc_residual_cost_dol: float = None

    def __new__(cls, *args, **kwargs):
        """
        Creates a new instance of the CapitalCosts class.
        """
        instance = super(CapitalCosts, cls).__new__(cls)
        return instance

    def __init__(
        self, vehicle: Vehicle, scenario: Scenario, msrp_total_dol: float = None
    ):
        """
        Initializes the CapitalCosts instance.

        Args:
            vehicle (Vehicle): The vehicle instance.
            scenario (Scenario): The scenario instance containing configuration data.
            msrp_total_dol (float, optional): MSRP in dollars as input.
        """
        if scenario.cost_toggles.msrp:
            if not msrp_total_dol and vehicle:
                self.set_glider_cost(scenario=scenario)
                self.set_fuel_converter_cost_dol(vehicle=vehicle, scenario=scenario)
                self.set_fuel_storage_cost(vehicle=vehicle, scenario=scenario)
                self.set_motor_control_power_elecs_cost(
                    vehicle=vehicle, scenario=scenario
                )
                self.set_plug_cost(vehicle=vehicle, scenario=scenario)
                self.set_battery_cost(vehicle=vehicle, scenario=scenario)
                self.set_msrp()
            else:
                self.msrp_total_dol = msrp_total_dol

        if scenario.cost_toggles.purchase_tax:
            self.set_purchase_tax(scenario=scenario)
        if scenario.cost_toggles.purchasing_downpayment:
            self.set_downpayment(scenario=scenario)
        if scenario.cost_toggles.residual_cost:
            self.set_residual_cost(scenario=scenario)
            self.set_disc_residual_cost(scenario=scenario)

        self.set_net_capital_cost()

    def set_glider_cost(self, scenario: Scenario) -> None:
        """
        Sets the glider cost for the vehicle.

        This method calculates the marked up glider cost based on the vehicle class and the base cost.

        Inputs from scenario:
        - vehicle_glider_cost_dol

        Estimated class variables:
        - glider_cost_dol

        Args:
            scenario (Scenario): The scenario instance containing configuration data, including the base cost for the glider.
        """
        self.glider_cost_dol = scenario.vehicle_glider_cost_dol
        self.glider_cost_dol = self.get_marked_up_value(self.glider_cost_dol, scenario)

    def set_fuel_converter_cost_dol(self, vehicle: Vehicle, scenario: Scenario) -> None:
        """
        Sets the fuel converter cost for the vehicle.

        This method calculates the marked up fuel converter cost based on the vehicle powertrain type and the cost per kW.

        Inputs from vehicle:
        - fc_max_kw

        Inputs from scenario:
        - fc_fuelcell_cost_dol_per_kw
        - fc_ice_cost_dol_per_kw
        - fc_cng_ice_cost_dol_per_kw
        - fc_ice_base_cost_dol

        Estimated class variables:
        - fuel_converter_cost_dol

        Args:
            vehicle (Vehicle): The vehicle instance.
            scenario (Scenario): The scenario instance containing configuration data, including the cost per kW for the fuel converter.
        """
        if vehicle.veh_pt_type == gl.BEV or vehicle.fc_max_kw == 0:
            self.fuel_converter_cost_dol = 0
        elif vehicle.veh_pt_type == gl.HEV:
            self.fuel_converter_cost_dol = (
                scenario.fc_fuelcell_cost_dol_per_kw * vehicle.fc_max_kw
            )
        elif vehicle.veh_pt_type == gl.CONV and scenario.fuel_type == "cng":
            self.fuel_converter_cost_dol = (
                scenario.fc_cng_ice_cost_dol_per_kw * vehicle.fc_max_kw
            ) + scenario.fc_ice_base_cost_dol
        else:
            self.fuel_converter_cost_dol = (
                scenario.fc_ice_cost_dol_per_kw * vehicle.fc_max_kw
            ) + scenario.fc_ice_base_cost_dol

        self.fuel_converter_cost_dol = self.get_marked_up_value(
            self.fuel_converter_cost_dol, scenario
        )

    def set_fuel_storage_cost(self, vehicle: Vehicle, scenario: Scenario) -> None:
        """
        Sets the fuel storage cost for the vehicle.

        This method calculates the marked up fuel storage cost based on the vehicle powertrain type and the cost per kWh.

        Inputs from vehicle:
        - fs_kwh

        Inputs from scenario:
        - fs_h2_cost_dol_per_kwh
        - fs_cng_cost_dol_per_kwh
        - fs_cost_dol_per_kwh

        Estimated class variables:
        - fuel_storage_cost_dol

        Args:
            vehicle (Vehicle): The vehicle instance.
            scenario (Scenario): The scenario instance containing configuration data, including the cost per kWh for the fuel storage.
        """
        if vehicle.veh_pt_type == gl.BEV:
            self.fuel_storage_cost_dol = 0
        elif vehicle.veh_pt_type == gl.HEV and scenario.fuel_type[0] == "hydrogen":
            self.fuel_storage_cost_dol = (
                scenario.fs_h2_cost_dol_per_kwh * vehicle.fs_kwh
            )
        elif (
            vehicle.veh_pt_type in [gl.CONV, gl.HEV] and scenario.fuel_type[0] == "cng"
        ):
            self.fuel_storage_cost_dol = (
                scenario.fs_cng_cost_dol_per_kwh * vehicle.fs_kwh
            )
        elif vehicle.veh_pt_type in [gl.CONV, gl.HEV]:
            self.fuel_storage_cost_dol = scenario.fs_cost_dol_per_kwh * vehicle.fs_kwh
        else:
            self.fuel_storage_cost_dol = 0

        self.fuel_storage_cost_dol = self.get_marked_up_value(
            self.fuel_storage_cost_dol, scenario
        )

    def set_motor_control_power_elecs_cost(
        self, vehicle: Vehicle, scenario: Scenario
    ) -> None:
        """
        Sets the motor control and power electronics cost for the vehicle.

        This method calculates the marked up motor control and power electronics cost based on the vehicle powertrain type and the cost per kW.

        Inputs from vehicle:
        - mc_max_kw

        Inputs from scenario:
        - pe_mc_base_cost_dol
        - pe_mc_cost_dol_per_kw

        Estimated class variables:
        - motor_control_power_elecs_cost_dol

        Args:
            vehicle (Vehicle): The vehicle instance.
            scenario (Scenario): The scenario instance containing configuration data, including the cost per kW for the motor control and power electronics.
        """
        if vehicle.mc_max_kw == 0 or vehicle.mc_max_kw is None:
            self.motor_control_power_elecs_cost_dol = 0
        else:
            self.motor_control_power_elecs_cost_dol = scenario.pe_mc_base_cost_dol + (
                scenario.pe_mc_cost_dol_per_kw * vehicle.mc_max_kw
            )
        self.motor_control_power_elecs_cost_dol = self.get_marked_up_value(
            self.motor_control_power_elecs_cost_dol, scenario
        )

    def set_plug_cost(self, vehicle: Vehicle, scenario: Scenario) -> None:
        """
        Sets the plug cost for the vehicle.

        This method calculates the marked up plug cost based on the base cost.

        Inputs from scenario:
        - plug_base_cost_dol

        Estimated class variables:
        - plug_cost_dol

        Args:
            vehicle (Vehicle): The vehicle instance.
            scenario (Scenario): The scenario instance containing configuration data, including the base cost for the plug.
        """
        if vehicle.veh_pt_type in [gl.BEV, gl.HEV] and vehicle.chg_eff:
            self.plug_cost_dol = scenario.plug_base_cost_dol
        else:
            self.plug_cost_dol = 0

        self.plug_cost_dol = self.get_marked_up_value(self.plug_cost_dol, scenario)

    def set_battery_cost(self, vehicle: Vehicle, scenario: Scenario) -> None:
        """
        Sets the battery cost for the vehicle.

        This method calculates the marked up battery cost based on the energy storage system (ESS) capacity and the cost per kWh.

        Inputs from vehicle:
        - ess_max_kwh

        Inputs from scenario:
        - ess_base_cost_dol
        - ess_cost_dol_per_kwh

        Estimated class variables:
        - battery_cost_dol

        Args:
            vehicle (Vehicle): The vehicle instance.
            scenario (Scenario): The scenario instance containing configuration data, including the cost per kWh for the battery.
        """
        if vehicle.ess_max_kwh == 0:
            self.battery_cost_dol = 0
        else:
            self.battery_cost_dol = scenario.ess_base_cost_dol + (
                scenario.ess_cost_dol_per_kwh * vehicle.ess_max_kwh
            )

        self.battery_cost_dol = self.get_marked_up_value(
            self.battery_cost_dol, scenario
        )

    def set_msrp(self) -> None:
        """
        Calculates the total MSRP (Manufacturer's Suggested Retail Price) for the vehicle.

        This method calculates the total MSRP by summing the costs of various components of the vehicle.
        The calculation uses the following CapitalCosts elements:
        - glider_cost_dol
        - fuel_storage_cost_dol
        - fuel_converter_cost_dol
        - motor_control_power_elecs_cost_dol
        - battery_cost_dol
        - plug_cost_dol

        Estimated class variables:
        - msrp_total_dol
        """

        self.msrp_total_dol = (
            self.glider_cost_dol
            + self.fuel_storage_cost_dol
            + self.fuel_converter_cost_dol
            + self.motor_control_power_elecs_cost_dol
            + self.battery_cost_dol
            + self.plug_cost_dol
        )

    def set_purchase_tax(self, scenario: Scenario) -> None:
        """
        Sets the purchase tax for the vehicle.

        This method calculates the purchase tax based on the total MSRP (Manufacturer's Suggested Retail Price) of the vehicle components.
        The calculations use the following CapitalCosts elements:
        - msrp_total_dol

        Inputs from scenario:
        - tax_rate_pct

        Estimated class variables:
        - purchase_tax_dol

        Args:
            scenario (Scenario): The scenario instance containing configuration data, including the tax rate.
        """
        self.purchase_tax_dol = self.msrp_total_dol * scenario.tax_rate_pct

    def set_downpayment(self, scenario: Scenario) -> None:
        """
        Sets the downpayment and initial principal for the vehicle purchase.

        This method calculates the downpayment and initial principal based on the purchasing method specified in the scenario.
        The calculations use the following CapitalCosts elements:
        - msrp_total_dol
        - purchase_tax_dol

        Inputs from scenario:
        - purchasing_method
        - purchasing_down_payment_pct
        - purchasing_interest_apr_pct_per_yr

        Estimated class variables:
        - purchasing_downpayment_dol
        - purchasing_initial_principal_dol

        Args:
            scenario (Scenario): The scenario instance containing configuration data, including the purchasing method, down payment percentage, and interest rate.
        """

        if scenario.purchasing_method == "loan":
            self.purchasing_downpayment_dol = (
                self.msrp_total_dol + self.purchase_tax_dol
            ) * scenario.purchasing_down_payment_pct
            self.purchasing_initial_principal_dol = (
                self.msrp_total_dol + self.purchase_tax_dol
            ) * (1 - scenario.purchasing_down_payment_pct)

        elif scenario.purchasing_method == "lease":
            scenario.leasing_money_factor = (
                scenario.purchasing_interest_apr_pct_per_yr / 24
            )
            self.purchasing_downpayment_dol = (
                self.msrp_total_dol + self.purchase_tax_dol
            ) * scenario.purchasing_down_payment_pct
            self.purchasing_initial_principal_dol = 0.0
        else:
            self.purchasing_downpayment_dol = (
                self.msrp_total_dol + self.purchase_tax_dol
            )
            self.purchasing_initial_principal_dol = 0.0

    def set_residual_cost(self, scenario: Scenario) -> None:
        """
        Sets the residual cost for the vehicle.

        This method calculates the residual cost based on the total MSRP (Manufacturer's Suggested Retail Price) of the vehicle components,
        the depreciation rates per year, and the vehicle's life span. The residual cost is the remaining value of the vehicle after depreciation.
        The calculation uses the following CapitalCosts elements:
        - msrp_total_dol

        Inputs from scenario:
        - depreciation_rates_pct_per_yr
        - vehicle_life_yr

        Estimated scenario variables:
        - residual_rate_pct

        Estimated class variables:
        - residual_cost_dol

        Args:
            scenario (Scenario): The scenario instance containing configuration data, including depreciation rates and vehicle life span.
        """

        # Assignment, not accumulation: residual_rate_pct is derived from the
        # depreciation rates, not a scenario input, so compounding it corrupts
        # every reuse of the same Scenario.
        scenario.residual_rate_pct = np.prod(
            [
                (1 - scenario.depreciation_rates_pct_per_yr[i])
                for i in range(scenario.vehicle_life_yr)
            ]
        )
        self.residual_cost_dol = -self.msrp_total_dol * scenario.residual_rate_pct

    def set_net_capital_cost(self) -> None:
        """
        Sets the total capital cost for the vehicle.

        This method calculates the total capital cost by summing the costs of various components and applying the purchase tax.
        The calculation uses the following CapitalCosts elements:
        - purchasing_downpayment_dol

        Inputs from scenario:
        - tax_rate_pct

        Estimated class variables:
        - net_capital_cost_dol

        """
        self.net_capital_cost_dol = (
            self.purchasing_downpayment_dol
            if self.purchasing_downpayment_dol
            else (self.msrp_total_dol + self.purchase_tax_dol)
        )

    def set_disc_residual_cost(self, scenario: Scenario) -> None:
        """
        Sets the discounted residual cost for the vehicle.

        Args:
            scenario (Scenario): The scenario instance containing configuration data.
        """
        self.disc_residual_cost_dol = scenario.get_discounted_value(
            self.residual_cost_dol, year_number=scenario.vehicle_life_yr
        )

    def get_marked_up_value(self, value: float, scenario: Scenario) -> float:
        """
        Returns the marked up value.

        Args:
            value (float): The value to mark up.
            scenario (Scenario): The scenario instance containing configuration data.

        Returns:
            float: The marked up value.
        """
        return value * (scenario.markup_pct if scenario.markup_pct else 1)
