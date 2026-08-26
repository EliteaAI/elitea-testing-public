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

Scope boundary (extended 2026-08-24, ELITEA-2235/2236/2241): this page object
covers BOTH onboarding states rendered by Onboarding.jsx:
  - the Welcome state (ELITEA-2231) — pre-click on "Sure, let's go!";
  - the tour + workspace-ready state — the OnboardingTour tips card, its
    full-screen dialog, and the WorkspaceIsReady banner.

The two states share the page shell (onboarding-page-container /
onboarding-page-logo / onboarding-progress-footer), which is why they live in
one page object: a testid appears in exactly one file (.agents/conventions.md).
The tour state needs NO route mock — an authenticated user WITH a personal
project navigating to /onboarding lands in it directly (Onboarding.jsx:130-134
sets thePrivateProjectIsReady whenever user.personal_project_id is truthy).
mock_fresh_user_state() belongs to the Welcome state only; never call it for
tour-state cases.
"""

import json
import logging

from playwright.sync_api import Locator
from utils.actions import action

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
    onboarding-progress-status-label, onboarding-progress-estimated-time,
    onboarding-progress-bar,
    sidebar-toggle, project-selector-trigger,
    project-selector-option-{label} (dynamic), sidebar-menu-item-{value} (dynamic),
    sidebar-settings-button, sidebar-agent-hub-button, select-option-selected-icon,
    onboarding-tour-container, onboarding-tour-tip-content,
    onboarding-tour-tip-image, onboarding-tour-page-indicator,
    onboarding-tour-prev-button, onboarding-tour-next-button,
    onboarding-tour-fullscreen-button,
    onboarding-tour-fullscreen-dialog, onboarding-tour-fullscreen-title,
    onboarding-tour-fullscreen-close-button,
    onboarding-workspace-ready-title,
    onboarding-workspace-ready-jump-in-button.
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
    progress_status_label = LocatorDescriptor(
        testid="onboarding-progress-status-label",
        description=(
            "'Configuring Personal project...' status line inside the progress "
            "footer (Onboarding.jsx:188-194). Present only while "
            "showTour && !thePrivateProjectIsReady."
        ),
    )
    progress_estimated_time = LocatorDescriptor(
        testid="onboarding-progress-estimated-time",
        description=(
            "'about 5 min' estimate inside the progress footer "
            "(Onboarding.jsx:195-201)."
        ),
    )
    progress_bar = LocatorDescriptor(
        testid="onboarding-progress-bar",
        description=(
            "Determinate MUI LinearProgress inside the progress footer "
            "(Onboarding.jsx:204-209). role='progressbar'; aria-valuenow starts "
            "at 5 and grows by 95/150 per second, capped at 95 "
            "(Onboarding.jsx:71-73) — client-side animation only."
        ),
    )

    # ------------------------------------------------------------------
    # Locators — onboarding tips card (OnboardingTour.jsx / TourContent.jsx)
    # ELITEA-2235 / ELITEA-2236
    # ------------------------------------------------------------------

    tour_container = LocatorDescriptor(
        testid="onboarding-tour-container",
        description="Tips-card wrapper (OnboardingTour.jsx styles.wrapper)",
    )
    tour_tip_content = LocatorDescriptor(
        testid="onboarding-tour-tip-content",
        description=(
            "Single markdown node carrying the slide's tip title, description and "
            "Quick Action (TourContent.jsx). The three parts have no testids of "
            "their own — the DOM inside is produced by the Markdown renderer, not "
            "by app JSX — so they are asserted with contains-text on this node. "
            "Resolves to TWO nodes while the full-screen dialog is open (the "
            "embedded copy stays mounted): scope with DIALOG_TIP_CONTENT."
        ),
    )
    tour_tip_image = LocatorDescriptor(
        testid="onboarding-tour-tip-image",
        description=(
            "Slide illustration (TourContent.jsx <Box component='img'>). "
            "Added for ELITEA-2236 (EliteaAI/EliteaUI@3ba7967d). "
            "Also resolves to two nodes while the dialog is open."
        ),
    )
    tour_page_indicator = LocatorDescriptor(
        testid="onboarding-tour-page-indicator",
        description=(
            "Slide counter '{currentStep} / {onboardingTips.length}' "
            "(TourContent.jsx). Two nodes while the dialog is open."
        ),
    )
    tour_prev_button = LocatorDescriptor(
        testid="onboarding-tour-prev-button",
        description=(
            "Previous-slide IconButton — disabled at slide 1 "
            "(TourContent.jsx: disabled={currentStep === 1})"
        ),
    )
    tour_next_button = LocatorDescriptor(
        testid="onboarding-tour-next-button",
        description=(
            "Next-slide IconButton — disabled at the last slide "
            "(TourContent.jsx: disabled={currentStep === onboardingTips.length}). "
            "Added for ELITEA-2237/2238/2239 (EliteaAI/EliteaUI@f647488d). "
            "Resolves to TWO nodes while the full-screen dialog is open: scope "
            "with DIALOG_NEXT_BUTTON."
        ),
    )
    tour_fullscreen_button = LocatorDescriptor(
        testid="onboarding-tour-fullscreen-button",
        description=(
            "Expand icon in the card's top-right corner (aria-label "
            "'View tour in full screen'). Added for ELITEA-2236 "
            "(EliteaAI/EliteaUI@3ba7967d)."
        ),
    )
    tour_fullscreen_dialog = LocatorDescriptor(
        testid="onboarding-tour-fullscreen-dialog",
        description=(
            "Full-screen Dialog PAPER — wired via slotProps.paper, deliberately "
            "NOT the MUI Modal root: the root is position:fixed/inset:0 for every "
            "dialog, so a bounding-box 'is it fullscreen' assertion against it "
            "would be a tautology. The paper is the element MUI resizes when "
            "fullScreen is set. Added for ELITEA-2236 (EliteaAI/EliteaUI@3ba7967d)."
        ),
    )
    tour_fullscreen_title = LocatorDescriptor(
        testid="onboarding-tour-fullscreen-title",
        description=(
            "'Onboarding tips' heading in the dialog header. "
            "Added for ELITEA-2236 (EliteaAI/EliteaUI@3ba7967d)."
        ),
    )
    tour_fullscreen_close_button = LocatorDescriptor(
        testid="onboarding-tour-fullscreen-close-button",
        description=(
            "X (collapse) IconButton in the dialog header (aria-label "
            "'Close full screen tour'). Added for ELITEA-2236 "
            "(EliteaAI/EliteaUI@3ba7967d)."
        ),
    )

    # Dialog-scoped selectors — the embedded TourContent stays mounted while the
    # dialog renders a SECOND copy, so the shared testids resolve to two visible
    # nodes and an unscoped expect() is a strict-mode violation. Class-level
    # constants containing [data-testid="..."] only, per
    # .claude/rules/page-objects.md / .agents/testing.md § Locator policy.
    DIALOG_TIP_CONTENT = (
        '[data-testid="onboarding-tour-fullscreen-dialog"] '
        '[data-testid="onboarding-tour-tip-content"]'
    )
    DIALOG_TIP_IMAGE = (
        '[data-testid="onboarding-tour-fullscreen-dialog"] '
        '[data-testid="onboarding-tour-tip-image"]'
    )
    DIALOG_PAGE_INDICATOR = (
        '[data-testid="onboarding-tour-fullscreen-dialog"] '
        '[data-testid="onboarding-tour-page-indicator"]'
    )
    DIALOG_PREV_BUTTON = (
        '[data-testid="onboarding-tour-fullscreen-dialog"] '
        '[data-testid="onboarding-tour-prev-button"]'
    )
    DIALOG_NEXT_BUTTON = (
        '[data-testid="onboarding-tour-fullscreen-dialog"] '
        '[data-testid="onboarding-tour-next-button"]'
    )

    # Card-scoped selectors — the mirror image of the dialog-scoped ones. While the
    # full-screen dialog is open the shared testids resolve to two nodes, so reading
    # the EMBEDDED copy also needs scoping. The dialog's paper is NOT a descendant of
    # onboarding-tour-container, so scoping into the card selects the embedded copy
    # alone (ELITEA-2239 step 9 — "consistent with the collapsed card view").
    CARD_PAGE_INDICATOR = (
        '[data-testid="onboarding-tour-container"] '
        '[data-testid="onboarding-tour-page-indicator"]'
    )
    CARD_TIP_CONTENT = (
        '[data-testid="onboarding-tour-container"] '
        '[data-testid="onboarding-tour-tip-content"]'
    )

    # Dynamic (runtime-parameterized) testids — class-level template constants per
    # .agents/testing.md § Locator policy (inline get_by_test_id(f"...") is NOT
    # compliant; the pattern must stay greppable at class level).
    PROJECT_SELECTOR_OPTION = '[data-testid="project-selector-option-{}"]'
    """Row inside the OPEN project dropdown, keyed by project label
    (SidebarProjectSelect.jsx customRenderOption — testid added for ELITEA-2232,
    EliteaAI/EliteaUI@bb8b9adc). Live value for the standard test user: 'Private'.
    """

    PROJECT_SELECTOR_OPTION_SELECTED = '[data-selected="true"] [data-testid="project-selector-option-{}"]'
    """The SELECTED project row inside the OPEN dropdown, keyed by project label.

    Selection state is a data-* attribute on a stable element, never a
    state-named testid (.agents/testing.md § Locator policy). The attribute sits
    on the MUI MenuItem root -- the option itself -- while the testid sits on the
    content row the project selector renders inside it (shared
    SingleSelectMenuItem.jsx: data-selected={isSelected ? 'true' : 'false'};
    SidebarProjectSelect.jsx customRenderOption: the project-selector-option-*
    Box). Added for ELITEA-2240 (EliteaAI/EliteaUI@b0a7d61a).
    """

    SIDEBAR_MENU_ITEM = '[data-testid="sidebar-menu-item-{}"]'
    """Sidebar entity menu item, keyed by entity value (SidebarBody.jsx:272,
    testId prop). Values: chat, agents, pipelines, skills, toolkits, mcps,
    credentials, applications, artifacts. The menu fills in progressively after
    the project becomes ready — anchor on ONE item with an auto-waiting expect(),
    never assert the item count.
    """

    # ------------------------------------------------------------------
    # Locators — sidebar bottom section + selected-option indicator
    # ELITEA-2240
    # ------------------------------------------------------------------

    sidebar_settings_button = LocatorDescriptor(
        testid="sidebar-settings-button",
        description=(
            "'Settings' button in the sidebar's bottom section "
            "(SettingsButton.jsx:27, testId prop). NOT a sidebar-menu-item-* -- the "
            "bottom section is rendered separately from the entity menu."
        ),
    )
    sidebar_agent_hub_button = LocatorDescriptor(
        testid="sidebar-agent-hub-button",
        description=(
            "'Catalog' button in the sidebar's bottom section "
            "(AgentHubButton.jsx:38). Same separate-section note as Settings; the "
            "product label is 'Catalog', the testid keeps the agent-hub name."
        ),
    )
    select_option_selected_icon = LocatorDescriptor(
        testid="select-option-selected-icon",
        description=(
            "Checkmark (CheckedIcon) in the selected option's ListItemIcon of any "
            "single-select menu (shared SingleSelectMenuItem.jsx, isSelected "
            "branch). Deliberately GENERIC -- the component is shared "
            "(.agents/testing.md § Locator policy). Exactly one node exists inside "
            "one open single-select. Added for ELITEA-2240 "
            "(EliteaAI/EliteaUI@b0a7d61a)."
        ),
    )

    # ------------------------------------------------------------------
    # Locators — workspace-ready banner (WorkspaceIsReady.jsx)
    # ELITEA-2235 / ELITEA-2241
    # ------------------------------------------------------------------

    workspace_ready_title = LocatorDescriptor(
        testid="onboarding-workspace-ready-title",
        description="Banner title 'Your Elitea workspace is ready!' (WorkspaceIsReady.jsx)",
    )
    workspace_ready_jump_in_button = LocatorDescriptor(
        testid="onboarding-workspace-ready-jump-in-button",
        description=(
            "'Jump in now!' button (WorkspaceIsReady.jsx) — handleJumpIn clears "
            "sessionStorage.onboarding_state and navigates to /chat"
        ),
    )

    # ------------------------------------------------------------------
    # Dialog-scoped locator accessors (tour full-screen state)
    # ------------------------------------------------------------------

    def dialog_tip_content(self) -> Locator:
        """Tip markdown node INSIDE the full-screen dialog."""
        return self.page.locator(self.DIALOG_TIP_CONTENT)

    def dialog_tip_image(self) -> Locator:
        """Slide illustration INSIDE the full-screen dialog."""
        return self.page.locator(self.DIALOG_TIP_IMAGE)

    def dialog_page_indicator(self) -> Locator:
        """Slide counter INSIDE the full-screen dialog."""
        return self.page.locator(self.DIALOG_PAGE_INDICATOR)

    def dialog_prev_button(self) -> Locator:
        """Previous-slide arrow INSIDE the full-screen dialog."""
        return self.page.locator(self.DIALOG_PREV_BUTTON)

    def dialog_next_button(self) -> Locator:
        """Next-slide arrow INSIDE the full-screen dialog."""
        return self.page.locator(self.DIALOG_NEXT_BUTTON)

    def card_page_indicator(self) -> Locator:
        """Slide counter on the EMBEDDED card (valid while the dialog is open)."""
        return self.page.locator(self.CARD_PAGE_INDICATOR)

    def card_tip_content(self) -> Locator:
        """Tip markdown node on the EMBEDDED card (valid while the dialog is open)."""
        return self.page.locator(self.CARD_TIP_CONTENT)

    def project_selector_option(self, label: str) -> Locator:
        """Project row inside the OPEN project dropdown, by project label."""
        return self.page.locator(self.PROJECT_SELECTOR_OPTION.format(label))

    def project_selector_option_selected(self, label: str) -> Locator:
        """SELECTED project row inside the OPEN project dropdown, by label."""
        return self.page.locator(self.PROJECT_SELECTOR_OPTION_SELECTED.format(label))

    def sidebar_menu_item(self, value: str) -> Locator:
        """Sidebar entity menu item, by entity value (e.g. 'chat')."""
        return self.page.locator(self.SIDEBAR_MENU_ITEM.format(value))

    # ------------------------------------------------------------------
    # Actions — tour card / banner
    # ------------------------------------------------------------------

    @action("Click 'Sure, let's go!' on the Welcome card")
    def click_get_started(self) -> None:
        """Leave the Welcome state and enter the tour state.

        Onboarding.jsx handleShowTour() writes sessionStorage.onboarding_state,
        starts the client-side progress animation and starts a 5 s poll of
        GET /api/v2/social/author/. It issues no provisioning call of its own.
        """
        self.welcome_get_started_button.click()

    @action("Open the project dropdown from the sidebar")
    def open_project_selector(self) -> None:
        """Click the sidebar project-selector trigger to list the projects."""
        self.project_selector_trigger.click()

    @action("Open the onboarding tips card in full screen")
    def open_tour_fullscreen(self) -> None:
        """Click the expand icon in the tips card's top-right corner."""
        self.tour_fullscreen_button.click()

    @action("Collapse the full-screen onboarding tips dialog")
    def close_tour_fullscreen(self) -> None:
        """Click the dialog's X button.

        Escape also closes the dialog (OnboardingTour.jsx handleKeyDown), but
        ELITEA-2236 step 8 asks specifically for the X button.
        """
        self.tour_fullscreen_close_button.click()

    @action("Advance the onboarding tips card to the next slide")
    def click_next_slide(self) -> None:
        """Click the embedded card's forward arrow."""
        self.tour_next_button.click()

    @action("Return the onboarding tips card to the previous slide")
    def click_prev_slide(self) -> None:
        """Click the embedded card's back arrow."""
        self.tour_prev_button.click()

    @action("Advance the full-screen tips dialog to the next slide")
    def click_dialog_next_slide(self) -> None:
        """Click the forward arrow inside the full-screen dialog."""
        self.dialog_next_button().click()

    @action("Return the full-screen tips dialog to the previous slide")
    def click_dialog_prev_slide(self) -> None:
        """Click the back arrow inside the full-screen dialog."""
        self.dialog_prev_button().click()

    @action("Click 'Jump in now!' in the workspace-ready banner")
    def click_jump_in(self) -> None:
        """Dismiss onboarding and navigate to the default project page."""
        self.workspace_ready_jump_in_button.click()

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
