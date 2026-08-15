# Test Case (family): Chat – Move Conversation Back to the List via Move To Menu

## Metadata
- **TMS IDs**: ELITEA-2139 ("Move Conversation Back to the List via Move To Menu"), ELITEA-2140
  ("Conversation Moved from Older Back to List Appears in Today")
- **family_afs**: true — same flow (a conversation inside a folder, moved back to the general list
  via "Move to" → "Back to the list"), same steps, same assertions; ELITEA-2140 differs from
  ELITEA-2139 only in ONE extra assertion (explicit absence from "Older") and a precondition detail
  addressed below, not in the interaction sequence itself.
- **Priority**: l3 for both (case frontmatter: `priority: medium` → `@pytest.mark.p2`)
- **Environment Explored**: local (`http://localhost:5173`, EliteaUI `automation/testids`, DEV
  backend; project id 399, Private project)
- **User set**: `${TEST_USER}` — dev-auth on localhost
- **Analyst**: test-automation-engineer (combined analyst+implementer), chat-remaining-w07
- **Status**: extend-existing (both members)
- **surface_key**: `chat-conversation-context-menu`

## Extension target
`automation/tests/ui/chat/test_move_conversation_to_folder.py` (same file as ELITEA-2135/2137/2138,
merged `origin/automation/base`, commit `37dbd948`). **Purely additive** — one new test method
(`test_move_conversation_back_to_list`, new class `TestMoveConversationBackToList`) covering both
case IDs via two stacked `@allure.issue` tags, per the same "near-duplicate case → tag-only/small-
gap extend" pattern this suite already uses repeatedly (see `_surface.md` §§ ELITEA-2133/2134,
ELITEA-2457). No existing test in this suite exercises `move_to_back_to_list_menuitem` at all
(grepped `tests/ui/chat/` for `back_to_list`/`back-to-list` before this pass — zero hits beyond the
locator's own declaration; canon ruling #511 — a page-object field isn't "referenced" until
something on an executed test path calls it. This test method is `move_to_back_to_list_menuitem`'s
FIRST live caller).

## Live exploration (this session, both case IDs)

Set up via `conversation_api`: created folder `folder` + conversation `conv_target`, moved
`conv_target` into `folder` via `conversation_api.move_conversation_to_folder()` (API — real setup,
not the tested action; the case's own precondition, "at least one conversation is inside a folder",
names no required MECHANISM for getting it there). Drove the UI: expanded `folder`
(`expand_folder()`), opened `conv_target`'s context menu (works identically for a
folder-contained conversation — same shared `chat-conversation-item-{id}` testid regardless of
container, confirmed live), opened "Move to" (submenu opens with the SAME known-defect retry as
ELITEA-2135/2137/2138 — #1117, not re-filed), clicked "Back to the list"
(`chat-move-to-back-to-list-menuitem`).

**Live-confirmed, captured via network interception**:
- `PUT /elitea_core/conversation/prompt_lib/{project_id}/{conv_id}` → `200`, response body
  `folder_id: null` (moved out) and, critically, **`updated_at` bumped to the request's own
  timestamp** — e.g. `created_at: "2026-08-15T07:13:23Z"` → `updated_at: "2026-08-15T07:14:22Z"`
  (~1 minute later, matching when the click fired), confirmed on a conversation that had NEVER been
  touched between creation and this move. This is the mechanism behind both cases' "appears in
  Today" expectation: the backend's date-group bucketing is server-side and keyed off `updated_at`
  (`DATE_GROUP_ORDER = ['today', 'this_week', 'older']`,
  `EliteaUI/src/[fsd]/features/chat/conversation-list/lib/constants/conversationList.constants.js`);
  the "Back to the list" PUT unconditionally refreshes that field to "now", independent of whatever
  the conversation's recency was before it entered the folder.
- Toast: `Chat moved to ungrouped area successfully` (distinct template from the
  move-TO-a-folder toast `useMoveToFolderConversation.hooks.js` already documents — this is the
  "moved OUT" variant of the same hook).
- Post-move: the conversation rendered under a newly-appeared "Today" heading; the (now-empty)
  source folder remained present and expandable in the sidebar (not deleted by the move).

## ELITEA-2140's precondition — investigated, not producible via any test-accessible surface

ELITEA-2140's stated precondition is "a conversation that was originally in Older is now inside a
folder." This was investigated directly, not assumed:
- **The live DEV project currently has zero conversations in the "Older" (or even "Today") group**
  (confirmed via a fresh page snapshot before any setup — only a populated "This Week" group was
  present) — no naturally-Older conversation exists to reuse read-only.
- **The API does not accept a caller-supplied `created_at`/`updated_at`.** Live-verified: created a
  conversation, then `PUT` its own endpoint with `{"updated_at": "2020-01-01T00:00:00Z",
  "created_at": "2020-01-01T00:00:00Z"}` — the server responded `200` but the returned/persisted
  timestamps were UNCHANGED from their real creation-time values. Both fields are server-controlled;
  no test-accessible surface (UI or REST) can backdate a conversation into "Older" on demand, and
  doing so via DB manipulation or `page.evaluate()`-injected state would be a fidelity-policy
  substitution (fabricated precondition), not a real observable.
- **This is not a gap in what gets tested, because the property IS mechanism-confirmed above**: the
  "Back to the list" PUT unconditionally resets `updated_at` to "now" regardless of the
  conversation's prior state — live-confirmed on this session's own fresh (Today-origin)
  conversation. A conversation's date-group membership BEFORE entering a folder has no bearing on
  its group AFTER being moved back out, because the backend does not retain or consult that prior
  state anywhere in this flow — folder membership (`folder_id`) and date-group bucket (`updated_at`)
  are orthogonal fields, and moving out always rewrites the latter.
- Given the above, ELITEA-2139's own test (any origin) IS the faithful exercise of ELITEA-2140's
  code path — the two cases assert the identical mechanism. ELITEA-2140's DISTINCT ask (its own
  step 3/Pass criteria: "Fail: appears in Older") is honored not by fabricating an Older-origin
  fixture, but by adding an EXPLICIT assertion that the post-move conversation is provably absent
  from "Older" specifically (ELITEA-2139's own test only asserts presence-in-Today, never
  absence-from-Older) — this is a real, additional, honestly-producible check, not a substitute for
  the untestable precondition.

This is a declared technique choice per `test-automation-implementation` Phase 2 (exploring *how* to
reach the case's own asserted observable, not changing *what* is asserted) — ELITEA-2140's Pass/Fail
criteria ("conversation appears in Today after moving back" / "Fail: appears in Older or is
missing") is satisfied in full; only the narrative precondition text ("originally Older") is
addressed by reasoning + a live-confirmed mechanism instead of by literal reproduction, because no
literal reproduction is available on this project's test-accessible surfaces.

## Preconditions
- User logged in (`${TEST_USER}` / dev-auth on localhost).
- At least one conversation is inside a folder — satisfied by setup (API-seeded, not ambient shared
  state).

## Test Data
- **`folder`** — via `conversation_api.create_folder(name)`.
- **`conv_target`** — via `conversation_api.create_conversation(name)`, then
  `conversation_api.move_conversation_to_folder(conv_target_id, folder_id)` (setup — reaches the
  "conversation inside a folder" precondition; not the action under test).

## Test Steps (shared by both case IDs)
1. Navigate to Chats, expand `folder` (`expand_folder()`).
   - **Verify**: `folder`'s `data-expanded` is `"true"`; `conv_target` renders scoped inside it
     (`is_conversation_in_folder()`).
2. Hover `conv_target`, click its 3-dot icon, hover "Move to" (`open_move_to_submenu()`, same
   known-defect retry as ELITEA-2135/2137/2138 — #1117).
   - **Verify**: the submenu mounts (`move_to_back_to_list_menuitem` visible, among others).
3. Click "Back to the list" (new method — see § Automation Hints).
   - **Verify**: `PUT .../conversation/prompt_lib/{project_id}/{conv_id}` resolves `200` with body
     `folder_id: null`; success toast (`toast-message`) reads exactly
     `Chat moved to ungrouped area successfully`.
4. Verify the conversation now appears in the Today date group.
   - **Verify**: `chat.is_conversation_in_group(conv_target_id, "today")` is `True`.
   - **[ELITEA-2140 only, additional]**: `chat.is_conversation_in_group(conv_target_id, "older")`
     is `False` — explicit absence-from-Older, the case's own distinguishing Pass/Fail criterion
     (see § above for why this is the honestly-producible form of the case's ask).
5. Verify the folder still exists even if now empty.
   - **Verify**: `chat.get_folder_item(folder_id)` is still visible in the sidebar after the move
     (the folder itself is not deleted by emptying it).

## Expected Results
Moving a conversation out of a folder via "Back to the list" unconditionally places it in Today
(server-side `updated_at` refresh), regardless of the conversation's state before entering the
folder; the source folder persists, empty.

## Coverage Map

### Axis 1 — Case coverage

#### ELITEA-2139

| Case element | Expected result | Covered by (AFS step) | Asserted where | Disposition |
|---|---|---|---|---|
| Preconditions: logged in, conv inside a folder | — | Setup | API-seeded folder + move | asserted |
| 1 Expand folder with a conversation | Folder expanded, conversation visible | AFS step 1 | step 1: `data-expanded` + scoped presence | asserted |
| 2 Hover conv, 3-dot, hover Move to | Submenu appears | AFS step 2 | step 2: submenu mounts | asserted, with the pre-existing filed defect #1117 (workaround per ELITEA-2135/2137/2138, not re-filed) |
| 3 Click 'Back to the list' | Conversation removed from folder | AFS step 3 | step 3: `PUT` 200, `folder_id: null` | asserted |
| 4 Verify conversation now in Today | Conversation in Today | AFS step 4 | step 4: `is_conversation_in_group(..., "today") == True` | asserted |
| 5 Verify success toast | Toast shown | AFS step 3 | step 3: exact toast text | asserted |
| 6 Verify folder still exists | Folder remains | AFS step 5 | step 5: folder item still visible | asserted |

#### ELITEA-2140

| Case element | Expected result | Covered by (AFS step) | Asserted where | Disposition |
|---|---|---|---|---|
| Precondition: "a conversation that was originally in Older is now inside a folder" | — | § ELITEA-2140's precondition (above) | mechanism live-confirmed (`updated_at` unconditionally reset on move); no test-accessible way to seed literal Older-origin | clarification *(precondition text describes an unreproducible setup detail that the mechanism proves irrelevant to the outcome — see full reasoning above; NOT a blocked case, the case's own Pass/Fail criteria are fully asserted)* |
| 1 Expand folder containing a conversation from Older | Conversation visible in folder | AFS step 1 | step 1: scoped presence | asserted *(via API-seeded, not literal-Older-origin, conversation — see clarification above)* |
| 2 Hover, 3-dot, Move to, 'Back to the list' | Conversation removed from folder | AFS steps 2–3 | steps 2–3 | asserted |
| 3 Verify conversation now appears in Today | Conversation appears in Today | AFS step 4 | step 4: `is_conversation_in_group(..., "today") == True` **and** `(..., "older") == False` | asserted |
| 4 Verify timestamp reflects recently modified | Conversation listed under Today | AFS step 4 | step 4 (Today-group membership IS the timestamp-recency proof — the group is computed from `updated_at`) | asserted |
| Pass/Fail: "Fail: appears in Older or is missing" | — | AFS step 4 | explicit `"older"` absence assertion | asserted |

Disposition key: `asserted` / `already-covered` / `clarification` / `blocked` / `out-of-scope`.

### Axis 2 — Analyst additions
- Step 3 asserts the `PUT` response body's `folder_id: null` directly (not just the eventual UI
  state) — *added: isolates a "moved server-side" regression from a "UI didn't re-render" one, same
  discipline ELITEA-2137/2138 already apply to their own `POST` responses.*
- Step 4's `"older"` absence check for ELITEA-2140 — *added: the case's own distinguishing ask,
  honestly producible without the unreproducible Older-origin precondition (see full reasoning
  above).*

## Cleanup
`try`/`finally`, independent per resource:
1. `conversation_api.delete_conversation(conv_target_id)`.
2. `chat.delete_folder_via_menu(folder_id)` (falls back to `delete_folder_via_api()` per #1309).

## Concrete Handles (discovered during exploration)
| Element | Testid handle | Provenance | Notes |
|---|---|---|---|
| "Move to" submenu — "Back to the list" item | `[data-testid="chat-move-to-back-to-list-menuitem"]` | pre-existing (`ChatPage.move_to_back_to_list_menuitem`, added ELITEA-2135's implementation pass) — on `automation/testids` ✓, provenance already documented in ELITEA-2135's own AFS | Locator existed with ZERO callers before this case (canon #511 — first live caller). No new testid work needed. |
| Folder item (for step 5's "still exists" check) | `[data-testid="chat-folder-item-{id}"]` | pre-existing (`ChatPage.FOLDER_ITEM`, ELITEA-2132) | Reused verbatim. |

**No new testids for either case.** All handles needed already exist and are provisioned; only a
new page-object METHOD is needed (see § Automation Hints) — a code-level gap, not a testid gap.

## Network Behavior
- `PUT /elitea_core/conversation/prompt_lib/{project_id}/{conv_id}` → `200`, body includes
  `folder_id: null` and a fresh `updated_at` (live-confirmed both cases' cases share this mechanism).
- Toast: `Chat moved to ungrouped area successfully` (distinct from the move-INTO-folder toast
  template ELITEA-2135/2137/2138 document).
- Pre-existing, unrelated: `secrets/secrets/default` `403` noise (excluded, per every sibling AFS).

## Known Defects Found During Exploration
None new. Reuses the already-filed, already-workaround-documented #1117 (submenu open-reliability)
from ELITEA-2135/2137/2138 — not re-filed.

## Blocked Steps
None. (ELITEA-2140's precondition-reproduction limitation is documented as a clarification, not a
block — the case's own asserted Pass/Fail criteria are fully honored, see § above.)

## Automation Hints
- **New page-object method needed** (locator already exists, method does not):
  ```python
  @action("Select 'Back to the list' in 'Move to' submenu")
  def select_move_to_back_to_list(self, timeout: int = 5000):
      """Click 'Back to the list' inside the open 'Move to' submenu.

      Moves the conversation out of its current folder into the general,
      date-grouped list (ELITEA-2139/2140). Mirrors select_move_to_folder()'s
      and select_move_to_create_folder()'s shape.
      """
      self.move_to_back_to_list_menuitem.wait_for(state="visible", timeout=timeout)
      self.move_to_back_to_list_menuitem.click()
  ```
  Place alongside `select_move_to_folder()`/`select_move_to_create_folder()` in the existing
  "Move to" submenu flow section of `chat_page.py`.
- Reuse `expand_folder()`, `is_conversation_in_folder()`, `is_conversation_in_group()`,
  `get_folder_item()`, `open_move_to_submenu()` — all pre-existing.
- `conversation_api.move_conversation_to_folder(conv_id, folder_id)` (pre-existing, `api/client.py`)
  is the setup primitive for "conversation inside a folder" — real API call, not a substitution
  (the case names no required mechanism for reaching this precondition).
