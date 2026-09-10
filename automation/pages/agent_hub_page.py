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
from contextlib import contextmanager

from playwright.sync_api import Page, expect
from playwright.sync_api import TimeoutError as PlaywrightTimeoutError
from utils.actions import action

from .base_page import BasePage
from .locator_descriptor import LocatorDescriptor

logger = logging.getLogger("elitea.pages.agent_hub")

_CATEGORY_SLUG_RE = re.compile(r"[^a-z0-9]+")

#: Budget (ms) for awaiting one of the Catalog's own bulk
#: ``/public_applications/prompt_lib/...`` responses.
#:
#: **Why it is SEPARATE from the callers' navigation/UI timeout (FIX card
#: #2078):** a response awaited AROUND :meth:`BasePage.navigate` is the OUTER
#: wait — its clock is armed at ``with`` entry and runs for the whole body —
#: yet it used to inherit the callers' 15s ``NAVIGATION_TIMEOUT``, far
#: tighter than what ``navigate()`` itself tolerates. So the response wait
#: could expire while the navigation it wraps was still legitimately in
#: flight.
#:
#: **45_000 is an EMPIRICAL MARGIN, not an invariant — do not cite it as
#: one.** ``navigate()`` has four sequential legs: ``goto()`` at the 30s
#: default (``conftest.py``'s ``set_default_navigation_timeout(30000)``) +
#: ``wait_for_load_state("networkidle", timeout=30000)`` swallowed
#: (``base_page.py``) + the spinner ``wait_for(state="hidden",
#: timeout=10000)`` swallowed + ``dismiss_popups()``. Its legitimate worst
#: case is therefore ~70s, so **no single number clears the enclosing ceiling
#: "by construction"**. 45s is chosen as ~4.5x the measured 9.0-10.6s
#: end-to-end for this fetch, and comfortably above the single
#: ``networkidle`` leg.
#:
#: The awaited bulk fetch is the heaviest request this page makes
#: (``...&limit=1000&offset=0``, ~2.5-3.0s of raw backend time vs ~0.35s for
#: the ``limit=20`` variants) and is gated behind ``agent_categories``
#: resolving first — so its 9.0-10.6s against the old 15s cap was only a
#: ~1.4x margin on a HEALTHY backend, tight enough to expire under load.
#: Endpoint, params, method and payload are unchanged; only our budget was
#: wrong.
CATALOG_RESPONSE_TIMEOUT = 45_000


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

    agents_tab = LocatorDescriptor(
        testid="catalog-agents-tab",
        description="Agents tab in Catalog page header (EliteaCatalog.jsx, ELITEA-2370).",
    )

    skills_tab = LocatorDescriptor(
        testid="catalog-skills-tab",
        description="Skills tab in Catalog page header (EliteaCatalog.jsx, ELITEA-2370).",
    )

    skills_tab_icon = LocatorDescriptor(
        testid="catalog-skills-tab-icon",
        description=(
            "Lightning-bolt icon inside the Skills tab (EliteaCatalog.jsx, ELITEA-2370) — "
            "testid added directly to the SkillsIcon svg (EliteaAI/EliteaUI@da16c70a), same "
            "precedent as version.helpers.jsx's PinIcon."
        ),
    )

    # Category section heading — dynamic per category name (slugified:
    # lowercase, non-alnum runs -> '-'). Templated class-level constant per
    # .agents/testing.md's dynamic-testid convention.
    CATEGORY_HEADING = '[data-testid="catalog-category-heading-{}"]'

    # Category section CONTAINER (ELITEA-2595/2598, EliteaAI/EliteaUI@c80de351
    # -- added to SkillCategorySection.jsx's outer Box). Same slugify
    # convention as CATEGORY_HEADING, but scoped to the whole section
    # (heading + card grid), not just the heading text. Lets a card-existence
    # check be scoped to "descendant of THIS category's section" instead of
    # "anywhere on the page" -- see get_skill_card()'s `category` parameter.
    # Naming deliberately mirrors CATEGORY_HEADING's undifferentiated
    # (agent/skill) convention so a future AgentCategorySection.jsx container
    # testid could reuse this same pattern -- NOT added there yet: no test on
    # this branch exercises an agent-card-under-category check, so adding it
    # now would be an unreferenced testid (.agents/testing.md "referenced =
    # called on the executed path" ruling).
    CATEGORY_SECTION = '[data-testid="catalog-category-section-{}"]'

    # Agent card — dynamic per application id (unknown ahead of time from a
    # display name alone), so a prefix-match + .filter(has_text=...) is used
    # to select by name, same idiom as AgentDetailPage.MODEL_SELECTOR_OPTION_ANY_SELECTOR.
    AGENT_CARD_PREFIX = '[data-testid^="catalog-agent-card-"]'

    #: The two mutually-exclusive TERMINAL renders of the Catalog content grid
    #: (FIX card #2166). ``CatalogBody.jsx`` renders exactly one of three things
    #: in its left column: anonymous loading skeleton ``<Box>``es (NO testid at
    #: all), the category sections (agent cards), or ``NoResultsMessage`` — so a
    #: union of the two testid'd branches is satisfied only once the grid has
    #: COMMITTED for the current query, and can never be satisfied early by the
    #: loading state. Used by :meth:`search` as its post-response render settle.
    #: AGENTS-tab scoped, deliberately: :meth:`search` already awaits the
    #: agents-only ``/public_applications/prompt_lib/`` response, so both this
    #: union and that predicate describe the same tab. A future Skills-tab
    #: search needs its own union over ``SKILL_CARD_PREFIX``.
    SEARCH_RESULTS_SETTLED = (
        '[data-testid^="catalog-agent-card-"], [data-testid="catalog-no-results-title"]'
    )

    # Skill card — the Skills-tab analog of AGENT_CARD_PREFIX above (ELITEA-2370).
    # Dynamic per skill id, same prefix-match idiom. testid added directly to the
    # SkillCard root Card element rendered by the Catalog's Skills tab
    # (`src/[fsd]/features/skill-hub/ui/SkillCard.jsx`, EliteaAI/EliteaUI@c8c621bd) —
    # NOT the identically-named `src/[fsd]/features/skill/ui/SkillCard.jsx` (a
    # different component, used by ApplicationSkills.jsx for an agent's attached
    # skills list, already carries `skill-card-{id}` but is never rendered on this
    # page — verified via import-graph trace during implementation, do not conflate).
    SKILL_CARD_PREFIX = '[data-testid^="catalog-skill-card-"]'

    # Skill card — per-id template (ELITEA-2599 unpublish/republish
    # lifecycle). Same testid family as SKILL_CARD_PREFIX above, but keyed
    # by the exact ``public_skill_id`` captured from a
    # ``publish_skill``/``confirm_publish_and_capture_response()`` response
    # body — the precise, collision-proof handle for "is THIS specific
    # public catalog entry present", vs SKILL_CARD_PREFIX's name-filtered
    # any-match. Required because a skill's ``public_skill_id`` changes
    # across an unpublish/republish boundary (a fresh republish is a new
    # public entry, AFS ELITEA-2599 § Network Behavior) — asserting by name
    # alone can't distinguish "the OLD entry is still there" from "a NEW
    # entry with the same name appeared".
    SKILL_CARD = '[data-testid="catalog-skill-card-{}"]'

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

    # Agent category filter-rail chip prefix (for querying all agent-scoped chips,
    # ELITEA-2370) — used to count and verify filter chips in the Agents view.
    AGENT_CATEGORY_FILTER_CHIP_PREFIX = '[data-testid^="catalog-agent-category-filter-chip-"]'

    # Skill category filter-rail chip prefix (ELITEA-2370) — same idiom as
    # AGENT_CATEGORY_FILTER_CHIP_PREFIX above, threaded from SkillsTab via its own
    # `chipTestIdPrefix="catalog-skill-category-filter-chip"` prop (shared CategoryRail.jsx,
    # feature-scoped per caller — .agents/testing.md's shared-component testid discipline).
    # Its prefix swapping with AGENT_CATEGORY_FILTER_CHIP_PREFIX on tab switch (confirmed
    # live: 11 agent chips -> 0, 0 skill chips -> 11) is this test's primary content-switch
    # signal — a testid-backed replacement for reading the raw <main> element's text
    # content, which the testid-only locator policy forbids (see AFS Declared Improvisation).
    SKILL_CATEGORY_FILTER_CHIP_PREFIX = '[data-testid^="catalog-skill-category-filter-chip-"]'

    # --- Filter-rail composition: FRONTEND CONSTANTS vs BACKEND DATA (ELITEA-2367,
    # FIX card #2079) ---
    #
    # The rail is assembled by ``AgentHubHelpers.buildAllCategories()``
    # (``[fsd]/features/agent-hub/lib/helpers/agentHub.helpers.js``) out of two
    # sources that change for completely different reasons:
    #
    #   * the Featured head and the trailing "Other" are FRONTEND CONSTANTS
    #     (``TRENDING_CATEGORY``/``MY_LIKED_CATEGORY``/``NEW_CATEGORY``/
    #     ``OTHER_CATEGORY`` in ``agentHub.constants.js``; the head is sliced by
    #     ``CatalogBody.jsx``'s ``FEATURED_COUNT``) -- they move only when the UI
    #     team deliberately ships a feature, so pinning them here is correct and a
    #     red is the informative signal;
    #   * the middle categories are BACKEND DATA (``GET
    #     /elitea_core/agent_categories/prompt_lib/{PUBLIC_PROJECT_ID}``) -- an admin
    #     can add/remove/rename one with no code change, so they must NEVER be
    #     pinned. They are read from the page's own response instead
    #     (:meth:`navigate_and_capture_category_names`).
    #
    # This split is why the count is derived and not hardcoded: the previous
    # ``== 11`` pinned both halves with one number and went red on the legitimate
    # third Featured chip "New" (EliteaAI/EliteaUI@18170f71, EL-6238). Bumping it to
    # 12 would have re-armed the same tripwire on the data half.
    FEATURED_CATEGORY_LABELS = ("Trending", "My Liked", "New")

    #: Trailing frontend constant -- ``buildAllCategories()`` strips "Other" from the
    #: sorted middle and re-appends it last, so it is the rail's deterministic END
    #: whether or not the backend happens to return it as a category.
    OTHER_CATEGORY_LABEL = "Other"

    #: URL fragment identifying the Catalog's own category-list request, the oracle
    #: for the rail's data half (``agentCategoriesApi.js``; consumed by
    #: ``useAgentHubData.hooks.js`` as ``categoriesData.categories[].name``).
    AGENT_CATEGORIES_URL_FRAGMENT = "/elitea_core/agent_categories/prompt_lib/"

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

    # Prefix + state-attribute filter, ELITEA-2355 — matches ANY rendered
    # like button currently showing data-liked="true", regardless of which
    # application id it belongs to. Used for dynamic "find a currently-liked
    # agent" discovery (case Step 2) — same templated-constant discipline as
    # LIKE_BUTTON above, just unparameterized for the "find the liked one"
    # direction instead of "read a known id".
    LIKED_LIKE_BUTTON_PREFIX = '[data-testid^="catalog-agent-like-button-"][data-liked="true"]'

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

    # --- Empty state messages (ELITEA-2367) ---
    no_results_title = LocatorDescriptor(
        testid="catalog-no-results-title",
        description="'No agents found' message when search matches zero agents (NoResultsMessage.jsx).",
    )

    no_results_description = LocatorDescriptor(
        testid="catalog-no-results-description",
        description="'Try adjusting your search terms' helper message (NoResultsMessage.jsx, ELITEA-2367).",
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

    @contextmanager
    def _expect_endpoint_response(self, predicate, timeout: int, description: str, *, url_fragment: str):
        """Await a response on ONE endpoint family, re-raising a timeout of that
        WAIT with the responses actually observed on that family (FIX cards
        #2078, #2169).

        Playwright's own ``expect_response`` timeout message names only the
        predicate's source location, so a slow or absent fetch reads as a bare
        "Timeout Nms exceeded" that says nothing about what the app did. This
        repo has two ledger entries (#2074, #2076) where exactly that shape
        named the WRONG subsystem and cost a full session; recording the
        endpoint family's traffic makes the two real cases distinguishable at a
        glance -- ``observed: ['none']`` (the request never fired, or the page
        never got that far) versus ``observed: ['200 ...my_liked=true...']``
        (the sibling calls landed; the awaited one alone was too slow).

        **The recorded family is the CALLER's, not a hardcoded one (#2169).**
        A listener keyed on an endpoint family the caller is not waiting on
        would report ``observed: ['none']`` on every timeout and actively
        mislead -- the exact failure mode this helper exists to prevent. So
        *url_fragment* is required at every call site:
        :meth:`_expect_applications_response` supplies the
        ``/public_applications/`` one, and
        :meth:`navigate_and_capture_category_names` its own
        :data:`AGENT_CATEGORIES_URL_FRAGMENT`.

        Only the WAIT's own timeout is re-raised with this context. An
        exception raised by the wrapped body -- the navigation, the click, the
        typing -- propagates untouched, so this can never re-label a failure
        that did not come from the response wait.

        Args:
            predicate: Response predicate, as passed to ``expect_response``.
            timeout: Response budget in ms -- see :data:`CATALOG_RESPONSE_TIMEOUT`.
            description: Short name of the awaited response, used in the
                re-raised message (e.g. ``"bulk all-applications"``).
            url_fragment: Substring identifying the endpoint family whose
                traffic is recorded for the diagnostic.
        """
        seen: list[str] = []

        def _record(response):
            if url_fragment in response.url:
                seen.append(f"{response.status} {response.url}")

        body_completed = False
        self.page.on("response", _record)
        try:
            with self.page.expect_response(predicate, timeout=timeout) as response_info:
                yield response_info
                body_completed = True
        except PlaywrightTimeoutError as err:
            if not body_completed:
                raise
            raise PlaywrightTimeoutError(
                f"Timed out after {timeout}ms waiting for the Catalog {description} response. "
                f"{url_fragment} responses observed meanwhile: {seen or ['none']}"
            ) from err
        finally:
            self.page.remove_listener("response", _record)

    def _expect_applications_response(self, predicate, timeout: int, description: str):
        """``/public_applications/`` flavour of :meth:`_expect_endpoint_response`.

        Kept as the four Catalog application-fetch call sites' entry point (FIX
        card #2078) so generalising the helper for #2169 left their behaviour and
        their re-raised message byte-identical.
        """
        return self._expect_endpoint_response(
            predicate, timeout, description, url_fragment="/public_applications/"
        )

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

    def get_skill_card(self, skill_name: str, category: str | None = None):
        """Return the Locator for the skill card matching *skill_name* (by
        visible text) — the Skills-tab analog of :meth:`get_agent_card`,
        same ``SKILL_CARD_PREFIX`` dynamic-testid + ``filter(has_text=...)``
        idiom (ELITEA-2595/2598, Catalog verification steps).

        Args:
            category: When given, scopes the search to that category's
                section container (``CATEGORY_SECTION``, same slugify
                convention as ``CATEGORY_HEADING``) — proving the returned
                card is a DESCENDANT of that specific category section, not
                merely present anywhere on the page. A skill published under
                the wrong category is a real regression an unscoped,
                page-wide ``filter(has_text=...)`` cannot catch (reviewer
                finding on PR #1464). Omit only for a genuine page-wide
                existence check.
        """
        if category is not None:
            section = self.page.locator(self.CATEGORY_SECTION.format(_slugify_category(category)))
            return section.locator(self.SKILL_CARD_PREFIX).filter(has_text=skill_name)
        return self.page.locator(self.SKILL_CARD_PREFIX).filter(has_text=skill_name)

    def get_visible_category_filter_chips(self):
        """Return the Locator for all visible agent category filter-rail chips.

        Used to count and verify filter chips in the Agents view (ELITEA-2367).
        Returns a Locator matching ALL agent-scoped filter chips (AGENT_CATEGORY_FILTER_CHIP_PREFIX).
        """
        return self.page.locator(self.AGENT_CATEGORY_FILTER_CHIP_PREFIX)

    def get_visible_skill_category_filter_chips(self):
        """Return the Locator for all visible skill category filter-rail chips (ELITEA-2370).

        Returns a Locator matching ALL skill-scoped filter chips (SKILL_CATEGORY_FILTER_CHIP_PREFIX)
        — the Skills-tab counterpart of :meth:`get_visible_category_filter_chips`.
        """
        return self.page.locator(self.SKILL_CATEGORY_FILTER_CHIP_PREFIX)

    def is_agents_tab_selected(self) -> bool:
        """Return True if the Agents tab currently carries ``aria-selected="true"``
        (ELITEA-2370).

        ``aria-selected`` is MUI ``Tabs``' own native accessibility-state attribute
        (confirmed live: flips true/false between the two tabs on every click) — not
        a custom attribute this suite added — so filtering the stable
        ``catalog-agents-tab`` testid by it is the same "state via attribute, not a
        state-switched testid" pattern as the existing ``data-selected``/``data-liked``
        precedents (:meth:`is_category_filter_chip_selected`, :meth:`is_agent_liked`).
        """
        return self.agents_tab.get_attribute("aria-selected") == "true"

    def is_skills_tab_selected(self) -> bool:
        """Return True if the Skills tab currently carries ``aria-selected="true"``
        (ELITEA-2370). See :meth:`is_agents_tab_selected` for the aria-selected rationale.
        """
        return self.skills_tab.get_attribute("aria-selected") == "true"

    @action("Click the Skills tab in Catalog")
    def click_skills_tab(self, timeout: int = 10000):
        """Click the Skills tab and wait for its own selection state + content
        switch to land (ELITEA-2370) — both the ``aria-selected`` flip and the
        filter-rail prefix swap (agent-scoped chips -> skill-scoped chips) happen
        synchronously with the click (confirmed live, no network round-trip to await),
        so a state-condition wait on ``aria-selected`` is the correct signal.
        """
        self.skills_tab.wait_for(state="visible", timeout=timeout)
        self.skills_tab.click()
        expect(self.skills_tab).to_have_attribute("aria-selected", "true", timeout=timeout)

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

    def get_category_filter_chip(self, category_label: str):
        """Return the Locator for the category filter-rail chip labelled
        *category_label* (ELITEA-2367), addressed by its own testid through
        :data:`CATEGORY_FILTER_CHIP`.

        The unscoped-getter counterpart of :meth:`is_category_filter_chip_visible`
        /:meth:`click_category_filter_chip`, for callers that need to make their own
        web-first assertion against the chip (e.g. ``expect(...).to_be_visible()``)
        rather than a boolean probe.

        Args:
            category_label: Human display label (e.g. "My Liked") -- slugified
                internally the same way EliteaUI does client-side (CategoryRail.jsx).
        """
        return self.page.locator(self.CATEGORY_FILTER_CHIP.format(_slugify_category(category_label)))

    def get_category_filter_chip_labels(self) -> list[str]:
        """Return the visible label of every currently-rendered agent category
        filter-rail chip (ELITEA-2367), in DOM order.

        ``CategoryRail.jsx`` renders each chip as ``<Chip label={category}>``, so the
        chip's own text IS the category display label -- which makes a set comparison
        against the categories the page fetched (see
        :meth:`expected_category_filter_labels`) name the delta in product terms
        ("missing: ['New']") instead of in slugs.
        """
        chips = self.page.locator(self.AGENT_CATEGORY_FILTER_CHIP_PREFIX)
        return [(chips.nth(i).text_content() or "").strip() for i in range(chips.count())]

    @classmethod
    def expected_category_filter_labels(cls, api_category_names) -> set[str]:
        """Return the set of chip labels the filter rail should render, given the
        category names the page's OWN categories response returned (ELITEA-2367).

        Mirrors ``AgentHubHelpers.buildAllCategories()`` exactly: the three
        :data:`FEATURED_CATEGORY_LABELS`, plus the backend's category names, plus the
        trailing :data:`OTHER_CATEGORY_LABEL` -- which the helper re-appends
        unconditionally, so it belongs in the expected set whether or not the backend
        returned it. Order is not modelled (the assertion is a set); see the
        class-level constants block for why the two halves are treated differently.

        Args:
            api_category_names: The ``name`` of each entry in the categories
                response's ``categories`` array.
        """
        return set(cls.FEATURED_CATEGORY_LABELS) | set(api_category_names) | {cls.OTHER_CATEGORY_LABEL}

    @action("Navigate to Agent Hub and capture the agent categories response")
    def navigate_and_capture_category_names(
        self, timeout: int = 15000, *, response_timeout: int = CATALOG_RESPONSE_TIMEOUT
    ) -> list[str]:
        """Navigate to the Catalog page (same target as :meth:`navigate`) and
        additionally capture the ``name`` of every category in the page's own
        ``GET /elitea_core/agent_categories/prompt_lib/{PUBLIC_PROJECT_ID}`` response
        (ELITEA-2367, FIX card #2079).

        This is the ORACLE for the filter rail's data half: RTK-Query caches the
        query per page session, so a fresh navigation fires it exactly once. The
        response is only OBSERVED -- nothing is routed, fulfilled or injected, so
        every asserted value is still produced by the system
        (``.agents/testing.md`` § Fidelity policy, "capture the real response and
        assert the UI against it").

        Two failure modes are named rather than swallowed (FIX card #2169): a fetch
        that never lands times out with the ``agent_categories`` traffic actually
        observed (:meth:`_expect_endpoint_response`), and a fetch that lands
        non-200 -- or without a ``categories`` list -- raises immediately, quoting
        the real status and URL. Redirect hops are NOT terminal responses and are
        excluded from the predicate; see its comment for the live re-auth path that
        makes that load-bearing.

        Args:
            timeout: Budget for :meth:`wait_for_page_load`'s element wait -- the
                UI-readiness half.
            response_timeout: SEPARATE budget for the categories fetch itself, for
                the same reason :meth:`navigate_and_capture_applications` keeps the
                two apart (FIX #2078): this response is awaited AROUND
                ``navigate()``, so its clock covers the whole navigation.

        Raises:
            AssertionError: The categories fetch landed, but not as a 200 carrying a
                ``categories`` list -- see the fast-fail block below.
            PlaywrightTimeoutError: No categories response arrived within
                *response_timeout*, re-raised with the endpoint family's observed
                traffic.
        """

        def _is_categories_response(response):
            # Matches a TERMINAL response for this endpoint -- any status except a
            # redirect hop (FIX card #2169, reviewer round 1).
            #
            # Why no `status == 200` filter: with one, a failed fetch simply never
            # matches, so the wait burns its full 45s budget before reporting anything.
            # What that buys is LATENCY, not naming -- measured on dev.elitea.ai with
            # the fetch forced to 404, 45.05s -> 7.37s. (Naming was already fixed by
            # routing this await through _expect_endpoint_response, whose recorder has
            # no status filter and would list the 404 under "observed meanwhile"; the
            # message below is simply a direct verdict instead of a timeout plus a
            # list.) The live shape this protects against is #2074, a full-page
            # gateway 5xx on DEV.
            #
            # Why 3xx IS excluded: `page.on("response")` and `expect_response` both
            # fire for redirect hops, and a 30x carries the REQUESTED url -- so a
            # redirect on this endpoint would satisfy the fragment+method test and be
            # reported as a backend fault. That is not hypothetical here:
            # EliteaUI/src/api/eliteaApi.js's `fetchBaseQuery.fetchFn` handles
            # `if (response.redirected)` and, on a forward-auth session-expiry
            # redirect, opens an auth popup and RE-FETCHES the original request
            # (`const retryResponse = await fetch(retryRequest || input, init)`). The
            # retried 200 is the real answer; the 302 is transport, not a verdict.
            # Nothing diagnostic is lost -- the recorder logs the 3xx regardless.
            #
            # NOT a shape on this endpoint: #1971 (project-id-less request during a
            # project transition). `useAgentHubData.hooks.js:43` calls
            # `useGetAgentCategoriesQuery({ projectId: PUBLIC_PROJECT_ID })` with a
            # CONSTANT, so that race cannot fire here.
            return (
                self.AGENT_CATEGORIES_URL_FRAGMENT in response.url
                and response.request.method == "GET"
                and not (300 <= response.status < 400)
            )

        with self._expect_endpoint_response(
            _is_categories_response,
            response_timeout,
            "agent-categories",
            url_fragment=self.AGENT_CATEGORIES_URL_FRAGMENT,
        ) as response_info:
            super().navigate("/elitea-catalog")

        # Judged BEFORE wait_for_page_load, so a backend fault surfaces in about its
        # own round-trip instead of behind the UI-readiness wait. Judged EXPLICITLY,
        # because the caller derives the filter rail's expected chip set from this
        # payload: degrading a failed or malformed response into "no categories"
        # would silently shrink that set and re-report a backend fault as a chip-set
        # delta -- a misleading red on the wrong subsystem.
        response = response_info.value
        if not response.ok:
            raise AssertionError(
                f"The Catalog's agent-categories fetch returned HTTP {response.status} "
                f"{response.status_text} for {response.url}. The filter rail's expected chip set "
                "cannot be derived from a failed response -- this is a backend/app fault, NOT a "
                "chip-set drift. Known shape: #2074 (full-page gateway 5xx on DEV). Redirect "
                "hops are excluded by the predicate, so this IS a terminal response."
            )
        try:
            body = response.json()
        except Exception as err:
            # `text()` is itself a body read, so it fails the same way when the body is
            # UNAVAILABLE (aborted request, navigation-cancelled response) rather than
            # merely malformed. Letting it raise from inside this handler would replace
            # the one message whose whole job is naming things with a raw chained
            # traceback, so the preview degrades instead of throwing.
            try:
                preview = repr(response.text()[:200])
            except Exception:  # noqa: BLE001 - diagnostics must not out-fail the diagnosis
                preview = "<body unavailable>"
            raise AssertionError(
                f"The Catalog's agent-categories fetch returned HTTP {response.status} for "
                f"{response.url} but a body that is not JSON: {preview}"
            ) from err
        if not isinstance(body, dict) or not isinstance(body.get("categories"), list):
            got = sorted(body) if isinstance(body, dict) else type(body).__name__
            raise AssertionError(
                f"The Catalog's agent-categories response from {response.url} carries no "
                f"'categories' list (got {got}). Treating that as an empty category set would "
                "silently shrink the filter rail's expected chips, so it is named instead: "
                "either the response contract changed or the backend is faulting."
            )

        self.wait_for_page_load(timeout=timeout)
        return [category["name"] for category in body["categories"]]

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

    @action("Click a conversation starter item in the agent preview modal")
    def click_modal_starter_item(self, match_text: str, timeout: int = 10000):
        """Click the modal starter item whose text CONTAINS *match_text*
        (ELITEA-2093) — resolves via ``MODAL_STARTER_ITEM`` +
        ``.filter(has_text=...)``, same idiom as
        :meth:`ChatPage.click_chat_starter_tile`.

        Unlike :meth:`click_start_chat`, this click does NOT need the known
        defect #1043 timing workaround: ``AgentConversationStarterItem.jsx``
        only renders once ``agentDetails?.version_details?.conversation_starters``
        has committed (confirmed via source — same data dependency as the
        race, but here the race manifests as the item not existing yet rather
        than a click-time exception), so callers that already waited for
        :meth:`get_modal_starter_items` to be visible (this case's own
        "verify starters visible" step) are naturally past the race window
        before this method is ever called.

        ``AgentModal.jsx``'s ``onSelectStarter`` handler both navigates to
        ``/chat`` (via ``onStartConversation``) AND closes the modal
        (``onClose()``) synchronously off this single click — no separate
        "Start Chat" click is involved for this flow.
        """
        item = self.page.locator(self.MODAL_STARTER_ITEM).filter(has_text=match_text)
        item.first.wait_for(state="visible", timeout=timeout)
        item.first.click()

    @action("Click Start Chat in the agent preview modal")
    def click_start_chat(self, timeout: int = 10000):
        """Click the 'Start Chat' button in the (already-ready) agent preview modal.

        Root-caused this dispatch (ELITEA-2360 debug task) via
        ``AgentModal.jsx`` source: the button's ``onClick={onStartConversation()}``
        (line 277) reads ``agentDetails.version_details.*`` from a
        ``useState(null)`` (line 52) populated by an async
        ``getPublicApplicationDetail`` RTK-Query fetch (lines 81-90). Clicking
        while ``agentDetails`` is still ``null`` throws an uncaught TypeError
        *inside* the click handler, BEFORE the ``dispatch(...)``/``navigate(...)``
        calls execute — the click registers, no exception surfaces to
        Playwright, the modal simply stays open forever. Already tracked as
        known defect #1043.

        :meth:`open_agent_by_name`'s own ready-signal (the agent-details GET
        response resolving + ``modal_show_instructions_link`` visible) is
        NOT sufficient — that link renders unconditionally regardless of
        fetch status (confirmed via source), and the HTTP response resolving
        in Playwright does not mean the React/Redux state that reads it has
        committed yet. No DOM signal distinguishes "agentDetails committed"
        from "still null" (both render identical visible content for a
        no-starters agent) — confirmed live via a scripted repro this
        dispatch: **0/3** navigations succeed when Start Chat is clicked
        within ~200ms of the modal opening (deterministic silent no-op,
        modal stays open — reproduced against a fresh no-cookie context
        matching this suite's own ``conftest.py`` fixtures), **3/3** succeed
        at >=300ms. A fixed 1s wait immediately before the click is the
        declared workaround already used successfully in two merged sibling
        tests (ELITEA-2368/2369) — moved in here so every caller gets it
        instead of relying on each test file to remember it (three prior
        unmerged attempts at ELITEA-2360/2361/2362 omitted this wait at the
        call site and hit the race 100% of the time — the systemic cause
        this method now closes). This is test synchronization for an
        unobservable async gap, not defect masking: the underlying product
        gap (no ``disabled={isFetching}`` guard on the button) stays tracked,
        untouched, on #1043.
        """
        self.modal_start_chat_button.wait_for(state="visible", timeout=timeout)
        # Known defect #1043 — see docstring above for the full root-cause
        # analysis and the live-tested 200ms/300ms threshold this wait clears.
        self.page.wait_for_timeout(1000)
        self.modal_start_chat_button.click()

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
    def navigate_and_capture_applications(
        self, timeout: int = 15000, *, response_timeout: int = CATALOG_RESPONSE_TIMEOUT
    ) -> list[dict]:
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

        Args:
            timeout: Budget for :meth:`wait_for_page_load`'s element wait --
                the UI-readiness half.
            response_timeout: SEPARATE budget for the bulk fetch itself. The
                two must not share one number: this response is awaited AROUND
                ``navigate()``, so its clock covers the whole navigation, while
                ``navigate()`` itself tolerates far more than the callers' 15s
                (~70s worst case across its four legs). See
                :data:`CATALOG_RESPONSE_TIMEOUT`, which also states why 45s is
                an empirical margin and NOT a guaranteed ceiling (FIX #2078).
        """

        def _is_all_applications_response(response):
            return (
                "/public_applications/prompt_lib/" in response.url
                and response.request.method == "GET"
                and "trend_start_period" not in response.url
                and "my_liked" not in response.url
            )

        with self._expect_applications_response(
            _is_all_applications_response, response_timeout, "bulk all-applications"
        ) as response_info:
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

    def get_like_button(self, application_id: int, *, first: bool = False):
        """Return the Locator for the like button (heart icon + count) on the
        agent card matching *application_id* (ELITEA-2354).

        Args:
            first: When True, scope to ``.first`` — collapses duplicate
                renders of the SAME agent card across multiple category
                sections (e.g. Trending + a category rail both render the
                identical ``catalog-agent-like-button-{id}`` testid;
                confirmed live, ELITEA-2358's Step 6a). A *dynamically
                discovered* application id (ELITEA-2354's zero/unliked
                lookups, ELITEA-2355's liked lookup) has no guarantee it
                renders in exactly one section, so callers acting on such an
                id should pass ``first=True`` to avoid a Playwright
                strict-mode violation. Default False preserves prior
                behaviour for existing callers that already scope
                separately (e.g. the modal test's own ``.first`` at the
                call site).
        """
        locator = self.page.locator(self.LIKE_BUTTON.format(application_id))
        return locator.first if first else locator

    def find_first_liked_application_id(self, timeout: int = 10000) -> int | None:
        """Return the application id of the first rendered agent card whose
        like button currently shows ``data-liked="true"`` (ELITEA-2355's
        dynamic "locate an already-liked agent" discovery — case Step 2), or
        ``None`` if no card currently renders liked.

        Uses ``.first`` on :attr:`LIKED_LIKE_BUTTON_PREFIX` to collapse
        duplicate renders of the SAME liked agent across multiple category
        sections (see :meth:`get_like_button`'s ``first`` docstring) — this
        method only needs to recover WHICH id is liked, not enumerate every
        rendered instance.
        """
        liked = self.page.locator(self.LIKED_LIKE_BUTTON_PREFIX)
        try:
            liked.first.wait_for(state="visible", timeout=timeout)
        except Exception:
            return None
        testid = liked.first.get_attribute("data-testid") or ""
        suffix = testid.rsplit("-", 1)[-1]
        return int(suffix) if suffix.isdigit() else None

    def get_like_count(self, application_id: int, timeout: int = 10000, *, first: bool = False) -> int:
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
        button = self.get_like_button(application_id, first=first)
        button.wait_for(state="visible", timeout=timeout)
        text = button.text_content() or "0"
        return int(text.strip())

    def wait_for_like_count(
        self, application_id: int, expected_count: int, timeout: int = 10000, *, first: bool = False
    ) -> None:
        """Wait (Playwright auto-retrying assertion) for the like button's
        text to read *expected_count* (ELITEA-2354) — see
        :meth:`get_like_count`'s docstring for why a retrying wait is
        required here instead of a one-shot read. ``first`` — see
        :meth:`get_like_button`.
        """
        expect(self.get_like_button(application_id, first=first)).to_have_text(str(expected_count), timeout=timeout)

    def wait_for_liked_state(
        self, application_id: int, liked: bool, timeout: int = 10000, *, first: bool = False
    ) -> None:
        """Wait (Playwright auto-retrying assertion) for the like button's
        ``data-liked`` attribute to read *liked* (ELITEA-2355) — an
        auto-retrying transition wait, unlike :meth:`is_agent_liked` below.

        The like/unlike DOM update is optimistic-client-side and
        asynchronous RELATIVE TO the click's own network response resolving
        (same class of race as :meth:`get_like_count`'s docstring — confirmed
        live during implementation: immediately after an unlike click's
        response resolves, a one-shot ``[data-liked="true"]`` visibility
        check can still find the STALE ``"true"`` state, because
        ``.wait_for(state="visible")`` only retries for a match to APPEAR —
        it has no way to wait for a match to disappear/flip). Use this
        method (not :meth:`is_agent_liked`) whenever asserting a state
        TRANSITION right after a click; use :meth:`is_agent_liked` for a
        point-in-time / already-settled read (e.g. a baseline before any
        action).
        """
        button = self.get_like_button(application_id, first=first)
        expect(button).to_have_attribute("data-liked", "true" if liked else "false", timeout=timeout)

    def is_agent_liked(self, application_id: int, timeout: int = 5000, *, first: bool = False) -> bool:
        """Return True if the like button for *application_id* currently shows
        ``data-liked="true"`` (ELITEA-2354) — same ``data-*`` state-attribute
        precedent as :meth:`is_category_filter_chip_selected`'s
        ``data-selected``. ``first`` — see :meth:`get_like_button`.

        This is a positive-existence, retry-until-APPEARS check — correct
        for asserting a card IS liked (waits it out if the optimistic update
        hasn't landed yet), but NOT for asserting a card is NOT/no-longer
        liked right after a click (see :meth:`wait_for_liked_state`).
        """
        liked_locator = self.page.locator(self.LIKE_BUTTON.format(application_id) + '[data-liked="true"]')
        if first:
            liked_locator = liked_locator.first
        try:
            liked_locator.wait_for(state="visible", timeout=timeout)
            return True
        except Exception:
            return False

    @action("Click like/unlike button on agent card")
    def click_like_button(self, application_id: int, timeout: int = 10000, *, first: bool = False):
        """Click the like button for *application_id*, toggling like/unlike,
        and return the underlying ``/social/like/prompt_lib/...`` network
        response (``201`` on like, ``204`` on unlike — AFS § Network
        Behavior, ELITEA-2354). ``first`` — see :meth:`get_like_button`."""
        button = self.get_like_button(application_id, first=first)
        button.wait_for(state="visible", timeout=timeout)
        with self.page.expect_response(
            lambda r: "/social/like/prompt_lib/" in r.url and r.request.method in ("POST", "DELETE"),
            timeout=timeout,
        ) as response_info:
            button.click()
        return response_info.value

    @action("Reload Agent Hub and capture the refreshed My Liked response")
    def reload_and_capture_my_liked(
        self, timeout: int = 15000, *, response_timeout: int = CATALOG_RESPONSE_TIMEOUT
    ) -> dict:
        """Reload the Catalog page and capture the My-Liked-specific bulk
        response (``GET /public_applications/prompt_lib/...my_liked=true...``
        — the same query-param signature :meth:`navigate_and_capture_applications`
        excludes when isolating the "all applications" response) fired on the
        page's initial mount (ELITEA-2365) — proves a full reload actually
        re-fetches cross-tab like state from the backend rather than merely
        re-rendering stale client cache, which is the actual product claim
        under test (Tab A has no live subscription to Tab B's mutation).

        Args:
            timeout: Budget for :meth:`wait_for_page_load`'s element wait --
                the UI-readiness half.
            response_timeout: SEPARATE budget for the network half -- BOTH the
                awaited My-Liked response AND the ``reload()`` that triggers
                it, since here the reload IS the enclosing navigation (unlike
                ``BasePage.navigate()`` it does not swallow its own
                ``networkidle`` timeout, so capping it at the callers' 15s
                would simply move the same premature failure one line up).
                Budget rationale, and why 45s is an empirical margin rather
                than a guaranteed ceiling: :data:`CATALOG_RESPONSE_TIMEOUT`
                (FIX card #2078).

        Returns the parsed JSON response body (contains ``rows``).
        """

        def _is_my_liked_response(response):
            return (
                "/public_applications/prompt_lib/" in response.url
                and response.request.method == "GET"
                and "my_liked" in response.url
            )

        with self._expect_applications_response(
            _is_my_liked_response, response_timeout, "My Liked"
        ) as response_info:
            self.page.reload(wait_until="networkidle", timeout=response_timeout)
        self.wait_for_page_load(timeout=timeout)
        logger.info("Agent Hub reloaded; My Liked response re-fetched")
        return response_info.value.json()

    @action("Search Catalog by agent name")
    def search(self, query: str, timeout: int = 15000, *, response_timeout: int = CATALOG_RESPONSE_TIMEOUT):
        """Type *query* into the Catalog search box and wait for the
        debounced (300ms — source: ``AgentsTab.jsx``'s
        ``useDebounceValue(query, 300)``) search request to resolve
        (ELITEA-2354).

        Uses ``press_sequentially()``, not ``fill()``, to trigger the MUI
        TextField's React ``onChange`` (``.claude/rules/mui-patterns.md``) —
        ``fill()`` sets the DOM value directly and would leave the debounced
        ``query`` React state empty, never firing a search request at all.

        THE RESPONSE IS NOT THE RENDER (FIX card #2166). ``useAgentHubData``'s
        ``searchAndCategorize()`` calls ``resetSearchByTag()`` -> ``clearCache()``
        BEFORE ``await fetchApplications(...)`` and dispatches
        ``setApplicationsData`` only in the response's continuation — so
        Playwright's ``expect_response`` above resolves while the grid is
        EMPTY (measured live on ``dev.elitea.ai``, 2026-09-10: **802 ms**
        between the search response landing and the first card becoming
        visible on a cold post-reload search). This method therefore ends on
        an explicit wait for the grid's terminal render
        (:data:`SEARCH_RESULTS_SETTLED`), so a caller may read the grid on the
        very next line.

        That wait REPLACES a trailing ``wait_for_network()``
        (``wait_for_load_state("networkidle")``), which was both fragile and
        useless — the #1847 class. It was the CI failure in
        `UI Tests DEV Stable` run #116 (3/3 attempts, ``Timeout 10000ms
        exceeded``), and measurement showed it settled nothing anyway: 0.00 s
        on DEV, where socket.io upgrades to a real WebSocket. Per #1847 the
        fix is to wait on what the caller actually needs, never to raise a
        timeout.

        Args:
            timeout: Budget for the search field's own element wait and the
                post-response render settle — the UI half, driven by the
                caller's ``UI_ELEMENT_TIMEOUT``.
            response_timeout: SEPARATE budget for the debounced search
                response, so a UI-element budget never caps a backend fetch
                (FIX card #2078). This method wraps NO navigation, so the
                enclosing-ceiling argument in
                :data:`CATALOG_RESPONSE_TIMEOUT` does not apply here — only
                its budget-decoupling half does. Trade-off, stated plainly: a
                search request that genuinely never fires now costs 45s before
                failing instead of 10s.
        """
        self.search_input.wait_for(state="visible", timeout=timeout)
        with self._expect_applications_response(
            lambda r: "/public_applications/prompt_lib/" in r.url and r.request.method == "GET",
            response_timeout,
            "debounced search",
        ):
            self.search_input.click()
            self.search_input.press_sequentially(query, delay=50)
        self.page.locator(self.SEARCH_RESULTS_SETTLED).first.wait_for(state="visible", timeout=timeout)

    @action("Clear Catalog search field")
    def clear_search(self, timeout: int = 15000, *, response_timeout: int = CATALOG_RESPONSE_TIMEOUT):
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

        CONTRACT — THIS METHOD ENDS ON THE RESPONSE, NOT ON A RENDER
        (FIX card #2168). It returns once the bulk empty-query response has
        resolved; the content grid re-renders **~376 ms later** (measured
        live on ``dev.elitea.ai``, 2026-09-10: 27-card baseline -> 6-card
        filtered -> 375.84 ms from the clear response landing to the grid
        being back at 27). **Callers MUST therefore read the restored grid
        through an auto-retrying assertion** — :meth:`wait_for_agent_card_count`
        with the pre-search baseline count — never a one-shot read on the
        next line.

        No trailing settle is attempted here, deliberately, because no
        TERMINAL signal for "the clear landed" is expressible without the
        caller's baseline count:

        * This method used to end on ``wait_for_network()``
          (``wait_for_load_state("networkidle")``) — the #1847 class. Its
          byte-identical twin in :meth:`search` took a sibling spec RED 3/3
          in ``UI Tests DEV Stable`` run #116 (``Timeout 10000ms exceeded``).
          Per #1847 the fix is to wait on what the caller actually needs,
          never to raise a timeout.
        * :data:`SEARCH_RESULTS_SETTLED` — :meth:`search`'s render settle —
          must NOT be copied here: it is **VACUOUS after a clear**. Its
          ``catalog-agent-card-*`` branch is already matched by the
          *pre-clear filtered* cards, so it has nothing to wait for.
          Measured on the same run: satisfied **4.72 ms** after the response,
          with the grid mid-restore at 12 of 27 cards — a wait that measures
          ~zero while the state the caller reads is genuinely not there yet
          (``.agents/testing.md``, #2166: "a settle can be fragile AND
          vacuous at the same time").
        * A count-CHANGE wait (``not_to_have_count(pre_clear_count)``) is
          equally non-terminal: the grid's category sections commit
          progressively, so the count leaves the filtered value (6) within a
          few ms while still short of the restored value (27).

        The caller's ``to_have_count(baseline)`` is the only terminal
        signal — and it is non-vacuous by construction, because the case
        asserts ``filtered < baseline`` before clearing.

        Args:
            timeout: Budget for the search field's own element wait — the UI
                half, driven by the caller's ``UI_ELEMENT_TIMEOUT``. No
                trailing settle consumes it (see CONTRACT above).
            response_timeout: SEPARATE budget for the re-fired BULK response
                — clearing re-fires the SAME heavy ``limit=1000`` fetch the
                initial mount does, so a UI-element budget must never cap it
                (FIX card #2078). This method wraps NO navigation, so the
                enclosing-ceiling argument in
                :data:`CATALOG_RESPONSE_TIMEOUT` does not apply here — only
                its budget-decoupling half does. Trade-off, stated plainly: a
                bulk request that genuinely never fires now costs 45s before
                failing instead of 10s.
        """

        def _is_bulk_applications_response(response):
            return (
                "/public_applications/prompt_lib/" in response.url
                and response.request.method == "GET"
                and "trend_start_period" not in response.url
                and "my_liked" not in response.url
            )

        self.search_input.wait_for(state="visible", timeout=timeout)
        with self._expect_applications_response(
            _is_bulk_applications_response, response_timeout, "bulk all-applications (search cleared)"
        ):
            self.search_input.click()
            self.search_input.press("ControlOrMeta+a")
            self.search_input.press("Backspace")

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

    def wait_for_any_skill_card(self, timeout: int = 10000) -> None:
        """Wait (Playwright auto-retrying assertion) for at least one skill
        card to be rendered (ELITEA-2370) — the Skills-tab content-visibility
        signal, same idiom as :meth:`wait_for_any_agent_card` above. Used to
        prove the main content area actually switched to Skills content after
        clicking the Skills tab, rather than inferring it from the (differently
        state-driven) filter-rail chip swap alone.
        """
        self.page.locator(self.SKILL_CARD_PREFIX).first.wait_for(state="visible", timeout=timeout)

    def get_skill_card_by_id(self, public_skill_id):
        """Return the Locator for the Catalog skill card matching *public_skill_id*
        exactly (ELITEA-2599) — see :attr:`SKILL_CARD` for why this is
        id-keyed rather than name-filtered.

        Args:
            public_skill_id: The skill's public catalog id (int or str), as
                returned by the ``publish_skill`` response body's
                ``public_skill_id`` field.
        """
        return self.page.locator(self.SKILL_CARD.format(public_skill_id))

    def is_skill_card_visible(self, public_skill_id, timeout: int = 10000) -> bool:
        """Return True if a Catalog skill card for *public_skill_id* is visible
        within *timeout* (ELITEA-2599).

        Args:
            public_skill_id: The skill's public catalog id.
            timeout: Maximum wait time in milliseconds.
        """
        try:
            self.get_skill_card_by_id(public_skill_id).first.wait_for(
                state="visible", timeout=timeout
            )
            return True
        except Exception:
            return False

    def wait_for_skill_card_absent(self, public_skill_id, timeout: int = 10000) -> None:
        """Wait (Playwright auto-retrying assertion) for the Catalog skill
        card matching *public_skill_id* to be gone (ELITEA-2599) — the
        unpublish removal signal, mirrors :meth:`wait_for_any_skill_card`'s
        presence-wait idiom in reverse.

        Args:
            public_skill_id: The skill's public catalog id.
            timeout: Maximum wait time in milliseconds.
        """
        expect(self.get_skill_card_by_id(public_skill_id)).to_have_count(0, timeout=timeout)

    def get_skill_card_count_by_name(self, skill_name: str) -> int:
        """Return the number of Catalog skill cards whose visible text matches
        *skill_name* (ELITEA-2599) — used to assert "exactly one card, never
        duplicates" across a version-coexistence sequence, independent of
        which ``public_skill_id`` is currently active.

        Args:
            skill_name: Exact skill name to match (rendered card text).
        """
        return self.page.locator(self.SKILL_CARD_PREFIX).filter(has_text=skill_name).count()

    def wait_for_category_heading(self, category_label: str, timeout: int = 10000) -> None:
        """Wait (Playwright auto-retrying assertion) for a SPECIFIC category's
        heading to render on the Skills tab (ELITEA-2595/2598) — use this
        BEFORE reading :meth:`get_visible_category_heading_texts` when
        asserting a particular category's presence, rather than relying on
        :meth:`wait_for_any_skill_card` alone.

        Unlike :meth:`wait_for_any_agent_card`'s "single commit" assumption
        (one bulk fetch, so any rendered card proves every category's initial
        slice already landed), the Skills tab's data flow
        (``useSkillHubData.hooks.js``) fires THREE independent fetches on
        mount — ``fetchAllAndCategorize`` (the ``ALL_SKILLS_LIMIT=1000``
        bulk fetch that buckets skills into non-Trending category sections
        like this one), ``fetchTrendingSkills`` (its own, much smaller
        page-sized request), and ``fetchMyLikedSkills``. These resolve
        independently, so the Trending section's card can (and, confirmed
        live, sometimes does) render and satisfy
        :meth:`wait_for_any_skill_card` well before the bulk-categorize
        fetch — and therefore this category's own section — has landed.
        Reading :meth:`get_visible_category_heading_texts` immediately after
        only "any card" is visible is a race that intermittently under-reads
        the heading list (observed: ``['Trending']`` with the target
        category's section not yet mounted). Waiting on the target heading
        directly closes that race with a framework-native wait, not a sleep.

        Args:
            category_label: Human display label (e.g. "Quality Assurance") —
                slugified internally the same way EliteaUI does client-side.
        """
        heading = self.page.locator(self.CATEGORY_HEADING.format(_slugify_category(category_label)))
        heading.first.wait_for(state="visible", timeout=timeout)

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
