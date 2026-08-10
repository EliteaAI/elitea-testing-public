---
status: ready-for-automation
priority: medium
type: functional
tms_id: ELITEA-2359
title: "Agent Hub — copy link from agent detail modal navigates to agent"
---

# ELITEA-2359: Agent Hub — copy link from agent detail modal navigates to agent

**Priority:** medium · **Type:** functional · **Status:** ready-for-automation

**Objective:** Verify that a link copied from the Agent Hub catalog modal's Share action successfully navigates to the agent and displays all agent details (name, description, conversation starters, welcome message) correctly in the reopened modal.

---

## Preconditions

- User is logged in to Elitea platform
- Agent Hub Catalog page (`/elitea-catalog`) is accessible
- At least one published agent exists in the catalog

---

## Test Flow & Concrete Handles

### Step 1 — Navigate to Agent Hub Catalog
**Action:** Navigate to `/elitea-catalog`
**Expected:** Catalog page loads with agent cards visible in the main content area; tab bar shows "Agents" (selected) and "Skills" tabs

**Handles:**
- Page URL: `http://localhost:5173/elitea-catalog`
- Agent cards: `[data-testid="catalog-agent-card-{id}"]` (e.g., `catalog-agent-card-275` for Entertainer Agent with id=275)
- Agent card name text within card: accessible via `getByText('Entertainer Agent')`

---

### Step 2 — Click an agent card to open modal
**Action:** Click any agent card (e.g., "Entertainer Agent")
**Expected:** Detail modal opens as a dialog overlay; modal displays:
  - Agent name (heading) with author avatar
  - Like button (currently showing like count, e.g., "0")
  - Overflow menu button
  - Close button (X icon)
  - Agent icon/image
  - Agent name and description below
  - "Show instructions" link (if instructions exist)
  - CHAT STARTERS section with clickable conversation starter chips
  - Welcome Message section with message text
  - "Start Chat" button at bottom

**Handles:**
- Modal dialog: `[active]` attribute, accessible via `dialog` role
- Agent name in modal heading: text content, accessible via `getByText(agent_name)`
- Like button: existing testid `catalog-agent-modal-like-button` OR `data-liked="true/false"` state attribute
- Menu button: `[data-testid="agent-hub-modal-menu-button"]`
- Close button: `aria-label="close"` or button text "close"
- Description text: accessible via card's text content
- Chat starters: chips within the modal, clickable
- Welcome Message text: visible in modal body
- Start Chat button: `[data-testid="catalog-agent-modal-start-chat-button"]`

---

### Step 3 — Click overflow menu button
**Action:** Click the overflow menu button (three-dot icon) in modal header
**Expected:** Menu dropdown opens with three options: "Export", "Fork", "Share"

**Handles:**
- Menu button: `[data-testid="agent-hub-modal-menu-button"]`
- Overflow menu: `menu` role
- Menu items: `menuitem` role with text labels
  - Export option: `[data-testid="export-agent-menuitem"]` (text "Export")
  - Fork option: `[data-testid="fork-agent-menuitem"]` (text "Fork")
  - Share option: `[data-testid="share-agent-menuitem"]` (text "Share")

---

### Step 4 — Click Share to copy link
**Action:** Click "Share" menu item
**Expected:** 
  - Link is copied to clipboard (no visible dialog appears, action is immediate)
  - Success notification appears in top-right area with message "The link has been copied to the clipboard"
  - Notification auto-dismisses after ~3-5 seconds OR can be dismissed via close button

**Handles:**
- Share menu item: `[data-testid="share-agent-menuitem"]`
- Success notification: `alert` role with text "The link has been copied to the clipboard"
- Notification close button: button within the alert
- Copied URL format: `http://localhost:5173/elitea-catalog?tab=agents&agentId={agent_id}`
  - Example: `http://localhost:5173/elitea-catalog?tab=agents&agentId=275` (Entertainer Agent)

---

### Step 5 — Open a new browser tab and navigate to copied URL
**Action:** Open a new browser tab, paste the copied URL into the address bar, and press Enter
**Expected:** 
  - URL resolves without errors
  - Catalog page loads (or auto-navigates)
  - Agent detail modal for the shared agent opens automatically
  - Modal shows the same agent as before

**Handles:**
- Target URL (as observed): `http://localhost:5173/elitea-catalog?tab=agents&agentId={agent_id}`
- Page waits for modal to render (via condition waits, not fixed sleep)

---

### Step 6 — Verify agent details in reopened modal
**Action:** Inspect the opened modal to confirm all agent information is present
**Expected:** Modal displays:
  - Agent name: "Entertainer Agent" (or the shared agent's actual name)
  - Agent description: Full description text
  - Chat Starters section: All conversation starters displayed and clickable
  - Welcome Message: Full welcome message text
  - Like button with current like count
  - Start Chat button

**Example data (Entertainer Agent, id=275):**
- Name: "Entertainer Agent"
- Description: "An entertaining conversational agent designed to engage users with playful responses, jokes"
- Chat Starters:
  - "Tell me a clean animal joke."
  - "Give me a funny robot joke."
  - "Play a quick riddle game with me."
- Welcome Message: "Hey! I'm your Entertainer Agent — here to make things fun with jokes, mini-games, silly prompts, and creative surprises. Want a joke, a riddle, a tiny story, or a random fun challenge?"

**Handles:**
- Modal: `dialog` role with `[active]` attribute
- Agent name: text content in heading
- Description: `generic` or `text` element within modal body
- Chat starters: `generic` elements with `[cursor=pointer]` attribute, clickable text
- Welcome Message: labeled section with heading "Welcome Message" + text content below
- All text content: `getByText(exact_text)` or substring match via `getByText(partial_pattern)`

---

## Coverage Map

| Case Element | Expected Result | Covered by | Asserted where | Disposition |
|---|---|---|---|---|
| Navigate to Catalog page | Page loads; agent cards visible | Step 1 | Page loads with agent cards rendered | ✅ Pass |
| Click agent card | Modal opens with agent details | Step 2 | Modal dialog visible with agent name, description, starters, welcome message | ✅ Pass |
| Overflow menu renders | Menu opens with Export/Fork/Share options | Step 3 | Menu items found and clickable | ✅ Pass |
| Share action copies link | Success notification appears; URL copied to clipboard | Step 4 | Notification text "The link has been copied to the clipboard" observed; URL captured via monkey-patch = `http://localhost:5173/elitea-catalog?tab=agents&agentId=275` | ✅ Pass |
| Navigate to copied URL | Page loads; modal reopens automatically for the same agent | Step 5–6 | Modal opens on navigation; agent name "Entertainer Agent" matches | ✅ Pass |
| Verify agent name displayed | Name matches original agent | Step 6 | Modal heading and body text match "Entertainer Agent" | ✅ Pass |
| Verify description displayed | Full description shown | Step 6 | Description text visible in modal | ✅ Pass |
| Verify conversation starters displayed | All starters visible and clickable | Step 6 | Chat starters section renders with all items | ✅ Pass |
| Verify welcome message displayed | Full message shown | Step 6 | Welcome message text visible in modal | ✅ Pass |

---

## Additional Observations

- **URL format:** The copied URL uses a query parameter structure (`?tab=agents&agentId={id}`) rather than a path-based structure (e.g., `/agents/all/{id}`). This is specific to the catalog modal; different from agent detail pages at `/agents/all/{id}`.
- **Modal auto-open:** Navigating directly to the catalog URL with the `agentId` query parameter automatically opens the agent detail modal without requiring a manual card click.
- **Navigation behavior:** The browser's navigation to the URL is instantaneous; modal rendering follows immediately without a noticeable page reload hop (unlike some entity-link cases that perform hard reloads).
- **Notification behavior:** The success toast notification displays briefly and auto-dismisses; no user action needed to clear it.
- **No defects encountered:** Case executed cleanly; all steps produced expected results without errors or console issues.

---

## Known Defects

None encountered during this execution.

---

## Test Data & Fixtures

**Agent used in analysis:** Entertainer Agent (id=275, owned by Oleksandr Chornyi3)
- This is a pre-existing agent in the public catalog of project `Private` (id=399)
- Can be referenced by ID or looked up by name in the catalog

**No test data creation required:** Analysis used existing published agents from the catalog.

---

## Automation Notes

- **Clipboard handling:** During exploratory testing, direct `navigator.clipboard.readText()` failed with permission denial. Workaround used: monkey-patch `navigator.clipboard.writeText()` before the Share action to capture the URL into `window.copiedUrl` (non-prod workaround; use Playwright context permissions `grantPermissions(['clipboard-read', 'clipboard-write'])` before click in actual tests).
- **Wait strategy:** After navigating to the copied URL, wait for the modal to be visible (condition-based) rather than a fixed delay; modal may render within 500–1000ms depending on network/rendering latency.
- **Browser context isolation:** Each new navigation should use a fresh or isolated page context to avoid clipboard state carrying over from prior clicks.

