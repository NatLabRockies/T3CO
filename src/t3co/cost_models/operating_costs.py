import ast

import pandas as pd

from t3co.constants import Global as gl
from t3co.cost_models.capital_costs import CapitalCosts
from t3co.cost_models.opportunity_costs import OpportunityCosts
from t3co.energy_models.energy import Energy
from t3co.input_data.scenario import Scenario
from t3co.input_data.vehicle import Vehicle
from t3co.utils.print_class_objects import get_path_object, obj_to_string


class OperatingCosts:
    fuel_cost_dol_per_yr: float = 0.0
    fuel_price_dol_per_gge: float = 0.0
    fuel_used_gal_gge_per_yr: float = 0.0
    fuel_used_gal_gde_per_yr: float = 0.0
    energy_used_kwh_per_yr: float = 0.0
    enroute_fuel_price_dol_per_gge: float = 0.0
    energy_fueled_enroute_kwh_per_yr: float = 0.0
    energy_fueled_offshift_kwh_per_yr: float = 0.0
    enroute_fuel_cost_dol_per_yr: float = 0.0
    offshift_fuel_cost_dol_per_yr: float = 0.0
    enroute_charging_duration_hr_per_yr: float = 0.0
    offshift_charging_duration_hr_per_yr: float = 0.0
    maintenance_cost_dol_per_yr: float = 0.0
    maintenance_cost_dol_per_mi: float = 0.0
    insurance_cost_dol_per_yr: float = 0.0
    distance_traveled_mi_per_yr: float = 0.0
    purchasing_payment_dol_per_yr: float = 0.0
    purchasing_tax_amount_dol_per_year: float = 0.0
    purchasing_cost_dol_per_yr: float = 0.0
    purchasing_remaining_principal_dol: float = 0.0
    fueling_dwell_labor_cost_dol_per_yr: float = 0.0
    net_oper_cost_dol_per_yr: float = 0.0
    disc_oper_cost_dol_per_yr: float = 0.0

    def __new__(cls, *args, **kwargs):
        """
        Creates a new instance of the OperatingCosts class.
        """
        instance = super(OperatingCosts, cls).__new__(cls)
        return instance

    def __init__(
        self,
        year_number: int,
        cap_costs: CapitalCosts,
        vehicle: Vehicle,
        scenario: Scenario,
        energy: Energy = None,
        oppy_costs: OpportunityCosts = None,
    ):
        """
        Initializes the OperatingCosts instance.

        Args:
            year_number (int): The year number for which the operating costs are calculated.
            cap_costs (CapitalCosts): The capital costs associated with the vehicle.
            vehicle (Vehicle): The vehicle instance.
            scenario (Scenario): The scenario instance containing configuration data.
            energy (Energy, optional): The energy model instance. Defaults to None.
            oppy_costs (OpportunityCosts, optional): The opportunity costs associated with the vehicle. Defaults to None.
        """
        if energy:
            self.mpgge = energy.mpgge
        self.distance_traveled_mi_per_yr = scenario.vmt[year_number - 1]

        if scenario.cost_toggles.fuel_cost:
            self.set_fuel_cost(
                year_number=year_number,
                vehicle=vehicle,
                scenario=scenario,
                oppy_costs=oppy_costs,
            )
        if scenario.cost_toggles.maintenance_oper_cost:
            self.set_maintenance_oper_cost(
                year_number=year_number, vehicle=vehicle, scenario=scenario
            )
        if scenario.cost_toggles.insurance_cost:
            self.set_insurance_cost(
                year_number=year_number,
                cap_cost=cap_costs,
                vehicle=vehicle,
                scenario=scenario,
            )
        if scenario.cost_toggles.fueling_dwell_labor:
            if scenario.activate_tco_fueling_dwell_time_cost and oppy_costs:
                self.set_fueling_dwell_labor_cost(
                    scenario=scenario, oppy_costs=oppy_costs
                )
            else:
                self.fueling_dwell_labor_cost_dol_per_yr = 0.0
        if scenario.cost_toggles.purchasing_cost:
            self.set_purchasing_payment_cost(
                year_number=year_number, scenario=scenario, cap_costs=cap_costs
            )
        self.set_net_oper_cost()
        self.set_disc_oper_cost(year_number=year_number, scenario=scenario)

    def set_fuel_cost(
        self,
        year_number: int,
        vehicle: Vehicle,
        scenario: Scenario,
        oppy_costs: OpportunityCosts = None,
    ) -> None:
        """
        Sets the fuel cost for the given year.

        This method calculates the fuel cost based on the fuel price and the amount of fuel used.
        For electricity, the energy is split into enroute and off-shift charging, each
        priced separately (see set_enroute_offshift_fuel_cost).
        The calculation uses the following OperatingCosts elements:
        - distance_traveled_mi_per_yr
        - mpgge

        Inputs from scenario:
        - fuel_prices_df
        - fuel_type
        - model_year
        - region

        Estimated class variables:
        - fuel_price_dol_per_gge
        - fuel_used_gal_gge_per_yr
        - fuel_used_gal_gde_per_yr
        - energy_used_kwh_per_yr
        - fuel_cost_dol_per_yr

        Args:
            year_number (int): The year number for which the fuel cost is calculated.
            vehicle (Vehicle): The vehicle instance.
            scenario (Scenario): The scenario instance containing configuration data.
            oppy_costs (OpportunityCosts, optional): The opportunity costs, whose charging_energy_kwh_per_yr is the energy charged enroute. Defaults to None.
        """
        if scenario.fuel_prices_df is None:
            scenario.fuel_prices_df = pd.read_csv(
                get_path_object(scenario.fuel_prices_file)
            )
            scenario.fuel_prices_df.set_index("Fuel", inplace=True)

        scenario.fuel_prices_df = scenario.fuel_prices_df[
            scenario.fuel_prices_df["Region"] == scenario.region
        ]

        if (
            "diesel" in scenario.fuel_type.lower()
            and "bio" not in scenario.fuel_type.lower()
        ):
            diesel_dol_per_gal = scenario.fuel_prices_df.loc[
                "diesel_dol_per_gal", str(scenario.model_year + year_number - 1)
            ]
            self.fuel_price_dol_per_gge = diesel_dol_per_gal * gl.DGE_TO_GGE
        elif "gasoline" in scenario.fuel_type.lower():
            gasoline_dol_per_gal = scenario.fuel_prices_df.loc[
                "gasoline_dol_per_gal", str(scenario.model_year + year_number - 1)
            ]
            self.fuel_price_dol_per_gge = gasoline_dol_per_gal
        elif "electricity" in scenario.fuel_type.lower():
            electricity_dol_per_kwh = scenario.fuel_prices_df.loc[
                "electricity_dol_per_kwh", str(scenario.model_year + year_number - 1)
            ]
            self.fuel_price_dol_per_gge = electricity_dol_per_kwh * gl.KWH_PER_GGE
            # Enroute charging falls back to the depot price when the fuel
            # prices file has no enroute row, so results don't change.
            if "enroute_electricity_dol_per_kwh" in scenario.fuel_prices_df.index:
                self.enroute_fuel_price_dol_per_gge = (
                    scenario.fuel_prices_df.loc[
                        "enroute_electricity_dol_per_kwh",
                        str(scenario.model_year + year_number - 1),
                    ]
                    * gl.KWH_PER_GGE
                )
            else:
                self.enroute_fuel_price_dol_per_gge = self.fuel_price_dol_per_gge
        elif scenario.fuel_type.lower() == "cng":
            cng_dol_per_gge = scenario.fuel_prices_df.loc[
                "cng_dol_per_gge", str(scenario.model_year + year_number - 1)
            ]
            self.fuel_price_dol_per_gge = cng_dol_per_gge
        elif scenario.fuel_type.lower() == "hydrogen":
            hydrogen_dol_per_gge = scenario.fuel_prices_df.loc[
                "hydrogen_dol_per_gge", str(scenario.model_year + year_number - 1)
            ]
            self.fuel_price_dol_per_gge = hydrogen_dol_per_gge
        else:
            raise Exception(
                f"Operating Costs calculation: Unknown fuel type {scenario.fuel_type}"
            )

        if self.mpgge and self.mpgge > 0:
            self.fuel_used_gal_gge_per_yr = (
                self.distance_traveled_mi_per_yr / self.mpgge
            )
            self.fuel_used_gal_gde_per_yr = (
                self.fuel_used_gal_gge_per_yr / gl.DGE_TO_GGE
            )
            self.energy_used_kwh_per_yr = self.fuel_used_gal_gge_per_yr * gl.KWH_PER_GGE

            if "electricity" in scenario.fuel_type.lower():
                self.set_enroute_offshift_fuel_cost(
                    scenario=scenario, oppy_costs=oppy_costs
                )
            else:
                self.fuel_cost_dol_per_yr = (
                    self.fuel_price_dol_per_gge * self.fuel_used_gal_gge_per_yr
                )
        else:
            self.fuel_used_gal_gge_per_yr = 0
            self.fuel_used_gal_gde_per_yr = 0
            self.energy_used_kwh_per_yr = 0
            self.fuel_cost_dol_per_yr = 0
            # print(f"Warning: mpgge is {self.mpgge}. Fuel cost set to 0.")

    def set_enroute_offshift_fuel_cost(
        self, scenario: Scenario, oppy_costs: OpportunityCosts = None
    ) -> None:
        """
        Splits the electricity used in the year into enroute and off-shift charging.

        Enroute charging is the energy refilled during fueling dwells within a shift
        (OpportunityCosts.charging_energy_kwh_per_yr), capped at the energy used.
        Off-shift charging, for example overnight at the depot, supplies the rest.
        Enroute energy is priced at enroute_fuel_price_dol_per_gge and off-shift energy
        at fuel_price_dol_per_gge. Charging durations assume
        scenario.ess_max_charging_power_kw for both and exclude dwell overhead.

        Inputs from scenario:
        - ess_max_charging_power_kw

        Inputs from oppy_costs:
        - charging_energy_kwh_per_yr

        Estimated class variables:
        - energy_fueled_enroute_kwh_per_yr
        - energy_fueled_offshift_kwh_per_yr
        - enroute_fuel_cost_dol_per_yr
        - offshift_fuel_cost_dol_per_yr
        - enroute_charging_duration_hr_per_yr
        - offshift_charging_duration_hr_per_yr
        - fuel_cost_dol_per_yr

        Args:
            scenario (Scenario): The scenario instance containing configuration data.
            oppy_costs (OpportunityCosts, optional): The opportunity costs. Without them, or when fueling dwell time is not calculated, all charging is off-shift. Defaults to None.
        """
        charged_enroute_kwh = getattr(oppy_costs, "charging_energy_kwh_per_yr", 0.0)
        self.energy_fueled_enroute_kwh_per_yr = min(
            max(0.0, charged_enroute_kwh), self.energy_used_kwh_per_yr
        )
        self.energy_fueled_offshift_kwh_per_yr = (
            self.energy_used_kwh_per_yr - self.energy_fueled_enroute_kwh_per_yr
        )

        self.enroute_fuel_cost_dol_per_yr = (
            self.enroute_fuel_price_dol_per_gge
            * self.energy_fueled_enroute_kwh_per_yr
            / gl.KWH_PER_GGE
        )
        self.offshift_fuel_cost_dol_per_yr = (
            self.fuel_price_dol_per_gge
            * self.energy_fueled_offshift_kwh_per_yr
            / gl.KWH_PER_GGE
        )
        self.fuel_cost_dol_per_yr = (
            self.enroute_fuel_cost_dol_per_yr + self.offshift_fuel_cost_dol_per_yr
        )

        if scenario.ess_max_charging_power_kw:
            self.enroute_charging_duration_hr_per_yr = (
                self.energy_fueled_enroute_kwh_per_yr
                / scenario.ess_max_charging_power_kw
            )
            self.offshift_charging_duration_hr_per_yr = (
                self.energy_fueled_offshift_kwh_per_yr
                / scenario.ess_max_charging_power_kw
            )

    def set_maintenance_oper_cost(
        self, year_number: int, vehicle: Vehicle, scenario: Scenario
    ) -> None:
        """
        Sets the maintenance operating cost for the given year.

        This method calculates the maintenance cost based on the maintenance cost per mile and the distance traveled.

        Inputs from scenario:
        - maint_oper_cost_dol_per_mi
        - vmt

        Estimated class variables:
        - maintenance_cost_dol_per_mi
        - maintenance_cost_dol_per_yr

        Args:
            year_number (int): The year number for which the maintenance cost is calculated.
            vehicle (Vehicle): The vehicle instance.
            scenario (Scenario): The scenario instance containing configuration data.
        """
        self.maintenance_cost_dol_per_mi = scenario.maint_oper_cost_dol_per_mi[
            year_number - 1
        ]

        self.maintenance_cost_dol_per_yr = (
            self.maintenance_cost_dol_per_mi * self.distance_traveled_mi_per_yr
        )

    def set_insurance_cost(
        self,
        year_number: int,
        cap_cost: CapitalCosts,
        vehicle: Vehicle,
        scenario: Scenario,
    ) -> None:
        """
        Sets the insurance cost for the given year.

        This method calculates the insurance cost based on the insurance rate and the total value of the vehicle.

        Inputs from scenario:
        - insurance_rates_pct_per_yr

        Inputs from cap_cost:
        - msrp_total_dol

        Estimated class variables:
        - insurance_cost_dol_per_yr

        Args:
            year_number (int): The year number for which the insurance cost is calculated.
            cap_cost (CapitalCosts): The capital costs associated with the vehicle.
            vehicle (Vehicle): The vehicle instance.
            scenario (Scenario): The scenario instance containing configuration data.
        """
        self.insurance_rates_pct_per_yr = (
            ast.literal_eval(scenario.insurance_rates_pct_per_yr)[year_number - 1]
            if isinstance(scenario.insurance_rates_pct_per_yr, str)
            else scenario.insurance_rates_pct_per_yr[year_number - 1]
        )

        self.insurance_cost_dol_per_yr = (
            cap_cost.msrp_total_dol * self.insurance_rates_pct_per_yr
        )

    def set_purchasing_payment_cost(
        self, year_number: int, scenario: Scenario, cap_costs: CapitalCosts
    ):
        """
        Sets the purchasing payment cost for the given year.

        This method calculates the purchasing payment cost based on the purchasing method specified in the scenario.

        Inputs from scenario:
        - purchasing_method
        - purchasing_interest_apr_pct_per_yr
        - purchasing_payment_frequency_months
        - purchasing_term_yr
        - tax_rate_pct
        - leasing_money_factor

        Inputs from cap_costs:
        - purchasing_initial_principal_dol
        - msrp_total_dol
        - purchase_tax_dol
        - purchasing_downpayment_dol
        - residual_cost_dol

        Estimated OperatingCosts variables:
        - purchasing_payment_dol_per_yr
        - purchasing_cost_dol_per_yr
        - purchasing_remaining_principal_dol
        - purchasing_tax_amount_dol_per_year

        Args:
            year_number (int): The year number for which the purchasing payment cost is calculated.
            scenario (Scenario): The scenario instance containing configuration data, including the purchasing method, interest rate, and term.
            cap_costs (CapitalCosts): The capital costs associated with the vehicle.
        """
        if scenario.purchasing_method == "cash":
            self.purchasing_payment_dol_per_yr = 0
            self.purchasing_cost_dol_per_yr = 0

        elif scenario.purchasing_method == "loan":
            if (
                scenario.purchasing_term_yr <= 0
                or scenario.purchasing_payment_frequency_months <= 0
            ):
                self.purchasing_payment_dol_per_yr = 0
                self.purchasing_cost_dol_per_yr = 0
                self.purchasing_remaining_principal_dol = 0
                return

            interest_rate_pct_per_frequency = (
                scenario.purchasing_interest_apr_pct_per_yr
                / 12
                * scenario.purchasing_payment_frequency_months
            )
            total_number_of_payments = int(
                scenario.purchasing_term_yr
                * 12
                / scenario.purchasing_payment_frequency_months
            )  # TODO check for missing payment
            annual_number_of_payments = int(
                12 / scenario.purchasing_payment_frequency_months
            )

            purchasing_payment_dol_per_freq = (
                cap_costs.purchasing_initial_principal_dol
                * interest_rate_pct_per_frequency
                * (1 + interest_rate_pct_per_frequency) ** total_number_of_payments
            ) / ((1 + interest_rate_pct_per_frequency) ** total_number_of_payments - 1)

            self.purchasing_remaining_principal_dol = (
                cap_costs.purchasing_initial_principal_dol
                * (1 + interest_rate_pct_per_frequency)
                ** (year_number * annual_number_of_payments)
            ) - purchasing_payment_dol_per_freq / interest_rate_pct_per_frequency * (
                (1 + interest_rate_pct_per_frequency)
                ** (year_number * annual_number_of_payments)
                - 1
            )

            self.purchasing_cost_dol_per_yr = sum(
                [
                    interest_rate_pct_per_frequency
                    * (
                        cap_costs.purchasing_initial_principal_dol
                        * (1 + interest_rate_pct_per_frequency) ** n
                        - purchasing_payment_dol_per_freq
                        / interest_rate_pct_per_frequency
                        * ((1 + interest_rate_pct_per_frequency) ** n - 1)
                    )
                    for n in range(
                        (year_number - 1) * annual_number_of_payments,
                        (year_number * annual_number_of_payments + 1),
                    )
                ]
            )

            self.purchasing_payment_dol_per_yr = (
                purchasing_payment_dol_per_freq * annual_number_of_payments
            )

        elif scenario.purchasing_method == "lease":
            if scenario.purchasing_term_yr <= 0:
                self.purchasing_payment_dol_per_yr = 0
                self.purchasing_cost_dol_per_yr = 0
                self.purchasing_tax_amount_dol_per_year = 0
                return

            adjusted_cap_cost_dol = (
                cap_costs.msrp_total_dol
                + cap_costs.purchase_tax_dol
                - cap_costs.purchasing_downpayment_dol
            )
            depreciation_cost_dol_per_month = (
                adjusted_cap_cost_dol + cap_costs.residual_cost_dol
            ) / (scenario.purchasing_term_yr * 12)
            finance_fee_dol_per_month = (
                adjusted_cap_cost_dol - cap_costs.residual_cost_dol
            ) * scenario.leasing_money_factor
            self.purchasing_tax_amount_dol_per_year = (
                (depreciation_cost_dol_per_month + finance_fee_dol_per_month)
                * scenario.tax_rate_pct
                * 12
            )
            self.purchasing_payment_dol_per_yr = (
                depreciation_cost_dol_per_month
                + finance_fee_dol_per_month
                + self.purchasing_tax_amount_dol_per_year / 12
            ) * 12
            self.purchasing_cost_dol_per_yr = finance_fee_dol_per_month * 12

    def set_fueling_dwell_labor_cost(
        self, scenario: Scenario, oppy_costs: OpportunityCosts
    ) -> None:
        """
        Sets the fueling dwell labor cost for the given year.

        This method calculates the fueling dwell labor cost based on the fueling dwell time and the labor rate.

        Inputs from scenario:
        - labor_rate_dol_per_hr

        Inputs from oppy_costs:
        - fueling_dwell_time_hr_per_yr

        Estimated OperatingCosts variables:
        - fueling_dwell_labor_cost_dol_per_yr

        Args:
            scenario (Scenario): The scenario instance containing configuration data.
            oppy_costs (OpportunityCosts): The opportunity costs associated with the vehicle.
        """
        self.fueling_dwell_labor_cost_dol_per_yr = (
            oppy_costs.fueling_dwell_time_hr_per_yr * scenario.labor_rate_dol_per_hr
        )

    def set_net_oper_cost(self) -> None:
        """
        Sets the net operating cost for the given year.

        This method calculates the net operating cost by summing the various operating cost components.
        The calculation uses the following OperatingCosts elements:
        - fuel_cost_dol_per_yr
        - fueling_dwell_labor_cost_dol_per_yr
        - maintenance_cost_dol_per_yr
        - insurance_cost_dol_per_yr
        - purchasing_payment_dol_per_yr

        Estimated OperatingCosts variables:
        - net_oper_cost_dol_per_yr
        """
        self.net_oper_cost_dol_per_yr = (
            self.fuel_cost_dol_per_yr
            + self.fueling_dwell_labor_cost_dol_per_yr
            + self.maintenance_cost_dol_per_yr
            + self.insurance_cost_dol_per_yr
            + self.purchasing_payment_dol_per_yr
        )

    def set_disc_oper_cost(self, year_number: int, scenario: Scenario) -> None:
        """
        Sets the discounted operating cost for the given year.

        This method calculates the discounted operating cost based on the net operating cost and the discount rate.
        The calculation uses the following OperatingCosts elements:
        - net_oper_cost_dol_per_yr

        Inputs from scenario:
        - discount_rate_pct_per_yr

        Estimated OperatingCosts variables:
        - disc_oper_cost_dol_per_yr

        Args:
            year_number (int): The year number for which the discounted operating cost is calculated.
            scenario (Scenario): The scenario instance containing configuration data.
        """
        self.disc_oper_cost_dol_per_yr = scenario.get_discounted_value(
            value=self.net_oper_cost_dol_per_yr, year_number=year_number
        )

    def __str__(self) -> str:
        """
        Returns a string representation of the OperatingCosts instance.

        Returns:
            str: String representation of the OperatingCosts instance.
        """
        return obj_to_string(self)
