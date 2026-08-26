---
id: ELITEA-2126
title: "Chat – Folder Rename – Check Icon Becomes Active at 3 Characters"
priority: medium
type: functional
module: chat-interface
status: draft
execution_type: manual
tags: [automated:UI:regression, feat:chat]
requirements: []
---

# ELITEA-2126: Chat – Folder Rename – Check Icon Becomes Active at 3 Characters

**Module:** chat-interface · **Priority:** medium · **Type:** functional

**Objective:** Verify that typing a third character in the folder rename field activates the checkmark icon.

---

## Preconditions

- User is logged in to the Elitea platform.
- At least one existing folder is present in the Chats section.

---

## Test Data

| Field | Value |
|-------|-------|
| Three chars | ABC |

---

## Steps

| # | Action | Expected Result |
|---|--------|--------------------|
| 1 | Navigate to Chats, hover over a folder, click three-dot icon, click Edit | Folder name is editable |
| 2 | Clear the current name and type 2 characters ('AB') | Checkmark is inactive |
| 3 | Type one more character ('ABC') | Checkmark icon becomes active/enabled |
| 4 | Click the checkmark icon | Folder renamed to 'ABC' in the folder list |

---

## Expected Final State

Checkmark activates at exactly 3 characters; folder renamed.

---

## Pass/Fail Criteria

**Pass:**
- All steps complete without errors.
- Checkmark activates at 3 chars; rename succeeds.

**Fail:**
- Any step produces an error or unexpected result.
- Checkmark does not activate at 3 chars.
