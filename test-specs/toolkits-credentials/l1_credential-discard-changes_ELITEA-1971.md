# Test Case: Credential — Discard Changes

## Metadata
- **TMS ID**: ELITEA-1971
- **Linked Story**: none
- **Priority**: l1 (case frontmatter: `critical`; case body table says `medium` —
  **pre-existing inconsistency in the source case**, not introduced by this
  AFS. Per dispatch instruction, `critical` from the frontmatter is treated as
  authoritative since the tracker issue for this case also states
  "Priority: critical". Recommend the TMS case body table be corrected
  upstream to remove the contradiction — not filed as a defect since it's a
  case-authoring nit, not a product bug.)
- **Environment Explored**: local (`http://localhost:5173`, EliteaUI
  `automation/testids` branch → DEV backend, project `Private` / `${ELITEA_PROJECT_ID}`=399)
- **User set**: `${TEST_USER}` (localhost `auth_state` fixture skips login via
  `VITE_DEV_TOKEN`; credential itself was created via API using
  `CredentialAPI.create_github_credential()`, authenticated with
  `${GIT_HUB_TOKEN}` as GitHub toolkit test data per `.agents/profile.md` §
  Roles & sample users — not a live GitHub token validity check, this case
  never exercises "Test connection")
- **Analyst**: qa-engineer (Sage), analyst slot
- **Status**: ready-for-automation
- **Case-gate note**: case frontmatter carries `status: draft`,
  `execution_type: manual`. `.agents/testing.md` has no documented `TMS
  case-gate` exclusion list for this project, so per the skill's default
  ("if absent, default to fetching all and flag the gap") this run proceeded
  and executed the case end-to-end. Flagging the gap here for scout to fill
  `.agents/testing.md` § TMS case-gate.

## Preconditions
- User is logged in to Elitea (on localhost, `auth_state` fixture skips login).
- A project is selected/accessible (`Private`, id `399` in this run).
- A credential of type Github named `autotest_discard_cred` exists — this AFS
  creates it via `CredentialAPI.create_github_credential()` (API-level setup,
  not a UI step; see Test Data). The case's own Step 1 ("Create a credential
  … of type Github") is satisfied by this API call rather than by walking the
  Credentials-create UI form — since this case's actual subject under test is
  the **Discard** flow on an existing credential's detail page, not credential
  creation (which is covered by other cases in this feature family, e.g. the
  Toolkit/MCP credential-creation flows already automated elsewhere per
  memory `toolkit_mcp_create_form_quirks`).

## Test Data

### generate-per-test (created in test setup, cleaned up in its own teardown)
- GitHub credential via `CredentialAPI.create_github_credential(display_name="autotest_discard_cred_<ts>", base_url="https://api.github.com", token=${GIT_HUB_TOKEN})`.
  Live-verified: returns `{"id": <int>, "uuid": "<uuid>", "label": "autotest_discard_cred", ...}`.
  Suffix the display name with a timestamp in the automated version — this
  exploration run used the literal case-data string `autotest_discard_cred`
  since the credential is deleted immediately after the run and no
  concurrent run collision is expected in this exploration, but the
  implementer should follow the project's existing per-test uniqueness
  convention (see `test_toolkit_indicators_for_credentials.py`'s
  `f"autotest_tk_cred_{ts}"[:32]` pattern) to avoid label collisions across
  parallel/retried CI runs.
- Changed Display Name value: `autotest_changed` (per case Test Data table).

No shared/reused fixture applies — the case's Discard assertion inherently
requires mutating a real, freshly-created credential record mid-test (an
unsaved-edit state cannot be asserted against a shared/reused credential
without risking cross-test interference on the same record).

## Test Steps

1. Create credential via API:
   `CredentialAPI.create_github_credential(display_name="autotest_discard_cred", base_url="https://api.github.com", token=${GIT_HUB_TOKEN})`.
   - **Verify**: response `200`-equivalent (`requests` raises on non-2xx via
     `_raise_for_status`), payload contains `"label": "autotest_discard_cred"`,
     `"type": "github"`, and both `"id"` (int, e.g. `1533` in this run) and
     `"uuid"` (e.g. `aaa6de0b-286d-4ec0-b78e-a93a1c9ca87e` in this run).
     **Capture the numeric `id`, not the `uuid`, for the navigation step below
     — see Known Defects #1.**

2. Navigate to the credential list (`${BASE_URL}/credentials/all`) and click
   the credential card matching the created Display Name (this is the real
   UI entry point a user follows — confirmed live via `browser_snapshot`; the
   card is a clickable `div` containing the display-name text, no
   `data-testid` — see Concrete Handles). This lands on
   `${BASE_URL}/credentials/all/{numeric_id}?viewMode=owner&name=autotest_discard_cred`
   (confirmed live — clicking the card correctly resolves the numeric `id`,
   NOT the `uuid`, into the URL param that the route calls `credential_uid`
   — naming mismatch, see Known Defects #1).
   - **Verify**: page loads (`tab` element selected shows the credential's
     Display Name as its accessible name — confirmed live,
     `tab "autotest_discard_cred" [selected]`), Display Name field
     (`data-testid="toolkit-field-label-input"`, confirmed live) shows
     `autotest_discard_cred`, **Save** button is `[disabled]`, **Discard**
     button is `[disabled]` (both confirmed live via snapshot immediately
     after page load — matches the case's implicit "no pending changes"
     starting state, not itself a numbered case step but useful as the
     baseline for Step 4's assertion).

3. Click into the Display Name field
   (`getByTestId("toolkit-field-label-input")`) and replace its value with
   `autotest_changed` (fill/clear+type — confirmed live via
   `page.getByTestId('toolkit-field-label-input').fill('autotest_changed')`).
   - **Verify**: the field's value is exactly `autotest_changed` (confirmed
     live via snapshot: `textbox "Display Name" [active]: autotest_changed`).
     **Side-observation** (Axis 2, not a case requirement): the disabled
     "ID *" field (`elitea_title`, live-computed) also updated to mirror
     `autotest_changed` — confirmed live, this is a derived/reactive field
     computed from the label while `elitea_title` is still auto-generated
     (i.e., before the user has ever manually edited the ID field
     separately); not itself asserted by this case but worth flagging for
     an implementer writing a broader credential-edit case.

4. Verify the Discard button becomes enabled.
   - **Verify**: `getByRole("button", { name: "Discard" })` is enabled
     (`disabled` attribute absent) — confirmed live via snapshot immediately
     after Step 3's fill (`button "Discard" [ref=...]` with no `[disabled]`
     marker, vs `button "Discard" [disabled]` in Step 2's baseline). **Save**
     also became enabled at the same time (not itself a numbered case step
     here but observed and consistent with Expected Final State's "no
     pending changes ⇒ Save disabled" contrapositive).

5. Click the **Discard** button
   (`getByRole("button", { name: "Discard" })`, scoped to the tab-bar
   controls, not the modal's own "Discard" — see Concrete Handles for
   disambiguation).
   - **Verify**: a `role="dialog"` opens (`Modal.BaseModal`, confirmed live)
     with heading `"Warning"` and body text
     `"Are you sure you want to discard changes?"` — confirmed live via
     snapshot, **exact match** to both the case's Step 5 expected text and
     the live source constant `WARNING_MESSAGES.DISCARD_CHANGES` in
     `EliteaUI/src/[fsd]/shared/lib/constants/modal.constants.js:38`. Dialog
     also exposes a "Close" (X) button and, in its footer, **Cancel** and
     **Discard** buttons (confirmed live).

6. Verify the confirmation modal is displayed with the expected message
   (already captured in Step 5's verification — case Step 6 is a
   duplicate/redundant assertion of the same observable as Step 5, not a
   distinct action; this AFS treats it as folded into Step 5 rather than a
   separate step, per Coverage Map disposition below).

7. Click the **Discard** button inside the confirmation modal
   (`getByRole("button", { name: "Discard" })` scoped to the dialog — this is
   a *different* element from the tab-bar's Discard button clicked in Step
   5, both share the accessible name "Discard"; see Concrete Handles for the
   disambiguation the implementer needs).
   - **Verify**: the modal closes (dialog no longer present in the
     accessibility tree — confirmed live via snapshot immediately after the
     click).

8. Verify Display Name reverts to `autotest_discard_cred`.
   - **Verify**: `getByTestId("toolkit-field-label-input")` value is exactly
     `autotest_discard_cred` (confirmed live via snapshot: `textbox
     "Display Name": autotest_discard_cred`, no `[active]` marker — field
     lost focus as part of the form reset). The "ID *" field also reverted
     to its original computed value
     `github_autotest_discard_cred_1784120706909` (confirmed live) —
     consistent with Step 3's side-observation, both fields are driven by
     the same Formik form state that `formik.resetForm()` restores on
     confirm (source: `CredentialTabBar.jsx`'s `onCancel`/`useEffect` on
     `wantToCancel`, calls `onClearCredentialDetails()` +
     `formik.resetForm()`).

9. Verify the Save button returns to disabled state.
   - **Verify**: `getByRole("button", { name: "Save" })` is `[disabled]`
     (confirmed live via snapshot: `generic "Save credential": button "Save"
     [disabled]`). **Discard** is also `[disabled]` again at the same time
     (Axis 2 addition — consistent with the Expected Final State's "no
     pending changes" wording, which logically implies both controls
     return to their baseline disabled state, not just Save).

**Side-channel check (all steps):** zero console errors or warnings across
the full flow (confirmed via `browser_console_messages` immediately after
Step 9 — `Total messages: 9 (Errors: 0, Warnings: 0)`).

## Expected Results
Matches the case's Pass criteria exactly, live-verified end-to-end: Discard
button enables on edit (Step 4), confirmation modal shows the exact expected
warning text (Step 5/6), confirming Discard reverts the Display Name field to
its original value (Step 8) and returns Save (and Discard) to the disabled
state (Step 9). No functional defect found in the Discard flow itself; one
navigation-URL naming/behavior observation is documented below (Known
Defects #1) but does not block or alter this case's own pass/fail outcome,
since the case's own entry point (click-through from the Credentials list)
resolves correctly.

## Coverage Map

### Axis 1 — Case coverage

| Case element | Expected result | Covered by (AFS step) | Asserted where | Disposition |
|---|---|---|---|---|
| Precondition: user logged in | — | AFS Preconditions | `auth_state` fixture (localhost dev token) | asserted |
| Precondition: project + Credentials section accessible | — | AFS Preconditions | project `399` selected, `/credentials/all` loads | asserted |
| 1 Create credential "autotest_discard_cred" of type Github | credential created successfully | step 1 | step 1: API response `id`/`uuid`/`label`/`type` fields | asserted *(via API, not UI create-form — see Preconditions note)* |
| 2 Open credential details page | page loads with original Display Name | step 2 | step 2: Display Name field shows `autotest_discard_cred`, Save/Discard disabled | asserted |
| 3 Change Display Name to "autotest_changed" | field shows "autotest_changed" | step 3 | step 3: field value snapshot | asserted |
| 4 Verify Discard becomes enabled | Discard active/clickable | step 4 | step 4: `disabled` attribute absent | asserted |
| 5 Click Discard | warning modal opens with expected message | step 5 | step 5: dialog + exact message text, source-confirmed constant | asserted |
| 6 Verify confirmation modal displayed with expected message | modal visible with message | step 5 (folded) | step 5's own assertion already covers this — case Step 6 restates Step 5's expected result rather than adding a new action | asserted *(decomposed/folded — case Steps 5 and 6 collapse to one AFS step since Step 6 has no distinct action, only a duplicate assertion of Step 5's outcome)* |
| 7 Click "Discard" in modal | modal closes, changes reverted | step 7 | step 7: dialog no longer in a11y tree | asserted |
| 8 Verify Display Name reverts | field shows original name | step 8 | step 8: field value snapshot == `autotest_discard_cred` | asserted |
| 9 Verify Save returns to disabled | Save inactive | step 9 | step 9: `[disabled]` on Save button | asserted |
| Expected Final State: Display Name reverted + Save disabled | — | steps 8–9 | steps 8 and 9 jointly | asserted |

### Axis 2 — Analyst additions

- step 2 documents the live Save/Discard **baseline disabled state**
  immediately after page load — *added: gives the implementer a concrete
  "before" snapshot to diff Step 4's "after" against, rather than asserting
  enabled/disabled in isolation.*
- step 3 documents that the disabled "ID *" (`elitea_title`) field mirrors
  the Display Name field's live value while unedited — *added: relevant
  context for anyone later writing a broader credential-edit case; not
  itself required by this case's Pass criteria.*
- step 4 documents that **Save** also becomes enabled alongside Discard —
  *added: the case only asks to verify Discard, but Save's parallel
  state change is the mechanism that makes Step 9's assertion meaningful
  (both return to disabled together, not independently).*
- step 5 documents the exact live warning message and its source constant
  (`modal.constants.js:38`) — *added: proves live text matches the case's
  literal expected string, not just "some warning shown," and gives the
  implementer a source-of-truth reference if the message ever needs to
  change.*
- step 9 documents that Discard also returns to disabled, not just Save —
  *added: consistent with "no pending changes," the case only names Save
  but the live behavior is symmetric.*
- "zero console errors/warnings across the full flow" — *added: side-channel
  check per this skill's standard discipline; not itself a case requirement,
  but confirms no silent JS error accompanies the discard/reset cycle.*

## Cleanup
1. Delete the credential created in Step 1 via
   `CredentialAPI.delete_credential(credential_id)` in test teardown
   (regardless of pass/fail) — confirmed live: `DELETE
   /configurations/configuration/{project_id}/{id}` returns success, credential
   no longer appears in `/credentials/all` list. This exploration run deleted
   credential `id=1533` after completing all 9 steps.
2. No other product state is created by this case — the credential is never
   actually saved with the changed name (that's the entire point of Discard),
   so no second credential record or orphaned data results from the edit
   itself.
3. No route interception, mocked network, or browser-context state needs
   explicit teardown beyond the normal per-test browser context lifecycle.

## Concrete Handles (discovered during exploration)

| Element | Recommended Locator | Fallback |
|---|---|---|
| Credentials list → credential card (entry point, `CredentialsList.jsx`) | **testid needed** — the clickable card `div` wrapping the display-name text has zero `data-testid` (confirmed live via snapshot: plain `generic [cursor=pointer]`). Request via `add-data-testid`, suggested name `credentials-list-card-{index}` or a stable `credentials-list-card` scoped by text | `page.get_by_text("autotest_discard_cred", exact=True)` scoped to the credentials list container — brittle: tied to the exact display name string, acceptable only because the display name is itself test-controlled data |
| Display Name field (`ToolBaseProperty.jsx`, `k === 'label'`) | `page.get_by_test_id("toolkit-field-label-input")` — **confirmed live, existing testid** (shared property-renderer pattern, matches memory note `toolkit_mcp_create_form_quirks`) | `page.get_by_role("textbox", { name: "Display Name" })` |
| ID field (disabled, `elitea_title`) | `page.get_by_test_id("toolkit-field-elitea_title-input")` (inferred from the same `ToolBaseProperty.jsx` naming pattern `toolkit-field-{k}-input`, `k="elitea_title"`; not independently re-confirmed live in this run beyond its `label`-mirroring value, since this case doesn't assert on it directly) | `page.get_by_role("textbox", { name: "ID *" })` |
| Save button (tab-bar, `CredentialTabBar.jsx`) | **testid needed** — plain MUI `Button` (`MuiButton variant="elitea"`), zero testid props. Suggested name: `credential-form-save-button` | `page.get_by_role("button", { name: "Save" })` scoped outside any dialog (disambiguates from any future in-dialog "Save", though none currently exists) |
| Discard button (tab-bar, `Button.DiscardButton` in `CredentialTabBar.jsx`) | **testid needed** — `BaseBtn` under `DiscardButton.jsx` receives no `data-testid`/`dataTestId` prop from the call site. Suggested name: `credential-form-discard-button` | `page.get_by_role("button", { name: "Discard" }).first()` **scoped outside `[role=dialog]`** — critical disambiguation, see next row |
| Discard confirmation dialog (`Modal.BaseModal` inside `DiscardButton.jsx`) | **testid needed** — `BaseModal.jsx` supports a `dataTestId` prop (`data-testid={dataTestId}` — confirmed via source, same gap pattern as ELITEA-1915's Concrete Handles) but `DiscardButton.jsx` never passes one through. Suggested name: `credential-discard-confirm-modal` | `page.get_by_role("dialog")` — acceptable only because exactly one dialog is open at a time in this flow |
| Discard confirmation dialog's "Discard" button | **testid needed** — `BaseModal` supports `confirmButtonDataTestId` (confirmed via source, `data-testid={confirmButtonDataTestId}`) but `DiscardButton.jsx` doesn't pass one. Suggested name: `credential-discard-confirm-button` | `page.get_by_role("dialog").get_by_role("button", { name: "Discard" })` — this is how this exploration disambiguated it from the tab-bar's Discard button live |
| Discard confirmation dialog's "Cancel" button | **testid needed** — same gap; `BaseModal` has no dedicated cancel-button testid prop observed in source at all (only close/confirm) | `page.get_by_role("dialog").get_by_role("button", { name: "Cancel" })` |
| Discard confirmation dialog's warning message text | **testid needed** — plain `content` prop rendered as text, no testid | `page.get_by_role("dialog").get_by_text("Are you sure you want to discard changes?")` — exact-match on the live source constant, low risk of drift since it's a shared constant (`WARNING_MESSAGES.DISCARD_CHANGES`) reused elsewhere (e.g. "unsaved changes" nav-blocker) |

**Summary for the implementer / `add-data-testid`:** the entire
Credential-detail Save/Discard/confirm-dialog flow has **zero**
`data-testid` attributes on its own interactive elements, despite the shared
`BaseModal` and `DiscardButton` components already supporting
`dataTestId`/`confirmButtonDataTestId` props that are simply never wired
through from `CredentialTabBar.jsx` / `DiscardButton.jsx`. This is the same
class of gap documented in ELITEA-1915's AFS for the "Build with AI" modal —
fixing it once in `DiscardButton.jsx` (pass `dataTestId`,
`confirmButtonDataTestId` through from each call site) would benefit every
other feature that reuses `Button.DiscardButton` (Agents, Pipelines, Skills,
Toolkits all likely share this component per its `@/[fsd]/shared/ui` home —
not independently verified for those other pages in this run, flagged for
awareness only).

## Network Behavior
No network calls are specific to the Discard flow itself — Discard is a
pure client-side `formik.resetForm()` + local-state reset (confirmed via
source, `CredentialTabBar.jsx`'s `onCancel`/`wantToCancel` `useEffect`); no
`PUT`/`PATCH` request fires until **Save** is clicked (not exercised by this
case). The only network calls observed during this run were:
- `GET /api/v2/configurations/configuration/{project_id}/{id}` — loads the
  credential detail on page navigation (Step 2).
- The credential's own `POST .../configurations/{project_id}` (create, Step 1)
  and `DELETE .../configuration/{project_id}/{id}` (cleanup) — both via
  `CredentialAPI`, not asserted as part of the Discard case itself.

## Known Defects Found During Exploration

1. **[Dead code / unreachable — NOT filed as a GitHub issue] Route-param
   naming mismatch in `useCredentialActions.js`'s `onEditAction`, but the
   hook is not wired into any live UI path.** Source
   (`EliteaUI/src/hooks/credentials/useCredentialActions.js:101`):
   `` `${RouteDefinitions.EditCredentialFromMain.replace(':uid', integration.uuid || integration.uid)}` ``
   — but the actual route pattern (`routes.js:28`) is
   `/credentials/:tab/:credential_uid`, which contains no `:uid` substring,
   so `.replace(':uid', ...)` is a no-op and `pagePath` would resolve to the
   **literal, unsubstituted string** `/credentials/:tab/:credential_uid` if
   this code path ever executed. Live-verified via `grep`: `useCredentialActions`
   is exported but has **zero import sites** anywhere else in `EliteaUI/src`
   — the hook (and its `onEditAction`) is dead code, unreachable from any
   current UI surface. **Not filed** per this project's bug-filing policy
   (`.agents/profile.md` § Bug filing targets *product* defects — this is
   unreachable code with no live user-facing effect); documented here only
   so a future author doesn't accidentally wire this hook up as-is and ship
   the bug live. Separately confirmed: the case's own actual entry point
   (clicking a credential card from `${BASE_URL}/credentials/all`) resolves
   the **numeric `id`** correctly into the URL (e.g.
   `/credentials/all/1533?viewMode=owner&name=...`) and loads the page
   without error — so this case's own Step 2 is unaffected.
2. **[Informational — not filed] Manually navigating directly to
   `/credentials/all/{uuid}` (using the credential's `uuid` field rather
   than its numeric `id`) 404s** (confirmed live:
   `GET /api/v2/configurations/configuration/399/{uuid}` → `404`, page
   renders `Page404`). The route param is literally named `:credential_uid`
   in `routes.js`, which reads as if it expects the UUID, but the backend
   configuration-detail endpoint only accepts the numeric database `id`.
   This is consistent with defect #1's mismatch, and only surfaces if
   something constructs a URL from `uuid` directly (as `onEditAction` would,
   if it were ever wired up) — the case's actual click-through entry point
   never does this, so it does not affect this case's outcome. Flagged as
   informational/context for whoever eventually looks at defect #1, not
   filed separately.
3. **[Non-blocking, informational — not filed] `data-testid` coverage gap
   on the entire Discard flow.** See Concrete Handles above for the full
   inventory — routed to `add-data-testid` per this project's locator
   policy, not to the tracker (matches `.agents/profile.md` guidance that a
   missing testid is a routing gap, not a product defect).

No functional product defect was found in the case's own Discard flow. All
9 case steps live-verified end-to-end with the expected pass criteria met
exactly.

## Blocked Steps
None. All 9 case steps (Step 1 via API, Steps 2–9 via UI) were executed
end-to-end live against the real DEV backend, including the full
create → edit → discard → verify-reverted round trip and teardown.

## Automation Hints
- Framework: Playwright + pytest, per `.agents/testing.md`. Likely home:
  `automation/tests/ui/toolkits/test_credential_discard_changes.py` (new
  file — grep of `automation/tests/ui/toolkits/` found no existing test
  exercising the Credential-detail Save/Discard tab-bar; the closest
  existing file, `test_toolkit_indicators_for_credentials.py`, covers a
  different concern — authentication-warning indicators on Toolkit/
  Pipeline/Agent pages that *consume* a credential, not the Credential
  detail page's own edit/discard controls).
- New page object suggested: `automation/pages/credential_detail_page.py`
  (parallel to the existing `toolkit_detail_page.py` — no credential-detail
  page object currently exists in `automation/pages/`), holding
  `LocatorDescriptor` fields for every handle in the Concrete Handles table
  above **once the corresponding testids land** via `add-data-testid`. Per
  this project's strict testid-only locator policy, do **not** ship this
  case using the role-based fallbacks used during this exploration — route
  the testid additions through `add-data-testid` first (dual-target flow:
  commit on `automation/testids`, draft PR to `main`), then implement.
- Existing `CredentialAPI` (`automation/api/client.py:949`) already provides
  `create_github_credential()`, `update_credential()`, and
  `delete_credential()` — reuse these directly for setup/teardown rather
  than adding new API helpers. The existing `credential_api` fixture
  (declared in `automation/conftest.py`, function-scoped) is the natural
  fixture to depend on.
- Disambiguating the two same-named "Discard" buttons (tab-bar vs. modal
  confirm) is the one non-obvious selector call an implementer needs: scope
  the tab-bar one with `page.get_by_role("button", { name: "Discard" })`
  outside `[role=dialog]`, and the modal one with
  `page.get_by_role("dialog").get_by_role("button", { name: "Discard" })` —
  or, once testids land per Concrete Handles, use
  `credential-form-discard-button` vs. `credential-discard-confirm-button`
  directly and skip the dialog-scoping workaround entirely.
- Wait strategy: no network response to await for the Discard/reset itself
  (pure client-side state reset, confirmed above) — wait on the dialog's
  `role="dialog"` appearing/disappearing from the accessibility tree
  (Playwright's built-in actionability waits on `get_by_role("dialog")`
  suffice; no fixed timeout needed) rather than a sleep.
