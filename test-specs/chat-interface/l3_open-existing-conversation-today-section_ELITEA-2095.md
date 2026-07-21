# Test Case: Chat — Open Existing Conversation from Today Section — Verify Full History, Active Input, Model Name, Context Budget, and Correct Participant

## Metadata
- **TMS ID**: ELITEA-2095
- **Linked Story**: [EliteaAI/elitea-testing-public#298](https://github.com/EliteaAI/elitea-testing-public/issues/298) (originating tracking issue)
- **Priority**: l3 (case frontmatter says `priority: medium` → 3=medium per AFS convention)
- **Environment Explored**: local (`http://localhost:5173`, EliteaUI `automation/testids` branch → DEV backend)
- **User set**: `${TEST_USER}` (on localhost, `auth_state` fixture skips login via `VITE_DEV_TOKEN` — dev-token user renders as "Test Bot"/"TB" avatar in the UI)
- **Analyst**: qa-engineer, analyst slot
- **Status**: **ready-for-automation** — case executed end-to-end live (all 8 steps observed against real, freshly-generated message history), no product defects found. A substantial testid gap exists (8 new testids, detailed below) — flagged as implementer work per policy, not softened into a defect or a blocker.

## Overlap check vs existing automation (required before classifying `ready-for-automation`)

Two existing tests brush this case's surface but neither covers its actual observable:

- `automation/tests/ui/chat/test_conversation_management.py::TestConversationList::test_click_conversation_to_open`
  (TC-CONV-004) covers a miniature of case steps 1–3: create a conversation via API, navigate to
  `/chat`, click it in the sidebar by name (`select_conversation_from_list`, a raw `text="{name}"`
  locator — NOT scoped to the Today group), verify the URL contains the conversation ID. It does
  **not**: scope the click to the Today date-group specifically, seed real message history, or
  assert scroll, active-input, model/agent name, Context Budget, or PARTICIPANTS panel — i.e. 5 of
  this case's 8 steps (4–8) have zero existing coverage.
- `automation/tests/ui/chat/test_context_management.py::test_context_budget_reflects_profile_max_tokens`
  covers Context Budget panel visibility and asserts `get_context_budget_max_tokens()` against the
  agent's configured profile — a different observable (max-tokens-matches-config, not
  Messages/Summaries counters) and a different flow (fresh conversation created and immediately
  used in the same session, not "opened from the Today section" after navigating away).

Given 5 of 8 case steps are wholly uncovered and the 2 touched steps use raw, non-Today-scoped
locators, extending either covering test would amount to a near-rewrite (new fixtures, new
project-switch flow, new Today-section scoping, four new assertion blocks) — this is
**`ready-for-automation`** (fresh spec), not `extend-existing`, per the skill's boundary rule.
`test_click_conversation_to_open` remains valid, complementary coverage for the general
click-to-open flow; this case adds Today-section scoping + the steps-4-8 assertions instead of
duplicating it.

## Preconditions
- User is logged in to the Elitea platform (`auth_state` — no-op on localhost).
- At least one conversation exists, or is created, in the **Today** section of the target project.
- **Reverse-masking guard — project choice is load-bearing, not incidental.** Case step 1 allows
  "the Private or Team project"; live exploration proved these are NOT interchangeable for step 8.
  Confirmed live via `document.querySelectorAll('[data-testid^="chat-participants-badge"]')`
  returning `[]` in the default Private project (`399`) for a bare-LLM conversation with zero
  added participants — **no participant badge renders there at all**, matching the already-filed,
  structural (not-a-defect) finding in the sibling `ELITEA-2094` AFS:
  `showUsersSection = !isPrivateProject` in `CollapsedPerticapantsList.jsx` unconditionally omits
  the whole Users/owner badge for the account's own Private project. Switching to a **Team**
  project (confirmed live: `471` "Elitea Testing Team", same project the `ELITEA-2094` AFS used)
  renders a "Users in this conversation" badge (collapsed) and a "USERS" section with the owner's
  avatar (expanded) — this is the ONLY environment where case step 8 ("PARTICIPANTS panel shows
  the correct participant") is genuinely assertable for a plain default-LLM conversation with no
  added agent/pipeline/toolkit/mcp participant. **Automation must target the Team project, not the
  default `ELITEA_PROJECT_ID=399`.**

## Test Data

### reuse-existing
- Project `471` ("Elitea Testing Team") — established, reused non-Private test project (also used
  by `ELITEA-1893` and `ELITEA-2094` AFS explorations); `ConversationAPI(project_id="471")`.

### generate-per-test (in test setup, cleaned up in its own teardown)
- **AMENDED (implementer Phase 2, confirmed live 4/4 attempts) — do NOT create the seed
  conversation via `ConversationAPI(...).create_conversation(name)`.** Sending the first UI
  message to a conversation that exists server-side with ZERO messages (whether opened via
  direct `/chat/{id}` navigation or via a sidebar-list click) does not append the message to
  that conversation — it silently creates a BRAND-NEW conversation instead (auto-titled from
  the message text) and leaves the API-created one orphaned and permanently empty. This is a
  confirmed product defect, filed as
  [EliteaAI/elitea-testing-public#691](https://github.com/EliteaAI/elitea-testing-public/issues/691)
  (root-caused to `ChatBox.jsx`'s `!activeConversation?.uuid` gate not being populated for a
  freshly-loaded, zero-message conversation). **Implemented instead**: seed the conversation via
  the UI's own `+Chat` flow (`ChatPage.click_create_conversation()`), matching the already-proven
  pattern in `test_create_conversation_via_ui_button` / `test_context_budget_reflects_profile_max_tokens`
  — the conversation id and (auto-generated) name are captured from the URL/API *after* the first
  send succeeds, not assigned in advance. Case coverage is unaffected: the case exercises the same
  8 elements (Today section, scroll, input, model, Context Budget, PARTICIPANTS) regardless of how
  the seed conversation came into existence.
- **Real message history, generated via UI** (required for a genuine step-4 scroll assertion —
  CSS `overflow` alone doesn't prove scrollability without content that overflows): send **two**
  message exchanges via `chat.send_message(...)` + `chat.wait_for_ai_response(...)`, e.g.
  `"Give me a short 5-item numbered list of fun facts about octopuses."` then a follow-up
  `"Thanks! Now give me 5 more facts, this time about jellyfish."`. Confirmed live: 4 messages
  (2 user + 2 AI) produced `scrollHeight: 1369` vs `clientHeight: 664` on the scroll container —
  clearly overflowing, genuinely scrollable. Two exchanges is the *minimum* confirmed live to
  reliably overflow the default viewport; do not reduce to one.
- This conversation naturally lands in the **Today** date-group once created/modified (server
  groups by last-activity date) — no separate "seed Today" step is needed beyond creating +
  messaging it in the current test run.
- **ADDED (PR #693 fix-only pass, reviewer finding #2) — a second, throwaway "other" conversation,
  created via `ConversationAPI.create_conversation(name)` (plain API create, zero messages, no
  `+Chat`/UI flow involved) so Step 2's "navigate away" click has a real OTHER conversation to
  target.** `ChatPage.click_first_other_conversation()` originally depended on an ambient,
  pre-existing conversation already being present in project 471 for this — an undocumented
  dependency the review correctly flagged, since nothing in this suite guarantees project 471
  always holds >=2 conversations (other tests clean up their own). Resolved by seeding this second
  conversation explicitly rather than documenting the ambient dependency as a precondition,
  because no fixture or other test actually guarantees a stable second conversation exists — the
  "reuse-existing" bucket would have recorded a precondition that isn't reliably true. Defect
  #691 (see above) does NOT apply to this conversation: #691 fires only when the first UI
  *message* is sent to a zero-message conversation, and no message is ever sent to this one — it
  exists purely to be clicked. Confirmed live (via the pre-existing sibling test
  `test_navigate_between_conversations` in `test_conversation_management.py`) that a plain
  API-created, zero-message conversation renders in the sidebar and is clickable. Cleaned up in
  the same test-level `finally` block as the primary seeded conversation.

## Test Steps

1. Navigate to the chat page (`chat.navigate_to_chat()`), confirm default/last-active project,
   then switch the active project to the Team project (`471`) via the sidebar project selector.
   - **Verify**: project selector shows "Project: {team project name}" / `471` in the id textbox.
2. Ensure the test's freshly-created + messaged conversation is visible in the sidebar list, then
   navigate away from it first (e.g. bare `/chat`, or open/click a different item) so the
   subsequent click is a genuine "open an EXISTING conversation" action, not a no-op on an
   already-open one.
3. Locate the **Today** heading in the middle (sidebar) panel.
   - **Verify**: "Today" heading is visible; it is in the expanded state (its `MuiCollapse`
     wrapper renders the conversation items, not collapsed-to-zero-height); at least one
     conversation button (the test's own conversation) renders directly under it.
4. Click the test's conversation from the Today list.
   - **Verify**: URL becomes `/chat/{conversation_id}`; the conversation's title text is shown.
5. Verify full message history renders with all 4 seeded messages (2 user + 2 AI) visible in
   the messages list, in original send order.
6. Verify the scroll container is genuinely scrollable.
   - **Verify**: `scrollHeight > clientHeight` on the scroll container; perform an actual scroll
     (e.g. `mouse_wheel` or `evaluate` setting `scrollTop`) and confirm `scrollTop` changes —
     don't stop at the CSS-overflow check alone, since a `overflow-y: scroll` container with no
     overflowing content would pass a height-only check without proving real scroll behavior.
7. Verify the message input field is active/ready.
   - **Verify**: `chat-message-input` is visible, editable (not disabled), and empty.
8. Verify the model/agent name is displayed in the composer's model-selector button.
   - **Verify**: `model-selector-button` text is non-empty (confirmed live: `"GPT-5.4"` for this
     conversation — the conversation's own configured model, not a hardcoded default).
9. Verify the Context Budget widget shows Messages and Summaries counters.
   - **Verify**: `context-budget-panel` visible; `context-budget-tokens` text matches
     `\d+\s*/\s*[\d\s]+tokens` (confirmed live: `"119 / 32 000 tokens"`); Messages counter reads
     `"4"` (matches the 4 seeded messages); Summaries counter reads `"0"` (no summarization
     triggered yet at this token volume).
10. Verify the PARTICIPANTS panel shows the correct participant.
    - **Verify**: expand the panel if collapsed; a "USERS" section is present containing exactly
      one avatar with the conversation owner's initials (confirmed live: `"TB"` = Test Bot, the
      dev-token user); this matches the conversation's actual owner (cross-check via
      `conversation_api.get_conversation(id)`'s owner/creator field, not just a DOM read).

## Expected Results
- Conversation opens with all 4 seeded messages visible, in original order, no console errors.
- The messages region is scrollable (`scrollHeight > clientHeight`; scrollTop changes on scroll).
- The message input is visible, enabled, and empty — ready for the next message.
- The composer's model-selector shows a non-empty model name matching the conversation's config.
- The Context Budget widget shows a tokens-used/tokens-max string, a `Messages:` count matching
  the actual message count, and a `Summaries:` count (0 for this data volume).
- The PARTICIPANTS panel, once expanded, shows exactly one USERS entry whose avatar/initials match
  the conversation's actual owner.
- No console errors specific to this flow (see § Network Behavior for one already-documented,
  unrelated 403 observed in this same project).

## Coverage Map

**Axis 1 — Case coverage.**

| Case element | Expected result | Covered by (AFS step) | Asserted where | Disposition |
|---|---|---|---|---|
| 1 Navigate to Private or Team project, go to Chats | Chats page displayed | AFS steps 1–2 | step 1: project selector text; step 2: chat page loaded | asserted *(project choice narrowed to Team — see Preconditions reverse-masking guard)* |
| 2 Locate Today section, verify expanded with conversations listed | Today section visible with conversations | AFS step 3 | step 3: "Today" heading visible + ≥1 conversation item under it | asserted |
| 3 Click a conversation from the Today list | Conversation content displayed with full message history | AFS step 4–5 | step 4: URL + title; step 5: all 4 messages present in order | asserted *(decomposed)* |
| 4 Verify scroll functionality is available | Message history is scrollable | AFS step 6 | step 6: `scrollHeight > clientHeight` + actual scroll interaction changes `scrollTop` | asserted |
| 5 Verify message input field is active and ready | Input field is active | AFS step 7 | step 7: `chat-message-input` visible + editable + empty | asserted |
| 6 Verify model/agent name displayed in input bar | Model/agent name visible | AFS step 8 | step 8: `model-selector-button` non-empty text | asserted |
| 7 Verify Context Budget indicator with Messages and Summaries counters | Context Budget widget visible | AFS step 9 | step 9: `context-budget-panel` visible, tokens text, Messages=4, Summaries=0 | asserted |
| 8 Verify PARTICIPANTS panel shows correct participant | PARTICIPANTS panel shows correct participant | AFS step 10 | step 10: USERS section avatar matches conversation owner (API cross-check) | asserted *(requires Team project — see Preconditions)* |
| Pass criteria: "All steps complete without errors... all expected UI elements visible" | — | all steps | console-error check (Axis 2) + all above | asserted |

Disposition: all `asserted`. No `blocked` / `clarification` / `out-of-scope` rows — every case
element was executable and confirmed live in this run (in the Team project; see Preconditions for
why Private alone would leave step 8 unassertable, which is documented, not silently dropped).

**Axis 2 — Analyst additions.**

- AFS step 1 asserts the project switch **actually happened** (project id textbox reads the
  target id) — *added: without this, a no-op click on the project selector would silently leave
  the test in the wrong project and step 8 would then fail for the wrong reason (private-project
  suppression) instead of a clean "project switch didn't work" signal.*
- AFS step 5 asserts message **order**, not just count — *added: confirmed live the octopus
  Q&A pair renders before the jellyfish Q&A pair; an order-blind count check would pass even if
  the SPA re-rendered messages out of sequence.*
- AFS step 6 performs a real scroll interaction, not just a CSS-property read — *added: an
  `overflow-y: scroll` container with content that happens to fit exactly would pass a
  height-only check without ever proving the user can actually scroll.*
- AFS step 9 cross-checks the Messages counter against the actual seeded message count (4) rather
  than asserting "a number is present" — *added: a stale/off-by-one counter would otherwise slip
  through a presence-only check.*
- AFS step 10 cross-checks the DOM-rendered owner initials against the conversation's real
  owner via the API — *added: a DOM-only check ("some avatar renders") wouldn't catch the panel
  showing the WRONG participant, which is literally what case step 8's wording ("correct
  participant") asks for.*
- Console-error check after every navigation/click — *added: standard side-channel discipline;
  confirmed clean (0 errors) throughout this run except one already-documented, project-scoped,
  unrelated 403 (see § Network Behavior).*

## Cleanup
1. Delete the test's seeded messages / conversation via `conversation_api.delete_conversation(id)`
   (or `ChatPage.delete_message()` ×2 if the fixture reuses a pre-existing conversation instead of
   creating a fresh one — this analyst run used a pre-existing "HI Chat" conversation in project
   471 for exploration and cleaned it back to its original 2-message state via the UI Delete
   action on the AI message, which removes the paired user+AI messages together).
2. No credential/toolkit data created — nothing else to clean up.

## Concrete Handles (discovered during exploration)

Locator policy: **testid-only** (`.agents/testing.md` § Locator policy,
`.agents/role-overrides.md`). No role/text/CSS fallback rungs — a missing testid is listed as
`testid needed: {section}-{element}-{type}`, never a raw handle.

| Element | testid | Provenance | Notes |
|---|---|---|---|
| Message input | `chat-message-input` | on-`automation/testids` ✓ (confirmed live) | Matches existing `ChatPage.message_input`. |
| Composer model-selector button | `model-selector-button` | on-`automation/testids` ✓ (confirmed live) | Matches existing `ChatPage.model_selector`. Text = model name (confirmed live: `"GPT-5.4"` / `"Anthropic Claude 4.5 Sonnet"` depending on project). |
| Context Budget panel container | `context-budget-panel` | on-`automation/testids` ✓ (confirmed live) | Matches existing `ChatPage.context_budget_panel`. Contains the tokens line AND the Messages/Summaries rows (no distinct testids on those two rows yet — see gaps below). |
| Context Budget tokens text | `context-budget-tokens` | on-`automation/testids` ✓ (confirmed live) | Matches existing `ChatPage.context_budget_tokens_display`. Text format `"119 / 32 000 tokens"`. |
| Messages `<ul>` container | `chat-message-list` | on-`automation/testids` ✓ (confirmed live) | **Existing-code mismatch, not a new gap**: `ChatPage.messages_list` (line ~203) declares `testid="chat-messages-list"` (plural "messages") but the live DOM testid is singular `chat-message-list` — the field currently matches nothing and has zero call sites (`grep` confirmed). Flagging for the implementer to fix the field's testid string rather than propagate the typo into new code. |
| Message item (`<li>`) | `chat-message-item` | on-`automation/testids` ✓ (confirmed live) | Matches existing `ChatPage.messages_container`. 4 items confirmed live for the seeded history. |
| AI answer body content | `chat-answer-content` | on-`automation/testids` ✓ (confirmed live) | Not yet a `LocatorDescriptor` field; useful if the implementer wants text-content assertions distinct from the existing `_extract_message_body()` helper. |
| Project-switcher option (dynamic) | `select-option-{project_id}` | on-`automation/testids` ✓ (confirmed live for `399` and `471`) | Same shared `SingleSelectMenuItem` dynamic testid family already documented in `agent_detail_page.py`'s `FORK_PROJECT_OPTION` (different UI surface, same DOM component) — reuse the pattern, don't invent a new one. Template: `[data-testid="select-option-{}"]`. |
| Project-selector trigger (combobox) | **NO TESTID** | needs-adding | `testid needed: project-selector-trigger`. The `role="combobox"` element showing "Project: {name}" has zero testid at any ancestor level (checked 4 levels up, confirmed live). Needed to open the dropdown before `select-option-{id}` can be clicked. No existing `ChatPage`/other page-object method switches projects today — this is new automation surface. |
| Conversation date-group heading ("Today"/"Yesterday"/"Older") | **NO TESTID** | needs-adding | `testid needed: chat-conversation-group-header-{group}` (dynamic, e.g. `.format("today")`). The `<h6>` "Today" element and every ancestor up to the list container have zero testid (checked 5 levels up, confirmed live). This is the ONLY reliable way to scope "conversations under Today specifically" instead of the existing raw `:has(h6) > button` CSS locator in `get_conversation_list_items()` (tracked tech debt, not to be extended — role-overrides.md). |
| Conversation list item (dynamic, per conversation) | **NO TESTID** | needs-adding | `testid needed: chat-conversation-item-{conversation_id}`. The clickable conversation row is a `<div role="button">` (class `active-conversation` when selected — a STATE class, not an identity handle) with zero testid at any level (checked 10 levels up from the title text node, confirmed live). Needed to click precisely within the Today group rather than a name-text match. |
| Messages scroll container | **NO TESTID** | needs-adding | `testid needed: chat-messages-scroll-container`. Confirmed live: the actual `overflow-y: scroll` element (`aria-label="scrollable content"`, `scrollHeight: 1369` vs `clientHeight: 664`) sits 2 DOM levels ABOVE the already-testid'd `chat-message-list` `<ul>` — neither it nor any of its 3 checked ancestors/descendant levels carry a testid. |
| Collapsed "Users in this conversation" badge | **NO TESTID** | needs-adding | `testid needed: chat-participants-badge-users` — this is NOT a new pattern, just a new instance of the EXISTING `PARTICIPANTS_BADGE = '[data-testid="chat-participants-badge-{}"]'` template already in `chat_page.py` (currently only confirmed for `agents`/`pipelines`/`toolkits`/`mcp`, per the sibling `ELITEA-2094` AFS). Confirmed live this run: the `aria-label="Users in this conversation"` element has zero testid at 4 checked ancestor levels — closes the "confirmation gap" the `ELITEA-2094` AFS flagged as unconfirmed-not-yet-a-blocker; it's now confirmed to be a real, missing testid. |
| Expanded PARTICIPANTS panel "USERS" section avatar | **NO TESTID** | needs-adding | `testid needed: chat-participants-users-avatar`. Confirmed live: the expanded panel's "USERS" label + "TB" avatar chain (5 checked levels) carries zero testid. Needed to read WHICH participant is shown (avatar initials/name), not just that a Users badge exists — case step 8 says "correct participant", which requires identity, not mere presence. |
| Context Budget "Messages:" counter row | **NO TESTID** | needs-adding | `testid needed: context-budget-messages-count`. Lives inside the already-testid'd `context-budget-panel` container but has no distinct testid of its own; confirmed live text `"Messages: 4"` is two separate DOM nodes (label + value) with no testid on either. |
| Context Budget "Summaries:" counter row | **NO TESTID** | needs-adding | `testid needed: context-budget-summaries-count`. Same shape as the Messages row; confirmed live text `"Summaries: 0"`. |

## Implementer Amendment (Phase 2 exploration, ELITEA-2095)

All 8 flagged testid gaps were added to `EliteaAI/EliteaUI` on `automation/testids`
(commit `8a3627ef`) and confirmed live before writing the spec. Two technique-level
notes (scope of the case's assertions is unchanged — see the reverse-masking guard
in § Preconditions for why Team/471 remains load-bearing):

- **`project-selector-trigger` — declared improvisation.** The shared
  `SingleSelect` component (`EliteaUI src/[fsd]/shared/ui/select/SingleSelect.jsx`)
  has a pre-established convention: a base `data-testid` prop lands on the `Select`
  root, and `SelectDisplayProps` auto-suffixes `-combobox` onto the actual
  interactive `role="combobox"` node. No sanctioned shape existed for a bare,
  non-suffixed trigger testid on this shared component, so `SidebarProjectSelect.jsx`
  wires `data-testid="project-selector-trigger"` at the `ProjectSelect` call site
  and the implementer's `ChatPage.project_selector_trigger` field targets the
  realized `project-selector-trigger-combobox` — reusing the existing convention
  rather than inventing a new prop path. Confirmed live: clicking it opens the
  project dropdown correctly.
- **Step 1's "471 in the id textbox" verify clause** — implemented via the
  project-selector's own display text (`ChatPage.get_selected_project_text()`
  asserting `"Elitea Testing Team" in text`) instead of the separate hidden/
  readonly `<input>` sibling the AFS's Verify line mentions. That textbox was
  never listed as a testid gap in this table (only 8 gaps were flagged and
  added), and per the testid-only locator policy a raw, non-testid handle
  cannot be added for it without exceeding the dispatch's scope. The
  project-name text assertion fully proves the switch succeeded (it names the
  target project unambiguously) and is itself backed by a real testid
  (`project_selector_trigger`), so no case-level assertion strength is lost.
- **`chat-conversation-group-header-{group}`** is placed on `DateGroup.jsx`'s
  OUTER wrapping `Box` (which renders both the header row AND that group's own
  `Collapse`'d conversation items in one component instance), not narrowly on
  just the clickable header row — this is what makes DOM-containment-based
  Today-scoping (`ChatPage.is_conversation_in_group()`) actually work, per the
  AFS's own stated intent ("the ONLY reliable way to scope conversations under
  Today specifically").

### Product defects found during implementation (2, both filed — see § Known Defects Found)

- **#691 — orphaned empty conversation on first send.** Invalidated the AFS's
  originally-specified Test Data approach (create via `ConversationAPI.create_
  conversation()`, then message via UI). Worked around by seeding via the UI's
  own `+Chat` flow instead (see § Test Data "AMENDED" note above).
- **#692 — stale `active-conversation` flag blocks re-click.** A conversation
  created via `+Chat` and then navigated away from (Step 2) cannot be re-clicked
  from the sidebar for the rest of the session — `ConversationItem.jsx`'s
  `if (!isActive) onSelectConversation(...)` guard silently no-ops the click
  because `isActive` never clears for that specific conversation object.
  Worked around with a `page.reload()` immediately after Step 2's
  navigate-to-a-different-conversation click (confirmed live: reloading while
  ON the different conversation's URL forces a full state re-derivation that
  correctly clears the stale flag; a same-URL reload of the seeded conversation
  does NOT fix it). This reload is test-side plumbing, not a case step — it
  does not appear as its own `allure.step`.

## Network Behavior
- No case-relevant network calls beyond standard conversation load
  (`GET .../conversation/prompt_lib/{project}/{id}?messages_limit=...`) and the WebSocket used for
  AI responses during test-data setup (~2–10s per response, confirmed live: "Thought for 8 secs" /
  "Thought for 7 secs" / "Thought for 1 sec" / "Thought for 2 secs" across the two projects used).
- **Pre-existing, already-documented, unrelated artifact** (not filed as a new defect — it recurs
  exactly as described in the `ELITEA-1893` AFS § Test Data / § Handles Reference): project `471`
  surfaces a `403 Forbidden` on `GET /api/v2/secrets/secrets/default/471` on every page load,
  regardless of any action taken. Confirmed live again this run. Environment/permission-scoping
  artifact of that specific project, not a symptom of anything this case's automation touches —
  do not chase it, do not gate this case's assertions on it being absent.
- **Exploration-only artifact, NOT reproducible via the case's real flow** (self-inflicted, not
  filed): navigating directly to a conversation ID that belongs to a DIFFERENT project than the
  currently-active one (an artificial cross-project mismatch this analyst created while probing
  project-switch behavior) produces two `400 Bad Request`s
  (`select_conversation/prompt_lib/{wrong-project}/{id}` and
  `conversation/prompt_lib/{wrong-project}/{id}?...`). The AFS's own Test Steps never do this —
  step 1 switches the active project BEFORE any conversation is opened, so this mismatch cannot
  occur in the automated flow. Noted here only so a future debugger doesn't mistake it for a
  regression if seen in an unrelated exploratory session.

## Known Defects Found During Exploration
None found (analyst pass). All gaps identified during the analyst's run are **testid asks**
(implementer work per `.agents/testing.md` § Locator policy — "missing testid alone ⇒ add it",
not a defect) or **already-documented, unrelated environment artifacts** (the project-471 secrets
403, cited above with its origin). No new product defect was observed against this case's actual
objective during analysis.

**Implementer pass (Phase 2/3) — 2 found**, both filed and both worked around without changing the
case's assertions (see § Implementer Amendment above for full detail):
- [EliteaAI/elitea-testing-public#691](https://github.com/EliteaAI/elitea-testing-public/issues/691)
  — sending the first UI message to an API-created (zero-message) conversation silently creates a
  brand-new conversation instead of using the existing one.
- [EliteaAI/elitea-testing-public#692](https://github.com/EliteaAI/elitea-testing-public/issues/692)
  — a `+Chat`-created conversation stays permanently marked "active" after navigating away, making
  it unclickable to re-select (worked around with a `page.reload()`).

## Blocked Steps
None. All 8 case steps were executed and confirmed live end-to-end (in the Team project — see
Preconditions for why that project choice, not the default Private one, is required for step 8).

## Automation Hints
- Framework: Playwright + pytest, testid-only `LocatorDescriptor` (`.agents/testing.md`).
- Page object: extend `automation/pages/chat_page.py` — do not duplicate. Needs one new method to
  switch the active project (no existing method does this): something like
  `switch_project(project_id: str)` using `project-selector-trigger` (new field) →
  `SELECT_OPTION.format(project_id)` (new dynamic template constant, reusing the
  `select-option-{}` pattern already precedented in `agent_detail_page.py`'s
  `FORK_PROJECT_OPTION`).
- Test data: `ConversationAPI(browser_cookies=..., project_id="471")` to create the conversation
  directly in the Team project (avoids relying on the UI project-switch for TEST-DATA setup,
  while still exercising the UI project-switch as part of the case's own Step 1 action).
- Existing `get_conversation_list_items()` (`:has(h6) > button` raw CSS) is tracked tech debt
  (role-overrides.md) — do not extend it for Today-scoping; use the new
  `chat-conversation-group-header-today` + `chat-conversation-item-{id}` testids instead once
  added.
- Wait strategy: `wait_for_conversations_to_load()` (existing) after project switch, before
  asserting the Today heading / clicking the conversation. AI responses during test-data setup use
  the existing `wait_for_ai_response()` — confirmed live at 1–8s per response, well within its
  default timeout.
- **Unverified, not gated as a defect** (single occurrence during test-data setup, not
  independently reproduced clean): clicking `sidebar-create-button` (+Chat) while an existing
  conversation was already open in the Team project, then typing immediately, once appended the
  new message to the PREVIOUSLY-open conversation instead of starting a fresh blank one (title bar
  and history stayed on the old conversation until Send). This may simply be a race between the
  click and typing (no explicit wait for the blank "Hello, {name}!" greeting state was used before
  typing, unlike the Private-project path where this greeting was confirmed to render first). If
  the implementer's test-data setup uses `+Chat` in a non-default project, wait for the blank
  greeting text (or `chat.message_input` becoming empty/re-mounted) before typing — or sidestep
  entirely by using the API-only conversation creation recommended above.
- Messages/Summaries counter parsing: no existing helper isolates these two rows (only
  `get_context_budget_tokens_text()`/`get_context_budget_max_tokens()` exist, both scoped to the
  tokens line). Once `context-budget-messages-count` / `context-budget-summaries-count` testids
  are added, add matching getters rather than regex-parsing the whole panel's `textContent`.

## AFS Amendment (2026-07-21, PR #693 fix-only pass — reviewer findings #1 and #2)

A fresh reviewer session on PR #693 returned `CHANGES_REQUESTED` with two findings, both
addressed in the same fix-only commit:

**Finding #1 (BLOCKING) — the console-error check was manual analysis, never automated.** The
Coverage Map's Pass-criteria row and an Axis 2 bullet both claim a "console-error check" backs
the `asserted` disposition, and § Expected Results / § Network Behavior both describe checking
for console errors during the analyst's manual exploration — but neither the test nor
`chat_page.py` implemented any actual `page.on("console", ...)` handling; the claim was
manual-observation-only, never translated into a real automated assertion. **Resolution**:
`test_open_conversation_today_section.py` now registers `page.on("console", _on_console)`
immediately after `chat = ChatPage(page)` (before Step 1, so every step's console output is
captured), filtering only the already-documented project-471 `secrets` 403 (via
`_is_known_project_471_secrets_403()`, same filter idiom as `test_credential_create.py`'s
`_is_known_554_warning` — matched on both message text and request location URL so a genuinely
new 403 elsewhere isn't swallowed), and asserts `not console_messages` in a dedicated
"Side-channel check" step before cleanup. The Pass-criteria row's and Axis 2's "console-error
check" claims are now backed by a real assertion, not a manual-only observation.

**Finding #2 (non-blocking) — `click_first_other_conversation()`'s ambient-data dependency was
undocumented.** Addressed via Test Data § generate-per-test (see the new "ADDED" bullet above):
seeded a second, throwaway, zero-message conversation via `ConversationAPI.create_conversation()`
so Step 2 always has a real conversation to navigate to, independent of whatever else happens to
exist in project 471. Chose seeding over documenting a `reuse-existing` precondition because no
fixture in this suite actually guarantees a second conversation persists in project 471 (every
other test cleans up its own) — recording it as `reuse-existing` would have documented a
precondition that isn't reliably true, which is worse than the minimal, self-cleaning seed.

## AFS Amendment (2026-07-21, PR #693 round-2 fix-only pass — reviewer findings A, B, and the
pageerror gap)

A fresh reviewer session on PR #693 independently re-ran the merged spec live 5 times (not just
trusting the prior Run Report) and found 2/5 runs RED — two distinct, reproducible race
conditions in this PR's own new code, plus a non-blocking gap. All three addressed in the same
fix-only commit:

**Finding A (Critical) — `get_context_budget_messages_count()` / `get_context_budget_summaries_count()`
raced an async DOM update.** Both getters did a one-shot `.text_content()` read with no poll;
`wait_for_context_budget_panel()` only waits for the panel *heading* to appear, not for the
Messages/Summaries rows to reflect the correct value. Reproduced live: an assertion failure
reading `'0'` where the failure screenshot, captured moments later, already showed `Messages: 4`
rendered — the read raced ahead of an async update shortly after the panel appears.
**Resolution**: added `wait_for_context_budget_messages_count(expected, timeout)` /
`wait_for_context_budget_summaries_count(expected, timeout)` to `ChatPage`, using a
`.filter(has_text=...)` + `.wait_for(state="visible")` locator wait — the same idiom as the
existing `wait_for_message_count()` / `wait_for_context_budget_panel()` methods, not a new
poll-loop invention. The test now calls the wait method before each getter, mirroring the
established `wait_for_message_count()` + `get_message_count()` pattern used at Step 5.

**Finding B (Critical) — missing `wait_for_generation_complete()` between the first and second
message sends.** The test already applies `wait_for_generation_complete()` before Step 2 (with an
inline comment documenting exactly why `wait_for_message_content_stable()` alone isn't
authoritative — the app's internal streaming/nav-blocking flag can trail the text heuristic
briefly), but the identical race existed between the *first* message's response and the *second*
`send_message()` call, where no such guard was applied. Reproduced live: `send_message()`'s
`fill()` timing out because the input was still disabled. **Resolution**: added the same
`chat.wait_for_generation_complete(timeout=AI_RESPONSE_TIMEOUT)` call after the first message's
`wait_for_message_content_stable()`, before the second message is sent.

**Secondary (Important, non-blocking) — console-only side-channel missed uncaught JS exceptions.**
Per the same-day precedent on the sibling ELITEA-2094 PR (#688): `page.on("console", ...)` alone
does not catch uncaught exceptions, only `page.on("pageerror", ...)` does. **Resolution**: added a
`page.on("pageerror", _on_pageerror)` listener alongside the existing console listener, appending
to a `page_errors` list included in the same "Side-channel check" assertion
(`not console_messages and not page_errors`). The known project-471 secrets 403 is a
console/network log, not a pageerror, so no additional filtering was needed on the pageerror side.

Verified: 5 fresh consecutive `pytest` invocations of the same node id, headless,
`-p no:cacheprovider`, all GREEN post-fix (plus a 6th confirmatory run with `--log-cli-level=INFO`
confirming both seeded conversations' cleanup fired). No `chat_page.py` method body was modified —
only two brand-new methods added (their only caller is this test, so no shared-caller regression
risk) — and the test-file diff is purely additive per the usual self-check.
