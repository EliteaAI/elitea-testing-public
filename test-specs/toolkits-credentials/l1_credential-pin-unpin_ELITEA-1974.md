# Test Case: Credential — Pin/Unpin

## Metadata
- **TMS ID**: ELITEA-1974
- **Linked Story**: none
- **Priority**: l1 (case frontmatter: `high`; case body header says `medium` —
  **pre-existing inconsistency in the source case**, not introduced by this
  AFS, same class of drift documented in ELITEA-1971's AFS. `high` from the
  frontmatter is treated as authoritative per that established convention.
  Not filed as a defect — case-authoring nit, not a product bug.)
- **Environment Explored**: local (`http://localhost:5173`, EliteaUI
  `automation/testids` branch → DEV backend, project `Private` /
  `${ELITEA_PROJECT_ID}`=399)
- **User set**: `${TEST_USER}` (localhost `auth_state` fixture skips login via
  `VITE_DEV_TOKEN`; credentials themselves were created via API using
  `CredentialAPI.create_github_credential()`, matching the pattern established
  in ELITEA-1971/1972/1975 — not a live GitHub token validity check, this
  case never exercises "Test connection")
- **Analyst**: qa-engineer (Sage), analyst slot
- **Status**: ready-for-automation
- **Case-gate note**: case frontmatter carries `status: draft`,
  `execution_type: manual`. Per `.agents/test-automation.yaml` § `intake`,
  `status: draft` is the **intake-eligible** value for this project (cases
  awaiting automation), not an exclusion — so this is not a gate finding, it
  confirms the case is in-scope. Proceeded to full execution.

## Preconditions
- User is logged in to Elitea (on localhost, `auth_state` fixture skips
  login).
- A project is selected/accessible (`Private`, id `399` in this run).
- The Credentials section is accessible (`/credentials/all`).
- **At least one credential exists.** Live-verified: with **zero**
  credentials in the project, `/credentials/all` **redirects** to
  `/credentials/create-credential` instead of showing an empty list —
  confirmed live via `browser_navigate` + snapshot before any test data was
  seeded (see Known Defects/Observations #1 for whether this is worth a
  clarification). The implementer's fixture MUST seed at least one
  credential before navigating to the list, or the case's own Step 1 ("list
  page loads") cannot be observed as authored.
- **This AFS seeds two credentials, not one** — a single pinned credential
  trivially satisfies "moved to the top" (nothing to be above), but doesn't
  prove *relative* reordering. A second, unpinned credential gives Steps 2
  and 7 an unambiguous before/after position to assert against (mirrors the
  reasoning already used for list-ordering assertions elsewhere in this
  suite).

## Test Data

### generate-per-test (created in test setup, cleaned up in its own teardown)
- Credential A: `CredentialAPI.create_github_credential(display_name="autotest_pin_cred_a_<ts>", base_url="https://api.github.com", token=${GIT_HUB_TOKEN})`.
  Live-verified this run: returns `{"id": 1570, "uuid": "cc9815c3-5c88-4788-92ce-55eee05b54d4", "label": "autotest_pin_cred_a_1784155050", ...}`.
  This is the credential that gets pinned/unpinned.
- Credential B: `CredentialAPI.create_github_credential(display_name="autotest_pin_cred_b_<ts>", base_url="https://api.github.com", token=<any string — never validated by this case>)`.
  Live-verified this run: returns `{"id": 1571, "uuid": "760dc755-e224-480b-8521-3c2b31eb80a7", "label": "autotest_pin_cred_b_1784155055", ...}`.
  Created **second** (`ts+5`s later) so it sorts **above** Credential A under
  the list's default `sort_by=created_at&sort_order=desc` — this is what
  gives Step 2/7 a real "position" to move to/from.
- No shared/reused fixture applies — pin state is a per-record mutation;
  reusing a shared credential across parallel/retried runs risks state
  bleed between tests asserting on list order.

## Test Steps

1. Navigate to the Credentials list (`${BASE_URL}/credentials/all`), with
   Credential A and Credential B already seeded via API (test setup, not a
   numbered case action — see Preconditions).
   - **Verify**: page loads, both credentials appear in Card list view
     (default view — a "Table view" / "Card list view" toggle also exists,
     not exercised by this case), in order **B above A** (both confirmed
     live via `browser_snapshot`: `autotest_pin_cred_b_...` row precedes
     `autotest_pin_cred_a_...` row) — this is the *before* baseline Step 2's
     assertion diffs against. Each card shows a **"Pin to top"** icon button
     (confirmed live, `IconButton` with `aria-label="Pin to top"`, visible
     unconditionally at rest in this run — MUI hover-opacity styling exists
     in source (`PinButton.jsx`'s `isVisible = isPinned || isHovered ||
     alwaysVisible`) but did not suppress the icon from the accessibility
     snapshot).

2. Click the "Pin to top" button on Credential A's card
   (`getByRole("button", { name: "Pin to top" }).nth(1)` in this run's DOM
   order — **fragile positional selector, see Concrete Handles for why a
   scoped/testid selector is required for automation**).
   - **Verify**: `POST /api/v2/social/pin/prompt_lib/{project_id}/configuration/{id}`
     fires and returns **201 Created** (confirmed live via
     `browser_network_requests`: `POST
     http://localhost:5173/api/v2/social/pin/prompt_lib/399/configuration/1570
     => [201] Created`). Immediately after, Credential A's card **moves to
     the top of the list** (confirmed live via re-snapshot: order is now
     **A above B**), and its icon button's accessible name flips to
     **"Unpin from top"** (confirmed live: `generic "Unpin from top": button
     "Unpin from top"`). Zero console errors/warnings across this
     interaction (confirmed via `browser_console_messages`).

3. Navigate to the pinned credential's detail page (click the Credential A
   card's display-name text — same click-through entry point documented in
   ELITEA-1971's AFS).
   - **Verify**: page loads at
     `${BASE_URL}/credentials/all/1570?viewMode=owner&name=autotest_pin_cred_a_...`
     (confirmed live), tab shows the credential's Display Name as its
     accessible name, form fields populate as expected (Display Name, ID,
     Base Url, Auth radio group, Access Token) — same detail-page shape
     documented in ELITEA-1971/1972's AFS, not re-derived here.

4. Click the three-dot menu button in the tab bar
   (`page.get_by_test_id("controls-menu-button")` — **confirmed live,
   existing testid**, `IconButton` rendered by the shared `DotMenu`
   component with `data-testid={id + '-menu-button'}` where `id="controls"`
   per `ControlsDropdown.jsx`'s default prop).
   - **Verify**: dropdown menu opens (confirmed live via snapshot:
     `menu [ref=...]` appears in the a11y tree) showing two items in this
     run: the pin-toggle item and **"Delete"**.

5. Verify the menu shows **"Unpin from top"**.
   - **Verify**: confirmed live — `menuitem "Unpin from top"` present in the
     opened menu's accessibility tree, matching the case's exact expected
     text (source: `usePinMenu.hooks.jsx` — `label: isPinned ? 'Unpin from
     top' : 'Pin to top'`, driven by the same `isPinned` derived-from-Formik
     state documented in Known Defects/Observations #2 below).

6. Click **"Unpin from top"**
   (`page.get_by_role("menuitem", { name: "Unpin from top" })` — **no
   `data-testid` on this menu item in the live DOM, see Concrete Handles**).
   - **Verify**: `DELETE
     /api/v2/social/pin/prompt_lib/{project_id}/configuration/{id}` fires
     and returns **204 No Content** (confirmed live via
     `browser_network_requests`: `DELETE
     http://localhost:5173/api/v2/social/pin/prompt_lib/399/configuration/1570
     => [204] No Content`). Zero console errors/warnings across this
     interaction (confirmed via `browser_console_messages`, total 9
     messages / 0 errors / 0 warnings across the full pin→navigate→unpin
     sequence up to this point).

7. Verify the credential returns to its normal position in the list.
   - **Verify** (two-part, both confirmed live):
     (a) Re-opening the same three-dot menu on the still-open detail page
     immediately shows **"Pin to top"** again (menu item text flipped back
     — confirmed live via re-snapshot right after Step 6's click, before
     navigating away, proving the unpin took effect client-side
     immediately, not just eventually);
     (b) navigating back to `${BASE_URL}/credentials/all` shows the list in
     its **original B-above-A order** (confirmed live via re-snapshot:
     `autotest_pin_cred_b_...` again precedes `autotest_pin_cred_a_...`,
     identical to Step 1's baseline), and Credential A's list-row icon
     button reads **"Pin to top"** again (confirmed live).

**Side-channel check (all steps):** zero console errors or warnings across
the full pin → navigate → menu-open → unpin → re-verify flow (confirmed via
`browser_console_messages`, `all: true` equivalent scope for this run).

## Expected Results
Matches the case's Pass criteria exactly, live-verified end-to-end: pinning
moves the credential to the top of the list (Step 2), the detail page's
three-dot menu reflects pinned state via "Unpin from top" (Steps 4–5),
unpinning fires the expected `DELETE` and reverts both the menu label and
the list position (Steps 6–7). No functional defect found in the pin/unpin
mechanism itself. Two non-blocking observations are documented below (Known
Defects/Observations #1 and #2) — neither alters this case's own pass/fail
outcome.

## Coverage Map

### Axis 1 — Case coverage

| Case element | Expected result | Covered by (AFS step) | Asserted where | Disposition |
|---|---|---|---|---|
| Precondition: user logged in | — | AFS Preconditions | `auth_state` fixture (localhost dev token) | asserted |
| Precondition: project exists with ≥1 credential | — | AFS Preconditions + Test Data | two credentials seeded via `CredentialAPI` | asserted *(seeded via API, not the create-form UI — see Preconditions note; also surfaces the empty-list-redirect observation, #1)* |
| Precondition: Credentials section accessible | — | AFS Preconditions | `/credentials/all` loads once ≥1 credential exists | asserted |
| 1 Navigate to Credentials list | list page loads | step 1 | step 1: both cards visible, B-above-A baseline order captured | asserted |
| 2 Find a credential, click "Pin to top" | credential moves to top | step 2 | step 2: `POST .../pin/...` 201, re-snapshot shows A-above-B, button label flips to "Unpin from top" | asserted |
| 3 Navigate to pinned credential's detail page | detail page loads | step 3 | step 3: URL + form fields populate | asserted |
| 4 Click the three-dot menu | dropdown menu opens | step 4 | step 4: menu appears in a11y tree via `controls-menu-button` | asserted |
| 5 Verify menu shows "Unpin from top" | menu option displays "Unpin from top" | step 5 | step 5: exact menuitem text match | asserted |
| 6 Click "Unpin from top" | credential is unpinned | step 6 | step 6: `DELETE .../pin/...` 204 | asserted |
| 7 Verify credential returns to normal position | credential no longer at top | step 7 | step 7a (menu re-check) + step 7b (list re-navigate, B-above-A restored) | asserted *(decomposed into two confirmations — menu-state and list-position — since the case's single expected result implies both, and only asserting one would leave the other unverified)* |
| Expected Final State: pinned then unpinned back to normal position | — | steps 2, 7 | step 2 (pin) and step 7 (unpin reversion) jointly | asserted |

### Axis 2 — Analyst additions

- step 1 documents the exact list-view "Pin to top" icon button and its
  live visibility behavior — *added: gives the implementer the entry-point
  handle and flags the hover-opacity styling in source that this
  accessibility-tree-based exploration could not independently confirm
  visually (see Concrete Handles).*
- step 2 documents the underlying `POST .../social/pin/...` network call
  and its 201 status — *added: the case only asks to verify visual
  reordering, but the network call is the mechanism an implementer will
  want to wait on (`page.wait_for_response`) rather than a fixed sleep.*
- step 4 documents that `controls-menu-button` **already carries a
  `data-testid`** — *added: saves the implementer an `add-data-testid`
  round-trip for this one element, unlike ELITEA-1971's fully-untested
  Discard flow.*
- step 6 documents the underlying `DELETE .../social/pin/...` call and its
  204 status — *added: same reasoning as step 2, for the reverse action.*
- step 7 documents the **immediate in-page menu-label flip** (7a) as a
  distinct, faster-to-assert observable *before* the full list re-navigation
  (7b) — *added: an implementer can assert 7a without a full navigation
  round-trip if a faster smoke check is ever wanted, though 7b is the
  case's literal "position in the list" ask and should remain the primary
  assertion.*
- "zero console errors/warnings across the full flow" — *added: side-channel
  check per this skill's standard discipline; not itself a case requirement.*

## Cleanup
1. Delete both credentials created in Test Data via
   `CredentialAPI.delete_credential(credential_id)` in test teardown
   (regardless of pass/fail) — confirmed live this run:
   `DELETE /configurations/configuration/{project_id}/{id}` for both `1570`
   and `1571`, then re-verified via `CredentialAPI.list_all_credentials()`
   that neither id remains in the project (empty match set, confirmed).
2. No other product state is created by this case — pin/unpin state lives
   on the credential record itself and is removed along with it; no
   separate "pin" record needs independent cleanup (confirmed via the
   `DELETE .../social/pin/...` call pattern observed — pinning is scoped to
   `configuration/{id}`, not a standalone entity).
3. No route interception, mocked network, or browser-context state needs
   explicit teardown beyond the normal per-test browser context lifecycle.

## Concrete Handles (discovered during exploration)

| Element | Recommended Locator | Fallback |
|---|---|---|
| Credentials list → "Pin to top" / "Unpin from top" icon button (`PinButton.jsx`, used in `DataTableRow.jsx`'s card/list rendering) | **testid needed** — confirmed live via `browser_evaluate`: zero `data-testid` attribute on the `IconButton` (`aria-label` only, "Pin to top"/"Unpin from top", flips with state). Request via `add-data-testid`, suggested name `credential-pin-toggle-button` scoped per-row (the shared `PinButton` component is reused across Skills/Toolkits/Applications/MCPs list rows per the widget's `entityType` prop — a single scoped testid pattern like `{entity}-pin-toggle-button` would benefit all of them, not just Credentials) — **to-verify in implementer Phase 2** whether the testid should be scoped per-card (e.g. include an id/index) since multiple rows render the same component | `page.get_by_role("button", { name: "Pin to top" })` scoped to the specific card container (by adjacent display-name text) — **do not** use an unscoped `.nth(n)` positional index as this AFS did during exploration; that breaks the moment sort order or page size changes |
| Credential detail page → three-dot menu button (`ControlsDropdown.jsx` → `DotMenu.jsx`, `id="controls"` default) | `page.get_by_test_id("controls-menu-button")` — **confirmed live, existing testid** (`data-testid={id + '-menu-button'}` in `DotMenu.jsx`, `id="controls"` passed by default from `ControlsDropdown`) | `page.get_by_role("button")` inside the tab-bar controls group, right of the disabled Discard/Save buttons |
| Credential detail page → pin-toggle menu item ("Pin to top" / "Unpin from top", `usePinMenu.hooks.jsx` → rendered via `DotMenu`'s `BasicMenuItem`) | **testid needed** — confirmed via source read: `DotMenu.jsx` only sets `data-testid={testId ? \`${testId}-menuitem\` : undefined}` where `testId = item.key`; the pin menu item object built in `CredentialsControls.jsx` (`{...pinMenuItem, disabled: ...}`) never sets a `key`, so `testId` is `undefined` and the rendered `MenuItem` gets **no `data-testid`** — unlike the adjacent **Delete** item, which does set `key: 'delete-credentials'` and correctly gets `delete-credentials-menuitem`. Suggested fix: add `key: 'pin-toggle-credential'` (or similar) to the `pinMenuItem` spread in `CredentialsControls.jsx`, which would then flow through to `{key}-menuitem` automatically — **to-verify in implementer Phase 2**, and note this same gap likely applies to `SkillControls.jsx` / `ToolkitsControls.jsx` / `ApplicationControls.jsx`, which all consume `usePinMenu` the same way (not independently re-confirmed for those other pages in this run) | `page.get_by_role("menuitem", { name: "Unpin from top" })` / `page.get_by_role("menuitem", { name: "Pin to top" })` — unambiguous in this run since only one menu is open at a time and only one item carries that exact accessible name |
| Credential detail page → "Delete" menu item | `page.get_by_test_id("delete-credentials-menuitem")` — **confirmed via source** (`key: 'delete-credentials'` set in `CredentialsControls.jsx`, flows to `DotMenu`'s `testId` prop); not independently clicked/live-confirmed in this run since Delete is outside this case's scope | `page.get_by_role("menuitem", { name: "Delete" })` |

**Summary for the implementer / `add-data-testid`:** two testid gaps found
— (1) the list-view Pin/Unpin icon button has zero `data-testid` on any of
the four+ entity types that reuse `PinButton.jsx`; (2) the pin-toggle menu
item on the entity-detail three-dot menu has zero `data-testid` on any of
the four+ entity types that reuse `usePinMenu.hooks.jsx` via `DotMenu`,
purely because the `pinMenuItem` object never sets a `key` (unlike its
sibling `Delete` item, which does and correctly gets one). Both are
one-line fixes at the shared-component/call-site level, not per-page.

## Network Behavior
- `POST /api/v2/social/pin/prompt_lib/{project_id}/configuration/{id}` —
  fires on pin (Step 2), returns `201 Created`. No response body inspected
  in this run beyond the status code.
- `DELETE /api/v2/social/pin/prompt_lib/{project_id}/configuration/{id}` —
  fires on unpin (Step 6), returns `204 No Content`.
- `GET /api/v2/configurations/configurations/{project_id}` (list) and
  `GET /api/v2/configurations/configuration/{project_id}/{id}` (detail) —
  standard list/detail loads, not specific to pin/unpin, consistent with
  the pattern documented in ELITEA-1971/1972's AFS.
- The credentials' own `POST .../configurations/{project_id}` (create,
  Test Data setup) and `DELETE .../configuration/{project_id}/{id}`
  (cleanup) — both via `CredentialAPI`, not asserted as part of the
  pin/unpin case itself.

## Known Defects / Observations Found During Exploration

1. **[Informational — not filed as a GitHub issue] Navigating to
   `/credentials/all` with zero credentials in the project redirects to
   `/credentials/create-credential`** rather than rendering an empty
   Credentials list. Confirmed live via `browser_navigate` +
   `browser_snapshot` before any test data existed in this run's project.
   This is plausibly intentional UX (steer a first-time user straight into
   creation) rather than a defect, and this case's own preconditions
   already require "a project exists with at least one credential" — so
   the case's own Step 1 is never actually exercised against a
   zero-credential state. Flagged here only so an implementer building a
   *separate* "empty Credentials list" case doesn't mistake this redirect
   for a bug; not filed per this project's bug-filing policy (behavior,
   not confirmed-wrong).
2. **[Informational, source-level only — not filed] Dead/no-op prop name in
   `CredentialsControls.jsx`.** Source
   (`EliteaUI/src/[fsd]/features/credentials/ui/credentials-tab-bar/CredentialsControls.jsx`,
   the `usePin(...)` call): the prop is spelled
   `шnitialPinned: !!credentialDetails?.is_pinned` — the first character is
   a **Cyrillic "ш" (U+0448), not a Latin "i"** — so this key never matches
   `usePin.hooks.js`'s destructured `initialPinned` parameter, and the
   real prop silently falls through to that hook's own default
   (`initialPinned = false`). **Confirmed this has no live observable
   effect on this case**: `usePin` derives `isPinned` from
   `formikContext?.values?.is_pinned` whenever a `formikContext` is passed
   (which `CredentialsControls` always does — it calls
   `useFormikContext()`), so `initialPinned`/`localIsPinned` is dead code
   on this call path regardless of the typo — the detail page's Formik
   initial values (populated from the credential's real `is_pinned` field
   on load) are what actually drove the correct "Unpin from top" /
   "Pin to top" menu text observed live in Steps 5 and 7a. **Not filed** —
   no functional defect, purely a source-level typo on an already-dead
   prop; flagged here only so a future refactor of this hook's
   formik-vs-local-state branching doesn't get bitten by it if the
   `formikContext` branch is ever removed.

No functional product defect was found in the case's own pin/unpin flow.
All 7 case steps live-verified end-to-end with the expected pass criteria
met exactly, including full round-trip reversion back to the original list
order.

## Blocked Steps
None. All 7 case steps were executed end-to-end live against the real DEV
backend, including the full seed → pin → verify-detail-menu → unpin →
verify-reverted → teardown round trip.

## Automation Hints
- Framework: Playwright + pytest, per `.agents/testing.md`. Likely home:
  `automation/tests/ui/toolkits/test_credential_pin_unpin.py` (new file —
  grep of `automation/tests/ui/toolkits/` found no existing test exercising
  pin/unpin for credentials; the four existing files in that directory
  cover discard, ID auto-generation, required-fields validation, and
  toolkit-indicator badges — none touch the pin/unpin widget).
- Existing `CredentialAPI` (`automation/api/client.py:949` region) already
  provides `create_github_credential()`, `list_all_credentials()`, and
  `delete_credential()` — reuse these directly for setup/teardown, same
  pattern as `test_credential_discard_changes.py`. No new API helper is
  needed for pin/unpin itself since the case only exercises pin/unpin
  through the UI (the `POST`/`DELETE .../social/pin/...` endpoints are
  incidental network observations, not something the automated test needs
  to call directly).
- New/extended page object: no dedicated `credential_detail_page.py`
  exists yet in `automation/pages/` (same gap noted in ELITEA-1971's AFS —
  if that page object lands first, this case's pin-toggle-menu-item and
  three-dot-menu-button locators belong on it as `LocatorDescriptor`
  fields). The list-view Pin/Unpin button belongs on whatever page object
  wraps `/credentials/all` (also not yet present under that name in
  `automation/pages/` per a grep of the directory — **to-verify in
  implementer Phase 2**).
- Per this project's strict testid-only locator policy, ship this case
  only after routing both testid gaps (list-view pin/unpin icon button;
  detail-page pin-toggle menu item) through `add-data-testid` first
  (dual-target flow: commit on `automation/testids`, draft PR to `main`,
  then implement against the landed testids) — do not ship using the
  role-based fallbacks used during this exploration.
- Wait strategy: wait on the `POST`/`DELETE .../social/pin/...` network
  response (`page.wait_for_response` matching the URL pattern) rather than
  a fixed sleep before asserting the reordering or menu-label flip —
  both observed to complete synchronously with the response in this run
  (no separate loading-state UI was observed for the pin toggle itself).
- Assertion for "moved to the top" / "returned to normal position": assert
  on the **relative order** of the two seeded credentials' display-name
  text nodes within the list container (e.g. compare
  `bounding_box().y` or DOM-order index of credential A vs. credential B),
  not on absolute page position — mirrors how this AFS validated ordering
  live via before/after snapshot diffing.
