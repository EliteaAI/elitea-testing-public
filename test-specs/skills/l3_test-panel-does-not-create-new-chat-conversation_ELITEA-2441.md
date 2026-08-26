# Test Case: Test panel does not create a new Chat conversation

## Metadata
- **TMS ID**: ELITEA-2441
- **Linked Story**: none
- **Priority**: l3 (case frontmatter/body: `medium`) — matches sibling
  `l3_test-panel-uses-selected-skill-version-instructions_ELITEA-2440.md`,
  same "medium" TMS priority label.
- **Environment Explored**: local (`http://localhost:5173`, EliteaUI
  `automation/testids` branch → DEV backend, project `Private` /
  `${ELITEA_PROJECT_ID}`=399)
- **User set**: `${TEST_USER}` (localhost `auth_state` fixture skips login via
  `VITE_DEV_TOKEN`)
- **Analyst**: qa-engineer (Sage), analyst slot
- **Status**: ready-for-automation
- **Case-gate note**: case frontmatter carries `status: draft`,
  `execution_type: manual` — per `.agents/test-automation.yaml` § `intake`,
  `status: draft` is the intake-eligible value, not an exclusion. Proceeded
  to full execution.
- **Dedup / reuse check**: grepped `test-specs/skills/` and
  `automation/tests/ui/skills/*.py` for "conversation" combined with the
  test-panel flow — no existing merged spec asserts the *absence* of a Chat
  conversation after a test-panel run. The two closest neighbours,
  `l3_test-panel-uses-selected-skill-version-instructions_ELITEA-2440.md`
  and `l3_llm-model-settings-configurable_ELITEA-2436.md`, both drive the
  same test panel (`SkillDetailPage.send_test_message()` /
  `wait_for_test_response()` / `get_last_test_response()`) but neither one
  asserts anything about the Chat section's conversation list/count — they
  only assert the test panel's own response content. Not a duplicate —
  proceeded as new coverage, reusing the same page-object methods.

## Preconditions
- User is logged in to Elitea (on localhost, `auth_state` fixture skips
  login).
- A project is selected/accessible (`Private`, id `399` in this run).
- The Skills section is accessible (`/skills/all`, `/skills/create`) and the
  Chat section is accessible (`/chat`).

## Test Data

### generate-per-test (created in test setup, cleaned up in teardown)
- Skill: created via the UI create-skill form (`SkillsListPage.navigate_to_create()`
  → `SkillFormPage.fill_form(name, instructions, description)` →
  `save_and_wait_for_navigation()`) — mirrors `l3_test-panel-uses-selected-
  skill-version-instructions_ELITEA-2440.md`'s step 1 exactly. A dedicated
  skill is created (rather than reusing an existing one) so cleanup is
  self-contained and the test panel's message history starts empty.
- Skill name used this run: `autotest-2441-notestpanel` (must satisfy the
  Name field's `^[a-z0-9]([a-z0-9-]*[a-z0-9])?$`, ≤32-char constraint
  documented in `test-specs/skills/_surface.md`).
- Instructions used this run: `"Always reply with the single word: PONG"` —
  any deterministic short instruction works; content is irrelevant to this
  case, only that a response is produced.
- `SkillAPI.delete_skill(skill_id)` reused for teardown (confirmed live —
  see Cleanup).

## Test Steps

1. Note the current number of conversations in the Chat section.
   - **Verify — confirmed live**: navigate to `/chat`; the ground-truth
     count is the number of `[data-testid^="chat-conversation-item-"]`
     elements in the sidebar (`ChatPage.CONVERSATION_ITEM_PREFIX`) —
     confirmed via `document.querySelectorAll(...).length` this run: `1`.
     This DOM count matches `ConversationAPI.list_conversations()`'s
     `total` field exactly (also `1`, same single conversation id `7929`
     both before and after this run) — the two ground truths agree, see
     Coverage Map / Axis 2 note on which one the implementer should assert
     against.

2. Open a Skill and run a test via the test panel.
   - Create the Skill (see Test Data), which navigates to its detail page
     with the SkillTestPanel visible.
   - Send a test prompt via `SkillDetailPage.send_test_message()` and wait
     for the AI response via `SkillDetailPage.wait_for_test_response()`.
   - **Verify — confirmed live**: message sends without error; response
     text stabilizes as `"PONG"` (`get_last_test_response()`).
     **Network evidence** (the case's actual pass criterion): across the
     entire skill-creation + test-panel-run flow, **zero requests fired
     against any `elitea_core/conversations*` endpoint** — the only
     conversation-shaped traffic observed was unrelated
     `support_assistant/conversations/` calls (the separate Support
     Assistant widget, not the Chat feature this case is about) and the
     skill's own `elitea_core/skills*` / `elitea_core/skill_categories*`
     calls. This is the strongest, most direct proof available that the
     test panel does not create a Chat conversation — the implementer
     should assert on this via `page.on("request", ...)` / a captured
     network log, not just a before/after count (belt-and-braces; see Axis
     2).

3. Navigate to Chat.
   - **Verify**: `/chat` loads; sidebar renders without error.

4. Verify no new conversation was created by the Skill test execution.
   - **Verify — confirmed live**: `[data-testid^="chat-conversation-item-"]`
     count is unchanged (`1`, same as step 1) and
     `ConversationAPI.list_conversations()`'s `total`/`rows[].id` are
     unchanged (`1`, id `7929`, same id — not merely the same count) both
     immediately after the test-panel run and after this run's own skill
     cleanup (delete via `SkillAPI.delete_skill()`).

## Expected Results
Matches the case's Pass criteria exactly, live-verified end-to-end: running
a test prompt through a Skill's SkillTestPanel does **not** create a new
Chat conversation. Confirmed three independent ways this run: (a) zero
`elitea_core/conversations*` network requests fired during the entire
skill-creation + test-panel-run flow, (b) the Chat sidebar's
`chat-conversation-item-*` DOM count stayed at `1` before and after, (c)
`ConversationAPI.list_conversations()`'s `total` and the exact conversation
`id` (`7929`) were unchanged before and after. No functional product defect
found.

## Coverage Map

### Axis 1 — Case coverage

| Case element | Expected result | Covered by (AFS step) | Asserted where | Disposition |
|---|---|---|---|---|
| Precondition: user logged in | — | AFS Preconditions | `auth_state` fixture | asserted |
| 1 Note the current number of conversations in the Chat section | action completes without error; expected UI state | step 1 | step 1: DOM count of `chat-conversation-item-*` = 1; cross-checked against `ConversationAPI.list_conversations().total` = 1 | asserted |
| 2 Open a Skill and run a test via the test panel | target page/section loads successfully | step 2 | step 2: skill detail page loads, test prompt sent, response `"PONG"` received; **network capture shows zero `elitea_core/conversations*` calls** | asserted |
| 3 Navigate to Chat | target page/section loads successfully | step 3 | step 3: `/chat` loads | asserted |
| 4 Verify no new conversation was created by the Skill test execution | condition holds | step 4 | step 4: DOM count still 1, API `total`/id unchanged | asserted |
| Expected Final State: no new conversation was created | — | step 4 | step 4, same assertion | asserted |

**Note on the case's own step ordering:** the case text implies "note count"
happens strictly before "run the test", then "navigate to Chat" happens
strictly after. Live execution followed that literal ordering (baseline
recorded via API *before* any browser action, then again via both DOM and
API after the test-panel run and after this run's cleanup) — no
decomposition or reordering was needed; the case's 4 steps map 1:1 to the
AFS's 4 steps.

### Axis 2 — Analyst additions

- **Network-request assertion (added) is the load-bearing check, not the
  count comparison alone** — *why: a before/after count comparison can pass
  "by accident" if a conversation is created AND deleted within the same
  flow (e.g. a create-then-auto-cleanup path), or if the count genuinely
  doesn't move for an unrelated reason. Capturing zero
  `elitea_core/conversations*` requests during the test-panel interaction is
  direct proof of absence-of-cause, not just absence-of-symptom. The
  implementer should register a request listener
  (`page.on("request", ...)`) scoped to the test-panel-run step and assert
  no URL matches `elitea_core/conversations` (a plain substring/regex
  check on the URL, not a locator — this is a network assertion, not a
  DOM one, so it carries no testid implication).*
- **Two independent ground truths for "count", not one — and which one
  to prefer** — *added: `ConversationAPI.list_conversations()` (cookie/
  Bearer-auth API call, already wired via the `conversation_api` fixture,
  `automation/fixtures/api_fixtures.py:115`) and the Chat sidebar's
  `chat-conversation-item-*` DOM count agree exactly in this run (both `1`,
  same id `7929`). Prefer the API check as the primary assertion (faster,
  no UI-timing flakiness, matches the fixture already used by other API-
  first specs) and the DOM count as a secondary UI-level corroboration for
  step 3/4's own "Navigate to Chat" requirement — the case explicitly wants
  a Chat-section visit, so drop the DOM check entirely only if the
  implementer is comfortable the API check alone satisfies "verify no new
  conversation was created" for review purposes.*
- **`[data-testid^="chat-conversation-item-"]` (`ChatPage.
  CONVERSATION_ITEM_PREFIX`), not `get_conversation_list_items()`'s CSS
  selector** — *added: `ChatPage` already has two ways to count conversation
  items — the testid-based `CONVERSATION_ITEM_PREFIX` class constant and
  the older `get_conversation_list_items()` method, which the method's own
  docstring flags as "tracked tech debt" using a raw `:has(h6) > button`
  CSS selector (predates the testid-only locator policy). This case's own
  count assertion must use the testid-based constant, not the tech-debt
  method — confirmed live it resolves correctly (`count() == 1`, matching
  both the DOM `querySelectorAll` check and the API total).*
- "zero console errors across the case's own 4 steps" — *added: side-channel
  check per this skill's standard discipline; confirmed live — 0 console
  errors were logged after the `/chat` navigation for step 3 (some
  pre-existing console entries were present in the browser session from
  before this case's own steps began — unrelated stale-tab artifacts, not
  produced by this case's actions; see Known Defects/Observations).*
- **Leftover `ELITEA2459RenameTest`/`ABC` folders in the Chat sidebar are
  FOLDERS, not conversations — do not let them corrupt a naive count check**
  — *added, observation only: the live Chat sidebar showed roughly a dozen
  duplicate `ELITEA2459RenameTest` and `ABC` **folder** entries (rendered as
  `heading > button` pairs), apparent leftover test data from a prior
  ELITEA-2459 rename-flow run that didn't clean up. These are NOT
  conversations — confirmed via DOM: the `chat-conversation-item-*`
  testid-scoped count stayed at exactly `1` despite the folder clutter, so
  the case's own count-based assertion is unaffected. Flagged here purely
  so the implementer doesn't accidentally write a broader "count all
  sidebar buttons/headings" check that would be corrupted by this
  pre-existing pollution — testid-scoped counting (`CONVERSATION_ITEM_PREFIX`)
  is immune to it. Not filed as a defect for THIS case (out of scope — this
  case only concerns the SkillTestPanel↔Chat-conversation relationship);
  noted for whichever case actually owns ELITEA-2459/folder cleanup
  hygiene.

## Cleanup
1. Delete the skill created in Test Data via `SkillAPI.delete_skill(skill_id)`
   in test teardown (`try`/`finally`), regardless of pass/fail.
2. This run's own skill (`autotest-2441-notestpanel`, id `1490`) was fully
   deleted via `SkillAPI.delete_skill(1490)` before this run ended —
   confirmed by the immediately-following `ConversationAPI.list_conversations()`
   call still returning `total: 1`, id `7929` (i.e. cleanup itself created
   no stray conversation either).

## Concrete Handles (discovered during exploration)

| Element | Recommended Locator | Fallback |
|---|---|---|
| Skill create form — Name field | `page.get_by_test_id("skill-name-input-field")` — **confirmed live, existing testid**, already `SkillFormPage.name_input` | n/a — testid already present |
| Skill create form — Description field | `page.get_by_test_id("skill-description-input-field")` — **confirmed live, existing testid**, already `SkillFormPage.description_input` | n/a — testid already present |
| Skill create form — Instructions CodeMirror editor content | `page.get_by_test_id("skill-instructions-editor-content")` — **confirmed live, existing testid**, already `SkillFormPage.instructions_editor_content` / `fill_instructions()` | n/a — testid already present |
| Skill create form — Save button | `page.get_by_test_id("skill-save-button")` — **confirmed live, existing testid** | n/a — testid already present |
| Test panel chat input | `page.get_by_test_id("chat-message-input")` — **confirmed live, existing testid**, already used inline in `SkillDetailPage.send_test_message()` | n/a — testid already present |
| Test panel send button | `page.get_by_test_id("chat-send-button")` — **confirmed live, existing testid**, already used inline in `SkillDetailPage.send_test_message()` | n/a — testid already present |
| Test panel last AI response text | `page.get_by_test_id("skill-test-last-response")` — **confirmed live, existing testid**, already `SkillDetailPage.get_last_test_response()` | n/a — testid already present |
| Chat sidebar — conversation item, any id (count) | `page.locator(ChatPage.CONVERSATION_ITEM_PREFIX)` i.e. `'[data-testid^="chat-conversation-item-"]'` — **confirmed live, existing dynamic-testid class constant** in `automation/pages/chat_page.py`, `.count()` confirmed live returns `1` | n/a — testid already present; do NOT use `get_conversation_list_items()`'s CSS-selector tech debt for this case |
| Chat navigation (sidebar) | `ChatPage.navigate_to_chat()` (`automation/pages/chat_page.py:1184`) — **confirmed live, existing page-object method** | n/a |

**Summary for the implementer / `add-data-testid`:** zero testid gaps found
this run — every UI element the case touches already carries a testid, all
already wired into `SkillFormPage` / `SkillDetailPage` / `ChatPage`
page-object methods/constants. No `add-data-testid` round-trip is needed
for this case. The case's own pass criterion is best proven at the network
layer (see Axis 2), which carries no locator/testid implication at all.

## Network Behavior
- `POST /api/v2/elitea_core/skills/prompt_lib/399` → `201 Created` (skill
  creation, step 2 setup).
- `GET /api/v2/elitea_core/skill/prompt_lib/399/{id}` → `200 OK` (skill
  detail load).
- AI test-panel response arrives over WebSocket (per `.agents/testing.md`),
  not a plain REST call — `wait_for_test_response()`'s content-stabilization
  polling is the correct wait strategy, not a network-response wait.
- **Confirmed live: zero requests to any `elitea_core/conversations*`
  endpoint** across skill creation + the test-panel send/response cycle —
  this is the case's own pass criterion at the network layer.
- `GET /api/v2/elitea_core/conversations/prompt_lib/399` → `200 OK`,
  `{"total": 1, "rows": [{"id": 7929, ...}]}` — confirmed identical both
  immediately before step 2 and immediately after step 4 / cleanup (same
  `total`, same single conversation `id`).
- `DELETE /api/v2/elitea_core/skill/prompt_lib/399/1490` → `204 No Content`
  (cleanup).

## Known Defects / Observations Found During Exploration

No functional product defect was found. The test panel correctly does NOT
create a Chat conversation — confirmed by network capture (zero
`elitea_core/conversations*` requests), DOM count (`chat-conversation-
item-*` stable at `1`), and API ground truth (`ConversationAPI.
list_conversations()` stable at `total: 1`, same conversation `id`) across
the entire flow.

**Observation (not a defect for this case):** the live Chat sidebar carries
roughly a dozen duplicate `ELITEA2459RenameTest`/`ABC` **folder** entries —
apparent leftover test data from a prior ELITEA-2459 rename-flow run that
didn't clean up its own folders. Confirmed these are folders, not
conversations (the testid-scoped conversation count is unaffected — see
Axis 2). Not filed as a defect: it doesn't affect this case's own
pass/fail, and filing a data-hygiene note against a specific prior case
without knowing which run left it behind risks a low-signal ticket: no
teardown failure, error, or reproducible trigger was observed this run —
only the residue. Recorded here and in analyst memory
(`test_panel_conversation_isolation.md`) so a future analyst working
ELITEA-2459 or any Chat-folder case sees it and can decide whether to file/
clean up from a position of actually reproducing the leak.

## Blocked Steps
None. All 4 case steps were executed end-to-end live against the real DEV
backend on localhost: recording the baseline conversation count/id (API +
DOM), creating a Skill and running a test-panel prompt with a captured
network log, navigating to Chat, and re-verifying the count/id were
unchanged — followed by full cleanup, itself confirmed to introduce no
stray conversation.

## Automation Hints
- Framework: Playwright + pytest, per `.agents/testing.md`. Likely home:
  `automation/tests/ui/skills/test_skill_test_panel_no_new_conversation.py`
  (new file — grep of `automation/tests/ui/skills/` found no existing test
  asserting conversation-count/network-absence around the test panel).
- Fixtures: `skill_api` (or the raw `SkillAPI`) for skill create/delete;
  `conversation_api` (`automation/fixtures/api_fixtures.py:115`, wraps
  `ConversationAPI`) for the before/after `list_conversations()` ground
  truth — reuse the fixture rather than instantiating `ConversationAPI`
  directly, mirroring how `skill_api` is already used in the ELITEA-2440
  sibling test.
- `SkillFormPage.fill_form()` / `save_and_wait_for_navigation()` for step 2
  setup (mirrors `test_skill_management.py::TestCreateSkill`'s Steps 1–3 and
  the ELITEA-2440 sibling test's Step 1 almost verbatim — reuse that
  sequence).
- Register `page.on("request", ...)` (or use Playwright's
  `page.expect_request()` negatively / collect all requests into a list
  and assert-not-any) scoped around the `send_test_message()` +
  `wait_for_test_response()` call — assert no captured request URL
  contains `elitea_core/conversations`.
- `conversation_api.list_conversations()` before skill creation and again
  after the test-panel run — assert `total` and the `rows[].id` set are
  byte-for-byte identical (stronger than a bare count comparison — catches
  a create+delete-within-flow that a count alone would miss).
- `ChatPage.navigate_to_chat()` for step 3, then
  `page.locator(ChatPage.CONVERSATION_ITEM_PREFIX).count()` for step 4's UI
  corroboration.
- Cleanup: `skill_api.delete_skill(skill_id)` in a `try`/`finally`.
