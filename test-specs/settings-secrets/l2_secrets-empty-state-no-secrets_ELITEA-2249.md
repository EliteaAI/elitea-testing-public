# Test Case: Settings → Secrets shows the empty state when no secrets exist

## Metadata
- **TMS ID**: ELITEA-2249
- **Priority**: l2 (case priority `medium`)
- **Environment Explored**: local (`http://localhost:5173`, `EliteaAI/EliteaUI` on `automation/testids`, DEV backend)
- **User set**: `${TEST_USER}` (auth via `auth_state` / `VITE_DEV_TOKEN` on localhost)
- **Analyst**: qa-engineer (Sage), batch `settings-w01`, 2026-08-24
- **Status**: **blocked** — the case's precondition ("a project with no secrets configured") cannot be produced honestly for the shared test user
- **Surface digest**: `test-specs/settings-secrets/_surface.md`
- **Filed**: bug **#1773** (permission-403 renders as the empty state), new-occurrence comment on **#1203** (unbounded render loop in that same state)

## Why this is blocked (read this first)

The case's *observable* is trivial and was confirmed live. What cannot be produced is
its *precondition*. Measured live 2026-08-24 — every project the shared test user can
select, and what `GET {ELITEA_API_BASE}/secrets/secrets/default/{project_id}` answers:

| Project | id | secrets API | Secrets table |
|---|---|---|---|
| `Private` (personal) | 399 | `200`, **120** secrets | 10 rows / page, "1 - 10 of 120" |
| `UI Testing` | 400 | `200`, **4** secrets | 4 rows, "1 - 4 of 4" |
| `Bugs & Features` | 406 | **`403`** | "No secrets" |
| `Elitea Development` | 25 | **`403`** | "No secrets" |
| `Elitea Testing Team` | 471 | **`403`** | "No secrets" |

So the three projects that *look* empty are permission artefacts, not empty projects:
`SecretsContent.jsx` skips the query entirely
(`skip: !projectId || !checkPermission(PERMISSIONS.secrets.list)`), `data` stays
`undefined`, and the `= []` default drives `GridTableContainer`'s empty branch. No
request is issued at all. Asserting the case there would assert a **different
scenario** (no access) while claiming the case's scenario (no data) — a
wrong-interface precondition under `.agents/testing.md` § Fidelity policy.

The remaining honest routes were checked and all fail:

1. **Empty a listable project.** Project 400 has 4 secrets; deleting them is
   *irreversible* — the API returns only names, never plaintext values, so a
   test cannot restore what it deletes. Project 399 (120 secrets) is the whole
   suite's shared secret store. Destroying either is not a test precondition.
2. **Create a throwaway project.** The project selector offers no create
   affordance for this user (5 fixed projects, no "+ New project" item); project
   creation is not reachable from the UI under test.
3. **A second identity.** `auth_state_user_b` exists
   (`automation/fixtures/session_fixtures.py:133`) but `pytest.skip`s on
   localhost by design ("Multi-user tests require deployed environment").
4. **Filter the table to zero rows** (search for a non-matching name) renders the
   *same* `"No secrets"` empty branch — but again that is "no match", not "no
   secrets configured". It also cannot exercise step 1 of the case at all.
5. **Fabricating the list response** (`route.fulfill` an empty array) is a
   **terminal substitution** — the case's entire observable would be read off the
   test's own payload. Forbidden; the case text asks for no simulation.

**Decision for the human (per `.agents/testing.md` § Fidelity policy):** this needs
either (a) a dedicated, disposable project in which the test user can list/create
secrets and which is guaranteed empty at test start, or (b) a ruling that the
filtered-to-zero variant is an acceptable rewrite of the case (which would make the
case text stale and want a TMS edit), or (c) the case is deployed-env-only with a
clean tenant. Not an implementation detail — routed, not engineered around.

## Preconditions (as they would be, once unblocked)
- User logged in (`auth_state`).
- Selected project must be one the user **can list secrets in** (API `200`) **and**
  which contains zero secrets. No such project exists today (table above).

## Test Data
### reuse-existing (would be)
None — the case is about the absence of data.

## Test Steps (executed live where possible; step 1 could not be satisfied honestly)
1. Select a project with no secrets configured.
   - **Blocked** — see § Why this is blocked. Executed against project 471 only to
     characterise the state; the observation is *not* usable as the case's evidence.
2. Navigate to Settings → Secrets (`/settings/secrets`).
   - **Verify**: `secrets-page-title` visible, text `Secrets`. *(confirmed live on
     every project, including the zero-row ones)*
3. Verify an empty-state message is shown (not a blank area, not an error).
   - **Verify**: exactly zero `[data-testid="secret-row"]`, and the empty message
     `No secrets` is rendered inside the table container.
   - ⚠ **The empty message has NO testid** — plain
     `<span class="MuiTypography-root ...">No secrets</span>` inside a `Box`
     (`GridTableContainer.jsx:37-43`, `emptyMessage` prop). Under the testid-only
     locator policy this needs `testid needed: grid-table-empty-message`, wired as a
     caller-supplied prop on the SHARED `GridTableContainer` (never hardcoded there —
     `.agents/testing.md` § shared components), passed by `SecretsTable.jsx`.
   - **Illustration**: there is none on this surface. The case's "or illustration" is
     satisfied by the message; do not look for an image (contrast Personal Tokens,
     which does render an `EmptyStatePage` image — ELITEA-2250).
4. Verify an "Add Secret" / "+" button is visible and accessible.
   - **Verify**: `secrets-add-button` visible **and enabled**. *(confirmed live: the
     header renders normally in the zero-row state, and the button is enabled — see
     bug #1773, which is exactly this button being offered on a 403 project.)*

## Handles Reference
| Element | Primary handle (testid-only) | Provenance | Notes |
|---|---|---|---|
| Page title | `secrets-page-title` | **on-main ✓** (verified `git grep` on `origin/main -- src/`, fetched 2026-08-24) | `DrawerPageHeader titleTestId` |
| Secret row | `secret-row` | **on-main ✓** | count === 0 is the empty proof |
| Add ("+") button | `secrets-add-button` | **on-main ✓** | enabled in the empty state |
| Pagination info | `secrets-pagination-info` | **on-main ✓** | absent when the table is empty — do not assert |
| Empty message "No secrets" | **testid needed: `grid-table-empty-message`** | needs-adding | shared `GridTableContainer`; add as a caller-supplied prop from `SecretsTable.jsx` |

*(Provenance verified with `cd ../EliteaUI && git fetch origin` in the same block; the
four existing testids resolve on `origin/main`.)*

## Coverage Map

### Axis 1 — every element of the TMS case
| Case element | Expected result (per live product) | Covered by | Asserted where | Disposition |
|---|---|---|---|---|
| Precondition: logged in | authenticated session | `auth_state` | fixture | covered |
| Step 1: navigate to a project with no secrets configured | project switch via `project-selector-trigger-combobox` | — | — | **blocked** — no such project exists for this user (§ Why this is blocked) |
| Step 2: navigate to Settings → Secrets | `/settings/secrets` renders, title "Secrets" | Step 2 | `secrets-page-title` | covered (confirmed live) |
| Step 3: empty-state message or illustration shown, not blank/error | plain "No secrets" message; NO illustration on this surface | Step 3 | row count 0 + empty-message testid (to add) | **blocked** on the precondition; observable itself confirmed live |
| Step 4: "Add Secret"/"+" visible and accessible | `secrets-add-button` visible + enabled | Step 4 | visibility + enabled | covered (confirmed live) |
| Expected Final State: "+" visible and accessible | as step 4 | Step 4 | same | covered |

### Axis 2 — asserted beyond the case
| Observable | Why |
|---|---|
| no console errors on the page | project standard — and this surface has an OPEN render-loop defect (#1203) whose severity depends on which project you land on; the axis is the early warning |
| the secrets list request actually fired and returned `200` | the whole reason this case is blocked: an empty table that came from a *skipped* query is a different state. Any future implementation must prove the list endpoint answered `200` with zero items, not that the table happened to be empty |

## Known Defects / Clarifications
- **#1203 (bug, OPEN)** — Settings → Secrets fires React `Maximum update depth
  exceeded` on mount. New occurrence + worse variant recorded there this session:
  **bounded** (5 errors) on a listable project, **unbounded** (140 in 6 s, ~28k over
  a few minutes) on a project whose query is skipped. Any test asserting "no console
  errors" on this page must account for it.
- **#1773 (bug, filed this session)** — a project the user cannot list secrets in
  (`403`) renders the ordinary "No secrets" empty state **with an enabled "+"**,
  indistinguishable from a genuinely empty project. This is what removes the last
  candidate precondition for this case.

## Blocked Steps
- **Step 1 — "a project with no secrets configured".** Needs a human decision:
  provision a disposable/empty project for the test user (preferred), or accept a
  rewritten case (filter-to-zero), or move the case to a deployed env with a clean
  tenant. Everything downstream of step 1 is confirmed and ready; the AFS is
  complete except for that one input.
