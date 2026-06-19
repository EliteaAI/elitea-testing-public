# Chat Interface - UI Tests

Playwright tests for the Elitea Chat interface and messaging functionality.

## Test Environment

- **URL**: `https://stage.elitea.ai/app/chat/{conversation_id}`
- **Base URL**: `https://stage.elitea.ai`
- **Auth**: Keycloak authentication required
- **Test User**: <your-test-user-email>

---

## 1. Page Load & Rendering

### TC-CHAT-001: Chat page loads successfully
**Priority**: P0  
**Steps**:
1. Login to Elitea
2. Navigate to `/app/chat` or `/app/chat/{id}`
3. Wait for page to load
**Expected**:
- Page title shows "Chat: {conversation_name}"
- Message input area is visible
- Sidebar navigation is accessible
- No console errors

**Playwright Code**:
```typescript
test('chat page loads successfully', async ({ page }) => {
  await page.goto('/app/chat');
  await expect(page).toHaveTitle(/Chat:/);
  await expect(page.getByPlaceholder(/Type your message/)).toBeVisible();
  await expect(page.getByRole('button', { name: /open drawer/ })).toBeVisible();
});
```

### TC-CHAT-002: Message input field is functional
**Priority**: P0  
**Steps**:
1. Navigate to chat page
2. Locate message input textarea
**Expected**:
- Textarea has placeholder: "Type your message. Use # to search and add AI assistants to conversation."
- Textarea is editable
- Send button is visible
- Attach files button is visible

**Playwright Code**:
```typescript
test('message input is functional', async ({ page }) => {
  await page.goto('/app/chat');
  
  const messageInput = page.getByPlaceholder(/Type your message/);
  await expect(messageInput).toBeVisible();
  await expect(messageInput).toBeEditable();
  
  const sendButton = page.getByRole('button', { name: /send your question/ });
  await expect(sendButton).toBeVisible();
  
  const attachButton = page.getByRole('button', { name: /attach files/ });
  await expect(attachButton).toBeVisible();
});
```

### TC-CHAT-003: Chat message history displays
**Priority**: P0  
**Steps**:
1. Navigate to an existing conversation
2. Observe message history area
**Expected**:
- Previous messages are displayed
- Messages show timestamp
- User messages are distinguishable from AI responses
- Messages are scrollable

**Playwright Code**:
```typescript
test('message history displays correctly', async ({ page }) => {
  await page.goto('/app/chat/121'); // existing conversation
  
  // Wait for messages to load
  await page.waitForSelector('[class*="message"], [role="log"]', { timeout: 5000 });
  
  // Check if messages exist
  const messages = page.locator('[class*="message"]');
  const count = await messages.count();
  expect(count).toBeGreaterThan(0);
});
```

---

## 2. Sending Messages

### TC-CHAT-004: Send a text message
**Priority**: P0  
**Steps**:
1. Navigate to chat page
2. Type "Hello, this is a test message" in message input
3. Click send button or press Enter
**Expected**:
- Message is sent
- Message appears in chat history
- Input field is cleared
- AI response starts generating

**Playwright Code**:
```typescript
test('send a text message', async ({ page }) => {
  await page.goto('/app/chat');
  
  const messageInput = page.getByPlaceholder(/Type your message/);
  const sendButton = page.getByRole('button', { name: /send/ });
  
  await messageInput.fill('Hello, this is a test message');
  await sendButton.click();
  
  // Verify message appears in history
  await expect(page.getByText('Hello, this is a test message')).toBeVisible();
  
  // Verify input is cleared
  await expect(messageInput).toHaveValue('');
});
```

### TC-CHAT-005: Send message with Enter key
**Priority**: P1  
**Steps**:
1. Navigate to chat page
2. Type message in input field
3. Press Enter
**Expected**:
- Message is sent
- Same behavior as clicking send button

**Playwright Code**:
```typescript
test('send message with Enter key', async ({ page }) => {
  await page.goto('/app/chat');
  
  const messageInput = page.getByPlaceholder(/Type your message/);
  await messageInput.fill('Testing Enter key');
  await messageInput.press('Enter');
  
  await expect(page.getByText('Testing Enter key')).toBeVisible();
});
```

### TC-CHAT-006: Send message with Shift+Enter adds new line
**Priority**: P2  
**Steps**:
1. Navigate to chat page
2. Type "Line 1" in message input
3. Press Shift+Enter
4. Type "Line 2"
**Expected**:
- Message is NOT sent
- New line is added in textarea
- Both lines are visible in input

**Playwright Code**:
```typescript
test('Shift+Enter creates new line', async ({ page }) => {
  await page.goto('/app/chat');
  
  const messageInput = page.getByPlaceholder(/Type your message/);
  await messageInput.fill('Line 1');
  await messageInput.press('Shift+Enter');
  await messageInput.type('Line 2');
  
  const value = await messageInput.inputValue();
  expect(value).toContain('Line 1');
  expect(value).toContain('Line 2');
});
```

### TC-CHAT-007: Cannot send empty message
**Priority**: P1  
**Steps**:
1. Navigate to chat page
2. Click send button without typing anything
**Expected**:
- Message is not sent
- Input remains focused
- No error message (button simply does nothing or is disabled)

**Playwright Code**:
```typescript
test('cannot send empty message', async ({ page }) => {
  await page.goto('/app/chat');
  
  const sendButton = page.getByRole('button', { name: /send/ });
  const initialMessageCount = await page.locator('[class*="message"]').count();
  
  await sendButton.click();
  
  // Verify no new message was added
  const newMessageCount = await page.locator('[class*="message"]').count();
  expect(newMessageCount).toBe(initialMessageCount);
});
```

---

## 3. Message Actions

### TC-CHAT-008: Copy message to clipboard
**Priority**: P1  
**Steps**:
1. Navigate to conversation with messages
2. Locate "Copy to clipboard" button on a message
3. Click copy button
**Expected**:
- Message text is copied to clipboard
- Confirmation feedback (toast/icon change)

**Playwright Code**:
```typescript
test('copy message to clipboard', async ({ page }) => {
  await page.goto('/app/chat/121');
  
  // Find copy button in message
  const copyButton = page.getByRole('button', { name: /Copy to clipboard/ }).first();
  await copyButton.click();
  
  // Verify clipboard (if accessible)
  // Note: clipboard access may require permissions in test
});
```

### TC-CHAT-009: Delete message
**Priority**: P1  
**Steps**:
1. Navigate to conversation
2. Locate "Delete" button on a message
3. Click delete
4. Confirm deletion if prompted
**Expected**:
- Message is removed from chat
- Confirmation dialog may appear
- Chat history updates

**Playwright Code**:
```typescript
test('delete message', async ({ page }) => {
  await page.goto('/app/chat');
  
  // Send a test message first
  const messageInput = page.getByPlaceholder(/Type your message/);
  await messageInput.fill('Message to delete');
  await page.getByRole('button', { name: /send/ }).click();
  
  // Wait for message to appear
  await expect(page.getByText('Message to delete')).toBeVisible();
  
  // Click delete button
  const deleteButton = page.getByRole('button', { name: /Delete/ }).first();
  await deleteButton.click();
  
  // Confirm deletion if dialog appears
  const confirmButton = page.getByRole('button', { name: /confirm|yes|delete/i });
  if (await confirmButton.isVisible()) {
    await confirmButton.click();
  }
  
  // Verify message is gone
  await expect(page.getByText('Message to delete')).not.toBeVisible();
});
```

---

## 4. Conversation UI Elements

### TC-CHAT-010: Model selector is functional
**Priority**: P1  
**Steps**:
1. Navigate to chat page
2. Locate model selector button (shows current model like "GPT-5 mini")
3. Click model selector
**Expected**:
- Dropdown/menu opens showing available models
- Can select different model
- Selection persists for conversation

**Playwright Code**:
```typescript
test('model selector works', async ({ page }) => {
  await page.goto('/app/chat');
  
  const modelButton = page.getByRole('button', { name: /GPT-5 mini|Select LLM Model/ });
  await expect(modelButton).toBeVisible();
  await modelButton.click();
  
  // Check if dropdown appeared
  await page.waitForSelector('[role="menu"], [role="listbox"]', { timeout: 3000 });
});
```

### TC-CHAT-011: Attach files button opens file picker
**Priority**: P1  
**Steps**:
1. Navigate to chat page
2. Click "attach files" button
**Expected**:
- File picker dialog opens
- Can select files to upload
- Files are attached to message

**Playwright Code**:
```typescript
test('attach files button works', async ({ page }) => {
  await page.goto('/app/chat');
  
  const attachButton = page.getByRole('button', { name: /attach files/ });
  await expect(attachButton).toBeVisible();
  
  // Setup file chooser listener
  const [fileChooser] = await Promise.all([
    page.waitForEvent('filechooser'),
    attachButton.click()
  ]);
  
  expect(fileChooser).toBeDefined();
});
```

### TC-CHAT-012: Internal tools toggle
**Priority**: P2  
**Steps**:
1. Navigate to chat page
2. Click "enable internal tools" button
**Expected**:
- Button toggles on/off
- Visual indication of state change
- Internal tools become available

**Playwright Code**:
```typescript
test('internal tools toggle works', async ({ page }) => {
  await page.goto('/app/chat');
  
  const toolsButton = page.getByRole('button', { name: /enable internal tools/ });
  await expect(toolsButton).toBeVisible();
  
  // Click to toggle
  await toolsButton.click();
  
  // Wait for state change (button text or attribute change)
  await page.waitForTimeout(500);
});
```

### TC-CHAT-013: Clear chat history
**Priority**: P1  
**Steps**:
1. Navigate to conversation with messages
2. Click "Clear chat history" button
3. Confirm action if prompted
**Expected**:
- Confirmation dialog appears
- After confirmation, all messages are cleared
- Empty conversation state displayed

**Playwright Code**:
```typescript
test('clear chat history', async ({ page }) => {
  await page.goto('/app/chat/121');
  
  const clearButton = page.getByRole('button', { name: /Clear chat history/ });
  await clearButton.click();
  
  // Confirm if dialog appears
  const confirmButton = page.getByRole('button', { name: /confirm|yes|clear/i });
  if (await confirmButton.isVisible()) {
    await confirmButton.click();
  }
  
  // Verify messages are cleared
  await page.waitForTimeout(1000);
  const messageCount = await page.locator('[class*="message"]').count();
  expect(messageCount).toBe(0);
});
```

---

## 5. Participants Panel

### TC-CHAT-014: Participants panel displays correctly
**Priority**: P1  
**Steps**:
1. Navigate to chat page
2. Observe participants panel (usually on right side)
**Expected**:
- Panel shows sections: Users, agents, pipelines, toolkits, MCPs
- Each section has "Add" button
- Current participants are listed

**Playwright Code**:
```typescript
test('participants panel displays', async ({ page }) => {
  await page.goto('/app/chat');
  
  // Check for participant sections
  await expect(page.getByText('Users')).toBeVisible();
  await expect(page.getByText('agents')).toBeVisible();
  await expect(page.getByText('pipelines')).toBeVisible();
  await expect(page.getByText('toolkits')).toBeVisible();
  await expect(page.getByText('MCPs')).toBeVisible();
  
  // Check for Add buttons
  await expect(page.getByRole('button', { name: /Add agent/ })).toBeVisible();
});
```

### TC-CHAT-015: Add agent to conversation
**Priority**: P1  
**Steps**:
1. Navigate to chat page
2. Click "Add agent" button in participants panel
3. Select an agent from list
**Expected**:
- Agent selection dialog/menu opens
- Can search and select agent
- Selected agent appears in participants list
- Agent is now active in conversation

**Playwright Code**:
```typescript
test('add agent to conversation', async ({ page }) => {
  await page.goto('/app/chat');
  
  const addAgentButton = page.getByRole('button', { name: /Add agent/ });
  await addAgentButton.click();
  
  // Wait for agent selector to appear
  await page.waitForSelector('[role="dialog"], [role="menu"]', { timeout: 3000 });
  
  // Select first available agent (implementation depends on UI)
  // await page.getByRole('option').first().click();
});
```

### TC-CHAT-016: Refresh agents list
**Priority**: P2  
**Steps**:
1. Navigate to chat page
2. Click "Refresh the agents" button
**Expected**:
- Agents list refreshes
- Loading indicator may appear briefly
- Updated list is displayed

**Playwright Code**:
```typescript
test('refresh agents list', async ({ page }) => {
  await page.goto('/app/chat');
  
  const refreshButton = page.getByRole('button', { name: /Refresh the agents/ });
  await refreshButton.click();
  
  // Wait for refresh to complete
  await page.waitForTimeout(1000);
});
```

---

## 6. # Search (Participant Search)

### TC-CHAT-017: Use # to search participants
**Priority**: P1  
**Steps**:
1. Navigate to chat page
2. Type "#" in message input
**Expected**:
- Dropdown/autocomplete menu appears
- Shows agents, pipelines, toolkits available to add
- Can search by typing name after #

**Playwright Code**:
```typescript
test('# triggers participant search', async ({ page }) => {
  await page.goto('/app/chat');
  
  const messageInput = page.getByPlaceholder(/Type your message/);
  await messageInput.fill('#');
  
  // Wait for autocomplete dropdown
  await page.waitForSelector('[role="listbox"], [role="menu"]', { timeout: 3000 });
});
```

### TC-CHAT-018: Add participant via # search
**Priority**: P1  
**Steps**:
1. Navigate to chat page
2. Type "#" in message input
3. Type partial agent/pipeline name
4. Select from dropdown
**Expected**:
- Search results filter as you type
- Clicking result adds participant to conversation
- Message input updates or participant appears in panel

**Playwright Code**:
```typescript
test('add participant via # search', async ({ page }) => {
  await page.goto('/app/chat');
  
  const messageInput = page.getByPlaceholder(/Type your message/);
  await messageInput.fill('#test');
  
  // Wait for results
  await page.waitForSelector('[role="option"]', { timeout: 3000 });
  
  // Select first option
  await page.getByRole('option').first().click();
  
  // Verify participant was added (check participants panel or message)
});
```

---

## 7. Context & Settings

### TC-CHAT-019: Edit context settings
**Priority**: P2  
**Steps**:
1. Navigate to chat page
2. Click "Edit context settings" button
**Expected**:
- Settings dialog/panel opens
- Can configure context window, budget, etc.
- Settings save successfully

**Playwright Code**:
```typescript
test('edit context settings', async ({ page }) => {
  await page.goto('/app/chat');
  
  const settingsButton = page.getByRole('button', { name: /Edit context settings/ });
  await settingsButton.click();
  
  // Wait for settings dialog
  await page.waitForSelector('[role="dialog"]', { timeout: 3000 });
});
```

### TC-CHAT-020: Model settings menu
**Priority**: P2  
**Steps**:
1. Navigate to chat page
2. Click "model settings menu" button
**Expected**:
- Settings menu/dialog opens
- Can adjust temperature, max tokens, etc.
- Settings apply to conversation

**Playwright Code**:
```typescript
test('model settings menu opens', async ({ page }) => {
  await page.goto('/app/chat');
  
  const settingsButton = page.getByRole('button', { name: /model settings menu/ });
  await settingsButton.click();
  
  await page.waitForSelector('[role="dialog"], [role="menu"]', { timeout: 3000 });
});
```

---

## 8. Sidebar Navigation

### TC-CHAT-021: Open/close sidebar drawer
**Priority**: P1  
**Steps**:
1. Navigate to chat page
2. Click "open drawer" button
**Expected**:
- Sidebar slides open
- Shows navigation menu (Chat, Agents, Pipelines, etc.)
- Click again to close

**Playwright Code**:
```typescript
test('toggle sidebar drawer', async ({ page }) => {
  await page.goto('/app/chat');
  
  const drawerButton = page.getByRole('button', { name: /open drawer/ });
  await drawerButton.click();
  
  // Verify sidebar is visible
  await expect(page.getByText('Chat')).toBeVisible();
  await expect(page.getByText('Agents')).toBeVisible();
  await expect(page.getByText('Pipelines')).toBeVisible();
  
  // Close drawer
  await drawerButton.click();
});
```

### TC-CHAT-022: Navigate to Agents from sidebar
**Priority**: P1  
**Steps**:
1. Open sidebar
2. Click "Agents" menu item
**Expected**:
- Navigates to /app/agents page
- Agents dashboard loads

**Playwright Code**:
```typescript
test('navigate to Agents page', async ({ page }) => {
  await page.goto('/app/chat');
  
  // Open drawer
  await page.getByRole('button', { name: /open drawer/ }).click();
  
  // Click Agents
  await page.getByText('Agents').click();
  
  await expect(page).toHaveURL(/\/app\/agents/);
});
```

---

## 9. Search Conversations

### TC-CHAT-023: Search conversations dialog
**Priority**: P1  
**Steps**:
1. Navigate to chat page
2. Click "Search conversations" button
**Expected**:
- Search dialog/dropdown opens
- Can type to search existing conversations
- Can select conversation from results

**Playwright Code**:
```typescript
test('search conversations', async ({ page }) => {
  await page.goto('/app/chat');
  
  const searchButton = page.getByRole('button', { name: /Search conversations/ });
  await searchButton.click();
  
  // Wait for search dialog
  await page.waitForSelector('[role="dialog"], input[type="search"]', { timeout: 3000 });
});
```

---

## 10. Error Handling

### TC-CHAT-024: Handle message send failure gracefully
**Priority**: P1  
**Steps**:
1. Navigate to chat page
2. Simulate network failure or disconnect
3. Try to send message
**Expected**:
- Error message is displayed
- Message is not lost
- Option to retry

**Playwright Code**:
```typescript
test('handle message send failure', async ({ page, context }) => {
  await page.goto('/app/chat');
  
  // Simulate offline
  await context.setOffline(true);
  
  const messageInput = page.getByPlaceholder(/Type your message/);
  await messageInput.fill('Test message during offline');
  await page.getByRole('button', { name: /send/ }).click();
  
  // Check for error indication
  // await expect(page.getByText(/error|failed|retry/i)).toBeVisible();
  
  await context.setOffline(false);
});
```

---

## Notes

- Many tests depend on existing conversations and data in the stage environment
- Adjust selectors based on actual implementation (MUI classes, data-testid attributes)
- Consider adding wait strategies for AI response generation
- Test isolation: each test should ideally create its own conversation or use fixtures

