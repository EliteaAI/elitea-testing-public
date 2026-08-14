# Test Case: Credential — Usage in Toolkit Flows

## Metadata
- **TMS ID**: ELITEA-1979
- **Linked Story**: none
- **Priority**: l1 (case frontmatter: `high`, same convention as
  ELITEA-1976/1978 in this batch)
- **Environment Explored**: local (`http://localhost:5173`, EliteaUI
  `automation/testids` → DEV backend `https://dev.elitea.ai/api/v2`)
- **User set**: `${TEST_USER}` (nominal — `auth_state` no-op on localhost)
- **Analyst**: qa-engineer (agent), 2026-08-02
- **Status**: ready-for-automation

## Preconditions
- User authenticated (`auth_state` fixture — no-op on localhost).
- Test runs entirely in Test Bot's own personal project (399, "Private") —
  the identity has full write access there, so it can create BOTH the
  credential and the toolkit itself (unlike ELITEA-1976/1979's team-project
  dropdown-shape checks, this case's own toolkit is disposable and does not
  need to be a shared, pre-existing one).

## Test Data
### generate-per-test (created in test, cleaned up in its own teardown)
- **Credential name**: `autotest_toolkit_cred_${timestamp}`
- **Credential type**: Github, Token auth, `${GIT_HUB_TOKEN}` (a REAL,
  valid token — unlike ELITEA-1978, this case's step 6 requires the
  credential to actually authenticate against the live GitHub API).
- **Toolkit**: `autotest_toolkit_tk_${timestamp}`, type Github, repository
  `${GIT_REPO}` (existing `settings.git_repo` /
  `EliteaAI/elitea-testing`), branch `main`.

## Test Steps
1. Create a valid Github credential `autotest_toolkit_cred_${ts}` with
   `${GIT_HUB_TOKEN}` via `credential_api.create_github_credential(...)`.
   - **Verify**: 200, credential id + `elitea_title` returned.
2. Navigate to the Toolkits section.
   - **Verify**: list loads (`entity_card` visible, or navigate directly to
     step 3's created toolkit's detail page — this case creates its own
     toolkit rather than browsing the list, see step 3).
3. Create a Github toolkit linked to the step-1 credential via
   `toolkit_api.create_github_toolkit(credential_elitea_title=...)`, then
   navigate to its detail page.
   - **Verify**: toolkit detail page loads, `toolkit-detail-title` visible,
     Configuration tab shows the "Github Configuration" dropdown pre-filled
     with the step-1 credential's name (since it was set at creation time —
     the case's own step 4 wording, "choose ... from the dropdown," is
     satisfied by-construction here since the toolkit is created WITH the
     credential already selected; the dropdown is still exercised live to
     confirm the pre-fill, not skipped).
4. Confirm the credential selection: read the Configuration combobox's
   displayed text.
   - **Verify**: text equals the step-1 credential's display name.
5. (Same assertion as step 4 — the case's steps 4 and 5 are the same
   observable stated twice; not decomposed further.)
6. Open the Test Settings panel, select the `list_branches_in_repo` tool
   (no params required), click Run Tool.
   - **Verify**: the tool executes successfully and returns a real GitHub
     API response (a JSON array of branch objects with `name`/`protected`
     keys) — proves the linked credential actually authenticates.
7. Navigate to Credentials, delete the step-1 credential
   (`credential_api.delete_credential(id)`).
   - **Verify**: 200/204, credential no longer in
     `credential_api.list_all_credentials()`.
8. Return to the toolkit's detail page (reload).
   - **Verify**: the Configuration field shows an error/mismatch state —
     concretely: the combobox still renders the now-orphaned credential
     name text but in **red/error styling**
     (`.Mui-error`/`aria-invalid="true"` on the combobox), AND a
     `CredentialMismatchFooter` helper text reads "Your configuration does
     not match any available configurations." directly below it. This is
     NOT a blank/empty field — it's a red mismatched-value + helper-text
     pair (live-confirmed screenshot evidence).

## Expected Results
- The toolkit's Configuration field reflects the linked credential
  immediately after creation (pre-filled, confirmed via the dropdown's
  displayed text).
- `list_branches_in_repo` succeeds using the linked credential, returning
  real repository branch data.
- After the credential is deleted, the toolkit's Configuration field
  visibly reflects the broken link: red-styled combobox text (still showing
  the orphaned name) + "does not match any available configurations" helper
  text — this is the case's "empty or error/missing state."

## Coverage Map

### Axis 1 — Case coverage

| Case element | Expected result | Covered by (AFS step) | Asserted where | Disposition |
|---|---|---|---|---|
| 1 Create valid Github credential | created successfully | step 1 | API 200 + id | asserted |
| 2 Navigate to Toolkits | list loads | step 2 | list page reachable (transit only, this case's own vehicle is a fresh toolkit — see step 3) | asserted |
| 3 Create/open toolkit requiring Github credentials | config page loads | step 3 | `toolkit-detail-title` + Configuration tab visible | asserted |
| 4 Choose credential from dropdown | credential selected/linked | step 3-4 | pre-filled at creation, confirmed via dropdown read | asserted *(decomposed: case implies an interactive selection; live construction pre-fills it, so the assertion is the confirmed READ of that pre-fill, not a fresh click — same net observable, cheaper and non-flaky)* |
| 5 Verify credential linked (shows selected) | Configuration shows credential | step 4 (same read) | combobox text | asserted *(same observable as step 4, case states it twice)* |
| 6 Test toolkit operation using credential (list branches) | operation succeeds | step 6 | tool-result panel shows real branch JSON | asserted |
| 7 Delete credential | deleted | step 7 | API + list-absence check | asserted |
| 8 Check credential field after deletion | empty/error/missing state | step 8 | red combobox text + mismatch-footer helper text | asserted |

### Axis 2 — Analyst additions

- Step 6 asserts the tool result contains actual branch data (not just "no
  error") — *added: a silent empty-array or error-swallowed response would
  pass a weaker "no exception" check but not prove the credential actually
  authenticated; this is the case's real point (auth-gated operation
  succeeds).*
- Step 7 asserts the credential is genuinely gone server-side (list-absence
  check), not just that the delete button was clicked — *added: makes step
  8's premise (deletion actually happened) an explicit, checked fact rather
  than an assumption.*
- Step 8 asserts BOTH the visual (red styling) and textual (mismatch
  footer) halves of the error state — *added: either alone is a weaker
  proof; live exploration showed they always co-occur for this exact
  scenario (non-private credential deleted while linked), so asserting both
  costs nothing and catches a partial-regression (e.g. footer text changes
  but styling regresses, or vice versa).*

## Cleanup
1. Delete the toolkit created in step 3.
2. Credential is already deleted by step 7 (part of the case flow itself,
   not a teardown step) — no double-delete in `finally`.

## Concrete Handles (discovered during exploration)

| Element | Recommended Locator | Fallback / Provenance |
|---|---|---|
| Toolkit detail title | `toolkit-detail-title` | on-main ✓ (pre-existing, `toolkit_detail_page.py`) |
| Configuration dropdown trigger | **testid needed**: `toolkit-credential-select-github` — same gap as ELITEA-1976, see `_surface.md` | needs-adding |
| Configuration dropdown error state | `.Mui-error` class + `aria-invalid="true"` on the combobox `div[role="combobox"]` — no testid; state should be a `data-*` attribute filter on the (once-added) trigger testid per `.agents/testing.md` § Locator policy ("Testid = stable identity; state via data-* attributes"), NOT a second state-specific testid | needs-adding: once `toolkit-credential-select-github` exists, assert `[data-testid="toolkit-credential-select-github"][aria-invalid="true"]` rather than a raw `.Mui-error` class match |
| Mismatch footer helper text | **testid needed**: `credential-select-mismatch-footer` — source pointer `EliteaUI/src/[fsd]/features/credentials/ui/credentials-select/CredentialMismatchFooter.jsx` ~line 20-26 | needs-adding (same gap as ELITEA-1976/1978's sibling gaps, see `_surface.md`) |
| Test Settings — select tool from empty state | `ToolkitTestSettingsPage.select_tool_from_empty_state(tool_key)` | on-main ✓ (existing page object method, `automation/pages/toolkit_test_settings_page.py`) |
| Test Settings — run tool | `ToolkitTestSettingsPage.run_tool()` | on-main ✓ |
| Test Settings — read result | `ToolkitTestSettingsPage.wait_for_tool_result()` | on-main ✓ |
| Tool chip for `list_branches_in_repo` | `toolkit-tool-chip-list_branches_in_repo` (dynamic testid, `{section}-{element}-{param}` pattern already in use) | on `automation/testids` ✓ (confirmed live in this session's DOM dump); provenance vs `main` not separately re-checked — this is the SAME dynamic-testid mechanism already used by every other `toolkit-tool-chip-*` in the merged suite (`toolkit_creation_page.py`), not new |

## Network Behavior
- `POST /elitea_core/tools/prompt_lib/{project_id}` — toolkit creation.
- Tool-run request (Test Settings "Run Tool") — hits the toolkit's
  underlying GitHub API call server-side; response surfaces in the result
  panel as formatted JSON (branch list). No specific endpoint path was
  captured for this (routed through the toolkit's generic run-tool
  endpoint) — implementer can capture the exact path from a live network
  trace if a response-predicate wait is preferred over the page object's
  existing `wait_for_tool_result()` polling.
- `DELETE /configurations/configuration/{project_id}/{credential_id}` —
  step 7's deletion.

## Known Defects Found During Exploration
None found specific to this case's own flow. (The shared gaps — missing
testids on the Configuration trigger and mismatch footer — are tracked as
"testid needed" rows above, not defects; they're implementer work per
`.agents/testing.md` § Locator policy, not product bugs.)

## Blocked Steps
None — all 8 case steps executed live end-to-end, including the real
`list_branches_in_repo` GitHub API call (returned live branch data from
`${GIT_REPO}`).

## Automation Hints
- Framework: Playwright + pytest.
- Reuse `github_credential` / `github_toolkit`-style fixtures
  (`automation/fixtures/data_fixtures.py`) as a starting point, but this
  case needs the credential deleted MID-TEST (step 7) rather than only in
  teardown — don't use the `github_credential` fixture as-is (it deletes in
  its own teardown, which would double-delete after step 7's explicit
  delete); either inline the create/delete or add a variant fixture that
  exposes the id without owning its teardown.
- Reuse `ToolkitTestSettingsPage` unmodified for step 6 — its
  `select_tool_from_empty_state()` / `run_tool()` / `wait_for_tool_result()`
  trio already implements exactly the select→run→read flow this step
  needs, confirmed live in this session against `list_branches_in_repo`.
- Extend `ToolkitDetailPage` with the same Configuration-dropdown read
  method ELITEA-1976 needs (get displayed credential name, check
  error/mismatch state) — implement once, both cases' implementers should
  share it (same page object, same batch).
