"""Shared Display-Name-field + Save-button mixin for credential page objects.

Both :class:`CredentialCreatePage` (``/credentials/create-credential/{type}``)
and :class:`CredentialDetailPage` (``/credentials/all/{id}``) render the same
``ToolBaseProperty``-backed Display Name field (``toolkit-field-label-input``)
and the same tab-bar Save button (``credential-form-save-button``) —
identical testids, identical MUI select-all-quirk workaround. Extracted to a
shared mixin (rather than duplicated per page object, per
``.claude/rules/page-objects.md`` "NO Method Duplication") — same treatment
already given to the ``/credentials/all`` crash-recovery helper in
``credentials_list_recovery.py``.

Promoted here for ELITEA-1970 (Credential - Test connection), which drives the
same ``CredentialForm.jsx`` block from the DETAIL page: the Test connection
button, the global API-error text, and the secret field's native password
input. All three were already declared once — on
:class:`CredentialCreatePage` — and are rendered identically by both pages, so
they move rather than duplicate (same treatment ``id_input`` already got). The
move is transparent to their existing callers: both page objects inherit this
mixin, so ``create_page.test_connection_button`` resolves exactly as before.
"""

from playwright.sync_api import Locator

from .locator_descriptor import LocatorDescriptor


class CredentialFormFieldsMixin:
    """Mixin providing the shared Display Name field + Save button.

    Expects the consuming class to also inherit :class:`BasePage` (for
    ``self.page``); this mixin declares no ``__init__`` of its own.
    """

    display_name_input = LocatorDescriptor(
        testid="toolkit-field-label-input",
        description="Credential Display Name input (shared ToolBaseProperty renderer)",
    )
    save_button = LocatorDescriptor(
        testid="credential-form-save-button",
        description="Save credential button (tab-bar) — gated on required-field validation",
    )
    id_input = LocatorDescriptor(
        testid="toolkit-field-elitea_title-input",
        description=(
            "Credential ID (elitea_title) input — disabled, live-mirrors Display "
            "Name. Promoted here from CredentialDetailPage (ELITEA-1962) so "
            "CredentialCreatePage can also assert the auto-generated mirror "
            "before Save — same testid, same shared ToolBaseProperty renderer."
        ),
    )

    test_connection_button = LocatorDescriptor(
        testid="credential-form-test-connection-button",
        description=(
            "Test connection button (CredentialForm.jsx). Disabled when the "
            "credential type's schema carries has_test_connection: false "
            "(Postman, of the ELITEA-1967 set) or when the type's "
            "check_connection.enabled_when fields are unset. Testid added for "
            "ELITEA-1967; promoted from CredentialCreatePage for ELITEA-1970, "
            "which clicks it on the credential DETAIL page."
        ),
    )
    api_error_message = LocatorDescriptor(
        testid="credential-form-api-error-message",
        description=(
            "Server-side API error text rendered below the form "
            "(CredentialForm.jsx) - e.g. the duplicate-elitea_title 400 message "
            "on Save. Testid added for ELITEA-1978; promoted from "
            "CredentialCreatePage for ELITEA-1970, which asserts it stays "
            "ABSENT when a failed Test connection maps onto a field instead "
            "(useCreateConfiguration.onTestConnection only falls back to this "
            "banner when extractInformationFromCredentialError maps nothing)."
        ),
    )

    # ------------------------------------------------------------------
    # Toast (shared Toast.jsx) - the success half of Test connection
    # ------------------------------------------------------------------
    # Repo precedent (agent_detail_page.py, generate_skill_modal_page.py):
    # every page object that raises a toast declares its own descriptors for
    # the shared testids, plus a severity-scoped class constant so the
    # severity is asserted as a data-* attribute filter rather than by CSS
    # class sniffing (.agents/testing.md - "state via data-* attributes").
    toast_alert = LocatorDescriptor(
        testid="toast-alert",
        description="Toast container (shared Toast.jsx) - carries data-severity",
    )
    toast_message = LocatorDescriptor(
        testid="toast-message",
        description="Toast body text (shared Toast.jsx)",
    )
    TOAST_ALERT_SEVERITY = '[data-testid="toast-alert"][data-severity="{}"]'

    # ------------------------------------------------------------------
    # Secret fields (shared SecretField.jsx renderer)
    # ------------------------------------------------------------------
    # Promoted from CredentialCreatePage (ELITEA-1970). A SECRET schema
    # property puts `toolkit-field-{key}-input` on the SecretField wrapper
    # <div> and `-input-field` on the native <input type="password">.
    FIELD_SECRET_INPUT = '[data-testid="toolkit-field-{}-input-field"]'
    # Any schema-driven form field, promoted from CredentialCreatePage for
    # ELITEA-1980 (the DETAIL route renders the same ToolBaseProperty fields).
    # A PLAIN field puts `toolkit-field-{key}-input` on the <input> itself;
    # a SECRET field puts it on the SecretField wrapper <div> (and the native
    # <input> carries FIELD_SECRET_INPUT), so this template resolves for both.
    FIELD_INPUT = '[data-testid="toolkit-field-{}-input"]'
    # Inline error/helper text under a secret field - caller-derived testid
    # added for ELITEA-1970 (EliteaAI/EliteaUI@58955184). Present only while
    # the field is in error; carries the backend's own message verbatim.
    FIELD_HELPER_TEXT = '[data-testid="toolkit-field-{}-input-helper-text"]'

    def field(self, field_key: str) -> Locator:
        """Return the form-field locator for schema property *field_key*.

        Resolves for plain fields (testid on the ``<input>``) and secret
        fields alike (testid on the ``SecretField`` wrapper ``<div>``) — see
        :data:`FIELD_INPUT`. Used by ELITEA-1967 for both presence and
        ``to_have_count(0)`` absence assertions, and by ELITEA-1980 to read a
        field's ``aria-invalid`` state after a failed Test connection.

        Promoted here from :class:`CredentialCreatePage` (ELITEA-1980) so the
        detail route can use it too; that class inherits this mixin, so its
        existing callers are unchanged.
        """
        return self.page.locator(self.FIELD_INPUT.format(field_key))

    def secret_native_input(self, field_key: str) -> Locator:
        """Return the Password-mode native ``<input type="password">`` of
        secret field *field_key* (present only in ``password`` mode)."""
        return self.page.locator(self.FIELD_SECRET_INPUT.format(field_key))

    def secret_field_helper_text(self, field_key: str) -> Locator:
        """Return the inline error/helper text rendered under secret field
        *field_key*.

        Rendered by the shared ``SecretField`` through MUI's
        ``slotProps.formHelperText``; the testid is derived from the field's
        own testid, so a form with several secret fields keeps one unique
        handle per field. A failed Test connection puts the backend's
        ``message`` here verbatim (see
        ``credentialError.helpers.js#extractInformationFromCredentialError``).
        """
        return self.page.locator(self.FIELD_HELPER_TEXT.format(field_key))

    def field_helper_text(self, field_key: str) -> Locator:
        """Return the inline error/helper text under ANY form field *field_key*
        — plain or secret.

        Additive sibling of :meth:`secret_field_helper_text` (left
        byte-identical for its ELITEA-1970 caller): both resolve the same
        :data:`FIELD_HELPER_TEXT` testid grammar, which now covers plain fields
        too. ``ToolBaseProperty`` passes the shared ``helperTextTestId`` prop
        (``InputBase.jsx:101``/``:270``) with the same caller-derived
        ``{field-testid}-helper-text`` value ``SecretField`` uses — added for
        ELITEA-1980 (EliteaAI/EliteaUI@54ce148e).

        Which field a failed Test connection lights up is decided by
        ``credentialError.helpers.js#extractInformationFromCredentialError``
        and is NOT always the secret one: when nothing in the backend message
        maps to a schema key, its fallback branch assigns the message to every
        ``*url*`` key — so a Github auth failure lands on **Base Url**
        (``_surface.md`` § Credential ERROR states).
        """
        return self.page.locator(self.FIELD_HELPER_TEXT.format(field_key))

    def replace_secret_value(self, field_key: str, value: str) -> None:
        """Replace secret field *field_key*'s value with *value*.

        Select-all + Backspace + ``press_sequentially`` rather than
        ``fill()``: MUI/React only commits on real key events
        (``.claude/rules/mui-patterns.md``), and the field may already hold a
        value (a saved credential's field carries its vault entry's name).
        """
        field = self.secret_native_input(field_key)
        field.click()
        field.press("ControlOrMeta+a")
        field.press("Backspace")
        field.press_sequentially(value, delay=20)

    def success_toast(self) -> Locator:
        """Return the success-severity toast container."""
        return self.page.locator(self.TOAST_ALERT_SEVERITY.format("success"))

    def set_display_name(self, value: str) -> None:
        """Replace the Display Name field's value, triggering React onChange.

        MUI fields don't fire React's onChange on Playwright's ``fill()`` —
        and ``press("Control+a")`` does NOT select-all on this field either
        (live-verified: it moves the caret to position 0 without selecting,
        so subsequent typing prepends instead of replacing). Uses
        ``select_text()`` + ``type()`` instead, which sets the DOM selection
        directly.
        """
        self.display_name_input.click()
        self.display_name_input.select_text()
        self.display_name_input.type(value)

    def is_save_enabled(self) -> bool:
        return self.save_button.is_enabled()
