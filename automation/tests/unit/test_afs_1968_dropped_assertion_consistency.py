"""Unit tests pinning the ELITEA-1968 AFS to what its spec actually asserts.

Regression coverage for the PR #1670 round-1 review finding: the AFS's
§ Coverage Map Axis-2 declared the stored-``{{secret.<name>}}``-template
assertion **DROPPED** (no compliant handle — MUI's ``MuiSelect-nativeInput``
carries the bound value and receives no testid), while the very same document
still told the reader it was asserted, in two places:

  * § Test Steps row 5 — "the underlying field value is ``{{secret.auth_token}}``"
  * § Coverage Map Axis 1, Step 5 — "Asserted where: … value ``{{secret.auth_token}}``"

An AFS that claims coverage the spec does not deliver is the failure mode the
doc-sync pass exists to prevent: the reviewer triangulates case <-> AFS <-> diff,
and a coverage claim nobody can execute reads as delivered coverage forever.

These tests pin the two artifacts to each other in BOTH directions, so the pair
can never drift apart again:

1. While the AFS declares the addition DROPPED, no row of its Test Steps or
   Coverage Map tables may present the template as an asserted observable.
   (§ Concrete Handles is out of scope — the saved-secret option's own testid,
   ``select-option-{{secret.<name>}}``, legitimately embeds the template.)
2. While the AFS declares it DROPPED, the spec's executable code (docstrings
   excluded) may not reference the template either — restoring the assertion
   without deleting the declaration fails here.

Both tests are two-sided: delete the DROPPED declaration without restoring the
assertion (or vice versa) and they fail from the other direction. Restoring the
assertion for real means deleting the declaration AND updating the ledger rows,
which is the only state that satisfies both.
"""

import ast
import re
from pathlib import Path

import pytest

#: Repo root — ``automation/tests/unit/<this file>`` -> three parents up.
REPO_ROOT = Path(__file__).resolve().parents[3]

AFS_PATH = REPO_ROOT / (
    "test-specs/toolkits-credentials/"
    "l1_credential-secret-password-storage-toggle_ELITEA-1968.md"
)
SPEC_PATH = REPO_ROOT / (
    "automation/tests/ui/toolkits/test_credential_secret_password_toggle.py"
)

#: The template the field stores behind the displayed secret name.
TEMPLATE_TOKEN = "{{secret."

#: The § Coverage Map Axis 2 heading that declares the addition dropped. Anchored
#: on the exact phrase, not a bare "dropped" — the word appears in ordinary prose
#: and in the not-asserted markers below, which would make detection self-fulfilling.
DROP_DECLARATION = re.compile(
    r"\*\*Dropped Axis-2 addition \(declared\)\.\*\*", re.IGNORECASE
)

#: Markers that make a row's mention of the template explicitly NON-coverage.
NOT_ASSERTED_MARKERS = ("not asserted", "not** asserted", "dropped")


@pytest.fixture(scope="module")
def afs_text() -> str:
    assert AFS_PATH.is_file(), f"AFS moved or renamed: {AFS_PATH}"
    return AFS_PATH.read_text(encoding="utf-8")


@pytest.fixture(scope="module")
def spec_source() -> str:
    assert SPEC_PATH.is_file(), f"Spec moved or renamed: {SPEC_PATH}"
    return SPEC_PATH.read_text(encoding="utf-8")


def _declares_the_drop(afs_text: str) -> bool:
    """True while the AFS still declares the stored-template addition dropped."""
    return bool(DROP_DECLARATION.search(afs_text))


def _coverage_table_rows(afs_text: str) -> list[tuple[int, str]]:
    """Table rows of the AFS's COVERAGE LEDGER, as ``(1-based line no, text)``.

    Scoped to § Test Steps and § Coverage Map — the two tables a reader scans
    to learn what the spec verifies, and where the false claim lived. Prose
    paragraphs may discuss the drop freely, and § Concrete Handles legitimately
    carries the template inside the saved-secret option's own *testid*
    (``select-option-{{secret.<name>}}``), which is a handle, not a claim.
    """
    rows: list[tuple[int, str]] = []
    in_ledger = False
    for number, line in enumerate(afs_text.splitlines(), start=1):
        stripped = line.strip()
        if stripped.startswith("#"):
            heading = stripped.lstrip("#").strip().lower()
            # Sub-headings of Coverage Map (### Axis 1 / ### Axis 2) keep the
            # ledger open; any other top-level section closes it.
            if heading.startswith(("test steps", "coverage map", "axis ")):
                in_ledger = True
            elif stripped.startswith("## "):
                in_ledger = False
            continue
        if in_ledger and stripped.startswith("|") and stripped.endswith("|"):
            rows.append((number, stripped))
    return rows


def _executable_strings(source: str) -> list[str]:
    """Every string literal in ``source`` except module/class/function docstrings."""
    tree = ast.parse(source)
    docstring_ids = set()
    for node in ast.walk(tree):
        if not isinstance(
            node, (ast.Module, ast.FunctionDef, ast.AsyncFunctionDef, ast.ClassDef)
        ):
            continue
        first = node.body[0] if node.body else None
        if (
            isinstance(first, ast.Expr)
            and isinstance(first.value, ast.Constant)
            and isinstance(first.value.value, str)
        ):
            docstring_ids.add(id(first.value))
    return [
        node.value
        for node in ast.walk(tree)
        if isinstance(node, ast.Constant)
        and isinstance(node.value, str)
        and id(node) not in docstring_ids
    ]


def test_afs_tables_agree_with_the_drop_declaration(afs_text):
    """The AFS's coverage ledger and its own drop declaration must agree."""
    claiming_rows = [
        (number, row)
        for number, row in _coverage_table_rows(afs_text)
        if TEMPLATE_TOKEN in row
        and not any(marker in row.lower() for marker in NOT_ASSERTED_MARKERS)
    ]

    if _declares_the_drop(afs_text):
        assert not claiming_rows, (
            "ELITEA-1968 AFS declares the stored-`{{secret.<name>}}` assertion "
            "DROPPED, but these coverage rows still present it as asserted "
            "(mark them not-asserted, or restore the assertion and delete the "
            "declaration):\n"
            + "\n".join(f"  {AFS_PATH.name}:{n}  {row}" for n, row in claiming_rows)
        )
    else:
        assert claiming_rows, (
            "ELITEA-1968 AFS no longer declares the stored-`{{secret.<name>}}` "
            "assertion dropped, so the assertion was restored — but no § Test "
            "Steps / § Coverage Map row states it as coverage. The ledger now "
            "UNDER-reports what the spec verifies."
        )


def test_spec_code_agrees_with_the_drop_declaration(afs_text, spec_source):
    """The other direction: the spec's executable code and the declaration must
    agree too."""
    references = [s for s in _executable_strings(spec_source) if TEMPLATE_TOKEN in s]

    if _declares_the_drop(afs_text):
        assert not references, (
            "ELITEA-1968 AFS still declares the stored-`{{secret.<name>}}` "
            "assertion DROPPED, but the spec's executable code references the "
            "template — the AFS is now UNDER-reporting real coverage. Update "
            "the AFS (§ Test Steps row 5, § Coverage Map) instead. Offending "
            f"literals: {references}"
        )
    else:
        assert references, (
            "ELITEA-1968 AFS no longer declares the stored-`{{secret.<name>}}` "
            "assertion dropped, but the spec's executable code never references "
            "the template — the AFS is claiming coverage the spec does not "
            "deliver, which is exactly the PR #1670 round-1 finding."
        )
