# Test Case: Create LLM Model — ID is auto-populated from Display Name

## Metadata
- **TMS ID**: ELITEA-2409
- **Linked Story**: none
- **Priority**: l3 (frontmatter `priority: medium`; folder mapping)
- **Environment Explored**: local (`http://localhost:5173`, `EliteaAI/EliteaUI` on
  `automation/testids` @ `7418c06f`, DEV backend), project `UI Testing` (id 400)
- **User set**: `${TEST_USER}` (`auth_state` fixture)
- **Analyst**: qa-engineer (analyst slot), 2026-08-29, batch `settings-w10`
- **Status**: ready-for-automation
- **Clarification filed**: EliteaAI/elitea-testing-public#1985 (case-text drift, step 4)
- **Surface digest**: `test-specs/settings-ai-providers/_surface.md`

## Case-text drift — step 4 asserts UI that does not exist (reverse-masking guard)

> Case step 4: *"Verify the ID field is editable if needed"*

**The ID field is never editable on this form — by design.** Live:
`toolkit-field-elitea_title-input` carries the DOM `disabled` attribute on a
pristine form and after typing a Display Name (`disabled: True`,
`readOnly: False`). Code, `ToolBase.jsx:245`:

```js
(key === 'elitea_title' && !enableEditEliteaTitle)
```

`enableEditEliteaTitle` is set in exactly one place (`CreateCredential.jsx:128`)
and only when a `prefillId` URL param is present — produced solely by the
`CredentialWarningBanner` "Create a credential" deep link, never by the
AI-Providers "+" flow.

Per `.agents/testing.md` reverse-masking guard the product is correct and the
**case text** is stale. This AFS asserts the **live** contract (the ID is
read-only and mirrors the Display Name); the drift is filed as a CLARIFICATION
(#1985), not a bug.

## Case-identity note
"Settings → AI Configuration → '+' → LLM Model" = `/settings/ai-providers` →
`sidebar-create-button` → `toolkit-type-card-llm_model`. Identity drift already
filed as #1250; not re-filed.

## Preconditions
- `auth_state` fixture.
- **Read-only case.** Nothing is saved; no cleanup, no shared-state mutation.

## Test Data

| Display Name typed | ID observed live |
|---|---|
| `My Test Model` (case's own value) | `my_test_model` |
| `Autotest LLM Model` | `autotest_llm_model` |
| `` (cleared) | `` (ID clears too) |

The derivation is lowercase + **underscore**-separated, not the hyphen slug the
case guesses ("e.g. `my-test-model` or similar slug" — "or similar" covers it).
Assert the derivation **rule**, not one hardcoded string, so a Display Name with
a per-run suffix still works: `id == label.lower().replace(" ", "_")` for the
values this case uses. (Do not over-generalise: punctuation/length handling was
not exercised — `MAX_NAME_LENGTH` truncation exists in `ToolBase.jsx:219`.)

## Test Steps

| # | Action | Expected (verified live 2026-08-29) |
|---|---|---|
| 1 | `/settings/ai-providers` → `sidebar-create-button` → `toolkit-type-card-llm_model` | create form renders; `toolkit-field-label-input` empty, `toolkit-field-elitea_title-input` empty and **disabled** |
| 2 | Type `My Test Model` into `toolkit-field-label-input` | input holds the typed value |
| 3 | Read `toolkit-field-elitea_title-input` value | **`my_test_model`** — auto-populated, no user action on the ID field |
| 4 | Read `toolkit-field-elitea_title-input` `disabled` | **`True`** — the field is read-only (case says "editable"; drift #1985) |

## Expected Results
1. The ID field is empty and disabled on a pristine form.
2. Typing a Display Name auto-populates the ID with the lowercase,
   underscore-separated derivation of that name.
3. The ID field is **not** user-editable — it is a derived, read-only mirror.

## Coverage Map

### Axis 1 — every case element
| Case element | Expected result | Covered by | Asserted where | Disposition |
|---|---|---|---|---|
| Precondition: logged in | — | `auth_state` | fixture | covered (setup) |
| 1. Navigate → "+" → LLM Model | loads | step 1 | URL + form present | covered (identity drift #1250) |
| 2. Type `My Test Model` in Display Name | field accepts and displays it | step 2 | `toolkit-field-label-input` value | covered |
| 3. ID field is automatically populated (slug) | holds | step 3 | `toolkit-field-elitea_title-input` value == `my_test_model` | covered — underscore, not hyphen (case says "or similar") |
| 4. ID field is editable if needed | holds | step 4 | `disabled` property == `True` | **clarification** — asserts the live contract (read-only). Drift #1985 |

### Axis 2 — asserted beyond the case
| Extra observable | Why (grounded) |
|---|---|
| ID is **empty** before any typing | without the before-state, "the ID matches the slug" could pass on a form that pre-filled it from something else entirely |
| ID **clears** when Display Name is cleared | verified live — the ID is a live mirror, not a one-shot derivation. This is the assertion that distinguishes a real binding from a coincidence, and it is what would break first if the derivation were moved to submit time |
| Save stays **disabled** throughout | proves nothing was accidentally submitted; keeps this read-only case honestly read-only |
| No console errors on the create form | verified live: a direct `goto` of the typed create route is **0 errors** (the `#656` React `key` warning belongs to the type-picker page only) |

## Cleanup
None — nothing is saved. Navigate away via the app (a dirty form arms the native
`beforeunload` dialog; see § Automation Hints).

## Concrete Handles

| Purpose | Handle | Provenance (fresh `git fetch origin`, 2026-08-29) |
|---|---|---|
| "+" create button | `sidebar-create-button` | on-main ✓ |
| LLM Model type card | `toolkit-type-card-llm_model` | on-main ✓ |
| Display Name input | `toolkit-field-label-input` (`CredentialFormFieldsMixin.display_name_input`) | on-main ✓ |
| ID input | `toolkit-field-elitea_title-input` (`CredentialFormFieldsMixin.id_input`) | on-main ✓ |
| Save (asserted disabled) | `credential-form-save-button` | on-main ✓ |

**No new testid is required for this case.** State is read from the input's own
`disabled` property — not from a state-variant testid
(`.agents/testing.md` § Locator policy).

## Network Behavior
The derivation is **purely client-side** (`ToolBase.jsx:216-219`) — typing into
Display Name fires no request. Never wait on network for step 3; wait on the ID
input's value.

## Known Defects Found During Exploration
- None for this case. (The same form's `Name`-field validation gap is
  EliteaAI/elitea-testing-public#1984, ELITEA-2408's subject — out of scope here.)
- Related observation recorded in ELITEA-2396's AFS: on the **edit** form the ID
  also re-derives when the Display Name changes, despite being disabled.

## Blocked Steps
None.

## Automation Hints
- Page object: `CredentialFormFieldsMixin` already declares both inputs; no new
  descriptors needed.
- After a direct `goto` to `/settings/create-ai-provider/llm_model`, **wait for
  `toolkit-field-label-input`** — the form mounts seconds after navigation
  (schema fetch). A `fill()` straight after `goto` fails.
- The ID updates synchronously with the Display Name input event; use Playwright's
  `expect(...).to_have_value(...)` (auto-retrying), never a sleep.
- A dirty form arms a native `beforeunload` dialog on reload/`goto` — it blocks
  every subsequent call until handled. Clear the fields or register a handler.
- Console via `utils/console_errors.collect_console_errors()` + `#1971` filter.
- `with allure.step("Step N — …")`. **Markers as shipped:** `ui`, `settings`,
  `p2`, `regression`, `new` — this folder maps l3 to `p2` (sibling ELITEA-2392 /
  ELITEA-2397 specs), amended at implementation.
