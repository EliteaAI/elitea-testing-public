# Canvas Feature - UI Tests

Playwright tests for the Canvas editing feature in conversations (code, tables, Mermaid diagrams).

## Test Environment

- **URL**: `https://stage.elitea.ai/app/chat/{conversation_id}`
- **Auth**: Keycloak authentication required
- **Feature**: Canvas - in-place editor for code/tables/diagrams

---

## 1. Canvas Activation

### TC-CANVAS-001: Canvas opens for code blocks
**Priority**: P1  
**Steps**:
1. Send message requesting code generation
2. Wait for AI response with code block
3. Look for Canvas activation button/icon
4. Click to open Canvas
**Expected**:
- Code response contains Canvas-compatible content
- "Open in Canvas" button or icon appears
- Clicking opens Canvas editor
- Code is editable in Canvas

**Playwright Code**:
```typescript
test('canvas opens for code blocks', async ({ page }) => {
  await page.goto('/app/chat');
  
  // Send request for code
  const messageInput = page.getByPlaceholder(/Type your message/);
  await messageInput.fill('Generate a Python function to calculate factorial');
  await page.getByRole('button', { name: /send/ }).click();
  
  // Wait for response with code
  await page.waitForSelector('pre code, [class*="code-block"]', { timeout: 15000 });
  
  // Look for Canvas open button
  const canvasButton = page.getByRole('button', { name: /canvas|edit/i });
  await expect(canvasButton).toBeVisible();
  
  await canvasButton.click();
  
  // Verify Canvas opened
  await expect(page.locator('[class*="canvas"], [role="dialog"]')).toBeVisible();
});
```

### TC-CANVAS-002: Canvas opens for tables
**Priority**: P1  
**Steps**:
1. Send message requesting table generation
2. Wait for AI response with table
3. Click Canvas activation
**Expected**:
- Table response is Canvas-compatible
- Canvas opens with table editor
- Table data is editable

**Playwright Code**:
```typescript
test('canvas opens for tables', async ({ page }) => {
  await page.goto('/app/chat');
  
  const messageInput = page.getByPlaceholder(/Type your message/);
  await messageInput.fill('Create a table comparing Python vs JavaScript features');
  await page.getByRole('button', { name: /send/ }).click();
  
  // Wait for table response
  await page.waitForSelector('table, [class*="table"]', { timeout: 15000 });
  
  // Open Canvas
  const canvasButton = page.getByRole('button', { name: /canvas/i });
  await canvasButton.click();
  
  // Verify table editor opened
  await expect(page.locator('[class*="canvas"]')).toBeVisible();
});
```

### TC-CANVAS-003: Canvas opens for Mermaid diagrams
**Priority**: P1  
**Steps**:
1. Send message requesting diagram generation
2. Wait for Mermaid diagram response
3. Click Canvas activation
**Expected**:
- Diagram renders correctly
- Canvas opens with Mermaid editor
- Diagram code is editable

**Playwright Code**:
```typescript
test('canvas opens for mermaid diagrams', async ({ page }) => {
  await page.goto('/app/chat');
  
  const messageInput = page.getByPlaceholder(/Type your message/);
  await messageInput.fill('Create a flowchart showing user login process using Mermaid');
  await page.getByRole('button', { name: /send/ }).click();
  
  // Wait for Mermaid diagram
  await page.waitForSelector('[class*="mermaid"], svg', { timeout: 15000 });
  
  // Open Canvas
  const canvasButton = page.getByRole('button', { name: /canvas/i });
  await canvasButton.click();
  
  await expect(page.locator('[class*="canvas"]')).toBeVisible();
});
```

---

## 2. Canvas Code Editor

### TC-CANVAS-004: Edit code in Canvas
**Priority**: P1  
**Steps**:
1. Open Canvas with code
2. Click in code editor area
3. Modify code
**Expected**:
- Code editor is syntax-highlighted
- Can type and edit freely
- Changes are reflected in real-time
- Syntax highlighting adapts to language

**Playwright Code**:
```typescript
test('edit code in canvas', async ({ page }) => {
  // Prerequisite: Canvas is open with code
  await page.goto('/app/chat');
  // ... open canvas with code ...
  
  // Find code editor (might be Monaco, CodeMirror, or textarea)
  const editor = page.locator('[class*="editor"], textarea, [contenteditable="true"]');
  await editor.click();
  
  // Edit code
  await editor.press('End'); // Move to end
  await editor.type('\n// Added comment');
  
  // Verify edit appears
  await expect(page.getByText('Added comment')).toBeVisible();
});
```

### TC-CANVAS-005: Copy code from Canvas
**Priority**: P1  
**Steps**:
1. Open Canvas with code
2. Click "Copy" button
**Expected**:
- Code is copied to clipboard
- Visual feedback (toast, icon change)
- Full code including edits is copied

**Playwright Code**:
```typescript
test('copy code from canvas', async ({ page }) => {
  // Canvas with code is open
  
  const copyButton = page.getByRole('button', { name: /Copy|copy to clipboard/i });
  await expect(copyButton).toBeVisible();
  await copyButton.click();
  
  // Verify feedback (might be toast or icon change)
  // await expect(page.getByText(/Copied/i)).toBeVisible({ timeout: 2000 });
});
```

### TC-CANVAS-006: Undo/Redo in Canvas
**Priority**: P2  
**Steps**:
1. Open Canvas with code
2. Make some edits
3. Click Undo button
4. Click Redo button
**Expected**:
- Undo button reverts last change
- Can undo multiple times
- Redo restores undone changes
- Keyboard shortcuts work (Ctrl+Z, Ctrl+Y)

**Playwright Code**:
```typescript
test('undo and redo in canvas', async ({ page }) => {
  // Canvas with code is open, make edit
  const editor = page.locator('[class*="editor"]');
  await editor.type('test edit');
  
  // Click Undo
  const undoButton = page.getByRole('button', { name: /Undo/i });
  await undoButton.click();
  
  // Verify edit reverted
  await expect(page.getByText('test edit')).not.toBeVisible();
  
  // Click Redo
  const redoButton = page.getByRole('button', { name: /Redo/i });
  await redoButton.click();
  
  // Verify edit restored
  await expect(page.getByText('test edit')).toBeVisible();
});
```

### TC-CANVAS-007: Save changes in Canvas
**Priority**: P1  
**Steps**:
1. Open Canvas
2. Make edits
3. Click "Save" button
**Expected**:
- Changes are saved
- Edited content appears in conversation
- Canvas can be closed
- Reopening shows saved changes

**Playwright Code**:
```typescript
test('save changes in canvas', async ({ page }) => {
  // Make edit in canvas
  const editor = page.locator('[class*="editor"]');
  await editor.type('// Saved edit');
  
  // Click Save
  const saveButton = page.getByRole('button', { name: /Save/i });
  await saveButton.click();
  
  // Wait for save confirmation
  await page.waitForTimeout(1000);
  
  // Verify saved (might show in message or update canvas state)
  // await expect(page.getByText('Saved')).toBeVisible();
});
```

---

## 3. Canvas Table Editor

### TC-CANVAS-008: Edit table cells in Canvas
**Priority**: P1  
**Steps**:
1. Open Canvas with table
2. Click on a table cell
3. Edit cell content
**Expected**:
- Cell becomes editable
- Can type new content
- Changes are reflected in table view
- Can navigate cells with Tab/Arrow keys

**Playwright Code**:
```typescript
test('edit table cells in canvas', async ({ page }) => {
  // Canvas with table is open
  
  // Click first cell
  const firstCell = page.locator('table td, [role="gridcell"]').first();
  await firstCell.click();
  
  // Edit content
  await firstCell.fill('Updated cell');
  
  // Verify update
  await expect(firstCell).toHaveText('Updated cell');
});
```

### TC-CANVAS-009: Add/remove table rows
**Priority**: P2  
**Steps**:
1. Open Canvas with table
2. Right-click on row or use add row button
3. Select "Add row" or "Delete row"
**Expected**:
- New row is inserted
- Can add rows above/below
- Delete removes row
- Table structure updates correctly

**Playwright Code**:
```typescript
test('add row to table in canvas', async ({ page }) => {
  // Canvas with table is open
  
  const initialRows = await page.locator('table tr').count();
  
  // Look for add row button or context menu
  // Implementation depends on table editor UI
  // const addRowButton = page.getByRole('button', { name: /Add row/i });
  // await addRowButton.click();
  
  // Verify new row added
  const newRows = await page.locator('table tr').count();
  expect(newRows).toBe(initialRows + 1);
});
```

### TC-CANVAS-010: Export table from Canvas
**Priority**: P2  
**Steps**:
1. Open Canvas with table
2. Click "Export" or "Download" button
3. Select format (CSV, JSON, etc.)
**Expected**:
- Export menu appears
- Can choose format
- File downloads successfully
- Data is correctly formatted

**Playwright Code**:
```typescript
test('export table from canvas', async ({ page }) => {
  // Canvas with table is open
  
  const exportButton = page.getByRole('button', { name: /Export|Download/i });
  await exportButton.click();
  
  // Wait for export menu or download
  // const downloadPromise = page.waitForEvent('download');
  // await page.getByText('CSV').click();
  // const download = await downloadPromise;
  // expect(download.suggestedFilename()).toContain('.csv');
});
```

---

## 4. Canvas Mermaid Editor

### TC-CANVAS-011: Edit Mermaid diagram code
**Priority**: P1  
**Steps**:
1. Open Canvas with Mermaid diagram
2. Modify diagram code
**Expected**:
- Mermaid code is editable as text
- Diagram preview updates in real-time
- Syntax errors are highlighted
- Valid changes render correctly

**Playwright Code**:
```typescript
test('edit mermaid diagram code', async ({ page }) => {
  // Canvas with Mermaid diagram is open
  
  const editor = page.locator('[class*="editor"], textarea');
  
  // Add new node to diagram
  await editor.press('End');
  await editor.type('\n    C --> D[New Node]');
  
  // Wait for diagram re-render
  await page.waitForTimeout(1000);
  
  // Verify new node appears in rendered diagram
  // await expect(page.getByText('New Node')).toBeVisible();
});
```

### TC-CANVAS-012: Switch Mermaid diagram type
**Priority**: P2  
**Steps**:
1. Open Canvas with Mermaid diagram
2. Change diagram type in code (e.g., flowchart to sequence)
**Expected**:
- Diagram type changes on valid code
- Preview updates to new diagram type
- Syntax is validated for new type

**Playwright Code**:
```typescript
test('change mermaid diagram type', async ({ page }) => {
  // Canvas with flowchart is open
  
  const editor = page.locator('[class*="editor"]');
  
  // Replace first line to change type
  // await editor.press('Control+A');
  // await editor.type('sequenceDiagram\n    Alice->>Bob: Hello');
  
  // Wait for re-render
  await page.waitForTimeout(1000);
  
  // Verify sequence diagram rendered
  // Sequence diagrams have specific visual markers
});
```

---

## 5. Canvas UI Controls

### TC-CANVAS-013: Close Canvas
**Priority**: P1  
**Steps**:
1. Canvas is open
2. Click Close or X button
**Expected**:
- Canvas closes
- Returns to conversation view
- Edits are preserved (if saved)
- Original message shows updated content

**Playwright Code**:
```typescript
test('close canvas', async ({ page }) => {
  // Canvas is open
  
  const closeButton = page.getByRole('button', { name: /Close|close|×/i });
  await closeButton.click();
  
  // Verify Canvas closed
  await expect(page.locator('[class*="canvas"]')).not.toBeVisible();
  
  // Verify back to conversation
  await expect(page.getByPlaceholder(/Type your message/)).toBeVisible();
});
```

### TC-CANVAS-014: Canvas keyboard shortcuts
**Priority**: P2  
**Steps**:
1. Canvas is open
2. Test keyboard shortcuts:
   - Ctrl+Z: Undo
   - Ctrl+Y: Redo
   - Ctrl+S: Save
   - Esc: Close
**Expected**:
- All shortcuts work correctly
- Actions match button clicks
- Shortcuts don't conflict with browser defaults

**Playwright Code**:
```typescript
test('canvas keyboard shortcuts', async ({ page }) => {
  // Canvas is open
  
  const editor = page.locator('[class*="editor"]');
  await editor.type('test');
  
  // Test Undo with Ctrl+Z
  await page.keyboard.press('Control+Z');
  await expect(page.getByText('test')).not.toBeVisible();
  
  // Test Redo with Ctrl+Y
  await page.keyboard.press('Control+Y');
  await expect(page.getByText('test')).toBeVisible();
  
  // Test Save with Ctrl+S
  await page.keyboard.press('Control+S');
  // Verify save action (might show toast or update state)
  
  // Test Close with Esc
  await page.keyboard.press('Escape');
  await expect(page.locator('[class*="canvas"]')).not.toBeVisible();
});
```

### TC-CANVAS-015: Canvas full-screen mode
**Priority**: P3  
**Steps**:
1. Canvas is open
2. Click full-screen or maximize button
**Expected**:
- Canvas expands to full screen
- More editing space available
- Can exit full-screen mode

**Playwright Code**:
```typescript
test('canvas full-screen mode', async ({ page }) => {
  // Canvas is open
  
  const fullscreenButton = page.getByRole('button', { name: /full.?screen|maximize/i });
  
  if (await fullscreenButton.isVisible()) {
    await fullscreenButton.click();
    
    // Verify canvas expanded
    const canvas = page.locator('[class*="canvas"]');
    const bbox = await canvas.boundingBox();
    expect(bbox?.width).toBeGreaterThan(1000);
  }
});
```

---

## 6. Canvas Integration

### TC-CANVAS-016: Canvas changes persist in conversation
**Priority**: P1  
**Steps**:
1. Open Canvas, make edits, save
2. Close Canvas
3. Reopen Canvas on same message
**Expected**:
- Changes from previous session are preserved
- Canvas reopens with saved state
- Can continue editing from where left off

**Playwright Code**:
```typescript
test('canvas changes persist', async ({ page }) => {
  // Open canvas and make edit
  // ... canvas open steps ...
  
  const editor = page.locator('[class*="editor"]');
  await editor.type('persistent edit');
  
  // Save and close
  await page.getByRole('button', { name: /Save/i }).click();
  await page.getByRole('button', { name: /Close/i }).click();
  
  // Reopen canvas
  const canvasButton = page.getByRole('button', { name: /canvas/i });
  await canvasButton.click();
  
  // Verify edit is still there
  await expect(page.getByText('persistent edit')).toBeVisible();
});
```

### TC-CANVAS-017: Multiple canvas instances in conversation
**Priority**: P2  
**Steps**:
1. Generate multiple code blocks in conversation
2. Open Canvas for first code block
3. Edit and save
4. Close and open Canvas for second code block
**Expected**:
- Each code block has independent Canvas
- Edits to one don't affect others
- Can switch between different Canvas instances

**Playwright Code**:
```typescript
test('multiple canvas instances', async ({ page }) => {
  await page.goto('/app/chat');
  
  // Generate multiple code blocks
  await page.getByPlaceholder(/Type your message/).fill('Generate Python code');
  await page.getByRole('button', { name: /send/ }).click();
  await page.waitForTimeout(5000);
  
  await page.getByPlaceholder(/Type your message/).fill('Generate JavaScript code');
  await page.getByRole('button', { name: /send/ }).click();
  await page.waitForTimeout(5000);
  
  // Open first canvas
  const canvasButtons = page.getByRole('button', { name: /canvas/i });
  await canvasButtons.nth(0).click();
  
  // Edit first
  await page.locator('[class*="editor"]').type('// First edit');
  await page.getByRole('button', { name: /Save|Close/i }).click();
  
  // Open second canvas
  await canvasButtons.nth(1).click();
  
  // Verify second canvas is different
  await expect(page.getByText('// First edit')).not.toBeVisible();
});
```

---

## Notes

- Canvas feature is a key differentiator - thorough testing critical
- Consider testing with large code blocks/tables for performance
- Verify accessibility (keyboard navigation, screen readers)
- Test on different browsers (Monaco editor compatibility)
- Mermaid diagram testing may need visual regression tests

