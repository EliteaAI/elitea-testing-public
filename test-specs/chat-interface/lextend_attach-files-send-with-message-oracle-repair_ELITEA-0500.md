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
- **Status**: `extend-existing` — modifies an existing merged spec. **No assertion is deleted**; the opaque-token oracle is *replaced* by a comprehension fact per canon card **#1664** (a change of HOW, not WHAT), so **no human sign-off is required.** Suite-wide oracle fix tracked as **#1913**.
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

**Oracle shape governed by canon card #1664** (§ #1664 applies here). The last-mile LLM assertion is
a **comprehension fact in ordinary prose**, never an opaque-token echo. The strong deterministic
assertions live on the **transport** layer.

### Test data — the planted comprehension fact (replaces the token)

`tmp_path` file `test_automation_file.txt`, ordinary prose, no identifier-shaped strings:

```
Project Aurora - weekly status.
The project mascot is the otter.
The team meets on Tuesday.
```

Question sent: **`"According to the attached file, what is the project mascot? Answer with the single word."`**
Expected comprehension answer: **`otter`** (case-insensitive substring of the settled reply).

`AUTOTEST_ATTACH_7X9` is deleted **as an oracle**, not as coverage — the observable ("the model
received and processed the file's content") is unchanged and is now asserted three independent ways.

### REMOVE

| # | Remove | Why this is not a weakening |
|---|---|---|
| R1 | Step 7's `file_acknowledged` **opaque-token echo** (`AUTOTEST_ATTACH_7X9`) | **Not a deletion — a substitution of oracle shape** (#1664). The same observable is asserted by the comprehension fact (step 8) plus two transport assertions (steps 6, 9). Per #1664: *"Both patterns are equally honest about fidelity; only one is stable."* This changes **HOW** the observable is read, not **WHAT** is verified — inside the declared-improvisation ceiling (`.agents/role-overrides.md`), unlike the deletion I proposed in v1 and withdrew. **No human sign-off required.** |
| R2 | Step 7's `"waking" not in ai_response` assertion | Subsumed by the corrected settle condition, which cannot return on a transient. |
| R3 | Step 3's `pytest.skip(...)` fallback | **Masking.** ELITEA-0500's Fail criteria include "Attach files button missing" — an unattachable file must fail. |
| R4 | The 3-tier raw-handle fallback ladder and its `try/except` swallowing | Legacy pre-policy raw handles (#25/#42 tech debt); tier 1 drives the hidden decoy. One testid'd path replaces it. |
| R5 | `wait_for_ai_response` **as currently implemented** | **Replace, don't drop** — the test still needs a settled turn. Use the corrected settle condition (step 8) locally in this spec; the suite-wide fix is **#1913**. |

### KEEP / ADD — the implementer's step-by-step assertion set

Enter `ChatPage.capture_websocket_frames()` **before** any navigation (the `websocket` event fires
only at connection-open time).

| Step | Action | Assertion | Handle / source |
|---|---|---|---|
| 1 | Enter frame capture, then navigate to the fresh conversation | — | `conversation_id` fixture |
| 2 | **ELITEA-0500 Step 1** — open the plus menu | Plus-menu trigger **visible and enabled**; attach item **visible and enabled** in the composer toolbar | `plus-menu-button`, `chat-attach-menuitem-button` |
| 3 | Write the planted-fact file; attach via `ChatPage.attach_file()` | `wait_for_attachment_chip_count(1)`; chip name == filename; capacity counter **decrements by exactly one** from a runtime-read baseline (never a hardcoded number — see § As-shipped deviations 1) | `chat-attachment-chip-{index}`, `chat-attach-menuitem-button` text |
| 4 | Type the comprehension question | `message_input.input_value()` == the question | `chat-message-input` |
| 5 | Capture `initial_count` | — | `chat-message-item` |
| 6 | **Send, wrapped in `page.expect_response(...)`** — upload fires at *send*, not at attach (`ChatBox.jsx:1080-1084`) | **TRANSPORT 1:** response to `POST **/attachments/prompt_lib/**` has `status in (200, 201)` **and** a non-empty `filepath` in the body | `useUploadWithProgress.js:52` |
| 7 | Wait for the user message to land | Message count > `initial_count`; the message at index `initial_count` contains the **filename** (the system's own render of what it transmitted) | `get_message_text_at(initial_count)` — **not** `.last` |
| 8 | **LAST MILE — auto-retrying assertion at the fixed index.** No settle detection at all | `expect(chat.messages_container.nth(initial_count + 1)).to_contain_text(expected_answer, ignore_case=True, timeout=ATTACHMENT_ANSWER_TIMEOUT)` with `ATTACHMENT_ANSWER_TIMEOUT = 90_000`. Web-first: it keeps polling **that same message** until the answer lands, so a mid-turn narration cannot satisfy it **by construction** | `chat-message-item` (`main:YES`) |
| 9 | **TRANSPORT 2 — frame assertion** (see § Frame-assertion constraints) | ≥1 received `chat_predict_attachment` frame whose `response_metadata.tool_name == "read_multiple_files"` **and** carries a `tool_output`; **every** such `tool_output` contains the planted fact (`"The project mascot is the otter."`) | `utils/websocket_frames.py` |
| 10 | Composer cleared | `wait_for_attachment_chip_count(0)` **and** `get_attachment_overflow_count() == 0` | chip helpers |
| 11 | Side channel | No unexpected console errors, via `utils/console_errors.collect_console_errors(page)` (URL-bearing — migrate this spec while touching it), **and** no uncaught page errors, via a `page.on("pageerror", …)` listener bound before navigation (an uncaught JS exception logs nothing to the console — the two listeners catch disjoint classes) | — |

**No new testids. No new page-object methods.** `open_attach_menuitem()` (`:2794`),
`wait_for_attachment_chip_count()` (`:3025`), `get_attachment_overflow_count()` (`:2976`),
`get_message_text_at()` (`:2258`), `messages_container` (`:843`) all already exist.
`capture_socketio_frames(page)` is called **directly** from `utils/websocket_frames.py` (see
§ As-shipped deviations).

### Why step 8 has no settle detection — and why `chat-stop-generation-button` was rejected

An earlier draft specced a stability-window settle keyed on `chat-stop-generation-button`
(*"not visible + Copy visible + stable ≥1.2 s"*). **That handle is NOT on EliteaUI `main`** —
verified fresh, `git fetch origin` then the two-stage grep:

```
chat-stop-generation-button        main:NO   testids:YES   (src/ComponentsLib/Chat/UserInput.jsx:531)
plus-menu-button                   main:YES  testids:YES
chat-attach-menuitem-button        main:YES  testids:YES
chat-attachment-chip               main:YES  testids:YES
chat-attachment-overflow-button    main:YES  testids:YES
chat-message-input                 main:YES  testids:YES
chat-send-button                   main:YES  testids:YES
chat-message-item                  main:YES  testids:YES
```

**This repair targets `main`, and the spec runs in GHA against dev.elitea.ai, which serves `main`.**
Localhost serves `automation/testids`, which HAS the testid — so the rejected design would have gone
**green in every local run and red on DEV**. We would have fixed one DEV red by shipping a different
one, and no amount of local evidence would have revealed it.

> **The general rule, for the next reader:** *a handle verified against the working tree is verified
> against `automation/testids`. A spec targeting `main` must be verified against `main`.* Run
> `git fetch origin` and grep `origin/main` explicitly — the dev server's green is not evidence about
> `main`. This is `.agents/workflow.md`'s ordering invariant biting from an easy-to-miss angle,
> because the testid was already live on the dev server the whole time the design was being measured.

**My process failure, recorded so it isn't repeated:** the handle entered via the *step table*
without a corresponding row in § Concrete Handles, so it bypassed the provenance check that every
other handle passed. **Any handle named in a step row must also appear in the handles table.**

**The shipped design is strictly stronger, not merely a workaround.** A stability window infers
"the turn is done" and can be wrong; the auto-retrying indexed assertion never needs to know. If the
model narrates a tool call first and answers later, `to_contain_text` keeps polling the same message
until the answer arrives. The mid-turn narration that caused the DEV red **cannot satisfy it by
construction**, rather than by a better transient-string blocklist. It also needs no testid that
isn't on `main`. Existing in-repo idiom, not an invention:
`test_create_agent_via_chat_canvas.py:345`, `test_pipeline_flow_editor_add_llm_node_from_chat_canvas.py:365`.

The `.last` → `get_message_text_at(initial_count + 1)` / `.nth(initial_count + 1)` **indexing
correction is preserved and still load-bearing** — it is what pins the assertion to the assistant's
turn instead of whatever message happens to be last.

### As-shipped deviations (implementer-declared, lead-accepted — part of this contract)

1. **Step 3 asserts the capacity counter DECREMENTS BY ONE, with the baseline read at runtime** —
   `remaining_before = chat.get_remaining_attachment_slots()` before the attach, then
   `to_contain_text(f"{remaining_before - 1} left")` after. **Neither endpoint value is hardcoded**,
   because `MAX_ATTACHMENTS` is a **per-project backend value**, not a product constant:
   `useChatConfig.js:27` → `data.chat_max_upload_count ?? ATTACHMENT_LIMITS.MAX_ATTACHMENTS`, fed by
   `useGetChatConfigQuery({ projectId })`; the literal in `common/constants.js` is only the
   client-side fallback. A hardcoded `"10 left"` would be green on this backend and red on any env
   configured otherwise (`test-ui-next.yml`, `test-ui-stage2.yml`, or dev.elitea.ai after a config
   change) — **a coupling the main-provenance check cannot catch, because the value never comes from
   `main` at all.** (Review catch, fix round 1; the *decrement* was always the intended evidence —
   the first implementation drifted from this rationale.)
   Two supporting mechanics, both source-verified:
   - **The in-flight fallback race is closed at Step 1**, not tolerated. `useChatConfig.js:22-24`
     (`if (!data) return ATTACHMENT_LIMITS`) renders the static fallback until the config query
     lands, so a baseline read too early can latch a value the product is about to replace. Step 1
     therefore wraps the navigation in
     `page.expect_response(lambda r: "/elitea_core/chat_config/prompt_lib/" in r.url)`
     (`src/api/chatConfig.js`) — the baseline is provably the environment's real value.
   - **The popper stays open across the attach**: nothing in `PlusChatButton.jsx` calls
     `setIsOpen(false)` on attach, so the counter updates in place with no re-open.
2. **Step 3's chooser handshake.** Step 2 must leave the popper **open** to assert the attach item is
   visible/enabled (it is not in the DOM otherwise), so Step 3 clicks the **already-open** item inside
   `page.expect_file_chooser(...)` rather than calling `ChatPage.attach_file()`, which would re-open
   the menu and toggle it closed.
3. **`capture_socketio_frames(page)` is called directly** from `utils/websocket_frames.py`, because
   the `ChatPage.capture_websocket_frames()` wrapper is base-only. The wrapper merely delegates to
   this collector; entered **before navigation** per its docstring.
4. **Step 7 ships as a web-first assertion, not a one-shot read.** The step table specifies
   `get_message_text_at(initial_count)`; the code ships
   `expect(chat.messages_container.nth(initial_count)).to_contain_text(file_name, …)`. Same message,
   same index, same observable — but auto-retrying, so it cannot race the user message's render.
   A **strengthening**, and the same web-first instinct step 8 is built on. (Recorded in fix round 1;
   the drift was previously undeclared.)
5. **One new page-object method: `ChatPage.get_remaining_attachment_slots()`** — the step table said
   "no new page-object methods", but deviation 1's runtime baseline needs one. It parses the `N left`
   counter off `chat-attach-menuitem-button`, exactly mirroring the existing
   `get_attachment_overflow_count()` idiom (regex over a control's own text), and raises rather than
   returning a silent `0`, which would make a decrement assertion pass vacuously. Purely additive.

### Frame-assertion constraints (step 9) — mandatory, from `.agents/testing.md` § ELITEA-1140

1. **Self-diagnosing message.** The failure message MUST carry the **total captured frame count**,
   the **distinct event names**, and the **distinct `(event, tool_name)` pairs** seen (the pairs are
   what `.agents/testing.md` § ELITEA-1140 specifies, and they are what separates a backend tool
   rename from the model declining to call it — opposite responses), so the outcomes read
   differently:
   - `0 matching of 0 frames captured` → the Socket.IO capture/transport failed — a **harness**
     problem (every frame behind this oracle was captured on **localhost**; this spec also runs in
     GHA against deployed envs where the transport was never verified — a proxy declining the
     websocket upgrade produces exactly this).
   - `0 matching of N frames captured` **with other tool names in the pairs** → the backend renamed
     or switched the read tool; **fix this spec**.
   - `0 matching of N frames captured` **with no tool calls at all** → frames flowed but the model
     declined to call the tool this turn — the trigger-side flake below; **re-run**.
   The expected tool name is hoisted to a module constant (`EXPECTED_ATTACHMENT_TOOL`) so the
   predicate and the failure message cannot drift apart.
   - Suggested shape: `f"expected >=1 chat_predict_attachment frame carrying tool_output for read_multiple_files; got {len(matches)} of {len(frames)} captured frames (events: {sorted(events)})"`
2. **Never conditional, never skipped.** Do **not** guard this assertion on "frames present". If the
   transport differs on DEV we want a legible red, not a silent pass. A `pytest.skip` here is the
   same masking as R3.
3. **`>= 1` plus all-match, never `frames[0]`.** Multiple `chat_predict_attachment` frames carry this
   tool (observed: 3 in one run — two with `tool_meta`, one with `tool_output`). Assert `>= 1`
   **and** that every frame carrying a `tool_output` for this tool satisfies the expectation —
   the ledger's explicit warning against reading `frames[0]` off a success-then-failure pair.

### Trigger-side caveat on step 9 — stated, not hidden

Step 9 asserts a **tool call happened**. I have been flagging tool-election nondeterminism all along,
so I will not quietly spec a dependency on it. Evidence that this one is **pipeline-driven rather
than model-elected**: the read fired **8/8**, including runs whose prose claimed the content was
already *"embedded in your message"* — a model that believed that would not elect a read. Combined
with the source finding that content is never inlined (the backend must read the file to give the
model anything), the read appears unconditional.

That is an **inference from 8 runs on one model**, not a proof. Constraint 1's self-diagnosing
message is precisely the protection: if the inference is wrong, the failure says
`0 matching of N frames` and names the real cause instead of looking like a product regression.

## Coverage Map

**Axis 1 — ELITEA-0500 elements owned by THIS test.** ELITEA-0500 is a multi-test case; its other
steps belong to the five sibling tests listed in its `automation_test_id`.

| Case element | Expected result | Covered by | Asserted where | Disposition |
|---|---|---|---|---|
| Step 1 — attach files button visible/accessible near chat input | Button visible and accessible | repair steps 2–3 | step 2: visible + enabled; step 3: it actually attaches | **asserted (newly — see below)** |
| Coverage bullet — "Attach files button opens file picker" | Picker opens | repair step 3 | the real `chat-attach-menuitem-button` control drives the chooser end-to-end (§ As-shipped deviations 2) | asserted |
| Fail criterion — "Attach files button missing" | Test must FAIL | R3 | `skip` removed → natural fail | asserted |
| *(Steps 2–7: context settings, model menu, sidebar, agents nav, search, oversized message)* | — | **the five sibling tests** | — | out-of-scope for this test |
| ~~AI echoes an opaque token~~ | — | replaced | steps 6, 8, 9 | **oracle shape swapped per #1664** — the observable (model received + processed the file) is now asserted by a comprehension fact (step 8) + upload response (step 6) + `tool_output` frame (step 9). Not a case element either way. |

> **ELITEA-0500 Step 1 is presently covered by NOTHING.** The case names
> `TestConversationUIElements::test_attach_files_button_opens_picker` as its Step-1 test, and that
> test **does not exist** in the repo (§ Stale correlation keys). So repair step 2 does not merely
> preserve coverage — it **restores** a case requirement that is currently unverified.

**Axis 2 — analyst additions beyond the case:**
- Chip render + capacity-counter decrement (step 3) — *the system's own confirmation that the attach
  the case asks about actually took effect; visibility alone cannot distinguish a live control from a dead one.*
- Filename present in the sent message (step 7) — *proves the attachment was submitted with the
  message, which is the honest, deterministic core of what R1 removed.*
- Composer-clears-after-send (step 10) — *cheap, deterministic, and the established idiom in every
  sibling attachment test.*
- Console/page-error side channel (step 11) — *standard project discipline.*
- Upload-response assertion (step 6) and `tool_output` frame assertion (step 9) — *the transport-layer half of #1664's split: the strong deterministic assertions belong there, and the comprehension fact is the last mile, not the whole proof. Both are model-wording-independent.*

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
| **Stop-generation (REJECTED — not used)** | `chat-stop-generation-button` | **main: NO** · testids: YES — disqualifying for a `main`-targeted spec; see § Why step 8 has no settle detection |

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

## Corrected-oracle hit rate — the experiment that fixed the settle condition

**Question:** under a corrected oracle, is the last-mile assertion reliably satisfiable?
**Answer: 8/8** — which retired the idea of *deleting* the last-mile assertion, and measured the
answer-latency band. It did **not** clear the token *shape* (canon card **#1664** governs that), and
the settle design it validated was later rejected on `main`-provenance grounds (below).

⚠️ **The 8 runs measured the *stability-window* design, which is NOT what shipped.** That design
was rejected because its settle signal (`chat-stop-generation-button`) is not on EliteaUI `main`
(§ Why step 8 has no settle detection). The shipped auto-retrying indexed assertion **supersedes**
it and was verified **green on its first live run** (16.02 s on step 8; send→answer ~17.8 s — inside
the band below). The experiment is kept, not deleted: it is what killed the *deletion* of the
assertion, and it remains the evidence for the answer-latency band.

⚠️ **These 8 runs used the OLD token file**, so they are not evidence for the comprehension-fact
shape. That shape has its own, separate evidence: #1664's (shipped on ELITEA-2421, three gate runs)
**and this spec's own implementation, green on its first live run** — so the analyst-side gap flagged
in v3 ("not yet live-verified on this flow") is now **closed**.

The settle condition **as measured** — ~~shipped~~ **REJECTED**, retained only to explain the numbers
below (see § Why step 8 has no settle detection):

- ~~`chat-stop-generation-button` **not** visible~~ — **not on `main`; this is what disqualified it**
- ~~Copy button visible on message index `initial_count + 1`~~
- ~~both stable across >=2 consecutive polls spanning >=1.2 s~~
- read via `get_message_text_at(initial_count + 1)` — **never** `.last` — **this part SHIPPED** and
  remains load-bearing in step 8's `.nth(initial_count + 1)`

Frames pumped with `page.wait_for_timeout()`, never `time.sleep` (the sync API only dispatches
`framereceived` inside a Playwright call — `utils/websocket_frames.py`).

| run | settled | token | secs | tool-read (frame evidence) |
|---|---|---|---|---|
| 1 | yes | **yes** | 20.4 | yes |
| 2 | yes | **yes** | 19.6 | yes |
| 3 | yes | **yes** | 19.8 | yes |
| 4 | yes | **yes** | 18.5 | yes |
| 5 | yes | **yes** | 21.1 | yes |
| 6 | yes | **yes** | 20.8 | yes |
| 7 | yes | **yes** | 19.6 | yes |
| V | yes | **yes** | 18.8 | yes (frame-dump verification run) |

**8/8 settled, 8/8 token present**, settle 18.5–21.1 s (mean 19.8 s) — a tight, deterministic band.

**Tool-read evidence is a real frame, not an inference.** The tool lifecycle rides
`chat_predict_attachment` frames (this flow emits **no** `agent_tool_end` and no `agent_llm_chunk`):

```
event='chat_predict_attachment' dir='received'
response_metadata -> {"tool_name": "read_multiple_files",
                      "tool_output": {"<uuid>/test_automation_file.txt":
                        "This file contains the unique token AUTOTEST_ATTACH_7X9 and was attached by automated testing."},
                      "finish_reason": "stop", "execution_time_seconds": 0.1797}
```

The `attachments` read tool ran and returned the file's real content in **every** run — including
runs whose prose claimed the content was already "embedded". So the model's narration style varies,
but the **tool call does not**: the content reliably reaches the model.

### Honest limits of this result

1. **All 8 runs are localhost / GPT-5.4. The DEV red was never reproduced** — not by these 8, and
   not by the 3 earlier runs of the *unmodified* test (also 3/3 green). So this experiment shows the
   token is **reliably satisfiable under a correct oracle here**; it does not by itself prove the DEV
   failure was H1 rather than a DEV-specific trigger-side miss.
2. **What does point hard at H1:** the tool ran 8/8 and the DEV capture
   (*"…Let me read the file directly…."*) is the model **announcing** that tool call. That is an
   intermediate narration, which is exactly the state the broken oracle can read and the corrected
   one cannot.
3. **Residual risk if DEV differs** (different default model, slower backend). Mitigation is the
   two transport assertions (steps 6 and 9), which are model-wording-independent — plus #1664's
   comprehension shape, which removes the guardrail-refusal exposure a token echo carries.

### Superseded by #1664

v2 of this AFS recommended keeping the token echo and adding a frame assertion. **Canon card #1664
supersedes that**: the token echo goes, the frame assertion stays. See § #1664 applies here.

## #1664 applies here — and this is its second, independent occurrence

**Card:** #1664 — *"[Canon] LLM-backed oracles: comprehension facts, not token echoes (guardrails
refuse the latter intermittently)"* (OPEN, `question`, raised from ELITEA-2421 in wave-02 of #1400).

Its ruling: asking a model to **echo an opaque identifier out of an uploaded file** is an unstable
oracle *shape*. Guardrails refuse the shape, not the vocabulary — neutralising the wording
(`ZEPHYR-4417` → "Build identifier") did not help. Its failure mode: **"it works in analysis and
refuses later"**, landing as a merged flaky test whose failure looks like a product regression.

`AUTOTEST_ATTACH_7X9` is exactly that shape. **I agree with #1664 and have adopted it.**

### Why my 8/8 does NOT clear the token assertion

The 8-run experiment measured the **oracle race (H1)** and fixed it. It could not have detected
guardrail exposure: 8 runs, one model (GPT-5.4), one session, minutes apart. #1664's refusals are
*intermittent and model-dependent* — precisely what a tight local sample cannot see. A green local
hit rate is not evidence about a failure mode that manifests elsewhere, later.

### One correction to the record — it strengthens #1664 rather than weakening it

The DEV failure text was:

> *"I don't see the file content embedded in this message—only the note about it. Let me read the file directly…."*

That is **not** a guardrail refusal. #1664's refusals look like *"I can't help extract or repeat
secret codename values from attachments"*. This text is the model **announcing a tool call** — the
H1 mid-turn narration. So the DEV red on this card is H1, **not** an instance of #1664 firing.

That distinction matters, and it makes the case for adopting #1664 **stronger**, not weaker:

- If the DEV red *were* a refusal, we would have one bug to fix.
- Because it is **not**, the token assertion carries **two independent instabilities**: the oracle
  race (H1, now fixed) **and** the un-fired guardrail exposure (#1664, still latent). Fixing H1
  would have shipped a test that is green today and refuses on some future model — the exact
  "merged flaky test whose failure looks like a product regression" #1664 was written to prevent.

So this is a **second, independent spec arriving at the same unstable shape**, having never seen the
card — ELITEA-2421 (support-assistant attachments) and ELITEA-0500 (chat attachments) reached
"plant a token, ask for it back" by convergent reasoning. That convergence is the argument for the
sub-rule: it is the obvious first idea, it is not forbidden by any current rule, and two teams found
it independently. **Recommend adopting #1664's sub-rule as written.**

Cost of adopting here: one file's contents and one prompt string. The observable is unchanged.

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
   product itself knows about — but note `chat-stop-generation-button` is **not on `main`**, so a
   central fix keyed on it would break every `main`-targeted spec; prefer a
   `socket.io` turn-complete frame via `utils/websocket_frames.py`) over "Copy button + text that
   isn't on a list of six placeholders".
2. Tie the read to the settled element: `wait_for_ai_response` settles index `initial_count + 1`
   while `get_last_message_text()` reads `.last`. Either return the settled locator, or read via
   `get_message_text_at(initial_count + 1)`.
3. Require the completion signal to be **stable** (e.g. present across ≥2 consecutive polls
   spanning >1 s), which alone would have defeated the ~0.6 s flicker measured here.

Recommend a `question` card, not a silent fix inside this repair.

## Questions — one open

1. ~~Sign off R1~~ · ~~Fix the shared oracle~~ · ~~AFS directory~~ — **all closed.** The deletion was
   retired by the corrected-oracle experiment, then the oracle *shape* was settled by canon **#1664**
   (lead posted the corroboration **and** a correction retracting the guardrail-refusal misreading —
   our red is H1 narration, now on the record). Suite-wide oracle fix filed as **#1913**.
   `test-specs/chat-interface/` accepted.

2. **OPEN — back-write ELITEA-0500's two stale `automation_test_id` entries?**
   `TestContextAndSettings::test_model_settings_menu` and
   `TestConversationUIElements::test_attach_files_button_opens_picker` reference tests that do not
   exist, and both break TMS correlation **silently**. Options: (a) drop the two missing refs;
   (b) additionally re-author `test_attach_files_button_opens_picker` as new `[Automate]` work.
   **Recommend (a) now + (b) as a follow-up card** — this repair's step 2 already restores Step-1
   verification, so (b) is no longer urgent. Orchestrator-owned; analysts never write this field.

## Evidence (on disk — upload + embed per § screenshot evidence; I did not upload)

| Artifact | Path |
|---|---|
| Attach control visible near composer (ELITEA-0500 Step 1) | `<repo-root>/ELITEA-0500-step-01-attach-button-visible.png` (absolute: `/Users/Alexander_Bychinskiy/Library/CloudStorage/OneDrive-EPAM/Github/EliteaAutomationFactory/elitea-testing-public/ELITEA-0500-step-01-attach-button-visible.png`) |
| Full oracle timeline, 3 instrumented runs (per-poll copy-button state + extracted body) | `/tmp/afs-attach/ELITEA-0500-oracle-timeline.json` |
| Corrected-oracle hit-rate, 8 runs (settled/token/secs/tool-read + events) | `/tmp/afs-attach/hitrate.jsonl` |

The scratch probe used to produce the timelines was deleted after the run — it is not a deliverable
and nothing in the repo references it.
