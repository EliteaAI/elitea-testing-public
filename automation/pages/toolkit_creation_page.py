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
import re

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

    # Dynamic testid template — a schema-driven CHECKBOX field's actual
    # `<input>` element (e.g. "available_by_mcp"), keyed the same way as
    # :attr:`TOOLKIT_FIELD_INPUT` — same `ToolBaseProperty.jsx` mechanism,
    # checkbox variant. Use THIS ("-checkbox-field") for `.is_checked()`
    # reads, never the sibling "-checkbox" testid, which lands on the
    # outer wrapper `<span>`, not the real `<input>` (same "wrapper vs.
    # actual input" gotcha ELITEA-1824 already documented for a different
    # field). NEW to ELITEA-1866 (the MCP-availability checkbox) — no new
    # template family needed, same shape as ``mcp_form_page.py``'s static
    # per-field "-checkbox-field" testids, templated here since the
    # Artifact form's fields are schema-driven rather than fixed.
    TOOLKIT_FIELD_CHECKBOX_INPUT = '[data-testid="toolkit-field-{}-checkbox-field"]'

    # Dynamic testid template — one MUI Chip per available tool in the
    # CONFIGURATION form's TOOLS section (ToolActionsItems.jsx), keyed by
    # the tool's schema key (e.g. "list_files"). Genuinely fresh surface
    # for ELITEA-1866 (the sibling ELITEA-1868 case never reaches the
    # Save-path form's TOOLS section). Same shape as
    # ``mcp_form_page.py``'s ``TOOL_CHIP_PREFIX`` — this page object's own
    # copy since it has no shared base with that one (own-copy precedent
    # already established by :attr:`TOOLKIT_FIELD_INPUT`'s siblings).
    # State (checkmarked/selected) is a SEPARATE ``data-selected``
    # attribute per ``.agents/testing.md`` § Locator policy's
    # testid=identity / data-*=state ruling — never a state-toggled testid.
    TOOL_CHIP_PREFIX = '[data-testid^="toolkit-tool-chip-"]'

    # Info (i) icon next to the "Bucket *" field's label. Testid added for
    # ELITEA-1866 (a caller-supplied `testId` prop threaded through the
    # shared InfoTooltip.jsx chain, wired only at the Bucket field's call
    # site in ToolBaseProperty.jsx) — the shared component's ambient
    # `data-info-tooltip` boolean attribute is NOT unique (matches 3
    # elements on this form: Pgvector Configuration, Embedding Model, and
    # Bucket each have one).
    bucket_info_icon = LocatorDescriptor(
        testid="toolkit-field-bucket-info-icon",
        description="Info (i) icon next to the Bucket field — hover reveals "
        "the bucket-naming-rules tooltip (KNOWN CLARIFICATION #669: the "
        "case text says 'click', the live product only wires hover/focus)",
    )

    # Bucket-field info tooltip's POPPER CONTENT (not the trigger icon
    # above). Testid added ELITEA-1866 PR #670 review round 1
    # (`EliteaAI/EliteaUI` `automation/testids` commit 0b61e8a2): a new
    # opt-in `contentTestId` prop threaded through the shared InfoTooltip
    # chain (ToolBaseProperty -> StyledInputEnhancer -> InputBase ->
    # InfoLabelWithTooltip -> InfoTooltip), wired ONLY at the Bucket
    # field's call site — the other two InfoTooltip instances on this same
    # form (Pgvector Configuration, Embedding Model) do not pass the prop
    # and remain unaffected (confirmed live: still only 3
    # `data-info-tooltip` icons total, only this one carries the content
    # testid).
    bucket_info_tooltip_content = LocatorDescriptor(
        testid="toolkit-field-bucket-info-tooltip-content",
        description="Bucket-field info tooltip's popper CONTENT wrapper — "
        "read the naming-rules text from here, not from the ambient "
        "[role='tooltip'] landmark",
    )

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

    # Confirmed live (ELITEA-1866 implementer Phase 2 exploration): 12
    # category tabs render as buttons on the type-picker, via the SHARED
    # ``GroupedCategory.jsx``/``Filter.CategoryFilter`` component (also used
    # by the Credential type-picker — confirmed by source read, PR #670
    # review round 1). Generic testid added ELITEA-1866 PR #670 review
    # round 1 (`EliteaAI/EliteaUI` `automation/testids` commit 0b61e8a2) —
    # a single shared value reused across every rendered chip, same reuse
    # pattern as the existing shared ``entity-card`` testid, since this
    # case's own step-6 observable is only "tabs are present" (count >= 1),
    # never per-tab identification.
    CATEGORY_TAB = '[data-testid="category-filter-tab"]'

    def count_category_tabs(self, timeout: int = 5000) -> int:
        """Return how many category filter tabs are currently rendered on the type-picker.

        Args:
            timeout: Maximum wait time in milliseconds for the first tab
                to appear before concluding there are none.
        """
        tabs = self.page.locator(self.CATEGORY_TAB)
        try:
            tabs.first.wait_for(state="visible", timeout=timeout)
        except Exception:
            return 0
        return tabs.count()

    @action("Hover the Bucket field's info icon")
    def hover_bucket_info_icon(self, timeout: int = 5000) -> None:
        """Hover (NOT click) the Bucket field's info icon to reveal its tooltip.

        KNOWN CLARIFICATION #669 — the case text says "click"; the live
        product's ``InfoTooltip.jsx`` has no ``onClick`` handler wired,
        only MUI ``Tooltip``'s default hover/focus trigger (confirmed via
        source read, ELITEA-1866 analyst pass).

        Args:
            timeout: Maximum wait time in milliseconds for the icon to
                become visible before hovering.
        """
        self.bucket_info_icon.wait_for(state="visible", timeout=timeout)
        self.bucket_info_icon.hover()
        logger.info("Hovered the Bucket field's info icon")

    def get_bucket_info_tooltip_text(self, timeout: int = 5000) -> str:
        """Return the currently-open info tooltip's text, whitespace-normalized.

        Reads via :attr:`bucket_info_tooltip_content` (the compliant
        testid on the popper's content wrapper, added ELITEA-1866 PR #670
        review round 1 — see that attribute's docstring for the
        caller-scoped threading rationale), not the ambient
        ``[role="tooltip"]`` landmark.

        Collapses internal whitespace/newlines to single spaces before
        returning — the live tooltip renders its bullet list with line
        breaks the case's own documented text doesn't use; this is a pure
        rendering-whitespace artifact, not a content difference (confirmed
        live, ELITEA-1866 implementer Phase 2 exploration: the normalized
        text matches the case's documented wording exactly).

        Args:
            timeout: Maximum wait time in milliseconds for the tooltip to
                become visible.
        """
        self.bucket_info_tooltip_content.wait_for(state="visible", timeout=timeout)
        raw_text = self.bucket_info_tooltip_content.text_content() or ""
        return " ".join(raw_text.split())

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

    def get_checkbox_field_locator(self, field_key: str):
        """Return the Locator for a dynamic schema-driven checkbox field's real `<input>`.

        Thin wrapper around :attr:`TOOLKIT_FIELD_CHECKBOX_INPUT` — same
        rationale as :meth:`get_field_locator`.

        Args:
            field_key: The field's schema property key (e.g.
                ``"available_by_mcp"``).
        """
        # TEMP FIX: testid doesn't exist yet — fallback to switch element
        # Issue #1575 - the MCP field is actually a SWITCH, not a checkbox
        testid_selector = self.TOOLKIT_FIELD_CHECKBOX_INPUT.format(field_key)
        if self.page.locator(testid_selector).count() > 0:
            return self.page.locator(testid_selector)

        # Fallback for available_by_mcp: it's a switch role, not checkbox
        # Located at bottom of TOOLS accordion with accessible name
        if field_key == "available_by_mcp":
            return self.page.get_by_role("switch", name="Enable MCP access for selected tools")

        # For other fields, try generic fallback
        return self.page.locator(
            '[data-testid="toolkit-tools-accordion"] '
            f'label:has-text("{field_key}") input'
        ).first

    def is_checkbox_field_checked(self, field_key: str, timeout: int = 5000) -> bool:
        """Return whether a dynamic schema-driven checkbox field is currently checked.

        Args:
            field_key: The field's schema property key (e.g.
                ``"available_by_mcp"``).
            timeout: Maximum wait time in milliseconds for the field to
                become visible before reading its state.
        """
        field = self.get_checkbox_field_locator(field_key)
        field.wait_for(state="visible", timeout=timeout)
        return field.is_checked()

    def wait_for_tools_section_loaded(self, timeout: int = 15000):
        """Wait for TOOLS section to render with at least one tool chip.

        Waits for:
        1. At least one tool chip to appear in DOM
        2. Page JavaScript to be fully executed
        3. Network to settle after React hydration

        Args:
            timeout: Maximum wait time in milliseconds.

        Raises:
            TimeoutError: If no tool chips appear within timeout.
        """
        import logging
        logger = logging.getLogger(__name__)

        # Wait for at least one tool chip using JavaScript check
        try:
            self.page.wait_for_function(
                f"document.querySelectorAll('{self.TOOL_CHIP_PREFIX}').length > 0",
                timeout=timeout
            )
            # Additional stabilization after chips appear
            self.page.wait_for_timeout(500)
            logger.info(f"TOOLS section loaded with {self.page.locator(self.TOOL_CHIP_PREFIX).count()} chips")
        except Exception as e:
            logger.error(f"TOOLS section did not load within {timeout}ms: {e}")
            raise

    def count_tool_chips(self, timeout: int = 5000) -> int:
        """Return the number of currently-visible TOOLS-section tool chips.

        Args:
            timeout: Maximum wait time in milliseconds for the first chip
                to appear before concluding there are none.
        """
        import logging
        logger = logging.getLogger(__name__)

        chips = self.page.locator(self.TOOL_CHIP_PREFIX)
        try:
            # Enhanced wait: use JavaScript check for more reliable detection
            self.page.wait_for_function(
                f"document.querySelectorAll('{self.TOOL_CHIP_PREFIX}').length > 0",
                timeout=timeout
            )
            # Additional stabilization wait for dynamic rendering
            self.page.wait_for_timeout(500)
            count = chips.count()
            logger.debug(f"Found {count} tool chips")
            return count
        except Exception as e:
            logger.warning(f"No tool chips found after {timeout}ms: {e}")
            return 0

    def all_tool_chips_selected(self) -> bool:
        """Return whether EVERY currently-rendered tool chip carries ``data-selected="true"``.

        Checks the attribute on every chip individually — a chip present
        but ``data-selected="false"`` would silently pass a naive
        count-only check while still failing the "with checkmarks"
        observable this exists to verify.
        """
        chips = self.page.locator(self.TOOL_CHIP_PREFIX)
        count = chips.count()
        return count > 0 and all(
            chips.nth(i).get_attribute("data-selected") == "true" for i in range(count)
        )

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

    @action("Save toolkit creation and capture the new toolkit ID")
    def save_creation(self, timeout: int = 15000) -> int:
        """Click Save, wait for the post-save detail-page URL, and return the new toolkit's ID.

        Added for ELITEA-1866 — the Save (persist) path, distinct from
        :meth:`cancel_creation`'s Cancel path this page object already
        modelled for the sibling ELITEA-1868 case. Waits for the URL to
        match ``**/toolkits/all/*`` and parses the numeric ID segment out
        of it — needed both by callers asserting the navigation (case
        steps 20/21/23) and by test teardown, which needs the ID for
        ``ToolkitAPI.delete_toolkit(toolkit_id)``.

        Args:
            timeout: Maximum wait time in milliseconds for the post-save URL.

        Returns:
            The new toolkit's numeric ID, parsed from ``/toolkits/all/{id}``.

        Raises:
            ValueError: If the post-save URL doesn't contain a numeric
                toolkit ID (unexpected navigation target).
        """
        self.save_button.click()
        self.page.wait_for_url("**/toolkits/all/*", timeout=timeout)
        match = re.search(r"/toolkits/all/(\d+)", self.page.url)
        if not match:
            raise ValueError(
                f"Could not parse a numeric toolkit ID from the post-save "
                f"URL: {self.page.url!r}"
            )
        toolkit_id = int(match.group(1))
        logger.info("Toolkit saved — new toolkit ID %d (url=%s)", toolkit_id, self.page.url)
        return toolkit_id

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
