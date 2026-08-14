---
id: ELITEA-2162
title: "Chat – Search Icon Opens Search Input Field, Returns Partial Results, Conversation Interactable and Modules Panel Accessible"
priority: high
type: functional
module: chat-interface
status: draft
execution_type: manual
tags: [automated:UI:regression, feat:chat]
requirements: []
---

# ELITEA-2162: Chat – Search Icon Opens Search Input Field, Returns Partial Results, Conversation Interactable and Modules Panel Accessible

**Module:** chat-interface · **Priority:** high · **Type:** functional

**Objective:** Verify the search icon opens a search field, partial and full-name queries filter results correctly, clicking a result opens the conversation, and the Modules panel is accessible from the conversation.

---

## Preconditions

- User is logged in to the Elitea platform.
- At least one conversation with a unique name exists.

---

## Test Data

| Field | Value |
|-------|-------|
| Partial query | un | Exact query | unique |

---

## Steps

| # | Action | Expected Result |
|---|--------|--------------------|
| 1 | Navigate to Chats and click the magnifier (search) icon | Left panel switches to search input; X icon appears; folder list replaced by search results area |
| 2 | Type 'un' as partial query | Filtered list shows conversations/folders whose names contain 'un'; non-matching items hidden |
| 3 | Type the exact full name 'unique' | Only matching conversation(s) shown; non-matching hidden |
| 4 | Click the matching conversation in search results | Conversation opens in main panel; URL updates; search input remains visible |
| 5 | Click the + icon at the bottom left of the message input area and click 'Modules' | Modules panel opens with toggleable features: Image creation, Data Analysis, Agents & Pipeline Builder, Planner, Python Sandbox, Swarm Mode, Smart Tool Selection |
| 6 | Toggle 'Image creation' on and off | Toggle state changes correctly; 'Modules configuration Updated' success message appears |
| 7 | Toggle 'Data Analysis' on and off; repeat for other modules | All toggles work; success message shown each time |
| 8 | Close the Modules panel | Main conversation view restored |

---

## Expected Final State

Search works correctly; conversation opens from search results; Modules panel accessible and all toggles functional.

---

## Pass/Fail Criteria

**Pass:**
- All steps complete without errors.
- Search filters correctly; Modules panel accessible with all toggles working.

**Fail:**
- Any step produces an error or unexpected result.
- Search fails or Modules panel is inaccessible.
