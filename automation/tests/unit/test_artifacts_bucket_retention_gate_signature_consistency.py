"""Static-analysis regression test for ELITEA-1810's sanctioned-RED gate
signature (review round 1 finding).

Guards against the drift shape a fresh-session reviewer flagged: the analyst's
AFS originally said Test Step 13 would produce "exactly one soft failure". The
implementation correctly needed TWO ``expect.soft()`` assertions for that one
cause (#1677 — a Months retention policy reopens as Days: the measure text
``'Months' != 'Days'`` AND the value ``'10' != '304'``), and the AFS's Test
Step 13 was amended to say so — but the SAME claim also lived in two places
that were never swept: the AFS's own § Known Defects bullet and the spec's
module docstring.

Why that is worth a guard rather than a one-line fix. ``.agents/testing.md``
§ Merge gate makes the stated signature load-bearing: the lead classifies the
3x gate run against it, and "any AFS / Run Report sentence claiming otherwise
mis-steers this gate". Measured against a documented "exactly one soft
failure", a real 2-sub-exception ``ExceptionGroup`` reads as an unknown extra
failure — so the lead either blocks a correct spec, or (the expensive
direction) waves a genuinely NEW second cause through as "the known defect".
The count is the only thing distinguishing those two outcomes.

Prose cannot be asserted for truth in general. What CAN be asserted is that
the number every artifact states still matches the number of soft assertions
the code actually makes, in BOTH artifacts a gate operator reads:

1. the count of ``expect.soft()`` calls in the spec is the single source of
   truth, read from the AST;
2. the spec's module docstring states that count as the gate signature;
3. the AFS states the same count; and
4. neither artifact still carries the retracted "exactly one soft failure"
   claim as a live statement — a mention is allowed only alongside an explicit
   negation, which is how both corrected artifacts now refer to it.
"""

import ast
import re
from pathlib import Path

import pytest

TESTS_UNIT_DIR = Path(__file__).resolve().parent
AUTOMATION_DIR = TESTS_UNIT_DIR.parent.parent  # .../automation
REPO_ROOT = AUTOMATION_DIR.parent

SPEC_FILE = (
    AUTOMATION_DIR
    / "tests"
    / "ui"
    / "artifacts"
    / "test_artifacts_bucket_retention_edit_persistence.py"
)
AFS_FILE = (
    REPO_ROOT
    / "test-specs"
    / "artifacts"
    / "l2_create-bucket-via-folder-icon-retention-edit-persistence_ELITEA-1810.md"
)

# The claim that shipped stale in round 1, in both artifacts.
RETRACTED_CLAIM = "exactly one soft failure"

# Words that mark a mention of the retracted claim as a correction rather than
# as a live statement of the signature.
NEGATION_MARKERS = ("not", "never", "no longer", "superseded", "retract")

# How far back to look for a negation marker before a retracted-claim mention.
NEGATION_WINDOW_CHARS = 80


def _normalize(text: str) -> str:
    """Collapse whitespace so a claim wrapped across lines still matches."""
    return re.sub(r"\s+", " ", text)


@pytest.fixture(scope="module")
def spec_source() -> str:
    assert SPEC_FILE.is_file(), f"expected spec file missing: {SPEC_FILE}"
    return SPEC_FILE.read_text(encoding="utf-8")


@pytest.fixture(scope="module")
def afs_text() -> str:
    assert AFS_FILE.is_file(), f"expected AFS file missing: {AFS_FILE}"
    return AFS_FILE.read_text(encoding="utf-8")


@pytest.fixture(scope="module")
def soft_assertion_count(spec_source: str) -> int:
    """The ground truth: how many ``expect.soft(...)`` calls the spec makes."""
    tree = ast.parse(spec_source)
    count = 0
    for node in ast.walk(tree):
        if not isinstance(node, ast.Call):
            continue
        func = node.func
        if (
            isinstance(func, ast.Attribute)
            and func.attr == "soft"
            and isinstance(func.value, ast.Name)
            and func.value.id == "expect"
        ):
            count += 1
    return count


@pytest.fixture(scope="module")
def spec_docstring(spec_source: str) -> str:
    docstring = ast.get_docstring(ast.parse(spec_source))
    assert docstring, f"{SPEC_FILE.name} has no module docstring"
    return docstring


def _assert_claim_only_appears_negated(text: str, artifact_name: str) -> None:
    normalized = _normalize(text)
    for match in re.finditer(re.escape(RETRACTED_CLAIM), normalized, re.IGNORECASE):
        window = normalized[
            max(0, match.start() - NEGATION_WINDOW_CHARS) : match.start()
        ].lower()
        assert any(marker in window for marker in NEGATION_MARKERS), (
            f"{artifact_name} states the retracted gate signature "
            f'"{RETRACTED_CLAIM}" as a live claim (no negation within the '
            f"preceding {NEGATION_WINDOW_CHARS} characters). The spec ships "
            "two expect.soft() assertions from one cause, so the real "
            "signature is an ExceptionGroup of 2 sub-exceptions — this is the "
            "round-1 drift shape, and .agents/testing.md § Merge gate makes "
            "the stated count load-bearing for classifying the gate run."
        )


def test_spec_makes_more_than_one_soft_assertion(soft_assertion_count):
    """Pins the premise of this whole guard: the spec's sanctioned-RED step is
    multi-assertion. If a future change makes it single-assertion, this test
    fails first and points at the docstring/AFS sentences that must change
    with it — rather than letting the artifacts drift silently again.
    """
    assert soft_assertion_count == 2, (
        f"{SPEC_FILE.name} now makes {soft_assertion_count} expect.soft() "
        "call(s), not 2. The gate signature stated in the module docstring "
        f"and in {AFS_FILE.name} must be updated to match, or the lead will "
        "classify the 3x gate run against a signature the code no longer "
        "produces."
    )


def test_spec_docstring_states_the_actual_soft_assertion_count(
    spec_docstring, soft_assertion_count
):
    """The module docstring is what a gate operator reads first — it must
    state the real number of sub-exceptions, not the analyst's original one.
    """
    normalized = _normalize(spec_docstring)
    expected = f"{soft_assertion_count} sub-exception"
    assert expected.lower() in normalized.lower(), (
        f"{SPEC_FILE.name}'s module docstring does not state the real gate "
        f'signature ("{expected}s"). The spec makes {soft_assertion_count} '
        "expect.soft() calls, which pytest-playwright re-raises together as "
        "one ExceptionGroup."
    )


def test_afs_states_the_actual_soft_assertion_count(afs_text, soft_assertion_count):
    """The AFS is the reviewer's and the lead's triangulation artifact — its
    § Known Defects bullet must agree with the code, not only its Test Step 13
    amendment (round 1 amended one and left the other stale).
    """
    normalized = _normalize(afs_text)
    expected = f"{soft_assertion_count} sub-exception"
    assert expected.lower() in normalized.lower(), (
        f"{AFS_FILE.name} does not state the real gate signature "
        f'("{expected}s") anywhere.'
    )


def test_spec_docstring_does_not_restate_the_retracted_claim(spec_docstring):
    """A mention of "exactly one soft failure" is allowed only as a correction."""
    _assert_claim_only_appears_negated(
        spec_docstring, f"{SPEC_FILE.name}'s module docstring"
    )


def test_afs_does_not_restate_the_retracted_claim(afs_text):
    """Same rule for the AFS — including its § Known Defects bullet, the
    location that shipped stale in round 1.
    """
    _assert_claim_only_appears_negated(afs_text, AFS_FILE.name)
