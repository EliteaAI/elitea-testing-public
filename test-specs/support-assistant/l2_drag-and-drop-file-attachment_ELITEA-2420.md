---
id: ELITEA-2420
title: Drag and drop file attachment
status: ready-for-automation
priority: medium
type: functional
module: support-assistant
tms_case: ../onetest-ai-tm-Elitea/tests/automated-full-regression-ui/support-assistant/ELITEA-2420_drag-and-drop-file-attachment.md
snapshot: .agents/automation/support-assistant-w02/cases/ELITEA-2420.md
analyst: qa-engineer (Sage)
analysis_date: 2026-08-22
clarifications: ["#1655"]
known_defects: ["#1653 — not asserted here, owned by ELITEA-2421's spec"]
surface_key: support-assistant-widget
---

# Automation-Friendly Spec: Drag and drop file attachment

**TMS Case:** ELITEA-2420 · **Status:** `ready-for-automation` · **Priority:** medium (l2)
**Surface:** Support Assistant widget composer (connected repo `../elitea_assistant`)
**Environment:** `http://localhost:5173/chat` — EliteaUI `automation/testids` + `elitea_assistant`
`automation/testids` (`VITE_ASSISTANT_LOCAL=1`), live DEV backend
**Analysis date:** 2026-08-22

---

## Executive Summary

**Executed all six steps live, end to end, in 70.7 s — the whole flow works.** Drag-and-drop
file attachment is fully implemented in the composer: a `dragenter` carrying `Files` renders a
`"Drop files here"` overlay and flips the input area to `--drag-over`; the `drop` stages an
attachment chip carrying the filename; typing a prompt enables Send; Send uploads the file
(`POST /api/v2/support_assistant/attachments/{uuid}` → **201**), the outbound `support_predict`
WebSocket frame carries `/attachments/{uuid}/ELITEA-2420-drag-test.txt`, and the assistant
**answered from the dropped file's content** (planted mascot word `capybara` returned verbatim).
Zero console errors.

Two case-text imprecisions surfaced — **the product is correct in both** — filed as
clarification **#1655** and asserted here in their live form:

1. **Only the composer accepts drops, not the "chat area".** `onDrop` lives on the input-area
   div (`MessageInput.tsx:192-199`); the message list is a *sibling*. Probed live: dragenter +
   drop on `.elitea-assistant-messages` → overlay 0, chips 0, no reaction whatsoever.
2. **An attachment alone does NOT enable Send — text is still required**
   (`isSendDisabled = disabled || isUploading || !attachmentsValid || !text.trim()`,
   `MessageInput.tsx:105-108`). Live: `send.is_disabled() == True` right after the drop,
   `False` after typing.

**Two testids are needed** (pure attribute adds in `MessageInput.tsx`): the drop target and the
drag-over overlay. Everything else this case touches is already testid'd from ELITEA-2419/2421.

---

## Coverage Map

### Axis 1 — every case element

| # | Case element | Expected result (case) | Covered by | Asserted where | Disposition |
|---|---|---|---|---|---|
| Pre | User is logged in to the Elitea platform | — | `auth_state` (localhost `VITE_DEV_TOKEN`) | § Preconditions | covered (setup) |
| 1 | Open the Support Assistant widget | Target page/section loads | Step 1 | `widget` visible + conversation settled | covered |
| 2 | Prepare a small test file (`drag-test.txt`, content `Drag and drop test`) | Completes without error | Step 2 | file written to `tmp_path`; content carries the per-run oracle instead of the literal case string (§ Declared improvisation) | covered (amended content) |
| 3 | Drag the file from the file system and drop it onto the widget chat area | Completes without error, expected UI state | Steps 3a/3b/3c | drag-over overlay visible + text; overlay gone after drop | covered (decomposed; "chat area" ⇒ composer — clarification #1655) |
| 4 | File accepted — preview/attachment chip appears in the input area | Condition holds | Step 4 | `attachment_chips` count 1 + `to_contain_text(FILENAME)` | covered |
| 5 | Send button becomes enabled | Condition holds | Step 5 | **disabled** with attachment-only, **enabled** after typing | covered (live contract; clarification #1655) |
| 6 | Click Send — message (with attachment) is submitted and the assistant acknowledges or processes it | Control responds; next state shown | Steps 6a/6b | chips cleared; user-item delta +1; upload `201`; `support_predict` frame carries the filepath; assistant reply contains the planted fact | covered (decomposed) |
| Final | Message with attachment submitted and processed | — | Step 6b | reply text | covered |

### Axis 2 — observables asserted beyond the case

| Observable | Assertion | Why (grounded) |
|---|---|---|
| Drag-over affordance | overlay visible, text `"Drop files here"` while dragging; absent after drop | The only DOM proof the drop zone *received* the drag; without it a drop that silently did nothing is indistinguishable from a drop that worked (`MessageInput.tsx:199`) |
| Upload HTTP status | `POST …/api/v2/support_assistant/attachments/{uuid}` → `2xx` | The file must actually leave the browser — the exact claim false bug #1584 got wrong (digest quirks 37/42) |
| Outbound `support_predict` frame | `attachments[]` contains the filename | Sending is a WebSocket frame, not a POST (digest quirks 8/38); this is the causal link between upload and reply |
| Composer cleared after send | `attachment_chips` count 0 | `clearAttachments()` runs LAST in `handleSend` — a sleep-free proof that upload + emit already happened (digest quirk 43) |
| Assistant read the dropped file | reply contains the per-run planted fact | The case's "processes it" has no other deterministic observable |
| Console errors | none (dev-server noise filtered) | Digest quirks 6/23 — silent errors are the ones that ship |

---

## Handles Reference

**Locator policy: testid-only** (`.agents/testing.md` § Locator policy). Provenance verified with a
fresh `git fetch origin` in **both** repos on 2026-08-22 (two-stage grep per
`.agents/workflow.md` § Closure record).

| # | Element | Handle (primary, testid-only) | Provenance |
|---|---|---|---|
| 1 | Sidebar launcher (click THIS, not the floating button) | `sidebar-support-assistant-button` (EliteaUI) | on-`automation/testids` only — EliteaAI/EliteaUI@37176b46 |
| 2 | Widget window | `support-assistant-widget` | on-`automation/testids` only — EliteaAI/elitea_assistant@b8a287b |
| 3 | Message input | `support-assistant-message-input` | on-`automation/testids` only — EliteaAI/elitea_assistant@b8a287b |
| 4 | Send button | `support-assistant-send-button` | on-`automation/testids` only — EliteaAI/elitea_assistant@b8a287b |
| 5 | Message item (+ `data-role="user"\|"assistant"`) | `support-assistant-message-item` | on-`automation/testids` only — @b8a287b / @216da01 |
| 6 | Assistant copy button (the reply-COMPLETE signal) | `support-assistant-message-copy-button` | on-`automation/testids` only — EliteaAI/elitea_assistant@216da01 |
| 7 | Attachment chip (composer) | `support-assistant-attachment-chip` | on-`automation/testids` only — EliteaAI/elitea_assistant@1960c8e |
| 8 | **Drop zone** — the composer input area that owns `onDragEnter/onDragOver/onDragLeave/onDrop` | **testid needed: `support-assistant-drop-zone`** — on the `div.elitea-assistant-input-area`, `MessageInput.tsx:192` | needs-adding (`no` on both `main` and `automation/testids`, verified 2026-08-22) |
| 9 | **Drop overlay** — the `"Drop files here"` affordance rendered while `isDragOver` | **testid needed: `support-assistant-drop-overlay`** — on the `div.elitea-assistant-drop-overlay`, `MessageInput.tsx:199` | needs-adding (`no` on both refs, verified 2026-08-22) |

**Testid work order (implementer):** both are **attribute-only** additions to
`../elitea_assistant/src/components/chat/MessageInput.tsx` on that repo's `automation/testids`
branch — no new DOM node, no new hook, no new state, nothing removed (the `isDragOver` state and
both elements already exist). Zero-functional-impact check passes by construction.

```jsx
// :192-199, after the change
<div
  data-testid="support-assistant-drop-zone"
  className={`elitea-assistant-input-area${isDragOver ? ' elitea-assistant-input-area--drag-over' : ''}`}
  onDragEnter={handleDragEnter} onDragLeave={handleDragLeave}
  onDragOver={handleDragOver} onDrop={handleDrop}
>
  {isDragOver && <div data-testid="support-assistant-drop-overlay" className="elitea-assistant-drop-overlay">Drop files here</div>}
```

Notes:
- **The drop-zone testid is stable identity, not state** — it sits on the always-mounted input
  area; the `--drag-over` modifier stays a class. No `data-testid={cond ? … : …}` anywhere
  (PR #581 ruling).
- **The overlay's testid is on a conditionally-MOUNTED element**, which is the accepted shape on
  this surface — exact precedent `support-assistant-history-dropdown`
  (`{showHistory && …}`, EliteaAI/elitea_assistant@7413180). Assert its **presence/absence**, and
  do **not** add a `data-drag-over` attribute: the overlay's own mount already encodes the state,
  and a second handle for one observable is testid noise (`.agents/testing.md` § scope is
  load-bearing).
- **Budget one dev-server restart** after committing these — stale Vite modules under OneDrive
  have hit 3-for-3 on this surface (digest quirks 7/18/44). Diagnose with
  `curl -s 'http://localhost:5173/@fs<abs>/src/components/chat/MessageInput.tsx' | grep -c support-assistant-drop-zone`.

---

## Fidelity Declaration

One substitution, **transit only**, and it is the *input gesture* — never an observable.

| What is substituted | Transit or terminal | Authority / real observable |
|---|---|---|
| The OS-level file drag. The test builds a `DataTransfer` in-page holding a real `File` whose bytes are the file the test just wrote to `tmp_path`, then dispatches `dragenter` / `dragleave` / `drop` at the drop zone. | **Transit** | The OS file-manager drag is not scriptable and is *not the system under test*; from `handleDrop` onward the product code path is byte-identical to a human drag. **Every asserted value is product-produced:** the overlay render, the chip and its filename, the Send disabled/enabled state, the `201` upload status, the `support_predict` frame's `attachments[]`, and the assistant's reply. |

Nothing else is substituted. **No `route.fulfill`, no injected app state, no seeding through a
different interface.** In particular the file is **not** attached through the file picker —
that is ELITEA-2421's interface and using it here would substitute the very subject of this case.
Typing uses real input events (`fill`); a synthetic `value` write does not update the React
controlled textarea and manufactures the false "Send never enables" defect #1581 (digest quirk 4/21).

Reviewer note: the provenance grep will show `.evaluate` hits (the `DataTransfer` construction).
They are disposition **2 — transit only**; the case's observables are named above. This is not a
new judgement — the identical technique is already merged and reviewed as
`ChatPage.drag_and_drop_file()` (`automation/pages/chat_page.py:2855`), whose own docstring
records the same reasoning.

---

## Preconditions

- `EliteaUI` dev server on `http://localhost:5173`, branch `automation/testids`, with
  `VITE_ASSISTANT_LOCAL=1` aliasing `../elitea_assistant/src` (start via `start-ui-localhost`).
- Both testids of § Handles Reference rows 8-9 committed + pushed to
  `EliteaAI/elitea_assistant` `automation/testids`, and the dev server restarted (quirk 44).
- `auth_state` — on localhost login is skipped via `VITE_DEV_TOKEN`; no Keycloak step.
- The test user's Support Assistant conversation is **not** cleaned up by any spec on this
  surface, so **every** count and text observable is a DELTA against a baseline captured after
  the widget opens (digest quirks 2/10/24). Never assert an absolute.

## Test Data

| Field | Value |
|---|---|
| Attachment filename | `ELITEA-2420-drag-test.txt` (case-id-prefixed so it can't collide with ELITEA-2421's file in the shared conversation) |
| Attachment content | `Project handbook — team facts\n\nThe project mascot is the {word}.\nThe team meets on Tuesdays.\n` |
| `{word}` | one of `platypus, narwhal, capybara, pangolin, axolotl, wombat, lemur, ibex, puffin, okapi` — chosen **per run** |
| Prompt | `According to the attached file, what is the project mascot? Answer with the single word.` |
| File location | pytest `tmp_path` (the test writes it; nothing is committed) |

Why not the case's literal `"Drag and drop test"` content: see § Declared improvisation.

---

## Step-by-step spec

Every step wrapped in `with allure.step("Step N — …")`.

**Setup (before navigation).** Arm three collectors on `page` — they must exist before the first
navigation: `page.on("websocket")` only fires for sockets opened after it is attached (quirk 8),
and the upload is an **XHR** that `page.on("response")` sees but a `fetch`-scoped expectation
would not (quirk 37).

- console errors, filtered to `msg.type == "error"` **minus** the two dev-server noise patterns
  (`@vite/client`, `/socket.io/` with `ERR_CONNECTION_REFUSED` — quirks 6/23);
- upload responses, filtered on the fragment **`/api/v2/support_assistant/attachments/`**
  — ⚠️ **not** the bare `/attachments/`: the Vite dev server serves
  `…/src/components/chat/attachments/AttachmentChip.tsx` etc. and those `200`s match the short
  fragment, so a collector keyed on it can be non-empty with **zero real uploads** (observed live
  this run — see § Evidence, and the finding against ELITEA-2421's spec in § Known Defects);
- outbound WS frames containing `support_predict`.

| Step | Action | Assertion (all auto-retrying; no sleeps) |
|---|---|---|
| 1 | `ChatPage.navigate_to_chat()`; `SupportAssistantPage.open_widget_via_sidebar()` | `widget` visible. Then settle the restored conversation: `expect(message_copy_buttons).not_to_have_count(0, timeout=60_000)` (quirk 35) and capture `baseline_copies`, `baseline_user_items` |
| 2 | Write the attachment to `tmp_path` with a per-run `{word}` | — (file exists; nothing in the UI yet) |
| 3a | Deliver `dragenter` carrying the file to the **drop zone** | `expect(drop_overlay).to_be_visible()` and `to_have_text("Drop files here")` |
| 3b | Deliver `dragleave` to the drop zone | `expect(drop_overlay).to_have_count(0)` — proves the affordance is driven by the drag, not a permanent element |
| 3c | Deliver `dragenter` again, then `drop` | `expect(drop_overlay).to_have_count(0)` (overlay dismissed by the drop) |
| 4 | — | `expect(attachment_chips).to_have_count(1)`; `expect(attachment_chips.first).to_contain_text("ELITEA-2420-drag-test.txt")` |
| 5 | — (composer still empty), then `set_message_text(PROMPT)` | **First** `expect(send_message_button).to_be_disabled()` — attachment alone does not enable Send (clarification #1655). **Then** `expect(message_input_field).to_have_value(PROMPT)` and `expect(send_message_button).to_be_enabled()` |
| 6a | Click Send | `expect(attachment_chips).to_have_count(0, timeout=REPLY_TIMEOUT)` — the sleep-free proof that the awaited upload **and** `emitPredict` already ran (quirk 43). Then, read immediately after it: `assert upload_statuses` non-empty and all `< 300` (observed `201`); `assert any("ELITEA-2420-drag-test.txt" in p for p in predict_attachment_paths)`. Also `expect(user_message_items()).to_have_count(baseline_user_items + 1)` |
| 6b | Wait for the reply | `expect(message_copy_buttons).to_have_count(baseline_copies + 1, timeout=200_000)` (the copy button renders only on a COMPLETE assistant message — quirks 9/17); `expect(last_assistant_item()).to_contain_text(word, ignore_case=True)` |
| 7 | — | `assert console_errors == []` |

**Page-object work (`automation/pages/support_assistant_page.py`, additive):**

- `drop_zone = LocatorDescriptor(testid="support-assistant-drop-zone", …)`
- `drop_overlay = LocatorDescriptor(testid="support-assistant-drop-overlay", …)`
- **Mirror the merged precedent** `ChatPage.drag_and_drop_file()`
  (`automation/pages/chat_page.py:2855-2910`) — same technique, already reviewed and shipped on
  the main chat composer: read the file's real bytes, base64 them into the page, rebuild a real
  `File` from a `Uint8Array`, wrap it in a `DataTransfer`, and dispatch the `DragEvent`s at the
  testid'd drop zone via `self.drop_zone.evaluate(...)`. Its docstring is the model for yours.
- **One difference from that precedent: expose composable phases, not one monolithic call** —
  `drag_file_over_composer(path)` / `drag_leave_composer()` / `drop_file_on_composer(path)` —
  because Step 3b asserts the overlay *reverts* mid-gesture (the artifacts drag primitives at
  `chat_page.py:8230-8251` set the precedent for splitting a gesture for exactly this reason).
  Each phase may build its own `DataTransfer`: `handleDragEnter` reads only
  `e.dataTransfer.types.includes('Files')`, `handleDragLeave` reads nothing (it just decrements
  `dragCounterRef`), and `handleDrop` reads `.files`. Events **must** be constructed with
  `{bubbles: true, cancelable: true, dataTransfer}` — React listens at the root container.
  Verified live this run in exactly this shape.
- Reuse as-is: `open_widget_via_sidebar`, `set_message_text`, `get_copy_button_count`,
  `get_user_message_item_count`, `user_message_items`, `last_assistant_item`,
  `message_copy_buttons`, `attachment_chips`, `send_message_button`, `message_input_field`.

**Where the spec goes:** a **new** file
`automation/tests/ui/support_assistant/test_support_assistant_drag_drop_attachment.py`, class
`TestSupportAssistantDragDropAttachment`. Deliberately **not** appended to
`test_support_assistant_attachment_send.py`: that spec is **sanctioned-RED by design** (#1653), and
mixing a green case into the same file muddies every gate run's signal. Lift its module-level
constants (`MASCOT_WORDS`, timeouts, the noise filter, `_predict_attachment_paths`) — duplicating
~30 lines across two files is cheaper than coupling a green spec to a red one; if the implementer
prefers, promote them to a small shared module under `tests/ui/support_assistant/` and say so in
the Run Report.

**Markers:** `p2`, `ui`, `support_assistant`, `regression` (not `smoke` — a live reply puts the
runtime near 70 s).

**Estimated runtime:** 60-90 s headless (analysis run: **70.7 s**, of which ~37 s was the reply).

---

## Cleanup

None. Consistent with every other spec on this surface, the conversation is left as-is (there is
no delete-conversation affordance in the widget). This is exactly why every observable in
§ Step-by-step spec is a delta and why the filename is case-id-prefixed and the mascot word is
per-run.

---

## Known Defects

- **#1653 — the sent user message carries no attachment indicator.** Reproduces here identically
  (live: the user bubble read only the prompt text). **Deliberately NOT asserted in this spec** —
  ELITEA-2421's `test_send_message_with_attached_file` already owns it as a linked
  `expect.soft()` red. Duplicating it would add a second permanent red for one defect with zero
  new information, and this case's "the attachment was submitted" claim is proved *more strongly*
  by the `201` upload, the `support_predict` frame carrying the filepath, and the assistant
  answering from the file's content. Recorded here so nobody re-files it.
- **#1655 (clarification, `question`)** — the two case-text imprecisions of § Executive Summary.
  Product is correct; the spec asserts the live contract.
- **Finding against a merged spec (not a product defect):**
  `test_support_assistant_attachment_send.py:196-202` (ELITEA-2421) filters its upload collector on
  the fragment `"/attachments/"`, which **also matches the Vite dev server's own module URLs**
  (`…/src/components/chat/attachments/AttachmentChip.tsx?t=…` → `200`). Observed verbatim in this
  run's capture. Its `assert upload_statuses` can therefore be satisfied with **no real upload**,
  and `all(status < 300)` passes on those `200`s — a vacuity risk, not a current failure (the real
  `201` was also present). Reported to the lead; this spec uses the full
  `/api/v2/support_assistant/attachments/` fragment.

---

## Classification Rationale

`ready-for-automation`.

**Why not `already-covered`.** The nearest merged-on-trunk spec,
`automation/tests/ui/support_assistant/test_support_assistant_attachment_send.py:222`
(ELITEA-2421), attaches through **the file picker** (`attach_file_via_testid` →
`expect_file_chooser`). It never dispatches a drag event, never touches the drop zone, and cannot
fail if `handleDrop` / `handleDragEnter` regress or if the drop overlay disappears. Same *screen*
and same *post-send* flow is not coverage of a different *entry point*.

**Why not `extend-existing`.** The gap is not a couple of trailing assertions — it is the entire
input half of the test (a new gesture, a new drop-target handle, a new overlay observable, and a
`to_be_disabled()` assertion the covering spec never makes). Appending it would be a near-rewrite
of the covering test body, which § Classify findings routes to `ready-for-automation`. The
post-send half is reused as *code* (constants + helpers), which is the right kind of reuse here.

**Why not `defect-found`.** Both divergences from the case text are case-text drift with the
product behaving per its own contract — the reverse-masking guard makes them clarifications
(#1655), and asserting the stale case text would be reverse-masking. #1653 reproduces but is
isolated, already filed, already owned by another spec, and blocks nothing.

**Why not `un-automatable`.** The drop gesture is deliverable with a real `DataTransfer` and the
full flow ran green live in one pass.

---

## Declared improvisation (canon-gap escalation)

**The case's Step 2 specifies the file content `"Drag and drop test"`. This spec plants a
per-run prose fact instead.** No canon shapes "what content does an attachment fixture carry when
the case asks the assistant to *process* the file", so, per `.agents/role-overrides.md`
§ Declared-improvisation protocol:

- **Chosen:** `The project mascot is the {word}.` with a per-run `{word}`, and a comprehension
  prompt asking for it back.
- **Why:** the case's Step 6 asks that the assistant *"acknowledges or processes"* the file. The
  literal content has **no assertable observable** — any assertion over a free-form reply to
  `"Drag and drop test"` is vacuous or flaky. A per-run fact that exists **only** inside the
  uploaded file makes the reply a genuine end-to-end oracle (upload → model → response) and is
  strictly stronger than the case's own bar. It also survives runs 2..N of a conversation that is
  never cleaned up (a fixed token would be satisfiable by a previous run's answer — quirk 24).
- **Ceiling check:** this changes *fixture data*, not *what is verified* — no substitution, no
  weakened or dropped observable, same subject.
- **Precedent, not a first encounter:** ELITEA-2421's merged spec already ships exactly this
  shape (its own AFS § Declared improvisation), including the guardrail-safe *prose fact* wording
  — the assistant **refuses** to relay opaque identifiers out of an attachment (digest quirk 48).
  This spec follows that established pattern rather than re-declaring a new one; the canon card
  for the pattern is the lead's open loop from ELITEA-2421, not a second one from this case.
- **Gate caution (inherited):** the Step-6b reply assertion rides a live LLM. A refusal on a gate
  run is the quirk-48 guardrail mechanism, not an attachment-pipeline regression — the upload
  status, the predict frame and the chip lifecycle are all independent of it and would still pass.

---

## Evidence

Live analysis run, 2026-08-22, headless, 70.7 s, exit **passed**:

```
[BASE] copies=7 users=7
[PROBE-A dragenter on messages] ok types=["Files"] files=1 overlay=0 chips=0
[PROBE-A drop on messages]                          overlay=0 chips=0
[STEP3 dragenter] overlay visible, text='Drop files here'
                  class='elitea-assistant-input-area elitea-assistant-input-area--drag-over'
[STEP3 dragleave] overlay=0 class='elitea-assistant-input-area'
[STEP4] chips=1 text='ELITEA-2420-drag-test.txt' testid-chips=1 overlay_after_drop=0
[STEP5 no-text]   send_disabled=True
[STEP5 with-text] send_disabled=False
[STEP6] chips cleared. uploads=[(200,'…/chat/attachments/index.tsx?t=…'),
        (200,'…/chat/attachments/AttachmentChip.tsx?t=…'),
        (200,'…/chat/attachments/AttachmentProgress.tsx'),
        (200,'…/chat/attachments/AttachmentIcon.tsx'),
        (201,'http://localhost:5173/api/v2/support_assistant/attachments/60eb02bc-…')]
[STEP6] predict attachments=['/attachments/60eb02bc-…/ELITEA-2420-drag-test.txt'] users=8 (base 7)
[STEP6] last user item text='6:36 AM\nAccording to the attached file, what is the project mascot? …'
[STEP6] token=capybara in_reply=True reply='6:37 AM\n\ncapybara'
[CONSOLE] []
```

(The four `200`s above are the Vite dev server's own module URLs — the vacuity trap called out in
§ Known Defects.)

Screenshots: `test-results/screenshots/ELITEA-2420-step-03-dragover.png`,
`…-step-04-chip.png`, `…-step-06-sent.png`.

Source read: `../elitea_assistant/src/components/chat/MessageInput.tsx:44-50, 105-108, 146-170,
192-199`; `src/theme/styles/input.css:13-28`.

---

## Blocked Steps

None.

---

## Out of Scope

- Multi-file drop, the `+N` overflow chip, and the 10-attachment cap (`MAX_ATTACHMENT_COUNT`) —
  separate cases.
- Rejected extensions / >150 MB client-side rejection and the >5 MB chunked-upload path.
- Removing a staged chip (`aria-label="Remove <filename>"`) — no case touches it yet.
- Paste-to-attach (`handlePaste`, `MessageInput.tsx:171-190`) — a distinct gesture, uncased.
- Dropping onto the message list: probed and confirmed inert (clarification #1655). Not asserted —
  the browser's default file-open behaviour on a real drag is outside the app's control, so a
  synthetic-event absence assertion would prove less than it appears to.
