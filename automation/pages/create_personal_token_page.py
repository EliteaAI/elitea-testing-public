"""Create Personal Token page object (Settings → Personal Tokens → "+").

URL: /settings/create-personal-token

Covers the "New Token" create-flow page (``CreatePersonalToken.jsx``) and the
``GeneratedTokenDialog`` it opens on a successful Generate — a full-page form
plus its own success dialog, tightly coupled as one user flow, so both live
in a single page object per the AFS's Automation Hints.

Reached from :class:`pages.personal_tokens_page.PersonalTokensPage` via
``click_add_button()`` (a route navigation, NOT an inline dialog — confirmed
live, ELITEA-2280 AFS Case-Text Note).

Locator provenance (ELITEA-2280, all new — zero pre-existing testids in this
component tree):
``create-personal-token-page-title`` reuses the same ``DrawerPageHeader`` +
``titleTestId`` mechanism as ``PersonalTokensPage.page_title`` (already
threaded, ELITEA-2277). ``create-personal-token-name-input`` /
``create-personal-token-expiration-value-input`` are ``data-testid`` set via
``Input.InputBase``'s existing ``inputProps`` object (native ``<input>``
attribute — same mechanism ``SimpleSearchBar`` already used).
``create-personal-token-expiration-measure-select`` is a ``data-testid`` prop
``SingleSelect`` already accepts; the shared component auto-derives a
``-combobox`` suffix for the actual clickable/visible-text element (same
established pattern as ``ArtifactsPage.bucket_retention_measure_combobox``).
``create-personal-token-generate-button`` is a static ``data-testid`` directly
on ``Button.BaseBtn`` (forwards unknown/`data-*` props). The
``generated-token-dialog-*`` testids are static ``data-testid``s directly on
``GeneratedTokenDialog.jsx``'s JSX (a feature-owned file, not a shared
component) — title, warning, token-name, token-value Typography elements, the
Copy button, and the close (X) icon (``Box``-wrapped ``CancelIcon`` with no
accessible role/name — a testid is the only stable handle available here).
"""

import logging

from playwright.sync_api import Page, expect

from .base_page import BasePage
from .locator_descriptor import LocatorDescriptor

logger = logging.getLogger("elitea.pages.create_personal_token")

UI_ELEMENT_TIMEOUT = 10_000
NAVIGATION_TIMEOUT = 15_000

# Substring identifying the token-create POST (`useTokenCreateMutation`) —
# used to wait for the real create response before asserting the dialog.
TOKEN_CREATE_URL_SUBSTRING = "/auth/token/"


class CreatePersonalTokenPage(BasePage):
    """Settings → Personal Tokens → "New Token" create-flow page + its
    GeneratedTokenDialog success dialog."""

    page_title = LocatorDescriptor(
        testid="create-personal-token-page-title",
        description='Page header title — exact text "New Token"',
    )
    name_input = LocatorDescriptor(
        testid="create-personal-token-name-input",
        description="Token name input — resolves to the native <input> "
        "(inputProps-wired testid), required + [a-zA-Z0-9_-] pattern.",
    )
    expiration_measure_combobox = LocatorDescriptor(
        testid="create-personal-token-expiration-measure-select-combobox",
        description="Expiration-period unit select's clickable combobox — "
        "the shared SingleSelect component auto-derives this '-combobox' "
        "suffix from the root 'create-personal-token-expiration-measure-select' "
        "testid; defaults to 'Days'.",
    )
    expiration_value_input = LocatorDescriptor(
        testid="create-personal-token-expiration-value-input",
        description="Expiration-period numeric value input — native <input>, "
        "defaults to '30'.",
    )
    generate_button = LocatorDescriptor(
        testid="create-personal-token-generate-button",
        description="Generate button — disabled until name is non-empty and valid.",
    )
    name_error = LocatorDescriptor(
        testid="create-personal-token-name-error",
        description="Name field's validation-error helper text — visible only "
        "while the entered name fails TOKEN_NAME_PATTERN "
        "(/^[a-zA-Z0-9_-]*$/); absent (count 0) once the name is valid.",
    )
    dialog_title = LocatorDescriptor(
        testid="generated-token-dialog-title",
        description='GeneratedTokenDialog title — exact text "New token generated!"',
    )
    dialog_warning = LocatorDescriptor(
        testid="generated-token-dialog-warning",
        description="GeneratedTokenDialog warning text (attention-styled).",
    )
    dialog_token_name = LocatorDescriptor(
        testid="generated-token-dialog-token-name",
        description="GeneratedTokenDialog's display of the entered token name.",
    )
    dialog_token_value = LocatorDescriptor(
        testid="generated-token-dialog-token-value",
        description="GeneratedTokenDialog's display of the full generated token string.",
    )
    dialog_copy_button = LocatorDescriptor(
        testid="generated-token-dialog-copy-button",
        description='Copy button — text flips to "Copied!" and disables ~5s after click.',
    )
    dialog_close_button = LocatorDescriptor(
        testid="generated-token-dialog-close-button",
        description="Dialog close (X) icon — Box-wrapped CancelIcon, no accessible "
        "role/name; closing navigates back to /settings/tokens.",
    )
    # App-wide generic toast (reused — see PersonalTokensPage's sibling pages'
    # `toast_message` / `success_toast_message` fields; already exists, zero
    # new testid work).
    toast_message = LocatorDescriptor(
        testid="toast-message",
        description="Generic app-wide toast — shows the Copy confirmation text.",
    )

    def __init__(self, page: Page):
        super().__init__(page)

    def wait_for_loaded(self, timeout: int = UI_ELEMENT_TIMEOUT) -> None:
        """Wait for the "New Token" form to be visible (name input present)."""
        self.name_input.wait_for(state="visible", timeout=timeout)

    def fill_name(self, name: str) -> None:
        """Type *name* into the Name field.

        Formik/MUI input — click + press_sequentially triggers React
        onChange (``.claude/rules/mui-patterns.md``); ``fill()`` would not.
        Waits for the Generate button to transition to enabled afterwards —
        the real signal, not a fixed delay.
        """
        self.name_input.click()
        self.name_input.press_sequentially(name, delay=20)
        expect(self.generate_button).to_be_enabled(timeout=UI_ELEMENT_TIMEOUT)

    def type_name(self, name: str) -> None:
        """Type *name* into the Name field without asserting Generate's
        resulting enabled/disabled state (unlike fill_name(), which asserts
        enabled — not valid for negative/invalid-name cases where Generate
        is expected to stay disabled)."""
        self.name_input.click()
        self.name_input.press_sequentially(name, delay=20)

    def clear_and_type_name(self, name: str) -> None:
        """Replace the Name field's current content with *name*.

        Uses Home + Shift+End to select the full line, then types over the
        selection — Control+a is unreliable here because Input.InputBase's
        enableAutoBlur fires a real blur()+focus() cycle ~10ms after every
        change, which can race a Control+a keypress and silently reset the
        cursor before the shortcut lands (confirmed live during ELITEA-2286
        AFS exploration).
        """
        self.name_input.click()
        self.page.keyboard.press("Home")
        self.page.keyboard.press("Shift+End")
        self.name_input.press_sequentially(name, delay=20)

    def get_expiration_measure_text(self) -> str:
        """Return the currently-selected expiration-unit display text."""
        return (self.expiration_measure_combobox.text_content() or "").strip()

    def get_expiration_value(self) -> str:
        """Return the expiration numeric value input's current value."""
        return self.expiration_value_input.input_value()

    def click_generate(self, timeout: int = UI_ELEMENT_TIMEOUT):
        """Click Generate; wait for the token-create POST to resolve 200,
        then for the GeneratedTokenDialog to appear.

        Returns the Playwright ``Response`` for the create POST (side-channel
        proof the create actually happened, per AFS step 5).
        """

        def _is_create_response(response) -> bool:
            return (
                TOKEN_CREATE_URL_SUBSTRING in response.url
                and response.request.method == "POST"
            )

        with self.page.expect_response(_is_create_response, timeout=timeout) as resp_info:
            self.generate_button.click()
        response = resp_info.value
        self.dialog_title.wait_for(state="visible", timeout=timeout)
        return response

    def get_dialog_title_text(self) -> str:
        return (self.dialog_title.text_content() or "").strip()

    def get_dialog_warning_text(self) -> str:
        return (self.dialog_warning.text_content() or "").strip()

    def get_dialog_token_name_text(self) -> str:
        return (self.dialog_token_name.text_content() or "").strip()

    def get_dialog_token_value_text(self) -> str:
        return (self.dialog_token_value.text_content() or "").strip()

    def is_token_name_above_token_value(self) -> bool:
        """Return True if the dialog's token-name element renders above (a
        smaller Y coordinate than) the token-value element — DOM/visual
        order proof for the AFS's "name shown above value" assertion."""
        name_box = self.dialog_token_name.bounding_box()
        value_box = self.dialog_token_value.bounding_box()
        assert name_box is not None and value_box is not None, (
            "Expected both the dialog token-name and token-value elements to "
            "have a bounding box (be rendered/visible)"
        )
        return name_box["y"] < value_box["y"]

    def click_copy_and_get_toast_text(self, timeout: int = UI_ELEMENT_TIMEOUT) -> str:
        """Click the Copy button, wait for the confirmation toast, and return
        its text. Does not wait on the button's own disabled-state revert."""
        self.dialog_copy_button.click()
        self.toast_message.wait_for(state="visible", timeout=timeout)
        return (self.toast_message.text_content() or "").strip()

    def get_copy_button_text(self) -> str:
        return (self.dialog_copy_button.text_content() or "").strip()

    def is_copy_button_disabled(self) -> bool:
        return self.dialog_copy_button.is_disabled()

    def read_clipboard_text(self) -> str:
        """Read the OS/browser clipboard's current text content.

        Requires the browser context to have been created with the
        ``clipboard-read`` permission granted (already true for the pytest
        suite's ``context`` fixture, ``conftest.py`` ~line 279). Do NOT call
        this from a context lacking that permission — it hangs indefinitely
        rather than rejecting (confirmed live during AFS exploration).
        """
        return self.page.evaluate("navigator.clipboard.readText()")

    def close_dialog(self, timeout: int = NAVIGATION_TIMEOUT) -> None:
        """Click the dialog's close (X) icon and wait for the navigation back
        to /settings/tokens (``onClose`` -> ``onCancel`` -> ``navigate(-1)``)."""
        self.dialog_close_button.click()
        self.page.wait_for_url("**/settings/tokens", timeout=timeout)
