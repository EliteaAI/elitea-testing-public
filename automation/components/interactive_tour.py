"""Interactive Tour component — the running-tour dialog + "Tour Complete!" modal.

Shared UI overlay (not scoped to a single feature area — the tour dialog
mounts independently of the current route). Testids are intentionally
generic (``interactive-tour-*`` / ``interactive-tour-complete-*``), shared by
every tour variant (sidebar/chat/agent/pipeline/...), so this component works
for any tour, not just the Help Center's Sidebar Interactive Tour.

Usage::

    from components.interactive_tour import InteractiveTourCard, TourCompleteCard

    tour = InteractiveTourCard(new_page)
    tour.wait_for_step()
    tour.click_next()

    complete = TourCompleteCard(new_page)
    complete.wait_for()
    complete.click_done()
"""

import logging

from pages.base_page import BasePage
from pages.locator_descriptor import LocatorDescriptor
from utils.actions import action

logger = logging.getLogger("elitea.components.interactive_tour")


class InteractiveTourCard(BasePage):
    """Running-tour dialog: title / description / step counter + footer buttons.

    Mounted independently of the route — works on whatever ``Page`` the tour
    was launched on (e.g. a new tab opened from a Help Center resource link).
    """

    title = LocatorDescriptor(testid="interactive-tour-title")
    description = LocatorDescriptor(testid="interactive-tour-description")
    step_counter = LocatorDescriptor(testid="interactive-tour-step-counter")
    skip_button = LocatorDescriptor(testid="interactive-tour-skip-button")
    back_button = LocatorDescriptor(testid="interactive-tour-back-button")
    # Single stable testid — label flips Next -> Finish on the last step
    # (testid-is-stable-identity ruling; state lives in the label, not the id).
    next_button = LocatorDescriptor(testid="interactive-tour-next-button")
    SPOTLIGHT_TESTID = "interactive-tour-spotlight"
    spotlight = LocatorDescriptor(testid=SPOTLIGHT_TESTID)

    def wait_for_step(self, timeout: int = 10000) -> None:
        """Wait for the tour dialog's step counter to become visible."""
        self.step_counter.wait_for(state="visible", timeout=timeout)

    def get_step_counter_text(self) -> str:
        return (self.step_counter.text_content() or "").strip()

    def get_title_text(self) -> str:
        return (self.title.text_content() or "").strip()

    def get_description_text(self) -> str:
        return (self.description.text_content() or "").strip()

    def is_back_disabled(self) -> bool:
        """Assert state via the ``disabled`` attribute, not colour (PR #581-style)."""
        return self.back_button.get_attribute("disabled") is not None

    def get_next_button_text(self) -> str:
        return (self.next_button.text_content() or "").strip()

    def get_spotlight_bounding_box(self) -> dict | None:
        """Return the spotlight's bounding box, or ``None`` if not rendered.

        The spotlight is only mounted when a target element is resolved.
        Used as the testable proxy for "the highlighted sidebar element
        changes accordingly" — compare consecutive calls' return values.
        """
        if self.spotlight.count() == 0:
            return None
        return self.spotlight.bounding_box()

    def wait_for_spotlight_change(self, previous_bbox: dict | None, timeout: int = 5000) -> dict | None:
        """Wait until the spotlight's bounding box differs from *previous_bbox*.

        The spotlight repositions on a CSS transition (~0.35s) driven by an
        async target-measurement hook (``useTourCardPosition``), so a bare
        read immediately after a step change can race the layout update.
        This is a condition wait (native ``wait_for_function`` polling the
        live DOM), not a sleep — it returns as soon as the rect actually
        changes, or raises on timeout.

        Args:
            previous_bbox: the bounding box to diff against (``None`` if the
                spotlight wasn't rendered before this step).
            timeout: Maximum wait time in milliseconds.

        Returns:
            The new bounding box (or ``None`` if the spotlight isn't rendered).
        """
        self.page.wait_for_function(
            """([selector, prev]) => {
                const el = document.querySelector(selector);
                if (!el) return prev === null;
                const r = el.getBoundingClientRect();
                if (!prev) return true;
                return r.x !== prev.x || r.y !== prev.y || r.width !== prev.width || r.height !== prev.height;
            }""",
            arg=[f'[data-testid="{self.SPOTLIGHT_TESTID}"]', previous_bbox],
            timeout=timeout,
        )
        return self.get_spotlight_bounding_box()

    @action("Click Next in the tour dialog")
    def click_next(self) -> None:
        self.next_button.click()

    @action("Click Back in the tour dialog")
    def click_back(self) -> None:
        self.back_button.click()

    @action("Click Skip in the tour dialog")
    def click_skip(self) -> None:
        self.skip_button.click()

    @action("Click Finish in the tour dialog")
    def click_finish(self) -> None:
        # Same testid as Next — its label flips to "Finish" on the last step.
        self.next_button.click()


class TourCompleteCard(BasePage):
    """"Tour Complete!" modal shown after clicking Finish on the last step."""

    complete_icon = LocatorDescriptor(testid="interactive-tour-complete-icon")
    complete_title = LocatorDescriptor(testid="interactive-tour-complete-title")
    keep_exploring_label = LocatorDescriptor(testid="interactive-tour-complete-keep-exploring-label")
    done_button = LocatorDescriptor(testid="interactive-tour-complete-done-button")

    # Dynamic testid template — the "Keep exploring" option keyed by tourId.
    COMPLETE_KEEP_EXPLORING_OPTION = '[data-testid="interactive-tour-complete-keep-exploring-{}"]'

    def wait_for(self, timeout: int = 10000) -> None:
        """Wait for the "Tour Complete!" modal to become visible."""
        self.complete_title.wait_for(state="visible", timeout=timeout)

    def keep_exploring_option(self, tour_id: str):
        """Locator for a "Keep exploring" option, e.g. ``tour_id="chat"``."""
        return self.page.locator(self.COMPLETE_KEEP_EXPLORING_OPTION.format(tour_id))

    @action("Click Done in the Tour Complete modal")
    def click_done(self) -> None:
        self.done_button.click()
