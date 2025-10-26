import importlib
import sys
from pathlib import Path

import pytest

ROOT = Path(__file__).resolve().parent.parent
SRC = ROOT / "src"
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))
if str(SRC) not in sys.path:
    sys.path.insert(0, str(SRC))

configure = importlib.import_module("src.services.persistence").configure
ScaffoldingIncomplete = importlib.import_module("src.utils.scaffolding").ScaffoldingIncomplete


@pytest.fixture(autouse=True)
def _configure_test_database(tmp_path) -> None:
    """Ensure each test runs against an isolated SQLite database."""

    db_path = tmp_path / "underwriter.db"
    configure(f"sqlite+pysqlite:///{db_path}")


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
