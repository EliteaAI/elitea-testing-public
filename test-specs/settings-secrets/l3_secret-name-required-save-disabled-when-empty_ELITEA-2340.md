# Test Case: Secret name is required — Save disabled when name is empty

## Metadata
- **TMS ID**: ELITEA-2340
- **Source case**: `.agents/automation/settings-w05/cases/ELITEA-2340.md` (intake snapshot)
- **Priority**: l3 (case frontmatter `priority: medium`) → **pytest marker `@pytest.mark.p2`**
- **Environment Explored**: local (`http://localhost:5173`, project `Private` / 399)
- **User set**: `${TEST_USER}`
- **Analyst**: test-automation-engineer (Axel), combined slot, batch `settings-w05`, 2026-08-27
- **Status**: **ready-for-automation** (with an isolated, filed, soft-asserted defect —
  `.agents/testing.md` § Merge gate → *Analysis-time entry*)
- **Surface digest**: `test-specs/settings-secrets/_surface.md`
- **Filed**: **#1903** (`bug`) — new-secret Save (✓) stays enabled with an EMPTY name.

## Preconditions
- Project `Private` (399). No secret is created or persisted by this case — the inline row
  is always cancelled, never saved (`Cancel` is client-side, zero network, digest-confirmed).

## Test Data
### generate-per-run
- `valid_name`: `autotest_required_<uuid4-hex[:8]>` — used only to satisfy the case's
  step 4; never saved.
- `secret_value`: `name-required-value-<uuid4-hex[:8]>`.

## The product's actual required-name contract (source + live confirmed 2026-08-27)

`EditSecretInputGridTable.jsx` derives its ONLY validation from

```js
const hasInvalidNameChars = field === 'name' && inputValue && !SECRET_NAME_PATTERN.test(inputValue);
```

The `inputValue &&` guard short-circuits on `''`, so an empty name produces **no**
validation error, `SecretsTable.jsx`'s `hasRowValidationErrors(row.id)` is `false`, and the
Save `IconButton` (`disabled={hasValidationErrors}`) stays **enabled** — while the same
component passes `required` to the input, i.e. the UI advertises a requirement it never
enforces.

**Live DOM read, "+" row with an empty name and a filled value:**

```
nameValue:      ""
valueValue:     "empty-name-probe-value"
saveDisabled:   false        <-- case expects disabled (or an inline error)
nameErrorText:  null         <-- no `secret-name-error`
helperTexts:    []           <-- no MUI helper text on the row at all
addButtonDisabled: true      (unrelated: "+" disables while any row is in edit mode)
```

**After typing a valid name** (case steps 4-5), the live read is
`saveDisabled: false`, `nameErrorText: null` — i.e. the case's step 5 expectation
("Save becomes enabled") **holds**, but only because Save was never disabled.

Filed as **#1903**; siblings on other surfaces: #1004, #526 (CLOSED), #633.

**Not probed on purpose:** what happens if Save is clicked with an empty name.
`useSecretRowUpdate.hooks.js` drops the row only when name **and** value are both empty,
so with a value present it would `POST` `name: ""` into shared live project data and could
leave an unnamed secret with no deletable URL path. The case's step 3 does not ask for it,
so the flow stops at the validation gate.

## Test Steps

1. Navigate to `${BASE_URL}/settings/secrets`; verify the page title is `Secrets`.

2. **(Case step 1)** Click **+**.
   - **Verify**: the inline editable row appears (`secret-name-input` visible) — the "+"
     inserts a row rather than opening a modal (digest § Inline create flow).

3. **(Case step 2)** Leave **Name** empty; fill **Value**.
   - **Verify**: `secret-name-input` value is `""` and `secret-value-input` value is the
     generated value — the precondition of step 3 is *asserted*, not assumed.

4. **(Case step 3 — KNOWN DEFECT #1903, isolated soft failure)** Verify the Save button is
   **disabled** OR an inline validation error is shown.
   - **Assert (soft, `# Known defect: #1903`)**: `secret-row-save-button` is disabled
     **or** `secret-name-error` is visible. **Live product satisfies neither** — this
     assertion is written as the *correct expected behaviour* and stays RED until the
     product fix ships (`.agents/testing.md` § Merge gate → sanctioned-RED, analysis-time
     entry). It is deliberately expressed as the case's own OR, so the fix passing via
     *either* branch turns it green.
   - **Assert (hard, Axis 2)**: the row is still in edit mode and nothing was persisted —
     no create `POST` fired during this step. This half is honest today and guards the
     bigger risk: that an empty name silently reached the server.

5. **(Case step 4)** Enter a valid name.
   - **Verify**: `secret-name-input` value == `valid_name` and `secret-name-error` is
     absent (a conforming `[A-Za-z0-9_]` name, so no character-class error either).

6. **(Case step 5)** Verify the Save button is enabled.
   - **Assert (hard)**: `secret-row-save-button` is **enabled**. Passes today.

7. **(Axis 2)** Cancel the row and verify it is discarded without any network call — the
   case creates no secret, and this keeps the shared project clean by construction rather
   than by teardown.

8. **(Axis 2)** No unexpected console errors (`#1203` isolated as a soft failure).

**Teardown:** none needed — nothing is ever saved (asserted in step 7).

## Handles Reference

| Element | Primary handle (testid-only) | Provenance | Notes |
|---|---|---|---|
| Page title | `secrets-page-title` | on-`automation/testids` | existing field |
| Add "+" button | `secrets-add-button` | on-`automation/testids` | existing field |
| Name input | `secret-name-input` | on-`automation/testids` | existing field |
| Value input | `secret-value-input` | on-`automation/testids` | existing field |
| Save (✓) | `secret-row-save-button` | on-`automation/testids` | existing field — the case's subject |
| Cancel (✗) | `secret-row-cancel-button` | on-`automation/testids` | existing field |
| Inline name error | `secret-name-error` | on-`automation/testids` (added by ELITEA-2337) | existing field — the OR's second branch |

**Zero new testids needed.**

## Assertion shape / Fidelity
Every asserted value is read off the live DOM the product rendered, plus the wire (no
create `POST`). No `page.route`, no `route.fulfill`, no injected state, no mocked client,
no `evaluate`.

## Implementer notes
- The step-4 assertion must be a **single soft failure carrying both branches**, so it
  goes green the moment the product fixes it *either* way. Use the file-local
  `soft_failures` + `pytest.fail()` idiom already used by every spec on this surface —
  **not** `pytest.skip`, `xfail`, or a weakened assertion.
- Do NOT click Save in this test (see § not probed on purpose).
- One page-object addition was needed after all: **`type_value()`** — an additive sibling
  of `type_name()`, because `fill_new_row()` always fills BOTH fields and this case must
  fill only the value (these MUI inputs need real keyboard events, not `fill()`, per
  `.claude/rules/mui-patterns.md`). `type_name()` / `click_cancel_button()` cover the rest.
- Assert enabled/disabled with `expect(...).to_be_enabled()` / `.to_be_disabled()`
  (web-first, polling) wherever the state is *asserted*. The step-3 check is a *branch*,
  not an assertion (it decides whether to record the `#1903` soft failure), so it reads the
  state once — after a web-first `expect(...).to_have_value(...)` on both inputs has
  already settled the row.

## Coverage Map

### Axis 1 — every element of the TMS case
| Case element | Expected result (per live product) | Covered by | Asserted where | Disposition |
|---|---|---|---|---|
| Precondition: logged in | authenticated session | `auth_state` | fixture | covered |
| Step 1: Settings → Secrets, click "+" | inline editable row appears | Steps 1-2 | title + `secret-name-input` visible | asserted |
| Step 2: leave Name empty, fill Value | empty name, filled value | Step 3 | both input values asserted | asserted |
| Step 3: Save is disabled **or** an inline error is shown | **NEITHER** — product defect **#1903** | Step 4 | soft assert (`# Known defect: #1903`) on the case's own OR | asserted (RED by design) |
| Step 4: enter a valid name | accepted, no error | Step 5 | input value + `secret-name-error` absent | asserted |
| Step 5: Save becomes enabled | enabled | Step 6 | `to_be_enabled()` | asserted |
| Expected Final State: Save becomes enabled | as step 5 | Step 6 | same | asserted |

### Axis 2 — asserted beyond the case
| Observable | Why |
|---|---|
| no create `POST` fires while the name is empty | the *consequential* half of the defect — a nameless secret reaching the server would be far worse than a mis-enabled button, and the case never checks it |
| the row is discarded on Cancel with zero network calls | keeps shared project data clean by construction; also re-confirms the digest's client-side-Cancel contract |
| no console errors (`#1203` isolated) | project standard |

## Known Defects / Clarifications
- **#1903 (OPEN, filed by this analysis)** — Save (✓) stays enabled with an empty name and
  no inline error, though the field is marked `required`. Isolated to step 3; every other
  step of the case passes. Soft-asserted ⇒ this spec is **sanctioned-RED** on this
  signature until the fix ships, and the case's status is `blocked-on-#1903`, never
  `automated`.
- **#1203 (OPEN)** — React "Maximum update depth exceeded" on mount; isolated soft failure
  (a second sanctioned-RED signature, shared by every spec on this surface).

> **Implementation outcome (2026-08-27, `test_secret_name_required_when_empty.py`):**
> the defect reproduced exactly as analysed — `disabled=False`, `secret-name-error`
> count `0` — recorded as the isolated soft failure for **#1903**. Every other assertion
> PASSED, including the Axis-2 guard that **no create POST fires while the name is
> empty** (so the gap is a UX/validation gap, not a data-integrity one on this path).
> `#1203` fired **33 times**. Two sanctioned-RED signatures on this spec: `#1903` (the
> case's own step 3) and `#1203` (surface-wide).

## Blocked Steps
None — the defect is isolated at the tail of the flow and does not prevent reaching
steps 4-5, so `ready-for-automation` is correct per `.agents/testing.md` § Merge gate →
*Analysis-time entry* (this is that bullet's declared improvisation, cited here).
