"""T3CO: Transportation Technology Total Cost of Ownership."""
from __future__ import annotations

from importlib.metadata import PackageNotFoundError, version

import t3co

try:
    # Read from the installed distribution so the reported version cannot
    # drift from the version declared in pyproject.toml.
    __version__ = version("t3co")
except PackageNotFoundError:  # imported from a source tree that was never installed
    __version__ = "0+unknown"
