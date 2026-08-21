"""UI Test for ELITEA-1837 — File Tree Behavior: Breadcrumb Path Updates on
Navigation.

Regression test: the main-panel breadcrumb and the browser URL track the
current Artifacts navigation state — bucket root shows the bucket crumb alone
with ``?bucket=<name>``; selecting subfolder ``a1`` shows ``bucket > a1`` with
``?bucket=<name>&folder=a1``; and clicking the bucket crumb navigates back to
the root, restoring the root listing, dropping the folder crumb and dropping
the ``folder`` query param.

Test flow:
Setup (transit, not case steps) — a fresh bucket via the ``artifact_bucket``
fixture, seeded through the artifacts API with ``a1/f1.txt`` (the subfolder)
and a root-level ``root.txt`` (so step 8's "root level contents are shown" is
a positive observable, not merely the absence of the subfolder view).
1-2. Navigate to Artifacts and select the bucket.
3. The breadcrumb shows the bucket alone; the URL carries only ``?bucket=``.
4-5. Select subfolder ``a1``; the breadcrumb becomes ``bucket > a1``.
6. The URL carries both ``bucket`` and ``folder`` params.
7-8. Click the bucket crumb; the root listing (``a1`` + ``root.txt``) returns.
9. The breadcrumb shows only the bucket again.
10. The URL is back to ``?bucket=<name>`` with no folder param.

URL assertions are anchored full-query matches, never substring checks — a
stale ``&folder=a1`` survives an ``"bucket=<name>" in url`` check, and that is
exactly the regression step 10 exists to catch.

Substitution declared (fidelity): the ONLY substitution is transit — the
bucket and its two seed files are created through the artifacts API, which the
case's precondition merely requires to exist. Every asserted observable
(breadcrumb text, crumb count, main-panel rows, browser URL) is produced by
the running product.

AFS: test-specs/artifacts/l3_file-tree-breadcrumb-path-updates-on-navigation_ELITEA-1837.md

Markers:
    - ui: requires browser
    - regression: regression test
    - p2: medium priority (matches case priority)
    - new: added on automation/base, not yet validated on a deployed env

Usage:
    cd automation
    pytest tests/ui/artifacts/test_artifacts_tree_breadcrumb_navigation.py -v
"""

import logging
import re

import allure
import pytest
from pages.artifacts_page import ArtifactsPage
from playwright.sync_api import expect

logger = logging.getLogger(__name__)

pytestmark = [pytest.mark.ui, pytest.mark.regression, pytest.mark.p2, pytest.mark.new]

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
SUBFOLDER_FILE = "f1.txt"
ROOT_FILE = "root.txt"
SEED_CONTENT = b"ELITEA-1837 seed content\n"


@allure.epic("Artifacts")
@allure.feature("File Tree Behavior")
class TestArtifactsTreeBreadcrumbNavigation:
    """ELITEA-1837 — breadcrumb and URL follow bucket/subfolder navigation."""

    @pytest.mark.p2
    @allure.title(
        "Breadcrumb and URL update when navigating into a subfolder, and the "
        "breadcrumb bucket crumb navigates back to the bucket root"
    )
    @allure.severity(allure.severity_level.NORMAL)
    @allure.issue(
        "https://github.com/EliteaAI/onetest-ai-tm-Elitea/blob/main/tests/"
        "automated-full-regression-ui/artifacts/"
        "ELITEA-1837_file-tree-breadcrumb-updates-on-navigation.md",
        "onetest-ai Test Case link",
    )
    def test_breadcrumb_and_url_update_on_navigation(
        self, page, artifact_bucket, artifact_api,
    ):
        """Breadcrumb + URL track navigation; the bucket crumb returns to root.

        Substitution declared: the bucket (``artifact_bucket`` fixture) and
        its seed files (``ArtifactAPI.upload_file``) are created via the
        artifacts API — transit only, reaching the case's stated precondition.
        """
        bucket_name = artifact_bucket["name"]
        root_url_re = re.compile(rf"\?bucket={re.escape(bucket_name)}$")
        folder_url_re = re.compile(
            rf"\?bucket={re.escape(bucket_name)}&folder={SUBFOLDER_NAME}$"
        )

        page.set_viewport_size({"width": VIEWPORT_WIDTH, "height": VIEWPORT_HEIGHT})
        artifacts_page = ArtifactsPage(page)

        with allure.step(
            f"Precondition — seed '{SUBFOLDER_KEY}{SUBFOLDER_FILE}' and "
            f"'{ROOT_FILE}' in bucket '{bucket_name}'"
        ):
            artifact_api.upload_file(
                bucket_name, f"{SUBFOLDER_KEY}{SUBFOLDER_FILE}", SEED_CONTENT,
            )
            artifact_api.upload_file(bucket_name, ROOT_FILE, SEED_CONTENT)

        with allure.step("Step 1 — Navigate to the Artifacts section"):
            artifacts_page.navigate_to_artifacts()
            artifacts_page.wait_for_page_load(timeout=NAVIGATION_TIMEOUT)
            bucket_row = artifacts_page.bucket_row(bucket_name)
            expect(bucket_row).to_have_count(1, timeout=NAVIGATION_TIMEOUT)
            # Guards the #651 already-selected-row toggle trap.
            expect(bucket_row).to_have_attribute(
                "data-selected", "false", timeout=UI_ELEMENT_TIMEOUT,
            )

        with allure.step(f"Step 2 — Click '{bucket_name}' in the bucket list"):
            artifacts_page.click_bucket_row(bucket_name, timeout=UI_ELEMENT_TIMEOUT)
            expect(bucket_row).to_have_attribute(
                "data-selected", "true", timeout=UI_ELEMENT_TIMEOUT,
            )

        with allure.step(
            f"Step 3 — The main panel breadcrumb displays '{bucket_name}'"
        ):
            assert artifacts_page.get_breadcrumb_bucket_text(
                timeout=UI_ELEMENT_TIMEOUT
            ) == bucket_name, "Breadcrumb bucket crumb should name the bucket"
            assert artifacts_page.get_breadcrumb_folder_names() == [], (
                "At bucket root the breadcrumb should carry no folder crumb"
            )
            # Baseline for step 10's return.
            expect(page).to_have_url(root_url_re, timeout=UI_ELEMENT_TIMEOUT)

        with allure.step(
            f"Step 4 — Click subfolder '{SUBFOLDER_NAME}' in the left panel"
        ):
            artifacts_page.click_tree_item(SUBFOLDER_KEY, timeout=UI_ELEMENT_TIMEOUT)
            expect(artifacts_page.tree_item(SUBFOLDER_KEY)).to_have_attribute(
                "data-selected", "true", timeout=TREE_TRANSITION_TIMEOUT,
            )

        with allure.step(
            f"Step 5 — The breadcrumb updates to '{bucket_name} > "
            f"{SUBFOLDER_NAME}'"
        ):
            assert artifacts_page.get_breadcrumb_bucket_text(
                timeout=UI_ELEMENT_TIMEOUT
            ) == bucket_name, "Bucket crumb should still name the bucket"
            assert artifacts_page.get_breadcrumb_folder_names() == [SUBFOLDER_NAME], (
                f"Breadcrumb should read '{bucket_name} > {SUBFOLDER_NAME}'"
            )

        with allure.step(
            "Step 6 — The URL reflects the subfolder path "
            f"(?bucket={bucket_name}&folder={SUBFOLDER_NAME})"
        ):
            expect(page).to_have_url(folder_url_re, timeout=UI_ELEMENT_TIMEOUT)

        with allure.step(
            f"Step 7 — Click '{bucket_name}' in the main panel breadcrumb"
        ):
            artifacts_page.click_breadcrumb_bucket_label(timeout=UI_ELEMENT_TIMEOUT)

        with allure.step(
            f"Step 8 — The main panel navigates back to the root of "
            f"'{bucket_name}'"
        ):
            expect(page).to_have_url(root_url_re, timeout=NAVIGATION_TIMEOUT)
            assert set(
                artifacts_page.get_file_names(timeout=UI_ELEMENT_TIMEOUT)
            ) == {SUBFOLDER_NAME, ROOT_FILE}, (
                "Main panel should list the bucket's ROOT contents "
                f"({SUBFOLDER_NAME}, {ROOT_FILE}), not the subfolder's"
            )

        with allure.step(
            f"Step 9 — The breadcrumb displays only '{bucket_name}'"
        ):
            assert artifacts_page.get_breadcrumb_bucket_text(
                timeout=UI_ELEMENT_TIMEOUT
            ) == bucket_name, "Bucket crumb should still name the bucket"
            assert artifacts_page.get_breadcrumb_folder_names() == [], (
                "The folder crumb should be gone after returning to root"
            )

        with allure.step(
            f"Step 10 — The URL is back to the root bucket path "
            f"(?bucket={bucket_name})"
        ):
            expect(page).to_have_url(root_url_re, timeout=UI_ELEMENT_TIMEOUT)
