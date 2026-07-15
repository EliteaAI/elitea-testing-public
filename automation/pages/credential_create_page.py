"""Credential create page object.

URL: /credentials/create-credential/{type} (entry via /credentials/all →
credential-type-selector card).

Covers the Create-Credential form's client-side Save-button gating on
required fields (``ToolBase.jsx``'s ``validateRequiredFields()`` helper +
``CredentialsTabBar.jsx``'s Save-disable logic). Testids for this flow were
already live at exploration time (landed via ELITEA-1971) — no
``add-data-testid`` round-trip was needed for ELITEA-1975.

Note (known defect — github.com/EliteaAI/elitea-testing-public#526):
clearing the Display Name field does not re-disable Save, unlike every
other required field. See
test-specs/toolkits-credentials/l1_create-credential-required-fields-validation_ELITEA-1975.md
for the full root-cause writeup.
"""

import logging

from playwright.sync_api import Page

from .base_page import BasePage
from .credential_form_fields import CredentialFormFieldsMixin
from .credentials_list_recovery import recover_from_credentials_list_crash
from .locator_descriptor import LocatorDescriptor

logger = logging.getLogger("elitea.pages.credential_create")

UI_ELEMENT_TIMEOUT = 10_000


class CredentialCreatePage(CredentialFormFieldsMixin, BasePage):
    """Credential create page (client-side required-field validation).

    URL: /credentials/create-credential/{type}

    Inherits the Display Name field + Save button (``set_display_name()``,
    ``is_save_enabled()``) from :class:`CredentialFormFieldsMixin`, shared
    with :class:`CredentialDetailPage`.
    """

    # ------------------------------------------------------------------
    # Credential-type selector (entry point, /credentials/all)
    # ------------------------------------------------------------------
    # Dynamic testid — class-level template constant per
    # .agents/testing.md § Locator policy (dynamic testid pattern).
    TYPE_CARD_SELECTOR = '[data-testid="toolkit-type-card-{}"]'

    # ------------------------------------------------------------------
    # Create-form fields
    # ------------------------------------------------------------------
    base_url_input = LocatorDescriptor(
        testid="toolkit-field-base_url-input",
        description="Base Url required field (Jira credential type)",
    )
    api_key_input = LocatorDescriptor(
        testid="toolkit-field-api_key-input-field",
        description="Api Key required field (Jira credential type, secret-toggle wrapper)",
    )
    username_input = LocatorDescriptor(
        testid="toolkit-field-username-input",
        description="Username required field (Jira credential type)",
    )

    def __init__(self, page: Page):
        super().__init__(page)

    def navigate_to_type(self, credential_type: str) -> None:
        """Navigate to /credentials/all and open the create form for *credential_type*.

        Args:
            credential_type: The credential type slug (e.g. ``"jira"``),
                matching the ``toolkit-type-card-{type}`` testid convention.
        """
        self.navigate("/credentials/all")
        self.wait_for_network()
        recover_from_credentials_list_crash(self.page)
        type_card = self.page.locator(self.TYPE_CARD_SELECTOR.format(credential_type))
        type_card.first.wait_for(state="visible", timeout=UI_ELEMENT_TIMEOUT)
        type_card.first.click()
        self.wait_for_page_load()

    def wait_for_page_load(self, timeout: int = UI_ELEMENT_TIMEOUT) -> None:
        """Wait for the create-credential form to render its Display Name field."""
        self.wait_for_network(timeout=timeout)
        self.display_name_input.wait_for(state="visible", timeout=timeout)

    def clear_display_name(self) -> None:
        """Clear the Display Name field via select-all + Backspace, triggering onChange."""
        self.display_name_input.click()
        self.display_name_input.select_text()
        self.display_name_input.press("Backspace")

    def set_base_url(self, value: str) -> None:
        """Fill the Base Url required field, triggering React onChange."""
        self.base_url_input.click()
        self.base_url_input.press_sequentially(value, delay=20)

    def clear_base_url(self) -> None:
        """Clear the Base Url required field via select-all + Backspace, triggering onChange."""
        self.base_url_input.click()
        self.base_url_input.select_text()
        self.base_url_input.press("Backspace")

    def set_api_key(self, value: str) -> None:
        """Fill the Api Key required field, triggering React onChange."""
        self.api_key_input.click()
        self.api_key_input.press_sequentially(value, delay=20)

    def set_username(self, value: str) -> None:
        """Fill the Username required field, triggering React onChange."""
        self.username_input.click()
        self.username_input.press_sequentially(value, delay=20)

    def clear_username(self) -> None:
        """Clear the Username required field via select-all + Backspace, triggering onChange."""
        self.username_input.click()
        self.username_input.select_text()
        self.username_input.press("Backspace")
