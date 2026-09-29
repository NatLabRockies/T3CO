# Scenario Input Descriptions

<div class="filter-container">
    <span class="filter-label"><strong>Filter Options</strong></span>
    <span class="filter-item"><strong>Units:</strong>
        <select id="scenarioUnitsFilter"><option value="">All</option></select>
    </span>
    <span class="filter-item"><strong>Powertrain:</strong>
        <select id="powertrainFilter">
            <option value="">All</option>
            <option value="Conv">Conv</option>
            <option value="BEV">BEV</option>
            <option value="HEV">HEV</option>
            <option value="FCEV">FCEV</option>
        </select>
    </span>
    <span class="filter-item"><strong>Data Type:</strong>
        <select id="scenariodatatypeFilter"><option value="">All</option></select>
    </span>
    <span class="filter-item"><strong>T3CO Component:</strong>
        <select id="t3coComponentFilter" multiple>
            <option value="General">General</option>
            <option value="RunFASTSim">RunFASTSim</option>
            <option value="TCO">TCO</option>
            <option value="CapitalCosts">CapitalCosts</option>
            <option value="OperatingCosts">OperatingCosts</option>
            <option value="OpportunityCosts">OpportunityCosts</option>
            <option value="Optimization">Optimization</option>
        </select>
    </span>
    <span class="button-container">
        <button id="downloadTemplateBtn">Download Scenario Template</button>
    </span>
</div>

<div class="table-container">
    <table id="scenarioTable">
    <thead>
        <tr>
            <th>Scenario Input Parameter</th>
            <th>Full Form</th>
            <th>Units</th>
            <th>Description</th>
            <th>Powertrains</th>
            <th>T3CO Component</th>
            <th>data_type</th>
        </tr>
    </thead>
    <tbody>
        <tr>
            <td>aero_drag_imp_curve_sel</td>
            <td>Aerodynamic Drag Coefficient Improvement Curve Selection</td>
            <td></td>
            <td>Complete file path to aero drag improvement curve - cost vs drag coefficient</td>
            <td>Conv, BEV, HEV, FCEV</td>
            <td>Optimization</td>
            <td>string</td>
        </tr>
        <tr>
            <td>avg_speed_mph</td>
            <td>Average Trip Speed</td>
            <td>MPH</td>
            <td>Average Speed of Vehicle during the drivecycle</td>
            <td>Conv, BEV, HEV, FCEV</td>
            <td>TCO - Efficiency</td>
            <td>float</td>
        </tr>
        <tr>
            <td>constant_trip_distance_mi</td>
            <td>Trip Distance for each Shift</td>
            <td></td>
            <td>Distance covered during drivecycle</td>
            <td>Conv, BEV, HEV, FCEV</td>
            <td>OpportunityCosts: Payload</td>
            <td>float</td>
        </tr>
        <tr>
            <td>constraint_accel</td>
            <td>Optimization Constraint: Select Acceleration Test</td>
            <td></td>
            <td>Optimization constraint - Acceleration 0-30mph, Acceleration 0-60mph</td>
            <td>Conv, BEV, HEV, FCEV</td>
            <td>Optimization</td>
            <td>bool</td>
        </tr>
        <tr>
            <td>constraint_c_rate</td>
            <td>Optimization Constraint: Select ESS Charge Rate</td>
            <td></td>
            <td>Optimization constraint - Charge Rate</td>
            <td>Conv, BEV, HEV, FCEV</td>
            <td>Optimization</td>
            <td>bool</td>
        </tr>
        <tr>
            <td>constraint_grade</td>
            <td>Optimization Constraint: Select Gradeability Test</td>
            <td></td>
            <td>Optimization constraint - Gradeability 1.25% grade and 6% grade</td>
            <td>Conv, BEV, HEV, FCEV</td>
            <td>Optimization</td>
            <td>bool</td>
        </tr>
        <tr>
            <td>constraint_range</td>
            <td>Optimization Constraint: Select Range</td>
            <td></td>
            <td>Optimization constraint - Range</td>
            <td>BEV, HEV, FCEV</td>
            <td>Optimization</td>
            <td>bool</td>
        </tr>
        <tr>
            <td>constraint_trace_miss_dist_percent_on</td>
            <td>Optimization Constraint: Select Distance Trace Miss</td>
            <td></td>
            <td>Optimization Constraint: Select Distance Trace Miss</td>
            <td>Conv, BEV, HEV, FCEV</td>
            <td>Optimization</td>
            <td>bool</td>
        </tr>
        <tr>
            <td>depreciation_rates_pct_per_yr</td>
            <td>Depreciation Rates per Year</td>
            <td>%/yr</td>
            <td>Depreciation rates per year as a vector. Used in calculating residual values year over year</td>
            <td>Conv, BEV, HEV, FCEV</td>
            <td>CapitalCosts:Residual, OperatingCosts: Purchasing</td>
            <td>list[float]</td>
        </tr>
        <tr>
            <td>discount_rate_pct_per_yr</td>
            <td>Discount Rate</td>
            <td>%/yr</td>
            <td>Discount rate per year as a fraction/year to account for time value of money and alternative investment opportunities. This is applied as a constant rate for TCO cost components</td>
            <td>Conv, BEV, HEV, FCEV</td>
            <td>OperatingCosts, OpportunityCosts</td>
            <td>float</td>
        </tr>
        <tr>
            <td>downtime_oppy_cost_dol_per_hr</td>
            <td>Downtime Opporunity Cost Rate</td>
            <td>$/hr</td>
            <td>Opportunity cost of dwell time for fueling vehicle as dollar per hour</td>
            <td>Conv, BEV, HEV, FCEV</td>
            <td>OpportunityCosts: Fueling Dwell, Maintenance Downtime</td>
            <td>float</td>
        </tr>
        <tr>
            <td>drive_cycle</td>
            <td>Drive Cycles</td>
            <td></td>
            <td>Relative filepath of drivecycle input file(s)  from /t3co/resources/cycles/ folder - accepts single drivecyle path, composite cycles (for example: &#39;[(&quot;EPA_Ph2_rural_interstate_65mph.csv&quot;, .86), (&quot;EPA_Ph2_urban_highway_55mph.csv&quot;, .09), (&quot;EPA_Ph2_transient.csv&quot;, .05)]&#39;), or path to folder containing multiple drivecycles (results in corresponding number of scenarios)</td>
            <td>Conv, BEV, HEV, FCEV</td>
            <td>RunFASTSim</td>
            <td>string</td>
        </tr>
        <tr>
            <td>eng_eff_imp_curve_sel</td>
            <td>Engine Efficiency Improvement Curve Selection</td>
            <td></td>
            <td>Complete file path to engine efficiency improvement curve - cost vs efficiency</td>
            <td>Conv, BEV, HEV, FCEV</td>
            <td>Optimization</td>
            <td>string</td>
        </tr>
        <tr>
            <td>ess_base_cost_dol</td>
            <td>ESS Base Cost</td>
            <td>kW</td>
            <td>Cost of ESSs packaging in dollars that is added to vehicle.ess_max_kwh * scenario.ess_cost_dol_per_kwh to estimate total ESS cost</td>
            <td>BEV, HEV, FCEV</td>
            <td>CapitalCosts: MSRP</td>
            <td>float</td>
        </tr>
        <tr>
            <td>ess_cost_dol_per_kwh</td>
            <td>ESS Cost Per Capacity</td>
            <td>$/kWh</td>
            <td>Cost of ESS in dollars per kWh of capacity</td>
            <td>BEV, HEV, FCEV</td>
            <td>CapitalCosts: MSRP</td>
            <td>float</td>
        </tr>
        <tr>
            <td>ess_max_charging_power_kw</td>
            <td>ESS Max Charging Power</td>
            <td>kW</td>
            <td>Maximum charging power available in kW (infrastructure dependent) for ESS (Energy Storage Systems like Li-ion battery packs) in xEVs</td>
            <td>BEV, HEV, FCEV</td>
            <td>OpportunityCosts: Fueling Dwell</td>
            <td>float</td>
        </tr>
        <tr>
            <td>fc_cng_ice_cost_dol_per_kw</td>
            <td>Fuel Converter CNG Engine Cost Rate</td>
            <td>$/kW</td>
            <td>Cost of CNG engine per kW of max power</td>
            <td>Conv, HEV, FCEV</td>
            <td>CapitalCosts: MSRP</td>
            <td>float</td>
        </tr>
        <tr>
            <td>fc_fuelcell_cost_dol_per_kw</td>
            <td>Fuel Converter Fuel Cell Cost Rate</td>
            <td>$/kW</td>
            <td>Cost of Hydrogen fuel cells per kW of power for FCEVs</td>
            <td>Conv, HEV, FCEV</td>
            <td>CapitalCosts: MSRP</td>
            <td>float</td>
        </tr>
        <tr>
            <td>fc_ice_base_cost_dol</td>
            <td>Fuel Converter IC Engine Base Cost</td>
            <td>$</td>
            <td>Cost of Fuel Convertor baseline that is added to vehicle.fc_max_kw \* scenario.fc_ice_cost_dol_per_kw to estimate total FC cost baseline that is added to vehicle.fc_max_kw \* scenario.fc_ice_cost_dol_per_kw to estimate total FC cost&quot;</td>
            <td>Conv, HEV, FCEV</td>
            <td>CapitalCosts: MSRP</td>
            <td>float</td>
        </tr>
        <tr>
            <td>fc_ice_cost_dol_per_kw</td>
            <td>Fuel Converter IC Engine Cost Rate</td>
            <td>$/kW</td>
            <td>Cost of Internal Combustion Engine per kW of power for Conventional vehicles</td>
            <td>Conv, HEV, FCEV</td>
            <td>CapitalCosts: MSRP</td>
            <td>float</td>
        </tr>
        <tr>
            <td>fdt_available_freetime_hr</td>
            <td>Fueling Dwell Time: Available Freetime for Operator Per Dwell</td>
            <td>hr</td>
            <td>Number of hours of dwell time that do not incur opportunity cost penalty (eg., charging vehicle during scheduled lunch stops)</td>
            <td>Conv, BEV, HEV, FCEV</td>
            <td>OpportunityCosts: Fueling Dwell</td>
            <td>float</td>
        </tr>
        <tr>
            <td>fdt_avg_overhead_hr_per_dwell_hr</td>
            <td>Fueling Dwell Time: Overhead Time for Fueling/Charging per dwell hour</td>
            <td>hr/hr</td>
            <td>Number of hours of overhead time during fueling/charging (eg., detour to gas station, time taken for plugging in charger, etc.)</td>
            <td>Conv, BEV, HEV, FCEV</td>
            <td>OpportunityCosts: Fueling Dwell</td>
            <td>float</td>
        </tr>
        <tr>
            <td>fdt_dwpt_fraction_power_pct</td>
            <td>Fueling Dwell Time: Fraction of Power Charging Onroad</td>
            <td>%</td>
            <td>Fraction of vehicle power consumption through dynamic wireless power transfer</td>
            <td>Conv, BEV, HEV, FCEV</td>
            <td>OpportunityCosts: Fueling Dwell</td>
            <td>float</td>
        </tr>
        <tr>
            <td>fdt_frac_full_charge_bounds</td>
            <td>Fueling Dwell Time: Partial Charging SOC Bounds</td>
            <td>(%,%)</td>
            <td>Lower and Upper bounds for fractional charge as a list [&lt;lower&gt;, &lt;upper&gt;]. &lt;lower&gt; is lowest fraction of charge/tank for a fractional charge at a fueling stop. &lt;upper&gt; is the highest fraction of charge/tank capacity above which it is preferred to rather fill up the batter/tank</td>
            <td>Conv, BEV, HEV, FCEV</td>
            <td>OpportunityCosts: Fueling Dwell</td>
            <td>list[float]</td>
        </tr>
        <tr>
            <td>fdt_num_free_dwell_trips</td>
            <td>Fueling Dwell Time: Number of Free Dwell Trips per Day</td>
            <td></td>
            <td>Number of free trips or overnight charging opportunities that do not incur an opportunity cost penalty</td>
            <td>Conv, BEV, HEV, FCEV</td>
            <td>OpportunityCosts: Fueling Dwell</td>
            <td>float</td>
        </tr>
        <tr>
            <td>fs_cng_cost_dol_per_kwh</td>
            <td>Fuel Storage CNG Cost Rate</td>
            <td>$/kW</td>
            <td>Cost of CNG fuel storage per kWh of max fuel tank capacity</td>
            <td>Conv</td>
            <td>CapitalCosts: MSRP</td>
            <td>float</td>
        </tr>
        <tr>
            <td>fs_cost_dol_per_kwh</td>
            <td>Fuel Storage Liquid Fueling Rate</td>
            <td>gal/min</td>
            <td>Cost of liquid fuel storage tanks per kWh of capacity for liquid fuel like diesel/gasoline</td>
            <td>Conv, HEV, FCEV</td>
            <td>CapitalCosts: MSRP</td>
            <td>float</td>
        </tr>
        <tr>
            <td>fs_fueling_rate_diesel_gpm</td>
            <td>Fuel Storage Cost Rate</td>
            <td>$/kWh</td>
            <td>Fill rate in gallons per min (GPM) for diesel - infrastructure dependent</td>
            <td>Conv, HEV</td>
            <td>OpportunityCosts: Fueling Dwell</td>
            <td>float</td>
        </tr>
        <tr>
            <td>fs_fueling_rate_gasoline_gpm</td>
            <td>Fuel Storage Liquid Fueling Rate</td>
            <td>gal/min</td>
            <td>Fill rate in gallons per min (GPM) for gasoline - infrastructure dependent</td>
            <td>Conv, HEV</td>
            <td>OpportunityCosts: Fueling Dwell</td>
            <td>float</td>
        </tr>
        <tr>
            <td>fs_fueling_rate_kg_per_min</td>
            <td>Fuel Storage Gaseous Fueling Rate</td>
            <td>kg/min</td>
            <td>Fill rate in kg per min (KPM) for gaseous fuels like hydrogen, propane - infrastructure dependent</td>
            <td>FCEV</td>
            <td>OpportunityCosts: Fueling Dwell</td>
            <td>float</td>
        </tr>
        <tr>
            <td>fs_h2_cost_dol_per_kwh</td>
            <td>Fuel Storage Hydrogen Cost Rate</td>
            <td>$/kWh</td>
            <td>Cost of gas fuel storage tanks per kWh of capacity for gaseous fuel like hydrogen</td>
            <td>FCEV</td>
            <td>CapitalCosts: MSRP</td>
            <td>float</td>
        </tr>
        <tr>
            <td>fuel_prices_file</td>
            <td>Fuel Prices Filepath</td>
            <td></td>
            <td>Filepath of FuelPrices.csv either as an absolute path or relative to the resources folder path</td>
            <td>Conv, BEV, HEV, FCEV</td>
            <td>OperatingCosts: Fuel</td>
            <td>string</td>
        </tr>
        <tr>
            <td>fuel_type</td>
            <td>Fuel Type</td>
            <td></td>
            <td>Fuel name - should be one of : [&#39;diesel&#39;, &#39;gasoline&#39;, &#39;hydrogen&#39;, &#39;electricity&#39;, &#39;cng&#39;]. For hybrids, use the primary fuel</td>
            <td>Conv, BEV, HEV, FCEV</td>
            <td>General</td>
            <td>string</td>
        </tr>
        <tr>
            <td>gvwr_credit_kg</td>
            <td>Gross Vehicle Weight Rating Credit</td>
            <td>kg</td>
            <td>Additional allowable weight in kg for advanced vehicles (eg. 2000lb credit for Class 8 BEVs)</td>
            <td>Conv, BEV, HEV, FCEV</td>
            <td>OpportunityCosts: Payload</td>
            <td>float</td>
        </tr>
        <tr>
            <td>gvwr_kg</td>
            <td>Gross Vehicle Weight Rating Limit</td>
            <td>kg</td>
            <td>Gross Vehicle Weight Rating upper limit  in kg for the vehicle&#39;s weight class</td>
            <td>Conv, BEV, HEV, FCEV</td>
            <td>OpportunityCosts: Payload</td>
            <td>float</td>
        </tr>
        <tr>
            <td>insurance_rates_pct_per_yr</td>
            <td>Insurance Rates per Year</td>
            <td>%/yr</td>
            <td>Insurance rates as a percent of MSRP per year as vector with length equal to number of TCO years</td>
            <td>Conv, BEV, HEV, FCEV</td>
            <td>OperatingCosts: Insurance</td>
            <td>list[float]</td>
        </tr>
        <tr>
            <td>knob_max_ess_kwh</td>
            <td>Optimization Bounds: Max ESS capacity</td>
            <td>kWh</td>
            <td>Optimization bounds - maximum ESS capacity in kWh</td>
            <td>BEV, HEV, FCEV</td>
            <td>Optimization</td>
            <td>float</td>
        </tr>
        <tr>
            <td>knob_max_fc_kw</td>
            <td>Optimization Bounds: Max Fuel Convertor Peak Power</td>
            <td>kW</td>
            <td>Optimization bounds - maximum fuel convertor peak power in kW</td>
            <td>Conv, HEV, FCEV</td>
            <td>Optimization</td>
            <td>float</td>
        </tr>
        <tr>
            <td>knob_max_fs_kwh</td>
            <td>Optimization Bounds: Max Fuel Storage Capacity</td>
            <td>kWh</td>
            <td>Optimization bounds - maximum fuel storage capacity in kWh</td>
            <td>Conv, HEV, FCEV</td>
            <td>Optimization</td>
            <td>float</td>
        </tr>
        <tr>
            <td>knob_max_motor_kw</td>
            <td>Optimization Bounds: Max Motor Power</td>
            <td>kW</td>
            <td>Optimization bounds - maximum motor peak power in kW</td>
            <td>BEV, HEV, FCEV</td>
            <td>Optimization</td>
            <td>float</td>
        </tr>
        <tr>
            <td>knob_min_ess_kwh</td>
            <td>Optimization Bounds: Min ESS capacity</td>
            <td>kWh</td>
            <td>Optimization bounds - minimum ESS capacity in kWh</td>
            <td>BEV, HEV, FCEV</td>
            <td>Optimization</td>
            <td>float</td>
        </tr>
        <tr>
            <td>knob_min_fc_kw</td>
            <td>Optimization Bounds: Min Fuel Convertor Peak Power</td>
            <td>kW</td>
            <td>Optimization bounds - minimum fuel convertor peak power in kW</td>
            <td>Conv, HEV, FCEV</td>
            <td>Optimization</td>
            <td>float</td>
        </tr>
        <tr>
            <td>knob_min_fs_kwh</td>
            <td>Optimization Bounds: Min Fuel Storage Capacity</td>
            <td>kWh</td>
            <td>Optimization bounds - minimum fuel storage capacity in kWh</td>
            <td>Conv, HEV, FCEV</td>
            <td>Optimization</td>
            <td>float</td>
        </tr>
        <tr>
            <td>knob_min_motor_kw</td>
            <td>Optimization Bounds: Min Motor Power</td>
            <td>kW</td>
            <td>Optimization bounds - minimum motor peak power in kW</td>
            <td>BEV, HEV, FCEV</td>
            <td>Optimization</td>
            <td>float</td>
        </tr>
        <tr>
            <td>labor_rate_dol_per_hr</td>
            <td>Labor Rate</td>
            <td>$/hr</td>
            <td>Labor Rate for dollars per hour of vehicle operation</td>
            <td>Conv, BEV, HEV, FCEV</td>
            <td>OperatingCosts: Fueling Dwell Labor</td>
            <td>float</td>
        </tr>
        <tr>
            <td>lw_imp_curve_sel</td>
            <td>Light Weighting Improvement Curve Selection</td>
            <td></td>
            <td>Complete file path to light weighting improvement curve - cost vs weight reduced</td>
            <td>Conv, BEV, HEV, FCEV</td>
            <td>Optimization</td>
            <td>string</td>
        </tr>
        <tr>
            <td>maint_oper_cost_dol_per_mi</td>
            <td>Maintenance Operating Cost Per Distance</td>
            <td>$/mi</td>
            <td>Vehicle maintenance operating cost in dollars per mile traveled as vector of length equal to number of TCO years</td>
            <td>Conv, BEV, HEV, FCEV</td>
            <td>OperatingCosts: Maintenance</td>
            <td>list[float]</td>
        </tr>
        <tr>
            <td>markup_pct</td>
            <td>Mark-up Percentage</td>
            <td>%</td>
            <td>Markup on price of vehicle as percentage of MSRP (eg., 1.20 means 20% markup_pct on MSRP)</td>
            <td>Conv, BEV, HEV, FCEV</td>
            <td>CapitalCosts: MSRP</td>
            <td>float</td>
        </tr>
        <tr>
            <td>max_time_0_to_30mph_at_gvwr_s</td>
            <td>Acceleration Test: Max Time for 0-30MPH Fully Laden</td>
            <td>s</td>
            <td>Maximum time taken by optimized vehicle (at GVWR weight limit) to accelerate from 0 to 30 mph - acceleration test</td>
            <td>Conv, BEV, HEV, FCEV</td>
            <td>Optimization</td>
            <td>float</td>
        </tr>
        <tr>
            <td>max_time_0_to_60mph_at_gvwr_s</td>
            <td>Acceleration Test: Max Time for 0-60MPH Fully Laden</td>
            <td>s</td>
            <td>Maximum time taken by optimized vehicle (at GVWR weight limit) to accelerate from 0 to 60 mph - acceleration test</td>
            <td>Conv, BEV, HEV, FCEV</td>
            <td>Optimization</td>
            <td>float</td>
        </tr>
        <tr>
            <td>min_speed_at_1p25pct_grade_in_5min_mph</td>
            <td>Gradeability Test: Min Speed Achieved at 1.25=% grade in 5 mins</td>
            <td>MPH</td>
            <td>Minimum speed in miles/hour for the optimized vehicle to attain from 0 mph in 5 mins for a 1.25 percent gradeability test</td>
            <td>Conv, BEV, HEV, FCEV</td>
            <td>Optimization</td>
            <td>float</td>
        </tr>
        <tr>
            <td>min_speed_at_6pct_grade_in_5min_mph</td>
            <td>Gradeability Test: Min Speed Achieved at 6% grade in 5 mins</td>
            <td>MPH</td>
            <td>Minimum speed in miles/hour for the optimized vehicle to attain from 0 mph in 5 mins for a 6 percent gradeability test</td>
            <td>Conv, BEV, HEV, FCEV</td>
            <td>Optimization</td>
            <td>float</td>
        </tr>
        <tr>
            <td>model_year</td>
            <td>Vehicle Model Year</td>
            <td></td>
            <td>Vehicle model year</td>
            <td>Conv, BEV, HEV, FCEV</td>
            <td>General</td>
            <td>int</td>
        </tr>
        <tr>
            <td>mpgge</td>
            <td>Miles Per Gallon Gasoline Equivalent</td>
            <td>mi/GGE</td>
            <td>Miles Per Gallon Gasoline Equivalent given as an exogenous input to Energy if desired, and is directly used in OperatingCosts calculations. Should be provided along with primary_fuel_range_mi. If left blank, FASTSim or other powertrain simulation runs within T3CO to estimate this value.</td>
            <td>Conv, BEV, HEV, FCEV</td>
            <td>OperatingCosts: Fuel</td>
            <td>float</td>
        </tr>
        <tr>
            <td>mr_avg_tire_life_mi</td>
            <td>Maintenance &amp; Repair Downtime: Average Tire Life</td>
            <td>mi</td>
            <td>Average life of tire in miles after which a tire replacement event takes place</td>
            <td>Conv, BEV, HEV, FCEV</td>
            <td>OpportunityCosts: Maintenance Downtime</td>
            <td>float</td>
        </tr>
        <tr>
            <td>mr_planned_downtime_hr_per_yr</td>
            <td>Maintenance &amp; Repair Downtime: Planned Downtime per Year</td>
            <td>hr/yr</td>
            <td>Regular/planned maintenance time in hours per year</td>
            <td>Conv, BEV, HEV, FCEV</td>
            <td>OpportunityCosts: Maintenance Downtime</td>
            <td>float</td>
        </tr>
        <tr>
            <td>mr_tire_replace_downtime_hr_per_event</td>
            <td>Maintenance &amp; Repair Downtime: Tire Replacement Downtime per Event</td>
            <td>hr/event</td>
            <td>Downtime hours per tire replacement event</td>
            <td>Conv, BEV, HEV, FCEV</td>
            <td>OpportunityCosts: Maintenance Downtime</td>
            <td>float</td>
        </tr>
        <tr>
            <td>mr_unplanned_downtime_hr_per_mi</td>
            <td>Maintenance &amp; Repair Downtime: Unplanned Downtime per Distance</td>
            <td>hr/mi</td>
            <td>Unplanned maintenance time per mile traveled as a vector with length equal to number of TCO years</td>
            <td>Conv, BEV, HEV, FCEV</td>
            <td>OpportunityCosts: Maintenance Downtime</td>
            <td>list[float]</td>
        </tr>
        <tr>
            <td>msrp_total_dol</td>
            <td>MSRP Intput</td>
            <td>$</td>
            <td>Manufacturer&#39;s Suggested Retail Price provided as an input override if required. This bypasses the CapitalCosts MSRP breakdown calculations and hence requires fewer inputs from the Vehicle model</td>
            <td>Conv, BEV, HEV, FCEV</td>
            <td>CapitalCosts: MSRP</td>
            <td>float</td>
        </tr>
        <tr>
            <td>objective_tco</td>
            <td>Optimization Objective: Total Cost of Ownership</td>
            <td></td>
            <td>Boolean switch for minimizing TCO as optimization objective</td>
            <td>Conv, BEV, HEV, FCEV</td>
            <td>Optimization</td>
            <td>bool</td>
        </tr>
        <tr>
            <td>pe_mc_base_cost_dol</td>
            <td>Power Electronics and Motor Controller Base Cost</td>
            <td>$</td>
            <td>Cost of Power Electronics and Motor Controllers baseline that is added to vehicle.mc_max_kw * scenario.pe_mc_cost_dol_per_kw to estimate total PE&amp;MC cost</td>
            <td>BEV, HEV, FCEV</td>
            <td>CapitalCosts: MSRP</td>
            <td>float</td>
        </tr>
        <tr>
            <td>pe_mc_cost_dol_per_kw</td>
            <td>Power Electronics and Motor Controller Cost Rate</td>
            <td>$/kW</td>
            <td>Cost of Power Electronics and Motor Controllers in dollars per kW</td>
            <td>BEV, HEV, FCEV</td>
            <td>CapitalCosts: MSRP</td>
            <td>float</td>
        </tr>
        <tr>
            <td>plf_ref_veh_empty_mass_kg</td>
            <td>Payload Loss Factor: Reference Vehicle Empty Mass</td>
            <td>kg</td>
            <td>Reference vehicle empty weight in kg for lost payload capacity opportunity cost calculation</td>
            <td>Conv, BEV, HEV, FCEV</td>
            <td>OpportunityCosts: Payload</td>
            <td>float</td>
        </tr>
        <tr>
            <td>plf_weight_distribution_file</td>
            <td>Payload Loss Factor: Weight Distribution Input Filepath</td>
            <td></td>
            <td>Filepath of Weight Distribution file (tractorweightvars.csv) either as an absolute path or relative to the resources folder path</td>
            <td>Conv, BEV, HEV, FCEV</td>
            <td>OpportunityCosts: Payload</td>
            <td>string</td>
        </tr>
        <tr>
            <td>plug_base_cost_dol</td>
            <td>Plugin Charger Base Cost</td>
            <td>dol</td>
            <td>Cost of plugin connections on  certain xEVs</td>
            <td>BEV, HEV, FCEV</td>
            <td>CapitalCosts: MSRP</td>
            <td>float</td>
        </tr>
        <tr>
            <td>primary_fuel_range_mi</td>
            <td>Primary Range of the Vehicle</td>
            <td>mi</td>
            <td>Primary Range of the Vehicle given as an exogenous input to Energy if desired, and is directly used in OperatingCosts and OpportunityCosts calculations.Should be provided along with mpgge. If left blank, FASTSim or other powertrain simulation runs within T3CO to estimate this value.</td>
            <td>Conv, BEV, HEV, FCEV</td>
            <td>OperatingCosts: Fuel, OpportunityCosts: Fueling Dwell</td>
            <td>float</td>
        </tr>
        <tr>
            <td>purchasing_down_payment_pct</td>
            <td>Purchasing Down-Payment Percentage</td>
            <td>%</td>
            <td>Purchasing downpayment percentage for leasing or loan, represented as a fraction of MSRP+Tax</td>
            <td>Conv, BEV, HEV, FCEV</td>
            <td>OperatingCosts: Purchasing</td>
            <td>float</td>
        </tr>
        <tr>
            <td>purchasing_interest_apr_pct_per_yr</td>
            <td>Purchasing Annual Interest Rate/APR</td>
            <td>%/yr</td>
            <td>Purchasing: Annual Interest rate or APR for loan/lease method representated as a scalar fraction</td>
            <td>Conv, BEV, HEV, FCEV</td>
            <td>OperatingCosts: Purchasing</td>
            <td>float</td>
        </tr>
        <tr>
            <td>purchasing_method</td>
            <td>Purchasing Method Selection</td>
            <td></td>
            <td>Purchasing: Purchasing Method selection, should be one of [&quot;cash&quot;, &quot;loan&quot;, &quot;lease&quot;]</td>
            <td>Conv, BEV, HEV, FCEV</td>
            <td>OperatingCosts: Purchasing</td>
            <td>string</td>
        </tr>
        <tr>
            <td>purchasing_payment_frequency_months</td>
            <td>Purchasing Payment Frequency</td>
            <td>months</td>
            <td>Purchasing: Payment frequency in number of months for loan method. Defaults to 1 for lease</td>
            <td>Conv, BEV, HEV, FCEV</td>
            <td>OperatingCosts: Purchasing</td>
            <td>float</td>
        </tr>
        <tr>
            <td>purchasing_term_yr</td>
            <td>Purchasing Loan/Lease Term</td>
            <td>years</td>
            <td>Purchasing: Purchasing Term in number of years for lease and loan method</td>
            <td>Conv, BEV, HEV, FCEV</td>
            <td>OperatingCosts: Purchasing</td>
            <td>float</td>
        </tr>
        <tr>
            <td>region</td>
            <td>Fuel Price Region/Model</td>
            <td></td>
            <td>Region name or US zipcode used to look up fuel prices. If set to a 5-digit US zipcode (e.g. 90210) and the Config did not already resolve EIA prices, T3CO fetches region-specific fuel price projections from the EIA AEO API. Otherwise the value is used as a key into FuelPrices.csv.</td>
            <td>Conv, BEV, HEV, FCEV</td>
            <td>OperatingCosts: Fuel</td>
            <td>string</td>
        </tr>
        <tr>
            <td>scenario_name</td>
            <td>Scenario Name</td>
            <td></td>
            <td>Name of the vehicle and scenario - Includes names</td>
            <td>Conv, BEV, HEV, FCEV</td>
            <td>General</td>
            <td>string</td>
        </tr>
        <tr>
            <td>selection</td>
            <td>Selection Index</td>
            <td></td>
            <td>Name of the vehicle and scenario - Includes names</td>
            <td>Conv, BEV, HEV, FCEV</td>
            <td>General</td>
            <td>string</td>
        </tr>
        <tr>
            <td>shifts_per_year</td>
            <td>Number of Shifts per Year </td>
            <td></td>
            <td>Selection number that is used to match with the corresponding vehicles on the Demo_FY22_vehicle_assumptions.csv file</td>
            <td>Conv, BEV, HEV, FCEV</td>
            <td>OpportunityCosts: Fueling Dwell</td>
            <td>int</td>
        </tr>
        <tr>
            <td>skip_opt</td>
            <td>Switch to Skip Optimization</td>
            <td></td>
            <td>Boolean switch for skipping the optimization module</td>
            <td>Conv, BEV, HEV, FCEV</td>
            <td>Optimization</td>
            <td>bool</td>
        </tr>
        <tr>
            <td>soc_norm_init_for_accel_pct</td>
            <td>Initial SOC override for Acceleration Test</td>
            <td>%</td>
            <td>Initial normalized SOC for acceleration test (only PHEV)</td>
            <td>BEV, HEV, FCEV</td>
            <td>Optimization</td>
            <td>float</td>
        </tr>
        <tr>
            <td>soc_norm_init_for_grade_pct</td>
            <td>Initial SOC override for Gradeability Test</td>
            <td>%</td>
            <td>Initial normalized SOC for gradeability test (only PHEV)</td>
            <td>BEV, HEV, FCEV</td>
            <td>Optimization</td>
            <td>float</td>
        </tr>
        <tr>
            <td>target_range_mi</td>
            <td>Target Vehicle Range</td>
            <td>mi</td>
            <td>Target range in miles to be achieved by the optimized vehicle</td>
            <td>Conv, BEV, HEV, FCEV</td>
            <td>Optimization</td>
            <td>float</td>
        </tr>
        <tr>
            <td>tax_rate_pct</td>
            <td>Tax Rate</td>
            <td>%</td>
            <td>Registration and other taxes during time of purchase as percent on the MSRP (eg., 0.125 means 12.5% of MSRP)</td>
            <td>Conv, BEV, HEV, FCEV</td>
            <td>CapitalCosts: Purchase Tax</td>
            <td>float</td>
        </tr>
        <tr>
            <td>trace_miss_dist_percent</td>
            <td>Distance Trace Miss Percentage Threshold</td>
            <td>%</td>
            <td>Distance trace miss percentage threshold for optimization</td>
            <td>Conv, BEV, HEV, FCEV</td>
            <td>Optimization</td>
            <td>float</td>
        </tr>
        <tr>
            <td>use_config</td>
            <td>Flag to Use Config Overrides</td>
            <td></td>
            <td>Boolean switch for using config file as override for scenario attributes</td>
            <td>Conv, BEV, HEV, FCEV</td>
            <td>General</td>
            <td>bool</td>
        </tr>
        <tr>
            <td>vehicle_glider_cost_dol</td>
            <td>Vehicle Glider Cost</td>
            <td>$</td>
            <td>Cost of glider (vehicle without powertrain) in dollars</td>
            <td>Conv, BEV, HEV, FCEV</td>
            <td>CapitalCosts: MSRP</td>
            <td>float</td>
        </tr>
        <tr>
            <td>vehicle_life_yr</td>
            <td>Vehicle Life</td>
            <td>yr</td>
            <td>Number of years to calculate TCO for - generally the expected life of the vehicle in years</td>
            <td>Conv, BEV, HEV, FCEV</td>
            <td>General</td>
            <td>int</td>
        </tr>
        <tr>
            <td>vmt</td>
            <td>Vehicle Miles Traveled per year</td>
            <td>mi</td>
            <td>Vehicle Miles Traveled as an array/list with length&gt;=vehicle_life_yr</td>
            <td>Conv, BEV, HEV, FCEV</td>
            <td>General</td>
            <td>list[int]</td>
        </tr>
        <tr>
            <td>vocation</td>
            <td>Vehicle Vocation Type</td>
            <td></td>
            <td>Vocation of the vehicle - only for user reference</td>
            <td>Conv, BEV, HEV, FCEV</td>
            <td>General</td>
            <td>string</td>
        </tr>
    </tbody>
</table>
</div>
