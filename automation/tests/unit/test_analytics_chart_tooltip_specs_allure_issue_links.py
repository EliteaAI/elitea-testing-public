"""Static-analysis regression test for the Analytics chart-tooltip specs'
`@allure.issue(...)` TMS case links (ELITEA-2326/2327/2328/2329, PR #1956
review round 1).

Guards against the defect a fresh-session reviewer flagged: all three specs
pointed at ``tests/automated-full-regression-ui/settings-analytics/`` — a folder
that does not exist in EliteaAI/onetest-ai-tm-Elitea. The real cases live under
``tests/automated-full-regression-ui/settings/analytics/`` (the AFS *directory*
in this repo is `test-specs/settings-analytics/`, and the hyphenated form leaked
from there into the URLs). One link was worse than dead: the parameterized
bar-chart spec's URL stopped at the bare folder, naming no case at all, and its
second case (ELITEA-2328) had no link whatsoever.

A dead Allure link never fails a run — the report just 404s on click — which is
why this needs a static guard. Same guard shape and rationale as
`test_mcp_type_filter_spec_allure_issue_link.py` (ELITEA-1942),
`test_artifacts_tree_specs_allure_issue_links.py` and
`test_skill_agent_interaction_allure_issue_links.py`.
`.agents/architecture.md` names `onetest-ai-tm-Elitea` as a mandatory sibling
clone at `../onetest-ai-tm-Elitea`, so resolution is checked on the local
filesystem — no network call, no GitHub API.
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

ADMIN_TESTS_DIR = AUTOMATION_DIR / "tests" / "ui" / "admin"

#: spec file -> every TMS case id it must carry a resolvable link for.
#: `test_analytics_user_detail_view.py` covers ELITEA-2313 and is extended by
#: ELITEA-2329 (`extend-existing`), so it owes BOTH links.
EXPECTED_CASE_IDS_BY_SPEC = {
    "test_analytics_overview_daily_chart_tooltip.py": ["ELITEA-2326"],
    "test_analytics_bar_chart_tooltip.py": ["ELITEA-2327", "ELITEA-2328"],
    "test_analytics_user_detail_view.py": ["ELITEA-2313", "ELITEA-2329"],
}

# Matches the `onetest-ai-tm-Elitea/blob/main/<path>.md` portion of an
# @allure.issue(...) URL string.
TMS_LINK_PATTERN = re.compile(
    r"onetest-ai-tm-Elitea/blob/main/(tests/automated-full-regression-ui/[\w./-]+\.md)"
)


def _extract_tms_case_paths(source: str) -> list[str]:
    """Return every TMS case repo-relative path referenced by an
    `@allure.issue(...)` decorator call in `source`, in source order.

    Parsed with `ast` rather than regexed off the raw text so adjacent
    string-literal concatenation inside the decorator call (these specs split
    each URL across two string tokens for line length) is resolved the way the
    Python parser resolves it.
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
    paths: dict[str, list[str]] = {}
    for spec_name in EXPECTED_CASE_IDS_BY_SPEC:
        spec_file = ADMIN_TESTS_DIR / spec_name
        assert spec_file.is_file(), f"expected spec file missing: {spec_file}"
        paths[spec_name] = _extract_tms_case_paths(spec_file.read_text(encoding="utf-8"))
    return paths


@pytest.mark.parametrize("spec_name", sorted(EXPECTED_CASE_IDS_BY_SPEC))
def test_spec_links_every_case_it_automates(spec_name, tms_case_paths_by_spec):
    """Every case a spec automates must have its OWN link.

    This is the half that catches the bar-chart spec's original state: one
    folder-only URL for a two-case parameterized spec, so ELITEA-2328 was
    untraceable from the report even before the path was wrong.
    """
    found_paths = tms_case_paths_by_spec[spec_name]
    found_ids = [Path(p).name.split("_", 1)[0] for p in found_paths]
    expected_ids = EXPECTED_CASE_IDS_BY_SPEC[spec_name]

    assert sorted(found_ids) == sorted(expected_ids), (
        f"{spec_name} must carry one @allure.issue TMS link per case it automates: "
        f"expected {expected_ids}, found {found_ids} (from {found_paths})"
    )


@pytest.mark.skipif(
    not OT_REPO_ROOT.is_dir(),
    reason=(
        f"sibling TMS cases repo not present at {OT_REPO_ROOT} — "
        "the four-sibling-clone layout (.agents/architecture.md) is not set up "
        "in this workspace"
    ),
)
@pytest.mark.parametrize("spec_name", sorted(EXPECTED_CASE_IDS_BY_SPEC))
def test_allure_issue_tms_links_resolve_to_real_case_files(spec_name, tms_case_paths_by_spec):
    """Each @allure.issue TMS-case URL must point at a file that actually exists
    in the onetest-ai-tm-Elitea sibling clone — the `settings-analytics/` folder
    the specs originally named does not exist there at all."""
    found_paths = tms_case_paths_by_spec[spec_name]
    assert found_paths, f"{spec_name} declared no @allure.issue TMS link"
    missing = [p for p in found_paths if not (OT_REPO_ROOT / p).is_file()]
    assert not missing, (
        f"these @allure.issue TMS case links in {spec_name} point at files that "
        f"don't exist in {OT_REPO_ROOT}: {missing}"
    )
