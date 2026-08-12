---
id: ELITEA-1920
title: "Build with AI — generating agent draft from in-chat AgentEditor works end-to-end"
priority: high
type: functional
module: agents
status: draft
execution_type: manual
tags: [automated:UI:regression, feat:agents]
requirements: []
---

# ELITEA-1920: Build with AI — generating agent draft from in-chat AgentEditor works end-to-end

**Module:** agents · **Priority:** high · **Type:** functional

**Objective:** Verify the complete end-to-end Build with AI flow when triggered from the in-chat AgentEditor: from opening the modal through generation, review, optional resource selection, approval, and the created agent appearing as a chat participant.

---

## Preconditions

- User is logged in to the Elitea platform with admin or editor role.
- An active chat conversation exists.
- The "+" button to add participants is accessible in the chat.

---

## Test Data

| Field | Value |
|-------|-------|
| Natural-language description | Any valid agent description |

---

## Steps

| # | Action | Expected Result |
|---|--------|-----------------|
| 1 | Open Agent creation editor menu through chat participants ("+" button in chat conversation) | The agent creation editor menu is displayed |
| 2 | Click the Build with AI button | The GenerateAgentModal opens |
| 3 | Enter a natural-language description and click "Generate agent" | The modal shows a loading state |
| 4 | Verify the modal shows loading state then transitions to the review form | The loading indicator is shown, then the review/edit form is displayed |
| 5 | Verify generated fields (Name, Description, Instructions, Welcome message, Conversation starters) are pre-populated | All required fields are pre-populated with generated values |
| 6 | Select desired suggested resources (if any) | Selected resource cards are highlighted |
| 7 | Click "Approve" / "Create Agent" | The agent creation is submitted |
| 8 | Verify the Agent is created and added as a participant in the current conversation | The newly created agent appears as a participant in the active chat conversation |
| 9 | Verify the created Agent is immediately available in the Participants list | The agent is listed in the chat Participants list |

---

## Expected Final State

The agent created via the in-chat Build with AI flow is active as a participant in the current conversation and visible in the Participants list.

---

## Pass/Fail Criteria

**Pass:**
- All steps complete without errors.
- The agent is created via the in-chat flow, added as a conversation participant, and visible in the Participants list.

**Fail:**
- Any step produces an error or unexpected result.
- The agent is not created, not added as a participant, or not visible in the Participants list after approval.
