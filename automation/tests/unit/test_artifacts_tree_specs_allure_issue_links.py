"""Static-analysis regression test for the three artifacts file-tree specs'
`@allure.issue(...)` TMS case links (ELITEA-1836/1837/1838, review round 1).

Guards against the defect a fresh-session reviewer flagged: all three specs
shipped `@allure.issue` URLs built from an invented `…file-tree-behavior-…`
filename shape rather than the TMS repo's real filenames, so every one of the
three report links 404'd:

- ELITEA-1836 shipped `…_file-tree-behavior-subfolder-expands-and-collapses.md`,
  real name `…_file-tree-subfolder-expands-collapses-on-click.md`
- ELITEA-1837 shipped `…_file-tree-behavior-breadcrumb-path-updates.md`,
  real name `…_file-tree-breadcrumb-updates-on-navigation.md`
- ELITEA-1838 shipped `…_file-tree-behavior-switching-between-buckets.md`,
  real name `…_file-tree-switching-between-buckets.md`

`.agents/architecture.md` names `onetest-ai-tm-Elitea` as a mandatory sibling
clone at `../onetest-ai-tm-Elitea`, so resolution is checked on the local
filesystem — no network call, no GitHub API. Same guard shape as
`test_skill_agent_interaction_allure_issue_links.py` (ELITEA-2609), which
covers a different spec file.
"""

import ast
import re
from pathlib import Path

import pytest

TESTS_UNIT_DIR = Path(__file__).resolve().parent
AUTOMATION_DIR = TESTS_UNIT_DIR.parent.parent  # .../automation
REPO_ROOT = AUTOMATION_DIR.parent  # .../elitea-testing-public
WORKSPACE_ROOT = REPO_ROOT.parent  # sibling-clones parent, per architecture.md
OT_REPO_ROOT = WORKSPACE_ROOT / "onetest-ai-tm-Elitea"

ARTIFACTS_TESTS_DIR = AUTOMATION_DIR / "tests" / "ui" / "artifacts"
TARGET_FILES = (
    ARTIFACTS_TESTS_DIR / "test_artifacts_tree_subfolder_expand_collapse.py",
    ARTIFACTS_TESTS_DIR / "test_artifacts_tree_breadcrumb_navigation.py",
    ARTIFACTS_TESTS_DIR / "test_artifacts_tree_switch_between_buckets.py",
)

# Matches the `onetest-ai-tm-Elitea/blob/main/<path>.md` portion of an
# @allure.issue(...) URL string.
TMS_LINK_PATTERN = re.compile(
    r"onetest-ai-tm-Elitea/blob/main/(tests/automated-full-regression-ui/[\w./-]+\.md)"
)


def _extract_tms_case_paths(source: str) -> list[str]:
    """Return every TMS case repo-relative path referenced by an
    `@allure.issue(...)` decorator call in `source`, in source order.

    Parsed with `ast` rather than regexed off the raw text so that adjacent
    string-literal concatenation inside the decorator call (used for line
    length — all three of these specs split the URL across three string
    tokens) is resolved the way the Python parser resolves it: `ast.parse`
    folds `"a" "b"` into a single `Constant` before this inspects it.
    """
    tree = ast.parse(source)
    paths: list[str] = []
    for node in ast.walk(tree):
        if not isinstance(node, ast.Call):
            continue
        func = node.func
        is_allure_issue = (
            isinstance(func, ast.Attribute)
            and func.attr == "issue"
            and isinstance(func.value, ast.Name)
            and func.value.id == "allure"
        )
        if not is_allure_issue or not node.args:
            continue
        first_arg = node.args[0]
        if isinstance(first_arg, ast.Constant) and isinstance(first_arg.value, str):
            match = TMS_LINK_PATTERN.search(first_arg.value)
            if match:
                paths.append(match.group(1))
    return paths


@pytest.fixture(scope="module")
def tms_case_paths() -> dict[Path, list[str]]:
    extracted: dict[Path, list[str]] = {}
    for target in TARGET_FILES:
        assert target.is_file(), f"expected spec file missing: {target}"
        extracted[target] = _extract_tms_case_paths(target.read_text(encoding="utf-8"))
    return extracted


def test_each_spec_declares_exactly_one_tms_case_link(tms_case_paths):
    """Sanity check on the extractor itself: each of these three specs
    automates exactly one TMS case, so each must yield exactly one link.

    A zero here would mean the extraction regex drifted from the
    `@allure.issue` URL shape and the resolution check below silently passed
    on an empty set — the failure mode this guard exists to prevent.
    """
    counts = {target.name: len(paths) for target, paths in tms_case_paths.items()}
    assert counts == {
        "test_artifacts_tree_subfolder_expand_collapse.py": 1,
        "test_artifacts_tree_breadcrumb_navigation.py": 1,
        "test_artifacts_tree_switch_between_buckets.py": 1,
    }, f"unexpected TMS-link counts per spec: {counts}"


@pytest.mark.skipif(
    not OT_REPO_ROOT.is_dir(),
    reason=(
        f"sibling TMS cases repo not present at {OT_REPO_ROOT} — "
        "the four-sibling-clone layout (.agents/architecture.md) is not "
        "set up in this workspace"
    ),
)
def test_allure_issue_tms_links_resolve_to_real_case_files(tms_case_paths):
    """Every @allure.issue TMS-case URL in the artifacts file-tree specs must
    point at a file that actually exists in the onetest-ai-tm-Elitea sibling
    clone — a stale/invented filename 404s the report link (the
    ELITEA-1836/1837/1838 review round 1 finding).
    """
    missing = {
        target.name: [p for p in paths if not (OT_REPO_ROOT / p).is_file()]
        for target, paths in tms_case_paths.items()
    }
    missing = {name: paths for name, paths in missing.items() if paths}
    assert not missing, (
        "these @allure.issue TMS case links point at files that don't exist "
        f"in {OT_REPO_ROOT}: {missing}"
    )
