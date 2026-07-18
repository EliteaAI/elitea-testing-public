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
"""

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
