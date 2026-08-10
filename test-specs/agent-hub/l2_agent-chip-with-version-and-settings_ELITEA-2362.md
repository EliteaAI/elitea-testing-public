---
case_id: ELITEA-2362
title: Agent Hub — agent chip visible in message input with version and settings
priority: medium
status: ready-for-automation
feature: agent-hub
afs_created: 2026-08-10
analyst: qa-engineer
---

# AFS: ELITEA-2362 — Agent chip in message input with version and settings

**Case ID:** ELITEA-2362 · **Priority:** medium · **Type:** functional

**Objective:** Verify that after starting a conversation with an agent from the Agent Hub catalog, the agent chip displays in the message input area with avatar, agent name, agent version, and a settings icon.

## Preconditions

- User is logged in to the Elitea platform (localhost auth via `VITE_DEV_TOKEN`)
- Agent Hub (Catalog) page is accessible at `/elitea-catalog`
- At least one agent with a configured version is available in the Catalog (e.g., "Business Analyst")

## Test Data

| Field | Value |
|-------|-------|
| Example agent | "Business Analyst" (id 31) or "User Story Creator" (id 172) |
| Expected version format | `v{major}.{minor}` (e.g., `v2.1`) |

---

## Test Flow

### Step 1 — Navigate to Agent Hub (Catalog)

**Action:** Browser navigates to `/elitea-catalog`

**Expected Result:** Catalog page loads successfully with:
- Page heading: "Welcome to ELITEA Catalog!" (testid: `catalog-page-heading`)
- "Agents" and "Skills" tabs at the top
- Search input (testid: `catalog-search-input`)
- Category filter rail on the right (Business Analyst, Elitea, DevOps, etc.)
- Agent cards grid showing Trending agents (testid: `catalog-agent-card-{id}`)

**Observable:** Page title contains "ELITEA Catalog"

---

### Step 2 — Open agent detail modal

**Action:** Click on any agent card (e.g., first visible agent or "Business Analyst" explicitly)

**Expected Result:** Agent detail modal opens with:
- Agent name heading (testid: `catalog-agent-modal-agent-name`)
- Agent description
- "Chat Starters" section (if configured)
- "Welcome Message" section (if configured)
- "Start Chat" button at the bottom (testid: `catalog-agent-modal-start-chat-button`)

**Observable:** Modal overlay is visible; modal content is populated with agent details

---

### Step 3 — Start conversation (navigate to chat)

**Action:** Click "Start Chat" button in the agent detail modal

**Expected Result:**
- Modal closes
- Browser navigates to `/chat` (initial new conversation page)
- Chat page loads with an empty message history and a new message input composer at the bottom
- Agent participant is pre-populated in the conversation

**Observable:** Page URL changes to `/chat` or `/chat/{conversation_id}` after navigation settles

---

### Step 4 — Verify agent chip is visible in message input

**Action:** Observe the message input area at the bottom of the chat page

**Expected Result:** Agent chip is visible in the message input composer area (left side, before the text input field)

**Handle:** `[data-testid="chat-switch-participant-button"]`

**Provenance:** on-automation/testids ✓ (ELITEA-2353)

**Observable:** Element is visible and interactive; clicking it opens a participant switcher panel

---

### Step 5 — Verify agent avatar/icon on chip

**Action:** Inspect the agent chip element

**Expected Result:** Agent chip contains:
- An `<img>` element with `alt="elitea"`
- Source points to the agent's default entity icon or custom avatar
- Icon is 1rem × 1rem, rounded

**Handle:** `[data-testid="chat-switch-participant-button"] img[alt="elitea"]`

**Provenance:** on-automation/testids ✓ (pre-existing, ELITEA-2361)

**Observable:** Avatar image is rendered and visible; no placeholder or fallback state

---

### Step 6 — Verify agent name displayed on chip

**Action:** Read the text content of the agent chip

**Expected Result:** Agent name is displayed next to the avatar
- Text: agent's registered name (e.g., "Business Analyst", "User Story Creator")
- Rendered in a `<span>` with MuiTypography classes
- Font size: small (labelSmall per MUI)

**Handle:** `[data-testid="chat-switch-participant-button"] span` (contains agent name text)

**Alternative (get text content):** `[data-testid="chat-switch-participant-button"]` → `.text_content()` contains agent name

**Provenance:** on-automation/testids ✓ (ELITEA-2361)

**Observable:** Agent name matches the agent card that was selected; text is readable and not truncated

---

### Step 7 — Verify agent version displayed

**Action:** Observe the version selector element adjacent to the agent chip

**Expected Result:** Version selector is visible and displays the agent's configured version
- Element testid: `chat-version-selector-trigger`
- Text format: `v{major}.{minor}` (e.g., `v2.1`, `v1.0`)
- Located immediately right of the agent chip (adjacent element, NOT part of the chip itself)
- Clickable; opens a version-selection dropdown

**Handle:** `[data-testid="chat-version-selector-trigger"]`

**Provenance:** on-automation/testids ✓ (ELITEA-2361)

**Observable:** Version string is visible and non-empty; reflects the agent's current selected version

**Note (case clarification):** The version is a SEPARATE element from the agent chip. The case title and case text imply a combined "agent chip with version", but the live product renders:
- Agent chip: `chat-switch-participant-button` (avatar + name)
- Version selector: `chat-version-selector-trigger` (version string)

These are two adjacent elements in the composer, not a single combined component. This is the correct/current product behavior (confirmed via ELITEA-2361 exploration).

---

### Step 8 — Verify settings icon/button is visible on or near the agent chip

**Action:** Inspect the agent chip and adjacent elements for a settings icon or button

**Expected Result:** A settings icon or button is visible on the agent chip
- Currently identified as: a `<button>` element with `aria-label="agent settings menu"`
- Rendered as part of a MuiButtonGroup (grouped horizontal layout)
- Icon is visible (currently an SVG or MUI icon within the button)
- Clickable; opens an agent settings menu when clicked

**Handle (current):** `[aria-label="agent settings menu"]`

**Handle (recommended — needs implementation):** `[data-testid="chat-participant-settings-button"]` or similar

**Provenance:** on-automation/testids — NEEDS TESTID (currently missing)

**Observable:** Settings button/icon is present and clickable; user can interact with it to modify agent settings within the conversation

**DEFECT/GAP:** The settings icon does not yet carry a stable `data-testid` attribute. Current handle relies on `aria-label` only. Per the team's testid-only locator policy, a testid should be added (e.g., `chat-participant-settings-button`) or a reasonable fallback agreed upon.

---

## Coverage Map

| Case Element | Expected Result | Covered By | Asserted | Disposition |
|---|---|---|---|---|
| Navigate to Agent Hub | Catalog page loads | Steps 1 | Page heading visible, URL = `/elitea-catalog` | ✓ Ready |
| Click agent card | Detail modal opens | Step 2 | Modal is visible with agent details | ✓ Ready |
| Click Start Chat | Chat page loads | Step 3 | URL changes to `/chat*`, agent pre-populated | ✓ Ready |
| Agent chip visible | Chip is visible in message input | Step 4 | `chat-switch-participant-button` visible | ✓ Ready |
| Avatar/icon visible | Avatar is rendered on chip | Step 5 | `<img alt="elitea">` is visible | ✓ Ready |
| Agent name visible | Agent name text is displayed | Step 6 | Text matches selected agent | ✓ Ready |
| Agent version visible | Version string is displayed | Step 7 | `chat-version-selector-trigger` shows version | ✓ Ready |
| Settings icon visible | Settings icon is visible on/near chip | Step 8 | `[aria-label="agent settings menu"]` is visible | ⚠️ Ready (needs testid) |

---

## Concrete Handles

| Element | Primary Selector | Fallback | Provenance | Status |
|---|---|---|---|---|
| Catalog page heading | `[data-testid="catalog-page-heading"]` | `text="Welcome to ELITEA Catalog"` | on-main ✓ (ELITEA-2075) | ✓ |
| Catalog agent card (any) | `[data-testid^="catalog-agent-card-"]` | nth card selection | on-main ✓ (ELITEA-2075) | ✓ |
| Agent modal start chat button | `[data-testid="catalog-agent-modal-start-chat-button"]` | `button:text("Start Chat")` | on-main ✓ (ELITEA-2075) | ✓ |
| Agent chip (in composer) | `[data-testid="chat-switch-participant-button"]` | none (testid required) | on-automation/testids ✓ (ELITEA-2361) | ✓ |
| Agent avatar image | `[data-testid="chat-switch-participant-button"] img[alt="elitea"]` | parent `img[alt]` | on-automation/testids ✓ | ✓ |
| Agent name text | `[data-testid="chat-switch-participant-button"] span` | `.text_content()` contains name | on-automation/testids ✓ | ✓ |
| Version selector | `[data-testid="chat-version-selector-trigger"]` | none (testid required) | on-automation/testids ✓ (ELITEA-2361) | ✓ |
| Settings icon/button | `[aria-label="agent settings menu"]` | **NEEDS testid** (e.g., `chat-participant-settings-button`) | NO testid (aria-label only) | ⚠️ Needs work |

---

## Known Defects & Notes

### [#1042] Case text drift: "Start Conversation" vs. "Start Chat"
- **Issue:** Case text and TMS family names use "Start conversation", but the live product label is "Start Chat"
- **Impact:** Minimal — the button is easily identifiable by both text and testid
- **Status:** Already filed; do not re-file
- **Mitigation:** Assert using testid (`catalog-agent-modal-start-chat-button`) rather than text

### [#1212] Case text drift: Missing "reload category items" icon
- **Issue:** Unrelated to this case, but part of the same Agent Hub family — mentioned for context
- **Status:** Already filed; not relevant to ELITEA-2362

### Settings icon missing stable testid (IMPLEMENTATION WORK)
- **Current state:** Settings button identified by `aria-label="agent settings menu"` only
- **Locator policy:** Team requires `data-testid` on all interactive elements
- **Recommendation:** Add `data-testid="chat-participant-settings-button"` to the settings button in `ChatBox.jsx` or the chat composer component
- **Implementer action:** Resolve via `add-data-testid` skill or manual JSX edit

---

## Assertions to Implement

### Pre-conversation setup
- [ ] Navigate to `/elitea-catalog` → page loads with `catalog-page-heading` visible
- [ ] Catalog contains at least one agent card visible (e.g., `catalog-agent-card-31` for Business Analyst)

### Start conversation flow
- [ ] Click an agent card → modal opens
- [ ] Modal displays agent name in heading
- [ ] Modal displays "Start Chat" button (testid: `catalog-agent-modal-start-chat-button`)
- [ ] Click "Start Chat" → navigate to `/chat*`
- [ ] Chat page loads; agent is pre-populated as a participant

### Verify agent chip
- [ ] Agent chip is visible: `[data-testid="chat-switch-participant-button"]` is visible
- [ ] Avatar is visible: `img[alt="elitea"]` exists within the chip
- [ ] Agent name matches selected agent (get text from chip span, assert === "Business Analyst" or expected name)
- [ ] Version selector is visible: `[data-testid="chat-version-selector-trigger"]` is visible
- [ ] Version text matches expected format (e.g., "v2.1" or "v1.0")
- [ ] Settings icon is visible: `[aria-label="agent settings menu"]` is visible
- [ ] Settings button is clickable (can be clicked without errors)

### Optional (behavioral, not case-scoped)
- [ ] Clicking settings icon opens a settings/options menu
- [ ] Clicking version selector opens a version-selection dropdown

---

## Test Data & Cleanup

### Setup
- No explicit setup required beyond login
- Use `auth_state` fixture to bypass Keycloak login on localhost
- Catalog loads default Trending agents automatically

### Preconditions (verified live)
- "Business Analyst" (id 31) is available in the Catalog
- "User Story Creator" (id 172) is available in the Catalog
- Both agents have configured versions (e.g., `v2.1`, `v0.1`)
- Both agents are searchable and clickable

### Cleanup
- No persistent side effects; a new conversation is created but can be left as-is
- If cleanup is required: delete the created conversation via `ConversationAPI.delete_conversation(conversation_id)` parsed from the chat page URL

---

## Evidence

| File | Step | Purpose |
|---|---|---|
| `test-results/screenshots/ELITEA-2362-step-01-catalog.png` | 1 | Catalog page layout, Trending agents visible |
| `test-results/screenshots/ELITEA-2362-step-02-modal-opened.png` | 2 | Agent detail modal opened |
| `test-results/screenshots/ELITEA-2362-step-03-chat-page.png` | 3 | Chat page after navigation |
| `test-results/screenshots/ELITEA-2362-step-03-full-analysis.png` | 4–8 | Agent chip visible, elements identified |
| `test-results/screenshots/ELITEA-2362-step-04-input-area.png` | 4–8 | Focused view of message input area and agent chip |
| `test-results/screenshots/ELITEA-2362-settings-icon.png` | 8 | Settings icon/button (MuiButtonGroup element) |
| `test-results/screenshots/ELITEA-2362-final-state.png` | 8 | Full page state with all elements visible |

---

## Summary

✓ **Execution complete.** All case steps executed against `localhost:5173` on 2026-08-10.

- Agent chip is visible in the message input area with avatar, agent name, version selector, and settings icon.
- All primary handles are stable and testid-backed (except settings icon, which needs a testid added).
- No blocking defects found; one testid gap identified for implementer work.

**Status:** `ready-for-automation`

**Implementer priority:**
1. Add `data-testid="chat-participant-settings-button"` (or similar) to the settings icon button
2. Write test assertions per the "Assertions to Implement" section above
3. Reuse existing `ChatPage` page-object methods and fixtures for chat navigation/waits
