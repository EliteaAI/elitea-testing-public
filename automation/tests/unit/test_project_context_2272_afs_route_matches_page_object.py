"""Regression test for ELITEA-2272's AFS vs its shipped spec
(ELITEA-2266/2267/2276 review round 1, fix round 1).

Guards the doc-sync gap a fresh-session reviewer flagged: the
ELITEA-2266/2267/2276 branch repaired issue #1794 by moving
``ProjectContextPage.click_create()`` and ELITEA-2272's merged spec off the
product's retired create-mode query param and onto the real
``/settings/project-context/edit`` route — but ELITEA-2272's own AFS still
specified the dead URL as the expected result of its step 3. Paper that
contradicts the code it describes is the single largest source of blocking
review findings on this project, and it is invisible to every test that only
runs the code.

This pins the AFS's route claim to the page object's own constant, so:

* re-introducing the retired query param into that AFS fails here;
* renaming ``PROJECT_CONTEXT_EDIT_PATH`` without amending the AFS fails here;
* the spec and the AFS can no longer drift apart silently.
"""

import ast
from pathlib import Path

import pytest
from pages.project_context_page import PROJECT_CONTEXT_EDIT_PATH, PROJECT_CONTEXT_PATH

TESTS_UNIT_DIR = Path(__file__).resolve().parent
AUTOMATION_DIR = TESTS_UNIT_DIR.parent.parent  # .../automation
REPO_ROOT = AUTOMATION_DIR.parent  # .../elitea-testing-public

AFS_PATH = (
    REPO_ROOT
    / "test-specs"
    / "settings-project-params"
    / "l2_project-context-character-limit-2500_ELITEA-2272.md"
)
SPEC_PATH = AUTOMATION_DIR / "tests" / "ui" / "admin" / "test_project_context_character_limit.py"

#: The create-mode query param the product retired (`routes.js` now declares two
#: real routes). Split so this guard file's own text cannot trip it.
RETIRED_CREATE_PARAM = "?" + "view=create"


@pytest.fixture(scope="module")
def afs_text() -> str:
    assert AFS_PATH.is_file(), f"ELITEA-2272 AFS missing at {AFS_PATH}"
    return AFS_PATH.read_text(encoding="utf-8")


def test_afs_does_not_specify_the_retired_create_route(afs_text):
    """The AFS must not state an expectation the shipped spec contradicts."""
    hits = [
        f"{n}: {line.strip()}"
        for n, line in enumerate(afs_text.splitlines(), start=1)
        if RETIRED_CREATE_PARAM in line
    ]
    assert not hits, (
        "ELITEA-2272's AFS specifies the retired create-mode query param, which the "
        "product no longer serves and its own shipped spec no longer asserts "
        f"(issue #1794). Amend the AFS to '{PROJECT_CONTEXT_EDIT_PATH}':\n  " + "\n  ".join(hits)
    )


def test_afs_specifies_the_live_editor_route(afs_text):
    """And it must state the route the page object actually waits for."""
    assert PROJECT_CONTEXT_EDIT_PATH in afs_text, (
        f"ELITEA-2272's AFS no longer names the live editor route "
        f"'{PROJECT_CONTEXT_EDIT_PATH}'. If the page object's route constant changed, the "
        f"AFS must be amended in the same PR (Phase 6 doc-sync)."
    )


def _executable_string_literals(source: str) -> list[str]:
    """Every string constant in *source* EXCEPT docstrings.

    The spec's docstrings legitimately narrate #1794's history (naming the param
    the product retired); only a live URL the code actually acts on is a defect.
    """
    tree = ast.parse(source)
    docstrings = {
        id(node.body[0].value)
        for node in ast.walk(tree)
        if isinstance(node, (ast.Module, ast.ClassDef, ast.FunctionDef, ast.AsyncFunctionDef))
        and node.body
        and isinstance(node.body[0], ast.Expr)
        and isinstance(node.body[0].value, ast.Constant)
        and isinstance(node.body[0].value.value, str)
    }
    return [
        node.value
        for node in ast.walk(tree)
        if isinstance(node, ast.Constant) and isinstance(node.value, str) and id(node) not in docstrings
    ]


def test_shipped_spec_asserts_the_same_route_the_afs_specifies():
    """Close the loop: the code the AFS describes must pin the same URL."""
    spec_text = SPEC_PATH.read_text(encoding="utf-8")

    live_hits = [s for s in _executable_string_literals(spec_text) if RETIRED_CREATE_PARAM in s]
    assert not live_hits, (
        "ELITEA-2272's spec acts on the retired create-mode query param again — that is "
        f"the #1794 timeout, reproduced. Offending literals: {live_hits}"
    )
    assert PROJECT_CONTEXT_EDIT_PATH in spec_text or "PROJECT_CONTEXT_EDIT_PATH" in spec_text, (
        f"ELITEA-2272's spec no longer pins '{PROJECT_CONTEXT_EDIT_PATH}'. The route "
        f"assertion must be repaired, never dropped — dropping it hides the next rename."
    )
    assert PROJECT_CONTEXT_PATH in spec_text or "PROJECT_CONTEXT_PATH" in spec_text, (
        "ELITEA-2272's spec no longer references the saved-view route it returns to "
        "after Save."
    )
