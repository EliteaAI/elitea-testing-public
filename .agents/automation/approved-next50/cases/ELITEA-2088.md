---
id: ELITEA-2088
title: "Chat – Generate Mermaid Diagram and Open in Canvas Mode"
priority: medium
type: functional
module: chat-interface
status: draft
execution_type: manual
tags: [automated:UI:regression, feat:chat]
requirements: []
---

# ELITEA-2088: Chat – Generate Mermaid Diagram and Open in Canvas Mode

**Module:** chat-interface · **Priority:** medium · **Type:** functional

**Objective:** Verify that an AI-generated Mermaid diagram can be opened in canvas mode for editing, that the Mermaid syntax is editable in the canvas, and that changes are applied back to the conversation view.

---

## Preconditions

- User is logged in to the Elitea platform.
- User has an open conversation in the Chats section.

---

## Test Data

| Field | Value |
|-------|-------|
| Message to send | generate a mermaid diagram |

---

## Steps

| # | Action | Expected Result |
|---|--------|--------------------|
| 1 | Navigate to Chats and open a conversation | Conversation view is displayed |
| 2 | Send the message "generate a mermaid diagram" | A visual flowchart/diagram is rendered in the conversation |
| 3 | Verify the diagram displays nodes and connecting lines/arrows | Diagram is rendered with connections |
| 4 | Locate the pencil/edit icon on the diagram | Edit icon is visible |
| 5 | Click the pencil icon | Canvas mode opens with heading "Edit diagram" |
| 6 | Verify the canvas displays the Mermaid code/syntax in a text editor | Mermaid syntax is visible and editable |
| 7 | Verify the interaction window shows "Diagram editing..." indicator with blue border | Editing indicator is visible |
| 8 | Edit one block of text by adding "edited" to it | Text is modified in the canvas |
| 9 | Verify the canvas validates Mermaid syntax in real-time | Syntax validation occurs |
| 10 | Close the canvas window | Canvas closes |
| 11 | Verify changes are applied to the edited block in the mermaid diagram | Updated diagram shown in conversation |

---

## Expected Final State

The Mermaid diagram canvas opens correctly, allows editing, and changes are applied back to the diagram in the conversation view.

---

## Pass/Fail Criteria

**Pass:**
- All steps complete without errors.
- Canvas opens, editing works, and changes are reflected in the conversation.

**Fail:**
- Any step produces an error or unexpected result.
- Canvas does not open, editing fails, or changes are not reflected.
