"""Unit tests pinning WHERE the ``default_changed`` teardown guard is assigned.

Regression coverage for the review finding on PR #1989 (ELITEA-2400,
``tests/ui/settings/test_vector_storage_edit.py``): the three Vector Storage
specs guard their ``finally`` restore of the section default with a boolean::

    finally:
        if default_changed and original_default_value:
            restore_section_default(...)
        delete_configurations_if_present(...)

Creating a Vector Storage configuration ASSIGNS it as the section default (live
contract), so the mutation happens inside ``form.save_and_return_to_list()``.
In the pre-fix ELITEA-2400 source the guard was set FOUR statements later --
after ``isolate_section``, a ``to_have_count(1)`` expectation, a card count read
and its assertion. Every one of those is a path on which a flake leaves
``default_changed`` False, so the ``finally`` skips the restore *while still
deleting the configuration that is now the project's default* -- the shared
seeded project is left with no default at all, and the sibling specs
(ELITEA-2399/2401) then refuse to run, because they assert an existing default
up front. The two siblings set the flag on the very next line, so the asymmetry
was the tell.

These tests are static (AST over the spec source) rather than behavioural,
because the defect is a statement-ordering shape, not a value: parsing the file
is enough, no browser and no live app. They fail against the pre-fix
ELITEA-2400 source and pass against all three specs after it.

The rule is checked in both directions:

1. The transit create must be followed IMMEDIATELY by ``default_changed = True``
   (no window at all between mutation and guard).
2. Every ``default_changed = True`` must directly follow a call that actually
   mutates the default -- so the first rule cannot be satisfied by hoisting the
   flag above the mutation, which would make the restore run against state that
   was never changed.
"""

from __future__ import annotations

import ast
from pathlib import Path

import pytest

#: The Vector Storage specs (settings-w10) that create a configuration -- and so
#: reassign the section default -- and owe a guarded restore in ``finally``.
VECTOR_STORAGE_SPECS = [
    "test_vector_storage_create.py",  # ELITEA-2399
    "test_vector_storage_edit.py",  # ELITEA-2400
    "test_set_vector_storage_default.py",  # ELITEA-2401
]

SETTINGS_TESTS_DIR = Path(__file__).resolve().parents[1] / "ui" / "settings"

#: The guard flag every one of these specs uses for the default restore.
GUARD_NAME = "default_changed"

#: Calls that CHANGE which configuration is the section default:
#: ``save_and_return_to_list`` creates one (the product makes a new Vector
#: Storage configuration the default), ``select_default_configuration`` sets one
#: explicitly.
MUTATING_METHODS = {"save_and_return_to_list", "select_default_configuration"}


def _parse(spec_name: str) -> ast.Module:
    path = SETTINGS_TESTS_DIR / spec_name
    assert path.is_file(), f"vector storage spec not found: {path}"
    return ast.parse(path.read_text(encoding="utf-8"), filename=str(path))


def _statement_blocks(tree: ast.Module) -> list[list[ast.stmt]]:
    """Every ``body``-like list of statements in the module.

    Statement adjacency only means anything within one block, so the checks
    below walk blocks rather than the flat node stream: ``with allure.step(...)``
    nesting must not make two statements look adjacent when they are not.
    """
    blocks: list[list[ast.stmt]] = []
    for node in ast.walk(tree):
        for field in ("body", "orelse", "finalbody"):
            value = getattr(node, field, None)
            if isinstance(value, list) and value and all(isinstance(item, ast.stmt) for item in value):
                blocks.append(value)
    return blocks


def _mutating_call(statement: ast.stmt) -> str | None:
    """The mutating method this statement calls, if any.

    Handles both the bare-call form (``form.save_and_return_to_list()``) and the
    assigned form (``resp = providers_page.select_default_configuration(...)``).
    """
    if isinstance(statement, ast.Expr):
        call = statement.value
    elif isinstance(statement, ast.Assign):
        call = statement.value
    else:
        return None
    if not isinstance(call, ast.Call) or not isinstance(call.func, ast.Attribute):
        return None
    return call.func.attr if call.func.attr in MUTATING_METHODS else None


def _is_guard_assignment(statement: ast.stmt, *, value: bool) -> bool:
    return (
        isinstance(statement, ast.Assign)
        and any(isinstance(target, ast.Name) and target.id == GUARD_NAME for target in statement.targets)
        and isinstance(statement.value, ast.Constant)
        and statement.value.value is value
    )


@pytest.mark.parametrize("spec_name", VECTOR_STORAGE_SPECS)
def test_guard_is_set_immediately_after_the_transit_create(spec_name: str) -> None:
    """No statement may sit between the transit create and ``default_changed = True``.

    This is the exact PR #1989 finding. Anything in that window is a path on
    which a flake skips the restore while the ``finally`` still deletes the
    configuration that is now the default.
    """
    tree = _parse(spec_name)
    creates = [
        (block, index)
        for block in _statement_blocks(tree)
        for index, statement in enumerate(block)
        if _mutating_call(statement) == "save_and_return_to_list"
    ]
    assert creates, (
        f"{spec_name}: no save_and_return_to_list() call found -- these specs all create the "
        "configuration they exercise, which is what reassigns the section default."
    )

    block, index = min(creates, key=lambda pair: pair[0][pair[1]].lineno)
    create_line = block[index].lineno
    following = block[index + 1] if index + 1 < len(block) else None
    assert following is not None and _is_guard_assignment(following, value=True), (
        f"{spec_name}: the transit create at line {create_line} is not immediately followed by "
        f"`{GUARD_NAME} = True` (found: "
        f"{ast.dump(following) if following is not None else 'end of block'} at line "
        f"{following.lineno if following is not None else create_line}). Creating a Vector Storage "
        "configuration makes it the section default, so every statement between the create and the "
        "guard is a path on which a flake skips `restore_section_default(...)` while the `finally` "
        "still deletes that configuration -- leaving the shared seeded project with NO default."
    )


@pytest.mark.parametrize("spec_name", VECTOR_STORAGE_SPECS)
def test_guard_is_only_raised_directly_after_a_mutating_call(spec_name: str) -> None:
    """``default_changed = True`` must directly follow the mutation it guards.

    Guards the other half: satisfying the first rule by hoisting the flag ABOVE
    the create would make the ``finally`` restore the default on runs that never
    changed it -- an unrequested write to shared project configuration.
    """
    tree = _parse(spec_name)
    raises = [
        (block, index)
        for block in _statement_blocks(tree)
        for index, statement in enumerate(block)
        if _is_guard_assignment(statement, value=True)
    ]
    assert raises, f"{spec_name}: no `{GUARD_NAME} = True` found -- the restore guard is missing entirely."

    for block, index in raises:
        statement = block[index]
        previous = block[index - 1] if index else None
        previous_call = _mutating_call(previous) if previous is not None else None
        assert previous_call in MUTATING_METHODS, (
            f"{spec_name}: `{GUARD_NAME} = True` at line {statement.lineno} does not directly follow a "
            f"call that changes the default (expected one of {sorted(MUTATING_METHODS)}, preceded by "
            f"{'nothing' if previous is None else f'line {previous.lineno}'}). The guard must be raised "
            "AT the mutation -- neither before it nor after any statement that can fail."
        )
