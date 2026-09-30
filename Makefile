generate_pydocs: 
	pipx install pydoc-markdown
	pydoc-markdown -I ../src -p t3co --render-toc > modules/CodeReference.md
	pydoc-markdown -I ../src -m t3co.cli.sweep --render-toc > modules/sweep.md
	pydoc-markdown -I ../src -m t3co/constants/Global --render-toc > modules/Global.md
	pydoc-markdown -I ../src -m t3co/cost_models/capital_costs --render-toc > modules/capital_costs.md
	pydoc-markdown -I ../src -m t3co/cost_models/operating_costs --render-toc > modules/operating_costs.md
	pydoc-markdown -I ../src -m t3co/cost_models/opportunity_costs --render-toc > modules/opportunity_costs.md
	pydoc-markdown -I ../src -m t3co/energy_models/fastsim_model/fastsim_wrapper --render-toc > modules/fastsim_wrapper.md
	pydoc-markdown -I ../src -m t3co/energy_models/energy --render-toc > modules/energy.md
	pydoc-markdown -I ../src -m t3co/input_data/config --render-toc > modules/config.md
	pydoc-markdown -I ../src -m t3co/input_data/scenario --render-toc > modules/scenario.md
	pydoc-markdown -I ../src -m t3co/input_data/vehicle --render-toc > modules/vehicle.md
	pydoc-markdown -I ../src -m t3co/input_data/toggles --render-toc > modules/toggles.md
	pydoc-markdown -I ../src -m t3co/tco/ledger --render-toc > modules/ledger.md
	pydoc-markdown -I ../src -m t3co/tco/tcocalc --render-toc > modules/tcocalc.md
	pydoc-markdown -I ../src -m t3co/utils/demo_inputs_installer --render-toc > modules/demo_inputs_installer.md
	pydoc-markdown -I ../src -m t3co/utils/print_class_objects --render-toc > modules/print_class_objects.md
	pydoc-markdown -I ../src -m t3co/visualize/charts --render-toc > modules/charts.md
	