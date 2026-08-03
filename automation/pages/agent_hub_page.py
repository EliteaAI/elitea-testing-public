"""Agent Hub ("Catalog") page object — ELITEA-2075.

Handles the public Agent Hub / Catalog listing (``/elitea-catalog``): the
page heading + search bar, category sections, agent cards, and the agent
preview modal opened by clicking a card (AgentModal.jsx).

No page object previously existed for this surface (confirmed via a fresh
grep against both ``origin/main`` and ``origin/automation/testids`` — zero
testids anywhere in ``AgentHub.jsx``/``AgentCard.jsx``/``AgentModal.jsx``
before this implementation) — this is genuinely new coverage.

URL: /elitea-catalog
"""

import logging

from playwright.sync_api import Page

from .base_page import BasePage
from .locator_descriptor import LocatorDescriptor
from utils.actions import action

logger = logging.getLogger("elitea.pages.agent_hub")


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

    @action("Click Start Chat in the agent preview modal")
    def click_start_chat(self, timeout: int = 10000):
        """Click the 'Start Chat' button in the (already-ready) agent preview modal.

        Callers MUST have already awaited :meth:`open_agent_by_name`'s own
        wait for ``modal_show_instructions_link`` — clicking before the
        modal's agent-details fetch resolves hits known defect #1043
        (uncaught TypeError, silent no-op, no navigation).
        """
        self.modal_start_chat_button.wait_for(state="visible", timeout=timeout)
        self.modal_start_chat_button.click()
