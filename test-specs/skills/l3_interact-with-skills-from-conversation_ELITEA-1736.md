# Test Case: Interact with Skills from Conversation

## Metadata
- **TMS ID**: ELITEA-1736
- **Linked Story**: none
- **Priority**: l3 (medium, per case)
- **Environment Explored**: local (`http://localhost:5173`, EliteaUI `automation/testids` branch → DEV backend, project `Private` / `${ELITEA_PROJECT_ID}`=399), model: Anthropic Claude 4.5 Sonnet
- **User set**: `${TEST_USER}` (on localhost, `auth_state` fixture skips login via `VITE_DEV_TOKEN`)
- **Analyst**: qa-engineer (Sage), analyst slot
- **Status**: defect-found — see Known Defects. Skill creation, agent creation
  + attach, chat-participant addition, and explicit `~mention` invocation
  (steps 1–3, 5) are ready-for-automation; step 4 (plain-message
  non-invocation, in a chat-**participant** context rather than the
  agent-level context of ELITEA-1735) reproduced the SAME known intermittent
  product defect (github.com/EliteaAI/elitea-testing-public/issues/38) on the
  **first and only** attempt in this run. Recommend automating with
  `expect.soft()` around the step-4 assertion per project's isolated-defect
  policy (`.agents/profile.md` § Bug filing), ticket #38 linked (do not file
  a duplicate — this is the same defect surfacing in a second context), rest
  of the flow hard-asserted.

## Preconditions
- User is logged in (on localhost, `auth_state` fixture skips login).
- A project is selected/accessible (`Private`, id `399` in this run).
- Skills, Agents, and Chat sections are available in the project.

## Test Data

### generate-per-test (in test setup, cleaned up in its own teardown)
- Skill name: kebab-case, e.g. `robot-joker-elitea-1736-<random>` — **must be
  lowercase letters/digits/hyphens only**, client-side validated (see
  `.agents/memory/qa-engineer/skill_form_and_export_import_quirks.md`). The
  case's literal name **"Robot-Joker"** (mixed case, no lowercase-only
  constraint honored) is **case-text drift** — the live product blocks it;
  don't try to script the literal case name (reverse-masking guard).
- Skill instructions: `"Tell jokes about robots. Always output in UPPER
  CASE"` (used verbatim from the case — this instruction text itself is
  fine, it's only the *skill name* that needs kebab-case substitution).
- Agent name: e.g. `Joker-elitea-1736-<random>`; description any non-empty
  string; instructions: `"Entertain the user with jokes"` (verbatim from
  case).
- Chat prompts: `"Tell me a joke"` (plain, step 4) and
  `"~<real-skill-name> Tell me a joke"` (skill-invoked, step 5) — the
  case's literal invocation syntax `~Robot-Joker` is **case-text drift**;
  the live mention syntax is `~<mention>` keyed on the skill's *actual*
  saved name via an autocomplete popper triggered by typing `~` (same
  finding as ELITEA-1735).

No `reuse-existing` or shared fixture applies — this is a fresh-state flow (1
skill + 1 agent + 1 chat conversation, all created and torn down within the
test).

## Test Steps

1. Navigate to `${BASE_URL}/skills/create` (via the sidebar "+ Skill"
   button — no testid, but stable accessible name `getByRole('button', {
   name: 'Skill', exact: true })`). Fill Name (`skill-name-input` — actually
   located via `getByRole('textbox', { name: 'Name *' })` in this run, no
   distinct testid observed separate from `agent-name-input`'s pattern —
   see Handles Reference), Description (`getByRole('textbox', { name:
   'Description *' })`), and Instructions (`skill-instructions-editor-content`,
   a CodeMirror editor — use `press_sequentially`/`type`, not `fill`, so
   React state updates) with the skill data above. Click Save
   (`skill-save-button`).
   - **Verify**: `POST /api/v2/elitea_core/skills/prompt_lib/{project}` →
     `201 Created`. Skill saved; note its ID (e.g. `92` in this run).
2. Navigate to `${BASE_URL}/agents/create` (sidebar "+ Agent" button, same
   pattern as "+ Skill"). Fill Name (`agent-name-input`), Description
   (`agent-description-input`), and Instructions (`agent-instructions-input`)
   with the agent data above. Click Save (`agent-save-button`).
   - **Verify**: navigates to `/agents/all/{agent-id}?destTab=configuration...`;
     note the Agent ID (e.g. `4578` in this run).
3. On the agent detail page, expand the **Skills** accordion section
   (heading text "Skills"). Click the add-skill button (accessible name
   "Skill", exact — `getByRole('button', { name: 'Skill', exact: true })`,
   same handle documented in ELITEA-1735). A "Mention skill"-style popper
   opens listing available skills by their real names (`role="menuitem"`).
   Click the skill's menuitem to attach it.
   - **Verify**: `PATCH /api/v2/elitea_core/skill/prompt_lib/{project}/{skill-id}`
     → `201 Created` fires immediately (auto-saved, no agent-level Save
     needed — same as ELITEA-1735). Skills section counter shows "1/5
     skills added." with a card for the attached skill showing `base`
     version.
4. Navigate to `${BASE_URL}/chat`. Click the `plus-menu-button` next to the
   chat input, select the "Agents" menuitem from the resulting tooltip
   menu, then select the just-created agent's menuitem from the "Search
   agents..." popper that opens.
   - **Verify**: the Model Selector group in the chat composer switches to
     show "Switch Agent → {agent name}"; an "Agents in this conversation"
     badge appears showing count `1`. No console errors.
5. Type a plain message with **no `~` mention** (case's literal text: "Tell
   me a joke") into `chat-message-input` and press Enter. This creates the
   conversation (URL becomes `/chat/{conversation-id}?name=...`).
   - **Verify (expected per case)**: response text is a joke in normal
     sentence case, NOT forced to UPPER CASE.
   - **Known defect** — see Known Defects below; this assertion is flaky
     (confirmed in this run, first attempt).
6. Click into `chat-message-input`, type `~` using `slowly`/
   `press_sequentially` (NOT `fill` — destroys the mention chip once
   inserted), select the attached skill's menuitem from the "Mention skill"
   popper (accessible name = the skill's own saved name, e.g.
   `robot-joker-elitea-1736`), then append " Tell me a joke" (again via
   `slowly`/`press_sequentially`). Send via `chat-send-button`.
   - **Verify**: the composed message text reads
     `~<skill-name> Tell me a joke` with the mention chip intact before
     sending. Response text is entirely UPPER CASE and is a robot-themed
     joke (e.g. `"WHY DID THE ROBOT CROSS THE ROAD? BECAUSE IT WAS
     PROGRAMMED TO GET TO THE OTHER SIDE!"`). The visible "Thinking" trace
     (expand "Thought for N secs") shows a `"Skill: <skill-name>"` tag
     confirming the skill was loaded for this turn.

## Handles Reference

| Element | testid / locator | Notes |
|---|---|---|
| Sidebar "+ Skill" button | no testid; stable accessible name `getByRole('button', { name: 'Skill', exact: true })` | Same pattern documented for ELITEA-1735's agent-level add-skill button, but this is the top-level sidebar "create a new Skill entity" button — a different button with the same accessible name; scope by page/section if both are ever on screen together. |
| Skill Name field | `getByRole('textbox', { name: 'Name *' })` | kebab-case-only client validation |
| Skill Description field | `getByRole('textbox', { name: 'Description *' })` | |
| Skill Instructions editor | `skill-instructions-editor-content` | CodeMirror; use `press_sequentially` |
| Skill Save button | `skill-save-button` | |
| Sidebar "+ Agent" button | no testid; accessible name `getByRole('button', { name: 'Agent', exact: true })` | Same pattern as "+ Skill" |
| Agent Name field | `agent-name-input` | |
| Agent Description field | `agent-description-input` | |
| Agent Instructions field | `agent-instructions-input` | |
| Agent Save button | `agent-save-button` | |
| Agent add-skill button (Skills accordion) | `getByRole('button', { name: 'Skill', exact: true })` | Confirmed live in this run (ELITEA-1735's Phase-2 amendment holds) |
| Skill-attach popper item | `role="menuitem"`, accessible name = skill name | Real ARIA menuitem, confirmed |
| Chat composer "+" button | `plus-menu-button` | Opens tooltip menu: Modules / Agents / Pipelines / Toolkits / MCPs |
| "Agents" menuitem in plus-menu | `role="menuitem"`, accessible name `"Agents"` | Opens "Search agents..." popper |
| Agent-select popper item (chat participant add) | `role="menuitem"`, accessible name = agent's display name | Confirmed via live snapshot; plain menuitems, no distinguishing testid beyond name |
| Chat message input | `chat-message-input` | mention-aware; use `press_sequentially`, never `fill()`, when a `~mention` chip must be preserved |
| Chat send button | `chat-send-button` | |
| Chat `~mention` popper item | plain `<div>`, **no ARIA role, no testid** (same `MentionSkillList.jsx` component documented in ELITEA-1735) | Locate via text match scoped under the "Mention skill" header container |
| Chat message list | `chat-message-list` | container for all turns |
| Chat message item | `chat-message-item` | one per turn (both user + agent) |
| Chat agent response content | `chat-answer-content` | assert case (upper/normal) and joke-topic text here |
| "Agents in this conversation" participant badge | no testid; MUI `Tooltip` `title="Agents in this conversation"` on a collapsed-participants icon button | **Implementer Phase-2 correction**: the visible participant count ("1") is rendered via a CSS `::after` pseudo-element (`content: "${count}"` in `EliteaUI/src/[fsd]/features/chat/participants/ui/CollapsedParticipants/CollapsedPerticapantsList.jsx:296-297`) — confirmed by reading the EliteaUI source. It has no DOM text node and is unreadable via `text_content()` or any accessible-name query; the tooltip `title` itself is only in the accessibility tree while hovered/open, not persistently. Automated as: `getByRole("button", { name: "Switch Agent" })` composer button instead — the other signal this AFS's own Expected Results names as equivalent evidence of participant membership. |
| "Switch Agent" composer button (agent-as-participant) | no testid; stable `aria-label="Switch Agent"` — `getByRole('button', { name: 'Switch Agent' })` | Confirmed live via DOM inspection (ELITEA-1736 implementer Phase 2): once an agent is added as a chat participant, this ButtonGroup member renders `aria-label="Switch Agent"` and its text content becomes the agent's name + active version, replacing the model-name display. This is the automated assertion target for "Agent appears as participant" — matches the AFS's own "Switch Agent -> {agent name}" wording literally (it's the accessible name, not a paraphrase). The `[data-testid="model-selector-button"]` testid stays on the *model*-selector element only and is absent once an agent participant is active — do not use it for this assertion. |
| "Thought for N secs" reasoning toggle | `role="button"`, accessible name pattern `"Thought for {n} secs"` | expandable; reveals `"Skill: <skill-name>"` tag when a skill was loaded for that turn — useful debug signal, not a stable assertion target per se |
| Conversation menu (sidebar, hover to reveal) | `conversation-menu-menu-button` | Rename / Move to / Playback / Pin on top / Delete |
| Agent overflow menu | `agent-actions-menu-button` | AGENT group → `delete-agent-menuitem` |
| Skill overflow menu | `skill-controls-menu-button` | SKILL group → `skill-delete-menu-item` |
| Delete-confirmation name field | `delete-confirm-name-input` (scope to inner `#name` field) | shared component across agent/skill/chat delete flows (chat delete instead uses a plain Cancel/Delete dialog, no type-to-confirm) |

## Expected Results
- The skill is created and saved successfully with a distinct ID.
- The agent is created, attaches the skill (shown as "1/5 skills added."),
  and is addable as a chat participant (composer switches to the agent,
  "Agents in this conversation" badge shows `1`).
- A plain message with no `~mention` should NOT apply the skill's UPPER
  CASE formatting — **this is not reliably true in a chat-participant
  context either; see Known Defects**.
- A message with `~<skill-name> <prompt>` returns a robot joke entirely in
  UPPER CASE, and the "Thinking" trace confirms `Skill: <skill-name>` was
  loaded for that turn.

## Coverage Map

### Axis 1 — Case element → Coverage
| Case element | Expected result | Covered by | Asserted where | Disposition |
|---|---|---|---|---|
| Step 1: Create Skill "Robot-Joker" | Skill created & saved | Test Step 1 | `POST .../skills/prompt_lib/{project}` → `201`, Skill ID assigned | covered (name substituted to kebab-case per case-text drift, see clarification row below) |
| Step 2: Create Agent "Joker", attach skill | Agent created with skill listed as attached | Test Steps 2–3 | Skills section shows "1/5 skills added.", card renders `robot-joker-elitea-1736` @ `base` | covered |
| Step 3: Open Chat, add Agent "Joker" as participant | Agent appears as participant in the conversation | Test Step 4 | Model Selector shows "Switch Agent → Joker-elitea-1736"; "Agents in this conversation" badge shows `1` | covered |
| Step 4: Plain message "Tell me a joke" → NOT upper case | Response is a joke, not upper case | Test Step 5 | Response text asserted for absence of forced UPPER CASE | **defect** — reproduced on first/only attempt this run; see Known Defects |
| Step 5: `~Robot-Joker Tell me a joke` → robot joke, UPPER CASE | Response is a robot joke, fully UPPER CASE | Test Step 6 | Response text asserted all-caps and robot-themed; "Thinking" trace shows `Skill: robot-joker-elitea-1736` tag | covered |
| Test Data: skill name literal `"Robot-Joker"` (mixed case) | literal name `Robot-Joker` | N/A — **case-text drift**, not a defect | Live Skill Name field client-side rejects non-kebab-case names ("Name must be lowercase letters, digits and hyphens only…"); substituted `robot-joker-elitea-1736` | clarification (reverse-masking; product's kebab-case constraint is correct/by-design, case text predates or ignores it — same finding independently confirmed in ELITEA-1737) |
| Test Data: invocation syntax `~Robot-Joker` (literal case-name form) | literal `~Robot-Joker` string | N/A — **case-text drift**, not a defect | Live syntax is `~<mention>` via an autocomplete keyed on the skill's actual saved name (which, per the row above, cannot literally be `Robot-Joker`); substituted `~robot-joker-elitea-1736` | clarification (reverse-masking; same finding as ELITEA-1735) |

### Axis 2 — Observables asserted beyond the case
| Observable | Reason |
|---|---|
| Skill-attach network call (`PATCH .../skill/prompt_lib/{project}/{id}` → `201`) | Confirms attachment is an immediate API-level auto-save, not deferred to agent-level Save (same finding as ELITEA-1735, re-confirmed here in the chat-participant flow) |
| "Agents in this conversation" participant badge count | Case says "Agent appears as a participant" but doesn't specify a stable UI signal — this badge is the most stable, semantic handle observed for asserting participant membership |
| "Thinking" trace `Skill: <skill-name>` tag | Not asserted directly (internal reasoning trace, not a stable contract per ELITEA-1735's own guidance) but recorded as a debug/diagnostic signal useful for confirming *why* a given turn did or didn't apply skill formatting |
| Console messages checked after every step | Zero errors observed across all 6 steps in this run |
| Cleanup performed live (chat, agent, skill all deleted) | Confirms the full delete lifecycle for a chat-participant-scoped skill/agent pairing works cleanly with no orphaned state or console errors |

## Known Defects

### github.com/EliteaAI/elitea-testing-public/issues/38 — [MAJOR] Agent applies skill formatting to plain (non-invoked) messages intermittently — RE-CONFIRMED in a second context (chat participant, not agent-level)
- **Context difference from the original report**: issue #38 was originally
  observed testing ELITEA-1735 (skill interaction *at the agent level*,
  i.e. talking to the agent directly via its own embedded chat panel on the
  agent detail page). This case (ELITEA-1736) tests the same underlying
  skill-invocation contract but via a **chat conversation where the agent
  is added as a participant** — a materially different code path (chat
  session/participant plumbing vs. direct agent chat). The defect
  reproduced here too, confirming it is not scoped to the agent-detail-page
  chat surface alone.
- **Repro rate this run**: 1/1 attempts (single attempt made; per the
  case's step ordering, step 4/plain-message was only exercised once before
  moving to step 5/skill-invoked. Given ELITEA-1735's 1/3 rate, treat this
  as consistent with the same non-deterministic root cause, not a 100%
  regression — a wider repro-rate sample would need multiple fresh
  conversations, out of scope for a single case-analysis pass).
- **Evidence**: plain message "Tell me a joke" (no `~mention`, agent
  "Joker-elitea-1736" as chat participant) returned:
  `"WHY DID THE ROBOT GO ON A DIET? BECAUSE IT HAD TOO MANY BYTES!"` — a
  ROBOT joke, fully UPPER CASE, despite zero invocation syntax in the
  message. The expandable "Thought for 2 secs" trace explicitly showed a
  `"Skill: robot-joker-elitea-1736"` tag for this turn, confirming the
  skill was autonomously loaded.
  Screenshot: `test-results/screenshots/ELITEA-1736-step4-skillbleed.png`
  (also saved as `.playwright-mcp/ELITEA-1736-step4-skillbleed.png` in this
  run's evidence folder).
- **Root-cause hint**: identical to ELITEA-1735's finding — the model
  scans `<available_skills>` and autonomously decides whether to
  `load_skill` based on perceived relevance to the message, not gated
  purely on `~mention` syntax. The fact that it reproduces in both the
  agent-level chat surface AND the chat-participant surface suggests the
  root cause lives in the shared LLM-prompt/skill-injection layer common
  to both surfaces, not in either surface's own UI/session code.
- **Automation guidance**: per `.agents/profile.md` § Bug filing (isolated
  defect → `expect.soft()` with ticket linked), assert step 5 (plain
  message) with a soft assertion referencing issue #38, and hard-assert
  the rest of the flow (skill creation, agent creation + attach, adding
  the agent as a chat participant, explicit `~mention` invocation) which
  reproduced 100% reliably in this run.
- **No new ticket filed** — per dispatch instructions, this is treated as
  a second confirmed repro of the existing #38 defect (different context:
  chat-participant vs. agent-level), not a new/duplicate bug. Reference
  #38 in the automated test's soft-assertion comment.

## Cleanup

One skill, one agent, and one chat conversation are created per run. All
three were deleted live in this run to confirm the mechanics below.

1. **Delete the chat conversation first**: hover the conversation's sidebar
   list item to reveal `conversation-menu-menu-button`, click it, select
   "Delete" menuitem, confirm via the "Are you sure to delete the {name}
   chat? It can't be restored." dialog's "Delete" button (**no
   type-to-confirm** for chat deletion, unlike agent/skill deletion).
   Verified: conversation removed from sidebar list, no console errors.
2. **Delete the Agent**: navigate to the agent detail page (via Agents list
   search or direct card click — **note**: navigating by a stale/bare
   `/agents/all/{id}?destTab=configuration` URL without the `name` query
   param returned a client-side "Page not found" in this run; always
   navigate via the Agents list UI or preserve the full URL with `name=`
   captured at creation time). Open `agent-actions-menu-button` → AGENT
   group → `delete-agent-menuitem` → type-to-confirm dialog
   (`delete-confirm-name-input` inner `#name` field, must match exactly) →
   click "Delete". Verified: redirects to `/agents/all`, no console errors.
3. **Delete the Skill**: navigate to the skill detail page, open
   `skill-controls-menu-button` → SKILL group → `skill-delete-menu-item` →
   same type-to-confirm dialog pattern → click "Delete". Verified:
   redirects to `/skills/all`, no console errors.
4. **Recommended teardown fixture shape**: mirrors ELITEA-1735's — a
   function-scoped fixture that creates the skill + agent + starts the
   chat conversation via UI in the test body, yields their IDs, and in its
   `finally`/post-yield block deletes the conversation first (own API/UI
   call), then the agent (`agent_api.delete_agent(agent_id)`), then the
   skill (`skill_api.delete_skill(skill_id)`), each in its own
   `try/except` so one failed delete doesn't skip the others.

## Blocked Steps
None — case executed end-to-end; the one blocker encountered (the known
defect above) does not prevent the remaining steps from completing.
