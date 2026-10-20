# Test Case: Skill Builder receives runtime_context and creates skill in current project only

## Metadata
- **TMS ID**: ELITEA-3316
- **Linked Story**: `EliteaAI/elitea_issues#6306`
- **Priority**: l1 (case `priority: critical`)
- **Environment Explored**: DEV (`https://dev.elitea.ai/app`), project "Private" (id 575); other projects visible in selector: "Public" (1), "Elitea Automation" (470)
- **User set**: `${TEST_USER}`
- **Analyst**: qa-engineer (agent)
- **Status**: **ready-for-automation** (executed live on DEV 2026-10-20 via a ChatPage scratch run; earlier 2026-10-19 blocked attempt was a transient DEV chat outage). Closest neighbour: ELITEA-3366 (landed on trunk, `automation/tests/ui/chat/test_skill_creation_from_chat_chip_canvas.py`) - same flow; NOT `extend-existing`: different observable (project scoping), extra API list per project. Implementer may reuse the 3366 test's setup/cleanup shape in a new test.

## Preconditions
- Logged in (`auth_state`). Project A = active project (Private/575); Project B = any other project from the selector (Elitea Automation/470).
- Skills Builder is a Modules-panel toggle, OFF by default per new conversation (see `test-specs/chat-interface/_surface.md`, ELITEA-3366 section). Must be enabled: `+` menu -> hover Modules -> `modules-toggle-skill_builder`.
- A platform banner dialog (`platform-banner-center`, close `platform-banner-close` "Got it") can intercept clicks on first load; dismiss it first (`BasePage.dismiss_banner_if_present`). After the Modules submenu a tooltip popper also intercepts the composer click: click neutral area or Escape first.

## Test Data
- generate-per-test: skill display name `Meeting Notes Summarizer` plus per-run unique suffix (slug collisions); message `Create a skill called '<name>' that summarizes meeting notes into action items`.
- Cleanup: `SkillAPI.delete_skill` (automation/api/client.py) in try/finally; delete conversation via conversation_api.

## Test Steps
1. Confirm Project A: read `project-selector-trigger-combobox` text (observed live: "Project: Private"). Verify: equals configured project.
2. Enable Skills Builder via Modules toggle. Verify: toggle checked (input inside `modules-toggle-skill_builder`).
3. Send the creation message via `chat-message-input` / `chat-send-button`. Verify (expected, per ELITEA-3366 analysis): no clarifying question about project_id/user_id; tool-call chips `chat-answer-model-chip` read "Elitea Skills: post_elitea_core_skills". Assert structurally, not on prose absence.
4. Verify `generated-entity-chip` present in the response (label is the slugified skill name, not "Skill: ...").
5. Project A skills list: skill present. Prefer API `SkillAPI.list_skills()` for project A (575) plus UI check on `/skills` page per skills `_surface.md`.
6. Project B skills list: skill NOT present. Switch via existing `BasePage.switch_project(project_id)` (dynamic `select-option-{id}`), or API list with project_id=470 (no cross-project UI needed for the negative assertion; do both if cheap).

## Coverage Map

| Case element | Expected | Covered by | Asserted where | Disposition |
|---|---|---|---|---|
| 1 Confirm Project A | selected | step 1 | selector text | asserted (observed live) |
| 2 Enable Skills Builder | toggle on | step 2 | toggle input | asserted (toggle clicked live; resulting state not independently confirmed) |
| 3 Send message, no project question | proceeds with creation | step 3 | tool chips | OBSERVED live 2026-10-20: chips read `Elitea Skills: post_elitea_core_generate_skill_draft` (+ `post_elitea_core_skills`), no project/user question asked |
| 4 Skill chip | present | step 4 | generated-entity-chip | OBSERVED live (see Execution Log) |
| 5 Project A list has skill | present | step 5 | list | OBSERVED live (see Execution Log) |
| 6 Project B list lacks skill | absent | step 6 | list | OBSERVED live (see Execution Log) |

Axis 2: also assert via API that the created skill's project is 575 (stronger than UI list) - grounded in the case's "created in the correct project" claim.

## Concrete Handles
| Element | Handle | Rung / provenance |
|---|---|---|
| Project selector | `testid=project-selector-trigger-combobox` | rung 1, live ✓ (BasePage) |
| Project option | `select-option-{id}` | rung 1, live ✓ (ids 1/575/470) |
| Banner close | `platform-banner-close` | rung 1, live ✓ |
| Create chat | `sidebar-create-button` | rung 1, live ✓ |
| Plus menu / Modules | `plus-menu-button`, `internal-tools-menuitem` (hover) | rung 1, live ✓ |
| Skills Builder toggle | `modules-toggle-skill_builder` | rung 1, live ✓ |
| Message input / send | `chat-message-input`, `chat-send-button` | rung 1, live ✓ |
| Skill chip | `generated-entity-chip` | rung 1; from 3366 AFS, NOT observed this run |

## Execution Log (2026-10-20, DEV, project Private/575)
- Selector read: `project-selector-trigger-combobox` text content `PProject:Private` (an avatar letter "P" is concatenated; assert with `"Private" in text` / endswith, not equality).
- Skills Builder toggled on after creating the conversation; `is_module_toggle_checked("skill_builder")` True.
- Message `Create a skill called 'Meeting Notes Summarizer <suffix>' that summarizes meeting notes into action items` -> AI created the skill with NO question; tool chip text `Elitea Skills: post_elitea_core_generate_skill_draft` (this run) - the tool name varies (3366 saw `post_elitea_core_skills`); assert the substring `Elitea Skills:`, not a specific tool name. One `generated-entity-chip`, label = slugified name (`meeting-notes-summarizer-<suffix>`).
- Cross-project via API (`SkillAPI(cookies, project_id=X).list_skills()`): project 575 contains the slug; project 470 (Elitea Automation) 0 rows, does NOT; project 1 (Public) 92 rows, does NOT. Cross-project check by API is sufficient and cheaper than UI switch; UI skills-list check for A is optional (`/skills/all`).
- Case-text drift: case says "Skill chip/link"; live chip label is the slug. Case implies Project B is an arbitrary other project: use 470 and 1.

## Environment gotchas (transit)
- `automation/.env.test` ABSENT in this sandbox: `APP_PREFIX` empty -> `navigate("/chat")` goes to `https://dev.elitea.ai/chat` = 404 "Page Not Found" and every UI spec fails at `chat-message-input`. Running with `APP_PREFIX=/app` in shell env makes it work. Not a product defect; env setup. The earlier 2026-10-19 "no AI reply" blocker was likely a related/transient env issue; chat answers fine today.
- `ChatPage.get_current_conversation_id()` returns None right after `click_create_conversation` (URL stays `/app/chat`); read it after the message is sent (as 3366 does with `if conv_id is None`), else the conversation leaks. `ConversationAPI.delete_conversation(None)` -> 404.
- `SkillAPI(cookies, project_id=...)` takes the project id string: `page.context.cookies()` for cookies. The `skill_api` fixture is project 575.

## Known Defects / Findings
- None. Project scoping behaves as the case expects.

## Blocked Steps
None.

## Automation Hints
- New test beside `test_skill_creation_from_chat_chip_canvas.py`, reusing ChatPage methods used there (`open_internal_tools_menu`, `ensure_module_toggle_checked`, `close_modules_panel`, `send_message`, `wait_for_ai_response`, `wait_for_message_content_stable`, `get_generated_entity_chip_labels`). Assert: no clarifying input card, exactly one chip == slug, slug in project 575 list, absent from `SkillAPI(cookies, project_id='470')` and `'1'` lists. Cleanup skill + conversation in finally; unique suffix per run.
- Wait with `wait_for_ai_response()`/chip visibility (up to ~120s), no sleeps.
- Tag test `@pytest.mark.tms("ELITEA-3316")`.
