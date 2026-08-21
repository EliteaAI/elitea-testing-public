"""UI Test for ELITEA-1838 — File Tree Behavior: Switching Between Buckets
Updates Tree and Main Panel.

Regression test: selecting a second bucket moves the left-panel highlight,
swaps the main-panel contents, breadcrumb and URL — WITHOUT collapsing the
previously selected bucket's tree. Returning to the first bucket restores its
highlight, its expansion and its contents.

"Expanded" is asserted through the bucket's own rendered tree nodes:
``SimpleBucketList.jsx`` renders ``{isExpanded && <BucketContent …>}``, so a
collapsed bucket has ZERO tree nodes in the DOM. There is no ``data-expanded``
attribute on the bucket row and none is needed.

Test flow:
Setup (transit, not case steps) — bucket A via the ``artifact_bucket``
fixture, seeded with ``a1/f1.txt`` + ``root.txt``; bucket B created as
``{A}-b`` (sorts immediately after A in the alphanumeric bucket list, so both
rows land in the same scroll band of a ~760-bucket panel) and seeded with a
distinctly-named ``b-root.txt``, so no tree assertion can match the other
bucket's node by coincidence. B is deleted in the fixture's own teardown.
1-2. Navigate to Artifacts; both bucket rows are present and neither selected.
3. Click A — highlighted, expanded, its files in the main panel.
4. Click B — A stays EXPANDED but loses its highlight (the case's core claim).
5-7. B is highlighted, its contents / breadcrumb / URL are shown.
8-9. Click A again — highlighted and expanded again, contents restored.

Substitution declared (fidelity): the ONLY substitution is transit — both
buckets and their files are created through the artifacts API, which the
case's precondition merely requires to exist. Every asserted observable (row
selection attributes, rendered tree nodes, main-panel rows, breadcrumb text,
browser URL) is produced by the running product.

AFS: test-specs/artifacts/l2_file-tree-switching-buckets-updates-tree-and-main-panel_ELITEA-1838.md

Markers:
    - ui: requires browser
    - regression: regression test
    - p1: high priority (matches case priority)
    - new: added on automation/base, not yet validated on a deployed env

Usage:
    cd automation
    pytest tests/ui/artifacts/test_artifacts_tree_switch_between_buckets.py -v
"""

import logging
import re

import allure
import pytest
from pages.artifacts_page import ArtifactsPage
from playwright.sync_api import expect

logger = logging.getLogger(__name__)

pytestmark = [pytest.mark.ui, pytest.mark.regression, pytest.mark.p1, pytest.mark.new]

# ---------------------------------------------------------------------------
# Timeout constants (ms)
# ---------------------------------------------------------------------------
UI_ELEMENT_TIMEOUT = 10_000
NAVIGATION_TIMEOUT = 15_000
TREE_TRANSITION_TIMEOUT = 10_000

VIEWPORT_WIDTH = 1600
VIEWPORT_HEIGHT = 900

SUBFOLDER_KEY = "a1/"
SUBFOLDER_NAME = "a1"
BUCKET_A_ROOT_FILE = "root.txt"
BUCKET_B_FILE = "b-root.txt"
SEED_CONTENT = b"ELITEA-1838 seed content\n"


@pytest.fixture
def second_artifact_bucket(artifact_bucket, artifact_api):
    """Create a SECOND bucket named ``{first}-b`` and delete it afterwards.

    The case needs two buckets side by side. Deriving the name from the
    fixture bucket keeps the two rows adjacent in the alphanumerically-sorted
    bucket list (test-specs/artifacts/_surface.md § Bucket-list ordering), so
    both are reachable in the same scroll band of a ~760-bucket panel.
    """
    name = f"{artifact_bucket['name']}-b"
    artifact_api.create_bucket(name)
    logger.info("Created second artifact bucket '%s'", name)
    yield name
    try:
        artifact_api.delete_bucket(name)
    except Exception as exc:  # teardown must never mask a test result
        logger.warning("Failed to delete second artifact bucket '%s': %s", name, exc)


@allure.epic("Artifacts")
@allure.feature("File Tree Behavior")
class TestArtifactsTreeSwitchBetweenBuckets:
    """ELITEA-1838 — switching buckets updates the tree and the main panel."""

    @pytest.mark.p1
    @allure.title(
        "Switching between buckets moves the highlight, main panel, breadcrumb "
        "and URL — and does NOT collapse the previously selected bucket"
    )
    @allure.severity(allure.severity_level.CRITICAL)
    @allure.issue(
        "https://github.com/EliteaAI/onetest-ai-tm-Elitea/blob/main/tests/"
        "automated-full-regression-ui/artifacts/"
        "ELITEA-1838_file-tree-behavior-switching-between-buckets.md",
        "onetest-ai Test Case link",
    )
    def test_switching_buckets_updates_tree_and_main_panel(
        self, page, artifact_bucket, second_artifact_bucket, artifact_api,
    ):
        """Selecting another bucket moves the highlight without collapsing.

        Substitution declared: both buckets and their files are created via
        the artifacts API (``artifact_bucket`` / ``second_artifact_bucket``
        fixtures, ``ArtifactAPI.upload_file``) — transit only, reaching the
        case's stated precondition.
        """
        bucket_a = artifact_bucket["name"]
        bucket_b = second_artifact_bucket
        url_a_re = re.compile(rf"\?bucket={re.escape(bucket_a)}$")
        url_b_re = re.compile(rf"\?bucket={re.escape(bucket_b)}$")

        page.set_viewport_size({"width": VIEWPORT_WIDTH, "height": VIEWPORT_HEIGHT})
        artifacts_page = ArtifactsPage(page)

        with allure.step(
            f"Precondition — seed '{bucket_a}' with {SUBFOLDER_KEY} and "
            f"{BUCKET_A_ROOT_FILE}, and '{bucket_b}' with {BUCKET_B_FILE}"
        ):
            artifact_api.upload_file(
                bucket_a, f"{SUBFOLDER_KEY}f1.txt", SEED_CONTENT,
            )
            artifact_api.upload_file(bucket_a, BUCKET_A_ROOT_FILE, SEED_CONTENT)
            artifact_api.upload_file(bucket_b, BUCKET_B_FILE, SEED_CONTENT)

        row_a = artifacts_page.bucket_row(bucket_a)
        row_b = artifacts_page.bucket_row(bucket_b)

        with allure.step("Step 1 — Navigate to the Artifacts section"):
            artifacts_page.navigate_to_artifacts()
            artifacts_page.wait_for_page_load(timeout=NAVIGATION_TIMEOUT)

        with allure.step(
            f"Step 2 — Both buckets are present: '{bucket_a}' and '{bucket_b}'"
        ):
            expect(row_a).to_have_count(1, timeout=NAVIGATION_TIMEOUT)
            expect(row_b).to_have_count(1, timeout=NAVIGATION_TIMEOUT)
            # Guards the #651 already-selected-row toggle trap for both rows.
            expect(row_a).to_have_attribute(
                "data-selected", "false", timeout=UI_ELEMENT_TIMEOUT,
            )
            expect(row_b).to_have_attribute(
                "data-selected", "false", timeout=UI_ELEMENT_TIMEOUT,
            )

        with allure.step(
            f"Step 3 — Click '{bucket_a}': it is highlighted, expands in the "
            "tree and its files are shown in the main panel"
        ):
            artifacts_page.click_bucket_row(bucket_a, timeout=UI_ELEMENT_TIMEOUT)
            expect(row_a).to_have_attribute(
                "data-selected", "true", timeout=UI_ELEMENT_TIMEOUT,
            )
            expect(artifacts_page.tree_item(SUBFOLDER_KEY)).to_be_visible(
                timeout=TREE_TRANSITION_TIMEOUT,
            )
            expect(artifacts_page.tree_item(BUCKET_A_ROOT_FILE)).to_be_visible(
                timeout=TREE_TRANSITION_TIMEOUT,
            )
            assert set(
                artifacts_page.get_file_names(timeout=UI_ELEMENT_TIMEOUT)
            ) == {SUBFOLDER_NAME, BUCKET_A_ROOT_FILE}, (
                f"Main panel should list '{bucket_a}' root contents"
            )
            assert artifacts_page.get_breadcrumb_bucket_text(
                timeout=UI_ELEMENT_TIMEOUT
            ) == bucket_a, "Breadcrumb should name the first bucket"
            assert artifacts_page.get_breadcrumb_folder_names() == [], (
                "At bucket root the breadcrumb should carry no folder crumb"
            )

        with allure.step(
            f"Step 4 — Click '{bucket_b}': '{bucket_a}' does NOT collapse but "
            "loses its highlighted state"
        ):
            artifacts_page.click_bucket_row(bucket_b, timeout=UI_ELEMENT_TIMEOUT)
            # The case's core claim — the previous bucket's subtree survives.
            expect(artifacts_page.tree_item(SUBFOLDER_KEY)).to_be_visible(
                timeout=TREE_TRANSITION_TIMEOUT,
            )
            expect(artifacts_page.tree_item(BUCKET_A_ROOT_FILE)).to_be_visible(
                timeout=TREE_TRANSITION_TIMEOUT,
            )
            expect(row_a).to_have_attribute(
                "data-selected", "false", timeout=UI_ELEMENT_TIMEOUT,
            )

        with allure.step(
            f"Step 5 — '{bucket_b}' becomes highlighted and its contents are "
            "shown in the main panel"
        ):
            expect(row_b).to_have_attribute(
                "data-selected", "true", timeout=UI_ELEMENT_TIMEOUT,
            )
            expect(artifacts_page.tree_item(BUCKET_B_FILE)).to_be_visible(
                timeout=TREE_TRANSITION_TIMEOUT,
            )
            assert set(
                artifacts_page.get_file_names(timeout=UI_ELEMENT_TIMEOUT)
            ) == {BUCKET_B_FILE}, (
                f"Main panel should list ONLY '{bucket_b}' contents"
            )

        with allure.step(
            f"Step 6 — The main panel breadcrumb displays '{bucket_b}'"
        ):
            assert artifacts_page.get_breadcrumb_bucket_text(
                timeout=UI_ELEMENT_TIMEOUT
            ) == bucket_b, "Breadcrumb should name the second bucket"
            assert artifacts_page.get_breadcrumb_folder_names() == [], (
                "At bucket root the breadcrumb should carry no folder crumb"
            )

        with allure.step(f"Step 7 — The URL reflects '{bucket_b}'"):
            expect(page).to_have_url(url_b_re, timeout=UI_ELEMENT_TIMEOUT)

        with allure.step(
            f"Step 8 — Click back on '{bucket_a}': it is highlighted again and "
            "expanded"
        ):
            artifacts_page.click_bucket_row(bucket_a, timeout=UI_ELEMENT_TIMEOUT)
            expect(row_a).to_have_attribute(
                "data-selected", "true", timeout=UI_ELEMENT_TIMEOUT,
            )
            expect(row_b).to_have_attribute(
                "data-selected", "false", timeout=UI_ELEMENT_TIMEOUT,
            )
            expect(artifacts_page.tree_item(SUBFOLDER_KEY)).to_be_visible(
                timeout=TREE_TRANSITION_TIMEOUT,
            )
            expect(artifacts_page.tree_item(BUCKET_A_ROOT_FILE)).to_be_visible(
                timeout=TREE_TRANSITION_TIMEOUT,
            )

        with allure.step(
            f"Step 9 — The main panel displays '{bucket_a}' contents again"
        ):
            assert set(
                artifacts_page.get_file_names(timeout=UI_ELEMENT_TIMEOUT)
            ) == {SUBFOLDER_NAME, BUCKET_A_ROOT_FILE}, (
                f"Main panel should list '{bucket_a}' root contents again"
            )
            assert artifacts_page.get_breadcrumb_bucket_text(
                timeout=UI_ELEMENT_TIMEOUT
            ) == bucket_a, "Breadcrumb should name the first bucket again"
            expect(page).to_have_url(url_a_re, timeout=UI_ELEMENT_TIMEOUT)
