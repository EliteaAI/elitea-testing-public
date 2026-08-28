# Test Case: Default Personality dropdown shows all documented options

## Metadata
- **TMS ID**: ELITEA-2381
- **Priority**: l3 (case priority `medium`)
- **Environment Explored**: local (`http://localhost:5173`, `EliteaAI/EliteaUI` `automation/testids`, DEV backend)
- **User set**: `${TEST_USER}` (localhost `auth_state` bypass via `VITE_DEV_TOKEN`)
- **Analyst**: qa-engineer, batch `settings-w08`, cluster ELITEA-2381/2382/2383/2384, 2026-08-29
- **Status**: ready-for-automation
- **Surface digest**: `test-specs/settings-user-profile/_surface.md` →
  `_surface/personalization-family.md`
- **Clarifications**: EliteaAI/elitea-testing-public#1963 (six-vs-seven option
  count), EliteaAI/elitea-testing-public#1960 (route drift — comment added for
  this case)

## Case-text drift — this spec asserts the LIVE contract

Two divergences, both **case-text stale, product correct** (reverse-masking
guard — do not classify as `defect-found`, do not assert the stale text):

1. **The case title says "six documented options"; its own step table lists
   seven** (steps 4–10: Generic, QA, Nerdy, Quirky, Cynical, None, Bare) and
   the live dropdown renders exactly those **seven**. Source of truth:
   `PERSONA_OPTIONS`, `EliteaUI` `src/common/constants.js:1120-1132`.
   **Assert seven.** Clarification #1963.
2. **"Navigate to Personalization → GENERAL section"** — no such page.
   Default Personality is the `Default persona` select of the
   `PERSONA MANAGEMENT` accordion on **Settings → AI Personality**
   (`/settings/ai-personality`). `GENERAL` on `/settings/preferences` carries
   the Theme toggle only. Clarification #1960.
3. **Step 12 "Click outside to trigger autosave"** — not this control's
   mechanism. `handlePersonaChange` calls `onAutoSaveRequested` directly, so
   the `PUT` fires on selection, before any outside click. Executing the step
   is harmless (it is a no-op) — the spec keeps it, so the case's step count
   is honoured, and asserts the PUT around the *selection*.

## Not already covered — checked

`automation/tests/ui/settings/test_personalization_autosave_no_save_button.py`
(ELITEA-2387, on batch trunk `tests/batch-settings-w08`) drives the same select
and covers the *tail* of this case (select a persona → autosave PUT 200 →
combobox shows the new label, steps 11–13). It never opens the option list and
never asserts what the list contains — which is this case's whole subject per
its title. That is the inverse of the `extend-existing` shape (most of the case
missing, a small tail covered), so this is a **fresh spec** that reuses
`SettingsPersonalizationPage` rather than an extension.

## Preconditions
- User is logged in (`auth_state`; localhost bypass).
- **Shared mutable account state.** `persona` lives on the shared `${TEST_USER}`
  record and drives chat behaviour. Read-before-write, restore in teardown, and
  never hardcode a "default" — observed `Generic` at the start of this session
  and restored to `Generic` at the end, but the next run may find anything.
  Reuse the route-guarded `_restore_persona` / `_restore_persona_best_effort`
  shape from ELITEA-2387's spec (see § Automation Hints).

## Test Data
### read-live (no fixture data required)
| Field | Value |
|---|---|
| Expected option set | the seven rows of the § Expected Results table, in DOM order |
| Persona selected by the case | `Nerdy` (value `nerdy`) |
| Fallback target | `Generic` (value `generic`) — used only if the account already sits on `Nerdy`, so the change is always a real change |

## Test Steps
1. **Case step 1 — open the page.** Navigate to Settings → AI Personality
   (`${BASE_URL}/settings/ai-personality`).
   - **Verify**: URL is `${BASE_URL}/settings/ai-personality`;
     `settings-nav-item-ai-personality` has `data-active="true"`;
     `ai-personality-persona-section` is visible.
   - Wait on `ai-personality-persona-select-combobox` (render race — the select
     is briefly absent right after the route resolves; an element wait, never a
     sleep).
   - Read and store the current persona label for teardown.
2. **Case step 2 — click the Default Personality dropdown.**
   Click `ai-personality-persona-select-combobox`.
   - **Verify**: the option list is open — `select-option-generic` is visible.
3. **Case steps 3–10 — verify the option set.**
   - **Verify (count)**: exactly **7** options are rendered — assert the count
     on the `select-option-*` collection, not just presence of each, so a new
     eighth option fails the test instead of passing silently.
   - **Verify (identity + order)**: the rendered labels, read in DOM order,
     equal `["Generic", "QA", "Nerdy", "Quirky", "Cynical", "None", "Bare"]`.
   - **Verify (each option individually addressable)**: for each value in
     `generic, qa, nerdy, quirky, cynical, none, bare`, the row
     `[data-testid="select-option-<value>"]` is visible and its text contains
     the label from § Expected Results.
   - **Verify (current selection)**: the row matching the persona read in
     step 1 carries `aria-selected="true"`; every other row `"false"`.
4. **Case step 11 — select a different personality.** Click
   `select-option-nerdy` (or `select-option-generic` when the account was
   already on `Nerdy`), wrapped in
   `page.expect_response(<PUT /api/v2/social/author/>)`.
   - **Verify**: the autosave response status is **200**.
5. **Case step 12 — click outside to trigger autosave.** Click a neutral area
   of the content pane. This is a no-op for this control (the PUT already
   landed in step 4) and the spec says so in its docstring; the step is
   executed so the case's flow is honoured.
   - ⚠️ Do **not** use the accordion header as the "outside" target — clicking
     it collapses `PERSONA MANAGEMENT` (confirmed live: `aria-expanded` flipped
     to `false`).
   - **Verify**: `ai-personality-persona-section`'s summary still reads
     `aria-expanded="true"` (the click did not collapse the section).
6. **Case step 13 — verify the dropdown shows the new personality.**
   - **Verify**: `ai-personality-persona-select-combobox` has text `Nerdy`.
7. **Beyond the case — verify the selection is server-persisted**, not just
   held in the SPA store: `page.reload()`, wait for the select, re-assert the
   label.
8. **Beyond the case — no unexpected console errors.** Collect via
   `utils/console_errors.collect_console_errors(page)` and assert the list is
   empty **after filtering the known `disableUnderline` message**
   (`# Known defect: #1771` — `/settings/ai-personality` logs exactly one on
   every load). Filter by that fragment only; anything broader is masking.
9. **Teardown — restore the original persona**, asserting the restore's own
   PUT returns 200 on the success path and best-effort on the failure path.

## Expected Results

The `Default persona` select renders exactly these seven options, in this DOM
order (labels and descriptions verified live 2026-08-29):

| # | testid | value | Label | Description |
|---|---|---|---|---|
| 1 | `select-option-generic` | `generic` | Generic | Balanced, professional assistant |
| 2 | `select-option-qa` | `qa` | QA | Precise, technical, testing-focused |
| 3 | `select-option-nerdy` | `nerdy` | Nerdy | Technical deep-dives, detailed explanations |
| 4 | `select-option-quirky` | `quirky` | Quirky | Creative, playful, thinking outside the box |
| 5 | `select-option-cynical` | `cynical` | Cynical | Skeptical, challenges assumptions |
| 6 | `select-option-none` | `none` | None | No personality overlay applied |
| 7 | `select-option-bare` | `bare` | Bare | No Elitea identity — only your instructions plus tool-required guidance |

Selecting `Nerdy` fires `PUT /api/v2/social/author/` → 200 immediately, the
combobox reads `Nerdy`, and the value survives a full page reload.

## Handles Reference

All primary handles are testids. **PROVENANCE verified 2026-08-29 after
`cd ../EliteaUI && git fetch origin`.**

| Element | Primary handle (testid) | Shape | Provenance |
|---|---|---|---|
| PERSONA MANAGEMENT accordion | `ai-personality-persona-section` | `LocatorDescriptor` — already on `SettingsPersonalizationPage` | on `automation/testids` only (EliteaAI/EliteaUI@fa505e37) — awaiting human promotion to `main` |
| Default persona select wrapper | `ai-personality-persona-select` | `LocatorDescriptor` — already present | on `automation/testids` only (EliteaAI/EliteaUI@fa505e37) |
| Default persona display / opener | `ai-personality-persona-select-combobox` | `LocatorDescriptor` — already present; derived by `SingleSelect` as `${dataTestId}-combobox` | on `automation/testids` only (EliteaAI/EliteaUI@fa505e37) |
| Option row (any persona) | `select-option-{value}` | **dynamic** — class constant `SELECT_OPTION = '[data-testid="select-option-{}"]'`, already on `SettingsPersonalizationPage:239`. Never an inline f-string | on `main` ✓ — generic `SingleSelect.jsx:416` testid, pre-existing |
| Settings nav item | `settings-nav-item-{tab}` | dynamic class constant `SETTINGS_NAV_ITEM`, already present | on `automation/testids` only |
| User instructions textarea (used only for the placeholder cross-check) | `ai-personality-user-instructions-textarea` | `LocatorDescriptor` — already present | on `automation/testids` only (EliteaAI/EliteaUI@fa505e37) |

**No new testid is needed for this case.** Every handle already exists and is
already declared as a page-object class field.

**Option-row enumeration without a raw handle.** The count/order assertions
need a collection, not a single row. Use the existing dynamic constant with an
attribute-prefix form declared as its own class constant, e.g.
`SELECT_OPTION_ANY = '[data-testid^="select-option-"]'` — still a literal
`[data-testid=` selector at class level, so it satisfies the mechanical grep.
Do **not** reach for `li[role="option"]`.

## Automation Hints

- **Reuse `automation/pages/settings_personalization_page.py` as-is.** It
  already carries `wait_for_persona_select()`, `get_persona()`,
  `open_persona_options()`, `persona_option(value)`, `select_persona(value)`,
  `open_settings_tab()` / `go_to_settings_tab()` and `nav_item()`. The only
  addition this case needs is the `SELECT_OPTION_ANY` collection constant plus
  a reader that returns the option labels in DOM order.
- **Assert the autosave PUT, never `wait_for_autosave()`.** That helper is a
  `networkidle` wait, and `networkidle` never settles on this app (the
  Socket.IO polling transport — #1847). Wrap the selection in
  `page.expect_response(lambda r: AUTHOR_SETTINGS_ENDPOINT in r.url and r.request.method == "PUT")`
  and assert `status == 200`. `AUTHOR_SETTINGS_ENDPOINT` is already exported
  from the page-object module.
- **Teardown must be route-guarded.** Copy the `_restore_persona` /
  `_restore_persona_best_effort` pair from
  `test_personalization_autosave_no_save_button.py` — the strict variant on the
  success path, best-effort on the failure path, so a teardown exception can
  never replace the real failure in the report.
- **Console filter is exactly `disableUnderline`.** One error fires on every
  `/settings/ai-personality` load (#1771). `/settings/profile` fires none — do
  not copy this filter to specs for other routes.
- Markers: `ui`, `settings`, `p3`, `regression`. Steps wrapped in
  `with allure.step("Step N — …")`.
- Suggested location: `automation/tests/ui/settings/test_default_personality_options.py`.

## Fidelity Declaration

**No substitutions.** Every asserted value is produced by the running app: the
option rows are read from the live DOM, the autosave status from the real
`PUT /api/v2/social/author/` response, and the post-reload value from a real
server round-trip. No `page.route`, no `route.fulfill`, no injected state.
`auth_state` is the framework's standard login fast-path and is not the subject
of this case.

## Coverage Map

### Axis 1 — Case coverage

| Case element | Expected result | Covered by (AFS step) | Asserted where | Disposition |
|---|---|---|---|---|
| Precondition: user logged in | — | fixture | `auth_state`; page loads | asserted (implicitly) |
| 1 Navigate to Personalization → GENERAL section | Page/section loads | AFS step 1 | URL + `data-active` + `ai-personality-persona-section` visible | clarification *(live route is Settings → AI Personality; #1960)* |
| 2 Click the Default Personality dropdown | Control responds | AFS step 2 | option list open (`select-option-generic` visible) | asserted |
| 3 Verify the following six options are listed | Condition holds | AFS step 3 | count == 7 + label list equality | clarification *(seven, not six — #1963; live contract asserted)* |
| 4 Generic | present | AFS step 3 | `select-option-generic` visible, label `Generic` | asserted |
| 5 QA | present | AFS step 3 | `select-option-qa` visible, label `QA` | asserted |
| 6 Nerdy | present | AFS step 3 | `select-option-nerdy` visible, label `Nerdy` | asserted |
| 7 Quirky | present | AFS step 3 | `select-option-quirky` visible, label `Quirky` | asserted |
| 8 Cynical | present | AFS step 3 | `select-option-cynical` visible, label `Cynical` | asserted |
| 9 None | present | AFS step 3 | `select-option-none` visible, label `None` | asserted |
| 10 Bare | present | AFS step 3 | `select-option-bare` visible, label `Bare` | asserted |
| 11 Select a different personality (e.g. "Nerdy") | Control responds | AFS step 4 | autosave PUT → 200 | asserted |
| 12 Click outside to trigger autosave | Control responds | AFS step 5 | section still `aria-expanded="true"` | asserted *(no-op for this control — #1963; step executed anyway)* |
| 13 Verify the dropdown shows "Nerdy" | Condition holds | AFS step 6 | combobox text == `Nerdy` | asserted |
| Expected final state: dropdown shows "Nerdy" | — | AFS steps 6–7 | combobox text, before and after reload | asserted |

### Axis 2 — Assertions beyond the case

| Observable | Why | AFS step |
|---|---|---|
| Exact option **count** is 7 (not merely "each of the 7 is present") | A presence-only check passes when an eighth option appears — the case's subject is the option *set*, so the set's size is part of the contract | 3 |
| Option **order** matches `PERSONA_OPTIONS` | Order is user-visible and code-defined; a reordering is a real UI change the case would otherwise miss | 3 |
| `aria-selected` marks exactly the current persona | Proves the list reflects live state rather than rendering a static menu | 3 |
| Autosave `PUT` returns **200** | "The dropdown shows Nerdy" is satisfiable by SPA state alone; only the write proves the selection was saved | 4 |
| Value survives a full page **reload** | Separates server persistence from the SPA store | 7 |
| No unexpected console errors (filtering #1771) | Silent errors are the ones that ship; the route has exactly one known, linked error | 8 |
| The accordion did not collapse on the "click outside" | The obvious "outside" target (the header) collapses the section — pinning this stops a future refactor from silently changing what step 12 does | 5 |

## Known Defects
None found. Two case-text clarifications (#1963, #1960) — the product is
correct in both.

## Blocked Steps
None.
