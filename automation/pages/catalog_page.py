"""Agent HUB (public agent catalog) page object.

Provides locators and methods for browsing the Agent HUB catalog, opening an
agent's detail modal, and starting a new conversation from it via "Start Chat".

URL: /elitea-catalog

New page object added for ELITEA-2092 — no prior page object covered the
Agent HUB entry point or its detail modal (see AFS
test-specs/hubs/l2_agent-hub-start-conversation-no-starters_ELITEA-2092.md
§ Automation Hints).
"""

import logging

from playwright.sync_api import Page
from utils.actions import action

from .base_page import BasePage
from .locator_descriptor import LocatorDescriptor

logger = logging.getLogger("elitea.pages.catalog")


class CatalogPage(BasePage):
    """Page object for the Agent HUB catalog (/elitea-catalog).

    Handles:
    - Sidebar navigation into the catalog ("Catalog" nav entry)
    - Browsing agent cards
    - Opening an agent's detail modal (conversation starters, "Start Chat")

    URL: /elitea-catalog
    """

    # ------------------------------------------------------------------
    # Sidebar entry point
    # ------------------------------------------------------------------

    sidebar_agent_hub_button = LocatorDescriptor(
        testid="sidebar-agent-hub-button",
        description=(
            "Sidebar 'Catalog' (Agent HUB) navigation entry, bottom of the "
            "sidebar above Support Bot."
        ),
    )

    # ------------------------------------------------------------------
    # Agent cards (dynamic per agent id)
    # ------------------------------------------------------------------

    # Dynamic per-agent card testid — same class-constant template mechanism
    # as ChatPage.CONVERSATION_ITEM (.agents/testing.md § Locator policy,
    # Dynamic testids). A given agent id can render TWICE in the DOM
    # (its own category bucket + the "Other"/"Trending" bucket) — confirmed
    # live; callers resolve via .first.
    CATALOG_AGENT_CARD = '[data-testid="catalog-agent-card-{}"]'

    # Prefix-match selector enumerating every agent card regardless of id —
    # same pattern as ChatPage.CONVERSATION_ITEM_PREFIX. Used by
    # find_agent_card_by_name() to resolve a card by its visible name
    # without the caller having to hardcode a numeric agent id.
    CATALOG_AGENT_CARD_PREFIX = '[data-testid^="catalog-agent-card-"]'

    # ------------------------------------------------------------------
    # Agent detail modal
    # ------------------------------------------------------------------

    agent_detail_modal = LocatorDescriptor(
        testid="catalog-agent-detail-modal",
        description="Agent detail modal (role=dialog) opened from an agent card.",
    )

    modal_starters_header = LocatorDescriptor(
        testid="catalog-agent-modal-starters-header",
        description=(
            "Conversation-starters section header inside the agent detail "
            "modal. Live copy is 'CHAT STARTERS' (case text says "
            "'CONVERSATION STARTERS' — clarification #1042, case-text drift)."
        ),
    )

    modal_starters_empty = LocatorDescriptor(
        testid="catalog-agent-modal-starters-empty",
        description=(
            "Empty-state message shown inside the conversation-starters "
            "section when the agent has no predefined starters."
        ),
    )

    modal_start_chat_button = LocatorDescriptor(
        testid="catalog-agent-modal-start-chat-button",
        description=(
            "'Start Chat' button inside the agent detail modal (case text "
            "says 'Start conversation' — same clarification #1042)."
        ),
    )

    def __init__(self, page: Page):
        super().__init__(page)

    @action("Navigate to Agent HUB via sidebar")
    def navigate_to_agent_hub(self, timeout: int = 15000):
        """Click the sidebar 'Catalog' entry and wait for the HUB to load.

        Assumes the caller already has an authenticated page open (e.g. the
        default /chat landing page) — the Agent HUB nav entry lives in the
        shared app sidebar, it has no standalone route to `navigate()`
        straight to on a fresh session.

        Args:
            timeout: Maximum wait time in milliseconds.
        """
        self.sidebar_agent_hub_button.click()
        self.page.wait_for_url(lambda url: "/elitea-catalog" in url, timeout=timeout)
        self.wait_for_network(timeout=timeout)
        logger.info("Navigated to Agent HUB (%s)", self.page.url)

    def get_agent_card(self, agent_id: str | int):
        """Return the Locator for a specific agent card by its numeric id.

        The same id can render twice (own category bucket + "Other"/
        "Trending" bucket) — callers resolve via ``.first``.

        Args:
            agent_id: Numeric application/agent id.
        """
        return self.page.locator(self.CATALOG_AGENT_CARD.format(agent_id))

    def find_agent_card_by_name(self, agent_name: str, timeout: int = 10000):
        """Return the Locator for an agent card matching *agent_name*.

        Filters the testid-prefixed card selector by visible text —
        avoids hardcoding a numeric agent id (an environment detail) in
        callers; the case's actual test data is the agent's NAME. The
        same agent id can render twice (its own category bucket +
        "Other"/"Trending"), so this may resolve >1 element — callers pick
        via ``.first``.

        Args:
            agent_name: Visible agent name (e.g. "Business Analyst").
            timeout: Maximum wait time in milliseconds for at least one
                card to render before filtering.
        """
        cards = self.page.locator(self.CATALOG_AGENT_CARD_PREFIX)
        cards.first.wait_for(state="visible", timeout=timeout)
        return cards.filter(has_text=agent_name)

    @staticmethod
    def get_agent_id_from_card(card) -> str:
        """Extract the numeric agent id from a resolved card Locator's own
        ``data-testid`` attribute (``catalog-agent-card-{id}``).

        Needed by ``open_agent_detail_modal()``, which keys off the id.

        Args:
            card: A single resolved card Locator (e.g. from
                ``find_agent_card_by_name(...).first``).
        """
        testid = card.get_attribute("data-testid") or ""
        return testid.removeprefix("catalog-agent-card-")

    @action("Open agent detail modal")
    def open_agent_detail_modal(self, agent_id: str | int, timeout: int = 10000):
        """Click an agent card and wait for its detail modal + agent-details
        fetch to settle before returning.

        Known defect (`#1043` — AFS § Known Defects): clicking "Start Chat"
        before the modal's own agent-details GET resolves throws an
        uncaught TypeError (``Cannot read properties of null (reading
        'version_details')``) and silently no-ops (no navigation, no
        visible error). Waiting for the response here narrows that race
        (confirmed live) but does not fully close it — see
        ``click_start_chat()``'s docstring for why no DOM-observable signal
        can close it deterministically, and the bounded-retry mitigation
        that handles what's left.

        Endpoint note: the AFS's own § Network Behavior names
        ``public_applications/prompt_lib/{agent_id}`` (plural), but the
        live request is ``GET /api/v2/elitea_core/public_application/
        prompt_lib/{agent_id}`` — SINGULAR ``public_application`` (confirmed
        live during implementation via a captured ``page.on("request", ...)``
        listener; matches this project's singular-for-get-one API
        convention, `.claude/rules/api-patterns.md`). The match below checks
        for ``public_application`` + ``/prompt_lib/`` separately so it holds
        regardless of which spelling a future endpoint change uses.

        Args:
            agent_id: Numeric application/agent id.
            timeout: Maximum wait time in milliseconds.
        """
        card = self.get_agent_card(agent_id).first
        card.wait_for(state="visible", timeout=timeout)
        with self.page.expect_response(
            lambda response: "public_application" in response.url and "/prompt_lib/" in response.url,
            timeout=timeout,
        ):
            card.click()
        self.agent_detail_modal.wait_for(state="visible", timeout=timeout)
        # Extra settle margin: the response event above fires once headers
        # arrive, before the app's own promise continuation
        # (setAgentDetails) has necessarily committed a re-render — confirmed
        # live that this narrows, but does not eliminate, the race
        # click_start_chat() still guards against.
        self.wait_for_network(timeout=timeout)
        logger.info("Opened agent detail modal for agent id=%s", agent_id)

    @action("Start chat from agent detail modal")
    def click_start_chat(self, timeout: int = 15000, max_attempts: int = 3):
        """Click "Start Chat" in the agent detail modal; wait for the modal
        to close and the chat composer to open.

        Must be called after ``open_agent_detail_modal()`` (which already
        narrows the `#1043` race) — never immediately after a bare card
        click.

        **Declared improvisation (canon gap — `.agents/role-overrides.md`
        § Declared-improvisation protocol):** `#1043` is a genuine,
        non-deterministic timing race in `AgentModal.jsx`'s `onStartConversation`
        callback — it reads `agentDetails.version_details` (no optional
        chaining) from React state that a `useEffect`-triggered async fetch
        populates, with NO loading/disabled guard on the button and NO
        DOM-observable signal that distinguishes "still loading" from
        "genuinely has no data" (confirmed live: the empty conversation-
        starters state renders identically in both cases —
        ``agentDetails?.version_details?.conversation_starters || []`` in
        the component source). Confirmed empirically during this
        implementation that the race is real timing, not a deterministic
        bug: a bare network-response wait plus a `networkidle` settle
        margin (``open_agent_detail_modal``) still let it fire on some
        runs, while an immediate SECOND click (after the race fired on the
        first) succeeded outright — proving the underlying state does
        resolve, just not deterministically fast enough for the button's
        current click, and proving no fixed delay is a safe substitute for
        an actual outcome check. With no reliable condition to await, this
        retries the ACTION itself, gated on the real desired OUTCOME (the
        modal closing) — not a guessed sleep — up to *max_attempts* times,
        stopping the moment the previous attempt's click already succeeded.
        This is a test-infrastructure workaround for an already-filed,
        non-blocking race (per the AFS: "Automation must add the explicit
        wait ... so the test itself doesn't inherit the race") — it does
        not weaken any assertion about product behavior.

        Args:
            timeout: Total wait budget in milliseconds, split evenly across
                attempts.
            max_attempts: Maximum number of times to click "Start Chat"
                before giving up.
        """
        per_attempt_timeout = max(2000, timeout // max_attempts)
        for attempt in range(1, max_attempts + 1):
            if not self.agent_detail_modal.is_visible():
                # A previous attempt's click already closed the modal.
                break
            self.modal_start_chat_button.click()
            try:
                self.agent_detail_modal.wait_for(state="hidden", timeout=per_attempt_timeout)
                break
            except Exception:
                if attempt == max_attempts:
                    raise
                logger.warning(
                    "click_start_chat attempt %d/%d: modal still open after "
                    "%dms (known defect #1043 race) — retrying",
                    attempt, max_attempts, per_attempt_timeout,
                )
        self.page.wait_for_url(lambda url: "/chat" in url, timeout=timeout)
        logger.info("Started chat from agent detail modal (%s)", self.page.url)
