# Test Case: Chat - Skill auto-invocation from user intent (no participant, no `~` mention)

## Metadata
- **TMS ID**: ELITEA-4630
- **Priority**: l1 (case priority: critical)
- **Environment explored**: DEV `https://dev.elitea.ai/app` (private project 575, `${TEST_USER}`), 2026-11-11; scripted python-playwright probes (storage state from `dev_storage_state.py`), 3 live passes
- **Status**: **ready-for-automation**
- **Analyst**: qa-engineer, batch `elitea-4630`
- **surface_key**: chat-skill-auto-invocation
- **Neighbours read**: ELITEA-4628 AFS (plus-menu skills), ELITEA-4629 AFS + `test_chat_tilde_mention_skill_without_agent.py` (fixture-skill + marker-token pattern, conversation cleanup, `ChatPage` message helpers), EliteaUI `ProjectSkillsSettings.jsx` + `mentionSkillTrace.helpers.js` (origin/main), chat `_surface.md`. Not already-covered: no merged spec sends a plain-language message with NO participant and NO `~` and asserts a skill ran (4629 is the explicit `~` mention path; 4628 is plus-menu add).

## Mechanism (source-confirmed + live)
Settings -> Project -> General -> "Project skills in chat" (`project-skills-settings-card`, select `project-skills-project-setting`; options Use platform default / Enabled / Disabled; tooltip: "chats in this project can use every project skill, not only the skills added to the chat. The model searches the project for a skill that fits the request and loads it only when it applies"). On DEV it is `default` = "Use platform default (Enabled)", so auto-invocation works with no setup. If a project/env turns it off the whole case cannot pass -> assert the precondition via the setting (read-only) and fail loudly.

## Preconditions
- `auth_state`; project 575. Project-skills setting = default/Enabled (read `GET /api/v2/elitea_core/project_skills_settings/prompt_lib/575` -> `available`, and/or the settings select value `default` showing "(Enabled)"; do not mutate).
- Two fixture skills via `skill_api.create_skill(name, description, instructions)` (name <=32 chars lowercase/hyphen, unique `-<ts>` suffix), deleted in `finally`:
  - A (Jira): name `jira-ticket-maker-<ts>`; description "Creates Jira tickets and issues for bug fixes. Use when the user wants to create a ticket or issue in Jira."; instructions "Whenever loaded, begin your reply with the exact token JIRATICKET: ..."
  - B (other domain): name `recipe-planner-<ts>`; description "Plans cooking recipes and meal menus. Use when the user wants a recipe, dinner idea or meal plan."; instructions "... begin with the exact token RECIPEPLAN: ..."
- `jira-issue-creator` named in the case does NOT exist on DEV -> fixture skills (clarification).
- **Test hygiene hazard**: leftover skills from a crashed earlier run stay in the project and ALSO match the intent (observed: a stale `recipe-planner-<oldts>` showed a second `Skill:` chip). Therefore assert chips by the exact fixture name and do not assert "exactly one Skill chip"; unique-intent descriptions keep A/B from crossing.

## Observed flow (executed live)
1. `/app/chat` -> dismiss banner -> `sidebar-create-button` -> blank chat; expand participants panel: 0 `chat-participant-row-*` (no skill participant, no agent).
2. Type (press_sequentially) "I need to create a new ticket in Jira for bug fix" -> `chat-send-button` (force click). URL becomes `/app/chat/<id>?name=...` (conversation persisted -> delete in `finally`).
3. Reply arrives in ~9 s total (condition: `button[aria-label="enter speaking mode"]` returns). Last `chat-message-item` text: `Thought for 2 secs / Skill: jira-ticket-maker-<ts> / 65ms / Anthropic Claude Haiku 5.5 ... JIRATICKET: Here's a draft outline for your bug-fix Jira ticket...` (3/3 passes; marker present 3/3).
4. Tool chip: `[data-testid="chat-answer-tool-chip"]` inside the AI message, inner text `Skill: <name>` (plus duration chip `chat-answer-chip-duration`, model chip `chat-answer-model-chip`, accordion `chat-answer-thought-accordion`). No participant row appeared in the panel after the run (still 0 rows -> auto-invoke does not add a participant).
5. Second intent in the SAME chat ("Can you suggest a vegetarian dinner menu for four people?") -> reply starts `RECIPEPLAN:` with chip `Skill: recipe-planner-<ts>` and NO `Skill: jira-ticket-maker` chip -> correct skill chosen for a different intent (step 8). Note: AI-message `inner_text` for older messages in the list is re-indexed oddly during streaming; scope assertions to the message reached after waiting for generation to finish, filter by marker token rather than by index.
6. Console: only unrelated 404 "Failed to load resource". DEV had a transient 503 window (~1-2 min) mid-session on `/api/v2/elitea_core/skills*` - infrastructure, not product behaviour; retries OK.

## Handles Reference (verified on DEV 2026-11-11)
| rung | handle | suggested_testid | provenance |
|---|---|---|---|
| testid | `sidebar-create-button`, `chat-participants-panel-toggle-button`, `platform-banner-close`, `chat-message-input`, `chat-send-button` | - | testid on DEV ✓ (existing ChatPage fields) |
| testid | `chat-message-item` (user and AI messages) | - | testid on DEV ✓; existing `ChatPage.messages_container` (used by 4629) |
| testid | `chat-answer-tool-chip` (text `Skill: <name>`) | - | testid on DEV ✓ - check for an existing ChatPage field before adding; assert by `messages_container.filter(has_text="Skill: <A>")` or scoped `get_by_text` |
| testid | `chat-participant-row-*` prefix (existing `PARTICIPANT_ROW_PREFIX`) | - | testid on DEV ✓ - assert count 0 before and after |
| testid | `project-skills-settings-card` / `project-skills-project-setting` (hidden native input, value `default`/`true`/`false`) | - | testid on DEV ✓; only if the precondition is asserted via UI (`/settings/project-general`); prefer the API endpoint (no page object work) |
| ladder (wait signal) | `button[aria-label="enter speaking mode"]` / existing `wait_for_generation_complete`, `wait_for_input_ready` | `chat-speaking-mode-button` | reuse existing helpers |

## Steps (AFS)
1. Fixtures create skills A (Jira) and B (recipe). Assert project-skills setting available (precondition). Open `/app/chat`, dismiss banner, `sidebar-create-button`, expand participants panel. **Verify** 0 participant rows (no agent, no skill; case step 1).
2. Type "I need to create a new ticket in Jira for bug fix" (press_sequentially). **Verify** composer value equals the text (step 2).
3. Click send. **Verify** user message item contains the text; capture conversation id from URL (step 3).
4. Wait for generation complete (condition wait, timeout 90 s) (steps 4-5).
5. **Verify** the AI reply contains marker `JIRATICKET:` (only skill A's instructions produce it) and a tool chip `Skill: <A name>` (`chat-answer-tool-chip`) (steps 5-7). **Verify** reply does NOT contain `RECIPEPLAN:` and no `Skill: <B name>` chip (wrong skill not selected).
6. **Verify** participants panel still has 0 `chat-participant-row-*` (skill was NOT an explicit participant) and the user message does not contain `~` (no mention).
7. Send second intent "Can you suggest a vegetarian dinner menu for four people?"; wait for generation complete. **Verify** a message contains `RECIPEPLAN:` and chip `Skill: <B name>` (step 8: different intent -> different skill). Assert the second AI message has no `Skill: <A name>` chip (scope to the new message: count of messages before vs after, last AI item).
8. Teardown: delete conversation (ConversationAPI) and skills A, B in `finally`.

## Coverage Map
| Case element | Expected | Covered by | Disposition |
|---|---|---|---|
| 1 Open chat w/o participant | empty/other participants | AFS 1, 6 | covered |
| 2 Type NL message | text in input | AFS 2 | covered |
| 3 Send | sends | AFS 3 | covered |
| 4 Analyse intent/metadata | system analyses | AFS 4-5 (observable via outcome) | covered indirectly; no UI signal for "analysis" itself |
| 5 Auto invokes skill | skill invoked | AFS 5 | covered (chip + marker) |
| 6 Skill executes, responds | response | AFS 5 | covered via marker token `JIRATICKET:` instead of real Jira creation (**clarification**: fixture skill has no Jira toolkit) |
| 7 Response indicates skill invoked | skill name / context shown | AFS 5 | covered (`Skill: <name>` chip) |
| 8 Other intent -> other skill | correct match | AFS 7 | covered |
| Fail: needs explicit participant / `~` | none | AFS 1, 6 | covered |
Axis 2 extras: wrong-skill negative checks (AFS 5, 7) from the case's own Fail criteria "Wrong skill is selected"; setting precondition (feature gate, source-confirmed).

## Clarifications (case-text drift, NOT defects)
- `jira-issue-creator` does not exist on DEV; fixture skills with intent-bearing descriptions are used. Skill execution is a marker-token response, not an actual Jira ticket.
- Case never states the gating setting "Project skills in chat" (Enabled via platform default); it is the precondition that makes the feature work.
- Selection is LLM-driven (Haiku 5.5): 3/3 live passes matched correctly with distinct-domain descriptions; keep descriptions distinct to avoid flake, and consider it a known nondeterminism risk for the gate.

## Known defects
None.

## Automation Hints
- Mostly reuse of 4629's test skeleton (skill_api, conversation_api, marker assertions, `wait_for_generation_complete`). New: tool-chip assertion helper in `ChatPage` (e.g. `has_skill_tool_chip(name)` over `messages_container.filter(has_text=...)`), participant-row-count helpers exist.
- Wait by condition, never sleep. Typing via `press_sequentially`; send with `send_button.click(force=True)`.
- Skill creation may 503 during DEV blips; cleanup in `finally`.
- Markers: `@pytest.mark.tms("ELITEA-4630")` + `@allure.issue` pair; ui, chat, skills, p0, regression. Case file path in TMS: `tests/automated-full-regression-ui/skills/ELITEA-4630_*.md` (confirm exact filename with the sibling 4629 pattern).
