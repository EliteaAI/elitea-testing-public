---
id: ELITEA-2421
title: Send message with attached file
status: ready-for-automation
priority: medium
type: functional
module: support-assistant
tms_case: ../onetest-ai-tm-Elitea/tests/automated-full-regression-ui/support-assistant/ELITEA-2421_send-message-with-attached-file.md
snapshot: .agents/automation/support-assistant-w02/cases/ELITEA-2421.md
analyst: qa-engineer (Sage)
analysis_date: 2026-08-22
supersedes: the 2026-08-18 `defect-found` analysis (commit 7941ba405) — refuted, see § Supersedes
known_defects: ["#1653"]
surface_key: support-assistant-widget
---

# Automation-Friendly Spec: Send message with attached file

**TMS Case:** ELITEA-2421 · **Status:** `ready-for-automation` · **Priority:** medium (l2)
**Surface:** Support Assistant widget (connected repo `../elitea_assistant`)
**Environment:** `http://localhost:5173/chat` — EliteaUI `automation/testids` + `elitea_assistant` `automation/testids` (`VITE_ASSISTANT_LOCAL=1`), live DEV backend
**Analysis date:** 2026-08-22

---

## Executive Summary

Executed all seven steps live. **Six of seven pass.** The attachment feature is fully
implemented end-to-end: the file uploads (`POST …/attachments/{uuid}` → **201**), its
filepath rides the outbound `support_predict` WebSocket frame, and the assistant
demonstrably **reads the file's content** — asked for a token that existed only inside
the attached file, it replied `ZEPHYR-4417` (73.7 s).

**One step fails: Step 6.** The sent user message carries **no attachment indicator** —
`TMessage` has no attachment field and `MessageItem.tsx` renders none, so the attachment
leaves no trace in the conversation once the composer chip clears. Isolated, deterministic,
single-cause, filed as **#1653** → automate per the sanctioned-RED analysis-time entry
(`.agents/testing.md` § Merge gate): assert the **correct** behaviour with `expect.soft()`
so it flips green when the product ships it. It does not block any other step.

---

## Supersedes — the 2026-08-18 `defect-found` analysis is refuted

The previous AFS for this case (commit `7941ba405`) concluded *"file attachment is NOT
implemented… stub UI… file NOT uploaded, NOT passed to the AI model"* and produced bug
**#1584**. **A live re-run disproves all three claims** (refutation posted on #1584):

| Prior claim | Live 2026-08-22 |
|---|---|
| "Network requests show no file upload to backend" | `POST /api/v2/support_assistant/attachments/{uuid}` → **201**. The upload fires on **Send**, not on attach — a capture armed around the attach click sees nothing. |
| "File NOT passed to the AI model" | `support_predict` frame carries `attachments:["/attachments/{uuid}/<file>.txt"]`. Sending is a **WebSocket frame, not a POST** (digest quirk 8) — "no POST" proves nothing. |
| "Response is a generic echo: `Echo: Summarize…`" | Not reproduced. Real reply, and it returned a token present **only** inside the file. |
| "Assistant response does not reference file content" | Refuted — that is exactly what Step 7 now asserts. |

Same pattern as **#1581** (the digest's quirk 21/32 — false bug from the same 2026-08-18
pass, since disproved four times). Any support-assistant finding from that pass needs a
re-run before it is acted on.

---

## Coverage Map

### Axis 1 — every case element

| # | Case element | Expected result | Covered by | Asserted where | Disposition |
|---|---|---|---|---|---|
| Pre | User logged in to Elitea | — | `auth_state` (localhost skips Keycloak via `VITE_DEV_TOKEN`) | § Preconditions | ✅ setup |
| 1 | Open the Support Assistant widget | Page/section loads | Click `sidebar-support-assistant-button`; wait for widget | `expect(widget).to_be_visible()` + copy-button settle | ✅ PASS |
| 2 | Click Attach file, select a small text file | Control responds | `expect_file_chooser` around attach-button click → `set_files()` | file chooser opened; chip appears | ✅ PASS |
| 3 | A file preview / attachment chip appears before sending | Condition holds | Attachment chip in composer | `expect(chip).to_have_count(1)` + `to_contain_text(FILENAME)` | ✅ PASS |
| 4 | Type "Summarize the content of this file" | Field accepts and displays input | Real `fill()` (never synthetic — quirk 4) | `to_have_value(MSG)`; send button `to_be_enabled()` | ✅ PASS |
| 5 | Click Send (or press Enter) | Control responds; next state shown | Click send button | upload `201` recorded; chip count → 0; user item `baseline+1` | ✅ PASS |
| 6 | The message is sent with the attachment indicator visible in the chat | Condition holds | Inspect the sent user message item | `expect.soft(last_user_item).to_contain_text(FILENAME)` | ❌ **FAIL — #1653**, soft-asserted |
| 7 | Assistant returns a response that references / processes the file content | Condition holds | Wait for reply; assert the file-only token | `expect(last_assistant_item).to_contain_text(TOKEN)` | ✅ PASS |
| Final | Assistant response references / processes file content | — | same as Step 7 | Step 7 assertion | ✅ PASS |
| P/F | "All steps complete without errors" | — | console-error side channel | `assert not console_errors` (filtered) | ✅ PASS (0 errors live) |

### Axis 2 — observables asserted beyond the case

| Observable | Why | Grounded in |
|---|---|---|
| `POST …/attachments/{conversation_uuid}` status is 2xx | Step 5's "control responds" is otherwise unfalsifiable; this is the system-produced proof the file really left the browser, and it is the exact claim the superseded AFS got wrong | `adapter.api.ts:100`; live 201 |
| Outbound `support_predict` frame contains a non-empty `attachments` array | Proves the filepath reached the model — the causal link between Step 5 and Step 7 | `chat.hook.ts:152,521-526`; live frame captured |
| Composer chip count returns to 0 after send | Distinguishes "chip cleared by design" from "chip never existed", so Step 6's soft failure can't be misread | `chat.hook.ts:424-427` `clearAttachments()` |
| Console errors (filtered per quirk 6/23) | Silent-failure side channel | standard practice; 0 live |

---

## Handles Reference

Locators are **testid-only**, as class-level `LocatorDescriptor` fields
(`.agents/testing.md` § Locator policy). Provenance verified 2026-08-22 with a fresh
`git fetch origin` in **both** repos + the two-stage grep.

| # | Element | Testid | Repo | PROVENANCE |
|---|---|---|---|---|
| 1 | Sidebar launcher | `sidebar-support-assistant-button` | EliteaUI | on `automation/testids` only (awaiting human promotion to main) |
| 2 | Widget window | `support-assistant-widget` | elitea_assistant | on `automation/testids` only |
| 3 | Message input | `support-assistant-message-input` | elitea_assistant | on `automation/testids` only |
| 4 | Send button | `support-assistant-send-button` | elitea_assistant | on `automation/testids` only |
| 5 | Message item (`data-role` filter) | `support-assistant-message-item` | elitea_assistant | on `automation/testids` only |
| 6 | Copy button (reply-complete signal) | `support-assistant-message-copy-button` | elitea_assistant | on `automation/testids` only |
| 7 | **Attach file button** | **`support-assistant-attach-button`** | elitea_assistant | ✅ added during implementation — EliteaAI/elitea_assistant@1960c8e on `automation/testids` only |
| 8 | **Attachment chip (composer)** | **`support-assistant-attachment-chip`** | elitea_assistant | ✅ added during implementation — EliteaAI/elitea_assistant@1960c8e on `automation/testids` only |

Rows 1-6 are already bound on `SupportAssistantPage` as `sidebar_launcher`, `widget`,
`message_input_field`, `send_message_button`, `message_items`, `message_copy_buttons`,
with constants `ASSISTANT_MESSAGE_ITEM` / `USER_MESSAGE_ITEM` and helpers
`open_widget_via_sidebar()`, `last_user_item()`, `last_assistant_item()`,
`get_copy_button_count()`, `user_message_item_with_text()`.

**Rows 7-8 — exact placement (pure attribute adds, zero functional impact):**

- **Row 7** — `../elitea_assistant/src/components/chat/MessageInput.tsx:266-274`, the
  `<button className="elitea-assistant-attach-button" aria-label="Attach file">`. Add
  `data-testid="support-assistant-attach-button"`.
- **Row 8** — `../elitea_assistant/src/components/chat/attachments/AttachmentChip.tsx:39`,
  the `<div className={getChipClassName(...)}>` inside `<Tooltip>`. Add
  `data-testid="support-assistant-attachment-chip"`. The chip's own text already contains
  the filename (`.elitea-assistant-file-chip-name` span), so **no separate name testid is
  needed** — assert `to_contain_text(FILENAME)` on the chip.

**Deliberately NOT requested** (canon #511 — testids only on elements the test's executed
path calls): the chip **remove** button, the `+N` overflow chip and its dropdown, the
history/expand/close controls. This case never touches them.

**No testid is requested for the Step-6 attachment indicator** — the element does not
exist (that is defect #1653). Step 6 is asserted as text containment on the already-
testid'd message item, so it needs no new handle and no speculative testid.

---

## Fidelity Declaration

**No substitutions.** Every asserted value is produced by the system: the upload status
comes from the real HTTP response, the attachments array from the real outbound WebSocket
frame, the reply text from the live model. The Step-7 oracle is the **file's own content**
(a token written by the test into the file it uploads, then read back out of the model's
answer) — the system, not the test, must carry it end-to-end. No `route.fulfill`, no
`page.evaluate`, no injected state, no seeded-via-API precondition.

Typing must be a **real** `fill()`/`type()` — synthetic `input.value = …` does not update
React state and manufactures a false "send button never enables" bug (digest quirk 4; the
origin of false bug #1581).

---

## Preconditions

- Localhost auto-authenticates via `VITE_DEV_TOKEN`; the `auth_state` fixture skips login.
- Support Assistant enabled for the project (observed `project_id: 399`, "Private").
- Dev server on `:5173` serving **both** integration branches, with `VITE_ASSISTANT_LOCAL=1`
  so the connected repo's source is aliased live.
- No New-chat step is required — the spec uses **baseline deltas** (digest quirks 2/10/24).

## Test Data

| Field | Value | Notes |
|---|---|---|
| Attachment | `test-results/ELITEA-2421-attachment.txt`, written by the test into `tmp_path` | `.txt` is in `ALLOWED_EXTENSIONS`; well under the 5 MB single-shot threshold |
| File content | **SHIPPED:** `The project mascot is the {word}.` in a short prose handbook, `{word}` chosen per run from a 10-item list. *(The originally specced `The secret project codename is ZEPHYR-4417.` is refused by the assistant — see § Amended during implementation item 4.)* | The planted word is the Step-7 oracle: it exists only inside the uploaded file, so the reply can carry it only by reading the upload |
| Message | **SHIPPED:** `According to the attached file, what is the project mascot? Answer with the single word.` | Sharper than the case's literal *"Summarize the content of this file"*, whose free-form summary has no deterministic observable. See § Declared improvisation. |

---

## Step-by-step spec

Each step in its own `with allure.step("Step N — …"):` block.

**Setup** — arm the collectors **before** navigation (quirk 8: `page.on("websocket")` only
sees sockets opened afterwards):
`page.on("response", …)` filtered to `"/attachments/"`, and `page.on("websocket")` →
`ws.on("framesent")` collecting frames containing `predict`.

1. **Open the widget** — click `sidebar_launcher`; `expect(widget).to_be_visible()`;
   settle with `expect(message_copy_buttons).not_to_have_count(0, timeout=60_000)`
   (quirk 35 — never read a baseline before the list renders). Capture
   `baseline_copy = get_copy_button_count()` and `baseline_user = user items count`.
2. **Attach** — `with page.expect_file_chooser(): attach_button.click()` →
   `set_files(path)`.
3. **Chip appears** — `expect(attachment_chips).to_have_count(1)` and
   `expect(attachment_chips.first).to_contain_text(FILENAME)`.
4. **Type** — `message_input_field.fill(MSG)`; `expect(message_input_field).to_have_value(MSG)`;
   `expect(send_message_button).to_be_enabled()`.
5. **Send** — click `send_message_button`. Then:
   - `expect(attachment_chips).to_have_count(0)` — composer cleared;
   - `expect(user_items).to_have_count(baseline_user + 1)`;
   - upload happened: the collected `/attachments/` responses are non-empty and **all**
     status `< 300` (live: one `201`);
   - the predict frame carries the file: at least one captured frame whose JSON has a
     non-empty `attachments` list containing the filename.
6. **Attachment indicator on the sent message — SOFT, known defect #1653**
   ```python
   # Known defect: #1653 — TMessage carries no attachment field and MessageItem
   # renders no indicator, so the sent message shows no trace of the file.
   # Asserting the CORRECT behaviour so this flips green when the product ships it.
   expect.soft(page_obj.last_user_item()).to_contain_text(FILENAME)
   ```
   Assert on the already-testid'd item — do **not** invent a locator for a
   non-existent element.
7. **Assistant processes the file** — wait on the copy-button delta, which is the true
   reply-complete signal (quirks 9/17):
   `expect(message_copy_buttons).to_have_count(baseline_copy + 1, timeout=200_000)`, then
   `expect(page_obj.last_assistant_item()).to_contain_text(TOKEN)`.
   The token exists **only** inside the uploaded file, so this single assertion proves
   upload → model → response end-to-end.
8. **Side channel** — assert no console errors after filtering the known dev-server noise
   (quirk 6/23: `Module "stream" has been externalized`, `@vite/client`,
   `/socket.io/?EIO=4&transport=polling` `ERR_CONNECTION_REFUSED`).

**Timing.** Reply latency measured **73.7 s** this run — inside the surface's 31-135 s
band. Use a **200 s** reply timeout (this case waits for an *upload plus* a
document-grounded answer, which sits at the slow end). Estimated spec runtime **90-120 s**.

---

## Amended during implementation (2026-08-22, test-automation-engineer)

1. **Rows 7-8 of § Handles Reference now EXIST** — added exactly where this AFS placed
   them, as pure attribute adds (EliteaAI/elitea_assistant@1960c8e, `automation/testids`
   only; a human cherry-picks to that repo's `main`). Bound as the additive class-level
   fields `SupportAssistantPage.attach_file_button` / `.attachment_chips` with the helpers
   `attach_file_via_testid()` / `get_attachment_chip_count()`.

2. **Step 5's chip-count assertion is also the flow's synchronisation point**, and the
   spec relies on that ordering rather than adding a wait. `handleSend`
   (`chat.hook.ts:483-540`) awaits `startUpload` FIRST, then pushes the user message,
   then calls `emitPredict`, and only then `clearAttachments()`. So
   `expect(attachment_chips).to_have_count(0)` is a DOM signal that both the upload
   response and the predict frame have already been observed — which is why the spec
   reads the collected `upload_statuses` / `predict_frames` immediately after it, with no
   sleep and no polling helper. (Source-confirmed this run; the AFS listed the four Step-5
   observables without ordering them.)

4. **§ Declared improvisation's "plant a unique token" oracle is REFUTED AS WRITTEN — the
   assistant refuses to relay opaque identifiers out of an attachment.** The analyst's
   single successful observation (`ZEPHYR-4417` returned) did **not** reproduce: two
   consecutive implementation runs got an explicit safety refusal instead —

   > *"I can't help extract or repeat secret codename values from attachments."*
   > *"I can't help extract or repeat secret identifiers from attachments."*

   The second refusal followed **neutral** wording (`Build identifier: <TOKEN>` /
   "reply with ONLY the build identifier"), which rules out the word *"secret"* as the
   trigger — the guardrail keys on **relaying an opaque identifier out of an
   attachment**, whatever it is called.

   **Shipped oracle instead — same strength, no guardrail collision:** plant an
   ordinary-prose fact and ask a comprehension question. The file reads
   `The project mascot is the {word}.` (word chosen per run from a 10-item list) and the
   prompt is *"According to the attached file, what is the project mascot? Answer with
   the single word."* The word still exists **only** inside the uploaded file, so the
   reply can contain it only by reading the upload — the case's observable is preserved
   and the assertion stays deterministic. Verified green twice consecutively.

   This is a **how** change inside the implementer's Phase-2 latitude (the AFS's own
   improvisation is "make the content-grounding deterministic"; only its *example
   payload* was unusable), not a change to what is verified. **It does confirm the
   assistant genuinely processes attachment content** — it answers about the file, it
   just will not echo identifiers — so #1584 stays refuted.

   **Gate risk to note:** this oracle rides a live LLM guardrail whose behaviour already
   proved non-reproducible once. If the 3x merge gate sees a refusal, that is this
   mechanism, not a regression in the attachment pipeline (Steps 1-5 are all
   product-produced and independent of it).

5. **Actual spec runtime: 55-65 s headless** across four runs (the estimate said 90-120 s).

6. **The `img` element inside the sent user message is the user AVATAR**
   (`MessageItem.tsx:35-43`, `alt="User avatar"`), not an attachment affordance. Noted
   because the Step-6 failure's aria snapshot shows it and it could be misread as a
   partial indicator on a future triage. **#1653 stands as written.**

## Cleanup

None. Consistent with every merged support-assistant spec: messages are left in the shared
conversation deliberately, which is exactly why **every** observable here is a baseline
delta and the Step-7 token is generated per-run (quirk 24 — an absolute count or a fixed
string is green on run 1 and red on runs 2..N, failing the lead's 3× merge gate).

---

## Known Defects

**#1653 — [BUG][ELITEA-2421] sent message shows no attachment indicator.** Minor.
Deterministic, single-cause, source-confirmed (`chat.types.ts:1-11` `TMessage` has no
attachment field; `chat.hook.ts:492-495` pushes `{id, role, content, timestamp}` only;
`MessageItem.tsx` renders no attachment element). Affects Step 6 alone; soft-asserted with
the correct expected behaviour. Every other step hard-asserts and passes, so this spec is
**not** sanctioned-RED overall — it is green today except for one soft failure.

**#1584 — refuted, left OPEN with a refutation comment.** Agents never close issues; a
human closes it. Do not treat it as a blocker for this case.

---

## Classification Rationale

**`ready-for-automation`.**

- Not `defect-found`: per `.agents/testing.md` § Merge gate → *Analysis-time entry
  (#557/ELITEA-1965)*, `defect-found` is correct only when the defect **blocks further
  exploration**. #1653 blocks nothing — Steps 1-5 and 7, including the case's own
  **Expected Final State**, all executed and passed. The defect is one isolable assertion
  at the tail, so the canon directs `ready-for-automation` + `expect.soft()` +
  `# Known defect: #N`, preserving coverage of six passing steps.
- Not `already-covered`: `test_support_assistant_smoke.py::TestSupportAssistantAttachments::test_attach_button_present_and_opens_picker`
  (line 423, merged) covers only Steps 1-3 — attach button visible → picker opens → file
  set. It asserts **nothing** about sending, the upload request, the predict payload, the
  sent message, or the assistant's use of the file content. Steps 4-7, the substance of
  this case, are entirely unproven.
- Not `extend-existing`: the gap (send + upload proof + predict payload + reply-content
  oracle + a soft defect assertion) is ~6 of 7 steps and a different flow shape from a
  file-chooser smoke check. Per the skill's boundary call, an extension here would be a
  near-rewrite. A new spec is correct; it reuses the same page object.

## Declared improvisation (canon-gap escalation)

**Step 4's prompt text deviates from the case's literal wording.** The case says type
*"Summarize the content of this file"*, and Step 7 asks to verify the reply *"references
or processes the file content"*. A free-form summary has **no deterministic observable** —
any assertion over it is either vacuous (non-empty text) or flaky (keyword guessing at an
LLM's phrasing).

Chosen instead: keep the *intent* (the assistant must demonstrably read the file) and make
it deterministic by planting a **unique token inside the file** and asking for it back.
This is strictly **stronger** than the case's own bar — a summary could be faked by
echoing the prompt, whereas the token can only be produced by actually reading the upload.
It follows `.agents/testing.md` § *How to test a NONDETERMINISTIC producer without
substituting it*: the real response is the oracle, and the invariant asserted is a
correlation the product must carry, not a string the test chose the model to say.

Scope check against the declaration ceiling (`.agents/role-overrides.md`): this changes
**how** the observable is made checkable, not **what** is verified — the case's observable
("the response references/processes the file content") is preserved and tightened, and no
substitution is involved. **Lead: this owes a `question` card before batch close**, either
to sanction "plant-a-token" as the canonical pattern for content-grounding assertions, or
to amend the TMS case text toward a deterministic prompt.

---

## Evidence

| File | Shows |
|---|---|
| `ELITEA-2421-step-03-attachment-chip.png` | chip in composer with filename, before send |
| `ELITEA-2421-step-06-sent-message-no-indicator.png` | sent message, text only — defect #1653 |
| `ELITEA-2421-step-07-assistant-read-file.png` | reply `ZEPHYR-4417` — the file-only token |

Attached to the `evidence` prerelease:
`https://github.com/EliteaAI/elitea-testing-public/releases/download/evidence/<name>.png`
(also on disk under `test-results/screenshots/`).

Raw observations — upload `201`, the `support_predict` frame, the sent-message HTML,
73.7 s latency, `0` console errors — are quoted inline above and in the #1584 refutation.

## Blocked Steps

None. All seven steps executed live.

## Out of Scope

Drag-and-drop attachment (own case ELITEA-2420 / bug #1583), multi-file and the `+N`
overflow chip, upload progress states, the 150 MB / 10-file limits, chunked upload above
5 MB, and image attachments. None are touched by this case.
