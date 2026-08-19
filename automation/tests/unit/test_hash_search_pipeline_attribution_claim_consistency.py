"""Regression test for `test_chat_interface.py::TestHashSearch::
test_add_pipeline_via_hash_search_joins_participants_and_responds`
(ELITEA-2208/2470 review round 1, fix round 1).

Guards against the defect a fresh-session reviewer flagged: the AFS Coverage
Map row for "Type a message and send" (and the mirrored Automation Hints
bullet) claimed the shipped test would assert 'header shows "to <Pipeline
Name>" attribution' -- a claim inherited via copy-paste from the
already-merged ELITEA-2207/2469 sibling AFS, whose own covering test never
implements it either. `ApplicationAnswer.jsx`'s response-header
participant-name text carries no testid on either `main` or
`automation/testids` (checked live, fresh `git fetch origin`), so no
testid-only-compliant assertion of that string is even possible today, and
neither TMS case's own wording asks for it.

This test parses the LIVE method's docstring plus the AFS file's own text
and fails if either one makes a bare *positive* "attributed to" claim with
no corresponding handle reference in the method body -- so a future edit
that reintroduces the claim (docstring or AFS) without also adding the
(currently nonexistent) implementation catches it here instead of shipping
a stale coverage claim silently, same failure class as
`coverage_map_row_can_partially_overclaim_one_clause.md`.
"""

import importlib
import inspect
import re
from pathlib import Path

import pytest

MODULE_PATH = "tests.ui.chat.test_chat_interface"
METHOD_NAME = "test_add_pipeline_via_hash_search_joins_participants_and_responds"

TESTS_UNIT_DIR = Path(__file__).resolve().parent
AUTOMATION_DIR = TESTS_UNIT_DIR.parent.parent  # .../automation
REPO_ROOT = AUTOMATION_DIR.parent  # .../elitea-testing-public
AFS_PATH = (
    REPO_ROOT
    / "test-specs"
    / "chat-interface"
    / "lextend_hash-search-select-pipeline-adds-participant-and-responds_ELITEA-2208.md"
)

ATTRIBUTION_CLAIM = re.compile(r"attribut", re.IGNORECASE)
# If a response-attribution assertion genuinely existed, the method body
# would have to read the response header via SOME handle -- these are the
# only plausible ones today (a future testid add would extend this list).
ATTRIBUTION_HANDLE_HINTS = ("sender_name", "SENDER_NAME", "participant_name", "response_header")


@pytest.fixture(scope="module")
def spec_module():
    return importlib.import_module(MODULE_PATH)


@pytest.fixture(scope="module")
def target_method(spec_module):
    cls = spec_module.TestHashSearch
    return getattr(cls, METHOD_NAME)


@pytest.fixture(scope="module")
def method_source(target_method) -> str:
    return inspect.getsource(target_method)


@pytest.fixture(scope="module")
def method_docstring(target_method) -> str:
    return target_method.__doc__ or ""


@pytest.fixture(scope="module")
def afs_text() -> str:
    assert AFS_PATH.is_file(), f"expected AFS file missing: {AFS_PATH}"
    return AFS_PATH.read_text(encoding="utf-8")


def _positive_attribution_claims(text: str) -> list[str]:
    """Lines mentioning "attribut..." that are NOT themselves a qualifier
    stating the check is absent (the fix's own corrective wording)."""
    claims = []
    for line in text.splitlines():
        if not ATTRIBUTION_CLAIM.search(line):
            continue
        lowered = line.lower()
        if "no testid" in lowered or "does not" in lowered or "no separate" in lowered:
            continue
        claims.append(line)
    return claims


def test_docstring_makes_no_bare_attribution_claim(method_docstring, method_source):
    """If the docstring ever again states an attribution check happens
    without qualifying it as absent, the method body must contain a
    matching handle reference -- a bare positive claim with no matching
    code is exactly the ELITEA-2208/2470 review-round-1 defect shape."""
    positive_claims = _positive_attribution_claims(method_docstring)
    if not positive_claims:
        pytest.skip("docstring makes no bare attribution claim -- nothing to cross-check")
    matched = any(hint in method_source for hint in ATTRIBUTION_HANDLE_HINTS)
    assert matched, (
        "docstring claims an attribution check but the method body has no "
        f"matching handle reference (checked for any of {ATTRIBUTION_HANDLE_HINTS!r}): "
        f"{positive_claims!r}"
    )


def test_docstring_explicitly_documents_the_non_claim(method_docstring):
    """The fix's own corrective line must stay present -- silently dropping
    it reopens the exact ambiguity a reviewer already flagged once."""
    lowered = method_docstring.lower()
    assert "does not" in lowered, (
        "expected the docstring to explicitly state it does NOT assert a "
        "response-attribution header string (fix-round correction) -- got:\n"
        f"{method_docstring}"
    )


def test_afs_coverage_map_row_makes_no_bare_attribution_claim(afs_text, method_source):
    """Mirrors the docstring check against the AFS's own Coverage Map row
    for the 'Type a message and send' step -- the other half of the
    original defect (row + docstring both overclaimed together)."""
    row_lines = [line for line in afs_text.splitlines() if line.startswith("| Type a message and send")]
    assert row_lines, "expected a 'Type a message and send' Coverage Map row in the AFS"
    row = row_lines[0]
    positive_claims = _positive_attribution_claims(row)
    if not positive_claims:
        return
    matched = any(hint in method_source for hint in ATTRIBUTION_HANDLE_HINTS)
    assert matched, (
        "AFS Coverage Map row claims an attribution check but the method "
        f"body has no matching handle reference: {row!r}"
    )
