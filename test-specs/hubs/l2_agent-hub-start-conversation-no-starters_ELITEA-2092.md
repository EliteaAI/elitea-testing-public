# Test Case: Create New Conversation via Agent HUB — Start Conversation (No Conversation Starters)

## Metadata
- **TMS ID**: ELITEA-2092
- **Linked Story**: GH#295 (`[Automate][ELITEA-2092][chat-interface] Create New Conversation via Agent HUB — Start Conversation (No Conversation Starters)`, board #9)
- **Priority**: l2 (case priority: high)
- **Environment Explored**: local (`http://localhost:5173`, EliteaUI `automation/testids` branch → DEV backend), project `Private` (`${ELITEA_PROJECT_ID}`=399)
- **User set**: `${TEST_USER}` (localhost `auth_state` — `VITE_DEV_TOKEN`, transparent, no login flow)
- **Analyst**: qa-engineer (Sage), analyst slot, batch `cov60`
- **Status**: ready-for-automation

## Preconditions
- User is logged in to the Elitea platform (localhost: `auth_state` fixture — no explicit login step needed).
- User is in a Private project (default project selection on localhost).
- Agent "Business Analyst" exists, is published, has NO `conversation_starters` set (confirmed live — its modal renders the empty-state message, not a starter grid).

## Test Data
### reuse-existing
- Agent name: `Business Analyst` (public/published agent, live count confirmed via `GET /elitea_core/public_applications/prompt_lib/` — stable system fixture, appears in both the "Other"/"Trending" bucket and its own "Business Analyst" category bucket per `test-specs/hubs/_surface.md`)
- First message text: `"hi"`

## Test Steps
1. Navigate to `${BASE_URL}/chat` (baseline authenticated page), then click the sidebar **"Catalog"** entry (bottom of sidebar, above Support Bot — this is the case's "Agent HUB" nav item)
   - **Verify**: URL becomes `${BASE_URL}/elitea-catalog` (no query string — `?tab=agents` is the component's own default), Agents tab content visible (agent cards render)
2. Click the "Business Analyst" agent card
   - **Verify**: detail modal (`role="dialog"`) opens; shows agent name "Business Analyst", author, description
3. Verify the **"CHAT STARTERS"** section (case text says "CONVERSATION STARTERS" — case-text drift, filed `#1042`; live label is "CHAT STARTERS") displays the empty-state message `"No predefined conversation starters – just type your request to begin."` (note: en dash, not em dash, per live copy) and no starter buttons/grid are rendered
4. **Wait for the agent-details fetch to settle** (see Known Defects — `#1043`; do NOT click Start Chat immediately after the modal opens) — recommend `wait_for_response` matching `public_applications/prompt_lib/` or an equivalent stabilizing wait — then click the **"Start Chat"** button (case text says "Start conversation" — same case-text drift, `#1042`)
   - **Verify**: modal closes; URL becomes `${BASE_URL}/chat?create=1` then `${BASE_URL}/chat` (new-conversation composer view)
5. Verify the composer shows the active-participant button with text "Business Analyst" and, adjacent, the version-selector trigger with text matching the agent's published version (confirmed live: `"v2.1"` — matches case's own example exactly, no drift), plus a "×"/clear button (aria-label `"switch to model"`)
6. Type `"hi"` into the message input and click Send
   - **Verify**: a new user message renders addressed "to Business Analyst"; an AI reply message renders shortly after, with "Business Analyst" shown as the respondent (alongside a "Thought for N secs" indicator and the underlying model name)
7. Verify a new conversation entry appears under the "Today" group header, showing the `conversation-naming-spinner` (spinner + "Naming" text) immediately after Send, which resolves within a few seconds to an auto-generated title derived from the message content (e.g. sending `"hi"` auto-named the conversation `"HI Chat"` in one live run; a differently-worded message named it after its own content — the exact string is non-deterministic per LLM-assisted naming, assert non-empty + spinner-then-resolved transition, not a literal string)

## Expected Results
- Agent HUB (`/elitea-catalog`) opens from the sidebar "Catalog" entry
- Agent detail modal shows correct agent info and the empty-conversation-starters message
- "Start Chat" closes the modal and opens the chat composer with the agent pre-loaded (name + version visible)
- Sending "hi" gets a real AI reply, respondent shown as the agent
- The new conversation is auto-named (transient "Naming" spinner → resolved title) and appears under "Today"
- No console errors during the happy-path flow (confirmed clean in the successful live runs — errors DO appear if Start Chat is clicked too early, see Known Defects; the AFS's own recommended wait avoids that)

## Coverage Map

**Axis 1 — Case coverage**

| Case element | Expected result | Covered by (AFS step) | Asserted where | Disposition |
|---|---|---|---|---|
| 1 Navigate to Agent HUB from sidebar | Agent HUB page opens | step 1 | `step 1`: URL `/elitea-catalog`, cards visible | asserted |
| 2 Click agent card with no starters | Detail modal opens with agent info | step 2 | `step 2`: dialog visible, name/author/description present | asserted |
| 3 Verify CONVERSATION STARTERS section text | No starter buttons shown | step 3 | `step 3`: empty-state text present, starter grid absent | asserted *(case-text drift: live header is "CHAT STARTERS" — clarification `#1042`; assert the live text)* |
| 4 Click Start conversation button | Modal closes; Chat opens with agent pre-loaded | step 4 | `step 4`: dialog gone, URL `/chat` | asserted *(case-text drift: live button is "Start Chat" — same `#1042`)* |
| 5 Verify input bar shows agent name+version and × button | Agent chip shown | step 5 | `step 5`: switch-participant button text, version-selector text, clear button present | asserted |
| 6 Type "hi" and Send | Agent processes and responds; agent name shown as respondent | step 6 | `step 6`: user message + AI reply message, respondent name | asserted |
| 7 Verify new Today entry with Naming… placeholder resolving to auto title | Conversation auto-named | step 7 | `step 7`: `conversation-naming-spinner` present then resolved, item text non-empty | asserted |

**Axis 2 — Analyst additions**

- `step 4` Automation Hint: an explicit wait for the agent-details fetch to settle before clicking "Start Chat" — *added: discovered a genuine intermittent race (2/3 fast-click fresh-navigation attempts crashed with an uncaught TypeError and silently failed to navigate) during exploration; filed `#1043`. Without this wait the automated test would inherit the same flake.*
- `step 3`/`step 4` assert the LIVE copy ("CHAT STARTERS" / "Start Chat") rather than the case's literal text — *added: reverse-masking guard, case text drift filed as clarification `#1042`, not a product defect.*
- `step 6` no-console-errors guard during the happy-path send — *added: standard side-channel check per skill discipline; confirmed clean across all successful runs.*

## Cleanup
- No explicit cleanup required — conversations created by this test are ordinary user data (same pattern as other chat tests in this suite); no seeded fixtures were created or mutated.

## Concrete Handles (discovered during exploration)

| Element | Recommended Locator | Provenance | Fallback |
|---|---|---|---|
| Sidebar "Catalog" (Agent HUB) nav entry | `[data-testid="sidebar-agent-hub-button"]` | **LANDED** on-automation/testids only (awaiting human promotion to main) — `EliteaAI/EliteaUI@ae7d2703`, `src/[fsd]/widgets/sidebar-root/ui/button/AgentHubButton.jsx` | — |
| Agent card (dynamic, per agent) | `CATALOG_AGENT_CARD = '[data-testid="catalog-agent-card-{}"]'` (template, suffix = `application.id`) | **LANDED** on-automation/testids only — `EliteaAI/EliteaUI@ae7d2703`, `AgentCard.jsx` | — |
| Agent detail modal (Dialog) | `[data-testid="catalog-agent-detail-modal"]` | **LANDED** on-automation/testids only — `EliteaAI/EliteaUI@ae7d2703`, `AgentModal.jsx` | — |
| Conversation-starters section header | `[data-testid="catalog-agent-modal-starters-header"]` | **LANDED** on-automation/testids only — `EliteaAI/EliteaUI@ae7d2703`, `AgentConversationStarters.jsx` | — |
| Conversation-starters empty-state message | `[data-testid="catalog-agent-modal-starters-empty"]` | **LANDED** on-automation/testids only — `EliteaAI/EliteaUI@ae7d2703`, `AgentConversationStarters.jsx` | — |
| "Start Chat" button | `[data-testid="catalog-agent-modal-start-chat-button"]` | **LANDED** on-automation/testids only — `EliteaAI/EliteaUI@ae7d2703`, `AgentModal.jsx` | — |
| Composer active-participant button | `[data-testid="chat-switch-participant-button"]` | on-main ✓ / on-automation/testids ✓ | — |
| Composer version-selector trigger | `[data-testid="chat-version-selector-trigger"]` | on-automation/testids only (awaiting human promotion to main) | — |
| Composer "×"/clear-participant button | `[data-testid="chat-clear-participant-button"]` (aria-label currently `"switch to model"`) | **LANDED** on-automation/testids only — `EliteaAI/EliteaUI@ae7d2703`, `AgentEditorPanel.jsx` | — |
| Message input | `[data-testid="chat-message-input"]` | on-main ✓ / on-automation/testids ✓ | — |
| Send button | `[data-testid="chat-send-button"]` | on-main ✓ / on-automation/testids ✓ | — |
| Message list item | `[data-testid="chat-message-item"]` | on-main ✓ / on-automation/testids ✓ | — |
| New-conversation greeting | `[data-testid="chat-new-conversation-greeting"]` | on-automation/testids only (awaiting human promotion to main) | — |
| Conversation list item (dynamic, per id) | `CONVERSATION_ITEM = '[data-testid="chat-conversation-item-{}"]'` | on-automation/testids only (awaiting human promotion to main) | — |
| "Today" group header | `[data-testid="chat-conversation-group-header-today"]` | on-automation/testids only (awaiting human promotion to main) | — |
| Naming spinner (transient) | `[data-testid="conversation-naming-spinner"]` | on-main ✓ / on-automation/testids ✓ | — |

No CSS/role/text fallback is proposed for any row — per this project's testid-only locator policy the correct next action for a gap would be `add-data-testid`, and (per the Redispatch confirmations below) that step is now DONE for every row this case needs: all 6 previously-`needs-adding` testids landed in one commit, `EliteaAI/EliteaUI@ae7d2703` ("test: [EL-0000] add data-testid for Agent Hub modal + Start Chat (ELITEA-2092)"), on `automation/testids` only (not yet on `main` — awaiting human cherry-pick). The next implementer should NOT re-run `add-data-testid` for this case; only the page objects (`CatalogPage`) + the `test_*.py` file remain.

## Network Behavior
- `GET /elitea_core/public_applications/prompt_lib/{agent_id}` (or equivalent detail endpoint via `useLazyPublicApplicationDetailsQuery`) — fires on modal open; **the implementer must wait for this to settle before clicking "Start Chat"** (see Known Defects `#1043`).
- Message send fires the standard chat send request; AI reply arrives over WebSocket/Socket.IO (per `.agents/testing.md` — condition wait, never a fixed sleep). Conversation-naming resolves asynchronously shortly after (confirmed live: ~1.5s on DEV backend) — wait on `conversation-naming-spinner`'s disappearance or the conversation-item's text changing, not a fixed timeout.

## Known Defects Found During Exploration
- **[MAJOR] `#1043`** — Agent Hub "Start Chat" button throws an uncaught TypeError and silently no-ops (no navigation, no conversation, no user-visible error) if clicked before the modal's own `agentDetails` fetch resolves. Reproduced 2/3 fresh-navigation fast-click attempts; a ~1s natural delay avoided it every time. Does NOT block this case (this analyst's own run completed successfully — steps 2–3 provide enough natural elapsed time before step 4's click). **Automation must add the explicit wait in step 4** so the test itself doesn't inherit the race.
- **[INFO/CLARIFICATION] `#1042`** — Case's step 3 ("CONVERSATION STARTERS" section) and step 4 ("Start conversation" button) literal text don't match live product copy ("CHAT STARTERS" / "Start Chat"). Reverse-masking: live product is correct/consistent, case text is stale. This AFS asserts the live copy.

## Blocked Steps
- None.

## Automation Hints
- Framework: Playwright + pytest (per `.agents/testing.md`), page-object pattern with testid-only `LocatorDescriptor`.
- **Testid work for this case is DONE — do not re-run `add-data-testid`.** All 6 gap testids landed in `EliteaAI/EliteaUI@ae7d2703` on `automation/testids` (see Redispatch confirmations below); only page objects + the test file remain.
- **No existing page object covers the Agent HUB entry point or its detail modal.** Recommend `automation/pages/catalog_page.py`, class `CatalogPage` (per `test-specs/hubs/_surface.md` § No page object / testids yet), owning: `CATALOG_AGENT_CARD` (dynamic template constant), `catalog-agent-detail-modal`, `catalog-agent-modal-starters-header`, `catalog-agent-modal-starters-empty`, `catalog-agent-modal-start-chat-button`, and `sidebar-agent-hub-button` (or place the sidebar nav locator on whichever page object already owns sidebar navigation, if one exists — check before adding it to `CatalogPage`). The chat-continuation half of the flow reuses the EXISTING `automation/pages/chat_page.py` (`ChatPage`) — this run also confirmed `chat-clear-participant-button` now resolves live and can be added there. Compose both page objects in the test, same pattern as other cross-surface flows in this suite.
- **No existing test file/directory covers Agent HUB.** Recommend a new `automation/tests/ui/agent_hub/` directory (matches the `module: agent-hub` tag most batch `cov60` sibling cases carry — ELITEA-2356/2360/2368/2369/etc. — even though this case's own TMS metadata says `module: chat-interface`). Declared improvisation: no established directory exists yet for this feature; flagging per `.agents/role-overrides.md` § Declared-improvisation protocol so the implementer/reviewer can confirm or redirect.
- Markers: this test should carry `chat` and/or a new `agent_hub` marker (check `pytest.ini` — add `agent_hub` if not present) plus `regression` and the `l2`/`high`-appropriate priority marker (`p1`).
- **Critical wait before clicking "Start Chat"**: see § Known Defects `#1043` — wait for the agent-details GET to settle (network-idle-scoped to the dialog, or `wait_for_response` on the `public_applications/prompt_lib/` path) before the click, to avoid inheriting the intermittent race. Re-confirmed live this redispatch (see below): a ~1.5s wait after modal-open avoided the race a third time.
- **Viewport-dependent text on `chat-switch-participant-button`/`chat-version-selector-trigger`**: at a narrow viewport (<~1000px) these collapse to icon-only (`innerText` empty, `aria-label` only) — confirmed live this redispatch. At the suite's actual viewport (1366×768, `automation/conftest.py`) both render their full text ("Business Analyst" / "v2.1") as the AFS already documented — no action needed, just don't be surprised if a manual spot-check at a smaller viewport shows empty text.
- Exploration digest updated: `test-specs/hubs/_surface.md` § "Agent detail modal → Start Chat → chat handoff (ELITEA-2092 — full findings)" — read it first; it has the full testid mechanics, the naming-spinner mechanics, and the race-condition detail this AFS summarizes. Digest's testid-gap list corrected to LANDED status alongside this AFS update (commit on `automation/base`, per analyst digest-commit authority).

## Redispatch confirmations

**Pass 2 (2026-07-24, ~06:35 dispatch) — analyst-slot redispatch on an already-`ready-for-automation` case.**

Board `case.md` History showed the by-now-familiar bounce shape (per
`.agents/memory/qa-engineer/analyst_redispatch_on_already_complete_case_check_board_git_then_bounded_spotcheck.md`
Generalized lesson #9): `ready-for-automation` (04:23:31Z) → `implementing`
(04:23:34Z) → `analysis` (06:35:31Z), ~2h12m later, zero reason recorded.
Ground truth in THIS repo looked zero-artifact: `env -u GITHUB_TOKEN gh pr
list --state all --limit 200 --json number,title,headRefName,state | grep
2092` → no hits; `git branch -a` / `git worktree list` → no branch, no
worktree for this case.

**It wasn't zero-artifact — the real progress landed in the dependency repo.**
`cd ../EliteaUI && git fetch origin` then `git log origin/main..origin/automation/testids --oneline -- src/ | grep -i 2092` surfaced:

```
ae7d2703 test: [EL-0000] add data-testid for Agent Hub modal + Start Chat (ELITEA-2092)
```

`git show --stat ae7d2703`:

```
 src/[fsd]/features/agent-hub/ui/AgentCard.jsx                 | 1 +
 src/[fsd]/features/agent-hub/ui/AgentConversationStarters.jsx | 2 ++
 src/[fsd]/features/agent-hub/ui/AgentModal.jsx                | 2 ++
 src/[fsd]/features/chat/ui/chat-input/AgentEditorPanel.jsx    | 1 +
 src/[fsd]/widgets/sidebar-root/ui/button/AgentHubButton.jsx   | 1 +
 5 files changed, 7 insertions(+)
```

`git grep` confirmed all 6 of this AFS's `needs-adding` testids from the
original pass landed byte-for-byte as recommended
(`sidebar-agent-hub-button`, `catalog-agent-card-{application.id}`,
`catalog-agent-detail-modal`, `catalog-agent-modal-starters-header`,
`catalog-agent-modal-starters-empty`, `catalog-agent-modal-start-chat-button`,
`chat-clear-participant-button`) — zero deviation. PROVENANCE re-check
against `origin/main` for the same 7 testids: all still `NOT on main`
(expected — this project's testid promotion is a human cherry-pick, not
automatic).

**Bounded live spot-check (isolated `browser-verify` CDP, port 9333 — shared
Playwright MCP lane 0 was contended at redispatch time, same recurring
symptom noted on ELITEA-2219/1934's redispatches; fell back per the
documented tool-substitution discipline).** Ran the FULL case end-to-end
against `http://localhost:5173` (not just a testid-presence check, since the
underlying flow is cheap/deterministic and this case carries a
previously-confirmed intermittent race — worth re-proving the wait still
holds):

1. `navigate /elitea-catalog` → `sidebar-agent-hub-button` resolves (`true`);
   found `catalog-agent-card-31` for "Business Analyst" (2 hits — appears in
   both its own category bucket and `Other`/`Trending`, consistent with
   `_surface.md`'s category-model note).
2. Clicked the card → `catalog-agent-detail-modal` present; `catalog-agent-modal-starters-header`
   text = `"CHAT STARTERS"`; `catalog-agent-modal-starters-empty` text =
   `"No predefined conversation starters – just type your request to begin."`
   (en dash, exact match); `catalog-agent-modal-start-chat-button` text =
   `"Start Chat"` — all 4 byte-identical to the AFS's live-copy claims.
3. Waited ~1.5s (per the AFS's own `#1043` wait recommendation), clicked
   `catalog-agent-modal-start-chat-button` → navigated `/chat?create=1` →
   `/chat`, **zero console errors** (checked `get-console --level error`
   explicitly) — the known race was NOT triggered, confirming the
   recommended wait is sufficient a third time.
4. At the default headless viewport (756×469) `chat-switch-participant-button`/
   `chat-version-selector-trigger` rendered ICON-ONLY (empty `innerText`,
   `aria-label` only — a responsive collapse, not a defect). Resized to
   1366×768 (the suite's actual `automation/conftest.py` viewport) and
   re-checked: `chat-switch-participant-button` text = `"Business Analyst"`,
   `chat-version-selector-trigger` text = `"v2.1"` — exact match to the
   AFS's existing claim. (New nuance captured in Automation Hints above —
   not a correction, a clarification for anyone spot-checking at a smaller
   viewport.) `chat-clear-participant-button` confirmed present
   (`aria-label="switch to model"`).
5. Typed `"hi"` into `chat-message-input`, clicked `chat-send-button` →
   `conversation-naming-spinner` present immediately after send → resolved
   (`wait-hidden`, ~2s) → conversation item text became `"HI Chat"` (an
   auto-generated title, matching the AFS's own worked example exactly) →
   `chat-message-item` showed the user message ("hi" to Business Analyst)
   and the AI reply ("Thought for less than a second · GPT-5.4-mini · "Hi
   there 👋 How can I help you today?"") with Business Analyst as
   respondent. Zero console errors across the whole exchange.

**Zero drift found.** Every claim in the original AFS — literal copy, testid
list, wait requirement, naming-spinner mechanics, respondent display — held
up exactly on this independent re-run. The ONLY thing that changed is that
the testid-authoring step (previously `needs-adding`) is now `LANDED` on
`automation/testids`, which this pass propagated into both this AFS's
Concrete Handles table and `test-specs/hubs/_surface.md`.

**Status returned: unchanged, `ready-for-automation`.** Explicit note to the
orchestrator: this is the SAME `implementing → analysis` zero-same-repo-
artifact bounce shape documented for ELITEA-2091 (Fifteenth confirmed
instance in the redispatch playbook) — the dependency-repo testid work is
genuinely done, so **the correct next dispatch is an implementer picking
this AFS up to write `CatalogPage` + the test file only, not another
analyst pass and not a fresh `add-data-testid` run.** No PR/branch exists
in `elitea-testing-public` for this case yet.

## Implementer note (Pass 3, 2026-07-24)

This AFS file did not exist in the implementer's isolated git worktree
(uncommitted analyst edits do not travel across isolated worktrees — only
committed refs do); it was recovered by reading the file directly from the
orchestrator's main checkout (where the analyst's Pass-2 uncommitted edit
was still on disk) and copied in verbatim. Content is otherwise unchanged
from the Pass-2 analyst version above. Flagging this as a process gap in the
Run Report rather than silently absorbing it — the AFS should be committed
by *someone* before the isolated-worktree implementer dispatch fires, or the
dispatch prompt should point at a committed ref.
