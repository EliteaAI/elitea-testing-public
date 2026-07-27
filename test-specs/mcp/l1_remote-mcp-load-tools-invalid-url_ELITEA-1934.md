# Test Case: Remote MCP — Load Tools from Invalid URL

## Metadata
- **TMS ID**: ELITEA-1934
- **Linked Story**: none
- **Priority**: l1 — **CONTRADICTORY METADATA, reported not resolved**: the
  source frontmatter says `priority: high`, but the case body's own header
  line says "**Priority:** medium". Filed as-is under `l1` (mapping the
  structured frontmatter field, per the `l<pri>` ↔ `pytest.mark.p<N>`
  convention confirmed against `test_mcp_load_tools_discovery.py` /
  `test_mcp_create_remote.py` / `test_mcp_delete_remote.py`'s own
  `pytestmark`), but the implementer/lead should reconcile which is correct
  (contradictory-metadata per `.agents/test-automation.yaml` § intake — report,
  don't guess).
- **Environment Explored**: local (`http://localhost:5173`, `EliteaAI/EliteaUI`
  @ `automation/testids`, DEV backend)
- **User set**: `${TEST_USER}` (localhost: no login needed — `VITE_DEV_TOKEN`
  auto-auths; confirmed working even on a brand-new, never-before-used Chrome
  profile, see Automation Hints)
- **Analyst**: qa-engineer (agent), session 2026-07-24
- **Status**: ready-for-automation

## Preconditions
- User is authenticated (on localhost this is automatic via `VITE_DEV_TOKEN`).
- Project context is set (sidebar shows `Project: Private`).
- No special test data / credentials required — the case's own fixture (an
  unresolvable hostname) is self-contained and needs no external service.

## Test Data

### generate-per-test (in test setup, cleaned up in its own teardown)
- Toolkit Name: case text says `autotest_tools_invalid_url` (27 chars) — this
  needs a per-run-unique suffix for parallel-safety, but the Toolkit Name
  input silently **truncates at 32 chars** (`MAX_NAME_LENGTH`,
  `EliteaUI/src/common/constants.js`, confirmed quirk from
  `test_mcp_load_tools_discovery.py`'s own comment) so appending a full
  `uuid4().hex[:8]` would overflow it. Recommend a shorter prefix, e.g.
  `f"autotest_inv_url_{uuid.uuid4().hex[:8]}"` (25 chars) — same pattern
  `test_mcp_load_tools_discovery.py` already uses (`autotest_tools_disc_{...}`).
- URL: `https://nonexistent.invalid/mcp` (exactly as specified by the case —
  the `.invalid` TLD is IANA-reserved specifically for this purpose, so DNS
  resolution failure is deterministic and requires no network mocking).

### reuse-existing
- `${TEST_USER}` — only needed on deployed envs; localhost skips login.

## Test Steps

1. Navigate to `${BASE_URL}/mcps/create`, click the Remote MCP type card
   (`[data-testid="toolkit-type-card-mcp"]`).
   - **Verify**: URL becomes `${BASE_URL}/mcps/create/mcp`; Toolkit Name / Url
     fields visible.
2. Fill Toolkit Name (`[data-testid="toolkit-form-name-input"]`) with the
   generated name.
   - **Verify**: field displays the typed value.
3. Fill Url (`[data-testid="toolkit-field-url-input"]`) with
   `https://nonexistent.invalid/mcp`.
   - **Verify**: field displays the typed value exactly (confirmed live — no
     client-side URL-format validation rejects it); Save button becomes
     enabled.
4. Click Save (`[data-testid="toolkit-form-save-button"]`).
   - **Verify**: `POST /api/v2/elitea_core/tools/prompt_lib/${PROJECT_ID}`
     returns `201 Created`; page navigates to `${BASE_URL}/mcps/all/{id}`;
     detail page title (`[data-testid="toolkit-detail-title"]`) shows the
     toolkit name; the Url field on the detail page still shows
     `https://nonexistent.invalid/mcp` unchanged (confirmed live — the
     invalid URL round-trips through save with no server-side rejection
     either; validation only happens at Load-Tools/sync time, not save time).
5. Click "Load Tools" (`[data-testid="toolkit-load-tools-button"]`).
   - **Verify**: button label flips to "Loading..." while in flight (confirmed
     live); `POST /api/v2/elitea_core/mcp_sync_tools/prompt_lib/${PROJECT_ID}
     ?await_response=true` resolves **`200`** (NOT a 4xx/5xx — the failure is
     communicated inside a 200 body, see § Network Behavior) with
     `result.success === false` and `result.error === "Failed to sync MCP
     tools: DNS resolution failed. Please check the server hostname in the
     URL."`; an error toast renders this exact string via the existing shared
     `[data-testid="toast-message"]` handle (confirmed live, char-for-char
     match against the case's expected message — see § Concrete Handles, this
     is a genuinely useful correction: the covering ELITEA-1933 AFS never
     looked for this testid on its own success toast and incorrectly implied
     toasts have no stable handle).
6. Verify the connection status indicator.
   - **Verify**: the status widget (globe icon + text, next to the Form/Raw
     Json toggle) shows **"Not Connected"** with a **"Login"** button
     alongside it — i.e. it never flips to "Connected!"/"Logout" (confirmed
     live via DOM query: only "Not Connected"/"Login" text present, twice
     across two independent Load-Tools attempts in this session — see
     Automation Hints for determinism note). **No testid exists anywhere in
     this widget's DOM tree** (confirmed via a 6-level ancestor walk from the
     "Not Connected" `<span>` — flagged as implementer work, see § Concrete
     Handles / Known Defects).

## Expected Results
- The Remote MCP toolkit is created successfully despite the URL being
  unreachable (save itself never validates connectivity).
- Clicking "Load Tools" against the invalid URL produces the exact error
  toast text specified by the case, delivered via the existing
  `toast-message` shared handle.
- The connection status stays "Not Connected" (with a "Login" button, never
  "Connected!"/"Logout") after the failed attempt.
- The Tools section keeps showing its pre-existing empty-state message (no
  phantom/partial tool list renders on failure).
- The "Load Tools" button itself is not left stuck in a "Loading..." state —
  it reverts to "Load Tools" once the (failed) sync resolves.

## Coverage Map

### Axis 1 — Case coverage

| Case element | Expected result | Covered by (AFS step) | Asserted where | Disposition |
|---|---|---|---|---|
| Preconditions: user logged in | session active | steps 1–2 | confirmed via successful navigation + form load | asserted |
| 1 Create Remote MCP named "autotest_tools_invalid_url" | form loads | step 1 | step 1 | asserted |
| 2 Fill URL with invalid URL | field accepts/displays it | step 2 | step 2 (via step 3 in this AFS's own numbering — case step 2 = AFS step 3) | asserted |
| 3 Save the MCP | detail page loads | step 3 | AFS step 4: 201 + navigation + title | asserted |
| 4 Click "Load Tools" | tool loading attempted | step 4 | AFS step 5: click + "Loading..." + network 200 | asserted |
| 5 Verify toast error message exact text | error toast w/ exact message | step 5 | AFS step 5: `[data-testid="toast-message"]` text confirmed char-for-char live | asserted |
| 6 Verify connection status shows "Not Connected" | status indicator shows it | step 6 | AFS step 6: DOM query, confirmed twice (2/2) | asserted |
| Expected Final State: error toast shown + status "Not Connected" | both hold together | steps 5–6 | steps 5–6 | asserted |
| Pass/Fail: all steps complete without errors; toast+status correct | | all steps | all steps | asserted — clean pass, no product defect; two testid-handle findings routed as implementer work (one already exists and just needed correct discovery; one is a genuine gap), not defects |

### Axis 2 — Analyst additions

- Verified the **HTTP-level contract**, not just the rendered toast: `mcp_sync_tools`
  returns `200` (never 4xx/5xx) with `{"result": {"success": false, "error": "...",
  "server_url": "..."}}` — confirmed via a direct authenticated POST replicating the
  exact browser request (see § Network Behavior). *Added because this is the actual
  signal the UI's `useGetRemoteMcpTools` hook branches on
  (`result?.success === false && result?.error` → `toastError(errorMessage)`,
  `EliteaUI/src/[fsd]/features/mcp/lib/hooks/useGetRemoteMcpTools.hooks.js:122-132`)
  — asserting the response body directly (not only the rendered toast text) catches a
  regression in the contract itself, independent of any future toast-copy change.*
- Verified the **"Load Tools" button reverts to its idle label** ("Load Tools", not
  stuck on "Loading...") after the failed sync resolves — *added: guards against a
  regression that leaves the button permanently disabled/stuck on failure, which the
  case's literal steps don't call out but which would silently block every retry.*
- Verified the **Tools section still shows its pre-existing empty-state text**
  (`[data-testid="toolkit-tools-empty-state"]`) after the failed Load Tools attempt —
  *added: guards against a regression that renders a phantom/partial tool list on a
  sync failure instead of leaving the empty state intact.*
- Verified **determinism across two independent attempts** in the same session:
  clicked Load Tools twice against the same invalid-URL toolkit; both times produced
  the identical toast text and both times left "Not Connected"/"Login" unchanged
  (2/2) — *added: confirms this is a deterministic server-side DNS-resolution
  failure, not a flaky/racy assertion, so the implementer can assert without retry
  logic.*
- Checked console messages both times — only the two already-tracked, unrelated
  pre-existing warnings fired (see § Known Defects); no new console errors from this
  flow itself.

## Cleanup

1. This case creates a persistent MCP toolkit (server-side `tool` entity via
   `POST /api/v2/elitea_core/tools/prompt_lib/${PROJECT_ID}` → `201 Created`).
   Delete it in test teardown via the existing `ToolkitAPI.delete_toolkit(toolkit_id)`
   client (`automation/api/client.py`), mirroring the exact pattern already used by
   `test_mcp_load_tools_discovery.py`.
2. **Two residue toolkits were left on the local DEV backend by this analysis
   session** (analyst has no cleanup/commit authority — same precedent as the
   ELITEA-1933/ELITEA-1922 AFS's own Cleanup sections):
   - id `1736`, name `autotest_inv_url_qa1934`, url `https://nonexistent.invalid/mcp`
     (created during an initial exploration attempt against a Chrome instance that
     turned out **not** to be isolated — see § Automation Hints tooling note — before
     the analyst switched to a genuinely isolated browser and re-ran the case cleanly)
   - id `1737`, name `autotest_inv_url_qa1934b`, url `https://nonexistent.invalid/mcp`
     (the clean re-run's own toolkit)
   Flag to the implementer: delete both via
   `DELETE ${ELITEA_API_BASE}/elitea_core/tool/prompt_lib/${ELITEA_PROJECT_ID}/1736`
   and `.../1737` before this case's own fixture data starts accumulating, or treat
   as harmless residue (`Private`-project-scoped, generated names won't collide with
   the implementer's own uuid-suffixed names).

## Concrete Handles (discovered during exploration)

| Element | Recommended Locator | Fallback |
|---|---|---|
| Remote MCP type-selector card | `[data-testid="toolkit-type-card-mcp"]` (existing) | none |
| Toolkit Name input | `[data-testid="toolkit-form-name-input"]` (existing) | none |
| Url input | `[data-testid="toolkit-field-url-input"]` (existing) | none |
| Save button (create form) | `[data-testid="toolkit-form-save-button"]` (existing) | none |
| Detail page title | `[data-testid="toolkit-detail-title"]` (existing) | none |
| "Load Tools" button | `[data-testid="toolkit-load-tools-button"]` (existing — added by the ELITEA-1933 implementer, already wired as `McpFormPage.load_tools_button`; `click_load_tools(project_id)` is directly reusable for THIS case too, see Automation Hints) | none needed |
| Tools section empty-state text | `[data-testid="toolkit-tools-empty-state"]` (existing) | none |
| **Error toast message** | `[data-testid="toast-message"]` — **existing, SHARED handle** (`EliteaUI/src/components/Toast.jsx:66`, confirmed live: exact text `"Failed to sync MCP tools: DNS resolution failed. Please check the server hostname in the URL."`). This exact testid is already used by 3 other page objects (`artifacts_page.py:315` `success_toast_message`, `skills_list_page.py:59` `import_success_toast_message`, `skill_detail_page.py:96` `version_toast_message`) — each declares its OWN named `LocatorDescriptor(testid="toast-message", ...)` field per that established per-page-object convention; `McpFormPage` should add its own (e.g. `sync_error_toast_message`) rather than reusing another page object's field. **Correction to the ELITEA-1933 AFS**: that AFS's own Concrete Handles table never looked for this testid on its (success) toast and implied toasts have no stable handle — they do, this session found it. | none needed |
| **Connection status widget** (globe icon + "Not Connected"/"Connected!" text + Login/Logout button) | **NO TESTID ANYWHERE** — confirmed via a 6-level DOM ancestor walk from the status `<span>`, all `data-testid: null`. Source: `EliteaUI/src/[fsd]/features/mcp/ui/McpAuthStatus.jsx` (lines 128–152) — an ordinary app component (NOT a literally-shared React instance across features despite structurally-similar siblings in `openapi`/`sharepoint` feature folders — each is an independently-implemented, feature-scoped copy, confirmed by reading all three files, so a feature-scoped testid here does not violate the shared-component naming rule). **Flag to `add-data-testid`**: recommend `toolkit-connection-status` on the outer `Box` (line 128) plus a `data-connected="true"/"false"` attribute mirroring `hasLoggedInToMcp` (state-via-data-attribute, per `.agents/testing.md` § Locator policy — same pattern as the existing `data-selected` on tool chips), and `toolkit-connection-auth-button` on the Login/Logout `Button.BaseBtn` (line 143). This is genuinely new implementer work — the ELITEA-1933 AFS mentioned this same widget only in passing ("no testid in scope for this case") since that case never needed to assert its text; THIS case's own step 6 does. | `page.get_by_text("Not Connected", exact=True)` / `page.get_by_text("Login", exact=True)` — page-level (no testid-bearing parent exists to scope within), interim only per stop+flag discipline; this is ordinary `EliteaUI/src` app JSX, NOT a sanctioned #579 exception, so the correct implementer action is to add the testid, not to ship this fallback long-term. |

## Network Behavior

- `POST /api/v2/elitea_core/tools/prompt_lib/${PROJECT_ID}` — fires on Save
  click; `201 Created`; response `id` needed for the detail-page URL + teardown.
- `POST /api/v2/elitea_core/mcp_sync_tools/prompt_lib/${PROJECT_ID}
  ?await_response=true` — fires on Load Tools click; **`200`** in BOTH the
  success (ELITEA-1933) and this case's failure path — the failure is
  communicated inside the 200 body, not via HTTP status. Confirmed live via a
  direct authenticated replication of the exact request:
  ```json
  {"result": {"success": false, "error": "Failed to sync MCP tools: DNS resolution failed. Please check the server hostname in the URL.", "server_url": "https://nonexistent.invalid/mcp"}}
  ```
  This means `McpFormPage.click_load_tools(project_id)` — ELITEA-1933's existing
  method, which waits on exactly this response and status — is **directly reusable
  as-is** for this case; only the assertions on the returned dict differ
  (`result["success"] is False` / `result["error"] == EXPECTED_MESSAGE` instead of a
  populated tool list).

## Known Defects Found During Exploration

**No product defect found.** The live product's behavior matches the case's
expected result exactly, character-for-character on the error message. Two
testid-handle findings, both implementer work (not defects):

- The error toast's `[data-testid="toast-message"]` handle already exists and
  is directly usable — no `add-data-testid` work needed for it (see Concrete
  Handles correction above).
- The connection-status widget (`McpAuthStatus.jsx`) has zero testids and
  needs `add-data-testid` work — genuinely new scope, not previously in any
  case's touched-element set (ELITEA-1933 never asserted this widget).
- **[MINOR] Pre-existing React dev-mode console warning on `/mcps/create`** —
  already tracked as `EliteaAI/elitea-testing-public#291` (`key`-prop
  warning), reproduced again this session (2× — once per navigation to the
  create form), no new issue filed (dedup, same as ELITEA-1933's session).
  No functional impact on this case.
- The already-tracked MUI Tabs console warning (`#549`, documented in the
  ELITEA-1933 AFS as firing on `/mcps/all/{id}`) did **not** reproduce this
  session — noted for completeness, not a regression (intermittent by nature
  per its own prior documentation).

## Blocked Steps

None. All case steps were executed to completion against the live local
environment.

## Automation Hints

- Framework: Playwright + pytest, testid-only `LocatorDescriptor`.
- **Reuse `automation/pages/mcp_form_page.py` (`McpFormPage`) entirely** —
  `navigate_to_create()`, `select_remote_mcp_type()`, `fill_name()`,
  `fill_url()`, `save_and_wait_for_created()`, `get_tools_empty_state_text()`,
  and critically **`click_load_tools(project_id)` as-is** (see § Network
  Behavior — same endpoint/status/wait mechanics whether the sync succeeds or
  fails; only the returned dict's `result["success"]`/`result["error"]`
  differ). No new click/wait method is needed for the Load Tools interaction
  itself.
- New methods/fields needed on `McpFormPage`:
  - `sync_error_toast_message = LocatorDescriptor(testid="toast-message", ...)`
    — a NEW named field on this page object (the shared testid already
    exists and is used by 3 other page objects under their own field names;
    follow that convention, don't cross-import another page object's field).
  - Once `add-data-testid` lands `toolkit-connection-status` /
    `toolkit-connection-auth-button`: `get_connection_status_text()` /
    `is_mcp_connected()` (reading the `data-connected` attribute, per the
    established `is_tool_chip_selected()`/`data-selected` pattern already in
    this same file).
- **Toast timing**: error-severity toasts auto-hide after **10000ms**
  (`TOAST_DURATION_DEFAULTS.error`, `EliteaUI/src/common/constants.js`) — a
  full 10s window, comfortably longer than the success toast's 3000ms that
  ELITEA-1933 had to warn about racing. Asserting the toast text immediately
  after `click_load_tools()` returns (which itself already waited on the
  network response) carries no realistic race risk here.
- **Toolkit Name truncation**: keep the generated name under 32 chars (see
  § Test Data) — same `MAX_NAME_LENGTH` quirk documented in
  `test_mcp_load_tools_discovery.py`'s own comment
  (`.agents/memory/test-automation-engineer/mcp_toolkit_create_form_implementer_quirks.md`).
- **Tooling note (analyst-tooling only, not a product/test-framework
  concern):** this session's assigned isolated browser lane (CDP port 9223,
  per the batch's browser-lane assignment) turned out to have a **pre-existing
  Chrome instance already mid-navigation on an unrelated page** when this
  analysis began, and that instance was clobbered by what appears to be a
  concurrent process partway through this session's own exploration (a
  `page-info` check unexpectedly showed a `Pipelines: New Pipeline` page
  mid-flow, on the SAME target/frame id, with no navigation issued by this
  session). The analyst abandoned that instance and spun up a genuinely
  isolated Chrome (`--remote-debugging-port=9323`, a fresh scratch
  `--user-data-dir`) to complete the case cleanly — all findings in this AFS
  are from that clean, verified-isolated run (single target confirmed via
  `list-targets` before and after every interaction). **Flag to the
  orchestrator**: the lane-1 port (9223) was not actually exclusive at the
  start of this session; other analysts hitting the same symptom (an
  unexplained mid-session navigation) should suspect lane contamination, not
  a product bug, and should re-verify on a freshly-launched, uniquely-ported/
  profiled instance before trusting any observation.
