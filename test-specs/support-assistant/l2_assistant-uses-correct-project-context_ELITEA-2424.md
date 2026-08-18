---
id: ELITEA-2424
title: Assistant uses correct project context
priority: medium
status: defect-found
test_type: ui
surface: support-assistant
defects:
  - issue: "#1585"
    summary: "Support Assistant cannot access project context — 403 Forbidden on project_info API, echoes questions instead of answering"
---

# ELITEA-2424: Assistant uses correct project context

**Status:** `defect-found`  
**Defect:** #1585 — Support Assistant cannot access project context (403 Forbidden)

## Defect Summary

The Support Assistant widget cannot retrieve current project information due to a **403 Forbidden** error when accessing `/api/v2/elitea_core/project_info/prompt_lib/{project_id}/project-info`. When asked about the current project, the assistant echoes the user's question instead of providing the requested information.

**Console Error:**
```
Failed to load resource: the server responded with a status of 403 (Forbidden) 
@ http://localhost:5173/api/v2/elitea_core/project_info/prompt_lib/1/project-info:0
```

**Reproduced:** 100% on both Private (ID: 121) and Public (ID: 1) projects.

## Test Objective

Verify that the Support Assistant correctly identifies and reports the user's current project name and project ID, and that switching projects updates this context.

## Preconditions

- User is authenticated and logged into the Elitea platform
- User has access to at least two different projects

## Test Data

| Field | Value |
|---|---|
| Test projects | Private (ID: 121), Public (ID: 1) |
| Test message | "What project am I currently working in? What is the project name and project ID?" |

## Steps Executed (Blocked by Defect)

| # | Action | Expected Result | Actual Result | Status |
|---|--------|-----------------|---------------|--------|
| 1 | Navigate to Private project via project selector | Settings page loads for Private project | ✅ Settings loaded, shows "Private" | PASS |
| 2 | Note current project: name "Private", ID "121" visible in Settings > General | Confirmed project context | ✅ Confirmed | PASS |
| 3 | Open Support Assistant widget via launcher button | Widget opens with greeting message | ✅ Widget opened, greeting displayed | PASS |
| 4 | Send message: "What project am I currently working in? What is the project name and project ID?" | Assistant responds with correct project name "Private" and ID "121" | ❌ **Assistant echoes question**: "Echo: What project am I currently working in?..." <br>**Console 403 error** on project_info API | BLOCKED |
| 5 | Verify response matches current project context | Assistant's response contains "Private" and "121" | ❌ Cannot verify — no actual response provided | BLOCKED |
| 6 | Switch to Public project, repeat steps 3-5 | Assistant reflects new context: "Public", ID "1" | ❌ Same echo behavior, **403 error** for project ID 1 | BLOCKED |

## Blocked Steps

**Steps 4-6** are blocked due to the 403 permissions error preventing the Support Assistant from accessing project information.

## Known Defects

- **#1585** (OPEN, blocking): Support Assistant 403 Forbidden on project_info endpoint — assistant cannot retrieve project context, echoes questions instead of answering

## Evidence

- **Screenshot:** `test-results/screenshots/ELITEA-2424-step-02-settings-private-project.png` — Settings showing Private project (ID: 121)
- **Screenshot:** `test-results/screenshots/ELITEA-2424-step-04-assistant-response-private-project.png` — Assistant echo response on Private project
- **Screenshot:** `test-results/screenshots/ELITEA-2424-step-06-switched-to-public-project.png` — Settings showing Public project (ID: 1)
- **Screenshot:** `test-results/screenshots/ELITEA-2424-step-06-assistant-response-public-project.png` — Assistant echo response on Public project
- **Console:** 403 Forbidden error: `/api/v2/elitea_core/project_info/prompt_lib/{project_id}/project-info`

## Handles Reference

All handles are from the Support Assistant widget (`elitea_assistant` package, consumed as `@eliteaai/elitea-assistant` git-dependency):

| Element | Handle | Provenance |
|---|---|---|
| Support Assistant launcher button | *JS-evaluate click* (MUI overlay interception) | Connected repo (elitea_assistant) — no testid yet |
| Message input textbox | `role="textbox", name="Type a message..."` | Connected repo — no testid yet |
| Send message button | `role="button", name="Send message"` | Connected repo — no testid yet |
| Assistant message text | Extract from message container DOM | Connected repo — no testid yet |

**Note:** The Support Assistant is a connected first-party repo (`EliteaAI/elitea_assistant`, branch `automation/testids`). Testids should be added in THAT repo's source, not EliteaUI. See `.agents/workflow.md` § Connected repos.

## Coverage Map

### Axis 1: TMS Case Elements → Test Coverage

| Case Element | Expected Result | Covered By | Asserted Where | Disposition |
|---|---|---|---|---|
| Step 1: Navigate to a project other than Support Assistant's deployment project | Target page loads successfully | Widget open + message send | Navigation successful, Settings loaded | ready-for-automation (post-fix) |
| Step 2: Note current project name in Settings | Action completes | Visual confirmation | Settings shows "Private", ID "121" | ready-for-automation (post-fix) |
| Step 3: Open Support Assistant widget | Widget opens | Widget launcher click | Widget opened, greeting visible | ready-for-automation (post-fix) |
| Step 4: Send message asking for project name and ID | Action completes | Message send | Message sent successfully | ready-for-automation (post-fix) |
| Step 5: Verify assistant responds with correct project name and ID matching current project | Response contains correct name and ID, NOT the Support Assistant's internal project | **Assistant response validation** | **BLOCKED by #1585** — 403 error prevents context retrieval | blocked |
| Step 6: Navigate to different project, repeat steps 3-5 | Assistant correctly reflects new project context | Project switch + repeat query | **BLOCKED by #1585** — same 403 error on different project | blocked |

### Axis 2: Additional Observables Beyond Case

| Observable | Reason | Asserted Where |
|---|---|---|
| Console 403 Forbidden error on `/api/v2/elitea_core/project_info/` | Root cause of echo behavior — assistant cannot access project context | Console error check |
| Assistant echoes question instead of answering | Symptom of missing project context data | Message text validation |
| Support Assistant widget remains functional (opens, accepts input, sends messages) | Widget UI itself works; only the context-retrieval backend fails | Widget interaction steps |

## Classification Rationale

**Status: `defect-found`**

The test case's core assertion — that the Support Assistant uses correct project context when answering questions — cannot be verified due to a backend permissions error (403 Forbidden). The assistant's behavior (echoing questions) indicates it has no project context data to work with, directly contradicting its greeting message claim that it "has context about your current screen and settings."

All non-blocked steps (widget opens, messages send) completed successfully, confirming the widget UI is functional. The failure is isolated to the project-context retrieval mechanism.

## Implementation Notes (Post-Fix)

Once defect #1585 is resolved:

1. **Add testids to Support Assistant widget** (in `elitea_assistant` repo on `automation/testids` branch):
   - Launcher button
   - Message input textbox
   - Send button
   - Message containers (user and assistant)

2. **Page object:** Extend `automation/pages/support_assistant_page.py` with testid-based `LocatorDescriptor` fields (update existing fallback handles)

3. **Test implementation:**
   - Navigate to first project, extract name/ID from Settings
   - Open widget, send query, wait for AI response (WebSocket, ~5s)
   - Assert response contains expected project name and ID (substring match)
   - Navigate to second project, repeat
   - Assert second response reflects new project context

4. **Wait strategy:** AI responses arrive via WebSocket with ~2-5s delay. Use framework wait for message count increase + response text visibility (not fixed sleep).

5. **Verification tie-breaker:** Cross-check assistant's reported project ID against the Settings page's displayed Project ID to confirm accuracy.

## Analyst Notes

- **Root cause confirmed via console:** The 403 error occurs BEFORE the assistant attempts to formulate a response, explaining the echo behavior
- **Reproducibility:** 100% across different projects (Private/Public), indicating a systematic permissions issue, not a transient backend failure
- **Connected-repo testid work:** Support Assistant source lives in `../elitea_assistant` (sibling clone), not EliteaUI. Testids go there, on ITS `automation/testids` branch. One extra promotion hop vs EliteaUI testids.
- **Launcher click quirk:** Standard Playwright MCP `browser_click` fails on the launcher button (MUI overlay interception). Used JS-evaluate click (`page.evaluate`) per project memory note.
