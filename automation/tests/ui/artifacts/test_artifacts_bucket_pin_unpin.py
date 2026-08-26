"""UI tests for ELITEA-1820 / ELITEA-1821 — pin and unpin an artifact bucket.

ELITEA-1820 pins a bucket to the top of the Artifacts left panel via its
bucket-row dot-menu ("Pin to top") and verifies the pin icon appears next to
the bucket's name and the bucket is repositioned above every unpinned bucket.
ELITEA-1821 is the inverse: it establishes the pinned state **through the same
UI menu**, then unpins ("Unpin from top") and verifies the icon is gone and the
bucket is back in its alphanumeric position.

**Ordering is alphanumeric, and that is verified, not assumed.** With nothing
pinned the panel renders its buckets in exact alphanumeric order (live-verified
over 766 buckets in project `Private`/399). `SimpleBucketList.jsx` does call
`sortBucketsByRecent`, but the listing payload carries no usable
`updated_at`/`created_at`, so every comparison is `NaN`, the sort is a no-op and
the backend's alphanumeric order survives. These tests assert the *observable*
(alphanumeric order), never the mechanism. Pinned buckets are rendered in a
separate list ABOVE the unpinned list (`BucketsListContent.jsx`), which is what
makes "first rendered row" the honest reading of "top of the list, above all
unpinned buckets".

**The list lags the pin request by ~8-10 s** (the `PATCH` returns 200 straight
away; the re-render follows). Every post-click assertion therefore uses a
web-first, auto-retrying `expect(...)` with a generous timeout — never a sleep.
While the list is stale the dot-menu is stale too (it still reads "Pin to top"
for an already-pinned bucket and clicking it re-sends `is_pinned: true`), so
ELITEA-1821 waits for the pinned state to actually render before re-opening the
menu.

**Testids added for these cases** (EliteaUI `automation/testids`):
`bucket-menu-pin-menuitem` (one stable testid for an item whose LABEL flips
between "Pin to top" and "Unpin from top" — PR #581: testid = identity, never
state) and the dynamic `artifacts-bucket-pin-indicator-{name}`. The row's
second, hover-only pin button is deliberately left untagged (canon ruling #511),
which is what keeps the absence assertion in ELITEA-1821 honest.

CLARIFICATION (case-text drift, already filed — reverse-masking guard):
- #666 (and its sibling #650) — both cases list the dot-menu's second item as
  "Edit"; the product labels it **"Rename"**. Nothing is broken, so the live
  label is asserted and the existing drift issue is referenced rather than a
  new one filed. The merged ELITEA-1817 spec already asserts the same string.

Fidelity: the only substitution is **transit** — the bucket under test is
created through `ArtifactAPI.create_bucket` instead of the UI's New Bucket form
(UI bucket creation is its own automated case, ELITEA-1808). Every observable
these cases read — the dropdown's labels, the PATCH result, the pin icon, the
list order — is produced by the product in response to real clicks. Teardown
clears the pin flag via the API before deleting: that is cleanup, never read
from, and it exists because bucket deletion on this project is unreliable
(`#636`) and a leaked *pinned* bucket would sit at the top of every project
member's bucket list forever.

AFS:
    test-specs/artifacts/l3_pin-artifact-bucket-to-top_ELITEA-1820.md
    test-specs/artifacts/l3_unpin-artifact-bucket-from-top_ELITEA-1821.md

Markers:
    - ui: requires browser
    - regression: regression test
    - new: added on automation/base, not yet validated on deployed envs

Usage:
    cd automation
    pytest tests/ui/artifacts/test_artifacts_bucket_pin_unpin.py -v
"""

import logging
import time

import allure
import pytest
from api.client import ArtifactAPI
from pages.artifacts_page import ArtifactsPage
from playwright.sync_api import expect

logger = logging.getLogger(__name__)

pytestmark = [pytest.mark.ui, pytest.mark.regression, pytest.mark.new]

# ---------------------------------------------------------------------------
# Timeout constants (ms)
# ---------------------------------------------------------------------------
UI_ELEMENT_TIMEOUT = 10_000
NAVIGATION_TIMEOUT = 30_000
# The bucket list re-renders ~8-10 s after the pin PATCH returns 200
# (live-measured, test-specs/artifacts/_surface.md). Generous, because the
# panel also renders 766 rows on this project.
LIST_REFRESH_TIMEOUT = 45_000

VIEWPORT_WIDTH = 1600
VIEWPORT_HEIGHT = 900

# Live dot-menu text for a bucket in a personal project (Share / Manage
# permissions are hidden by `isPersonalProject`). The case text says "Edit"
# where the product says "Rename" — CLARIFICATION #666.
MENU_TEXT_UNPINNED = "Upload filesRenamePin to topDelete"
MENU_TEXT_PINNED = "Upload filesRenameUnpin from topDelete"

HTTP_OK = 200


@pytest.fixture
def pin_bucket(artifact_api: ArtifactAPI, request):
    """Create one bucket whose name sorts near the END of the alphanumeric list.

    The `zzz-` prefix is load-bearing: both cases need a bucket that is NOT at
    the top of the list to begin with, and that lands far from the top once
    unpinned again — so "moved to the top" and "returned to its alphanumeric
    position" cannot pass by accident.

    Teardown clears the pin flag BEFORE deleting. Deletion on this project is
    unreliable (`#636`), and a leaked *pinned* bucket would sit at the top of
    every project member's bucket list forever.

    Yields:
        str: the bucket name.
    """
    ts = str(int(time.time() * 1000))[-6:]
    safe = request.node.name.lower().replace("_", "-").replace("[", "").replace("]", "")[:36]
    name = f"zzz-{safe}-{ts}"

    artifact_api.create_bucket(name)
    logger.info("Created pin-test bucket '%s'", name)

    yield name

    try:
        artifact_api.set_bucket_pinned(name, False)
    except Exception as exc:  # cleanup must never mask a test result
        logger.warning("Failed to unpin bucket '%s' during teardown: %s", name, exc)
    try:
        artifact_api.delete_bucket(name)
    except Exception as exc:
        logger.warning("Failed to delete bucket '%s' during teardown: %s", name, exc)


@allure.epic("Artifacts")
@allure.feature("Bucket pin / unpin")
class TestArtifactsBucketPinUnpin:
    """ELITEA-1820 / ELITEA-1821 — pin a bucket to the top and unpin it again."""

    # ------------------------------------------------------------------
    # Suite-local helpers
    # ------------------------------------------------------------------

    @staticmethod
    def _open_artifacts(page, bucket_name: str) -> ArtifactsPage:
        """Open /artifacts and wait until the given bucket's row is rendered."""
        page.set_viewport_size({"width": VIEWPORT_WIDTH, "height": VIEWPORT_HEIGHT})
        artifacts_page = ArtifactsPage(page)
        artifacts_page.navigate_to_artifacts()
        expect(artifacts_page.bucket_row(bucket_name)).to_be_visible(timeout=NAVIGATION_TIMEOUT)
        return artifacts_page

    @staticmethod
    def _assert_first_bucket_is(artifacts_page: ArtifactsPage, bucket_name: str) -> None:
        """Wait (auto-retrying) until *bucket_name* is the first rendered row."""
        expect(artifacts_page.first_bucket_row()).to_have_attribute(
            "data-testid", f"artifacts-bucket-row-{bucket_name}", timeout=LIST_REFRESH_TIMEOUT
        )

    @staticmethod
    def _assert_first_bucket_is_not(artifacts_page: ArtifactsPage, bucket_name: str) -> None:
        """Wait (auto-retrying) until *bucket_name* is NOT the first rendered row."""
        expect(artifacts_page.first_bucket_row()).not_to_have_attribute(
            "data-testid", f"artifacts-bucket-row-{bucket_name}", timeout=LIST_REFRESH_TIMEOUT
        )

    @staticmethod
    def _pin_via_menu(artifacts_page: ArtifactsPage, bucket_name: str, expected_menu_text: str) -> None:
        """Open the bucket's dot-menu, assert its text, click the pin/unpin item."""
        artifacts_page.open_bucket_menu(bucket_name, timeout=UI_ELEMENT_TIMEOUT)
        assert artifacts_page.get_bucket_menu_items_text(bucket_name) == expected_menu_text
        assert artifacts_page.click_bucket_menu_pin_item() == HTTP_OK

    # ------------------------------------------------------------------
    # ELITEA-1820
    # ------------------------------------------------------------------

    @pytest.mark.p2
    @allure.title("ELITEA-1820 — Pin an artifact bucket to the top of the list")
    @allure.description(
        "Pins a bucket via its row's dot-menu 'Pin to top' item and verifies "
        "the pin request persists (PATCH 200), a pin icon appears next to the "
        "bucket name, and the bucket is repositioned above every unpinned "
        "bucket while the rest of the list stays alphanumeric."
    )
    def test_pin_bucket_to_top(self, page, pin_bucket):
        artifacts_page = None

        with allure.step("Step 1 — Navigate to Artifacts; the bucket list is displayed"):
            artifacts_page = self._open_artifacts(page, pin_bucket)

        with allure.step("Step 2 — The bucket list is displayed in alphanumeric order"):
            # The case's ordering claim only holds while nothing is pinned, so
            # the precondition is verified rather than assumed.
            expect(artifacts_page.any_bucket_pin_indicator()).to_have_count(0, timeout=UI_ELEMENT_TIMEOUT)
            baseline = artifacts_page.get_rendered_bucket_names()
            assert baseline == sorted(baseline), "Bucket list is not in alphanumeric order"

        with allure.step("Step 3 — The target bucket is not currently at the top of the list"):
            assert pin_bucket in baseline
            self._assert_first_bucket_is_not(artifacts_page, pin_bucket)

        with allure.step("Step 4 — Hovering the bucket row reveals its 3-dot actions icon"):
            trigger = artifacts_page.bucket_menu_button(pin_bucket)
            expect(trigger).not_to_be_visible()
            artifacts_page.hover_bucket_row(pin_bucket, timeout=UI_ELEMENT_TIMEOUT)
            expect(trigger).to_be_visible(timeout=UI_ELEMENT_TIMEOUT)

        with allure.step("Step 5 — Clicking the 3-dot actions icon opens the dropdown"):
            artifacts_page.open_bucket_menu(pin_bucket, timeout=UI_ELEMENT_TIMEOUT)
            expect(artifacts_page.bucket_menu_container(pin_bucket)).to_be_visible(timeout=UI_ELEMENT_TIMEOUT)

        with allure.step("Step 6 — The dropdown offers Upload files / Rename / Pin to top / Delete"):
            # Case text says "Edit"; the product labels it "Rename" — the live
            # contract is asserted, the drift is filed as #666 (reverse-masking
            # guard, .agents/testing.md § Locator policy neighbours).
            assert artifacts_page.get_bucket_menu_items_text(pin_bucket) == MENU_TEXT_UNPINNED

        with allure.step("Step 7 — Click 'Pin to top'; the pin request completes"):
            assert artifacts_page.click_bucket_menu_pin_item() == HTTP_OK

        with allure.step("Step 8 — A pin icon appears next to the bucket name"):
            expect(artifacts_page.bucket_pin_indicator(pin_bucket)).to_be_visible(timeout=LIST_REFRESH_TIMEOUT)

        with allure.step("Step 9 — The bucket is now at the top, above all unpinned buckets"):
            self._assert_first_bucket_is(artifacts_page, pin_bucket)
            after_pin = artifacts_page.get_rendered_bucket_names()
            assert after_pin[0] == pin_bucket
            # Exactly one bucket was lifted out of the ordered list — the rest
            # must still be alphanumeric, and unchanged.
            assert after_pin[1:] == sorted(after_pin[1:])
            assert after_pin[1:] == [name for name in baseline if name != pin_bucket]

    # ------------------------------------------------------------------
    # ELITEA-1821
    # ------------------------------------------------------------------

    @pytest.mark.p2
    @allure.title("ELITEA-1821 — Unpin an artifact bucket from the top of the list")
    @allure.description(
        "With a bucket pinned through the product's own 'Pin to top' menu "
        "item, unpins it via 'Unpin from top' and verifies the unpin request "
        "persists (PATCH 200), the pin icon is removed, and the bucket returns "
        "to its alphanumeric position — the whole list restored to its pre-pin "
        "order."
    )
    def test_unpin_bucket_from_top(self, page, pin_bucket):
        with allure.step("Step 1 — Navigate to Artifacts; capture the alphanumeric baseline"):
            artifacts_page = self._open_artifacts(page, pin_bucket)
            expect(artifacts_page.any_bucket_pin_indicator()).to_have_count(0, timeout=UI_ELEMENT_TIMEOUT)
            baseline = artifacts_page.get_rendered_bucket_names()
            assert baseline == sorted(baseline), "Bucket list is not in alphanumeric order"
            assert pin_bucket in baseline
            self._assert_first_bucket_is_not(artifacts_page, pin_bucket)

        with allure.step("Precondition — Pin the bucket through the product's own 'Pin to top' item"):
            self._pin_via_menu(artifacts_page, pin_bucket, MENU_TEXT_UNPINNED)

        with allure.step("Step 2 — The bucket is at the top of the list with a pin icon next to its name"):
            expect(artifacts_page.bucket_pin_indicator(pin_bucket)).to_be_visible(timeout=LIST_REFRESH_TIMEOUT)
            self._assert_first_bucket_is(artifacts_page, pin_bucket)

        with allure.step("Step 3 — Clicking the 3-dot actions icon opens the dropdown"):
            artifacts_page.open_bucket_menu(pin_bucket, timeout=UI_ELEMENT_TIMEOUT)
            expect(artifacts_page.bucket_menu_container(pin_bucket)).to_be_visible(timeout=UI_ELEMENT_TIMEOUT)

        with allure.step("Step 4 — The dropdown now offers 'Unpin from top'"):
            assert artifacts_page.get_bucket_menu_items_text(pin_bucket) == MENU_TEXT_PINNED

        with allure.step("Step 5 — Click 'Unpin from top'; the unpin request completes"):
            assert artifacts_page.click_bucket_menu_pin_item() == HTTP_OK

        with allure.step("Step 6 — The pin icon is no longer displayed next to the bucket"):
            expect(artifacts_page.bucket_pin_indicator(pin_bucket)).to_have_count(0, timeout=LIST_REFRESH_TIMEOUT)
            # And nothing else got pinned by mistake.
            expect(artifacts_page.any_bucket_pin_indicator()).to_have_count(0, timeout=UI_ELEMENT_TIMEOUT)

        with allure.step("Step 7 — The bucket is no longer at the top of the list"):
            self._assert_first_bucket_is_not(artifacts_page, pin_bucket)

        with allure.step("Step 8 — The bucket is back in its correct alphanumeric position"):
            after_unpin = artifacts_page.get_rendered_bucket_names()
            assert after_unpin == sorted(after_unpin), "Bucket list is not in alphanumeric order after unpin"
            assert after_unpin == baseline, "Bucket list order was not restored to its pre-pin state"
