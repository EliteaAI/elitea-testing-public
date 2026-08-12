# Test Case: Agent with Skills Publishing Flow — skills embedded in the published snapshot, never listed independently, thought process shows invocation

## Metadata
- **TMS ID**: ELITEA-2600
- **Linked Story**: none
- **Priority**: l2 (high, per case frontmatter)
- **Environment Explored**: local (`http://localhost:5173`, EliteaUI `automation/testids`
  branch → DEV backend, project `Private` / `${ELITEA_PROJECT_ID}`=399), model:
  Anthropic Claude 4.5 Sonnet
- **User set**: `${TEST_USER}` (on localhost, `auth_state` fixture skips login via
  `VITE_DEV_TOKEN`)
- **Analyst**: qa-engineer (Sage), analyst slot
- **Status**: `ready-for-automation` — case executed end-to-end live against the real
  system: 3 skills created, attached to a fresh agent, agent published via the
  publish wizard, Skills Catalog searched (confirmed skills NOT independently
  listed), published agent opened from the Agents Catalog, chat started, and TWO
  separate skills invoked via explicit `~mention` — both invocations confirmed
  visible in the "Thought for N secs" accordion via the pre-existing
  `chat-answer-tool-chip` testid (text `"Skill: {skill_name}"`). No blockers, no
  product defects. One case-text-adjacent discovery (not a defect — see Automation
  Hints): the agent-publish AI validation gate ALSO inspects each *attached skill's
  own* instructions length (≥100 chars), not just the agent's own fields — a skill
  with short instructions blocks the AGENT's publish with a Critical issue naming
  that skill, so all attached skills need ≥100-char instructions for the happy path
  to reach `0 Critical`.

## Preconditions
- User is logged in (on localhost, `auth_state` fixture skips login).
- A project is selected/accessible (`Private`, id `399` in this run).
- The Skills and Agents sections are available in the project.
- User has `applications.publish` permission — confirmed live (same as ELITEA-1892):
  the "Publish" menu item rendered enabled in the agent's VERSION actions menu.

## Test Data

### generate-per-test (in test setup, cleaned up in its own teardown)
- Skill 1 name: kebab-case, e.g. `format-uppercase-2600` — **must be lowercase
  letters/digits/hyphens only** (client-side Skill-name validation, confirmed
  again live in this run — see `.agents/memory/qa-engineer/skill_form_and_export_import_quirks.md`).
  Description: any non-empty string (e.g. "Convert all text to UPPERCASE format").
  Instructions: **must be ≥100 characters** to clear the AGENT's own publish
  validation gate (see Status note above) — a short instructions string like
  "Convert all text ... to the uppercase text." (109 chars in this run) passed;
  a shorter 84-char string on a different skill in this same run did NOT (see
  Test Steps step 6).
- Skill 2 name: e.g. `word-counter-2600`. Description: any non-empty string.
  Instructions ≥100 chars (same constraint as Skill 1).
- Skill 3 name: e.g. `summarizer-2600`. Description: any non-empty string.
  Instructions ≥100 chars (same constraint — **this is the skill that failed
  validation in this run at 84 chars and had to be lengthened to 179 chars**;
  automation should seed all three skills at ≥100 chars from the start to avoid
  the extra edit-and-retry round-trip this run needed).
- Agent name: e.g. `multi-skill-agent-2600`. Description: any non-empty string.
  Instructions: substantive text describing the agent's purpose (same
  "no vague capability statement" gate documented in ELITEA-1892's AFS — a
  Warning, not Critical, but worth a real sentence).
- At least 1 Tag on the agent (e.g. `automation`, an existing suggested tag) —
  **Critical** gate per ELITEA-1892 (`tags: No tags defined` blocks Publish).
- Publish wizard Version name: e.g. `v1-elitea-2600` (regex
  `/^[a-zA-Z0-9._-]*$/`). Category: any option (this run used
  `Quality Assurance`) — required to enable "Continue", assertions don't depend
  on which value.
- Chat prompts for the two skill-invocation steps: any short text preceded by
  the skill's explicit `~<skill-name>` mention — this run used
  `~word-counter-2600 one two three four five six seven eight nine ten` (10
  words) and `~format-uppercase-2600 elitea test message`.

## Test Steps

1. Navigate to `/skills/create`, fill Name/Description/Instructions (≥100 chars)
   for Skill 1, click Save.
   - **Verify**: redirected to `/skills/all/{id}`, skill created.
2. Repeat step 1 for Skill 2.
   - **Verify**: skill 2 created.
3. Repeat step 1 for Skill 3.
   - **Verify**: skill 3 created.
4. Navigate to `/agents/create`, fill Name/Description/Instructions, add 1 Tag,
   Save. Then on the agent detail page, expand the Skills section and attach all
   3 skills via the "+ Skill" popper (one at a time — the popper closes after
   each selection and the `N/5 skills added.` counter must be polled until it
   changes before reopening for the next attach, per the existing
   `AgentDetailPage.attach_skill()` pattern).
   - **Verify**: agent created; Skills section counter reads `3/5 skills added.`
     and lists all 3 skill names with `base` version.
5. Open the agent's overflow (⋮) menu → VERSION group → "Publish".
   - **Verify**: `role="dialog"` opens, 3-step wizard (Preparation / Validation /
     Publishing), same `PublishWizardModal.jsx` component ELITEA-1892 documents.
     The Publishing Terms panel's "1 - Exclusions Notice" section contains a
     literal sentence confirming the case's core premise (captured verbatim this
     run): **"Exception: attached Skills and sub-agents are not stripped — their
     instructions are embedded in the published agent. Retained Skills are never
     listed as separate entries in the catalog."**
6. Fill Version name, select a Category, check the Publishing Terms checkbox,
   click "Continue".
   - **Verify — PASSES, with a discovery beyond the case text.** Validation
     (`POST publish_validate/prompt_lib/{project}/{versionId}`) inspects BOTH the
     agent's own fields AND each attached skill's content. In this run's first
     attempt (Skill 3's instructions at 84 chars), the response showed
     `Critical Issues (1)`: `"skills [skill: summarizer-2600]: Skill content is
     too short (min 100 chars)"` with `Fix: Expand the skill instructions
     (currently 84 chars)` — Publish button stayed disabled. After editing
     Skill 3's instructions to 179 chars and re-opening the wizard, the SAME
     validation returned `Critical: 0`, `Warnings: 5` (description lacks action
     verbs / no custom icon / vague instructions / no welcome message / no
     conversation starters — all non-blocking), `Suggestions: 2` — Publish
     button (`agent-publish-confirm-button`) became enabled.
7. Click "Publish".
   - **Verify — PASSES.** `POST publish/prompt_lib/{project}/{versionId}` returns
     200; app navigates to a new version id (`/agents/all/{agentId}/{newVersionId}`);
     `VERSION:` combobox shows the typed version name, selected.
8. Navigate to `/elitea-catalog?tab=agents`, search for the agent's name.
   - **Verify**: the published agent's card is present, grouped under the
     selected Category heading (confirmed live: card rendered under "Quality
     Assurance").
9. Navigate to `/elitea-catalog?tab=skills`, search for each of the 3 skill
   names individually (or a shared substring, e.g. the run's `2600` suffix).
   - **Verify — PASSES, confirms the case's core assertion.** Search returned
     **"No skills found"** for all 3 skill names — the attached skills are NOT
     independently listed as searchable Catalog entities, even though the agent
     that embeds them IS published and visible.
10. Click the agent's Catalog card → the agent-detail modal opens → click
    "Start Chat".
    - **Verify**: navigates to `/chat`, a new conversation opens with the
      published agent as the sole participant, version selector shows the
      published version name (confirmed live: `v1-elitea-2600`).
11. Type `~<skill-2-name>` in the chat input, select it from the "Mention skill"
    popper (do NOT use `fill()` for the trailing prompt text — it replaces the
    whole textbox value and destroys the inserted mention chip; use
    `press_sequentially` throughout, exactly as
    `ChatPage.send_message_with_skill_mention()` already does), append a short
    prompt (10 distinct words, for the word-counter skill), send.
    - **Verify**: message sends as `~word-counter-2600 <prompt>`; AI response
      arrives; the "Thought for N secs" accordion is present and already
      expanded by default (no separate expand click needed — confirmed live,
      matching `agent_detail_page.py`'s existing `get_outer_thought_accordion()`
      behavior for tool/model chips).
12. Inspect the thought-accordion's chip row.
    - **Verify — confirms the case's core "visible in thought process"
      assertion.** A chip with `data-testid="chat-answer-tool-chip"` (the
      SAME pre-existing testid already used for external-toolkit tool calls,
      `ChatPage.answer_tool_chip`) renders with text **`"Skill: word-counter-2600"`**
      — i.e. skill invocations reuse the generic tool-chip mechanism with
      `toolkitName` hardcoded to the literal string `"Skill"` and `toolName` =
      the skill's name, NOT the `"{toolkit_name}: {tool_name}"` shape the page
      object's docstring describes for a true external toolkit (that shape still
      applies to toolkit chips; skills are a distinct, simpler `"Skill: {name}"`
      text). The accordion also carries the standard `chat-answer-model-chip`
      ("Anthropic Claude 4.5 Sonnet"). The final answer text was `"Word count: 10"`
      — correct per Skill 2's instructions.
13. Repeat step 11–12 with `~<skill-1-name>` (uppercase skill) and a fresh short
    prompt, in the SAME conversation.
    - **Verify — PASSES.** A second `chat-answer-tool-chip` renders with text
      `"Skill: format-uppercase-2600"`; final answer text was the prompt fully
      upper-cased (`"ELITEA TEST MESSAGE"` for the prompt `"elitea test
      message"`) — confirms the skill's own instructions were actually applied,
      not just that a chip rendered.

## Expected Results
- The agent publishes successfully with all 3 attached skills (0 Critical
  validation issues once every attached skill independently clears the ≥100-char
  content gate).
- The 3 attached skills are NOT independently searchable/listed in the Skills
  Catalog after the agent publishes (`/elitea-catalog?tab=skills` search returns
  "No skills found" for each skill's name).
- The published agent is listed and openable from the Agents Catalog, grouped
  under its selected Category.
- Chatting with the published agent and explicitly mentioning an attached skill
  (`~<skill-name>`) correctly invokes that skill's instructions (response content
  reflects the skill's behavior).
- Each skill invocation renders a `chat-answer-tool-chip` (text
  `"Skill: {skill_name}"`) inside the "Thought for N secs" accordion — observable
  and asserted, satisfying the case's "visible in thought process" requirement.

## Coverage Map

### Axis 1 — Case coverage

| Case element | Expected result | Covered by (AFS step) | Asserted where | Disposition |
|---|---|---|---|---|
| 1 Create Skill 1 (`format-uppercase`) | Skill 1 created and saved | step 1 | `step 1`: redirect to `/skills/all/{id}` | asserted |
| 2 Create Skill 2 (`word-counter`) | Skill 2 created and saved | step 2 | `step 2`: redirect to `/skills/all/{id}` | asserted |
| 3 Create Skill 3 (`summarizer`) | Skill 3 created and saved | step 3 | `step 3`: redirect to `/skills/all/{id}` | asserted |
| 4 Create Agent, attach all 3 skills | Agent created with 3 skills listed as attached | step 4 | `step 4`: Skills counter reads `3/5 skills added.` | asserted |
| 5 Open Agent publish wizard | Publish wizard opens | step 5 | `step 5`: `role="dialog"` visible, Preparation step shown | asserted |
| 6 Complete the publishing process | Agent is published successfully | steps 6–7 | `step 7`: 200 response, new version id, VERSION combobox shows published name | asserted *(decomposed: Preparation+Validation in step 6, Publish confirm in step 7)* |
| 7 Navigate to Agent Hub/Catalog | Published agent appears in the catalog | step 8 | `step 8`: agent card present under its Category heading | asserted |
| 8 Search for the individual skills in the Skills Catalog | Skills NOT listed as independent entities (embedded in agent snapshot) | step 9 | `step 9`: "No skills found" for all 3 skill names | asserted |
| 9 Open the published agent from the Catalog | Agent details page loads | step 10 | `step 10`: agent-detail modal opens with Start Chat | asserted |
| 10 Start a conversation with the published agent | Chat interface opens | step 10 | `step 10`: navigates to `/chat`, new conversation with agent participant | asserted |
| 11 Send a message that triggers one of the attached skills | Agent responds using the skill | step 11 | `step 11`: response text is `"Word count: 10"` | asserted |
| 12 Expand the thought process/reasoning panel | Thought process is visible | step 11 | `step 11`: accordion already expanded by default — no separate expand action needed (case-text drift, see Axis 2) | asserted, with drift noted |
| 13 Verify that the invoked skill is shown in the thought process | Skill invocation is logged/visible in thought process | step 12 | `step 12`: `chat-answer-tool-chip` text `"Skill: word-counter-2600"` | asserted |
| 14 Test another skill invocation | Second skill also works and appears in thought process | step 13 | `step 13`: `chat-answer-tool-chip` text `"Skill: format-uppercase-2600"`, response fully upper-cased | asserted |

### Axis 2 — Analyst additions

- `step 6` asserts the AGENT-level publish validation ALSO fails when an
  attached SKILL's own instructions are too short (a Critical issue naming the
  skill by name) — *added: discovered live when Skill 3's 84-char instructions
  blocked the whole agent's publish; this is load-bearing test-data guidance for
  automation, not just an observation, so it is asserted as its own checkpoint
  rather than only mentioned in Test Data.*
- `step 5` asserts the exact Publishing Terms disclosure text confirming skills
  are embedded, not independently catalog-listed — *added: this is the
  platform's own documented guarantee for the case's core premise, worth a
  content assertion beyond just the functional Catalog-search proof in step 9,
  so a text regression in the disclosure itself would also be caught.*
- `step 13` asserts the SECOND skill's answer content is correctly transformed
  (not just that a chip renders) — *added: a chip alone doesn't prove the
  skill's instructions were actually applied; asserting on the uppercase output
  closes that gap.*

## Cleanup
1. Delete the 3 skills via `SkillAPI.delete_skill(skill_id)` (cookie-auth) in a
   `try/finally`.
2. Delete the agent via `AgentAPI.delete_agent(agent_id)` (cookie-auth) in the
   same `try/finally` — deleting the agent does not delete the published Catalog
   entry's underlying data retroactively in a way this case needs to reverse
   further; no separate "unpublish" step is required for teardown (unlike
   ELITEA-2599's lifecycle case, this case doesn't assert post-unpublish state).
3. This run's scratch entities (left on the DEV backend, not cleaned up by the
   analyst — see `.agents/testing.md` § Test data strategy, analysis-time data is
   the automated test's own teardown responsibility): skills `1605`
   (`format-uppercase-2600`), `1606` (`word-counter-2600`), `1607`
   (`summarizer-2600`, instructions later lengthened to 179 chars); agent `9131`
   (`multi-skill-agent-2600`), published version id `9403`, public catalog agent
   id `315`.

## Concrete Handles (discovered during exploration)

Locator policy: testid-only (`.agents/testing.md` § Locator policy,
`.agents/role-overrides.md`). All rows below are pre-existing testids —
**no `add-data-testid` work needed for this case.**

| Element | Testid | Provenance | Notes |
|---|---|---|---|
| Skill Name input | `skill-name-input-field` | on-`automation/testids` (pre-existing, used by prior skill AFS) | `SkillFormPage` |
| Skill Description input | `skill-description-input-field` | on-`automation/testids` (pre-existing) | |
| Skill Instructions editor | `skill-instructions-editor-content` | on-`automation/testids` (pre-existing) | CodeMirror content node |
| Skill Save button | `skill-save-button` | on-`automation/testids` (pre-existing) | |
| Agent Name input | `agent-name-input` | on-`automation/testids` (pre-existing) | `AgentFormPage` |
| Agent Description input | `agent-description-input` | on-`automation/testids` (pre-existing) | |
| Agent Instructions input | `agent-instructions-input` | on-`automation/testids` (pre-existing) | |
| Agent Save button | `agent-save-button` | on-`automation/testids` (pre-existing) | |
| Agent Tags combobox | role-based `combobox "Tags"` — **no dedicated testid found**; not requested (out of this case's core assertions, matches existing `AgentFormPage` scope) | n/a | Options are plain MUI `option` role items |
| Skills section container | `agent-skills-section` | on-`automation/testids` (pre-existing, ELITEA-1735 rework) | `AgentDetailPage.skills_section` |
| "+ Skill" button | `agent-add-skill-button` | on-`automation/testids` (pre-existing, ELITEA-1735 rework) | |
| Skill-attach popper item | `[data-testid="toolkit-menu-item"]` (scoped inside the popper, filtered by name) | on-`automation/testids` (pre-existing, shared with Toolkit attach) | `Popper.select_menuitem_by_testid()` |
| Agent actions overflow menu | `agent-actions-menu-button` | on-`automation/testids` (pre-existing) | |
| Publish menu item | `publish-version-menuitem` | on-`automation/testids` (pre-existing, runtime-constructed `${item.key}-menuitem`) | Not a literal JSX string — see ELITEA-1892's AFS note |
| Publish wizard version-name input | `agent-publish-version-name-input` | on-`automation/testids` (pre-existing) | |
| Publish wizard category select | `agent-publish-category-select-combobox` | on-`automation/testids` (pre-existing) | dynamic option: `select-option-{Category Name}` |
| Publish wizard agree checkbox | role-based `checkbox "I agree with the Publishing Terms."` — carries testid `agent-publish-agree-checkbox` per source (role locator suffices; MCP's generated code doesn't surface the testid, per ELITEA-2595's digest note) | on-`automation/testids` (pre-existing) | |
| Publish wizard Continue button | `agent-publish-continue-button` | on-`automation/testids` (pre-existing) | |
| Publish wizard Publish/confirm button | `agent-publish-confirm-button` | on-`automation/testids` (pre-existing) | |
| Catalog search input | `catalog-search-input` | on-`automation/testids` (pre-existing) | shared Agents/Skills tabs |
| Catalog Agents tab | `catalog-agents-tab` | on-`automation/testids` (pre-existing) | |
| Catalog Skills tab | `catalog-skills-tab` | on-`automation/testids` (pre-existing) | |
| Catalog agent card (dynamic) | `[data-testid="catalog-agent-card-{public_id}"]` (prefix-match idiom: `AGENT_CARD_PREFIX`) | on-`automation/testids` (pre-existing) | confirmed live: `catalog-agent-card-315` |
| Catalog agent modal "Start Chat" | `catalog-agent-modal-start-chat-button` | on-`automation/testids` (pre-existing) | |
| Chat message input | `chat-message-input` | on-`automation/testids` (pre-existing) | `ChatPage.message_input` |
| Chat send button | `chat-send-button` | on-`automation/testids` (pre-existing) | |
| Skill mention popper container | `skill-mention-list` | on-`automation/testids` (pre-existing, ELITEA-1736 rework) | |
| Skill mention item (dynamic) | `[data-testid="skill-mention-item-{skill_name}"]` (`ChatPage.MENTION_SKILL_ITEM`) | on-`automation/testids` (pre-existing) | confirmed live for both skills this run |
| Thought accordion header | `chat-answer-thought-accordion` | on-`automation/testids` (pre-existing) | `ChatPage.answer_thought_accordion` |
| Model chip inside accordion | `chat-answer-model-chip` | on-`automation/testids` (pre-existing) | text "Anthropic Claude 4.5 Sonnet" |
| Skill/tool chip inside accordion | `chat-answer-tool-chip` | on-`automation/testids` (pre-existing) | **confirmed live this run for SKILL invocations**: text is `"Skill: {skill_name}"` — same testid the page object's docstring documents for toolkit calls (`"{toolkit_name}: {tool_name}"`); the skill shape is simpler and distinct, worth calling out explicitly since the docstring doesn't currently mention it |
| Published agent's message list container | `ul.MuiList-root > li.MuiListItem-root` (standard MUI message pattern, per `.claude/rules/mui-patterns.md`) | n/a (structural, not testid) | use `_extract_message_body()` idiom, never raw `text_content()` |

## Network Behavior
- `POST .../elitea_core/publish_validate/prompt_lib/{project}/{versionId}` —
  fires on wizard "Continue"; response's `critical_issues[]` includes a
  `field: "skills"` entry (`{skill: <name>}` detail) when an attached skill's own
  content is too short — this is new information beyond what ELITEA-1892's AFS
  documents (that AFS only exercised agents with no attached skills).
- `POST .../elitea_core/publish/prompt_lib/{project}/{versionId}` — fires on
  "Publish", 200 on success, returns the new published version id.
- Skill-mention send fires the normal chat-send WebSocket flow (same as any
  agent message); no extra REST call is associated with the `~mention` syntax
  itself — the mention is purely a client-side text/skill-selection convention
  read by the backend from the message content.

## Known Defects Found During Exploration
None found. (The agent-level "skills content length" validation gate is a
**discovery**, not a defect — it is the platform correctly guarding publish
quality; documented above as Automation-relevant test-data guidance.)

## Blocked Steps
None.

## Automation Hints
- Framework: Playwright + pytest (per `.agents/testing.md`).
- Page objects: `SkillFormPage` (skill create), `AgentFormPage`/`AgentDetailPage`
  (agent create, attach skill, publish wizard — reuse
  `AgentDetailPage.attach_skill()` and the ELITEA-1892-pattern publish-wizard
  methods if they exist as reusable helpers by the time this is implemented),
  `AgentHubPage`/Catalog page object (search, tabs, card, start-chat), `ChatPage`
  (`send_message_with_skill_mention()` — **already exists**, use it verbatim
  rather than re-deriving the mention mechanics; the docstring explicitly warns
  against `fill()` for the trailing prompt text).
- **Seed all 3 skills' instructions at ≥100 chars from the start** — do not
  reproduce this run's discovery-by-failure sequence (create short, hit the
  agent-publish Critical gate, go edit the skill, retry). Automation should
  simply seed correct test data.
- Wait strategy: AI responses arrive over WebSocket ~2–10s after send in this
  run (longest observed: word-counter response took ~10s including the "Skill:"
  status chip appearing mid-stream before final content) — use
  `wait_for_ai_response()`/equivalent condition waits, never a fixed sleep. The
  thought accordion header text ("Thought for N secs") is dynamic and streams in
  progressively — assert on the `chat-answer-tool-chip` testid's presence/text,
  not on the accordion header's exact wording.
- The "Mention skill" popper (`skill-mention-list`) appears immediately on
  typing `~` (no debounce needed) and is keyed by the SAME popper-item pattern
  used elsewhere in the suite — confirmed items rendered for all 3 attached
  skills with their full descriptions as secondary text.
