# Test Case: Search Credentials by Name

## Metadata
- **TMS ID**: ELITEA-1965
- **Linked Story**: none
- **Priority**: l2 (case frontmatter + body header both say `medium`, consistent —
  mapped `high`→l1 / `medium`→l2 / `low`→l3 per the convention established in
  ELITEA-1971/1972/1974/1975's AFS files)
- **Environment Explored**: local (`http://localhost:5173`, EliteaUI
  `automation/testids` branch → DEV backend, project `Private` /
  `${ELITEA_PROJECT_ID}`=399)
- **User set**: `${TEST_USER}` (localhost `auth_state` fixture skips login via
  `VITE_DEV_TOKEN`; seeded credentials were created via the UI create-credential
  flow, github type, Anonymous auth — matches the "Create credentials" step the
  case itself specifies; not a live GitHub token validity check, "Test
  connection" is never exercised)
- **Analyst**: qa-engineer (Sage), analyst slot
- **Status**: ready-for-automation

  **Classification note (declared improvisation):** execution surfaced a real,
  deterministic product defect (see § Known Defects Found #1) that makes the
  case's own literal step 6 (clear the search box **after** a zero-results
  search) fail every time. `spec-format.md`'s status vocabulary reads
  `defect-found` as "automation paused until fix" — but that would discard
  the 5 of 6 steps that pass cleanly and duplicate work once the fix ships. I
  classified this `ready-for-automation` instead, per `.agents/testing.md` §
  Merge gate "Sanctioned-RED exception (isolated known defect)": the failure
  is deterministic (2/2), single-cause, and now tied to an OPEN defect
  (`elitea-testing-public#551`). The implementer should write the step-6
  assertion as the **correct** expected behavior (list restored) with a
  `# Known defect: #551` comment / soft-assert, let it merge RED per that
  exception, and it goes green the moment the product fix ships. Reviewer:
  please confirm this reasoning holds (role-overrides.md § Declared-
  improvisation protocol) — recommend codifying "isolated known defect
  discovered during analysis, not just during later automation" as a first-
  class case for the Sanctioned-RED exception if this call is endorsed.
- **Case-gate note**: case frontmatter carries `status: draft`,
  `execution_type: manual`. Per `.agents/test-automation.yaml` § `intake`,
  `draft` is intake-eligible (not an exclusion). Proceeded to full execution.

## Preconditions
- User is logged in to Elitea (on localhost, `auth_state` fixture skips login).
- A project is selected/accessible (`Private`, id `399` in this run).
- The Credentials section is accessible (`/credentials/all`).
- **At least one credential must already exist in the project.** Live-verified
  in a prior AFS (ELITEA-1974, l1_credential-pin-unpin) and consistent with
  this run: a **zero**-credential project redirects `/credentials/all` →
  `/credentials/create-credential` instead of showing an empty list. This run's
  project already had one pre-existing credential ("AutoTest GitHub
  1784156122"), so the zero-credential redirect was never in play here — but
  the implementer's fixture must still guarantee ≥1 credential exists before
  navigating to the list (reuse the existing `credential_api` /
  `github_credential` fixture pattern, do not rely on incidental project state).

## Test Data

### generate-per-test (created in test setup, deleted in teardown)
- Three credentials with deliberately distinct/overlapping-prefix names, so the
  partial-match, full-prefix-match, and no-match search predicates are all
  exercisable against known, recognizable data:
  - `autotest_cred_alpha`
  - `autotest_cred_beta`
  - `autotest_cred_gamma`
  - Type: `github`, Auth: `Anonymous` (no token needed — this case never
    exercises "Test connection", only Display Name + list/search behavior).
    Base URL defaults to `https://api.github.com` and is left as-is.
  - **Test-data call (Hard Rule 10):** the project's one pre-existing credential
    ("AutoTest GitHub 1784156122") does **not** satisfy this case's predicates —
    it shares no prefix with `alpha`/`autotest_cred`/`nonexistent_xyz`, so it
    can't stand in for "type autotest_cred → 3 matches" or "type alpha → 1
    match" without seeding. Seed+cleanup is justified; reuse-existing was
    checked and rejected first.
  - Live-verified during this run: created via UI (`/credentials/create-
    credential/github`, fill Display Name, Save — Anonymous auth needs no other
    required field). IDs observed: `alpha`=1606, `beta`=1607, `gamma`=1608
    (this run; the implementer's fixture will get fresh IDs — capture them from
    the create response for cleanup, do not hardcode).
  - Cleanup: `credential_api.delete_credential(id)` for all three, in a
    `finally` block (pattern from ELITEA-1972/1974's tests) — **do not** rely
    on UI delete for the automated test; UI delete requires typing the
    credential's name into a confirmation dialog and is unnecessary overhead
    when the API client already exists.

### reuse-existing
- `${TEST_USER}` — see `.agents/profile.md` § Roles & sample users.

## Test Steps
1. Create three credentials: `autotest_cred_alpha`, `autotest_cred_beta`,
   `autotest_cred_gamma` (see § Test Data).
   - **Verify**: all three appear as cards on `/credentials/all` (via
     `entity_card_name` collection locator).
2. Navigate to `/credentials/all`.
   - **Verify**: page loads, all 4 credentials visible (3 seeded + 1
     pre-existing), search box present and empty.
3. Click the search input, type `alpha`, **press Enter** (see note below — this
   is not optional).
   - **Verify**: only `autotest_cred_alpha` is displayed; the network request
     `GET /configurations/configurations/{project}?...&query=alpha&section=
     credentials...` fires and returns 200.
4. Clear and type `autotest_cred` in the search box, press Enter.
   - **Verify**: all three seeded credentials (`alpha`, `beta`, `gamma`) are
     displayed; the pre-existing "AutoTest GitHub 1784156122" is correctly
     excluded (no prefix match); network `query=autotest_cred` fires.
5. Clear and type `nonexistent_xyz`, press Enter.
   - **Verify**: empty state renders — "Nothing found. Create yours now!" with
     the rocket-icon illustration; network `query=nonexistent_xyz` fires,
     returns 200 with `total: 0`.
6. Click the search box's Clear (X) icon.
   - **Verify (case's literal expectation)**: all credentials are listed again
     on `/credentials/all`.
   - **Actual (known defect — see § Known Defects #1)**: the app navigates to
     `/credentials/create-credential` instead. This assertion is expected to
     FAIL until `elitea-testing-public#551` is fixed — implement it as the
     correct expectation with a `# Known defect: #551` marker per the
     Sanctioned-RED exception (`.agents/testing.md` § Merge gate).

### Interaction-discovery note (role-overrides.md ladder, applied)
Typing alone does **not** filter the list — confirmed live: after typing
`alpha` with no Enter/blur/send-click, all 4 cards remained visible and only a
suggestions popper appeared. Read the source
(`EliteaUI/src/components/SearchBar.jsx`): `onChange` only updates local
`searchString`; the actual `dispatch(actions.setQuery(...))` (which drives the
list re-fetch) happens exclusively in `onSearch()`, wired to `onKeyDown`
(`Enter`) and the send-icon's `onClick`. This mirrors the previously-documented
#44 pattern (Skills search) — **not** a new finding, but re-confirmed for this
component instance since the case text ("Type X in the search box") is
ambiguous about activation mode and a first guess of live-filtering would have
been wrong. Not a defect, not a clarification — this is the case under-
specifying HOW, which role-overrides.md treats as normal; the intended mode
(Enter) works correctly.

## Expected Results
- Search is **explicit-activation** (Enter or send-icon click), not
  live-filter-as-you-type — server-side, via `query=` param on
  `GET /configurations/configurations/{project}`.
- Partial name match (`alpha`) returns exactly the credentials whose name
  contains it.
- Prefix match (`autotest_cred`) returns all three seeded credentials, only.
- No-match search (`nonexistent_xyz`) shows the empty state, not an error.
- Clearing the search box after a **non-empty**-result search correctly
  restores the full list (live-verified working).
- Clearing the search box after a **zero**-result search should also restore
  the full list, but currently does not (see Known Defects #1).
- No console errors at any step (checked after every interaction).

## Coverage Map

### Axis 1 — Case coverage

| Case element | Expected result | Covered by (AFS step) | Asserted where | Disposition |
|---|---|---|---|---|
| 1 Create 3 credentials | all three created and visible | AFS step 1 | step 1: `entity_card_name` collection contains all 3 | asserted |
| 2 Navigate to credentials list | list page loads | AFS step 2 | step 2: `entity_card` visible, 4 cards | asserted |
| 3 Type "alpha" in search box | only alpha shown | AFS step 3 (decomposed: type + **Enter**, see interaction-discovery note) | step 3: card count = 1, name = alpha; network `query=alpha` 200 | asserted |
| 4 Type "autotest_cred" | all three shown | AFS step 4 | step 4: card count = 3, names = alpha/beta/gamma; network `query=autotest_cred` 200 | asserted |
| 5 Type "nonexistent_xyz" | empty/no-results shown | AFS step 5 | step 5: "Nothing found. Create yours now!" text visible; network `query=nonexistent_xyz` 200, `total:0` | asserted |
| 6 Clear the search box | all credentials listed again | AFS step 6 | step 6: assert URL stays `/credentials/all` and full list restored — **currently fails, known defect #551** | asserted *(known defect — see § Known Defects #1; Sanctioned-RED per classification note)* |
| Expected Final State: "search filters dynamically; clearing restores full list" | — | AFS steps 3–6 | as above | asserted, partially contradicted for the zero-results→clear path (defect #551) |

### Axis 2 — Analyst additions

- `step 3` (before pressing Enter): asserted that typing alone does **not**
  trigger a network request / does not filter the list — *added: this is the
  crux fact behind the interaction-discovery ladder call above; a future
  regression that silently switches this control to live-filter (or removes
  the Enter-gate) should be caught, not assumed.*
- `step 4`: asserted the pre-existing unrelated credential ("AutoTest GitHub
  1784156122") is correctly **excluded** from the `autotest_cred` prefix match
  — *added: verifies the search is a genuine substring/prefix match, not "any
  GitHub-type credential."*
- New scenario not in the case text: clearing the search box **after a
  non-empty-result search** (e.g. after step 3's `alpha` search) — *added:
  needed to establish the defect in § Known Defects #1 is scoped to the
  zero-results path specifically, not "Clear is broken" generally; also
  becomes the regression guard once #551 is fixed and doubles as the "clear
  works" happy-path assertion the case's step 6 originally intended.*
- All steps: no console errors — *added, standard side-channel check per
  test-case-analysis skill.*

## Cleanup
1. Delete the three seeded credentials via `credential_api.delete_credential(id)`
   for each of `alpha`/`beta`/`gamma`'s numeric `id` (captured from the create
   response), in a `finally` block so cleanup runs even on assertion failure.
2. No other state to clean up — search query is client/URL-local and clears on
   next navigation; no server-side "saved search" concept observed.

## Concrete Handles (discovered during exploration)

Locator policy: **testid-only** (`.agents/testing.md` § Locator policy,
`.agents/role-overrides.md`) — no role/label/text/CSS fallback rung. Every
element lacking a testid is `testid needed: ...`, not a lower-tier handle.

| Element | Testid | Provenance | Fallback |
|---|---|---|---|
| Search input (shared `SearchBar`, reused on every list page incl. Credentials) | `agent-search-input` (default `testId` prop value in `SearchBar.jsx`; page-specific override exists only for Pipelines→`pipeline-search-input`, Credentials uses the default) | **on-main ✓** | none (testid-only; do not use `getByPlaceholder`) |
| Search submit / send icon | `skills-search-send-button` (hardcoded in `SearchBar.jsx`, same value on every page — pre-existing naming oddity, not introduced by this AFS) | **on-automation/testids only** (draft `EliteaAI/EliteaUI#543`, EL-1739) | none |
| Search **Clear (X)** icon | `agent-search-clear-button` — **implementer confirmed** the analyst's proposed naming (mirrors the send button's generic cross-page naming); added via `add-data-testid` | **on-automation/testids ✓** (draft `EliteaAI/EliteaUI#573`) | none |
| Credential card outer container (list) | `entity-card` | **on-automation/testids only** (draft `EliteaAI/EliteaUI#544`, EL-1740) | none |
| Credential card name/title (list) | `entity-card-name` | **on-main ✓** | none |
| Create-form Display Name input (used to seed test credentials) | `toolkit-field-label-input` (`ToolBaseProperty.jsx`'s dynamic `toolkit-field-${k}-input` pattern, `k="label"`) | **on-automation/testids only** (draft `EliteaAI/EliteaUI#554`, EL-1922) | none |
| Create-form Save button | `credential-form-save-button` | **on-automation/testids only** (draft `EliteaAI/EliteaUI#562`, EL-1971) | none |
| GitHub credential-type selector card (create flow entry) | `toolkit-type-card-github` (`CategoryItemCard.jsx`'s dynamic `toolkit-type-card-${itemKey}` pattern) | **on-automation/testids only** (draft `EliteaAI/EliteaUI#554`, EL-1922) | none |
| Empty-state text ("Nothing found. Create yours now!") | `credentials-search-empty-state` — implementer chose the testid route (not `page.get_by_text(...)`) per the strict testid-only policy in `.agents/role-overrides.md` (any non-testid handle added is `CHANGES_REQUESTED`, no exception for content-vs-interaction); added via `add-data-testid` on the `EmptyListPlaceHolder`'s non-empty-query `<Box>` in `CredentialsList.jsx` | **on-automation/testids ✓** (draft `EliteaAI/EliteaUI#574`) | none |

### Page object impact (Automation Hints continued)

`automation/pages/credentials_list_page.py` (`CredentialsListPage`) has no
search-related locators/methods yet — this case is the first to need them.
Add, as class-level `LocatorDescriptor` fields:
```python
search_input = LocatorDescriptor(testid="agent-search-input", description="Credentials search box (shared SearchBar component)")
search_send_button = LocatorDescriptor(testid="skills-search-send-button", description="Search submit icon (shared component, generic testid)")
search_clear_button = LocatorDescriptor(testid="agent-search-clear-button", description="Search clear (X) icon — testid added via add-data-testid for ELITEA-1965")
```
and methods `search(term: str)` (type + press Enter, wait for the
`configurations` GET response) and `clear_search()` (click
`search_clear_button`, wait for the unfiltered list to re-render) — do not
inline these in the spec file (`.claude/rules/page-objects.md`).

## Network Behavior
- `GET /api/v2/configurations/configurations/{project_id}?include_shared=true&shared_offset=0&shared_limit=20&limit=20&offset=0&sort_by=created_at&sort_order=desc&query={term}&section=credentials&section=storage`
  — fires **only** on Enter / send-icon click, never on keystroke alone. Wait
  on this response (`page.expect_response`), never a fixed sleep, before
  asserting the filtered card list.
- Clearing the search box does **not** independently fire a fresh GET with
  `query=` in the success (non-empty) path in a way visibly distinct from a
  normal re-render — the implementer should wait for the list's re-fetch
  (`onClear()` dispatches `resetQuery()`, which the `useLoadAllCredentials`
  hook reacts to) rather than assuming an immediate DOM update.

## Known Defects Found During Exploration

1. **[MAJOR] Clearing a zero-results Credentials search redirects to
   `/credentials/create-credential` instead of restoring the list.**
   Filed: `elitea-testing-public#551`.
   Repro: search `nonexistent_xyz` (Enter) → empty state renders correctly →
   click Clear (X) → app navigates away from `/credentials/all`. Reproduced
   2/2, deterministic, single native click each time, fresh page navigation
   each time (pristine-repro gate passed). Root cause (read from
   `CredentialsList.jsx`): the "redirect an empty project to Create
   Credential" `useEffect` guard checks `!hasQuery && total === 0`; `onClear()`
   flips `hasQuery` to `false` synchronously, but `total` is still the stale
   `0` from the just-cleared zero-results search until the unfiltered list
   re-fetch completes — a one-render race that fires the empty-*project*
   redirect for a merely empty-*filtered-view* project. **Scoped**: clearing
   after a non-empty-result search (e.g. `alpha` → 1 match) does **not**
   trigger this — `total` is non-zero at the moment `hasQuery` flips, so the
   guard's `total === 0` never fires. Directly blocks TMS case ELITEA-1965's
   own steps 5→6 sequence.
2. **testid needed** (implementer work, not a product defect): the search
   box's Clear (X) icon has no `data-testid`. See § Concrete Handles for the
   proposed name and the declared-improvisation reasoning.

### Implementer-phase addendum — newly discovered during automation (Phase 2/4)

3. **[MINOR] Intermittent 404 console error, unrelated to search:
   `GET /elitea_core/toolkits/prompt_lib/` (empty projectId) on
   `/credentials/all` load.** Filed: `elitea-testing-public#554`. Root cause
   (read from `EliteaUI/src/api/toolkits.js`): the `toolkitTypes` RTK-Query
   endpoint (backing the right-panel "TYPES" filter) builds its URL from
   `projectId`; when the query fires before `useSelectedProjectId()` resolves,
   the URL collapses to `.../toolkits/prompt_lib/` (no id segment) and 404s.
   Reproduced intermittently (~4/8 identical automated runs during
   implementation — a client-side query-timing race, not deterministic).
   Cosmetic only — the TYPES panel still renders correctly once the query
   re-fires with a real id; no functional impact on any of this case's
   assertions observed. Out of scope for this case (not a search defect) —
   the implementation filters this specific, already-tracked console message
   out of its console-error assertion (same treatment as the pre-existing
   #291 warning), so it is NOT part of the Sanctioned-RED signature for
   Known Defect #1 above.

## Blocked Steps
None — all 6 case steps were executed and observed end-to-end. Step 6 diverges
from its expected result due to Known Defect #1, but this did not block
execution or observation (see § Test Steps step 6 and the classification note
in § Metadata).

## Automation Hints
- Framework: Playwright + pytest, confirmed (`.agents/testing.md`).
- Seed credentials via UI (`CredentialCreatePage.navigate_to_type("github")` →
  `set_display_name()` → `save_button.click()`), matching the precedent in
  ELITEA-1972/1974/1975's tests — not via raw `credential_api.create_credential()`
  payload construction, since the case's own step 1 is "Create credentials"
  through the product UI, not an API shortcut. Delete via `credential_api`
  (API is fine for cleanup — it's not part of the case's observable behavior).
- Wait strategy: `page.expect_response(...)` on the `configurations` GET with
  `query=` in the URL, matching the pattern already used in
  `test_credential_id_auto_generation.py` for the create/rename POST/PUT waits.
  Never a fixed `page.wait_for_timeout()` for the search itself.
- Step 6's assertion: written as the **correct** expected behavior (full list
  restored, URL stays `/credentials/all`) using `expect.soft()` with a
  `# Known defect: #551` comment — **not** the first case needing this
  pattern in `toolkits-credentials` after all: `test_credential_required_
  fields_validation.py` (ELITEA-1975, defect #526) already established
  `expect.soft()` + `# Known defect: <id>` as this suite's convention (the
  AFS's original framing of "may be the first" undersold an existing
  precedent in the same directory — `xfail` was not used, to stay consistent
  with the established sibling test rather than introduce a second pattern).
  Both `expect.soft()` calls (URL + full-list-restored count) plus a
  count-gated follow-on read reproduced 3/3 identical (deterministic) across
  separate pytest invocations — meets `.agents/testing.md` § Merge gate's
  Sanctioned-RED bar.
