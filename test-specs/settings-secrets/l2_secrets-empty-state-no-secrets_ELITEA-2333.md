# Test Case: Secrets page shows the empty state when no secrets exist

## Metadata
- **TMS ID**: ELITEA-2333
- **Source case**: `.agents/automation/settings-w05/cases/ELITEA-2333.md` (intake snapshot)
- **Priority**: l2 (case frontmatter `priority: medium`)
- **Environment Explored**: local (`http://localhost:5173`, DEV backend), all 5 selectable projects
- **User set**: `${TEST_USER}` (auth via `auth_state` / `VITE_DEV_TOKEN` on localhost)
- **Analyst**: test-automation-engineer (Axel), combined slot, batch `settings-w05`, 2026-08-28
- **Status**: **blocked** — the case's precondition ("a project with no secrets") still
  cannot be produced honestly for the shared test user
- **Surface digest**: `test-specs/settings-secrets/_surface.md`
- **Duplicate scenario of**: **ELITEA-2249**
  (`l2_secrets-empty-state-no-secrets_ELITEA-2249.md`, parked `blocked` 2026-08-24 for
  the same reason). This AFS is NOT `already-covered`: `already-covered` may only target
  a spec **merged to `origin/automation/base`**, and ELITEA-2249 produced no spec at all.

## Why this is blocked (read this first)

The case's *observable* is trivial and confirmed live. What cannot be produced is its
*precondition*. **Re-verified 2026-08-28** (not copied from ELITEA-2249 — every project
re-probed this session):

```
GET {ELITEA_API_BASE}/secrets/secrets/default/{project_id}
  399 Private              -> 200, 121 secrets
  400 UI Testing           -> 200,   4 secrets
  406 Bugs & Features      -> 403  {"ok": false, "error": "access_denied", ...}
  25  Elitea Development   -> 403
  471 Elitea Testing Team  -> 403
```

**There is no project this user can list secrets in AND that is empty.** The three
projects that *look* empty in the UI are permission artefacts, not empty projects:
`SecretsContent.jsx` skips the query entirely
(`skip: !projectId || !checkPermission(PERMISSIONS.secrets.list)`), `data` stays
`undefined`, the `= []` default drives `GridTableContainer`'s empty branch, and **zero
network requests fire** (re-confirmed live this session — see § Live evidence).
Asserting the case there would assert a **different scenario** (no access) while
claiming the case's scenario (no data) — a wrong-interface precondition under
`.agents/testing.md` § Fidelity policy. Filed as bug **#1773**.

Every honest alternative route was re-checked this session and all still fail:

1. **Empty a listable project.** 400 has 4 secrets and 399 has 121; the API returns
   only names, never plaintext values, so a test **cannot restore what it deletes**.
   399 is the whole suite's shared secret store. Destroying either is not a precondition.
2. **Create a throwaway project.** The project selector offers 5 fixed options and no
   create affordance for this user — project creation is not reachable from the UI.
3. **A second identity.** `auth_state_user_b` (`automation/fixtures/session_fixtures.py:133`)
   `pytest.skip`s on localhost by design.
4. **Filter the table to zero rows** renders the *same* `No secrets` branch, but that is
   "no match", not "no secrets configured" — and it cannot exercise case step 1 at all.
5. **Fabricating the list response** (`route.fulfill` an empty array) is a **terminal
   substitution**: the case's entire observable would be read off the test's own
   payload. Forbidden — the case text asks for no simulation
   (`.agents/testing.md` § Fidelity policy).

## Live evidence gathered this session

Executed against project 471 (403 path) purely to *characterise* the state — this
observation is explicitly **not** usable as the case's evidence:

| Observation | Value |
|---|---|
| `secrets-page-title` | present, text `Secrets` |
| `secrets-add-button` | present and **enabled** |
| `secret-row` count | 0 |
| empty text rendered | `No secrets` |
| secrets-list requests fired | **none** (query skipped client-side) |
| console errors on mount | **144** `Maximum update depth exceeded` (#1203, unbounded variant) |

## Preconditions (as they would be, once unblocked)
- User logged in (`auth_state`).
- Selected project must be one the user **can list secrets in** (API `200`) **and** that
  contains zero secrets. No such project exists today.

## Test Data
### reuse-existing
None — the case is about the absence of data.

## Test Steps (would-be; step 1 cannot be satisfied honestly)
1. Select a project with no secrets configured.
   - **BLOCKED** — see § Why this is blocked.
2. Navigate to Settings → Secrets (`/settings/secrets`).
   - **Verify**: `secrets-page-title` visible, text `Secrets`. *(confirmed live)*
3. Verify an empty-state message or illustration is shown (not a blank area or error).
   - **Verify**: exactly zero `[data-testid="secret-row"]`, and `No secrets` rendered
     inside the table container.
   - ⚠ The empty message has **no testid** — a bare
     `<span class="MuiTypography-root …">` produced by the SHARED `GridTableContainer`
     (`GridTableContainer.jsx:37-43`, `emptyMessage` prop). Needs
     `testid needed: grid-table-empty-message`, threaded as a **caller-supplied prop**
     from `SecretsTable.jsx` — never hardcoded in the shared component
     (`.agents/testing.md` § shared components).
   - **Illustration**: there is none on this surface. The case's "or illustration" is
     satisfied by the message; do not look for an image (contrast Personal Tokens,
     which does render an `EmptyStatePage` image — ELITEA-2250).
4. Verify the "+" button is still visible and accessible.
   - **Verify**: `secrets-add-button` visible **and enabled**. *(confirmed live)*

## Handles Reference
| Element | Primary handle (testid-only) | Provenance | Notes |
|---|---|---|---|
| Page title | `secrets-page-title` | **on-main ✓** | `DrawerPageHeader titleTestId` |
| Secret row | `secret-row` | **on-main ✓** | count === 0 is the empty proof |
| Add ("+") button | `secrets-add-button` | **on-main ✓** | enabled in the empty state |
| Pagination info | `secrets-pagination-info` | **on-main ✓** | **absent** when the table is empty — do not assert |
| Empty message `No secrets` | **testid needed: `grid-table-empty-message`** | needs-adding | shared `GridTableContainer`; caller-supplied prop from `SecretsTable.jsx` |

## Coverage Map

### Axis 1 — every element of the TMS case
| Case element | Expected result (per live product) | Covered by | Asserted where | Disposition |
|---|---|---|---|---|
| Precondition: user logged in | authenticated session | `auth_state` | fixture | covered |
| Step 1: navigate to Settings → Secrets **in a project with no secrets** | project switch, then `/settings/secrets` renders | — | — | **blocked** — no such project exists for this user |
| Step 2: empty-state message or illustration shown, not blank/error | plain `No secrets`; no illustration on this surface | — | — | **blocked** on the precondition; observable itself confirmed live |
| Step 3: "+" button still visible and accessible | `secrets-add-button` visible + enabled | — | — | **blocked** on the precondition; observable itself confirmed live |
| Expected Final State: "+" visible and accessible | as step 3 | — | — | **blocked** |

### Axis 2 — would be asserted beyond the case
| Observable | Why |
|---|---|
| the secrets list request actually fired and returned `200` with zero items | the whole reason this is blocked — an empty table produced by a *skipped* query is a different state (#1773). Any future implementation must prove the endpoint answered, not that the table happened to be empty |
| no console errors on the page | project standard — and this surface carries the OPEN render-loop defect #1203, unbounded exactly in the skipped-query state |

## Known Defects / Clarifications
- **#1773 (bug, OPEN)** — a project the user cannot list secrets in (403) renders the
  ordinary `No secrets` empty state with an **enabled "+"**, indistinguishable from a
  genuinely empty project. This is what removes the last candidate precondition.
- **#1203 (bug, OPEN)** — `Maximum update depth exceeded` on mount; **unbounded** in the
  skipped-query state (144 errors measured this session on project 471).

## Blocked Steps
- **Step 1 — "a project with no secrets"** needs a human decision, unchanged from
  ELITEA-2249: (a) provision a disposable/empty project the test user can list secrets
  in, or (b) rule that a filtered-to-zero variant is an acceptable rewrite of the case
  (which would make the case text stale and want a TMS edit), or (c) move the case to a
  deployed env with a clean tenant. Everything downstream of step 1 is confirmed and
  ready; the AFS is complete except for that one input.
