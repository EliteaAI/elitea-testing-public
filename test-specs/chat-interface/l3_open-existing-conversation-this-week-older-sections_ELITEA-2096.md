# Test Case: Open Existing Conversation from This Week / Older Sections (Family)

## Metadata
- **TMS ID (family)**: ELITEA-2096 (This Week), ELITEA-2097 (Older) —
  `family_afs: true`, this file is the single AFS for both cases (parameter
  table below has one row per case).
- **Linked Story**: none
- **Priority**: l3 (medium — both source cases declare `priority: medium`)
- **Environment Explored**: local (`http://localhost:5173`, EliteaUI
  `automation/testids` branch → DEV backend). Dev server confirmed running
  (`curl` 200) at run start.
- **User set**: `${TEST_USER}` (on localhost, `auth_state` fixture skips
  login via `VITE_DEV_TOKEN`)
- **Analyst**: qa-engineer, analyst slot (cluster dispatch alongside
  ELITEA-2098, one live session)
- **Status**: **blocked** — see § Blocked Steps. The flow itself (expand a
  collapsed date-group, click a conversation inside it, verify history/
  input/model/participants) is fully proven and page-object-supported —
  `ChatPage.is_conversation_group_visible(group)` /
  `click_conversation_in_group(id, group)` already accept `group="this_week"`
  and `group="older"` today (added ELITEA-2091/2095, confirmed live via
  source read, `automation/pages/chat_page.py:2723-2827`). What blocks
  execution is that **neither project this account can reach
  (Private/399, Elitea Testing Team/471) currently holds a single
  conversation dated outside "Today"**, and there is no honest way to
  produce one within a live test run (see below) — not a defect, not a
  missing handle.

## Family classification rationale

Per `test-case-analysis` § 3 "differ only in DATA vs. differ in STEPS":
ELITEA-2096 and ELITEA-2097 drive the **identical** flow (locate the
target date-group section → verify it is collapsed by default → expand it
→ click a conversation inside it → verify full history + active input +
model name + PARTICIPANTS panel) against the **same** `DateGroup`
component (`EliteaUI/src/[fsd]/features/chat/conversation-list/ui/groups/
DateGroup.jsx`) and the same `ChatPage` methods, differing only in which
`group` key (`this_week` vs `older`) is targeted. One parameterized spec,
2 data rows — both currently blocked by the identical environmental
constraint, so the blocker is documented once here rather than duplicated.

## Preconditions
- User is logged in to the Elitea platform (`${TEST_USER}` / localhost
  `auth_state`).
- **This Week (ELITEA-2096)**: at least one conversation dated after the
  start of the current calendar week but NOT today.
- **Older (ELITEA-2097)**: at least one conversation dated before the start
  of the current calendar week.
- `DEFAULT_EXPANDED_GROUP = 'today'` (source-confirmed,
  `conversationList.constants.js:9`) — This Week and Older render
  collapsed by default, matching both case texts exactly (not case-text
  drift).

## Test Data

### Parameter table (one row per source TMS case)

| # | Source case | Group key | `DATE_GROUP_DISPLAY_NAMES` label | Required conversation age |
|---|---|---|---|---|
| 1 | ELITEA-2096 | `this_week` | "This Week" | created after this week's start, before today |
| 2 | ELITEA-2097 | `older` | "Older" | created before this week's start |

Source: `EliteaUI/src/[fsd]/features/chat/conversation-list/lib/constants/conversationList.constants.js`.

## Test Steps (per parameter row, once unblocked)

1. Navigate to the Chats page
   - **Verify**: Chats page displayed
2. Locate `{group}`'s date-group header; verify it is collapsed by default
   (no conversation items rendered beneath it yet)
3. Click the `{group}` section header to expand it
   - **Verify**: `is_conversation_group_visible(group)` true, and the seed
     conversation is visible via `is_conversation_in_group(id, group)`
4. Click the seeded conversation inside `{group}`
   - **Verify**: URL contains the conversation id; browser title shows its
     name
5. Verify full message history renders with scroll (mirrors ELITEA-2095
   steps 5–6, same `ChatPage` methods)
6. Verify the message input is active (`message_input.is_editable()`)
7. Verify the model/agent name is displayed (`get_selected_model()`
   non-empty)
8. Verify the PARTICIPANTS panel shows the correct participant
   (`expand_participants_panel()` + `get_participants_user_avatar_text()`,
   cross-checked against `ConversationAPI.get_conversation()`'s
   `participants` field — same idiom as ELITEA-2095)

## Expected Results
- Target section expands on click; conversation opens with full history
  and active input, correct model name, correct PARTICIPANTS entry.
- No console errors / uncaught exceptions across the flow.

## Coverage Map

### Axis 1 — Case coverage

| Case element | Expected result | Covered by (AFS step) | Asserted where | Disposition |
|---|---|---|---|---|
| ELITEA-2096 step 2 / ELITEA-2097 step 2: section collapsed by default | only label + arrow shown | step 2 | — | blocked |
| ELITEA-2096 step 3 / ELITEA-2097 step 3: expand section | conversations listed | step 3 | — | blocked |
| ELITEA-2096 step 4 / ELITEA-2097 step 4: click conversation | full history + scroll | step 4–5 | — | blocked |
| ELITEA-2096 step 5 / ELITEA-2097 step 5: input active | input ready | step 6 | — | blocked |
| ELITEA-2096 step 6 / ELITEA-2097 step 6: model/agent name shown | name visible | step 7 | — | blocked |
| ELITEA-2096 step 7 / ELITEA-2097 step 7: PARTICIPANTS correct | correct participant shown | step 8 | — | blocked |

Every row is `blocked` for the identical reason (§ Blocked Steps) — not a
per-step gap, a precondition-level block.

### Axis 2 — Analyst additions

- None beyond the case (execution never reached the point of adding
  observables).

## Cleanup

n/a — no test data was created for these two cases (blocked before seeding
was attempted; see § Blocked Steps for why seeding isn't possible).

## Concrete Handles (discovered during exploration — confirmed working live via ELITEA-2098's sibling flow this session)

Provenance verified fresh (`cd ../EliteaUI && git fetch origin` run this
session) against `origin/main` and `origin/automation/testids` — **all
YES/YES, zero new testids needed** once the data blocker is resolved:

| Element | Locator (`LocatorDescriptor` / class constant) | Provenance |
|---|---|---|
| Date-group header (dynamic) | `CONVERSATION_GROUP_HEADER = '[data-testid="chat-conversation-group-header-{}"]'`.format(`"this_week"` / `"older"`) | on-main ✓ |
| Conversation item scoped in group | `CONVERSATION_ITEM = '[data-testid="chat-conversation-item-{}"]'`, scoped under the group header (see `ChatPage.is_conversation_in_group()`) | on-main ✓ |
| Message input | `message_input` (`LocatorDescriptor`, existing field) | on-main ✓ |
| Model selector name | `model_selector_name` (existing field, `get_selected_model()`) | on-main ✓ |
| Participants toggle | `chat-participants-panel-toggle-button` (existing field, `expand_participants_panel()`) | on-main ✓ |

No `testid needed:` rows — every handle this flow touches already exists
and is exercised successfully by the sibling ELITEA-2095 (Today) and
ELITEA-2098 (Folder, this same session) specs. The blocker is data, not
handles.

## Network Behavior

- `GET .../elitea_core/conversations/prompt_lib/{project_id}?grouped=true`
  — **the date-group bucketing (`today`/`this_week`/`older`) is computed
  SERVER-SIDE**, confirmed via source read
  (`EliteaUI/src/[fsd]/features/chat/conversation-list/api/
  conversationList.api.js:47-91`, `grouped: true` param on both the
  top-level list query and the paginated per-group `conversations` query
  at line 88). This is the load-bearing fact behind the blocker below —
  the client does not compute the bucket from a locally-readable `Date`,
  so no client-side timing trick (e.g. Playwright `page.clock`) can move a
  same-day conversation into a different bucket; only the server's own
  clock and the conversation's real `created_at` decide the bucket.

## Known Defects Found During Exploration

None. No product defect — this is a test-data/environment constraint (see
§ Blocked Steps).

## Blocked Steps

**Root cause:** both cases require a conversation that is genuinely older
than "today" (This Week: 1–6 days old; Older: 7+ days old), and there is
no honest way to produce that inside a single live test run:

1. **Grouping is server-computed** from the conversation's real
   `created_at`/`updated_at` (confirmed via source, § Network Behavior) —
   not a client-side date computation, so mocking the browser's clock
   (`page.clock`) would have zero effect on which bucket a conversation
   renders in. This rules out the one timing-control technique that is
   fidelity-compliant (`.agents/testing.md` § Fidelity policy) for
   date-dependent UI.
2. **The API cannot backdate a conversation.** Confirmed via the live
   OpenAPI spec (`GET /shared/openapi/?plugins=elitea_core&all=true` on
   `dev.elitea.ai`, `ConversationUpdate` schema): the PUT
   `/elitea_core/conversation/{mode}/{project_id}/{id}` payload accepts
   only `name`, `is_private`, `folder_id`, `attachment_participant_id`,
   `instructions`, `is_hidden`, `meta` — no `created_at` or any other
   timestamp field. `ConversationCreate` likewise has no timestamp
   override. There is no supported way to seed a conversation dated in
   the past via this API.
3. **The environment currently has zero non-today data.** Queried both
   accessible projects live via `ConversationAPI.list_conversations()`
   this session: Private/399 — 2 rows, both `created_at`/`updated_at`
   2026-08-14 (today); Elitea Testing Team/471 — 1 row, same day. This is
   consistent with every prior chat AFS in this feature area seeding its
   own conversations and deleting them in a `finally` block
   (ELITEA-2095/2091/2098 all do this) — nothing is left around long
   enough to age into a later bucket.
4. **Fabricating the bucket via `page.route()`/`page.evaluate()` would be
   a TERMINAL substitution**, forbidden per `.agents/testing.md` §
   Fidelity policy — the case's own observable (does the real product's
   server-computed grouping correctly place and render this conversation)
   would be read off a value the test itself wrote, not the system. The
   case text does not ask for simulation, so this route is closed.

**What would unblock this (for a human to decide):**
- Seed 1–2 durable conversations now, deliberately NOT cleaned up, and
  accept the case stays `blocked` until they naturally age past the
  This-Week/Older calendar boundaries (unverified how many real days
  This-Week actually requires — depends on the server's own week-start
  convention, not inspected further this session since it doesn't change
  today's disposition either way); or
- A test-data seeding endpoint / DB fixture that can set `created_at`
  directly (environment/backend change, out of this repo's control); or
- Accept the manual-only status for these two cases until aged data
  exists organically from the campaign's own ongoing activity (127-case
  chat-remaining campaign will, over several real days, naturally leave
  some conversations that age past Today — worth re-probing on a later
  wave rather than this session).

Routed to the lead per `test-case-analysis` § Classify findings ("the
observable cannot be produced honestly... route it: AFS blocked → lead →
a question card for a human").

## Automation Hints

- Framework: Playwright + pytest (confirmed).
- Page object: `automation/pages/chat_page.py` — `is_conversation_group_visible()`,
  `get_conversation_group_header()`, `get_conversation_item_in_group()`,
  `is_conversation_in_group()`, `click_conversation_in_group()` all already
  accept `group="this_week"` / `group="older"` (docstrings enumerate both)
  — zero new page-object work needed once data is unblocked.
- Once unblocked, this can reuse `test_open_conversation_today_section.py`
  (ELITEA-2095) near-verbatim, parameterized over `group` — same class
  shape, same seeding pattern (UI `+Chat` flow, not `ConversationAPI.
  create_conversation()`, per the ELITEA-2095 docstring's documented
  #691 workaround), only the wait for the conversation to actually AGE
  into the target bucket is new and currently has no known mechanism.
