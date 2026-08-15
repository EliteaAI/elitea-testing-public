# Test Case: Chat – Move Conversation to Existing Folder – Conversation Removed from Date Group

## Metadata
- **TMS ID**: ELITEA-2136
- **Linked Story**: none (case `requirements: []`)
- **Priority**: l3 (case frontmatter: `priority: medium` → `@pytest.mark.p2`, matching the
  ELITEA-2135/2137/2132 siblings' medium→l3/p2 mapping)
- **Environment Explored**: local (`http://localhost:5173`, EliteaUI `automation/testids`, DEV
  backend; project id 399, Private project — treat as `${ELITEA_PROJECT_ID}`)
- **User set**: `${TEST_USER}` — `auth_state`/`VITE_DEV_TOKEN` skips explicit login on localhost
- **Analyst**: test-automation-engineer (combined analyst+implementer), chat-remaining-w07
- **Status**: extend-existing
- **surface_key**: `chat-conversation-context-menu`

## Extension target
`automation/tests/ui/chat/test_move_conversation_to_folder.py::TestMoveConversationToExistingFolder::test_move_conversation_to_existing_folder`
(ELITEA-2135, merged `origin/automation/base`, commit `37dbd948`).

ELITEA-2136 is the SAME flow as ELITEA-2135 (move conv_target into `target_folder` via the "Move
to" submenu) with a stricter step 4: the case explicitly asks for "This Week" and "Older" to be
checked too, not just "Today". ELITEA-2135's own step 4 only asserts `conv_target` is absent from
the `"today"` group (its setup conversation is always created fresh, so it can only ever start in
Today) — it never asserts the `"this_week"`/`"older"` groups. Since a freshly-API-created
conversation cannot naturally be non-empty-in-those-groups anyway, the assertion is a genuine
belt-and-braces check (the SAME conversation, if it somehow rendered under multiple groups due to
a stale-cache regression, would be caught here) — not a duplicate of step 4's own "today" check.

No new test method — this is a **named-insertion-point extension** (Phase 3 "extend-existing"
mechanics, `test-automation-implementation` skill): two new `assert` lines land INSIDE the existing
`test_move_conversation_to_existing_folder`'s own `"Step 4"` `allure.step` block, immediately after
its existing `today`-group assertion. The rest of that test body (setup, steps 1–3, step 5, cleanup)
stays byte-identical.

## Preconditions
Identical to ELITEA-2135's own (reused conv_target/target_folder from the same setup — no separate
setup needed).

## Test Data
Identical to ELITEA-2135's own (`conv_target` via `conversation_api.create_conversation`,
`target_folder` named `"New folder6"` via the CHATS-header create-folder UI flow).

## Test Steps
1–3. Identical to ELITEA-2135's own steps 1–3 (open context menu, "Move to" submenu, select
   `target_folder`).
4. Verify `conv_target` is no longer rendered under **any** date-group heading — Today, This Week,
   AND Older (case's own step 4).
   - **Verify**: `chat.is_conversation_in_group(conv_target_id, "today")` is `False` (ELITEA-2135's
     existing assertion) **AND** `chat.is_conversation_in_group(conv_target_id, "this_week")` is
     `False` **AND** `chat.is_conversation_in_group(conv_target_id, "older")` is `False` (the two
     NEW assertions this case adds).
5. Identical to ELITEA-2135's own step 5 (expand `target_folder`, verify `conv_target` inside it).

## Expected Results
Same as ELITEA-2135, plus: the moved conversation is provably absent from every date-group bucket,
not merely the one it happened to start in.

## Coverage Map

### Axis 1 — Case coverage

| Case element | Expected result | Covered by (AFS step) | Asserted where | Disposition |
|---|---|---|---|---|
| 1 Note conversation name + date group (Today) | Conversation noted | Setup | `conv_target` created via API, renders under "today" by construction | asserted |
| 2 Hover conv, click 3-dot, hover Move to, select folder | Success toast appears | ELITEA-2135's steps 1–3 (unmodified) | ELITEA-2135's own Coverage Map | already-covered *(target: ELITEA-2135's own test, merged `origin/automation/base`)* |
| 3 Verify Today no longer contains it | Removed from Today | ELITEA-2135's step 4 (unmodified) | ELITEA-2135's own Coverage Map | already-covered |
| 4 Verify This Week and Older also do not contain it | Removed from all date groups | **NEW** — 2 assertion lines inserted into `test_move_conversation_to_existing_folder`'s Step 4 block | inline, immediately after the existing `today` assertion | asserted |
| 5 Verify conversation appears exclusively in the selected folder | Conversation only in folder | ELITEA-2135's step 5 (unmodified) | ELITEA-2135's own Coverage Map | already-covered |
| Pass/Fail: "Conversation remains in date groups or appears in multiple places" (Fail) | — | step 4 (extended) | the 3 negative-group assertions together | asserted |

Disposition key: `asserted` / `already-covered` / `clarification` / `blocked` / `out-of-scope`.

### Axis 2 — Analyst additions
- None beyond the case's own step 4 — no new observable is introduced, only a stricter version of
  an existing one (checking two more groups the case explicitly names).

## Cleanup
Unchanged — ELITEA-2135's existing `finally` block already deletes `conv_target` and
`target_folder`; no new resources are created by this extension.

## Concrete Handles (discovered during exploration)
No new handles. Reuses `ChatPage.is_conversation_in_group(conversation_id, group)` (pre-existing,
ELITEA-2135/2137 — already supports `"today"` / `"this_week"` / `"older"` per its own docstring;
live-confirmed this session by reading `chat_page.py` end-to-end, not re-derived).

## Network Behavior
Unchanged from ELITEA-2135 — no new requests fire from this extension (both new assertions are
pure DOM-state reads).

## Known Defects Found During Exploration
None new for this case.

## Blocked Steps
None.

## Automation Hints
- Insert the two new `assert not chat.is_conversation_in_group(conv_target_id, "this_week", ...)`
  / `"older"` lines directly after the existing `assert not chat.is_conversation_in_group(...,
  "today", ...)` line inside `test_move_conversation_to_existing_folder`'s `"Step 4"` `allure.step`
  block — same method, same timeout constant, no new page-object work.
- Verify additive-only via `git diff <base> -- automation/tests/ui/chat/test_move_conversation_to_folder.py
  | grep -E '^-[^-]'` — should show ONLY the two original assertion lines being replaced by
  themselves-plus-two-more inside the same step (i.e. no removed line, only added ones), confirming
  the existing three case elements this test already proves (ELITEA-2135's own steps 1,2,3,5) stay
  untouched.
