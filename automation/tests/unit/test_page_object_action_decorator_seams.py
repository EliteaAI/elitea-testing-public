"""Static-analysis regression test for stolen/stacked ``@action`` decorators
(ELITEA-1853/1854/1855 review round 1 finding).

Guards against the defect a fresh-session reviewer flagged in
`automation/pages/artifacts_page.py`: new page-object methods were inserted
BETWEEN a pre-existing ``@action("Edit file preview content")`` decorator and
its ``def``. Both halves of that seam fail silently — nothing raises, no test
goes red:

1. the first inserted method ends up double-decorated and therefore logs and
   reports under the PREVIOUS method's step name, and
2. the pre-existing method silently LOSES its ``@action`` decorator, so its own
   merged callers stop emitting a step and stop capturing the
   screenshot-on-failure that ``@action`` wires up.

``@action`` records nothing on the wrapper (`utils/actions.py` closes over
``step_description``), so this can only be checked at the source level.
Two checks, both mechanical:

* **no page-object method carries more than one** ``@action`` — stacking is
  never intentional and is the exact fingerprint of the insertion seam;
* the two methods the seam actually damaged carry their expected labels, so a
  future re-insertion at the same spot is caught by name.
"""

import ast
from pathlib import Path

import pytest

TESTS_UNIT_DIR = Path(__file__).resolve().parent
AUTOMATION_DIR = TESTS_UNIT_DIR.parent.parent  # .../automation
PAGES_DIR = AUTOMATION_DIR / "pages"

# The exact seam that shipped: label -> method it must decorate.
SEAM_ANCHORS = {
    "edit_file_preview_content": "Edit file preview content",
    "click_file_preview_discard": "Open the Discard warning modal",
}


def _action_labels(node: ast.FunctionDef) -> list[str | None]:
    """Return one entry per ``@action`` decorator on *node*, newest first."""
    labels: list[str | None] = []
    for dec in node.decorator_list:
        if not isinstance(dec, ast.Call):
            continue
        func = dec.func
        name = func.id if isinstance(func, ast.Name) else getattr(func, "attr", None)
        if name != "action":
            continue
        if dec.args and isinstance(dec.args[0], ast.Constant):
            labels.append(dec.args[0].value)
        else:
            labels.append(None)
    return labels


def _functions(path: Path):
    tree = ast.parse(path.read_text(encoding="utf-8"))
    for node in ast.walk(tree):
        if isinstance(node, (ast.FunctionDef, ast.AsyncFunctionDef)):
            yield node


def test_no_page_object_method_carries_stacked_action_decorators():
    """A method with two ``@action`` decorators means an insertion seam stole one."""
    page_files = sorted(PAGES_DIR.glob("*.py"))
    assert page_files, f"no page objects found under {PAGES_DIR}"

    stacked = [
        f"{path.name}::{node.name} (line {node.lineno}) — {_action_labels(node)}"
        for path in page_files
        for node in _functions(path)
        if len(_action_labels(node)) > 1
    ]

    assert not stacked, (
        "Page-object methods must carry at most ONE @action decorator; a stack "
        "means a method was inserted between a previous @action and its def, "
        "which mislabels this method and strips the previous one:\n  "
        + "\n  ".join(stacked)
    )


@pytest.mark.parametrize(("method_name", "expected_label"), sorted(SEAM_ANCHORS.items()))
def test_seam_methods_keep_their_own_action_label(method_name, expected_label):
    """The two methods the ELITEA-1853 seam damaged keep exactly their own label."""
    target = PAGES_DIR / "artifacts_page.py"
    matches = [n for n in _functions(target) if n.name == method_name]
    assert len(matches) == 1, f"expected exactly one {method_name} in {target.name}"

    labels = _action_labels(matches[0])
    assert labels == [expected_label], (
        f"ArtifactsPage.{method_name} must be decorated with exactly "
        f"@action({expected_label!r}); found {labels!r}"
    )
