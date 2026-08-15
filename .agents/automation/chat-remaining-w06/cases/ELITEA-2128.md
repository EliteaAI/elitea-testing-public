---
id: ELITEA-2128
title: "Chat – Folder Rename – Maximum 50 Characters Accepted"
priority: medium
type: functional
module: chat-interface
status: draft
execution_type: manual
tags: [automated:UI:regression, feat:chat]
requirements: []
---

# ELITEA-2128: Chat – Folder Rename – Maximum 50 Characters Accepted

**Module:** chat-interface · **Priority:** medium · **Type:** functional

**Objective:** Verify that exactly 50 characters can be entered in the folder rename field and saved successfully.

---

## Preconditions

- User is logged in to the Elitea platform.
- At least one existing folder is present in the Chats section.

---

## Test Data

| Field | Value |
|-------|-------|
| 50-char string | 50 characters (e.g. AAAA...AA) |

---

## Steps

| # | Action | Expected Result |
|---|--------|--------------------|
| 1 | Navigate to Chats, hover over a folder, click three-dot icon, click Edit | Folder name is editable |
| 2 | Clear the current name and type exactly 50 characters | All 50 characters are accepted |
| 3 | Click the checkmark icon | Folder saved with 50-character name; no error shown |

---

## Expected Final State

Folder saved with a 50-character name.

---

## Pass/Fail Criteria

**Pass:**
- All steps complete without errors.
- 50-character name accepted and saved.

**Fail:**
- Any step produces an error or unexpected result.
- Name rejected at 50 chars or error shown.
