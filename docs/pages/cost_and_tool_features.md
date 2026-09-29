# T3CO Cost and Tool Features

## Cost Features

### Capital Cost Components

- *MSRP Breakdown:* Glider, Fuel Converter, Fuel Storage, Battery, Motor Controller and Power Electronics, Plugin
- *Purchase or Sales Tax*
- *Purchasing Downpayment:* For loan or lease purchasing method
- *Residual Cost:* Salvage value at end of life of vehicle

### Operating Cost Components

- *Fuel Expense*: Total cost of fuel or energy consumed
- *Maintenance Cost*
- *Purchasing Cost:* Recurring payments for loan or lease purchasing method
- *Insurance Cost*
- *Fueling Dwell Labor cost*
- All operating costs are discounted year over year to account for time value of money

#### EIA Fuel Price Projections

When a US zipcode is provided in the Config or Scenario `region` field, T3CO can fetch fuel price projections from the EIA Annual Energy Outlook (AEO) API. The system auto-discovers the latest AEO publication year and reference scenario, resolves the zipcode to a US Census division, and retrieves region-specific nominal prices for diesel, gasoline, electricity, and CNG. Hydrogen prices fall back to the static `FuelPrices.csv`. This feature requires a free EIA API key and is controlled by the `eia_fuel_prices` toggle in `cost_toggles.json`.

### Opportunity Cost Components

- *Lost Payload Capacity Cost*: Cost of fractionally additional advanced powertrain vehicles needed to carry the same payload as a conventional one (only for Class 8)
- *Fueling/Charging Dwell Time Opportunity Cost*: Cost of unproductive dwell time while charging or fueling a vehicle
- *Maintenance & Repair Downtime Opportunity Cost*: Cost of planned and unplanned vehicle downtime due to M&R
- All opportunity costs are discounted year over year to account for time value of money

### Total Cost of Ownership

- *Two methods of estimating discounted TCO:* 'DIRECT' and 'EFFICIENCY'
- *Annualized total costs:* And 
- *Total cost per mile and levelized cost per mile*

## Tool Features

- Ability to generate individual Ledger and TCO Per Year reports exported as CSV or JSON files
- Ability to run multiple Vehicle-Scenario-Energy selections from input files and export results to CSV
- Option to run FASTSim simulations for energy calculations
- Option to provide exogenous MPGGE and vehicle range inputs instead of running a powertrain simulation
- BatchMode to run a folder of drivecycles through FASTSim and generate multiple scenarios per selection
- Multiprocessing/Parallelization to reduce runtime for large selections. Can be clubbed with BatchMode to run 1000s of drivecycles on a local machine
- Dynamic Wireless Power Transfer - Analyze on-road charging technologies and its impact on cost
- Optimization Toolbox with NSGA2, PatternSearch, NelderMead, and PSO algorithms for vehicle sizing and TCO minimization
- Regionalized fuel prices via EIA AEO API with automatic zipcode-to-census-division resolution
- Visualization module to plot TCO breakdowns, histograms, and violin plots from results — static (matplotlib) or interactive HTML (Plotly), with a `--plot` flag on the sweep CLI

## Features Roadmap

- Labor Cost as an operating cost component
- Grants incentives, registration, title, and recurring fees added as Capital and Operating Cost components
- Battery replacement and battery degradation accounted for in Operating Costs and Energy calculations
- Regionalized registration and labor cost inputs
- Option to run RouteE for Energy calculations
