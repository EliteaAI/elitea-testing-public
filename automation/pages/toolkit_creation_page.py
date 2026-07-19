"""Toolkit Creation Page - the "New Toolkit" wizard (type-picker + form).

Handles: /toolkits/create, /toolkits/create/{type}
- "Choose the toolkit type" picker (search + type cards, grouped by category)
- The per-type configuration form (Name, schema-driven fields, Save/Cancel)
- The Cancel → confirm ("Discard") flow

Deliberately does NOT extend :class:`ToolkitDetailPage` (AFS § Overlap
check) — that page object models an EXISTING toolkit's detail/config view
(credential-status indicators, Save/Discard on an already-saved toolkit)
and shares no real behavior with this wizard. Added for ELITEA-1868 —
``automation/pages/`` previously had zero coverage of the creation wizard.

``ToolkitTypeSelector.jsx``/``CreateToolkitToolTabBar.jsx`` are the SAME
shared components used for Toolkit/MCP/Application creation (``isMCP``/
``isApplication`` props only switch labels/destination routes) — the
Cancel-confirm-dialog flow and its testids
(``toolkit-form-cancel-button``/``-confirm-dialog``/``-confirm-button``)
are wired generically at that shared call site, not toolkit-specific,
though only the plain-toolkit type-search input carries the
``toolkit-wizard-type-search-input`` testid (scoped per the shared-component
testid ruling — MCP/Application creation get no testid on that field since
no case touches them there yet).
"""

import logging

from playwright.sync_api import Page

from .base_page import BasePage
from .locator_descriptor import LocatorDescriptor
from utils.actions import action

logger = logging.getLogger("elitea.pages.toolkit_creation")


class ToolkitCreationPage(BasePage):
    """Page object for the "New Toolkit" creation wizard.

    URL: /toolkits/create, /toolkits/create/{type}
    """

    # ------------------------------------------------------------------
    # Type-picker ("Choose the toolkit type")
    # ------------------------------------------------------------------

    type_search_input = LocatorDescriptor(
        testid="toolkit-wizard-type-search-input",
        description="Type-picker's search field ('Search toolkits') — filters "
        "the type cards live via onChange, no Enter/debounce required "
        "(confirmed live, ELITEA-1868 implementer Phase 2 exploration)",
    )

    # Dynamic testid template — a specific toolkit-type card, keyed by its
    # schema type key (e.g. "artifact", "github"). CategoryItemCard.jsx.
    # NEVER locate this card via text-matching — a text-based Playwright
    # locator (`page.locator('div').filter({ hasText: /^Artifact$/ })`)
    # resolves to a non-interactive wrapper <div> and silently no-ops
    # (confirmed live, both ELITEA-1868 exploration runs).
    TOOLKIT_TYPE_CARD = '[data-testid="toolkit-type-card-{}"]'

    # Prefix (any-type) variant — matches every currently-rendered type
    # card regardless of type key. Same `[data-testid^="…"]` prefix-count
    # pattern already established elsewhere (artifacts_page.py's
    # BUCKET_ROW_ANY_SELECTOR) — used to prove the type-search filter
    # narrows the rendered list down to exactly one match.
    TOOLKIT_TYPE_CARD_ANY_SELECTOR = '[data-testid^="toolkit-type-card-"]'

    # ------------------------------------------------------------------
    # Configuration form
    # ------------------------------------------------------------------

    name_input = LocatorDescriptor(
        testid="toolkit-form-name-input",
        description="Toolkit Name field — generic across ALL toolkit types "
        "(NameDescriptionInput.jsx), not artifact-specific",
    )

    # Dynamic testid template — a schema-driven field, keyed by its schema
    # property key (e.g. "bucket"). ToolBaseProperty.jsx — the SAME
    # mechanism every schema-driven toolkit field uses.
    TOOLKIT_FIELD_INPUT = '[data-testid="toolkit-field-{}-input"]'

    save_button = LocatorDescriptor(
        testid="toolkit-form-save-button",
        description="Save button — shared across toolkit/MCP/application creation",
    )

    cancel_button = LocatorDescriptor(
        testid="toolkit-form-cancel-button",
        description="Cancel button (trigger) — opens the confirm dialog on click, "
        "shared across toolkit/MCP/application creation (CreateToolkitToolTabBar.jsx)",
    )

    cancel_confirm_dialog = LocatorDescriptor(
        testid="toolkit-form-cancel-confirm-dialog",
        description="'Warning' confirmation dialog shown after clicking Cancel",
    )

    cancel_confirm_button = LocatorDescriptor(
        testid="toolkit-form-cancel-confirm-button",
        description="'Discard' (confirm) button inside the Cancel confirmation dialog",
    )

    def __init__(self, page: Page):
        super().__init__(page)

    # ------------------------------------------------------------------
    # Type-picker
    # ------------------------------------------------------------------

    @action("Search toolkit types")
    def search_toolkit_type(self, term: str) -> None:
        """Type *term* into the type-picker's search field.

        Filters the type cards live via ``onChange`` — no Enter/send-icon
        needed and no server round-trip (client-side against the already-
        fetched schema list), confirmed live (ELITEA-1868 implementer
        Phase 2 exploration).

        Args:
            term: Search text (e.g. ``"art"``).
        """
        self.type_search_input.click()
        self.type_search_input.press_sequentially(term, delay=20)
        self.page.wait_for_timeout(500)  # client-side filter render settle
        logger.info("Searched toolkit types for %r", term)

    def get_type_card(self, type_key: str):
        """Return the Locator for a specific toolkit-type card, by schema key.

        Thin wrapper around :attr:`TOOLKIT_TYPE_CARD` so callers (tests)
        never construct the dynamic-testid locator inline themselves —
        locators stay behind the page-object boundary
        (``.claude/rules/ui-tests.md``).

        Args:
            type_key: The toolkit type's schema key (e.g. ``"artifact"``).
        """
        return self.page.locator(self.TOOLKIT_TYPE_CARD.format(type_key))

    def count_type_cards(self, timeout: int = 5000) -> int:
        """Return the number of currently-visible toolkit-type cards (any type).

        Args:
            timeout: Maximum wait time in milliseconds for the first card
                to appear before concluding there are none.
        """
        cards = self.page.locator(self.TOOLKIT_TYPE_CARD_ANY_SELECTOR)
        try:
            cards.first.wait_for(state="visible", timeout=timeout)
        except Exception:
            return 0
        return cards.count()

    @action("Select a toolkit type from the type-picker")
    def select_toolkit_type(self, search_term: str, type_key: str, timeout: int = 15000) -> None:
        """Search the type-picker, then click the matching type card.

        Clicks the card via its dynamic ``[data-testid="toolkit-type-card-{type_key}"]``
        testid — NEVER a text-based locator (see :attr:`TOOLKIT_TYPE_CARD`).
        Waits for the resulting configuration form to render (the Name
        field becoming visible) rather than for network-idle — background
        config-schema GETs fired for embedding/vectorstore-backed types
        (e.g. Artifact) can lag behind the form's own readiness (AFS §
        Automation Hints).

        Args:
            search_term: Text to type into the type-picker search field.
            type_key: The toolkit type's schema key (e.g. ``"artifact"``).
            timeout: Maximum wait time in milliseconds.
        """
        self.search_toolkit_type(search_term)
        card = self.page.locator(self.TOOLKIT_TYPE_CARD.format(type_key))
        card.wait_for(state="visible", timeout=timeout)
        card.click()
        self.name_input.wait_for(state="visible", timeout=timeout)
        logger.info("Selected toolkit type '%s' via search '%s'", type_key, search_term)

    # ------------------------------------------------------------------
    # Configuration form
    # ------------------------------------------------------------------

    @action("Fill Toolkit Name field")
    def fill_name(self, name: str) -> None:
        """Type into the Toolkit Name field.

        MUI/formik field — ``click()`` + ``press_sequentially()``, NOT
        ``fill()``: confirmed live a bare ``fill()``-equivalent does not
        reliably flip ``formik.dirty``, which gates the Save button's
        enabled state (``.claude/rules/mui-patterns.md``).

        Args:
            name: Toolkit name to type.
        """
        self.name_input.click()
        self.name_input.press_sequentially(name, delay=30)
        logger.info("Filled toolkit name field with '%s'", name)

    @action("Fill a schema-driven toolkit field")
    def fill_field(self, field_key: str, value: str) -> None:
        """Type into a dynamic schema-driven field, by its schema property key.

        Same MUI ``click()`` + ``press_sequentially()`` pattern as
        :meth:`fill_name` — the field is rendered by the same
        ``ToolBaseProperty.jsx``/formik machinery.

        Args:
            field_key: The field's schema property key (e.g. ``"bucket"``).
            value: Text to type.
        """
        field = self.page.locator(self.TOOLKIT_FIELD_INPUT.format(field_key))
        field.click()
        field.press_sequentially(value, delay=30)
        logger.info("Filled toolkit field '%s' with '%s'", field_key, value)

    def get_field_locator(self, field_key: str):
        """Return the Locator for a dynamic schema-driven field, by its key.

        Thin wrapper around :attr:`TOOLKIT_FIELD_INPUT` — same rationale as
        :meth:`get_type_card`.

        Args:
            field_key: The field's schema property key (e.g. ``"bucket"``).
        """
        return self.page.locator(self.TOOLKIT_FIELD_INPUT.format(field_key))

    def get_field_value(self, field_key: str) -> str:
        """Return the current value of a dynamic schema-driven field.

        Args:
            field_key: The field's schema property key (e.g. ``"bucket"``).
        """
        return self.page.locator(self.TOOLKIT_FIELD_INPUT.format(field_key)).input_value()

    def is_save_enabled(self, timeout: int = 5000) -> bool:
        """Return whether the Save button is currently visible and enabled.

        Args:
            timeout: Maximum wait time in milliseconds for Save to appear.
        """
        self.save_button.wait_for(state="visible", timeout=timeout)
        return self.save_button.is_enabled()

    def is_cancel_enabled(self, timeout: int = 5000) -> bool:
        """Return whether the Cancel button is currently visible and enabled.

        Args:
            timeout: Maximum wait time in milliseconds for Cancel to appear.
        """
        self.cancel_button.wait_for(state="visible", timeout=timeout)
        return self.cancel_button.is_enabled()

    # ------------------------------------------------------------------
    # Cancel flow
    # ------------------------------------------------------------------

    @action("Cancel toolkit creation (two-click confirm flow)")
    def cancel_creation(self, timeout: int = 10000) -> None:
        """Click Cancel, wait for the confirm dialog, then click Discard.

        Two-click sequence (confirmed live, ELITEA-1868 AFS): the case
        text's single "Click Cancel" step under-specifies it — the live
        product always shows a "Warning" confirmation dialog first
        (``DiscardButton.jsx`` unconditionally opens it before calling the
        caller's ``onDiscard``).

        Returns nothing — the caller asserts the post-cancel URL via
        ``expect.soft()``: KNOWN DEFECT
        (https://github.com/EliteaAI/elitea-testing-public/issues/655) —
        confirming Discard does NOT navigate back to the Toolkits list, it
        falls back to the type-picker at the same URL instead.

        Args:
            timeout: Maximum wait time in milliseconds for the confirm
                dialog to appear.
        """
        self.cancel_button.click()
        self.cancel_confirm_dialog.wait_for(state="visible", timeout=timeout)
        self.cancel_confirm_button.click()
        logger.info("Confirmed Cancel via the Warning dialog's Discard button")
