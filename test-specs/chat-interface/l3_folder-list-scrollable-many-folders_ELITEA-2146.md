# Test Case: Chat – Folder List is Scrollable When Many Folders Exist

## Metadata
- **TMS ID**: ELITEA-2146
- **Linked Story**: none (case `requirements: []`)
- **Priority**: l3 (case frontmatter: `priority: medium` → `@pytest.mark.p2`; see ELITEA-2135's
  AFS for the medium→l3/p2 mapping evidence in this suite)
- **Environment Explored**: local (`http://localhost:5173`, EliteaUI `automation/testids`, DEV
  backend; project id 399, the account's own Private/personal project — treat as
  `${ELITEA_PROJECT_ID}`, don't hardcode)
- **User set**: `${TEST_USER}` — on localhost, `auth_state`/`VITE_DEV_TOKEN` skips explicit
  Keycloak login
- **Analyst**: qa-engineer (agent) — cluster dispatch with ELITEA-2147, ELITEA-2148 (chat-remaining
  wave-07); each case has genuinely different steps, so each got its own AFS (see the shared cluster
  session note in ELITEA-2147/ELITEA-2148's own AFS files)
- **Status**: ready-for-automation
- **surface_key**: `chat-folder-list`

## Preconditions
- User is logged in (`${TEST_USER}` / dev-auth on localhost).
- More folders exist than fit in the visible panel area. **The account this session ran against
  already carries 65+ ambient/orphaned folders** (a known, already-tracked test-data-hygiene gap —
  see `test-specs/chat-interface/_surface.md`'s ELITEA-2142/2143/2144/2145 section), which on its own
  is enough to reproduce genuine overflow live (confirmed this pass — see § Concrete Handles). That
  ambient state is NOT something this test may depend on (a future cleanup pass would silently break
  it) — the test seeds its own deterministic folder set instead (§ Test Data) so it stays green
  regardless of the account's ambient folder count.

## Test Data

### generate-per-test (created via API in setup, cleaned up in teardown)
- **`seeded_folders`** — 25 folders, created via `conversation_api.create_folder(f"AutoScrollFolder{i}")`
  for `i` in `range(25)`. 25 was chosen from a live-measured collapsed folder-row height of **41px**
  (folder `279`, this session) against the scroll container's measured `clientHeight` of **828px** at
  a 1440×900 viewport (25 × 41px = 1025px > 828px, comfortably overflowing even on an otherwise-empty
  account — see § Concrete Handles for the live measurement).

## Test Steps

1. Navigate to `${BASE_URL}/chat`. Verify the folder list contains many folders.
   - **Verify**: `ChatPage.get_folder_link_count()` (pre-existing, `FOLDER_ITEM_PREFIX`-based) returns
     `>= 25` (the seeded set; ambient folders may add more — assert `>=`, not `==`).
2. Hover over the folder list area — verify the list is genuinely scrollable, not just visually tall.
   - **Verify**: the sidebar's scroll container (`ref={listRef}` in `Conversations.jsx` —
     **testid needed**, see § Concrete Handles) has `scrollHeight > clientHeight` via
     `.evaluate("el => ({scrollHeight: el.scrollHeight, clientHeight: el.clientHeight})")` — the same
     "don't trust CSS overflow alone" discipline `is_messages_scrollable()` already applies to the
     chat-messages container. Live-confirmed this pass: `scrollHeight=2946` vs `clientHeight=828` (at
     1440×900, with the account's ambient 67 folders present) — genuine overflow, not a false
     positive from `overflow-y: scroll` alone.
3. Scroll down through the folder list via a REAL scroll gesture (mouse wheel, hovering the
   container — same idiom as `scroll_messages_container()`, never a synthetic `el.scrollTop =`
   assignment in the shipped test).
   - **Verify**: `scrollTop` reads > 0 after the scroll and strictly greater than its value before
     scrolling (before/after comparison, matching `scroll_messages_container()`'s own return shape).
4. Verify all folders are accessible via scrolling — scroll to the bottom of the container.
   - **Verify** (AMENDED during implementation — see note below): identify a seeded folder currently
     positioned BELOW the container's visible viewport; scroll down via repeated real wheel gestures
     (checking reachability after every gesture) until its row falls within the container's own
     bounding box — proves the scroll genuinely reaches a folder that was off-screen, not just that
     `scrollTop` moved.
5. Scroll back up and verify the top folders are still accessible.
   - **Verify** (AMENDED — see note below): identify a seeded folder now positioned ABOVE the visible
     viewport (scrolled past by step 4); scroll back up via repeated real wheel gestures until its row
     is again within the container's own bounding box — mirrors step 4's assertion at the opposite
     end, proving the round trip doesn't leave anything permanently inaccessible.

**Implementer amendment (steps 4–5, discovered during ELITEA-2146 implementation):** the original
verify text above ("scroll to `scrollTop == scrollHeight - clientHeight`; the LAST/FIRST seeded
folder by creation order is at that extreme") assumed the container's raw scroll maximum lands on the
last-created seeded folder. Live-confirmed this is FALSE on two counts: (1) `Conversations.jsx`'s
`ref={listRef}` container holds folders AND the full pinned/date-grouped conversation list in ONE
shared scroll region — on this account (carrying many ambient conversations) the container's true
scroll extreme sits well past the folder section entirely, confirmed via a deeply negative
`getBoundingClientRect().y` on the target folder after scrolling to the literal max; (2) the folder
list itself renders NEWEST-created folders closer to the TOP, not the bottom (confirmed via bounding
boxes of all 25 seeded folders — id order strictly correlates with descending `y`), so "last created"
and "bottommost" are opposite ends, not the same one. The shipped test instead identifies, empirically
via live bounding boxes, a folder genuinely below/above the current viewport and proves it becomes
reachable — this verifies the same case-level claim (no folder permanently inaccessible, round trip
intact) without assuming a specific creation-order position. See
`automation/tests/ui/chat/test_folder_list_scrollability_and_expand_states.py` for the implementation.

## Expected Results
- The sidebar list container genuinely overflows (`scrollHeight > clientHeight`) once enough folders
  exist.
- A real scroll gesture moves `scrollTop` and brings folders at both ends of the list into view.
- No folder is permanently inaccessible at either scroll extreme.

## Coverage Map

### Axis 1 — Case coverage

| Case element | Expected result | Covered by (AFS step) | Asserted where | Disposition |
|---|---|---|---|---|
| Precondition: more folders than fit in the visible area | — | Setup | 25 API-seeded folders (§ Test Data) | asserted |
| 1 Navigate to Chats and verify the folder list contains many folders | Many folders visible | AFS step 1 | `get_folder_link_count() >= 25` | asserted |
| 2 Hover over the folder list area | Scrollbar appears or list is scrollable | AFS step 2 | `scrollHeight > clientHeight` on the scroll container | asserted |
| 3 Scroll down through the folder list | Additional folders become visible | AFS step 3 | `scrollTop` before/after comparison | asserted |
| 4 Verify all folders are accessible via scrolling | No folders hidden or cut off | AFS step 4 | last seeded folder's bounding box within container bounds at max scroll | asserted |
| 5 Scroll back up and verify top folders are still accessible | Top folders visible after scrolling back | AFS step 5 | first seeded folder's bounding box within container bounds at `scrollTop=0` | asserted |
| Expected Final State (prose): "All folders are accessible via scrolling" | — | steps 4–5 | covered by the rows above | asserted |
| Pass/Fail: "All steps complete without errors" | — | all steps | console-check (Axis 2) | asserted |

Disposition key: `asserted` / `already-covered` / `clarification` / `blocked` / `out-of-scope`.

### Axis 2 — Analyst additions

- Step 2 asserts `scrollHeight > clientHeight` directly rather than trusting the CSS `overflow-y:
  scroll` declaration alone — *added: the same "CSS overflow ≠ proven scrollability" discipline
  `is_messages_scrollable()` already applies elsewhere in this page object; a container can declare
  `overflow-y: scroll` and still not overflow if content is short (confirmed live this pass at an
  unusually tall 4000px-tall viewport carried over from a prior session — at that height the SAME
  container's `scrollHeight === clientHeight`, i.e. NOT scrollable, until resized back down; see
  § Concrete Handles).*
- Steps 4–5 assert bounding-box containment of the FIRST/LAST seeded folder specifically, not just a
  `scrollTop` value change — *added: a `scrollTop` move alone doesn't prove any particular folder
  became reachable (it could plateau early against a `max-height` clamp with content still cut off);
  anchoring on the actual first/last seeded folder's visibility closes that gap.*
- Console/network side-channel checked after every interaction — *added: standard side-channel
  discipline for this suite; not independently re-stated per step below, see § Network Behavior.*

## Cleanup
1. Delete all 25 `seeded_folders` via `conversation_api.delete_folder(id)`.
2. Standard `try/finally` per `.claude/rules/ui-tests.md` § Test Data Lifecycle.

## Concrete Handles (discovered during exploration)

| Element | Testid handle | Provenance | Notes |
|---|---|---|---|
| Folder items (all) | `[data-testid^="chat-folder-item-"]` (`FOLDER_ITEM_PREFIX`) | pre-existing, on-`automation/testids` ✓ | `ChatPage.get_folder_link_count()` (pre-existing). |
| Individual folder row | `[data-testid="chat-folder-item-{id}"]` (`FOLDER_ITEM`) | pre-existing, on-`automation/testids` ✓ | `ChatPage.get_folder_item(folder_id)`. |
| **Sidebar list scroll container** (folders + pinned + date-grouped conversations, ALL share this one container) | **testid needed**: e.g. `chat-conversation-list-scroll-container` on `Conversations.jsx`'s `ref={listRef}` `Box` (line ~731, `sx={{ overflowY: 'scroll', height: 'calc(100% - 40px)', ... }}`) — the SAME naming family as the existing `chat-messages-scroll-container` precedent (`ChatPage.chat_messages_scroll_container`). | **ADD via `add-data-testid`.** Zero new DOM node — the `Box` already exists and already renders `ref={listRef}`; this is a pure `data-testid` attribute addition, same shape as the `chat-messages-scroll-container` precedent already in this file. | New: `ChatPage.chat_conversation_list_scroll_container = LocatorDescriptor(testid="chat-conversation-list-scroll-container")` + `get_conversation_list_scroll_metrics()` / `is_conversation_list_scrollable()` / `scroll_conversation_list_container()` mirroring the existing `get_messages_scroll_metrics()` / `is_messages_scrollable()` / `scroll_messages_container()` trio exactly (`chat_page.py:1519-1548`). |

**Live measurement (this pass, confirms the container genuinely overflows):**
- At the CARRIED-OVER 1280×4000 viewport (leftover from the prior ELITEA-2142/2143/2144/2145 session
  sharing this MCP browser instance): `scrollHeight === clientHeight === 3928` — NOT scrollable. A
  test that resizes/inherits an oversized viewport would give a FALSE negative here; the shipped test
  must run at a normal viewport (this repo's default, not overridden) — flagging so nobody "fixes" a
  future flake here by enlarging the viewport, which is the opposite of the fix needed.
- After resizing to 1440×900 (this repo's `pytest-playwright` default is comparable — not 4000px
  tall): `scrollHeight=2946`, `clientHeight=828` — genuinely scrollable, matches this AFS's steps.
- Folder row height (collapsed): 41px (`chat-folder-item-279`, measured via `getBoundingClientRect()`).

## Network Behavior
- Folder creation: `POST /elitea_core/folder/prompt_lib/{project_id}` `{"name": "..."}` → 201
  (`ConversationAPI.create_folder`, ELITEA-2098-documented).
- Folder deletion: `DELETE /elitea_core/folder/prompt_lib/{project_id}/{folder_id}` → 204
  (`ConversationAPI.delete_folder`).
- No new console errors expected during scroll interactions themselves (scroll is a pure client-side
  operation once folders are loaded). Pre-existing, unrelated: project 399's `secrets/secrets/default`
  `403` on every page load — excluded from "no new console errors" checks, same as every sibling AFS.

## Known Defects Found During Exploration
None found specific to this case. The scroll mechanism itself works correctly and genuinely — the
only finding is a MISSING TESTID (§ Concrete Handles), which is implementer work, not a product
defect.

## Blocked Steps
None.

## Automation Hints
- Framework: Playwright + pytest, testid-only `LocatorDescriptor`.
- Page object: extend `automation/pages/chat_page.py` — add the scroll-container `LocatorDescriptor`
  + the three scroll-metric methods per § Concrete Handles, directly mirroring
  `chat_messages_scroll_container` / `get_messages_scroll_metrics()` / `is_messages_scrollable()` /
  `scroll_messages_container()` (`chat_page.py:644-1548`). Do not invent a second pattern for the
  same "is this container genuinely scrollable" question.
- Real scroll gesture: `container.hover()` then `page.mouse.wheel(0, delta_y)` — same idiom as
  `scroll_messages_container()`. Never assign `el.scrollTop = N` directly in the shipped test (that
  was used only for THIS exploration pass, via `browser_evaluate`, to confirm the mechanism quickly —
  it is not a real user gesture and must not ship in the automated test per the project's fidelity
  policy: a synthetic property assignment doesn't prove a user CAN scroll the container the way a
  real wheel event does).
- Priority marker: `@pytest.mark.p2` (see ELITEA-2135's AFS note on the l3/p2 mapping).
- Feature markers: `@pytest.mark.chat`, `@pytest.mark.regression`.
