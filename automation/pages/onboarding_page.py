"""Page object for the Elitea Onboarding Welcome page.

URL: /onboarding (reached via redirect from root '/' when the user has no
personal project — personal_project_id is null in Redux state).

The Welcome screen is only rendered when:
  - personal_project_id is null in Redux state (IndexRoute redirects to /onboarding)
  - sessionStorage.onboarding_state is not 'true' (Onboarding.jsx:36)
  - showTour is false (Onboarding.jsx:152)

In a standard test run neither first condition holds naturally for an
existing user, so mock_fresh_user_state() establishes the first-login
precondition by intercepting GET /social/author/ and mutating the response.

Scope boundary: this page object covers the Welcome state only (pre-click on
"Sure, let's go!"). The post-click OnboardingTour state belongs to ELITEA-2232+.
"""

import json
import logging

from .base_page import BasePage
from .locator_descriptor import LocatorDescriptor

logger = logging.getLogger("elitea.pages.onboarding")


class OnboardingPage(BasePage):
    """Onboarding Welcome page object.

    URL: /onboarding

    Testids in use: onboarding-page-container, onboarding-page-logo,
    onboarding-welcome-card, onboarding-welcome-illustration,
    onboarding-welcome-title, onboarding-welcome-greeting,
    onboarding-welcome-body-text, onboarding-welcome-secondary-text,
    onboarding-welcome-get-started-button, onboarding-progress-footer,
    sidebar-toggle (absence), project-selector-trigger (absence).
    """

    # ------------------------------------------------------------------
    # Route pattern — class-level constant per
    # generate_entity_modal_page_base.py:45 (GENERATE_DRAFT_ROUTE)
    # ------------------------------------------------------------------

    AUTHOR_DETAILS_ROUTE = "**/social/author/"
    """Matches GET /api/v2/social/author/ — the authorDetails RTK Query
    endpoint (src/api/social.js:5,122) whose personal_project_id field
    controls the IndexRoute redirect and the Welcome render gate.
    """

    # ------------------------------------------------------------------
    # Locators — page container and logo (Onboarding.jsx)
    # ------------------------------------------------------------------

    page_container = LocatorDescriptor(
        testid="onboarding-page-container",
        description="Full-screen page wrapper (Onboarding.jsx styles.page)",
    )
    page_logo = LocatorDescriptor(
        testid="onboarding-page-logo",
        description="Elitea brand wordmark SVG container above the card (Onboarding.jsx:147-155)",
    )

    # ------------------------------------------------------------------
    # Locators — Welcome card and its contents (Welcome.jsx)
    # ------------------------------------------------------------------

    welcome_card = LocatorDescriptor(
        testid="onboarding-welcome-card",
        description="Welcome card root container (Welcome.jsx styles.container)",
    )
    welcome_illustration = LocatorDescriptor(
        testid="onboarding-welcome-illustration",
        description="Welcome illustration image (chat-welcome.png, alt='Elitea', Welcome.jsx:16-22)",
    )
    welcome_title = LocatorDescriptor(
        testid="onboarding-welcome-title",
        description="Title 'Welcome to Elitea!' (Welcome.jsx:23-29)",
    )
    welcome_greeting = LocatorDescriptor(
        testid="onboarding-welcome-greeting",
        description="Greeting 'Hello, [name]!' first Typography in card body (Welcome.jsx:30-36)",
    )
    welcome_body_text = LocatorDescriptor(
        testid="onboarding-welcome-body-text",
        description="Body text: workspace setup copy (Welcome.jsx:37-45)",
    )
    welcome_secondary_text = LocatorDescriptor(
        testid="onboarding-welcome-secondary-text",
        description="Secondary text: 'Ready to explore Elitea's smart tools and tips?' (Welcome.jsx:46-51)",
    )
    welcome_get_started_button = LocatorDescriptor(
        testid="onboarding-welcome-get-started-button",
        description="'Sure, let's go!' button (Welcome.jsx:52-58) — NOT clicked in ELITEA-2231",
    )

    # ------------------------------------------------------------------
    # Locators — absence assertions (existing testids, on-main ✓)
    # ------------------------------------------------------------------

    sidebar_toggle = LocatorDescriptor(
        testid="sidebar-toggle",
        description=(
            "Sidebar toggle — verified on-main (SidebarBody.jsx:221). "
            "Must be absent on the Welcome screen: MainSidebar.jsx:42 returns null "
            "when isOnboardingPage && !user.personal_project_id."
        ),
    )
    project_selector_trigger = LocatorDescriptor(
        testid="project-selector-trigger",
        description=(
            "Project dropdown trigger — verified on-main (SidebarProjectSelect.jsx:94). "
            "Must be absent on the Welcome screen (sidebar is null, so this is also absent)."
        ),
    )

    # ------------------------------------------------------------------
    # Locators — progress footer (Onboarding.jsx, absence assertion)
    # ------------------------------------------------------------------

    progress_footer = LocatorDescriptor(
        testid="onboarding-progress-footer",
        description=(
            "Configuring Personal project... footer (Onboarding.jsx:182-208). "
            "Rendered only when showTour && !thePrivateProjectIsReady. "
            "Must be absent at the Welcome state (before button click)."
        ),
    )

    # ------------------------------------------------------------------
    # Route mock — fresh-user (first-login) precondition
    # ------------------------------------------------------------------

    def mock_fresh_user_state(self) -> dict:
        """Install a route mock that simulates a fresh-user (first-login) state.

        Intercepts GET /social/author/ via AUTHOR_DETAILS_ROUTE, fetches the
        genuine backend response via route.fetch(), and re-fulfills it with
        personal_project_id set to null while leaving every other field
        byte-identical. All other fields (user name, email, id, etc.) are real
        backend values — the greeting assertion therefore tests the product's
        rendering of the real user's real name.

        DECLARED IMPROVISATION (per .agents/role-overrides.md § Declared-
        improvisation-protocol): Route interception is a sanctioned mechanism
        in this suite — precedent in generate_entity_modal_page_base.py:100-141
        (mock_generate_failure / mock_generate_success), which use
        self.page.route(self.GENERATE_DRAFT_ROUTE, handler) and route.fulfill()
        inside a page-object base class with the route pattern as a class-level
        constant. Prior uses control timing or force error states. THIS use
        establishes an auth/onboarding precondition — a new application of the
        same sanctioned mechanism, ruled by the test-automation lead in batch
        onboarding-w1 DECISIONS.md § D3.

        Coverage boundary: this mock verifies the first-login Welcome UI contract
        when Redux state carries personal_project_id: null. It does NOT verify
        that the backend genuinely returns personal_project_id: null for a
        brand-new user. That is a separate API-level case.

        MUST be called BEFORE the first page.goto() so the very first
        authorDetails call from ProtectedRoutes.jsx is already intercepted.

        Returns:
            A mutable dict that is populated with key 'user' (the real backend
            user dict with personal_project_id replaced with None) once the mock
            handler fires. The caller reads captured['user']['name'] for greeting
            assertions AFTER navigation completes (by which point the handler has
            already fired and populated the dict).
        """
        captured: dict = {}

        def handler(route):
            response = route.fetch()
            body = response.json()
            body["personal_project_id"] = None
            captured["user"] = body
            route.fulfill(
                status=response.status,
                headers=dict(response.headers),
                body=json.dumps(body),
            )

        self.page.route(self.AUTHOR_DETAILS_ROUTE, handler)
        logger.info("Installed fresh-user mock on %s", self.AUTHOR_DETAILS_ROUTE)
        return captured

    def clear_author_details_mock(self) -> None:
        """Remove the route mock on the authorDetails endpoint.

        Called in test teardown. The mock is also auto-cleaned when the browser
        context closes (function-scoped context), so this is a best-practice
        explicit cleanup.
        """
        self.page.unroute(self.AUTHOR_DETAILS_ROUTE)
        logger.info("Cleared fresh-user mock on %s", self.AUTHOR_DETAILS_ROUTE)
