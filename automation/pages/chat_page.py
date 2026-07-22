"""Chat page object for Elitea chat interface.

Provides locators and methods for interacting with chat conversations,
message input, participants, and chat settings.
"""

import logging
import re
import time
from playwright.sync_api import Page
from .base_page import BasePage
from .locator_descriptor import LocatorDescriptor, OptionalLocatorDescriptor
from components.mui import Dialog, Popper
from utils.actions import action
from config import settings

logger = logging.getLogger("elitea.pages.chat")


class FeatureNotAvailableError(Exception):
    """Raised when a UI feature is not available in the current UI version."""
    pass


class ChatPage(BasePage):
    """Page object for Elitea chat interface (/chat).

    Handles:
    - Message sending and history
    - Model selection
    - Chat settings and context
    - Sidebar navigation
    - File attachments
    - Message actions (copy, delete, regenerate)

    URL: /chat, /chat/{conversation_id}
    """

    # ------------------------------------------------------------------
    # Message input area
    # ------------------------------------------------------------------

    message_input = LocatorDescriptor(
        testid="chat-message-input",
        fallback=lambda page: page.locator('textarea#standard-multiline-static'),
        description="Main message input textarea. Uses stable ID #standard-multiline-static"
    )

    send_button = LocatorDescriptor(
        testid="chat-send-button",
        fallback=lambda page: page.get_by_role("button", name="send your question"),
        description="Send message button"
    )

    attach_files_button = LocatorDescriptor(
        testid="chat-attach-button",
        fallback=lambda page: page.get_by_role("button", name="attach files"),
        description="Attach files button"
    )

    # ------------------------------------------------------------------
    # Sidebar / drawer
    # ------------------------------------------------------------------

    sidebar_toggle = LocatorDescriptor(
        testid="sidebar-toggle",
        fallback=lambda page: page.get_by_role("button", name="open drawer"),
        description="Sidebar toggle button"
    )

    create_conversation_button = LocatorDescriptor(
        testid="sidebar-create-button",
        description=(
            "+Chat / +Conversation button in the top sidebar nav. Disabled while "
            "a new blank conversation is open and unsent; re-enables immediately "
            "on Send. (ELITEA-2090)"
        ),
    )

    search_conversations_input = LocatorDescriptor(
        testid="conversation-search-input",
        fallback=lambda page: page.locator('input[placeholder="Search conversations..."]'),
        description="Search conversations input field in sidebar"
    )

    # ------------------------------------------------------------------
    # Project selector (ELITEA-2095)
    # ------------------------------------------------------------------
    # The role=combobox trigger showing "Project: {name}" in the sidebar.
    # Realized as ``project-selector-trigger-combobox`` on the actual
    # interactive node: SidebarProjectSelect.jsx wires a base
    # data-testid="project-selector-trigger" onto its shared ProjectSelect ->
    # SingleSelect component, which auto-suffixes "-combobox" onto the
    # role=combobox node via SelectDisplayProps (SingleSelect.jsx's existing,
    # pre-established convention — declared improvisation, see PR description
    # for ELITEA-2095: no sanctioned shape for a bare, non-suffixed trigger
    # testid on this shared component).
    project_selector_trigger = LocatorDescriptor(
        testid="project-selector-trigger-combobox",
        description=(
            "Sidebar project selector combobox trigger. Click opens the "
            "project dropdown; options resolve via the dynamic "
            "SELECT_OPTION template (same shared SingleSelectMenuItem family "
            "as AgentDetailPage.FORK_PROJECT_OPTION)."
        ),
    )

    # Project-selector dropdown options — same shared select-option-{value}
    # family (SingleSelectMenuItem.jsx) as AgentDetailPage.FORK_PROJECT_OPTION
    # — reuse the pattern, don't invent a new one.
    SELECT_OPTION = '[data-testid="select-option-{}"]'

    # ------------------------------------------------------------------
    # Model selector
    # ------------------------------------------------------------------

    model_selector = LocatorDescriptor(
        testid="model-selector-button",
        fallback=lambda page: page.locator('[class*="model"], button:has-text("GPT"), button:has-text("Claude")'),
        description="Model selector dropdown button"
    )

    # ------------------------------------------------------------------
    # Chat actions
    # ------------------------------------------------------------------

    # ------------------------------------------------------------------
    # Context Budget panel (right sidebar, visible after first message)
    # LOCATOR NOTE: The panel has no data-testid. Located by its heading
    # text "Context Budget" which is stable in the DOM structure:
    #   generic > generic > "Context Budget" + info icon
    #             generic > "22 / 64 000 tokens" + percentage
    #             generic > Strategy / Messages / Summaries rows
    # ------------------------------------------------------------------

    context_budget_panel = LocatorDescriptor(
        testid="context-budget-panel",
        fallback=lambda page: page.locator('main').get_by_text("Context Budget").locator("xpath=ancestor::div[2]"),
        description=(
            "Context Budget panel in the right sidebar. "
            "Appears only after at least one message has been sent."
        ),
    )

    context_budget_tokens_display = LocatorDescriptor(
        testid="context-budget-tokens",
        fallback=lambda page: page.locator('main').get_by_text("Context Budget").locator("xpath=ancestor::div[3]").locator("div").nth(1),
        description=(
            "Token usage display inside Context Budget panel. "
            "Shows text like '22 / 64 000 tokens'."
        ),
    )

    context_budget_messages_count = LocatorDescriptor(
        testid="context-budget-messages-count",
        description="Messages counter value inside the Context Budget panel (e.g. '4').",
    )

    context_budget_summaries_count = LocatorDescriptor(
        testid="context-budget-summaries-count",
        description="Summaries counter value inside the Context Budget panel (e.g. '0').",
    )

    edit_context_button = LocatorDescriptor(
        testid="context-settings-button",
        fallback=lambda page: page.get_by_role("button", name="Edit context settings"),
        description="Edit context settings button in the right panel Context Budget section"
    )

    plus_menu_button = LocatorDescriptor(
        testid="plus-menu-button",
        fallback=lambda page: page.get_by_role("button", name="plus menu"),
        description="Plus menu button - entry point for adding participants, internal tools, and attachments"
    )

    internal_tools_menuitem = LocatorDescriptor(
        locator='[role="menuitem"]:has-text("Modules")',
        description="Modules menuitem inside plus menu dropdown (formerly Internal Tools)"
    )

    # Legacy locator - kept for backward compatibility but no longer works
    internal_tools_toggle = LocatorDescriptor(
        testid="internal-tools-toggle",
        fallback=lambda page: page.locator('button[aria-label="enable internal tools"]'),
        description="DEPRECATED: Internal tools toggle button (moved to plus menu in v2.0.3)"
    )

    # ------------------------------------------------------------------
    # Message actions
    # ------------------------------------------------------------------

    copy_message_button = LocatorDescriptor(
        testid="message-copy-button",
        fallback=lambda page: page.locator('button[aria-label="Copy to clipboard"]'),
        description="Copy message to clipboard button"
    )

    regenerate_button = LocatorDescriptor(
        testid="message-regenerate-button",
        fallback=lambda page: page.get_by_role("button", name="Regenerate"),
        description="Regenerate AI response button"
    )

    # ------------------------------------------------------------------
    # Voice / TTS Controls
    # ------------------------------------------------------------------
    # VoiceMiniPlayer appears in chat only when Read-out and Voice mode
    # features are activated. By default it should NOT be visible.

    voice_mini_player = OptionalLocatorDescriptor(
        testid="chat-voice-mini-player",
        description="Voice mini player container. Only visible when voice features activated."
    )

    voice_play_stop_button = LocatorDescriptor(
        testid="chat-voice-play-stop-button",
        description="Play/Stop button in voice mini player"
    )

    voice_settings_button = LocatorDescriptor(
        testid="chat-voice-settings-button",
        description="Voice settings button in voice mini player"
    )

    read_out_button = LocatorDescriptor(
        testid="chat-read-out-button",
        description="Read out (speaker) button on AI messages to start TTS"
    )

    # ------------------------------------------------------------------
    # Messages
    # ------------------------------------------------------------------
    # The chat UI renders all messages (user + AI) as
    # <li class="MuiListItem-root"> inside a <ul class="MuiList-root">.
    # This is consistent across regular chat, agent-participant chat,
    # and embedded chat.

    messages_list = LocatorDescriptor(
        testid="chat-message-list",
        fallback=lambda page: page.locator('main'),
        description="Main messages list container"
    )

    messages_container = LocatorDescriptor(
        testid="chat-message-item",
        fallback=lambda page: page.locator('main ul.MuiList-root > li.MuiListItem-root'),
        description="Individual message items (user + AI)"
    )

    # The actual overflow-y:scroll SimpleBar content-wrapper wrapping
    # chat-message-list (confirmed live: sits 2 DOM levels above the
    # chat-message-list <ul>). Use to assert genuine scrollability
    # (scrollHeight > clientHeight) and to drive a real scroll interaction —
    # a CSS-overflow check alone doesn't prove a user can actually scroll.
    chat_messages_scroll_container = LocatorDescriptor(
        testid="chat-messages-scroll-container",
        description="Scrollable messages region (SimpleBar content-wrapper).",
    )

    # ------------------------------------------------------------------
    # Active participant / skill-mention popper (ELITEA-1736 testid rework)
    # ------------------------------------------------------------------

    switch_participant_button = LocatorDescriptor(
        testid="chat-switch-participant-button",
        description=(
            "Composer's active-participant button (was 'Switch Agent'/"
            "'Switch Pipeline' Tooltip-derived accessible name). Shown once"
            " an agent or pipeline is added as a chat participant."
        )
    )

    mention_skill_list = LocatorDescriptor(
        testid="skill-mention-list",
        description="Container for the '~mention' skill autocomplete popper's item list"
    )

    # Dynamic per-row testid for a skill in the mention popper — templated,
    # never an inline f-string get_by_test_id (.claude/rules/page-objects.md).
    MENTION_SKILL_ITEM = '[data-testid="skill-mention-item-{}"]'

    # ------------------------------------------------------------------
    # Participant removal + "Mention skill" popper testid rework
    # (ELITEA-1793 framework-alignment rework, issue #35 — closes PR #52's
    # raw text/aria-label/xpath-ancestor/role-based handle gap; EliteaUI
    # draft PR EliteaAI/EliteaUI#548, commits ab81f3b/be48cd5 on
    # automation/testids)
    # ------------------------------------------------------------------

    # Empty-state row inside the mention popper ("No skills attached to
    # this agent") — scoped sub-selector, resolved against
    # ``self.mention_skill_list``, never a page-level field.
    MENTION_LIST_EMPTY = '[data-testid="skill-mention-list-empty"]'

    # Prefix-match selector enumerating every mention-item row regardless
    # of skill name — used by ``is_skill_in_mention_popper()`` to fall back
    # to a substring (e.g. description) search across all rows.
    MENTION_SKILL_ITEM_PREFIX = '[data-testid^="skill-mention-item-"]'

    # "Agents in this conversation" collapsed-participants badge — dynamic
    # per entity section (this case only ever calls ``.format("agents")``).
    PARTICIPANTS_BADGE = '[data-testid="chat-participants-badge-{}"]'

    # The badge's clickable trigger IconButton — static, but only ever
    # resolved scoped under a ``PARTICIPANTS_BADGE`` container (multiple
    # sections can render simultaneously, each with its own trigger).
    # Declared improvisation: the AFS specced a testid for the wrapping Box
    # only; this button is the actual click target and has no accessible
    # name, so a second testid was added to keep the click testid-only
    # (see .agents/role-overrides.md's canon-gap protocol).
    PARTICIPANTS_BADGE_BUTTON = '[data-testid="chat-participants-badge-button"]'

    participants_popper = LocatorDescriptor(
        testid="chat-participants-popper",
        description="'Agents'/'Pipelines'/etc. participants popper container (Popper/Grow Paper)"
    )

    # Dynamic per-participant row inside the participants popper —
    # uniqueId = getChatParticipantUniqueId(participant), e.g.
    # "application_4687_399" for an agent participant.
    PARTICIPANT_ROW = '[data-testid="chat-participant-row-{}"]'

    # Hover-reveal "Remove <entityType>" icon button — static, scoped via
    # the row's dynamic testid (multiple simultaneous rows disambiguate
    # through the parent row selector, not this button's own testid).
    PARTICIPANT_REMOVE_BUTTON = '[data-testid="chat-participant-remove-button"]'

    # ------------------------------------------------------------------
    # Users participant type (ELITEA-2095) — independent of the Agent/
    # Pipeline/Toolkit/MCP participant work above (different participant
    # type: "Users", the conversation's own members). The collapsed
    # "Users in this conversation" badge reuses the EXISTING
    # PARTICIPANTS_BADGE template (.format("users")) — no new template
    # needed there; is_participants_badge_visible(section="users") /
    # open_participants_popover(section="users") already work as-is.
    # ------------------------------------------------------------------

    participants_users_avatar = LocatorDescriptor(
        testid="chat-participants-users-avatar",
        description=(
            "Avatar in the expanded PARTICIPANTS panel's USERS section, "
            "showing the participant's initials/name (e.g. 'TB')."
        ),
    )

    # Conversation date-group heading container ("today"/"this_week"/
    # "older") — scopes BOTH the group's header text AND that group's own
    # conversation items (DateGroup.jsx renders header + Collapse'd items
    # in one outer element). The reliable way to assert "conversation X is
    # under Today specifically" — replaces the raw ``:has(h6) > button``
    # CSS in get_conversation_list_items() (tracked tech debt,
    # role-overrides.md) for Today-scoping.
    CONVERSATION_GROUP_HEADER = '[data-testid="chat-conversation-group-header-{}"]'

    # Individual conversation list item — dynamic per conversation id.
    CONVERSATION_ITEM = '[data-testid="chat-conversation-item-{}"]'

    # Prefix-match selector enumerating every conversation item regardless of
    # id — same pattern as MENTION_SKILL_ITEM_PREFIX above. Used to find "any
    # OTHER conversation" to navigate to.
    CONVERSATION_ITEM_PREFIX = '[data-testid^="chat-conversation-item-"]'

    # ------------------------------------------------------------------
    # Conversation context menu (three-dot) + delete-confirmation dialog
    # (ELITEA-2114)
    # ------------------------------------------------------------------

    # The 3-dot menu button's testid ("conversation-menu-menu-button") is
    # NOT globally unique — ConversationItem.jsx passes the same static
    # id="conversation-menu" to every DotMenu instance, so an unscoped
    # query resolves to N elements once N conversations are on screen
    # (confirmed live: "strict mode violation ... resolved to 2 elements").
    # Always resolve it scoped inside a CONVERSATION_ITEM container — see
    # get_conversation_menu_button().
    CONVERSATION_MENU_BUTTON = '[data-testid="conversation-menu-menu-button"]'

    # Context-menu item template — {} is one of CONVERSATION_MENU_ITEM_KEYS.
    # Only the currently-open conversation's own MUI Menu is mounted in the
    # DOM (menus unmount their content while closed), so — unlike the menu
    # button above — this does not need per-conversation scoping.
    CONVERSATION_MENU_ITEM = '[data-testid="chat-conversation-menu-{}-menuitem"]'

    # Prefix-match selector enumerating every menu item currently rendered
    # (i.e. belonging to whichever conversation's menu is open) — used to
    # assert the total item count, catching unexpected extra/missing items.
    CONVERSATION_MENU_ITEM_PREFIX = '[data-testid^="chat-conversation-menu-"][data-testid$="-menuitem"]'

    # The 7 stable menu-item keys wired in ConversationItem.jsx's menuItems
    # array. "pin" covers both the "Pin on top" and "Unpin" labels — one
    # stable testid, state carried by the label text (not a second testid),
    # per the testid=identity/state=data-* ruling.
    CONVERSATION_MENU_ITEM_KEYS = (
        "rename", "move-to", "playback", "make-public", "share", "pin", "delete",
    )

    # Delete-confirmation dialog (DeleteEntityModal.jsx, rendered via the
    # shared BaseModal.jsx). Same testids as artifacts_page.py /
    # mcp_form_page.py's own delete_confirm_* fields — this is a shared
    # component reused across pages, each page object declares its own
    # LocatorDescriptor for it (existing repo precedent).
    delete_confirm_dialog = LocatorDescriptor(
        testid="delete-confirm-dialog",
        description="Delete-confirmation modal container (shared DeleteEntityModal).",
    )

    delete_confirm_title = LocatorDescriptor(
        testid="delete-confirm-title",
        description=(
            "Delete-confirmation modal title (BaseModal.jsx DialogTitle "
            "wrapper, ELITEA-2114). A fresh, correct handle — does NOT "
            "depend on the broken id=\"alert-dialog-title\" wiring (BUG #694)."
        ),
    )

    delete_confirm_message = LocatorDescriptor(
        testid="delete-confirm-message",
        description="Delete-confirmation modal body text.",
    )

    delete_confirm_cancel_button = LocatorDescriptor(
        testid="delete-confirm-cancel-button",
        description="Cancel button inside the delete-confirmation modal (ELITEA-2114).",
    )

    delete_confirm_button = LocatorDescriptor(
        testid="delete-confirm-button",
        description="Delete (confirm) button inside the delete-confirmation modal.",
    )

    # ------------------------------------------------------------------
    # Chat folders — creation via CHATS header icon (ELITEA-2132)
    # ------------------------------------------------------------------
    # All handles below carry testids added directly to EliteaUI during the
    # analyst pass for this case (commit 6fceb3e2 on automation/testids) —
    # the whole "Folders" feature area had zero data-testid coverage before
    # this. Reuses CONVERSATION_MENU_BUTTON (the shared, non-unique DotMenu
    # button testid, scoped inside FOLDER_ITEM) for the folder dot-menu —
    # FolderAccordion.jsx wires the same DotMenu id="conversation-menu" as
    # ConversationItem.jsx.

    conversations_panel_heading = LocatorDescriptor(
        testid="chat-conversations-heading",
        description=(
            "'Chats' heading in the CHATS panel header (Conversations.jsx). "
            "ADDED this implementation — used as step-1 proof the CHATS "
            "panel itself is displayed."
        ),
    )

    create_folder_button = LocatorDescriptor(
        testid="chat-create-folder-button",
        description=(
            "CHATS panel header 'Create folder' icon, positioned immediately "
            "before the search button. Conversations.jsx renders this in two "
            "mutually-exclusive branches (expanded/collapsed sidebar) with "
            "the same testid — only one branch is ever mounted at a time."
        ),
    )

    search_conversations_button = LocatorDescriptor(
        testid="conversation-search-button",
        description=(
            "Search-conversations icon button (ConversationSearchButton.jsx) "
            "— pre-existing testid (not added this implementation), used as "
            "the positional anchor for the folder-creation icon's step-2 "
            "'immediately before the search icon' check. Distinct from "
            "search_conversations_input, which is the search text field."
        ),
    )

    folder_name_input = LocatorDescriptor(
        testid="chat-folder-name-input",
        description=(
            "Inline folder-name editor input (FolderItem.jsx) — shared "
            "between the create-new-folder and rename-existing-folder "
            "flows. Only one folder can be in edit mode at a time, so no "
            "scoping is needed."
        ),
    )

    folder_name_confirm_button = LocatorDescriptor(
        testid="chat-folder-name-confirm-button",
        description="Checkmark (confirm) icon next to the folder-name editor input.",
    )

    folder_name_cancel_button = LocatorDescriptor(
        testid="chat-folder-name-cancel-button",
        description="X (cancel) icon next to the folder-name editor input.",
    )

    # Folder item row (whole accordion) — dynamic per folder id. Carries
    # data-expanded="true"/"false" on the SAME element (testid = stable
    # identity, state via data-* attribute — PR #581 ruling), scoping BOTH
    # the header (icon/name/expand-arrow/dot-menu) AND the body (empty
    # state / conversation list) as descendants.
    FOLDER_ITEM = '[data-testid="chat-folder-item-{}"]'

    # Scoped sub-selectors — non-unique across simultaneously-rendered
    # folders, ALWAYS resolved via .locator() on a FOLDER_ITEM-scoped
    # element, never at page level.
    FOLDER_ICON = '[data-testid="chat-folder-icon"]'
    FOLDER_EXPAND_ICON = '[data-testid="chat-folder-expand-icon"]'
    FOLDER_EMPTY_STATE = '[data-testid="chat-folder-empty-state"]'

    # Folder dot-menu "Delete" item — ADDED this implementation
    # (FolderItem.jsx's menuItems had no `key`, so DotMenu/BasicMenuItem
    # never emitted a data-testid for them; ConversationItem.jsx's sibling
    # items already follow this exact key -> "{key}-menuitem" convention —
    # mirrored here as a one-line addition, EliteaUI
    # src/[fsd]/features/chat/conversation-list/ui/folders/FolderItem.jsx).
    # Only "delete" was keyed — Rename/Pin are untouched by this case's own
    # test, per the team's testid-scope ruling (testids go only on elements
    # a test actually touches).
    FOLDER_MENU_DELETE_ITEM = '[data-testid="chat-folder-menu-delete-menuitem"]'

    def __init__(self, page: Page):
        super().__init__(page)
        
    @action("Navigate to chat")
    def navigate_to_chat(self, conversation_id: str = None):
        """Navigate to chat page and wait until ready.

        When navigating to a specific conversation the SPA may redirect to
        the last-viewed conversation stored in the browser session.  If that
        happens we retry once with a hard reload.

        Automatically waits for the page to load (spinner disappears, input
        visible). For explicit waiting (e.g., after sending a message), use
        wait_for_page_load().

        Args:
            conversation_id: Optional conversation ID to navigate to specific chat
        """
        # Wait a moment for page URL to settle (may be in navigation)
        try:
            self.page.wait_for_load_state("domcontentloaded", timeout=5000)
        except Exception:
            pass  # Page might not be loaded yet

        # Check if already on chat page (skip navigation if so)
        current_url = self.page.url
        already_on_chat = "/chat" in current_url and "about:blank" not in current_url

        if already_on_chat:
            logger.info("Already on chat page (%s), skipping navigation", current_url)
        else:
            path = f"/chat/{conversation_id}" if conversation_id else "/chat"
            self.navigate(path)

            # If we targeted a specific conversation, verify the SPA didn't redirect
            if conversation_id and f"/chat/{conversation_id}" not in self.page.url:
                logger.warning(
                    "SPA redirected to %s instead of /chat/%s — retrying",
                    self.page.url, conversation_id,
                )
                self.page.goto(
                    f"{settings.elitea_url}{settings.app_prefix}/chat/{conversation_id}",
                    wait_until="domcontentloaded",
                )
                try:
                    self.page.wait_for_load_state("networkidle", timeout=30000)
                except Exception:
                    logger.debug("navigate_to_chat: networkidle not reached after SPA redirect — continuing")

        self.wait_for_page_load()
        logger.info(f"Navigated to chat, page loaded (actual URL: {self.page.url})")

    def wait_for_page_load(self, timeout: int = 30000):
        """Wait for chat page to fully load.

        Args:
            timeout: Maximum wait time in ms (default 30s)
        """
        import time as _time

        # Wait for network idle — best-effort: TTS WebSocket connections from prior
        # tests can keep the network active indefinitely, preventing networkidle.
        # The element-level waits below are the real readiness signals.
        try:
            self.wait_for_network(timeout=timeout)
        except Exception:
            logger.debug("wait_for_page_load: networkidle not reached — continuing")

        # Primary check: message input is visible AND editable (page is truly usable).
        # Waiting for "visible" alone is not sufficient — the textarea becomes visible
        # before the page finishes loading, but "fill()" requires the element to be
        # editable as well. The context default timeout (10s) would expire during fill()
        # if we only waited for visibility here.
        try:
            self.message_input.wait_for(state="visible", timeout=timeout)
            # Poll for editable state — Playwright's wait_for() only supports
            # attached/detached/visible/hidden states, not editable.
            deadline = _time.monotonic() + timeout / 1000.0
            while _time.monotonic() < deadline:
                if self.message_input.is_editable():
                    break
                _time.sleep(0.2)
            else:
                logger.warning("Message input did not become editable within timeout")
            logger.info("Chat page loaded - message input visible and editable")
        except Exception:
            # Fallback: check for full-page loading spinner and wait for it
            spinner = self.page.locator('svg[class*="CircularProgress"], [role="progressbar"], [class*="spinner"]')
            if spinner.count() > 0:
                try:
                    spinner.first.wait_for(state="hidden", timeout=timeout)
                    logger.info("Loading spinner disappeared")
                except Exception:
                    logger.warning("Spinner did not disappear within timeout — continuing")
            # Try message input again
            self.message_input.wait_for(state="visible", timeout=15000)
            deadline = _time.monotonic() + 15.0
            while _time.monotonic() < deadline:
                if self.message_input.is_editable():
                    break
                _time.sleep(0.2)
            logger.info("Chat page loaded after spinner wait")
        
    @action("Switch project")
    def switch_project(self, project_id: str, timeout: int = 10000):
        """Switch the active project via the sidebar project selector.

        Opens the ``project_selector_trigger`` combobox and clicks the
        option matching *project_id*, resolved via the dynamic
        ``SELECT_OPTION`` template — the same shared SingleSelectMenuItem
        pattern already precedented in ``agent_detail_page.py``'s
        ``select_fork_target_project()`` / ``FORK_PROJECT_OPTION`` (different
        UI surface, same underlying DOM component).

        Args:
            project_id: Numeric id of the target project (string or
                int-like).
            timeout: Maximum wait time in milliseconds.
        """
        logger.info("Switching active project to id=%s", project_id)
        self.project_selector_trigger.click()
        option = self.page.locator(self.SELECT_OPTION.format(project_id))
        option.wait_for(state="visible", timeout=timeout)
        option.click()
        self.wait_for_network(timeout=timeout)
        logger.info("Switched to project id=%s", project_id)

    def get_selected_project_text(self) -> str:
        """Return the visible text of the sidebar project selector trigger.

        Reads ``project_selector_trigger``'s own text (e.g. "Project:
        Elitea Testing Team") — a testid-only handle. There is no separate
        testid'd element exposing the raw numeric project id in the
        sidebar (only the combobox's display text), so callers verifying a
        project switch assert against the project NAME here and, where a
        numeric id must be confirmed, cross-check via the API (e.g.
        ``ConversationAPI.get_conversation()``'s ``project_id`` field)
        rather than reaching for a raw, non-testid DOM handle.
        """
        text = self.project_selector_trigger.text_content() or ""
        return text.strip()

    @action("Send message")
    def send_message(self, text: str, use_enter: bool = False):
        """Send a message in the chat.

        Args:
            text: Message text to send
            use_enter: If True, use Enter key instead of clicking send button
        """
        logger.info(f"Sending message: {text[:50]}...")
        # For very large inputs (>1000 chars) use JavaScript to set the value directly.
        # Playwright's fill() triggers React's onChange handler on every character which
        # makes filling 100k-character strings extremely slow (minutes vs milliseconds).
        # Using JS to set the value + dispatch a synthetic input event updates React
        # state instantly regardless of content length.
        if len(text) > 1000:
            element = self.message_input.element_handle()
            self.page.evaluate(
                """(args) => {
                    const [el, value] = args;
                    const nativeInputValueSetter = Object.getOwnPropertyDescriptor(
                        window.HTMLTextAreaElement.prototype, 'value'
                    ).set;
                    nativeInputValueSetter.call(el, value);
                    el.dispatchEvent(new Event('input', { bubbles: true }));
                    el.dispatchEvent(new Event('change', { bubbles: true }));
                }""",
                [element, text],
            )
        else:
            self.message_input.fill(text)

        if use_enter:
            self.message_input.press("Enter", timeout=60000)
        else:
            # Wait for send button to be visible and enabled, then click.
            # force=True is needed because MUI overlay elements can
            # intercept pointer events on the send button.
            self.send_button.wait_for(state="visible", timeout=5000)
            self.send_button.click(force=True, timeout=5000)
            
    @action("Send multi-line message")
    def send_message_with_shift_enter(self, lines: list):
        """Send a multi-line message using Shift+Enter for line breaks.

        Args:
            lines: List of text lines to send
        """
        logger.info(f"Sending multi-line message with {len(lines)} lines")
        for i, line in enumerate(lines):
            self.message_input.type(line)
            if i < len(lines) - 1:
                self.message_input.press("Shift+Enter")
        self.send_button.click(force=True)
        
    def get_message_count(self) -> int:
        """Get the count of messages in the chat history.

        Returns:
            Number of messages displayed
        """
        count = self.messages_container.count()
        logger.info(f"Message count: {count}")
        return count

    def get_messages_scroll_metrics(self) -> dict:
        """Return scrollHeight/clientHeight/scrollTop for the messages scroll container."""
        return self.chat_messages_scroll_container.evaluate(
            "el => ({scrollHeight: el.scrollHeight, clientHeight: el.clientHeight, "
            "scrollTop: el.scrollTop})"
        )

    def is_messages_scrollable(self) -> bool:
        """Return True if the messages region genuinely overflows (scrollHeight > clientHeight)."""
        metrics = self.get_messages_scroll_metrics()
        return metrics["scrollHeight"] > metrics["clientHeight"]

    def scroll_messages_container(self, delta_y: int = 200) -> tuple[int, int]:
        """Perform a real scroll on the messages container; return (scrollTop_before, scrollTop_after).

        A CSS ``overflow-y: scroll`` container with content that happens to
        fit exactly would pass a height-only check without ever proving the
        user can actually scroll — this drives an actual wheel interaction
        and reads ``scrollTop`` before/after so the caller can assert it
        changed.

        Args:
            delta_y: Vertical scroll delta in pixels (positive = scroll down).
        """
        before = self.chat_messages_scroll_container.evaluate("el => el.scrollTop")
        self.chat_messages_scroll_container.hover()
        self.page.mouse.wheel(0, delta_y)
        self.page.wait_for_timeout(300)
        after = self.chat_messages_scroll_container.evaluate("el => el.scrollTop")
        logger.info("Scrolled messages container: scrollTop %s -> %s", before, after)
        return before, after
        
    @staticmethod
    def _extract_message_body(message_locator) -> str:
        """Extract the body text from a message ``<li>``, excluding headers.

        Each message ``<li>`` contains a header row (sender name,
        timestamp, etc.) and a body area.  For AI messages the body
        is an ``<Answer>`` div rendered via ``<Markdown>`` which
        produces ``<p>`` tags for paragraphs and ``<ul><li>`` for
        bullet/numbered lists.  For user messages the body is a
        ``<Typography variant="bodyMedium">`` span.

        The extractor collects text from all ``<p>`` and ``<li>``
        elements so that list responses (e.g. branch listings) are
        captured in full rather than only the introductory sentence.

        Returns an empty string when no body content is found (e.g.
        the AI is still streaming or the response is empty).  This
        is intentional — callers like ``wait_for_message_content_stable``
        treat empty text as "not ready yet" and keep polling.
        """
        # AI messages: content is rendered via Markdown which produces <p> for
        # paragraphs and <ul><li> for bullet lists.  Collect all block-level
        # text nodes so that list items are not silently dropped.
        # Strategy: grab the inner text of all <p> and <li> elements in
        # document order, then join them.  Using `inner_text()` on the
        # container would include header metadata (sender name, timestamp),
        # so we enumerate block elements explicitly.
        block_elements = message_locator.locator('p, li')
        if block_elements.count() > 0:
            parts = []
            for i in range(block_elements.count()):
                parts.append(block_elements.nth(i).text_content() or "")
            text = "\n".join(p for p in parts if p.strip()).strip()
            if text:
                return text

        # User messages: content is in bodyMedium Typography spans
        body_spans = message_locator.locator('.MuiTypography-bodyMedium')
        if body_spans.count() > 0:
            parts = []
            for i in range(body_spans.count()):
                parts.append(body_spans.nth(i).text_content() or "")
            text = "\n".join(parts).strip()
            if text:
                return text

        return ""

    def get_last_message_text(self) -> str:
        """Get the text content of the last message body.

        Extracts the body content (excluding header/metadata) from
        the last message ``<li>`` element.

        Returns:
            Text of the last message body
        """
        last_msg = self.messages_container.last
        text = self._extract_message_body(last_msg)
        logger.info(f"Last message: {text[:50]}...")
        return text
        
    def wait_for_ai_response(self, initial_count: int = 0, timeout: int = 60000):
        """Wait for the AI to fully respond after sending a message.

        Waits for a new AI message to appear AND for its Copy button to become
        visible, which indicates the response is fully rendered (not still
        streaming). This is more reliable than checking text stability because
        it doesn't depend on specific transient message strings.

        After the user sends a message, the conversation grows by at least 2:
        the user's own message at index ``initial_count``, and the AI's response
        at index ``initial_count + 1``.

        Args:
            initial_count: Number of messages present *before* the user sent
                           the message (captured via ``get_message_count()``).
            timeout: Maximum wait time in milliseconds (default 60s for toolkit
                     execution which may involve external API calls).
        """
        logger.info(
            "Waiting for AI response with Copy button (initial_count=%d, timeout=%dms)...",
            initial_count,
            timeout,
        )
        # User's message lands at nth(initial_count).
        # AI's response lands at nth(initial_count + 1).
        ai_response_index = initial_count + 1
        ai_message = self.messages_container.nth(ai_response_index)

        # Step 1: Wait for the AI message element to appear
        ai_message.wait_for(state="visible", timeout=timeout)
        logger.info("AI response element appeared at index %d", ai_response_index)

        # Step 2: Wait for the Copy button within that message to appear
        # The Copy button only renders when the message is fully generated
        copy_button = ai_message.locator('button[aria-label="Copy to clipboard"]')
        deadline = time.monotonic() + timeout / 1000.0
        poll_interval = 0.5
        copy_button_seen = False

        while time.monotonic() < deadline:
            try:
                if copy_button.count() > 0 and copy_button.first.is_visible():
                    if not copy_button_seen:
                        logger.info("Copy button visible, verifying content...")
                        copy_button_seen = True
                    # Step 3: Verify message body has non-transient content
                    # The Copy button can appear before actual content renders
                    current_text = self._extract_message_body(ai_message)
                    if current_text and not self._is_transient_message(current_text):
                        logger.info("AI response complete — content verified: %s...", current_text[:50])
                        self.wait_for_network(timeout=5000)
                        return
                    logger.debug("Copy button visible but content still transient: %s", current_text[:50] if current_text else "(empty)")
            except Exception:
                pass  # Element temporarily detached during re-render
            time.sleep(poll_interval)

        # Timeout reached - log what we have for debugging
        try:
            current_text = self._extract_message_body(ai_message)
            logger.warning(
                "Timeout waiting for AI response. Copy button seen: %s, Current text: %s",
                copy_button_seen,
                current_text[:200] if current_text else "(empty)"
            )
        except Exception:
            pass

        raise TimeoutError(
            f"AI response did not complete within {timeout}ms — "
            f"Copy button {'appeared but content was transient' if copy_button_seen else 'never appeared'}"
        )

    # Transient messages that indicate generation is still in progress
    TRANSIENT_MESSAGES = frozenset([
        "waking the agent",
        "waking the agent…",
        "waking the agent...",
        "thinking",
        "thinking…",
        "thinking...",
    ])

    def _is_transient_message(self, text: str) -> bool:
        """Check if the message is a transient state that should be ignored.

        Normalises non-breaking spaces (``\\xa0``, used by the "Waking the
        agent…" placeholder when an agent is cold-starting after being newly
        added as a chat participant — confirmed live during ELITEA-1736
        implementer Phase 2) to regular spaces before matching against
        ``TRANSIENT_MESSAGES``, which is written with plain-space literals.
        Without this, the nbsp variant silently fails the membership check
        and ``wait_for_message_content_stable`` treats the placeholder as
        real, stable content — a false-stable race, not a real defect.

        Also detects dynamic status patterns like "Thought for X seconds"
        and "Packing its tools" which are streaming status indicators.
        """
        normalized = text.replace("\xa0", " ").lower().strip()
        # Check exact matches against TRANSIENT_MESSAGES
        if normalized.rstrip(".…") in self.TRANSIENT_MESSAGES or \
           normalized in self.TRANSIENT_MESSAGES:
            return True
        # Check dynamic patterns (streaming status indicators)
        if normalized.startswith("thought for "):
            return True
        if "packing" in normalized and "tool" in normalized:
            return True
        return False

    def wait_for_message_content_stable(
        self, stable_duration_ms: int = 2000, timeout: int = 30000
    ):
        """Wait until the last message content stops changing.

        Polls the last message text at short intervals and considers it
        stable once the text hasn't changed for *stable_duration_ms*.
        Ignores transient states like "Waking the agent…" or "Thinking…".

        Args:
            stable_duration_ms: Duration in ms the content must remain
                unchanged before it's considered stable.
            timeout: Maximum total wait time in milliseconds.
        """
        logger.info(
            "Waiting for message content to stabilise "
            "(stable=%dms, timeout=%dms)...",
            stable_duration_ms,
            timeout,
        )
        poll_interval = 0.5  # seconds
        stable_duration = stable_duration_ms / 1000.0
        deadline = time.monotonic() + timeout / 1000.0

        last_text = ""
        stable_since = time.monotonic()

        while time.monotonic() < deadline:
            try:
                current_text = self._extract_message_body(
                    self.messages_container.last
                )
            except Exception:
                current_text = ""

            # Skip transient messages - they don't count as stable content
            if self._is_transient_message(current_text):
                logger.debug("Skipping transient message: %s", current_text[:50])
                time.sleep(poll_interval)
                continue

            if current_text != last_text:
                last_text = current_text
                stable_since = time.monotonic()

            if (
                last_text
                and time.monotonic() - stable_since >= stable_duration
            ):
                logger.info("Message content stable after %.1fs", time.monotonic() - (stable_since - stable_duration))
                return

            time.sleep(poll_interval)

        # If we only saw transient messages, raise an error
        if self._is_transient_message(last_text) or not last_text:
            raise TimeoutError(
                f"Timed out waiting for non-transient message content. "
                f"Last message: '{last_text}'"
            )
        logger.warning("Timed out waiting for stable message content (last: %s)", last_text[:100])

    def wait_for_generation_complete(self, timeout: int = 60000):
        """Wait until the AI finishes generating the full response.

        Call this after ``wait_for_ai_response`` to guarantee you read the
        complete response rather than a mid-generation snapshot.

        Args:
            timeout: Maximum wait in milliseconds (default 60 s — long enough
                     for toolkit execution which involves an external API call).
        """
        logger.info("Waiting for generation to complete (Speaking mode button)...")
        # The Speaking mode button appears when generation is complete
        # During generation, a stop button is shown instead
        speaking_mode_btn = self.page.locator(
            'span[aria-label="Speaking mode"], '
            'button[aria-label="enter speaking mode"]'
        )
        deadline = time.monotonic() + timeout / 1000.0
        while time.monotonic() < deadline:
            try:
                if speaking_mode_btn.count() > 0 and speaking_mode_btn.first.is_visible():
                    logger.info("Generation complete — Speaking mode button visible")
                    return
            except Exception:
                pass  # element temporarily detached during re-render
            time.sleep(0.5)
        raise TimeoutError(
            f"Generation did not complete within {timeout} ms — "
            "Speaking mode button never appeared"
        )

    def wait_for_input_ready(self, timeout: int = 10000):
        """Wait until the message input is visible and interactable.

        Useful after sending a message when the SPA may navigate to a new
        URL (``/chat/{id}?name=...``) and re-render the page.
        """
        self.page.wait_for_load_state("domcontentloaded", timeout=timeout)
        self.message_input.wait_for(state="visible", timeout=timeout)

    def wait_for_message_count(self, expected_count: int, timeout: int = 10000):
        """Wait until the displayed message count reaches *expected_count*.

        Args:
            expected_count: Minimum number of messages expected.
            timeout: Maximum wait time in milliseconds.
        """
        logger.info("Waiting for message count >= %d", expected_count)
        self.messages_container.nth(expected_count - 1).wait_for(
            state="visible", timeout=timeout,
        )

    def wait_for_navigation(self, url_pattern: str, timeout: int = 10000):
        """Wait for the page URL to match *url_pattern*.

        Args:
            url_pattern: Substring that the URL must contain.
            timeout: Maximum wait time in milliseconds.
        """
        logger.info("Waiting for URL to contain '%s'", url_pattern)
        self.page.wait_for_url(lambda url: url_pattern in url, timeout=timeout)

    def is_input_empty(self) -> bool:
        """Check if message input is empty.
        
        Returns:
            True if input is empty
        """
        value = self.message_input.input_value()
        return len(value.strip()) == 0
        
    def is_send_button_enabled(self) -> bool:
        """Check if send button is enabled.
        
        Returns:
            True if send button is enabled
        """
        return self.send_button.is_enabled()
        
    @action("Clear chat history")
    def clear_chat_history(self):
        """Click the Clear chat history button."""
        logger.info("Clearing chat history")
        self.clear_history_button.click()
        
    def click_model_selector(self):
        """Click the model selector to open model menu."""
        logger.info("Opening model selector")
        self.model_selector.first.click()
        
    def get_selected_model(self) -> str:
        """Get the currently selected model name.
        
        Returns:
            Model name (e.g., 'GPT-5 mini', 'Claude 4.6')
        """
        model_text = self.model_selector.first.text_content()
        logger.info(f"Selected model: {model_text}")
        return model_text
        
    def open_sidebar(self):
        """Open the sidebar drawer to show full text labels.

        The sidebar has two states:
        - Collapsed: shows only icons (mini-sidebar)
        - Expanded: shows icons + text labels

        The "open drawer" button toggles between these states.
        """
        logger.info("Opening sidebar")
        # Check if already expanded (Agents text visible)
        agents_btn = self.page.get_by_role("button", name="Agents", exact=True)
        if agents_btn.is_visible():
            logger.info("Sidebar already expanded")
            return

        # Click the toggle to expand
        if self.sidebar_toggle.is_visible():
            self.sidebar_toggle.click()
            self.page.wait_for_timeout(300)  # Allow animation

    def close_sidebar(self):
        """Close the sidebar drawer to show only icons (mini-sidebar).

        Clicks the drawer toggle to collapse to icon-only mode.
        """
        logger.info("Closing sidebar")
        # Check if already collapsed (Agents text not visible)
        agents_btn = self.page.get_by_role("button", name="Agents", exact=True)
        if not agents_btn.is_visible():
            logger.info("Sidebar already collapsed")
            return

        # Click the toggle to collapse
        if self.sidebar_toggle.is_visible():
            self.sidebar_toggle.click()
            self.page.wait_for_timeout(300)  # Allow animation
        
    def open_file_chooser(self, timeout: int = 10000):
        """Click the attach button and return the FileChooser dialog.

        Use this when the test needs to inspect chooser properties (e.g.
        ``is_multiple()``) before selecting files.  For the common case of
        just attaching a file, call ``attach_file()`` instead.

        Args:
            timeout: Maximum wait for the file chooser to appear (ms).

        Returns:
            playwright.sync_api.FileChooser
        """
        with self.page.expect_file_chooser(timeout=timeout) as fc_info:
            self.attach_files_button.click()
        return fc_info.value

    @action("Attach file")
    def attach_file(self, file_path: str, timeout: int = 10000):
        """Attach a file to the message.

        Clicks the attach button, waits for the OS file chooser, selects
        the file, then waits for the upload network activity to settle.

        Args:
            file_path: Absolute or relative path to the file to attach.
            timeout: Maximum wait for the file chooser to appear (ms).
        """
        logger.info("Attaching file: %s", file_path)
        file_chooser = self.open_file_chooser(timeout=timeout)
        file_chooser.set_files(file_path)
        self.wait_for_network(timeout=timeout)
        
    @action("Copy message")
    def copy_message(self, message_index: int = -1):
        """Copy a message to clipboard.

        Hovers over the target message to reveal action buttons, then clicks
        the copy button within that message. Waits for the clipboard operation
        to complete.

        Args:
            message_index: Index of message to copy (-1 for last)
        """
        logger.info(f"Copying message at index {message_index}")

        # Get the target message block
        message_block = self.messages_container.nth(message_index)
        message_block.scroll_into_view_if_needed()

        # Hover over the message to reveal action buttons
        message_block.hover()
        self.page.wait_for_timeout(500)  # Wait for hover effect

        # Find and click the copy button within this message
        copy_button = message_block.locator('button[aria-label="Copy to clipboard"]')
        if copy_button.count() == 0:
            from playwright.sync_api import TimeoutError as PlaywrightTimeoutError
            raise PlaywrightTimeoutError(
                f"No copy button found on message at index {message_index}"
            )
        copy_button.first.click()

        # Wait for clipboard API to complete (async operation)
        self.page.wait_for_timeout(500)
        logger.info("Copy to clipboard completed")

    @action("Delete message")
    def delete_message(self, message_index: int = -1):
        """Delete a message by hovering over it and clicking the delete button.

        The delete button has NO aria-label. It's a button inside a generic
        container with text "Delete". The button only becomes visible on hover
        over the message. After clicking, a confirmation dialog appears.

        Args:
            message_index: Index of message to delete (-1 for last)
        """
        logger.info(f"Deleting message at index {message_index}")

        # Get the target message block
        message_block = self.messages_container.nth(message_index)
        message_block.scroll_into_view_if_needed()

        # Hover over the message to reveal action buttons
        message_block.hover()
        self.page.wait_for_timeout(500)  # Wait for hover effect

        # Find the delete button within this message
        # The delete button structure:
        # - It's the 3rd button after Copy and Regenerate buttons
        # - Inside a generic with accessible name "Delete"
        # - Has NO aria-label attribute

        # Strategy: Get all buttons in the message, filter by position
        # Buttons appear in order: Copy (index 0), Regenerate (index 1), Delete (index 2)
        buttons = message_block.locator('button')
        button_count = buttons.count()
        logger.info(f"Found {button_count} buttons in message")

        # The delete button is typically the last button (or 3rd if all 3 are present)
        # Use -1 to get the last button which should be Delete
        delete_button = buttons.last

        # Click the delete button
        delete_button.click(force=True)
        logger.info("Clicked delete button")

        # Handle the confirmation dialog
        dialog = Dialog.wait_for(self.page, timeout=5000)
        Dialog.click_button(dialog, "Confirm")
        logger.info("Confirmed message deletion")

        # Wait for deletion to complete
        self.page.wait_for_timeout(1000)
        
    @action("Regenerate response")
    def regenerate_response(self):
        """Click regenerate button on last AI message."""
        logger.info("Regenerating AI response")
        self.regenerate_button.click()
        
    @action("Search participants")
    def search_participants_with_hash(self, query: str):
        """Use # to search for participants to add.

        Types ``#query`` into the message input and waits for a dropdown.

        Args:
            query: Search query after #

        Raises:
            TimeoutError: If no dropdown appears within 5 seconds.
        """
        logger.info(f"Searching participants with #{query}")
        self.message_input.fill(f"#{query}")
        # Wait for search results dropdown (multiple possible selectors)
        self.page.wait_for_selector(
            '[role="listbox"], [role="option"], [class*="dropdown"], '
            '[class*="popper"], [class*="autocomplete"], [class*="mention"]',
            timeout=5000,
        )
        
    @action("Select participant")
    def select_participant_from_search(self, participant_name: str):
        """Select a participant from # search results.
        
        Args:
            participant_name: Name of participant to select
        """
        logger.info(f"Selecting participant: {participant_name}")
        option = self.page.get_by_role("option", name=participant_name).first
        option.click()
        
    def edit_context_settings(self):
        """Open context settings dialog."""
        logger.info("Opening context settings")
        self.edit_context_button.click()
        
    def toggle_internal_tools(self):
        """Toggle internal tools checkbox."""
        logger.info("Toggling internal tools")
        self.internal_tools_toggle.click()

    def close_open_dialogs(self):
        """Close any open dialogs or modals by pressing Escape."""
        dialog = self.page.locator('[role="dialog"], [class*="MuiDialog-root"], [class*="modal"]')
        if dialog.count() > 0:
            self.page.keyboard.press("Escape")
            self.page.wait_for_timeout(500)

    def wait_for_model_menu(self, timeout: int = 5000):
        """Wait for model selector menu to appear after clicking.

        Returns the menu locator.
        """
        menu = self.page.locator('[role="menu"], [role="listbox"], [class*="menu"], [class*="popover"]')
        menu.first.wait_for(state="visible", timeout=timeout)
        return menu

    def wait_for_hash_search_dropdown(self, timeout: int = 5000):
        """Wait for # mention search results panel to appear.

        In v2.0.3+, typing #query shows a search results panel above the input
        with matching agents, pipelines, etc.

        Returns the search results panel locator or raises TimeoutError.
        """
        # Look for the search results panel that contains "Search results" heading
        # or the results container with agent/pipeline items
        search_results = self.page.locator(
            ':has-text("Search results"), '
            '[class*="dropdown"], [class*="popper"], '
            '[class*="autocomplete"], [class*="mention"]'
        ).filter(has=self.page.locator(':text("agent"), :text("pipeline")'))

        search_results.first.wait_for(state="visible", timeout=timeout)
        return search_results

    def get_hash_search_first_option(self):
        """Get the first clickable option from hash search results.

        The hash search panel structure:
        - "Search results" title
        - List of participant cards with EntityIcon + name text

        Each card contains an SVG icon and the participant name in a Typography.
        Returns the first clickable card locator or None if no options.
        """
        # Find the search results panel
        results_title = self.page.locator('text=/search results/i').first
        if results_title.count() == 0:
            return None

        # Go up to the container and find clickable cards with icons
        container = results_title.locator('xpath=ancestor::div[3]')

        # Participant cards have an SVG icon and text
        cards = container.locator('div').filter(
            has=self.page.locator('svg')
        ).filter(
            has=self.page.locator('p:not(:has-text("Search results")):not(:has-text("No matching"))')
        )

        if cards.count() > 0:
            return cards.first

        # Fallback: look for any element with agent/pipeline type labels
        cards = container.locator('div:has(p:text("agent")), div:has(p:text("pipeline"))')
        if cards.count() > 0:
            return cards.first

        return None


    def is_hash_search_dropdown_visible(self) -> bool:
        """Check if the # mention search results panel is currently visible.

        Returns:
            True if the search results panel is visible, False if it has closed.
        """
        search_results = self.page.get_by_text("Search results")
        return search_results.count() > 0 and search_results.first.is_visible()

    def wait_for_search_dialog(self, timeout: int = 5000):
        """Wait for search conversations input to appear.

        Clicking "Search chats" button opens an inline search textbox
        (not a modal dialog). Placeholder is "Search conversations...".

        Returns the search input locator.
        """
        search_input = self.page.locator(
            'input[placeholder*="Search conversations"], '
            'input[placeholder*="Search chats"], '
            '[role="searchbox"]'
        )
        search_input.first.wait_for(state="visible", timeout=timeout)
        return search_input

    def wait_for_sidebar_expanded(self, timeout: int = 5000):
        """Wait for sidebar to expand and show full labels."""
        # Sidebar items are buttons with text labels when expanded
        # Use exact=True to avoid matching conversation items with "Agents" in their name
        agents_btn = self.page.get_by_role("button", name="Agents", exact=True)
        agents_btn.wait_for(state="visible", timeout=timeout)

    def has_error_notification(self) -> bool:
        """Check if an error notification is present on the page.

        Returns:
            True if error notification visible, False otherwise.
        """
        error = self.page.locator('[role="alert"], [class*="error"], [class*="notification"]')
        return error.count() > 0 and error.first.is_visible()

    def open_search_conversations(self):
        """Open search conversations via the Search chats button.

        Uses the "Search chats" button in the conversations panel header.
        This reveals an inline search textbox (not a dialog).
        """
        logger.info("Opening search conversations via button")
        search_btn = self.page.get_by_role("button", name="Search chats")
        search_btn.wait_for(state="visible", timeout=5000)
        search_btn.click()
        
    def navigate_to_agents(self):
        """Navigate to Agents page via the sidebar drawer."""
        logger.info("Navigating to Agents")
        self.open_sidebar()
        # Sidebar items are buttons with accessible names
        # Use exact=True to avoid matching conversation items with "Agents" in their name
        agents_btn = self.page.get_by_role("button", name="Agents", exact=True)
        agents_btn.wait_for(state="visible", timeout=5000)
        agents_btn.click()

    # ------------------------------------------------------------------
    # Conversation management helpers
    # ------------------------------------------------------------------

    @action("Create new conversation")
    def click_create_conversation(self, timeout: int = 10000):
        """Click the "+ Conversation" button in the sidebar.

        Uses data-testid attribute locator for stability across label changes.
        The button label varies by current route (e.g. "Chat" on /chat, "Create"
        on settings pages) so text-based locators are unreliable.

        LOCATOR: [data-testid="sidebar-create-button"]

        Args:
            timeout: Maximum wait time in milliseconds.
        """
        logger.info("Clicking +Conversation button")
        btn = self.page.get_by_test_id("sidebar-create-button").first
        btn.wait_for(state="visible", timeout=timeout)
        btn.click(force=True)
        # Wait for the "Creating conversation..." state to finish
        self.page.wait_for_timeout(1000)
        # networkidle is best-effort: /chat has a persistent WebSocket that
        # keeps the network active indefinitely, preventing networkidle from
        # being reached.  The message_input wait below is the real signal.
        try:
            self.wait_for_network(timeout=timeout)
        except Exception:
            logger.debug("click_create_conversation: networkidle not reached — continuing")
        # The message input should become available in the new conversation
        self.message_input.wait_for(state="visible", timeout=timeout)
        logger.info("New conversation created, URL: %s", self.page.url)

    @action("Create new conversation")
    def click_create_new_conversation(self, timeout: int = 10000):
        """Click the "+Conversation" button in the sidebar.

        Uses data-testid attribute locator for stability across label changes.

        LOCATOR: [data-testid="sidebar-create-button"]

        Args:
            timeout: Maximum wait time in milliseconds.
        """
        logger.info("Clicking +Conversation button")
        btn = self.page.get_by_test_id("sidebar-create-button").first
        btn.wait_for(state="visible", timeout=timeout)
        btn.click(force=True)
        self.page.wait_for_timeout(1000)
        # networkidle is best-effort: /chat has a persistent WebSocket that
        # keeps the network active indefinitely, preventing networkidle from
        # being reached.  The message_input wait below is the real signal.
        try:
            self.wait_for_network(timeout=timeout)
        except Exception:
            logger.debug("click_create_new_conversation: networkidle not reached — continuing")
        self.message_input.wait_for(state="visible", timeout=timeout)
        logger.info("New conversation created, URL: %s", self.page.url)

    def get_conversation_list_items(self):
        """Return a Playwright locator for conversation items in the sidebar list.

        Each conversation is rendered as a <button> element that is a direct
        child of the conversation list container.  That container also holds
        date-group headers (h6 elements like "Today", "Yesterday") as siblings.

        The selector ``:has(h6) > button`` exploits this structural relationship:
        - ``:has(h6)`` — the list container that holds at least one date-group heading
        - ``> button`` — direct-child conversation item buttons only

        This avoids brittle CSS class names (which are MUI-generated and change
        between builds) and correctly excludes toolbar buttons (which are nested
        deeper or have aria-label attributes).
        """
        return self.page.locator(':has(h6) > button')

    def is_conversation_group_visible(self, group: str = "today", timeout: int = 5000) -> bool:
        """Return True if the date-group container for *group* is visible.

        LOCATOR: ``CONVERSATION_GROUP_HEADER`` (``chat-conversation-group-
        header-{group}``, added ELITEA-2095) — a stable testid replacing a
        raw ``<h6>``-text lookup. The container renders whenever the group
        has at least one conversation and is expanded by default
        (``DEFAULT_EXPANDED_GROUP`` in EliteaUI); it is NOT scoped to the
        collapsed/expanded animation state itself — callers wanting to
        assert "expanded" do so via ``is_conversation_in_group()`` finding a
        real item underneath, per the project's state-via-data-attribute
        policy (there is no separate collapsed/expanded testid).

        Args:
            group: Date-group key — "today" (default), "this_week", or
                "older".
            timeout: Maximum wait time in milliseconds.
        """
        container = self.page.locator(self.CONVERSATION_GROUP_HEADER.format(group))
        try:
            container.first.wait_for(state="visible", timeout=timeout)
            return True
        except Exception:
            return False

    def get_conversation_group_header(self, group: str = "today"):
        """Return the Locator for a date-group heading container.

        Same handle as ``is_conversation_group_visible`` (``CONVERSATION_
        GROUP_HEADER``), but returns the raw Locator instead of a bool —
        needed by callers that compare its ``bounding_box()`` against
        another element (e.g. ELITEA-2132's "new folder entry renders
        ABOVE the 'Today' heading" positional check), not just whether it
        exists.

        Args:
            group: Date-group key — "today" (default), "this_week", or
                "older".
        """
        return self.page.locator(self.CONVERSATION_GROUP_HEADER.format(group))

    def is_conversation_in_group(
        self, conversation_id: str | int, group: str = "today", timeout: int = 5000,
    ) -> bool:
        """Return True if *conversation_id* renders inside date-group *group* specifically.

        Scopes the dynamic ``CONVERSATION_ITEM`` testid WITHIN the dynamic
        ``CONVERSATION_GROUP_HEADER`` container (DateGroup.jsx renders the
        header row and its own Collapse'd conversation items in one outer
        element) — this is what actually proves "conversation X is under
        Today", not merely that both render somewhere on the page. Replaces
        the raw ``:has(h6) > button`` CSS in ``get_conversation_list_items()``
        (tracked tech debt, role-overrides.md) for Today-scoping.

        Args:
            conversation_id: Numeric conversation id.
            group: Date-group key — "today" (default), "this_week", or
                "older".
            timeout: Maximum wait time in milliseconds.
        """
        group_container = self.page.locator(self.CONVERSATION_GROUP_HEADER.format(group))
        item = group_container.locator(self.CONVERSATION_ITEM.format(conversation_id))
        try:
            item.first.wait_for(state="visible", timeout=timeout)
            return True
        except Exception:
            return False

    @action("Select conversation in date-group")
    def click_conversation_in_group(
        self, conversation_id: str | int, group: str = "today", timeout: int = 5000,
    ):
        """Click the conversation item scoped within date-group *group*.

        Args:
            conversation_id: Numeric conversation id.
            group: Date-group key — "today" (default), "this_week", or
                "older".
            timeout: Maximum wait time in milliseconds.
        """
        logger.info("Clicking conversation %s in group %r", conversation_id, group)
        group_container = self.page.locator(self.CONVERSATION_GROUP_HEADER.format(group))
        item = group_container.locator(self.CONVERSATION_ITEM.format(conversation_id))
        item.wait_for(state="visible", timeout=timeout)
        item.click(force=True)
        self.wait_for_network(timeout=timeout)

    @action("Select any other conversation")
    def click_first_other_conversation(self, exclude_id: str | int, timeout: int = 5000):
        """Click the first sidebar conversation item OTHER than *exclude_id*.

        Used to force a genuine navigation away from the currently-open
        conversation: the bare "/chat" route auto-redirects back to the
        last-viewed conversation (SPA "resume" behavior), so navigating to
        it does not reliably leave a specific conversation — clicking a
        DIFFERENT real conversation does (ELITEA-2095 case step 2).

        Args:
            exclude_id: Conversation id to skip.
            timeout: Maximum wait time in milliseconds.

        Raises:
            AssertionError: If no other conversation item is found.
        """
        items = self.page.locator(self.CONVERSATION_ITEM_PREFIX)
        items.first.wait_for(state="visible", timeout=timeout)
        exclude_testid = f"chat-conversation-item-{exclude_id}"
        for i in range(items.count()):
            item = items.nth(i)
            target_testid = item.get_attribute("data-testid")
            if target_testid != exclude_testid:
                logger.info("Clicking other conversation: %s", target_testid)
                item.click(force=True)
                # A deterministic wait on the URL, not wait_for_network(): the
                # resulting client-side route change may involve no new
                # network request (conversation data already cached), so
                # networkidle can report "settled" before the SPA's router
                # has actually pushed the new URL — confirmed live, this was
                # a real flake source (ELITEA-2095).
                target_id = target_testid.removeprefix("chat-conversation-item-")
                self.wait_for_conversation_url(target_id, timeout=timeout)
                return
        raise AssertionError(
            f"No other conversation item found besides {exclude_testid!r} "
            "to navigate away to"
        )

    def get_conversation_names(self, timeout: int = 5000) -> list[str]:
        """Return the names of all conversations visible in the sidebar list.

        Uses the same locator as get_conversation_list_items() to ensure consistency.

        Args:
            timeout: Time to wait for at least one item to appear.

        Returns:
            List of conversation name strings (may be empty).
        """
        items = self.get_conversation_list_items()
        try:
            items.first.wait_for(state="visible", timeout=timeout)
        except Exception:
            logger.info("No conversation items visible in list")
            return []
        
        names = []
        for i in range(items.count()):
            try:
                text = items.nth(i).text_content().strip()
                if text:
                    names.append(text)
            except Exception as e:
                logger.debug(f"Failed to extract text from item {i}: {e}")
                continue
        
        logger.info(f"Found {len(names)} conversation(s): {names}")
        return names

    @action("Select conversation")
    def select_conversation_from_list(self, name: str, timeout: int = 5000):
        """Click a conversation in the sidebar list by its name.

        Uses ``force=True`` because MUI overlay divs (``css-1pybsfx``)
        can intercept pointer events in the conversations panel.

        Args:
            name: The conversation name to click.
            timeout: Maximum wait time in milliseconds.
        """
        logger.info("Selecting conversation: %s", name)
        item = self.page.locator(f'text="{name}"').first
        item.wait_for(state="visible", timeout=timeout)
        item.click(force=True)
        self.wait_for_network(timeout=timeout)

    @action("Select conversation by ID")
    def select_conversation_by_id(self, conversation_id: str | int, timeout: int = 5000):
        """Click a conversation in the sidebar list by its numeric ID.
        
        This is more reliable than name-based selection because conversation names
        can be auto-renamed after the first message is sent.
        
        Attempts multiple strategies:
        1. Look for data-conversation-id or similar attributes
        2. Look for href containing /chat/{id}
        3. Fallback: extract ID from all visible conversations and match
        
        Args:
            conversation_id: Numeric conversation ID (can be string or int).
            timeout: Maximum wait time in milliseconds.
            
        Raises:
            AssertionError: If conversation with given ID is not found.
        """
        conv_id = str(conversation_id)
        logger.info("Selecting conversation by ID: %s", conv_id)
        
        # Strategy 1: Try data attributes
        item = self.page.locator(
            f'[data-conversation-id="{conv_id}"], '
            f'[data-id="{conv_id}"], '
            f'[id*="conversation-{conv_id}"]'
        ).first
        
        if item.count() > 0:
            logger.info("Found conversation via data attribute")
            item.wait_for(state="visible", timeout=timeout)
            item.click(force=True)
            self.wait_for_network(timeout=timeout)
            return
        
        # Strategy 2: Look for href with /chat/{id}
        item = self.page.locator(f'a[href*="/chat/{conv_id}"]').first
        if item.count() > 0:
            logger.info("Found conversation via href attribute")
            item.wait_for(state="visible", timeout=timeout)
            item.click(force=True)
            self.wait_for_network(timeout=timeout)
            return
        
        # Strategy 3: JavaScript evaluation to find by href in onclick/data
        result = self.page.evaluate(f"""
            () => {{
                const elements = Array.from(document.querySelectorAll('[class*="conversation"]'));
                for (const el of elements) {{
                    const onclick = el.getAttribute('onclick') || '';
                    const href = el.getAttribute('href') || '';
                    const data = el.getAttribute('data-href') || '';
                    if (onclick.includes('{conv_id}') || href.includes('{conv_id}') || data.includes('{conv_id}')) {{
                        return el.textContent || null;
                    }}
                }}
                return null;
            }}
        """)
        
        if result:
            logger.info("Found conversation via JS evaluation, clicking by text: %s", result)
            item = self.page.locator(f'text="{result}"').first
            item.wait_for(state="visible", timeout=timeout)
            item.click(force=True)
            self.wait_for_network(timeout=timeout)
            return
        
        raise AssertionError(
            f"Could not find conversation with ID {conv_id} in the sidebar. "
            "The conversation list may not have loaded, or the ID doesn't match any visible conversation."
        )

    def conversation_exists_in_list(self, name: str, timeout: int = 3000) -> bool:
        """Check whether a conversation with *name* is visible in the sidebar.

        Uses ``:has-text()`` for partial matching because conversation
        names may be truncated with "..." in the sidebar.

        Args:
            name: Conversation name (or prefix) to look for.
            timeout: How long to wait for it to appear.

        Returns:
            True if the conversation is visible, False otherwise.
        """
        try:
            self.page.locator(f':has-text("{name}")').first.wait_for(
                state="visible", timeout=timeout,
            )
            return True
        except Exception:
            return False

    def open_search_conversations_button(self, timeout: int = 5000):
        """Click the search conversations icon/button in the conversations sidebar.

        The search button appears as an icon in the conversations panel header
        inside ``<main>`` (not ``<aside>``).  It has a stable ``aria-label``.

        A banner overlay (z-index 1200) may cover the button on first load,
        so we dismiss it before clicking.

        Args:
            timeout: Maximum wait time in milliseconds.
        """
        logger.info("Opening search conversations via button")
        self.dismiss_banner_if_present()
        search_btn = self.page.get_by_test_id("conversation-search-button")
        search_btn.wait_for(state="visible", timeout=timeout)
        search_btn.click()

    def search_conversations_via_button(self, query: str, timeout: int = 5000):
        """Open the search dialog and type a query.

        Args:
            query: Text to type into the search input.
            timeout: Maximum wait time in milliseconds.
        """
        self.open_search_conversations_button(timeout=timeout)
        search_input = self.page.locator(
            '[role="dialog"] input, [role="search"] input, '
            'input[placeholder*="Search"], input[placeholder*="search"]'
        )
        search_input.first.wait_for(state="visible", timeout=timeout)
        search_input.first.fill(query)
        logger.info("Searched conversations for: %s", query)

    def delete_conversation_ui(self, timeout: int = 5000):
        """Delete the current conversation via the UI three-dot / delete button.

        Looks for a delete button inside the conversations panel context
        menu or action buttons, then confirms the deletion dialog.

        Args:
            timeout: Maximum wait time in milliseconds.
        """
        logger.info("Deleting conversation via UI")
        # The conversation panel may have a delete icon or context menu
        delete_btn = self.page.locator(
            'button[aria-label="Delete conversation"], '
            'button[aria-label="delete conversation"], '
            'button[aria-label="Delete"]'
        )
        delete_btn.first.wait_for(state="visible", timeout=timeout)
        delete_btn.first.click()

        # Handle confirmation dialog
        dialog = Dialog.wait_for(self.page, timeout=timeout)
        Dialog.click_first_button(dialog, "Confirm", "Delete")
        self.wait_for_network(timeout=timeout)
        logger.info("Conversation deleted via UI")

    def open_conversation_menu(self, conv_name: str = None, timeout: int = 5000):
        """Open the three-dot context menu on a conversation list item.

        Hovers the conversation item to reveal the hidden menu button,
        then clicks it via JS (to bypass MUI overlay).  If *conv_name*
        is ``None``, operates on the first conversation in the list.

        Args:
            conv_name: Name of the conversation to target.
            timeout: Maximum wait time in milliseconds.
        """
        logger.info("Opening conversation menu for: %s", conv_name or "(first)")
        if conv_name:
            item = self.page.locator(
                f'[role="button"][aria-roledescription="draggable"]:has-text("{conv_name}")'
            ).first
        else:
            item = self.page.locator(
                '[role="button"][aria-roledescription="draggable"]'
            ).first
        item.wait_for(state="visible", timeout=timeout)
        item.hover()
        self.page.wait_for_timeout(500)

        # Click the three-dot button via JS — it may be hidden by CSS
        menu_btn = item.locator("#conversation-menu-action")
        menu_btn.wait_for(state="attached", timeout=timeout)
        menu_btn.evaluate("el => el.click()")
        self.page.wait_for_timeout(300)
        logger.info("Conversation context menu opened")

    @action("Rename conversation")
    def rename_conversation_via_menu(
        self, new_name: str, conv_name: str = None, timeout: int = 5000,
    ):
        """Rename a conversation using the three-dot → Rename flow.

        Opens the context menu, clicks *Rename*, clears the inline input,
        types *new_name*, and presses Enter to confirm.

        Args:
            new_name: The new conversation name.
            conv_name: Current name of the conversation (``None`` = first).
            timeout: Maximum wait time in milliseconds.
        """
        logger.info("Renaming conversation to '%s'", new_name)
        self.open_conversation_menu(conv_name, timeout=timeout)

        # Click "Rename" menu item (was "Edit" in older versions)
        self.page.locator('[role="menuitem"]:has-text("Rename")').click()
        self.page.wait_for_timeout(500)

        # Find the inline rename input (MUI Input or textbox)
        rename_input = self.page.locator(
            "input.MuiInputBase-input.MuiInput-input, "
            '[class*="conversation"] input, '
            'input[type="text"]'
        ).first
        rename_input.wait_for(state="visible", timeout=timeout)
        rename_input.clear()
        rename_input.fill(new_name)
        rename_input.press("Enter")
        self.page.wait_for_timeout(500)
        self.wait_for_network(timeout=timeout)
        logger.info("Conversation renamed to '%s'", new_name)

    @action("Delete conversation")
    def delete_conversation_via_menu(
        self, conv_name: str = None, timeout: int = 5000,
    ):
        """Delete a conversation via three-dot → Delete → confirm dialog.

        Args:
            conv_name: Name of the conversation to delete (``None`` = first).
            timeout: Maximum wait time in milliseconds.
        """
        logger.info("Deleting conversation via three-dot menu: %s", conv_name or "(first)")
        self.open_conversation_menu(conv_name, timeout=timeout)

        # Click "Delete" menu item
        self.page.locator('[role="menuitem"]:has-text("Delete")').click()

        # Handle confirmation dialog
        dialog = Dialog.wait_for(self.page, timeout=timeout)
        Dialog.click_button(dialog, "Delete")
        self.wait_for_network(timeout=timeout)
        logger.info("Conversation deleted via menu")

    def click_create_folder(self, timeout: int = 5000):
        """Click the "Create folder" button in the Conversations panel.

        Args:
            timeout: Maximum wait time in milliseconds.
        """
        logger.info("Clicking Create folder")
        btn = self.page.get_by_label("Create folder").get_by_role("button")
        btn.wait_for(state="visible", timeout=timeout)
        btn.click()

    def get_delete_button_count(self) -> int:
        """Get count of delete message buttons visible on the page.

        Delete buttons have aria-label="Delete" and appear on hover
        over messages. This count indicates the number of messages
        that have been interacted with or are actively shown.

        Returns:
            Number of delete buttons found
        """
        delete_btns = self.page.locator('button[aria-label="Delete"]')
        count = delete_btns.count()
        logger.info(f"Delete button count: {count}")
        return count

    def wait_for_conversation_url(self, conv_id: str, timeout: int = 10000):
        """Wait for URL to reflect the conversation ID.

        Args:
            conv_id: Conversation ID to wait for in URL
            timeout: Maximum wait time in milliseconds
        """
        logger.info(f"Waiting for URL to contain /chat/{conv_id}")
        self.page.wait_for_url(
            lambda url: f"/chat/{conv_id}" in url,
            timeout=timeout
        )

    def wait_for_naming_label_to_resolve(self, timeout: int = 10000):
        """Wait for 'Naming' placeholder to be replaced with actual title.

        After creating a conversation, the backend asynchronously generates
        a title based on the first message. The UI shows "Naming" as a
        placeholder until this completes.

        Args:
            timeout: Maximum wait time in milliseconds
        """
        logger.info("Waiting for 'Naming' label to resolve to actual title")
        naming_label = self.page.locator('text="Naming"')
        if naming_label.count() > 0:
            try:
                naming_label.first.wait_for(state="hidden", timeout=timeout)
                logger.info("Naming label resolved")
            except Exception as e:
                logger.info(f"Naming label did not resolve within timeout: {e}")

    def get_conversation_link_count(self) -> int:
        """Get count of conversation items in the sidebar list.

        Delegates to get_conversation_list_items() which locates role="button"
        elements inside the conversationList panel.

        Returns:
            Number of conversation items found
        """
        items = self.get_conversation_list_items()
        count = items.count()
        logger.info(f"Conversation link count: {count}")
        return count

    def get_conversation_link_titles(self, limit: int = 5) -> list[str]:
        """Get titles of conversations in sidebar (first N items).

        Returns text content of conversation list items, useful for verifying
        titles are not stuck on placeholder values like "Naming".

        Args:
            limit: Maximum number of titles to return

        Returns:
            List of conversation title strings
        """
        items = self.get_conversation_list_items()
        count = min(items.count(), limit)
        titles = [items.nth(i).text_content() or "" for i in range(count)]
        logger.info(f"Conversation link titles (first {limit}): {titles}")
        return titles

    def wait_for_conversations_to_load(self, timeout: int = 5000) -> bool:
        """Wait for at least one conversation to appear in sidebar.

        Returns True if conversations loaded, False if not available.
        Used to verify the conversation list populates after actions.

        Args:
            timeout: Maximum wait time in milliseconds

        Returns:
            True if conversations loaded, False otherwise
        """
        logger.info("Waiting for conversations to load in sidebar")
        items = self.get_conversation_list_items()
        try:
            items.first.wait_for(state="attached", timeout=timeout)
            logger.info("Conversations loaded")
            return True
        except Exception:
            logger.info("No conversations loaded within timeout")
            return False

    def click_delete_menu_item(self):
        """Click Delete menu item in conversation context menu.

        Must be called after open_conversation_menu() has been used
        to reveal the context menu.
        """
        logger.info("Clicking Delete menu item")
        self.page.locator('[role="menuitem"]:has-text("Delete")').click()

    # ------------------------------------------------------------------
    # Conversation context menu by id + delete-confirmation (ELITEA-2114)
    # ------------------------------------------------------------------
    # Distinct from open_conversation_menu()/click_delete_menu_item() above
    # (name-based targeting, raw #conversation-menu-action id + role-text
    # selectors — tracked tech debt, ELITEA-2114 Concrete Handles). These
    # target by conversation id and use the real per-item testids.

    def hover_conversation_item(self, conversation_id: str | int, timeout: int = 5000):
        """Hover *conversation_id*'s sidebar item to reveal its 3-dot menu button.

        The button is present in the DOM at all times but CSS
        ``display:none`` until hover (ConversationItem.jsx's ``menuWrapper``
        style) — this only hovers; it does not click.
        """
        item = self.page.locator(self.CONVERSATION_ITEM.format(conversation_id))
        item.wait_for(state="visible", timeout=timeout)
        item.hover()

    def get_conversation_menu_button(self, conversation_id: str | int):
        """Return the item-scoped 3-dot menu button Locator for *conversation_id*.

        Returns a Locator (not a bool) so the caller can assert visibility
        transitions with ``expect()`` — same precedent as
        ``get_conversation_list_items()``.
        """
        item = self.page.locator(self.CONVERSATION_ITEM.format(conversation_id))
        return item.locator(self.CONVERSATION_MENU_BUTTON)

    @action("Open conversation context menu")
    def open_conversation_context_menu(self, conversation_id: str | int, timeout: int = 5000):
        """Hover *conversation_id*'s sidebar item and click its scoped 3-dot menu button."""
        logger.info("Opening context menu for conversation %s", conversation_id)
        self.hover_conversation_item(conversation_id, timeout=timeout)
        menu_button = self.get_conversation_menu_button(conversation_id)
        menu_button.wait_for(state="visible", timeout=timeout)
        menu_button.click(force=True)

    def get_conversation_menu_item(self, item_key: str):
        """Return the Locator for a context-menu item by its stable key.

        *item_key* must be one of ``CONVERSATION_MENU_ITEM_KEYS``. Assumes
        the conversation's context menu is already open (see
        ``open_conversation_context_menu()``).
        """
        return self.page.locator(self.CONVERSATION_MENU_ITEM.format(item_key))

    def get_open_conversation_menu_item_count(self) -> int:
        """Return how many context-menu items are currently rendered.

        Scoped to whichever conversation's menu is open (menus unmount
        their items while closed, so this can't pick up a stale menu).
        """
        return self.page.locator(self.CONVERSATION_MENU_ITEM_PREFIX).count()

    @action("Click conversation context-menu item")
    def click_conversation_menu_item(self, item_key: str, timeout: int = 5000):
        """Click a context-menu item (e.g. ``"delete"``) by its stable key.

        See ``CONVERSATION_MENU_ITEM_KEYS``. Distinct from the pre-existing
        ``click_delete_menu_item()`` (raw ``:has-text("Delete")`` pattern,
        tracked tech debt) — this resolves the real per-item testid.
        """
        logger.info("Clicking conversation menu item: %s", item_key)
        item = self.get_conversation_menu_item(item_key)
        item.wait_for(state="visible", timeout=timeout)
        item.click()

    def is_conversation_active(self, conversation_id: str | int, timeout: int = 5000) -> bool:
        """Return True if *conversation_id*'s sidebar item carries ``data-active="true"``.

        Mirrors the project's state-via-data-attribute pattern
        (``data-expanded`` et al.) — a stable replacement for a CSS-class
        or URL-only proxy for "this row is the highlighted/active
        conversation" (ELITEA-2114).
        """
        item = self.page.locator(self.CONVERSATION_ITEM.format(conversation_id))
        item.wait_for(state="visible", timeout=timeout)
        return item.get_attribute("data-active") == "true"

    def wait_for_conversation_url_change(self, exclude_id: str | int, timeout: int = 10000):
        """Wait until the URL points at ``/chat/{some_id}`` where ``some_id != exclude_id``.

        Used after the ACTIVE conversation is deleted and the app
        auto-selects a replacement: the replacement's id isn't
        deterministic when other conversations exist in the project
        (ELITEA-2114 Automation Hints), so this asserts "moved to SOME
        other conversation" rather than a specific id.
        """
        exclude_str = str(exclude_id)
        logger.info("Waiting for URL to move away from conversation %s", exclude_str)
        self.page.wait_for_url(
            lambda url: bool(re.search(r"/chat/(\d+)", url)) and f"/chat/{exclude_str}" not in url,
            timeout=timeout,
        )

    @action("Confirm delete conversation")
    def confirm_delete_conversation(self, conversation_id: str | int, timeout: int = 10000):
        """Click the delete-confirm button and return the DELETE response.

        Waits for the network response so callers can assert its status
        code (e.g. 204) — proves the deletion is real, not just a
        client-side list splice (ELITEA-2114 Axis 2 addition).
        """
        with self.page.expect_response(
            lambda r: (
                r.request.method == "DELETE"
                and "/conversation/prompt_lib/" in r.url
                and str(conversation_id) in r.url
            ),
            timeout=timeout,
        ) as resp_info:
            self.delete_confirm_button.click()
        return resp_info.value

    # ------------------------------------------------------------------
    # Internal Tools / Image Creation
    # ------------------------------------------------------------------

    def open_internal_tools_menu(self, timeout: int = 5000):
        """Open the Modules panel via plus menu → Modules.

        Clicks plus menu, then "Modules" menuitem to reveal the tools
        panel with toggles for Image creation, Data Analysis, Planner, etc.

        Args:
            timeout: Maximum wait time in milliseconds

        Raises:
            FeatureNotAvailableError: If the plus menu or Modules menuitem
                is not visible
        """
        logger.info("Opening modules menu via plus menu")

        # Step 1: Open plus menu
        if not self.plus_menu_button.is_visible():
            raise FeatureNotAvailableError(
                "Plus menu button not visible — feature may not be available "
                "in current UI version"
            )
        self.plus_menu_button.wait_for(state="visible", timeout=timeout)
        self.plus_menu_button.click()
        self.page.wait_for_timeout(300)  # Menu animation

        # Step 2: Hover "Modules" menuitem to reveal submenu
        # The submenu is triggered by onMouseEnter, not onClick
        self.internal_tools_menuitem.wait_for(state="visible", timeout=timeout)
        self.internal_tools_menuitem.hover()

        # Wait for the tools panel with switches to appear
        self.page.locator('[role="switch"]').first.wait_for(
            state="visible", timeout=timeout
        )
        logger.info("Modules menu opened")

    def get_visible_switch_count(self) -> int:
        """Count visible toggle switches in internal tools panel.

        Use after open_internal_tools_menu() to verify expected tool count.

        Returns:
            Number of visible switch elements
        """
        return self.page.locator('[role="switch"]').count()

    @action("Enable image creation")
    def enable_image_creation(self, timeout: int = 5000):
        """Enable the Image creation toggle in internal tools menu.

        Opens the internal tools menu if not already open, then enables
        the Image creation switch.

        Args:
            timeout: Maximum wait time in milliseconds
        """
        logger.info("Enabling Image creation")

        # Check if menu is already open by looking for the switch
        image_switch = self.page.get_by_role("switch", name="Image creation")
        if image_switch.count() == 0:
            self.open_internal_tools_menu(timeout=timeout)
            image_switch = self.page.get_by_role("switch", name="Image creation")

        image_switch.wait_for(state="visible", timeout=timeout)

        # Check if already enabled (checked attribute)
        is_checked = image_switch.is_checked()
        if not is_checked:
            image_switch.click()
            logger.info("Image creation enabled")
        else:
            logger.info("Image creation was already enabled")

        # Close the menu by clicking elsewhere
        self.page.keyboard.press("Escape")
        self.page.wait_for_timeout(300)

    @action("Disable image creation")
    def disable_image_creation(self, timeout: int = 5000):
        """Disable the Image creation toggle in internal tools menu.

        Args:
            timeout: Maximum wait time in milliseconds
        """
        logger.info("Disabling Image creation")

        image_switch = self.page.get_by_role("switch", name="Image creation")
        if image_switch.count() == 0:
            self.open_internal_tools_menu(timeout=timeout)
            image_switch = self.page.get_by_role("switch", name="Image creation")

        image_switch.wait_for(state="visible", timeout=timeout)

        is_checked = image_switch.is_checked()
        if is_checked:
            image_switch.click()
            logger.info("Image creation disabled")
        else:
            logger.info("Image creation was already disabled")

        self.page.keyboard.press("Escape")
        self.page.wait_for_timeout(300)

    def is_image_creation_enabled(self, timeout: int = 5000) -> bool:
        """Check if Image creation toggle is enabled.

        Args:
            timeout: Maximum wait time in milliseconds

        Returns:
            True if Image creation is enabled, False otherwise
        """
        image_switch = self.page.get_by_role("switch", name="Image creation")
        if image_switch.count() == 0:
            self.open_internal_tools_menu(timeout=timeout)
            image_switch = self.page.get_by_role("switch", name="Image creation")

        image_switch.wait_for(state="visible", timeout=timeout)
        is_checked = image_switch.is_checked()

        self.page.keyboard.press("Escape")
        self.page.wait_for_timeout(300)

        return is_checked

    @action("Select model")
    def select_model(self, model_name: str, timeout: int = 5000):
        """Select a specific LLM model from the model selector.

        Args:
            model_name: Name of the model to select (e.g., "GPT-5.2", "Claude 4.6 Sonnet")
            timeout: Maximum wait time in milliseconds
        """
        logger.info(f"Selecting model: {model_name}")

        # Click the model selector to open the dropdown
        self.model_selector.first.click()

        # Wait for menu to appear
        menu = self.page.locator('[role="menu"], [role="listbox"]')
        menu.first.wait_for(state="visible", timeout=timeout)

        # Find and click the model option
        model_option = self.page.locator(f'[role="menuitem"]:has-text("{model_name}")')
        model_option.wait_for(state="visible", timeout=timeout)
        model_option.click()

        # Wait for menu to close and selection to apply
        self.page.wait_for_timeout(500)
        logger.info(f"Model '{model_name}' selected")

    def get_images_in_last_message(self) -> int:
        """Get count of generated images in the last message.

        Returns:
            Number of meaningful images (> 50px) in the last message,
            excluding small UI elements like the sender avatar.
        """
        last_msg = self.messages_container.last
        images = last_msg.locator('img:not([alt="EliteaStage"]):not([class*="avatar"])')
        count = sum(
            1 for i in range(images.count())
            if (box := images.nth(i).bounding_box()) and box["width"] > 50 and box["height"] > 50
        )
        logger.info(f"Found {count} images in last message")
        return count

    def wait_for_image_in_response(self, timeout: int = 60000):
        """Wait for a generated image in the last AI message, failing fast if generation ends without one.

        Uses native browser-side polling (wait_for_function, 100ms interval). Returns as soon
        as an image is found. If the send button re-enables with no image, raises AssertionError
        immediately rather than waiting out the full timeout.

        Avatar images (alt='Elitea' / alt='EliteaStage') are excluded.

        Args:
            timeout: Maximum wait time in milliseconds

        Raises:
            AssertionError: If AI finished responding with no image in last message
            TimeoutError: If timeout is reached before either condition
        """
        from playwright.sync_api import TimeoutError as PlaywrightTimeoutError

        logger.info("Waiting for image in last AI message (timeout=%dms)...", timeout)
        try:
            handle = self.page.wait_for_function(
                """() => {
                    const msgs = document.querySelectorAll(
                        'main ul.MuiList-root > li.MuiListItem-root'
                    );
                    if (!msgs.length) return null;
                    const lastMsg = msgs[msgs.length - 1];

                    // Non-avatar image present — success
                    for (const img of lastMsg.querySelectorAll('img')) {
                        const alt = img.alt || '';
                        if (alt !== 'Elitea' && alt !== 'EliteaStage' && img.src?.length > 0) {
                            return 'image';
                        }
                    }

                    // Fail fast: send button enabled means generation is complete
                    // Use multiple selectors with case-insensitive aria-label match
                    const btn = document.querySelector(
                        '[data-testid="chat-send-button"], button[aria-label*="send" i], button[type="submit"]'
                    );
                    if (btn && !btn.disabled && btn.getAttribute('aria-disabled') !== 'true') {
                        return 'done';
                    }

                    return null;
                }""",
                timeout=timeout,
            )
        except PlaywrightTimeoutError:
            raise TimeoutError(f"No image appeared in response within {timeout}ms")

        result = handle.json_value()
        if result == "image":
            logger.info("Image found in last AI message")
        elif result == "done":
            raise AssertionError("AI finished responding but no image found in last message")

    def get_generated_image_src(self) -> str | None:
        """Get the source URL of the generated image in the last message.

        Skips small UI elements (like the sender avatar, which is < 50px) and
        returns the src of the first large image (width > 50px AND height > 50px).

        Returns:
            Image source URL or None if no generated image found
        """
        last_msg = self.messages_container.last
        images = last_msg.locator('img:not([alt="EliteaStage"]):not([class*="avatar"])')
        for i in range(images.count()):
            img = images.nth(i)
            box = img.bounding_box()
            if box and box["width"] > 50 and box["height"] > 50:
                src = img.get_attribute("src")
                logger.info(f"Generated image src: {src[:50] if src else 'None'}...")
                return src
        return None

    # ------------------------------------------------------------------
    # Participants Panel helpers
    # ------------------------------------------------------------------

    def is_participants_panel_expanded(self) -> bool:
        """Return True if the Participants panel is expanded (showing full content).

        In v2.0.3+, the Participants panel is collapsed by default. When collapsed,
        only a narrow strip with icons is visible. When expanded, the full
        "Participants" title and "Context Budget" section are visible.

        Returns:
            True if the panel is expanded (Participants title is visible).
        """
        participants_title = self.page.locator('main').get_by_text("Participants", exact=True)
        return participants_title.count() > 0 and participants_title.first.is_visible()

    def expand_participants_panel(self, timeout: int = 5000) -> bool:
        """Expand the Participants panel if it's currently collapsed.

        In v2.0.3+, the Participants panel is collapsed by default per AC2.
        This method finds and clicks the expand button (DoubleLeftIcon) to
        show the full panel with Context Budget.

        Args:
            timeout: Maximum wait time in milliseconds.

        Returns:
            True if panel is now expanded, False if expand button not found.
        """
        if self.is_participants_panel_expanded():
            logger.info("Participants panel already expanded")
            return True

        logger.info("Attempting to expand Participants panel...")

        # The expand button is in the collapsed panel area on the right side.
        # It's a button containing the DoubleLeftIcon (chevron pointing left).
        # Look for buttons in the rightmost area of main that aren't in the chat area.
        expand_btn = self.page.evaluate("""() => {
            // Find the collapsed participants panel expand button
            // It's the button in the rightmost section that shows a percentage (0%)
            const mainEl = document.querySelector('main');
            if (!mainEl) return false;

            // Look for buttons near a percentage display (collapsed Context Budget shows "0%")
            const allButtons = mainEl.querySelectorAll('button');
            for (const btn of allButtons) {
                const parent = btn.parentElement;
                if (parent && parent.textContent && /\\d+%/.test(parent.textContent)) {
                    btn.click();
                    return true;
                }
            }

            // Alternative: find the rightmost button in main that's not the message actions
            const rect = mainEl.getBoundingClientRect();
            const rightThreshold = rect.right - 100;  // Within 100px of right edge
            for (const btn of allButtons) {
                const btnRect = btn.getBoundingClientRect();
                if (btnRect.left > rightThreshold && !btn.getAttribute('aria-label')) {
                    btn.click();
                    return true;
                }
            }
            return false;
        }""")

        if expand_btn:
            self.page.wait_for_timeout(500)  # Wait for animation
            if self.is_participants_panel_expanded():
                logger.info("Successfully expanded Participants panel")
                return True

        logger.warning("Could not find Participants panel expand button")
        return False

    def collapse_participants_panel(self, timeout: int = 5000) -> bool:
        """Collapse the Participants panel if it's currently expanded.

        Args:
            timeout: Maximum wait time in milliseconds.

        Returns:
            True if panel is now collapsed, False if collapse button not found.
        """
        if not self.is_participants_panel_expanded():
            logger.info("Participants panel already collapsed")
            return True

        logger.info("Attempting to collapse Participants panel...")

        # The collapse button is next to the "Participants" title
        participants_title = self.page.locator('main').get_by_text("Participants", exact=True)
        if participants_title.count() > 0:
            # Find the button in the same container as the title
            parent = participants_title.first.locator("xpath=ancestor::div[1]")
            collapse_btn = parent.locator('button')
            if collapse_btn.count() > 0:
                collapse_btn.first.click()
                self.page.wait_for_timeout(500)  # Wait for animation
                if not self.is_participants_panel_expanded():
                    logger.info("Successfully collapsed Participants panel")
                    return True

        logger.warning("Could not find Participants panel collapse button")
        return False

    # ------------------------------------------------------------------
    # Context Budget helpers
    # ------------------------------------------------------------------

    def is_context_budget_panel_visible(self) -> bool:
        """Return True if the Context Budget panel is visible in the sidebar.

        The panel only appears after at least one message has been sent in
        the conversation.

        Returns:
            True if the Context Budget heading is visible.
        """
        budget_heading = self.page.locator('main').get_by_text("Context Budget", exact=True)
        visible = budget_heading.count() > 0 and budget_heading.first.is_visible()
        logger.info("Context Budget panel visible: %s", visible)
        return visible

    def wait_for_context_budget_panel(self, timeout: int = 10000) -> None:
        """Wait until the Context Budget panel becomes visible.

        In v2.0.3+, the Participants panel (containing Context Budget) is
        collapsed by default. This method will automatically expand the panel
        if needed before waiting for the Context Budget heading.

        Should be called after sending the first message in a conversation.

        Args:
            timeout: Maximum wait time in milliseconds.

        Raises:
            TimeoutError: If the panel does not appear within *timeout*.
        """
        logger.info("Waiting for Context Budget panel to appear...")

        # First, expand the Participants panel if it's collapsed (v2.0.3+ behavior)
        if not self.is_participants_panel_expanded():
            logger.info("Participants panel is collapsed, expanding it first...")
            self.expand_participants_panel(timeout=timeout // 2)

        budget_heading = self.page.locator('main').get_by_text("Context Budget", exact=True)
        budget_heading.wait_for(state="visible", timeout=timeout)
        logger.info("Context Budget panel is visible")

    def get_context_budget_tokens_text(self) -> str:
        """Return the raw tokens display string from the Context Budget panel.

        The text has the format ``"22 / 64 000 tokens"`` (may include spaces
        in the number for locale formatting).

        Returns:
            Raw text of the token usage line (e.g. ``"22 / 64 000 tokens"``).

        Raises:
            TimeoutError: If the panel is not visible.
        """
        # Find the token display by matching text pattern "N / M tokens"
        # The element is inside the Context Budget panel in the right sidebar
        token_locator = self.page.locator('main').get_by_text(re.compile(r"\d+\s*/\s*[\d\s]+tokens"))
        text = token_locator.first.text_content() or ""
        logger.info("Context Budget tokens display: %r", text)
        return text.strip()

    def get_context_budget_max_tokens(self) -> int:
        """Parse and return the max-tokens value from the Context Budget panel.

        Extracts the second number from ``"22 / 64 000 tokens"``-style text,
        stripping spaces used as thousands separators.

        Returns:
            Max token limit as integer (e.g. 64000 from ``"22 / 64 000 tokens"``).

        Raises:
            ValueError: If the text cannot be parsed.
        """
        text = self.get_context_budget_tokens_text()
        # Format: "N / M tokens" where M may contain spaces (locale thousands sep)
        # e.g. "22 / 64 000 tokens" → max=64000
        # Note: May contain narrow no-break space (\u202f) or regular space
        try:
            after_slash = text.split("/")[1]  # " 64 000 tokens"
            numeric_part = after_slash.replace("tokens", "").strip()  # "64 000"
            # Remove all whitespace characters including Unicode spaces
            cleaned = re.sub(r"[\s\u00a0\u202f,]+", "", numeric_part)
            max_tokens = int(cleaned)
            logger.info("Parsed max tokens from Context Budget: %d", max_tokens)
            return max_tokens
        except (IndexError, ValueError) as exc:
            raise ValueError(
                f"Cannot parse max tokens from Context Budget text: {text!r}"
            ) from exc

    def get_context_budget_messages_count(self) -> str:
        """Return the Messages counter text from the Context Budget panel (e.g. "4").

        Uses the dedicated ``context-budget-messages-count`` testid rather
        than regex-parsing the whole panel's ``textContent``.

        This is a one-shot read — the counter updates asynchronously shortly
        after the panel becomes visible, so call
        ``wait_for_context_budget_messages_count()`` first when a specific
        value is expected (mirrors the ``wait_for_message_count()`` +
        ``get_message_count()`` pattern used elsewhere in this class).
        """
        text = self.context_budget_messages_count.first.text_content() or ""
        return text.strip()

    def wait_for_context_budget_messages_count(self, expected: str, timeout: int = 10000) -> None:
        """Wait until the Context Budget Messages counter reads *expected*.

        The counter updates asynchronously shortly after the Context Budget
        panel/heading becomes visible — a one-shot read immediately after
        ``wait_for_context_budget_panel()`` can observe a stale value (e.g.
        "0") before the real count renders (confirmed live: PR #693 review
        round 2 reproduced a failure reading '0' where the failure
        screenshot, captured moments later, already showed the correct
        value rendered). Call this before ``get_context_budget_messages_count()``
        whenever a specific value is expected.

        Args:
            expected: Expected counter text (e.g. "4").
            timeout: Maximum wait time in milliseconds.

        Raises:
            TimeoutError: If the counter does not reach *expected* within *timeout*.
        """
        logger.info("Waiting for Context Budget Messages counter to read %r", expected)
        target = self.context_budget_messages_count.filter(
            has_text=re.compile(rf"^\s*{re.escape(expected)}\s*$")
        )
        target.first.wait_for(state="visible", timeout=timeout)
        logger.info("Context Budget Messages counter reached %r", expected)

    def get_context_budget_summaries_count(self) -> str:
        """Return the Summaries counter text from the Context Budget panel (e.g. "0").

        Uses the dedicated ``context-budget-summaries-count`` testid rather
        than regex-parsing the whole panel's ``textContent``.

        This is a one-shot read — see
        ``get_context_budget_messages_count()`` docstring for why
        ``wait_for_context_budget_summaries_count()`` should be called first
        when a specific value is expected.
        """
        text = self.context_budget_summaries_count.first.text_content() or ""
        return text.strip()

    def wait_for_context_budget_summaries_count(self, expected: str, timeout: int = 10000) -> None:
        """Wait until the Context Budget Summaries counter reads *expected*.

        See ``wait_for_context_budget_messages_count()`` for why this poll
        is needed — the same async-update race applies to the Summaries
        counter.

        Args:
            expected: Expected counter text (e.g. "0").
            timeout: Maximum wait time in milliseconds.

        Raises:
            TimeoutError: If the counter does not reach *expected* within *timeout*.
        """
        logger.info("Waiting for Context Budget Summaries counter to read %r", expected)
        target = self.context_budget_summaries_count.filter(
            has_text=re.compile(rf"^\s*{re.escape(expected)}\s*$")
        )
        target.first.wait_for(state="visible", timeout=timeout)
        logger.info("Context Budget Summaries counter reached %r", expected)

    def open_add_teammate_dialog(self, timeout: int = 5000) -> tuple[bool, str]:
        """Open the 'Invite Users' dialog via the plus menu.

        In v2.0.3+, adding teammates/users is done via the plus menu → "Invite Users"
        option. This option is ONLY available in Team Projects (not Private Projects).

        Per story #5188 AC3: "Adding Participants is Only Allowed via the `+` Icon"
        The "Invite Users" menuitem only appears when:
        - The project is a Team Project (not Private)
        - The user has permission to invite others

        Args:
            timeout: Maximum wait time in milliseconds

        Returns:
            Tuple of (success: bool, reason: str)
            - (True, "") if dialog opened successfully
            - (False, reason) if feature not available with explanation
        """
        logger.info("Attempting to open Invite Users dialog via plus menu")

        # Open the plus menu
        plus_menu = self.page.get_by_role("button", name="plus menu")
        if not plus_menu.is_visible():
            return (False, "Plus menu button not visible")

        plus_menu.click()
        self.page.wait_for_timeout(500)

        # Look for "Invite Users" menuitem in the plus menu
        invite_users = self.page.get_by_role("menuitem", name="Invite Users")

        if invite_users.count() == 0:
            # Close the menu
            self.page.keyboard.press("Escape")
            logger.info("'Invite Users' not found in plus menu — likely a Private Project")
            return (False, "Invite Users option not available — this feature is only available in Team Projects, not Private Projects (per story #5188)")

        if not invite_users.is_enabled():
            self.page.keyboard.press("Escape")
            logger.info("'Invite Users' is disabled — user may not have permission")
            return (False, "Invite Users option is disabled — user may not have invite permissions")

        invite_users.click()
        self.page.wait_for_timeout(500)

        # Wait for a user picker dialog
        picker = self.page.locator(
            '[role="dialog"], [role="listbox"], '
            'input[placeholder*="user" i], input[placeholder*="email" i], '
            'input[placeholder*="search" i]'
        )
        try:
            picker.first.wait_for(state="visible", timeout=timeout)
            logger.info("Invite Users dialog opened")
            return (True, "")
        except Exception as e:
            logger.warning(f"Invite Users dialog did not appear: {e}")
            return (False, f"Dialog did not appear after clicking Invite Users: {e}")

    # ------------------------------------------------------------------
    # Participant management helpers
    # ------------------------------------------------------------------

    def wait_for_add_agent_button(self, timeout: int = 15000) -> None:
        """Wait for the 'plus menu' button to be visible (entry point for adding agents)."""
        self.page.get_by_role("button", name="plus menu").wait_for(state="visible", timeout=timeout)

    @action("Add agent participant")
    def add_agent_participant(self, agent_name_prefix: str, timeout: int = 10000):
        """Add an agent as a chat participant via the plus menu → Agents flow.

        Opens the plus menu, clicks 'Agents', searches for agents whose name starts with
        *agent_name_prefix*, selects the first result, and waits for the agent to be added.

        Args:
            agent_name_prefix: Search prefix (e.g. "autotest_")
            timeout: Maximum wait time in milliseconds
        """
        logger.info("Adding agent participant with prefix '%s'", agent_name_prefix)

        # Step 1: Open plus menu
        plus_btn = self.page.get_by_role("button", name="plus menu")
        plus_btn.wait_for(state="visible", timeout=timeout)
        plus_btn.click(force=True)
        self.page.wait_for_timeout(300)  # Menu animation

        # Step 2: Click "Agents" menuitem
        agents_menu = self.page.get_by_role("menuitem", name="Agents")
        agents_menu.wait_for(state="visible", timeout=timeout)
        agents_menu.click()
        self.page.wait_for_timeout(300)  # Submenu animation

        # Step 3: Search for agent in the search input
        search_input = self.page.get_by_placeholder("Search agents...")
        search_input.wait_for(state="visible", timeout=timeout)
        search_input.click()
        search_input.press_sequentially(agent_name_prefix, delay=50)
        self.page.wait_for_timeout(500)  # Search debounce

        # Step 4: Select the agent from results
        agent_item = self.page.locator(
            f'li[role="menuitem"]:has-text("{agent_name_prefix}")'
        ).first
        agent_item.wait_for(state="visible", timeout=timeout)
        agent_item.click()

        # Wait for the API write to complete
        self.wait_for_network(timeout=timeout)

        logger.info("Agent added as chat participant")

    @action("Add toolkit participant")
    def add_toolkit_participant(self, toolkit_name: str, timeout: int = 10000):
        """Add a toolkit as a chat participant via the plus menu → Toolkits flow.

        Opens the plus menu, clicks 'Toolkits', searches for toolkits whose name
        contains *toolkit_name*, selects the first result, and waits for the
        toolkit to be added.

        Args:
            toolkit_name: Toolkit name or prefix to search for
            timeout: Maximum wait time in milliseconds
        """
        logger.info("Adding toolkit participant '%s'", toolkit_name)

        # Step 1: Open plus menu
        plus_btn = self.page.get_by_role("button", name="plus menu")
        plus_btn.wait_for(state="visible", timeout=timeout)
        plus_btn.click(force=True)
        self.page.wait_for_timeout(300)  # Menu animation

        # Step 2: Click "Toolkits" menuitem
        toolkits_menu = self.page.get_by_role("menuitem", name="Toolkits")
        toolkits_menu.wait_for(state="visible", timeout=timeout)
        toolkits_menu.click()
        self.page.wait_for_timeout(300)  # Submenu animation

        # Step 3: Search for toolkit in the search input
        search_input = self.page.get_by_placeholder("Search toolkits...")
        search_input.wait_for(state="visible", timeout=timeout)
        search_input.click()
        search_input.press_sequentially(toolkit_name[:20], delay=50)
        self.page.wait_for_timeout(500)  # Search debounce

        # Step 4: Select the toolkit from results
        toolkit_item = self.page.locator(
            f'li[role="menuitem"]:has-text("{toolkit_name[:15]}")'
        ).first
        toolkit_item.wait_for(state="visible", timeout=timeout)
        toolkit_item.click()

        # Wait for the API write to complete
        self.wait_for_network(timeout=timeout)

        logger.info("Toolkit '%s' added as chat participant", toolkit_name)

    def is_agent_participant_in_composer(self, agent_name: str, timeout: int = 10000) -> bool:
        """Return True if *agent_name* is shown as the active agent in the composer.

        LOCATOR: ``chat-switch-participant-button`` — the composer's
        active-participant button, added to EliteaUI on ``automation/testids``
        during the ELITEA-1736 testid rework (draft PR EliteaAI/EliteaUI#541).
        Previously located via its Tooltip-derived accessible name
        ("Switch Agent"/"Switch Pipeline"); the testid resolves the same
        physical element regardless of which participant type is active.
        Replaces the model-name display used when no agent participant is
        active.

        NOTE (ELITEA-1736 Phase-2 exploration): the "Agents in this
        conversation" collapsed-participants badge documented in the AFS
        renders its participant count via a CSS ``::after`` pseudo-element
        (``content: "${count}"`` in ``CollapsedPerticapantsList.jsx``), which
        has no DOM text node and is not readable via ``text_content()`` or
        any accessible-name query — confirmed by reading the EliteaUI
        source. This button is the stable, semantic signal instead; the
        AFS's own Expected Results names both as equivalent evidence of
        participant membership.

        Args:
            agent_name: The agent's exact display name.
            timeout: Maximum wait time in milliseconds.
        """
        switch_participant_btn = self.switch_participant_button
        switch_participant_btn.wait_for(state="visible", timeout=timeout)
        text = switch_participant_btn.text_content() or ""
        found = agent_name in text
        logger.info(
            "Switch-participant composer button text: %r — contains agent name %r: %s",
            text, agent_name, found,
        )
        return found

    def is_switch_agent_button_visible(self, timeout: int = 3000) -> bool:
        """Return True if the active-participant composer button currently exists.

        Unlike ``is_agent_participant_in_composer()`` (which asserts a
        *positive* expectation and raises if the button never appears —
        the correct behavior for its existing callers), this is a safe
        boolean check for callers that need to assert the button's
        *absence* (e.g. after removing the last agent participant) without
        a TimeoutError. Added for ELITEA-1793; the two methods are
        intentionally not merged to keep ``is_agent_participant_in_composer``'s
        existing raise-on-timeout contract byte-identical for its callers.

        Args:
            timeout: Maximum wait time in milliseconds.
        """
        try:
            self.switch_participant_button.wait_for(
                state="visible", timeout=timeout,
            )
            return True
        except Exception:
            return False

    @action("Send chat message with skill mention")
    def send_message_with_skill_mention(
        self, skill_name: str, prompt: str, timeout: int = 10000,
    ):
        """Type "~<skill_name> <prompt>" in the main chat input and send it.

        Same "Mention skill" popper mechanics as
        ``AgentDetailPage.send_chat_message_with_mention`` (``MentionSkillList``
        — a plain div-based list, now testid-backed: ``skill-mention-list``
        for the container and ``skill-mention-item-{name}`` per row, added to
        EliteaUI on ``automation/testids`` during the sibling ELITEA-1735
        rework, commit 916fcc3, draft PR EliteaAI/EliteaUI#540; confirmed
        already live for this chat-participant surface too during the
        ELITEA-1736 testid rework). Uses ``press_sequentially`` throughout —
        never ``fill()`` — because filling the whole textbox value would
        destroy the mention chip inserted after selecting from the popper.

        Args:
            skill_name: Exact name of the attached skill to mention.
            prompt: Text to append after the mention chip.
            timeout: Maximum wait time in milliseconds.
        """
        logger.info("Sending mention message: ~%s %s", skill_name, prompt[:60])
        self.message_input.wait_for(state="visible", timeout=timeout)
        self.message_input.click()
        self.message_input.press_sequentially("~", delay=50)

        self.mention_skill_list.wait_for(state="visible", timeout=timeout)
        mention_item = self.mention_skill_list.locator(
            self.MENTION_SKILL_ITEM.format(skill_name)
        )
        mention_item.wait_for(state="visible", timeout=timeout)
        mention_item.click()
        self.page.wait_for_timeout(300)

        self.message_input.press_sequentially(f" {prompt}", delay=30)
        self.page.wait_for_timeout(300)

        self.send_button.wait_for(state="visible", timeout=timeout)
        self.send_button.click(force=True, timeout=timeout)
        logger.info("Mention message sent (~%s)", skill_name)

    # ------------------------------------------------------------------
    # Participant removal + "Mention skill" popper inspection (ELITEA-1793)
    # ------------------------------------------------------------------

    def is_participants_badge_visible(self, timeout: int = 3000, section: str = "agents") -> bool:
        """Return True if the participants badge for *section* exists in the DOM.

        LOCATOR: ``chat-participants-badge-{section}`` (dynamic per entity
        section) — added to EliteaUI on ``automation/testids`` during the
        ELITEA-1793 testid rework (draft PR EliteaAI/EliteaUI#548, closing
        the framework-alignment audit's gap on PR #52's raw
        ``[aria-label="Agents in this conversation"]`` handle). This
        container **disappears entirely from the DOM** once the
        participant count returns to 0 for that section (it is not
        rendered showing a "0" label) — callers must assert absence via
        this method, not a text-content check for "0".

        Args:
            timeout: Maximum wait time in milliseconds.
            section: Entity section — "agents" (default), "pipelines",
                "toolkits", or "mcp". This case only ever exercises "agents".
        """
        badge = self.page.locator(self.PARTICIPANTS_BADGE.format(section))
        try:
            badge.first.wait_for(state="visible", timeout=timeout)
            return True
        except Exception:
            return False

    def get_participants_user_avatar_text(self, timeout: int = 5000) -> str:
        """Return the initials/text on the expanded PARTICIPANTS panel's USERS avatar.

        Must be called after ``expand_participants_panel()``. Used to read
        WHICH participant is shown (e.g. "TB"), not merely that a USERS
        section is present — case step 8 asks for "the correct participant".

        Args:
            timeout: Maximum wait time in milliseconds.
        """
        self.participants_users_avatar.first.wait_for(state="visible", timeout=timeout)
        return (self.participants_users_avatar.first.text_content() or "").strip()

    def open_participants_popover(self, timeout: int = 10000, section: str = "agents"):
        """Click the participants badge for *section* to open the participants popper.

        LOCATORS: ``chat-participants-badge-{section}`` (badge wrapper) →
        ``chat-participants-badge-button`` (its clickable IconButton,
        scoped under the badge wrapper) → ``chat-participants-popper`` (the
        opened Popper/Grow content container) — all added to EliteaUI on
        ``automation/testids`` during the ELITEA-1793 testid rework, closing
        the framework-alignment audit's gap on PR #52's raw
        ``[aria-label=...]`` + CSS-tag-and-text-filter + xpath-ancestor
        handles.

        Returns the ``participants_popper`` Locator.

        Args:
            timeout: Maximum wait time in milliseconds.
            section: Entity section — "agents" (default), "pipelines",
                "toolkits", or "mcp". This case only ever exercises "agents".
        """
        badge_container = self.page.locator(self.PARTICIPANTS_BADGE.format(section))
        badge_button = badge_container.locator(self.PARTICIPANTS_BADGE_BUTTON)
        badge_button.first.wait_for(state="visible", timeout=timeout)
        badge_button.first.click()

        self.participants_popper.wait_for(state="visible", timeout=timeout)
        return self.participants_popper

    @action("Remove agent participant from chat")
    def remove_agent_participant(self, agent_id: int, timeout: int = 10000):
        """Remove the agent participant identified by *agent_id* from chat.

        Opens the participants popper, resolves the participant row
        directly via its dynamic ``chat-participant-row-{uniqueId}``
        testid (``uniqueId`` = ``getChatParticipantUniqueId(participant)``
        in EliteaUI — for an agent participant this is
        ``application_{agent_id}_{project_id}``, confirmed both live and by
        reading ``participants.helpers.js`` during the ELITEA-1793 testid
        rework), hovers it to reveal its hover-only "Remove agent" icon
        button (``chat-participant-remove-button``, same hover-reveal
        pattern as the agent-detail Skills card's remove control — see
        ``.agents/memory/qa-engineer/agent_skill_card_remove_control_quirks.md``),
        clicks it, and confirms via the "Remove agent?" dialog. No text
        lookup or xpath-ancestor walk needed — replaces PR #52's raw
        text-and-ancestor-walk and accessible-name-based handles.

        Args:
            agent_id: Numeric ID of the participant agent to remove.
            timeout: Maximum wait time in milliseconds.
        """
        logger.info("Removing agent participant id=%s from chat", agent_id)
        popper = self.open_participants_popover(timeout=timeout)

        unique_id = f"application_{agent_id}_{settings.elitea_project_id}"
        row = popper.locator(self.PARTICIPANT_ROW.format(unique_id))
        row.wait_for(state="visible", timeout=timeout)
        row.scroll_into_view_if_needed()
        row.hover()
        self.page.wait_for_timeout(300)  # hover-reveal CSS transition

        remove_btn = row.locator(self.PARTICIPANT_REMOVE_BUTTON)
        remove_btn.wait_for(state="visible", timeout=timeout)
        remove_btn.click(force=True)

        dialog = Dialog.wait_for(self.page, timeout=timeout)
        Dialog.click_button(dialog, "Remove")
        self.wait_for_network(timeout=timeout)

        # Residual real-mouse hover can keep :hover engaged on the wrong
        # element after the confirm click (same gotcha documented for the
        # agent-detail Skills card remove control, ELITEA-1792 implementer
        # memory) — reset before any subsequent hover-reveal check.
        self.page.mouse.move(0, 0)
        logger.info("Agent participant id=%s removed from chat", agent_id)

    @action("Open Mention skill popper")
    def open_mention_skill_popper(self, timeout: int = 10000):
        """Clear the message input and type "~" to open the "Mention skill" popper.

        Uses ``press_sequentially`` — never ``fill()`` — because a
        ``fill()`` bypasses the mention-trigger keyup handler and the
        popper never opens (same gotcha as ``send_message_with_skill_mention``).
        Clears any pre-existing content (e.g. a literal "~" left over from a
        previously dismissed popper — dismissing via Escape does NOT clear
        the input) via Control+a/Backspace before typing, so the trigger is
        always a single fresh "~" and never something like "~~" that no
        longer opens the popper.

        NOTE: the composer's message input is a *fresh* element after any
        re-render (e.g. right after an agent participant is added/removed) —
        ``self.message_input`` re-resolves the ``LocatorDescriptor`` on each
        access (a live ``get_by_test_id`` locator, not a captured element
        handle), so no manual re-snapshot/ref bookkeeping is needed here.

        Returns the ``mention_skill_list`` Locator (``skill-mention-list``
        testid — REUSE of the same field ``send_message_with_skill_mention``
        already uses; replaces PR #52's raw heading-text-and-ancestor-walk
        handle). Contains either skill-name rows (when the active agent participant
        has attached skills) or the empty-state row
        (``skill-mention-list-empty``, "No skills attached to this agent")
        when there is no participant, or the participant has no skills.

        Args:
            timeout: Maximum wait time in milliseconds.
        """
        self.message_input.wait_for(state="visible", timeout=timeout)
        self.message_input.click()
        self.message_input.press("Control+a")
        self.message_input.press("Backspace")
        self.message_input.press_sequentially("~", delay=50)

        self.mention_skill_list.wait_for(state="visible", timeout=timeout)
        return self.mention_skill_list

    def is_skill_in_mention_popper(self, popper, skill_name: str, timeout: int = 3000) -> bool:
        """Return True if *skill_name* appears as a row inside an open mention popper.

        First tries an exact match via the row's ``skill-mention-item-{name}``
        testid (``MENTION_SKILL_ITEM``, same pattern as
        ``send_message_with_skill_mention``). Falls back to a substring
        match across all mention-item rows (``MENTION_SKILL_ITEM_PREFIX``)
        for callers checking a row's *description* text rather than its
        exact name (e.g. this case's step 3 assertion) — replaces PR #52's
        raw exact-text-match handle.

        Args:
            popper: The popper container Locator returned by
                ``open_mention_skill_popper()``.
            skill_name: Exact skill name, or a substring of a row's text
                (e.g. its description) to look for.
            timeout: Maximum wait time in milliseconds.
        """
        try:
            exact_item = popper.locator(self.MENTION_SKILL_ITEM.format(skill_name))
            exact_item.first.wait_for(state="visible", timeout=timeout)
            return True
        except Exception:
            pass

        try:
            matching_rows = popper.locator(self.MENTION_SKILL_ITEM_PREFIX).filter(
                has_text=skill_name,
            )
            matching_rows.first.wait_for(state="visible", timeout=timeout)
            return True
        except Exception:
            return False

    def is_mention_popper_empty_state(self, popper, timeout: int = 3000) -> bool:
        """Return True if the mention popper shows the "No skills attached to this agent" empty state.

        LOCATOR: ``skill-mention-list-empty`` (``MENTION_LIST_EMPTY``) —
        added to EliteaUI on ``automation/testids`` during the ELITEA-1793
        testid rework, replacing PR #52's raw empty-state-text handle.

        Args:
            popper: The popper container Locator returned by
                ``open_mention_skill_popper()``.
            timeout: Maximum wait time in milliseconds.
        """
        try:
            popper.locator(self.MENTION_LIST_EMPTY).first.wait_for(
                state="visible", timeout=timeout,
            )
            return True
        except Exception:
            return False

    def dismiss_mention_popper(self):
        """Press Escape to dismiss an open "Mention skill" popper without selecting anything."""
        self.page.keyboard.press("Escape")

    def is_mention_popper_open(self, timeout: int = 2000) -> bool:
        """Return True if the "Mention skill" popper is currently visible.

        LOCATOR: ``mention_skill_list`` (``skill-mention-list`` testid) —
        REUSE of the same field used elsewhere in this file; replaces
        PR #52's raw heading-text handle.

        Args:
            timeout: Maximum wait time in milliseconds.
        """
        try:
            self.mention_skill_list.wait_for(state="visible", timeout=timeout)
            return True
        except Exception:
            return False

    # ------------------------------------------------------------------
    # UI state wait helpers
    # ------------------------------------------------------------------

    def wait_for_input_empty(self, timeout: int = 5000):
        """Wait until the message input textarea becomes empty.

        Encapsulates the raw page.wait_for_function pattern.
        Use after send_message_with_shift_enter() to confirm the message was submitted.

        Args:
            timeout: Maximum wait time in milliseconds
        """
        self.page.wait_for_function(
            """() => {
                const ta = document.querySelector('textarea#standard-multiline-static');
                return ta && ta.value.trim() === '';
            }""",
            timeout=timeout,
        )
        logger.info("Message input is empty")

    def wait_for_sidebar_collapsed(self, timeout: int = 5000):
        """Wait for the sidebar to collapse — expanded text labels become hidden.

        The sidebar is considered collapsed when the 'Agents' button's text
        is no longer visible (only icon remains in mini-sidebar mode).

        Args:
            timeout: Maximum wait time in milliseconds
        """
        # When collapsed, sidebar buttons show only icons, not text
        # Check for the text "Agents" being hidden (not the button itself)
        agents_text = self.page.locator('nav :text("Agents"), aside :text("Agents")').first
        try:
            agents_text.wait_for(state="hidden", timeout=timeout)
        except Exception:
            # Some deployments keep mini-sidebar visible; fall back to network settle
            self.page.wait_for_load_state("networkidle", timeout=timeout)
        logger.info("Sidebar collapsed")

    def get_internal_tool_switch(self, tool_name: str):
        """Get the toggle switch locator for a named internal tool.

        Must be called while the internal tools menu is open
        (after open_internal_tools_menu()).

        Args:
            tool_name: Accessible name of the tool
                (e.g. "Image creation", "Data Analysis", "Planner")

        Returns:
            Playwright Locator for the switch element
        """
        return self.page.get_by_role("switch", name=tool_name)

    # ------------------------------------------------------------------
    # TTS (Text-to-Speech) Controls
    # ------------------------------------------------------------------

    def is_voice_mini_player_visible(self) -> bool:
        """Check if Voice Mini Player is visible in chat.

        The Voice Mini Player should NOT be visible by default.
        It only appears when Read-out and Voice mode features are activated.

        Returns:
            True if Voice Mini Player is visible, False otherwise.
        """
        return self.voice_mini_player is not None and self.voice_mini_player.count() > 0 and self.voice_mini_player.first.is_visible()

    @action("Click read out button")
    def click_read_out(self, message_index: int = -1, timeout: int = 10000):
        """Click the 'Read out' (speaker) button on a message to start TTS.

        The read out button appears on AI messages and triggers text-to-speech
        playback. When clicked, a playback control bar appears with play/stop
        and settings controls.

        Args:
            message_index: Index of message (-1 for last AI message).
            timeout: Maximum wait time in milliseconds.
        """
        logger.info("Clicking Read out button on message %d", message_index)
        message = self.messages_container.nth(message_index)
        message.scroll_into_view_if_needed()
        message.hover()
        self.page.wait_for_timeout(500)

        # Find read out button by testid
        read_out_btn = message.locator('[data-testid="chat-read-out-button"]')

        # Wait for button to be visible and ENABLED (disabled while AI is generating)
        read_out_btn.first.wait_for(state="visible", timeout=timeout)
        # Wait until not disabled
        self.page.wait_for_function(
            """(selector) => {
                const btn = document.querySelector(selector);
                return btn && !btn.disabled;
            }""",
            arg='[data-testid="chat-read-out-button"]',
            timeout=timeout
        )
        read_out_btn.first.click()
        self.page.wait_for_timeout(500)
        logger.info("Read out button clicked, TTS playback started")

    def is_tts_playing(self) -> bool:
        """Check if TTS playback is currently active.

        Looks for the TTS control bar that appears during playback.

        Returns:
            True if TTS control bar is visible, False otherwise.
        """
        # Check for play/stop button in voice mini player using direct locator
        # (LocatorDescriptor raises error if testid not found, so use page.locator directly)
        try:
            locator = self.page.locator('[data-testid="chat-voice-play-stop-button"]')
            return locator.count() > 0 and locator.first.is_visible()
        except Exception:
            return False

    def wait_for_tts_controls(self, timeout: int = 5000):
        """Wait for TTS playback controls to become visible.

        The control bar appears after clicking Read out and contains
        play/stop button, settings gear, and volume controls.

        Args:
            timeout: Maximum wait time in milliseconds.
        """
        logger.info("Waiting for TTS playback controls...")
        # Wait for voice mini player to appear
        self.voice_mini_player.first.wait_for(state="visible", timeout=timeout)
        logger.info("TTS playback controls visible")

    @action("Open voice settings from TTS")
    def open_voice_settings_from_tts(self, timeout: int = 5000):
        """Open the Voice Settings dialog from the TTS playback control bar.

        Must be called while TTS playback is active (after click_read_out).
        Clicks the gear/settings icon in the TTS control bar.

        Args:
            timeout: Maximum wait time in milliseconds.

        Returns:
            Locator to the Voice Settings dialog.
        """
        from components.voice_settings import VoiceSettingsDialog

        logger.info("Opening Voice Settings from TTS control bar")
        self.voice_settings_button.first.wait_for(state="visible", timeout=timeout)
        self.voice_settings_button.first.click()

        dialog = VoiceSettingsDialog.wait_for(self.page, timeout=timeout)
        return dialog

    def trigger_tts_and_open_settings(self, message_index: int = -1, timeout: int = 10000):
        """Convenience method: trigger TTS on a message and open Voice Settings.

        Combines click_read_out and open_voice_settings_from_tts into a single
        action for tests that need to access voice settings from chat.

        Idempotent: if TTS is already playing (mini player visible), skips
        click_read_out and goes directly to opening settings. This allows
        tests to call this method multiple times without worrying about state.

        Args:
            message_index: Index of message (-1 for last).
            timeout: Maximum wait time in milliseconds.

        Returns:
            Locator to the Voice Settings dialog.
        """
        if not self.is_tts_playing():
            self.click_read_out(message_index=message_index, timeout=timeout)
            self.wait_for_tts_controls(timeout=timeout)
        return self.open_voice_settings_from_tts(timeout=timeout)

    # ------------------------------------------------------------------
    # Chat folder methods (ELITEA-2132)
    # ------------------------------------------------------------------

    @action("Open folder-name editor")
    def click_create_folder_button(self, timeout: int = 5000):
        """Click the CHATS header 'Create folder' icon (testid-based).

        Distinct from the legacy ``click_create_folder()`` (``get_by_label``,
        pre-dates the testid policy — left in place as tracked tech debt).
        New automation should use this method. Waits for the inline
        folder-name editor input to become visible before returning.

        Args:
            timeout: Maximum wait time in milliseconds.
        """
        logger.info("Clicking chat-create-folder-button")
        self.create_folder_button.wait_for(state="visible", timeout=timeout)
        self.create_folder_button.click()
        self.folder_name_input.wait_for(state="visible", timeout=timeout)
        logger.info("Folder-name editor opened")

    def get_folder_item(self, folder_id: str | int):
        """Return the Locator for a folder's whole accordion row (id-scoped).

        Args:
            folder_id: Numeric folder id (as returned by the create-folder
                response, or read back from the DOM).
        """
        return self.page.locator(self.FOLDER_ITEM.format(folder_id))

    def is_folder_expanded(self, folder_id: str | int) -> bool:
        """Return True if *folder_id*'s row carries ``data-expanded="true"``."""
        value = self.get_folder_item(folder_id).get_attribute("data-expanded")
        return value == "true"

    @action("Expand folder")
    def expand_folder(self, folder_id: str | int, timeout: int = 5000):
        """Click a folder row to expand it; waits for ``data-expanded`` to flip.

        Args:
            folder_id: Numeric folder id.
            timeout: Maximum wait time in milliseconds.
        """
        logger.info("Expanding folder %s", folder_id)
        self.get_folder_item(folder_id).click()
        expanded_item = self.page.locator(
            f'{self.FOLDER_ITEM.format(folder_id)}[data-expanded="true"]'
        )
        expanded_item.wait_for(state="visible", timeout=timeout)
        logger.info("Folder %s expanded", folder_id)

    def get_folder_empty_state_text(self, folder_id: str | int) -> str:
        """Return the empty-state text scoped inside *folder_id*'s row.

        Args:
            folder_id: Numeric folder id.
        """
        item = self.get_folder_item(folder_id)
        return item.locator(self.FOLDER_EMPTY_STATE).text_content() or ""

    @action("Delete folder via menu")
    def delete_folder_via_menu(self, folder_id: str | int, timeout: int = 5000):
        """Delete a folder via its scoped 3-dot menu -> Delete -> confirm dialog.

        Mirrors the id-scoped delete flow used for conversations
        (``open_conversation_context_menu`` / ``click_conversation_menu_item``),
        but folder menu items currently carry a testid ONLY on "Delete"
        (``FOLDER_MENU_DELETE_ITEM`` — added this implementation; Rename/Pin
        are untouched, out of this case's testid scope). Reuses the shared,
        non-unique ``CONVERSATION_MENU_BUTTON`` testid (same underlying
        DotMenu component as conversation items), scoped inside the folder's
        own row so it resolves to exactly one element.

        Hovers ``FOLDER_ICON``, NOT the outer ``FOLDER_ITEM`` row, to reveal
        the dot-menu. ``FolderAccordion.jsx`` only flips its ``#Menu``
        visibility on hover of the fixed ~49px header sub-box
        (``summaryContainer``), not the whole accordion. A bare
        ``item.hover()`` targets the row's geometric center, which is safe
        while collapsed but lands inside the (now-visible) body once the
        folder is expanded -- the dot-menu never appears and
        ``menu_button.wait_for`` times out. ``FOLDER_ICON`` lives inside
        ``summaryContainer`` itself and is rendered in both expand states,
        so hovering it reliably lands within the header regardless of
        whether the folder is collapsed or expanded.

        Args:
            folder_id: Numeric folder id.
            timeout: Maximum wait time in milliseconds.
        """
        logger.info("Deleting folder %s via 3-dot menu", folder_id)
        item = self.get_folder_item(folder_id)
        item.locator(self.FOLDER_ICON).hover()
        menu_button = item.locator(self.CONVERSATION_MENU_BUTTON)
        menu_button.wait_for(state="visible", timeout=timeout)
        menu_button.click(force=True)

        delete_item = self.page.locator(self.FOLDER_MENU_DELETE_ITEM)
        delete_item.wait_for(state="visible", timeout=timeout)
        delete_item.click()

        self.delete_confirm_dialog.wait_for(state="visible", timeout=timeout)
        self.delete_confirm_button.click()
        self.wait_for_network(timeout=timeout)
        logger.info("Folder %s deleted via menu", folder_id)
