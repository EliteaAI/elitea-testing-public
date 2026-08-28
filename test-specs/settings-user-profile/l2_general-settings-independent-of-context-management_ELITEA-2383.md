# Test Case: Personality settings are independent of the context-management toggle

## Metadata
- **TMS ID**: ELITEA-2383
- **Priority**: l2 (case priority `high`)
- **Environment Explored**: local (`http://localhost:5173`, `EliteaAI/EliteaUI` `automation/testids`, DEV backend)
- **User set**: `${TEST_USER}` (localhost `auth_state` bypass via `VITE_DEV_TOKEN`)
- **Analyst**: qa-engineer, batch `settings-w08`, cluster ELITEA-2381/2382/2383/2384, 2026-08-29
- **Status**: ready-for-automation
- **Surface digest**: `test-specs/settings-user-profile/_surface.md` →
  `_surface/personalization-family.md` + `_surface/memory-context-management.md`
- **Clarifications**: EliteaAI/elitea-testing-public#1960 (route drift + "Click
  Save" + this case's premise — comment added), #1238, #1244

## Case-text drift — and why the case is still worth automating

The case assumes **one page** carrying both the context-management toggle and
the personality controls, ending with a **Save** button. Neither holds:

| Case text | Live product |
|---|---|
| "Navigate to Personalization" | No such page. The **toggle** is on `/settings/memory` (`CONTEXT MANAGEMENT` accordion); the **Default Personality dropdown + Default User Instructions textarea** are on `/settings/ai-personality` (`PERSONA MANAGEMENT`) |
| Step 3: personality controls "remain editable and are NOT grayed out" | Structurally unreachable *as a co-location risk* — they are not on the toggle's page at all. Verified live: `[data-testid="ai-personality-persona-select"]` has **count 0** on `/settings/memory` |
| Step 5: "Click Save" | **There is no Save button** on `/settings/preferences`, `/settings/memory` or `/settings/ai-personality`. All three autosave. Already recorded on #1960 / #1244 |

**This is case-text drift, not a defect** (reverse-masking guard) — and the
case is **not** vacuous. The risk it is pointing at survives the relocation and
is now *more* interesting than the case knew: **one `PUT /api/v2/social/author/`
carries both structures** — `personalization.persona` /
`personality_instructions` *and* `default_context_management`. So a
personality write that clobbered the context-management state, or a
context-management write that reset the persona, would be a real regression
that no other spec in the suite would catch. The spec therefore asserts the
live contract: *editable while the toggle is off*, **plus** *neither write
disturbs the other's state*.

## Not already covered — checked

- `automation/tests/ui/settings/test_context_management_toggle.py` (ELITEA-2374,
  on batch trunk) covers the toggle enabling/disabling the **numeric** fields on
  `/settings/memory`. It never leaves that route and never touches persona.
- `test_personalization_autosave_no_save_button.py` (ELITEA-2387, on batch
  trunk) covers persona autosave on `/settings/ai-personality`, with the
  context-management toggle in whatever state it happened to be. It asserts
  nothing about the two being independent.
- No spec asserts the cross-structure invariant. Fresh spec.

## Preconditions
- User is logged in (`auth_state`; localhost bypass).
- **Shared mutable account state, two structures.** The spec flips
  `default_context_management.enabled` and changes `personalization.persona`,
  both on the shared `${TEST_USER}` record. Read-before-write and restore
  **both**. Observed at the start of this session: toggle **ON**,
  `max_context_tokens: 32000`, `preserve_recent_messages: 3`, persona
  `Generic` — all restored at the end. **Never hardcode these as defaults.**
- Order matters for teardown: restore the toggle last, so a failed persona
  restore cannot leave the toggle off for every other settings spec.

## Test Data
### read-live
| Field | Value |
|---|---|
| Toggle state under test | OFF (case step 2) |
| Persona the case selects | `Quirky` (value `quirky`) |
| Fallback persona | `Nerdy` (value `nerdy`) — used only if the account already sits on `Quirky`, so the change is always a real change |

## Test Steps
1. **Setup / baseline.** Navigate to `${BASE_URL}/settings/memory`; wait for
   `context-management-section`.
   - Read and store the toggle's checked state (teardown).
   - Navigate to `${BASE_URL}/settings/ai-personality`; wait for
     `ai-personality-persona-select-combobox`; read and store the persona
     label (teardown).
2. **Case step 1 — navigate to the settings area.** Back to
   `${BASE_URL}/settings/memory`.
   - **Verify**: `settings-nav-item-memory` has `data-active="true"`;
     `context-management-section` is visible.
3. **Case step 2 — turn OFF the context management toggle.** If it is already
   off, turn it on first so the case's action is a real transition. Click
   `context-management-toggle` wrapped in
   `page.expect_response(<PUT /api/v2/social/author/>)`.
   - **Verify**: the PUT returns **200**.
   - **Verify**: the toggle reads OFF. *(Amended during implementation: the
     established reader is
     `UserProfileSettingsPage.is_context_management_enabled()`, which checks the
     `Mui-checked` class on the `SwitchBase` `<span>` the testid sits on —
     Playwright's `is_checked()` raises "Not a checkbox or radio button" on that
     span, and the suite already standardised on the class read. Same
     observable, existing mechanism, no new handle.)*
   - **Verify (the toggle really took effect)**: `max-context-tokens-input` has
     **count 0** — the numeric fields are conditionally **unmounted** when the
     toggle is off. `to_have_count(0)`, not `not_to_be_visible()`; this is the
     unmount mechanism, not the accordion's `visibility: hidden` one.
4. **Case step 3 — verify the personality controls remain editable and are not
   grayed out.** Navigate to `${BASE_URL}/settings/ai-personality`; wait for
   the select.
   - **Verify (present)**: `ai-personality-persona-section`,
     `ai-personality-persona-select-combobox` and
     `ai-personality-user-instructions-textarea` are all visible.
   - **Verify (editable)**: the textarea is `to_be_editable()` (neither
     `disabled` nor `readonly`); the persona combobox has **no**
     `aria-disabled="true"`.
   - **Verify (not grayed out)**: no element inside
     `ai-personality-persona-section` carries MUI's disabled marker — assert
     the `.Mui-disabled` collection scoped under the section testid has count
     **0**. *(Scoped raw handle, #579 discipline: the parent is the real app
     testid and the class selector is chained off it. Declare the exception in
     the page-object method's docstring — a class that MUI adds cannot carry a
     testid.)*
   - **Verify (interactive, not merely present)**: open the option list and
     confirm `select-option-quirky` is visible, then close it. A control can be
     visible and still refuse to open.
5. **Case step 4 — change the Default Personality to "Quirky"**, wrapped in
   `page.expect_response(<PUT /api/v2/social/author/>)`.
   - **Verify**: the PUT returns **200** — this is the live equivalent of the
     case's "Click Save" (#1960: the page autosaves; there is no Save button).
   - **Verify**: `ai-personality-persona-select-combobox` reads `Quirky`.
6. **Case step 5 — verify the settings saved without error.**
   - **Verify (absence of a Save button)**: no `Save` control exists in the
     content pane. Reuse `SettingsPersonalizationPage.save_buttons()` /
     `page_save_buttons()` → `to_have_count(0)`. This is the honest rendering
     of the case's step 5, and it is a first-class absence assertion.
   - **Verify (no error surface)**: no error toast/alert appeared.
7. **Beyond the case — the independence invariant (the point of this case).**
   Navigate back to `${BASE_URL}/settings/memory` and re-read the toggle.
   - **Verify**: the toggle is **still OFF** — the persona write did not
     re-enable context management.
   - **Verify**: `max-context-tokens-input` still has count 0.
   *(Live evidence 2026-08-29: the author payload fetched immediately after the
   persona PUT read `personalization.persona: "quirky"` **and**
   `default_context_management.enabled: false` — both structures intact in the
   same response.)*
8. **Beyond the case — the inverse direction.** Turn the toggle back ON
   (assert its PUT → 200), then return to `/settings/ai-personality`.
   - **Verify**: the persona still reads `Quirky` — the context-management
     write did not reset the personality. This is the half the case never
     asks for and the half a shared-payload bug is most likely to break.
9. **Beyond the case — no unexpected console errors.** Collect via
   `utils/console_errors.collect_console_errors(page)`; assert empty after
   filtering the known `disableUnderline` message (`# Known defect: #1771` —
   fires on **both** `/settings/memory` and `/settings/ai-personality`).
10. **Teardown** — restore the persona first, then the toggle, each asserting
    its own PUT; route-guarded, strict on the success path, best-effort on the
    failure path.

## Expected Results
- Turning the context-management toggle OFF unmounts the numeric fields on
  `/settings/memory` and changes nothing about `/settings/ai-personality`.
- The `Default persona` select and `User instructions` textarea stay visible,
  enabled, editable and un-grayed with the toggle off.
- Changing the persona while the toggle is off saves successfully
  (`PUT /api/v2/social/author/` → 200), with no Save button anywhere.
- Neither write disturbs the other structure: `default_context_management`
  stays `enabled: false` across the persona write, and the persona survives the
  toggle write.

## Handles Reference

All primary handles are testids. **PROVENANCE verified 2026-08-29 after
`cd ../EliteaUI && git fetch origin`.**

| Element | Primary handle (testid) | Shape | Provenance |
|---|---|---|---|
| CONTEXT MANAGEMENT accordion | `context-management-section` | `LocatorDescriptor` — already on `SettingsPersonalizationPage` | on `automation/testids` only |
| Context management toggle | `context-management-toggle` | `LocatorDescriptor` — already present. Testid is on the MUI `SwitchBase` `<span>`; read `checked` from the `<input>` inside it | on `automation/testids` only |
| Max Context Tokens field (unmount probe) | `max-context-tokens-input` | `LocatorDescriptor` — already on `UserProfileSettingsPage` | on `automation/testids` only |
| PERSONA MANAGEMENT accordion | `ai-personality-persona-section` | `LocatorDescriptor` — already present | on `automation/testids` only (EliteaAI/EliteaUI@fa505e37) |
| Default persona display / opener | `ai-personality-persona-select-combobox` | `LocatorDescriptor` — already present | on `automation/testids` only (EliteaAI/EliteaUI@fa505e37) |
| User instructions textarea | `ai-personality-user-instructions-textarea` | `LocatorDescriptor` — already present | on `automation/testids` only (EliteaAI/EliteaUI@fa505e37) |
| Persona option row | `select-option-{value}` | dynamic class constant `SELECT_OPTION` | on `main` ✓ |
| Settings nav item | `settings-nav-item-{tab}` | dynamic class constant `SETTINGS_NAV_ITEM` | on `automation/testids` only |

**No new testid is needed for this case.**

**One sanctioned scoped raw handle** (`#579` discipline): the "not grayed out"
assertion needs MUI's `.Mui-disabled` marker class, which the app cannot put a
testid on. Chain it off the `ai-personality-persona-section` testid parent
(`self.persona_section.locator(".Mui-disabled")` as an UPPER_CASE class
constant), declare the exception in the method docstring, and do not extend it
to anything that could carry a testid.

## Automation Hints

- **Two page objects, one spec.** `SettingsPersonalizationPage` already covers
  both routes (`open_settings_tab("memory")` / `("ai-personality")`), the
  toggle, the persona select and the Save-button absence handles. Add only a
  disabled-marker reader and a toggle checked-state reader.
- **Two hide mechanisms on this surface — pick per control.** The toggle
  **unmounts** its numeric fields (`to_have_count(0)`); a collapsed accordion
  merely hides children (`visibility: hidden` → `not_to_be_visible()`). Using
  the wrong one silently passes.
- **Assert every PUT, never `wait_for_autosave()`** (`networkidle` never
  settles — #1847).
- **Teardown order is load-bearing**: persona first, toggle last.
- **Console filter `disableUnderline` applies to both routes** in this spec.
- Markers: `ui`, `settings`, `p2`, `regression`; steps wrapped in
  `with allure.step("Step N — …")`.
- Suggested location:
  `automation/tests/ui/settings/test_personality_independent_of_context_management.py`.

## Fidelity Declaration

**No substitutions.** Every asserted value is produced by the running app —
toggle state read from the live DOM, save outcomes from real
`PUT /api/v2/social/author/` responses, cross-structure independence verified
by re-reading the *other* page after each write. No `page.route`, no
`route.fulfill`, no injected state, no API-seeded precondition (the toggle is
flipped through the UI exactly as the case says). `auth_state` is the
framework's standard login fast-path and is not this case's subject.

## Coverage Map

### Axis 1 — Case coverage

| Case element | Expected result | Covered by (AFS step) | Asserted where | Disposition |
|---|---|---|---|---|
| Precondition: user logged in | — | fixture | `auth_state`; pages load | asserted (implicitly) |
| 1 Navigate to Personalization | Page loads | AFS step 2 | `data-active` + `context-management-section` visible | clarification *(live route is Settings → Memory; #1960/#1238)* |
| 2 Turn OFF the context management toggle | Completes without error | AFS step 3 | PUT → 200; input unchecked; numeric fields count 0 | asserted |
| 3 Verify the Default Personality dropdown and Default User Instructions textarea remain editable and are NOT grayed out | Condition holds | AFS step 4 | visible + editable + no `aria-disabled` + `.Mui-disabled` count 0 + option list opens | asserted *(on `/settings/ai-personality` — the controls are not co-located with the toggle; #1960)* |
| 4 Change the Default Personality to "Quirky" | Completes without error | AFS step 5 | PUT → 200; combobox reads `Quirky` | asserted |
| 5 Click Save — verify the settings save without error | Control responds | AFS step 6 | Save-button count 0 (page autosaves) + no error surface | clarification *(no Save button exists; #1960/#1244 — the autosave PUT's 200 is the live equivalent)* |
| Expected final state: settings save without error | — | AFS steps 5–6 | PUT 200 + no error | asserted |

### Axis 2 — Assertions beyond the case

| Observable | Why | AFS step |
|---|---|---|
| The toggle is still OFF after the persona write | This is the case's actual subject, made assertable. One `PUT` carries both structures, so a serialization bug could clobber the toggle — nothing else in the suite would catch it | 7 |
| The persona survives the toggle write (inverse direction) | Independence is symmetric; the case only asks one way, and the other way is equally likely to break | 8 |
| Numeric fields have count 0 while the toggle is off | Proves the toggle actually took effect, so step 4's "editable" result is being read under the real precondition rather than a no-op | 3 |
| Persona option list actually opens | A control can be visible and enabled-looking yet not interactive; "editable" without an interaction is a weak assertion | 4 |
| No Save button in the content pane (absence assertion) | The honest rendering of case step 5, and a guard: if a Save button ever appears here, the autosave premise this whole family rests on has stopped holding | 6 |
| No unexpected console errors (filtering #1771) | Silent errors ship; both routes have exactly one known, linked error | 9 |

## Known Defects
None found. Case-text clarifications on #1960 (route drift, Save button, the
co-location premise) — the product is correct.

## Blocked Steps
None.
