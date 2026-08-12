---
id: ELITEA-2086
title: "Chat – Edit Generated Table in Canvas Mode – Open Editor and Verify Table Display"
priority: medium
type: functional
module: chat-interface
status: draft
execution_type: manual
tags: [automated:UI:regression, feat:chat]
requirements: []
---

# ELITEA-2086: Chat – Edit Generated Table in Canvas Mode – Open Editor and Verify Table Display

**Module:** chat-interface · **Priority:** medium · **Type:** functional

**Objective:** Verify that clicking the edit icon on an AI-generated table opens the canvas mode editor displaying the table in an editable grid format with sortable columns, row checkboxes, pagination, and a download button.

---

## Preconditions

- User is logged in to the Elitea platform.
- User has an open conversation with an LLM.

---

## Test Data

| Field | Value |
|-------|-------|
| Message to send | generate a table of top 10 IT companies |

---

## Steps

| # | Action | Expected Result |
|---|--------|--------------------|
| 1 | Navigate to Chats and open a conversation | Conversation view is displayed |
| 2 | Send the message "generate a table of top 10 IT companies" | Table is generated and displayed in the conversation |
| 3 | Verify the table shows columns such as Rank, Company, HQ, Primary Focus Areas | Table structure is correct |
| 4 | Verify the table shows company data (e.g. Microsoft, Apple, Alphabet, Amazon, etc.) | Table data is present |
| 5 | Locate the pencil/edit icon in the top right corner of the table | Edit icon is visible |
| 6 | Click the pencil/edit icon | Canvas mode opens with heading "Edit table" |
| 7 | Verify the canvas displays the table in an editable grid format with all columns and rows | Editable grid is shown |
| 8 | Verify sortable column headers with sort icons are present | Column headers are sortable |
| 9 | Verify row checkboxes appear on the left for selecting rows | Row checkboxes visible |
| 10 | Verify pagination controls show "1-10 of 10" and "Rows per page: 50" | Pagination controls correct |
| 11 | Verify a "Download as xlsx" button appears at the bottom right | Download button is visible |

---

## Expected Final State

The canvas mode editor opens correctly showing the full editable table with sortable headers, row checkboxes, pagination, and a download option.

---

## Pass/Fail Criteria

**Pass:**
- All steps complete without errors.
- Canvas editor opens with all required table elements.

**Fail:**
- Any step produces an error or unexpected result.
- Table editor does not open or is missing required elements.
