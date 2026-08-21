"""UI Test for ELITEA-1836 — File Tree Behavior: Subfolder Expands and
Collapses on Click.

Regression test: in the Artifacts left-panel tree, clicking a subfolder
expands it (its files appear as child tree nodes) and updates the main-panel
header to ``bucket > a1``; clicking the same subfolder again collapses it (the
child nodes are removed from the DOM) while the subfolder itself stays listed
under its bucket.

Ordering discipline (load-bearing — do NOT reorder):
    The two ``a1/`` clicks are separated by the case's own Step-4 assertions.
    A collapse click fired immediately after the expand click is silently
    discarded 2 times in 5 (measured live) — ``BucketContent.jsx``'s
    ``isFetching`` early-return unmounts the ``FileTreeItem`` subtree, which
    re-initialises ``isExpanded`` from ``expandedPaths``. Filed as MINOR
    product defect https://github.com/EliteaAI/elitea-testing-public/issues/1631.
    With the intermediate assertions in place the collapse was reliable
    (5/5, plus 7/7 in two earlier probes), so this test asserts the correct
    behaviour with hard assertions and no masking.

Test flow:
Setup (transit, not case steps) — a fresh bucket via the ``artifact_bucket``
fixture, seeded with ``a1/f1.txt`` and ``a1/f2.txt`` through the artifacts API
(``a1/`` is an S3 key prefix; there is no "create folder" UI). Seeding only
files under ``a1/`` makes the bucket's tree top level exactly ``[a1]``, which
is the state the case's Step 6 describes.
1. Navigate to Artifacts; assert the bucket row is present and NOT selected
   (guards the #651 already-selected-row toggle trap).
2. Click the bucket row — it is highlighted, ``a1`` appears beneath it, and
   ``a1``'s own children are NOT rendered yet (the pre-state that makes the
   expansion in step 3 observable).
3. Click ``a1`` — both child files appear as tree nodes; ``a1`` is the
   selected tree node.
4. The main-panel header reads ``bucket > a1`` and the panel lists the
   subfolder's files.
5. Click ``a1`` again — both child nodes are removed from the tree.
6. The tree still shows the bucket with ``a1`` listed, now collapsed.

Substitution declared (fidelity): the ONLY substitution is transit — the
bucket and its two seed files are created through the artifacts API, which the
case's precondition merely requires to exist. Every asserted observable (tree
nodes, selection attributes, breadcrumb text, main-panel rows) is rendered by
the running product.

AFS: test-specs/artifacts/l3_file-tree-subfolder-expands-and-collapses-on-click_ELITEA-1836.md

Markers:
    - ui: requires browser
    - regression: regression test
    - p2: medium priority (matches case priority)
    - new: added on automation/base, not yet validated on a deployed env

Usage:
    cd automation
    pytest tests/ui/artifacts/test_artifacts_tree_subfolder_expand_collapse.py -v
"""

import logging

import allure
import pytest
from pages.artifacts_page import ArtifactsPage
from playwright.sync_api import expect

logger = logging.getLogger(__name__)

pytestmark = [pytest.mark.ui, pytest.mark.regression, pytest.mark.p2, pytest.mark.new]

# ---------------------------------------------------------------------------
# Timeout constants (ms)
# ---------------------------------------------------------------------------
UI_ELEMENT_TIMEOUT = 10_000       # rows, tree nodes, header labels
NAVIGATION_TIMEOUT = 15_000       # SPA route transitions
TREE_TRANSITION_TIMEOUT = 10_000  # MUI Collapse enter/exit (~300 ms) + refetch

# The file table's "Last update" column clips below ~1600 px (test-specs/
# artifacts/_surface.md) — the viewport every sibling artifacts spec pins.
VIEWPORT_WIDTH = 1600
VIEWPORT_HEIGHT = 900

SUBFOLDER_KEY = "a1/"             # tree/S3 folder keys carry the trailing slash
SUBFOLDER_NAME = "a1"
CHILD_FILES = ("f1.txt", "f2.txt")
SEED_CONTENT = b"ELITEA-1836 seed content\n"


@allure.epic("Artifacts")
@allure.feature("File Tree Behavior")
class TestArtifactsTreeSubfolderExpandCollapse:
    """ELITEA-1836 — a subfolder expands and collapses on click."""

    @pytest.mark.p2
    @allure.title(
        "Clicking a subfolder in the left-panel tree expands it (files listed, "
        "header shows 'bucket > a1') and clicking it again collapses it"
    )
    @allure.severity(allure.severity_level.NORMAL)
    @allure.issue(
        "https://github.com/EliteaAI/onetest-ai-tm-Elitea/blob/main/tests/"
        "automated-full-regression-ui/artifacts/"
        "ELITEA-1836_file-tree-behavior-subfolder-expands-and-collapses.md",
        "onetest-ai Test Case link",
    )
    def test_subfolder_expands_and_collapses_on_click(
        self, page, artifact_bucket, artifact_api,
    ):
        """A subfolder toggles expanded/collapsed on successive clicks.

        Substitution declared: the bucket (``artifact_bucket`` fixture) and
        its two files under ``a1/`` (``ArtifactAPI.upload_file``) are created
        via the artifacts API — transit only, reaching the case's stated
        precondition. Every asserted observable is produced by the product.
        """
        bucket_name = artifact_bucket["name"]

        page.set_viewport_size({"width": VIEWPORT_WIDTH, "height": VIEWPORT_HEIGHT})
        artifacts_page = ArtifactsPage(page)

        # ------------------------------------------------------------------
        # Setup (precondition, not a case step)
        # ------------------------------------------------------------------
        with allure.step(
            f"Precondition — seed '{SUBFOLDER_KEY}' in bucket '{bucket_name}' "
            f"with {', '.join(CHILD_FILES)}"
        ):
            for file_name in CHILD_FILES:
                artifact_api.upload_file(
                    bucket_name, f"{SUBFOLDER_KEY}{file_name}", SEED_CONTENT,
                )

        with allure.step("Step 1 — Navigate to the Artifacts section"):
            artifacts_page.navigate_to_artifacts()
            artifacts_page.wait_for_page_load(timeout=NAVIGATION_TIMEOUT)
            bucket_row = artifacts_page.bucket_row(bucket_name)
            expect(bucket_row).to_have_count(1, timeout=NAVIGATION_TIMEOUT)
            # `/artifacts` auto-selects a bucket on a param-less load; a click
            # on an ALREADY-selected row TOGGLES tree expansion instead of
            # expanding it (CLARIFICATION #651). Assert we are not in that
            # state rather than silently mis-stepping.
            expect(bucket_row).to_have_attribute(
                "data-selected", "false", timeout=UI_ELEMENT_TIMEOUT,
            )

        with allure.step(
            f"Step 2 — Click '{bucket_name}': it expands and shows subfolder "
            f"'{SUBFOLDER_NAME}' beneath it"
        ):
            artifacts_page.click_bucket_row(bucket_name, timeout=UI_ELEMENT_TIMEOUT)
            expect(bucket_row).to_have_attribute(
                "data-selected", "true", timeout=UI_ELEMENT_TIMEOUT,
            )
            expect(artifacts_page.tree_item(SUBFOLDER_KEY)).to_be_visible(
                timeout=TREE_TRANSITION_TIMEOUT,
            )
            # Pre-state: the subfolder starts COLLAPSED. Without this, step 3's
            # "files are visible" would pass on an already-expanded tree.
            for file_name in CHILD_FILES:
                expect(
                    artifacts_page.tree_item(f"{SUBFOLDER_KEY}{file_name}")
                ).to_have_count(0, timeout=UI_ELEMENT_TIMEOUT)

        with allure.step(
            f"Step 3 — Click subfolder '{SUBFOLDER_NAME}': it expands and its "
            "files are listed beneath it in the left panel tree"
        ):
            artifacts_page.click_tree_item(SUBFOLDER_KEY, timeout=UI_ELEMENT_TIMEOUT)
            for file_name in CHILD_FILES:
                expect(
                    artifacts_page.tree_item(f"{SUBFOLDER_KEY}{file_name}")
                ).to_be_visible(timeout=TREE_TRANSITION_TIMEOUT)
            expect(artifacts_page.tree_item(SUBFOLDER_KEY)).to_be_visible(
                timeout=UI_ELEMENT_TIMEOUT,
            )
            expect(artifacts_page.tree_item(SUBFOLDER_KEY)).to_have_attribute(
                "data-selected", "true", timeout=UI_ELEMENT_TIMEOUT,
            )

        with allure.step(
            f"Step 4 — The main panel header displays '{bucket_name} > "
            f"{SUBFOLDER_NAME}'"
        ):
            assert artifacts_page.get_breadcrumb_bucket_text(
                timeout=UI_ELEMENT_TIMEOUT
            ) == bucket_name, (
                "Breadcrumb bucket crumb should name the selected bucket"
            )
            assert artifacts_page.get_breadcrumb_folder_names() == [SUBFOLDER_NAME], (
                f"Breadcrumb should read '{bucket_name} > {SUBFOLDER_NAME}' while "
                f"the subfolder is selected"
            )
            # The header and the table are driven by the same `currentPrefix`;
            # asserting both makes "the main panel updated" mean its contents.
            assert set(
                artifacts_page.get_file_names(timeout=UI_ELEMENT_TIMEOUT)
            ) == set(CHILD_FILES), (
                f"Main panel should list the subfolder's files {CHILD_FILES}"
            )

        with allure.step(
            f"Step 5 — Click subfolder '{SUBFOLDER_NAME}' again: it collapses "
            "and its files are no longer shown in the tree"
        ):
            artifacts_page.click_tree_item(SUBFOLDER_KEY, timeout=UI_ELEMENT_TIMEOUT)
            for file_name in CHILD_FILES:
                expect(
                    artifacts_page.tree_item(f"{SUBFOLDER_KEY}{file_name}")
                ).to_have_count(0, timeout=TREE_TRANSITION_TIMEOUT)

        with allure.step(
            f"Step 6 — The left panel tree shows '{bucket_name}' with "
            f"'{SUBFOLDER_NAME}' listed but collapsed"
        ):
            expect(bucket_row).to_have_count(1, timeout=UI_ELEMENT_TIMEOUT)
            expect(artifacts_page.tree_item(SUBFOLDER_KEY)).to_be_visible(
                timeout=UI_ELEMENT_TIMEOUT,
            )
            for file_name in CHILD_FILES:
                expect(
                    artifacts_page.tree_item(f"{SUBFOLDER_KEY}{file_name}")
                ).to_have_count(0, timeout=UI_ELEMENT_TIMEOUT)
