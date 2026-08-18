---
id: ELITEA-2421
title: Send message with attached file
status: defect-found
priority: medium
type: functional
module: support-assistant
tms_case: ../onetest-ai-tm-Elitea/tests/automated-full-regression-ui/support-assistant/ELITEA-2421_send-message-with-attached-file.md
analyst: qa-engineer
analysis_date: 2026-08-18
---

# Automation-Friendly Spec: Send message with attached file

**TMS Case:** ELITEA-2421  
**Status:** `defect-found`  
**Priority:** medium  
**Surface:** Support Assistant widget  
**Analysis Date:** 2026-08-18

---

## Executive Summary

Executed ELITEA-2421 against `http://localhost:5173` (EliteaUI `automation/testids` branch). 

**DEFECT FOUND:** File attachment functionality is **NOT implemented** in the Support Assistant. While the UI allows selecting a file via the file picker, and the attachment chip appears before sending, **the file is not included with the sent message** and **the assistant response does not reference or process the file content**. The assistant returns only an echo response that does not demonstrate file processing capability.

The case cannot proceed to `ready-for-automation` until this defect is resolved.

---

## Coverage Map

### Axis 1: Case Element → Coverage

| Case Element | Expected Result | Covered By | Asserted Where | Disposition |
|---|---|---|---|---|
| Step 1: Open Support Assistant widget | Widget loads successfully | Click launcher + wait for widget visible | Widget title "Elitea Assistant" visible | ✅ PASS |
| Step 2: Click Attach file button and select file | File picker opens and file selected | Click attach button + file_chooser.set_files() | File chooser opened | ✅ PASS |
| Step 3: Verify file preview/chip appears | Attachment chip visible before send | Visual inspection of DOM | Chip with filename + remove button present | ✅ PASS |
| Step 4: Type message | Input accepts text | Type into textbox | Message displayed in input | ✅ PASS |
| Step 5: Click Send | Message sent | Click send button | User message appears in chat | ✅ PASS |
| Step 6: Verify attachment indicator in sent message | Sent message shows file was attached | Visual inspection of sent message | **❌ FAIL** - No attachment indicator |
| Step 7: Verify assistant processes file content | Response references/summarizes file content | Check assistant response text | **❌ FAIL** - Echo response only, no file processing |

### Axis 2: Observable Beyond Case

| Observable | Why Asserted | Grounded In |
|---|---|---|
| Attachment chip removal button | Confirms UI allows removing before send | Standard file-attachment UX pattern |
| Send button state changes (disabled → enabled) | Confirms button responds to input state | Standard form validation pattern |
| Console errors | Side-channel check for silent failures | Standard defect discovery practice |

---

## Known Defects

### DEFECT: File attachment not implemented in Support Assistant

**Severity:** Major  
**Impact:** High - Core functionality advertised by UI but not working

**Observed Behavior:**
1. File selection UI works correctly - file picker opens, file can be selected
2. Attachment chip appears in the input area with filename and remove button
3. **BUG:** After clicking Send, the sent user message has **no attachment indicator**
4. **BUG:** Assistant response is generic echo: "Echo: Summarize the content of this file" - does NOT process or reference the file content
5. The file content ("This is a test file for the Support Assistant...") is never acknowledged

**Expected Behavior:**
- Sent message should show attachment indicator (file icon, chip, or filename)
- Assistant response should reference or summarize the actual file content

**Evidence:**
- Screenshots: `test-results/screenshots/ELITEA-2421-step-03-file-attached.png` (chip visible before send)
- Screenshots: `test-results/screenshots/ELITEA-2421-step-06-message-sent-with-attachment.png` (no attachment after send)
- Network requests show no file upload to backend
- DOM inspection confirms sent message lacks attachment metadata

**Root Cause Assessment:**
The Support Assistant UI provides file attachment controls but the feature is not connected to the backend. The file is:
- Held in browser state locally
- NOT uploaded to the server
- NOT passed to the AI model
- NOT referenced in the response

This is a **stub UI** - the controls exist but file handling is not implemented.

---

## Handles Reference

| Element | Handle Type | Value | Context | PROVENANCE |
|---|---|---|---|---|
| Support Assistant launcher | aria-label | `button[aria-label="Support Assistant"]` | Main page | needs verification (legacy fallback) |
| Widget title | text content | "Elitea Assistant" | Widget header | on-main ✓ (verified) |
| Attach file button | aria-label | `button[aria-label="Attach file"]` | Widget input area | needs verification (legacy fallback) |
| Message input | placeholder | `textbox[placeholder="Type a message..."]` | Widget input area | needs verification (legacy fallback) |
| Send button | aria-label | `button[aria-label="Send message"]` | Widget input area | needs verification (legacy fallback) |
| Attachment chip container | class selector | `.elitea-assistant-*` (dynamic) | Input area before send | needs verification |
| Attachment filename | text content | Within chip container | — | needs verification |
| Remove attachment button | aria-label pattern | Contains "Remove" + filename | Within chip | needs verification |

**Critical Note:** All handles above use legacy fallback selectors (aria-label, placeholder, class). Per testid-only policy (`.agents/testing.md`), every element touched by automation requires a `data-testid`. The implementer must run `add-data-testid` skill on ALL Support Assistant elements before implementation.

**Provenance Verification Status:** Handles documented from live observation against `localhost:5173` (`automation/testids` branch, 2026-08-18). Testid presence NOT verified - assume ALL need adding.

---

## Fidelity Declaration

No substitutions used. All observations from the live Support Assistant widget against DEV backend at `http://localhost:5173`.

---

## Preconditions

- User logged in to Elitea platform (localhost uses `VITE_DEV_TOKEN`, skips Keycloak)
- Support Assistant feature enabled for the project
- Access to any page where Support Assistant launcher appears

---

## Test Data

| Field | Value | Source |
|---|---|---|
| Test file | `test_attachment.txt` | Created during analysis |
| File content | "This is a test file for the Support Assistant. It contains sample content about the Elitea platform. The platform helps users collaborate with AI assistants." | Analyst-generated sample |
| Test message | "Summarize the content of this file" | From case Step 4 |

---

## Classification Rationale

**Status: `defect-found`**

This case cannot be automated in its current form because the feature under test is not implemented. Steps 1-5 work correctly (UI interactions), but Steps 6-7 (the actual file attachment and processing) fail due to a product defect.

The defect blocks automation because:
1. **Step 6 cannot be verified** - There is no attachment indicator to assert on
2. **Step 7 cannot be verified** - The assistant does not process the file, so there is no file-related content to assert

**Why not `blocked`?** 
- `blocked` means the analyst cannot complete exploration due to access/env/data issues
- Here, exploration completed successfully and revealed a defect
- The implementation is blocked by the defect, not the analysis

**Next Steps:**
1. File defect ticket in tracker per `.agents/profile.md` § Bug filing
2. Link defect to this AFS
3. Return status `defect-found` with defect ID
4. Case returns to analyst queue after defect is fixed

---

## Notes for Implementer

**DO NOT IMPLEMENT until defect is resolved.** 

Once fixed, the implementer will need to:

1. **Add testids** - Run `add-data-testid` on EVERY Support Assistant element (launcher, widget controls, attach button, input, send button, message containers). The page object `support_assistant_page.py` currently uses fallback locators - all must become testid-only.

2. **Verify attachment indicator** - After fix, determine how attachments are displayed in sent messages (chip? icon? filename?) and capture the specific element/attribute to assert on.

3. **Verify response behavior** - Confirm assistant response actually references file content (not just echoes the prompt). Capture the expected response pattern for assertion.

4. **Network verification** - Check that file upload request actually fires and succeeds (status 200, file in payload).

5. **Extend existing test** - `test_support_assistant_smoke.py` already has `test_attach_button_present_and_opens_picker` covering Steps 1-3. Extend or create new test for the full send + response flow (Steps 4-7).

---

## Evidence Paths

All evidence stored under `test-results/screenshots/`:
- `ELITEA-2421-step-02-widget-open.png` - Widget opened, showing attach button
- `ELITEA-2421-step-03-file-attached.png` - File chip visible before send
- `ELITEA-2421-step-04-message-typed.png` - Message typed with attachment present
- `ELITEA-2421-step-06-message-sent-with-attachment.png` - After send, no attachment visible

Test file: `test-results/test_attachment.txt`

---

## Blocked Steps

None - all steps were executed. The defect was discovered through execution, not blocked by inability to execute.

---

## Out of Scope

None identified.

