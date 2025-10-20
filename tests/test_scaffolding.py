from pathlib import Path

import pytest

pytest_plugins = ("pytester",)

from src.utils.scaffolding import ScaffoldingIncomplete, scaffold, scaffoldable


def test_scaffold_helper_raises_custom_exception():
    with pytest.raises(ScaffoldingIncomplete) as excinfo:
        scaffold("demo feature")
    assert excinfo.value.feature_name == "demo feature"
    assert "demo feature" in str(excinfo.value)


def test_scaffoldable_decorator_raises_when_called():
    @scaffoldable(feature_name="decorated feature")
    def _placeholder() -> None:
        raise AssertionError("should not execute")

    with pytest.raises(ScaffoldingIncomplete) as excinfo:
        _placeholder()
    assert excinfo.value.feature_name == "decorated feature"


def test_scaffolding_failure_is_reported_as_skip(pytester):
    repo_root = Path(__file__).resolve().parent.parent
    pytester.makeconftest(
        f"""
import sys
from pathlib import Path

ROOT = Path({repr(str(repo_root))})
for path in [ROOT / "src", ROOT / "tests"]:
    if str(path) not in sys.path:
        sys.path.insert(0, str(path))

import pytest
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
            pytest.skip(f"Scaffolding incomplete for {{feature_name}}")
    elif excinfo and excinfo.errisinstance(ScaffoldingIncomplete):
        feature_name = getattr(excinfo.value, "feature_name", "unknown feature")
        outcome.force_result(None)
        pytest.skip(f"Scaffolding incomplete for {{feature_name}}")

@pytest.hookimpl(tryfirst=True, hookwrapper=True)
def pytest_runtest_makereport(item, call):
    outcome = yield
    rep = outcome.get_result()
    if rep.when != "call":
        return

    excinfo = call.excinfo
    if excinfo and excinfo.errisinstance(ScaffoldingIncomplete):
        feature_name = getattr(excinfo.value, "feature_name", "unknown feature")
        rep.outcome = "skipped"
        rep.wasxfail = False
        rep.longrepr = f"Skipped: scaffolding incomplete for {{feature_name}}"
        rep.shortrepr = "s"
"""
    )

    pytester.makepyfile(
        """
from src.utils.scaffolding import scaffold

def test_pending_feature():
    scaffold("Pending feature X")
"""
    )

    result = pytester.runpytest("-q")
    result.assert_outcomes(skipped=1)
    result.stdout.fnmatch_lines(["*Pending feature X*"])
