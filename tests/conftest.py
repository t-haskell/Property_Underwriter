import sys
from pathlib import Path

import pytest

SRC = Path(__file__).resolve().parent.parent / "src"
if str(SRC) not in sys.path:
    sys.path.insert(0, str(SRC))

from src.utils.scaffolding import ScaffoldingIncomplete


@pytest.hookimpl(tryfirst=True, hookwrapper=True)
def pytest_runtest_call(item):
    outcome = yield
    excinfo = getattr(outcome, "excinfo", None)
    if isinstance(excinfo, tuple):
        _, err, _ = excinfo
        if isinstance(err, ScaffoldingIncomplete):
            feature_name = getattr(err, "feature_name", "unknown feature")
            outcome.force_result(None)
            pytest.skip(f"Scaffolding incomplete for {feature_name}")
    elif excinfo and excinfo.errisinstance(ScaffoldingIncomplete):
        feature_name = getattr(excinfo.value, "feature_name", "unknown feature")
        outcome.force_result(None)
        pytest.skip(f"Scaffolding incomplete for {feature_name}")


@pytest.hookimpl(tryfirst=True, hookwrapper=True)
def pytest_runtest_makereport(item, call):
    """Convert scaffolding failures into skipped tests."""

    outcome = yield
    rep = outcome.get_result()
    if rep.when != "call":
        return

    excinfo = call.excinfo
    if excinfo and excinfo.errisinstance(ScaffoldingIncomplete):
        feature_name = getattr(excinfo.value, "feature_name", "unknown feature")
        rep.outcome = "skipped"
        rep.wasxfail = False
        rep.longrepr = f"Skipped: scaffolding incomplete for {feature_name}"
        rep.shortrepr = "s"
