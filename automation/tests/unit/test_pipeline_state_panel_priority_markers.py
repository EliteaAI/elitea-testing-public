"""Unit tests pinning the per-function priority-marker override in
`tests.ui.pipelines.test_pipeline_state_panel_default_and_custom_variables`
(ELITEA-2044, PR #1366 review round 1).

Regression coverage for the priority-marker-drift defect class documented in
`.agents/memory/qa-engineer/priority_marker_drift_afs_vs_pytest_mark.md`
(recurrence #7): the module declares `pytestmark = [..., pytest.mark.p1, ..., pytest.mark.new]`
because its FIRST test (ELITEA-2042, case priority high) is correctly p1 —
but a sibling test added later for a *different*-priority case
(ELITEA-2044, case priority medium → p2) silently inherited that module-level
p1 unless it carries its own `@pytest.mark.p2` decorator. pytest does not
"override" a module-level mark with a function-level one — both apply — so
the only way to make the correct marker (`p2`) present on the function at
all is the per-function decorator; its absence is exactly the bug this test
would have caught before it reached review.
"""

from tests.ui.pipelines.test_pipeline_state_panel_default_and_custom_variables import (
    test_state_panel_default_and_custom_variables as _covering_test_func,
)
from tests.ui.pipelines.test_pipeline_state_panel_default_and_custom_variables import (
    test_state_panel_delete_custom_variable as _delete_test_func,
)

# Aliased on import (leading underscore) so pytest's `python_functions = test_*`
# collector does NOT re-discover and re-execute these live UI tests (with real
# `page`/`pipeline_id` browser fixtures) as a side effect of importing them here
# — only the module-level statements below (which DO match `test_*`) should run.


def _own_marker_names(test_func) -> set[str]:
    """Markers applied directly to the function via `@pytest.mark.xxx`,
    as distinct from the module-level `pytestmark` list (which pytest merges
    in separately at collection time and is NOT what this regression targets)."""
    return {mark.name for mark in getattr(test_func, "pytestmark", [])}


def test_delete_custom_variable_has_own_p2_priority_override():
    """ELITEA-2044 (case priority: medium) must carry its own p2 marker —
    the module-level pytestmark is p1, correct only for the p1/high
    ELITEA-2042 covering test, and would otherwise leak onto this test too."""
    own_markers = _own_marker_names(_delete_test_func)
    assert "p2" in own_markers, (
        "test_state_panel_delete_custom_variable (ELITEA-2044, medium priority) "
        f"must declare its own @pytest.mark.p2 override; found {own_markers or '(none)'} "
        "— without it, the test silently inherits the module's p1 (high)"
    )


def test_default_and_custom_variables_has_no_conflicting_own_priority_marker():
    """ELITEA-2042 (case priority: high) relies on the module-level p1 and
    must NOT carry a competing per-function priority marker — if it ever
    does, the two tests' priority intent has diverged from the module marker
    and needs re-auditing, not a silent stack-up."""
    own_markers = _own_marker_names(_covering_test_func)
    priority_markers = {m for m in own_markers if m.startswith("p") and m[1:].isdigit()}
    assert not priority_markers, (
        "test_state_panel_default_and_custom_variables (ELITEA-2042, high priority) "
        f"picked up an unexpected own priority marker {priority_markers!r} — "
        "it should rely on the module-level pytest.mark.p1 only"
    )
