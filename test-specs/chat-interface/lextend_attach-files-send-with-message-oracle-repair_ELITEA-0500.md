# Test Case: Chat Interface – Advanced Features – Attach Files (REPAIR / ADJUSTMENT)

> **This is an ADJUSTMENT AFS** (`adjust-automated-test`), not new coverage. It repairs an
> already-merged, already-promoted test that went red in CI. Target test:
> `automation/tests/ui/chat/test_chat_interface.py::TestConversationUIElements::test_attach_files_button_sends_file_with_message`
> (present on **both** `origin/main` and `origin/automation/base`).

## Metadata
- **TMS ID**: ELITEA-0500 (`chat-interface/ELITEA-0500_chat-interface-advanced-features.md`)
- **Board task**: EliteaAI/elitea-testing-public#1888
- **Priority**: l2 (case `priority: medium`; the test itself carries `@pytest.mark.p1`)
- **Environment Explored**: local (`http://localhost:5173`, EliteaUI `automation/testids`, DEV backend), project 471 "Elitea Testing Team", model **GPT-5.4**
- **User set**: `${TEST_USER}` — on localhost `auth_state`/`VITE_DEV_TOKEN` skips Keycloak (renders as "Test Bot"/"TB")
- **Analyst**: qa-engineer (analyst slot), 2026-08-28
- **Status**: `extend-existing` — modifies an existing merged spec; **one removal needs lead sign-off** (§ Sign-off required)
- **Triage class**: **A (test-code oracle defect) + case over-reach**, with a **D**-flavoured trigger-side nondeterminism amplifier. **NOT B, NOT C, NOT E, NOT F.**

> ⚠️ **The board card names ELITEA-1142 — that is wrong.** ELITEA-1142 maps to four
> *other* tests in this file. The owning case is ELITEA-0500, per the test's own
> `@allure.issue` decorator and ELITEA-0500's `automation_test_id` list. Do not
> re-propagate the card's error.

---

## The failure under repair

GHA run **33066098636**, target `dev.elitea.ai`, Step 7:

```
AI response should mention the unique token from the attached file (AUTOTEST_ATTACH_7X9).
Got: I don't see the file content embedded in this message—only the note about it.
     Let me read the file directly....
tests/ui/chat/test_chat_interface.py:363: assert file_acknowledged
```

---

## Verdict — H1 + H3 confirmed; H2 refuted

### H2 — product behaviour change → **REFUTED**

The attach pipeline is healthy and the model's sentence is **literally correct, by design**.

Source trace (EliteaUI `automation/testids`):

| Fact | Evidence |
|---|---|
| Selecting a file does **not** upload | `src/hooks/chat/useAttachmentState.js:13-15` — pushes `File` objects into React state only |
| Upload happens **at send time**, to a real endpoint | `src/[fsd]/features/chat/ui/chat-box/ChatBox.jsx:1080-1084` → `src/hooks/chat/useUploadWithProgress.js:52` → `POST /elitea_core/attachments/prompt_lib/{projectId}/{conversationId}` (multipart, 5 MB chunks) |
| **Only a reference reaches the model — content is NEVER inlined** | `src/common/messagePayloadUtils.js:51-55`, `:96-100`, `:179-183` — all three payload builders emit `attachments_info: [{ filepath }]` and nothing else. `user_input` is the raw typed question (`:44`, `:87`). Nothing appends file text, base64, or even the filename to the prompt. |
| The model must call a tool to read it | file lands in the `attachments` artifact bucket (`DEFAULT_ATTACHMENT_BUCKET = 'attachments'`, `src/[fsd]/shared/lib/constants/internalTools.constants.js:5`); the built-in **`attachments`** internal tool reads it |

So *"I don't see the file content embedded in this message — only the note about it"* is an
**accurate description of the product's intended contract**, not a defect. Live-confirmed: my
runs show the agent calling `read_multiple_files` against `/attachments/<uuid>/test_automation_file`.

**No `bug` issue is warranted for the attach pipeline.** Attach, upload, chip render, send and
tool-read all worked in every observation.

### H1 — oracle defect in `ChatPage.wait_for_ai_response()` → **CONFIRMED**

`wait_for_ai_response(initial_count)` (`pages/chat_page.py:2273`) returns as soon as, for the
message at index `initial_count + 1`:

1. a `Copy to clipboard` button is present **and visible**, and
2. `_extract_message_body()` returns text that `_is_transient_message()` does not recognise.

Both conditions are satisfiable **mid-turn**:

- **`_extract_message_body()` (`:2143`) collects every `<p>` and `<li>`** in the message. Streamed
  narration prose renders as `<p>`, so it returns real prose long before the turn ends.
- **`_is_transient_message()` (`:2400`) knows only six strings** — `"waking the agent"`,
  `"thinking"` (+ ellipsis variants) — plus a dynamic `"Thought for X"` pattern
  (`TRANSIENT_MESSAGES`, `:2391`). An agentic narration such as *"Let me read the file directly…"*
  is **not** in that set, so it is treated as a completed answer.
- **The Copy button demonstrably flickers ON mid-turn.** Observed in **all three** instrumented
  runs, while the body was still a tool-call label:

  | Run | Copy button appears | Body at that instant | Disappears |
  |---|---|---|---|
  | 1 | t = 11.3 s | `Attachments: read_multiple_fi…` | t = 12.3 s |
  | 2 | t = 11.1 s | `Attachments: read_multiple_fi…` | t = 11.7 s |
  | 3 | t = 10.7 s / 11.0 s | `Thought for less than a second` | — |

  Run 3 is the decisive one. Instrumenting the oracle's **exact** condition:

  ```
  [ORACLE] t=10.7s copyVisible transient=True  body='Thought for less than a second'
  [ORACLE] t=11.0s copyVisible transient=True  body='Thought for less than a second'
  [ORACLE] t=18.9s copyVisible transient=False body="I'll read the content of the attached file for you...."
  ```

  At t = 10.7 s the oracle's **first** condition (copy button visible) was already TRUE. The only
  thing that prevented an early return was `_is_transient_message` happening to match the
  `"Thought for …"` pattern. **Substitute narration prose for that placeholder — exactly what DEV
  captured — and `transient` is `False`, the oracle returns, and `get_last_message_text()` reads
  the narration.** That is the CI failure, reproduced in mechanism.

- **Secondary defect, same method:** the wait settles on index `initial_count + 1`, but
  `get_last_message_text()` (`:2243`) reads `messages_container.last`. These are the same element
  only while the assistant emits exactly one message. They are **not** guaranteed to be the same
  element, and nothing in the test ties the assertion to the message the wait actually settled on.

**Blast radius — this is not a one-test bug.** `wait_for_ai_response` is the shared chat oracle.
ELITEA-2201's merged test (`test_send_message_with_attachments_verify_included.py`) reads its AI
response through the same method and carries the same latent race. See § Escalation.

### H3 — case over-reach → **CONFIRMED (documentary, not probabilistic)**

ELITEA-0500's **Step 1** expected result is, in full:

> *"The attach files button is visible and accessible near the chat input."*

There is **no step anywhere in ELITEA-0500** — and nothing in its Coverage bullets, Pass/Fail
criteria, or Expected Final State — requiring the AI to read an attachment's content or echo a
token from it. The `file_acknowledged` assertion verifies a requirement the case does not contain,
and does so through the least deterministic path in the system (LLM tool-call election →
tool-execution latency → streaming render → DOM oracle).

This is the documented trigger-side flake class (`.agents/testing.md` § Known issues: HITL
trigger-side, toolkit-chat `agent_tool_end`, mermaid render): a *precondition* that the model
elects, upstream of everything the case asserts, and therefore never a member of a sanctioned-RED set.

**Corroborating precedent — the team already hit this exact wall.** ELITEA-2201's AFS records that
its own per-file assertion went red at the batch gate and was deliberately broadened to "any one of
three markers", because *"the model varies its engagement style run to run"*. That AFS also records
a run in which the model's own trace said *"The content has been embedded directly in the messages,
so I don't need to use file reading tools"* — the **opposite** of the DEV failure text. Both
behaviours are real; which one occurs is not controlled by the test.

### Reproduction status — stated honestly

**6 live observations on localhost, 0 reds.**

| # | What | Result |
|---|---|---|
| 1–3 | Instrumented probe (real code path, real attach, real send) | 3× green; mid-turn Copy-button flicker captured in all 3 |
| 4–6 | The **actual** failing test, clean process each time | 3× **PASSED** (29.24 s / 28.95 s / 28.91 s) |

```
cd automation && HEADLESS=true ../.venv/bin/pytest \
  "tests/ui/chat/test_chat_interface.py::TestConversationUIElements::test_attach_files_button_sends_file_with_message" \
  -v -p no:cacheprovider --reruns=0        # ×3 → 1 passed each
```

**I did not reproduce the red.** Green locally + red in CI is, by the skill's own rule, *not* drift —
and the mechanism above explains why it is intermittent rather than deterministic. The verdict rests
on (a) the documentary fact that the assertion is not in the case, (b) the source fact that content
is never inlined, and (c) the live-captured mid-turn oracle window — **not** on a reproduction.

---

## Additional defect found: masking already present in the test

Step 3 currently ends with:

```python
if not file_attached:
    pytest.skip("File attachment UI not accessible — attach button exists but "
                "file could not be attached via input or file chooser methods.")
```

**This is defect masking and must go.** ELITEA-0500's own Fail criteria include *"Attach files
button missing"* — i.e. an unattachable file is precisely the failure this case exists to catch.
The `skip` converts that red into a silent non-result. Forbidden by `.agents/profile.md`
§ Bug filing ("Never mask") and the team's no-masking rule.

## Additional finding: the test drives a hidden decoy button

The current locator `button[aria-label="attach files"] input[type="file"]` resolves, with the plus
menu **closed**, to the **invisible decoy** `AttachmentButton` at `PlusChatButton.jsx:336-343` —
0×0, `overflow: hidden`, `pointerEvents: 'none'`, passed **no `testId`**, existing only to expose the
drag/drop `onDrop` handle (`styles.hiddenAttachment`, `:452-458`). Live-confirmed: with the menu
closed the probe measured `file_input.count() == 1`, and that one match is the decoy.

It "works" only because `set_input_files` operates on hidden inputs. The user-visible control is the
plus-menu item `chat-attach-menuitem-button`. The repair routes through the real control.

---

## Repair spec — the exact assertion set

Preserve `TestConversationUIElements`, the test name, `@allure.issue`, `@pytest.mark.p1`, and the
`allure.step("Step N — …")` structure. **Update in place — no new file, no new class.**

### REMOVE

| # | Remove | Why this is not a weakening |
|---|---|---|
| R1 | Step 7's `file_acknowledged` token-echo assertion + the `normalized_response` line | Verifies a requirement **absent from ELITEA-0500**, through the most nondeterministic path in the system. Removing an assertion the case never specified does not reduce the case's coverage. ⚠️ **But see § Sign-off required — there IS a transient gap on `main`.** |
| R2 | Step 7's `"waking" not in ai_response` assertion | Subsumed — the repaired test no longer reads AI prose at all. |
| R3 | Step 3's `pytest.skip(...)` fallback | **Masking** (above). An unattachable file must fail. |
| R4 | The 3-tier raw-handle fallback ladder (direct input → `expect_file_chooser` → plus-menu popper) and its `try/except` swallowing | Legacy pre-policy raw handles (#25/#42 tech debt, not precedent); tier 1 drives the hidden decoy. Replaced by one testid'd path. |
| R5 | Step 5's `wait_for_ai_response` + `wait_for_network(AI_RESPONSE_TIMEOUT)` | The repaired test asserts nothing about AI prose, so it must not depend on the defective oracle. Message-count growth is awaited on the DOM directly. |

### KEEP / ADD — case-faithful assertion set

| Step | Action | Assertion | Handle (all testid, all `on-main ✓`) |
|---|---|---|---|
| 1 | Navigate to the fresh conversation | — | `conversation_id` fixture |
| 2 | **ELITEA-0500 Step 1 (currently uncovered — see § Coverage Map)** — open the plus menu | Plus-menu trigger visible **and enabled**; attach item visible **and enabled**, positioned in the composer toolbar | `plus-menu-button`, `chat-attach-menuitem-button` |
| 3 | Create the `.txt` file (`tmp_path`) and attach it via the real control | `ChatPage.attach_file(path)` succeeds; **chip renders** (`wait_for_attachment_chip_count(1)`); chip name == the filename; the "Attach Files (N left)" counter reads **"9 left"** (decremented by exactly 1 from a fresh conversation's 10) | `chat-attachment-chip-{index}` (`CHAT_ATTACHMENT_CHIP`), `chat-attach-menuitem-button` text |
| 4 | Capture `initial_count`; type + send | Input holds the typed text before send | `chat-message-input`, `chat-message-item` |
| 5 | Wait for the **user** message to land | Message count **increases** (web-first wait on `chat-message-item` count > `initial_count`) — **no AI oracle** | `chat-message-item` |
| 6 | Verify the attachment was **submitted with the message** | The sent user message's text contains the **filename** — the system's own render of what it transmitted | `chat-message-item` at `initial_count` (`get_message_text_at`, not `.last`) |
| 7 | Verify the composer cleared | `wait_for_attachment_chip_count(0)` **and** `get_attachment_overflow_count() == 0` | chip helpers |
| 8 | Side channel | No unexpected console errors / page errors, via `utils/console_errors.collect_console_errors(page)` (URL-bearing — migrate this spec while touching it, per `.agents/testing.md`) | — |

**No new testids. No new page-object methods.** `ChatPage.attach_file()` (`:2831`),
`open_attach_menuitem()` (`:2794`), `wait_for_attachment_chip_count()` (`:3025`),
`get_attachment_chip_count()` (`:2972`), `get_attachment_overflow_count()` (`:2976`),
`get_message_text_at()` (`:2258`) all already exist.

### Optional Axis-2 addition (declared improvisation — lead's call)

Assert the **upload response** rather than the model's prose: capture
`POST /elitea_core/attachments/prompt_lib/{projectId}/{conversationId}` via
`page.expect_response(...)` and assert `status == 200` and that the returned `filepath` is
non-empty. This is deterministic, is produced **entirely by the system** (the § Fidelity policy
"capture the real response and assert the UI against it" pattern), and proves transmission without
touching the LLM. It is **beyond ELITEA-0500's text**, so it is declared, not assumed —
recommend including it; it is the honest replacement for what R1 removes.

---

## Coverage Map

**Axis 1 — ELITEA-0500 elements owned by THIS test.** ELITEA-0500 is a multi-test case; its other
steps belong to the five sibling tests listed in its `automation_test_id`.

| Case element | Expected result | Covered by | Asserted where | Disposition |
|---|---|---|---|---|
| Step 1 — attach files button visible/accessible near chat input | Button visible and accessible | repair steps 2–3 | step 2: visible + enabled; step 3: it actually attaches | **asserted (newly — see below)** |
| Coverage bullet — "Attach files button opens file picker" | Picker opens | repair step 3 | `attach_file()` drives the real control end-to-end | asserted |
| Fail criterion — "Attach files button missing" | Test must FAIL | R3 | `skip` removed → natural fail | asserted |
| *(Steps 2–7: context settings, model menu, sidebar, agents nav, search, oversized message)* | — | **the five sibling tests** | — | out-of-scope for this test |
| ~~AI echoes attachment token~~ | — | — | — | **not a case element — removed (R1)** |

> **ELITEA-0500 Step 1 is presently covered by NOTHING.** The case names
> `TestConversationUIElements::test_attach_files_button_opens_picker` as its Step-1 test, and that
> test **does not exist** in the repo (§ Stale correlation keys). So repair step 2 does not merely
> preserve coverage — it **restores** a case requirement that is currently unverified.

**Axis 2 — analyst additions beyond the case:**
- Chip render + "9 left" counter decrement (step 3) — *the system's own confirmation that the attach
  the case asks about actually took effect; visibility alone cannot distinguish a live control from a dead one.*
- Filename present in the sent message (step 6) — *proves the attachment was submitted with the
  message, which is the honest, deterministic core of what R1 removed.*
- Composer-clears-after-send (step 7) — *cheap, deterministic, and the established idiom in every
  sibling attachment test.*
- Console/page-error side channel (step 8) — *standard project discipline.*
- *(Optional)* upload-response assertion — *declared above.*

---

## Concrete Handles (verified live this session)

Locator policy: **testid-only**. Provenance re-verified with a fresh
`cd ../EliteaUI && git fetch origin`, two-stage grep per `.agents/workflow.md` § Closure record:

| Element | Testid | main / automation/testids |
|---|---|---|
| Plus-menu trigger | `plus-menu-button` | **on-main ✓** |
| "Attach Files" popper item | `chat-attach-menuitem-button` | **on-main ✓** |
| Attachment chip (dynamic) | `chat-attachment-chip-{index}` | **on-main ✓** |
| Message item (user + AI) | `chat-message-item` | **on-main ✓** |
| Message input | `chat-message-input` | **on-main ✓** |
| Send button | `chat-send-button` | **on-main ✓** |
| Composer dropzone (not used by repair) | `chat-composer-dropzone` | main: **no** · testids: YES |

**Zero new testids needed; zero promotion gap for the repair** — every handle the repaired test uses
is already on `origin/main`, so the fix is safe to promote with the test. (Class **F** is therefore
ruled out: no testid this test depends on is missing from `main`.)

Raw handles being **removed**: `button[aria-label="attach files"] input[type="file"]`,
`get_by_role("button", name="attach files")`, `get_by_role("button", name="plus menu")`,
`.MuiPopper-root`. Net change to non-testid handles: **negative**.

## Network Behavior
- `POST /elitea_core/attachments/prompt_lib/{projectId}/{conversationId}` — multipart, field `file`,
  `overwrite_attachments=1`, 5 MB chunking (`useUploadWithProgress.js:52,93-98`). Fires **at send**, not at select.
- Predict payload carries `attachments_info: [{ filepath }]` only (`messagePayloadUtils.js:51-55/96-100/179-183`).
- Backend emits a `chat_predict_attachment` socket event for indexing progress
  (`src/components/Chat/hooks.js:1486-1502`, subscribed `:1687`).
- No `socket_validation_error` frames observed in any run.

## Known Defects Found During Exploration
**None in the product.** Attach → upload → chip → send → tool-read behaved correctly in all
6 observations. The findings are in the **test** (oracle, masking, decoy locator) and in the
**TMS metadata** (below).

## Blocked Steps
None.

---

## Sign-off required (preserve-the-nature rail)

R1 deletes an assertion. Per `adjust-automated-test` § Step 3, that needs **explicit human sign-off
recorded in the PR body** — I do not take it unilaterally. The honest statement of the trade:

- **Against the case (ELITEA-0500): not a weakening.** The token echo is not a case element. Its
  removal costs the case nothing, and the repair *adds* coverage of Step 1, which is currently
  verified by nothing at all.
- **Against `main` as a whole: a genuine, temporary gap.** The observable "an attachment's content
  actually reaches the model" is covered honestly by ELITEA-2201
  (`test_send_message_with_attachments_verify_included.py`, per-file marker assertion at
  `:241`) — but **that test is on `automation/base` and NOT yet on `main`**:

  ```
  test_send_message_with_attachments_verify_included.py   main:no   base:YES
  test_attach_files_10_file_limit_warning.py              main:YES  base:YES
  ```

  So between this repair landing on `main` and ELITEA-2201's promotion, `main` has no test asserting
  that attachment content reaches the model.

**My recommendation:** accept R1. The assertion was never a reliable guard — it passes or fails on
the model's mood, so its removal loses a *signal that was already noise*, and the coverage it
nominally provided returns (deterministically, per-file, already-hardened) the moment ELITEA-2201
promotes. Taking the optional Axis-2 upload-response assertion closes most of the gap immediately
and deterministically. But this is the lead's call to record, not mine.

## Stale correlation keys in ELITEA-0500 (separate defect — flagged, not fixed)

`adjust-automated-test` § Step 4 requires flagging an `automation_test_id` that does not resolve.
**2 of ELITEA-0500's 8 entries reference tests that do not exist:**

```
MISSING  TestContextAndSettings::test_model_settings_menu
MISSING  TestConversationUIElements::test_attach_files_button_opens_picker
EXISTS   TestContextAndSettings::test_edit_context_settings
EXISTS   TestConversationUIElements::test_attach_files_button_sends_file_with_message
EXISTS   TestSidebarNavigation::test_open_close_sidebar
EXISTS   TestSidebarNavigation::test_navigate_to_agents_from_sidebar
EXISTS   TestSearchAndErrorHandling::test_search_conversations_dialog
EXISTS   TestSearchAndErrorHandling::test_handle_message_send_failure
```

Both break TMS correlation **silently** (🟥 gap in `automation_coverage`, never an error). This is
also *why* ELITEA-0500 Step 1 is unverified: the case believes `test_attach_files_button_opens_picker`
covers it. Orchestrator-owned (back-writes are never an analyst's job).

## Escalation — the oracle defect is suite-wide, not local to this test

`ChatPage.wait_for_ai_response()` is the shared chat oracle. The repair **routes around** it for this
test (which no longer asserts AI prose) but does **not fix** it. Every chat test that reads AI prose
through it carries the same latent race — including ELITEA-2201's merged test, which asserts
per-file references off `wait_for_ai_response` + `get_last_message_text`.

This is a cross-cutting page-object change with real blast radius, so per my slot contract it is
escalated rather than specced here. Sketch of the fix, for whoever picks it up:

1. `_is_transient_message` cannot enumerate agentic narration — the completion signal must not be a
   string blocklist. Prefer a **positive** end-of-turn signal (the streaming-complete state the
   product itself knows about, e.g. the absence of `chat-stop-generation-button`, or a
   `socket.io` turn-complete frame via `utils/websocket_frames.py`) over "Copy button + text that
   isn't on a list of six placeholders".
2. Tie the read to the settled element: `wait_for_ai_response` settles index `initial_count + 1`
   while `get_last_message_text()` reads `.last`. Either return the settled locator, or read via
   `get_message_text_at(initial_count + 1)`.
3. Require the completion signal to be **stable** (e.g. present across ≥2 consecutive polls
   spanning >1 s), which alone would have defeated the ~0.6 s flicker measured here.

Recommend a `question` card, not a silent fix inside this repair.

## Questions for a human (I did not guess)

1. **Sign off R1?** (delete the token-echo assertion) — options: (a) accept as specced, ELITEA-2201
   restores the observable on promotion; (b) accept **and** take the optional Axis-2 upload-response
   assertion; (c) reject and keep an AI-content assertion in this test, broadened 2201-style.
   **Recommend (b)** — case-faithful, deterministic, and closes the `main` gap now.
2. **Fix the shared oracle?** — options: (a) separate `question`/tech-debt card, repair lands first;
   (b) fold the oracle fix into this repair. **Recommend (a)** — the blast radius (every chat spec)
   should not ride a single-test repair PR, and this repair does not depend on it.
3. **Back-write ELITEA-0500's two stale `automation_test_id` entries?** — options: (a) drop the two
   missing refs; (b) keep `test_attach_files_button_opens_picker` and author it as new `[Automate]`
   work. **Recommend (a) now + (b) as a follow-up card** — noting the repair's step 2 already
   restores Step-1 verification, so (b) is no longer urgent.
4. **AFS directory.** The dispatch said `test-specs/chat/`; the project's actual directory (145 AFS
   files, matching the case's `module: chat-interface`) is `test-specs/chat-interface/`. I followed
   the project convention. Flagging in case `chat/` was deliberate.

## Evidence (on disk — upload + embed per § screenshot evidence; I did not upload)

| Artifact | Path |
|---|---|
| Attach control visible near composer (ELITEA-0500 Step 1) | `<repo-root>/ELITEA-0500-step-01-attach-button-visible.png` (absolute: `/Users/Alexander_Bychinskiy/Library/CloudStorage/OneDrive-EPAM/Github/EliteaAutomationFactory/elitea-testing-public/ELITEA-0500-step-01-attach-button-visible.png`) |
| Full oracle timeline, 3 instrumented runs (per-poll copy-button state + extracted body) | `/tmp/afs-attach/ELITEA-0500-oracle-timeline.json` |

The scratch probe used to produce the timelines was deleted after the run — it is not a deliverable
and nothing in the repo references it.
