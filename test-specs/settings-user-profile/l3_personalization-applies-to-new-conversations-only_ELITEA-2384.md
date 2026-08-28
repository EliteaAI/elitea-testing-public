# Test Case: Personalization settings apply to new conversations only

## Metadata
- **TMS ID**: ELITEA-2384
- **Priority**: l3 (case priority `medium`)
- **Environment Explored**: local (`http://localhost:5173`, `EliteaAI/EliteaUI` `automation/testids`, DEV backend)
- **User set**: `${TEST_USER}` (localhost `auth_state` bypass via `VITE_DEV_TOKEN`)
- **Analyst**: qa-engineer, batch `settings-w08`, cluster ELITEA-2381/2382/2383/2384, 2026-08-29
- **Status**: ready-for-automation
- **Surface digest**: `test-specs/settings-user-profile/_surface.md` →
  `_surface/personalization-family.md` + `test-specs/chat-interface/_surface.md`
- **Clarifications**: EliteaAI/elitea-testing-public#1960 (route drift + the
  observable — comment added for this case)

## The observable — read this first

The case's steps 4 and 6 ("verify the existing conversation settings have NOT
changed" / "verify the new conversation uses the updated personality setting")
have **no UI surface**. There is no per-conversation personality indicator
anywhere in the front end — `meta.context_strategy` is the only conversation
meta the UI consumes (`ParticipantsWrapper.jsx:66`, `ChatPanel.jsx:153`,
`ConfigurationTab.jsx:170`). Judging the assistant's *tone* would be
nondeterministic LLM output requiring semantic judgment, i.e. un-assertable.

**But the conversation record itself carries the snapshot, and the app fetches
it on the real user path.** Verified live 2026-08-29:

| Endpoint (real, driven by the UI action) | Field |
|---|---|
| `POST /api/v2/elitea_core/conversations/prompt_lib/<project>` → 201, on sending the first message | `meta.persona`, top-level `instructions` |
| `GET /api/v2/elitea_core/conversation/prompt_lib/<project>/<id>` → 200, on opening a conversation | same |

Live evidence from this session:

| Conversation | Created while the default was | `meta.persona` | `instructions` |
|---|---|---|---|
| `9871` | `Quirky` (empty instructions slot) | `"quirky"` | `""` |
| `9871` **re-opened after** the default moved to `Nerdy` | — | still `"quirky"` | still `""` |
| `9872` | `Nerdy` (slot held text) | `"nerdy"` | `"Always respond in a concise manner. Focus on practical solutions."` |

So the case is fully automatable with a deterministic, **system-produced**
observable. The assertion reads the product's own response body; nothing is
fabricated. This is not a substitution — the UI action is the trigger, the
response is the oracle (`.agents/testing.md` § Fidelity policy, *"How to test a
NONDETERMINISTIC producer without substituting it"*).

**The spec never waits on an LLM answer.** The conversation — and its persona
snapshot — is created by *sending*, not by the model replying (the `201` lands
before any answer arrives), so the known LLM trigger-side flakiness stays out
of this case entirely.

## Case-text drift

- **"Navigate to Personalization"** → the Default Personality dropdown is on
  `/settings/ai-personality`. #1960.
- **Step 1 "Open an existing chat conversation"** — **no pre-existing
  conversation can be assumed.** Verified live: the current project's
  conversation list renders folders only, zero `chat-conversation-item-*` rows
  (same finding as ELITEA-2390). The spec therefore *creates* its own
  "previously existing" conversation under a first persona — which is also what
  makes step 4 falsifiable, because we then know exactly what that conversation
  should still report.
- **Step 6's wording** ("uses the updated personality setting") is
  unfalsifiable as written; recommend the case name `meta.persona`.
  Recorded on #1960.

Case-text stale, product correct — assert the live contract.

## Not already covered — checked

`automation/tests/ui/settings/test_context_settings_new_conversations_only.py`
(ELITEA-2390, on batch trunk `tests/batch-settings-w08`) proves the *same
architectural principle* — a conversation snapshots the user's defaults at
creation time — but for **context management** (`meta.context_strategy`,
asserted through the per-conversation Context Budget modal in the UI). This
case's subject is **persona / instructions**, a different structure with a
different observable and a different write path. Not coverage; it is a reuse
target for the conversation-creation machinery only.

## Preconditions
- User is logged in (`auth_state`; localhost bypass).
- **Shared mutable account state**: `persona` and the `personality_instructions`
  map. Read-before-write, restore both in teardown.
- **The spec creates 2 conversations per run** in the active project.
  *Amended during implementation:* both are **deleted in cleanup** via
  `conversation_api.delete_conversation()`, the same API teardown ELITEA-2390's
  merged spec already uses on this surface — so this spec does **not** add to
  the `#1082` shared-test-user pollution class after all. Deletion is
  best-effort and logged, never able to mask a real failure.

## Test Data
### create-per-run
| Phase | Persona | That persona's instructions slot | Purpose |
|---|---|---|---|
| Baseline A | `Quirky` (`quirky`) | left as-is (empty on a clean account) | in force when the "previously existing" conversation is created |
| Case value B | `Nerdy` (`nerdy`) | set to the § marker text | in force when the NEW conversation is created |

`quirky` vs `nerdy` is the discriminator: the two must differ, or step 6's
assertion could pass by accident. Setting B's instructions slot gives a
**second, independent** discriminator (`instructions` non-empty vs empty).

- Instructions marker text:
  `Always respond in a concise manner. Focus on practical solutions.`
- Conversation seed message: `Reply with the single word OK.`

## Test Steps
1. **Baseline A — set the persona to `Quirky`.** Navigate to
   `${BASE_URL}/settings/ai-personality`; wait for the select; read and store
   the current persona + the `nerdy` slot's text (teardown). Select `Quirky`
   wrapped in `page.expect_response(<PUT /api/v2/social/author/>)`; assert 200.
2. **Case step 1 — create the "previously existing" conversation.** Navigate to
   `${BASE_URL}/chat`, type the seed message into `chat-message-input`, and
   send it while wrapped in
   `page.expect_response(<POST …/elitea_core/conversations/prompt_lib/…>)`.
   - **Verify**: the response status is **201**.
   - **Verify (baseline, records what step 5 must still see)**:
     `meta.persona == "quirky"`; `instructions == ""`.
   - Capture the conversation id from the response body (and cross-check it
     against the `/chat/<id>` URL the app navigates to).
   - ⚠️ **Send with `Enter`, not by clicking `chat-send-button`** — an overlay
     intercepts pointer events on that button on the fresh-chat view
     (reproduced live: `<div class="MuiBox-root css-15msj7j"> … intercepts
     pointer events`). `ChatPage.send_message(text, use_enter=True)` already
     does this.
3. **Case step 2 — change Default Personality to a different option.** Back to
   `${BASE_URL}/settings/ai-personality`; select `Nerdy` (PUT → 200); type the
   marker text into `ai-personality-user-instructions-textarea` and blur
   (PUT → 200).
   - **Verify**: the combobox reads `Nerdy`; the textarea's value is the marker
     text.
4. **Case step 3 — return to the existing conversation.** Navigate to
   `${BASE_URL}/chat/<id from step 2>`, wrapped in
   `page.expect_response(<GET …/elitea_core/conversation/prompt_lib/…/<id>>)`.
   - **Verify**: the response status is **200**.
5. **Case step 4 — verify the existing conversation has NOT changed.**
   - **Verify**: `meta.persona == "quirky"` — the value in force when THAT
     conversation was created, **not** the new global `nerdy`.
   - **Verify**: `instructions == ""` — the new persona's marker text did
     **not** leak into it.
6. **Case step 5 — create a new conversation.** Navigate to `${BASE_URL}/chat`,
   send the seed message, wrapped in `page.expect_response(<POST … 201>)`.
   - **Verify**: the response status is **201** and the new conversation id
     differs from step 2's.
7. **Case step 6 — verify the new conversation uses the updated setting.**
   - **Verify**: `meta.persona == "nerdy"`.
   - **Verify**: `instructions == ` the marker text — the *resolved* value from
     the `nerdy` slot, which additionally proves the per-persona instructions
     map is what feeds a conversation.
8. **Beyond the case — no unexpected console errors** across the whole run.
   Collect via `utils/console_errors.collect_console_errors(page)`; assert
   empty after filtering the known `disableUnderline` message
   (`# Known defect: #1771`, `/settings/ai-personality`).
9. **Teardown — restore** the `nerdy` instructions slot to its captured
   original and the persona to its captured original, route-guarded; strict on
   the success path, best-effort on the failure path.

## Expected Results
- A conversation snapshots the user's personalization (`meta.persona` and the
  resolved `instructions`) **at creation time**.
- Changing the defaults afterwards affects only conversations created after the
  change; a pre-existing conversation keeps its own values, on re-open.
- Confirmed live end-to-end 2026-08-29 (conversations `9871` / `9872`) — see
  § The observable.

## Handles Reference

**PROVENANCE verified 2026-08-29 after `cd ../EliteaUI && git fetch origin`.**

| Element | Primary handle | Shape | Provenance |
|---|---|---|---|
| Default persona display / opener | `ai-personality-persona-select-combobox` | `LocatorDescriptor` — already on `SettingsPersonalizationPage` | on `automation/testids` only (EliteaAI/EliteaUI@fa505e37) |
| Persona option row | `select-option-{value}` | dynamic class constant `SELECT_OPTION` | on `main` ✓ |
| User instructions textarea | `ai-personality-user-instructions-textarea` | `LocatorDescriptor` — already present | on `automation/testids` only (EliteaAI/EliteaUI@fa505e37) |
| Chat composer input | `chat-message-input` | `LocatorDescriptor` — already on `ChatPage:51` | pre-existing |
| Chat send button *(present but NOT clicked — see step 2)* | `chat-send-button` | `LocatorDescriptor` — already on `ChatPage:57` | pre-existing |
| Chat message item (send landed) | `chat-message-item` | `LocatorDescriptor` — already on `ChatPage:844` | pre-existing |
| Settings nav item | `settings-nav-item-{tab}` | dynamic class constant `SETTINGS_NAV_ITEM` | on `automation/testids` only |

**No new testid is needed for this case.** The case's own observables are API
response fields, not DOM nodes:

| Observable | Where |
|---|---|
| `meta.persona` | `POST …/elitea_core/conversations/prompt_lib/<project>` (201) · `GET …/elitea_core/conversation/prompt_lib/<project>/<id>` (200) |
| `instructions` (top level, resolved from the persona's slot) | same two responses |

## Automation Hints

- **Lift the conversation-creation machinery from
  `test_context_settings_new_conversations_only.py`** (ELITEA-2390) — same
  create-then-compare skeleton, same "no pre-existing conversation can be
  assumed" precondition, same "the 201 lands before the LLM answers" fact. Only
  the observable differs (response JSON here vs the Context Budget modal there).
- **Read the response body, not the DOM.** Wrap each triggering interaction in
  `page.expect_response(...)` and `resp.json()` the result. This keeps the
  assertion on the system's own output while every action stays a real UI
  action.
- **Send with Enter.** `chat-send-button` is pointer-intercepted on the fresh
  `/chat` view; `ChatPage.send_message(text, use_enter=True)` is the working
  path.
- **The project id in the URL is dynamic** (`399` in this session) — match the
  endpoint by path fragment (`/elitea_core/conversations/prompt_lib/`), never a
  hardcoded id.
- **Assert every settings PUT** rather than `wait_for_autosave()`
  (`networkidle` never settles — #1847).
- **Restore both** the persona and the instructions slot: leaving text in the
  `nerdy` slot changes what a later run of this very spec observes.
- Markers: `ui`, `settings`, `chat`, `p3`, `regression`; steps wrapped in
  `with allure.step("Step N — …")`.
- Suggested location:
  `automation/tests/ui/settings/test_personalization_new_conversations_only.py`.

## Fidelity Declaration

**No substitutions.** Every asserted value is produced by the system: personas
are changed through the real select (real `PUT` → 200), conversations are
created by really sending a message through the composer, and the asserted
`meta.persona` / `instructions` are read off the product's own `201`/`200`
response bodies. Nothing is fabricated, injected or seeded through a
wrong-interface precondition. Reading an API response that a UI action produced
is **not** a substitution — it is the response-as-oracle pattern
(`.agents/testing.md` § Fidelity policy). `auth_state` is the framework's
standard login fast-path and is not this case's subject.

## Coverage Map

### Axis 1 — Case coverage

| Case element | Expected result | Covered by (AFS step) | Asserted where | Disposition |
|---|---|---|---|---|
| Precondition: user logged in | — | fixture | `auth_state`; pages load | asserted (implicitly) |
| 1 Open an existing chat conversation and note its current behavior/settings | Page loads | AFS steps 1–2 | conversation created under baseline A; `201`; `meta.persona == "quirky"`, `instructions == ""` recorded | clarification *(no pre-existing conversation can be assumed — the spec creates its own; #1960)* |
| 2 Navigate to Personalization and change Default Personality to a different option | Page loads / change applies | AFS step 3 | `/settings/ai-personality`; PUT → 200; combobox reads `Nerdy` | clarification *(live route; #1960)* |
| 3 Return to the existing conversation | Completes without error | AFS step 4 | `GET …/conversation/…/<id>` → 200 | asserted |
| 4 Verify the existing conversation settings have NOT changed | Condition holds | AFS step 5 | `meta.persona == "quirky"`, `instructions == ""` | asserted *(via the conversation record — no UI surface exists; #1960)* |
| 5 Create a new conversation | Completes; state updates | AFS step 6 | `POST …/conversations/…` → 201; new id ≠ old id | asserted |
| 6 Verify the new conversation uses the updated personality setting | Condition holds | AFS step 7 | `meta.persona == "nerdy"` **and** `instructions == ` marker text | asserted *(case wording is unfalsifiable as written; the record field is the live contract — #1960)* |
| Expected final state: new conversation uses the updated personality | — | AFS step 7 | same | asserted |

### Axis 2 — Assertions beyond the case

| Observable | Why | AFS step |
|---|---|---|
| `instructions` as a **second** discriminator alongside `meta.persona` | Two independent fields must both flip; a bug that snapshots the persona label but resolves instructions live would pass a persona-only check | 5, 7 |
| The existing conversation's `instructions` is still `""` | The mirror of the persona check — it catches leakage in the direction the case never looks | 5 |
| The new conversation id differs from the old one | Guards the whole comparison: if the app reused the same conversation, steps 5 and 7 would be reading one record twice and could not disagree | 6 |
| Response **status codes** (201 / 200) asserted, not just bodies | A body read off a failed request is not evidence | 2, 4, 6 |
| No unexpected console errors (filtering #1771) | Silent errors ship; a run this long crosses four routes | 8 |

## Known Defects
None found. Case-text clarifications recorded on #1960 — the product is
correct.

## Blocked Steps
None.

## Notes for the lead
*Amended during implementation:* the spec now deletes both conversations it
creates (`conversation_api.delete_conversation()`, best-effort, mirroring
ELITEA-2390), so it leaves nothing behind on the shared `${TEST_USER}` account.
The broader `#1082` pollution class is untouched by this — its durable fix
remains the rotating/clean test identity in `.agents/testing.md`
§ Suite-health pointer.
