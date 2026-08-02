"""Credential create page object.

URL: /credentials/create-credential/{type} — navigated to directly (see
``navigate_to_type()`` docstring for why this changed from the earlier
click-a-card-on-/credentials/all flow, ELITEA-1963).

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

from playwright.sync_api import Locator, Page

from .base_page import BasePage
from .credential_form_fields import CredentialFormFieldsMixin
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

    # Auth-method radiogroup (ELITEA-1962) — dynamic testid template,
    # `toolkit-field-auth-radio-{slug}` where slug is the option's underlying
    # VALUE (lowercased, spaces->hyphens), not its label text. E.g. label
    # "Anonymous" -> slug "none", label "Token" -> slug "token". See the AFS
    # Concrete Handles table for the full label-to-slug mapping.
    AUTH_METHOD_RADIO = '[data-testid="toolkit-field-auth-radio-{}"]'

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
    access_token_input = LocatorDescriptor(
        testid="toolkit-field-access_token-input-field",
        description=(
            "Access Token required field (GitHub credential type, Token auth "
            "method, secret-toggle wrapper — same rendered field family as "
            "api_key_input, relabeled for GitHub's Token auth)."
        ),
    )
    api_error_message = LocatorDescriptor(
        testid="credential-form-api-error-message",
        description=(
            "Server-side API error text rendered below the form on a failed "
            "Save (CredentialForm.jsx) — e.g. the duplicate-elitea_title "
            "400 message. Testid added for ELITEA-1978."
        ),
    )

    def __init__(self, page: Page):
        super().__init__(page)

    def navigate_to_type(self, credential_type: str) -> None:
        """Navigate directly to the create form for *credential_type*.

        Args:
            credential_type: The credential type slug (e.g. ``"jira"``),
                matching the ``/credentials/create-credential/{type}`` route
                and the ``toolkit-type-card-{type}`` testid convention.

        Note (infra fix, ELITEA-1963): previously this navigated to
        ``/credentials/all`` and clicked the ``toolkit-type-card-{type}``
        card there. ``CredentialsList.jsx`` only renders that type-selector
        grid on ``/credentials/all`` when the project has **zero**
        credentials (see its "Navigate to New Credential page for private
        projects with no credentials" auto-redirect effect) — once any
        credential exists (the normal state of a shared DEV project), the
        card never renders and the old flow times out waiting for it. The
        create-form URL (``/credentials/create-credential/{type}``) is a
        stable, directly-routable target per ``EliteaUI/src/routes.js``
        (``CreateCredentialTypeFromMain``), so navigating there directly
        avoids the now-broken card-click intermediary entirely. Verified
        against the live app that this lands on the same create form the
        card click used to reach (same testids: ``toolkit-field-label-input``,
        ``credential-form-save-button``, etc.).
        """
        self.navigate(f"/credentials/create-credential/{credential_type}")
        self.wait_for_page_load()

    def type_card(self, credential_type: str) -> Locator:
        """Return the credential-type selector card locator for *credential_type*.

        Only rendered on the "Choose the credentials type" grid — reached via
        the sidebar "+" button (see :meth:`click_type_card`), as opposed to
        :meth:`navigate_to_type`'s direct-URL shortcut which skips this grid
        entirely.
        """
        return self.page.locator(self.TYPE_CARD_SELECTOR.format(credential_type))

    def click_type_card(self, credential_type: str) -> None:
        """Click the credential-type selector card for *credential_type* and
        wait for the resulting type-specific create form to render (ELITEA-1962).
        """
        self.type_card(credential_type).click()
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

    def auth_radio(self, method_slug: str) -> Locator:
        """Return the Auth radio-button locator for *method_slug* (e.g. ``"token"``).

        The testid lands on the MUI ``FormControlLabel`` wrapping the native
        ``<input type="radio">`` (not the input itself) — live-verified that
        Playwright's ``is_checked()`` still resolves correctly through this
        wrapper, so no extra unwrap is needed by callers.
        """
        return self.page.locator(self.AUTH_METHOD_RADIO.format(method_slug))

    def select_auth_method(self, method_slug: str) -> None:
        """Click the Auth radio button matching *method_slug* (e.g. ``"token"``).

        Args:
            method_slug: The auth option's underlying value slug, not its
                label text (see :data:`AUTH_METHOD_RADIO` docstring note).
        """
        self.auth_radio(method_slug).click()

    def set_access_token(self, value: str) -> None:
        """Fill the Access Token field, triggering React onChange.

        Only rendered once the "Token" auth method is selected — call
        :meth:`select_auth_method` first.
        """
        self.access_token_input.click()
        self.access_token_input.press_sequentially(value, delay=20)
