# Test Case: Expired tokens show ⊗ icon and active tokens show ✅ icon with remaining days

## Metadata
- **TMS ID**: ELITEA-2284
- **Source case**: `.agents/automation/elitea-2284/cases/ELITEA-2284.md`
  (snapshot; TMS module `settings-personal-tokens`)
- **Linked Story**: EliteaAI/elitea-testing-public#792 (tracking issue)
- **Priority**: l3 (medium, per case frontmatter `priority: high` — note: case
  frontmatter says `priority: high` but body doesn't otherwise argue urgency;
  siblings ELITEA-2277/2280 on the same module both used `l3`/`p2` for
  `medium`-labelled cases — this case's frontmatter genuinely says `high`, so
  **l2** is used here, one notch above its siblings, per the frontmatter value
  actually present)
- **Environment Explored**: local (`http://localhost:5173`, EliteaUI
  `automation/testids` branch → DEV backend, project `Private` /
  `${ELITEA_PROJECT_ID}` = 399)
- **User set**: `${TEST_USER}` (localhost `auth_state` skips login via `VITE_DEV_TOKEN`)
- **Analyst**: qa-engineer (combined analyst+implementer slot dispatch)
- **Status**: extend-existing

## Extension target

**Covering spec**: `automation/tests/ui/admin/test_personal_token_create_and_verify.py`
(class `TestPersonalTokenCreateAndVerify`), merged to `automation/base` in
PR #1174 (ELITEA-2280, commit `4ae8fdf0`).

**Behavioural-overlap argument**: this case's steps 4–5 ("locate an active
token; verify the Expiration column shows a green ✅ icon and 'in X days'
label") are **already asserted, verbatim in substance**, by the covering
spec's own **Step 12** (`test_create_personal_token_and_verify_in_table`,
lines ~185-192):

```python
status = tokens_page.get_row_expiration_status(row, state="active")
expect(status).to_be_visible(timeout=ROW_WAIT_TIMEOUT)
status_text = (status.text_content() or "").strip()
assert status_text == "in 30 days", ...
```

`get_row_expiration_status(row, state="active")` resolves the exact same
`token-expiration-status`/`data-expiration-state="active"` DOM branch that
renders `SuccessIcon` (green ✅) + `"in N days"` (`TokensTable.jsx`'s
`ExpiryInDays`, confirmed live and in source — see § Concrete Handles). The
row under test there is a token this same spec creates with the default
30-day expiration, so "active token → green check + in-X-days label" is a
real, executed, merged assertion. No new assertion is needed for steps 4–5.

**Gap**: this case's steps 2–3 ("locate an expired token; verify the
Expiration column shows an ⊗ icon and 'Expired' label") have **zero existing
coverage anywhere** in the merged suite (grepped
`expiration_status|expiration-state|get_row_expiration_status` across
`automation/tests` and `test-specs` — the only hit is the covering spec's
own Step 12, `state="active"`). This AFS's Gap assertions section (below)
specs a new, read-only, additive test in the same file/class asserting the
`state="expired"` branch (gray `RemoveIcon` + `"Expired"`) against existing
live data — no token creation needed for this half.

## Preconditions
- User is logged in to the Elitea platform (localhost dev-token auth).
- Active project is `${ELITEA_PROJECT_ID}` (399, "Private").
- At least one token with a **past** expiration date exists in the project's
  token list (confirmed live 2026-08-05: tokens `Marian` and `New` are both
  expired — real persistent data, not a fixture; see § Concrete Handles).
  If this data is ever bulk-deleted, the new test correctly goes RED for a
  genuinely missing precondition (same posture as ELITEA-2277's read-only
  test) — it is not this AFS's job to create an expired token (expiration is
  time-based; a freshly-created token can't be made "expired" without either
  waiting real time or a backend seed hook neither of which exists here).

## Test Data
### reuse-existing
- An existing expired token row, matched by name `Marian` or `New` (either
  suffices — both confirmed `data-expiration-state="expired"` live). Use
  `tokens_page.get_row_by_name("Marian")` (or fall back to `"New"` if
  `Marian` is ever removed — page object supports either without change).

(No `generate-per-test` / `generate-shared-with-cleanup` test data — the gap
half of this case is fully read-only, per `.agents/testing.md` § Test data
strategy / implementation Hard Rule 10.)

## Test Steps
1. Navigate to Settings → Personal Tokens (`tokens_page.navigate()`).
   - **Verify**: token rows are visible.
2. Locate the row named `Marian` (`get_row_by_name("Marian")`).
   - **Verify**: exactly one matching row exists.
3. Verify the Expiration column shows the expired-state icon (gray
   `RemoveIcon` via `data-expiration-state="expired"`) and the exact text
   `"Expired"`.

(Steps 4–5 of the original case — active token, green icon, "in X days" —
are satisfied by the covering spec's existing Step 12; not repeated here.)

## Expected Results
- The expired token's Expiration cell resolves via
  `get_row_expiration_status(row, state="expired")`, is visible, and its
  text content is exactly `"Expired"`.
- No console errors during the check.

## Coverage Map

### Axis 1 — Case coverage

| Case element | Expected result | Covered by (AFS step) | Asserted where | Disposition |
|---|---|---|---|---|
| 1 Navigate to Settings → Personal Tokens | page loads | step 1 | new test, step 1 | asserted |
| 2 Locate a token whose expiration date has passed | action completes | step 2 | new test, step 2 | asserted |
| 3 Verify Expiration column shows ⊗ icon and "Expired" label | condition holds | step 3 | new test, step 3 | asserted |
| 4 Locate a token that is still active | action completes | — | covering spec `test_create_personal_token_and_verify_in_table` Step 11 (creates + locates the token by name) | already-covered |
| 5 Verify Expiration column shows green ✅ icon and "in X days" label | condition holds | — | covering spec `test_create_personal_token_and_verify_in_table` Step 12 (`get_row_expiration_status(row, state="active")`, asserts `"in 30 days"`) | already-covered |

### Axis 2 — Analyst additions

- None beyond the case. The new test's own navigation/no-console-error checks
  are the same house style as the covering spec's Step 13, not an added
  observable — omitted here to avoid duplicating the covering spec's console
  check on the same page load context (the new test is a targeted read-only
  addition, not a full page-load re-verification).

## Gap assertions (implementer: append to the covering spec)

Add a **new, independent `test()` method** to
`automation/tests/ui/admin/test_personal_token_create_and_verify.py`'s
`TestPersonalTokenCreateAndVerify` class — purely additive, the existing
`test_create_personal_token_and_verify_in_table` body stays byte-identical.
Tag the new method with the same `@allure.issue` pattern, pointing at this
case's TMS source, plus append `ELITEA-2284` to the class/module's coverage
so both TMS IDs trace to this file (module already carries
`pytestmark = [pytest.mark.ui, pytest.mark.admin, pytest.mark.p2,
pytest.mark.regression]` — reuse as-is, no new markers needed since both
cases share module/priority).

```python
def test_expired_token_shows_expired_icon_and_label(self, page):
    """ELITEA-2284 (steps 2-3) — an existing expired token's Expiration
    cell shows the gray/expired state icon and the exact 'Expired' label.
    Read-only: uses existing live project data, no token created or
    deleted. (Steps 4-5 of ELITEA-2284 — active token, green icon, 'in X
    days' — are already asserted by test_create_personal_token_and_verify_in_table's
    Step 12; not repeated here.)"""
    tokens_page = PersonalTokensPage(page)

    with allure.step("Step 1 — Navigate to Settings -> Personal Tokens"):
        tokens_page.navigate()

    with allure.step("Step 2 — Locate an existing expired token row"):
        row = tokens_page.get_row_by_name("Marian")
        expect(row).to_have_count(1, timeout=ROW_WAIT_TIMEOUT)

    with allure.step(
        'Step 3 — Verify the Expiration cell shows the expired state '
        '(gray icon) and the exact "Expired" label'
    ):
        status = tokens_page.get_row_expiration_status(row, state="expired")
        expect(status).to_be_visible(timeout=ROW_WAIT_TIMEOUT)
        status_text = (status.text_content() or "").strip()
        assert status_text == "Expired", (
            f"Expected the Expiration cell to read 'Expired', got {status_text!r}"
        )
```

No new imports needed (`PersonalTokensPage`, `allure`, `expect`,
`ROW_WAIT_TIMEOUT` are all already imported/defined in the covering spec).

## Concrete Handles (discovered during exploration)

All handles pre-exist — confirmed live 2026-08-05, no new testid work.

| Element | Recommended Locator | Fallback |
|---|---|---|
| Token row by name | `PersonalTokensPage.get_row_by_name("Marian")` (wraps `[data-testid="token-row"]` filtered by text) | `get_row_by_name("New")` — also confirmed expired live |
| Expiration cell, expired state | `PersonalTokensPage.get_row_expiration_status(row, state="expired")` → `[data-testid="token-expiration-status"][data-expiration-state="expired"]` | none needed — testid+state is already the stable form |
| Expiration cell, active state (already-covered, no new use) | `get_row_expiration_status(row, state="active")` | n/a |

Source confirmation (`EliteaUI/src/[fsd]/features/settings/ui/personal-tokes/TokensTable.jsx`,
`ExpiryInDays` sub-component): the `expiryInDays === -1` branch renders "Never"
(not relevant to this case); the falsy/else branch (expired) renders
`RemoveIcon` (`theme.palette.icon.fill.disabled`, gray) + literal text
`"Expired"` — matches the case's informal "⊗ icon" description (the actual
component is `RemoveIcon`, not a literal ⊗ glyph; asserting the stable
`data-expiration-state="expired"` selector + text is the correct testid-first
verification per this project's "testid = stable identity, state via data-*"
locator ruling, not a pixel/glyph comparison).

Live data snapshot (2026-08-05, `${ELITEA_PROJECT_ID}` = 399): 5 rows —
`for_ui_tests` (Never), `Levon` (Never), `Marian` (Expired), `New` (Expired),
`uautomate` (Never). **No persistently-active "in X days" row exists in
stable data** — every non-expired token here has no expiry ("Never"), which
is exactly why the covering spec's Step 12 assertion had to create its own
token (only a freshly-created token, with a finite expiration, exhibits the
"active, N days remaining" state). This confirms the Gap-assertions design
above: expired-state coverage is achievable read-only; active-state coverage
inherently requires the mutation the covering spec already performs — reuse
it rather than duplicating a token-creation flow here.

## Network Behavior
None beyond the covering spec's existing `navigate()` wait on the token-list
GET (`TOKEN_LIST_URL_SUBSTRING`) — no new network behavior introduced by the
gap assertion (pure read of already-loaded row data).

## Known Defects Found During Exploration
None found.

## Blocked Steps
None.

## Automation Hints
- Framework: Playwright + pytest (per `.agents/testing.md`), same as the
  covering spec.
- Page object: `automation/pages/personal_tokens_page.py` — no changes
  needed, `get_row_by_name` + `get_row_expiration_status` already exist.
- No fixture changes; `page` fixture only, same as the covering spec's
  `test_create_personal_token_and_verify_in_table`.
