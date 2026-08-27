# Test Case: Token expiration period unit and value can be configured

## Metadata
- **TMS ID**: ELITEA-2282
- **Source case**: `.agents/automation/settings-w04/cases/ELITEA-2282.md` (intake snapshot)
- **Priority**: l3 (case frontmatter `priority: medium`) → **pytest marker `@pytest.mark.p2`**
- **Environment Explored**: local (`http://localhost:5173`, `EliteaAI/EliteaUI` on
  `automation/testids` → DEV backend, project `Private` / `${ELITEA_PROJECT_ID}` = 399)
- **User set**: `${TEST_USER}` (localhost `auth_state` skips login via `VITE_DEV_TOKEN`)
- **Analyst**: qa-engineer (Sage), batch `settings-w04`, cluster session, 2026-08-27
- **Status**: **ready-for-automation** (with one case-text drift — see § Case-Text Note)
- **Surface digest**: `test-specs/settings-personal-tokens/_surface.md`
- **Filed**: **#1882** — `[Clarification][ELITEA-2282] A 7-day token shows the AMBER
  'warning' icon, not green` (label `question`, **not** a product defect).
- **Testid work**: **NONE.** Every handle below is already on `EliteaAI/EliteaUI` `main`.

## ⚠️ Case-Text Note — the case's final expected result is STALE (reverse-masking guard)

The case's step 6 / Expected Final State demands *"a **green ✅** icon and 'in 7 days'
label"*. **The live product renders the AMBER "warning" icon at exactly 7 days, and it is
correct to do so.** `ExpiryInDays.jsx` branches on a strict `> 7`:

```jsx
if (expiryInDays > 7)    -> data-expiration-state="active"  + SuccessIcon   green #2BD48D
if (expiryInDays > 0)    -> data-expiration-state="warning" + AttentionIcon amber #E97912
if (expiryInDays === -1) -> data-expiration-state="never"   + SuccessIcon   green #2BD48D
else                     -> data-expiration-state="expired" + RemoveIcon    gray
```

`calculateExpiryInDays` (`src/common/utils.jsx:692-706`) rounds the remaining duration to
whole days, so a token created with `Days`/`7` evaluates to exactly `7`, fails `> 7`, and
lands in the amber "expiring soon" branch by design. Green is reserved for **more than**
7 days.

Verified live 2026-08-27, not inferred: creating `afs2282-days7` produced
`data-expiration-state="warning"`, icon fill `#E97912`, label `in 7 days`, and
`POST /api/v2/auth/token/` returned `expires: "Thu, 03 Sep 2026 17:50:43 GMT"` for a
create at `2026-08-27 17:50` — i.e. exactly the 7 days the case asked for.

**Per `.agents/testing.md` / the reverse-masking guard, the AFS asserts the LIVE
contract** (`warning` + `in 7 days`), never the stale case text. Asserting "green" would
make a correct product fail. Clarification filed as **#1882**; the case owner decides
whether to fix the wording or change the test data to a value above 7.

## Why this is NOT already covered

`test_create_personal_token_and_verify_in_table` (ELITEA-2280, merged) exercises the
create form's **defaults only** (`Days` / `30` → `active` / `in 30 days`, its Step 4
explicitly asserts the defaults are *unchanged*). It never opens the unit dropdown, never
enumerates the options, and never changes either expiration control. This case's
observables — the two-part expiration field, the five available units, and a
**configured** (non-default) unit+value flowing through to the table — are asserted
nowhere. The `warning` expiration state has **no test coverage at all** today (surface
digest: only `active` and `expired` are exercised); this case is its first.

## Preconditions
- Logged-in user; the tokens page reachable at `/settings/tokens`.
- No specific existing data required (the case creates its own token).

## Test Data
### create-and-destroy
- One token named `autotest-token-{uuid4().hex[:8]}`, unit **`Days`**, value **`7`**.
- **The case text never mentions a name**, but Generate is disabled until a valid
  non-empty name is entered (`isGenerateDisabled = !name || (touched.name &&
  Boolean(errors.name))`). Supplying one is a *precondition of the case's own step 5*,
  not an added scenario — note it in the docstring.
- **Mandatory cleanup** (`finally:`): delete the created token via the row's
  `token-action-delete-button` + the shared delete dialog, exactly as ELITEA-2280 does.
  This creates real, persistent data in shared live state.

## The product's actual expiration-configuration contract (source + live confirmed)

- `CreatePersonalToken.jsx` renders the Expiration period as **two controls**: a
  `SingleSelect` (`measure`, default `"days"`) plus a numeric `<input>` (`expiration`,
  default `30` = `DEFAULT_TOKEN_EXPIRATION_DAYS`).
- Options come from `EXPIRATION_MEASURES` (`src/common/constants.js:492`):
  `['never', 'days', 'weeks', 'hours', 'minutes']` — **exactly five**, in that order.
  Live-confirmed rendered order/labels: `Never, Days, Weeks, Hours, Minutes`.
- Each option carries a **runtime-composed testid from the shared select component**:
  `SingleSelectMenuItem.jsx:117` → ``data-testid={option.testId ?? `select-option-${option.value}`}``
  ⇒ `select-option-never` / `-days` / `-weeks` / `-hours` / `-minutes`.
  Present on **both** `origin/main` and `origin/automation/testids` (the template line is
  identical on both). Note: a bare `git grep 'select-option-days'` finds **nothing** —
  the string is composed at runtime; this is the documented stage-1 grep blind spot in
  `.agents/workflow.md` § Closure record, not a missing testid.
- The numeric value input is `type="number"`, `name="expiration"`, with **no** `min`/`max`
  attributes.
- Generate → `POST /api/v2/auth/token/` (**200**) with a body carrying the chosen
  `{measure, value}`; the response includes `expires` as an RFC-1123 date string.

### Live observations (2026-08-27, real interactions)

| Step | Observed |
|---|---|
| Landed on `/settings/create-personal-token` | title `New Token`, name empty, unit `Days`, value `30`, Generate **disabled** |
| Opened unit dropdown | 5 options: `Never/never`, `Days/days`, `Weeks/weeks`, `Hours/hours`, `Minutes/minutes` — testids `select-option-<value>` |
| Selected `Days`, set value `7`, typed name | unit reads `Days`, value reads `7`, Generate **enabled** |
| Generate | `POST /auth/token/` → **200**, `expires: "Thu, 03 Sep 2026 17:50:43 GMT"` (= +7 d) |
| Success dialog | title `New token generated!`, name matches |
| Closed dialog → `/settings/tokens` | row `afs2282-days7`, value `...fYHA`, expiration **`in 7 days`**, state **`warning`**, icon fill **`#E97912`** |

Console across the whole session: **0 errors**.

## Test Steps

1. **Step 1 — Navigate to Settings → Personal Tokens and click "+".**
   `PersonalTokensPage.navigate()` then `click_add_button()` (already waits for the URL
   `**/settings/create-personal-token` — the "+" **navigates**, it does not open a modal).
   - **Verify**: `create-personal-token-page-title` text == `New Token`.

2. **Step 2 — Verify the Expiration period field has two parts: a unit dropdown and a
   numeric value input.**
   - **Verify**: `create-personal-token-expiration-measure-select-combobox` is visible
     and its text == `Days` (the default).
   - **Verify**: `create-personal-token-expiration-value-input` is visible, its
     `input_value()` == `30`, and its `type` attribute == `number` (that attribute is
     what makes it a *numeric* input — the case's own wording).

3. **Step 3 — Click the unit dropdown; verify the options include at least Days, Weeks,
   Hours, Minutes and Never.**
   - Click the combobox; wait for the option list (`select-option-days` visible).
   - **Verify**: each of `select-option-never|days|weeks|hours|minutes` has count **1**
     and the expected label text (`Never`, `Days`, `Weeks`, `Hours`, `Minutes`).
   - **Verify (Axis 2)**: the *total* rendered option count is **5** — the case says "at
     least", but a superset would mean an unreviewed unit shipped, and the closed set is
     `EXPIRATION_MEASURES`. Assert exactly 5 and name the constant in a comment.

4. **Step 4 — Select "Days" and enter value "7".**
   - Click `select-option-days`.
   - **Verify**: the combobox text == `Days`.
   - Clear the numeric input (`ControlOrMeta+a` — this input is **not** the `useAutoBlur`
     name field, so select-all is reliable here) and `press_sequentially("7")`.
   - **Verify**: `input_value()` == `7` (the case's "field accepts the input" claim).
   - Enter the token name (`fill_name(token_name)`, which also waits for Generate to
     enable) — see § Test Data on why the name is a precondition of step 5.

5. **Step 5 — Click "Generate" and close the dialog.**
   - `click_generate()` (wraps the click in `expect_response` on the create `POST`).
   - **Verify**: `response.status == 200`.
   - **Verify (Axis 2)**: the response body's `expires` parses to a date **7 days ±1 day**
     from `datetime.now(timezone.utc)` — the backend's own confirmation that the *value*
     was configured, independent of any DOM rendering.
   - **Verify**: `generated-token-dialog-title` text == `New token generated!` and
     `generated-token-dialog-token-name` text == `token_name`.
   - `close_dialog()` (waits for `**/settings/tokens`).

6. **Step 6 — Verify the Expiration column's icon and label for the new token.**
   - Wait for the row: `expect(get_row_by_name(token_name)).to_have_count(1)` with
     `ROW_WAIT_TIMEOUT` (the table refetches after a create and is briefly unmounted —
     never read the row count immediately after landing).
   - **Verify**: the row's expiration label text == `in 7 days` (matches the case).
   - **Verify**: `get_row_expiration_status(row, state="warning")` has count **1** —
     i.e. `[data-testid="token-expiration-status"][data-expiration-state="warning"]`.
     **This is the live contract, not the case's "green"** — see § Case-Text Note.
     Add `# Case-text drift: see issue #1882` at this assertion.
   - **Verify**: `get_row_expiration_status(row, state="active")` has count **0** —
     the absence assertion that makes the "not green" claim explicit rather than implied.
   - Do **not** assert on the SVG's fill hex. The `data-expiration-state` attribute is the
     stable, testid-anchored handle for the state (per `.agents/testing.md` § Locator
     policy — state via `data-*`); the hex was read live only as evidence for #1882.

7. **Axis 2 — No console errors** across the flow (0 observed live).

8. **Cleanup (`finally:`, unwrapped)** — delete the created token (row trash icon →
   `fill_delete_confirm_name(token_name)` → `confirm_delete()` → wait for the row to
   reach count 0), exactly as ELITEA-2280's cleanup does.

## Handles Reference

| Element | Handle (testid) | Page-object member | PROVENANCE |
|---|---|---|---|
| Add (+) button | `personal-tokens-add-button` | `PersonalTokensPage.click_add_button()` | on-main ✓ |
| Create page title | `create-personal-token-page-title` | `CreatePersonalTokenPage.page_title` | on-main ✓ |
| Name input | `create-personal-token-name-input` | `name_input` / `fill_name()` | on-main ✓ |
| Unit dropdown (clickable) | `create-personal-token-expiration-measure-select-combobox` | `expiration_measure_combobox` | on-main ✓ (derived `-combobox` suffix of `create-personal-token-expiration-measure-select`) |
| Unit option (dynamic) | `select-option-{measure}` — `never/days/weeks/hours/minutes` | **new class-level template constant needed** (see below) | on-main ✓ (runtime-composed in shared `SingleSelectMenuItem.jsx:117`; identical on both refs) |
| Numeric value input | `create-personal-token-expiration-value-input` | `expiration_value_input` / `get_expiration_value()` | on-main ✓ |
| Generate button | `create-personal-token-generate-button` | `generate_button` / `click_generate()` | on-main ✓ |
| Success dialog title | `generated-token-dialog-title` | `dialog_title` | on-main ✓ |
| Success dialog name | `generated-token-dialog-token-name` | `dialog_token_name` | on-main ✓ |
| Dialog close (X) | `generated-token-dialog-close-button` | `dialog_close_button` / `close_dialog()` | on-main ✓ |
| Token row | `token-row` | `PersonalTokensPage.token_row` / `get_row_by_name()` | on-main ✓ |
| Expiration status (state-filtered) | `[data-testid="token-expiration-status"][data-expiration-state="{}"]` | `TOKEN_EXPIRATION_STATUS_SELECTOR` / `get_row_expiration_status()` | on-main ✓ |
| Row delete icon | `token-action-delete-button` | `get_row_action_icon()` | on-main ✓ |

Provenance verified 2026-08-27 after `cd ../EliteaUI && git fetch origin`, two-stage
`git grep` against `origin/main` **and** `origin/automation/testids` — all `YES`/`YES`.

**New page-object work (no EliteaUI change):** the unit options need the sanctioned
dynamic-testid shape on `CreatePersonalTokenPage` — a class-level UPPER_CASE template
plus a small method, never an inline `get_by_test_id(f"…")`:

```python
# class level — keeps the testid pattern in the greppable inventory
EXPIRATION_MEASURE_OPTION_SELECTOR = '[data-testid="select-option-{}"]'

def get_expiration_measure_option(self, measure: str):
    """Option in the open expiration-unit dropdown (`EXPIRATION_MEASURES`)."""
    return self.page.locator(self.EXPIRATION_MEASURE_OPTION_SELECTOR.format(measure))
```

The `{}` parameter is a value from the app's own closed `EXPIRATION_MEASURES` set, not
test-generated data. Also add an `open_expiration_measure_dropdown()` helper and a
`select_expiration_measure(measure)` that clicks the option and waits for the combobox
text to change.

## Automation Hints

- Target file: **`automation/tests/ui/admin/test_personal_token_create_and_verify.py`**
  (owns the create flow and both page objects) as a new test method, or a dedicated
  `test_personal_token_expiration_config.py`. Implementer's call.
- Markers: `ui`, `admin`, `p2`, `regression`.
- The docstring must record two things (project canon): that the name is supplied though
  the case omits it, and that step 6 asserts `warning` (amber) not `green` per issue
  **#1882**.
- `select-option-*` is an **app-wide generic** testid from the shared select. Only one
  select exists on this page, so a page-level locator is unambiguous here — do not reuse
  this assumption on a page with several selects.
- Never `sleep`; `expect(...)` polling plus `expect_response` cover every wait.

## Coverage Map

### Axis 1 — every element of the TMS case

| Case element | Expected result | Covered by | Asserted where | Disposition |
|---|---|---|---|---|
| Precondition: user logged in | — | `auth_state` | fixture | covered |
| Step 1 — Navigate + click "+" | Page loads | Step 1 | URL wait + `New Token` title | covered |
| Step 2 — Expiration field has a unit dropdown + numeric value input | Condition holds | Step 2 | combobox visible (`Days`) + numeric input visible (`30`, `type=number`) | covered |
| Step 3 — Options include Days, Weeks, Hours, Minutes, Never | Control responds | Step 3 | 5 named option testids + labels (+ exact-count Axis-2) | covered |
| Step 4 — Select "Days", enter "7" | Control responds | Step 4 | combobox text `Days`, input value `7` | covered |
| Step 5 — Click Generate and close the dialog | Control responds | Step 5 | `POST` 200 + `expires` ≈ +7 d + dialog title/name + navigation back | covered |
| Step 6 — Expiration column shows a **green ✅** icon and "in 7 days" | Condition holds | Step 6 | label `in 7 days` ✓; icon asserted as **`warning`/amber** (+ `active` absent) | **clarification — #1882** (live contract asserted; case text stale) |
| Expected Final State — same as step 6 | — | Step 6 | same | **clarification — #1882** |

### Axis 2 — observables asserted BEYOND the case

| Extra observable | Why it is grounded |
|---|---|
| `POST /auth/token/` → 200 and `expires` ≈ now + 7 days | The case's claim is that the expiration **value** was configured. The rendered label is downstream of the backend; asserting the response makes the case's real subject observable, and it is produced by the system (no substitution). |
| Exactly **5** unit options | The case says "at least"; the product's closed set is `EXPIRATION_MEASURES`. A 6th option would be an unreviewed change that "at least" silently tolerates. |
| `data-expiration-state="active"` has count **0** | Makes the "not green at exactly 7 days" contract an explicit, test-enforced invariant rather than an implication of the `warning` assertion — this is the exact boundary #1882 is about, so it must be pinned. |
| Numeric input's `type == "number"` | The case's own wording is "numeric value input"; visibility alone would pass for a plain text box. |
| No console errors | Standard side-channel axis; 0 observed live. |

## Known Defects
None. The one divergence from the case text is a **case-text drift** (issue #1882), not a
product defect — the `> 7` threshold is deliberate design.

## Blocked Steps
None.
