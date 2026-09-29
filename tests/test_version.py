from importlib.metadata import version

import t3co


def test_version_matches_installed_distribution():
    """t3co.__version__ must report the version that was actually installed.

    It was a hardcoded "0.0.1" through the 2.0.0 release, so every install
    reported the wrong version, and the publish workflow's post-upload
    check could not tell which release it had installed.
    """
    assert t3co.__version__ == version("t3co")
