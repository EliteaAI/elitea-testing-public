---
name: "Agent Hub — agent chip visible in message input with version and settings"
description: "Verify that after starting a conversation from Agent Hub, the composer (message-input area) shows the active agent as a chip with avatar, name, version, and a settings icon"
type: ready-for-automation
priority: medium
case_id: ELITEA-2362
tms_case_path: tests/automated-full-regression-ui/agent_hub/ELITEA-2362_agent-hub-agent-chip-visible-in-message-input-with-version-a.md
status: ready-for-automation
---

# ELITEA-2362 — Agent Hub: Agent Chip Visible in Message Input With Version and Settings

**Objective:** Verify that when starting a conversation from the Agent Hub (Catalog), the
composer's active-participant chip — in the message-input area at the bottom of the chat,
distinct from the Participants panel (covered by ELITEA-2361) — shows the agent's avatar,
name, version, and a settings icon.

## Preconditions

- User is logged in to the Elitea platform
- Agent Hub (Catalog) page is accessible at `/elitea-catalog`
- Test agent available (e.g., "User Story Creator", id=172)

## Test Data

| Field | Value |
|---|---|
| Test agent | User Story Creator (id=172) |
| Expected version | skills-v3.0 |

## Coverage Map (Axis 1 — Original case → AFS)

| Step # | Original case text | AFS Status | Assertion | Notes |
|---|---|---|---|---|
| 1 | Navigate to Agent Hub | asserted | Page loads to `/elitea-catalog` | |
| 2 | Click on an agent card (e.g., "User Story Creator") to open the detail modal | asserted | Modal opens with agent details visible | Uses `catalog-agent-card-172` |
| 3 | Click "Start conversation" | asserted | Button click succeeds; navigation to `/chat` begins | Live product labels this "Start Chat" per #1042 (already tracked, not re-filed) |
| 4 | Verify the agent chip is visible in the message input area at the bottom | asserted | Composer's active-participant chip button visible | `switch_participant_button` / testid `chat-switch-participant-button` |
| 5 | Verify the chip displays the agent avatar/icon | asserted | Avatar `<img>` visible inside the chip | testid `chat-switch-participant-avatar` — **needs-adding → added this dispatch** |
| 6 | Verify the chip displays the agent name (e.g., "User Story Creator") | asserted | Text "User Story Creator" present in the chip | Rendered inside `chat-switch-participant-button` (`participantDetails.name`) |
| 7 | Verify the chip displays the agent version (e.g., "ver-0.1") | asserted | Text "skills-v3.0" displayed | `chat_version_selector_trigger` / testid `chat-version-selector-trigger`; case example "ver-0.1" is stale — live shows "skills-v3.0" (same drift as ELITEA-2361, tracked under #1042) |
| 8 | Verify a settings icon is visible on the agent chip | asserted | Settings button visible in the composer, alongside the chip | testid `chat-participant-settings-button` — pre-existing on `automation/testids`, not yet wired into `ChatPage`; wired this dispatch |

## Concrete Handles (Axis 2 — Locators & test data)

| Handle | Locator/Method | Provenance | Notes |
|---|---|---|---|
| Agent Hub page | `navigate("/elitea-catalog")` | pre-existing | Page object method |
| User Story Creator card | `[data-testid="catalog-agent-card-172"]` | on-automation/testids ✓ (ELITEA-2075) | Agent id=172 "no starters/no welcome message" precondition |
| Agent modal | auto-waits on GET `/api/v2/elitea_core/public_application/prompt_lib/{id}` | `_surface.md` | Opens on card click |
| Start Chat button | `[data-testid="catalog-agent-modal-start-chat-button"]` | on-automation/testids ✓ (pre-existing, ELITEA-2075) | `AgentHubPage.click_start_chat()` owns the known-defect-#1043 1s wait internally |
| Chat page | URL `/chat` + `ChatPage.wait_for_page_load()` | built-in | Navigation target after Start Chat |
| Composer agent chip (button) | `[data-testid="chat-switch-participant-button"]` | on-main ✓ (pre-existing, ELITEA-1736) | `ChatPage.switch_participant_button`; contains avatar `<img>` + name `Typography` |
| Composer agent chip avatar | `[data-testid="chat-switch-participant-avatar"]` scoped inside `chat-switch-participant-button` | **needs-adding → added this dispatch**, on-automation/testids ✓ (EliteaAI/EliteaUI@91746dfc, ELITEA-2362) | `EntityIcon`'s `imgTestId` prop threaded to `EliteAImage`; same idiom as ELITEA-2361's `chat-participant-avatar`. Alt text is hardcoded `"elitea"` regardless of caller (EliteAImage quirk — see qa memory). `ChatPage.CHAT_SWITCH_PARTICIPANT_AVATAR` + `get_switch_participant_avatar()` |
| Composer version chip | `[data-testid="chat-version-selector-trigger"]` | on-automation/testids ✓ (ELITEA-2166), NOT yet on main | `ChatPage.chat_version_selector_trigger`; text = selected version name (e.g. "skills-v3.0") when not in small-view |
| Composer settings button | `[data-testid="chat-participant-settings-button"]` | on-automation/testids ✓ (pre-existing, same AgentEditorPanel.jsx rework as `chat-version-selector-trigger`), NOT yet on main | **needs-adding to page object → wired this dispatch.** `ChatPage.chat_participant_settings_button`; renders a `SettingIcon` (or "Editing…"/"Viewing…" text only if the panel is actively being edited — not applicable to this flow) |

## Test Outline

1. Navigate to Agent Hub at `/elitea-catalog`
2. Click the User Story Creator agent card to open the modal
3. Wait for modal to load (GET `.../prompt_lib/172` resolves)
4. Click the "Start Chat" button in the modal (`AgentHubPage.click_start_chat()`)
5. Verify URL changes to `/chat`; `ChatPage.wait_for_page_load()`
6. Verify the composer's `chat-switch-participant-button` chip is visible
7. Within that chip: verify the avatar `<img>` (`chat-switch-participant-avatar`) is visible
8. Within that chip: verify the text contains "User Story Creator"
9. Verify the composer's version chip (`chat-version-selector-trigger`) is visible and reads "skills-v3.0"
10. Verify the composer's settings button (`chat-participant-settings-button`) is visible

## Expected Behavior

- **Navigation:** URL transitions from `/elitea-catalog` → `/chat`
- **Composer chip:** `AgentEditorPanel`'s `ButtonGroup` renders three adjacent controls once
  an agent participant is active: the switch-participant chip (avatar + name), a
  version-selector trigger, and a settings button
- **Agent chip:** avatar visible, name "User Story Creator" visible
- **Version chip:** "skills-v3.0" visible
- **Settings button:** visible (not disabled — the version is unpublished/draft, so
  `isEditSettingsDisabled` is false; not asserted directly, visibility is the case's ask)
- **No errors:** no console errors or network failures during the flow (side-channel check)

## Known Issues / Case-Text Drift

- **#1042:** Case text says "Start conversation"; live product displays "Start Chat".
  AFS uses the product's actual label. Same case-text drift already tracked for
  ELITEA-2361 and other Agent-Hub siblings — not re-filed.
- **Version format:** Case text example shows "ver-0.1"; live agent displays "skills-v3.0".
  AFS asserts the actual live version format (same drift class as ELITEA-2361).

## Axis 2 Notes

Live-verified 2026-08-11 via Playwright MCP against `http://localhost:5173`: opened
"User Story Creator" (id=172) from the Catalog, clicked "Start Chat", landed on `/chat`,
and read the composer DOM directly. Confirmed three adjacent controls inside one
`ButtonGroup` (`AgentEditorPanel.jsx`):
- `button[data-testid="chat-switch-participant-button"]` (accessible name "Switch Agent")
  containing `<img alt="elitea">` (no testid before this dispatch) + text "User Story Creator"
- `button[data-testid="chat-version-selector-trigger"]` (accessible name "version selector
  menu") with text "skills-v3.0"
- `button[data-testid="chat-participant-settings-button"]` (accessible name "agent settings
  menu")

The avatar `<img>` had **no testid** — confirmed via `browser_evaluate` reading
`outerHTML` before the fix. `EntityIcon.jsx` already supports an `imgTestId` prop
(threaded to `EliteAImage`'s `data-testid`, same mechanism ELITEA-2361 used for
`chat-participant-avatar`), so the fix is additive: `imgTestId="chat-switch-participant-avatar"`
added to `AgentEditorPanel.jsx`'s `EntityIcon` call (the ONLY `EntityIcon` call in that
file lacking a testid — the composer's chip; no other call sites touched, canon #511
scope discipline). Pushed to `automation/testids` (`EliteaAI/EliteaUI@91746dfc`).

`chat-version-selector-trigger` and `chat-participant-settings-button` both already
existed in `AgentEditorPanel.jsx`/`VersionSelector.jsx` source on `automation/testids`
(added during the unrelated ELITEA-2166 ruling, declared improvisation) but
`chat-participant-settings-button` had never been wired into `ChatPage` as a
`LocatorDescriptor` — added this dispatch (canon ruling #511: a testid not yet
referenced by any page-object field/method is not "referenced" until a test's
executed path calls it — this AFS's Test Outline step 10 is that path).

Per canon ruling #511 (agent chip is two separate elements, name+version are NOT
combined into one handle): confirmed live — the name lives inside
`chat-switch-participant-button`'s own `Typography`, and the version lives in a
**separate sibling button** (`chat-version-selector-trigger`), not a combined
"AgentName vX" string on one element. The AFS's Coverage Map rows 6/7 assert them
as two independent facts on two different handles, matching the DOM.

## Amendments

- **2026-08-11 (implementer, ELITEA-2362):** AFS created fresh (no prior AFS existed —
  intake gap; this dispatch performed the analyst pass live before implementation).
  Sibling coverage check: `test_agent_hub_start_conversation_with_starters.py`
  (ELITEA-2369) already asserts `is_agent_participant_in_composer()` (name) +
  `chat_version_selector_trigger` (version) for a *different* agent/flow (with
  conversation starters) — but does NOT assert the avatar or the settings button.
  Neither existing spec is a covering spec for this case's full step set (avatar +
  settings are unique to this case), so this ships as its own `ready-for-automation`
  spec rather than `extend-existing` or `already-covered`.

## Status

**ready-for-automation** — All case steps mapped and verified live (2026-08-11, this
dispatch). All handles confirmed present and interactable, one new testid added
(avatar), one pre-existing-but-unwired testid wired into the page object (settings
button). Flow executes successfully without blockers.
