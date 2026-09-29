# Ledger Output Parameters


**Filter Options:**
- **Category:** <select id="ledgercategoryFilter"><option value="">All</option></select>
- **Units:** <select id="ledgerUnitsFilter"><option value="">All</option></select>
- **Data Type:** <select id="ledgerdatatypeFilter"><option value="">All</option></select>

<div class="table-container">
<table id="ledgerTable">
    <thead>
        <tr>
            <th>Ledger Output Parameters</th>
            <th>Category</th>
            <th>Full Form</th>
            <th>Units</th>
            <th>Description</th>
            <th>Data Type(s)</th>
        </tr>
    </thead>
    <tbody>
        <tr>
            <td>selection</td>
            <td>Scenario</td>
            <td>Selection Number</td>
            <td></td>
            <td>Selection number of vehicle/scenario</td>
            <td>Union[int, str]</td>
        </tr>
        <tr>
            <td>scenario_name</td>
            <td>Scenario</td>
            <td>Scenario Name</td>
            <td></td>
            <td>Name of the selected scenario/vehicle</td>
            <td>str</td>
        </tr>
        <tr>
            <td>model_year</td>
            <td>Scenario</td>
            <td>Vehicle Model Year</td>
            <td></td>
            <td>Current year or Vehicle Model Year</td>
            <td>int</td>
        </tr>
        <tr>
            <td>vehicle_life_yr</td>
            <td>Analysis</td>
            <td>Vehicle Life</td>
            <td>yr</td>
            <td>Number of years to calculate TCO for - generally the expected life of the   vehicle in years</td>
            <td>int</td>
        </tr>
        <tr>
            <td>tco_method</td>
            <td>Analysis</td>
            <td>TCO Calculation Method</td>
            <td></td>
            <td>Choose TCO Calculation method between &#39;DIRECT&#39; and &#39;EFFICIENCY&#39;. &#39;DIRECT&#39;   method uses scenario.downtime_oppy_cost_dol_per_hr to estimate downtime   opportunity costs while &#39;EFFICIENCY&#39; method uses a time-based efficiency   value to implicitly include downtime opportunity costs in the   discounted_tco_dol. Defaults to &#39;DIRECT&#39; if left blank.</td>
            <td>str</td>
        </tr>
        <tr>
            <td>tco_per_year</td>
            <td>TCOCalc</td>
            <td>TCO Calculations Per Year</td>
            <td></td>
            <td>List of dictionary of TCOCalc objects for each year of calculations.   TCOCalc objects contain yearly total costs, and cost components for   CapitalCosts, OperatingCosts, and OpportunityCosts</td>
            <td>list[TCOCalc]</td>
        </tr>
        <tr>
            <td>discounted_total_cap_cost_dol</td>
            <td>CapitalCosts</td>
            <td>Discounted Total Capital Cost</td>
            <td>$</td>
            <td>Discounted Total Capital Costs - Contains MSRP and Tax or Purchasing   Downpayment. It is discounted for zero years, effectively not discounted due   to the cost occuring during the start of lifecycle.</td>
            <td>float</td>
        </tr>
        <tr>
            <td>discounted_total_oper_cost_dol</td>
            <td>OperatingCosts</td>
            <td>Discounted Total Operating Costs</td>
            <td>$</td>
            <td>Discounted Total Operating Costs in dollars - Sum of discounted values of   fuel expense, maintenance, insurance, purchasing, and fueling dwell labor</td>
            <td>float</td>
        </tr>
        <tr>
            <td>discounted_downtime_oppy_cost_dol</td>
            <td>OpportunityCosts</td>
            <td>Discounted Total Opportunity Cost</td>
            <td>$</td>
            <td>Discounted Total Opportunity Costs in dollars- sum of discounted values   of lost payload capacity cost, fueling dwell opportunity cost, and   maintenance &amp; repair downtime opportunity cost</td>
            <td>float</td>
        </tr>
        <tr>
            <td>discounted_tco_dol</td>
            <td>TCO</td>
            <td>Discounted Total Cost of Ownership</td>
            <td>$</td>
            <td>Discounted total cost of ownership in dollars - calculated based on   config.tco_method. For DIRECT method, it is the sum of discounted capital   costs, operating costs, and opportunity costs per year. For EFFICIENCY   method, it is estimated by taking productivity or value of downtime instead   of adding downtime opportunity costs</td>
            <td>float</td>
        </tr>
        <tr>
            <td>cumu_disc_tco_dol_per_yr</td>
            <td>TCO</td>
            <td>Cumulative Discounted Total Cost of Ownership</td>
            <td>$</td>
            <td>Cumulative sum of discounted TCO per year in dollars presented as a   vector of length=vehicle_life_yr</td>
            <td>list[float]</td>
        </tr>
        <tr>
            <td>cumu_tco_dol_per_mi</td>
            <td>TCO</td>
            <td>Cumulative Total Cost of Ownership Per Mile</td>
            <td>$</td>
            <td>Cumulative discounted TCO in dollars divided by cumulative vmt presented   as a vector of length=vehicle_life_yr</td>
            <td>list[float]</td>
        </tr>
        <tr>
            <td>cumu_levelized_tco_dol_per_mi</td>
            <td>TCO</td>
            <td>Cumulative Levelized Total Cost of Ownership Per Mile</td>
            <td>$</td>
            <td>Cumulative discounted TCO in dollars divided by cumulative discounted VMT   presented as a vector of length=vehicle_life_yr</td>
            <td>list[float]</td>
        </tr>
        <tr>
            <td>total_vmt</td>
            <td>Scenario</td>
            <td>Total Vehicle Miles Traveled</td>
            <td>mi</td>
            <td>Sum of Vehicle Miles Traveled (scenario.vmt) for all years in   vehicle_life_yr</td>
            <td>float</td>
        </tr>
        <tr>
            <td>disc_total_vmt</td>
            <td>Scenario</td>
            <td>Discounted Total Vehicle Miles Traveled</td>
            <td>mi</td>
            <td>Sum of scenario.vmt discounted at the rate of   scenario.discount_rate_pct_per_yr</td>
            <td>float</td>
        </tr>
        <tr>
            <td>glider_cost_dol</td>
            <td>CapitalCosts</td>
            <td>Glider Cost</td>
            <td>$</td>
            <td>Estimated glider component cost in dollars - contributes to MSRP</td>
            <td>float</td>
        </tr>
        <tr>
            <td>fuel_converter_cost_dol</td>
            <td>CapitalCosts</td>
            <td>Fuel Converter Cost</td>
            <td>$</td>
            <td>Estimated fuel converter component cost in dollars - contributes to MSRP</td>
            <td>float</td>
        </tr>
        <tr>
            <td>fuel_storage_cost_dol</td>
            <td>CapitalCosts</td>
            <td>Fuel Storage Cost</td>
            <td>$</td>
            <td>Estimated fuel storage component cost in dollars - contributes to MSRP</td>
            <td>float</td>
        </tr>
        <tr>
            <td>motor_control_power_elecs_cost_dol</td>
            <td>CapitalCosts</td>
            <td>Motor Controller &amp; Power Electronics Cost</td>
            <td>$</td>
            <td>Estimated motor and power electronics component cost in dollars -   contributes to MSRP</td>
            <td>float</td>
        </tr>
        <tr>
            <td>plug_cost_dol</td>
            <td>CapitalCosts</td>
            <td>Plugin Charger Cost</td>
            <td>$</td>
            <td>Estimated plugin charger component cost in dollars - contributes to MSRP</td>
            <td>float</td>
        </tr>
        <tr>
            <td>battery_cost_dol</td>
            <td>CapitalCosts</td>
            <td>Battery Cost</td>
            <td>$</td>
            <td>Estimated battery/ESS component cost in dollars - contributes to MSRP</td>
            <td>float</td>
        </tr>
        <tr>
            <td>purchase_tax_dol</td>
            <td>CapitalCosts</td>
            <td>Purchase Tax</td>
            <td>$</td>
            <td>Estimated purchased/excise tax  in   dollars - calculated from MSRP</td>
            <td>float</td>
        </tr>
        <tr>
            <td>msrp_total_dol</td>
            <td>CapitalCosts</td>
            <td>Manufacturer&#39;s Suggester Retail Price</td>
            <td>$</td>
            <td>Estimated manufacturer&#39;s suggested retail price in dollars - calculated   from vehicle component costs</td>
            <td>float</td>
        </tr>
        <tr>
            <td>purchasing_downpayment_dol</td>
            <td>CapitalCosts</td>
            <td>Purchasing Downpayment Cost</td>
            <td>$</td>
            <td>Estimated purchasing downpayment in dollars. For loan or lease, it is   calculated from scenario.purchasing_downpayment_pct and   mrsp_total_dol+purchase_tax. For cash method, it is equal to   mrsp_total_dol+purchase_tax</td>
            <td>float</td>
        </tr>
        <tr>
            <td>residual_cost_dol</td>
            <td>CapitalCosts</td>
            <td>Residual Cost</td>
            <td>$</td>
            <td>Estimated residual cost of vehicle in dollars (residual value is the   negative of residual cost)</td>
            <td>float</td>
        </tr>
        <tr>
            <td>total_fuel_cost_dol</td>
            <td>OperatingCosts</td>
            <td>Total Fuel Operating Cost</td>
            <td>$</td>
            <td>Estimated fuel operating cost in dollars - calculated from energy   consumption and fuel prices</td>
            <td>float</td>
        </tr>
        <tr>
            <td>total_maintenance_cost_dol</td>
            <td>OperatingCosts</td>
            <td>Total Maintenance Operating Cost</td>
            <td>$</td>
            <td>Estimated maintenance operating cost in dollars - calculated from VMT and   scenario.maint_oper_cost_dol_per_mi</td>
            <td>float</td>
        </tr>
        <tr>
            <td>total_purchasing_cost_dol</td>
            <td>OperatingCosts</td>
            <td>Total Purchasing Operating Cost</td>
            <td>$</td>
            <td>Estimated purchasing cost - additional payments due to interest or rent   fee for loan and lease methods respectively</td>
            <td>float</td>
        </tr>
        <tr>
            <td>total_purchasing_payment_dol</td>
            <td>OperatingCosts</td>
            <td>Total Purchasing Payments</td>
            <td>$</td>
            <td>Estimated discounted sum of loan or lease payments (principal and interest for loan; depreciation, rent fee, and tax for lease). This is the purchasing amount included in discounted operating costs and TCO. Zero for the cash method</td>
            <td>float</td>
        </tr>
        <tr>
            <td>insurance_cost_dol</td>
            <td>OperatingCosts</td>
            <td>Insurance Cost</td>
            <td>$</td>
            <td>Estimated insurance cost of vehicle in dollars - estimated from MSRP and   scenario.insurance_rates_pct_per_yr</td>
            <td>float</td>
        </tr>
        <tr>
            <td>fueling_dwell_labor_cost_dol</td>
            <td>OperatingCosts</td>
            <td>Fueling/Charging Dwell Labor Cost</td>
            <td>$</td>
            <td>Estimated labor cost incurred during fueling/charging dwell time</td>
            <td>float</td>
        </tr>
        <tr>
            <td>payload_capacity_cost_dol</td>
            <td>OpportunityCosts</td>
            <td>Lost Payload Capacity Opportunity Cost</td>
            <td>$</td>
            <td>Lost payload capacity opportunity cost in dollars - estimated from   payload_cap_cost_multiplier and estimated tco</td>
            <td>float</td>
        </tr>
        <tr>
            <td>fueling_downtime_oppy_cost_dol</td>
            <td>OpportunityCosts</td>
            <td>Fueling/Charging Dwell Opportunity Cost</td>
            <td>$</td>
            <td>Estimated opportunity cost associated with fueling/charging dwell time</td>
            <td>float</td>
        </tr>
        <tr>
            <td>mr_downtime_oppy_cost_dol</td>
            <td>OpportunityCosts</td>
            <td>Maintenance Downtime Opportunity Cost</td>
            <td>$</td>
            <td>Estimated labor cost incurred during maintenance &amp; repair downtime</td>
            <td>float</td>
        </tr>
        <tr>
            <td>discounted_downtime_oppy_cost_dol</td>
            <td>OpportunityCosts</td>
            <td>Discounted Total Downtime Opportunity Cost</td>
            <td>$</td>
            <td>Estimated discounted opportunity cost for both fueling dwell time and   M&amp;R downtime in dollars - estimation is based on config.TCO_method</td>
            <td>float</td>
        </tr>
        <tr>
            <td>total_fuel_used_gal_ge</td>
            <td>Energy</td>
            <td>Total Fuel Used Gallon Gasoline Equivalent</td>
            <td>GGE</td>
            <td>Estimated total fuel used in gallons gasoline equivalent - estimated from   energy efficiency and distance traveled</td>
            <td>float</td>
        </tr>
        <tr>
            <td>total_fuel_used_gal_de</td>
            <td>Energy</td>
            <td>Total Fuel Used Gallon Diesel Equivalent</td>
            <td>DGE</td>
            <td>Estimated total fuel used in diesels gasoline equivalent - estimated from   energy efficiency and distance traveled</td>
            <td>float</td>
        </tr>
        <tr>
            <td>mpgge</td>
            <td>Energy</td>
            <td>Miles Per Gallon Gasoline Equivalent</td>
            <td>mi/GGE</td>
            <td>Miles per Gallon of Gasoline Equivalent - from drivecycle simulation</td>
            <td>float</td>
        </tr>
        <tr>
            <td>grid_mpgge</td>
            <td>Energy</td>
            <td>Grid Impact Fuel Economy</td>
            <td>mi/GGE</td>
            <td>Miles per Gallon of Gasoline Equivalent effect to grid - mpgge times   charger efficiency</td>
            <td>float</td>
        </tr>
        <tr>
            <td>mpgde</td>
            <td>Energy</td>
            <td>Miles Per Gallon Diesel Equivalent</td>
            <td>mi/DGE</td>
            <td>Miles per Gallon of Diesel Equivalent - from drivecycle simulation</td>
            <td>float</td>
        </tr>
        <tr>
            <td>kwh_per_mi</td>
            <td>Energy</td>
            <td>Energy Per Distance</td>
            <td>km/mi</td>
            <td>Energy spent per mile of operation - estimated from drivecycle simulation</td>
            <td>float</td>
        </tr>
        <tr>
            <td>payload_cap_cost_multiplier</td>
            <td>OpportunityCosts</td>
            <td>Lost Payload Capacity   Multiplier</td>
            <td></td>
            <td>Lost payload capacity opportunity cost factor - represents the   fractionally extra vehicle required to compensate for reduced payload   capacity compared to conventional vehicle - Currently only for Class 8   vehicles</td>
            <td>float</td>
        </tr>
        <tr>
            <td>total_fueling_dwell_time_hr</td>
            <td>OpportunityCosts</td>
            <td>Fueling/Charging Dwell Time</td>
            <td>hr</td>
            <td>Total dwell time of vehicle due to fueling/charging - used to   estimate downtime opportunity cost</td>
            <td>float</td>
        </tr>
        <tr>
            <td>total_mr_downtime_hr</td>
            <td>OpportunityCosts</td>
            <td>Maintenance Downtime</td>
            <td>hr</td>
            <td>Total dwell time of vehicle due to maintenance &amp; repair   (planned, unplanned, and tire replacement) - used to estimate downtime   opportunity cost</td>
            <td>float</td>
        </tr>
        <tr>
            <td>total_downtime_hr</td>
            <td>OpportunityCosts</td>
            <td>Total Downtime</td>
            <td>hr</td>
            <td>Total downtime due to fueling/charging and maintenance events</td>
            <td>float</td>
        </tr>
    </tbody>
</table>
</div>