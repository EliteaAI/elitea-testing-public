# Test Case: Ghost skill not shown after Agent participant removed (Chat `~` mention)

## Rework Note (issue #35 — framework-alignment audit)

This AFS is **amended in place** (Phase-2 "amend-in-PR" convention) to close a
compliance gap flagged by the framework-alignment audit against the merged
PR #52 (implementer's original delivery for this case): PR #52 added 9 new
methods to `automation/pages/chat_page.py`, all locating elements via raw
`get_by_role`/`aria-label`/text+`xpath` handles instead of `data-testid`, in
violation of `.agents/testing.md` § Locator policy (testid-only, no ladder —
see `.agents/role-overrides.md`). This rework re-verifies the flow, confirms
2 reuse cases against testids already added by prior case reworks, and specs
5 NEW testids for the participant-removal flow (previously unexplored by any
prior testid rework). **No test/page-object code is written here** — this is
the analyst slot's rework of the spec-of-record; the implementer applies the
`add-data-testid` dual-target flow and rewires `chat_page.py` per the
Handles Reference below.

**Provenance verified fresh** (`cd ../EliteaUI && git fetch origin` run
immediately before every check below, 2026-07-15).

## Implementer Amendment (Phase 2 — issue #35 rework, 2026-07-15)

Two decisions made while wiring the Handles Reference below, recorded here
per the amend-in-PR convention:

1. **`remove_agent_participant()` signature changed from `agent_name: str`
   to `agent_id: int`.** The dynamic `chat-participant-row-{uniqueId}`
   testid this method now resolves against requires `uniqueId =
   getChatParticipantUniqueId(participant)`, which for an agent participant
   is `application_{agent_id}_{project_id}` — computable from the agent's
   numeric ID (already captured by the test as `agent_id`), not from its
   display name. This removes the last text/xpath-ancestor walk from the
   method entirely. The test's call site was updated to pass `agent_id`
   instead of `AGENT_NAME`.
2. **A 6th testid was added beyond the AFS's original 5**:
   `chat-participants-badge-button` on `CollapsedPerticapantsList.jsx`'s
   `IconButton` (line ~223, inside the `chat-participants-badge-{section}`
   Box the AFS specced). The AFS named a testid for the wrapping Box only,
   but the actual click target (the IconButton) has no accessible name —
   `get_by_role`/CSS-tag lookup would have been needed to click it, which
   the locator policy also forbids. Declared improvisation per
   `.agents/role-overrides.md`'s canon-gap protocol: the button is touched
   by this same test, so adding its testid is in-scope, not scope creep.
   Cherry-picked into the same EliteaUI draft PR (EliteaAI/EliteaUI#548,
   commit `be48cd5`).

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

## Handles Reference (testid-only — amended for the PR #52 audit rework)

Locator policy: testid-only (`.agents/role-overrides.md` +
`.agents/testing.md` § Locator policy). The `test-automation-workflow`
skill's example ladder does not apply. Every row below is testid-first;
where the case's steps 1–3 (skill/agent create, attach-skill popper) reuse
handles from an EARLIER, already-reviewed case (ELITEA-1735/1736/1737) that
predate PR #52 and are **out of scope for this rework** (PR #52 only touched
`chat_page.py`'s participant-removal + mention-popper methods), they are
kept unchanged and marked accordingly — not retrofitted here to avoid scope
creep beyond this ticket.

PROVENANCE legend: `on-main ✓` / `on-automation/testids only (draft #N)` /
`needs-adding`. Verified fresh (`cd ../EliteaUI && git fetch origin` run
immediately before each `git grep <ref>` below, 2026-07-15).

| Element | testid / locator | Provenance | Notes |
|---|---|---|---|
| Skill Name field | `getByRole('textbox', { name: 'Name *' })` | — (out of scope, pre-existing, `skill_form_page.py`) | From ELITEA-1735/1736/1737; not touched by PR #52 |
| Skill Description field | `getByRole('textbox', { name: 'Description *' })` | — (out of scope, pre-existing) | Same as above |
| Skill Instructions editor | `skill-instructions-editor-content` | on-automation/testids only (draft EliteaAI/EliteaUI#525) | `CreateSkillForm.jsx:303` `contentTestId=`; CodeMirror, use `press_sequentially` |
| Skill Save button | `skill-save-button` | on-main ✓ | |
| Agent Name field | `agent-name-input` | on-main ✓ | `CreateAgentForm.jsx:133` |
| Agent Description field | `agent-description-input` | on-main ✓ | `CreateAgentForm.jsx:166` |
| Agent Instructions field | `agent-instructions-input` | on-main ✓ | `InstructionsInput.jsx:347` |
| Agent Save button | `agent-save-button` | on-main ✓ | `CreateApplicationTabBar.jsx:70` / `SaveApplicationButton.jsx:72` |
| Agent add-skill button (Skills accordion) | `getByRole('button', { name: 'Skill', exact: true })` | — (out of scope, pre-existing) | Same handle as ELITEA-1735/1736; not touched by PR #52 |
| Skill-attach popper item | `role="menuitem"`, accessible name = skill name | — (out of scope, pre-existing) | Same as above |
| Chat composer "+" button | `plus-menu-button` | on-main ✓ | |
| "Agents" menuitem in plus-menu | `role="menuitem"`, accessible name `"Agents"` | — (out of scope, pre-existing) | Not touched by PR #52 |
| Agent-select popper item (chat participant add) | `role="menuitem"`, accessible name = agent's display name | — (out of scope, pre-existing) | Not touched by PR #52 |
| Chat message input | `chat-message-input` | on-main ✓ | `ComponentsLib/Chat/UserInput.jsx:360`; mention-aware, use `press_sequentially`, never `fill()` — always re-snapshot after composer re-render |
| Chat send button | `chat-send-button` | on-main ✓ | not used in this case (never sent a message) |
| **"Switch Agent" composer button** — **REUSE, do not re-add** | `switch_participant_button` field → `chat-switch-participant-button` | on-automation/testids only (draft EliteaAI/EliteaUI#541) | `AgentEditorPanel.jsx:219`. Added for ELITEA-1736; PR #52 wrongly re-implemented `is_switch_agent_button_visible()` via raw `get_by_role('button', {name:'Switch Agent'})` instead of reusing the existing `LocatorDescriptor` field. **Fix: rewire the method to use `self.switch_participant_button` (already present at `chat_page.py:209`).** |
| **"Mention skill" popper container** — **REUSE, do not re-add** | `mention_skill_list` field → `skill-mention-list` | on-automation/testids only (draft EliteaAI/EliteaUI#540) | `MentionSkillList.jsx:56`. Added for ELITEA-1735, confirmed already live for the chat surface during ELITEA-1736. PR #52's `open_mention_skill_popper()`/`is_skill_in_mention_popper()` wrongly located it via `get_by_text("Mention skill")` + `xpath=ancestor::div[2]` instead of reusing this field. **Fix: rewire both methods to use `self.mention_skill_list`.** |
| **Mention-popper skill row** — **REUSE, do not re-add** | `MENTION_SKILL_ITEM` class constant → `[data-testid="skill-mention-item-{}"]` | on-automation/testids only (draft EliteaAI/EliteaUI#540) | `MentionSkillList.jsx:81` `testId={`skill-mention-item-${item.name}`}`. `is_skill_in_mention_popper()` wrongly used `popper.get_by_text(skill_name, exact=True)`. **Fix: `self.mention_skill_list.locator(self.MENTION_SKILL_ITEM.format(skill_name))`** (same pattern already used by `send_message_with_skill_mention`, `chat_page.py:2186-2187`). |
| **Mention-popper empty state — NEW testid needed** | proposed `skill-mention-list-empty` | needs-adding | `MentionSkillList.jsx:67` (the `<Box sx={styles.empty}>` wrapping the `"No skills attached to this agent"` `Typography`, `EMPTY_LABEL` const at line 11). Container already has `skill-mention-list`, but `is_mention_popper_empty_state()` currently asserts via a bare `popper.get_by_text("No skills attached to this agent", exact=False)` — scoped inside a testid container, but still an added `get_by_text(` line that fails the reviewer's mechanical grep verbatim. **Fix: add `data-testid="skill-mention-list-empty"` to the `Box` at line 67; rewire the method to `self.mention_skill_list.get_by_test_id("skill-mention-list-empty")`.** |
| **"Agents in this conversation" participant badge — NEW testid needed** | proposed `chat-participants-badge-{section}` (dynamic; this case only ever exercises `section="agents"` → `chat-participants-badge-agents`) | needs-adding | `CollapsedPerticapantsList.jsx:218` — the `<Box sx={styles.root}>` wrapping the section's `IconButton` (participant-count badge rendered via a CSS `::after`, per `.agents/memory/qa-engineer/…` — no DOM text node) — inside the `ENTITY_SECTIONS.map(entity => …)` loop (`entity.section` gives `'agents'`/`'pipelines'`/`'toolkits'`/`'mcp'`). PR #52's `is_participants_badge_visible()`/`open_participants_popover()` locate it via `[aria-label="Agents in this conversation"]`, resolving against the `StyledTooltip`'s auto-derived `aria-label` from its `title` prop (`${entity.label} in this conversation`, line 207) — brittle and Tooltip-internal. **Fix: template the testid per section (canonical dynamic-testid pattern, `.agents/testing.md` § Locator policy), add it to the `Box` at line 218, and only ever call it with `.format("agents")` in this test — do NOT hardcode a testid per other section, that's out of this test's scope.** |
| **"Agents" participants popper — NEW testid needed** | proposed `chat-participants-popper` | needs-adding | `CollapsedParticipantsDropdown.jsx:136` — the `<Paper sx={[styles.paper, sx]}>` (the actual Popper/Grow content container; heading `Typography` at line 144 renders `entityType` prop, `"Agents"` for this flow). PR #52 located it via `page.locator("p").filter(has_text=re.compile(r"^Agents$"))` + `xpath=ancestor::div[3]` (with an explicit code comment acknowledging the fragility). **Fix: add `data-testid="chat-participants-popper"` to the `Paper` at line 136; rewire `open_participants_popover()` to `self.page.get_by_test_id("chat-participants-popper")`.** NOTE: this component renders once per open entity-type section — since only one section (`openSectionType`) is ever open at a time in this test's single-agent-participant flow, a static testid is unambiguous here; flag to the implementer if a future multi-entity-type case needs disambiguation. |
| **Participant row — NEW testid needed** | proposed `chat-participant-row-{uniqueId}` (dynamic; `uniqueId` = `getChatParticipantUniqueId(participant)`, e.g. `application_4687_399`) | needs-adding | `ParticipantItem.jsx:250` — the hoverable `<Box onClick={onClickHandler} onMouseEnter={onMouseEnter} onMouseLeave={onMouseLeave} sx={styles.contentWrapper}>` (the row `contentWrapper`, shared by every participant type via this one component). PR #52's `remove_agent_participant()` locates the row via `popper.get_by_text(agent_name, exact=True).first.locator("xpath=ancestor::div[2]")` — fragile ancestor-walk off free text. **Fix: add `data-testid={`chat-participant-row-${getChatParticipantUniqueId(participant)}`}` to this `Box` (helper already imported one level up in `CollapsedParticipantsDropdown.jsx`; import `getChatParticipantUniqueId` from `@/[fsd]/features/chat/participants/lib/helpers` into `ParticipantItem.jsx` too); rewire the page-object method to hover `self.page.locator(self.PARTICIPANT_ROW.format(unique_id))` (new UPPER_CASE class constant, same templated pattern as `MENTION_SKILL_ITEM`). |
| **"Remove agent" hover-reveal icon button — NEW testid needed** | proposed `chat-participant-remove-button` (static; scope via the row's dynamic testid, no need for the button itself to be dynamic — multiple simultaneous rows disambiguate through the parent row testid) | needs-adding | `DeleteParticipantButton.jsx:75` — the `<IconButton disabled={disabled} onClick={onClickDelete} variant="elitea" color="tertiary" id="DeleteButton" sx={sx}>` (shared `ParticipantActions`/`DeleteParticipantButton` component, used by every participant type; label text is `Remove ${entityType}` — `"Remove agent"` for this case). PR #52 locates it via `row.get_by_role("button", name="Remove agent")` (hover-reveal already correctly handled with `row.hover()` + a 300ms CSS-transition wait — keep that mechanic, only the locator changes). **Fix: add `data-testid="chat-participant-remove-button"` to the `IconButton`; rewire to `row.get_by_test_id("chat-participant-remove-button")` where `row` is now resolved via the new `chat-participant-row-{uniqueId}` testid instead of the old ancestor-walk.** |
| "Edit agent" icon button — **NOT touched by this test, no testid added** | — | out-of-scope (flagged for future work) | `EditParticipantButton.jsx` (same `ParticipantActions` row). The case's step 7 hovers the row (which reveals both buttons) but only ever clicks "Remove agent" — per `.agents/role-overrides.md`'s scope rule ("exactly the elements the case's test touches"), do NOT add a testid to the Edit button in this rework; whichever case first exercises agent-in-chat editing should add `chat-participant-edit-button` then. |
| "Remove agent?" confirmation dialog | `Dialog.wait_for(page)` / `Dialog.click_button(dialog, "Remove")` (`automation/components/mui.py`) — `[role="dialog"]` + `button:has-text(...)`, **NOT testid-based** | — (pre-existing shared framework component, out of scope) | Checked per dispatch instructions: the shared `Dialog` helper is generic role/text-based infra reused across ~15+ existing flows, predates this rework, and is not new code PR #52 introduced — retrofitting it to testid is a framework-wide change outside this ticket's scope, not something to fix ad hoc here. Body text `"Are you sure to remove the {agent name} agent from chat?"`, buttons `"Cancel"`/`"Remove"`. No type-to-confirm (unlike agent/skill entity delete). |
| Agent overflow menu (agent detail page) | `agent-actions-menu-button` | on-main ✓ (dynamically constructed: `DotMenu.jsx:346` `` data-testid={id ? `${id}-menu-button` : undefined} `` with `id="agent-actions"` from `ApplicationControls.jsx:219` — not a literal string in source, confirmed by tracing the prop, not a plain grep) | AGENT group → `delete-agent-menuitem` (same dynamic pattern: `DotMenu.jsx:57` `` `${testId}-menuitem` `` with `testId={item.key}`, `key: 'delete-agent'` from `DeleteApplicationButton.jsx:63`) |
| Skill overflow menu (skill detail page) | `skill-controls-menu-button` | on-main ✓ | `SkillControls.jsx:233` (explicit `anchorButtonProps`) |
| Delete-confirmation name field | `delete-confirm-name-input` (scope to inner `#name` field) | on-automation/testids only (draft EliteaAI/EliteaUI#525) | `DeleteEntityModal.jsx:81`; shared component across agent/skill delete flows; type-to-confirm required |

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
