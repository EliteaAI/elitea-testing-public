"""Personal Tokens page object (Settings → Personal Tokens).

URL: /settings/tokens

Covers the page layout (header title, search input, add-token button) and the
tokens table (``TokensTable.jsx``, built on the shared ``grid-table``
components) — column headers and each token row's four action icons
(preview/VSCode/JetBrains/delete).

Locator provenance (ELITEA-2277, testid needed for the whole surface — zero
pre-existing testids in the personal-tokes component tree):
``personal-tokens-page-title`` / ``personal-tokens-search-input`` /
``personal-tokens-add-button`` are new caller-supplied testid props threaded
through the shared ``DrawerPageHeader`` (``titleTestId`` prop,
``slotProps.searchInput.testId`` forwarded onto the already-testid-aware
``SimpleSearchBar``, ``slotProps.addButton.testId`` on the add IconButton) —
per ``.agents/testing.md`` "shared components never hardcode feature-scoped
testids", the values are supplied at the ``PersonalTokens.jsx`` call site, not
hardcoded in ``DrawerPageHeader``. ``personal-token-column-header-*`` wires
``GridTableHeader``'s existing ``columnTestIdPrefix`` prop (already accepted,
``TokensTable.jsx`` just didn't pass it). ``token-row`` wires ``GridTableRow``'s
existing ``data-testid`` prop (same "wire an existing prop" pattern as
``NotificationCenterPage.notification_row``). ``token-action-preview-button`` /
``token-action-vscode-button`` / ``token-action-jetbrains-button`` are new
static ``data-testid``s on the three per-row icon elements in
``TokenActionsCell``. ``token-action-delete-button`` wires the shared
``DeleteEntityButton``'s existing ``testId`` prop.
"""

import logging

from playwright.sync_api import Page, expect

from .base_page import BasePage
from .locator_descriptor import LocatorDescriptor

logger = logging.getLogger("elitea.pages.personal_tokens")

UI_ELEMENT_TIMEOUT = 10_000
NAVIGATION_TIMEOUT = 15_000

# Substring shared by the token-list fetch (`useTokenListQuery`) — used to wait
# for the initiating GET to resolve before asserting on the rendered table.
TOKEN_LIST_URL_SUBSTRING = "/auth/token/"

# Route the add-button navigates to (ELITEA-2280) — a dedicated page, NOT an
# inline dialog (confirmed live). Shared with create_personal_token_page.py.
CREATE_PERSONAL_TOKEN_PATH = "/settings/create-personal-token"


class PersonalTokensPage(BasePage):
    """Settings → Personal Tokens page (page layout + tokens table)."""

    page_title = LocatorDescriptor(
        testid="personal-tokens-page-title",
        description='Page header title — exact text "Personal Tokens"',
    )
    search_input = LocatorDescriptor(
        testid="personal-tokens-search-input",
        description='Token search input — placeholder "Search tokens..."',
    )
    add_button = LocatorDescriptor(
        testid="personal-tokens-add-button",
        description="Add-token (+) button, top-right of the header",
    )
    token_row = LocatorDescriptor(
        testid="token-row",
        description="Token table row (repeatable, one per visible row)",
    )
    column_header_name = LocatorDescriptor(
        testid="personal-token-column-header-name",
        description='Table column header — "Token name"',
    )
    column_header_token = LocatorDescriptor(
        testid="personal-token-column-header-token",
        description='Table column header — "Token value"',
    )
    column_header_expires = LocatorDescriptor(
        testid="personal-token-column-header-expires",
        description='Table column header — "Expiration"',
    )
    column_header_actions = LocatorDescriptor(
        testid="personal-token-column-header-actions",
        description='Table column header — "Actions"',
    )
    row_name_cell = LocatorDescriptor(
        testid="token-name-cell",
        description="Token name cell (repeatable, one per visible row) — resolves "
        "every row's name cell in DOM order, so the rendered sort order can be "
        "asserted with an auto-retrying to_have_text(list) assertion.",
    )
    table_empty_message = LocatorDescriptor(
        testid="personal-tokens-table-empty-message",
        description='Grid-table empty message ("No tokens") shown when a search '
        "matches nothing. NOTE: this is the *no-match* branch of the populated "
        "page — the page header, search box and rows container stay mounted. It is "
        "NOT the zero-tokens-exist EmptyStatePage (empty-state-title, "
        '"No tokens yet"), which replaces the whole page.',
    )

    # Delete-confirmation modal (shared DeleteEntityModal.jsx, ELITEA-2280
    # cleanup flow) — testids already exist app-wide (repo precedent: each
    # page object that triggers this shared modal declares its own
    # LocatorDescriptor for it, e.g. mcp_form_page.py / chat_page.py /
    # artifacts_page.py — no new testid work here).
    delete_confirm_dialog = LocatorDescriptor(
        testid="delete-confirm-dialog",
        description="Delete-confirmation modal container (shared DeleteEntityModal).",
    )
    delete_confirm_name_input = LocatorDescriptor(
        testid="delete-confirm-name-input",
        description="Delete dialog's type-to-confirm Name field — resolves to the "
        "MUI TextField wrapper, NOT the real <input> (same shape as "
        "mcp_form_page.py's field); click + press_sequentially() types into "
        "the focused inner input.",
    )
    delete_confirm_button = LocatorDescriptor(
        testid="delete-confirm-button",
        description="Delete dialog's confirm button — disabled until the typed "
        "name matches the entity name exactly.",
    )
    delete_confirm_title = LocatorDescriptor(
        testid="delete-confirm-title",
        description='Delete dialog title — exact text "Delete confirmation" '
        "(shared DeleteEntityModal; testid pre-existing, ELITEA-2281).",
    )
    delete_confirm_message = LocatorDescriptor(
        testid="delete-confirm-message",
        description="Delete dialog body text — "
        '"Are you sure to delete the {name}? Enter the name to complete the action."',
    )
    delete_confirm_cancel_button = LocatorDescriptor(
        testid="delete-confirm-cancel-button",
        description='Delete dialog\'s Cancel button — exact text "Cancel".',
    )

    # ---- IDE Settings Preview pane (eye icon, ELITEA-2291 / ELITEA-2285) ----
    # `SettingsPreview.jsx` had ZERO testids and ZERO accessible names on all
    # three of its header IconButtons (aria-label null on each, confirmed
    # live), so there was no honest non-testid handle for any of them. All
    # seven below were added as pure call-site additions in
    # EliteaAI/EliteaUI@efda0603 — five ride MUI Box/Typography/IconButton prop
    # spread, the select reuses `SingleSelect`'s existing `data-testid` prop
    # (which auto-derives the "-combobox" suffix onto the clickable node,
    # same shape as CreatePersonalTokenPage.expiration_measure_combobox), and
    # the body reuses `Field.CodeMirrorEditor`'s existing `contentTestId` prop
    # (applied straight onto the `.cm-content` node via
    # EditorView.contentAttributes — the merged `toolkit-raw-json-editor-content`
    # precedent, which is why NO #579 raw-handle exception is needed here).
    settings_preview_panel = LocatorDescriptor(
        testid="token-settings-preview-panel",
        description="IDE Settings Preview pane root. NOTE: an in-page "
        "react-split pane, NOT a modal and NOT a route change — the URL stays "
        "/settings/tokens and the tokens table stays mounted beside it.",
    )
    settings_preview_title = LocatorDescriptor(
        testid="token-settings-preview-title",
        description="Preview pane header title — exact text "
        '"{token name} • {IDE} Settings" (U+2022 BULLET, one space either side).',
    )
    settings_preview_close_button = LocatorDescriptor(
        testid="token-settings-preview-close-button",
        description="Preview pane close (X) IconButton. The close is animated "
        "THEN unmounted (sizes -> [100, 0], then a 50 ms setTimeout, "
        "PersonalTokens.jsx:143-149) — always assert the disappearance with an "
        "auto-retrying expectation, never an immediate read.",
    )
    settings_preview_ide_select_combobox = LocatorDescriptor(
        testid="token-settings-preview-ide-select-combobox",
        description="Preview pane IDE-type select's clickable combobox — the "
        "shared SingleSelect auto-derives this '-combobox' suffix from the root "
        "'token-settings-preview-ide-select' testid. Defaults to 'VSCode'.",
    )
    settings_preview_copy_button = LocatorDescriptor(
        testid="token-settings-preview-copy-button",
        description="Preview pane copy IconButton (copies the rendered config "
        "to the clipboard).",
    )
    settings_preview_download_button = LocatorDescriptor(
        testid="token-settings-preview-download-button",
        description="Preview pane download IconButton (downloads the rendered "
        "config as settings.json / elitea.xml).",
    )
    settings_preview_content = LocatorDescriptor(
        testid="token-settings-preview-content",
        description="Preview pane body — the read-only CodeMirror editor's "
        ".cm-content node. Read it with inner_text(), NEVER text_content(): "
        "CodeMirror renders each line as its own <div> and text_content() "
        "concatenates them with no separator, so the result will not parse as "
        "JSON/XML.",
    )

    # Scoped sub-selectors — count/prefix assertions within a parent testid,
    # per .agents/testing.md § Locator policy (UPPER_CASE class constants).
    COLUMN_HEADER_PREFIX_SELECTOR = '[data-testid^="personal-token-column-header-"]'
    TOKEN_ACTION_PREFIX_SELECTOR = '[data-testid^="token-action-"]'
    # Named-testid template — scoped lookup of a single action icon within an
    # already-testid-scoped row (the ``{}`` parameter is the exact testid, not
    # data-derived; kept as a class-level template per the same "pattern stays
    # in the inventory" rationale as a runtime-parameterized testid).
    TOKEN_ACTION_ICON_SELECTOR = '[data-testid="{}"]'
    # Row cell-content selectors (ELITEA-2280) — static per-row testids,
    # scoped by chaining off an already-testid-scoped row locator (same
    # sanctioned pattern as TOKEN_ACTION_ICON_SELECTOR / get_first_row_action_icon).
    TOKEN_NAME_CELL_SELECTOR = '[data-testid="token-name-cell"]'
    TOKEN_VALUE_CELL_SELECTOR = '[data-testid="token-value-cell"]'
    # State via data-* attribute on a stable testid (not a state-switched
    # testid) — per .agents/testing.md "Testid = stable identity" ruling.
    # The ``{}`` parameter is the exact ``data-expiration-state`` value
    # (active|warning|never|expired), not test-generated data.
    TOKEN_EXPIRATION_STATUS_SELECTOR = '[data-testid="token-expiration-status"][data-expiration-state="{}"]'
    # State-AGNOSTIC sibling of the above (ELITEA-2279): the state-filtered
    # selector can only answer "is this row in state X?", never "what state is
    # this row in?" — which is what an expiration *sort* assertion needs.
    TOKEN_EXPIRATION_STATUS_ANY_SELECTOR = '[data-testid="token-expiration-status"]'
    # Sort controls — emitted by GridTableHeader's columnTestIdPrefix for
    # sortable columns ONLY (ELITEA-2279). The prefix form counts them; the
    # named form addresses one column (the ``{}`` parameter is the column
    # field name from TOKENS_COLUMNS, not test-generated data).
    SORT_ICON_PREFIX_SELECTOR = '[data-testid^="personal-token-sort-icon-"]'
    SORT_ICON_SELECTOR = '[data-testid="personal-token-sort-icon-{}"]'

    def __init__(self, page: Page):
        super().__init__(page)

    def _is_token_list_response(self, response) -> bool:
        """True for the token-list GET (`useTokenListQuery`)."""
        return (
            TOKEN_LIST_URL_SUBSTRING in response.url
            and response.request.method == "GET"
        )

    def navigate(self) -> None:
        """Navigate to /settings/tokens and wait for the first token row to
        become visible.

        Waiting on the row (not just DOM visibility of the page shell)
        matters here: the page renders a loading spinner, then either the
        populated table or an `EmptyStatePage` ("No tokens yet") depending on
        whether the project has any tokens — this confirms the populated
        path was reached, per the AFS's precondition proof (step 1).
        """
        with self.page.expect_response(
            self._is_token_list_response, timeout=NAVIGATION_TIMEOUT
        ):
            super().navigate("/settings/tokens")
        self.token_row.first.wait_for(state="visible", timeout=UI_ELEMENT_TIMEOUT)

    def get_column_header_count(self) -> int:
        """Return the number of rendered table column-header elements
        (matched by the shared ``personal-token-column-header-`` prefix)."""
        return self.page.locator(self.COLUMN_HEADER_PREFIX_SELECTOR).count()

    def get_first_row_action_icon_count(self) -> int:
        """Return the number of action-icon elements in the FIRST token row's
        Actions cell (matched by the shared ``token-action-`` prefix, scoped
        to that row — sanctioned chaining off an already-testid-scoped
        element, per .agents/testing.md § Locator policy)."""
        first_row = self.token_row.first
        return first_row.locator(self.TOKEN_ACTION_PREFIX_SELECTOR).count()

    def get_first_row_action_icon(self, testid: str):
        """Return the Locator for a single named action icon within the
        FIRST token row, scoped to that row (same chaining rationale as
        :meth:`get_first_row_action_icon_count`)."""
        first_row = self.token_row.first
        return first_row.locator(self.TOKEN_ACTION_ICON_SELECTOR.format(testid))

    def click_add_button(self) -> None:
        """Click the add-token ("+") button and wait for the resulting
        navigation to the "New Token" create-flow page.

        The add-button does NOT open an inline dialog — confirmed live
        (ELITEA-2280 AFS) — it navigates to a separate route,
        ``/settings/create-personal-token``. This waits for that URL change
        rather than any in-page dialog.
        """
        self.add_button.click()
        self.page.wait_for_url(
            f"**{CREATE_PERSONAL_TOKEN_PATH}", timeout=NAVIGATION_TIMEOUT
        )

    def get_row_by_name(self, name: str):
        """Return the token row Locator filtered by exact row text match on
        *name* (sanctioned chaining off the already-testid-scoped
        :attr:`token_row`, same pattern as :meth:`get_first_row_action_icon`)."""
        return self.token_row.filter(has_text=name)

    def get_row_name_cell(self, row):
        """Return the name-cell Locator scoped within *row* (a Locator
        returned by :meth:`get_row_by_name`)."""
        return row.locator(self.TOKEN_NAME_CELL_SELECTOR)

    def get_row_value_cell(self, row):
        """Return the masked-value-cell Locator scoped within *row*."""
        return row.locator(self.TOKEN_VALUE_CELL_SELECTOR)

    def get_row_expiration_status(self, row, state: str = "active"):
        """Return the expiration-status Locator scoped within *row*, filtered
        to the given ``data-expiration-state`` value (state via data-*
        attribute on a stable testid, not a state-switched testid — see
        :attr:`TOKEN_EXPIRATION_STATUS_SELECTOR`)."""
        return row.locator(self.TOKEN_EXPIRATION_STATUS_SELECTOR.format(state))

    def get_row_action_icon(self, row, testid: str):
        """Return the Locator for a single named action icon within an
        arbitrary *row* (not necessarily the first row) — generalizes
        :meth:`get_first_row_action_icon` for a row located by
        :meth:`get_row_by_name`."""
        return row.locator(self.TOKEN_ACTION_ICON_SELECTOR.format(testid))

    def get_column_header(self, field: str):
        """Return the column-header Locator for *field* (one of the four
        ``TOKENS_COLUMNS`` fields: ``name`` / ``token`` / ``expires`` /
        ``actions``)."""
        headers = {
            "name": self.column_header_name,
            "token": self.column_header_token,
            "expires": self.column_header_expires,
            "actions": self.column_header_actions,
        }
        try:
            return headers[field]
        except KeyError as exc:
            raise ValueError(
                f"Unknown column field {field!r}; expected one of {sorted(headers)}"
            ) from exc

    def click_column_header(self, field: str) -> None:
        """Click the *field* column header to toggle its sort.

        The whole header cell carries the ``onClick`` (``GridTableHeader.jsx``),
        so the header itself is the control — there is no separate button.
        Sorting is CLIENT-SIDE (the list is already in the RTK-Query cache), so
        no request fires: callers wait on the reordered DOM, never on a
        response.
        """
        self.get_column_header(field).click()

    def get_sort_icon_count(self) -> int:
        """Return the number of rendered sort controls across all columns
        (matched by the shared ``personal-token-sort-icon-`` prefix)."""
        return self.page.locator(self.SORT_ICON_PREFIX_SELECTOR).count()

    def get_sort_icon(self, field: str):
        """Return the sort-control Locator for *field*'s column header.

        Only sortable columns render one, so this is also the handle for the
        ABSENCE assertion on the non-sortable columns.
        """
        return self.page.locator(self.SORT_ICON_SELECTOR.format(field))

    def get_row_names(self) -> list[str]:
        """Return every visible row's token name, in rendered DOM order."""
        return [
            (cell.text_content() or "").strip()
            for cell in self.row_name_cell.all()
        ]

    def get_row_expiration_states(self) -> list[str]:
        """Return every visible row's ``data-expiration-state`` value
        (``active``/``warning``/``never``/``expired``), in rendered DOM order.

        Uses the state-agnostic selector — see
        :attr:`TOKEN_EXPIRATION_STATUS_ANY_SELECTOR`.
        """
        return [
            row.locator(self.TOKEN_EXPIRATION_STATUS_ANY_SELECTOR).get_attribute(
                "data-expiration-state"
            )
            for row in self.token_row.all()
        ]

    def get_first_row_expiration_status(self, state: str):
        """Return the FIRST row's expiration-status Locator filtered to
        *state* — the anchor an expiration-sort assertion waits on
        (``to_have_count`` auto-retries until the re-render lands)."""
        return self.get_row_expiration_status(self.token_row.first, state=state)

    def type_search(self, text: str) -> None:
        """Type *text* into the token search box one character at a time.

        ``SimpleSearchBar`` filters from the native ``onChange`` — per
        keystroke, no Enter, no submit control, no debounce — so
        ``press_sequentially`` is what actually exercises the "real time"
        claim. Never press Enter here.
        """
        self.search_input.click()
        self.search_input.press_sequentially(text, delay=30)

    def clear_search(self) -> None:
        """Clear the token search box via select-all + Backspace.

        ``SimpleSearchBar`` is a plain MUI ``InputBase`` with no ``useAutoBlur``
        wrapper, so ``ControlOrMeta+a`` is reliable here — unlike the
        create-token Name field, whose refocus cycle races the shortcut
        (surface digest § Name-field client-side validation).
        """
        self.search_input.click()
        self.search_input.press("ControlOrMeta+a")
        self.search_input.press("Backspace")

    def get_search_value(self) -> str:
        """Return the current value of the token search box.

        The testid resolves to the native ``<input>`` (wired through
        ``SimpleSearchBar``'s ``inputProps``), so ``input_value()`` works
        directly — unlike the delete dialog's MUI-wrapper field on this page.
        """
        return self.search_input.input_value()

    def fill_delete_confirm_name(self, name: str) -> None:
        """Type *name* into the delete-confirmation dialog's type-to-confirm
        Name field and wait for the Delete button to become enabled.

        Same click + press_sequentially shape as ``mcp_form_page.py``'s
        ``fill_delete_confirm_name`` — MUI needs keyboard events for React
        onChange (``.claude/rules/mui-patterns.md``), and waiting on the
        button's enabled state is the real signal the typed value propagated,
        rather than a fixed delay.
        """
        self.delete_confirm_name_input.click()
        self.delete_confirm_name_input.press_sequentially(name, delay=20)
        expect(self.delete_confirm_button).to_be_enabled(timeout=UI_ELEMENT_TIMEOUT)

    def type_delete_confirm_name(self, text: str, click_first: bool = True) -> None:
        """Type *text* into the delete dialog's type-to-confirm Name field
        WITHOUT asserting the Delete button's resulting state.

        The sibling of :meth:`fill_delete_confirm_name` for the negative half
        of the exact-match gate (ELITEA-2281 step 5): typing a PREFIX must
        leave Delete disabled, so a helper that waits for "enabled" cannot be
        used there. Pass ``click_first=False`` to continue typing into the
        already-focused field without moving the caret (a second click could
        land mid-string and interleave the characters).
        """
        if click_first:
            self.delete_confirm_name_input.click()
        self.delete_confirm_name_input.press_sequentially(text, delay=20)

    def confirm_delete(self) -> None:
        """Click the delete-confirmation dialog's Delete button."""
        self.delete_confirm_button.click()

    def _is_token_delete_response(self, response) -> bool:
        """True for a token DELETE (`useTokenDeleteMutation`, by uuid)."""
        return (
            TOKEN_LIST_URL_SUBSTRING in response.url
            and response.request.method == "DELETE"
        )

    def confirm_delete_and_wait_for_response(self, timeout: int = NAVIGATION_TIMEOUT):
        """Click Delete and return the Playwright ``Response`` for the
        ``DELETE /auth/token/{uuid}`` it fires (204, empty body — never call
        ``.json()`` on it).

        The side-channel proof that the deletion reached the backend, rather
        than a row vanishing client-side (ELITEA-2281 step 5).
        """
        with self.page.expect_response(
            self._is_token_delete_response, timeout=timeout
        ) as resp_info:
            self.confirm_delete()
        return resp_info.value

    def reload_and_wait_for_tokens(self, timeout: int = NAVIGATION_TIMEOUT):
        """Reload /settings/tokens and return the ``Response`` for the token
        list GET the reload triggers.

        Waits for the first row to become visible afterwards — the page shows
        a ``CircularProgress`` for ~2-2.5 s on every load, so a bare read
        straight after the reload sees no rows (surface digest § Mount
        timing). Returning the response lets a caller assert against the API
        payload itself, independent of the DOM (ELITEA-2281 step 7).
        """
        with self.page.expect_response(
            self._is_token_list_response, timeout=timeout
        ) as resp_info:
            self.page.reload()
        self.token_row.first.wait_for(state="visible", timeout=UI_ELEMENT_TIMEOUT)
        return resp_info.value

    def open_settings_preview(self, row, timeout: int = UI_ELEMENT_TIMEOUT) -> None:
        """Click *row*'s eye icon and wait for the IDE Settings Preview pane.

        Waits on the pane's own root becoming visible — the eye icon only
        flips React state and resizes the ``react-split`` panes
        (``PersonalTokens.jsx:133-141``); no request fires, so there is
        nothing to await on the network and no reason to sleep.
        """
        self.get_row_action_icon(row, "token-action-preview-button").click()
        self.settings_preview_panel.wait_for(state="visible", timeout=timeout)

    def close_settings_preview(self, timeout: int = UI_ELEMENT_TIMEOUT) -> None:
        """Close the IDE Settings Preview pane and wait for it to unmount.

        The close is animated THEN unmounted (a 50 ms ``setTimeout`` after the
        pane resize), so this asserts the disappearance with an auto-retrying
        expectation rather than reading immediately.
        """
        self.settings_preview_close_button.click()
        expect(self.settings_preview_panel).to_have_count(0, timeout=timeout)

    def get_settings_preview_body(self) -> str:
        """Return the Settings Preview pane's rendered config text.

        Uses ``inner_text()`` deliberately — see
        :attr:`settings_preview_content`.
        """
        return self.settings_preview_content.inner_text()

    def download_ide_settings(self, row, icon_testid: str, timeout: int):
        """Click *row*'s named IDE-config download icon and return the
        Playwright ``Download``.

        *icon_testid* is the caller's parameter (``token-action-vscode-button``
        / ``token-action-jetbrains-button``), never a hardcoded locator here —
        both icons call the same ``onIdeSettingsDownload`` handler.

        The handler builds the file content as a string, wraps it in a
        ``Blob`` and clicks a synthesized ``<a download>`` — a **pure
        client-side download, no request fires**. ``expect_download`` IS the
        wait; there is no response to await.
        """
        with self.page.expect_download(timeout=timeout) as download_info:
            self.get_row_action_icon(row, icon_testid).click()
        return download_info.value
