---
name: "Agent Hub — started conversation has agent added as participant"
description: "Verify that when starting a conversation from Agent Hub, the selected agent appears as a participant in the chat with avatar, name, and version visible"
type: ready-for-automation
priority: medium
case_id: ELITEA-2361
tms_case_path: tests/automated-full-regression-ui/agent-hub/ELITEA-2361.md
status: ready-for-automation
---

# ELITEA-2361 — Agent Hub: Started Conversation Has Agent Added as Participant

**Objective:** Verify that when starting a conversation from the Agent Hub (Catalog), the selected agent is automatically added as a participant in the chat. Success is confirmed by verifying the agent's avatar, name, and version are all visible in the Participants panel.

## Preconditions

- User is logged in to the Elitea platform
- Agent Hub (Catalog) page is accessible at `/elitea-catalog`
- Test agent available (e.g., "User Story Creator", id=172)

## Test Data

| Field | Value |
|-------|-------|
| Test agent | User Story Creator (id=172) |
| Expected version | skills-v3.0 |

## Coverage Map (Axis 1 — Original case → AFS)

| Step # | Original case text | AFS Status | Assertion | Notes |
|---|---|---|---|---|
| 1 | Navigate to Agent Hub | asserted | Page loads to `/elitea-catalog` | |
| 2 | Click on an agent card (e.g., "User Story Creator") to open the detail modal | asserted | Modal opens with agent details visible | Uses `catalog-agent-card-172` |
| 3 | Click "Start conversation" | asserted | Button click succeeds; navigation begins | Live product labels this "Start Chat" per #1042 |
| 4 | In the new chat, open the Participants panel on the right side | asserted | Participants panel expands | Uses `chat-participants-panel-toggle-button` |
| 5 | Verify the agent appears under the AGENTS section of the participants list | asserted | AGENTS section visible with agent row | Contains participant row `chat-participant-row-application_172_1` |
| 6 | Verify the agent name matches the selected agent (e.g., "User Story Creator") | asserted | Agent name displayed correctly | Text "User Story Creator" present in participant row |
| 7 | Verify the agent version is displayed (e.g., "ver-0.1") | asserted | Agent version visible | Text "skills-v3.0" displayed in participant row |
| 8 | Verify agent's avatar is visible in Participants section | asserted | Avatar image present | `img` element with alt="elitea" in participant row |

## Concrete Handles (Axis 2 — Locators & test data)

| Handle | Locator/Method | Provenance | Notes |
|---|---|---|---|
| Agent Hub page | `navigate("/elitea-catalog")` | pre-existing | Page object method |
| User Story Creator card | `[data-testid="catalog-agent-card-172"]` | on-automation/testids ✓ (ELITEA-2075) | Agent id=172 "no starters/no welcome message" precondition |
| Agent modal | auto-waits on GET `/api/v2/elitea_core/public_application/prompt_lib/{id}` | _surface.md | Opens on card click |
| Start Chat button | `[data-testid="catalog-agent-modal-start-chat-button"]` | on-automation/testids ✓ (pre-existing, ELITEA-2075) | Creates new conversation |
| Chat page | URL `/chat` + page title contains "Chat" | built-in | Navigation target after Start Chat |
| Participants panel toggle | `[data-testid="chat-participants-panel-toggle-button"]` | on-automation/testids ✓ (confirmed live 2026-08-10) | Button to expand/collapse participants panel on right side |
| Participant row (agent) | `[data-testid="chat-participant-row-application_172_1"]` | on-automation/testids ✓ (confirmed live 2026-08-10) | Container for agent participant entry in Participants panel; format: `application_{agent_id}_{participant_index}` |
| Agent avatar in participants | `img` within `chat-participant-row-application_172_1` | on-automation/testids ✓ (confirmed live 2026-08-10) | Avatar image for agent; alt="elitea" |
| Agent name in participants | text "User Story Creator" within `chat-participant-row-application_172_1` | on-automation/testids ✓ (confirmed live 2026-08-10) | Agent name displayed in participant row |
| Agent version in participants | text "skills-v3.0" within `chat-participant-row-application_172_1` | on-automation/testids ✓ (confirmed live 2026-08-10) | Agent version/skill version displayed in participant row |

## Test Outline

1. Navigate to Agent Hub at `/elitea-catalog`
2. Click the User Story Creator agent card to open the modal
3. Wait for modal to load (GET `.../prompt_lib/172` resolves)
4. Click the "Start Chat" button in the modal
5. Verify URL changes to `/chat`
6. Click the Participants panel toggle button (right-side drawer)
7. Verify the Participants panel expands and displays the "AGENTS" section
8. Locate the agent participant row by `data-testid="chat-participant-row-application_172_1"`
9. Within that row, verify:
   - Avatar image is present and visible
   - Agent name "User Story Creator" is displayed
   - Agent version "skills-v3.0" is displayed

## Expected Behavior

- **Navigation:** URL transitions from `/elitea-catalog` → `/chat`
- **Participants Panel:** Opens on the right side showing "AGENTS" section
- **Agent Participant:** The selected agent (User Story Creator) appears as a row in the participants list with:
  - ✅ Avatar image visible
  - ✅ Agent name matching the selected agent
  - ✅ Agent version/skill version displayed
- **No errors:** No console errors or network failures during the flow

## Known Issues / Case-Text Drift

- **#1042:** Case text says "Start conversation"; live product displays "Start Chat". AFS uses the product's actual labels.
- **Version format:** Case text example shows "ver-0.1"; live agent displays "skills-v3.0". AFS asserts the actual live version format.

## Axis 2 Notes

All handles are pre-existing on `automation/testids` or are stable product elements. No new testids required.

**Participant row naming convention:** The participant row uses `data-testid="chat-participant-row-application_{agent_id}_{participant_index}"` format, where:
- `agent_id` = 172 (User Story Creator)
- `participant_index` = 1 (first/primary agent participant in this conversation)

This format allows targeting specific agent participants in conversations with multiple agents.

## Status

**ready-for-automation** — All case steps mapped and executed live (2026-08-10). All handles confirmed present and interactable. Flow executes successfully without blockers. Agent successfully appears as participant with all required attributes visible (avatar, name, version).
