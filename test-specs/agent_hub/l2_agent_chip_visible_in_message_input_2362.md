---
afs_version: "1.0"
status: ready-for-automation
family_afs: false
---

# AFS: ELITEA-2362 — Agent Hub — agent chip visible in message input with version and settings

**TMS Case:** ELITEA-2362 — Agent Hub — agent chip visible in message input with version and settings  
**Feature:** Agent Hub  
**Priority:** medium  
**Test Type:** functional

---

## Coverage Map

| Axis 1 — Step / Expectation | Source | Assertion | Status |
|---|---|---|---|
| **Setup: User is logged in** | Preconditions | Auth state via fixture | asserted |
| **Step 1: Navigate to Agent Hub** | Steps 1 | Catalog page loads at `/elitea-catalog` | asserted |
| **Step 2: Click agent card (e.g., "Business Analyst")** | Steps 2 | Modal opens displaying agent details | asserted |
| **Step 3: Click "Start conversation"** | Steps 3 | Navigation to chat page with agent participant | asserted |
| **Step 4: Verify agent chip visible in message input area** | Steps 4 | Chip renders with testid `chat-participant-row-application-*` | asserted |
| **Step 5: Verify chip displays avatar/icon** | Steps 5 | Image element present in chip with src to default_entity_icons | asserted |
| **Step 6: Verify chip displays agent name** | Steps 6 | Agent name text ("Business Analyst") visible in chip | asserted |
| **Step 7: Verify chip displays version** | Steps 7 | Version text (e.g., "v2.1") visible in chip | asserted |
| **Step 8: Verify settings icon visible** | Steps 8 | Settings button `chat-participant-edit-view-button` visible with aria-label="View settings" | asserted |

---

## Handles Reference

| Element | Testid / Selector | Notes | Provenance |
|---|---|---|---|
| Agent Hub catalog page | URL `/elitea-catalog` | Navigate to entry point | on-main ✓ |
| Agent card (first visible) | `[data-testid*='agent-card']:first-of-type` | Clickable card row | on-automation/testids ✓ (live-confirmed) |
| Start Chat button on modal | `data-testid="catalog-agent-modal-start-chat-button"` | Initiates conversation | on-automation/testids ✓ (live-confirmed) |
| Agent participant chip row | `data-testid="chat-participant-row-application_*"` | Dynamic testid with app id | on-automation/testids ✓ (live-confirmed) |
| Chip avatar image | `img` inside participant chip | Avatar visual element | on-automation/testids ✓ (live-confirmed) |
| Chip agent name text | span containing agent name | Text locator: "Business Analyst" | on-automation/testids ✓ (live-confirmed) |
| Chip version text | span containing version (e.g., "v2.1") | Text locator: version string | on-automation/testids ✓ (live-confirmed) |
| Settings button on chip | `data-testid="chat-participant-edit-view-button"` | Gear icon button with aria-label="View settings" | on-automation/testids ✓ (live-confirmed) |
| Remove button on chip | `data-testid="chat-participant-remove-button"` | X icon button with aria-label="Remove agent" | on-automation/testids ✓ (live-confirmed) |
| Chat message input | `data-testid="chat-message-input"` | Textarea for sending messages | on-main ✓ |

---

## Preconditions

- User is logged in (via `auth_state` fixture)
- Elitea platform is accessible at `http://localhost:5173`

---

## Test Data

None required. Case uses existing agents from the Agent Hub catalog.

---

## Execution Notes

- Navigate to the Agent Hub catalog at `/elitea-catalog`
- Click any visible agent card to open its detail modal
- Click the "Start Chat" button (`catalog-agent-modal-start-chat-button`)
- User should be redirected to `/chat` with the selected agent added as a participant
- The agent chip should render at the bottom of the page in the message input area
- The chip should display:
  - Avatar image from the agent's icon
  - Agent name text
  - Agent version text
  - Settings button (gear icon) with aria-label="View settings"

---

## Known Defects / Gaps

None identified.

---

## Related Cases

- **ELITEA-2360:** Agent Hub start conversation creates new chat and redirects (covers the navigation/redirect behavior)
- **ELITEA-2361:** Agent added as participant in started conversation (covers participant addition)

---

## AFS Amendments

None.
