"""Guard the interactive parameter tables in the built documentation.

The Inputs and Outputs pages are plain HTML tables that only become filterable
because ``mkdocs.yml`` pulls in jQuery, DataTables and ``datatables.js``. Those
``extra_javascript`` / ``extra_css`` keys were silently dropped in a merge once
before, which left every dropdown stuck on "All" on the published site while the
docs still built cleanly. This check fails the build if that happens again.

Usage:
    mkdocs build -d site
    python tests/docs/check_built_docs.py site
"""

import re
import sys
from pathlib import Path

# Page -> the table it must render
PAGES = {
    "pages/vehicle_inputs_descriptions/index.html": "vehicleTable",
    "pages/scenario_inputs_descriptions/index.html": "scenarioTable",
    "pages/config_inputs_descriptions/index.html": "configTable",
    "pages/ledger_outputs_descriptions/index.html": "ledgerTable",
}

# Assets every one of those pages must reference
REQUIRED_ASSETS = [
    "jquery-3.6.0.min.js",
    "datatables/datatables.min.js",
    "datatables/datatables.min.css",
    "stylesheets/datatables.js",
    "stylesheets/extra.css",
]

# Every filter dropdown, and the page it belongs to
FILTERS = {
    "pages/vehicle_inputs_descriptions/index.html": [
        "unitsFilter", "powertrainFilter", "datatypeFilter",
    ],
    "pages/scenario_inputs_descriptions/index.html": [
        "scenarioUnitsFilter", "powertrainFilter", "scenariodatatypeFilter",
        "t3coComponentFilter",
    ],
    "pages/config_inputs_descriptions/index.html": [
        "configUnitsFilter", "configdatatypeFilter",
    ],
    "pages/ledger_outputs_descriptions/index.html": [
        "ledgercategoryFilter", "ledgerUnitsFilter", "ledgerdatatypeFilter",
    ],
}


def check(site_dir):
    site = Path(site_dir)
    errors = []

    # Every table must be initialised by datatables.js, or its filters do nothing
    script = site / "stylesheets" / "datatables.js"
    if not script.is_file():
        errors.append("missing built asset: stylesheets/datatables.js")
        script_text = ""
    else:
        script_text = script.read_text()

    for page, table_id in PAGES.items():
        html_path = site / page
        if not html_path.is_file():
            errors.append("missing built page: %s" % page)
            continue
        html = html_path.read_text()

        if 'id="%s"' % table_id not in html:
            errors.append("%s: table #%s not rendered" % (page, table_id))

        for asset in REQUIRED_ASSETS:
            if asset not in html:
                errors.append(
                    "%s: does not reference %s - check extra_javascript/extra_css "
                    "in mkdocs.yml" % (page, asset)
                )

        for filter_id in FILTERS[page]:
            if 'id="%s"' % filter_id not in html:
                errors.append("%s: filter #%s missing" % (page, filter_id))

        if script_text and '"%s"' % table_id not in script_text:
            errors.append(
                "stylesheets/datatables.js has no setupDataTable call for #%s, so its "
                "filters will stay stuck on 'All'" % table_id
            )

        # Markdown list syntax around inline HTML leaks through as literal text
        if re.search(r"<p>-\s*<strong>", html):
            errors.append(
                "%s: filter row rendered as literal '- **Label:**' text - use "
                "<div class=\"filter-container\"> instead of a markdown list" % page
            )

    return errors


if __name__ == "__main__":
    site_dir = sys.argv[1] if len(sys.argv) > 1 else "site"
    failures = check(site_dir)
    if failures:
        print("Documentation check failed:\n")
        for failure in failures:
            print("  - %s" % failure)
        sys.exit(1)
    print("Documentation check passed: %d table pages wired up correctly." % len(PAGES))
