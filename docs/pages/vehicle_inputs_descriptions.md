# Vehicle Input Descriptions

<div class="filter-container">
    <span class="filter-label"><strong>Filter Options</strong></span>
    <span class="filter-item"><strong>Units:</strong>
        <select id="unitsFilter"><option value="">All</option></select>
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
        <select id="datatypeFilter"><option value="">All</option></select>
    </span>
    <span class="button-container">
        <button id="downloadTemplateBtn">Download Vehicle Template</button>
    </span>
</div>

<div class="table-container">
    <table id="vehicleTable">
    <thead>
        <tr>
            <th>Vehicle Input Parameter</th>
            <th>Full Form</th>
            <th>Units</th>
            <th>Description</th>
            <th>Powertrain</th>
            <th>Data Type(s)</th>
        </tr>
    </thead>
    <tbody>
        <tr>
            <td>alt_eff</td>
            <td>Alternator Efficiency</td>
            <td>%</td>
            <td>Alternator efficiency</td>
            <td>Conv, BEV, HEV, FCEV</td>
            <td>float</td>
        </tr>
        <tr>
            <td>aux_kw</td>
            <td>Auxiliary Load</td>
            <td>kW</td>
            <td>Auxiliary load power, $kW$</td>
            <td>Conv, BEV, HEV, FCEV</td>
            <td>float</td>
        </tr>
        <tr>
            <td>cargo_kg</td>
            <td>Cargo Mass</td>
            <td>kg</td>
            <td>Cargo mass including passengers, $kg$</td>
            <td>Conv, BEV, HEV, FCEV</td>
            <td>float</td>
        </tr>
        <tr>
            <td>chg_eff</td>
            <td>Charging Efficiency</td>
            <td>%</td>
            <td>Charger efficiency</td>
            <td>BEV, HEV, FCEV</td>
            <td>float</td>
        </tr>
        <tr>
            <td>comp_mass_multiplier</td>
            <td>Component Mass Multiplier</td>
            <td></td>
            <td>Component mass multiplier for vehicle mass calculation</td>
            <td>Conv, BEV, HEV, FCEV</td>
            <td>float</td>
        </tr>
        <tr>
            <td>drag_coef</td>
            <td>Aero Drag Coefficient</td>
            <td></td>
            <td>Aerodynamic drag coefficient</td>
            <td>Conv, BEV, HEV, FCEV</td>
            <td>float</td>
        </tr>
        <tr>
            <td>drive_axle_weight_frac</td>
            <td>Drive Axle Weight Fraction</td>
            <td>%</td>
            <td>Fraction of weight on the drive axle while stopped</td>
            <td>Conv, BEV, HEV, FCEV</td>
            <td>float</td>
        </tr>
        <tr>
            <td>ess_base_kg</td>
            <td>ESS Base Mass</td>
            <td>kg</td>
            <td>Traction battery base mass, $kg$</td>
            <td>BEV, HEV, FCEV</td>
            <td>float</td>
        </tr>
        <tr>
            <td>ess_chg_to_fc_max_eff_perc</td>
            <td>ESS Charge to Maximize Fuel Converter Efficiency</td>
            <td>%</td>
            <td>ESS charge effort toward max FC efficiency</td>
            <td>BEV, HEV, FCEV</td>
            <td>float</td>
        </tr>
        <tr>
            <td>ess_dischg_to_fc_max_eff_perc</td>
            <td>ESS Discharge to Maximize Fuel Converter Efficiency</td>
            <td>%</td>
            <td>ESS discharge effort toward max FC efficiency</td>
            <td>BEV, HEV, FCEV</td>
            <td>float</td>
        </tr>
        <tr>
            <td>ess_kg_per_kwh</td>
            <td>ESS Mass per Capacity</td>
            <td>kg/kWh</td>
            <td>Traction battery mass per energy, $\frac{kg}{kWh}$</td>
            <td>BEV, HEV, FCEV</td>
            <td>float</td>
        </tr>
        <tr>
            <td>ess_life_coef_a</td>
            <td>ESS Life Coeficient A</td>
            <td></td>
            <td>Traction battery cycle life coefficient A, see reference</td>
            <td>BEV, HEV, FCEV</td>
            <td>float</td>
        </tr>
        <tr>
            <td>ess_life_coef_b</td>
            <td>ESS Life Coeficient B</td>
            <td></td>
            <td>Traction battery cycle life coefficient B, see reference</td>
            <td>BEV, HEV, FCEV</td>
            <td>float</td>
        </tr>
        <tr>
            <td>ess_max_kw</td>
            <td>ESS Max Power</td>
            <td>kW</td>
            <td>Traction battery maximum power output, $kW$</td>
            <td>BEV, HEV, FCEV</td>
            <td>float</td>
        </tr>
        <tr>
            <td>ess_max_kwh</td>
            <td>ESS Max Capacity</td>
            <td>kWh</td>
            <td>Traction battery energy capacity, $kWh$</td>
            <td>BEV, HEV, FCEV</td>
            <td>float</td>
        </tr>
        <tr>
            <td>ess_round_trip_eff</td>
            <td>ESS Round Trip Efficiency</td>
            <td>%</td>
            <td>Traction battery round-trip efficiency</td>
            <td>BEV, HEV, FCEV</td>
            <td>float</td>
        </tr>
        <tr>
            <td>ess_to_fuel_ok_error</td>
            <td>ESS to Fuel Error Threshold</td>
            <td>%</td>
            <td>Maximum acceptable ratio of change in ESS energy to expended fuel energy (used in hybrid SOC balancing), $\frac{\Delta E_{ESS}}{\Delta E_{fuel}}$</td>
            <td>BEV, HEV, FCEV</td>
            <td>float</td>
        </tr>
        <tr>
            <td>fc_base_kg</td>
            <td>Fuel Converter Base Mass</td>
            <td>kg</td>
            <td>Fuel converter base mass, $kg$</td>
            <td>Conv, HEV, FCEV</td>
            <td>float</td>
        </tr>
        <tr>
            <td>fc_eff_map</td>
            <td>Fuel Converter Efficiency Map</td>
            <td>%</td>
            <td>Fuel converter efficiency map</td>
            <td>Conv, HEV, FCEV</td>
            <td>list [float]</td>
        </tr>
        <tr>
            <td>fc_eff_type</td>
            <td>Fuel Converter Efficiency Type</td>
            <td></td>
            <td>Fuel converter efficiency type, one of [SI, ATKINSON, DIESEL, H2FC, HD_DIESEL] Used for calculating fc_eff_map, and other calculations if H2FC</td>
            <td>Conv, HEV, FCEV</td>
            <td>string</td>
        </tr>
        <tr>
            <td>fc_kw_per_kg</td>
            <td>Fuel Converter Specific Power</td>
            <td>kW/kg</td>
            <td>Fuel converter specific power (power-to-weight ratio), $\frac{kW}{kg}$</td>
            <td>Conv, HEV, FCEV</td>
            <td>float</td>
        </tr>
        <tr>
            <td>fc_max_kw</td>
            <td>Fuel Converter Max Power</td>
            <td>kW</td>
            <td>Fuel converter peak continuous power, $kW$</td>
            <td>Conv, HEV, FCEV</td>
            <td>float</td>
        </tr>
        <tr>
            <td>fc_peak_eff_override</td>
            <td>Fuel Converter Peak Efficiency Override</td>
            <td>%</td>
            <td>Fuel converter efficiency peak override, scales entire curve</td>
            <td>Conv, HEV, FCEV</td>
            <td>float</td>
        </tr>
        <tr>
            <td>fc_pwr_out_perc</td>
            <td>Fuel Converter Power Output Map</td>
            <td>%</td>
            <td>Fuel converter output power percentage map, x values of fc_eff_map</td>
            <td>Conv, HEV, FCEV</td>
            <td>list [float]</td>
        </tr>
        <tr>
            <td>fc_sec_to_peak_pwr</td>
            <td>Fuel Converter Time to Peak Power</td>
            <td>s</td>
            <td>Fuel converter time to peak power, $s$</td>
            <td>Conv, HEV, FCEV</td>
            <td>float</td>
        </tr>
        <tr>
            <td>force_aux_on_fc</td>
            <td>Force Auxiliary Load from Fuel Converter</td>
            <td></td>
            <td>Force auxiliary power load to come from fuel converter</td>
            <td>Conv, HEV, FCEV</td>
            <td>bool</td>
        </tr>
        <tr>
            <td>frontal_area_m2</td>
            <td>Frontal Area</td>
            <td>m^2</td>
            <td>Frontal area, $m^2$</td>
            <td>Conv, BEV, HEV, FCEV</td>
            <td>float</td>
        </tr>
        <tr>
            <td>fs_kwh</td>
            <td>Fuel Storage Energy Capacity</td>
            <td>kWh</td>
            <td>Fuel storage energy capacity, $kWh$</td>
            <td>Conv, HEV, FCEV</td>
            <td>float</td>
        </tr>
        <tr>
            <td>fs_kwh_per_kg</td>
            <td>Fuel Specific Energy</td>
            <td>kWh/kg</td>
            <td>Fuel specific energy, $\frac{kWh}{kg}$</td>
            <td>Conv, HEV, FCEV</td>
            <td>float</td>
        </tr>
        <tr>
            <td>fs_max_kw</td>
            <td>Fuel Storage Max Power Output</td>
            <td>kW</td>
            <td>Fuel storage max power output, $kW$</td>
            <td>Conv, HEV, FCEV</td>
            <td>float</td>
        </tr>
        <tr>
            <td>fs_secs_to_peak_pwr</td>
            <td>Fuel Storage Time to Peak Power</td>
            <td>s</td>
            <td>Fuel storage time to peak power, $s$</td>
            <td>Conv, HEV, FCEV</td>
            <td>float</td>
        </tr>
        <tr>
            <td>glider_kg</td>
            <td>Vehicle Glider Mass</td>
            <td>kg</td>
            <td>Vehicle mass excluding cargo, passengers, and powertrain components, $kg$</td>
            <td>Conv, BEV, HEV, FCEV</td>
            <td>float</td>
        </tr>
        <tr>
            <td>idle_fc_kw</td>
            <td>Fuel Converter Idle Power</td>
            <td>kW</td>
            <td>Fuel converter idle power, $kW$</td>
            <td>Conv, HEV, FCEV</td>
            <td>float</td>
        </tr>
        <tr>
            <td>kw_demand_fc_on</td>
            <td>Power Demand for Fuel Converter ON</td>
            <td>kW</td>
            <td>Power demand above which to require fuel converter on, $kW$</td>
            <td>Conv, HEV, FCEV</td>
            <td>float</td>
        </tr>
        <tr>
            <td>max_accel_buffer_mph</td>
            <td>Max Acceleration Buffer</td>
            <td>MPH</td>
            <td>Speed where the battery reserved for accelerating is zero</td>
            <td>Conv, BEV, HEV, FCEV</td>
            <td>float</td>
        </tr>
        <tr>
            <td>max_accel_buffer_perc_of_useable_soc</td>
            <td>Max Acceleration Buffer as % of Usuable SOC</td>
            <td>%</td>
            <td>Percent of usable battery energy reserved to help accelerate</td>
            <td>Conv, BEV, HEV, FCEV</td>
            <td>float</td>
        </tr>
        <tr>
            <td>max_regen</td>
            <td>Maximum Regenerative Braking Efficiency</td>
            <td>%</td>
            <td>Maximum brake regeneration efficiency</td>
            <td>BEV, HEV, FCEV</td>
            <td>float</td>
        </tr>
        <tr>
            <td>max_soc</td>
            <td>Maximum State of Charge</td>
            <td>%</td>
            <td>Traction battery maximum state of charge</td>
            <td>BEV, HEV, FCEV</td>
            <td>float</td>
        </tr>
        <tr>
            <td>mc_eff_map</td>
            <td>Motor Controller Efficiency Map</td>
            <td>%</td>
            <td>Electric motor efficiency map</td>
            <td>BEV, HEV, FCEV</td>
            <td>list [float]</td>
        </tr>
        <tr>
            <td>mc_max_kw</td>
            <td>Motor Controller Max Power</td>
            <td>kW</td>
            <td>Peak continuous electric motor power, $kW$</td>
            <td>BEV, HEV, FCEV</td>
            <td>float</td>
        </tr>
        <tr>
            <td>mc_pe_base_kg</td>
            <td>Motor Controller Power Electronics Base Mass</td>
            <td>kg</td>
            <td>Motor power electronics base mass, $kg$</td>
            <td>BEV, HEV, FCEV</td>
            <td>float</td>
        </tr>
        <tr>
            <td>mc_pe_kg_per_kw</td>
            <td>Motor Controller Power Electronics Mass Per Power</td>
            <td>kg/kW</td>
            <td>Motor power electronics mass per power output, $\frac{kg}{kW}$</td>
            <td>BEV, HEV, FCEV</td>
            <td>float</td>
        </tr>
        <tr>
            <td>mc_peak_eff_override</td>
            <td>Motor Controller Peak Efficiency Override</td>
            <td>%</td>
            <td>Motor efficiency peak override, scales entire curve</td>
            <td>BEV, HEV, FCEV</td>
            <td>float</td>
        </tr>
        <tr>
            <td>mc_pwr_out_perc</td>
            <td>Motor Controller Power Output Map</td>
            <td>%</td>
            <td>Electric motor output power percentage map, x values of mc_eff_map</td>
            <td>BEV, HEV, FCEV</td>
            <td>list [float]</td>
        </tr>
        <tr>
            <td>mc_sec_to_peak_pwr</td>
            <td>Motor Controller Time to Peak Power</td>
            <td>s</td>
            <td>Electric motor time to peak power, $s$</td>
            <td>BEV, HEV, FCEV</td>
            <td>float</td>
        </tr>
        <tr>
            <td>min_fc_time_on</td>
            <td>Minimum Fuel Converter Time On</td>
            <td>s</td>
            <td>Minimum time fuel converter must be on before shutoff (for HEV, PHEV)</td>
            <td>Conv, HEV, FCEV</td>
            <td>float</td>
        </tr>
        <tr>
            <td>min_soc</td>
            <td>Minimum State of Charge</td>
            <td>%</td>
            <td>Traction battery minimum state of charge</td>
            <td>BEV, HEV, FCEV</td>
            <td>float</td>
        </tr>
        <tr>
            <td>mph_fc_on</td>
            <td>Speed for Fuel Converter to Turn On</td>
            <td>MPH</td>
            <td>Speed at which the fuel converter must turn on, $mph$</td>
            <td>Conv, HEV, FCEV</td>
            <td>float</td>
        </tr>
        <tr>
            <td>num_wheels</td>
            <td>Number of Wheels</td>
            <td></td>
            <td>Number of wheels</td>
            <td>Conv, BEV, HEV, FCEV</td>
            <td>float</td>
        </tr>
        <tr>
            <td>perc_high_acc_buf</td>
            <td>Percentage of High Acceleration SOC Buffer</td>
            <td>%</td>
            <td>Percent SOC buffer for high accessory loads during cycles with long idle time</td>
            <td>Conv, BEV, HEV, FCEV</td>
            <td>float</td>
        </tr>
        <tr>
            <td>scenario_name</td>
            <td>Scenario Name</td>
            <td></td>
            <td>Name of the vehicle and scenario - Includes names</td>
            <td>Conv, BEV, HEV, FCEV</td>
            <td>string</td>
        </tr>
        <tr>
            <td>selection</td>
            <td>Selection Index</td>
            <td></td>
            <td>Name of the vehicle and scenario - Includes names</td>
            <td>Conv, BEV, HEV, FCEV</td>
            <td>int</td>
        </tr>
        <tr>
            <td>stop_start</td>
            <td>Stop/Start Flag</td>
            <td></td>
            <td>Stop/start micro-HEV flag</td>
            <td>Conv, BEV, HEV, FCEV</td>
            <td>bool</td>
        </tr>
        <tr>
            <td>trans_eff</td>
            <td>Transmission Efficiency</td>
            <td>%</td>
            <td>Transmission efficiency</td>
            <td>Conv, BEV, HEV, FCEV</td>
            <td>float</td>
        </tr>
        <tr>
            <td>trans_kg</td>
            <td>Transmission Mass</td>
            <td>kg</td>
            <td>Transmission mass, $kg$</td>
            <td>Conv, BEV, HEV, FCEV</td>
            <td>float</td>
        </tr>
        <tr>
            <td>veh_cg_m</td>
            <td>Vehicle Center of Gravity</td>
            <td>m</td>
            <td>Vehicle center of mass height, $m$ NOTE: positive for FWD, negative for RWD, AWD, 4WD</td>
            <td>Conv, BEV, HEV, FCEV</td>
            <td>float</td>
        </tr>
        <tr>
            <td>veh_override_kg</td>
            <td>Vehicle Mass Override</td>
            <td>kg</td>
            <td>Total vehicle mass, overrides mass calculation, $kg$</td>
            <td>Conv, BEV, HEV, FCEV</td>
            <td>float</td>
        </tr>
        <tr>
            <td>veh_pt_type</td>
            <td>Vehicle Powertrain Type</td>
            <td></td>
            <td>Vehicle powertrain type, one of [CONV, HEV, PHEV, BEV]</td>
            <td>Conv, BEV, HEV, FCEV</td>
            <td>string</td>
        </tr>
        <tr>
            <td>veh_year</td>
            <td>Vehicle Life</td>
            <td>yr</td>
            <td>Number of years to calculate TCO for - generally the expected life of the vehicle in years</td>
            <td>Conv, BEV, HEV, FCEV</td>
            <td>int</td>
        </tr>
        <tr>
            <td>wheel_base_m</td>
            <td>Vehicle wheelbase</td>
            <td>m</td>
            <td>Wheelbase, $m$</td>
            <td>Conv, BEV, HEV, FCEV</td>
            <td>float</td>
        </tr>
        <tr>
            <td>wheel_coef_of_fric</td>
            <td>Wheel Coefficient of Friction</td>
            <td></td>
            <td>Wheel coefficient of friction</td>
            <td>Conv, BEV, HEV, FCEV</td>
            <td>float</td>
        </tr>
        <tr>
            <td>wheel_inertia_kg_m2</td>
            <td>Wheel Inertia</td>
            <td>kg/m^2</td>
            <td>Mass moment of inertia per wheel, $kg \cdot m^2$</td>
            <td>Conv, BEV, HEV, FCEV</td>
            <td>float</td>
        </tr>
        <tr>
            <td>wheel_radius_m</td>
            <td>Wheel Radius</td>
            <td>m</td>
            <td>Wheel radius, $m$</td>
            <td>Conv, BEV, HEV, FCEV</td>
            <td>float</td>
        </tr>
        <tr>
            <td>wheel_rr_coef</td>
            <td>Wheel Rolling Resistance Coefficient</td>
            <td></td>
            <td>Rolling resistance coefficient</td>
            <td>Conv, BEV, HEV, FCEV</td>
            <td>float</td>
        </tr>
    </tbody>
</table>
</div>
