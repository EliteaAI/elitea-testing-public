# Test Case: Default User Instructions text persists after save and reload

## Metadata
- **TMS ID**: ELITEA-2382
- **Priority**: l3 (case priority `medium`)
- **Environment Explored**: local (`http://localhost:5173`, `EliteaAI/EliteaUI` `automation/testids`, DEV backend)
- **User set**: `${TEST_USER}` (localhost `auth_state` bypass via `VITE_DEV_TOKEN`)
- **Analyst**: qa-engineer, batch `settings-w08`, cluster ELITEA-2381/2382/2383/2384, 2026-08-29
- **Status**: ready-for-automation
- **Surface digest**: `test-specs/settings-user-profile/_surface.md` →
  `_surface/personalization-family.md`
- **Clarifications**: EliteaAI/elitea-testing-public#1960 (route drift +
  per-persona storage — comment added for this case)

## Case-text drift — this spec asserts the LIVE contract

1. **"Navigate to Personalization → GENERAL section"** — no such page. The
   `Default User Instructions` textarea is the `User instructions` field of the
   `PERSONA MANAGEMENT` accordion on **Settings → AI Personality**
   (`/settings/ai-personality`). #1960.
2. **The field is NOT global — it is stored per persona.**
   `AIPersonalityPersonalization.jsx` writes
   `personality_instructions.<persona>`; the textarea renders the slot for the
   *currently selected* persona only, and is **absent from the DOM entirely
   when the persona is `None`** (`values.persona !== 'none'` guard). Verified
   live: text saved under `Nerdy` read back empty after switching the select to
   `Quirky`, and the server payload showed the text in the `nerdy` key only.
   **Consequence for automation: the spec must pin the persona** before typing
   and read back under the *same* persona, or the assertion is
   non-deterministic on whatever the previous run left. The case text is silent
   on this — clarification recorded on #1960.

Both are **case-text stale, product correct** (reverse-masking guard) — assert
the live contract, do not file as a defect.

## Not already covered — checked

- `automation/tests/ui/settings/test_personalization_autosave_no_save_button.py`
  (ELITEA-2387, on batch trunk) proves autosave-and-persist for the **persona
  select**, and reads the instructions textarea's `placeholder` only. It never
  types into the field, never saves a value, and never reads the field's
  `value` back. Different control, different storage slot → not coverage.
- `grep -rn "user-instructions\|personality_instructions" automation/tests/`
  finds no other spec touching this field.

Fresh spec, reusing `SettingsPersonalizationPage`.

## Preconditions
- User is logged in (`auth_state`; localhost bypass).
- **Shared mutable account state** — both `persona` and the
  `personality_instructions` map live on the shared `${TEST_USER}` record and
  feed real chat behaviour (see ELITEA-2384). Read-before-write and restore
  **both** in teardown: the persona label AND the original text of the slot the
  spec writes.

## Test Data
### create-per-run
| Field | Value |
|---|---|
| Persona pinned for the run | `Nerdy` (value `nerdy`) — any non-`none` persona works; pinning makes the read-back deterministic |
| Instructions text | `Always respond in a concise manner. Focus on practical solutions.` (verbatim from case step 3) |
| Discriminator persona | `Quirky` (value `quirky`) — used only by the Axis-2 per-persona-isolation check |

## Test Steps
1. **Case step 1 — open the page.** Navigate to
   `${BASE_URL}/settings/ai-personality`; wait for
   `ai-personality-persona-select-combobox` (render race — element wait, never
   a sleep).
   - **Verify**: `settings-nav-item-ai-personality` has `data-active="true"`;
     `ai-personality-persona-section` is visible.
   - Read and store the current persona label (teardown).
2. **Setup — pin the persona to `Nerdy`** (skipped when already there), wrapped
   in `page.expect_response(<PUT /api/v2/social/author/>)`; assert 200.
   - **Verify**: `ai-personality-user-instructions-textarea` is visible and its
     `placeholder` is `No custom instructions for the Nerdy persona yet. Type
     here to add some.` — proves the field is showing the *Nerdy* slot, so the
     read-back in step 6 is unambiguous.
   - Read and store the slot's current `value` (teardown).
3. **Case step 2 — click the Default User Instructions textarea.**
   Click `ai-personality-user-instructions-textarea`.
   - **Verify**: it is the focused element, and is neither `disabled` nor
     `readonly`.
4. **Case step 3 — enter the text.** Fill the textarea with the § Test Data
   string.
   - **Verify**: the field's `value` equals the entered text.
5. **Case step 4 — click outside to trigger autosave.** Blur the textarea by
   clicking a neutral area of the content pane, wrapped in
   `page.expect_response(<PUT /api/v2/social/author/>)`.
   - **Verify**: the autosave response status is **200**.
   - ⚠️ Do **not** blur onto the `PERSONA MANAGEMENT` accordion header — that
     collapses the section (confirmed live).
   - Blur genuinely is the trigger here (unlike the persona select):
     `AIPersonalityFormContent` wraps the form in
     `useFormikAutoSaveOnBlur`'s `onBlur`, and `handleInstructionsChange` does
     **not** call `onAutoSaveRequested` itself.
6. **Case step 5 — reload the page.** `page.reload()`; wait for the select,
   then for the textarea.
7. **Case step 6 — verify the field shows the entered text.**
   - **Verify**: `ai-personality-user-instructions-textarea` `value` equals the
     § Test Data string.
   - **Verify**: the persona select still reads `Nerdy` (the reload restored
     the same slot, so the value read is the one that was written).
8. **Beyond the case — per-persona isolation.** Switch the select to `Quirky`
   (assert its PUT → 200).
   - **Verify**: the textarea's `value` is empty and its `placeholder` names
     the *Quirky* persona.
   - Switch back to `Nerdy` (assert PUT → 200) and **verify** the text
     reappears.
9. **Beyond the case — no unexpected console errors.** Collect via
   `utils/console_errors.collect_console_errors(page)`; assert empty after
   filtering the known `disableUnderline` message (`# Known defect: #1771`).
10. **Teardown — restore both** the original instructions text for the pinned
    slot (blur + assert the PUT) and the original persona, route-guarded;
    strict on the success path, best-effort on the failure path.

## Expected Results
- The textarea accepts the text and shows it immediately.
- Blurring the field fires `PUT /api/v2/social/author/` → 200.
- After a full page reload the field still shows
  `Always respond in a concise manner. Focus on practical solutions.`
- Confirmed live end-to-end 2026-08-29: the text survived a full reload, and
  the server payload showed
  `personality_instructions.nerdy = "Always respond in a concise manner. Focus
  on practical solutions."` with every other persona slot `""`.

## Handles Reference

All primary handles are testids. **PROVENANCE verified 2026-08-29 after
`cd ../EliteaUI && git fetch origin`.**

| Element | Primary handle (testid) | Shape | Provenance |
|---|---|---|---|
| PERSONA MANAGEMENT accordion | `ai-personality-persona-section` | `LocatorDescriptor` — already present | on `automation/testids` only (EliteaAI/EliteaUI@fa505e37) — awaiting human promotion to `main` |
| Default persona display / opener | `ai-personality-persona-select-combobox` | `LocatorDescriptor` — already present | on `automation/testids` only (EliteaAI/EliteaUI@fa505e37) |
| Persona option row | `select-option-{value}` | dynamic class constant `SELECT_OPTION` (already on the page object) | on `main` ✓ (generic `SingleSelect.jsx:416`) |
| **User instructions textarea** | `ai-personality-user-instructions-textarea` | `LocatorDescriptor` — already present; applied via `inputProps={{ 'data-testid': … }}` so it lands on the `<textarea>` itself (confirmed live: `tagName === "TEXTAREA"`) | on `automation/testids` only (EliteaAI/EliteaUI@fa505e37) |
| Settings nav item | `settings-nav-item-{tab}` | dynamic class constant `SETTINGS_NAV_ITEM` | on `automation/testids` only |

**No new testid is needed for this case.**

## Automation Hints

- **Reuse `SettingsPersonalizationPage`.** It already exposes
  `user_instructions_textarea`, `wait_for_persona_select()`, `get_persona()`,
  `select_persona()` and `open_settings_tab()`. Add only what this case needs:
  a `get_user_instructions()` / `set_user_instructions()` pair and a neutral
  blur target — all as page-object methods over existing class-level
  descriptors.
- **The blur target matters.** The accordion header collapses the section;
  pick a neutral node inside `settings-content`, or blur by clicking the
  persona-select label area. Whatever is chosen, assert afterwards that
  `ai-personality-persona-section`'s summary is still `aria-expanded="true"`.
- **Assert the PUT, never `wait_for_autosave()`** (`networkidle` never settles
  here — #1847). `AUTHOR_SETTINGS_ENDPOINT` is exported from the page-object
  module.
- **Restore two things, not one.** A run that restores the persona but leaves
  text in a slot pollutes ELITEA-2384's `instructions` observable — the two
  cases read the same account field.
- Markers: `ui`, `settings`, `p3`, `regression`; steps wrapped in
  `with allure.step("Step N — …")`.
- Suggested location:
  `automation/tests/ui/settings/test_default_user_instructions_persist.py`.

## Fidelity Declaration

**No substitutions.** The text is typed into the real control, saved by the
product's own blur-autosave, and re-read after a real page reload — the value
asserted is the one the server returned. No `page.route`, no `route.fulfill`,
no injected state. `auth_state` is the framework's standard login fast-path and
is not the subject of this case.

## Coverage Map

### Axis 1 — Case coverage

| Case element | Expected result | Covered by (AFS step) | Asserted where | Disposition |
|---|---|---|---|---|
| Precondition: user logged in | — | fixture | `auth_state`; page loads | asserted (implicitly) |
| 1 Navigate to Personalization → GENERAL section | Section loads | AFS step 1 | URL + `data-active` + section visible | clarification *(live route is Settings → AI Personality; #1960)* |
| 2 Click the Default User Instructions textarea | Control responds | AFS step 3 | focused, not disabled/readonly | asserted |
| 3 Enter the instructions text | Field accepts and displays it | AFS step 4 | `value` == the entered text | asserted |
| 4 Click outside to trigger autosave | Control responds | AFS step 5 | blur fires `PUT` → 200 | asserted |
| 5 Reload the page | Completes without error | AFS step 6 | `page.reload()`; select + textarea re-render | asserted |
| 6 Verify the field shows the entered text | Condition holds | AFS step 7 | `value` == the entered text after reload | asserted |
| Expected final state: field shows the entered text | — | AFS step 7 | same | asserted |
| *(implicit in the case: one global instructions field)* | — | AFS step 2 + 8 | persona pinned before typing; per-persona isolation asserted | clarification *(field is per-persona — #1960)* |

### Axis 2 — Assertions beyond the case

| Observable | Why | AFS step |
|---|---|---|
| Autosave `PUT` returns **200** | "The text is still there after reload" could in principle be served by a cache; only the write's status proves a save happened | 5 |
| Placeholder names the pinned persona before typing | Makes the read-back unambiguous — without it the spec could write one slot and read another | 2 |
| Per-persona isolation (`Quirky` slot empty, `Nerdy` slot restored) | This is the product's actual storage contract and the single most likely thing to regress in a refactor; it is invisible to the case as written | 8 |
| Persona select still reads `Nerdy` after reload | Guards the step-7 read: a reload that landed on a different persona would be reading a different slot | 7 |
| Textarea is not `disabled` / `readonly` | The case says "field accepts the input"; asserting only the value would pass on a readonly field pre-filled by a previous run | 3 |
| No unexpected console errors (filtering #1771) | Silent errors ship; the route has exactly one known, linked error | 9 |

## Known Defects
None found. Case-text clarifications recorded on #1960 — the product is
correct.

## Blocked Steps
None.
