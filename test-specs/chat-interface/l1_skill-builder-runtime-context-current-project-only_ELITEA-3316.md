# Test Case: Skill Builder receives runtime_context and creates skill in current project only

## Metadata
- **TMS ID**: ELITEA-3316
- **Linked Story**: `EliteaAI/elitea_issues#6306`
- **Priority**: l1 (case `priority: critical`)
- **Environment Explored**: DEV (`https://dev.elitea.ai/app`), project "Private" (id 575); other projects visible in selector: "Public" (1), "Elitea Automation" (470)
- **User set**: `${TEST_USER}`
- **Analyst**: qa-engineer (agent)
- **Status**: **blocked** (environment: DEV chat returned no AI reply in this sandbox; skill creation, chip and cross-project check could not be observed). Same blocker as ELITEA-3367.

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
| 3 Send message, no project question | proceeds with creation | step 3 | tool chips | blocked - no AI reply observed |
| 4 Skill chip | present | step 4 | generated-entity-chip | blocked (by 3) |
| 5 Project A list has skill | present | step 5 | list | blocked (by 3) |
| 6 Project B list lacks skill | absent | step 6 | list | blocked (by 3) |

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

## Known Defects / Findings
- Environment: after sending the message on DEV, the response area showed only the model chip "Dial-GPT-5.6-Luna" with no content for 120s; no `POST .../skills/prompt_lib` fired. Prior chats in the sandbox ("Say hello", "Create skill for onboarding") look equally unanswered. ELITEA-3366 worked on DEV earlier the same day, so likely intermittent model/backend outage. Not a filed product bug (unconfirmed, could be Dial model issue).

## Blocked Steps
Steps 3-6. Unblock: DEV chat must answer; then run live and confirm chip, skill project via API, and absence in project 470.

## Automation Hints
- Likely a clustered/extension of the ELITEA-3366 ChatPage skill-builder flow (generated-entity-chip field, toggle). Same `click_module_toggle` toast caveat applies.
- Wait with `wait_for_ai_response()`/chip visibility (up to ~120s), no sleeps.
- Tag test `@pytest.mark.tms("ELITEA-3316")`.
