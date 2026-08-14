---
id: ELITEA-2085
title: "Chat – Create MCP from Conversation – Save Configuration and Verify MCP is Created"
priority: high
type: functional
module: chat-interface
status: draft
execution_type: manual
tags: [automated:UI:regression, feat:chat]
requirements: []
---

# ELITEA-2085: Chat – Create MCP from Conversation – Save Configuration and Verify MCP is Created

**Module:** chat-interface · **Priority:** high · **Type:** functional

**Objective:** Verify that saving a Remote MCP configuration creates the MCP successfully, shows a "Not Connected" warning banner, and after closing the canvas the MCP appears in the PARTICIPANTS panel with a disconnected warning.

---

## Preconditions

- User is logged in to the Elitea platform.
- User has an open conversation in the Chats section.

---

## Test Data

| Field | Value |
|-------|-------|
| MCP Name | test |
| URL | https://api.githubcopilot.com/mcp |
| Client Secret | (any test value) |

---

## Steps

| # | Action | Expected Result |
|---|--------|--------------------|
| 1 | Navigate to Chats and open a conversation | Conversation view is displayed |
| 2 | Click + icon, select "MCPs", click "+ Create New MCP" | "New MCP" canvas opens |
| 3 | Click "Remote" tab and select "Remote MCP" | Configuration canvas opens |
| 4 | Type "test" in "Toolkit Name *" field | Name entered |
| 5 | Type "https://api.githubcopilot.com/mcp" in "Url *" field | URL entered |
| 6 | Enter a test secret value in "Client Secret" field | Secret entered |
| 7 | Click the "Create" button | MCP saved successfully; "The toolkit has been created successfully" success message appears |
| 8 | Verify the canvas header shows "test" as the MCP name | Canvas header updated |
| 9 | Verify a "Not Connected" warning banner appears with orange background and "Login" button | Disconnected warning visible |
| 10 | Click X to close the canvas | Only conversation window is displayed |
| 11 | Verify a "MCPS" section appears in the PARTICIPANTS panel with "test" listed | MCP listed in PARTICIPANTS |
| 12 | Verify an orange warning triangle icon appears next to the MCP with text "Server is disconnected! Reconnect it to use. Log in." | Disconnected warning shown in PARTICIPANTS |

---

## Expected Final State

MCP "test" is created and appears in the PARTICIPANTS panel with a disconnected/not-connected state indicated by orange warning styling.

---

## Pass/Fail Criteria

**Pass:**
- All steps complete without errors.
- MCP is created; disconnected warning appears in canvas and PARTICIPANTS panel.

**Fail:**
- Any step produces an error or unexpected result.
- MCP is not created or does not appear in PARTICIPANTS.
