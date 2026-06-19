# Chat & Conversations - UI Test Cases

This folder contains comprehensive UI test specifications for Elitea's Chat & Conversations feature.

## Test Files

### 📝 test_chat_interface.md (24 test cases)
Core chat functionality - sending messages, UI elements, participants, model selection.

**Coverage:**
- Page load & rendering (TC-CHAT-001 to 003)
- Sending messages (TC-CHAT-004 to 007)
- Message actions (TC-CHAT-008 to 009)
- Conversation UI elements (TC-CHAT-010 to 013)
- Participants panel (TC-CHAT-014 to 016)
- # Search (TC-CHAT-017 to 018)
- Context & settings (TC-CHAT-019 to 020)
- Sidebar navigation (TC-CHAT-021 to 022)
- Search conversations (TC-CHAT-023)
- Error handling (TC-CHAT-024)

### 📝 test_conversation_management.md (19 test cases)
Creating, organizing, and managing conversations.

**Coverage:**
- Create new conversation (TC-CONV-001 to 002)
- Conversation list & navigation (TC-CONV-003 to 005)
- Conversation actions (TC-CONV-006 to 008)
- Folders & organization (TC-CONV-009 to 011)
- Visibility & sharing (TC-CONV-012 to 015)
- Conversation starters (TC-CONV-016 to 017)
- History & timestamps (TC-CONV-018 to 019)

### 📝 test_canvas_feature.md (17 test cases)
Canvas in-place editor for code, tables, and Mermaid diagrams.

**Coverage:**
- Canvas activation (TC-CANVAS-001 to 003)
- Code editor (TC-CANVAS-004 to 007)
- Table editor (TC-CANVAS-008 to 010)
- Mermaid editor (TC-CANVAS-011 to 012)
- Canvas UI controls (TC-CANVAS-013 to 015)
- Canvas integration (TC-CANVAS-016 to 017)

## Total Test Cases

**60 test cases** covering Chat & Conversations EPIC

### By Priority:
- **P0 (Critical)**: 8 test cases
- **P1 (High)**: 39 test cases
- **P2 (Medium)**: 12 test cases
- **P3 (Low)**: 1 test case

## Test Environment

- **Base URL**: https://stage.elitea.ai
- **Chat URL**: https://stage.elitea.ai/app/chat/{id}
- **Auth**: Keycloak (<your-test-user-email>)
- **Framework**: Playwright (TypeScript/Python)

## Running Tests

```bash
# Run all chat tests
pytest ui-tests/chat-conversations/ -v

# Run specific file
pytest ui-tests/chat-conversations/test_chat_interface.md -v

# Run by priority
pytest -m "priority_p0" ui-tests/chat-conversations/
```

## Implementation Notes

### Actual UI Findings (from exploration):
- **Sidebar toggle**: "open drawer" button
- **Message input**: Textarea with placeholder "Type your message. Use # to search..."
- **Model selector**: Shows current model (e.g., "GPT-5 mini")
- **Participants sections**: Users, agents, pipelines, toolkits, MCPs
- **Action buttons**: attach files, enable internal tools, send, Clear chat history, Edit context settings

### Selectors to verify:
Many test cases use placeholder selectors that need to be verified against actual implementation:
- Canvas activation buttons
- Folder UI elements
- Visibility/sharing settings
- Conversation list structure

### Data-testid attributes recommended:
- `[data-testid="message-input"]`
- `[data-testid="send-button"]`
- `[data-testid="canvas-button"]`
- `[data-testid="add-agent-button"]`
- `[data-testid="conversation-item"]`

## Test Data Requirements

- At least 2 test user accounts for collaboration tests
- Sample conversations with messages
- Sample agents, pipelines, toolkits for participant tests
- Test folders for organization tests

## Future Enhancements

- [ ] Add visual regression tests for Canvas rendering
- [ ] Add performance tests for large conversations
- [ ] Add accessibility (a11y) tests
- [ ] Add mobile responsive tests
- [ ] Add real-time collaboration tests
- [ ] Add network failure simulation tests

## Related Documentation

- [UI Test EPICs](../../docs/UI_TEST_EPICS.md) - Full EPIC breakdown
- [Elitea Docs - Chat](https://elitea.ai/docs/menus/chat/) - Feature documentation
- [Elitea Docs - Canvas](https://elitea.ai/docs/how-tos/chat-conversations/how-to-canvas/) - Canvas feature guide

