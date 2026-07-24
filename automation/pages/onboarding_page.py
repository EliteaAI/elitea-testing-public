"""Onboarding page object for the Elitea onboarding surface (/onboarding).

First page object for this surface — built as part of the cov60 campaign's
foundation pass
(test-specs/onboarding/l2_sure-lets-go-triggers-provisioning-and-onboarding-tips_ELITEA-2232.md).
Covers the Welcome screen (never-onboarded user) and the 48-slide onboarding
tour it hands off to after "Sure, let's go!" is clicked.

A genuinely fresh/never-onboarded user cannot be reached via the suite's
normal ``auth_state`` fast-path on localhost (every call carries a fixed
dev token for one persistent backend user whose ``personal_project_id`` is
already set, and there is no in-app signup route) — see the
``fresh_user_route`` fixture (``fixtures/onboarding_fixtures.py``), which
simulates the precondition via route interception, per the AFS's Declared
Improvisation.

URL: / (bare root — ``IndexRoute.jsx`` redirects to ``/onboarding`` when the
authenticated user's ``personal_project_id`` is falsy). Never navigate to
``/onboarding`` directly — it is the redirect TARGET, not a legitimate entry
point a real user would type.
"""

import logging

from utils.actions import action

from .base_page import BasePage
from .locator_descriptor import LocatorDescriptor

logger = logging.getLogger("elitea.pages.onboarding")


class OnboardingPage(BasePage):
    """Page object for the Elitea onboarding flow (Welcome screen + tour).

    Reuses ``ChatPage.sidebar_toggle`` and ``ChatPage.project_selector_trigger``
    for the post-provisioning "ready" state (AFS ELITEA-2232 § Concrete
    Handles) — no new fields are declared here for those two; import
    ``ChatPage`` directly wherever that assertion is needed.

    URL: / (redirects to /onboarding)
    """

    # ------------------------------------------------------------------
    # Welcome screen
    # ------------------------------------------------------------------
    onboarding_welcome_card = LocatorDescriptor(
        testid="onboarding-welcome-card",
        description="Welcome card container shown to a never-onboarded user.",
    )
    onboarding_welcome_get_started_button = LocatorDescriptor(
        testid="onboarding-welcome-get-started-button",
        description='"Sure, let\'s go!" button on the Welcome card.',
    )

    # ------------------------------------------------------------------
    # Tour view (post "Sure, let's go!")
    # ------------------------------------------------------------------
    onboarding_tour_logo = LocatorDescriptor(
        testid="onboarding-tour-logo",
        description="ELITEA logo shown top-center of the tour view.",
    )
    onboarding_tour_content = LocatorDescriptor(
        testid="onboarding-tour-content",
        description="Tip title + description + Quick Action block (one container per slide).",
    )
    onboarding_tour_slide_counter = LocatorDescriptor(
        testid="onboarding-tour-slide-counter",
        description='Slide counter — e.g. "1 / 48".',
    )
    onboarding_tour_progress_footer = LocatorDescriptor(
        testid="onboarding-tour-progress-footer",
        description='Provisioning progress footer — "Configuring Personal project..." + ETA.',
    )
    onboarding_tour_progress_bar = LocatorDescriptor(
        testid="onboarding-tour-progress-bar",
        description="Determinate MUI LinearProgress bar inside the progress footer.",
    )

    # ------------------------------------------------------------------
    # Navigation
    # ------------------------------------------------------------------
    @action("Navigate to onboarding entry point")
    def navigate_to_entry(self) -> None:
        """Navigate to the bare root path.

        ``IndexRoute.jsx`` redirects to ``/onboarding`` when
        ``!user.personal_project_id`` — always navigate to ``/``, never
        ``/onboarding`` directly (AFS ELITEA-2232 § Automation Hints).
        """
        self.navigate("/")

    @action("Wait for Welcome screen")
    def wait_for_welcome_screen(self, timeout: int = 15000) -> None:
        """Wait for the Welcome card to become visible."""
        self.onboarding_welcome_card.wait_for(state="visible", timeout=timeout)

    @action("Click 'Sure, let's go!'")
    def click_get_started(self) -> None:
        """Click the Welcome card's "Sure, let's go!" button."""
        self.onboarding_welcome_get_started_button.click()

    @action("Wait for onboarding tour view")
    def wait_for_tour_view(self, timeout: int = 15000) -> None:
        """Wait for the tour content (post-click) to become visible."""
        self.onboarding_tour_content.wait_for(state="visible", timeout=timeout)

    def get_tour_content_text(self) -> str:
        """Return the tour content block's text (tip title + description + Quick Action)."""
        return self.onboarding_tour_content.text_content() or ""

    def get_slide_counter_text(self) -> str:
        """Return the slide counter's text — e.g. "1 / 48"."""
        return self.onboarding_tour_slide_counter.text_content() or ""

    def is_progress_footer_visible(self) -> bool:
        """Return whether the provisioning progress footer is currently visible."""
        return self.onboarding_tour_progress_footer.is_visible()
