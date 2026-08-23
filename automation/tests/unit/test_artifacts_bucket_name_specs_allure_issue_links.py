"""Static-analysis regression test for the bucket-name specs'
`@allure.issue(...)` TMS case links (ELITEA-1812, ELITEA-1816).

Guards the defect a fresh-session reviewer flagged on ELITEA-1810 (review
round 2): the URL named a filename derived from the case *title* / AFS slug
rather than the real TMS case file, so the Allure report link 404'd. A dead
link never fails a run, which is why it needs a static guard.

Same guard shape (and same rationale) as
`test_artifacts_bucket_retention_spec_allure_issue_link.py` (ELITEA-1810),
`test_artifacts_delete_all_specs_allure_issue_links.py` (ELITEA-1848/1849/1850)
and `test_artifacts_tree_specs_allure_issue_links.py` (ELITEA-1836/1837/1838),
which cover different spec files. `.agents/architecture.md` names
`onetest-ai-tm-Elitea` as a mandatory sibling clone at `../onetest-ai-tm-Elitea`,
so resolution is checked on the local filesystem — no network call, no GitHub
API.
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

ARTIFACTS_SPEC_DIR = AUTOMATION_DIR / "tests" / "ui" / "artifacts"

# spec filename -> the single TMS case id it automates
TARGET_FILES = {
    "test_artifacts_bucket_name_lowercase.py": "ELITEA-1812",
    "test_artifacts_bucket_name_readonly_in_edit_mode.py": "ELITEA-1816",
}

# Matches the `onetest-ai-tm-Elitea/blob/main/<path>.md` portion of an
# @allure.issue(...) URL string.
TMS_LINK_PATTERN = re.compile(
    r"onetest-ai-tm-Elitea/blob/main/(tests/automated-full-regression-ui/[\w./-]+\.md)"
)


def _extract_tms_case_paths(source: str) -> list[str]:
    """Return every TMS case repo-relative path referenced by an
    `@allure.issue(...)` decorator call in `source`, in source order.

    Parsed with `ast` rather than regexed off the raw text so that adjacent
    string-literal concatenation inside the decorator call (these specs split
    the URL across three string tokens for line length) is resolved the way
    the Python parser resolves it: `ast.parse` folds `"a" "b"` into a single
    `Constant` before this inspects it.
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
def tms_case_paths_by_spec() -> dict[str, list[str]]:
    extracted: dict[str, list[str]] = {}
    for spec_name in TARGET_FILES:
        spec_path = ARTIFACTS_SPEC_DIR / spec_name
        assert spec_path.is_file(), f"expected spec file missing: {spec_path}"
        extracted[spec_name] = _extract_tms_case_paths(
            spec_path.read_text(encoding="utf-8")
        )
    return extracted


@pytest.mark.parametrize(("spec_name", "case_id"), sorted(TARGET_FILES.items()))
def test_each_spec_declares_one_tms_case_link_for_its_own_case(
    tms_case_paths_by_spec, spec_name, case_id
):
    """Sanity check on the extractor itself: each spec automates exactly one
    TMS case, so it must yield exactly one link, naming that case.

    A zero count here would mean the extraction regex drifted from the
    `@allure.issue` URL shape and the resolution check below silently passed
    on an empty set — the failure mode this guard exists to prevent.
    """
    paths = tms_case_paths_by_spec[spec_name]
    assert len(paths) == 1, (
        f"expected 1 @allure.issue TMS link in {spec_name}, got {len(paths)}: {paths}"
    )
    found_case_id = Path(paths[0]).name.split("_", 1)[0]
    assert found_case_id == case_id, (
        f"unexpected case id in {spec_name}'s TMS link: {found_case_id}"
    )


@pytest.mark.skipif(
    not OT_REPO_ROOT.is_dir(),
    reason=(
        f"sibling TMS cases repo not present at {OT_REPO_ROOT} — "
        "the four-sibling-clone layout (.agents/architecture.md) is not "
        "set up in this workspace"
    ),
)
def test_allure_issue_tms_links_resolve_to_real_case_files(tms_case_paths_by_spec):
    """Every @allure.issue TMS-case URL must point at a file that actually
    exists in the onetest-ai-tm-Elitea sibling clone — an invented filename
    404s the report link (the ELITEA-1810 review round 2 finding).
    """
    missing = [
        f"{spec_name}: {path}"
        for spec_name, paths in tms_case_paths_by_spec.items()
        for path in paths
        if not (OT_REPO_ROOT / path).is_file()
    ]
    assert not missing, (
        "these @allure.issue TMS case links point at files that don't exist "
        f"in {OT_REPO_ROOT}: {missing}"
    )
