"""Regression test for canon ruling #511 on the Project Context Build-with-AI
modal (ELITEA-2269/2270, review round 1, fix round 1).

Guards the defect a fresh-session reviewer flagged on ELITEA-2269: the testid
``generate-project-context-loading-indicator`` was added to EliteaUI
(EliteaAI/EliteaUI@d6eb52b6, ``loadingIndicatorTestId=``) and declared as a
``LocatorDescriptor`` field on :class:`GenerateProjectContextModalPage`, but no
spec ever reached it — the only readers are the inherited
``wait_for_loading_visible()`` / ``wait_for_loading_hidden()``, which nothing
called. That is exactly an **orphan testid**: wired into a page object but never
invoked on a test's executed code path, so it inflates the presence-based
coverage metric the team measures UI automation by
(``.agents/testing.md`` § Locator policy, canon ruling #511 — "a testid wired
into a page-object method or ``LocatorDescriptor`` field is NOT 'referenced'
unless the test invokes that method on its executed path").

Why the existing gates missed it: three artifacts agreed and all three were
wrong — the AFS § Concrete Handles claimed *"Every testid added by this case is
referenced on the test's executed code path (#511)"*, the EliteaUI commit
message claimed *"All referenced on the executed path"*, and the page object
declared the field. Only a **reachability** analysis over the call graph
disagrees, which is what this file performs.

The check, per #511's own definition of "referenced":

* collect every ``LocatorDescriptor`` field declared on the modal page object;
* collect every ``modal.<name>`` the specs touch (attribute or method call) —
  the executed path's entry points;
* walk ``self.<name>`` transitively through the page object **and its base**
  (a spec calling ``click_apply()`` does reference ``approve_button``);
* every declared locator must be reachable that way. One that is not is an
  orphan and fails here, before it can ship as inflated coverage again.

Scope: the Build-with-AI modal page object and the two specs that drive it. The
shared base ``GenerateEntityModalPageBase`` declares its locators as ``None``
placeholders, which is precisely what invites this class of defect — a subclass
fills every placeholder in reflexively, whether or not its case exercises it.
"""

import ast
from pathlib import Path

import pytest

TESTS_UNIT_DIR = Path(__file__).resolve().parent
AUTOMATION_DIR = TESTS_UNIT_DIR.parent.parent  # .../automation
PAGES_DIR = AUTOMATION_DIR / "pages"
ADMIN_TESTS_DIR = AUTOMATION_DIR / "tests" / "ui" / "admin"

PAGE_OBJECT = PAGES_DIR / "generate_project_context_modal_page.py"
PAGE_OBJECT_BASE = PAGES_DIR / "generate_entity_modal_page_base.py"
PAGE_OBJECT_CLASS = "GenerateProjectContextModalPage"

#: Every spec that drives the modal. A new one must be added here, or its
#: locators look unreachable and this guard reports a false orphan.
DRIVING_SPECS = (
    ADMIN_TESTS_DIR / "test_project_context_build_with_ai_generates.py",
    ADMIN_TESTS_DIR / "test_project_context_build_with_ai_cancel.py",
)


def _module(path: Path) -> ast.Module:
    return ast.parse(path.read_text(encoding="utf-8"), filename=str(path))


def _class_def(path: Path, class_name: str | None = None) -> ast.ClassDef:
    """Return the (first, or named) class defined in ``path``."""
    for node in _module(path).body:
        if isinstance(node, ast.ClassDef) and (class_name is None or node.name == class_name):
            return node
    raise AssertionError(f"No class {class_name or ''} found in {path}")


def _locator_fields(class_def: ast.ClassDef) -> dict[str, str]:
    """Class-level ``LocatorDescriptor(testid=...)`` fields → their testid."""
    fields: dict[str, str] = {}
    for node in class_def.body:
        if not isinstance(node, ast.Assign) or not isinstance(node.value, ast.Call):
            continue
        func = node.value.func
        if not (isinstance(func, ast.Name) and func.id == "LocatorDescriptor"):
            continue
        testid = next(
            (
                kw.value.value
                for kw in node.value.keywords
                if kw.arg == "testid" and isinstance(kw.value, ast.Constant)
            ),
            "",
        )
        for target in node.targets:
            if isinstance(target, ast.Name):
                fields[target.id] = testid
    return fields


def _self_attributes(node: ast.AST) -> set[str]:
    """Every ``self.<name>`` touched inside ``node``."""
    return {
        child.attr
        for child in ast.walk(node)
        if isinstance(child, ast.Attribute)
        and isinstance(child.value, ast.Name)
        and child.value.id == "self"
    }


def _methods(class_def: ast.ClassDef) -> dict[str, set[str]]:
    """Method name → the ``self.<name>`` references in its body."""
    return {
        node.name: _self_attributes(node)
        for node in class_def.body
        if isinstance(node, (ast.FunctionDef, ast.AsyncFunctionDef))
    }


def _modal_attributes_touched_by(spec_path: Path) -> set[str]:
    """Every attribute a spec reads off a ``GenerateProjectContextModalPage``.

    Resolves the page object's variable name from its construction site rather
    than assuming ``modal``, so renaming the local cannot silently empty the
    analysis.
    """
    tree = _module(spec_path)

    variables = {
        target.id
        for node in ast.walk(tree)
        if isinstance(node, ast.Assign)
        and isinstance(node.value, ast.Call)
        and isinstance(node.value.func, ast.Name)
        and node.value.func.id == PAGE_OBJECT_CLASS
        for target in node.targets
        if isinstance(target, ast.Name)
    }

    return {
        node.attr
        for node in ast.walk(tree)
        if isinstance(node, ast.Attribute)
        and isinstance(node.value, ast.Name)
        and node.value.id in variables
    }


def _reachable(entry_points: set[str], methods: dict[str, set[str]]) -> set[str]:
    """Transitive closure of ``self.<name>`` references from ``entry_points``."""
    reached: set[str] = set()
    pending = list(entry_points)
    while pending:
        name = pending.pop()
        if name in reached:
            continue
        reached.add(name)
        pending.extend(methods.get(name, set()) - reached)
    return reached


@pytest.fixture(scope="module")
def analysis() -> dict:
    subclass = _class_def(PAGE_OBJECT, PAGE_OBJECT_CLASS)
    base = _class_def(PAGE_OBJECT_BASE)

    # Subclass methods override the base's of the same name.
    methods = {**_methods(base), **_methods(subclass)}

    entry_points: set[str] = set()
    for spec in DRIVING_SPECS:
        entry_points |= _modal_attributes_touched_by(spec)

    return {
        "locators": _locator_fields(subclass),
        "reachable": _reachable(entry_points, methods),
        "entry_points": entry_points,
    }


def test_analysis_is_not_vacuous(analysis):
    """A meta-test that analysed nothing would pass silently — assert it did."""
    for spec in DRIVING_SPECS:
        assert spec.is_file(), f"Driving spec missing: {spec}"
    assert PAGE_OBJECT.is_file() and PAGE_OBJECT_BASE.is_file()
    assert analysis["locators"], (
        f"No LocatorDescriptor fields parsed from {PAGE_OBJECT.name} — the guard would "
        f"pass on an empty set. Did the declaration style change?"
    )
    assert analysis["entry_points"], (
        f"No {PAGE_OBJECT_CLASS} attribute access found in any of "
        f"{[spec.name for spec in DRIVING_SPECS]} — the reachability walk has no entry "
        f"points, so every locator would look orphaned or the walk is broken."
    )


def test_every_declared_locator_is_reached_by_a_spec(analysis):
    """#511: a declared testid that no spec reaches is an orphan."""
    orphans = {
        field: testid
        for field, testid in analysis["locators"].items()
        if field not in analysis["reachable"]
    }
    assert not orphans, (
        f"{PAGE_OBJECT_CLASS} declares locator field(s) no spec reaches on its executed "
        f"path: {orphans}. Canon ruling #511 (.agents/testing.md § Locator policy): a "
        f"testid wired into a page object but never invoked is NOT 'referenced' — it "
        f"inflates the presence-based coverage metric. Either exercise it from a spec "
        f"in DRIVING_SPECS (directly, or via a page-object method the spec calls — an "
        f"absence assertion counts), or drop the field AND the testid from EliteaUI. "
        f"There is no third option: 'reusable scaffolding' and 'a future case will use "
        f"it' are exactly the soft justifications #511 rejects."
    )
