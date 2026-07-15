"""Credential detail page object.

URL: /credentials/all/{numeric_id}

Covers the Credential-detail Save/Discard/discard-confirm flow
(``CredentialsTabBar.jsx`` + ``DiscardButton.jsx`` + ``BaseModal.jsx`` in
EliteaUI). Testids for this flow were added via ``add-data-testid`` for
ELITEA-1971 (see test-specs/toolkits-credentials/
l1_credential-discard-changes_ELITEA-1971.md, Concrete Handles).

Note: the tab-bar Discard button and the confirmation modal's Discard
button share the same accessible name ("Discard") but are two distinct
DOM elements — they now carry distinct testids
(``credential-form-discard-button`` vs ``credential-discard-confirm-button``)
so no dialog-scoping workaround is needed.
"""

import logging

from playwright.sync_api import Page

from .base_page import BasePage
from .locator_descriptor import LocatorDescriptor

logger = logging.getLogger("elitea.pages.credential_detail")

UI_ELEMENT_TIMEOUT = 10_000


class CredentialDetailPage(BasePage):
    """Credential detail/edit page.

    URL: /credentials/all/{numeric_id}
    """

    # ------------------------------------------------------------------
    # Credentials list (entry point)
    # ------------------------------------------------------------------
    # `entity-card` / `entity-card-name` are the shared list-card testids
    # (EliteaUI src/components/Card.jsx) reused across every card-rendered
    # list page (Applications, Pipelines, Toolkits, Credentials, ...).
    # Scoped sub-selector per .agents/testing.md's class-level-constant rule.
    ENTITY_CARD_SELECTOR = '[data-testid="entity-card"]'

    # ------------------------------------------------------------------
    # Credential detail form fields
    # ------------------------------------------------------------------
    display_name_input = LocatorDescriptor(
        testid="toolkit-field-label-input",
        description="Credential Display Name input (shared ToolBaseProperty renderer)",
    )
    id_input = LocatorDescriptor(
        testid="toolkit-field-elitea_title-input",
        description="Credential ID (elitea_title) input — disabled, mirrors Display Name",
    )

    # ------------------------------------------------------------------
    # Tab-bar controls
    # ------------------------------------------------------------------
    save_button = LocatorDescriptor(
        testid="credential-form-save-button",
        description="Save credential button (tab-bar)",
    )
    discard_button = LocatorDescriptor(
        testid="credential-form-discard-button",
        description="Discard button (tab-bar) — opens the confirm modal",
    )

    # ------------------------------------------------------------------
    # Discard confirmation modal
    # ------------------------------------------------------------------
    discard_confirm_modal = LocatorDescriptor(
        testid="credential-discard-confirm-modal",
        description="Discard confirmation modal (BaseModal)",
    )
    discard_confirm_button = LocatorDescriptor(
        testid="credential-discard-confirm-button",
        description="Discard button inside the confirmation modal",
    )

    def __init__(self, page: Page):
        super().__init__(page)

    def open_credential_by_name(self, display_name: str) -> None:
        """Navigate to /credentials/all and open the credential card matching *display_name*.

        Args:
            display_name: The credential's Display Name (card title text).
        """
        self.navigate("/credentials/all")
        self.wait_for_network()
        self._recover_from_credentials_list_crash()
        card = self.page.locator(self.ENTITY_CARD_SELECTOR).filter(has_text=display_name)
        card.first.wait_for(state="visible", timeout=UI_ELEMENT_TIMEOUT)
        card.first.click()
        self.wait_for_page_load()

    def _recover_from_credentials_list_crash(self) -> bool:
        """Reload once if /credentials/all crashed with the known refetch race.

        Known defect (github.com/EliteaAI/elitea-testing-public#518):
        ``CredentialsList.jsx``'s mount effect calls ``onRefetch()`` twice
        unconditionally on this exact pathname, and
        ``useLoadCredentials.js``'s underlying RTK Query ``refetch()`` throws
        "Cannot refetch a query that has not been started yet" when the
        query hasn't started — an unhandled error that trips the route's
        error boundary. Live-verified during ELITEA-1971 exploration at a
        ~60% reproduction rate; out of scope for the Discard flow this page
        object exists to test, so a single reload recovers (the race window
        doesn't reliably re-trigger on the second mount) rather than letting
        every Discard-flow run flake on an unrelated, already-filed bug.

        This is a recovery-only check (not a test locator/assertion) — text
        match against the app's generic React-Router error boundary output,
        the same "workaround, not policy exception" pattern as
        ``BasePage.dismiss_banner_if_present()``.

        Returns:
            True if the crash was detected and recovered from.
        """
        crashed = self.page.get_by_text("Unexpected Application Error!").count() > 0
        if crashed:
            logger.warning(
                "Recovering from known CredentialsList crash (elitea-testing-public#518) — reloading"
            )
            self.page.reload(wait_until="domcontentloaded")
            self.wait_for_network()
        return crashed

    def wait_for_page_load(self, timeout: int = UI_ELEMENT_TIMEOUT) -> None:
        """Wait for the credential detail page to render its Display Name field."""
        self.wait_for_network(timeout=timeout)
        self.display_name_input.wait_for(state="visible", timeout=timeout)

    def set_display_name(self, value: str) -> None:
        """Replace the Display Name field's value, triggering React onChange.

        MUI fields don't fire React's onChange on Playwright's ``fill()`` —
        use ``select_text()`` + ``type()`` instead
        (.claude/rules/mui-patterns.md). NOTE: ``press("Control+a")`` does
        NOT select-all on this field — live-verified during Phase 2
        exploration: it moves the caret to position 0 without selecting,
        so subsequent typing prepends instead of replacing. ``select_text()``
        sets the DOM selection directly and is unaffected by whatever
        intercepts the Ctrl+A keydown.
        """
        self.display_name_input.click()
        self.display_name_input.select_text()
        self.display_name_input.type(value)

    def get_display_name(self) -> str:
        """Return the current Display Name field value."""
        return self.display_name_input.input_value()

    def is_save_enabled(self) -> bool:
        return self.save_button.is_enabled()

    def is_discard_enabled(self) -> bool:
        return self.discard_button.is_enabled()

    def click_discard(self) -> None:
        """Click the tab-bar Discard button, opening the confirmation modal."""
        self.discard_button.click()
        self.discard_confirm_modal.wait_for(state="visible", timeout=UI_ELEMENT_TIMEOUT)

    def get_discard_confirm_message(self) -> str:
        """Return the confirmation modal's full text content (heading + body)."""
        return self.discard_confirm_modal.text_content() or ""

    def confirm_discard(self) -> None:
        """Click Discard inside the confirmation modal and wait for it to close."""
        self.discard_confirm_button.click()
        self.discard_confirm_modal.wait_for(state="detached", timeout=UI_ELEMENT_TIMEOUT)
