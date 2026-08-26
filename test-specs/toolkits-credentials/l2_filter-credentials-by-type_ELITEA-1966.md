# Test Case: Filter Credentials by Type

## Metadata
- **TMS ID**: ELITEA-1966
- **Linked Story**: none
- **Priority**: l2 (case frontmatter `priority: medium` + body header `Priority: medium`,
  consistent — mapped `high`→l1 / `medium`→l2 / `low`→l3 per the convention
  established by ELITEA-1965/1971/1972/1974/1975's AFS files)
- **Environment Explored**: local (`http://localhost:5173`, EliteaUI
  `automation/testids` → DEV backend `https://dev.elitea.ai/api/v2`), project
  `Private` / `${ELITEA_PROJECT_ID}`=399, identity "Test Bot"
- **User set**: `${TEST_USER}` (localhost `auth_state` fixture skips login via
  `VITE_DEV_TOKEN`)
- **Analyst**: test-automation-engineer (Axel), combined analyst+implementer slot
- **Status**: ready-for-automation
- **Case-gate note**: case frontmatter carries `status: draft`,
  `execution_type: manual`. Per `.agents/test-automation.yaml` § `intake`,
  `draft` is intake-eligible. Proceeded to full live execution 2026-08-22.

## Preconditions
- User is logged in to Elitea (on localhost, `auth_state` skips login).
- Project `Private` (399) selected.
- **Credentials of at least three distinct types must exist** so the filter has
  something to narrow. Live-verified: `GET /configurations/types/{project}`
  returns ONLY the types actually present in the project (probe run: with one
  `s3_api_credentials` credential the panel showed exactly one chip; after
  seeding github/jira/confluence it returned
  `{"rows":["github","jira","s3_api_credentials","confluence"],"total":4}`).
  So the TYPES panel is data-derived — the test MUST seed its own typed
  credentials rather than rely on incidental project state.
- **At least one credential must exist at all** — a zero-credential project
  redirects `/credentials/all` → `/credentials/create-credential`
  (`CredentialsList.jsx`'s empty-project `useEffect`). Note the same guard
  explicitly skips the redirect while a type filter is active
  (`hasTypeFilter` short-circuit), so a filter that matches nothing does NOT
  redirect.

## Test Data

### generate-per-test (created in setup, deleted in teardown)
Three credentials, one per type the case names, created via
`credential_api.create_credential(payload)`:

| Type | Display Name (label) | `data` payload |
|---|---|---|
| `github` | `autotest_cred_type_github_<ts>` | `{"base_url": "https://api.github.com"}` |
| `jira` | `autotest_cred_type_jira_<ts>` | `{"base_url": "https://example.atlassian.net", "username": "…", "api_key": "…"}` |
| `confluence` | `autotest_cred_type_confluence_<ts>` | `{"base_url": "https://example.atlassian.net/wiki", "username": "…", "api_key": "…"}` |

- **API seeding is transit, not terminal substitution** (`.agents/testing.md`
  § Fidelity policy): the case's own observable is *which credentials the
  filter displays*, which the product computes server-side and renders itself.
  The case's step 1 is a bare precondition ("Ensure credentials of different
  types exist"), not a UI-create step — unlike ELITEA-1965, whose step 1 IS
  "Create credentials". Placeholder `username`/`api_key` values are dummy
  strings: no connection test is ever exercised by this case.
- **Test-data call (Hard Rule 10):** reuse-existing was checked first and
  rejected — the live project carries exactly ONE credential
  (`Bearer - Test Bot`, type `s3_api_credentials`), so Github/Jira/Confluence
  simply do not exist to filter on. Seed is required; it is minimal (3 rows)
  and torn down in a `finally`.
- Cleanup: `credential_api.delete_credential(id)` per seeded id in `finally`.

### reuse-existing
- `${TEST_USER}` — see `.agents/profile.md` § Roles & sample users.
- Whatever credentials already exist in the project — they are counted as the
  unfiltered baseline, never mutated.

## Test Steps

1. **Ensure credentials of different types exist** (case step 1) — seed the
   three typed credentials above.
   - **Verify**: `GET /configurations/types/{project}` (the panel's own data
     source) now lists `github`, `jira` and `confluence`; the credentials list
     page shows all three seeded cards.
2. **Navigate to `/credentials/all`** (case step 2).
   - **Verify**: the list page renders (`entity-card` visible); the right-hand
     TYPES panel renders one chip per type present — at minimum
     `tags-panel-chip-Github`, `tags-panel-chip-Jira`,
     `tags-panel-chip-Confluence`; the "Clear all" control
     (`tags-panel-clear-all`) is ABSENT (no filter active).
3. **Click the "Github" type chip** (case step 3).
   - **Verify**: URL becomes `/credentials/all?tags[]=Github`; exactly the
     Github-type credential(s) are displayed — the seeded Jira and Confluence
     cards are GONE (`to_have_count(0)`) and the seeded Github card is present;
     every rendered card's type badge (`entity-card-tag-chip`) reads `Github`;
     `tags-panel-clear-all` is now VISIBLE (system-produced "a filter is
     active" signal).
4. **Click the "Github" chip again to remove it, then click "Jira"**
   (case step 4 — "Click the Jira type filter (removing Github filter first)").
   - **Verify** after the de-select: URL returns to `/credentials/all` with no
     `tags[]` param.
   - **Verify** after the Jira click: URL becomes `/credentials/all?tags[]=Jira`;
     only the Jira-type credential(s) are displayed (seeded Github and
     Confluence cards `to_have_count(0)`); every card's type badge reads `Jira`.
5. **Remove the active type filter** (case step 5) — click `tags-panel-clear-all`.
   - **Verify**: URL returns to `/credentials/all` with no `tags[]` param;
     all three seeded credentials are visible again AND the card count is back
     to the pre-filter baseline captured in step 2; `tags-panel-clear-all` is
     ABSENT again.

### Interaction-discovery note (role-overrides.md ladder — not needed here)
The type chips are direct-activation controls: a single click mutates the URL
`tags[]` param synchronously (`useCredentialTypes.updateTypeInUrl` →
`navigate(...)`), which re-drives `useLoadAllCredentials` with a server-side
`type=` parameter. No debounce, no Enter, no submit control. Confirmed live on
all four clicks in this run — the ladder was not needed, but the mechanism is
recorded so nobody re-derives it.

## Expected Results
- The TYPES panel is **data-derived**: exactly the credential types present in
  the project, alphabetically sorted, one chip each.
- Clicking a type chip **narrows the list server-side** (`type=` query param on
  `GET /configurations/configurations/{project}`), not client-side.
- Selection is a **toggle** — clicking the selected chip again clears it.
- Removing all filters restores the full, unfiltered list.
- "Clear all" (`tags-panel-clear-all`) renders only while ≥1 type is selected.
- No console errors at any step. Only the #554 prompt_lib-404 filter is
  applied (closed 2026-08-11 as a local-UI/test-client artifact, pinned to
  that exact URL shape). The suite's `#518` `<CredentialsList>`-crash filter
  is deliberately NOT reused: #518 is CLOSED as NOT REPRODUCIBLE, so that
  signature is now a regression of the component under test.

## Coverage Map

### Axis 1 — Case coverage

| Case element | Expected result | Covered by (AFS step) | Asserted where | Disposition |
|---|---|---|---|---|
| Precondition: user logged in, project + mixed-type credentials exist | — | AFS § Preconditions + step 1 | `auth_state` fixture; step 1 seeds the 3 types and asserts the types endpoint lists them | asserted |
| 1 Ensure credentials of different types exist | list shows mixed types | AFS step 1 | step 1: all 3 seeded cards present on `/credentials/all` | asserted |
| 2 Navigate to the credentials list | list page loads | AFS step 2 | step 2: `entity-card` visible; TYPES chips for Github/Jira/Confluence present | asserted |
| 3 Click the "Github" type filter | only Github-type credentials displayed | AFS step 3 | step 3: Jira+Confluence cards `count()==0`, Github card visible, every badge == "Github", URL `?tags[]=Github` | asserted |
| 4 Click "Jira" (removing Github first) | only Jira-type credentials displayed | AFS step 4 | step 4: Github+Confluence cards `count()==0`, Jira card visible, every badge == "Jira", URL `?tags[]=Jira` | asserted |
| 5 Remove the active type filter | all credential types shown again | AFS step 5 | step 5: all 3 seeded cards visible, count back to the step-2 baseline, URL has no `tags[]` | asserted |
| Expected Final State: "filter narrows; removing restores" | — | AFS steps 3–5 | as above | asserted |
| Pass criterion: "all steps complete without errors" | — | all steps | console side-channel assertion at the end | asserted |

### Axis 2 — Analyst additions
- `tags-panel-clear-all` presence/absence asserted at steps 2/3/5 — *added: the
  case says "remove the active type filter" without naming HOW; the Clear-all
  control is the product's own affordance for it AND the only system-produced,
  non-CSS signal that a filter is active (the chip's own selected state is
  expressed purely as a background colour, no `data-*` attribute — see
  § Known Defects/Gaps #2).*
- Per-card **type badge** assertion (`entity-card-tag-chip` reads the filtered
  type) — *added: proves the filter narrowed by TYPE, not merely that the count
  dropped; a filter that returned an arbitrary single row would pass a
  count-only check.*
- Absence assertions (`to_have_count(0)`) on the two non-matching seeded cards —
  *added: "only X are displayed" is only proven by naming what must be gone.*
- Step-4 intermediate assertion that de-selecting Github clears the URL param —
  *added: the case's parenthetical "(removing Github filter first)" describes a
  toggle-off the case never verifies; a regression that made selection additive
  would otherwise silently pass step 4 (the list would show Github+Jira).*
- No console errors — *added, standard side-channel check.*

## Cleanup
1. `credential_api.delete_credential(id)` for each of the three seeded ids, in a
   `finally` block so it runs on assertion failure too.
2. Nothing else to clean: the type filter is URL-local and does not persist.

## Concrete Handles (discovered during exploration)

Locator policy: **testid-only** (`.agents/testing.md` § Locator policy).

| Element | Testid | Provenance | Fallback |
|---|---|---|---|
| Type filter chip (right TYPES panel) | `tags-panel-chip-{TypeLabel}` — dynamic, e.g. `tags-panel-chip-Github` / `-Jira` / `-Confluence`. Label comes from `CredentialNameHelpers.extraCredentialName(type)`: `github`→`Github`, `s3_api_credentials`→`S3 api credentials` | **on-main ✓** (`src/components/Categories.jsx`, verified 2026-08-22 after `git fetch origin`) | none |
| "Clear all" filters button | `tags-panel-clear-all` | **on-main ✓** | none |
| TYPES panel empty state | `tags-panel-empty-state` | on-`automation/testids` only (not referenced by this test) | none |
| Credential card container | `entity-card` | **on-automation/testids only** | none |
| Credential card name | `entity-card-name` | **on-main ✓** | none |
| Credential card type badge | `entity-card-tag-chip` | on-`automation/testids` (already used by `CredentialsListPage.get_type_badge()`) | none |

**No `add-data-testid` work was required for this case** — every handle it
touches already existed.

### Page object impact
`automation/pages/credentials_list_page.py` gains, as class-level fields /
constants:
```python
TYPE_FILTER_CHIP = '[data-testid="tags-panel-chip-{}"]'
tags_clear_all_button = LocatorDescriptor(testid="tags-panel-clear-all", ...)
```
plus `click_type_filter(type_label)` (click + wait for the filtered
`configurations` GET), `clear_all_type_filters()` and `get_visible_type_badges()`.

## Network Behavior
- `GET /api/v2/configurations/configurations/{project}?...&type=<type>&section=credentials&section=storage`
  — fires on each chip click; `type` carries the RAW type key (`github`), not
  the chip label (`Github`): `useLoadAllCredentials` maps label→type via the
  `/configurations/types/{project}` response before querying. Wait on this
  response, never a sleep.
- `GET /api/v2/configurations/types/{project}` — the TYPES panel's own data
  source; returns only types present in the project.

## Known Defects Found During Exploration
1. **None.** All five case steps behaved exactly as the case specifies,
   first try, 1/1.
2. **Gap (not a defect, not implementer work for this case):** the type chip's
   *selected* state is expressed only as a CSS `background` on `StyledChip`
   (`src/components/DataDisplay/StyledChip.jsx` — `isSelected` is a styled-prop,
   filtered out of the DOM). There is no `data-selected` / `aria-pressed`
   attribute, so per `.agents/testing.md` § Locator policy ("state via `data-*`
   attributes") the chip's own selected state is **not assertable** by a
   testid-only test. This case does not need it — the case's observables are the
   filtered list and the restored list, and the `tags-panel-clear-all` control
   covers "a filter is active". Recorded so a future case that DOES need chip
   state knows it is a UI change, not a locator problem.

### Implementer-phase addendum — discovered during automation

3. **Render race on filter REMOVAL (not a defect — a wait-strategy fact).**
   The list `GET` that follows a filter removal (chip toggle-off or
   "Clear all") resolves *before* React has re-rendered the cards, so a
   synchronous read immediately after `wait_for_network()` can legitimately
   observe an EMPTY grid — this is exactly what the first implementation run
   hit at step 5 (`got: []`). Settled deterministically in
   `CredentialsListPage._settle_unfiltered_list()`: network settle **plus**
   `entity_card.first.wait_for(state="visible")`. Never a sleep. The
   *applying* direction (chip click → filtered list) did not show this — the
   `type=`-predicated response wait plus network settle was sufficient.

## Blocked Steps
None — all 5 case steps executed and observed live end-to-end on 2026-08-22.

## Automation Hints
- Framework: Playwright + pytest (`.agents/testing.md`).
- Markers: `ui`, `credentials`, `p2`, `regression`.
- Seed via `credential_api.create_credential(payload)` (see § Test Data);
  delete in `finally`.
- Wait strategy: `page.expect_response` on the `configurations` GET carrying
  `type=`; then `wait_for_network()` before reading card state (the React
  re-render lands a tick after the response, exactly as
  `CredentialsListPage.search()` already handles).
- Console filter: reuse ONLY this suite's `#554` prompt_lib-404 filter —
  `/credentials/all` is loaded here too. Do NOT copy forward the `#518`
  `<CredentialsList>`-crash filter: #518 is CLOSED (NOT REPRODUCIBLE,
  2026-08-11) and it would mask a crash of the component under test.
  `tests/unit/test_credentials_console_filters_scope.py` pins this.
