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

    # Generic schema-driven field testids (ELITEA-1967). The credential create
    # form is rendered entirely from the backend schema
    # (``GET /configurations/available/?section=credentials``), and every field
    # testid is derived from the schema property key by the shared
    # ``ToolBaseProperty`` renderer — so these templates cover ANY credential
    # type without a per-type constant. Class-level template constants per
    # .agents/testing.md § Locator policy (dynamic testid pattern).
    #
    # A PLAIN field puts ``toolkit-field-{key}-input`` on the <input> itself;
    # a SECRET field puts it on the wrapper <div> and adds
    # ``toolkit-field-{key}-input-field`` on the native <input>. FIELD_INPUT
    # therefore resolves for both, which is what a presence/absence inventory
    # needs.
    FIELD_INPUT = '[data-testid="toolkit-field-{}-input"]'
    # Secret/Password toggle rendered beside every secret field. Second
    # placeholder is the mode: "secret" | "password".
    FIELD_SECRET_TOGGLE = '[data-testid="toolkit-field-{}-input-toggle-{}"]'
    # Enum (dropdown) field, e.g. Jira/Confluence "Hosting".
    FIELD_SELECT = '[data-testid="toolkit-field-{}-select"]'
    # --- Secret-field "Secret" mode (ELITEA-1968 / ELITEA-1969) ---------
    # A SecretField in `secret` mode swaps its native <input> for a
    # SingleSelect over the project's secret vault. The select's display node
    # inherits the caller's data-testid with a `-combobox` suffix
    # (`SingleSelect.jsx` SelectDisplayProps); the native password <input>
    # (`FIELD_SECRET_INPUT`) is absent in that mode, and vice versa.
    FIELD_SECRET_COMBOBOX = '[data-testid="toolkit-field-{}-input-combobox"]'
    # FIELD_SECRET_INPUT + secret_native_input() moved to
    # CredentialFormFieldsMixin for ELITEA-1970 (the credential DETAIL page
    # renders the same secret fields); inherited here unchanged.
    # "Saved Secrets" group-header refresh button — caller-derived testid added
    # for ELITEA-1969 (EliteaAI/EliteaUI@29214bf1).
    FIELD_SECRET_REFRESH_BUTTON = (
        '[data-testid="toolkit-field-{}-input-refresh-secrets-button"]'
    )
    # Dropdown group headers. `SingleSelect.jsx` renders
    # `select-group-header-{group.key}`; SecretField's two group keys are the
    # literals "Create" and "Saved Secrets" (the rendered TEXT is uppercased by
    # CSS: "CREATE" / "SAVED SECRETS").
    SECRET_GROUP_HEADER_CREATE = '[data-testid="select-group-header-Create"]'
    SECRET_GROUP_HEADER_SAVED = '[data-testid="select-group-header-Saved Secrets"]'
    # The CREATE-section action option. Its VALUE is the same
    # `__create_private_secret__` sentinel in every project scope; only its
    # LABEL changes ("New Private Secret" on the personal project, "New Project
    # Secret" elsewhere) — see the ELITEA-1968 AFS § Case-text divergence.
    SECRET_CREATE_OPTION = '[data-testid="select-option-__create_private_secret__"]'
    # A saved secret's option. The option VALUE is the `{{secret.<name>}}`
    # template, so the testid embeds the braces literally; `{{` / `}}` below are
    # str.format escapes that render as single braces.
    SECRET_SAVED_OPTION = '[data-testid="select-option-{{{{secret.{}}}}}"]'
    # Prefix form, for counting the saved-secret options (ELITEA-1969 asserts a
    # baseline+1 delta across the refresh). NOT a format template — the `{{`
    # here is the literal double brace the testid itself carries.
    SECRET_SAVED_OPTION_PREFIX = '[data-testid^="select-option-{{secret."]'

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

    def open_type_form(self, credential_type: str, timeout: int = UI_ELEMENT_TIMEOUT) -> None:
        """Navigate to the create form for *credential_type* and settle on the
        rendered form, NOT on ``networkidle`` (ELITEA-1967).

        Additive sibling of :meth:`navigate_to_type` — that method's
        :meth:`wait_for_page_load` calls ``wait_for_network()``
        (``wait_for_load_state("networkidle")``), and the credentials routes do
        **not** reliably reach network-idle: background traffic against the DEV
        backend keeps the connection count above zero. Live-observed here on
        step 8 of a 10-navigation run — 7 navigations settled, the 8th raised a
        bare ``TimeoutError`` from ``networkidle`` on an already fully-rendered
        page. The same characteristic is recorded for ``/credentials/all`` in
        ``test-specs/toolkits-credentials/_surface.md`` (ELITEA-1964) and fixed
        there the same way.

        The form is schema-driven: it renders only once
        ``GET /configurations/available/?section=credentials`` has resolved and
        ``CreateCredential.jsx`` has built ``credentialDetails``. So the
        Display Name field becoming visible IS the "form is ready" condition —
        a real product signal, no sleep, no idle heuristic.

        :meth:`navigate_to_type` is left byte-identical for its four existing
        callers (additive-only on a shared-caller page object).
        """
        self.navigate(f"/credentials/create-credential/{credential_type}")
        self.display_name_input.wait_for(state="visible", timeout=timeout)

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

    def field(self, field_key: str) -> Locator:
        """Return the form-field locator for schema property *field_key*.

        Resolves for plain fields (testid on the ``<input>``) and secret
        fields alike (testid on the ``SecretField`` wrapper ``<div>``) — see
        :data:`FIELD_INPUT`. Used by ELITEA-1967 for both presence and
        ``to_have_count(0)`` absence assertions.
        """
        return self.page.locator(self.FIELD_INPUT.format(field_key))

    def secret_toggle(self, field_key: str, mode: str) -> Locator:
        """Return the Secret/Password toggle button of secret field *field_key*.

        Args:
            field_key: The schema property key (e.g. ``"api_key"``).
            mode: ``"secret"`` or ``"password"`` — the toggle's two options.
        """
        return self.page.locator(self.FIELD_SECRET_TOGGLE.format(field_key, mode))

    def field_select(self, field_key: str) -> Locator:
        """Return the enum-dropdown locator for schema property *field_key*
        (e.g. Jira/Confluence ``"hosting"``)."""
        return self.page.locator(self.FIELD_SELECT.format(field_key))

    # ------------------------------------------------------------------
    # Secret-field "Secret" mode — vault dropdown (ELITEA-1968 / ELITEA-1969)
    # ------------------------------------------------------------------
    def secret_combobox(self, field_key: str) -> Locator:
        """Return the Secret-mode select display node of secret field
        *field_key* (present only while the field is in ``secret`` mode)."""
        return self.page.locator(self.FIELD_SECRET_COMBOBOX.format(field_key))

    def open_secret_dropdown(self, field_key: str) -> None:
        """Open the Secret-mode vault dropdown of secret field *field_key*.

        Waits on the first SAVED-SECRETS *option*, not on a network idle and not
        on the group header. The vault query
        (``GET /secrets/secrets/default/{project}``) is ``skip``-gated on the
        field's mode, so on the first entry into Secret mode the menu opens
        BEFORE the list resolves: the group headers render immediately while the
        group body is still an empty placeholder. Waiting on the header alone
        therefore returns an open-but-empty dropdown (cost one rerun,
        ELITEA-1968). ``networkidle`` is unusable on the credentials routes
        (`.agents/testing.md`, ELITEA-1964/1967).

        Assumes the case's own precondition — at least one saved secret exists
        in the project's vault.
        """
        self.secret_combobox(field_key).click()
        self.secret_saved_group_header.wait_for(
            state="visible", timeout=UI_ELEMENT_TIMEOUT
        )
        self.saved_secret_options.first.wait_for(
            state="visible", timeout=UI_ELEMENT_TIMEOUT
        )

    @property
    def secret_create_group_header(self) -> Locator:
        """CREATE group header inside the open vault dropdown."""
        return self.page.locator(self.SECRET_GROUP_HEADER_CREATE)

    @property
    def secret_saved_group_header(self) -> Locator:
        """SAVED SECRETS group header inside the open vault dropdown."""
        return self.page.locator(self.SECRET_GROUP_HEADER_SAVED)

    @property
    def secret_create_option(self) -> Locator:
        """The CREATE-section action option ("New Private Secret" on a personal
        project, "New Project Secret" on a team project — same testid)."""
        return self.page.locator(self.SECRET_CREATE_OPTION)

    def saved_secret_option(self, secret_name: str) -> Locator:
        """Return the vault-dropdown option for the saved secret *secret_name*."""
        return self.page.locator(self.SECRET_SAVED_OPTION.format(secret_name))

    @property
    def saved_secret_options(self) -> Locator:
        """Every saved-secret option currently rendered in the open dropdown."""
        return self.page.locator(self.SECRET_SAVED_OPTION_PREFIX)

    def secret_refresh_button(self, field_key: str) -> Locator:
        """Return the SAVED SECRETS group-header refresh button of secret field
        *field_key* (refetches the vault list without closing the dropdown)."""
        return self.page.locator(self.FIELD_SECRET_REFRESH_BUTTON.format(field_key))
