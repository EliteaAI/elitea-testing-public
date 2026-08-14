"""Static-analysis regression test for `test_skill_agent_interaction.py`'s
`@allure.issue(...)` TMS case links (ELITEA-2609 review round 1, fix round 1).

Guards against the defect a fresh-session reviewer flagged: the
`test_skill_explicit_and_autonomous_invocation_coexistence` `@allure.issue`
decorator pointed at
`skills/ELITEA-2609_skill-explicit-autonomous-invocation-coexistence.md`
(missing "and-" between "explicit" and "autonomous"), a filename that does
not exist in the TMS cases repo — the report link 404s. The real file is
`skills/ELITEA-2609_skill-explicit-and-autonomous-coexistence.md`
(`.agents/architecture.md` names `onetest-ai-tm-Elitea` as the mandatory
sibling clone at `../onetest-ai-tm-Elitea`, so this is checked on the local
filesystem — no network call, no GitHub API).

This test parses every `@allure.issue(...)` TMS-case URL in
`test_skill_agent_interaction.py` (not just the ELITEA-2609 one that broke)
and asserts each resolves to a real file in the sibling TMS repo, so a
future filename typo on ANY of this file's three test methods fails the
suite instead of shipping a 404 into an Allure report.
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

TARGET_FILE = AUTOMATION_DIR / "tests" / "ui" / "skills" / "test_skill_agent_interaction.py"

# Matches the `onetest-ai-tm-Elitea/blob/main/<path>.md` portion of an
# @allure.issue(...) URL string.
TMS_LINK_PATTERN = re.compile(
    r"onetest-ai-tm-Elitea/blob/main/(tests/automated-full-regression-ui/[\w./-]+\.md)"
)


def _extract_tms_case_paths(source: str) -> list[str]:
    """Return every TMS case repo-relative path referenced by an
    `@allure.issue(...)` decorator call in `source`, in source order.

    Parses the source with `ast` rather than regexing the raw text so that
    adjacent string-literal concatenation inside the decorator call (used
    for line-length — see the ELITEA-2607 and ELITEA-2609 decorators, which
    split the URL across two string tokens) is resolved the same way the
    Python parser resolves it: `ast.parse` folds `"a" "b"` into a single
    `Constant(value="ab")` node before this ever inspects it.
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
def target_source() -> str:
    assert TARGET_FILE.is_file(), f"expected spec file missing: {TARGET_FILE}"
    return TARGET_FILE.read_text(encoding="utf-8")


@pytest.fixture(scope="module")
def tms_case_paths(target_source: str) -> list[str]:
    paths = _extract_tms_case_paths(target_source)
    assert paths, (
        "no onetest-ai-tm-Elitea TMS case links found in "
        f"{TARGET_FILE} — extraction regex likely drifted from the "
        "@allure.issue URL shape"
    )
    return paths


def test_finds_all_three_tms_case_links(tms_case_paths):
    """Sanity check on the extractor itself: this file covers exactly three
    TMS cases (ELITEA-1735, ELITEA-2607, ELITEA-2609) as of this writing —
    a count drift means either a case was added/removed or the extraction
    regex stopped matching a decorator's URL shape (silently under-covering
    this guard), so surface it explicitly rather than passing on zero rows.
    """
    assert len(tms_case_paths) == 3, (
        f"expected 3 TMS case links in {TARGET_FILE.name}, found "
        f"{len(tms_case_paths)}: {tms_case_paths}"
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
    """Every @allure.issue TMS-case URL in test_skill_agent_interaction.py
    must point at a file that actually exists in the onetest-ai-tm-Elitea
    sibling clone — a stale/typo'd filename 404s the report link
    (ELITEA-2609 review round 1 finding).
    """
    missing = [
        repo_relative_path
        for repo_relative_path in tms_case_paths
        if not (WORKSPACE_ROOT / "onetest-ai-tm-Elitea" / repo_relative_path).is_file()
    ]
    assert not missing, (
        "these @allure.issue TMS case links in "
        f"{TARGET_FILE.name} point at files that don't exist in "
        f"{OT_REPO_ROOT}: {missing}"
    )
