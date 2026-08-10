---
name: "Agent Hub — start conversation creates new chat and redirects to Chat page"
description: "Verify that clicking Start Chat in an agent modal creates a new conversation and redirects to the Chat interface with welcome message displayed"
type: ready-for-automation
priority: medium
case_id: ELITEA-2360
tms_case_path: tests/automated-full-regression-ui/agent-hub/ELITEA-2360.md
status: ready-for-automation
---

# ELITEA-2360 — Agent Hub: Start Conversation Creates New Chat and Redirects

**Objective:** Verify that starting a conversation from the Agent Hub (Catalog) creates a new chat conversation and redirects the user to the Chat interface with the welcome message displayed.

## Preconditions

- User is logged in to the Elitea platform
- Agent Hub (Catalog) page is accessible at `/elitea-catalog`
- Test agents are available (e.g., "User Story Creator")

## Test Data

| Field | Value |
|-------|-------|
| Test agent | User Story Creator (id=172) |

## Coverage Map (Axis 1 — Original case → AFS)

| Step # | Original case text | AFS Status | Assertion | Notes |
|---|---|---|---|---|
| 1 | Navigate to Agent Hub | asserted | Page loads to `/elitea-catalog` | |
| 2 | Click on an agent card (e.g., "User Story Creator") to open the detail modal | asserted | Modal opens with agent details visible | Uses `catalog-agent-card-172` |
| 3 | Click the "Start conversation" button | asserted | Button click succeeds; navigation begins | Live product labels this "Start Chat" not "Start conversation" per #1042 |
| 4 | Verify a new chat conversation is created | asserted | Chat page loads successfully | URL changes to `/chat` |
| 5 | Verify the user is redirected to the Chat interface | asserted | Chat page is displayed | URL `/chat` confirmed |
| 6 | Verify the chat welcome message is displayed | asserted | Welcome greeting visible | "Hello, [username]! What can I do for you today?" displayed |

## Concrete Handles (Axis 2 — Locators & test data)

| Handle | Locator/Method | Provenance | Notes |
|---|---|---|---|
| Agent Hub page | `navigate("/elitea-catalog")` | pre-existing | Page object method |
| User Story Creator card | `[data-testid="catalog-agent-card-172"]` | on-automation/testids ✓ (per ELITEA-2075) | Agent id=172 is the example agent for "no starters/no welcome message" precondition |
| Agent modal | auto-waits on GET `/api/v2/elitea_core/public_application/prompt_lib/{id}` | per _surface.md | Open via `AgentHubPage.open_agent_by_name()` or card click |
| Start Chat button | `[data-testid="catalog-agent-modal-start-chat-button"]` | on-automation/testids ✓ (pre-existing, ELITEA-2075) | |
| Chat welcome message | `[data-testid="chat-new-conversation-greeting"]` | on-automation/testids ✓ (per _surface.md) | Contains "Hello, {user}! What can I do for you today?" |
| Chat page | URL `/chat` + page title contains "Chat" | built-in | Navigation target after Start Chat click |

## Test Outline

1. Navigate to Agent Hub (`/elitea-catalog`)
2. Click the User Story Creator agent card to open the modal
3. Wait for the modal to load (GET `.../prompt_lib/172` resolves)
4. Click the "Start Chat" button in the modal
5. Verify the URL changes from `/elitea-catalog` to `/chat`
6. Verify the page title contains "Chat"
7. Verify the welcome greeting element is visible with expected text

## Expected Behavior

- **Navigation:** URL transitions from `/elitea-catalog` → `/chat`
- **Welcome Message:** "Hello, {username}! What can I do for you today?" is visible in the chat interface
- **No errors:** No console errors or network failures during the flow

## Known Issues / Case-Text Drift

- **#1042:** Case text says "Start conversation" / "CONVERSATION STARTERS"; live product displays "Start Chat" / "CHAT STARTERS". AFS uses the product's actual labels.
- **No cleanup needed for this case:** A new conversation is created but NOT deleted. Cleanup (if any) is deferred to test-data-reuse decision by the implementer during Phase 3.

## Axis 2 Notes

All handles are pre-existing on `automation/testids` or are stable product elements. No new testids are required.

## Status

**ready-for-automation** — All case steps mapped, all handles confirmed live (2026-08-10), flow executes successfully without blockers.
