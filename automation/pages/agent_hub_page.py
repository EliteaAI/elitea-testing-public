"""Agent Hub ("Catalog") page object — ELITEA-2075.

Handles the public Agent Hub / Catalog listing (``/elitea-catalog``): the
page heading + search bar, category sections, agent cards, and the agent
preview modal opened by clicking a card (AgentModal.jsx).

No page object previously existed for this surface (confirmed via a fresh
grep against both ``origin/main`` and ``origin/automation/testids`` — zero
testids anywhere in ``AgentHub.jsx``/``AgentCard.jsx``/``AgentModal.jsx``
before this implementation) — this is genuinely new coverage.

ELITEA-2350 extends this page object with the category filter-rail chips
(``CategoryRail.jsx``, shared with the Skills tab) and an agent-card-count
helper, for the page-load verification case.

ELITEA-2352 adds click/selected-state helpers for the same filter-rail chips.
The chip's "selected" state has no accessible signal via Playwright's own
`[active]` accessibility marker (that reflects DOM focus, not app selection —
see ``test-specs/agent-hub/_surface.md``); a ``data-selected`` state attribute
was added to the chip in ``CategoryRail.jsx`` (``EliteaAI/EliteaUI@9b93f67c``)
per ``.agents/testing.md``'s "state via data-* attributes" rule.

URL: /elitea-catalog
"""

import logging
import re

from playwright.sync_api import Page, expect
from utils.actions import action

from .base_page import BasePage
from .locator_descriptor import LocatorDescriptor

logger = logging.getLogger("elitea.pages.agent_hub")

_CATEGORY_SLUG_RE = re.compile(r"[^a-z0-9]+")


def _slugify_category(category: str) -> str:
    """Slugify a category display label the same way EliteaUI does client-side
    (``AgentCategorySection.jsx``/``CategoryRail.jsx``): lowercase, then
    non-alphanumeric runs collapsed to a single ``-`` (e.g. "Knowledge &
    Documentation" -> "knowledge-documentation").
    """
    return _CATEGORY_SLUG_RE.sub("-", category.lower())


class AgentHubPage(BasePage):
    """Page object for the Agent Hub / Catalog listing + agent preview modal.

    Inherits nothing — this surface has no relation to the agent CRUD form
    hierarchy (``AgentFormPage``/``AgentDetailPage``); it is a read-only
    public listing + preview modal (see ``.claude/rules/page-objects.md``
    "Don't inherit when pages are unrelated").
    """

    page_heading = LocatorDescriptor(
        testid="catalog-page-heading",
        description="'Welcome to ELITEA Catalog!' heading (EliteaCatalog.jsx).",
    )

    search_input = LocatorDescriptor(
        testid="catalog-search-input",
        description="Catalog search TextField (agents/skills, shared across both tabs).",
    )

    # Category section heading — dynamic per category name (slugified:
    # lowercase, non-alnum runs -> '-'). Templated class-level constant per
    # .agents/testing.md's dynamic-testid convention.
    CATEGORY_HEADING = '[data-testid="catalog-category-heading-{}"]'

    # Agent card — dynamic per application id (unknown ahead of time from a
    # display name alone), so a prefix-match + .filter(has_text=...) is used
    # to select by name, same idiom as AgentDetailPage.MODEL_SELECTOR_OPTION_ANY_SELECTOR.
    AGENT_CARD_PREFIX = '[data-testid^="catalog-agent-card-"]'

    # Content-list category heading — prefix match across ALL rendered category
    # sections (ELITEA-2352), used to enumerate which categories are currently
    # visible rather than probing one at a time. Same underlying testid as
    # CATEGORY_HEADING above, just unparameterized for the "list them all" case.
    CATEGORY_HEADING_PREFIX = '[data-testid^="catalog-category-heading-"]'

    # Category filter-rail chip (Featured + Categories sections,
    # CategoryRail.jsx, ELITEA-2350) — dynamic per category name, same
    # slugify convention as CATEGORY_HEADING above. Threaded from AgentsTab
    # via a caller-supplied `chipTestIdPrefix` prop per the shared-component
    # testid discipline (CategoryRail is shared with SkillsTab).
    CATEGORY_FILTER_CHIP = '[data-testid="catalog-agent-category-filter-chip-{}"]'

    # Like button (heart icon + count) on an agent card, ELITEA-2354 —
    # dynamic per application id, same idiom as CATEGORY_FILTER_CHIP/
    # CATEGORY_HEADING above. Root component is the SHARED `Like.jsx`
    # (also consumed by the data-table widget and pipeline Card.jsx), so
    # the testid is a caller-supplied `testId` prop threaded
    # AgentCard.jsx -> AgentHubLike.jsx -> Like.jsx, not hardcoded inside
    # Like.jsx itself (EliteaAI/EliteaUI@e079c0d0). "Liked" state is a
    # `data-liked="true"/"false"` attribute on the SAME button (state via
    # data-*, not a state-switched testid — same precedent as
    # CATEGORY_FILTER_CHIP's `data-selected`, ELITEA-2352).
    LIKE_BUTTON = '[data-testid="catalog-agent-like-button-{}"]'

    # --- Agent preview modal (AgentModal.jsx) ---
    modal_agent_name = LocatorDescriptor(
        testid="catalog-agent-modal-agent-name",
        description="Agent name heading inside the preview modal.",
    )

    modal_show_instructions_link = LocatorDescriptor(
        testid="catalog-agent-modal-show-instructions-link",
        description=(
            "'Show instructions' text link inside the agent preview modal. "
            "Used as the modal's own 'ready' signal (its content, incl. this "
            "link, only renders once the agent-details fetch resolves) — "
            "clicking Start Chat before this is visible hits a known, "
            "already-tracked defect (issue #1043): an uncaught TypeError "
            "that silently no-ops the click."
        ),
    )

    modal_start_chat_button = LocatorDescriptor(
        testid="catalog-agent-modal-start-chat-button",
        description="'Start Chat' button in the agent preview modal (AgentModal.jsx).",
    )

    modal_dialog = LocatorDescriptor(
        testid="catalog-agent-modal",
        description="Preview modal's main panel — the overlay content root (ELITEA-2356).",
    )

    modal_agent_icon = LocatorDescriptor(
        testid="catalog-agent-modal-agent-icon",
        description="Agent icon (EntityIcon) inside the preview modal (ELITEA-2356).",
    )

    modal_owner_name = LocatorDescriptor(
        testid="catalog-agent-modal-owner-name",
        description="Author/owner name Typography inside the preview modal header (ELITEA-2356).",
    )

    modal_menu_button = LocatorDescriptor(
        testid="agent-hub-modal-menu-button",
        description=(
            "Overflow ('...') menu button in the preview modal header (AgentHubModalMenu.jsx) — "
            "contains Export/Fork/Share; 'Share' performs the copy-link action (ELITEA-2356)."
        ),
    )

    modal_share_menu_item = LocatorDescriptor(
        testid="share-agent-menuitem",
        description=(
            "'Share' menu item in the overflow menu (AgentHubModalMenu.jsx) — triggers clipboard write "
            "of the agent catalog link. Testid auto-generated from menu key 'share-agent' (ELITEA-2359)."
        ),
    )

    modal_share_success_toast = LocatorDescriptor(
        testid="toast-alert",
        description=(
            "Success toast notification that appears after 'Share' action copies the link "
            "(Toast.jsx — 'The link has been copied to the clipboard.'). Testid shared with all toasts; "
            "filtered by [data-severity=\"success\"] when needed (ELITEA-2359)."
        ),
    )

    modal_close_button = LocatorDescriptor(
        testid="catalog-agent-modal-close-button",
        description="'x' close IconButton (aria-label='close') in the preview modal header (ELITEA-2356).",
    )

    modal_description = LocatorDescriptor(
        testid="catalog-agent-modal-description",
        description="Agent description Typography inside the preview modal (ELITEA-2356).",
    )

    modal_chat_starters_section = LocatorDescriptor(
        testid="catalog-agent-modal-chat-starters-section",
        description="'CHAT STARTERS' section container inside the preview modal (ELITEA-2356).",
    )

    modal_welcome_message_section = LocatorDescriptor(
        testid="catalog-agent-modal-welcome-message-section",
        description="'Welcome Message' section container inside the preview modal (ELITEA-2356).",
    )

    # Dynamic (state-filtered) like button — the SAME testid as the plain field
    # above, combined with the data-liked state attribute (Like.jsx auto-derives
    # it from testId presence — same precedent as the card-list like button,
    # ELITEA-2354). Templated class-level constant per .agents/testing.md's
    # dynamic-testid convention (no per-modal-instance parameter needed — only
    # one modal renders at a time).
    MODAL_LIKE_BUTTON = '[data-testid="catalog-agent-modal-like-button"]'
    MODAL_LIKE_BUTTON_LIKED_STATE = '[data-testid="catalog-agent-modal-like-button"][data-liked="{}"]'

    # Individual starter item inside the modal's CHAT STARTERS section
    # (AgentConversationStarterItem.jsx, ELITEA-2369) — static testid, one per
    # rendered item; disambiguate a specific starter via .filter(has_text=...)
    # (same idiom as PARTICIPANT_ROW_PREFIX / AGENT_CARD_PREFIX above).
    MODAL_STARTER_ITEM = '[data-testid="catalog-agent-modal-starter-item"]'

    def __init__(self, page: Page):
        super().__init__(page)

    @action("Navigate to Agent Hub (Catalog)")
    def navigate(self):
        """Navigate to the Catalog page and wait for it to be ready."""
        super().navigate("/elitea-catalog")
        self.wait_for_page_load()

    def wait_for_page_load(self, timeout: int = 15000):
        """Wait for the Catalog heading to become visible."""
        self.page_heading.wait_for(state="visible", timeout=timeout)
        logger.info("Agent Hub (Catalog) page loaded")

    def is_category_section_visible(self, category_slug: str, timeout: int = 10000) -> bool:
        """Return True if the category heading for *category_slug* is visible.

        Args:
            category_slug: Lowercased, non-alnum-stripped category name (e.g.
                ``"trending"`` for the "Trending" section).
        """
        heading = self.page.locator(self.CATEGORY_HEADING.format(category_slug))
        try:
            heading.first.wait_for(state="visible", timeout=timeout)
            return True
        except Exception:
            return False

    def get_agent_card(self, agent_name: str):
        """Return the Locator for the agent card matching *agent_name* (by visible text)."""
        return self.page.locator(self.AGENT_CARD_PREFIX).filter(has_text=agent_name)

    def get_agent_card_count(self) -> int:
        """Return the number of agent cards currently rendered in the main content area."""
        return self.page.locator(self.AGENT_CARD_PREFIX).count()

    def is_category_filter_chip_visible(self, category_label: str, timeout: int = 10000) -> bool:
        """Return True if the category filter-rail chip for *category_label* is visible.

        Args:
            category_label: Human display label (e.g. "Knowledge & Documentation",
                "My Liked") — slugified internally the same way EliteaUI does
                client-side (CategoryRail.jsx).
        """
        chip = self.page.locator(self.CATEGORY_FILTER_CHIP.format(_slugify_category(category_label)))
        try:
            chip.first.wait_for(state="visible", timeout=timeout)
            return True
        except Exception:
            return False

    @action("Click category filter-rail chip")
    def click_category_filter_chip(self, category_label: str, timeout: int = 10000):
        """Click the category filter-rail chip for *category_label* (ELITEA-2352).

        Args:
            category_label: Human display label (e.g. "Business Analyst") —
                slugified internally the same way EliteaUI does client-side.
        """
        chip = self.page.locator(self.CATEGORY_FILTER_CHIP.format(_slugify_category(category_label)))
        chip.first.wait_for(state="visible", timeout=timeout)
        chip.first.click()

    def is_category_filter_chip_selected(self, category_label: str, timeout: int = 10000) -> bool:
        """Return True if the category filter-rail chip for *category_label* is
        currently selected (ELITEA-2352).

        Uses the ``data-selected="true"`` state attribute added to the chip in
        ``CategoryRail.jsx`` (``EliteaAI/EliteaUI@9b93f67c``) — NOT Playwright's
        own accessibility-tree ``[active]`` marker, which reflects DOM focus,
        not the app's selection state (confirmed live: focus moves away from a
        still-selected chip the instant another element is clicked, while
        ``data-selected`` correctly persists). See
        ``test-specs/agent-hub/_surface.md`` for the full finding.

        Args:
            category_label: Human display label (e.g. "Business Analyst") —
                slugified internally the same way EliteaUI does client-side.
        """
        selected_chip = self.page.locator(
            self.CATEGORY_FILTER_CHIP.format(_slugify_category(category_label)) + '[data-selected="true"]'
        )
        try:
            selected_chip.first.wait_for(state="visible", timeout=timeout)
            return True
        except Exception:
            return False

    def get_visible_category_heading_texts(self) -> list[str]:
        """Return the text of every currently-rendered content-list category
        heading (ELITEA-2352) — e.g. ``["Business Analyst"]`` after a
        single-category filter click, proving other categories' sections were
        excluded, not merely that the expected one is present.
        """
        headings = self.page.locator(self.CATEGORY_HEADING_PREFIX)
        return [(headings.nth(i).text_content() or "").strip() for i in range(headings.count())]

    @action("Open agent preview modal from Catalog")
    def open_agent_by_name(self, agent_name: str, timeout: int = 15000):
        """Click the agent card matching *agent_name* to open its preview
        modal, and wait for the modal's OWN agent-details fetch to resolve
        (``GET .../public_application/prompt_lib/{id}``) before returning.

        The "Show instructions" link is NOT a valid ready-signal by itself
        — it is unconditionally rendered in ``AgentModal.jsx`` regardless of
        fetch status (confirmed via source), so waiting on its visibility
        alone does not prove the fetch resolved. Waiting on the network
        response itself is the only deterministic signal (AFS § Network
        Behavior): clicking Start Chat before this resolves hits known
        defect #1043 (uncaught TypeError reading ``version_details``,
        silent no-op).
        """
        logger.info("Opening Catalog agent preview modal: %s", agent_name)
        card = self.get_agent_card(agent_name)
        card.first.wait_for(state="visible", timeout=timeout)
        with self.page.expect_response(
            lambda r: "/public_application/prompt_lib/" in r.url and r.request.method == "GET",
            timeout=timeout,
        ):
            card.first.click()
        self.modal_show_instructions_link.wait_for(state="visible", timeout=timeout)

    def get_modal_liked_state(self) -> str:
        """Return the preview modal's like button ``data-liked`` value
        ('true'/'false') (ELITEA-2356) — same ``data-*`` state-attribute
        precedent as :meth:`is_agent_liked` for the card-list like button.
        """
        return self.page.locator(self.MODAL_LIKE_BUTTON).get_attribute("data-liked") or ""

    def get_modal_like_button(self):
        """Return the Locator for the like button (heart icon + count) in the
        agent preview modal (ELITEA-2358).
        """
        return self.page.locator(self.MODAL_LIKE_BUTTON)

    def get_modal_like_count(self, timeout: int = 10000) -> int:
        """Return the like button's numeric count in the preview modal
        (ELITEA-2358) — the count ``Typography`` is the only text node
        inside the button besides the icon ``<svg>``.

        This is a one-shot, non-retrying read (use
        :meth:`wait_for_modal_like_count` for a retrying wait).
        """
        button = self.get_modal_like_button()
        button.wait_for(state="visible", timeout=timeout)
        text = button.text_content() or "0"
        return int(text.strip())

    def wait_for_modal_like_count(self, expected_count: int, timeout: int = 10000) -> None:
        """Wait (Playwright auto-retrying assertion) for the modal like button's
        text to read *expected_count* (ELITEA-2358) — same rationale as
        :meth:`wait_for_like_count` for card-level buttons.
        """
        expect(self.get_modal_like_button()).to_have_text(str(expected_count), timeout=timeout)

    @action("Click like/unlike button in the agent preview modal")
    def click_modal_like_button(self, timeout: int = 10000):
        """Click the like button in the agent preview modal, toggling
        like/unlike, and return the underlying ``/social/like/prompt_lib/...``
        network response (``201`` on like, ``204`` on unlike — AFS § Network
        Behavior, ELITEA-2358).
        """
        button = self.get_modal_like_button()
        button.wait_for(state="visible", timeout=timeout)
        with self.page.expect_response(
            lambda r: "/social/like/prompt_lib/" in r.url and r.request.method in ("POST", "DELETE"),
            timeout=timeout,
        ) as response_info:
            button.click()
        return response_info.value

    def get_modal_starter_items(self):
        """Return the Locator matching ALL rendered starter items inside the
        preview modal's CHAT STARTERS section (ELITEA-2369) — use
        ``.count()`` to verify "multiple options" render.
        """
        return self.page.locator(self.MODAL_STARTER_ITEM)

    def click_agent_card(self, agent_id: int, timeout: int = 15000):
        """Click an agent card by application ID to open its preview modal.

        This method clicks the agent card identified by its application ID
        and waits for the modal's agent-details fetch to complete before returning.

        Args:
            agent_id: Application ID of the agent to open (e.g. 172 for User Story Creator).
            timeout: Maximum wait time for modal to open and fetch to complete (default 15000ms).
        """
        logger.info("Opening Catalog agent preview modal by ID: %s", agent_id)
        card = self.page.locator(f'[data-testid="catalog-agent-card-{agent_id}"]')
        card.wait_for(state="visible", timeout=timeout)
        # Wait for the agent-details fetch to complete before proceeding
        # (defect #1043: clicking before fetch resolves causes silent no-op)
        with self.page.expect_response(
            lambda r: "/public_application/prompt_lib/" in r.url and r.request.method == "GET",
            timeout=timeout,
        ):
            card.click()
        self.modal_show_instructions_link.wait_for(state="visible", timeout=timeout)

    def wait_for_agent_modal_to_load(self, timeout: int = 10000):
        """Wait for the agent preview modal to be fully loaded and ready for interaction.

        This waits for the 'Show instructions' link to become visible, which is
        the signal that the agent-details fetch has resolved (ELITEA-2356).

        Args:
            timeout: Maximum wait time for modal content to load (default 10000ms).
        """
        self.modal_show_instructions_link.wait_for(state="visible", timeout=timeout)

    @action("Click Start Chat in the agent preview modal")
    def click_start_chat(self, timeout: int = 10000):
        """Click the 'Start Chat' button in the (already-ready) agent preview modal.

        Callers MUST have already awaited :meth:`open_agent_by_name`'s own
        wait for ``modal_show_instructions_link`` — clicking before the
        modal's agent-details fetch resolves hits known defect #1043
        (uncaught TypeError, silent no-op, no navigation).
        """
        self.modal_start_chat_button.wait_for(state="visible", timeout=timeout)
        self.modal_start_chat_button.click(force=True)

    @action("Close the agent preview modal with X button")
    def close_modal(self, timeout: int = 10000):
        """Click the close ('x') button in the agent preview modal and wait
        for the modal to transition to hidden state.

        The modal's CSS fade-out transition takes ~300ms (MUI Dialog default);
        this method waits up to *timeout* milliseconds for the modal's
        ``state="hidden"`` condition (ELITEA-2357).

        Args:
            timeout: Maximum wait time for modal to close (default 10000ms).
        """
        self.modal_close_button.wait_for(state="visible", timeout=timeout)
        self.modal_close_button.click()
        self.modal_dialog.wait_for(state="hidden", timeout=timeout)

    # --- Like/unlike (ELITEA-2354) ---

    @action("Navigate to Agent Hub and capture the initial applications snapshot")
    def navigate_and_capture_applications(self, timeout: int = 15000) -> list[dict]:
        """Navigate to the Catalog page (same target as :meth:`navigate`) and
        additionally capture the initial bulk "all applications" response body
        (``GET /public_applications/prompt_lib/...`` — source:
        ``useAgentHubData.hooks.js``'s ``fetchAllAndCategorize``, the
        ``ALL_AGENTS_LIMIT`` bulk fetch, distinct from the separate Trending/
        My-Liked requests fired on the same mount, which are excluded by
        checking for their own distinguishing query params), returning its
        ``rows`` (each a dict with ``id``, ``name``, ``likes``, ...).

        Used for ELITEA-2354's dynamic "find a 0-like agent" discovery —
        reading the network payload directly is more robust than parsing card
        DOM text for the agent name (``AgentCard.jsx``'s name ``Typography``
        carries no testid).
        """

        def _is_all_applications_response(response):
            return (
                "/public_applications/prompt_lib/" in response.url
                and response.request.method == "GET"
                and "trend_start_period" not in response.url
                and "my_liked" not in response.url
            )

        with self.page.expect_response(_is_all_applications_response, timeout=timeout) as response_info:
            super().navigate("/elitea-catalog")
        self.wait_for_page_load(timeout=timeout)
        return response_info.value.json().get("rows", [])

    @staticmethod
    def find_zero_like_application(applications: list[dict]) -> dict | None:
        """Return the first application dict (as returned by
        :meth:`navigate_and_capture_applications`) whose ``likes`` field is 0,
        or ``None`` if none currently qualify.

        ELITEA-2354's dynamic-discovery requirement — like counts are mutable
        shared product data, not a stable per-name fixture (see this case's
        AFS § Test Data: the case text's own example agent does not reliably
        show 0 likes session-to-session).
        """
        for app in applications:
            if app.get("likes", 0) == 0:
                return app
        return None

    @staticmethod
    def find_unliked_application(applications: list[dict]) -> dict | None:
        """Return the first application dict (as returned by
        :meth:`navigate_and_capture_applications`) whose ``is_liked`` field is
        falsy (the CURRENT user has not liked it), or ``None`` if none
        currently qualify (ELITEA-2365).

        Distinct from :meth:`find_zero_like_application` (ELITEA-2354, which
        filters on a TOTAL like count of 0): this case only needs an agent
        the test's own user hasn't liked yet — its total like count from
        other users is irrelevant to the cross-tab-propagation claim under
        test. The bulk applications response includes an ``is_liked``
        boolean per row (source: ``Like.jsx``'s ``const { id, name, likes =
        0, is_liked = false, cardType } = data;`` — the same field the app
        itself reads to render the heart icon's state).
        """
        for app in applications:
            if not app.get("is_liked", False):
                return app
        return None

    @staticmethod
    def find_liked_application(applications: list[dict]) -> dict | None:
        """Return the first application dict (as returned by
        :meth:`navigate_and_capture_applications`) whose ``is_liked`` field is
        truthy (the CURRENT user has already liked it), or ``None`` if none
        currently qualify (ELITEA-2355).

        Inverse of :meth:`find_unliked_application`: used to locate an already-
        liked agent for the unlike test, ensuring the test can always find a
        starting agent regardless of which agent the user has previously liked.
        """
        for app in applications:
            if app.get("is_liked", False):
                return app
        return None

    def get_like_button(self, application_id: int):
        """Return the Locator for the like button (heart icon + count) on the
        agent card matching *application_id* (ELITEA-2354)."""
        return self.page.locator(self.LIKE_BUTTON.format(application_id))

    def get_like_count(self, application_id: int, timeout: int = 10000) -> int:
        """Return the like button's numeric count (ELITEA-2354) — the count
        ``Typography`` is the only text node inside the button besides the
        icon ``<svg>`` (which has no text).

        This is a one-shot, non-retrying read — correct for a pre-action
        baseline check (the value isn't expected to be changing). To assert
        an EXPECTED count after a like/unlike click, use
        :meth:`wait_for_like_count` instead — the count update is optimistic
        client-side and asynchronous relative to the click's own network
        response resolving, so a one-shot read taken immediately after the
        click can race the state update (confirmed live during
        implementation: the cleanup unlike's response returned 204 but a
        same-tick ``get_like_count`` read still showed the pre-unlike value).
        """
        button = self.get_like_button(application_id)
        button.wait_for(state="visible", timeout=timeout)
        text = button.text_content() or "0"
        return int(text.strip())

    def wait_for_like_count(self, application_id: int, expected_count: int, timeout: int = 10000) -> None:
        """Wait (Playwright auto-retrying assertion) for the like button's
        text to read *expected_count* (ELITEA-2354) — see
        :meth:`get_like_count`'s docstring for why a retrying wait is
        required here instead of a one-shot read.
        """
        expect(self.get_like_button(application_id)).to_have_text(str(expected_count), timeout=timeout)

    def is_agent_liked(self, application_id: int, timeout: int = 5000) -> bool:
        """Return True if the like button for *application_id* currently shows
        ``data-liked="true"`` (ELITEA-2354) — same ``data-*`` state-attribute
        precedent as :meth:`is_category_filter_chip_selected`'s
        ``data-selected``.
        """
        liked_locator = self.page.locator(self.LIKE_BUTTON.format(application_id) + '[data-liked="true"]')
        try:
            liked_locator.wait_for(state="visible", timeout=timeout)
            return True
        except Exception:
            return False

    @action("Click like/unlike button on agent card")
    def click_like_button(self, application_id: int, timeout: int = 10000):
        """Click the like button for *application_id*, toggling like/unlike,
        and return the underlying ``/social/like/prompt_lib/...`` network
        response (``201`` on like, ``204`` on unlike — AFS § Network
        Behavior, ELITEA-2354)."""
        button = self.get_like_button(application_id)
        button.wait_for(state="visible", timeout=timeout)
        with self.page.expect_response(
            lambda r: "/social/like/prompt_lib/" in r.url and r.request.method in ("POST", "DELETE"),
            timeout=timeout,
        ) as response_info:
            button.click()
        return response_info.value

    @action("Reload Agent Hub and capture the refreshed My Liked response")
    def reload_and_capture_my_liked(self, timeout: int = 15000) -> dict:
        """Reload the Catalog page and capture the My-Liked-specific bulk
        response (``GET /public_applications/prompt_lib/...my_liked=true...``
        — the same query-param signature :meth:`navigate_and_capture_applications`
        excludes when isolating the "all applications" response) fired on the
        page's initial mount (ELITEA-2365) — proves a full reload actually
        re-fetches cross-tab like state from the backend rather than merely
        re-rendering stale client cache, which is the actual product claim
        under test (Tab A has no live subscription to Tab B's mutation).

        Returns the parsed JSON response body (contains ``rows``).
        """

        def _is_my_liked_response(response):
            return (
                "/public_applications/prompt_lib/" in response.url
                and response.request.method == "GET"
                and "my_liked" in response.url
            )

        with self.page.expect_response(_is_my_liked_response, timeout=timeout) as response_info:
            self.page.reload(wait_until="networkidle", timeout=timeout)
        self.wait_for_page_load(timeout=timeout)
        logger.info("Agent Hub reloaded; My Liked response re-fetched")
        return response_info.value.json()

    @action("Search Catalog by agent name")
    def search(self, query: str, timeout: int = 15000):
        """Type *query* into the Catalog search box and wait for the
        debounced (300ms — source: ``AgentsTab.jsx``'s
        ``useDebounceValue(query, 300)``) search request to resolve
        (ELITEA-2354).

        Uses ``press_sequentially()``, not ``fill()``, to trigger the MUI
        TextField's React ``onChange`` (``.claude/rules/mui-patterns.md``) —
        ``fill()`` sets the DOM value directly and would leave the debounced
        ``query`` React state empty, never firing a search request at all.
        """
        self.search_input.wait_for(state="visible", timeout=timeout)
        with self.page.expect_response(
            lambda r: "/public_applications/prompt_lib/" in r.url and r.request.method == "GET",
            timeout=timeout,
        ):
            self.search_input.click()
            self.search_input.press_sequentially(query, delay=50)
        self.wait_for_network(timeout=timeout)

    @action("Clear Catalog search field")
    def clear_search(self, timeout: int = 15000):
        """Clear the Catalog search field and wait for the debounced
        empty-query BULK request (the one that actually drives the main
        content grid) to resolve (ELITEA-2363).

        Uses select-all + Backspace, NOT `fill("")` — per
        `.claude/rules/mui-patterns.md`, `fill()` sets the DOM value
        directly and would not fire the debounced React `onChange`,
        leaving the `query` state (and therefore the rendered list)
        unchanged. There is no dedicated clear/X button on this field
        (confirmed via source — EliteaCatalog.jsx's TextField has no
        InputProps endAdornment) — this IS the intended interaction.

        Clearing re-fires the SAME 3-request pattern as initial page mount
        (bulk all-applications, Trending, My Liked — AFS § Network
        Behavior) — all three share the ``/public_applications/prompt_lib/``
        substring, so the predicate below excludes the Trending/My-Liked
        query params the same way :meth:`navigate_and_capture_applications`
        does, to deterministically await the BULK response specifically
        (confirmed live during implementation: awaiting "any" matching
        response could resolve on the faster My-Liked/Trending call while
        the bulk request — and therefore the re-rendered content grid — was
        still in flight, a race that left the main card grid still showing
        the pre-clear filtered set for a beat after this method returned).
        """

        def _is_bulk_applications_response(response):
            return (
                "/public_applications/prompt_lib/" in response.url
                and response.request.method == "GET"
                and "trend_start_period" not in response.url
                and "my_liked" not in response.url
            )

        self.search_input.wait_for(state="visible", timeout=timeout)
        with self.page.expect_response(_is_bulk_applications_response, timeout=timeout):
            self.search_input.click()
            self.search_input.press("ControlOrMeta+a")
            self.search_input.press("Backspace")
        self.wait_for_network(timeout=timeout)

    def wait_for_any_agent_card(self, timeout: int = 10000) -> None:
        """Wait (Playwright auto-retrying assertion) for at least one agent
        card to be rendered (ELITEA-2363) — the render-completion signal to
        use after :meth:`navigate_and_capture_applications`'s network-level
        wait, before reading :meth:`get_visible_agent_card_names` for a
        baseline.

        Deliberately NOT a wait for the DOM card count to equal the fetch
        response's raw row count: each category section only displays its
        first ``INITIAL_CARD_DISPLAY_COUNT`` items initially, with the rest
        behind "Show more" (``AgentCategorySection.jsx``) — the bulk
        response can (and normally does) list far more rows than are ever
        rendered in the grid at once, so comparing rendered-card-count to
        response-row-count is comparing the wrong two numbers (confirmed
        live during implementation: a 46-row response against a 23-card
        initial render). React 18 batches the per-category dispatch calls
        issued from the same fetch's `.then()` continuation into a single
        commit, so once ANY card is visible, that commit — and therefore
        every category's initial slice — has already landed.
        """
        self.page.locator(self.AGENT_CARD_PREFIX).first.wait_for(state="visible", timeout=timeout)

    def wait_for_agent_card_count(self, expected_count: int, timeout: int = 10000) -> None:
        """Wait (Playwright auto-retrying assertion) for the number of
        currently-rendered agent cards to equal *expected_count* (ELITEA-2363).

        The Catalog content grid's re-render after a search/clear is
        asynchronous relative to the underlying network response resolving
        (same class of race documented on :meth:`wait_for_like_count`), so a
        one-shot read taken immediately after :meth:`clear_search`/:meth:`search`
        return can observe stale DOM.
        """
        expect(self.page.locator(self.AGENT_CARD_PREFIX)).to_have_count(expected_count, timeout=timeout)

    def wait_for_agent_card_count_not(self, unexpected_count: int, timeout: int = 10000) -> None:
        """Wait (Playwright auto-retrying assertion) for the number of
        currently-rendered agent cards to no longer equal *unexpected_count*
        (ELITEA-2363) — used after :meth:`search` to deterministically await
        the content grid narrowing to a filtered result set, without
        hardcoding the exact filtered count (the Catalog's agent list is
        live, mutable, shared product data — AFS § Test Data).
        """
        expect(self.page.locator(self.AGENT_CARD_PREFIX)).not_to_have_count(unexpected_count, timeout=timeout)

    def get_visible_agent_card_names(self) -> list[str]:
        """Return the text content of every currently-rendered agent card
        (ELITEA-2363), read via ``AGENT_CARD_PREFIX`` (this class's existing
        dynamic-testid prefix, ELITEA-2075/2354 — the same handle
        :meth:`get_agent_card`/:meth:`get_agent_card_count` already use).

        Used to assert the search-filtered set structurally (fewer cards,
        every name contains the query substring) and the clear-restores-all
        invariant (exact set equality against the pre-search baseline)
        without hardcoding a card count — the Catalog's agent list is live,
        mutable, shared product data (AFS § Test Data).

        Note: each card's ``text_content()`` also includes its like-count
        digit (``AgentHubLike``/``Like.jsx``, no separator) since the agent
        name ``Typography`` itself carries no dedicated testid — harmless for
        substring/set-equality comparisons, since no like state changes
        during this case.
        """
        cards = self.page.locator(self.AGENT_CARD_PREFIX)
        return [(cards.nth(i).text_content() or "").strip() for i in range(cards.count())]

    # --- Tab navigation (ELITEA-2370) ---

    def is_agents_tab_selected(self, timeout: int = 10000) -> bool:
        """Return True if the Agents tab is currently selected (aria-selected='true')."""
        agents_tab = self.page.locator('[role="tab"]:has-text("Agents")')
        try:
            agents_tab.first.wait_for(state="visible", timeout=timeout)
            selected = agents_tab.first.get_attribute("aria-selected")
            return selected == "true"
        except Exception:
            return False

    def is_skills_tab_selected(self, timeout: int = 10000) -> bool:
        """Return True if the Skills tab is currently selected (aria-selected='true')."""
        skills_tab = self.page.locator('[role="tab"]:has-text("Skills")')
        try:
            skills_tab.first.wait_for(state="visible", timeout=timeout)
            selected = skills_tab.first.get_attribute("aria-selected")
            return selected == "true"
        except Exception:
            return False

    def is_skills_tab_visible(self, timeout: int = 10000) -> bool:
        """Return True if the Skills tab is visible."""
        skills_tab = self.page.locator('[role="tab"]:has-text("Skills")')
        try:
            skills_tab.first.wait_for(state="visible", timeout=timeout)
            return True
        except Exception:
            return False

    @action("Click the Skills tab")
    def click_skills_tab(self, timeout: int = 10000):
        """Click the Skills tab to switch from Agents to Skills view."""
        skills_tab = self.page.locator('[role="tab"]:has-text("Skills")')
        skills_tab.first.wait_for(state="visible", timeout=timeout)
        skills_tab.first.click()
        # Wait for content to switch
        self.page.wait_for_load_state("networkidle", timeout=timeout)

    def wait_for_filter_panel_visible(self, timeout: int = 10000) -> bool:
        """Wait for the right-side filter panel (category chips) to be visible.

        Returns True if filter panel is visible, used as a verification that
        the Skills tab content has loaded with its filter options.
        """
        # Look for category filter chips or the filter panel container
        filter_chips = self.page.locator(
            '[data-testid^="catalog-agent-category-filter-chip-"], '
            '[data-testid^="catalog-skill-category-filter-chip-"]'
        )
        try:
            filter_chips.first.wait_for(state="visible", timeout=timeout)
            return True
        except Exception:
            return False
