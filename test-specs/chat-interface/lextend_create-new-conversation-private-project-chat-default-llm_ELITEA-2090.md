# Test Case: Create New Conversation from Private Project via +Chat with Default LLM

## Metadata
- **TMS ID**: ELITEA-2090
- **Linked Story**: [EliteaAI/elitea-testing-public#293](https://github.com/EliteaAI/elitea-testing-public/issues/293) (originating tracking issue)
- **Priority**: l2 (case frontmatter says `priority: high`; per AFS convention 1=critical/
  2=high/3=medium/4=low → l2. NOTE: the dispatch's illustrative path used an `l1_` prefix,
  but this case's determined status is `extend-existing`, so the filename prefix is
  `lextend_` per spec-format.md's explicit rule that the priority digit is replaced for
  `extend-existing`/`already-covered` outcomes — see § Status below.)
- **Environment Explored**: local (`http://localhost:5173`, EliteaUI `automation/testids`
  branch → DEV backend; project `Private`, id `399`/`${ELITEA_PROJECT_ID}` — confirmed live
  via the sidebar's "Project: Private" combobox AND the created conversation's own
  `is_private: true` API field, see § Concrete Handles)
- **User set**: `${TEST_USER}` (on localhost, `auth_state` fixture skips login via
  `VITE_DEV_TOKEN` — dev-token user renders as "Test Bot"/"Test!" in the UI)
- **Analyst**: qa-engineer, analyst slot
- **Status**: **extend-existing** — case executed end-to-end live (all 6 steps, both
  preconditions, both LLM-response completions observed), zero product defects. The case's
  core flow (navigate to Chats → click +Chat → type → send → conversation created,
  auto-named, LLM responds) is a **partial** overlap with two already-merged specs. See
  § Overlap check for the dedup/extend boundary call and § Gap assertions for exactly what
  the implementer appends/inserts.

## Overlap check vs existing automation

Both sibling tests named in the dispatch, plus their AFS-equivalent context (no AFS existed
for either — this is the first `test-case-analysis` pass over `chat-interface`), were read
in full before this run:

**`automation/tests/ui/chat/test_conversation_management.py::TestCreateConversation::
test_create_conversation_via_ui_button`** (lines 121–158, covers ELITEA-0571) —
Step 1 navigates to `/chat` (`chat.navigate_to_chat()`), Step 2 clicks the same `+Chat`
button this case's step 2 targets (`chat.click_create_conversation()`, which resolves
`get_by_test_id("sidebar-create-button")` internally — same testid I clicked live), Step 3
types `"at_create_ui_test"` and sends via **Enter key** (`send_message(test_msg,
use_enter=True)`), then waits for the AI response, Step 4 extracts the conversation ID via
URL/API for cleanup, Step 5 calls `wait_for_naming_label_to_resolve()` +
`wait_for_conversations_to_load()` and asserts `get_conversation_link_count() > 0`.

**This structurally matches ELITEA-2090's steps 1–3, 5, and half of 6** (conversation
created, message sent, AI responds, conversation appears in sidebar, naming placeholder
resolves). **Confirmed live this run it does NOT assert**:
- the Private-project precondition specifically (it runs in whatever project
  `conversation_api`/`page` default to — confirmed live this run that project IS `Private`/
  `399`, satisfying the precondition, but the covering test never asserts this itself);
- the `+Chat` button's disabled↔enabled toggle (case steps 2 and part of 6) — the covering
  test never reads this button's state at all;
- the default-LLM-pre-selected observable (case step 4) — that's the OTHER sibling test's
  job (see below), not this one's;
- clicking the Send **button** specifically (case step 5 says "Click the Send button"; the
  covering test uses the Enter key). Confirmed live this run (see § Gap assertions) that the
  `+Chat` button's enable-on-send transition happens on the actual `chat-send-button` click
  path — I did not independently re-verify the Enter-key path produces the identical timing,
  so the gap assertion below deliberately re-uses the covering test's own send action
  in-place rather than asserting a claim about the Enter-key path I did not test.

**`automation/tests/ui/chat/test_conversation_management.py::TestCreateConversation::
test_new_conversation_default_settings`** (lines 180–191, covers ELITEA-0569) — navigates to
an **already-existing** conversation via the `conversation_id` fixture (not the +Chat
creation flow) and asserts `chat.get_selected_model()` is truthy. **Same observable** ELITEA-
2090's step 4 wants (a default model string is shown) but proven on a *different* code path
(pre-existing conversation via fixture, vs. a conversation freshly opened via +Chat before
anything has been typed or sent). Confirmed live this run: the model selector already shows
`"Anthropic Claude 4.5 Sonnet"` in the **blank, not-yet-sent** +Chat state — a moment
ELITEA-0569's own test never visits (its fixture-created conversation already has an ID and
skips the blank-composer state entirely).

**Dedup verdict (Rule 6): partial overlap on two axes** (conversation-creation mechanics
from ELITEA-0571's test; default-model observable from ELITEA-0569's test), **with three
case-specific gaps neither test closes**: the Private-project precondition assertion, the
`+Chat` button's own disabled/enabled state transitions, and the default-model check
happening specifically in the pre-send +Chat blank state rather than on a fixture-supplied
conversation. This is the "small number of missing assertions on an existing state-machine
test" shape `extend-existing` exists for — not a fresh scenario (the mechanics are already
proven) and not `already-covered` (the case's own distinguishing observables — Private
project, button toggle, pre-send model check — are not asserted anywhere today). See
§ Gap assertions for the precise insertion points.

## Preconditions
- User is logged in (on localhost, `auth_state` fixture skips login via `VITE_DEV_TOKEN`).
- User is in a Private project — confirmed live this run: the fixed `${ELITEA_PROJECT_ID}`
  (`399`) used by every fixture in this suite renders `"Project: Private"` in the sidebar
  combobox, and a conversation created inside it carries `"is_private": true` in its own API
  representation (see § Concrete Handles / § Network Behavior). This project is fixed by
  `.env.test`, so the precondition holds for every run in this environment — no setup step
  needed beyond what the existing fixtures already do.

## Test Data

### reuse-existing
- `${TEST_USER}` — dev-token auth, no explicit login needed on localhost.
- The covering test's own `test_msg = "at_create_ui_test"` literal — reused as-is for the
  base flow; do not introduce a second message literal for the gap assertions below (they
  observe state around the SAME send action, not a second one).

### generate-per-test (none beyond what the covering test already creates)
- No new conversation, bucket, agent, or other entity is required — the gap assertions
  observe the SAME conversation the covering test already creates and cleans up via its own
  `finally: conversation_api.delete_conversation(int(conv_id))` block.

No `generate-shared-with-cleanup` applies.

## Test Steps

*(Case's own 6 steps, executed live this run in TWO passes: an initial full pass —
`ELITEA-1808`-style manual walk creating conversation id 5484 — plus a second, pristine-tab
clean re-verification, id 5486, after an unrelated confounding finding surfaced in a THIRD,
in-between conversation — see § Known Defects Found During Exploration for why that finding
is explicitly NOT filed as a defect against this case.)*

1. Navigate to the Private project and go to the Chats page.
   - **Verify**: sidebar shows `"Project: Private"`; Chats panel visible with `"Chats"`
     heading. Confirmed live.
2. Click the `+ Chat` button in the left sidebar (`sidebar-create-button` testid).
   - **Verify**: greeting screen (`"Hello, Test! What can I do for you today?"`) shown,
     message input active/focused, **and** `sidebar-create-button` becomes `disabled`.
     Confirmed live — this is the case's own expected result AND a new gap assertion (see
     § Gap assertions GA1).
3. Type `"Generate test cases for login functionality"` in the input field.
   - **Verify**: text appears in `chat-message-input`. Confirmed live.
4. Observe the model selector — verify the default LLM is pre-selected.
   - **Verify**: `model-selector-button` shows a non-empty model name
     (`"Anthropic Claude 4.5 Sonnet"` this run — case's own `"e.g. GPT-5.2"` is explicitly an
     example, not a literal expected value). Confirmed live, in the pre-send blank-composer
     state specifically (see § Gap assertions GA2).
5. Click the Send button (`chat-send-button` testid).
   - **Verify**: a new entry appears under the `"Today"` date-group heading in the sidebar
     showing a `"Naming"` placeholder + `progressbar` spinner. Confirmed live — **but this
     state is extremely short-lived** (observed window: as little as ~100 ms in one run, up
     to ~2.4 s in another — see § Known Defects Found During Exploration's timing evidence).
     Not recommended as a hard/blocking assertion — see § Automation Hints.
   - **Also verify** (new gap assertion, GA3): `sidebar-create-button` becomes `enabled`
     again — confirmed live this happens **immediately on Send**, not gated on generation/
     naming completion (a nuance the case's own step ordering implies but does not state
     explicitly — see § Coverage Map).
6. Wait for naming to complete.
   - **Verify**: `"Naming"` placeholder resolves to a real title (a truncated version of the
     first message — NOT an AI-summarized title distinct from it; confirmed live via network
     capture, see § Network Behavior), `+Chat` button stays active (already true since
     step 5), and the LLM response renders in the message list. Confirmed live both runs (27s
     and 8s "Thought for Ns" durations respectively — model response time varies).

## Expected Results
- A new conversation is created under the Private project, auto-named from a truncation of
  the first message (not a separate AI-generated summary — see § Network Behavior), and the
  configured default LLM (`Anthropic Claude 4.5 Sonnet` in this environment) responds
  successfully.
- The `+Chat` button (`sidebar-create-button`) is `disabled` for the entire blank-composer
  window (between clicking +Chat and clicking Send) and `enabled` immediately once Send is
  clicked — not gated on naming/generation completion.
- No console errors during a clean, single-pass run (confirmed: 0 errors in both the first
  full run and the pristine re-verification run — see § Known Defects for the one CONFOUNDED
  run that did show errors, and why it's excluded).

## Coverage Map

### Axis 1 — Case element → Coverage
| Case element | Expected result | Covered by (AFS step) | Asserted where | Disposition |
|---|---|---|---|---|
| Precondition: user logged in | Session valid | Preconditions | `auth_state` fixture (skips login on localhost) | asserted *(already proven by covering tests)* |
| Precondition: user is in a Private project | Private-project context | Preconditions + Gap Step (new) | fixed `${ELITEA_PROJECT_ID}`=399 renders "Private" in sidebar combobox; conversation's own `is_private: true` API field (new assertion, GA4) | asserted |
| Step 1: Navigate to Private project + Chats page | Chats page displayed | Test Step 1 | covering test's own Step 1 (`navigate_to_chat`, `wait_for_page_load`), unchanged | asserted *(already proven)* |
| Step 2: Click +Chat button | Blank conversation opens, +Chat inactive | Test Step 2 + Gap Step GA1 (new) | covering test's own Step 2 (`click_create_conversation`) for the click+blank-state; **GA1 (new)**: `sidebar-create-button.is_disabled()` immediately after | asserted *(click mechanics already proven; disabled-state assertion is new)* |
| Step 3: Type message | Message entered | Test Step 3 | covering test's own Step 3 send-input (types via `send_message`'s `fill()`), unchanged | asserted *(already proven)* |
| Step 4: Observe model selector — default LLM pre-selected | Default LLM shown | Gap Step GA2 (new) | `get_selected_model()` truthy, asserted in the PRE-SEND blank-composer state — closes the gap ELITEA-0569's own test leaves (it only checks an already-existing fixture conversation, never the blank +Chat state) | asserted *(new — different code path than the covering sibling test)* |
| Step 5: Click Send button | New "Today" entry with "Naming…" spinner | Test Step 3 (send action) + Gap Step GA3 (new) | covering test's own send action (currently via Enter key, not click — see § Overlap check) proves the conversation-creation mechanics; **GA3 (new)**: `sidebar-create-button.is_enabled()` immediately after send | asserted *(spinner-appearance itself is NOT hard-asserted — see below; disposition: asserted for the button-toggle sub-observable, `clarification` for the spinner-timing sub-observable)* |
| Step 5 (sub-observable): "Naming…" placeholder + spinner appears | Visible transient state | — (best-effort only) | `wait_for_naming_label_to_resolve()` (existing method, tolerant of already-resolved) | `clarification` — confirmed live the state is real (screenshot evidence) but too short-lived (~100 ms–2.4 s observed) to safely hard-assert without introducing flakiness; case text is accurate, recommend NOT gating on it (see § Automation Hints) |
| Step 6: Wait for naming to complete | Auto-named, spinner gone, +Chat active, LLM responds | Test Step 5 (existing `wait_for_naming_label_to_resolve` + `wait_for_conversations_to_load` + count assertion) | unchanged | asserted *(already proven — button-active-ness already covered by GA3 firing earlier, at Send time, not gated on this step)* |
| Objective: "conversation is auto-named based on first message" | Truncated-first-message title, not a separate AI summary | — (analyst finding, informational) | confirmed live via network capture — `PUT .../conversation/.../` name field never changes from the truncated value across the whole generation lifecycle (see § Network Behavior) | asserted *(informational nuance — case text is accurate but slightly underspecifies the mechanism; not a defect)* |

### Axis 2 — Observables asserted beyond the case
- **`sidebar-create-button` disabled/enabled state transitions** (GA1, GA3) — *added:
  observed live this is a real, stable, testid-backed signal the case's own wording ("+Chat
  button becomes inactive" / "becomes active") already implies but the existing covering
  test never reads; closes that gap cheaply (no new page-object method needed beyond a
  class-level `LocatorDescriptor`, see § Automation Hints).*
- **Conversation's `is_private` API field** (GA4) — *added: a stable, non-UI signal for the
  Private-project precondition that survives UI refactors; the existing covering test
  already calls `conversation_api.get_conversation()` for other purposes, so this is a
  one-line addition to an already-open API response, not new plumbing.*
- **Network-level proof that "naming" is a truncation of the first message, not a distinct
  AI-generated summary** — *added: this materially changes what "wait for naming to
  complete" should assert (a placeholder resolving to already-known text, not a
  non-deterministic AI output) — see § Network Behavior.*
- **Timing measurement of the "Naming" placeholder's visible window** (~100 ms – 2.4 s
  across two clean runs) — *added: directly informs why this AFS recommends NOT hard-
  asserting the placeholder's appearance (a fixed low-timeout `expect(...).to_be_visible()`
  would be a coin-flip; a "wait then assert resolved" pattern, which is what the existing
  `wait_for_naming_label_to_resolve()` already does, is the correct shape).*

## Gap assertions (what the implementer appends/inserts into the covering tests)

**Covering spec 1**: `automation/tests/ui/chat/test_conversation_management.py::
TestCreateConversation::test_create_conversation_via_ui_button` (method body: lines
121–158).

**Covering spec 2** (context only, not modified): `automation/tests/ui/chat/
test_conversation_management.py::TestCreateConversation::test_new_conversation_default_settings`
(lines 180–191) — left untouched; GA2 below proves the same "default model shown" fact on
the *different* (blank, pre-send) code path this case cares about, inside covering spec 1
instead of duplicating a whole new test.

**Insertion points**: all four gap assertions are **inserted in place** around the covering
test's EXISTING steps (not appended as trailing steps) — this case's gaps are observations
about states the covering test already passes through, not a new trailing scenario:

```python
            with allure.step("Step 2 — Click Create Conversation button"):
                chat.click_create_conversation(timeout=NAVIGATION_TIMEOUT)

            with allure.step(
                "Step 2b (ELITEA-2090 extension) — Verify +Chat button is disabled in "
                "the blank-composer state, and the default LLM is pre-selected"
            ):
                # GA1 — +Chat button disabled immediately after being clicked, before Send.
                assert chat.create_conversation_button.is_disabled(), (
                    "sidebar-create-button should be disabled while a new blank "
                    "conversation is open and no message has been sent yet"
                )
                # GA2 — default LLM shown in the PRE-SEND blank-composer state (closes the
                # gap ELITEA-0569's own test leaves — it only checks an existing
                # conversation_id-fixture conversation, never the blank +Chat state).
                model_text = chat.get_selected_model()
                assert model_text, (
                    "A default model should be pre-selected before any message is sent"
                )

            with allure.step("Step 3 — Send a message to create conversation"):
                test_msg = "at_create_ui_test"
                initial_count = chat.get_message_count()
                chat.send_message(test_msg, use_enter=True)

                # GA3 — +Chat button re-enabled immediately on Send, NOT gated on
                # naming/generation completion. Confirmed live this run: re-enablement
                # happens right as the URL updates to /chat/{id}, well before the
                # "Naming" placeholder resolves or the LLM finishes responding.
                assert chat.create_conversation_button.is_enabled(), (
                    "sidebar-create-button should re-enable as soon as Send is clicked"
                )

                chat.wait_for_input_ready()
                chat.wait_for_ai_response(initial_count=initial_count, timeout=AI_RESPONSE_TIMEOUT)

            with allure.step("Step 4 — Extract conversation ID for cleanup"):
                conv_id = _extract_conversation_id(page, conversation_api, test_msg)

            with allure.step(
                "Step 4b (ELITEA-2090 extension) — Verify the conversation belongs to "
                "the Private project"
            ):
                # GA4 — Private-project precondition, verified via the conversation's own
                # API representation rather than a UI-only combobox read (no testid exists
                # on that combobox today — see § Concrete Handles).
                assert conv_id, "conv_id must be resolved before checking is_private"
                conv_data = conversation_api.get_conversation(int(conv_id))
                assert conv_data.get("is_private") is True, (
                    "Conversation created via +Chat in the Private project should be "
                    "flagged is_private=true"
                )

            with allure.step("Step 5 — Verify conversation appears in sidebar"):
                chat.wait_for_naming_label_to_resolve()
                chat.wait_for_conversations_to_load(timeout=UI_ELEMENT_TIMEOUT)
                assert chat.get_conversation_link_count() > 0, (
                    "At least one conversation should appear in sidebar after creation"
                )
```

**New page-object field required** (`automation/pages/chat_page.py`) — the two existing
methods that touch this button (`click_create_conversation`, `click_create_new_conversation`,
lines ~1055–1109) construct it **inline** (`self.page.get_by_test_id("sidebar-create-button")`),
which is pre-existing tech debt against `.claude/rules/page-objects.md`'s "locators are
class-level fields only" rule. GA1/GA3 need a reusable handle for `.is_disabled()`/
`.is_enabled()`, so add a proper class-level field rather than perpetuating the inline
pattern:

```python
create_conversation_button = LocatorDescriptor(
    testid="sidebar-create-button",
    description="+Chat / +Conversation button in the top sidebar nav. Disabled while "
                "a new blank conversation is open and unsent; re-enables immediately on Send."
)
```

(Optionally refactor the two existing methods to use this field instead of their inline
`get_by_test_id` call — out of scope for this extension but flagged since the implementer
will be touching this exact area.)

## Cleanup
1. No new entities beyond what the covering test already creates — its own
   `finally: conversation_api.delete_conversation(int(conv_id))` block (line 155) already
   covers the extended flow unchanged.
2. **This exploration run's own artifacts** (manual verification, not part of the automated
   test): three conversations were created directly via the live UI during this analysis —
   id `5484` (first full pass, message "Generate test cases for login functionality",
   deleted via UI during this session), id `5485` (confounding run — see § Known Defects,
   appears to have failed server-side creation; never appeared in the sidebar list on
   reload, nothing further to clean up), id `5486` (pristine re-verification pass, message
   "Clean run verification message", deleted via UI during this session, confirmed removed —
   0 console errors on delete). No conversations from this analysis remain in the Private
   project.
3. Local exploration screenshots (repo root, untracked): none committed as part of this AFS
   hand-off (in-session `.playwright-mcp/` snapshots/screenshots only, used for live
   verification, not attached — the timing evidence in § Known Defects is reproducible via
   the JS snippet documented there rather than a static image).

## Concrete Handles (discovered during exploration)

**Locator policy note (overrides spec-format's generic ladder):** this project's locator
policy (`.agents/testing.md` § Locator policy, `.agents/role-overrides.md`) is
**testid-only, no fallback ladder**. Every row below was confirmed live via
`document.querySelector('[data-testid="..."]')` against the running `automation/testids`
dev server this session (already synced + restarted per this run's dispatch note).

| Element | testid | Notes |
|---|---|---|
| +Chat / +Conversation button | `sidebar-create-button` | Confirmed live: text is `"Chat"` (no literal "+" in textContent — the "+" is an icon). Two-part split button — this testid is the LEFT/main action; the RIGHT chevron (opens an entity-type dropdown: Chat/Agent/Skill/Pipeline/…/Invite User) is a **separate, untested-id button** — do not click the chevron by accident (confirmed live it opens a type-selector menu, not the chat-creation flow). Existing page object (`ChatPage`) accesses this testid only via inline `get_by_test_id()` calls in `click_create_conversation()`/`click_create_new_conversation()` — no class-level `LocatorDescriptor` exists yet; add one (see § Gap assertions). |
| Message input | `chat-message-input` | Matches existing `ChatPage.message_input` field exactly. |
| Send button | `chat-send-button` | Matches existing `ChatPage.send_button` field exactly. Only present in the DOM once the input has text (absent/replaced by voice/speaking-mode controls on an empty composer). |
| Model selector button | `model-selector-button` | Matches existing `ChatPage.model_selector` field exactly. `textContent` is the live model name (`"Anthropic Claude 4.5 Sonnet"` this run) — confirmed already populated in the PRE-SEND blank-composer state (case step 4), not just after a message exists. |
| "Naming" placeholder | *(no testid — text-based)* | Existing `ChatPage.wait_for_naming_label_to_resolve()` already locates via `page.locator('text="Naming"')`; confirmed live this text + an adjacent `progressbar` role element render together, then the whole node disappears (replaced by the resolved title) once naming completes. |
| Conversation three-dot context menu button | `conversation-menu-menu-button` | **New finding**: `ChatPage.open_conversation_menu()` currently locates this via `item.locator("#conversation-menu-action")` (a DOM `id`, not a testid) — confirmed live this exact element ALSO now carries `data-testid="conversation-menu-menu-button"`. Both work today; flagging so a future testid-coverage pass can migrate `open_conversation_menu()` off the legacy `#id` selector. Out of scope to fix here (existing method works, not part of this case's own steps). |
| Delete-confirmation dialog "Delete" button | `delete-confirm-button` | Matches `components/mui.Dialog` usage elsewhere in this file; confirmed live. |
| Generic alert-dialog confirm button (e.g. "No such conversation..." info dialog) | `alert-dialog-confirm-button` | Encountered only during the CONFOUNDED run (see § Known Defects) — not part of this case's own flow; documented for completeness only. |
| Project combobox ("Project: Private") | *(no testid)* | `role="combobox"`, `textContent` = `"PProject:Private"` (avatar letter + label concatenated, no separator in the DOM text). **No `data-testid` exists on this element** — if a future case wants to assert the Private-project precondition via the UI specifically (rather than the API's `is_private` field, which this AFS uses instead), a testid would need to be added via `add-data-testid`. Not needed for THIS case's gap assertions (GA4 uses the API field instead), so no testid work was triggered this run. |

## Network Behavior
- **Conversation creation**: `POST {ELITEA_URL}/api/v2/elitea_core/conversations/
  prompt_lib/{project_id}` → `201 Created`, initial `name: "New Chat"` (the platform's
  literal default-name constant).
- **Naming resolution**: `PUT {ELITEA_URL}/api/v2/elitea_core/conversation/prompt_lib/
  {project_id}/{id}` → `200 OK`, `name` updated to a **truncation of the first user
  message** (confirmed live: `"Generate test cases for login functionality"` →
  `"Generate test cases for login"`; `"Clean run verification message"` unchanged since it
  was already ≤ the truncation length). **Confirmed via a second, later fetch of the same
  conversation (after full LLM generation completed) that the `name` field never changes
  again** — naming is a one-shot client-truncation, not a separate AI-generated summary
  step distinct from generation. This directly informs § Test Steps step 6's wording.
- **`is_private` field**: every conversation-fetch response (create, get, and the post-
  generation re-fetch) carries `"is_private": true` for conversations created in this
  Private project — the field GA4 asserts on.
- **Timing evidence for the "Naming" placeholder's visible window** (captured via a
  `document.body.innerText` poll every 100–200 ms starting immediately after the Send
  click, run twice):
  - Run A (conversation 5485, the confounded run): appeared within ~100 ms of Send,
    still visible when the same poll was re-run manually ~2 minutes later (see
    § Known Defects — this run also showed backend 400/500 errors and is excluded from the
    clean-behavior claim).
  - Run B (conversation 5486, the pristine re-verification run, **0 console errors
    throughout**): absent at t≈37.7 s (poll start), present from t≈37.9 s, still present
    through t≈40.2 s, **absent again by t≈40.4 s** — a clean ~2.4 s visible window, then
    resolved. This is the run this AFS's "do not hard-assert the spinner's appearance"
    recommendation is based on (§ Automation Hints).
- No unexpected requests observed in either clean run; 0 console errors in both (the first
  full pass and the pristine re-verification pass).

## Known Defects Found During Exploration

**None filed against this case.** One anomaly was observed and explicitly ruled OUT as
self-inflicted test-session pollution rather than a product defect, per this project's
"Synthetic Input Hygiene" / fresh-context-reverification discipline:

- **What happened**: after the first full pass (conversation 5484: created, message sent,
  full LLM response received, then **deleted via the UI** while it was still the active/
  displayed conversation), a THIRD conversation (5485) was created in the SAME tab
  immediately afterward. That conversation showed: an "info" alert dialog reading *"The
  conversation you are looking for does not exist in your project or you don't have access
  to it"*; six console errors including a `500 Internal Server Error` on
  `entity_settings/prompt_lib/399/5485` and `400 Bad Request` on both
  `conversation/prompt_lib/399/5485` and `select_conversation/prompt_lib/399/5485`
  (plus stale `400`s referencing the already-deleted `5484`); the "Naming" placeholder never
  resolved even after 2+ minutes; and on a fresh page reload, the sidebar reported
  `"Still no conversations created"` — i.e. conversation 5485 does not appear to have
  persisted correctly server-side.
- **Why this is NOT filed as a defect against ELITEA-2090**: this sequence — delete the
  active conversation via the UI, then immediately create a new one in the same tab/session
  — is **not part of this case's own precondition or steps** (the case is a single, clean
  conversation-creation flow with no prior delete). Per the `playwright-testing` skill's
  "Synthetic Input Hygiene" guidance ("a 'bug' seen only after synthetic input isn't a bug
  yet... re-verify in a new, isolated context before trusting it"), I opened a **brand new
  browser tab** (fresh React app state, same auth session) and re-ran the case's own exact
  flow with no delete beforehand (conversation 5486). That run completed with **0 console
  errors**, a clean ~2.4 s "Naming" window that resolved correctly, the `+Chat` button
  toggling exactly as GA1/GA3 describe, and clean deletion afterward (also 0 errors). This
  strongly indicates the 5485 anomaly is state pollution specific to the rapid
  delete-then-create sequence I performed while exploring — not a defect this case's own
  flow would trigger. **Recommendation, not a filed ticket**: if a future session
  reproduces conversation-creation failures specifically following a delete of the
  previously-active conversation, that would be worth its own bug report and reproduction
  pass (out of scope here — no fresh-context confirmation of THAT specific sequence was
  attempted, per the confirmation-gate discipline of not filing on a single confounded
  observation).

## Blocked Steps
None.

## Automation Hints
- Framework: Playwright + pytest (confirmed from `.agents/testing.md`).
- **Do not create a new test file.** Insert GA1–GA4 directly into
  `test_create_conversation_via_ui_button` per § Gap assertions — the covering test already
  walks through every state this case's gaps observe; a fresh test would duplicate the
  conversation-creation/send/naming mechanics for no new reason.
- **Do not hard-assert the "Naming" placeholder's appearance** (case step 5's spinner).
  Confirmed live its visible window can be as short as ~100 ms — a `expect(...).
  to_be_visible(timeout=500)`-style assertion would be a coin-flip depending on network/CPU
  timing between the Send click and Playwright's next poll. The existing
  `wait_for_naming_label_to_resolve()` (tolerant of the placeholder having already resolved
  by the time it's checked) is the correct shape; keep using it as Step 5 already does.
- **Add the `create_conversation_button` `LocatorDescriptor`** to `ChatPage` (see § Gap
  assertions) rather than reusing the two existing methods' inline `get_by_test_id()` calls
  — needed for GA1/GA3's `.is_disabled()`/`.is_enabled()` reads.
- Known related note (`.agents/testing.md` § Known issues): "Model-selector button text
  changes with the selected model" — already true here (`"Anthropic Claude 4.5 Sonnet"`,
  not the case text's illustrative `"GPT-5.2"`); GA2 asserts truthiness only, matching the
  existing sibling test's own pattern, not a literal string match.
- Wait strategy: no new network-level waits needed beyond what `send_message()` /
  `wait_for_ai_response()` already provide; GA1/GA3/GA4 are synchronous state reads
  (`.is_disabled()`, `.is_enabled()`, an already-open API response), not new async waits.
