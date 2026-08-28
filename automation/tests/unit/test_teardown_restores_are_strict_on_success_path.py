"""Unit tests pinning the teardown SHAPE of the AI-personality family specs.

Regression coverage for the review finding on PR #1964 (ELITEA-2384): the
spec's restores sat in a bare ``finally`` block, every one of them wrapped in
:func:`utils.personalization_autosave.best_effort`. ``finally`` runs on both
paths, so the wrapper that is correct on the FAILURE path (a teardown exception
there would replace the real failure in the report) silently downgraded the
SUCCESS path too: a restore that failed on a green run logged a warning and the
test still reported PASS, leaking the changed persona / instructions onto the
shared ``${TEST_USER}`` record for every other spec that reads them.

The correct shape -- already used by the three sibling specs in the same unit --
splits the two paths::

    try:
        ...body...
    except BaseException:
        best_effort(restore_a, "...")   # failure path: never mask the real failure
        best_effort(restore_b, "...")
        raise
    else:
        restore_a()                     # success path: STRICT, allowed to fail the test
        restore_b()

These tests are static (AST over the spec source) rather than behavioural,
because the defect is a control-flow shape, not a value: importing the module is
enough, no browser and no live app. They fail against the pre-fix ELITEA-2384
source and pass against all four specs after it.

A deliberate carve-out: a ``finally`` block may still hold cleanup whose failure
cannot corrupt what a later spec READS -- ELITEA-2384's conversation deletion is
best-effort on both paths by design. The rule below therefore targets
``best_effort`` specifically, which is the marker of a *state restore* in this
family, not "any cleanup in a finally".
"""

from __future__ import annotations

import ast
from pathlib import Path

import pytest

#: The four specs of the AI-personality family (settings-w08). Each mutates
#: shared `${TEST_USER}` account state and therefore owes a strict restore.
FAMILY_SPECS = [
    "test_default_personality_options.py",  # ELITEA-2381
    "test_default_user_instructions_persist.py",  # ELITEA-2382
    "test_personality_independent_of_context_management.py",  # ELITEA-2383
    "test_personalization_new_conversations_only.py",  # ELITEA-2384
]

SETTINGS_TESTS_DIR = Path(__file__).resolve().parents[1] / "ui" / "settings"


def _parse(spec_name: str) -> ast.Module:
    path = SETTINGS_TESTS_DIR / spec_name
    assert path.is_file(), f"family spec not found: {path}"
    return ast.parse(path.read_text(encoding="utf-8"), filename=str(path))


def _calls_named(node: ast.AST, name: str) -> list[ast.Call]:
    """Every ``name(...)`` call anywhere under ``node``."""
    return [
        child
        for child in ast.walk(node)
        if isinstance(child, ast.Call)
        and isinstance(child.func, ast.Name)
        and child.func.id == name
    ]


def _try_nodes(tree: ast.Module) -> list[ast.Try]:
    return [node for node in ast.walk(tree) if isinstance(node, ast.Try)]


@pytest.mark.parametrize("spec_name", FAMILY_SPECS)
def test_no_best_effort_restore_inside_a_finally_block(spec_name: str) -> None:
    """A ``best_effort`` restore in ``finally`` downgrades the success path.

    This is the exact PR #1964 finding: ``finally`` runs on the green path too,
    so the failure-path wrapper swallows a genuine restore failure and the run
    still reports PASS with the shared account left mutated.
    """
    tree = _parse(spec_name)
    offenders = [
        node.lineno
        for try_node in _try_nodes(tree)
        for statement in try_node.finalbody
        for node in _calls_named(statement, "best_effort")
    ]
    assert not offenders, (
        f"{spec_name}: best_effort(...) called inside a `finally` block at line(s) {offenders}. "
        "`finally` runs on the SUCCESS path as well, where a swallowed restore failure leaks "
        "shared ${TEST_USER} state and still reports PASS. Split the paths: best_effort in "
        "`except BaseException: ... raise`, strict restores in `else:`."
    )


@pytest.mark.parametrize("spec_name", FAMILY_SPECS)
def test_best_effort_teardown_is_paired_with_a_strict_else_branch(spec_name: str) -> None:
    """Every failure-path teardown owes a matching strict success-path teardown.

    Guards the other half of the same defect: moving the restores out of
    ``finally`` into ``except BaseException`` alone would leave the success path
    with NO restore at all, which leaks the same state even more loudly.
    """
    tree = _parse(spec_name)
    trys_with_best_effort = [
        try_node
        for try_node in _try_nodes(tree)
        if any(_calls_named(handler, "best_effort") for handler in try_node.handlers)
    ]
    assert trys_with_best_effort, (
        f"{spec_name}: expected at least one try/except teardown using best_effort(...) on the "
        "failure path -- these specs all mutate shared ${TEST_USER} account state."
    )
    for try_node in trys_with_best_effort:
        assert try_node.orelse, (
            f"{spec_name}: the try/except at line {try_node.lineno} restores shared state "
            "best-effort on the failure path but has no `else:` branch, so a green run restores "
            "nothing at all."
        )
        assert any(
            isinstance(node, ast.Raise) for handler in try_node.handlers for node in ast.walk(handler)
        ), (
            f"{spec_name}: the teardown handler at line {try_node.lineno} must re-`raise` -- "
            "swallowing the body's failure would turn a red test green."
        )
