# Test Case: Agent Hub — open agent detail modal

## Metadata
- **TMS ID**: ELITEA-2356
- **Linked Story**: none (case `requirements: []`)
- **Priority**: l3 (case priority: medium)
- **Environment Explored**: local (`http://localhost:5173/elitea-catalog`, EliteaUI `automation/testids`, DEV backend; sidebar project selector reads "Project: Private" by default for `${TEST_USER}` — no explicit project switch needed)
- **User set**: `${TEST_USER}` — on localhost, `auth_state`/`VITE_DEV_TOKEN` skips explicit Keycloak login
- **Analyst**: qa-engineer (agent)
- **Status**: **ready-for-automation** — case executed end-to-end live via Playwright MCP. All 7 steps reproduced live (screenshot: `test-results/screenshots/ELITEA-2356-step-04-modal-open.png`). Zero console errors, zero 4xx/5xx. Two case-text drifts (CLARIFICATION, both already/now tracked — see § Known Defects). Six `testid needed` gaps on elements this case's own steps touch (agent icon, owner name, like button, close button, description, and each of the two content sections) — implementer work via `add-data-testid`; none are fallback-worthy per project locator policy.
- **Related surfaces reused**: `AgentHubPage` (`automation/pages/agent_hub_page.py`) already covers Catalog navigation, search, agent-card lookup (`open_agent_by_name()`, `get_agent_card()`) and three of the modal's fields (`modal_agent_name`, `modal_show_instructions_link`, `modal_start_chat_button` — all pre-existing testids). **Not a target for `extend-existing`**: the only merged spec that opens this same modal is `test_agent_hub_participant_readonly_canvas_llm_override.py` (ELITEA-2075, `automation/tests/ui/chat/`), and it asserts exactly ONE of this case's nine observables (the agent-name text, `agent_hub.modal_agent_name.text_content()` — `automation/tests/ui/chat/test_agent_hub_participant_readonly_canvas_llm_override.py:135-138`) before immediately clicking "Start Chat" and moving on into the chat/canvas flow. It never asserts the icon, owner name, liked status, overflow/copy-link menu, close button, description, CHAT STARTERS section, or WELCOME MESSAGE section — eight of nine case elements are unasserted there. That gap is not "a small number of assertions missing" (the `extend-existing` boundary call in `test-case-analysis/SKILL.md` § 5); it is nearly the entire case, and this case's own flow is also materially different in STEPS (stops at the modal — never starts a chat, never needs conversation cleanup) rather than merely different DATA. Genuinely fresh, narrow coverage: `ready-for-automation`.

## Preconditions
- User is logged in to the Elitea platform (`${TEST_USER}` / dev-auth on localhost).
- Active project context is "Private" (this project's default `${TEST_USER}` project on localhost).
- At least one published Catalog agent exists. Confirmed live: **"User Story Creator"** (application id 172, author "Levon Dadayan", 0 likes, description "Thuis agent is responsible for creating proper user stories accordingly using provided user_template.md which is included in sub-agent." [sic — a typo in the agent's own author-authored description field, live product data, not a UI defect], no conversation starters, no welcome message set). Matches the case's own "e.g." example verbatim. If this specific agent is later renamed/removed, any published Catalog agent exercises the same code path (component review confirms the rendering logic is generic, not agent-specific).

## Test Data

### reuse-existing
- `${TEST_USER}` — see `.agents/profile.md` § Roles & sample users.
- Catalog agent: **"User Story Creator"** (case's own "e.g." example — confirmed present live, application id 172).

(No other test data required — case's own Test Data table says "(none required)".)

## Test Steps

1. Navigate to Agent Hub (`/elitea-catalog`).
   - **Verify**: page loads — `catalog-page-heading` visible (reuse `AgentHubPage.navigate()` / `wait_for_page_load()`).
2. Click on any agent card (e.g., "User Story Creator").
   - **Verify**: click succeeds; the underlying `GET /api/v2/elitea_core/public_application/prompt_lib/{id}` request fires (confirmed live: `.../public_application/prompt_lib/172` → `200`) — reuse `AgentHubPage.open_agent_by_name()`, which already waits on this exact response before returning.
3. Verify the agent detail modal opens as an overlay.
   - **Verify**: a MUI `Dialog` (`role="dialog"`) becomes visible over the Catalog page content — confirmed live.
4. Verify the modal displays agent icon, agent name, owner name, liked status, copy link icon, "x" button and description.
   - **Verify — agent icon**: `EntityIcon` renders inside the modal content area, above the name (confirmed live: default "elitea" branded icon for an agent with no custom `icon_meta`) — **testid needed**: `catalog-agent-modal-agent-icon` (the underlying `EntityIcon` component already accepts a `data-testid` prop and renders it on its own root `Box` — `EliteaUI/src/components/EntityIcon.jsx:203`; AgentModal.jsx's call site (`EliteaUI/src/[fsd]/features/agent-hub/ui/AgentModal.jsx:222-227`) currently passes none).
   - **Verify — agent name**: `catalog-agent-modal-agent-name` (pre-existing testid) reads "User Story Creator" — confirmed live.
   - **Verify — owner name**: a `Typography` reading "Levon Dadayan" renders next to the author avatar in the modal header (`AgentModal.jsx:190-195`, `{cardAuthors[0]?.name || 'Author'}`) — confirmed live — **testid needed**: `catalog-agent-modal-owner-name`.
   - **Verify — liked status**: an icon+count button (heart icon, count "0") renders in the modal header (`AgentHubLike`/`Like.jsx`, `AgentModal.jsx:198-201`) — confirmed live, but **currently threads NO `testId` prop at all** (unlike the card-list-view like button, which does thread one — `catalog-agent-like-button-{id}`, ELITEA-2354). **Testid needed**: thread `testId="catalog-agent-modal-like-button"` into the `<AgentHubLike>` call in `AgentModal.jsx:198-201` (static, not per-id — only one modal instance renders at a time, so no disambiguation risk vs. the card grid's own `catalog-agent-like-button-{id}` testids, which use a different prefix). Once threaded, `Like.jsx` automatically derives `data-liked="true"/"false"` from the same `testId` presence (`Like.jsx:66`, same precedent as the card-list like button) — assert `data-liked="false"` for this case's 0-like agent.
   - **Verify — copy link icon**: **CASE-TEXT DRIFT (CLARIFICATION, filed — see § Known Defects)**: there is no standalone copy-link icon in the modal header. What's there is an overflow ("...", three-dot) menu button — `agent-hub-modal-menu-button` (**pre-existing testid**, `AgentHubModalMenu.jsx`) — confirmed live, visible next to the like button. Opening it (out of scope for this case — a sibling case, ELITEA-2359/#867, exercises the actual copy-link action) reveals Export/Fork/Share items, where "Share" performs the copy-to-clipboard action. This case asserts the overflow menu button's visibility only.
   - **Verify — "x" button**: an icon-only `IconButton` with `aria-label="close"` renders at the top-right of the modal header (`AgentModal.jsx:208-216`) — confirmed live — **testid needed**: `catalog-agent-modal-close-button` (closing it is out of scope for this case — a sibling case, ELITEA-2357/#865, exercises the close action itself).
   - **Verify — description**: a `Typography` renders the agent's description text below the name (`AgentModal.jsx:236-241`) — confirmed live, reads "Thuis agent is responsible for creating proper user stories accordingly using provided user_template.md which is included in sub-agent." (agent-authored content, not app-generated text — the typo is live product DATA, not a rendering defect; assert non-empty/visible, not the literal string, so the assertion doesn't silently start failing on unrelated content edits) — **testid needed**: `catalog-agent-modal-description`.
5. Verify the modal shows a "CONVERSATION STARTERS" section.
   - **CASE-TEXT DRIFT (CLARIFICATION, already tracked — see § Known Defects)**: the live section header literally renders **"CHAT STARTERS"**, not "CONVERSATION STARTERS" (`AgentConversationStarters.jsx`, `<Typography variant="subtitle">CHAT STARTERS</Typography>`) — confirmed live, and already documented for this exact sibling-case family in [EliteaAI/elitea-testing-public#1042](https://github.com/EliteaAI/elitea-testing-public/issues/1042) (filed from ELITEA-2092, explicitly names ELITEA-2356 as an affected sibling). Not re-filed.
   - **Verify**: the section container is visible, showing "CHAT STARTERS" as the header and (for this 0-starter agent) the empty-state text "No predefined chat starters – just type your request to begin." — confirmed live — **testid needed**: `catalog-agent-modal-chat-starters-section` on the section's container `Box` (`AgentConversationStarters.jsx`, currently has none).
6. Verify the modal shows a "WELCOME MESSAGE" section.
   - **Verify**: the section container is visible, showing "Welcome Message" as the header (note: NOT all-caps in the live product, unlike the "CHAT STARTERS" header above — a minor casing nuance, not itself worth a separate ticket) and (for this agent, which has no welcome message set) the empty-state text "No welcome message set – the agent will start without a greeting." — confirmed live — **testid needed**: `catalog-agent-modal-welcome-message-section` on the section's container `Box` (`AgentWelcomeMessage.jsx`, currently has none).
7. Verify the "Start conversation" button is visible at the bottom of the modal.
   - **CASE-TEXT DRIFT (CLARIFICATION, already tracked — see § Known Defects)**: the live button reads **"Start Chat"**, not "Start conversation" (`AgentModal.jsx:260-268`) — confirmed live, already documented in [#1042](https://github.com/EliteaAI/elitea-testing-public/issues/1042) (same ticket as step 5's drift). Not re-filed.
   - **Verify**: `catalog-agent-modal-start-chat-button` (**pre-existing testid**, `AgentHubPage.modal_start_chat_button`) is visible, in the modal's fixed `DialogActions` footer (not the scrollable content area) — confirmed live, matches the case's own "visible at the bottom of the modal" wording exactly. This case does NOT click it (starting a conversation is a materially different, already-tracked sibling case — ELITEA-2360/#868 — and clicking here would also risk the known race-condition defect [#1043](https://github.com/EliteaAI/elitea-testing-public/issues/1043), which only matters to cases that actually click it).

## Expected Results
- Clicking any Catalog agent card opens the agent detail modal as an overlay.
- The modal displays: agent icon, agent name, owner name, liked status (heart icon + count), an overflow menu containing the copy-link/Share action, a close ("x") button, and the agent's description.
- The modal shows a CHAT STARTERS section (case text: "CONVERSATION STARTERS" — drift, see above) and a Welcome Message section (case text: "WELCOME MESSAGE" — casing drift only).
- The "Start Chat" button (case text: "Start conversation" — drift, see above) is visible at the bottom of the modal.
- Zero console errors, zero 4xx/5xx.

## Coverage Map

### Axis 1 — Case coverage

| Case element | Expected result | Covered by (AFS step) | Asserted where | Disposition |
|---|---|---|---|---|
| 1 Navigate to Agent Hub | Target page/section loads successfully | step 1 | `catalog-page-heading` visible | asserted |
| 2 Click on any agent card | Control responds; expected next state is shown | step 2 | agent-details GET fires, resolves 200 | asserted |
| 3 Verify the agent detail modal opens as an overlay | Condition holds as described | step 3 | dialog visible | asserted |
| 4 Verify modal displays icon, name, owner, liked status, copy link icon, "x" button, description | Condition holds as described | step 4 | 7 sub-elements, each own handle (see step 4 detail) | asserted *(copy-link-icon sub-element is drift, see clarification)* |
| 5 Verify "CONVERSATION STARTERS" section | Condition holds as described | step 5 | `catalog-agent-modal-chat-starters-section` visible, header text asserted against live copy | asserted *(label drift, see clarification, already tracked #1042)* |
| 6 Verify "WELCOME MESSAGE" section | Condition holds as described | step 6 | `catalog-agent-modal-welcome-message-section` visible | asserted |
| 7 Verify "Start conversation" button visible at bottom | Condition holds as described | step 7 | `catalog-agent-modal-start-chat-button` visible in footer | asserted *(label drift, see clarification, already tracked #1042)* |
| Expected Final State: "Start conversation" button visible at bottom of modal | — | step 7 | as above | asserted |

Disposition legend: `asserted` | `already-covered` | `clarification` | `blocked` | `out-of-scope`.

### Axis 2 — Analyst additions

- **step 2** asserts the underlying agent-details network request resolves 200 (not merely "modal appears") — *added: this is the concrete, deterministic ready-signal the implementer needs; a bare visibility wait on modal content risks the same race class as known defect #1043 (which manifests on the Start Chat button specifically, but the root cause — content rendered from an unresolved fetch — applies to every field this case asserts: liked status, description, and both sections all read from `agentDetails`/`agent` state that only fully populates once this request resolves).*
- **step 3** asserts zero console errors during the open interaction — *added: standard side-channel regression guard per this skill's own discipline (confirmed live: 0 errors).*
- **step 4** decomposes the case's one compound step ("displays icon, name, owner, liked status, copy link icon, x button, description") into 7 independently-asserted sub-elements, each with its own handle — *added: the case's own step is a single line covering 7 distinct DOM elements; a single "modal looks right" assertion would not actually prove each one is present, and would mask a regression in any single element behind the others still rendering correctly.*
- (nothing else added beyond the case's own 7 steps.)

## Cleanup

None — read-only modal-open interaction, no state created. No agent liked, no conversation started, no navigation away from Catalog.

## Concrete Handles (discovered during exploration)

| Element | Recommended Locator | Fallback | Provenance |
|---|---|---|---|
| Catalog page heading | `AgentHubPage.page_heading` (`catalog-page-heading`) | none | on-main ✓ (pre-existing, ELITEA-2075) |
| Agent card | `AgentHubPage.AGENT_CARD_PREFIX` / `get_agent_card()` (`[data-testid^="catalog-agent-card-"]`) | none | on-main ✓ (pre-existing, ELITEA-2075) |
| Modal agent name | `AgentHubPage.modal_agent_name` (`catalog-agent-modal-agent-name`) | none | on-main ✓ (pre-existing, ELITEA-2075) |
| Modal agent icon | testid needed: `catalog-agent-modal-agent-icon` (pass as `data-testid` prop to the existing `<EntityIcon>` call, `AgentModal.jsx:222-227` — the component already supports the prop) | none | needs-adding |
| Modal owner name | testid needed: `catalog-agent-modal-owner-name` (`AgentModal.jsx:190-195` `Typography`) | none | needs-adding |
| Modal liked status / like button | testid needed: thread `testId="catalog-agent-modal-like-button"` into `<AgentHubLike>` (`AgentModal.jsx:198-201`) — combined with state via `[data-testid="catalog-agent-modal-like-button"][data-liked="false"]` once threaded (`Like.jsx` auto-derives `data-liked` from `testId` presence) | none | needs-adding |
| Modal overflow/copy-link menu button | `agent-hub-modal-menu-button` (raw string constant — pre-existing, `AgentHubModalMenu.jsx`) | none | on-main ✓ (pre-existing) |
| Modal close ("x") button | testid needed: `catalog-agent-modal-close-button` (`AgentModal.jsx:208-216` `IconButton aria-label="close"`) | none | needs-adding |
| Modal description | testid needed: `catalog-agent-modal-description` (`AgentModal.jsx:236-241` `Typography`) | none | needs-adding |
| Modal "CHAT STARTERS" section | testid needed: `catalog-agent-modal-chat-starters-section` (`AgentConversationStarters.jsx` container `Box`) | none | needs-adding |
| Modal "Welcome Message" section | testid needed: `catalog-agent-modal-welcome-message-section` (`AgentWelcomeMessage.jsx` container `Box`) | none | needs-adding |
| Modal "Start Chat" button | `AgentHubPage.modal_start_chat_button` (`catalog-agent-modal-start-chat-button`) | none | on-main ✓ (pre-existing, ELITEA-2075) |

## Network Behavior
- `GET /api/v2/elitea_core/public_application/prompt_lib/{id}` (singular — distinct from the bulk-listing `public_applications` endpoint) — fires on card click, resolves `200`, populates `agentDetails` (source of the two sections' actual content and the description/icon fallback values). Confirmed live: `.../public_application/prompt_lib/172` → `200`.
- No 4xx/5xx observed during the whole open-modal interaction.

## Known Defects Found During Exploration
- **[CLARIFICATION, already tracked, not re-filed]** [EliteaAI/elitea-testing-public#1042](https://github.com/EliteaAI/elitea-testing-public/issues/1042) — case text says "CONVERSATION STARTERS" section / "Start conversation" button; live product reads "CHAT STARTERS" / "Start Chat" respectively. Filed from a sibling case (ELITEA-2092) and explicitly names ELITEA-2356 as an affected sibling — same `AgentModal.jsx`/`AgentConversationStarters.jsx` component tree. Automation asserts the live copy as correct expected behavior.
- **[CLARIFICATION, filed this dispatch]** [EliteaAI/elitea-testing-public#1218](https://github.com/EliteaAI/elitea-testing-public/issues/1218) — case text says "copy link icon"; live product has no standalone copy-link icon — it's an overflow ("...") menu (`agent-hub-modal-menu-button`) whose "Share" item performs the copy action. Automation asserts the overflow menu button's visibility as the live expected behavior.
- Not re-verified/not relevant to this case (visibility-only, no click): [#1043](https://github.com/EliteaAI/elitea-testing-public/issues/1043) — Start Chat button race condition, only triggers on click, which this case does not perform.
- None else found — zero console errors, zero 4xx/5xx, all 7 case steps reproduced live and match the case's core intent (modal opens correctly and displays the expected content, modulo the two tracked copy drifts above).

## Blocked Steps
None — all 7 case steps were reached and observed live.

## Automation Hints
- Framework: Playwright + pytest (this project), Playwright MCP tools used this dispatch.
- **No new page object needed** — extend the existing `AgentHubPage` (`automation/pages/agent_hub_page.py`) with the 6 new `LocatorDescriptor` fields listed in § Concrete Handles (agent icon, owner name, like button [+ its `data-liked` state variant], close button, description, and the two section containers), once their testids are added via `add-data-testid`. `AgentHubPage.open_agent_by_name()` is reused as-is for reaching the modal (already waits on the exact `GET /public_application/prompt_lib/{id}` response this AFS's step 2 relies on).
- Selector policy: testid-only, no fallback (`.agents/testing.md` § Locator policy). The like button's `data-liked` state attribute follows the exact precedent already established for the card-list like button (ELITEA-2354) and the category filter chip (ELITEA-2352) — state via `data-*`, never a state-switched testid.
- Assert the CHAT STARTERS / Welcome Message empty-state copy against the LIVE strings ("No predefined chat starters – just type your request to begin." / "No welcome message set – the agent will start without a greeting.") for this specific 0-starter/0-welcome-message agent — do not assert the case's literal "CONVERSATION STARTERS"/"WELCOME MESSAGE" header text (drift, see § Known Defects).
- Marker suggestion: `@pytest.mark.p2` (medium priority → l3), `@pytest.mark.regression`, `@pytest.mark.agents` (matches the rest of this family's marker set, e.g. ELITEA-2350/ELITEA-2352).
