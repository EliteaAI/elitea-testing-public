---
id: ELITEA-1934
title: "Remote MCP — Load Tools from Invalid URL"
priority: high
type: functional
module: elitea-platform
status: draft
execution_type: manual
tags: [automated:UI:regression]
requirements: []
---

# ELITEA-1934: Remote MCP — Load Tools from Invalid URL

**Module:** elitea-platform · **Priority:** medium · **Type:** functional

**Objective:** Verify that attempting to load tools from a Remote MCP with an invalid or unreachable URL produces an appropriate error toast and displays "Not Connected" status.

---

## Preconditions

- User is logged in to the Elitea platform.

---

## Test Data

| Field | Value |
|-------|-------|
| Toolkit Name | autotest_tools_invalid_url |
| Invalid URL | https://nonexistent.invalid/mcp |

---

## Steps

| # | Action | Expected Result |
|---|--------|-----------------|
| 1 | Create a new Remote MCP with name "autotest_tools_invalid_url" | MCP creation form loads |
| 2 | Fill URL with an invalid URL (e.g., "https://nonexistent.invalid/mcp") | Field accepts and displays the URL |
| 3 | Save the MCP | MCP detail page loads |
| 4 | Click "Load Tools" | Tool loading is attempted |
| 5 | Verify toast error indication appears with message "Failed to sync MCP tools: DNS resolution failed. Please check the server hostname in the URL." | Error toast is displayed with correct message |
| 6 | Verify connection status shows "Not Connected" | Status indicator shows "Not Connected" |

---

## Expected Final State

An error toast is shown with the DNS failure message, and the connection status displays "Not Connected".

---

## Pass/Fail Criteria

**Pass:**
- All steps complete without errors.
- Error toast with DNS message is shown and status is "Not Connected".

**Fail:**
- Any step produces an error or unexpected result.
- No error is shown, or status does not reflect the connection failure.
