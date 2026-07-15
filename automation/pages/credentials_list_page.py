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

from playwright.sync_api import Locator, Page, Response

from .base_page import BasePage
from .credentials_list_recovery import recover_from_credentials_list_crash

logger = logging.getLogger("elitea.pages.credentials_list")

UI_ELEMENT_TIMEOUT = 10_000


class CredentialsListPage(BasePage):
    """Credentials list page (Card list view).

    URL: /credentials/all
    """

    ENTITY_CARD_SELECTOR = '[data-testid="entity-card"]'
    ENTITY_CARD_NAME_SELECTOR = '[data-testid="entity-card-name"]'
    # Parameterized template — credential id filled in per-call, per the
    # dynamic-testid convention (.claude/rules/page-objects.md).
    PIN_TOGGLE_BUTTON = '[data-testid="credential-pin-toggle-button-{}"]'

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
        self.page.locator(self.ENTITY_CARD_SELECTOR).first.wait_for(
            state="visible", timeout=UI_ELEMENT_TIMEOUT
        )

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
        names = self.page.locator(self.ENTITY_CARD_NAME_SELECTOR)
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
        card = self.page.locator(self.ENTITY_CARD_SELECTOR).filter(has_text=display_name)
        card.first.wait_for(state="visible", timeout=UI_ELEMENT_TIMEOUT)
        card.first.click()
