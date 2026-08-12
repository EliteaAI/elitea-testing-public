---
title: "Agent Hub — empty state when no agents match filter or search"
priority: p2
type: functional
case_id: ELITEA-2367
afs_version: 1.0
module: agent-hub
status: ready-for-automation
classification: empty-state-verification
execution_type: automated
tags: [automated:UI:regression, feat:agent-hub]
---

# ELITEA-2367 — Agent Hub — empty state when no agents match filter or search

**Priority:** p2 · **Type:** functional · **Module:** agent-hub · **Surface:** UI (Agents listing page `/agents/all?viewMode=owner`)

**Objective:** Verify that the Agent Hub empty state renders correctly and displays consistent layout when no agents match a filter or search query.

---

## Preconditions

- User is logged in to the Elitea platform (`${TEST_USER}`)
- At least one agent exists in the project (baseline state)
- Target: `http://localhost:5173/agents/all?viewMode=owner` (Agents page, card-list view)

---

## Test Data

| Field | Value |
|-------|-------|
| Search term for no matches | `DEFINITELYNONEXISTENTTERM` (or any string confirmed not to match existing agent names) |
| Filter category with no agents | (To be determined via UI exploration; see § Known Issues) |

---

## Test Scope & Steps

### Step 1 — Navigate to Agent Hub (Agents listing page)

**Action:** Navigate to `/agents/all?viewMode=owner`

**Expected Result:**
- Page title: `"Agents: all - <project_name>"`
- URL: `http://localhost:5173/agents/all?viewMode=owner`
- Main content area displays agent cards in card-list view (button-pressed state on the "Card list view" toggle)
- Search input visible in the right panel with placeholder text "Let's find something amazing!"
- Right panel also shows "Tags" section (initially "No tags to display.")
- Agent count in the right-panel footer shows "Agents: 19" (or the current project's total)

**Concrete Handles:**
- Page heading: `generic` with text "Agents"
- View toggle group: `group "Small View Toggler"` with two buttons: "Table view" (unpressed) and "Card list view" (pressed by default on this run)
- Search input: `textbox "search"` with `placeholder="Let's find something amazing!"`
- Agent cards container: `generic [ref=f11e165]` with child `generic` nodes, each representing an agent card
- Right panel Tags section: `generic [ref=f11e192]` containing "Tags" heading and tag list

### Step 2 — Apply search filter with term matching no agents

**Action:** Type `DEFINITELYNONEXISTENTTERM` into the search input (`textbox "search"`)

**Expected Result:**
- Search input fills with the term (text is visible in the input field)
- Autocomplete/suggestion tooltip may appear showing "No Agents Match" as an option (observed in live run)
- **Main content area: all agent cards disappear; empty state is displayed instead**
- Empty state shows:
  - A clear "No agents found" or equivalent message
  - A helper message (e.g., "Try adjusting your search terms") as specified in case Step 4
  - Layout remains consistent with no broken UI elements (no misaligned text, no orphaned buttons, etc.)
  - Right panel structure remains intact (visible but showing empty/no-match states)

**Concrete Handles (to be discovered during implementation):**
- Search input active state: `textbox "search" [active]`
- Empty state container: TBD — search for `role="status"` or `aria-live="polite"` if present; otherwise a `generic` div containing the empty-state message
- Empty state message text: `"No agents found"` or similar (exact wording TBD)
- Helper message text: TBD (case text says "Try adjusting your search terms" but live wording may differ)
- Clear/reset buttons: TBD (may include an X icon to clear the search, `data-testid` pattern TBD)

### Step 3 — Verify layout consistency (no broken UI elements)

**Action:** Examine the rendered empty state for visual/structural integrity

**Expected Result:**
- No console errors (checked via browser console)
- No missing/orphaned elements (e.g., floating buttons, misaligned text)
- Right panel structure still visible (Tags heading, filter controls)
- Agent card grid area shows only the empty-state content, no partial card renders
- Empty state message is center-aligned and legible
- Helper message is visible below the main message (if present)

**Concrete Handles:**
- Browser console for errors: use `browser_console_messages()` to capture errors
- Right panel visibility: confirm `generic [ref=f11e187]` (right panel) is still in DOM
- Card grid empty state: confirm main content area (`generic [ref=f11e165]`) contains ONLY empty-state content, no agent cards

### Step 4 — Clear search and verify agents reappear

**Action:** Click the clear/reset button (X icon) in the search input, or select-all and delete the search term

**Expected Result:**
- Search input clears
- Agent cards reappear in the main content area
- Layout returns to the initial state (Step 1)
- No console errors during the transition

**Concrete Handles:**
- Clear button: `generic [ref=f11e603]` or `generic [ref=f11e606]` (observed as clickable clear/reset icons next to the search input in snapshots)
- Agent cards reappear: verify first agent card `generic [ref=f11e214]` (or similar) is back in the DOM
- Right panel footer count: confirms "Agents: 19" (or the total) is still displayed

---

## Coverage Map — Case Elements → Expected Results

| Case Element | Expected Observable | AFS Step Coverage | Handle / Assertion | Disposition |
|---|---|---|---|---|
| Navigate to Agent Hub | Page loads, agents displayed | Step 1 | URL + page title + agent cards visible | ready-for-automation |
| Apply category filter that has no agents | Empty state displays | Step 2 (variant: filter vs. search) | TBD (filter mechanism not yet discovered) | clarification (see § Known Issues) |
| Type search term matching no agents | Empty state displays | Step 2 | Search input + empty state message visible | ready-for-automation |
| "No agents found" message displayed | Text visible in main content area | Step 2 | `role="status"` or empty-state container with message text | ready-for-automation |
| Helper message appears ("Try adjusting...") | Text visible below main message | Step 2 | Empty-state helper text handle (TBD) | clarification (exact wording TBD) |
| Layout remains consistent, no broken UI | Visual/structural integrity | Step 3 | Console error check + right panel visibility + grid empty state | ready-for-automation |
| Clear search, agents reappear | Return to initial state | Step 4 | Clear button click + agent cards reappear + right panel count | ready-for-automation |

**Axis 2 — Observables Beyond Case Scope:**
- Browser console remains error-free during all transitions (no 4xx/5xx visible in network tab for the agents list API call when empty results are fetched) — confirms filter is applied cleanly on the backend or client-side without infrastructure defects.

---

## Known Issues & Gaps

### Clarification: Filter mechanism for "category filter that has no agents"

**Finding:** Case Step 2 mentions "Apply a category filter that has no agents" as an alternative to search. The live Agent Hub page (`/agents/all?viewMode=owner`) does show a Tags panel on the right (initially "No tags to display."), but the mechanism for selecting a specific tag/category filter that results in zero agents is **not yet explored**. 

**Status:** The case text may be referring to:
1. A UI control (e.g., tag-filter chips) that is not visible in the initial page state and requires scrolling or interaction
2. A secondary filter applied via the Categories/TrendingAuthors component in the right panel (which does carry tag-list data, per `PrivateAgentsList.jsx`)
3. Or the case intent may be to test EITHER a category filter OR search (the "OR" is an exclusive choice, not a requirement to test both)

**Recommendation:** 
- If tag/category filters are discoverable and testable on the `/agents/all` page, add a parallel Step 2b to test the category-filter variant.
- If the tags panel is non-interactive or hidden, this case's automation focuses on the search variant (Step 2), and the category-filter case (ELITEA-2368 or a separate TMS case) should be filed as a followup.

**Resolution:** Treated as `ready-for-automation` under the assumption that the search-variant (Step 2 as written) is the primary, automatable flow; category-filter variant deferred to separate case if required.

### TBD: Exact empty-state message text

**Finding:** Case text specifies `"No agents found"` message and a helper message "Try adjusting your search terms", but live wording may differ (common pattern: "Nothing found. Create yours now!" per `PrivateAgentsList.jsx` code, lines 55–61). 

**Status:** Implementer should capture the ACTUAL text rendered in the empty state and verify it matches case intent (a clear, actionable message guiding the user to refine search or create new agents).

---

## Implementation Hints

### Locator Strategy

- **Search input:** use `input[placeholder*="find something amazing"]` or look for `data-testid` on the textbox if wired (not found in initial snapshots, but may be added post-AFS)
- **Empty-state message:** search for `role="status"` or `aria-live` regions; fallback to a container with text matching "No agents found" or "Nothing found"
- **Clear button:** identified as clickable `generic` elements next to the search input in snapshots (test both `[ref=f11e603]` and `[ref=f11e606]`)
- **Agent cards:** each card is a `generic [ref=f11e###]` child of the main content area container; when empty, this container should contain ONLY the empty-state UI, no card generics

### Data Flow

- Search is **live/reactive** (debounced, ~300ms per source code `useDebounceValue(query, 300)`) — no Enter key needed, but waits for debounce are recommended before asserting empty state
- Backend API call: `GET /api/v2/elitea_core/applications/prompt_lib/{projectId}?query={searchTerm}&...` (endpoint from case exploration; capture full URL per implementation)
- Empty state may be **client-side (no results in response) or server-side (empty array returned)** — both are valid; verify via network capture

### Waits

- Wait for debounce: use a 500–1000ms buffer after typing (debounce is 300ms, plus network latency)
- Wait for empty-state message: use `browser_wait_for(text="No agents found")` or equivalent
- Network-based wait: listen for the agents-list API response and verify it contains `total: 0` or empty `rows` array

### Assertions

- Primary: empty-state message text is visible and readable
- Secondary: no agent cards render (verify card count = 0)
- Tertiary: right panel remains visible and interactive (Tags section, clear button)
- Quaternary: browser console has no errors during the empty-state transition

---

## Preconditions & Test Data Verification

- **Agent count:** live project has 19 agents (confirmed from right-panel footer); search term `DEFINITELYNONEXISTENTTERM` guaranteed to match zero agents
- **Auth state:** user is logged in as `${TEST_USER}` (test fixture account with admin-equivalent permissions in project 399)
- **Isolation:** no parallel tests modifying agent data during this case execution

---

## Pass/Fail Criteria

**Pass:**
- Empty-state message displays in the main content area when no agents match the search
- Helper message (or equivalent guidance) is visible
- Layout remains consistent with no broken UI elements
- Clearing the search returns agents to view
- No console errors at any step

**Fail:**
- Empty-state message does NOT display (agents ghost-hide or error occurs)
- Layout breaks (orphaned buttons, misaligned text, right panel disappears)
- Console errors appear during search/clear transitions
- Clearing search does NOT restore agents to view
- Any of the expected UI states/validations is not observed

---

## Notes for Implementer

- This is a **happy-path empty-state validation** — no error injection or network failures are tested here
- The case text's mention of "layout consistency" is asserting that the empty state is a *valid, designed state*, not a broken/degraded one — confirm via visual inspection + structure checks
- Future variants (ELITEA-2368+) may test edge cases: single-character search, search with spaces, rapid search changes, etc.
- The right-panel Tags section behavior during empty state is documented in the `_surface.md` digest (ELITEA-2358/2359); reuse that for handle discovery if tags become filterable

---

## AFS Metadata

- **Surface:** `/agents/all?viewMode=owner` (Agents listing page, card-list view)
- **Priority:** p2 (medium — empty states are important UX but not critical to core functionality)
- **Classification:** empty-state-verification
- **Automation:** UI only (no API-level setup required; uses existing test fixture agents)
- **Flakiness Risk:** low (empty state is deterministic; search is debounced with stable waits)
- **Estimated Test Duration:** ~10–15 seconds per run (search delay + wait for empty state + clear + wait for restore)
