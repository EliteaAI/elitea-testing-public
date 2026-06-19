# Conversation Management - UI Tests

Playwright tests for creating, organizing, and managing conversations in Elitea.

## Test Environment

- **URL**: `https://stage.elitea.ai/app/chat`
- **Auth**: Keycloak authentication required
- **Test User**: <your-test-user-email>

---

## 1. Create New Conversation

### TC-CONV-001: Create new conversation via Create button
**Priority**: P0  
**Steps**:
1. Login to Elitea
2. Open sidebar (click "open drawer" button)
3. Click "Create" button
4. Select "Chat" or "Conversation" option from menu
**Expected**:
- Menu with creation options appears
- Selecting "Chat" creates new empty conversation
- Redirects to new conversation URL
- Message input is ready

**Playwright Code**:
```typescript
test('create new conversation', async ({ page }) => {
  await page.goto('/app/chat');
  
  // Open sidebar
  const drawerButton = page.getByRole('button', { name: /open drawer/ });
  await drawerButton.click();
  
  // Click Create button
  const createButton = page.getByRole('button', { name: /Create/ });
  await createButton.click();
  
  // Select Chat option
  const chatOption = page.getByText(/Chat|Conversation/);
  await chatOption.click();
  
  // Verify new conversation opened
  await expect(page).toHaveURL(/\/app\/chat\/\d+/);
  await expect(page.getByPlaceholder(/Type your message/)).toBeVisible();
});
```

### TC-CONV-002: New conversation has default settings
**Priority**: P1  
**Steps**:
1. Create new conversation
2. Check initial state
**Expected**:
- Empty message history
- Default LLM model is selected
- No participants added yet
- Private visibility by default

**Playwright Code**:
```typescript
test('new conversation default settings', async ({ page }) => {
  // Create new conversation (reuse TC-CONV-001 steps)
  await page.goto('/app/chat');
  // ... create conversation steps ...
  
  // Check empty state
  const messageCount = await page.locator('[class*="message"]').count();
  expect(messageCount).toBe(0);
  
  // Check default model
  await expect(page.getByText(/GPT|Claude|LLM/)).toBeVisible();
});
```

---

## 2. Conversation List & Navigation

### TC-CONV-003: View list of conversations
**Priority**: P1  
**Steps**:
1. Open sidebar
2. Click "Chat" menu item
3. Observe conversation list
**Expected**:
- List of existing conversations is displayed
- Each conversation shows title/preview
- Recent conversations appear first
- Can scroll through list

**Playwright Code**:
```typescript
test('view conversation list', async ({ page }) => {
  await page.goto('/app/chat');
  
  // Open sidebar and navigate to Chat
  await page.getByRole('button', { name: /open drawer/ }).click();
  await page.getByText('Chat').click();
  
  // Verify conversations are listed
  const conversations = page.locator('[class*="conversation"], [role="listitem"]');
  const count = await conversations.count();
  expect(count).toBeGreaterThan(0);
});
```

### TC-CONV-004: Click conversation to open it
**Priority**: P0  
**Steps**:
1. View conversation list
2. Click on a conversation item
**Expected**:
- Selected conversation opens
- Messages from that conversation load
- URL updates to conversation ID
- Conversation is highlighted in list

**Playwright Code**:
```typescript
test('open conversation from list', async ({ page }) => {
  await page.goto('/app/chat');
  
  // Navigate to conversation list
  await page.getByRole('button', { name: /open drawer/ }).click();
  
  // Click first conversation
  const firstConv = page.locator('[class*="conversation"]').first();
  await firstConv.click();
  
  // Verify conversation opened
  await expect(page).toHaveURL(/\/app\/chat\/\d+/);
});
```

### TC-CONV-005: Search conversations
**Priority**: P1  
**Steps**:
1. Click "Search conversations" button
2. Type search query
3. View filtered results
**Expected**:
- Search dialog appears
- Results filter as you type
- Can click result to open conversation
- Shows "no results" if no matches

**Playwright Code**:
```typescript
test('search conversations', async ({ page }) => {
  await page.goto('/app/chat');
  
  // Click search button
  const searchButton = page.getByRole('button', { name: /Search conversations/ });
  await searchButton.click();
  
  // Type search query
  const searchInput = page.getByRole('searchbox');
  await searchInput.fill('test');
  
  // Wait for results
  await page.waitForTimeout(500);
  
  // Verify results appear or "no results" message
  // await expect(page.locator('[role="option"]')).toBeVisible();
});
```

---

## 3. Conversation Actions

### TC-CONV-006: Rename conversation
**Priority**: P1  
**Steps**:
1. Open a conversation
2. Locate conversation title or settings menu
3. Click edit/rename option
4. Enter new name
5. Save
**Expected**:
- Rename dialog/input appears
- Can type new name
- Name updates in conversation header
- Name updates in conversation list

**Playwright Code**:
```typescript
test('rename conversation', async ({ page }) => {
  await page.goto('/app/chat/121');
  
  // Find and click rename option (implementation depends on UI)
  // This might be in a context menu, settings dropdown, etc.
  // await page.getByRole('button', { name: /edit|rename/i }).click();
  
  // Enter new name
  // const nameInput = page.getByLabel(/name|title/i);
  // await nameInput.fill('Renamed Conversation');
  
  // Save
  // await page.getByRole('button', { name: /save/i }).click();
  
  // Verify name changed
  // await expect(page.getByText('Renamed Conversation')).toBeVisible();
});
```

### TC-CONV-007: Delete conversation
**Priority**: P1  
**Steps**:
1. Open a conversation (preferably a test one)
2. Click delete button
3. Confirm deletion
**Expected**:
- Confirmation dialog appears
- After confirming, conversation is deleted
- Redirects to conversation list or new conversation
- Conversation removed from list

**Playwright Code**:
```typescript
test('delete conversation', async ({ page }) => {
  // First create a test conversation to delete
  await page.goto('/app/chat');
  // ... create new conversation ...
  
  // Click delete button
  const deleteButton = page.getByRole('button', { name: /Delete/ });
  await deleteButton.click();
  
  // Confirm deletion
  const confirmButton = page.getByRole('button', { name: /confirm|yes|delete/i });
  await confirmButton.click();
  
  // Verify redirected away from deleted conversation
  await expect(page).not.toHaveURL(/\/app\/chat\/\d+/);
});
```

### TC-CONV-008: Duplicate conversation
**Priority**: P2  
**Steps**:
1. Open a conversation
2. Click duplicate/copy option
**Expected**:
- New conversation is created
- New conversation has same settings and participants
- Messages may or may not be copied (depending on feature)
- Redirects to new conversation

**Playwright Code**:
```typescript
test('duplicate conversation', async ({ page }) => {
  await page.goto('/app/chat/121');
  
  // Find duplicate option
  // await page.getByRole('button', { name: /duplicate|copy/i }).click();
  
  // Verify new conversation created
  // await expect(page).toHaveURL(/\/app\/chat\/\d+/);
  // await expect(page).not.toHaveURL(/121/); // different ID
});
```

---

## 4. Folders & Organization

### TC-CONV-009: Create conversation folder
**Priority**: P1  
**Steps**:
1. Navigate to conversation list
2. Click "Create folder" or similar option
3. Enter folder name
4. Save
**Expected**:
- Folder is created
- Folder appears in conversation list/sidebar
- Can expand/collapse folder

**Playwright Code**:
```typescript
test('create conversation folder', async ({ page }) => {
  await page.goto('/app/chat');
  
  // Open sidebar
  await page.getByRole('button', { name: /open drawer/ }).click();
  
  // Look for create folder option
  // Implementation depends on UI - might be in Create menu
  // await page.getByRole('button', { name: /Create/ }).click();
  // await page.getByText(/Folder/).click();
  
  // Enter folder name
  // const nameInput = page.getByLabel(/name/i);
  // await nameInput.fill('Test Folder');
  // await page.getByRole('button', { name: /Create|Save/ }).click();
  
  // Verify folder created
  // await expect(page.getByText('Test Folder')).toBeVisible();
});
```

### TC-CONV-010: Move conversation to folder
**Priority**: P1  
**Steps**:
1. Open conversation or select from list
2. Click move/organize option
3. Select target folder
4. Confirm
**Expected**:
- Conversation moves to folder
- Conversation appears under folder in list
- Conversation retains all settings and messages

**Playwright Code**:
```typescript
test('move conversation to folder', async ({ page }) => {
  await page.goto('/app/chat/121');
  
  // Find move option (might be in context menu)
  // await page.getByRole('button', { name: /move|organize/i }).click();
  
  // Select folder
  // await page.getByText('Test Folder').click();
  
  // Verify conversation moved
  // await expect(page.getByText('Test Folder')).toBeVisible();
});
```

### TC-CONV-011: Expand/collapse folder
**Priority**: P2  
**Steps**:
1. Navigate to conversation list with folders
2. Click on folder name or chevron icon
**Expected**:
- Folder expands to show conversations inside
- Click again to collapse
- State persists across page reloads

**Playwright Code**:
```typescript
test('expand and collapse folder', async ({ page }) => {
  await page.goto('/app/chat');
  
  // Find folder
  const folder = page.getByText('Test Folder');
  await folder.click();
  
  // Verify contents are visible
  // await expect(page.locator('[class*="folder-content"]')).toBeVisible();
  
  // Click again to collapse
  await folder.click();
  
  // Verify contents are hidden
  // await expect(page.locator('[class*="folder-content"]')).not.toBeVisible();
});
```

---

## 5. Conversation Visibility & Sharing

### TC-CONV-012: Set conversation as private
**Priority**: P1  
**Steps**:
1. Open conversation settings
2. Set visibility to "Private"
3. Save
**Expected**:
- Conversation is marked as private
- Only creator can see conversation
- Page title or indicator shows "Private"

**Playwright Code**:
```typescript
test('set conversation as private', async ({ page }) => {
  await page.goto('/app/chat/121');
  
  // Open visibility settings
  // Implementation depends on UI
  // await page.getByRole('button', { name: /visibility|share/i }).click();
  // await page.getByLabel('Private').check();
  // await page.getByRole('button', { name: /Save/ }).click();
  
  // Verify private indicator
  await expect(page.getByText(/Private/)).toBeVisible();
});
```

### TC-CONV-013: Share conversation with team
**Priority**: P1  
**Steps**:
1. Open conversation settings
2. Set visibility to "Team" or select team members
3. Save
**Expected**:
- Conversation is visible to selected team members
- Team members can access via URL
- Indicator shows team/shared status

**Playwright Code**:
```typescript
test('share conversation with team', async ({ page }) => {
  await page.goto('/app/chat/121');
  
  // Open share settings
  // await page.getByRole('button', { name: /share/i }).click();
  
  // Select team visibility
  // await page.getByLabel('Team').check();
  // await page.getByRole('button', { name: /Save/ }).click();
  
  // Verify shared status
  // await expect(page.getByText(/Team|Shared/)).toBeVisible();
});
```

### TC-CONV-014: Make conversation public
**Priority**: P2  
**Steps**:
1. Open conversation settings
2. Set visibility to "Public"
3. Save
**Expected**:
- Conversation is publicly accessible
- URL can be shared
- Public indicator is displayed

**Playwright Code**:
```typescript
test('make conversation public', async ({ page }) => {
  await page.goto('/app/chat/121');
  
  // Open visibility settings
  // await page.getByRole('button', { name: /visibility/i }).click();
  // await page.getByLabel('Public').check();
  // await page.getByRole('button', { name: /Save/ }).click();
  
  // Verify public indicator
  // await expect(page.getByText(/Public/)).toBeVisible();
});
```

### TC-CONV-015: Add teammate to conversation
**Priority**: P1  
**Steps**:
1. Open conversation
2. Click "Add teammate" or user management button
3. Search for user
4. Select user to add
**Expected**:
- User search/selection dialog opens
- Can search by name or email
- Selected user is added to conversation
- User appears in Users section of participants panel

**Playwright Code**:
```typescript
test('add teammate to conversation', async ({ page }) => {
  await page.goto('/app/chat/121');
  
  // Look for add user option
  // May be in Users section of participants panel
  // const addUserButton = page.getByRole('button', { name: /Add user|Add teammate/ });
  // await addUserButton.click();
  
  // Search and select user
  // const searchInput = page.getByRole('searchbox');
  // await searchInput.fill('teammate@example.com');
  // await page.getByText('teammate@example.com').click();
  
  // Verify user added
  // await expect(page.getByText('teammate@example.com')).toBeVisible();
});
```

---

## 6. Conversation Starters

### TC-CONV-016: View conversation starters
**Priority**: P2  
**Steps**:
1. Open a conversation that has starter prompts configured
2. Observe chat input area
**Expected**:
- Pre-configured starter prompts are displayed
- Prompts are clickable buttons or chips
- Displayed before any messages are sent

**Playwright Code**:
```typescript
test('conversation starters are displayed', async ({ page }) => {
  await page.goto('/app/chat/121');
  
  // Look for starter prompts
  // These might be displayed as buttons near the input
  // await expect(page.locator('[class*="starter"], [class*="prompt-chip"]')).toBeVisible();
});
```

### TC-CONV-017: Use conversation starter
**Priority**: P2  
**Steps**:
1. Open conversation with starters
2. Click on a starter prompt
**Expected**:
- Prompt text is inserted into message input
- Can edit before sending or sends automatically
- Conversation begins with that prompt

**Playwright Code**:
```typescript
test('use conversation starter', async ({ page }) => {
  await page.goto('/app/chat/121');
  
  // Click first starter
  // const starter = page.locator('[class*="starter"]').first();
  // await starter.click();
  
  // Verify message sent or input filled
  // const messageInput = page.getByPlaceholder(/Type your message/);
  // await expect(messageInput).not.toBeEmpty();
});
```

---

## 7. Conversation History & Timestamps

### TC-CONV-018: Messages show timestamps
**Priority**: P2  
**Steps**:
1. Navigate to conversation with messages
2. Observe message details
**Expected**:
- Each message shows timestamp
- Timestamp format is consistent
- Recent messages may show relative time (e.g., "2 minutes ago")

**Playwright Code**:
```typescript
test('messages show timestamps', async ({ page }) => {
  await page.goto('/app/chat/121');
  
  // Look for timestamp elements
  // const timestamps = page.locator('[class*="timestamp"], time');
  // const count = await timestamps.count();
  // expect(count).toBeGreaterThan(0);
});
```

### TC-CONV-019: Scroll to load older messages
**Priority**: P2  
**Steps**:
1. Open conversation with many messages
2. Scroll to top of message history
**Expected**:
- Older messages load as you scroll up
- Loading indicator may appear
- Smooth scroll behavior

**Playwright Code**:
```typescript
test('load older messages on scroll', async ({ page }) => {
  await page.goto('/app/chat/121');
  
  const messageContainer = page.locator('[class*="messages"], [class*="chat-history"]');
  
  // Get initial message count
  const initialCount = await page.locator('[class*="message"]').count();
  
  // Scroll to top
  await messageContainer.evaluate((el) => el.scrollTo(0, 0));
  
  // Wait for potential loading
  await page.waitForTimeout(1000);
  
  // Check if more messages loaded
  // const newCount = await page.locator('[class*="message"]').count();
  // expect(newCount).toBeGreaterThanOrEqual(initialCount);
});
```

---

## Notes

- Many conversation management features depend on UI discovery
- Need to verify exact selectors and menu locations in actual implementation
- Consider using data-testid attributes for more reliable test selectors
- Test with multiple users for collaboration features
- Folder functionality may not be fully implemented yet

