# Test Case: Build with AI — generating an agent draft from the in-chat AgentEditor works end-to-end

## Metadata
- **TMS ID**: ELITEA-1920
- **Linked Story**: none
- **Priority**: l2 (case priority: `high`)
- **Status**: `ready-for-automation`
- **Environment Explored**: local (`http://localhost:5173`, EliteaUI `automation/testids` branch → DEV backend, project `Private` / `${ELITEA_PROJECT_ID}`=399)
- **User set**: `${TEST_USER}` (dev-token auth on localhost, `auth_state` skips login)
- **Analyst**: qa-engineer (Sage), analyst slot — cluster dispatch with ELITEA-1999 (shared session, separate AFS — see Coverage decision below)
- **Case-gate note**: same recurring gap as every prior "Build with AI" AFS (ELITEA-1907/1909/1911/1915): `.agents/testing.md` has no `TMS case-gate` section defining excluded statuses. Case frontmatter carries `status: draft` / `execution_type: manual`; per the skill's default this run proceeded and fetched/executed the case. Flagging again for scout.
- **Tooling note**: no Playwright MCP server was available this session; explored via standalone `sync_playwright` scripts driving the existing page objects directly (`ChatPage`, `AgentCanvasPage`, `GenerateAgentModalPage`), not committed, scratch-only.

## Coverage decision — why `ready-for-automation`, not `extend-existing`

This case's shell (steps 1–2: open the in-chat "+ Create New Agent" canvas)
and the resulting participant-addition behaviour (steps 8–9) are already
proven by the MERGED spec `automation/tests/ui/chat/test_create_agent_via_chat_canvas.py`
(`TestCreateAgentViaChatCanvas.test_create_new_conversation_and_add_agent_via_canvas`,
ELITEA-2166) — but for a **manually filled** agent form. This case's
distinguishing content (steps 2–7: click "Build with AI" instead of filling
fields by hand, drive the full generate → loading → review → select
resources → approve flow) is a completely different interaction shape,
already itself fully proven **from a different host page**
(`/agents/create`) by `test_agent_build_with_ai.py`
(`TestAgentBuildWithAIGenerationFailureRetry`,
`TestAgentBuildWithAISuggestedResources`,
`TestAgentBuildWithAISelectedResourcesAttached` — ELITEA-1907/1909/1911/1915).

Live exploration (see Test Steps) confirms **both halves render/behave
identically when hosted inside the chat canvas** — the canvas renders the
exact same `CreateAgentForm.jsx` component as `/agents/create`
(`AgentCanvasPage`'s own docstring already documents this for the manual
fields; this run confirms it also holds for the `GenerateAgentButton`/
`GenerateAgentModal` sub-tree, entity-identical testids, entity-identical
network contract). What is **genuinely new and previously unexercised** is
only the **completion wiring**: from `/agents/create`, `onAgentCreated`
auto-navigates to `/agents/all/{id}` (ELITEA-1909's documented behavior);
from the chat canvas, `onAgentCreated` is `useAgentCreation.js`'s hook
instead — it transforms the created agent into a participant, calls
`addNewParticipants(...)`, and auto-activates it, with **no navigation away
from `/chat` at all**. This is a distinct code path
(`src/hooks/chat/useAgentCreation.js`) that no existing spec touches (the
manual-entry ELITEA-2166 test exercises the SAME hook, but only reaches it
via manual form-fill, never via the generation modal).

Per the `test-case-analysis` skill's extend/fresh boundary ("if the gap is
large enough that the extension would be a near-rewrite of the covering
spec, treat as `ready-for-automation` instead"): swapping ELITEA-2166's
steps 4–7 (fill 3 fields, click Save) for the entire multi-step Build-with-AI
modal flow (open, prompt, generate, wait for review, optionally select
resources, approve) is not "a small number of missing assertions" against
one covering spec — it is a different creation mechanism layered onto the
same shell. **No new page-object locators or testids are needed anywhere in
this case** (100% reuse — see Concrete Handles): the correct shape is a
**new, small test module** that composes the three already-existing page
objects (`ChatPage` + `AgentCanvasPage` + `GenerateAgentModalPage`), mirroring
how `test_agent_with_toolkit_chat.py` already composes `AgentPage` +
`ChatPage` for a similar cross-cutting scenario, and asserting steps 8–9
with the same `open_participants_popover()` helper ELITEA-2166 already
wrote and proved.

## Preconditions
- User is logged in with sufficient permission to open "Build with AI" (`${TEST_USER}`, confirmed live — `generate-agent-open-button` renders and is clickable, same permission finding as every prior "Build with AI" AFS).
- An active chat conversation exists — this run used a fresh, unsaved `/chat` conversation (created via `+ Chat`), same precondition ELITEA-2166 already uses; the case's own preconditions ("An active chat conversation exists") are satisfied identically by either a fresh or a persisted conversation — not re-investigated separately, no gap found here.
- The "+" button to add participants (`plus-menu-button`) is accessible — confirmed live.

## Test Data

### reuse-existing
- Natural-language prompt used (not verbatim from the case, which gives no exact wording): `"An agent that summarizes GitHub pull request descriptions into a single concise sentence."` — arbitrary, per the case's own Test Data table ("Any valid agent description").
- `${TEST_USER}` — already has sufficient permission (see Preconditions).

No data is left behind — the created agent and the conversation (if it acquires an id) are deleted in Cleanup.

## Test Steps

1. Navigate to `${BASE_URL}/chat`, click `+ Chat` (`sidebar-create-button`) to open a fresh conversation, click the composer's plus menu (`plus-menu-button`), hover `agents-menuitem` to reveal its submenu, click `agents-create-new-button`.
   - **Verify**: the in-chat "Create New Agent" canvas panel opens (`AgentCanvasPage.wait_for_open()`), heading `agent-canvas-title` reads `"Create New Agent"` — confirmed live. This is exactly `ChatPage.open_create_new_agent_canvas()` + `AgentCanvasPage`, reused verbatim from ELITEA-2166.

2. Click **"Build with AI"** (`data-testid="generate-agent-open-button"`) inside the canvas.
   - **Verify (live-confirmed, the case's own step-2 core claim)**: the button IS rendered inside the canvas — `CreateAgentForm.jsx` conditionally renders `<GenerateAgentButton>` whenever `entityType !== 'pipeline'` (default `'application'`), and the canvas hosts the exact same `CreateAgentForm` component as `/agents/create` (source-confirmed, `src/pages/NewChat/AgentEditor.jsx` → `CreateAgentForm`). `GenerateAgentModal` (`data-testid="generate-agent-modal"`) opens — same modal, same testids as the `/agents/create` flow.

3. Fill the prompt textarea (`generate-agent-prompt-input`) with the Test Data prompt, click **"Generate"** (`generate-agent-submit-button`).
   - **Verify**: `POST /api/v2/elitea_core/generate_application_draft/prompt_lib/399` resolves `200` (confirmed live). A brief loading state (`generate-agent-loading-indicator`) is shown (not independently timed this run — already characterized by ELITEA-1915's AFS, not re-derived here), then the review form renders.

4. Loading → review-form transition.
   - **Verify**: review form renders with populated Name (`"PR Summary Generator"` this run), Description, Instructions, Welcome Message, conversation starters — all pre-populated (case step 5's exact claim, confirmed live) — same field-population contract ELITEA-1907/1909/1911 already documented in detail (not re-derived field-by-field here). This run's draft returned `suggested_toolkits: 1`, `suggested_skills: 0` — a "Suggested Toolkits:" section rendered (not independently re-verified item-by-item; that exact rendering contract is ELITEA-1907's own subject and stays out of scope here per Rule-6 reuse).

5. (Case step 6, optional per the case's own wording "if any") Suggested-resource selection is **not exercised** in this AFS — it is the OWN, already-covered subject of ELITEA-1907/1909/1911 (select/leave-unchecked/verify-attached/verify-absent, entity-generic across Toolkit/Agent/Skill). Re-deriving it here would duplicate coverage without adding anything chat-specific. The implementer may add a resource-selection assertion opportunistically if convenient, but it is not required for this AFS's Pass criteria.

6. Click **"Create Agent"** (`generate-agent-approve-button`).
   - **Verify**: `POST /api/v2/elitea_core/applications/prompt_lib/399` resolves `201` (confirmed live, agent id `6738` this run, name `"PR Summary Generator"`).
   - **Verify (the case's genuinely new subject, step 8)**: the page does **NOT** navigate away from `/chat` — URL observed live: `http://localhost:5173/chat?edited_participant_id=6738` (contrast with the `/agents/create` flow's `/agents/all/{id}` auto-navigation, ELITEA-1909's documented behavior — confirmed live to be genuinely different here, not a guess). The canvas transitions from its create-mode heading to the saved-agent view: `agent-canvas-title` now reads `"PR Summary Generator"` (same post-save title-transition contract ELITEA-2166 already documented for the manual-fill flow — confirmed live to hold identically for the AI-generated agent too).

7. Open the PARTICIPANTS panel (`chat.open_participants_popover(section="agents")`, the exact helper ELITEA-2166 wrote and already uses for its own step 8).
   - **Verify (case step 9)**: the popover contains the created agent's name (`"PR Summary Generator"`) — confirmed live (`participants popover contains created agent name: True`, popover text snippet observed: `"AgentsPR Summary GeneratorEditing..."` — the `"Editing..."` status label is the SAME transient state ELITEA-2166's AFS already documented and filed a clarification about (issue EliteaAI/elitea-testing-public#709: composer/participant text shows "Editing…" while the just-created agent's own canvas is still open, not yet the plain agent name — not re-filed, same recurring UI state, already tracked).

## Expected Results
Matches the case's stated Pass criteria in full: the in-chat canvas opens (step 1), "Build with AI" is present and opens the SAME generation modal used elsewhere (step 2), generation reaches a populated review form (steps 3–5), approving creates the agent (step 6) WITHOUT navigating away from the conversation, and the newly created agent is confirmed both auto-added as a participant and visible in the Participants list (step 7 / case steps 8–9). All 9 case steps executed live (step 6's optional resource-selection sub-step intentionally not exercised — see step 5's rationale); no blockers, no product defect found. One pre-existing, already-filed cosmetic finding observed (see Known Defects).

## Coverage Map

### Axis 1 — Case coverage

| Case element | Expected result | Covered by (AFS step) | Asserted where | Disposition |
|---|---|---|---|---|
| Precondition: active chat conversation, "+" accessible | reachable | Preconditions | `plus-menu-button` visible/clickable | asserted |
| 1 Open Agent creation editor menu via chat "+" | editor menu displayed | step 1 | `agent-canvas-title` = "Create New Agent" | asserted (reused from ELITEA-2166) |
| 2 Click Build with AI | GenerateAgentModal opens | step 2 | `generate-agent-open-button` present inside canvas (live-confirmed, was NOT previously known to be true — see Coverage decision), `generate-agent-modal` visible | asserted |
| 3 Enter description, click Generate | modal shows loading state | step 3 | `generate_application_draft` → 200 | asserted |
| 4 Loading → review form | loading indicator then review form | step 4 | review form fields visible | asserted (field-population detail out of scope, ELITEA-1907/1909's subject) |
| 5 Generated fields pre-populated | Name/Description/Instructions/Welcome/Starters populated | step 4 | draft name observed = "PR Summary Generator" | asserted (not re-verified field-by-field, see step 4 note) |
| 6 Select suggested resources (if any) | selected cards highlighted | step 5 | — | **out-of-scope by design — see step 5 rationale (already ELITEA-1907/1909/1911's own subject)** |
| 7 Click Approve/Create Agent | creation submitted | step 6 | `POST .../applications/...` → 201 | asserted |
| 8 Agent created + added as participant in current conversation | agent is a participant | step 6 | URL stays on `/chat` (no navigation), `agent-canvas-title` = agent name (the genuinely new, previously-unproven observable) | asserted |
| 9 Agent immediately available in Participants list | listed | step 7 | Participants popover (`open_participants_popover`) contains agent name | asserted |

### Axis 2 — Analyst additions

- Step 2 documents, with a source-code citation, WHY the Build-with-AI button is even present inside the chat canvas (`CreateAgentForm.jsx`'s `entityType !== 'pipeline'` conditional) — *added: the case text doesn't explain this, and without it an implementer might assume new UI work is needed to expose the button in this context, when in fact zero UI changes are needed.*
- Step 6 documents the EXACT code path (`useAgentCreation.js`) responsible for the participant-add behavior, contrasted against the `/agents/create` page's navigate-away behavior — *added: this is the single most implementer-relevant fact in this AFS — without it, someone reusing `GenerateAgentModalPage`'s existing `approve_button.click()` + implicit "wait for /agents/all/{id} navigation" pattern (which ELITEA-1909's test uses) would hang or false-fail waiting for a navigation that never happens here.*
- Step 7 cross-references the exact pre-existing helper (`open_participants_popover`) and the exact pre-existing clarification (issue #709) an implementer would otherwise re-discover from scratch — *added: saves a full debugging cycle on the "Editing..." vs agent-name transient state.*

## Cleanup
1. Created agent (id `6738` this run, deleted live via `AgentAPI.delete_agent()` in the exploration script — confirmed via 204/404 on subsequent fetch).
2. The exploration's conversation never persisted a `/chat/{id}` (no message was sent), so there was nothing to delete server-side — same "unsaved until first message" behavior ELITEA-2166's AFS already documents. An implementation that DOES send a message (to more fully exercise the created-agent-as-participant flow, e.g. reusing ELITEA-2166's own step 10 pattern) must delete the resulting conversation too.

## Concrete Handles (discovered during exploration — 100% reuse, zero new testids/locators needed)

| Element | Recommended Locator | PROVENANCE | Fallback |
|---|---|---|---|
| Plus menu button | `ChatPage.plus_menu_button` (`plus-menu-button`) | on-main ✓ (fresh `git fetch origin` this run) | n/a — already present |
| Agents submenu item | `ChatPage.agents_menuitem` | on-main ✓ | n/a — already present |
| "+ Create New Agent" | `ChatPage.agents_create_new_button` (`agents-create-new-button`, added by ELITEA-2166) | on-main ✓ | n/a — already present |
| Canvas title/subtitle | `AgentCanvasPage.title` / `.subtitle` (`agent-canvas-title` / `agent-canvas-subtitle`) | on-main ✓ | n/a — already present |
| "Build with AI" open button | `GenerateAgentModalPage.open_button` (`generate-agent-open-button`) | on-main ✓ (verified live, case-insensitive `git grep` this run — a prior AFS's case-sensitive grep falsely reported this as `main:no`; corrected here, see Known Defects/notes) | n/a — already present |
| Prompt textarea / Generate / Approve buttons | `GenerateAgentModalPage.prompt_input` / `.generate_button` / `.approve_button` | on-main ✓ | n/a — already present |
| Participants popover (Agents section) | `ChatPage.open_participants_popover(section="agents")` | on-main ✓ (pre-existing, ELITEA-2166) | n/a — already present |

**Summary for the implementer:** zero `add-data-testid` work needed. This case is pure composition of three existing page objects (`ChatPage`, `AgentCanvasPage`, `GenerateAgentModalPage`) — no new locators, no new testids. The only new artifact is a new test module/class.

## Network Behavior
- `POST /api/v2/elitea_core/generate_application_draft/prompt_lib/399` → `200` — identical contract to the `/agents/create`-hosted flow (ELITEA-1907/1909's documented shape); host page does not affect this call.
- `POST /api/v2/elitea_core/applications/prompt_lib/399` → `201` — creates the agent; identical payload/response shape to ELITEA-1909's documented contract.
- **No subsequent navigation-triggering call fires** — confirmed by URL staying on `/chat?edited_participant_id={id}` rather than transitioning to `/agents/all/{id}` (contrast with the `/agents/create` flow). The participant-add itself happens client-side via `addNewParticipants` (chat state, not observed as a separate REST call in this run — worth re-confirming with a full network capture at implementation time if the implementer wants to assert on it directly rather than via the Participants-popover UI check).

## Known Defects Found During Exploration

**No functional product defect found in this case's own subject.** One pre-existing, already-filed cosmetic finding observed incidentally while in the review form (not re-filed):

1. **[Not re-filed — already tracked as EliteaAI/elitea-testing-public#1050]** A React DOM-prop warning (`disableUnderline`/`disableunderline` not recognized) fires in the console every time the Build-with-AI review form renders (`GenerateAgentReviewForm.jsx`'s Name field) — observed again in this run, cosmetic only, does not affect functionality. Confirmed via `env -u GITHUB_TOKEN gh issue list` dedup check before considering filing — already tracked, not duplicated.
2. **[Not a defect — methodology note for future AFS authors]** A prior AFS's provenance-verification `git grep` for `generate-agent-open-button` against `origin/main` used a case-sensitive filter (`grep -E "(data-testid|testid.*=.*$t)"`), which misses the button's actual wiring (`buttonTestId="generate-agent-open-button"` — capital `T`, doesn't match lowercase `testid`) and would have reported a false `main:no`. This run's re-check used `git grep -qiE` (case-insensitive) and confirmed `main:YES`. Flagging for whoever next revises the closure-record grep in `.agents/workflow.md` — the documented two-stage pattern there should also be case-insensitive, not just substring-tolerant.

## Blocked Steps
None. All case steps executed live end-to-end (step 6's optional resource-selection sub-step deliberately not exercised — see step 5 rationale, not a blocker).
