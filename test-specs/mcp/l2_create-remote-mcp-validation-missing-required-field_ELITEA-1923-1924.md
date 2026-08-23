# Test Case: Create Remote MCP — Validation Error on a Missing Required Field (FAMILY)

## Metadata
- **TMS IDs**: ELITEA-1923 (missing Url), ELITEA-1924 (missing Toolkit Name)
- **Family AFS**: yes — both cases are flow-variants of ONE flow (open the Remote MCP
  create form, fill exactly one of the two required fields, attempt Save, observe the
  inline `Field is required` error on the empty field and that nothing is created, then
  supply the missing field and save successfully). Implemented as ONE parameterized
  spec, one row per TMS case, each row asserting its OWN expected values.
- **Linked Story**: none
- **Priority**: l2
  - **Contradictory case metadata (report, not guess)** — affects BOTH cases: each case's
    YAML frontmatter says `priority: high` while its own body prose says
    `**Priority:** medium`. Used the frontmatter (structured field) as authoritative,
    mapping `high` → `l2` / `pytest.mark.p2`, consistent with ELITEA-1934 (frontmatter
    `high` → `l2_..._ELITEA-1934.md`, `pytest.mark.p2`). Same class of TMS-authoring
    mismatch already reported at ELITEA-1921. Not a product defect; flagged for the
    TMS owner to reconcile. Does not block automation.
- **Environment Explored**: local (`http://localhost:5173`, `EliteaAI/EliteaUI` @
  `automation/testids`, DEV backend), 2026-08-24
- **User set**: `${TEST_USER}` (localhost: no login needed — `VITE_DEV_TOKEN` auto-auths;
  sidebar confirmed "Elitea is connected", `Project: Private`, project id `399`)
- **Analyst**: test-automation-engineer (combined analyst+implementer slot), session 2026-08-24
- **Status**: ready-for-automation
  - **Classification note (declared improvisation — `.agents/role-overrides.md`
    § Declared-improvisation protocol, invoking `.agents/testing.md` § Merge gate →
    *Analysis-time entry*):** ELITEA-1924's **step 4 is contradicted by the live
    product** (details in § Known Defects). Per the analysis-time-entry bullet, the
    defect is deterministic, single-cause, isolable (it does NOT block reaching any
    later step) and linked to an **OPEN** issue (#633), so the family stays
    `ready-for-automation` and ELITEA-1924's step-4 assertion is written as the
    **case's** documented expected behaviour with `expect.soft()` +
    `# Known defect: #633`. It is NOT rewritten to the live behaviour — swapping a
    case's central observable is a human decision (§ ceiling, limit 1), and doing it
    silently would be reverse-masking. The divergence therefore stays **visible as a
    red** until a human rules. Every other step of both cases is asserted **hard**.
    ELITEA-1923 carries no soft assertions and is expected fully green.

## Preconditions
- User is authenticated (localhost: automatic via `VITE_DEV_TOKEN`; deployed envs:
  standard Keycloak login via `${TEST_USER}`).
- Project context is set (project id from `${ELITEA_PROJECT_ID}`, confirmed live as `399`).
- No precondition data needs seeding — both cases are self-contained create flows.
- **The create form must be reached by CLICKING the Remote MCP type card**, never by
  direct navigation to `/mcps/create/mcp` (that URL redirects back to the type picker
  with the wrong tab pre-selected — pre-existing finding, ELITEA-1921 § Automation Hints,
  re-confirmed this session).

## Test Data

### Parameter table (one row per TMS case)

| TMS case | Field left EMPTY | Field filled first | Toolkit Name used | Url used | Helper-text testid asserted | Save state after the partial fill (the case's OWN expected value) | Assertion strength |
|---|---|---|---|---|---|---|---|
| ELITEA-1923 | `Url` | `Toolkit Name` | `autotest_validation_no_url_<4hex>` | `https://mcp.example.com/sse` | `toolkit-field-url-input-helper-text` | **enabled** (case step 4: "Save button becomes enabled (name alone enables it)") | hard |
| ELITEA-1924 | `Toolkit Name` | `Url` | `autotest_validation_name_<4hex>` | `https://mcp.example.com/sse` | `toolkit-form-name-input-helper-text` | **disabled** (case step 4: "Save button remains disabled") — **contradicted live**, see § Known Defects | `expect.soft()` + `# Known defect: #633` |

### generate-per-test (created by the test, deleted in its own teardown)
- **Toolkit Name — MUST be uuid-suffixed for uniqueness**, and the suffix length is
  constrained: `MAX_NAME_LENGTH = 32` (`EliteaUI/src/common/constants.js`) is enforced as
  an `inputProps.maxLength` on the Name field and **silently truncates** anything longer.
  - `autotest_validation_no_url` = 26 chars → `_<4hex>` = **31 chars** ✓
  - `autotest_validation_name` = 24 chars → `_<4hex>` = **29 chars** ✓
  - Use a **4-hex-char** suffix for both (same precedent and reasoning as ELITEA-1921).
- **Url**: `https://mcp.example.com/sse` (static, straight from both case texts). It is
  never dialled — this family never clicks Load Tools — so an unreachable host is
  irrelevant here and no DeepWiki fixture is needed.

### reuse-existing
- `${TEST_USER}` — deployed envs only; localhost skips login entirely.

## Test Steps

Steps below are written once for the family; `{empty_field}` / `{filled_field}` /
`{helper_testid}` / `{expected_save_state}` resolve per the parameter table row.

1. Navigate to `/mcps/create` and verify the type picker is reachable.
   - **Verify**: `/mcps/create` is in `page.url`; `toolkit-type-card-mcp` is visible.
   - **Wait note (confirmed live this session, twice):** after a fresh page load the
     type-card mounts *asynchronously* — an immediate query for
     `toolkit-type-card-mcp` misses it. Use the framework's auto-waiting
     (`McpFormPage.navigate_to_create()` already does), never a bare
     `query_selector` / immediate read.
2. Click the Remote MCP type card (`toolkit-type-card-mcp`).
   - **Verify**: `/mcps/create/mcp` is in `page.url`; `toolkit-form-name-input` is visible.
3. Verify the Save button (`toolkit-form-save-button`) is **disabled** on the pristine,
   untouched form.
   - **Verify**: `save_button` is disabled. *(Confirmed live: `disabled: true`.)*
4. Fill `{filled_field}` with its row value; leave `{empty_field}` untouched.
   - **Verify**: `{filled_field}` displays the typed value AND `{empty_field}`'s input
     value is still exactly `""` (asserting the emptiness is the precondition of the
     whole case — see Axis 2).
5. Verify the Save button's state matches `{expected_save_state}` for this row.
   - ELITEA-1923 → **hard** assert Save is **enabled**. *(Confirmed live: `disabled: false`.)*
   - ELITEA-1924 → **`expect.soft()`** assert Save is **disabled**, with a
     `# Known defect: #633` comment. *(Live: `disabled: false` — this soft assertion
     WILL fail; that red is the intended, sanctioned signal. See § Known Defects.)*
6. Click Save (`toolkit-form-save-button`) and verify **no toolkit is created**.
   - **Verify (all three, hard, both rows)**:
     a. **No** `POST .../elitea_core/tools/prompt_lib/${PROJECT_ID}` fires within a
        short absence window. *(Confirmed live for both rows via
        `browser_network_requests`: zero POSTs.)*
     b. The page is still on `/mcps/create/mcp`.
     c. The `{empty_field}` input carries `aria-invalid="true"`.
7. Verify the inline validation error `Field is required` is displayed under
   `{empty_field}`.
   - **Verify**: `{helper_testid}` is visible, its text is exactly `Field is required`,
     and it carries the MUI error class (`Mui-error`).
   - *(Confirmed live: ELITEA-1923 → `toolkit-field-url-input-helper-text` =
     "Field is required", `Mui-error` true. ELITEA-1924 →
     `toolkit-form-name-input-helper-text` = "Field is required", `Mui-error` true —
     **testid added this session**, see § Concrete Handles.)*
8. Fill the previously-empty `{empty_field}` with its row value.
   - **Verify**: the field displays the typed value, the `{helper_testid}` error element
     is **gone from the DOM**, and `{empty_field}`'s `aria-invalid` is no longer `"true"`.
   - *(Confirmed live for both rows: the helper element is removed, not merely hidden —
     assert absence via `to_have_count(0)`, not `not_to_be_visible()`.)*
9. Click Save again; verify the toolkit is created.
   - **Verify**: `POST .../elitea_core/tools/prompt_lib/${PROJECT_ID}` returns
     **`201 Created`** with a numeric `id`; the page navigates to `/mcps/all/{id}`.
   - *(Confirmed live: ELITEA-1923 → id `2990`; ELITEA-1924 → id `2991`; both `201`.)*
10. Verify the created MCP's detail page shows the persisted values.
    - **Verify**: `toolkit-detail-title` contains the generated toolkit name;
      `toolkit-form-name-input` = the toolkit name; `toolkit-field-url-input` =
      `https://mcp.example.com/sse`.

## Expected Results
- Save is disabled on the pristine form (both rows).
- After exactly one required field is filled, the Save button state matches the row's
  own expected value — **enabled** for ELITEA-1923 (holds live), **disabled** for
  ELITEA-1924 (does NOT hold live; soft-asserted, tied to open #633).
- Clicking Save with a required field empty creates **nothing**: no `POST`, the form
  stays on `/mcps/create/mcp`, and an inline `Field is required` error appears under the
  empty field with `aria-invalid="true"`.
- Supplying the missing field clears the error element from the DOM entirely.
- The second Save succeeds: `201 Created`, redirect to `/mcps/all/{id}`, and the detail
  page shows the persisted Name and Url.
- Net effect per row: exactly ONE toolkit created, and it is deleted in teardown.

## Coverage Map

### Axis 1 — Case coverage

#### ELITEA-1923 — Validation Error on Missing URL

| Case element | Expected result | Covered by (AFS step) | Asserted where | Disposition |
|---|---|---|---|---|
| Preconditions: user logged in; on MCP creation page with "Remote MCP" selected | — | steps 1–2 | fixture (`auth_state` / dev token) + steps 1–2 | asserted |
| 1 Navigate to MCP creation page and select "Remote MCP" → "Form page loads at /app/mcps/create/mcp" | form page loads | steps 1–2 | step 2: `in page.url` substring + name input visible | asserted — **localhost has no `/app` prefix** (`APP_PREFIX` empty, `.agents/profile.md`); live URL is `/mcps/create/mcp?viewMode=owner`. Substring assertion, same pattern as ELITEA-1921/1922. Not a defect. |
| 2 Fill "Toolkit Name *" with `autotest_validation_no_url` | field accepts and displays input | step 4 | step 4: `input_value()` | asserted *(uuid-suffixed — see Test Data)* |
| 3 Leave "Url *" empty | URL field remains empty | step 4 | step 4: `url_input.input_value() == ""` | asserted |
| 4 Verify Save becomes enabled (name alone enables it) | Save is clickable | step 5 | step 5: hard assert enabled | asserted — **holds live** (`disabled: false`) |
| 5 Click Save | save is attempted | step 6 | step 6 | asserted |
| 6 Verify error "Field is required" appears below the Url field | error displayed under URL field | step 7 | step 7: `toolkit-field-url-input-helper-text` text + `Mui-error` | asserted |
| 7 Verify MCP is NOT created (stays on create page) | page remains on create page | step 6 | step 6a (no POST) + 6b (URL) + 6c (`aria-invalid`) | asserted — strengthened beyond the case's URL-only check, see Axis 2 |
| 8 Fill "Url *" with `https://mcp.example.com/sse` | field accepts and displays URL | step 8 | step 8: `input_value()` + error element gone | asserted |
| 9 Click Save again — MCP created successfully | redirect to detail page | step 9 | step 9: `201` + `/mcps/all/{id}` | asserted |
| Expected Final State: MCP created; validation error no longer shown | — | steps 8–10 | steps 8, 9, 10 | asserted |
| Pass/Fail: error appears when URL missing; creation succeeds after supplying it | — | all steps | steps 5–10 | asserted |

#### ELITEA-1924 — Validation Error on Missing Name

| Case element | Expected result | Covered by (AFS step) | Asserted where | Disposition |
|---|---|---|---|---|
| Preconditions: user logged in; on MCP creation page with "Remote MCP" selected | — | steps 1–2 | fixture + steps 1–2 | asserted |
| 1 Navigate to MCP creation page and select "Remote MCP" → "/app/mcps/create/mcp" | form page loads | steps 1–2 | step 2 | asserted — same `/app`-prefix note as ELITEA-1923 row 1 |
| 2 Leave "Toolkit Name *" empty | name field remains empty | step 4 | step 4: `name_input.input_value() == ""` | asserted |
| 3 Fill "Url *" with `https://mcp.example.com/sse` | field accepts and displays URL | step 4 | step 4: `input_value()` | asserted |
| 4 Verify Save **remains disabled** (name is required to enable save) | Save button is disabled | step 5 | step 5: **`expect.soft()`** + `# Known defect: #633` | asserted **as the case states it — SANCTIONED RED.** Live product returns `disabled: false`; root cause `shouldDisableSave = isLoading \|\| !formik?.dirty` (`CreateToolkitToolTabBar.jsx:43-45`) never consults the name. NOT rewritten to the live value (that would be reverse-masking); NOT dropped (that would be defect-masking). See § Known Defects + Classification note. |
| 5 Fill "Toolkit Name *" with `autotest_validation_name` | field accepts and displays input | step 8 | step 8: `input_value()` + error element gone | asserted *(uuid-suffixed)* |
| 6 Verify Save button becomes enabled | Save is clickable | step 8 | step 8 (hard assert Save enabled once both fields hold values) | asserted — holds live |
| 7 Click Save — verify MCP is created | redirect to detail page | step 9 | step 9: `201` + `/mcps/all/{id}` | asserted |
| Expected Final State: MCP created once both required fields filled | — | steps 9–10 | steps 9, 10 | asserted |
| Pass/Fail: "Save button is disabled until Toolkit Name is provided" | — | step 5 | step 5 (soft) | asserted — **this Pass criterion does not hold live**; it is the same single cause as case step 4 (#633), not a second failure |
| Pass/Fail: "MCP creation fails" would be a Fail | MCP created after both fields filled | steps 9–10 | steps 9, 10 | asserted |

### Axis 2 — Analyst additions

- **Step 6a — "no `POST` fired" is asserted directly**, not inferred from the URL.
  *Added: both cases' "MCP is NOT created" expectation is only checked by the case text
  via "stays on create page", which a client-side route guard could satisfy even if a
  toolkit had been created. Asserting the absence of the create `POST` is what actually
  proves nothing was created. Confirmed live for both rows (zero POSTs).*
- **Step 6c — `aria-invalid="true"` on the empty field.** *Added: proves the field itself
  is in the invalid state, not merely that some error text exists somewhere on the page.*
- **Step 7 — the error text is asserted EXACTLY (`== "Field is required"`) and the
  `Mui-error` class is checked**, rather than a substring/visibility check. *Added: a
  bare visibility assertion would pass on the unrelated, always-present
  "Enter scopes separated by commas or spaces" helper text, which lives in the same
  `.MuiFormHelperText-root` family (observed live).*
- **Step 8 — the error element must be GONE from the DOM (`to_have_count(0)`), not merely
  invisible.** *Added: confirmed live that the helper element is unmounted when the field
  becomes valid; asserting absence-by-count is the accurate observable and is a
  first-class reference per canon ruling #511's absence-assertion extension.*
- **Step 4 — the "empty" field's value is asserted `== ""` before Save is clicked.**
  *Added: the emptiness IS the precondition of both cases; leaving it unasserted would let
  a stray autofill or a leaked value from a previous parameterized row silently turn the
  case into a no-op.*
- **Step 10 — detail-page persistence of Name + Url after the recovery save.** *Added:
  ELITEA-1923's step 9 only asserts "redirect occurs"; asserting the two values actually
  round-tripped proves the recovery save persisted the corrected form, not just that some
  navigation happened.*
- **No console-error assertion added.** *Both `/mcps/create` and `/mcps/create/mcp`
  reproduce the same pre-existing, unrelated React dev-mode warnings already filed as
  `EliteaAI/elitea-testing-public#291` (re-confirmed this session). Coupling this
  functional case to them would create false red — same decision as ELITEA-1921/1922.*
- **Deliberately NOT added: an assertion that Save is disabled on the pristine form is
  "because required fields are empty".** *The pristine-form disabled state (step 3) is
  real and asserted, but its CAUSE is `!formik.dirty`, not required-field emptiness — see
  #633. Asserting the causal reading would be asserting a false mechanism.*

## Cleanup

1. Each parameterized row creates exactly ONE persistent server-side toolkit (confirmed
   live: `POST .../tools/prompt_lib/399` → `201` with a numeric `id`).
2. Delete it in teardown via the existing `ToolkitAPI.delete_toolkit(toolkit_id)`
   (`automation/api/client.py`), in a `finally` block — same pattern as the two merged
   tests in `test_mcp_create_remote.py`. Capture the id from the Save response.
3. **The teardown must run even when the row's soft assertion has failed** — the
   `expect.soft()` failure is raised at the END of `pytest_runtest_call`, i.e. after the
   test body's `finally` has already executed, so an ordinary `try/finally` is sufficient
   and no special handling is needed.
4. This session's own exploration toolkits (ids `2990`, `2991`) **were deleted** via
   `DELETE .../elitea_core/tool/prompt_lib/399/{id}` → `204 No Content` for both. No
   residue left for the implementer.
5. No credential/secret cleanup — this family never touches Client Secret.

## Concrete Handles (discovered/re-confirmed during exploration)

**PROVENANCE verified via `cd ../EliteaUI && git fetch origin` immediately before writing
this table.**

| Element | Locator | PROVENANCE | Fallback |
|---|---|---|---|
| Remote MCP type-selector card | `[data-testid="toolkit-type-card-mcp"]` | on-`automation/testids` only | none — testid-only |
| Toolkit Name input | `[data-testid="toolkit-form-name-input"]` | on-`automation/testids` only | none |
| Url input | `[data-testid="toolkit-field-url-input"]` | on-`automation/testids` only | none |
| Save button (create form) | `[data-testid="toolkit-form-save-button"]` | on-`automation/testids` only | none |
| **Url validation helper text** | `[data-testid="toolkit-field-url-input-helper-text"]` | on-`automation/testids` only — **already existed**, emitted by `ToolBaseProperty.jsx:610` as `helperTextTestId={`toolkit-field-${k}-input-helper-text`}` | none |
| **Toolkit Name validation helper text** | `[data-testid="toolkit-form-name-input-helper-text"]` | **needs-adding → ADDED THIS SESSION**, EliteaAI/EliteaUI@35440c78 on `automation/testids`; **not yet on `main`** (human cherry-pick pending) | none |
| Detail page title heading | `[data-testid="toolkit-detail-title"]` | on-`automation/testids` only | none |

**Why the Name helper testid had to be added rather than worked around.** The Url field
renders through `ToolBaseProperty.jsx` (schema-driven), which already passes
`helperTextTestId`. The Toolkit Name field renders through a *different* component,
`NameDescriptionInput.jsx`, which passed `helperText` but **no** `helperTextTestId` — so
the error node carried only a React-generated, unstable id (`:r2n:-helper-text`).
`helperTextTestId` is a first-class prop of the shared `InputBase` (`InputBase.jsx:101,270`,
already used by 4 other call sites), so the fix is a **one-line, purely additive prop** —
no new DOM node, no new hook, no structural change, zero functional impact
(`add-data-testid` § Step 5.5 clean). Naming follows the established
`<input-testid>-helper-text` derivation used by `ToolBaseProperty` and `SecretField.jsx:88`.
The **Description** field's helper text was deliberately left without a testid — this
family never asserts it (canon ruling #511: add only what the test calls).

## Network Behavior
- `POST /api/v2/elitea_core/tools/prompt_lib/${PROJECT_ID}` — fires **only** on the
  recovery Save; `201 Created`, body `id` = new toolkit id. **Confirmed live that it does
  NOT fire** on the first Save while a required field is empty (client-side Formik/Yup
  validation blocks it) — this is the observable behind step 6a for both rows.
- `GET /api/v2/elitea_core/toolkit_available_tools/prompt_lib/${PROJECT_ID}/{id}` — fires
  on detail-page load after creation (`200`).
- `DELETE /api/v2/elitea_core/tool/prompt_lib/${PROJECT_ID}/{id}` — teardown; `204`.

## Known Defects Found During Exploration

### [BLOCKING FOR ELITEA-1924 STEP 4 ONLY] Save button is enabled with Toolkit Name empty — tracked on OPEN issue #633

**Not filed as a new issue.** `EliteaAI/elitea-testing-public#633` (OPEN, label `bug`,
`[INFO]`) already tracks this exact behaviour — same object, same trigger, same
expected/actual — so per `.agents/profile.md` § Bug filing → dedup, the new occurrence was
**commented onto #633** rather than refiled:
https://github.com/EliteaAI/elitea-testing-public/issues/633#issuecomment-5388800232

**What was confirmed live this session (2026-08-24):**

| Observation | Result |
|---|---|
| Pristine form, nothing touched | Save `disabled: true` |
| **Url filled only, Toolkit Name empty** | Save `disabled: false` ← contradicts ELITEA-1924 step 4 |
| Click Save in that state | **no** `POST`; `Field is required` under Toolkit Name; `aria-invalid="true"`; stays on `/mcps/create/mcp` |
| Fill Toolkit Name, click Save | `POST` → `201`, redirect to `/mcps/all/2991` |

**Root cause, read from source** (`src/pages/Toolkits/CreateToolkitToolTabBar.jsx:43-45`):

```js
const shouldDisableSave = useMemo(() => {
  return isLoading || !formik?.dirty;
}, [isLoading, formik?.dirty]);
```

The disabled state consults **only** `formik.dirty` — never the name field, never
required-field validity. Deterministic and single-cause.

**Why this escalates beyond what #633 originally recorded.** #633 was written for
ELITEA-1921, where the contradicted behaviour was a peripheral assertion nobody needed.
For **ELITEA-1924 it is the case's entire Objective, its step 4, and one of its two Pass
criteria** — so the case cannot pass as written. A human must rule on one of:

1. **Product changes** — `shouldDisableSave` also gates on required-field validity; or
2. **Case text changes** — ELITEA-1924's Objective/step 4/Pass criterion are rewritten to
   the real contract ("Save is enabled once any field is touched; submission is blocked
   with `Field is required` under Toolkit Name and no toolkit is created").

Until then the assertion stays as the case states it, `expect.soft()`-ed and linked, so
the divergence is a **visible red** rather than a silent swap. **The name requirement
itself IS correctly enforced** — just at submit time rather than via the button — and that
enforcement is asserted HARD at steps 6 and 7, so this family still delivers real coverage
of the case's stated intent.

### [MINOR] Pre-existing React dev-mode console warnings — already filed as #291
Re-confirmed identical on `/mcps/create` and `/mcps/create/mcp` this session (missing
`key` prop in `CategorySection`/`GroupedCategory`; invalid `<p>`-in-`<p>` nesting from
`InfoTooltip`). Not refiled; no console assertion added (see Axis 2).

### [NOTE — not a product defect] Contradictory TMS metadata on BOTH cases
`priority: high` (frontmatter) vs `**Priority:** medium` (body prose) in each of
ELITEA-1923 and ELITEA-1924. Reported per the intake "contradictory-metadata → report not
guess" rule; frontmatter used. Same class as ELITEA-1921's. Not tracker-filed — a TMS
authoring-quality note for the case owner.

### [NOTE] `/app` prefix in both case texts
Both cases state the form loads at `/app/mcps/create/mcp`. On localhost `APP_PREFIX` is
empty, so the live URL is `/mcps/create/mcp?viewMode=owner`. Handled with substring
assertions (existing project convention); not a defect and not filed.

## Blocked Steps

None. **Every step of both cases was executed to completion against the live local
environment**, including both create→error→recover→create round trips and full cleanup.
ELITEA-1924's step 4 was executed and observed — it *fails* rather than being unreachable,
which is why the family is `ready-for-automation` with a sanctioned-RED soft assertion
rather than `blocked`.

## Automation Hints

- Framework: Playwright + pytest, testid-only `LocatorDescriptor` (`.agents/testing.md`).
- **ONE parameterized spec, one row per TMS case** (family AFS): parametrize with
  `pytest.mark.parametrize` using `ids=["ELITEA-1923", "ELITEA-1924"]` so each row's node
  id names its own case and the gate can address them separately.
- **Reuse `automation/pages/mcp_form_page.py` (`McpFormPage`) — do not duplicate**
  (`.claude/rules/page-objects.md` § NO Method Duplication). Already present and
  sufficient: `navigate_to_create()`, `select_remote_mcp_type()`, `fill_name()`,
  `fill_url()`, `is_save_button_disabled()`, `save_and_wait_for_created()`,
  `get_detail_heading_text()`, plus `name_input` / `url_input` / `save_button`
  `LocatorDescriptor`s.
  - **Missing — add as new class-level `LocatorDescriptor` fields** (additive only):
    `name_helper_text` (`toolkit-form-name-input-helper-text`) and `url_helper_text`
    (`toolkit-field-url-input-helper-text`). Both are plain static testids, so plain
    `LocatorDescriptor` fields — no UPPER_CASE selector constant needed.
  - The row must choose between the two helper locators; select the attribute by name
    from the parametrized row rather than constructing any locator in the test body
    (locators stay page-object class fields).
- **Asserting "no POST fired"** is an absence-of-network-request observable, which
  Playwright's `expect.soft` cannot express. Use the established in-repo idiom: a
  `page.expect_response(...)` inside `try/except PlaywrightTimeoutError` with a short
  timeout, treating the timeout as the PASS (see
  `tests/ui/artifacts/test_artifacts_create_bucket_56char_limit_warning_delete_cancel.py`).
  Keep this a **hard** assertion — it is not the known defect.
- **The `expect.soft()` for #633 targets a locator** (`save_button`), so
  `expect.soft(form.save_button).to_be_disabled()` is the right shape — no
  `soft_failures`/`pytest.fail()` aggregation needed for it.
- **`expect.soft` failures ARE pytest failures** (`.agents/testing.md` § Merge gate):
  the ELITEA-1924 row is expected **RED** and its case status is `blocked-on-#633`, never
  `automated`. The ELITEA-1923 row is expected fully green.
- **A dirty, unsaved form triggers a native `beforeunload` confirm dialog** if the harness
  navigates away mid-test. Register `page.on("dialog", lambda d: d.accept())` at the top of
  the test — both merged tests in this file already do.
- **Never navigate directly to `/mcps/create/mcp`** (redirects to the type picker with the
  wrong tab). Always click-through via `navigate_to_create()` → `select_remote_mcp_type()`.
- **Type-card mount is async after a fresh load** — rely on framework auto-waiting; an
  immediate DOM read misses it (observed twice this session).
- Suggested location: a new test in the existing
  `automation/tests/ui/toolkits/test_mcp_create_remote.py`? **No** — that file holds two
  large single-scenario create tests. Put this family in its own sibling file,
  `automation/tests/ui/toolkits/test_mcp_create_validation.py`, since it is a
  parameterized negative/validation family with its own module-level constants and a
  different purpose (validation gating) from the two positive create tests.
- Markers: `pytest.mark.ui, toolkits, mcp, p2, regression, new` — `p2` per the `high`
  frontmatter priority (matching ELITEA-1934's precedent).
