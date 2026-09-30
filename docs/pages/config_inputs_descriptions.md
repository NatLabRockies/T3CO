# Config Input Parameters

<div class="filter-container">
    <span class="filter-label"><strong>Filter Options</strong></span>
    <span class="filter-item"><strong>Units:</strong>
        <select id="configUnitsFilter"><option value="">All</option></select>
    </span>
    <span class="filter-item"><strong>Data Type:</strong>
        <select id="configdatatypeFilter"><option value="">All</option></select>
    </span>
    <span class="button-container">
        <button id="downloadTemplateBtn">Download Config Template</button>
    </span>
</div>

<div class="table-container">
    <table id="configTable">
        <thead>
            <tr>
                <th>Config Input Parameter</th>
                <th>Full Form</th>
                <th>Units</th>
                <th>Description</th>
                <th>Data Type</th>
            </tr>
        </thead>
    <tbody>
        <tr>
            <td>analysis_id</td>
            <td>Analysis Index</td>
            <td></td>
            <td>Index for managing T3CO analyses   or runs</td>
            <td>int</td>
        </tr>
        <tr>
            <td>analysis_name</td>
            <td>Analysis Name</td>
            <td></td>
            <td>Name of T3CO Analysis for user&#39;s   reference</td>
            <td>string</td>
        </tr>
        <tr>
            <td>vehicle_file</td>
            <td>Vehicle Filepath</td>
            <td></td>
            <td>Filepath to vehicle input file   either absolute or relative to /resources/ folder</td>
            <td>string</td>
        </tr>
        <tr>
            <td>scenario_file</td>
            <td>Scenario Filepath</td>
            <td></td>
            <td>Filepath to scenario input file   either absolute or relative to /resources/ folder</td>
            <td>string</td>
        </tr>
        <tr>
            <td>dst_dir</td>
            <td>Destination Directory</td>
            <td></td>
            <td>Filepath to results destination   directory either absolute or relative to /resources/ folder</td>
            <td>string</td>
        </tr>
        <tr>
            <td>summary_group_by</td>
            <td>Results Summary Grouping</td>
            <td></td>
            <td>Optional result columns to group by, e.g. vehicle_veh_pt_type; scenario_vehicle_class. When set, the sweep also writes summary_&lt;results file&gt;.csv next to the results with run counts, medians and VMT-weighted means per group. Leave blank to skip.</td>
            <td>string or list</td>
        </tr>
        <tr>
            <td>selections</td>
            <td>Selections List</td>
            <td></td>
            <td>List of selections from   vehicle/scenario files to include in the analysis. Takes input as an integer   or list of integers. &#39;-1&#39; makes T3CO run all vehicles in the vehicle file</td>
            <td>int/list</td>
        </tr>
        <tr>
            <td>vehicle_life_yr</td>
            <td>Vehicle Life</td>
            <td>yr</td>
            <td>Override number of TCO years for   all selections.. If left blank, T3CO uses selection specific vehicle_life_yr   from scenario file</td>
            <td>int</td>
        </tr>
        <tr>
            <td>ess_max_charging_power_kw</td>
            <td>ESS Max Charging Power Override</td>
            <td>kW</td>
            <td>Override ESS max charging power   for all selections. If left blank, T3CO uses selection specific   ess_max_charging_power_kw from scenario file</td>
            <td>float</td>
        </tr>
        <tr>
            <td>fs_fueling_rate_kg_per_min</td>
            <td>Fuel Storage Gaseous Fueling Rate</td>
            <td>kg/min</td>
            <td>Override gaseous fueling fill   rate for all selections. If left blank, T3CO uses selection specific   fs_fueling_rate_kg_per_min from scenario file</td>
            <td>float</td>
        </tr>
        <tr>
            <td>fs_fueling_rate_gasoline_gpm</td>
            <td>Fuel Storage Gasoline Fueling Rate</td>
            <td>gal/min</td>
            <td>Override gasoline liquid fueling   fill rate for all selections. If left blank, T3CO uses selection specific   fs_fueling_rate_gasoline_gpm from scenario file</td>
            <td>float</td>
        </tr>
        <tr>
            <td>fs_fueling_rate_diesel_gpm</td>
            <td>Fuel Storage Diesel Fueling Rate</td>
            <td>gal/min</td>
            <td>Override diesel liquid fueling   fill rate for all selections. If left blank, T3CO uses selection specific   fs_fueling_rate_diesel_gpm from scenario file</td>
            <td>float</td>
        </tr>
        <tr>
            <td>algorithms</td>
            <td>Optimization Algorithms</td>
            <td></td>
            <td>Algorithm for pymoo   optimization. Select from    [&quot;NSGA2&quot;, &quot;PatternSearch&quot;, &quot;NelderMead&quot;, &quot;PSO&quot;]</td>
            <td>string</td>
        </tr>
        <tr>
            <td>pop_size</td>
            <td>Population Size</td>
            <td></td>
            <td>Population size for the NSGA2 algorithm. Default: 25.</td>
            <td>int</td>
        </tr>
        <tr>
            <td>x_tol</td>
            <td>Design Space Tolerance</td>
            <td></td>
            <td>Convergence tolerance on design variables for optimization termination. Default: 0.001.</td>
            <td>float</td>
        </tr>
        <tr>
            <td>f_tol</td>
            <td>Objective Tolerance</td>
            <td></td>
            <td>Convergence tolerance on objective function values for optimization termination. Default: 0.001.</td>
            <td>float</td>
        </tr>
        <tr>
            <td>n_max_gen</td>
            <td>Maximum Generations</td>
            <td></td>
            <td>Maximum number of generations before optimization terminates. Default: 1000.</td>
            <td>int</td>
        </tr>
        <tr>
            <td>n_last</td>
            <td>Convergence Window</td>
            <td></td>
            <td>Number of recent generations that must all satisfy x_tol and f_tol before the optimization stops. Default when the column is absent: 5.</td>
            <td>int</td>
        </tr>
        <tr>
            <td>nth_gen</td>
            <td>Convergence Check Interval</td>
            <td></td>
            <td>Check convergence every nth_gen generations. Default when the column is absent: 1.</td>
            <td>int</td>
        </tr>
        <tr>
            <td>n_processes</td>
            <td>Optimizer Processes</td>
            <td></td>
            <td>Number of processes used to evaluate each generation&#x27;s designs in parallel. Ignored under --run-multi, where each selection already runs in its own worker. Default when the column is absent: 9.</td>
            <td>int</td>
        </tr>
        <tr>
            <td>parallel</td>
            <td>Parallel Design Evaluation</td>
            <td></td>
            <td>TRUE evaluates each generation&#x27;s designs in a process pool of n_processes; FALSE evaluates them one at a time. Results are identical either way. Default when the column is absent: TRUE.</td>
            <td>bool</td>
        </tr>
        <tr>
            <td>lw_imp_curves</td>
            <td>Lightweighting Improvement Curves Filepath</td>
            <td></td>
            <td>Filepath to lightweighting   improvement cost curve either absolute or relative to /resources/ folder</td>
            <td>string</td>
        </tr>
        <tr>
            <td>eng_eff_imp_curves</td>
            <td>Engine Efficiency Improvement Curves Filepath</td>
            <td></td>
            <td>Filepath to engine efficiency   improvement cost curve either absolute or relative to /resources/ folder</td>
            <td>string</td>
        </tr>
        <tr>
            <td>aero_drag_imp_curves</td>
            <td>Aero Drag Coefficient Improvement   Curves Filepath</td>
            <td></td>
            <td>Filepath to aerodynamic drag   coefficient improvement cost curve either absolute or relative to /resources/   folder</td>
            <td>string</td>
        </tr>
        <tr>
            <td>lw_imp_curve_sel</td>
            <td>Lightweighting Improvement Curve   Selection Override</td>
            <td></td>
            <td>Override selection of light   weighting improvement curve from lw_imp_curves file for all selections</td>
            <td>string</td>
        </tr>
        <tr>
            <td>eng_eff_imp_curve_sel</td>
            <td>Engine Efficiency Improvement Curve   Selection Override</td>
            <td></td>
            <td>Override selection of engine   efficiency improvement curve from eng_eff_imp_curves file for all selections</td>
            <td>string</td>
        </tr>
        <tr>
            <td>aero_drag_imp_curve_sel</td>
            <td>Aero Drag Coefficient Improvement   Curve Selection Override</td>
            <td></td>
            <td>Override selection of   aerodynamic drag improvement curve from aero_drag_imp_curves file for all   selections</td>
            <td>string</td>
        </tr>
        <tr>
            <td>skip_all_opt</td>
            <td>Skip All Optimization</td>
            <td></td>
            <td>Boolean switch to override skip   optimization for all selections</td>
            <td>bool</td>
        </tr>
        <tr>
            <td>constraint_range</td>
            <td>Optimization Constraint: Range</td>
            <td></td>
            <td>Override boolean switch for   optimization range constraint for all selections - if left blank, T3CO uses   selection specific switch</td>
            <td>bool</td>
        </tr>
        <tr>
            <td>constraint_accel</td>
            <td>Optimization Constraint: Acceleration Test</td>
            <td></td>
            <td>Override boolean switch for   optimization acceleration constraint for all selections- if left blank, T3CO   uses selection specific switch</td>
            <td>bool</td>
        </tr>
        <tr>
            <td>constraint_grade</td>
            <td>Optimization Constraint: Gradeability Test</td>
            <td></td>
            <td>Override boolean switch for   optimization gradeability constraint for all selections- if left blank, T3CO   uses selection specific switch</td>
            <td>bool</td>
        </tr>
        <tr>
            <td>objective_tco</td>
            <td>Optimization Objective: Total Cost of Ownership</td>
            <td></td>
            <td>Override boolean switch for   optimization objective as TCO for all selections- if left blank, T3CO uses   selection specific switch</td>
            <td>bool</td>
        </tr>
        <tr>
            <td>constraint_c_rate</td>
            <td>Optimization Constraint: Charge Rate</td>
            <td></td>
            <td>Override boolean switch for   optimization charge rate constraint for all selections- if left blank, T3CO   uses selection specific switch</td>
            <td>bool</td>
        </tr>
        <tr>
            <td>constraint_trace_miss_dist_percent_on</td>
            <td>Optimization Constraint: Distance Trace Miss</td>
            <td></td>
            <td>Override boolean switch for   optimization distance trace miss percentage for all selections- if left   blank, T3CO uses selection specific switch</td>
            <td>bool</td>
        </tr>
        <tr>
            <td>activate_tco_payload_cap_cost_multiplier</td>
            <td>Override Switch to Calculate Payload   Capacity Cost Multiplier</td>
            <td></td>
            <td>Override boolean switch for lost   payload capacity opportunity cost calculations- if left blank, T3CO uses   selection specific switch</td>
            <td>bool</td>
        </tr>
        <tr>
            <td>activate_tco_fueling_dwell_time_cost</td>
            <td>Override Switch to Calculate   Fueling/Charging Dwell Time</td>
            <td></td>
            <td>Override boolean switch for   fueling dwell time opportunity cost calculations- if left blank, T3CO uses   selection specific switch</td>
            <td>bool</td>
        </tr>
        <tr>
            <td>fdt_frac_full_charge_bounds</td>
            <td>Fueling Dwell Time: Fractional   Charge SOC Bounds Override</td>
            <td></td>
            <td>Override fraction of lower and   upper bounds for fractional charge- if left blank, T3CO uses selection   specific switch</td>
            <td>list</td>
        </tr>
        <tr>
            <td>activate_mr_downtime_cost</td>
            <td>Override Switch to Calculate   Maintenance &amp; Repair Downtime</td>
            <td></td>
            <td>Override boolean switch for   maintenance and repair downtime opportunity cost calculations- if left blank,   T3CO uses selection specific switch</td>
            <td>bool</td>
        </tr>
        <tr>
            <td>drive_cycle</td>
            <td>Drive Cycle</td>
            <td></td>
            <td>Path to a single drive cycle file or a folder of drive cycle files (for Batch Mode). Either absolute or relative to /resources/ folder. If left blank, T3CO uses the scenario-level drive cycle.</td>
            <td>string</td>
        </tr>
        <tr>
            <td>cost_toggles_file</td>
            <td>Cost Toggles Filepath</td>
            <td></td>
            <td>Filepath to a JSON file containing cost model toggles (e.g. <code>eia_fuel_prices</code>). Defaults to <code>resources/inputs/cost_toggles.json</code>.</td>
            <td>string</td>
        </tr>
        <tr>
            <td>TCO_method</td>
            <td>TCO Calculation Method</td>
            <td></td>
            <td>Method for computing discounted TCO. Accepted values: <code>DIRECT</code> (default) or <code>EFFICIENCY</code>.</td>
            <td>string</td>
        </tr>
        <tr>
            <td>purchasing_method</td>
            <td>Purchasing Method</td>
            <td></td>
            <td>Vehicle purchasing method. Accepted values: <code>cash</code> (default), <code>loan</code>, or <code>lease</code>.</td>
            <td>string</td>
        </tr>
        <tr>
            <td>fuel_prices_file</td>
            <td>Fuel Prices Filepath</td>
            <td></td>
            <td>Filepath to auxiliary fuel prices CSV file, either absolute or relative to /resources/ folder</td>
            <td>string</td>
        </tr>
        <tr>
            <td>region</td>
            <td>Fuel Price Region or Zipcode</td>
            <td></td>
            <td>Region identifier for fuel prices. If set to a 5-digit US zipcode (e.g. 90210) and the <code>eia_fuel_prices</code> toggle is enabled, T3CO fetches fuel price projections from the EIA AEO API for the corresponding census division. If left blank, T3CO uses the scenario-level region to look up prices from the static FuelPrices.csv file.</td>
            <td>string/int</td>
        </tr>
        <tr>
            <td>eia_aeo_year</td>
            <td>EIA AEO Publication Year</td>
            <td></td>
            <td>AEO publication year to query from the EIA API (e.g. &quot;2023&quot;, &quot;2025&quot;). If left blank, T3CO auto-discovers the latest available AEO year.</td>
            <td>string</td>
        </tr>
        <tr>
            <td>eia_aeo_case</td>
            <td>EIA AEO Scenario Case</td>
            <td></td>
            <td>AEO scenario case ID to query (e.g. &quot;aeo2023ref&quot;). If left blank, T3CO auto-discovers the reference case for the resolved AEO year.</td>
            <td>string</td>
        </tr>
    </tbody>
</table>
</div>