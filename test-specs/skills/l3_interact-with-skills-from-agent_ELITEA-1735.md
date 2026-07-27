# Test Case: Interact with Skills from Agent

## Metadata
- **TMS ID**: ELITEA-1735
- **Linked Story**: none
- **Priority**: l3 (medium, per case)
- **Environment Explored**: local (`http://localhost:5173`, EliteaUI `automation/testids` branch → DEV backend, project `Private` / `${ELITEA_PROJECT_ID}`=399), model: Anthropic Claude 4.5 Sonnet
- **User set**: `${TEST_USER}` (on localhost, `auth_state` fixture skips login via `VITE_DEV_TOKEN`)
- **Analyst**: qa-engineer (Sage), analyst slot
- **Status**: ready-for-automation (Phase 3 handles-only rework, 2026-07-14 —
  see Handles Reference rework note). Coverage, steps, and defect handling are
  unchanged from the prior pass: skill creation, attachment, and explicit
  `~mention` invocation (steps 1–3, 5–6) are ready-for-automation outright; step 4
  (plain-message non-invocation) has a confirmed intermittent product defect
  (github.com/EliteaAI/elitea-testing-public/issues/38) and should automate with
  `expect.soft()` around the step-4 assertion per project's isolated-defect policy
  (`.agents/profile.md` § Bug filing), ticket linked, rest of the flow
  hard-asserted. What changed in this pass: every Handles Reference row is now
  testid-only with a live-verified provenance column — the prior pass's
  role/text/xpath handles (shipped in PR #39 off a since-retracted "no testid
  needed" amendment) are replaced with either a confirmed on-main testid or an
  explicit `testid needed:` work order for the implementer.

## Preconditions
- User is logged in (on localhost, `auth_state` fixture skips login).
- A project is selected/accessible (`Private`, id `399` in this run).
- Skills and Agents sections are available in the project.

## Test Data

### generate-per-test (in test setup, cleaned up in its own teardown)
- Skill 1 name: kebab-case, e.g. `elitea-1735-skill-uppercase` — **must be
  lowercase letters/digits/hyphens only** (same client-side Skill-name validation
  documented for ELITEA-1737 — see `.agents/memory/qa-engineer/skill_form_and_export_import_quirks.md`).
- Skill 1 description: any non-empty string.
- Skill 1 instructions: `"Always respond with the exact text the user asked for,
  but convert the ENTIRE output to UPPER CASE letters. Do not use any lowercase
  letters in your response."`
- Skill 2 name: e.g. `elitea-1735-skill-underscore`.
- Skill 2 instructions: `"Always respond with the exact text the user asked for,
  but replace every space between words with an underscore character _ so the
  output is underscore_delimited like_this."`
- Agent name: e.g. `elitea-1735-skills-agent`; description and a short generic
  instructions string (agent instructions do not need to mention skills — skill
  availability/mention behavior is driven by the platform, not by the agent's own
  instructions field).
- Chat prompts: any short, distinct plain-language request per turn (e.g. "Tell
  me a fun fact about <topic>") — vary wording per attempt so response content
  itself doesn't accidentally satisfy the uppercase/underscore check by coincidence.

No `reuse-existing` or shared fixture applies — this is a fresh-state flow (2
skills + 1 agent, all created and torn down within the test).

## Test Steps

1. Navigate to `${BASE_URL}/skills/create`. Fill Name (`skill-name-input`),
   Description (`skill-description-input`), and Instructions
   (`skill-instructions-editor-content`, a CodeMirror editor — use
   `press_sequentially`/`type`, not `fill`, so React state updates) with the
   Skill 1 uppercase-instruction data above. Click Save
   (`skill-save-button`).
   - **Verify**: a "There are unsaved changes. Are you sure you want to leave?"
     nav-blocker dialog appears immediately after Save (same quirk as
     ELITEA-1737) — confirm it via `alert-dialog-confirm-button` testid. URL
     settles on `/skills/all/{id}`; note Skill 1's ID (e.g. `66`).
2. Repeat step 1 for Skill 2 with the underscore-instruction data. Note Skill
   2's ID (e.g. `67`).
   - **Verify**: same nav-blocker/Save flow; Skill 2 saved with a distinct ID.
3. Navigate to `${BASE_URL}/agents/create`. Fill Name
   (`agent-name-input`), Description (`agent-description-input`), and
   Instructions (`agent-instructions-input`) with generic agent data. Click
   Save (`agent-save-button`).
   - **Verify**: navigates to `/agents/all/{agent-id}?destTab=configuration...`;
     note the Agent ID (e.g. `4565`).
4. On the agent detail page, expand the **Skills** accordion section (heading
   text "Skills"). Click the **add-skill button** (a small icon-only button,
   **no `data-testid` and no accessible name in current DOM** — located as
   the first button inside the Skills section's header row; recommend filing
   an `add-data-testid` request, e.g. `agent-add-skill-button`, before
   automating this step). A "Mention skill"-style popper opens listing
   available skills by name.
   - **Verify**: popper lists both Skill 1 and Skill 2 by their actual names
     (menuitem role, accessible name = skill name).
5. Click the Skill 1 menuitem to attach it, then repeat step 4–5 to attach
   Skill 2.
   - **Verify**: after each attach, the Skills section counter updates
     ("1/5 skills added." → "2/5 skills added.") and a card renders per
     attached skill showing its name and `base` version. **Attachment is
     immediate/auto-saved via API** — confirmed via network trace:
     `PATCH /api/v2/elitea_core/skill/prompt_lib/{project}/{skill-id}` →
     `201 Created` fires on each attach; the page-level `Save`/`Save As
     Version` button stays disabled throughout (no explicit agent-level save
     needed for skill attachment).
6. In the agent's embedded chat panel, type a plain message with **no `~`
   mention** (e.g. "Tell me a fun fact about cats.") into
   `chat-message-input` and press Enter (or click `chat-send-button`).
   - **Verify (expected per case)**: response text uses normal sentence
     case, no forced ALL-CAPS, words separated by spaces (not underscores).
   - **Known defect** — see Known Defects below; this assertion is flaky.
7. Clear the chat (button inside the "Clear the chat" tooltip group, no
   stable testid observed — located via accessible name `clear the chat`).
   Click into `chat-message-input`, type `~` using `slowly`/`press_sequentially`
   (NOT `fill` — see Known Defects/quirks note on the mention chip), select
   Skill 1 from the "Mention skill" popper's menuitem (accessible name =
   skill's own name, e.g. `elitea-1735-skill-uppercase`), then append a
   prompt (again via `slowly`/`press_sequentially` — `fill()` overwrites the
   inserted mention chip since it replaces the whole textbox value rather
   than inserting at the cursor). Send.
   - **Verify**: response text is entirely UPPER CASE (all letters
     uppercased, e.g. `"ELEPHANTS ARE THE ONLY MAMMALS THAT CANNOT
     JUMP!..."`). The chat's visible "Thinking" trace (expand the
     "Thought for N secs" toggle) shows the model explicitly recognizing the
     `~<skill-name>` mention and invoking `load_skill` for it — useful signal
     if this step needs debugging, not something to assert on directly (it's
     an internal reasoning trace, not a stable contract).
8. Clear the chat again. Repeat step 7's mention flow with Skill 2 instead
   (mention `elitea-1735-skill-underscore`, different prompt text, e.g.
   "Tell me a fun fact about penguins.").
   - **Verify**: response text has every space between words replaced with
     `_` (e.g. `"Penguins_can_drink_saltwater_because_they_have_a_special_
     gland_above_their_eyes_that_filters_out_the_salt_from_their_
     bloodstream."`) and is NOT upper-cased.

## Handles Reference

**Rework note (ELITEA-1735 Phase 3 — handles-only rework of PR #39):** PR #39
shipped several non-testid handles (`get_by_role`, `get_by_text`,
`get_by_label`, ancestor-xpath walks) on the strength of a since-retracted
analyst amendment claiming "the accessible name is stable, no testid
needed" for the add-skill button. Per `.agents/role-overrides.md` §
Implementer slot, amending a testid request away is out of contract — a
testid request is satisfied by a testid or escalated to the lead, never
re-scoped down. That amendment is now void. Every row below was re-verified
live (Playwright MCP, snapshot-first, browser discipline) on
2026-07-14 against a freshly created Skill (id 382) + Agent (id 4742) in
project `Private`/399 — both entities created, exercised, and deleted in
this verification pass. `git fetch origin` was run in `../EliteaUI`
immediately before every provenance check below; commands and their output
are the provenance basis, not inference from source alone.

| Element | Primary handle | Provenance | Notes |
|---|---|---|---|
| Skill Name field | `skill-name-input` | on-main ✓ (confirmed via live DOM, this run) | kebab-case validation |
| Skill Description field | `skill-description-input` | on-main ✓ (confirmed via live DOM, this run) | |
| Skill Instructions editor | `skill-instructions-editor-content` | on-main ✓ (confirmed via live DOM, this run) | CodeMirror; use `press_sequentially`, not `fill` |
| Skill Save button | `skill-save-button` | on-main ✓ (confirmed via live DOM, this run) | |
| Nav-blocker confirm | `alert-dialog-confirm-button` | on-main ✓ (confirmed via live DOM, this run) | fires on every Save from create form |
| Agent Name field | `agent-name-input` | on-main ✓ (confirmed via live DOM, this run) | |
| Agent Description field | `agent-description-input` | on-main ✓ (confirmed via live DOM, this run) | |
| Agent Instructions field | `agent-instructions-input` | on-main ✓ (confirmed via live DOM, this run) | |
| Agent Save button | `agent-save-button` | on-main ✓ (confirmed via live DOM, this run) | |
| Agent add-skill button ("+ Skill", `SkillMenu.jsx`) | `testid needed: agent-add-skill-button` | needs-adding — `git grep -in "agent-add-skill" origin/main origin/automation/testids -- '*.jsx'` → no hits; no open UI-repo PR touches this element (`gh pr list --repo EliteaAI/EliteaUI --search skill` checked, 6 open, none add this testid) | Confirmed live: `BaseBtn` renders no `data-testid` and no `aria-label`; its accessible name resolves from visible text content "Skill" (`getByRole('button', {name:'Skill', exact:true})` DOES technically work — verified via `element.evaluate` on live DOM, `ariaLabel: null, textContent: "Skill"`). **That accessible-name stability is irrelevant to the policy**: per role-overrides.md this is implementer work, not a note — spec it as `testid needed`, never re-scoped to a role/name handle. |
| Skills section container (`ApplicationSkills.jsx`, the `Box` wrapping header row + cards) | `testid needed: agent-skills-section` | needs-adding — no hits on main or automation/testids; source confirms (`ApplicationSkills.jsx`) the container `Box` carries only `sx` styling, no `data-testid` | Scope: exactly the container the case's test touches (header row + counter + cards), per role-overrides.md's no-blanket-add rule — do not testid the whole accordion, just this content Box. |
| Skills counter text ("N/5 skills added.") | `testid needed: agent-skills-counter` | needs-adding — no hits on main or automation/testids | Live-confirmed the counter updates 0/5 → 1/5 on attach with no testid on the `Typography` node (`ApplicationSkills.jsx`). |
| Attached skill card (`SkillCard.jsx`) | `testid needed: skill-card-{skill_id}` (dynamic; `skill.skill_id` is in scope in the component) | needs-adding — no hits on main or automation/testids | Live-confirmed: card renders name + `base` version with zero testid anywhere in `cardContainer`/`cardHeader`/action buttons; `skill_id` is available as a prop, so the dynamic id is a same-PR addition, not a follow-up. |
| Skill-attach popper item (add-skill flow, step 4–5; shared `UnifiedDropdown.jsx`) | `[data-testid="toolkit-menu-item"]` scoped by accessible name (`getByRole('menuitem', {name: skill_name})` filtered to the testid) | on-main ✓ — `git grep -n "toolkit-menu-item" origin/main -- '*.jsx'` → 2 hits, `src/components/UnifiedDropdown.jsx:303,339`; also on `origin/automation/testids` (same 2 lines) | **Live-confirmed for the SKILL-attach flow specifically**, not just toolkits: attached a real skill end-to-end this run — clicking the "+ Skill" button opens `UnifiedDropdown` and the resulting `menuitem` for the skill (`elitea-1735-rework-verify`) carries `data-testid="toolkit-menu-item"` (checked via live `element.evaluate` → `{testid: "toolkit-menu-item", role: "menuitem"}`). Name is generic/shared (reused from the Toolkits popper) but present on every `UnifiedDropdown` consumer including skills — implementer needs the additive `Popper.select_menuitem`-sibling helper called out in dispatch, not a modification to the existing method (other callers depend on it). |
| Chat message input, real `<input>` node (`UserInput.jsx` `slotProps.htmlInput`) | `chat-message-input`, as a class-level `LocatorDescriptor` field | on-main ✓ — `git grep -n "chat-message-input" origin/main` → `src/ComponentsLib/Chat/UserInput.jsx:360` (plus an unrelated FSD constants-file reference, not a second DOM node) | Live-confirmed via `getByTestId('chat-message-input').evaluate(...)` → testid present. Implementer note: promote out of the inline `get_by_test_id(...)` call in the method body used by PR #39 into a class field — the testid itself was already correct, only its Python-side shape violated policy. |
| Chat send button | `chat-send-button`, already a class field `chat_send_button` — reuse it | on-main ✓ — `git grep -n "chat-send-button" origin/main` → `src/[fsd]/features/chat/ui/chat-button/SendButton.jsx:76` | No new work; PR #39 re-constructed this handle inline instead of reusing the existing field — stop doing that, nothing to add. |
| Last chat response text (`ApplicationAnswer.jsx`) | `skill-test-last-response`, as a class-level `LocatorDescriptor` field | on-main ✓ — `git grep -n "skill-test-last-response" origin/main` → `src/[fsd]/features/chat/ui/chat-box/ApplicationAnswer.jsx:593` (conditional: `isLastMessage ? 'skill-test-last-response' : 'chat-answer-content'`) | Same shape fix as the chat input row: testid already correct and present on main, just needs to move from an inline call into a class field. |
| Clear-the-chat button (shared `ClearChatButton.jsx`, 5 consumers incl. the agent detail page) | `testid needed: chat-clear-button` on the shared component | needs-adding — no hits on main or automation/testids | Confirmed ambiguity live and in source: `ClearChatButton.jsx` (`aria-label="clear the chat"`) and `RunHistoryContainer.jsx:77` (`aria-label="clear the chat"`, unrelated raw button) both carry the identical literal aria-label — PR #39's `get_by_label("clear the chat").first` is a footgun (works today by DOM order, not by contract). Adding the testid to the shared component is safe for all 5 consumers (additive, no behavior change). |
| Mention popper container (`MentionSkillList.jsx`) | `testid needed: skill-mention-list` on the container `Box` | needs-adding — no hits on main or automation/testids | Live-confirmed: typed `~` in `chat-message-input`, popper appeared with header text "Mention skill"; container `Box` and the header `Typography` both carry no `role` and no `data-testid` (`element.evaluate` → `{testid: null, role: null}`). PR #39's ancestor-xpath walk (`get_by_text("Mention skill").locator("xpath=ancestor::div[2]")`) is exactly the fragile pattern this policy exists to kill. |
| Mention popper item (`MentionToolItem.jsx`, shared with `InstructionsSlashSuggestionList.jsx` via `MentionToolList.jsx`) | `testid needed: skill-mention-item-{skill-name}` via an optional `testId` prop (only `MentionSkillList` passes it; `InstructionsSlashSuggestionList` leaves it undefined) | needs-adding — no hits on main or automation/testids | Live-confirmed: the rendered item (`elitea-1735-rework-verify` / description) is a plain `<Box onClick>` with no `role`, no `data-testid` (`element.evaluate` → `{testid: null, role: null, tag: "DIV"}`). Additive optional prop — the other `MentionToolItem` consumer is unaffected since it won't pass `testId`. |
| Skill controls (overflow) menu | `skill-controls-menu-button` | on-main ✓ (confirmed via live DOM, this run — used to delete the verification skill) | opens VERSION/SKILL grouped menu |
| Delete-skill menu item | `skill-delete-menu-item` | on-main ✓ (confirmed via live DOM, this run) | in the SKILL group |
| Agent actions (overflow) menu | `agent-actions-menu-button` | on-main ✓ (confirmed via live DOM, this run — used to delete the verification agent) | opens VERSION/AGENT grouped menu |
| Delete-agent menu item | `delete-agent-menuitem` | on-main ✓ (confirmed via live DOM, this run) | in the AGENT group |
| Delete-confirmation name field | `delete-confirm-name-input` (scope to inner `#name` field) | on-main ✓ (confirmed via live DOM, this run) | shared component, used by both skill and agent delete flows |
| Delete-confirmation confirm button | `testid needed: delete-confirm-button` — currently `getByRole('button', { name: 'Delete' })` scoped to the dialog | needs-adding (role/name handle in use today; no testid found on main or automation/testids for this specific button) | Out of this case's touch-scope per role-overrides.md's no-blanket-add rule (the case doesn't assert *this* button as its own observable, cleanup only uses it) — flagged here for completeness, not filed as a blocking request for ELITEA-1735; the implementer may fold it into the same `add-data-testid` batch as the other cleanup-flow testids if convenient, but it does not block `ready-for-automation` for this case. |

## Expected Results
- Skills 1 and 2 are created and saved successfully with distinct IDs.
- The agent is created and both skills attach with `base` version shown on
  each card; attachment persists immediately (API-level auto-save, no
  agent-level Save needed).
- A plain message with no `~mention` should NOT apply either skill's
  formatting — **this is not reliably true; see Known Defects**.
- A message with `~<skill-1-name> <prompt>` returns the prompt's answer
  entirely in UPPER CASE.
- A message with `~<skill-2-name> <prompt>` returns the prompt's answer with
  every space replaced by `_`.

## Coverage Map

### Axis 1 — Case element → Coverage
| Case element | Expected result | Covered by | Asserted where | Disposition |
|---|---|---|---|---|
| Step 1: Create Skill 1 (uppercase) | Skill created & saved | Test Step 1 | Skill ID assigned, URL settles on `/skills/all/{id}` | covered |
| Step 2: Create Skill 2 (underscore) | Skill created & saved | Test Step 2 | Skill ID assigned, distinct from Skill 1 | covered |
| Step 3: Create Agent, attach both skills | Agent created, both skills listed attached | Test Steps 3–5 | Skills section shows "2/5 skills added.", both cards render | covered |
| Step 4: Plain message → no skill formatting | Response NOT uppercase, NOT underscore-delimited | Test Step 6 | Response text asserted for absence of forced-uppercase/underscore pattern | **defect** — intermittently fails (1/3 in this run); see Known Defects |
| Step 5: `~skill1 <prompt>` → uppercase | Response entirely UPPER CASE | Test Step 7 | Response text asserted all-caps | covered |
| Step 6: `~skill2 <prompt>` → underscore-delimited | Response uses `_` between words | Test Step 8 | Response text asserted underscore-delimited, not uppercase | covered |
| Test Data: invocation syntax `~skill1`/`~skill2` (case placeholder names) | literal `~skill1`/`~skill2` strings | N/A — **case-text drift**, not a defect | Live syntax is `~<mention>` via an autocomplete keyed on the skill's actual name, triggered by typing `~` | clarification (reverse-masking; case uses generic placeholder names, product correctly uses real skill names as mention targets) |

### Axis 2 — Observables asserted beyond the case
| Observable | Reason |
|---|---|
| Skill-attach network call (`PATCH .../skill/prompt_lib/{project}/{id}` → `201`) | Confirms attachment is an immediate API-level auto-save, not deferred to agent-level Save — material for correct wait strategy in automation (don't wait on/assert `agent-save-button` state after attaching a skill) |
| Console messages checked after every step | Zero errors observed across all 8 steps; ruled out silent JS failures as an explanation for the intermittent defect |
| `fill()` vs `press_sequentially()` on the mention-aware chat input | `fill()` replaces the entire textbox value, destroying an already-inserted `~mention` chip; this is a load-bearing automation gotcha, not explicit in the case, but any implementer will hit it on first attempt |

## Known Defects

### github.com/EliteaAI/elitea-testing-public/issues/38 — [MAJOR] Agent applies skill formatting to plain (non-invoked) messages intermittently
- **Repro rate**: 1/3 attempts in this run. Plain message "Write one short
  sentence about the weather today." (no `~mention`) returned
  `THE_SUN_IS_SHINING_BRIGHTLY_THIS_AFTERNOON.` — both skills' formatting
  applied simultaneously with no invocation. Two subsequent plain-message
  attempts ("Tell me a fun fact about cats.", "What is the capital of
  France?") returned normal, unformatted prose.
- **Root-cause hint**: the model's own "Thinking" trace (observed during the
  explicit-invocation steps) shows the agent is instructed to scan
  `<available_skills>` and autonomously decide whether to `load_skill` based
  on relevance to the user's message — not gated purely on the `~mention`
  syntax. This makes plain-message behavior a model judgment call rather
  than a deterministic contract.
- **Evidence**: `test-results/screenshots/ELITEA-1735-step4-plain-message-defect.png`,
  `test-results/screenshots/ELITEA-1735-step4-plain-message-normal-attempt3.png`.
- **Automation guidance**: per `.agents/profile.md` § Bug filing (isolated
  defect → `expect.soft()` with ticket linked), assert step 6 (plain message)
  with a soft assertion referencing issue #38, and hard-assert the rest of
  the flow (skill creation, attachment, explicit-mention invocation for both
  skills) which reproduced 100% reliably across all attempts in this run.

## Cleanup

Three entities are created per run: Skill 1 (uppercase), Skill 2 (underscore),
and the Agent that attaches both. All three were deleted live in this run to
confirm the mechanics below.

1. **Delete the Agent first, then the two Skills.** Verified live: deletion
   order does **not** actually matter at the API level — a skill can be
   deleted via `SkillAPI.delete_skill()` / the UI overflow menu **while still
   attached to an agent**, with no dependency error (`DELETE
   .../skill/prompt_lib/{project}/{skill_id}` returned `204 No Content` with
   skill 66 still attached to agent 4565 at the time of deletion). The
   agent's Skills section self-corrects on next load — it silently dropped
   the deleted skill's card and updated the counter from "2/5 skills added."
   to "1/5 skills added." with no console error, no dangling-reference UI
   state. **Recommended order is still agent-before-skills** (delete the
   thing with more attached state first) purely for teardown hygiene/least
   astonishment, not because the API enforces it.
2. **Agent deletion**: via UI overflow menu → "AGENT" group → "Delete agent"
   (`data-testid="delete-agent-menuitem"`) → type-to-confirm dialog (same
   pattern as skills — `data-testid="delete-confirm-name-input"`, inner
   `#name` field) → click "Delete". Verified: `DELETE
   /api/v2/elitea_core/application/prompt_lib/{project}/{agent_id}` → `204
   No Content`, redirects away from the agent detail page, no console
   errors. **For automated cleanup, prefer the existing `agent_api` fixture**
   (`automation/fixtures/api_fixtures.py`) — `AgentAPI.delete_agent(agent_id)`
   in `automation/api/client.py:452`. A project-level session-scoped safety
   net (`cleanup_autotest_agents_at_end` in
   `automation/fixtures/cleanup_fixtures.py`) already deletes any leftover
   `autotest_`-prefixed agents at session end, but is skipped on localhost
   (no browser-cookie auth) and only catches the `autotest_` naming
   convention — don't rely on it alone; give the agent an `autotest_`-
   prefixed name if you want that safety net to apply, and still delete it
   explicitly in the test's own teardown.
3. **Skill deletion (both Skill 1 and Skill 2)**: via UI overflow menu →
   "SKILL" group → "Delete skill" (`data-testid="skill-delete-menu-item"`) →
   same type-to-confirm dialog pattern → click "Delete". Verified: `DELETE
   /api/v2/elitea_core/skill/prompt_lib/{project}/{skill_id}` → `204 No
   Content` for both skills, no console errors (the immediate follow-up `GET
   .../skill/prompt_lib/{project}/{skill_id}` → `404` seen in the network
   log afterward is an expected stale-refetch artifact of the redirect, not
   a defect). **For automated cleanup, use the existing `skill_api` fixture**
   (`automation/fixtures/api_fixtures.py`) — `SkillAPI.delete_skill(skill_id)`
   in `automation/api/client.py:1227` — mirroring the `clean_skill` fixture
   pattern in `automation/tests/ui/skills/test_skill_management.py:32`
   (list-and-delete-if-exists before the test, delete again in teardown,
   tolerating "already gone" errors). Track both skill IDs from Test Steps 1
   and 2 and delete both.
4. **Recommended teardown fixture shape** (mirrors `clean_skill`): a
   function-scoped fixture that creates the agent + 2 skills via UI in the
   test body, yields their IDs, and in its `finally`/post-yield block calls
   `agent_api.delete_agent(agent_id)` then `skill_api.delete_skill(skill_id)`
   for each skill ID, wrapping each call in its own `try/except` so one
   failed delete doesn't skip the others (same tolerance pattern as
   `clean_skill`'s `_delete_if_exists`).

## Blocked Steps
None — case executed end-to-end; the one blocker encountered (defect above)
does not prevent the remaining steps from completing.
