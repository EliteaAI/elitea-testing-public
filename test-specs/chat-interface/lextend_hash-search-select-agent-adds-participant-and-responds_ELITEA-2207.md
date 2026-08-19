# Test Case: Chat – Mentions with # – Select Agent from List and Verify Agent is Added to Participants

## Metadata
- **TMS IDs (family)**: ELITEA-2207 (priority medium, 3 steps) + ELITEA-2469 (priority high, 7
  granular steps) — SAME flow, ELITEA-2469 is a more granular re-statement of ELITEA-2207 asking for
  two extra structural details (icon/version in the PARTICIPANTS row) that ELITEA-2207's wording
  doesn't spell out. Differ only in assertion GRANULARITY, not in steps/actions — one family AFS,
  `family_afs=true`, same `afs_path`.
- **Linked Story**: none (both cases `requirements: []`)
- **Environment Explored**: local (`http://localhost:5173`, EliteaUI `automation/testids`, DEV backend;
  Private project, `projectId=1` per the resolved participant `uniqueId`, sidebar shows project display
  id `399` — two different id spaces, not a discrepancy: `application_{agent_id}_{project_id}` uses the
  INTERNAL project id, the sidebar shows a separate display/short id)
- **User set**: `${TEST_USER}` — localhost: no login needed, `VITE_DEV_TOKEN` auto-auths
- **Analyst**: qa-engineer (agent), batch `chat-remaining-w14`, 2026-08-19
- **Status**: **extend-existing** (both cases)
- **surface_key**: `chat-hash-search-participants` (same surface as ELITEA-2206, analysed earlier this
  same session — reused its digest section for the `#` mechanics and testid provenance)

## Preconditions
- User is logged in to the Elitea platform.
- Agents exist in the project (ambient DEV data — 60+ agents/pipelines already present, no seeding
  needed; the shipped test should select whichever agent-type card the `#` dropdown returns first,
  not hardcode a name, for resilience against account data changes — same approach ELITEA-2206 used).

## Extension target — Rule-6 partial overlap

**Covering spec:** `automation/tests/ui/chat/test_chat_interface.py`, class `TestHashSearch`, method
`test_add_participant_via_hash_search` (line 434, merged `origin/automation/base`, confirmed via fresh
`git fetch origin` this session — `git log origin/automation/base -1 -- automation/tests/ui/chat/test_chat_interface.py`
→ `8981927cc`, contains this class). The SAME class's `test_hash_search_shows_agents_and_pipelines_from_all_sources`
(ELITEA-2206, landed earlier this session on this batch trunk) is a sibling extension of the same
covering test, not itself a coverage source for this family — it only proves dropdown-open + per-card
subtitle/icon/source/click-away, never anything about the PARTICIPANTS panel or messaging.

**Behavioural-overlap argument.** `test_add_participant_via_hash_search` already proves: typing `#`
opens the dropdown, clicking **the first available option (agent OR pipeline, not scoped to either)**
selects it, and the dropdown closes. That covers this family's own Step 1 (open dropdown) and half of
Step "select from list" (a selection mechanism exists and closes the dropdown). Live-reconfirmed this
session on `/chat/9082` — typing `#`, clicking a card, dropdown closed.

**Gap: the covering test's own scope stops at "dropdown closes" — it asserts NOTHING about what
selecting a participant actually DOES**, which is this family's entire subject. Three live-confirmed
gaps, none touched by the covering test:

1. **Selection must be scoped to an AGENT specifically** (not "whichever card is first" — the covering
   test's `get_hash_search_first_option()` may click a pipeline). Both cases' own title/steps say
   "Select Agent" — the shipped test must filter `get_hash_search_items()` by
   `get_hash_search_item_subtitle(item) == "agent"` (reusing the exact ELITEA-2206-added handles) before
   clicking, not reuse `get_hash_search_first_option()` as-is.
2. **PARTICIPANTS panel gains an AGENTS section, and the composer shows the selected agent as its
   active participant** — the covering test never opens the participants popover or inspects the
   composer at all after its own selection click. Live-confirmed this session (see Concrete Handles):
   `chat-participants-badge-agents` badge (via `is_participants_badge_visible(section="agents")`)
   appears where it was previously ABSENT, and `chat-switch-participant-button`
   (`is_agent_participant_in_composer(agent_name)`) shows the selected agent's name.
3. **Sending a message reaches the selected agent, the agent responds, and it remains a participant
   after the response completes** — the covering test never sends a message at all. Live-confirmed:
   sent "hello", the agent ("Agent testing skills" this session) replied "Hello! How can I help?",
   `wait_for_ai_response()`-style Copy-button completion reached, and the AGENTS badge still read "1"
   afterward — matches both cases' own final assertion ("agent responds and remains in participants").

All three gaps are additive assertions layered on the SAME `#`-select-and-close mechanism the covering
test already proves — no new interaction primitive for opening/closing the dropdown itself (that part
is reused verbatim), only new assertions on participants/composer/messaging AFTER the existing select
click. Classified `extend-existing`, not `ready-for-automation`.

## Test Steps (source cases, reproduced for traceability; only the gap steps below need new code)

### ELITEA-2207 (3 compound steps)
1. Create a new conversation; verify no AGENTS in PARTICIPANTS — **GAP** (never asserted by the
   covering test at all; use a FRESH `conversation_id`-fixture conversation, which is guaranteed to
   have zero participants, rather than re-deriving "no agents" against an existing conversation).
2. Type '#' and click an agent from the dropdown → agent name appears in message field with # mention;
   AGENTS section added to PARTICIPANTS — **already-covered (open+select+close) + GAP (participant
   panel + composer assertions)**. See Clarification below re: "message field" wording.
3. Type 'hello' and send → agent responds; remains in PARTICIPANTS — **GAP** (entirely new; covering
   test never sends a message).

### ELITEA-2469 (7 granular steps — same flow, finer-grained assertions)
1. Navigate to Chats, create a new conversation — **already-covered** (`navigate_to_chat()` / existing
   conversation-creation flow, unrelated to hash-search).
2. Verify PARTICIPANTS panel shows no AGENTS section initially — **GAP**, same as ELITEA-2207 Step 1.
3. Type "#", click an agent from "SEARCH RESULTS" — **already-covered (open/select/close) + GAP
   (must scope to an agent-type card specifically, per point 1 above)**.
4. Verify agent name appears in message input field with # mention — **GAP, with a Clarification**
   (see below — it's the COMPOSER's active-participant chip, not literal text in the input).
5. Verify PARTICIPANTS panel shows AGENTS section with the agent's **name, version, and icon** —
   **GAP**, stricter than ELITEA-2207's Step 2 (ELITEA-2207 only asks for the section to exist;
   ELITEA-2469 asks for three specific sub-elements of the row). Live-confirmed this session: the
   popover row for an added agent shows an icon, the name ("Agent testing skills"), and a version
   control (rendered as "ver" — see Concrete Handles).
6. Type "hello" and send — **GAP**, same as ELITEA-2207 Step 3's send half.
7. Verify the agent responds and remains in PARTICIPANTS — **GAP**, same as ELITEA-2207 Step 3's
   response half.

## Expected Results
- Dropdown open + select-first-option + dropdown-closes: already proven by the covering test,
  live-reconfirmed this session.
- No-AGENTS-initially, agent-scoped selection, participant-panel-gains-AGENTS-section,
  composer-shows-active-agent, message-reaches-agent, agent-responds, agent-remains-a-participant: all
  genuinely new assertions, ALL live-confirmed this session on `/chat/9082` (an existing conversation
  used as a stand-in for exploration; the shipped test uses the `conversation_id` fixture for a
  guaranteed-fresh, guaranteed-zero-agents starting state — see Automation Hints). No defect found on
  any of them — the live product does exactly what both cases' own intent describes, once the
  Clarification below is accounted for.

## Coverage Map

### Axis 1 — Case elements

| Case element | Expected result | Covered by | Asserted where | Disposition |
|---|---|---|---|---|
| Precondition: agents exist in project | — | ambient DEV data | 60+ agents present | already-covered |
| New conversation → no AGENTS in PARTICIPANTS | AGENTS section absent | **GAP** | `not is_participants_badge_visible(section="agents")` on a fresh `conversation_id` conversation | **extend — gap assertion** |
| Type '#' → dropdown appears | dropdown appears | covering `test_add_participant_via_hash_search` | `wait_for_hash_search_dropdown()` | already-covered |
| Click an AGENT (not any card) from dropdown | agent selected, dropdown closes | select/close: covering test; agent-type scoping: **GAP** | `get_hash_search_items()` filtered by `get_hash_search_item_subtitle()=="agent"`, then `.click()`; `not is_hash_search_dropdown_visible()` | **extend — gap assertion** |
| Agent name appears "in message field" with # mention | mention visible | **GAP + Clarification** | `is_agent_participant_in_composer(agent_name)` on `chat-switch-participant-button` (NOT literal text in `chat-message-input` — see Clarification) | **extend — gap assertion, case-text drift noted** |
| AGENTS section added to PARTICIPANTS | AGENTS section + row visible | **GAP** | `is_participants_badge_visible(section="agents")` → True; `open_participants_popover(section="agents")` shows a row | **extend — gap assertion** |
| (ELITEA-2469 only) row shows name, version, icon | all 3 sub-elements present | **GAP** | scoped read inside the popover's participant row (name text, version control, icon element) | **extend — gap assertion, ELITEA-2469 only** |
| Type 'hello' and send | message sent to the agent | **GAP** | `send_message("hello")`; header shows "to <Agent Name>" attribution | **extend — gap assertion** |
| Agent responds | response rendered | **GAP** | `wait_for_ai_response(initial_count)` — Copy button + non-transient content | **extend — gap assertion** |
| Agent remains in PARTICIPANTS after response | AGENTS badge still shows the agent | **GAP** | `is_participants_badge_visible(section="agents")` still True post-response | **extend — gap assertion** |

Disposition key: `asserted` / `already-covered` / `clarification` / `blocked` / `out-of-scope`.

### Axis 2 — Analyst additions
- **Clarification, not a defect (reverse-masking guard)**: both cases say the agent name/mention
  appears "in the message input field" (ELITEA-2207 Step 2, ELITEA-2469 Steps 3-4). Live-confirmed this
  session (screenshot evidence): after clicking an agent from the `#` dropdown, the message
  **input stays completely empty** (placeholder "Type your message..." unchanged) — the selected agent
  instead renders as a dedicated chip in the composer's control row (`chat-switch-participant-button`,
  labelled "Agent testing skills" this session, pre-existing testid from the ELITEA-1736 rework, with
  its own page-object assertion helper `is_agent_participant_in_composer()`). This is the SAME
  established UI pattern this digest already documents for every other participant-mention family
  (slash-mention toolkit/MCP, hash-search) — participant selection always produces a composer-level
  active-participant control, never literal inserted text in the message body. Live-consistent,
  self-consistent product behavior; the case text's "message field" wording is the stale half — assert
  against the real composer chip, do not file as a defect.
- **Source-confirmed mechanism (not re-derived from the case text alone)**: the participants popover's
  per-row version control is rendered as the same "ver" + chevron control the composer's own
  `chat-version-selector-trigger` uses (per the class's existing `version_selector` machinery) — read
  the row's rendered text, don't assume a literal version number string is always present (this account's
  ambient "Agent testing skills" agent shows exactly "ver" with no trailing number in this session,
  consistent with a single-version agent).
- Console/network side-channel checked throughout this session's live exploration — 0 console errors
  before, during, or after the participant-add + send-message + remove-participant sequence.

## Cleanup
This session's exploration on `/chat/9082` (a shared conversation reused for read-only exploration by
the ELITEA-2206 analysis earlier the same session) DID mutate state — a real agent participant was
added and a real "hello" message + AI response were sent. Restored via the existing
`remove_agent_participant(agent_id=280)` mechanism (UI: hover the popover row → "Remove agent" →
confirm "Remove" in the `Remove agent?` dialog) immediately after confirming the response — the
`chat-participants-badge-agents` badge is confirmed gone from the DOM afterward (matches
`wait_for_participants_badge_absent()`'s documented "disappears from DOM at count 0" contract). The
sent "hello" message + the agent's reply remain in `/chat/9082`'s history (message history is not
retroactively deleted by removing a participant — same as every other participant-removal precedent in
this digest) — cosmetic only, does not affect any other case's exploration of this conversation.

## Concrete Handles (discovered during exploration)

Locator policy on this project is **testid-only** — no role/label/text fallback ladder
(`.agents/testing.md` § Locator policy, `.agents/role-overrides.md`). Provenance verified via
`git grep` on both `origin/main` and `origin/automation/testids` in the sibling `EliteaUI` clone
(fetched fresh this session) unless noted "pre-existing, page-object confirmed" (already relied on by
multiple merged tests, so provenance was established in earlier sessions this digest already records).

| Element | Testid / handle | Provenance | Notes |
|---|---|---|---|
| Message input | `chat-message-input` | on-`main` ✓ | Reused as-is — `ChatPage.message_input`. |
| Hash-search results container | `chat-hash-search-results-list` | on-`automation/testids` only (ELITEA-2206, this session) | Reused verbatim from the ELITEA-2206 unit merged earlier on this batch trunk — do not re-add. |
| Per-card item | `chat-hash-search-item-{project_id}_{id}` (dynamic) | on-`automation/testids` only (ELITEA-2206, this session) | `ChatPage.HASH_SEARCH_ITEM` template constant + `get_hash_search_items()`/`get_hash_search_item()`, reused as-is. Live-confirmed this session: clicking `chat-hash-search-item-1_280` ("Agent testing skills") selected it. |
| Per-card subtitle (`agent`/`pipeline`) | `{testId}-type` (dynamic) | on-`automation/testids` only (ELITEA-2206, this session) | `ChatPage.HASH_SEARCH_ITEM_TYPE` + `get_hash_search_item_subtitle()` — THIS family's own new usage: filter cards by this to guarantee an agent (not pipeline) is selected, addressing gap 1 above. First caller that actually branches logic on the subtitle value rather than only asserting it exists — still the same testid, no new one needed. |
| Composer active-participant chip | `chat-switch-participant-button` | on-`automation/testids` ✓ (pre-existing, ELITEA-1736 rework, already relied on by merged tests per this digest) | `ChatPage.switch_participant_button` + `is_agent_participant_in_composer(agent_name)` — reused as-is. Live-confirmed this session: text contains "Agent testing skills" after selection. |
| Composer chip avatar | `chat-switch-participant-avatar` | on-`automation/testids` ✓ (pre-existing, ELITEA-2362) | `ChatPage.CHAT_SWITCH_PARTICIPANT_AVATAR` + `get_switch_participant_avatar()` — available if a future pass wants to assert the icon specifically; not required to satisfy either case's literal wording (name + mention-indicator is sufficient). |
| AGENTS participants badge (collapsed) | `chat-participants-badge-agents` (`PARTICIPANTS_BADGE.format("agents")`) | on-`main` ✓ (pre-existing, ELITEA-1793 rework) | `is_participants_badge_visible(section="agents")` / `wait_for_participants_badge_absent(section="agents")` — reused as-is for BOTH the "absent initially" and "present after select" and "still present after response" assertions. |
| AGENTS badge clickable trigger | `chat-participants-badge-button` | on-`main` ✓ | `open_participants_popover(section="agents")` — reused as-is. |
| Participants popper container | `chat-participants-popper` | on-`main` ✓ | Reused as-is. |
| Per-participant row (expanded/popover) | `chat-participant-row-{uniqueId}` (dynamic; agent uniqueId = `application_{agent_id}_{project_id}`) | on-`main` ✓ (pre-existing, ELITEA-1793) | `ChatPage.PARTICIPANT_ROW` — live-confirmed this session as `chat-participant-row-application_280_1` for the selected agent. Row text includes the agent name + a "ver" version control; icon is the row's leading avatar element (same structural position as `PARTICIPANT_AVATAR` in the expanded-panel row shape — this popover row is the SAME shared row component, not a separate one). |
| Remove-agent hover button | `chat-participant-remove-button` | on-`main` ✓ (pre-existing, ELITEA-1793) | `remove_agent_participant(agent_id)` — reused as-is for this AFS's own Cleanup step; not part of either case's asked-for assertions. |
| Remove-confirm dialog button | `delete-confirm-button` | on-`main` ✓ (pre-existing) | Confirms the "Remove agent?" dialog — used only for Cleanup, not case-asked. |

**Provenance grep (this session, fresh `git fetch origin` first) — only NEW-to-this-family handles,
the rest are pre-existing and already relied upon by merged specs per this digest's own prior entries:**
```
chat-switch-participant-button          main:YES (pre-existing, ELITEA-1736)
chat-participants-badge-agents          main:YES (pre-existing, ELITEA-1793)
chat-hash-search-item-{}_{}-type        testids:YES (EliteaAI/EliteaUI@58d30f08, ELITEA-2206 this session) main:no
```
No genuinely new testid is needed for this family — every handle either already exists on `main`, or was
already added by the ELITEA-2206 unit earlier in this same batch/session.

## Network Behavior
- Selecting a participant via `#` is client-side state (no network call at selection time) — same
  "no network call at keystroke/click time" pattern this digest already documents for the sibling
  attachment-chip and hash-search-open surfaces.
- Sending "hello" fires the normal chat-send request/WebSocket flow already covered by every other
  message-send test in this suite — no new network assertion needed; `wait_for_ai_response()` already
  waits past it via its own `wait_for_network()` call.

## Known Defects Found During Exploration
None. Live product behavior matches both cases' own intent on every gap assertion — the "message
field" wording is a case-text clarification (see Axis 2), not a defect.

## Blocked Steps
None.

## Automation Hints
- Framework: Playwright + pytest, testid-only `LocatorDescriptor` (`.agents/testing.md`).
- Implement as a NEW test method in `TestHashSearch` (`test_chat_interface.py`) — do not modify
  `test_hash_search_participants`/`test_add_participant_via_hash_search`/
  `test_hash_search_shows_agents_and_pipelines_from_all_sources`'s existing bodies (additive-only).
- **Use the `conversation_id` fixture** (fresh, API-seeded, zero participants) rather than an existing
  conversation — this is what makes the "no AGENTS initially" assertion (both cases' own Step
  1/2) trivially true and deterministic, and avoids the shared-conversation contention this digest
  already documents elsewhere (`/chat` bare redirecting, multi-session conversation collisions). This
  session's own live exploration used an existing conversation (`/chat/9082`) only because a bare
  `/chat` navigation hit a persistent loading-spinner block on this heavy ambient account (65+ folders)
  — not a product defect, just an artifact of this account's data volume; the fixture sidesteps it
  entirely by not depending on the sidebar's folder list finishing its own load.
- **Family parameterization**: one test method (or `@pytest.mark.parametrize`) covering both TMS ids via
  two `@allure.issue` decorators, same pattern as ELITEA-2179/2466's family AFS. ELITEA-2469's extra
  name+version+icon row assertion (Coverage Map row 7) is the only per-case delta — implement it as an
  additional assertion block tagged for ELITEA-2469 specifically if using one shared method, or as a
  second thin test reusing the same setup if parametrizing.
- **Agent selection must filter by type**: do NOT reuse `get_hash_search_first_option()` as-is (it may
  resolve a pipeline). Iterate `get_hash_search_items()`, resolve each item's `get_hash_search_item_subtitle()`,
  and click the first one where it equals `"agent"` (lowercase — case-text says "Agent" capitalized,
  same ELITEA-2206-documented drift).
- Query string: bare `#` is sufficient (matches all participants; this session's first-page results
  already included multiple agent-type cards, e.g. "Agent testing skills", "AA", "el-1795-agent-...").
- Wait strategy: reuse `wait_for_hash_search_dropdown()` for open; after clicking an agent card, wait on
  `is_participants_badge_visible(section="agents")` (condition wait, not a fixed sleep) before asserting
  the popover contents — the badge's appearance is the correct signal that the participant-add mutation
  has landed client-side.
- For the send+response step: capture `initial_count = get_message_count()` before `send_message("hello")`,
  then `wait_for_ai_response(initial_count)` — standard pattern already used by every other
  message-send test in this file.
- Cleanup: call `remove_agent_participant(agent_id)` in a `finally`/fixture-teardown style if the test
  seeds via UI-selection rather than an API precondition, so a failed assertion mid-test doesn't leak a
  participant into a conversation that then gets deleted anyway by the `conversation_id` fixture's own
  teardown — actually not required for correctness (the fixture deletes the whole conversation
  afterward), but keeps behavior symmetric with this AFS's own live-exploration Cleanup note. Optional,
  not a correctness requirement since `conversation_id` fixture deletes the entire conversation
  (participant and all) on teardown regardless.
