"""Unit tests for `_is_known_defect_1203()` in
`tests.ui.admin.test_secret_create_inline_checkmark_x_cancel` (ELITEA-2336).

Regression coverage for PR #1204 round-3 review finding
(`.agents/memory/qa-engineer/elitea_2336_pr1204_r3_known_1203_matcher_too_strict.md`):
the matcher previously required BOTH the "Maximum update depth exceeded" text
AND a "SecretsContent.jsx" component-stack substring in the same console
message. Playwright's console-message capture does not always include the
full component stack for this warning — the implementer's own round-2
verification reruns hit a short-form occurrence (no stack suffix) 1/3 times,
which fell into `unexpected_errors` and hard-failed the test with a
different signature than the other 2 runs. That non-determinism directly
undermines the sanctioned-RED gate's "(a) deterministic — identical failure
3/3" requirement (`.agents/testing.md` § Merge gate). These tests pin the
fix: match on the warning's own stable text prefix alone.
"""

from tests.ui.admin.test_secret_create_inline_checkmark_x_cancel import (
    _is_known_defect_1203,
)

# A long-form occurrence, as observed in the normal case — full React
# component stack included, ending in the component where the warning
# originates.
_LONG_FORM_TEXT = (
    "Warning: Maximum update depth exceeded. This can happen when a "
    "component calls setState inside useEffect, but useEffect either "
    "doesn't have a dependency array, or one of the dependencies changes on "
    "every render.\n    at div\n    at SecretsContent\n    "
    "(https://localhost:5173/src/pages/Settings/Secrets/SecretsContent.jsx:42:11)\n"
    "    at SecretsPage\n    at Suspense\n    at Route"
)

# A short-form occurrence, as observed 1/3 times during round-2 verification
# — the same warning, but with NO component-stack suffix captured at all.
_SHORT_FORM_TEXT = (
    "Warning: Maximum update depth exceeded. This can happen when a "
    "component calls setState inside useEffect, but useEffect either "
    "doesn't have a dependency array, or one of the dependencies changes on "
    "every render."
)


def test_matches_long_form_occurrence_with_full_component_stack():
    """The normal-shape occurrence (full stack incl. SecretsContent.jsx)
    must still be recognized as the known defect."""
    assert _is_known_defect_1203(_LONG_FORM_TEXT) is True


def test_matches_short_form_occurrence_with_no_component_stack():
    """The short-form occurrence (no SecretsContent.jsx stack suffix at
    all) must ALSO be recognized as the known defect — this is the exact
    case the old dual-substring matcher misclassified as unexpected and
    hard-failed on."""
    assert _is_known_defect_1203(_SHORT_FORM_TEXT) is True


def test_does_not_match_an_unrelated_console_error():
    """A genuinely different console error must still hard-fail — the
    matcher stays isolated to this one known signature."""
    assert _is_known_defect_1203("TypeError: Cannot read properties of undefined") is False
