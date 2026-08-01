# Test Case: Remote MCP — Load Tools from Invalid URL

## Metadata
- **TMS ID**: ELITEA-1934
- **Linked Story**: none
- **Priority**: l2 — TMS frontmatter says `priority: high` (the case body's own
  "Priority: medium" line is stale/inconsistent with its own frontmatter — same
  pattern seen elsewhere in this TMS, e.g. ELITEA-1921's AFS). Used the sibling
  same-priority case ELITEA-1933 (`priority: high` → `l2_`) as the l-number
  precedent. Note for the lead: this TMS's `high`→l-number mapping is NOT
  perfectly consistent across existing AFS history — `l1_mcp-dashboard-view-
  toggle-card-table_ELITEA-1944.md` is also `priority: high` per TMS but was
  filed as `l1_`. Flagging, not resolving — doesn't block automation.
- **Environment Explored**: local (`http://localhost:5173`, `EliteaAI/EliteaUI`
  @ `automation/testids`, DEV backend)
- **User set**: `${TEST_USER}` (localhost: no login needed — `VITE_DEV_TOKEN`
  auto-auths the dev server)
- **Analyst**: qa-engineer (agent), session 2026-08-01 (cluster dispatch with
  ELITEA-1937, shared login/navigation/discovery — steps executed and
  observed individually per case)
- **Status**: ready-for-automation

## Preconditions
- User is authenticated (localhost: automatic via `VITE_DEV_TOKEN`).
- Project context is set (`Project: Private`, project id `399` this session).

## Test Data

### generate-per-test (in test setup, cleaned up in its own teardown)
- Toolkit Name: `autotest_tools_invalid_url` (case's own literal value — no
  uniqueness collision risk explored this session, matches the case's own
  Test Data table verbatim; recommend the implementer suffix with a per-run
  token if a collision is ever observed, same open question noted at
  ELITEA-1922/1933).
- Invalid URL: `https://nonexistent.invalid/mcp` (case's own literal value — a
  real, guaranteed-unresolvable hostname; DNS lookup fails deterministically,
  no flakiness risk from a transient network hiccup on a "real" domain).

## Test Steps

1. Navigate to `${BASE_URL}/mcps/create`, click the Remote MCP type card
   (`[data-testid="toolkit-type-card-mcp"]`).
   - **Verify**: URL becomes `${BASE_URL}/mcps/create/mcp`; Toolkit Name / Url
     fields are visible.
2. Fill Toolkit Name (`[data-testid="toolkit-form-name-input"]`) with
   `autotest_tools_invalid_url`.
   - **Verify**: field displays the typed value.
3. Fill Url (`[data-testid="toolkit-field-url-input"]`) with
   `https://nonexistent.invalid/mcp`.
   - **Verify**: field displays the typed value; Save button
     (`[data-testid="toolkit-form-save-button"]`) becomes enabled.
4. Click Save.
   - **Verify**: `POST /api/v2/elitea_core/tools/prompt_lib/${PROJECT_ID}`
     returns `201 Created`; page navigates to
     `${BASE_URL}/mcps/all/{id}?name=autotest_tools_invalid_url`.
5. On the detail page, before Load Tools, verify the connection-status
   indicator shows "Not Connected".
   - **Verify**: text content is exactly `Not Connected` — confirmed live via
     DOM snapshot before any Load Tools interaction. **No testid on this
     element** (see Concrete Handles) — an interim text-based locator is used
     here.
6. Click the "Load Tools" element
   (`[data-testid="toolkit-load-tools-button"]`).
   - **Verify**: `POST /api/v2/elitea_core/mcp_sync_tools/prompt_lib/${PROJECT_ID}?await_response=true`
     resolves `200 OK` (NOT an error status — the backend reports the DNS
     failure as a `200` envelope with `{"result": {"success": false, "error":
     "...", "server_url": "..."}}`, confirmed live via network capture — see
     § Network Behavior). This is the real completion signal for step 7,
     not an HTTP error code.
7. Verify a toast error indication appears with the message "Failed to sync
   MCP tools: DNS resolution failed. Please check the server hostname in the
   URL."
   - **Verify**: confirmed live — `role="alert"` MUI Alert renders with EXACTLY
     that text, immediately after the `mcp_sync_tools` response resolves.
     **Auto-dismisses within a few seconds** (confirmed: a snapshot taken ~3s
     after the click could no longer find the alert element) — assert on it
     immediately after the click resolves, in the same wait chain, never as a
     separate later step. No testid on the toast (see Concrete Handles).
8. Verify connection status still shows "Not Connected" after the failed Load
   Tools attempt.
   - **Verify**: confirmed live — `document.body.textContent` still contains
     "Not Connected" after the toast fires; the failed sync does not flip the
     indicator to "Connected!".

## Expected Results
- Saving a Remote MCP with an unresolvable URL succeeds (the MCP entity
  itself is created — URL reachability isn't validated at Save time).
- Clicking "Load Tools" against that URL produces a `200` API response whose
  body reports `success: false` with the exact DNS-failure message the case
  expects, server-side.
- The UI surfaces that failure as a toast with the identical message text.
- The connection-status indicator stays "Not Connected" both before and after
  the failed attempt — no false "Connected" state.
- **No product defect found** — live behavior matches the case's expected
  result exactly, verbatim message included.

## Coverage Map

### Axis 1 — Case coverage

| Case element | Expected result | Covered by (AFS step) | Asserted where | Disposition |
|---|---|---|---|---|
| Preconditions: user logged in | — | — | localhost auto-auth | asserted |
| 1 Create Remote MCP named "autotest_tools_invalid_url" | form loads | steps 1–2 | step 2 | asserted |
| 2 Fill URL with invalid URL | field accepts/displays URL | step 3 | step 3 | asserted |
| 3 Save the MCP | detail page loads | step 4 | step 4: 201 + navigation | asserted |
| 4 Click "Load Tools" | tool loading attempted | step 6 | step 6: network fires | asserted |
| 5 Verify toast error with exact DNS message | toast shown | step 7 | step 7 | asserted — exact text match confirmed live |
| 6 Verify connection status shows "Not Connected" | status shows Not Connected | step 8 | step 8 | asserted — **also verified as the PRE-existing state at step 5, added value beyond the case's literal step order** |
| Expected Final State: error toast + Not Connected status | — | steps 7–8 | steps 7–8 | asserted |
| Pass/Fail criteria: all steps complete, toast + status correct | — | all steps | all steps | asserted — no blocking errors; live behavior matches case exactly |

### Axis 2 — Analyst additions

- `step 5` asserts "Not Connected" is shown BEFORE Load Tools is even
  clicked (case only asks for it after) — *added: proves the indicator's
  baseline state, so step 8's "still Not Connected" is a real regression
  guard (no accidental transient "Connected" flash) rather than an assertion
  against an indicator that was never anything else.*
- `step 6` asserts the `mcp_sync_tools` response status is `200` with a
  `success: false` envelope, NOT a `4xx`/`5xx` — *added: this is the kind of
  fact a raw "wait for network idle" implementation would silently get wrong
  (treating any non-2xx as the failure signal); the case's own step 4/5 don't
  specify the HTTP-level shape, so this fixes the wait condition an
  implementer would otherwise have to guess.*
- No console-error assertion added — the same pre-existing tracked warnings
  from the ELITEA-1933 session (issues #291, #549) reproduced again here,
  unrelated to this case's own pass/fail criteria.

## Cleanup

1. This case creates a persistent MCP toolkit entity (confirmed via `201
   Created`, `id: 2139` this session, name `autotest_tools_invalid_url`).
2. Delete it in test teardown via the existing `ToolkitAPI.delete_toolkit(toolkit_id)`
   client, same pattern as ELITEA-1933/1922.
3. Not deleted during this analysis session (analyst has no automation
   authoring/cleanup authority — `.agents/memory/qa-engineer/analyst_slot_has_no_git_commit_authority.md`).
   Flag to the implementer: `id 2139`, `Private` project — harmless residue,
   won't collide with a uniquified generated name.

## Concrete Handles (discovered during exploration)

| Element | Recommended Locator | Fallback |
|---|---|---|
| Remote MCP type-selector card | `[data-testid="toolkit-type-card-mcp"]` (existing) | none |
| Toolkit Name input | `[data-testid="toolkit-form-name-input"]` (existing) | none |
| Url input | `[data-testid="toolkit-field-url-input"]` (existing) | none |
| Save button | `[data-testid="toolkit-form-save-button"]` (existing) | none |
| "Load Tools" button | `[data-testid="toolkit-load-tools-button"]` (existing — added at ELITEA-1933, confirmed live and already wired into `automation/pages/mcp_form_page.py` as `load_tools_button`) | none needed |
| Connection-status indicator (shows "Not Connected"/"Connected!") | **RESOLVED (2026-08-02, this PR):** `toolkit-connection-status` added via `add-data-testid` on `McpAuthStatus.jsx` (the wrapping `Typography`), same element identified during analysis — text remains the observable per `.agents/testing.md` § Locator policy. Live on `automation/testids` (EliteaUI@a467c0ac); **not yet on `main`** — awaiting human cherry-pick, tracked in the PR's closure record. Wired as `McpFormPage.connection_status` (`LocatorDescriptor(testid="toolkit-connection-status")`). | n/a — resolved, no fallback needed |
| Error toast (DNS-failure message) | **RESOLVED (2026-08-02, this PR):** confirmed live to reuse the existing app-wide `toast-message` testid (`Toast.jsx`, same shared component as `artifacts_page.py`/`skills_list_page.py`/`skill_detail_page.py`) — already on `main`, no new testid needed. Wired as `McpFormPage.sync_error_toast_message` (`LocatorDescriptor(testid="toast-message")`). | n/a — resolved, no fallback needed |

## Network Behavior

- `POST /api/v2/elitea_core/tools/prompt_lib/${PROJECT_ID}` — fires on Save
  click; `201 Created`.
- `GET /api/v2/elitea_core/tool/prompt_lib/${PROJECT_ID}/{id}?` — fires on
  detail-page load; `200`.
- `POST /api/v2/elitea_core/mcp_sync_tools/prompt_lib/${PROJECT_ID}?await_response=true`
  — fires on Load Tools click; **`200 OK`** (NOT an error status — the DNS
  failure is reported IN the response body, not via HTTP status). Confirmed
  live response body this session:
  ```json
  {"result": {"success": false, "error": "Failed to sync MCP tools: DNS resolution failed. Please check the server hostname in the URL.", "server_url": "https://nonexistent.invalid/mcp"}}
  ```
  This is the exact source of the toast text — the frontend surfaces
  `result.error` verbatim.

## Known Defects Found During Exploration

**No defect found.** All 8 AFS steps completed against the live local
environment; the invalid-URL Load Tools flow behaves exactly per the case's
own expected result, including an EXACT string match on the DNS-failure
message (case text and live product both read: `"Failed to sync MCP tools:
DNS resolution failed. Please check the server hostname in the URL."`).

Two testid gaps were found (connection-status indicator, error toast) — see
Concrete Handles; these were `add-data-testid` work items, not product defects,
per this project's testid-only locator policy. **Both resolved during
implementation of this same PR** (2026-08-02) — see Concrete Handles for the
final testids and provenance.

## Blocked Steps

None. All case steps executed to completion against the live local
environment.

## Automation Hints

- Framework: Playwright + pytest, testid-only `LocatorDescriptor`.
- **Reuse `automation/pages/mcp_form_page.py`** (`McpFormPage`) — this case
  needs zero new page-object methods beyond what ELITEA-1933 already added
  (`navigate_to_create`, `select_remote_mcp_type`, `fill_name`, `fill_url`,
  `save_and_wait_for_created`, `click_load_tools`). Two NEW methods were
  added (both testid-backed, per the resolved Concrete Handles rows above):
  - `get_connection_status_text()` — reads `LocatorDescriptor(testid=
    "toolkit-connection-status")`.
  - `wait_for_sync_error_toast()` — waits for `LocatorDescriptor(testid=
    "toast-message")` to become visible IMMEDIATELY after
    `click_load_tools()`'s network wait resolves (don't insert a separate
    step in between — the toast auto-dismisses fast), returns its text.
- **`click_load_tools()` already waits on the `mcp_sync_tools` response and
  returns its parsed JSON body** (existing method, ELITEA-1933) — this case
  can assert `response["result"]["success"] is False` and
  `response["result"]["error"] == EXPECTED_ERROR_MESSAGE` directly from that
  return value, in addition to (not instead of) the toast assertion — both
  are real signals worth locking down (API contract + UI surface).
- Wait strategy: the SAME `expect_response` pattern `click_load_tools()`
  already uses is sufficient — no new wait primitive needed. The toast
  assertion must run immediately in the same synchronous chain (`response =
  form.click_load_tools(...)` then immediately check the toast), since
  by the time a *separate* pytest step/assertion block runs, the toast may
  already be gone (confirmed live: gone within ~3s).
