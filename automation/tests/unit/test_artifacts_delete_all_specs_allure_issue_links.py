"""Static-analysis regression test for the delete-all/dismissal spec's three
`@allure.issue(...)` TMS case links (ELITEA-1848/1849/1850, review round 1).

Guards against the defect a fresh-session reviewer flagged: two of the three
`@allure.issue` URLs were built from a filename shape invented off the AFS
slug rather than the TMS repo's real case filenames, so both report links
404'd (ELITEA-1849's happened to coincide and resolved):

- ELITEA-1848 shipped `…_delete-flow-delete-all-select-all-checkbox.md`,
  real name `…_delete-flow-all-files-select-all-checkbox.md`
- ELITEA-1850 shipped `…_delete-flow-close-x-on-delete-confirmation.md`,
  real name `…_delete-flow-close-x-modal-keeps-items.md`

Same guard shape (and same rationale) as
`test_artifacts_tree_specs_allure_issue_links.py` (ELITEA-1836/1837/1838) and
`test_skill_agent_interaction_allure_issue_links.py` (ELITEA-2609), which
cover different spec files. `.agents/architecture.md` names
`onetest-ai-tm-Elitea` as a mandatory sibling clone at
`../onetest-ai-tm-Elitea`, so resolution is checked on the local filesystem —
no network call, no GitHub API.
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

TARGET_FILE = (
    AUTOMATION_DIR
    / "tests"
    / "ui"
    / "artifacts"
    / "test_artifacts_delete_all_and_dismissal.py"
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
    length — this spec splits each URL across three string tokens) is
    resolved the way the Python parser resolves it: `ast.parse` folds
    `"a" "b"` into a single `Constant` before this inspects it.
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
def tms_case_paths() -> list[str]:
    assert TARGET_FILE.is_file(), f"expected spec file missing: {TARGET_FILE}"
    return _extract_tms_case_paths(TARGET_FILE.read_text(encoding="utf-8"))


def test_spec_declares_one_tms_case_link_per_automated_case(tms_case_paths):
    """Sanity check on the extractor itself: this spec automates three TMS
    cases (ELITEA-1848/1849/1850), one `test_` per case, so it must yield
    exactly three links — one naming each case id.

    A zero (or a short) count here would mean the extraction regex drifted
    from the `@allure.issue` URL shape and the resolution check below
    silently passed on an empty/partial set — the failure mode this guard
    exists to prevent.
    """
    assert len(tms_case_paths) == 3, (
        f"expected 3 @allure.issue TMS links in {TARGET_FILE.name}, "
        f"got {len(tms_case_paths)}: {tms_case_paths}"
    )
    case_ids = sorted(Path(p).name.split("_", 1)[0] for p in tms_case_paths)
    assert case_ids == ["ELITEA-1848", "ELITEA-1849", "ELITEA-1850"], (
        f"unexpected case ids in the TMS links: {case_ids}"
    )


@pytest.mark.skipif(
    not OT_REPO_ROOT.is_dir(),
    reason=(
        f"sibling TMS cases repo not present at {OT_REPO_ROOT} — "
        "the four-sibling-clone layout (.agents/architecture.md) is not "
        "set up in this workspace"
    ),
)
def test_allure_issue_tms_links_resolve_to_real_case_files(tms_case_paths):
    """Every @allure.issue TMS-case URL in the delete-all/dismissal spec must
    point at a file that actually exists in the onetest-ai-tm-Elitea sibling
    clone — a stale/invented filename 404s the report link (the
    ELITEA-1848/1850 review round 1 finding).
    """
    missing = [p for p in tms_case_paths if not (OT_REPO_ROOT / p).is_file()]
    assert not missing, (
        "these @allure.issue TMS case links point at files that don't exist "
        f"in {OT_REPO_ROOT}: {missing}"
    )
