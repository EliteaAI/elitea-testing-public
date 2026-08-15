---
id: ELITEA-2125
title: "Chat – Folder Rename – Check Icon Inactive for Less Than 3 Characters"
priority: medium
type: functional
module: chat-interface
status: draft
execution_type: manual
tags: [automated:UI:regression, feat:chat]
requirements: []
---

# ELITEA-2125: Chat – Folder Rename – Check Icon Inactive for Less Than 3 Characters

**Module:** chat-interface · **Priority:** medium · **Type:** functional

**Objective:** Verify that entering fewer than 3 characters in the folder rename field keeps the checkmark icon disabled.

---

## Preconditions

- User is logged in to the Elitea platform.
- At least one existing folder is present in the Chats section.

---

## Test Data

| Field | Value |
|-------|-------|
| Short input | AB |

---

## Steps

| # | Action | Expected Result |
|---|--------|--------------------|
| 1 | Navigate to Chats, hover over a folder, click three-dot icon, click Edit | Folder name is editable |
| 2 | Clear the current name and type exactly 2 characters ('AB') | 2 characters in field |
| 3 | Verify the checkmark icon is in a disabled/inactive state and tooltip is shown | Checkmark inactive; tooltip visible |
| 4 | Attempt to click the checkmark | Click has no effect |

---

## Expected Final State

Checkmark stays inactive for input shorter than 3 characters.

---

## Pass/Fail Criteria

**Pass:**
- All steps complete without errors.
- Checkmark inactive for < 3 characters.

**Fail:**
- Any step produces an error or unexpected result.
- Checkmark active for < 3 characters.
