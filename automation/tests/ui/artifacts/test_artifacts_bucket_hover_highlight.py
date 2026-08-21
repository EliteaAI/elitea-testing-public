"""UI test for ELITEA-1823 — a bucket row highlights while the mouse hovers it.

Verifies the Artifacts left panel's hover highlight: the row under the cursor
renders a non-default background, every other row stays at its default one, the
previously hovered row reverts as the cursor moves on, and moving the cursor off
the list clears the highlight entirely.

**Highlighted is asserted as "not the default background", not as a colour
literal.** The default is ``conversation.normal: 'transparent'`` in **both**
palettes (``darkPalette.js:352`` / ``lightPalette.js:350``) → computed
``rgba(0, 0, 0, 0)``, so "this row is in its default appearance" is a
theme-independent fact. The *hover* colour is not: ``white6`` →
``rgba(255, 255, 255, 0.06)`` in dark (live-measured 2026-08-21), ``dark6`` in
light. Asserting default-vs-not-default is exactly what the case's expected
results say ("background colour changes to indicate highlight" / "returns to its
default appearance") without pinning a literal that flips with the user's theme.

**Why the target rows are chosen at run time, never "the first bucket".**
``/artifacts`` auto-selects (and expands) a bucket when the URL carries no
``?bucket=`` param, and ``BucketItem.jsx``'s ``getBackgroundColor()`` returns the
*selected* colour before it ever looks at ``isHovering`` — so hovering the
selected row produces no background change at all (live-measured: row ``aa``
stayed ``rgba(41, 184, 245, 0.15)`` while hovered). The case's literal "the first
bucket in the list" is therefore a trap on a fresh load; filed as a case-text
clarification, https://github.com/EliteaAI/elitea-testing-public/issues/1623.
This test picks the first three rows with ``data-selected="false"`` that are
inside the panel's visible band (a row scrolled out of the ``overflow: auto``
container cannot be hovered).

**Hover here is React state, not a CSS ``:hover`` rule** — ``isHovering`` is set
by ``onMouseEnter``/``onMouseLeave`` on the row's root Box — so a real pointer
move is required, and the single-highlight invariant is structural (one flag per
row, cleared on leave). Each hover is a real ``Locator.hover()``.

Fidelity: **no substitution of any kind** — no seeding, no ``page.route``, no
injected state, no ``evaluate()``. Every asserted value is the
``background-color`` the product computed in response to real mouse events. The
case's ≥2-bucket precondition is satisfied by the project's existing buckets
(768 live), so the test is fully read-only (workflow skill Hard Rule 10) and adds
nothing to the known ``#636`` bucket leak.

AFS:
    test-specs/artifacts/l3_bucket-highlights-on-mouse-hover_ELITEA-1823.md

Markers:
    - ui: requires browser
    - regression: regression test
    - new: added on automation/base, not yet validated on deployed envs

Usage:
    cd automation
    pytest tests/ui/artifacts/test_artifacts_bucket_hover_highlight.py -v
"""

import logging

import allure
import pytest
from pages.artifacts_page import ArtifactsPage
from playwright.sync_api import expect

logger = logging.getLogger(__name__)

pytestmark = [pytest.mark.ui, pytest.mark.regression, pytest.mark.new]

# ---------------------------------------------------------------------------
# Constants
# ---------------------------------------------------------------------------
VIEWPORT_WIDTH = 1600
VIEWPORT_HEIGHT = 900

#: The case's own precondition ("at least two buckets are present").
MIN_BUCKETS = 2

#: How many rows the case's Step 8 ("repeat for several buckets") needs.
HOVER_TARGET_COUNT = 3

#: The computed `background-color` of a bucket row in its DEFAULT appearance —
#: `theme.palette.background.conversation.normal`, which is the literal
#: `'transparent'` in BOTH palettes, hence theme-independent.
DEFAULT_ROW_BACKGROUND = "rgba(0, 0, 0, 0)"

#: How far down the rendered list to scan for hoverable candidates. ~19 rows fit
#: in the panel at 1600x900; 25 keeps the scan short without assuming a row count.
CANDIDATE_SCAN_LIMIT = 25


class TestArtifactsBucketHoverHighlight:
    """ELITEA-1823 — only the bucket under the cursor is highlighted."""

    @staticmethod
    def _assert_default(artifacts_page: ArtifactsPage, bucket_name: str, why: str) -> None:
        """Assert *bucket_name*'s row renders its default (unhighlighted) background."""
        expect(
            artifacts_page.bucket_row(bucket_name),
            f"Bucket {bucket_name!r} should render its default background ({why})",
        ).to_have_css("background-color", DEFAULT_ROW_BACKGROUND)

    @staticmethod
    def _assert_highlighted(artifacts_page: ArtifactsPage, bucket_name: str, why: str) -> None:
        """Assert *bucket_name*'s row renders a NON-default background."""
        expect(
            artifacts_page.bucket_row(bucket_name),
            f"Bucket {bucket_name!r} should be highlighted ({why})",
        ).not_to_have_css("background-color", DEFAULT_ROW_BACKGROUND)

    def test_bucket_highlights_on_mouse_hover(self, page):
        """Hover three bucket rows in turn; only the hovered one is highlighted."""
        page.set_viewport_size({"width": VIEWPORT_WIDTH, "height": VIEWPORT_HEIGHT})
        artifacts_page = ArtifactsPage(page)

        with allure.step("Step 1 — Navigate to the Artifacts section"):
            artifacts_page.navigate_to_artifacts()
            artifacts_page.wait_for_page_load()
            assert artifacts_page.any_bucket_row().is_visible(), (
                "Artifacts page loaded but the left panel rendered no bucket row"
            )

        with allure.step("Step 2 — The bucket list is displayed with at least two buckets"):
            bucket_names = artifacts_page.get_rendered_bucket_names()
            logger.info("Rendered buckets: %d", len(bucket_names))
            assert len(bucket_names) >= MIN_BUCKETS, (
                f"The case needs at least {MIN_BUCKETS} buckets in the project; "
                f"the left panel rendered {len(bucket_names)}"
            )

            # Hover targets are discovered live, never hardcoded: the SELECTED
            # row's background supersedes the hover colour (see the module
            # docstring), and a row clipped by the panel's overflow cannot be
            # hovered at all.
            targets = [
                name
                for name in bucket_names[:CANDIDATE_SCAN_LIMIT]
                if not artifacts_page.is_bucket_selected(name)
                and artifacts_page.is_bucket_row_within_panel(name)
            ][:HOVER_TARGET_COUNT]
            assert len(targets) == HOVER_TARGET_COUNT, (
                f"Need {HOVER_TARGET_COUNT} unselected bucket rows inside the visible panel "
                f"to exercise the case's 'repeat for several buckets' step; found "
                f"{len(targets)} in the first {CANDIDATE_SCAN_LIMIT} rendered rows"
            )
            first_bucket, second_bucket, third_bucket = targets
            logger.info("Hover targets: %s", targets)

        with allure.step("Step 3 — Move the cursor away from the bucket list: nothing is highlighted"):
            artifacts_page.move_mouse_off_bucket_list()
            for name in targets:
                self._assert_default(artifacts_page, name, "the cursor is off the bucket list")

        with allure.step("Steps 4-5 — Hover the first bucket: its background changes to a highlight"):
            artifacts_page.hover_bucket_row(first_bucket)
            self._assert_highlighted(artifacts_page, first_bucket, "it is under the cursor")
            for name in (second_bucket, third_bucket):
                self._assert_default(artifacts_page, name, "it is not the hovered row")

        with allure.step(
            "Steps 6-7 — Move to the next bucket: the previous one reverts, the new one highlights"
        ):
            artifacts_page.hover_bucket_row(second_bucket)
            self._assert_highlighted(artifacts_page, second_bucket, "it is now under the cursor")
            self._assert_default(
                artifacts_page, first_bucket, "the cursor has moved off it to the next bucket"
            )
            self._assert_default(artifacts_page, third_bucket, "it was never hovered")

        with allure.step(
            "Step 8 — Repeat for a third bucket: only the bucket under the cursor is highlighted"
        ):
            artifacts_page.hover_bucket_row(third_bucket)
            self._assert_highlighted(artifacts_page, third_bucket, "it is now under the cursor")
            for name in (first_bucket, second_bucket):
                self._assert_default(artifacts_page, name, "the cursor has moved past it")

        with allure.step(
            "Expected Final State — Moving the cursor off the list removes the highlight"
        ):
            artifacts_page.move_mouse_off_bucket_list()
            for name in targets:
                self._assert_default(artifacts_page, name, "the cursor left the bucket list")
