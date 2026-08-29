"""AI-Provider create/edit form page object (Settings -> AI Providers -> "+" / card).

Routes:
    * create — ``/settings/create-ai-provider/{provider_type}?viewMode=owner&from=ai-providers``
    * edit   — ``/settings/edit-ai-provider/{configuration_id}?from=ai-providers``

Both routes render the SAME schema-driven credential form the
``/credentials/create-credential/{type}`` route renders
(``ToolBase.jsx`` -> ``ToolBaseProperty``/``SecretField``), so every plain field
handle (``toolkit-field-label-input``, ``toolkit-field-elitea_title-input``,
``credential-form-save-button``, ``FIELD_INPUT``/``FIELD_HELPER_TEXT``
templates, ...) is INHERITED from :class:`CredentialFormFieldsMixin` rather
than redeclared here -- the same treatment
:class:`~pages.credential_create_page.CredentialCreatePage` and
:class:`~pages.credential_detail_page.CredentialDetailPage` already get.

What this page object adds on top of the mixin is only what is specific to the
AI-provider flow:

* the **Ai Credentials** picker (``toolkit-credential-select--combobox``). The
  trailing dash is real, not a typo: the JSX is
  ``toolkit-credential-select-${type}`` (``CredentialsSelect.jsx:519``) and
  ``type`` is empty on this form. Its saved-credential options carry
  JSON-shaped testids -- see :data:`SAVED_CREDENTIAL_OPTION`.
* the three-dot controls menu + the shared ``DeleteEntityModal`` handles, which
  are how an AI-provider configuration is deleted (the only teardown path).

Locator provenance (ELITEA-2395/2396/2408/2409, 2026-08-29): every testid used
by this page object is **pre-existing on ``origin/main``** -- nothing here was
added by this implementation. The one testid this cluster DID add
(``ai-providers-configuration-group`` / ``-group-name``) belongs to the list
page and lives on :class:`~pages.ai_providers_page.AIProvidersPage`.

Declared decision (`.agents/role-overrides.md` § declared-improvisation): the
shared ``DeleteEntityModal`` testids (``delete-confirm-dialog`` /
``-entity-name`` / ``-name-input`` / ``-button``) are declared here as well as
on ``credential_detail_page.py``, ``secrets_page.py``,
``personal_tokens_page.py`` and ``mcp_form_page.py`` -- five entity surfaces,
one shared modal. Extracting them into a shared mixin would rewrite four merged
page objects in a test-case PR; that refactor is named as tech debt in this
unit's Run Report instead of smuggled in here.
"""

import logging
import re

from playwright.sync_api import Locator, Page

from .base_page import BasePage
from .credential_form_fields import CredentialFormFieldsMixin
from .locator_descriptor import LocatorDescriptor

logger = logging.getLogger("elitea.pages.ai_provider_form")

UI_ELEMENT_TIMEOUT = 10_000
NAVIGATION_TIMEOUT = 20_000

CREATE_PATH = "/settings/create-ai-provider/{}?viewMode=owner&from=ai-providers"

#: The list page the form returns to on a successful Save / Delete.
AI_PROVIDERS_URL_PATTERN = re.compile(r"/settings/ai-providers(\?|#|$)")

#: ``/settings/edit-ai-provider/{configuration_id}`` -- the edit form's own route.
EDIT_URL_PATTERN = re.compile(r"/settings/edit-ai-provider/(\d+)")


class AiProviderFormPage(CredentialFormFieldsMixin, BasePage):
    """Create / edit form for an AI-provider configuration (LLM model, ...)."""

    # -- Ai Credentials picker ------------------------------------------
    credential_select_combobox = LocatorDescriptor(
        testid="toolkit-credential-select--combobox",
        description="Ai Credentials picker -- clickable combobox node; its "
        "text content is the selected credential's display name. The trailing "
        "dash is real (`toolkit-credential-select-${type}` with an empty type).",
    )

    # Dynamic (runtime-parameterized) testid -- the shared `Select` component
    # stringifies the option's own VALUE into the testid, and a saved
    # credential's value is a JSON object. Braces doubled for `.format`, per
    # `.agents/testing.md` § Locator policy's dynamic-testid class-constant
    # pattern (an inline `get_by_test_id(f"...")` would not be compliant).
    SAVED_CREDENTIAL_OPTION = (
        '[data-testid=\'select-option-{{"kind":"saved","elitea_title":"{}","private":false}}\']'
    )

    # -- Tab-bar controls ------------------------------------------------
    discard_button = LocatorDescriptor(
        testid="credential-form-discard-button",
        description="Cancel/Discard button (tab-bar) -- disabled while the form is pristine",
    )

    # -- Three-dot controls menu + shared DeleteEntityModal --------------
    controls_menu_button = LocatorDescriptor(
        testid="controls-menu-button",
        description="Three-dot controls menu on the edit form",
    )
    delete_menuitem = LocatorDescriptor(
        testid="delete-credentials-menuitem",
        description='"Delete" item in the three-dot menu -- testid composed at '
        "runtime by DotMenu.jsx:58 from the item key 'delete-credentials'",
    )
    delete_confirm_dialog = LocatorDescriptor(
        testid="delete-confirm-dialog",
        description="Shared type-to-confirm delete dialog (DeleteEntityModal)",
    )
    delete_confirm_entity_name = LocatorDescriptor(
        testid="delete-confirm-entity-name",
        description="The exact entity name the delete dialog asks you to retype",
    )
    delete_confirm_name_input = LocatorDescriptor(
        testid="delete-confirm-name-input",
        description="Type-to-confirm Name input inside the delete dialog",
    )
    delete_confirm_button = LocatorDescriptor(
        testid="delete-confirm-button",
        description="Delete button inside the delete-confirmation dialog",
    )

    def __init__(self, page: Page):
        super().__init__(page)

    # ------------------------------------------------------------------
    # Navigation
    # ------------------------------------------------------------------
    def navigate_to_create(self, provider_type: str = "llm_model", timeout: int = NAVIGATION_TIMEOUT) -> None:
        """Open the create form for *provider_type* directly and settle on the
        rendered form.

        Settles on ``toolkit-field-label-input`` becoming visible, NOT on
        navigation or ``networkidle``: the form is schema-driven
        (``GET /configurations/available/?section=...`` resolves first), so it
        mounts seconds after the route changes -- a ``fill()`` straight after
        the goto fails with "does not match any elements" (live-observed,
        `_surface.md`). ``networkidle`` is separately unusable on these routes
        (`.agents/testing.md` #1847).
        """
        self.navigate(CREATE_PATH.format(provider_type))
        self.display_name_input.wait_for(state="visible", timeout=timeout)

    def wait_for_form(self, timeout: int = NAVIGATION_TIMEOUT) -> None:
        """Wait for the (create or edit) form's Display Name field to mount."""
        self.display_name_input.wait_for(state="visible", timeout=timeout)

    def wait_for_schema_field(self, field_key: str, timeout: int = NAVIGATION_TIMEOUT) -> None:
        """Wait for the TYPE-SPECIFIC schema field *field_key* to mount.

        :meth:`wait_for_form` settles on ``toolkit-field-label-input``, which
        the form renders in its PRE-schema pass too -- so it can return while
        ``GET /configurations/available/?section=...`` is still in flight, and
        the schema-driven re-render that follows WIPES anything typed in the
        gap (`_surface.md`: "a direct goto of a create route can silently wipe
        an early fill()"). Live-measured on ELITEA-2399: Display Name typed and
        read back correctly, Save observed ENABLED, then Save was still
        disabled 10 s later at the click -- the label had been cleared by the
        re-render after the assertions passed.

        Waiting for a field that exists ONLY in the schema render
        (``connection_string`` for pgvector, ``name`` for llm_model /
        embedding_model) proves that render has landed, so nothing typed after
        this call can be wiped. Additive: :meth:`wait_for_form` and
        :meth:`navigate_to_create` keep their merged callers unchanged.
        """
        self.field(field_key).wait_for(state="visible", timeout=timeout)

    def fill_secret_field(self, field_key: str, value: str) -> None:
        """Type *value* into secret field *field_key* and BLUR it.

        The blur is load-bearing, not tidiness: the shared ``Input``/
        ``InputBase`` renderer runs with ``enableAutoBlur`` and some
        schema-typed fields only commit their value into the form state on
        blur (the same reason :meth:`CredentialFormFieldsMixin.type_into_field`
        blurs) -- which is exactly what a human does by moving to the next
        control. :meth:`CredentialFormFieldsMixin.replace_secret_value` does
        not blur and is left byte-identical for its merged callers.
        """
        self.replace_secret_value(field_key, value)
        self.secret_native_input(field_key).blur()

    def configuration_id_from_url(self) -> str:
        """Return the ``{configuration_id}`` segment of the edit route.

        Raises:
            AssertionError: the browser is not on an edit form.
        """
        match = EDIT_URL_PATTERN.search(self.page.url)
        assert match, f"Not on an AI-provider edit form: {self.page.url}"
        return match.group(1)

    def wait_for_ai_providers_list(self, timeout: int = NAVIGATION_TIMEOUT) -> None:
        """Wait until the app has navigated back to ``/settings/ai-providers``."""
        self.page.wait_for_url(AI_PROVIDERS_URL_PATTERN, timeout=timeout)

    def clear_display_name(self) -> None:
        """Clear the Display Name field via select-all + Backspace, triggering
        React ``onChange`` (MUI does not commit on ``fill()`` --
        ``.claude/rules/mui-patterns.md``). Same shape as
        :meth:`~pages.credential_create_page.CredentialCreatePage.clear_display_name`.
        """
        self.display_name_input.click()
        self.display_name_input.select_text()
        self.display_name_input.press("Backspace")

    # ------------------------------------------------------------------
    # Ai Credentials picker
    # ------------------------------------------------------------------
    def saved_credential_option(self, elitea_title: str) -> Locator:
        """Return the dropdown option for the SAVED credential *elitea_title*."""
        return self.page.locator(self.SAVED_CREDENTIAL_OPTION.format(elitea_title))

    def select_saved_credential(self, elitea_title: str, timeout: int = UI_ELEMENT_TIMEOUT) -> None:
        """Open the Ai Credentials picker and select the saved credential
        *elitea_title* (the credential's ``elitea_title``, e.g. ``"elps"`` --
        NOT its displayed label)."""
        self.credential_select_combobox.click()
        option = self.saved_credential_option(elitea_title)
        option.wait_for(state="visible", timeout=timeout)
        option.click()

    # ------------------------------------------------------------------
    # Save
    # ------------------------------------------------------------------
    def save_and_return_to_list(self, timeout: int = NAVIGATION_TIMEOUT) -> None:
        """Click Save and wait for the app's own navigation back to the AI
        Providers list -- the product's signal that the write succeeded (the
        list then re-renders from its own refetch; no manual reload)."""
        self.save_button.click()
        self.wait_for_ai_providers_list(timeout=timeout)

    # ------------------------------------------------------------------
    # Delete (the only teardown path for a configuration)
    # ------------------------------------------------------------------
    def delete_current_configuration(self, display_name: str, timeout: int = UI_ELEMENT_TIMEOUT) -> None:
        """Delete the configuration whose EDIT form is currently open.

        Three-dot menu -> "Delete" -> retype *display_name* into the shared
        confirm dialog -> Delete. Uses ``press_sequentially`` because MUI only
        commits React ``onChange`` on real key events
        (``.claude/rules/mui-patterns.md``).
        """
        self.controls_menu_button.click()
        self.delete_menuitem.click()
        self.delete_confirm_dialog.wait_for(state="visible", timeout=timeout)
        self.delete_confirm_name_input.click()
        self.delete_confirm_name_input.press_sequentially(display_name, delay=20)
        self.delete_confirm_button.click()
        self.delete_confirm_dialog.wait_for(state="detached", timeout=timeout)
