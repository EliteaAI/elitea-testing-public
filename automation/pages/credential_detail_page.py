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

ID-autogeneration/URL-stability handles (``get_credential_id_from_url()``,
``is_id_field_disabled()``) were added for ELITEA-1972 (see test-specs/
toolkits-credentials/l1_credential-id-auto-generation_ELITEA-1972.md).

Three-dot menu / pin-toggle handles (``controls_menu_button``,
``pin_toggle_menuitem``, ``open_controls_menu()``,
``get_pin_toggle_menu_label()``, ``click_pin_toggle_menu_item()``) were
added for ELITEA-1974 (see test-specs/toolkits-credentials/
l1_credential-pin-unpin_ELITEA-1974.md). The ``pin-toggle-credential-menuitem``
testid required a one-line fix in ``CredentialsControls.jsx`` (the
``pinMenuItem`` spread never set a ``key``, unlike its sibling ``Delete``
item) — added via ``add-data-testid``.

Delete handles (``delete_menuitem`` + the shared ``DeleteEntityModal``
dialog handles, ``delete_credential_via_menu()``) were added for ELITEA-1964
(see test-specs/toolkits-credentials/l1_delete-credential_ELITEA-1964.md).
Every one of those testids already existed on ``main`` — the menu item's
``delete-credentials-menuitem`` is auto-derived by ``DotMenu.jsx`` from the
``key: 'delete-credentials'`` set in ``CredentialsControls.jsx``, and the
dialog testids come from the shared ``DeleteEntityModal.jsx`` — so no
``add-data-testid`` round-trip was needed.
"""

import logging
import re

from config import settings
from playwright.sync_api import Page

from .base_page import BasePage
from .credential_form_fields import CredentialFormFieldsMixin
from .credentials_list_recovery import recover_from_credentials_list_crash
from .locator_descriptor import LocatorDescriptor

logger = logging.getLogger("elitea.pages.credential_detail")

UI_ELEMENT_TIMEOUT = 10_000
DELETE_RESPONSE_TIMEOUT = 15_000


class CredentialDetailPage(CredentialFormFieldsMixin, BasePage):
    """Credential detail/edit page.

    URL: /credentials/all/{numeric_id}

    Inherits the Display Name field + Save button (``set_display_name()``,
    ``is_save_enabled()``) from :class:`CredentialFormFieldsMixin`, shared
    with :class:`CredentialCreatePage`.
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
    # id_input is inherited from CredentialFormFieldsMixin (ELITEA-1962) —
    # same testid, promoted so CredentialCreatePage can share it too.

    # ------------------------------------------------------------------
    # Tab-bar controls
    # ------------------------------------------------------------------
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

    # ------------------------------------------------------------------
    # Three-dot menu (ControlsDropdown / DotMenu, id="controls" default)
    # ------------------------------------------------------------------
    controls_menu_button = LocatorDescriptor(
        testid="controls-menu-button",
        description="Three-dot menu button in the tab bar (pre-existing testid)",
    )
    pin_toggle_menuitem = LocatorDescriptor(
        testid="pin-toggle-credential-menuitem",
        description="Pin/Unpin toggle menu item inside the three-dot menu",
    )
    delete_menuitem = LocatorDescriptor(
        testid="delete-credentials-menuitem",
        description=(
            "Delete menu item inside the three-dot menu — testid auto-derived "
            "by DotMenu.jsx from the item key 'delete-credentials' "
            "(CredentialsControls.jsx). Pre-existing on main (ELITEA-1964)."
        ),
    )

    # ------------------------------------------------------------------
    # Delete-confirmation dialog (shared DeleteEntityModal.jsx, ELITEA-1964)
    # ------------------------------------------------------------------
    # Repo precedent: each page object that triggers this shared modal
    # declares its own LocatorDescriptors for it (personal_tokens_page.py,
    # mcp_form_page.py, artifacts_page.py) — no new testid work here.
    delete_confirm_dialog = LocatorDescriptor(
        testid="delete-confirm-dialog",
        description="Delete-confirmation modal container (shared DeleteEntityModal)",
    )
    delete_confirm_title = LocatorDescriptor(
        testid="delete-confirm-title",
        description="Delete-confirmation modal title ('Delete confirmation')",
    )
    delete_confirm_message = LocatorDescriptor(
        testid="delete-confirm-message",
        description=(
            "Delete-confirmation modal body text ('Are you sure to delete the "
            "<name>? Enter the name to complete the action.')"
        ),
    )
    delete_confirm_entity_name = LocatorDescriptor(
        testid="delete-confirm-entity-name",
        description="The credential name rendered inside the confirmation message",
    )
    delete_confirm_name_input = LocatorDescriptor(
        testid="delete-confirm-name-input",
        description=(
            "Type-to-confirm Name field — resolves to the MUI TextField "
            "WRAPPER, not the real <input> (same shape as "
            "personal_tokens_page.py / mcp_form_page.py); click + "
            "press_sequentially() types into the focused inner input."
        ),
    )
    delete_confirm_button = LocatorDescriptor(
        testid="delete-confirm-button",
        description=(
            "Delete (confirm) button inside the confirmation modal — disabled "
            "until the typed name matches the credential name exactly "
            "(shouldRequestInputName: true in CredentialsControls.jsx)"
        ),
    )
    delete_confirm_cancel_button = LocatorDescriptor(
        testid="delete-confirm-cancel-button",
        description="Cancel button inside the delete-confirmation modal",
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

        Delegates to the shared :func:`recover_from_credentials_list_crash`
        helper (github.com/EliteaAI/elitea-testing-public#518) — see that
        module for the full root-cause writeup. Extracted out of this page
        object so :class:`CredentialCreatePage` (which also lands on
        ``/credentials/all``) doesn't need a duplicate method
        (``.claude/rules/page-objects.md`` "NO Method Duplication").

        Returns:
            True if the crash was detected and recovered from.
        """
        return recover_from_credentials_list_crash(self.page)

    def wait_for_page_load(self, timeout: int = UI_ELEMENT_TIMEOUT) -> None:
        """Wait for the credential detail page to render its Display Name field."""
        self.wait_for_network(timeout=timeout)
        self.display_name_input.wait_for(state="visible", timeout=timeout)

    def get_display_name(self) -> str:
        """Return the current Display Name field value."""
        return self.display_name_input.input_value()

    def get_credential_id_from_url(self) -> str:
        """Extract the numeric credential id from the current detail-page URL.

        URL shape: ``/credentials/all/{numeric_id}?viewMode=owner&name=...``.
        """
        match = re.search(r"/credentials/all/(\d+)", self.page.url)
        assert match, f"Expected a numeric credential id in the URL, got: {self.page.url}"
        return match.group(1)

    def is_id_field_disabled(self) -> bool:
        """Return True if the ID (elitea_title) field is disabled (read-only)."""
        return not self.id_input.is_enabled()

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

    def open_controls_menu(self) -> None:
        """Click the three-dot menu button and wait for the pin-toggle item to render."""
        self.controls_menu_button.click()
        self.pin_toggle_menuitem.wait_for(state="visible", timeout=UI_ELEMENT_TIMEOUT)

    def get_pin_toggle_menu_label(self) -> str:
        """Return the pin-toggle menu item's current text ("Pin to top" / "Unpin from top")."""
        return self.pin_toggle_menuitem.text_content() or ""

    def click_pin_toggle_menu_item(self):
        """Click the pin-toggle menu item and wait for the underlying
        ``POST``/``DELETE .../social/pin/prompt_lib/{project}/configuration/{id}``
        response, per the AFS's wait-on-network-response guidance (no fixed sleep).

        Returns:
            The matched Playwright ``Response``.
        """
        credential_id = self.get_credential_id_from_url()
        pattern = "/social/pin/prompt_lib/"
        with self.page.expect_response(
            lambda r: pattern in r.url and r.url.rstrip("/").endswith(f"/configuration/{credential_id}")
        ) as response_info:
            self.pin_toggle_menuitem.click()
        return response_info.value

    def open_delete_dialog(self) -> None:
        """Click the three-dot menu's "Delete" item and wait for the shared
        delete-confirmation dialog to render (ELITEA-1964, case step 4).

        Precondition: the three-dot menu is already open
        (:meth:`open_controls_menu`).
        """
        self.delete_menuitem.click()
        self.delete_confirm_dialog.wait_for(state="visible", timeout=UI_ELEMENT_TIMEOUT)

    def fill_delete_confirm_name(self, name: str) -> None:
        """Type *name* into the delete dialog's type-to-confirm Name field.

        Same click + ``press_sequentially`` shape as
        ``personal_tokens_page.py`` / ``mcp_form_page.py`` — MUI needs real
        keyboard events for React onChange (``.claude/rules/mui-patterns.md``),
        and the testid resolves to the TextField wrapper rather than the inner
        input (the click focuses that input, the keystrokes land in it).
        """
        self.delete_confirm_name_input.click()
        self.delete_confirm_name_input.press_sequentially(name, delay=20)

    def confirm_delete(self, credential_id: str):
        """Click the dialog's Delete button and wait for the underlying
        ``DELETE .../configurations/configuration/{project}/{credential_id}``
        response (no fixed sleep).

        Note the SINGULAR ``configuration`` path segment — the plural
        ``configurations`` endpoint is the list/create one.

        Args:
            credential_id: The credential's numeric id (see
                :meth:`get_credential_id_from_url`), used to pin the awaited
                response to this exact credential.

        Returns:
            The matched Playwright ``Response``.
        """
        with self.page.expect_response(
            lambda r: (
                r.request.method == "DELETE"
                and r.url.rstrip("/").endswith(f"/configurations/configuration/{self._project_id}/{credential_id}")
            ),
            timeout=DELETE_RESPONSE_TIMEOUT,
        ) as response_info:
            self.delete_confirm_button.click()
        return response_info.value

    @property
    def _project_id(self) -> int:
        """The project id the suite is configured against (``config.settings``)."""
        return settings.elitea_project_id
