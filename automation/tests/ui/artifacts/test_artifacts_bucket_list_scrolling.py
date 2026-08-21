"""UI test for ELITEA-1822 — scroll through a bucket list with 20+ buckets.

Verifies that the Artifacts left panel's bucket list is fully scrollable in
both directions with the **mouse wheel** and with the **arrow keys**: from the
first bucket down to the very last one and back.

**Why "visible" is measured as geometry, not ``is_visible()``.** The bucket list
lives in a Box with ``overflow-y: auto`` (``BucketsPanel.jsx``) and is NOT
virtualised — all 768 buckets of the project are real DOM rows (container
``scrollHeight`` 30792 vs ``clientHeight`` 755, live-measured 2026-08-21). A row
30 000 px below the fold still has a bounding box and no ``visibility: hidden``,
so Playwright reports it *visible*. The honest oracle is therefore
``ArtifactsPage.is_bucket_row_within_panel()``: the row's own box compared with
the scroll container's — both located by testid.

**Keyboard scrolling works even though nothing is focusable.** The panel carries
no ``tabIndex`` and no ``onKeyDown``; after a click inside it,
``document.activeElement`` stays ``BODY``. Chromium nevertheless keeps the
clicked scroll container as the arrow-key scroll target — live-measured at
~38.7 px per press. The click deliberately lands in the container's left padding
gutter: clicking a bucket ROW would select and expand that bucket, a different
interaction from the one the case describes (verified live — the gutter click
leaves the URL unchanged and selects nothing).

**Reaching the top before Step 4 is part of the setup, not a hidden assertion.**
``SimpleBucketList.jsx`` scrolls the URL-selected bucket into view on first load
and ``/artifacts`` auto-selects a bucket, so the list does not reliably start at
its top. The test wheels up to the top first — using the product's own scrolling,
no injected scroll position — because the case's Steps 4-6 presume a top start.

Fidelity: **no substitution of any kind** — no seeding, no ``page.route``, no
injected state, no ``evaluate()``. Every observable is geometry the product
rendered in response to real wheel / key events. The case's ≥20-bucket
precondition is satisfied by the project's existing buckets (768 live), so the
test is fully read-only (workflow skill Hard Rule 10) and adds nothing to the
known ``#636`` bucket leak — deliberately NOT creating "bucket-1…bucket-20".

AFS:
    test-specs/artifacts/l3_scroll-bucket-list-20-or-more-buckets_ELITEA-1822.md

Markers:
    - ui: requires browser
    - regression: regression test
    - new: added on automation/base, not yet validated on deployed envs

Usage:
    cd automation
    pytest tests/ui/artifacts/test_artifacts_bucket_list_scrolling.py -v
"""

import logging

import allure
import pytest
from pages.artifacts_page import ArtifactsPage

logger = logging.getLogger(__name__)

pytestmark = [pytest.mark.ui, pytest.mark.regression, pytest.mark.new]

# ---------------------------------------------------------------------------
# Constants
# ---------------------------------------------------------------------------
VIEWPORT_WIDTH = 1600
VIEWPORT_HEIGHT = 900

#: The case's own precondition / Step 3 expected result.
MIN_BUCKETS = 20

#: One "notch" of the wheel, and the long stride used to traverse a list that is
#: ~30 000 px tall. Both are plain wheel events — only the delta differs.
WHEEL_NOTCH_PX = 500
WHEEL_STRIDE_PX = 5000

#: Bounds for the "keep scrolling until …" loops. Live: 6 strides reach the
#: bottom of 768 buckets, 7 return to the top; ~20 ArrowDown presses clear the
#: fold. The bounds are generous so a slower environment still finishes, and
#: finite so a broken scroll fails loudly instead of hanging.
MAX_WHEEL_STEPS = 40
MAX_KEY_PRESSES = 80

#: Where to start scanning for the first bucket below the fold. ~19 rows fit in
#: the panel at 1600x900; scanning from 15 keeps the scan short without assuming
#: an exact row count.
FOLD_SCAN_START = 15
FOLD_SCAN_END = 80

#: "The first bucket is at the top" tolerance: the container's own 16 px padding
#: plus one 40 px row.
TOP_ALIGNMENT_TOLERANCE_PX = 56

SCROLL_SETTLE_TIMEOUT = 5_000


class TestArtifactsBucketListScrolling:
    """ELITEA-1822 — mouse-wheel and keyboard scrolling of the bucket list."""

    def test_scroll_bucket_list_with_20_or_more_buckets(self, page):
        """Scroll a 20+ bucket list end-to-end with the wheel and the arrow keys."""
        page.set_viewport_size({"width": VIEWPORT_WIDTH, "height": VIEWPORT_HEIGHT})
        artifacts_page = ArtifactsPage(page)

        with allure.step("Step 1 — Navigate to the Artifacts section"):
            artifacts_page.navigate_to_artifacts()
            artifacts_page.wait_for_page_load()
            assert artifacts_page.any_bucket_row().is_visible(), (
                "Artifacts page loaded but the left panel rendered no bucket row"
            )

        with allure.step("Steps 2-3 — The bucket list is displayed with at least 20 buckets"):
            bucket_names = artifacts_page.get_rendered_bucket_names()
            logger.info("Rendered buckets: %d", len(bucket_names))
            assert len(bucket_names) >= MIN_BUCKETS, (
                f"The case needs at least {MIN_BUCKETS} buckets in the project; "
                f"the left panel rendered {len(bucket_names)}"
            )
            first_bucket = bucket_names[0]
            last_bucket = bucket_names[-1]

        with allure.step("Step 4 — Place the mouse cursor over the bucket list panel"):
            artifacts_page.hover_buckets_panel()

            # Setup, not an assertion: reach the top of the list with the
            # product's own wheel scrolling — /artifacts auto-selects a bucket
            # and scrolls it into view, so the list does not reliably start there.
            for _ in range(MAX_WHEEL_STEPS):
                if artifacts_page.is_bucket_row_within_panel(first_bucket):
                    break
                artifacts_page.wheel_buckets_panel(-WHEEL_STRIDE_PX)
            assert artifacts_page.wait_until_bucket_row_within_panel(
                first_bucket, timeout=SCROLL_SETTLE_TIMEOUT
            ), f"Could not reach the top of the bucket list ({first_bucket!r} never came into view)"

            # The first bucket below the fold — discovered live, never hardcoded:
            # row and panel heights are theme- and viewport-dependent.
            below_fold_bucket = next(
                (
                    name
                    for name in bucket_names[FOLD_SCAN_START:FOLD_SCAN_END]
                    if not artifacts_page.is_bucket_row_within_panel(name)
                ),
                None,
            )
            assert below_fold_bucket is not None, (
                "No bucket row is out of view at the top of the list — the list is "
                "not longer than the panel, so there is nothing to scroll"
            )

        with allure.step("Step 5 — Scroll down using the mouse scroll wheel"):
            artifacts_page.wheel_buckets_panel(WHEEL_NOTCH_PX)
            assert artifacts_page.wait_until_bucket_row_within_panel(
                below_fold_bucket, timeout=SCROLL_SETTLE_TIMEOUT
            ), (
                f"After one wheel notch the bucket below the fold ({below_fold_bucket!r}) "
                "is still not visible — the list did not scroll down"
            )
            assert not artifacts_page.is_bucket_row_within_panel(first_bucket), (
                f"The list did not move: the first bucket ({first_bucket!r}) is still in view "
                "after scrolling down"
            )

        with allure.step("Step 6 — Continue scrolling down until the last bucket is visible"):
            for _ in range(MAX_WHEEL_STEPS):
                if artifacts_page.is_bucket_row_within_panel(last_bucket):
                    break
                artifacts_page.wheel_buckets_panel(WHEEL_STRIDE_PX)
            assert artifacts_page.wait_until_bucket_row_within_panel(
                last_bucket, timeout=SCROLL_SETTLE_TIMEOUT
            ), (
                f"The last bucket ({last_bucket!r}, #{len(bucket_names)}) never became visible "
                f"within {MAX_WHEEL_STEPS} wheel steps — the full list is not reachable by wheel"
            )

        with allure.step("Step 7 — Scroll back up using the mouse scroll wheel"):
            artifacts_page.wheel_buckets_panel(-WHEEL_NOTCH_PX)
            assert artifacts_page.wait_until_bucket_row_within_panel(
                last_bucket, expected=False, timeout=SCROLL_SETTLE_TIMEOUT
            ), (
                f"After one upward wheel notch the last bucket ({last_bucket!r}) is still in "
                "view — the list did not scroll up"
            )

        with allure.step("Step 8 — Continue scrolling up until the first bucket is visible"):
            for _ in range(MAX_WHEEL_STEPS):
                if artifacts_page.is_bucket_row_within_panel(first_bucket):
                    break
                artifacts_page.wheel_buckets_panel(-WHEEL_STRIDE_PX)
            assert artifacts_page.wait_until_bucket_row_within_panel(
                first_bucket, timeout=SCROLL_SETTLE_TIMEOUT
            ), f"The first bucket ({first_bucket!r}) never came back into view when scrolling up"
            offset = artifacts_page.bucket_row_offset_from_panel_top(first_bucket)
            assert offset is not None and offset <= TOP_ALIGNMENT_TOLERANCE_PX, (
                f"The first bucket ({first_bucket!r}) is visible but sits {offset} px below the "
                f"panel's top edge — the list is not scrolled back to the top"
            )

        with allure.step("Step 9 — Click into the panel and press the Down arrow repeatedly"):
            url_before_click = page.url
            artifacts_page.click_into_buckets_panel()
            assert page.url == url_before_click, (
                "Clicking the bucket list panel's gutter navigated "
                f"({url_before_click} -> {page.url}) — it must not select a bucket"
            )
            for _ in range(MAX_KEY_PRESSES):
                if artifacts_page.is_bucket_row_within_panel(below_fold_bucket):
                    break
                artifacts_page.press_key_in_buckets_panel("ArrowDown")
            assert artifacts_page.wait_until_bucket_row_within_panel(
                below_fold_bucket, timeout=SCROLL_SETTLE_TIMEOUT
            ), (
                f"ArrowDown x{MAX_KEY_PRESSES} did not bring {below_fold_bucket!r} into view — "
                "the bucket list does not scroll under the keyboard"
            )
            assert not artifacts_page.is_bucket_row_within_panel(first_bucket), (
                f"The first bucket ({first_bucket!r}) is still in view after pressing ArrowDown — "
                "the list did not scroll down"
            )

        with allure.step("Step 10 — Press the Up arrow repeatedly to return to the first bucket"):
            for _ in range(MAX_KEY_PRESSES):
                if artifacts_page.is_bucket_row_within_panel(first_bucket):
                    break
                artifacts_page.press_key_in_buckets_panel("ArrowUp")
            assert artifacts_page.wait_until_bucket_row_within_panel(
                first_bucket, timeout=SCROLL_SETTLE_TIMEOUT
            ), f"ArrowUp x{MAX_KEY_PRESSES} did not scroll back to the first bucket"
            offset = artifacts_page.bucket_row_offset_from_panel_top(first_bucket)
            assert offset is not None and offset <= TOP_ALIGNMENT_TOLERANCE_PX, (
                f"After ArrowUp the first bucket ({first_bucket!r}) sits {offset} px below the "
                "panel's top edge — the list is not back at the first listed bucket"
            )
