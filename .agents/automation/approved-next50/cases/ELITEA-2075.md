---
id: ELITEA-2075
title: "Chat – Agent Hub Agent – Verify Only LLM and LLM Settings Can Be Changed and Changes Are Saved Per Conversation Only"
priority: high
type: functional
module: chat-interface
status: draft
execution_type: manual
tags: [automated:UI:regression, feat:chat]
requirements: []
---

# ELITEA-2075: Chat – Agent Hub Agent – Verify Only LLM and LLM Settings Can Be Changed and Changes Are Saved Per Conversation Only

**Module:** chat-interface · **Priority:** high · **Type:** functional

**Objective:** Verify that when opening an Agent Hub agent's settings canvas in a conversation, only the LLM model selector and LLM settings are editable, while all other sections (Instructions, Welcome Message, Tools, Skills) are read-only.

---

## Preconditions

- User is logged in to the Elitea platform.
- Agent HUB is accessible from the left sidebar.

---

## Test Data

| Field | Value |
|-------|-------|
| Agent name | Reflexion |
| LLM model to select | Anthropic Claude 4.5 Sonnet |
| Test message | hello |

---

## Steps

| # | Action | Expected Result |
|---|--------|--------------------|
| 1 | Navigate to Agent HUB from the left sidebar | Agent HUB page opens with categories |
| 2 | Locate the "Reflexion" agent and click on it | Agent preview modal opens |
| 3 | Click the "Start conversation" button | New conversation is created; PARTICIPANTS panel shows "Reflexion v1.0" |
| 4 | Click the "View settings" button next to the agent in PARTICIPANTS | Agent settings canvas opens showing "Reflexion v1.0" with "Public" label |
| 5 | Verify the LLM model selector is visible at the top | LLM model chip (e.g. "GPT-5.4-mini") is displayed and clickable |
| 6 | Verify the INSTRUCTIONS section appears READ-ONLY | Text is visible but not editable |
| 7 | Verify module toggles in TOOLS section appear DISABLED | Toggles are greyed out and cannot be changed |
| 8 | Verify no SAVE button is visible (confirming view-only mode for most settings) | No Save button in canvas header |
| 9 | Click the LLM model chip and select "Anthropic Claude 4.5 Sonnet" from the dropdown | Model selector updates to show new model |
| 10 | Click the settings/gear icon next to the LLM model selector | Model settings modal opens with REASONING slider, MAX COMPLETION TOKENS, CAPABILITIES |
| 11 | Adjust REASONING slider to "High" and click "Apply" | Modal closes; LLM settings updated |
| 12 | Attempt to click into the INSTRUCTIONS text area | No cursor appears; text cannot be edited |
| 13 | Close the canvas by clicking X and verify canvas closes | Conversation view is displayed |
| 14 | Send a test message "hello" | Agent responds using the newly selected LLM model |

---

## Expected Final State

Agent Hub agent's canvas allows LLM model and LLM settings changes only. Instructions and tools remain read-only. The new LLM is used for the conversation.

---

## Pass/Fail Criteria

**Pass:**
- All steps complete without errors.
- Only LLM model and settings can be changed; all other sections are read-only.

**Fail:**
- Any step produces an error or unexpected result.
- Instructions become editable, or LLM model cannot be changed.
