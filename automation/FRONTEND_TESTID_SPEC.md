# Frontend data-testid Specification for EliteAUI

Specification for adding `data-testid` attributes to [EliteAUI](https://github.com/EliteaAI/EliteAUI) React components to support stable Playwright test automation.

**Audience**: Frontend team (EliteAUI contributors)
**Consumer**: Test automation in [elitea-testing/automation](../automation/)

---

## Naming Convention

Pattern: `<section>-<element>-<variant>`

| Segment | Values | Examples |
|---------|--------|----------|
| section | `chat`, `agent`, `conversation`, `sidebar`, `model`, `toolkit`, `credential`, `participant`, `context` | |
| element | descriptive noun | `send`, `message`, `search`, `name`, `card` |
| variant | element type | `button`, `input`, `list`, `item`, `dialog`, `menu` |

Examples: `chat-send-button`, `agent-name-input`, `conversation-search-input`

---

## Existing data-testid Attributes (already in codebase)

| File | data-testid | Element |
|------|------------|---------|
| `src/components/Chat/ChatMessageList.jsx` | `chat-bottom-spacer` | Bottom spacer div |
| `src/pages/NewChat/ConversationItem.jsx` | `conversation-naming-spinner` | Naming-in-progress spinner |

---

## Components Needing data-testid Attributes

### 1. Chat Input & Send Button

**File**: `src/ComponentsLib/Chat/UserInput.jsx`

| Element | Current Identifier | Proposed data-testid | Test Scenario |
|---------|-------------------|---------------------|---------------|
| Chat textarea | `id="standard-multiline-static"` | `chat-message-input` | Send messages, multi-line input |
| Send button | `aria-label="send your question"` | `chat-send-button` | Click to send message |
| Stop button | Tooltip only | `chat-stop-button` | Cancel streaming response |
| Attach files button | `aria-label="attach files"` | `chat-attach-button` | File attachment tests |

**Where to add**:
```jsx
// On TextField
<TextField data-testid="chat-message-input" id="standard-multiline-static" ... />

// On send IconButton
<IconButton data-testid="chat-send-button" aria-label="send your question" ... />

// On stop IconButton
<IconButton data-testid="chat-stop-button" ... />
```

---

### 2. Chat Message List

**File**: `src/components/Chat/ChatMessageList.jsx`

| Element | Current Identifier | Proposed data-testid | Test Scenario |
|---------|-------------------|---------------------|---------------|
| Message list (`<ul>`) | `MuiList-root` (CSS class) | `chat-message-list` | Count messages, wait for responses |

**Where to add**:
```jsx
// On the MessageList (styled List) wrapper
<MessageList data-testid="chat-message-list" ... />
```

---

### 3. User Message

**File**: `src/components/Chat/UserMessage.jsx`

| Element | Current Identifier | Proposed data-testid | Test Scenario |
|---------|-------------------|---------------------|---------------|
| Message `<li>` wrapper | `MuiListItem-root` (CSS class) | `chat-message-user` | Identify user messages |
| Delete button | Tooltip "Delete" | `chat-message-delete` | Delete message tests |
| Copy button | Tooltip "Copy to clipboard" | `chat-message-copy` | Copy message tests |
| Edit button | Tooltip "Edit..." | `chat-message-edit` | Edit message tests |

**Where to add**:
```jsx
// On UserMessageContainer
<UserMessageContainer data-testid="chat-message-user" ... />

// On each IconButton inside ButtonsContainer
<IconButton data-testid="chat-message-delete" ... />  // Delete
<IconButton data-testid="chat-message-copy" ... />    // Copy
<IconButton data-testid="chat-message-edit" ... />    // Edit
```

---

### 4. AI Response (ApplicationAnswer)

**File**: `src/components/Chat/ApplicationAnswer.jsx`

| Element | Current Identifier | Proposed data-testid | Test Scenario |
|---------|-------------------|---------------------|---------------|
| Message `<li>` wrapper | `MuiListItem-root` (CSS class) | `chat-message-ai` | Identify AI messages |
| Response body | `<Answer>` styled div | `chat-message-ai-body` | Extract response text |
| Delete button | Tooltip "Delete" | `chat-message-ai-delete` | Delete AI message |
| Copy button | Tooltip "Copy to clipboard" | `chat-message-ai-copy` | Copy AI response |
| Regenerate button | Tooltip "Regenerate" | `chat-message-regenerate` | Regenerate response |
| Error info toggle | Text "Error debugging info" | `chat-message-error-toggle` | Expand error details |

**Where to add**:
```jsx
// On UserMessageContainer for AI messages
<UserMessageContainer data-testid="chat-message-ai" ... />

// On Answer div
<Answer data-testid="chat-message-ai-body" ... />

// On action buttons
<IconButton data-testid="chat-message-ai-delete" ... />
<IconButton data-testid="chat-message-ai-copy" ... />
<IconButton data-testid="chat-message-regenerate" ... />
```

---

### 5. Model Selector

**File**: `src/[fsd]/widgets/LLMModelSelector/ui/LLMModelSelector.jsx`

| Element | Current Identifier | Proposed data-testid | Test Scenario |
|---------|-------------------|---------------------|---------------|
| Selector button group | `aria-label="Model Selector Menu"` | `model-selector-button` | Click to open model menu |
| Model name display | Button text content | `model-selector-name` | Read current model |
| Settings button | `aria-label="model settings menu"` | `model-settings-button` | Open model settings |
| Dropdown menu | `<Menu>` MUI component | `model-selector-menu` | Select different model |
| Each model option | `<MenuItem>` | `model-selector-option` | Click to select model |

**Where to add**:
```jsx
// On ButtonGroup
<ButtonGroup data-testid="model-selector-button" aria-label="Model Selector Menu" ... />

// On model name Button
<Button data-testid="model-selector-name" ... >{modelName}</Button>

// On Menu
<Menu data-testid="model-selector-menu" ... />
```

---

### 6. Conversation Sidebar

**File**: `src/pages/NewChat/Conversations.jsx`

| Element | Current Identifier | Proposed data-testid | Test Scenario |
|---------|-------------------|---------------------|---------------|
| Conversations panel | None | `conversation-list` | Conversation list visibility |
| Search button | `<ConversationSearchButton>` | `conversation-search-button` | Open search |
| Search input | `placeholder="Search conversations..."` | `conversation-search-input` | Type search query |
| Create folder button | Tooltip "Create folder" | `conversation-folder-create` | Create folder tests |

**Where to add**:
```jsx
// On main container
<Box data-testid="conversation-list" ... />

// On search button component
<ConversationSearchButton data-testid="conversation-search-button" ... />

// On SimpleSearchBar input
<SimpleSearchBar data-testid="conversation-search-input" placeholder="Search conversations..." ... />
```

---

### 7. Conversation Item

**File**: `src/pages/NewChat/ConversationItem.jsx`

| Element | Current Identifier | Proposed data-testid | Test Scenario |
|---------|-------------------|---------------------|---------------|
| Conversation row | `role="button"` with `aria-roledescription="draggable"` | `conversation-item` | Click to select, drag to reorder |
| Three-dot menu | `id="conversation-menu"` | `conversation-menu-action` | Open context menu |
| Conversation name text | Typography | `conversation-item-name` | Read/verify name |

**Where to add**:
```jsx
// On the conversation row container
<Box data-testid="conversation-item" ... />

// On DotMenu
<DotMenu data-testid="conversation-menu-action" id="conversation-menu" ... />
```

---

### 8. Sidebar Navigation

**File**: `src/[fsd]/widgets/Sidebar/ui/SidebarMenuItem.jsx`

| Element | Current Identifier | Proposed data-testid | Test Scenario |
|---------|-------------------|---------------------|---------------|
| Nav container | None | `sidebar-nav` | Sidebar visibility |
| Each menu item | `<ListItemButton>` + text content | `sidebar-item-{slug}` | Navigate to section |

**Where to add** (dynamic, based on `menuTitle` prop):
```jsx
// On ListItemButton — generate slug from menuTitle
<ListItemButton data-testid={`sidebar-item-${menuTitle.toLowerCase().replace(/\s+/g, '-')}`} ... />
```

Expected values: `sidebar-item-chat`, `sidebar-item-agents`, `sidebar-item-pipelines`, `sidebar-item-credentials`, `sidebar-item-toolkits`, `sidebar-item-apps`, `sidebar-item-mcps`, `sidebar-item-artifacts`

**File**: `src/[fsd]/widgets/Sidebar/ui/SidebarBody.jsx` or `Sidebar.jsx`

| Element | Current Identifier | Proposed data-testid | Test Scenario |
|---------|-------------------|---------------------|---------------|
| Sidebar container | None | `sidebar-nav` | Toggle sidebar open/close |
| Sidebar toggle button | `aria-label="open drawer"` | `sidebar-toggle` | Open/close sidebar |

---

### 9. Chat Right Panel (Participants)

**File**: `src/pages/NewChat/Participants/ParticipantSection.jsx`

| Element | Current Identifier | Proposed data-testid | Test Scenario |
|---------|-------------------|---------------------|---------------|
| Add Agent button | Tooltip "Add Agent" | `participant-add-agent` | Add agent to chat |
| Add Toolkit button | Tooltip "Add toolkit" | `participant-add-toolkit` | Add toolkit to chat |
| Add Pipeline button | Tooltip "Add pipeline" | `participant-add-pipeline` | Add pipeline |
| Add MCP button | Tooltip "Add mcp" | `participant-add-mcp` | Add MCP |
| Refresh Agents button | Tooltip "Refresh the agents" | `participant-refresh-agents` | Refresh agent list |
| Refresh Toolkits button | Tooltip "Refresh the toolkits" | `participant-refresh-toolkits` | Refresh toolkit list |
| Agents section | None | `participant-agents-list` | Verify agents added |
| Toolkits section | None | `participant-toolkits-list` | Verify toolkits added |
| Empty state text | Text "Still no {type} added" | `participant-empty-{type}` | Verify empty state |

**Where to add** (dynamic, based on section type):
```jsx
// On Add buttons
<IconButton data-testid={`participant-add-${entityType.toLowerCase()}`} ... />

// On Refresh buttons
<IconButton data-testid={`participant-refresh-${entityType.toLowerCase()}`} ... />

// On section container
<ParticipantsAccordion data-testid={`participant-${entityType.toLowerCase()}-list`} ... />
```

---

### 10. Agent Dashboard

**File**: `src/pages/Applications/Applications.jsx`

| Element | Current Identifier | Proposed data-testid | Test Scenario |
|---------|-------------------|---------------------|---------------|
| Search input | `placeholder="Let's find something amazing!"` | `agent-search-input` | Search agents |
| Create Agent button | `aria-label="Create Agent"` area | `agent-create-button` | Create new agent |
| Agent card | Card component | `agent-card` | Click to open agent |
| Table view toggle | `name="Table view"` | `agent-table-view-button` | Switch to table view |
| Card view toggle | `name="Card list view"` | `agent-card-view-button` | Switch to card view |

---

### 11. Agent Form (Create/Edit)

**Files**: `src/pages/Applications/CreateApplication.jsx`, `src/pages/Applications/EditApplication.jsx`

| Element | Current Identifier | Proposed data-testid | Test Scenario |
|---------|-------------------|---------------------|---------------|
| Name field | `input#name` or `placeholder="Name"` | `agent-name-input` | Fill agent name |
| Description field | `placeholder="Description"` | `agent-description-input` | Fill description |
| Instructions field | `placeholder="Guidelines for the AI agent"` | `agent-instructions-input` | Fill instructions |
| Welcome message field | `placeholder="Input your welcome message"` | `agent-welcome-message-input` | Fill welcome msg |
| Save button | `name="Save"` | `agent-save-button` | Save agent |
| Discard button | `name="Discard"` | `agent-discard-button` | Discard changes |
| Actions menu (3-dot) | `aria-haspopup="true"` (last) | `agent-actions-menu` | Open actions |
| Configuration tab | `name="Configuration"` | `agent-tab-configuration` | Switch tab |
| History tab | `name="History"` | `agent-tab-history` | Switch tab |

---

### 12. Agent Toolkit Card

**File**: `src/pages/Applications/Components/Tools/ToolCard.jsx`

| Element | Current Identifier | Proposed data-testid | Test Scenario |
|---------|-------------------|---------------------|---------------|
| Card container | `<Box>` with styles | `agent-toolkit-card` | Identify toolkit card |
| Toolkit name | `<Typography variant="bodyMedium">` | `agent-toolkit-name` | Read toolkit name |
| Delete button | `id="DeleteButton"`, `aria-label="delete tool"` | `agent-toolkit-delete-button` | Remove toolkit |
| Open in new tab | `id="OpenInNewTabButton"`, `aria-label="open in new tab"` | `agent-toolkit-open-button` | Open toolkit page |
| Show tools link | Text "Show tools" | `agent-toolkit-show-tools` | Expand tool list |

**Where to add**:
```jsx
// On card container Box
<Box data-testid="agent-toolkit-card" sx={styles.cardContainer} ... />

// On toolkit name Typography
<TypographyWithConditionalTooltip data-testid="agent-toolkit-name" ... />

// On delete button (keep existing id/aria-label)
<IconButton data-testid="agent-toolkit-delete-button" id="DeleteButton" aria-label="delete tool" ... />
```

---

### 13. Agent Toolkit Add (Popper)

**File**: `src/pages/Applications/Components/Tools/` (toolkit add button area)

| Element | Current Identifier | Proposed data-testid | Test Scenario |
|---------|-------------------|---------------------|---------------|
| Add Toolkit button | `name="Toolkit"` (exact) | `agent-toolkit-add-button` | Open toolkit search |
| Search input | `placeholder="Search toolkits..."` | `agent-toolkit-search-input` | Filter toolkits |
| Each toolkit option | `role="menuitem"` | `agent-toolkit-option` | Select a toolkit |

---

### 14. Chat Action Buttons (Header Bar)

**File**: `src/pages/NewChat/NewChatInput.jsx` and `ChatBox.jsx`

| Element | Current Identifier | Proposed data-testid | Test Scenario |
|---------|-------------------|---------------------|---------------|
| Clear history button | `aria-label="Clear the chat history"` | `chat-clear-history` | Clear all messages |
| Context settings button | `aria-label="Edit context settings"` | `context-settings-button` | Open context dialog |
| Internal tools toggle | `aria-label="enable internal tools"` | `chat-internal-tools-toggle` | Toggle tools |

---

### 15. Context Settings Dialog

**File**: `src/pages/NewChat/` (context management dialog)

| Element | Current Identifier | Proposed data-testid | Test Scenario |
|---------|-------------------|---------------------|---------------|
| Dialog container | `role="dialog"` | `context-settings-dialog` | Dialog visibility |
| Strategy dropdown | Form field | `context-strategy-select` | Change strategy |
| Summarization toggle | Form field | `context-summarization-toggle` | Toggle summarization |
| User instructions | Textarea | `context-instructions-input` | Set instructions |

---

### 16. Toolkit Dashboard

**File**: `src/pages/Toolkits/Toolkits.jsx`

| Element | Current Identifier | Proposed data-testid | Test Scenario |
|---------|-------------------|---------------------|---------------|
| Search input | `placeholder="Let's find something amazing!"` | `toolkit-search-input` | Search toolkits |
| Toolkit card | Card component | `toolkit-card` | Click to open |
| Create button | Create area | `toolkit-create-button` | Create new toolkit |

---

### 17. Toolkit Test Settings Panel

**File**: `src/pages/Toolkits/TestSettings.jsx`

| Element | Current Identifier | Proposed data-testid | Test Scenario |
|---------|-------------------|---------------------|---------------|
| Test Settings header | Text "Test Settings" | `toolkit-test-settings` | Panel visibility |
| Tool selector dropdown | `<SingleSelectWithSearch label="Tool">` | `toolkit-tool-selector` | Select tool to test |
| Parameter fields container | `.index-config-field` | `toolkit-param-field` | Fill parameters |
| Run Tool button | Text "RUN TOOL" | `toolkit-run-tool-button` | Execute tool |
| Result container | Result area | `toolkit-tool-result` | Check execution result |

**Where to add**:
```jsx
// On RUN TOOL button
<Button data-testid="toolkit-run-tool-button" variant="special">RUN TOOL</Button>

// On result container
<Box data-testid="toolkit-tool-result" ... />
```

---

### 18. Embedded Chat (Agent Detail Page)

**File**: `src/pages/Applications/` (embedded chat components — reuses Chat components)

| Element | Current Identifier | Proposed data-testid | Test Scenario |
|---------|-------------------|---------------------|---------------|
| Chat input | `name="Type your message."` | `embedded-chat-input` | Send message in agent chat |
| Send button | `aria-label="send your question"` | `embedded-chat-send-button` | Click to send |
| Message list | `ul.MuiList-root` | `embedded-chat-message-list` | Count messages |

**Note**: The embedded chat reuses `UserInput.jsx`, so the `data-testid` from component #1 may apply. If the same `UserInput` is used in both contexts, consider making the testid dynamic via a prop (e.g., `testIdPrefix="embedded-chat"`).

---

### 19. Loading Spinner

**File**: Various (common component)

| Element | Current Identifier | Proposed data-testid | Test Scenario |
|---------|-------------------|---------------------|---------------|
| CircularProgress | `class*="CircularProgress"`, `role="progressbar"` | `loading-spinner` | Wait for page load |

---

### 20. Banner Overlay

**File**: Various (notification/banner component)

| Element | Current Identifier | Proposed data-testid | Test Scenario |
|---------|-------------------|---------------------|---------------|
| Banner container | z-index > 1000 overlay | `banner-overlay` | Dismiss before interaction |
| Close button | `aria-label="close"` | `banner-close-button` | Close banner |

---

## Implementation Priority

### P0 — Critical (blocks most tests if fragile)

1. `chat-message-input` — every chat test
2. `chat-send-button` — every chat test
3. `chat-message-list` — message counting, response detection
4. `chat-message-user` / `chat-message-ai` — message identification
5. `model-selector-button` — model selection tests
6. `agent-name-input` — every agent test
7. `agent-save-button` — every agent create/edit test

### P1 — High (commonly used in tests)

8. `conversation-item` — conversation management tests
9. `conversation-menu-action` — rename/delete conversation tests
10. `conversation-search-button` — search tests
11. `agent-toolkit-card` — toolkit attachment tests
12. `agent-toolkit-delete-button` — toolkit removal tests
13. `agent-toolkit-add-button` — toolkit addition tests
14. `sidebar-item-*` — navigation tests
15. `chat-message-delete` / `chat-message-copy` — message action tests

### P2 — Medium (nice to have)

16. `participant-add-agent` / `participant-add-toolkit` — participant tests
17. `toolkit-run-tool-button` — toolkit test settings
18. `toolkit-tool-result` — toolkit execution verification
19. `context-settings-button` — context management tests
20. `chat-clear-history` — clear history tests
21. `agent-search-input` — agent search tests

### P3 — Low (rarely tested)

22. `embedded-chat-*` — agent embedded chat (reuses main chat components)
23. `loading-spinner` — page load detection
24. `banner-overlay` — banner dismissal
25. `credential-*` — credential management

---

## Implementation Notes

### Adding data-testid to Styled Components

MUI styled components pass through `data-testid`:

```jsx
// Works — styled components forward unknown props to the DOM
const MessageList = styled(List)({ ... });
<MessageList data-testid="chat-message-list" />
// Renders: <ul class="MuiList-root" data-testid="chat-message-list" />
```

### Dynamic data-testid Values

For repeating elements (message items, conversation items), append an index or ID:

```jsx
// Option A: Index-based
<UserMessageContainer data-testid={`chat-message-user-${index}`} />

// Option B: Just the type (tests use nth() for indexing)
<UserMessageContainer data-testid="chat-message-user" />
```

**Recommendation**: Use the type-only variant (`chat-message-user`) since Playwright's `nth()` handles indexing well, and index-based testids add noise.

### Preserving Existing Identifiers

`data-testid` should be **added alongside**, never replacing, existing `aria-label`, `id`, or `role` attributes. These serve accessibility and may be used by other code:

```jsx
// Correct: add data-testid, keep aria-label
<IconButton
  data-testid="chat-send-button"
  aria-label="send your question"  // keep for accessibility
  ...
/>
```

### Multiple Instances of Same Component

When `UserInput.jsx` is used in both the main chat and embedded agent chat, distinguish with a `testIdPrefix` prop:

```jsx
// In UserInput.jsx
<TextField data-testid={`${testIdPrefix || 'chat'}-message-input`} ... />
<IconButton data-testid={`${testIdPrefix || 'chat'}-send-button`} ... />

// Usage in main chat
<UserInput testIdPrefix="chat" />

// Usage in embedded agent chat
<UserInput testIdPrefix="embedded-chat" />
```

---

## Automation-Side Reference

The test automation code maps these `data-testid` values in:
- **`components/locators.py`** — `Testid` class with all constants
- **`components/__init__.py`** — exports `by_testid()`, `Testid`
- **`pages/chat_page.py`** — TODO comments showing future `by_testid()` usage
- **`pages/agent_page.py`** — TODO comments showing future `by_testid()` usage
- **`CLAUDE.md`** — Locator Strategy section documenting the approach
