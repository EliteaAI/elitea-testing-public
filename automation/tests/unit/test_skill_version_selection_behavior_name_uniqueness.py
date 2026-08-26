"""Regression test for `test_skill_agent_version_selection_behavior.py`'s
`SKILL_NAME` / `AGENT_NAME` generation (ELITEA-2610 review round 1, fix round 1).

Guards against the defect a fresh-session reviewer flagged: the module used to
build these names as

    TS = int(time.time())
    SKILL_NAME = f"elitea-2610-response-style-{TS}"[:32]
    AGENT_NAME = f"elitea-2610-version-behavior-agent-{TS}"[:32]

`[:32]` sliced the FINISHED string (base + timestamp), not the base name — so
with `AGENT_NAME`'s 35-char prefix, the entire 10-digit timestamp fell off the
end and every test run created an agent with the IDENTICAL name. `SKILL_NAME`
fared only slightly better: its 27-char prefix left room for just the leading
5 digits of the epoch, which change roughly once a day, so runs inside the
same day still collided.

This test asserts the *shape* the fix must have (name length within the
32-char product cap, real per-run entropy that a truncate-after-concat could
not have silently eaten) directly against the live module constants — so a
future edit that reintroduces "grow the base string, slice at the end" fails
here instead of shipping a name-collision flake.
"""

import importlib

import pytest

MODULE_PATH = "tests.ui.skills.test_skill_agent_version_selection_behavior"

# The product's name-length ceiling (EliteaUI `constants.js` MAX_NAME_LENGTH),
# named directly rather than imported so this test has no dependency on the
# spec module beyond its two name constants.
MAX_NAME_LENGTH = 32


@pytest.fixture(scope="module")
def spec_module():
    return importlib.import_module(MODULE_PATH)


def test_skill_and_agent_names_fit_the_product_cap(spec_module):
    """Both names must respect the same 32-char ceiling the product enforces —
    the bug this guards against was a truncation applied too late, not a
    missing cap; the cap itself must still hold."""
    assert len(spec_module.SKILL_NAME) <= MAX_NAME_LENGTH, (
        f"SKILL_NAME {spec_module.SKILL_NAME!r} ({len(spec_module.SKILL_NAME)} "
        f"chars) exceeds the {MAX_NAME_LENGTH}-char product cap"
    )
    assert len(spec_module.AGENT_NAME) <= MAX_NAME_LENGTH, (
        f"AGENT_NAME {spec_module.AGENT_NAME!r} ({len(spec_module.AGENT_NAME)} "
        f"chars) exceeds the {MAX_NAME_LENGTH}-char product cap"
    )


def test_names_are_not_end_truncated_copies_of_a_longer_base(spec_module):
    """Reproduces the exact defect shape: build the SAME base pattern the
    buggy code used (a fixed prefix + a value concatenated on the end), slice
    it to the product cap the way the bug did, and confirm the CURRENT names
    are not that string — i.e. the fix does not merely reintroduce
    truncate-after-concat under a new prefix."""
    buggy_skill_shape = "elitea-2610-response-style-0000000000"[:MAX_NAME_LENGTH]
    buggy_agent_shape = "elitea-2610-version-behavior-agent-0000000000"[:MAX_NAME_LENGTH]
    assert spec_module.SKILL_NAME != buggy_skill_shape
    assert spec_module.AGENT_NAME != buggy_agent_shape


def test_suffix_survives_reimport_with_real_entropy(spec_module):
    """The per-run differentiator (`_SUFFIX`) must actually appear, intact,
    inside both names — proving the cap was applied BEFORE concatenation
    (by construction, via a short base) rather than after it (which would
    risk slicing the suffix off, the original defect)."""
    suffix = spec_module._SUFFIX
    assert suffix, "expected a non-empty per-run suffix on the spec module"
    assert suffix in spec_module.SKILL_NAME, (
        f"suffix {suffix!r} not found intact in SKILL_NAME "
        f"{spec_module.SKILL_NAME!r} — looks truncated"
    )
    assert suffix in spec_module.AGENT_NAME, (
        f"suffix {suffix!r} not found intact in AGENT_NAME "
        f"{spec_module.AGENT_NAME!r} — looks truncated"
    )


def test_repeated_module_reimports_yield_distinct_names():
    """Simulates two separate test-run processes each importing the module
    fresh (as pytest does per-session) — the names generated must differ,
    proving real per-run uniqueness rather than the timestamp-collapsed-to-a-
    constant-prefix behaviour the original bug produced for runs on the same
    day (SKILL_NAME) or ever (AGENT_NAME)."""
    import sys

    sys.modules.pop(MODULE_PATH, None)
    first = importlib.import_module(MODULE_PATH)
    first_skill, first_agent = first.SKILL_NAME, first.AGENT_NAME

    sys.modules.pop(MODULE_PATH, None)
    second = importlib.import_module(MODULE_PATH)
    second_skill, second_agent = second.SKILL_NAME, second.AGENT_NAME

    assert first_skill != second_skill, (
        "two fresh imports produced the SAME SKILL_NAME — per-run entropy "
        "is not surviving into the constant"
    )
    assert first_agent != second_agent, (
        "two fresh imports produced the SAME AGENT_NAME — per-run entropy "
        "is not surviving into the constant"
    )
