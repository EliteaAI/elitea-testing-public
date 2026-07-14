# Test Case: Ghost skill not shown after Agent participant removed (Chat `~` mention)

## Metadata
- **TMS ID**: ELITEA-1793
- **Linked Story**: none
- **Priority**: l3 (medium, per case)
- **Environment Explored**: local (`http://localhost:5173`, EliteaUI `automation/testids` branch → DEV backend), project `Private` / `${ELITEA_PROJECT_ID}`=399, model: Anthropic Claude 4.5 Sonnet
- **User set**: `${TEST_USER}` (on localhost, `auth_state` fixture skips login via `VITE_DEV_TOKEN`)
- **Analyst**: qa-engineer (Sage), analyst slot
- **Status**: **defect-found** — see Known Defects. All 6 case steps were executed
  end-to-end; steps 1–4 (add participant, confirm `~mention` shows the skill,
  dismiss, remove participant) behave exactly as expected. Steps 5–6 (re-check
  `~mention` after removal) **fail**: the removed agent's skill remains
  listed in the "Mention skill" popper. Reproduced 2/2 in this run (once in
  the original session, once again after a full page reload as an
  independent confirmation). Filed as
  github.com/EliteaAI/elitea-testing-public/issues/51 — new defect, not a
  duplicate of #38 (that defect is about *autonomous invocation without a
  mention*; this one is about the mention **suggestion list itself**
  retaining a stale entry).
- **Classification rationale (fresh vs extend-existing)**: ELITEA-1736
  covers *adding* an agent participant and using `~mention` to invoke its
  skill, but never removes the participant — the remove-then-recheck flow is
  entirely novel. Given the case failed (defect-found), this is emitted as a
  standalone fresh AFS rather than an extension of ELITEA-1736's spec — once
  the defect is fixed, the implementer should decide whether to fold the
  remove-and-recheck assertions into `test_skill_conversation_interaction.py`
  (extending the existing fixture) or keep this as its own test; the AFS
  captures the handles either way.

## Preconditions
- User is logged in (on localhost, `auth_state` fixture skips login).
- A project is selected/accessible (`Private`, id `399` in this run).
- Skills, Agents, and Chat sections are available in the project.

## Test Data

### generate-per-test (in test setup, cleaned up in its own teardown)
- Skill name: kebab-case, e.g. `robot-joker-1793-<random>` — **must be
  lowercase letters/digits/hyphens only**, client-side validated (same
  constraint documented in ELITEA-1736/1737's AFS files). The case's literal
  name **"Robot-Joker"** is case-text drift; the live product blocks mixed
  case. Used `robot-joker-1793` in this run (skill id `271`).
- Skill instructions: any non-empty string (used `"Tell jokes about robots.
  Always output in UPPER CASE"`, reused from ELITEA-1736 for consistency —
  content is irrelevant to this case, only the skill's *presence in the
  mention list* is asserted).
- Skill description: any non-empty string (used as the description text
  visible in the "Mention skill" popper card — assert this too, it's a
  free signal that the correct skill row is showing).
- Agent name: e.g. `Joker-Agent-1793-<random>` (case's literal "Joker
  Agent" — mixed-case with a space — is accepted live for **Agent** names,
  unlike Skill names; no client-side kebab-case constraint observed on the
  Agent Name field). Used `Joker-Agent-1793` in this run (agent id `4687`).
- Agent description / instructions: any non-empty string.
- No chat message is ever sent in this case — `~` is typed and the popper
  is inspected, but Enter/send is never pressed, so **no conversation
  object is ever created** (chat sidebar stays "Still no conversations
  created." throughout). This simplifies cleanup: no conversation delete
  step is needed, only agent + skill deletion.

No `reuse-existing` or shared fixture applies — this is a fresh-state flow (1
skill + 1 agent, created and torn down within the test; no persistent
conversation).

## Test Steps

1. Navigate to `${BASE_URL}/skills/create`. Fill Name
   (`getByRole('textbox', { name: 'Name *' })`) with a kebab-case skill
   name, Description (`getByRole('textbox', { name: 'Description *' })`),
   and Instructions (`skill-instructions-editor-content`, CodeMirror — use
   `press_sequentially`, not `fill`). Click Save (`skill-save-button`).
   - **Verify**: `POST /api/v2/elitea_core/skills/prompt_lib/{project}` →
     `201 Created`. Note the skill ID (`271` in this run).
2. Navigate to `${BASE_URL}/agents/create`. Fill Name (`agent-name-input`),
   Description (`agent-description-input`), Instructions
   (`agent-instructions-input`). Click Save (`agent-save-button`).
   - **Verify**: navigates to `/agents/all/{agent-id}?destTab=configuration...`.
     Note the Agent ID (`4687` in this run).
3. On the agent detail page, the **Skills** accordion is expanded by
   default. Click the add-skill button (`getByRole('button', { name:
   'Skill', exact: true })` inside the Skills region — same handle as
   ELITEA-1735/1736). A "Search skills..." popper opens with menuitems
   `role="menuitem"`, including a `"Create new"` option and every existing
   skill by name. Click the target skill's menuitem.
   - **Verify**: `PATCH /api/v2/elitea_core/skill/prompt_lib/{project}/{skill-id}`
     → `201 Created` fires immediately (auto-saved). Skills section shows
     "1/5 skills added." with a card for the attached skill (`base` version).
4. Navigate to `${BASE_URL}/chat`. Click `plus-menu-button` → "Agents"
   menuitem (opens a tooltip menu: Modules / Agents / Pipelines / Toolkits
   / MCPs) → select the agent's menuitem from the "Search agents..."
   popper that opens.
   - **Verify**: composer's Model Selector group switches to `button
     "Switch Agent"` showing the agent's name; a button labelled with the
     participant count (`"1"`) appears next to it, wrapped in a
     `generic[aria-label="Agents in this conversation"]` container (no
     distinct testid).
5. Click into `chat-message-input`, type `~` via `press_sequentially`/
   `slowly` (NOT `fill` — a `fill()` bypasses the mention-trigger keyup
   handler and the popper never opens).
   - **Verify**: a "Mention skill" popper (heading text `"Mention skill"`,
     plain `<div>`s, no ARIA role/testid — same `MentionSkillList.jsx`
     component documented in ELITEA-1735/1736) opens listing the attached
     skill by its real saved name (e.g. `robot-joker-1793`) with its
     description text alongside.
6. Press `Escape` to dismiss the popper without selecting anything.
   - **Verify**: the popper closes; the literal `~` character remains in
     the (still-focused) message input; no navigation, no console errors.
7. Clear the message input (select-all + delete). Click the participant
   badge (`getByRole('button', { name: '1' })`, the same "Agents in this
   conversation" badge from step 4) to open a small popper headed
   `"Agents"` listing each participant agent by name + version
   (`plain <div>`, no ARIA role/testid). **Hover** the agent's row — this
   reveals two icon buttons absent from the accessibility tree until
   hovered: `button "Edit agent"` and `button "Remove agent"` (same
   hover-reveal pattern as the agent-detail Skills card's remove control,
   per `.agents/memory/qa-engineer/agent_skill_card_remove_control_quirks.md`).
   Click `button "Remove agent"`.
   - **Verify**: a confirmation dialog opens — `heading "Remove agent?"`,
     body text `"Are you sure to remove the {agent name} agent from
     chat?"`, `button "Cancel"` / `button "Remove"`. Click `"Remove"`.
   - **Verify**: composer reverts to `"Select LLM Model"` →
     `"Anthropic Claude 4.5 Sonnet"` (default model, no agent); the
     "Agents in this conversation" badge/button disappears entirely from
     the DOM (0 participants — no badge shown at all, not a badge showing
     `"0"`).
8. Click into `chat-message-input` again (a *fresh* textbox element after
   the composer re-render — re-snapshot to get a new ref) and type `~`
   again via `press_sequentially`.
   - **Expected per case**: the "Mention skill" popper either does not
     appear, or appears without the removed agent's skill listed (e.g.
     `"No skills attached to this agent"`, the empty-state text confirmed
     live in a fresh conversation that never had a participant added).
   - **Actual (DEFECT)**: the "Mention skill" popper opens and **still
     lists the skill** that belonged to the just-removed agent, with its
     description text, exactly as in step 5 — as if the agent were still
     a participant. See Known Defects.

## Handles Reference

| Element | testid / locator | Notes |
|---|---|---|
| Skill Name field | `getByRole('textbox', { name: 'Name *' })` | kebab-case-only client validation |
| Skill Description field | `getByRole('textbox', { name: 'Description *' })` | |
| Skill Instructions editor | `skill-instructions-editor-content` | CodeMirror; use `press_sequentially` |
| Skill Save button | `skill-save-button` | |
| Agent Name field | `agent-name-input` | mixed-case + spaces accepted (unlike Skill Name) |
| Agent Description field | `agent-description-input` | |
| Agent Instructions field | `agent-instructions-input` | |
| Agent Save button | `agent-save-button` | |
| Agent add-skill button (Skills accordion) | `getByRole('button', { name: 'Skill', exact: true })` | Confirmed live; same handle as ELITEA-1735/1736 |
| Skill-attach popper item | `role="menuitem"`, accessible name = skill name | |
| Chat composer "+" button | `plus-menu-button` | Opens tooltip menu: Modules / Agents / Pipelines / Toolkits / MCPs |
| "Agents" menuitem in plus-menu | `role="menuitem"`, accessible name `"Agents"` | Opens "Search agents..." popper |
| Agent-select popper item (chat participant add) | `role="menuitem"`, accessible name = agent's display name | |
| Chat message input | `chat-message-input` | mention-aware; use `press_sequentially`, never `fill()` — ref changes across composer re-renders (e.g. after agent add/remove), always re-snapshot before reusing |
| Chat send button | `chat-send-button` | not used in this case (never sent a message) |
| "Mention skill" popper container | plain `<div>` headed `"Mention skill"`, **no ARIA role, no testid** (`MentionSkillList.jsx`) | Contains either skill-name menuitem-like rows, or the empty-state text `"No skills attached to this agent"` when the participant agent has no skills / no participant exists |
| "Switch Agent" composer button (agent-as-participant) | no testid; `aria-label="Switch Agent"` — `getByRole('button', { name: 'Switch Agent' })` | Renders once an agent is added as chat participant; text = agent name |
| "Agents in this conversation" participant badge | no testid; wrapping `div[aria-label="Agents in this conversation"]` containing `getByRole('button', { name: <participant count> })` | Click opens the small "Agents" participants popper (step 7). **Disappears entirely from the DOM** when the participant count returns to 0 — assert absence, not a `"0"` label. |
| "Agents" participants popper | plain `<div>` headed `"Agents"`, one row per participant (agent name + version, e.g. `"base"`) | No ARIA role/testid on rows |
| Participant row "Edit agent" / "Remove agent" icon buttons | `button "Edit agent"`, `button "Remove agent"` | **Hover-revealed** — absent from the accessibility-tree snapshot until the row is hovered (same hover-reveal pattern as the agent-detail Skills card's remove control) |
| "Remove agent?" confirmation dialog | `heading "Remove agent? Close"`, body text `"Are you sure to remove the {agent name} agent from chat?"`, `button "Cancel"`, `button "Remove"` | Standard MUI confirm dialog, no type-to-confirm (unlike agent/skill entity delete) |
| Agent overflow menu (agent detail page) | `agent-actions-menu-button` | AGENT group → `delete-agent-menuitem` |
| Skill overflow menu (skill detail page) | `skill-controls-menu-button` | SKILL group → `skill-delete-menu-item` |
| Delete-confirmation name field | `delete-confirm-name-input` (scope to inner `#name` field) | shared component across agent/skill delete flows; type-to-confirm required |

## Expected Results
- Adding an agent as a chat participant surfaces its attached skill via
  `~mention` (matches ELITEA-1736's finding).
- Dismissing the popper with Escape works cleanly, no residual state.
- Removing the agent participant clears both the "Switch Agent" composer
  button and the "Agents in this conversation" badge.
- Re-typing `~` after removal should NOT surface the removed agent's
  skill — **this is NOT true live; see Known Defects.**

## Coverage Map

### Axis 1 — Case element → Coverage
| Case element | Expected result | Covered by | Asserted where | Disposition |
|---|---|---|---|---|
| Step 1: Add "Joker Agent" as chat participant | Agent appears in participants list | Test Steps 1–4 | "Switch Agent" composer button shows agent name; "Agents in this conversation" badge shows count `1` | covered |
| Step 2: Type `~`, dropdown shows "Robot-Joker" | "Mention skill" popper lists the skill | Test Step 5 | Popper shows `robot-joker-1793` + description | covered (skill name substituted per case-text drift — see clarification row below) |
| Step 3: Dismiss dropdown without selecting | Dropdown closes | Test Step 6 | Popper closed via Escape; input retains literal `~` | covered |
| Step 4: Remove "Joker Agent" from participants | Agent no longer listed as participant | Test Step 7 | "Switch Agent" button gone, composer shows default model; participant badge removed from DOM entirely | covered |
| Step 5: Type `~` again | Dropdown either absent or shows without the skill | Test Step 8 | Popper still shows the removed agent's skill (`robot-joker-1793`) | **defect** — see Known Defects |
| Step 6: Confirm skill absent from `~` suggestions | Skill not shown | Test Step 8 | Skill IS shown (ghost) | **defect** — see Known Defects |
| Test Data: skill name literal "Robot-Joker" (mixed case) | literal name `Robot-Joker` | N/A — case-text drift, not a defect | Live Skill Name field rejects non-kebab-case names client-side; substituted `robot-joker-1793` | clarification (reverse-masking; same finding as ELITEA-1736/1737) |

### Axis 2 — Observables asserted beyond the case
| Observable | Reason |
|---|---|
| Control check: fresh conversation, no participant ever added, type `~` | Confirms the "No skills attached to this agent" empty state is the CORRECT baseline behavior when there's genuinely no participant — proves the bug is specifically a stale-state-after-removal issue, not "the mention list always shows all project skills" (a second, unattached skill `automated-test-explainer` existed in the project throughout and never appeared in any popper state, ruling out a project-wide-list theory) |
| Skill-attach network call (`PATCH .../skill/prompt_lib/{project}/{id}` → `201`) | Confirms attachment is an immediate API-level auto-save |
| No network round-trip on typing `~` (before or after removal) | Confirms the "Mention skill" popper is populated from client-side state, not a fresh API call per keystroke — this pins the defect to stale front-end state (a memo/cache not invalidated on participant removal), not a backend data-sync issue |
| Console messages checked after every step (both repro attempts) | Zero errors in either attempt; only pre-existing unrelated warnings (MUI Tooltip disabled-child, Vite "stream" externalization) |
| Reproduced 2/2 (independent cycles, second one after a full page reload) | Confirms this is a deterministic defect, not a flaky/timing issue like #38 |
| Cleanup performed live (agent + skill deleted; no conversation ever created) | Confirms delete lifecycle works cleanly; also documents that this case's flow never creates a persisted conversation, simplifying teardown relative to ELITEA-1736 |

## Known Defects

### github.com/EliteaAI/elitea-testing-public/issues/51 — [MAJOR] Ghost skill remains in `~` mention suggestions after its Agent participant is removed from Chat
- **This IS the defect the TMS case exists to catch** — case ELITEA-1793
  passed a hypothesis ("removed agent's skill should disappear from
  `~mention`") through live execution and the hypothesis failed.
- **Repro rate**: 2/2 (add → confirm-shown → remove → confirm-hidden,
  repeated twice; second attempt after a full page reload as an
  independent session, ruling out one-off React state corruption from the
  first attempt).
- **Evidence**: screenshots `test-results/screenshots/ELITEA-1793-step2-mention-before-removal.png`
  (correct pre-removal state), `test-results/screenshots/ELITEA-1793-step4-remove-agent-control.png`
  (hover-revealed remove control), `test-results/screenshots/ELITEA-1793-step5-ghost-skill-still-shown.png`
  and `test-results/screenshots/ELITEA-1793-repro2-ghost-skill.png` (both
  show the ghost skill post-removal).
- **Root-cause hint**: no network call fires when typing `~` in either the
  correct or ghost case — the mention-skill list is populated from
  client-side component state. Most likely a memoized/derived list of
  "skills contributed by current participant agents" that updates on
  participant-*add* but isn't recomputed/invalidated on participant-
  *remove*. A fresh page load with no participant ever added correctly
  shows the "No skills attached to this agent" empty state, which rules
  out "the popper always lists all project skills" as an alternative
  explanation.
- **Not a duplicate of #38** — #38 is about an agent *autonomously
  invoking* a skill on a plain non-`~mention` message (intermittent,
  ~1/3 rate, LLM-prompt-layer root cause). This defect is purely a UI
  suggestion-list staleness bug with a 2/2 deterministic repro and no LLM
  involvement at all (never got as far as sending a message).
- **Automation guidance**: per `.agents/profile.md` § Bug filing, this is
  a genuine blocking defect for steps 5–6 of the case — the implementer
  should hard-assert steps 1–4 (add participant, confirm mention shown,
  dismiss, remove participant) and either (a) skip/xfail steps 5–6 with
  the issue linked until #51 is fixed, or (b) assert the *current* (buggy)
  behavior with a comment referencing #51 so the test goes red the moment
  the fix ships (team preference — not prescribed here, since #51 is a
  blocking rather than isolated defect per the profile's distinction).

## Blocked Steps
None — the case was executed end-to-end; the defect above does not block
completion, it IS the case's finding.

## Cleanup

One skill and one agent are created per run; **no conversation is ever
created** (message never sent, so no conversation object exists to
delete).

1. **Delete the Agent**: navigate to the agent detail page → open
   `agent-actions-menu-button` → AGENT group → `delete-agent-menuitem` →
   type-to-confirm dialog (`delete-confirm-name-input` inner `#name`
   field, must match exactly) → click "Delete". Verified: redirects to
   `/agents/all`, no console errors.
2. **Delete the Skill**: navigate to the skill detail page → open
   `skill-controls-menu-button` → SKILL group → `skill-delete-menu-item` →
   same type-to-confirm dialog pattern → click "Delete". Verified:
   redirects to `/skills/all`, no console errors.
3. **Recommended teardown fixture shape**: a function-scoped fixture that
   creates the skill + agent via UI in the test body, yields their IDs,
   and in its `finally`/post-yield block deletes the agent then the skill,
   each in its own `try/except`. No conversation cleanup needed for this
   specific case's flow (never sends a message) — but if the implementer
   extends this into a version that DOES send a message post-removal (to
   further probe the ghost skill's actual invokability, not just its
   listing), add conversation deletion per ELITEA-1736's pattern
   (`conversation-menu-menu-button` → "Delete" → plain Cancel/Delete
   confirm, no type-to-confirm).
