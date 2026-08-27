# Test Case: Secrets page shows an error state on network failure, and recovers

## Metadata
- **TMS ID**: ELITEA-2349
- **Source case**: `.agents/automation/settings-w05/cases/ELITEA-2349.md` (intake snapshot)
- **Priority**: l3 (case frontmatter `priority: medium`) → **pytest marker `@pytest.mark.p2`**
- **Environment Explored**: local (`http://localhost:5173`, project `Private` / 399, 121 secrets)
- **User set**: `${TEST_USER}`
- **Analyst**: test-automation-engineer (Axel), combined slot, batch `settings-w05`, 2026-08-28
- **Status**: **ready-for-automation**
- **Surface digest**: `test-specs/settings-secrets/_surface.md`
- **Filed**: **#1910** — `[BUG][ELITEA-2349]` the transport-failure toast reads a bare
  `Unknown error` (`buildErrorMessage` has no `FETCH_ERROR` branch). Does **not** hold
  this spec red — see § Fidelity Declaration and § Implementer notes.

## Fidelity Declaration (`.agents/testing.md` § Fidelity policy)

| What is substituted | Transit or terminal | Authority |
|---|---|---|
| The **transport** of `GET /secrets/secrets/default/{project_id}` is failed via `page.route(..., route.abort("failed"))` for the duration of step 1-2 | **Case-authorised simulation** — the case's own step 1 says *"Navigate to Settings → Secrets **on a throttled or offline connection**"*. The offline condition IS the case's stated precondition. | Quoted case line above (`.agents/automation/settings-w05/cases/ELITEA-2349.md` § Steps, row 1) |

**Nothing the case observes is fabricated.** The error message, its severity, the page
shell and the recovered list are all produced by the product in response to a real
transport failure — the test authors **no response body**. `route.abort()` produces a
genuine `FETCH_ERROR` in RTK Query, exactly as a dropped connection would; it is the
network condition being simulated, not the observable.

Step 3-4 (**restore and reload**) run with the route **unrouted** — the recovery half
asserts against a live `200` and the product's own payload, with **zero** interception
in play.

## Preconditions
- User logged in (`auth_state`).
- Project `Private` (399) — user holds `configuration.secrets.secret.list`, **121
  secrets live** (re-verified 2026-08-28). A populated project is required so step 4's
  "the secrets list loads correctly" is non-vacuous.
- **Read-only case.** Nothing is created, edited or deleted.

## Test Data
### reuse-existing
- The live secret set, read-only. The recovery assertion is **relational**: the rendered
  row count is compared to the **live API response's own** item count (capped at the
  page size the product paginates to), never to a hardcoded number. A literal `121`
  would break the day anyone adds a secret.

## Test Steps (all executed live 2026-08-28, framework run)

1. **Navigate to Settings → Secrets with the connection down.** Route
   `**/secrets/secrets/default/**` to `abort("failed")`, then `goto /settings/secrets`.
   - **Verify**: the page shell renders — `secrets-page-title` visible with text
     `Secrets`, and `secrets-add-button` visible. *(This is the case's "not a blank
     page".)*
   - *Live:* title present, add button present **and enabled**, 0 rows, body text 335
     chars of full app chrome.

2. **Verify a user-friendly error message is shown (not a blank page or raw stack trace).**
   - **Verify**: the toast is present **with error severity**, located as
     `[data-testid="toast-alert"][data-severity="error"]` — `Toast.jsx` renders
     `data-severity={severity}` alongside the testid, so state is asserted by
     **attribute filter on a stable testid**, the shape `.agents/testing.md`
     § Locator policy requires (the product classified this as an **error**, not
     info — contrast #1121, where a toast used the wrong severity).
   - **Verify**: `toast-message` text is **non-empty**.
   - **Verify (the "not a raw stack trace" half, asserted as an invariant on both the
     toast text and the Settings content pane `settings-content`)**: contains none of
     `TypeError`, `Uncaught`, `at Object.`, `.jsx:`, `.js:`, `\n    at ` — i.e. no
     stack frame, no exception class, no source-file coordinate leaked to the user.
     (Scoped to `settings-content`, not a raw `body` handle: a React error boundary
     renders inside that pane, and it is a real app testid.)
   - *Live:* toast present, `MuiAlert-colorError`, message = `Unknown error`, no stack
     marker anywhere in the body, toast still present after a further 6 s (error toasts
     do not fast-auto-hide).
   - ⚠ **Why the literal string is not asserted:** `Unknown error` is the product's
     current text and it is **not** user-friendly (filed as **#1910** —
     `buildErrorMessage` has no `FETCH_ERROR` branch and falls through to `undefined`).
     Pinning the literal would (a) make the spec go red the day the product *improves*
     the message, which is backwards, and (b) encode a defect as the expected contract.
     The case's own criterion is *"a user-friendly error message is shown (not a blank
     page or raw stack trace)"* — the spec asserts exactly that shape: an error-severity
     toast, non-empty text, no stack trace. That is the honest reading of the case, and
     it is strictly stronger than "something rendered".

3. **Restore the connection and reload.** `page.unroute(...)`, then `reload()` while
   waiting for the real secrets-list response.
   - **Verify**: the secrets-list `GET` returns **`200`** and its JSON body is a
     non-empty list. *(Proves the request genuinely fired and was answered by the
     backend — the #1773 trap is a table that looks fine because no query ran at all.)*
   - *Live:* status `200`, 121 items.

4. **Verify the page recovers and the secrets list loads correctly.**
   - **Verify**: `secret-row` count `== min(len(api_body), 10)` — the product paginates
     at 10 rows/page by default, so the rendered count is derived from the **live API
     payload**, not hardcoded.
   - **Verify**: every rendered row's name appears in the API response's name set —
     the UI carried the backend's data through faithfully, it did not render leftovers.
   - **Verify**: the error toast is **gone** (`toast-alert` count 0) — recovery clears
     the failure state rather than stacking on it.
   - *Live:* 10 rows rendered from 121 API items, toast count 0.

## Handles Reference
| Element | Primary handle (testid-only) | Provenance | Notes |
|---|---|---|---|
| Page title | `secrets-page-title` | **on-main ✓** — prop indirection, `titleTestId="secrets-page-title"` at `SecretsContent.jsx:143` | `DrawerPageHeader titleTestId` |
| Add ("+") button | `secrets-add-button` | **on-main ✓** — object literal, `testId: 'secrets-add-button'` at `SecretsContent.jsx:158` | visible in the failure state |
| Secret row | `secret-row` | **on-main ✓** — `SecretsTable.jsx:569` | 0 in failure state, `min(api_count, 10)` after recovery |
| Toast container | `toast-alert` | **on-main ✓** (`src/components/Toast.jsx:60`) | severity read from its class list |
| Toast message | `toast-message` | **on-main ✓** (`src/components/Toast.jsx:74`) | the text asserted for shape |
| Toast severity filter | `TOAST_ALERT_SEVERITY` = `[data-testid="toast-alert"][data-severity="{}"]` | **on-main ✓** (`data-severity` at `src/components/Toast.jsx:61`) | class constant on `SecretsPage`; state via `data-*` filter, never a state-switched testid |
| Settings content pane | `settings-content` | **on-`automation/testids` only (awaiting human promotion to `main`)** — `src/[fsd]/pages/settings/index.jsx:268`, EliteaAI/EliteaUI@e1e031a1 | scope for the no-stack-trace check; already used by `SettingsDrawerPage.settings_content` |

*(Provenance **re-verified 2026-08-28, fix round 3** — `cd ../EliteaUI && git fetch origin`
in the same command block, then the two-stage grep of `.agents/workflow.md` § Closure
record, against `origin/main` = `f27645bc` and `origin/automation/testids` = `249c0186`.
**Every row above re-confirmed unchanged**; only source anchors and the introducing commit
were added. `Toast.jsx` is byte-identical on both refs (`git diff origin/main
origin/automation/testids -- src/components/Toast.jsx` → empty), so its three rows are
on-`main` at the exact lines cited. Note `data-severity={severity}` at `:61` carries no
`data-testid` token on its own line, so a naive two-stage grep keyed on that testid
reports a **false negative** for it — it was confirmed by reading the file, not by grep.)*

**No new testid is needed.** `toast-alert` / `toast-message` already exist on `main`.
`settings-content` does **not** — this case is green on localhost and **RED on any
deployed env** until a human cherry-picks EliteaAI/EliteaUI@e1e031a1 to `main`, and the
closure record's promotability row must say so.

## Implementer notes
- `SecretsPage.navigate()` **cannot be reused for step 1** — it waits for
  `secret_row.first` to become visible, which never happens in the failure state. Add an
  **additive** page-object method (e.g. `navigate_expecting_no_rows()`) that goes to the
  route and waits on the page shell instead. Do not modify `navigate()` — it has many
  merged callers (`.agents/role-overrides.md` § additive-only).
- Toast severity: **use the `data-severity` attribute filter**, not a MUI class regex.
  `Toast.jsx:61` renders `data-severity={severity}` next to the testid, so
  `SecretsPage.TOAST_ALERT_SEVERITY` (`[data-testid="toast-alert"][data-severity="{}"]`)
  is the compliant class-constant shape. *(Superseded during implementation — the
  original note here proposed a `MuiAlert-colorError` class assertion before the
  `data-severity` attribute was found.)*
  Call it through `SecretsPage.toast_alert_with_severity(severity)`, the accessor that
  already wraps that constant — a spec must never build the locator itself
  (`.agents/conventions.md` § Hard don'ts; review finding, fix round 1).
- Read the recovered rows' names with `SecretsPage.get_row_names()` — it already strips
  and preserves rendered order. Re-implementing it inline in the spec was the second
  half of the same review finding.
- **Grep the page object for the attribute NAME before declaring a handle**, not just
  for the testid: `SecretsPage` is >1000 lines and a sibling unit had already declared
  `toast_alert` / `toast_message` / `TOAST_ALERT_SEVERITY` ~120 lines above the point
  this branch appended its own copies (review finding, fix round 2).
- `route.abort("failed")` (not `fulfill`) — nothing is authored, only the transport is cut.
- **`page.unroute` before the reload**, and let `expect_response` capture the real `200`
  so the recovery assertions read the product's own payload.
- **#1203 console noise**: the spec visits `/settings/secrets` on project 399, which
  fires the *bounded* mount burst (59 errors measured in the failure state this session).
  A console-error axis on this spec would be pure #1203 noise and is **deliberately
  omitted** — see § Deliberately NOT asserted.

## Deliberately NOT asserted (and why)
- **A console-error axis.** Measured live this session: **59** `Maximum update depth
  exceeded` errors during the failure state alone (#1203, OPEN). Adding the axis would
  make this spec a permanent duplicate red for a defect that already has its own
  soft-asserted coverage in `test_secrets_page_layout.py` (ELITEA-2330). Recording the
  count here instead keeps the evidence without the noise.
- **The literal toast string `Unknown error`.** See step 2's ⚠ note and **#1910**.
- **A retry affordance.** The product renders none; asserting its absence would encode a
  gap the case never asked about.

## Coverage Map

### Axis 1 — every element of the TMS case
| Case element | Expected result (per live product) | Covered by | Asserted where | Disposition |
|---|---|---|---|---|
| Precondition: user logged in | authenticated session | `auth_state` | fixture | covered |
| Step 1: navigate to Settings → Secrets on a throttled/offline connection; "target page/section loads successfully" | the page **shell** loads (title + "+"), the table cannot populate | Step 1 | `secrets-page-title` visible + text `Secrets`; `secrets-add-button` visible | **asserted** |
| Step 2: a user-friendly error message is shown (not a blank page or raw stack trace) | error-severity toast with non-empty text; no stack trace anywhere | Step 2 | `toast-alert` visible + `MuiAlert-colorError`; `toast-message` non-empty; no stack markers in toast text or page body | **asserted** (shape, not literal — see step 2 ⚠ and #1910) |
| Step 3: restore connection and reload | the secrets-list `GET` fires and answers `200` | Step 3 | response status `200`, body a non-empty list | **asserted** |
| Step 4: the page recovers and the secrets list loads correctly | rows render from the live payload; error toast clears | Step 4 | `secret-row` count `== min(len(body), 10)`; every rendered name ∈ API name set; `toast-alert` count 0 | **asserted** |
| Expected Final State: page recovers, list loads correctly | as step 4 | Step 4 | same | **asserted** |

### Axis 2 — asserted beyond the case
| Observable | Why |
|---|---|
| The toast's **severity** is `error`, not info/warning (via `data-severity="error"`) | the case says "error message"; a blue info toast for a failed load would satisfy a text-only check while misinforming the user (#1121 is that exact defect on another surface) |
| The failure-state page still renders its **shell** (title + "+") | this is the case's "not a blank page" made mechanical — a whole-page crash and a graceful error look identical to a toast-only assertion |
| The recovered rows' names are **a subset of the live API response's names** | proves the UI carried the backend's data through rather than re-rendering stale/leftover state; a bare count check would pass on stale rows |
| The list response is asserted `200` **with items**, not just "rows appeared" | the #1773 trap — on this surface a table can look settled because the query never ran. Proving the endpoint answered is what makes step 4 real |

## Known Defects / Clarifications
- **#1910 (bug, filed this session)** — the transport-failure toast reads a bare
  `Unknown error`; `buildErrorMessage` (`src/common/utils.jsx:146-184`) has no
  `FETCH_ERROR` / `TIMEOUT_ERROR` / `PARSING_ERROR` branch and falls through to
  `err?.data` → `undefined`. Shared helper, so every surface shows the same. Isolated,
  does not block this case — the spec asserts the case's stated shape and passes.
- **#1203 (bug, OPEN)** — `Maximum update depth exceeded` on Secrets mount; 59 errors
  measured in the failure state. Deliberately outside this spec's assertions.
- **#1773 (bug, OPEN)** — unrelated 403 path, but the reason step 3 asserts the response
  status rather than trusting the rendered table.

## Implementation outcome (test-automation-engineer, 2026-08-28)

Shipped as
`automation/tests/ui/admin/test_secrets_error_state_on_network_failure.py::TestSecretsErrorStateOnNetworkFailure::test_secrets_error_state_on_network_failure_and_recovery`.
Green first run, **0 reruns** (2 passed in 27.67 s alongside ELITEA-2348).

Fix round 1 replaced the two spec-built locators with the page object's existing
`toast_alert_with_severity()` / `get_row_names()` accessors; both are pinned by
`automation/tests/unit/test_secrets_access_and_error_spec_invariants.py`.

Fix round 2 removed three page-object members this branch should never have added:
`toast_alert`, `toast_message` and `TOAST_ALERT_SEVERITY` **already existed on
`SecretsPage`**, contributed by a sibling settings-w05 unit that merged into the batch
trunk before this branch was cut. Python keeps the LAST definition, so the branch's
thinner copies silently shadowed the richer originals (severity auto-hide durations,
the secrets-flow message catalogue). Ruff, the reviewer's locator grep and a green run
are all blind to this class — an AST duplicate-member walk is the only cheap detector,
and it is now pinned by
`test_secrets_page_defines_every_member_once`.

`SecretsPage`'s net gain from this branch is therefore **two additive members** —
`navigate_expecting_no_rows()` and the `settings_content` descriptor. `navigate()` and
every pre-existing member are untouched; the only `-` lines on
`pages/secrets_page.py` are the three shadowing duplicates this round deleted.

## Blocked Steps
- None.
