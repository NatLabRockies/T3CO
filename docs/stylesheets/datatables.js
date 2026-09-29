document.addEventListener("DOMContentLoaded", function () {
    /**
     * Replace a native <select multiple> with a collapsed dropdown of checkboxes.
     *
     * The native element stays in the DOM (visually hidden) and remains the source of
     * truth: ticking a box flips `option.selected` and fires a `change` event, so the
     * filtering code keeps reading `selectedOptions` exactly as it would otherwise. If
     * this script fails to load, the plain list box is still rendered and usable.
     */
    function enhanceMultiSelect(select) {
        let options = Array.from(select.options);

        let wrapper = document.createElement("div");
        wrapper.className = "ms-dropdown";
        select.parentNode.insertBefore(wrapper, select);
        wrapper.appendChild(select);
        select.classList.add("ms-dropdown__native");

        let toggle = document.createElement("button");
        toggle.type = "button";
        toggle.className = "ms-dropdown__toggle";
        toggle.setAttribute("aria-haspopup", "true");
        toggle.setAttribute("aria-expanded", "false");
        wrapper.appendChild(toggle);

        let panel = document.createElement("div");
        panel.className = "ms-dropdown__panel";
        panel.hidden = true;
        wrapper.appendChild(panel);

        function updateLabel() {
            let selected = options.filter(option => option.selected);
            if (selected.length === 0) {
                toggle.textContent = "All";
            } else if (selected.length === 1) {
                toggle.textContent = selected[0].textContent;
            } else {
                toggle.textContent = selected.length + " selected";
            }
        }

        options.forEach(function (option, index) {
            let label = document.createElement("label");
            label.className = "ms-dropdown__option";

            let checkbox = document.createElement("input");
            checkbox.type = "checkbox";
            checkbox.checked = option.selected;
            checkbox.value = option.value;
            checkbox.id = select.id + "-option-" + index;
            checkbox.addEventListener("change", function () {
                option.selected = checkbox.checked;
                updateLabel();
                select.dispatchEvent(new Event("change", { bubbles: true }));
            });

            label.appendChild(checkbox);
            label.appendChild(document.createTextNode(" " + option.textContent));
            panel.appendChild(label);
        });

        function close() {
            panel.hidden = true;
            toggle.setAttribute("aria-expanded", "false");
        }

        toggle.addEventListener("click", function (event) {
            event.stopPropagation();
            let opening = panel.hidden;
            panel.hidden = !opening;
            toggle.setAttribute("aria-expanded", String(opening));
        });
        panel.addEventListener("click", function (event) {
            event.stopPropagation();
        });
        document.addEventListener("click", close);
        document.addEventListener("keydown", function (event) {
            if (event.key === "Escape") {
                close();
            }
        });

        updateLabel();
    }

    function setupDataTable(tableId, unitsFilterId, dataTypeFilterId, powertrainFilterId, t3coComponentFilterId, categoryFilterId, unitsColumn, dataTypeColumn, powertrainColumn, t3coComponentColumn, categoryColumn) {
        let table = new DataTable("#" + tableId, {
            paging: false,   // Show all rows
            searching: true, // Enable search
            ordering: true,  // Enable sorting
            info: false      // Hide table info
        });

        // Populate dropdowns with the unique values actually present in the column
        function populateDropdown(columnIndex, dropdownId) {
            let uniqueValues = new Set();
            table.column(columnIndex - 1).data().each(function (value) {
                uniqueValues.add(String(value).trim());
            });

            let dropdown = document.getElementById(dropdownId);
            dropdown.innerHTML = '<option value="">All</option>'; // Reset dropdown
            Array.from(uniqueValues).sort().forEach(value => {
                let option = document.createElement("option");
                option.value = value;
                option.textContent = value;
                dropdown.appendChild(option);
            });
        }

        if (unitsFilterId) {
            populateDropdown(unitsColumn, unitsFilterId);  // Units column
        }
        if (dataTypeFilterId) {
            populateDropdown(dataTypeColumn, dataTypeFilterId);  // Data Type column
        }
        if (categoryFilterId) {
            populateDropdown(categoryColumn, categoryFilterId);  // Category column
        }

        // Lift DataTables' search box out of the scrolling table box so it stays
        // visible while the rows scroll underneath it.
        let wrapper = table.table().container();
        let container = wrapper.closest(".table-container");
        let searchBox = wrapper.querySelector(".dataTables_filter");
        if (container && searchBox) {
            container.parentNode.insertBefore(searchBox, container);
        }

        function cellValue(searchData, column) {
            return column ? String(searchData[column - 1] || "").toLowerCase() : "";
        }

        /**
         * Filter through DataTables' own search pipeline rather than by hiding rows.
         *
         * An earlier version called .show()/.hide() on the row nodes, which DataTables
         * undoes on every redraw - so sorting a column or typing in the search box
         * brought filtered-out rows back. Registering here keeps the dropdowns, the
         * search box and column sorting consistent with each other.
         */
        DataTable.ext.search.push(function (settings, searchData) {
            if (settings.nTable.id !== tableId) {
                return true;  // Not our table - leave it alone
            }

            let unitsValue = unitsFilterId ? document.getElementById(unitsFilterId).value.toLowerCase() : "";
            let dataTypeValue = dataTypeFilterId ? document.getElementById(dataTypeFilterId).value.toLowerCase() : "";
            let powertrainValue = powertrainFilterId ? document.getElementById(powertrainFilterId).value.toLowerCase() : "";
            let t3coComponentValues = t3coComponentFilterId ? Array.from(document.getElementById(t3coComponentFilterId).selectedOptions).map(option => option.value.toLowerCase()) : [];
            let categoryValue = categoryFilterId ? document.getElementById(categoryFilterId).value.toLowerCase() : "";

            let rowUnits = cellValue(searchData, unitsColumn);
            let rowDataType = cellValue(searchData, dataTypeColumn);
            let rowPowertrain = cellValue(searchData, powertrainColumn);
            let rowT3coComponent = cellValue(searchData, t3coComponentColumn);
            let rowCategory = cellValue(searchData, categoryColumn);

            // Powertrain and T3CO Component cells hold several values at once
            // ("Conv, BEV, HEV, FCEV", "CapitalCosts: MSRP"), so they match on substring
            // while the single-valued columns match exactly.
            let matchUnits = unitsValue === "" || rowUnits === unitsValue;
            let matchDataType = dataTypeValue === "" || rowDataType === dataTypeValue;
            let matchPowertrain = powertrainValue === "" || rowPowertrain.includes(powertrainValue);
            let matchT3coComponent = t3coComponentValues.length === 0 || t3coComponentValues.some(value => rowT3coComponent.includes(value));
            let matchCategory = categoryValue === "" || rowCategory === categoryValue;

            return matchUnits && matchDataType && matchPowertrain && matchT3coComponent && matchCategory;
        });

        [unitsFilterId, dataTypeFilterId, powertrainFilterId, t3coComponentFilterId, categoryFilterId].forEach(function (filterId) {
            if (filterId) {
                document.getElementById(filterId).addEventListener("change", function () {
                    table.draw();
                });
            }
        });

        if (t3coComponentFilterId) {
            enhanceMultiSelect(document.getElementById(t3coComponentFilterId));
        }

        // Download the parameter names of the currently filtered rows as CSV
        function downloadCSV() {
            let InputParameters = [];
            table.rows({ search: "applied" }).data().each(function (rowData) {
                InputParameters.push(String(rowData[0]).trim());  // First column is the parameter name
            });

            let csvContent = "data:text/csv;charset=utf-8," + InputParameters.join(",") + "\n";
            let encodedUri = encodeURI(csvContent);
            let link = document.createElement("a");
            link.setAttribute("href", encodedUri);
            link.setAttribute("download", tableId + "_input_parameters.csv");
            document.body.appendChild(link);
            link.click();
            document.body.removeChild(link);
        }

        // Add the download event listener for the table's download button
        let downloadButton = document.getElementById("downloadTemplateBtn");
        if (downloadButton) {
            downloadButton.addEventListener("click", downloadCSV);
        }
    }

    // Initialize the vehicle parameters table
    if (document.getElementById("vehicleTable")) {
        setupDataTable("vehicleTable", "unitsFilter", "datatypeFilter", "powertrainFilter", null, null, 3, 6, 5, null, null);
    }

    // Initialize the scenario parameters table
    if (document.getElementById("scenarioTable")) {
        setupDataTable("scenarioTable", "scenarioUnitsFilter", "scenariodatatypeFilter", "powertrainFilter", "t3coComponentFilter", null, 3, 7, 5, 6, null);
    }

    // Initialize the config parameters table
    if (document.getElementById("configTable")) {
        setupDataTable("configTable", "configUnitsFilter", "configdatatypeFilter", null, null, null, 3, 5, null, null, null);
    }

    // Initialize the ledger outputs table
    // Columns: 1 Parameter, 2 Category, 3 Full Form, 4 Units, 5 Description, 6 Data Type
    if (document.getElementById("ledgerTable")) {
        setupDataTable("ledgerTable", "ledgerUnitsFilter", "ledgerdatatypeFilter", null, null, "ledgercategoryFilter", 4, 6, null, null, 2);
    }
});
