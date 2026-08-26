"""Regression test for the "the seeded TEXT is never asserted" clause
(ELITEA-2268/2273/2274/2275, review round 1, fix round 1).

Guards the defect a fresh-session reviewer flagged on ELITEA-2275: the spec's
docstring and its AFS § Fidelity Declaration both promised that the seeded text
is never asserted, while the spec's own final assertion was

    expect(context_page.editor_lines()).to_have_text([SEED_CONTENT])

— reading the case's observable straight off the string the test wrote. A
declaration is only worth what the code does; this one had drifted from it, and
nothing failed. The AFS specified a different assertion again ("the typed
character is absent"), so all three artifacts disagreed and every gate passed.

The shipped fix is the ELITEA-2274 pattern: the comparison baseline is READ OFF
THE PRODUCT before the edit (`get_editor_lines()`), and the post-Discard content
is compared against *that*. This file pins the invariant mechanically, so a
future edit that re-introduces the seed constant into an assertion fails here
rather than shipping a green tautology:

* every `SEED_CONTENT` reference in a declaring spec must be an argument to the
  seeding fixture — never an assertion operand;
* a spec that declares the clause must actually read its baseline off the
  product;
* the AFS that declares it must say so too (doc-sync).

Scope: the specs that MAKE the promise. A spec is in scope because its own
docstring claims it, so the guard cannot be silenced by deleting the claim
without also deleting the substitution it excuses — the reviewer reads the
declaration either way.
"""

import ast
import re
from pathlib import Path

import pytest

TESTS_UNIT_DIR = Path(__file__).resolve().parent
AUTOMATION_DIR = TESTS_UNIT_DIR.parent.parent  # .../automation
REPO_ROOT = AUTOMATION_DIR.parent  # .../elitea-testing-public
ADMIN_TESTS_DIR = AUTOMATION_DIR / "tests" / "ui" / "admin"
AFS_DIR = REPO_ROOT / "test-specs" / "settings-project-params"

SEED_FIXTURE = "project_context_seed"
SEED_CONSTANT = "SEED_CONTENT"

#: The page-object read that makes a baseline product-produced.
PRODUCT_BASELINE_READ = "get_editor_lines"

#: Phrases by which a spec docstring makes the promise this file enforces.
#: Matched against whitespace-normalised text — both spec docstrings and AFS prose
#: are hard-wrapped, so a literal search would miss a promise split across lines.
DECLARATION_MARKERS = (
    "seeded TEXT is never asserted",
    "not taken from the seed string",
    "never taken from the seed string",
)

#: The same promise as the AFS § Fidelity Declaration states it.
AFS_DECLARATION_MARKERS = ("never asserted", "not taken from the seed string")

#: Specs that declare the clause → the AFS that must declare it too.
DECLARING_SPECS = {
    ADMIN_TESTS_DIR
    / "test_project_context_save_discard_dirty_state.py": AFS_DIR
    / "l3_project-context-save-discard-enabled-only-when-dirty_ELITEA-2275.md",
    ADMIN_TESTS_DIR
    / "test_project_context_discard_reverts.py": AFS_DIR
    / "l3_project-context-discard-reverts-unsaved-changes_ELITEA-2274.md",
}

SPEC_IDS = {path: path.stem for path in DECLARING_SPECS}


def _normalised(text: str) -> str:
    """Collapse runs of whitespace so a hard-wrapped promise still matches."""
    return re.sub(r"\s+", " ", text)


def _module(path: Path) -> ast.Module:
    return ast.parse(path.read_text(encoding="utf-8"), filename=str(path))


def _seed_call_argument_nodes(tree: ast.Module) -> set[int]:
    """Every node id sitting inside a ``project_context_seed(...)`` call.

    Passing the constant TO the seeder is the one legitimate use — that is the
    substitution being declared, not an assertion on it.
    """
    inside: set[int] = set()
    for node in ast.walk(tree):
        if (
            isinstance(node, ast.Call)
            and isinstance(node.func, ast.Name)
            and node.func.id == SEED_FIXTURE
        ):
            for argument in [*node.args, *(kw.value for kw in node.keywords)]:
                inside.update(id(child) for child in ast.walk(argument))
    return inside


@pytest.mark.parametrize("spec_path", list(DECLARING_SPECS), ids=lambda p: SPEC_IDS[p])
def test_spec_still_declares_the_clause(spec_path):
    """Sanity: the parametrization is driven by a promise that is really made."""
    docstring = _normalised(ast.get_docstring(_module(spec_path)) or "")
    assert any(marker in docstring for marker in DECLARATION_MARKERS), (
        f"{spec_path.name} no longer declares that the seeded text is never asserted. "
        f"If the substitution itself was dropped, drop this spec from DECLARING_SPECS; "
        f"if only the sentence went, restore it — the seed is still a declared transit "
        f"substitution (.agents/testing.md § Fidelity policy)."
    )


@pytest.mark.parametrize("spec_path", list(DECLARING_SPECS), ids=lambda p: SPEC_IDS[p])
def test_seed_constant_is_never_an_assertion_operand(spec_path):
    """``SEED_CONTENT`` may be SEEDED and nothing else."""
    tree = _module(spec_path)
    seeded = _seed_call_argument_nodes(tree)

    offenders = [
        node.lineno
        for node in ast.walk(tree)
        if isinstance(node, ast.Name)
        and node.id == SEED_CONSTANT
        and isinstance(node.ctx, ast.Load)
        and id(node) not in seeded
    ]
    assert not offenders, (
        f"{spec_path.name} uses {SEED_CONSTANT} outside the {SEED_FIXTURE}() call "
        f"(line(s) {offenders}). Its docstring promises the seeded text is never "
        f"asserted; reading the case's observable off the string the test wrote is a "
        f"terminal substitution (.agents/testing.md § Fidelity policy). Read the "
        f"baseline off the product with {PRODUCT_BASELINE_READ}() and compare against "
        f"that instead — the ELITEA-2274 pattern."
    )


@pytest.mark.parametrize("spec_path", list(DECLARING_SPECS), ids=lambda p: SPEC_IDS[p])
def test_spec_reads_its_baseline_off_the_product(spec_path):
    """The promise is only kept if a product-read replaces the seed constant."""
    assert PRODUCT_BASELINE_READ in spec_path.read_text(encoding="utf-8"), (
        f"{spec_path.name} declares that the seeded text is never asserted but never "
        f"calls {PRODUCT_BASELINE_READ}(). Something has to supply the comparison "
        f"baseline; if it is not the product, it is the test's own payload."
    )


@pytest.mark.parametrize("spec_path", list(DECLARING_SPECS), ids=lambda p: SPEC_IDS[p])
def test_afs_declares_the_same_clause(spec_path):
    """Doc-sync: the AFS § Fidelity Declaration must carry the same promise."""
    afs_path = DECLARING_SPECS[spec_path]
    assert afs_path.is_file(), f"AFS missing at {afs_path}"

    afs_text = _normalised(afs_path.read_text(encoding="utf-8"))
    assert any(marker in afs_text for marker in AFS_DECLARATION_MARKERS), (
        f"{afs_path.name} no longer declares that the seed's text is never asserted, "
        f"while {spec_path.name} still does. The reviewer triangulates case ↔ AFS ↔ "
        f"diff; a Fidelity Declaration that disagrees with the shipped spec is the "
        f"blind spot this guard exists to close."
    )
