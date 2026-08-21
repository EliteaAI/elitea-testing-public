"""Static-analysis regression test for the ELITEA-1836 spec's module docstring
(review round 1 finding).

Guards against the defect a fresh-session reviewer flagged: when the #1631
mechanism was corrected during implementation (the collapse click interrupts
MUI `Collapse`'s enter transition — NOT `BucketContent.jsx`'s `isFetching`
early-return remounting `FileTreeItem`), the AFS and `_surface.md` were
re-synced but `test_artifacts_tree_subfolder_expand_collapse.py`'s module
docstring was not. It kept asserting the retracted mechanism and the retracted
measurements ("discarded 2 times in 5", "reliable 5/5, plus 7/7") as fact, and
never named `wait_for_tree_item_stable()` — the settle wait the test actually
depends on. A reader of the test, who does not read the AFS, was being told
something known to be false.

Docstring prose can't be asserted for truth in general; what CAN be asserted is
the specific drift shape that shipped:

1. the docstring names the mechanism the code relies on
   (`wait_for_tree_item_stable`), and
2. it does not state the retracted `isFetching` hypothesis or its retracted
   numbers as current fact — a mention is allowed only alongside an explicit
   retraction word, which is how the corrected docstring refers to it.
"""

import ast
import re
from pathlib import Path

import pytest

TESTS_UNIT_DIR = Path(__file__).resolve().parent
AUTOMATION_DIR = TESTS_UNIT_DIR.parent.parent  # .../automation

TARGET_FILE = (
    AUTOMATION_DIR
    / "tests"
    / "ui"
    / "artifacts"
    / "test_artifacts_tree_subfolder_expand_collapse.py"
)

# Numbers measured under the retracted hypothesis and superseded by the
# implementation-time probe (3/3 failures, 18/18 successes).
RETRACTED_MEASUREMENTS = (
    "discarded 2 times in 5",
    "5/5, plus 7/7",
)

# Words that mark a mention of the old hypothesis as historical rather than
# as a live claim.
RETRACTION_MARKERS = ("retract", "wrong", "superseded", "no longer")


@pytest.fixture(scope="module")
def module_docstring() -> str:
    assert TARGET_FILE.is_file(), f"expected spec file missing: {TARGET_FILE}"
    docstring = ast.get_docstring(ast.parse(TARGET_FILE.read_text(encoding="utf-8")))
    assert docstring, f"{TARGET_FILE.name} has no module docstring"
    return docstring


def test_docstring_names_the_settle_wait_the_test_depends_on(module_docstring):
    """The ordering/settle discipline the test enforces in code must be
    findable from the docstring — `wait_for_tree_item_stable()` is what makes
    step 5's single collapse click deterministic.
    """
    assert "wait_for_tree_item_stable" in module_docstring, (
        f"{TARGET_FILE.name}'s module docstring explains the two-click ordering "
        "without naming wait_for_tree_item_stable(), the wait the test actually "
        "relies on — the round-1 drift shape"
    )


def test_docstring_does_not_state_the_retracted_mechanism_as_fact(module_docstring):
    """`isFetching` / `FileTreeItem` remount was the FIRST-PASS hypothesis and
    was disproved during implementation (zero network requests across the
    window). It may be referenced only as a retraction, never as the reason.
    """
    lowered = module_docstring.lower()
    mentions_old_mechanism = "isfetching" in lowered or "filetreeitem" in lowered
    if not mentions_old_mechanism:
        return
    assert any(marker in lowered for marker in RETRACTION_MARKERS), (
        f"{TARGET_FILE.name}'s module docstring cites the retracted "
        "isFetching/FileTreeItem-remount mechanism without marking it as "
        f"retracted (expected one of {RETRACTION_MARKERS})"
    )


def test_docstring_does_not_carry_the_retracted_measurements(module_docstring):
    """The 2-in-5 / 5-of-5 / 7-of-7 figures were measured against the wrong
    mechanism and were superseded by 3/3 failures and 18/18 successes.
    """
    collapsed_whitespace = re.sub(r"\s+", " ", module_docstring)
    stale = [m for m in RETRACTED_MEASUREMENTS if m in collapsed_whitespace]
    assert not stale, (
        f"{TARGET_FILE.name}'s module docstring still quotes retracted "
        f"measurements {stale} — superseded by 3/3 failures / 18/18 successes"
    )
