"""Data-testid locator helpers for Elitea test automation.

Provides a centralized registry of ``data-testid`` selectors and helper
functions.  Once the frontend team adds ``data-testid`` attributes to
EliteAUI components, tests can use these stable locators instead of
fragile CSS/role/text-based selectors.

Usage::

    from components.locators import by_testid, Testid

    # Get a Playwright locator by test ID
    send_btn = by_testid(page, Testid.CHAT_SEND_BUTTON)
    send_btn.click()

    # Or use Playwright's built-in get_by_test_id (same effect)
    send_btn = page.get_by_test_id("chat-send-button")
"""

from playwright.sync_api import Locator, Page


class Testid:
    """Registry of ``data-testid`` values expected in EliteAUI.

    Naming convention: ``<section>-<element>-<variant>``
    Examples: ``chat-send-button``, ``agent-name-input``, ``sidebar-nav``

    These constants map 1:1 to ``data-testid`` attributes that the
    frontend team should add to EliteAUI components.  See
    ``FRONTEND_TESTID_SPEC.md`` for the full specification.
    """

    # ── Chat page ─────────────────────────────────────────────────────
    CHAT_MESSAGE_INPUT = "chat-message-input"
    CHAT_SEND_BUTTON = "chat-send-button"
    CHAT_ATTACH_BUTTON = "chat-attach-button"
    CHAT_CLEAR_HISTORY = "chat-clear-history"
    CHAT_MESSAGE_LIST = "chat-message-list"
    CHAT_MESSAGE_ITEM = "chat-message-item"           # on each <li>
    CHAT_MESSAGE_USER = "chat-message-user"            # user message body
    CHAT_MESSAGE_AI = "chat-message-ai"                # AI message body
    CHAT_MESSAGE_DELETE = "chat-message-delete"
    CHAT_MESSAGE_COPY = "chat-message-copy"
    CHAT_MESSAGE_REGENERATE = "chat-message-regenerate"
    CHAT_BOTTOM_SPACER = "chat-bottom-spacer"          # already exists!

    # ── Model selector ────────────────────────────────────────────────
    MODEL_SELECTOR_BUTTON = "model-selector-button"
    MODEL_SELECTOR_MENU = "model-selector-menu"
    MODEL_SELECTOR_OPTION = "model-selector-option"    # on each option

    # ── Context settings ──────────────────────────────────────────────
    CONTEXT_SETTINGS_BUTTON = "context-settings-button"
    CONTEXT_SETTINGS_DIALOG = "context-settings-dialog"

    # ── Conversation sidebar ──────────────────────────────────────────
    CONVERSATION_LIST = "conversation-list"
    CONVERSATION_ITEM = "conversation-item"            # on each item
    CONVERSATION_CREATE = "conversation-create-button"
    CONVERSATION_SEARCH = "conversation-search-button"
    CONVERSATION_SEARCH_INPUT = "conversation-search-input"
    CONVERSATION_MENU_ACTION = "conversation-menu-action"  # 3-dot menu
    CONVERSATION_FOLDER_CREATE = "conversation-folder-create"

    # ── Agent dashboard ───────────────────────────────────────────────
    AGENT_SEARCH_INPUT = "agent-search-input"
    AGENT_CARD = "agent-card"                          # on each card
    AGENT_CREATE_BUTTON = "agent-create-button"
    AGENT_TABLE_VIEW = "agent-table-view-button"
    AGENT_CARD_VIEW = "agent-card-view-button"

    # ── Agent form ────────────────────────────────────────────────────
    AGENT_NAME_INPUT = "agent-name-input"
    AGENT_DESCRIPTION_INPUT = "agent-description-input"
    AGENT_INSTRUCTIONS_INPUT = "agent-instructions-input"
    AGENT_WELCOME_MESSAGE_INPUT = "agent-welcome-message-input"
    AGENT_WELCOME_MESSAGE_EXPAND = "agent-welcome-message-expand"
    AGENT_WELCOME_MESSAGE_COUNTER = "agent-welcome-message-counter"
    AGENT_WELCOME_MESSAGE_DIALOG = "agent-welcome-message-dialog"
    AGENT_WELCOME_MESSAGE_DIALOG_TEXTAREA = "agent-welcome-message-dialog-textarea"
    AGENT_WELCOME_MESSAGE_DIALOG_COUNTER = "agent-welcome-message-dialog-counter"
    AGENT_WELCOME_MESSAGE_DIALOG_CLOSE = "agent-welcome-message-dialog-close"
    AGENT_SAVE_BUTTON = "agent-save-button"
    AGENT_DISCARD_BUTTON = "agent-discard-button"
    AGENT_ACTIONS_MENU = "agent-actions-menu"          # 3-dot menu

    # ── Agent conversation starters ───────────────────────────────────
    AGENT_CONVERSATION_STARTERS_SECTION = "agent-conversation-starters-section"
    AGENT_CONVERSATION_STARTER_ADD = "agent-conversation-starter-add"
    AGENT_CONVERSATION_STARTER_INPUT = "agent-conversation-starter-input"
    AGENT_CONVERSATION_STARTER_COUNTER = "agent-conversation-starter-counter"

    # ── Agent toolkits section ────────────────────────────────────────
    AGENT_TOOLKIT_ADD = "agent-toolkit-add-button"
    AGENT_TOOLKIT_CARD = "agent-toolkit-card"          # on each card
    AGENT_TOOLKIT_DELETE = "agent-toolkit-delete-button"
    AGENT_TOOLKIT_SEARCH = "agent-toolkit-search-input"

    # ── Agent embedded chat ───────────────────────────────────────────
    EMBEDDED_CHAT_INPUT = "embedded-chat-input"
    EMBEDDED_CHAT_SEND = "embedded-chat-send-button"
    EMBEDDED_CHAT_MESSAGE_LIST = "embedded-chat-message-list"

    # ── Sidebar navigation ────────────────────────────────────────────
    SIDEBAR_NAV = "sidebar-nav"
    SIDEBAR_TOGGLE = "sidebar-toggle"
    SIDEBAR_ITEM_CHAT = "sidebar-item-chat"
    SIDEBAR_ITEM_AGENTS = "sidebar-item-agents"
    SIDEBAR_ITEM_PIPELINES = "sidebar-item-pipelines"
    SIDEBAR_ITEM_CREDENTIALS = "sidebar-item-credentials"
    SIDEBAR_ITEM_TOOLKITS = "sidebar-item-toolkits"

    # ── Chat right panel (participants) ───────────────────────────────
    PARTICIPANT_ADD_AGENT = "participant-add-agent"
    PARTICIPANT_ADD_TOOLKIT = "participant-add-toolkit"
    PARTICIPANT_ADD_PIPELINE = "participant-add-pipeline"
    PARTICIPANT_ADD_MCP = "participant-add-mcp"
    PARTICIPANT_AGENTS_LIST = "participant-agents-list"
    PARTICIPANT_TOOLKITS_LIST = "participant-toolkits-list"

    # ── Toolkit pages ─────────────────────────────────────────────────
    TOOLKIT_SEARCH_INPUT = "toolkit-search-input"
    TOOLKIT_CARD = "toolkit-card"
    TOOLKIT_CREATE_BUTTON = "toolkit-create-button"
    TOOLKIT_RUN_TOOL_BUTTON = "toolkit-run-tool-button"
    TOOLKIT_TOOL_RESULT = "toolkit-tool-result"

    # ── Credential pages ──────────────────────────────────────────────
    CREDENTIAL_SEARCH_INPUT = "credential-search-input"
    CREDENTIAL_CARD = "credential-card"
    CREDENTIAL_CREATE_BUTTON = "credential-create-button"

    # ── Common / shared ───────────────────────────────────────────────
    LOADING_SPINNER = "loading-spinner"
    BANNER_OVERLAY = "banner-overlay"
    CONFIRMATION_DIALOG = "confirmation-dialog"


def by_testid(page: Page, testid: str) -> Locator:
    """Return a Playwright locator for a ``data-testid`` attribute.

    This is a thin wrapper around ``page.get_by_test_id()`` that
    reads from the ``Testid`` registry.  Prefer using the Testid
    constants for consistency::

        send = by_testid(page, Testid.CHAT_SEND_BUTTON)

    Args:
        page: Playwright Page instance.
        testid: The data-testid value to match.

    Returns:
        Playwright Locator matching ``[data-testid="<testid>"]``.
    """
    return page.get_by_test_id(testid)


def by_testid_selector(testid: str) -> str:
    """Return the raw CSS selector string for a data-testid value.

    Useful when building compound selectors or when a locator
    function isn't appropriate (e.g. in ``page.wait_for_selector``).

    Args:
        testid: The data-testid value.

    Returns:
        CSS selector string, e.g. ``[data-testid="chat-send-button"]``.
    """
    return f'[data-testid="{testid}"]'
