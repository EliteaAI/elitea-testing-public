"""Regression test for `test_help_center_version_info.py`'s component-version
assertions (ELITEA-2225 review round 1, fix round 1).

Guards against the defect a fresh-session reviewer flagged: the module used to
pin exact live backend deploy versions as literal expected values —
``EXPECTED_COMPONENT_VERSIONS = {"elitea_core": "0.673", "admin": "0.77", ...}``
— and assert them directly in steps 4/5/9. Those numbers are live deploy
metadata (``systemInfo.plugins``), not stable entity properties: the very next
backend release that bumps any one of the 6 listed components turns the test
red for a reason unrelated to this feature.

This test inspects the LIVE spec module and its source and asserts the shape
the fix requires — no module attribute pairs a component name with one of the
original pinned semver literals, and the format-then-fidelity pattern
(``VERSION_FORMAT`` regex + a run-time ``observed_versions`` mapping) is
present — so a future edit that reintroduces "hardcode the analysis-time
literal" fails here instead of shipping a version-bump flake.
"""

import importlib
import inspect

import pytest

MODULE_PATH = "tests.ui.help_center.test_help_center_version_info"

# The exact literals the ORIGINAL buggy shape pinned (live-confirmed 2026-08-14
# systemInfo.plugins versions) — named here only to prove they're gone, never
# reused as expected values.
ORIGINAL_PINNED_VERSIONS = {"0.673", "0.77", "0.21", "0.160", "0.9.13", "0.854"}


@pytest.fixture(scope="module")
def spec_module():
    return importlib.import_module(MODULE_PATH)


@pytest.fixture(scope="module")
def spec_source(spec_module):
    return inspect.getsource(spec_module)


def test_no_module_attribute_pins_a_component_name_to_a_version_literal(spec_module):
    """The buggy shape was a dict literal pairing a stable component name with
    a volatile version string. No module-level dict may reproduce that pairing
    (checked by value, not just name — a rename wouldn't hide the defect)."""
    for name, value in vars(spec_module).items():
        if name.startswith("__") or not isinstance(value, dict) or not value:
            continue
        pinned = {v for v in value.values() if isinstance(v, str)} & ORIGINAL_PINNED_VERSIONS
        assert not pinned, (
            f"module attribute {name!r} = {value!r} pins version literal(s) "
            f"{pinned} — reproduces the original hardcoded-version defect shape"
        )


def test_expected_components_is_a_plain_name_list_not_a_version_mapping(spec_module):
    """Component NAMES are stable app config and may stay literal; the
    container holding them must be a plain list, not a name->version dict."""
    assert hasattr(spec_module, "EXPECTED_COMPONENTS"), (
        "expected an EXPECTED_COMPONENTS name list on the spec module"
    )
    assert isinstance(spec_module.EXPECTED_COMPONENTS, list)
    assert all(isinstance(c, str) and ":" not in c for c in spec_module.EXPECTED_COMPONENTS)


def test_version_format_pattern_present_and_pinned_dict_gone(spec_module):
    """The fix's format-then-fidelity pattern must be present (a VERSION_FORMAT
    regex asserting SHAPE), and the original defect's dict-constant name must
    be gone (checked by name — the by-value check lives in the test above;
    this one guards a rename that keeps only the empty/renamed constant)."""
    assert hasattr(spec_module, "VERSION_FORMAT"), (
        "expected a VERSION_FORMAT constant asserting version SHAPE, not a pinned literal"
    )
    assert not hasattr(spec_module, "EXPECTED_COMPONENT_VERSIONS"), (
        "EXPECTED_COMPONENT_VERSIONS reappeared — this was the original "
        "pinned-literal defect's constant name"
    )


def test_clipboard_fidelity_check_reads_a_runtime_observed_mapping(spec_source):
    """Step 9's clipboard check must iterate a run-time ``observed_versions``
    mapping captured from the live tooltip (Step 5), not a frozen constant —
    otherwise the fidelity check silently degrades back into a pinned-literal
    assertion under a different variable name."""
    assert "observed_versions" in spec_source, (
        "expected the spec to read from a run-time `observed_versions` mapping "
        "populated from the live tooltip text, not a frozen module constant"
    )
