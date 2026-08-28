# Test Case (family): Default Personality / Default User Instructions apply to NEW conversations only

## Metadata
- **TMS IDs**: **ELITEA-2388** (Default Personality) · **ELITEA-2389** (Default User Instructions)
- **Family AFS** — the two cases are the *same flow* parameterised by which personalization field is changed and which conversation-record field is read. One shared extension, one Coverage Map row set per case.
- **Priority**: l3 (case priority `medium` for both)
- **Environment Explored**: local (`http://localhost:5173`, `EliteaAI/EliteaUI` `automation/testids` @ `36733706`, DEV backend)
- **User set**: `${TEST_USER}` (localhost `auth_state` bypass via `VITE_DEV_TOKEN`)
- **Analyst**: qa-engineer, batch `settings-w08`, cluster ELITEA-2385/2386/2388/2389, 2026-08-29
- **Status**: **extend-existing**
- **Extends**: `automation/tests/ui/settings/test_personalization_new_conversations_only.py:210`
  (`TestPersonalizationAppliesToNewConversationsOnly::test_personalization_applies_to_new_conversations_only`,
  ELITEA-2384) — **on batch trunk `tests/batch-settings-w08`**, merged there by the
  ELITEA-2381/2382/2383/2384 unit (`47ddf7d62`, `9cd2be7b1`). Permitted target per the
  merged-target rule: an extension shares this batch's fate.
- **Surface digest**: `test-specs/settings-user-profile/_surface.md` → `_surface/personalization-family.md`
- **Clarification**: EliteaAI/elitea-testing-public#1967 (route drift, unobservable per-conversation personality, no pre-existing conversation) — siblings #1960, #1963
- **Defects filed**: none for these two cases (the product behaved correctly on every step, verified live)

## Behavioural overlap — what the covering spec already proves

ELITEA-2384's case is the *combined* form of these two: it changes **both** the default
persona and that persona's user-instructions slot, then compares a conversation created
before the change with one created after. Its merged spec already asserts, against the
product's own response bodies:

| Covering assertion | Line | Satisfies |
|---|---|---|
| baseline conversation records `meta.persona == "quirky"`, `instructions == ""` | `:283`, `:287` | 2388 step 6-7 / 2389 step 6-7 setup |
| Default persona changed to **Nerdy** via the real select, autosave `PUT /api/v2/social/author/` → 200 | `:264`-`:275` | **2388 step 2** |
| that persona's user-instructions typed into the real textarea, blur-autosave `PUT` → 200, field re-reads the typed value | `:277`-`:291` | **2389 step 2** |
| re-opened pre-existing conversation still reports `meta.persona == "quirky"` | `:298` | **2388 step 7** |
| re-opened pre-existing conversation still reports `instructions == ""` | `:303` | **2389 step 7** |
| conversation created *after* the change reports `meta.persona == "nerdy"` | `:321` | **2388 steps 4-5** |
| conversation created *after* the change reports `instructions == <the marker text>` | `:325` | **2389 steps 4-5** |

That is 6 of each case's 7 steps, asserted on the deterministic oracle (the conversation
record the app itself fetches), with real UI actions throughout and no substitutions.
Re-implementing either case fresh would produce a spec that duplicates this one end to end.

**Independently re-verified live during this analysis** (not taken on trust):
conversation `9879` created while the persona was `Generic` → `meta.persona: "generic"`,
`instructions: ""`; default then changed to `Nerdy` + instructions
`"Always respond with bullet points."`; conversation `9880` → `meta.persona: "nerdy"`,
`instructions: "Always respond with bullet points."` (plus a new `meta.default_instructions`
mirror); re-opening `9879` afterwards still returned `"generic"` / `""`.

## Gap assertions — what the covering spec does NOT do

**One gap, shared by both cases: step 3.**

> *"Navigate away and back to confirm the value was auto-saved."*

The covering spec asserts the autosave **request** (`PUT` → 200) but never leaves the route
and returns. A `PUT` that returns 200 while the server drops the field, or an SPA store that
holds the value only in memory, would pass today. Sibling specs prove *persistence* via
`page.reload()` (ELITEA-2381 step 14, ELITEA-2382 step 5) — a **reload** is a different
journey from a **route change within the SPA**: reload rebuilds the whole store from the
server, whereas navigate-away-and-back exercises the mount/unmount + refetch path these two
cases actually name, and is the one the user performs.

Append to the covering spec, immediately after its existing Step 2 (the block that changes
the persona and types the instructions), a new step:

- **New Step 2b — "the values survive a route change"** (`allure.step("Step 2b — …")`):
  1. `personalization.open_settings_tab("preferences")` — navigate away to a sibling
     Settings route (real in-app navigation, not `page.goto`).
     - **Verify**: `voice-personalization-section` is visible (the other route really
       mounted — otherwise the "away" half is vacuous).
  2. `personalization.open_settings_tab("ai-personality")` — navigate back.
     - Wait on `ai-personality-persona-select-combobox` (documented render race — element
       wait, never a sleep).
     - **Verify (ELITEA-2388)**: `ai-personality-persona-select-combobox` has text `Nerdy`.
     - **Verify (ELITEA-2389)**: `ai-personality-user-instructions-textarea` has value
       equal to the spec's `INSTRUCTIONS_MARKER`.

No new page-object methods are required — `open_settings_tab`, `wait_for_persona_select`,
`persona_select_combobox` and `user_instructions_textarea` all already exist on
`SettingsPersonalizationPage`. No new testids are required.

**Also update, in the same edit:**
- the spec's `@allure.issue` block and module docstring to name **ELITEA-2388** and
  **ELITEA-2389** alongside ELITEA-2384, so the traceability resolves for all three;
- the docstring's case-text-drift note to reference clarification **#1967** as well as #1960.

## Parameter table — one row per TMS case

| Case | Settings field changed | Where | Value written | Conversation-record field read | New conversation expects | Pre-existing conversation expects |
|---|---|---|---|---|---|---|
| **ELITEA-2388** | `Default persona` select | `/settings/ai-personality` → `PERSONA MANAGEMENT` | `Nerdy` (`nerdy`) | `meta.persona` | `"nerdy"` | unchanged — the value it was born with (`"quirky"` in the covering spec, `"generic"` in this analysis) |
| **ELITEA-2389** | `User instructions` textarea (**per-persona slot**) | same accordion, same route | `"Always respond with bullet points."` (covering spec uses its own marker text — equivalent, data-only difference) | top-level `instructions` | the exact written text | `""` (the baseline persona's slot is empty) |

## Case-text drift — asserted against the LIVE contract

All rows are **case-text stale, product correct**; clarification #1967, no defect filed.

1. **"Settings → Personalization → GENERAL"** (both cases, step 1) — `/settings/personalization`
   404s, and `GENERAL` on `/settings/preferences` holds the **Theme toggle only**. Both
   fields live on **`/settings/ai-personality`** (`PERSONA MANAGEMENT`).
2. **"Default User Instructions field"** implies one global field (2389) — it is a
   **per-persona map** (`personality_instructions.<persona>`); the textarea renders only
   the current persona's slot and is absent from the DOM while the persona is `None`.
   ⇒ the persona must be pinned before typing and read back under the same persona
   (the covering spec already does exactly this).
3. **"Verify the new conversation uses the 'Nerdy' personality setting"** (2388 step 5) and
   **"verify the AI response style reflects the user instructions"** (2389 step 5) — there
   is **no per-conversation personality indicator in the UI**, and LLM tone is not a
   falsifiable assertion. The record is the contract:
   `POST /api/v2/elitea_core/conversations/prompt_lib/<project>` → **201** and
   `GET /api/v2/elitea_core/conversation/prompt_lib/<project>/<id>` → **200** both carry
   `meta.persona` + a resolved top-level `instructions`.
   *(Observed anecdotally during this analysis: with the bullet-point instructions in force
   the model did answer `• Blue` / `• Red`. Real, but nondeterministic — it is evidence the
   feature works, not an assertion anything should depend on.)*
4. **"Open a previously existing conversation"** (both, step 6) — none can be assumed on
   the shared account, so the spec creates its own baseline conversation first. That is also
   what makes step 7 falsifiable: we know exactly what that conversation should still report.

## Preconditions
- User is logged in (`auth_state`; localhost bypass).
- **Shared mutable account state** — `persona` and `personality_instructions` live on the
  `${TEST_USER}` record. The covering spec already reads both before writing and restores
  them (strict on the success path, best-effort on failure, route-guarded). The new
  Step 2b changes nothing, so no teardown change is needed.
- The covering spec creates 2 conversations and deletes both via the `conversation_api`
  fixture. Unchanged.

## Fidelity Declaration
**No substitutions, transit or terminal.** Every value asserted is produced by the system:
the settings are changed through the real controls, saved by the product's own autosave, and
the conversation personalization is read from the response bodies of the two endpoints the
normal user path already triggers (response-as-oracle, `.agents/testing.md` § Fidelity
policy). The new Step 2b adds only real in-app navigation.

## Automation Hints
- **Navigate with `open_settings_tab()`, not `page.goto()`** — the gap being closed is the
  SPA route-change path; a full document navigation would test the same thing
  `page.reload()` already tests in ELITEA-2381/2382.
- **Render race**: right after the route resolves, `ai-personality-persona-select-combobox`
  is briefly absent from the DOM (observed live again this session). Wait on the element.
- ⚠️ **`beforeunload` dialog when leaving a just-created chat.** Navigating away from
  `/chat/<id>` seconds after sending the first message raises a `beforeunload` dialog.
  Playwright auto-dismisses dialogs, so pytest is unaffected — but a Playwright-MCP or
  headed debugging session will *hang* there until it is handled. Cost this analysis one
  timeout; recorded so the next debugger does not re-diagnose it.
- **Console filter unchanged**: `/settings/ai-personality` logs exactly the known #1771
  `disableUnderline` warning; the covering spec's `unexpected_console_errors()` already
  filters precisely that and nothing broader.
- **Back-write**: on merge, ELITEA-2388 and ELITEA-2389 both take the covering spec's
  Form-C id —
  `tests.ui.settings.test_personalization_new_conversations_only.TestPersonalizationAppliesToNewConversationsOnly.test_personalization_applies_to_new_conversations_only`
  — the same ref ELITEA-2384 carries (one test may cover several cases;
  `.agents/test-automation.yaml` § `backwrite_on_done`).

## Handles Reference (testid-only) — all pre-existing, **nothing to add**

| Element | Testid | Provenance (verified 2026-08-29 after `git fetch origin`) |
|---|---|---|
| AI Personality nav item | `settings-nav-item-ai-personality` | dynamic `SETTINGS_NAV_ITEM` constant; on `automation/testids` |
| Preferences nav item | `settings-nav-item-preferences` | same |
| Persona accordion | `ai-personality-persona-section` | on `automation/testids` only (awaiting human promotion to main) |
| Persona select display | `ai-personality-persona-select-combobox` | on `automation/testids` only — derived by `SingleSelect` from `ai-personality-persona-select` |
| Persona option row | `[data-testid="select-option-{}"]` (class constant) | **on-main ✓** |
| User instructions textarea | `ai-personality-user-instructions-textarea` | on `automation/testids` only |
| Voice section (away-route probe) | `voice-personalization-section` | **on-main ✓** |
| Chat composer | `chat-message-input` | **on-main ✓** |

## Coverage Map

### Axis 1 — ELITEA-2388
| Case element | Expected result | Covered by | Asserted where | Disposition |
|---|---|---|---|---|
| Precondition: logged in | — | `auth_state` | fixture | covered (setup) |
| Step 1 navigate to the personality setting | page loads | covering spec Setup + Step 2 (`open_settings_tab("ai-personality")`, `wait_for_persona_select`) | `:249`, `:266` | covered (route corrected — #1967) |
| Step 2 set Default Personality to "Nerdy" | expected UI state | covering spec `_select_persona(CASE_PERSONA_VALUE="nerdy")` + autosave `PUT` 200 + combobox text | `:264`-`:275`, `:157`-`:170` | covered |
| Step 3 navigate away and back → value auto-saved | page loads, value held | **GAP → new Step 2b** | new assertion: combobox text `Nerdy` after `preferences` → `ai-personality` | **gap assertion (this AFS)** |
| Step 4 create a new conversation | completes successfully | covering spec `_create_conversation` (send via Enter → `POST` 201, URL `/chat/<id>`) | `:172`-`:208`, `:311` | covered |
| Step 5 new conversation uses "Nerdy" | condition holds | `new_persona == CASE_PERSONA_VALUE` | `:321` | covered (**observable relocated to `meta.persona`** — #1967) |
| Step 6 open a previously existing conversation | page loads | covering spec Step 3 (`open_conversation` → `GET` 200) | `:293`-`:296` | covered (**baseline conversation is created by the spec** — #1967) |
| Step 7 existing conversation personality unchanged | condition holds | `reopened_persona == BASELINE_PERSONA_VALUE` | `:298` | covered |
| Expected final state | — | same as step 7 | `:298` | covered |

### Axis 1 — ELITEA-2389
| Case element | Expected result | Covered by | Asserted where | Disposition |
|---|---|---|---|---|
| Precondition: logged in | — | `auth_state` | fixture | covered (setup) |
| Step 1 navigate to the instructions field | page loads | covering spec Step 2 | `:266` | covered (route corrected — #1967) |
| Step 2 enter the instructions text | field accepts + displays it | covering spec `fill_user_instructions` + blur autosave `PUT` 200 + `to_have_value` | `:277`-`:291` | covered (data-only difference: the covering spec's marker text, not the case's literal sentence) |
| Step 3 navigate away and back → value auto-saved | page loads, value held | **GAP → new Step 2b** | new assertion: textarea value == marker after route change | **gap assertion (this AFS)** |
| Step 4 create a new conversation | completes successfully | covering spec `_create_conversation` | `:172`-`:208` | covered |
| Step 5 send a message; response style reflects the instructions | expected UI state | covering spec: the message IS sent (that is what creates the conversation) and the conversation's resolved `instructions` is asserted | `:325` | covered **as far as it is falsifiable** — LLM tone is not asserted (#1967); the resolved-instructions field is the deterministic contract |
| Step 6 open a previously existing conversation | page loads | covering spec Step 3 | `:293`-`:296` | covered |
| Step 7 existing conversation unaffected | condition holds | `reopened_instructions == ""` | `:303` | covered |
| Expected final state | — | same as step 7 | `:303` | covered |

### Axis 2 — asserted beyond the two cases (already in the covering spec, retained)
| Observable | Why |
|---|---|
| the two conversations have different ids (`:313`) | guards against "step 4 landed back on the existing conversation", which would compare one record with itself and pass vacuously |
| the created conversation's `id` equals the id in the URL (`:203`) | ties the asserted response body to the conversation the user is actually looking at |
| autosave `PUT` status is 200 for both fields | separates "the UI updated" from "the server accepted it" — a 4xx with an optimistic UI would otherwise pass |
| 0 unexpected console errors (#1771 filtered) | the route's known-error set is closed, so anything else is signal |
| **new**: the away-route really mounted (`voice-personalization-section` visible, Step 2b) | without it, a failed navigation would make the "navigate away" half vacuous and the persistence check meaningless |
