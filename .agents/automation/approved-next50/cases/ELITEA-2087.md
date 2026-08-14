---
id: ELITEA-2087
title: "Chat – Edit Table in Canvas Mode – Modify Cell Value and Save Changes"
priority: medium
type: functional
module: chat-interface
status: draft
execution_type: manual
tags: [automated:UI:regression, feat:chat]
requirements: []
---

# ELITEA-2087: Chat – Edit Table in Canvas Mode – Modify Cell Value and Save Changes

**Module:** chat-interface · **Priority:** medium · **Type:** functional

**Objective:** Verify that editing a cell value in the canvas table editor and closing the canvas synchronizes the changes back to the conversation interaction window.

---

## Preconditions

- User is logged in to the Elitea platform.
- The canvas table editor is open (following ELITEA-2086).

---

## Test Data

| Field | Value |
|-------|-------|
| Original cell value | Microsoft |
| Edited cell value | Microsoft_edited |

---

## Steps

| # | Action | Expected Result |
|---|--------|--------------------|
| 1 | Verify the table canvas editor is open | Canvas shows the table in editable grid format |
| 2 | Verify the interaction window on the left shows "Table editing..." indicator with blue border | Editing indicator is visible |
| 3 | Click on the "Microsoft" cell in the Company column | Cell becomes editable with cursor appearing |
| 4 | Change "Microsoft" to "Microsoft_edited" | Cell shows the new value |
| 5 | Press Enter or click outside the cell to confirm the change | Cell displays "Microsoft_edited" |
| 6 | Verify save/update occurs automatically | Canvas shows the updated value |
| 7 | Click the X button to close the canvas | Canvas closes |
| 8 | Locate the table in the conversation | Table is visible in the conversation |
| 9 | Verify the table now displays "Microsoft_edited" in the first row Company column | Changed value is reflected |
| 10 | Verify all other data remains unchanged (Apple, Alphabet, Amazon, etc.) | No other data was affected |

---

## Expected Final State

The edited cell value "Microsoft_edited" is synchronized from the canvas editor back to the conversation table display.

---

## Pass/Fail Criteria

**Pass:**
- All steps complete without errors.
- Cell modification is saved and synchronized to the conversation view.

**Fail:**
- Any step produces an error or unexpected result.
- Changes are not saved or not reflected in the conversation view.
