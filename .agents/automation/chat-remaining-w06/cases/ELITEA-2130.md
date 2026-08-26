---
id: ELITEA-2130
title: "Chat – Pinned Folder Can Be Renamed"
priority: medium
type: functional
module: chat-interface
status: draft
execution_type: manual
tags: [automated:UI:regression, feat:chat]
requirements: []
---

# ELITEA-2130: Chat – Pinned Folder Can Be Renamed

**Module:** chat-interface · **Priority:** medium · **Type:** functional

**Objective:** Verify that a pinned folder can be renamed via the context menu and retains its pinned state after the rename.

---

## Preconditions

- User is logged in to the Elitea platform.
- At least one pinned folder exists in the Chats section.

---

## Test Data

| Field | Value |
|-------|-------|
| New pinned folder name | Pinned Renamed Folder |

---

## Steps

| # | Action | Expected Result |
|---|--------|--------------------|
| 1 | Navigate to Chats and identify a pinned folder (pin icon visible) | Pinned folder found |
| 2 | Hover over the pinned folder, click three-dot icon, verify context menu: Delete, Edit, Export, Unpin | Context menu visible |
| 3 | Click Edit, clear name and type 'Pinned Renamed Folder' | New name in input |
| 4 | Click the checkmark icon | Pinned folder renamed; new name displayed |
| 5 | Verify the folder retains its pinned state (pin icon still visible after rename) | Pin icon still visible |
| 6 | Verify no error message is shown | Rename successful |

---

## Expected Final State

Pinned folder renamed and retains its pinned state.

---

## Pass/Fail Criteria

**Pass:**
- All steps complete without errors.
- Folder renamed; pinned state preserved.

**Fail:**
- Any step produces an error or unexpected result.
- Folder loses pinned state or rename fails.
