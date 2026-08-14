---
id: ELITEA-1937
title: "Remote MCP — Test Settings Panel — Select and Run Tool"
priority: medium
type: functional
module: elitea-platform
status: draft
execution_type: manual
tags: [automated:UI:regression]
requirements: []
---

# ELITEA-1937: Remote MCP — Test Settings Panel — Select and Run Tool

**Module:** elitea-platform · **Priority:** medium · **Type:** functional

**Objective:** Verify that the Test Settings panel on a Remote MCP detail page allows selecting a tool from the dropdown and executing it, with the result displayed in the chat area.

---

## Preconditions

- User is logged in to the Elitea platform.
- A Remote MCP with discovered tools (e.g., "Web Search") is available.

---

## Test Data

| Field | Value |
|-------|-------|
| Tool to select | tavily_search |

---

## Steps

| # | Action | Expected Result |
|---|--------|-----------------|
| 1 | Open a Remote MCP detail page that has discovered tools (e.g., "Web Search") | Detail page loads |
| 2 | Verify right-side "Test Settings" panel is visible | Test Settings panel is displayed |
| 3 | Verify LLM model selector shows a default model (e.g., "GPT-5.4-mini") | Default model is shown in the selector |
| 4 | Verify "Tool" label and combobox dropdown are present | Tool dropdown is visible |
| 5 | Click the Tool combobox dropdown | Dropdown opens |
| 6 | Verify dropdown lists all available tools for this MCP (e.g., tavily_search, tavily_extract, etc.) | All MCP tools are listed |
| 7 | Select a tool (e.g., "tavily_search") | Tool is selected in the dropdown |
| 8 | Verify welcome message in chat area: "Welcome! Select a tool from the Test Settings panel and click 'RUN TOOL' to see the results here." | Welcome message is shown |
| 9 | Type a test query in the tool parameters and click "RUN TOOL" | Tool execution is triggered |
| 10 | Verify response appears in the chat area from the selected tool | Response from the tool is displayed in chat |

---

## Expected Final State

The selected tool executes successfully and returns a response visible in the chat area of the Test Settings panel.

---

## Pass/Fail Criteria

**Pass:**
- All steps complete without errors.
- Tool runs and response appears in the chat area.

**Fail:**
- Any step produces an error or unexpected result.
- Tool does not run, or no response appears in chat.
