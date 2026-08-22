"""Credentials list page object.

URL: /credentials/all

Covers the Credentials list (Card list view, the default) — card entries
carry the shared ``entity-card`` / ``entity-card-name`` testids (see
``EliteaUI/src/components/Card.jsx``, also used by ``CredentialDetailPage``
for its ``open_credential_by_name`` entry point). Each card's "Pin to
top"/"Unpin from top" icon button is rendered by the shared
``PinButton.jsx`` widget and carries a per-credential testid
(``credential-pin-toggle-button-{id}``) added via ``add-data-testid`` for
ELITEA-1974 (see test-specs/toolkits-credentials/
l1_credential-pin-unpin_ELITEA-1974.md, Concrete Handles).
"""

import logging

from config import settings
from playwright.sync_api import Locator, Page, Response

from .base_page import BasePage
from .credentials_list_recovery import recover_from_credentials_list_crash
from .locator_descriptor import LocatorDescriptor

logger = logging.getLogger("elitea.pages.credentials_list")

UI_ELEMENT_TIMEOUT = 10_000
SEARCH_RESPONSE_TIMEOUT = 15_000


class CredentialsListPage(BasePage):
    """Credentials list page (Card list view).

    URL: /credentials/all
    """

    # Shared Card.jsx component testid (also used by Mcp/Skills/Agents/
    # Pipelines list pages) — collection locator, one per visible card.
    entity_card = LocatorDescriptor(
        testid="entity-card",
        description="Credential card outer container (card view)",
    )

    entity_card_name = LocatorDescriptor(
        testid="entity-card-name",
        description="Credential card name (title) — collection locator, one per visible card",
    )

    # Sidebar "+" create button (shared component, contextual label reads
    # "Credential" while on /credentials/*). Not scoped per-page — same
    # testid AgentsListPage.create_agent_button already uses on /agents/all.
    create_button = LocatorDescriptor(
        testid="sidebar-create-button",
        description="Sidebar '+' create button (opens the credential-type selector)",
    )

    # Shared SearchBar.jsx component testids (also used by every other list
    # page — Skills, Mcp, Agents, Pipelines). Credentials uses the default
    # `testId` prop value for the input; the send/clear icons carry
    # pre-existing, hardcoded, cross-page-generic testids (not scoped per
    # page — see ELITEA-1965 AFS Concrete Handles for provenance).
    search_input = LocatorDescriptor(
        testid="agent-search-input",
        description="Credentials search box (shared SearchBar component, default testId)",
    )
    search_send_button = LocatorDescriptor(
        testid="search-send-button",
        description=(
            "Search submit (send) icon — shared SearchBar, generic testid "
            "(renamed from skills-search-send-button by EliteaUI PR #581 "
            "review fix e0407b70)"
        ),
    )
    search_clear_button = LocatorDescriptor(
        testid="search-clear-button",
        description=(
            "Search clear (X) icon — testid added via add-data-testid for "
            "ELITEA-1965 (EliteaAI/EliteaUI#573); renamed from "
            "agent-search-clear-button by EliteaUI PR #581 review fix e0407b70"
        ),
    )
    search_empty_state = LocatorDescriptor(
        testid="credentials-search-empty-state",
        description=(
            "Zero-results empty-state container ('Nothing found. Create yours "
            "now!') — testid added via add-data-testid for ELITEA-1965 "
            "(EliteaAI/EliteaUI#574)"
        ),
    )

    # Parameterized template — credential id filled in per-call, per the
    # dynamic-testid convention (.claude/rules/page-objects.md).
    PIN_TOGGLE_BUTTON = '[data-testid="credential-pin-toggle-button-{}"]'

    # Scoped sub-selector — a credential card's own type badge, used to
    # search within a single filtered card (get_type_badge()). Same pattern
    # as SkillsListPage.CARD_TAG_CHIP.
    ENTITY_CARD_TAG_CHIP_SELECTOR = '[data-testid="entity-card-tag-chip"]'

    def __init__(self, page: Page):
        super().__init__(page)

    def navigate(self) -> None:
        """Navigate to /credentials/all and wait for at least one card to render.

        Precondition: at least one credential must already exist in the
        project — a zero-credential project redirects to
        ``/credentials/create-credential`` instead (see AFS Preconditions).
        """
        super().navigate("/credentials/all")
        self.wait_for_network()
        recover_from_credentials_list_crash(self.page)
        self.entity_card.first.wait_for(
            state="visible", timeout=UI_ELEMENT_TIMEOUT
        )

    def search(self, term: str, *, assert_unfiltered_while_typing: bool = False) -> Response:
        """Type *term* into the search box and press Enter (explicit-activation
        control — typing alone does NOT filter, per ELITEA-1965's interaction-
        discovery finding: ``SearchBar.jsx``'s ``dispatch(actions.setQuery(...))``
        fires only from ``onSearch()``, wired to ``onKeyDown``/Enter or the send
        icon's ``onClick``).

        Waits for the server-side filtered ``GET .../configurations/configurations/
        {project}?...&query={term}&section=credentials...`` response rather than a
        fixed sleep.

        Args:
            term: The search term to type.
            assert_unfiltered_while_typing: When ``True``, asserts the card
                list is still at its pre-type baseline count right after
                typing *and before Enter is pressed* — proof that typing
                alone does not trigger a filter (a future regression that
                flips this control to live-filter-as-you-type would fail
                here). Opt-in (default ``False``) and intended for a single
                call site right after a freshly-settled, unfiltered list
                (e.g. right after ``navigate()``): callers made right after
                ``clear_search()`` race a known React-re-render lag (see
                ``clear_search()``'s docstring) that this flag does not
                attempt to distinguish from a real defect, so it would be
                unreliable there.

        Returns:
            The matched Playwright ``Response``.
        """
        if assert_unfiltered_while_typing:
            pre_type_card_count = self.entity_card_name.count()
        with self.page.expect_response(
            lambda r: (
                f"/configurations/configurations/{settings.elitea_project_id}" in r.url
                and f"query={term}" in r.url
                and r.request.method == "GET"
            ),
            timeout=SEARCH_RESPONSE_TIMEOUT,
        ) as response_info:
            self.search_input.click()
            self.search_input.press_sequentially(term, delay=20)
            if assert_unfiltered_while_typing:
                # Synchronous `.count()` read (not the auto-retrying
                # `expect()`, which would just wait for eventual settle and
                # prove nothing about this window) — right after typing and
                # BEFORE Enter is pressed.
                post_type_card_count = self.entity_card_name.count()
                assert post_type_card_count == pre_type_card_count, (
                    f"Typing {term!r} must not filter the list before Enter is "
                    f"pressed (explicit-activation control) — expected the "
                    f"pre-type baseline of {pre_type_card_count} card(s), got "
                    f"{post_type_card_count} right after typing"
                )
            self.search_input.press("Enter")
        response = response_info.value
        # The response resolves as soon as headers/body arrive — the React
        # re-render driven by the Redux dispatch is a task tick later. Wait
        # for network to settle so callers reading card state right after
        # search() don't race the render.
        self.wait_for_network()
        return response

    def clear_search(self) -> None:
        """Click the search box's Clear (X) icon and wait for network to settle.

        Per the AFS's Network Behavior section, clearing does not reliably fire
        a fresh GET distinguishable by a ``query=`` predicate in the success
        (non-empty-result) path — ``onClear()`` dispatches ``resetQuery()``,
        which the ``useLoadAllCredentials`` hook reacts to with a re-fetch, so
        a generic network-settle wait is used instead of a response predicate.
        This also correctly covers the zero-results known-defect path (#551),
        where clicking Clear navigates away from ``/credentials/all`` entirely
        rather than triggering an in-place re-fetch — ``wait_for_network()``
        still applies after a client-side route change.
        """
        self.search_clear_button.click()
        self.wait_for_network()

    def pin_toggle_button(self, credential_id) -> Locator:
        """Return the list-row "Pin to top"/"Unpin from top" icon button for *credential_id*."""
        return self.page.locator(self.PIN_TOGGLE_BUTTON.format(credential_id))

    def get_pin_toggle_label(self, credential_id) -> str:
        """Return the button's current accessible label ("Pin to top" / "Unpin from top").

        Read as an attribute off the already-testid-located button — not used
        as a locator strategy (testid-only policy, .agents/testing.md).
        """
        return self.pin_toggle_button(credential_id).get_attribute("aria-label") or ""

    def click_pin_toggle(self, credential_id) -> Response:
        """Click the list-row pin/unpin button and wait for the underlying
        ``POST``/``DELETE .../social/pin/prompt_lib/{project}/configuration/{id}``
        response, per the AFS's wait-on-network-response guidance (no fixed sleep).

        Returns:
            The matched Playwright ``Response``.
        """
        pattern = f"/social/pin/prompt_lib/"
        with self.page.expect_response(
            lambda r: pattern in r.url and r.url.rstrip("/").endswith(f"/configuration/{credential_id}")
        ) as response_info:
            self.pin_toggle_button(credential_id).click()
        return response_info.value

    def get_display_name_order(self) -> list[str]:
        """Return the DOM order of credential display names currently rendered.

        Used to assert *relative* card ordering (pinned credential moves
        above/below another) rather than absolute page position — mirrors
        the AFS's before/after snapshot-diff approach.
        """
        names = self.entity_card_name
        return [names.nth(i).text_content() or "" for i in range(names.count())]

    def click_credential_card(self, display_name: str) -> None:
        """Click the already-rendered credential card matching *display_name*.

        Unlike :meth:`CredentialDetailPage.open_credential_by_name` (which
        re-navigates to ``/credentials/all`` before clicking — the right
        entry point when landing fresh on the detail page), this assumes
        the caller is already on the list page (e.g. right after asserting
        card order) and just performs the click, avoiding a redundant
        navigation round-trip.
        """
        card = self.entity_card.filter(has_text=display_name)
        card.first.wait_for(state="visible", timeout=UI_ELEMENT_TIMEOUT)
        card.first.click()

    def card_by_name(self, display_name: str) -> Locator:
        """Return the credential-card locator filtered to *display_name*.

        Chains ``.filter(has_text=...)`` off the ``entity-card`` testid
        collection (same shape as :meth:`click_credential_card` /
        :meth:`get_type_badge`) so callers can make presence AND absence
        assertions — e.g. ``expect(card_by_name(n)).to_have_count(0)`` after
        a delete (ELITEA-1964).
        """
        return self.entity_card.filter(has_text=display_name)

    def reload_list(self) -> None:
        """Reload ``/credentials/all`` in place and wait for it to settle.

        Used where the case itself asks for a page reload (ELITEA-1964 step 7)
        rather than a fresh navigation. Deliberately does NOT wait for a card
        to appear (unlike :meth:`navigate`): the point of the reload may be to
        assert a card is GONE, and the project may legitimately be left with
        zero credentials. Still runs the shared ``#518`` crash recovery.
        """
        self.page.reload(wait_until="domcontentloaded")
        self.wait_for_network()
        recover_from_credentials_list_crash(self.page)

    def get_type_badge(self, display_name: str) -> str:
        """Return the type-badge text (e.g. "Github") on the card matching *display_name*.

        Scopes to the specific card via the same ``entity_card.filter(has_text=...)``
        pattern as :meth:`click_credential_card`, so two cards with overlapping
        badge text can't cross-contaminate the read.

        Args:
            display_name: The credential's exact Display Name (card title text).

        Returns:
            The badge text content, or ``""`` if the card or badge isn't found.
        """
        card = self.entity_card.filter(has_text=display_name)
        if card.count() == 0:
            return ""
        badge = card.first.locator(self.ENTITY_CARD_TAG_CHIP_SELECTOR)
        if badge.count() == 0:
            return ""
        return badge.first.text_content() or ""
