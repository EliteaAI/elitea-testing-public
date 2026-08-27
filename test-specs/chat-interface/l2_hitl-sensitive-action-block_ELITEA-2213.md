# Test Case: Chat – HITL Authorization – Click Block Prevents the Toolkit Tool from Executing

## Metadata
- **TMS ID**: ELITEA-2213
- **Linked Story**: none
- **Priority**: l2
- **Environment Explored**: local for the toolkit-call/chip mechanics;
  source-verified (`ChatHitlActions.jsx`) for the Block button itself. See
  ELITEA-2211 § Preconditions for the shared environment-limitation note
  (not repeated here).
- **User set**: `${TEST_USER}`
- **Analyst**: qa-engineer (cluster run, ELITEA-2211..2215, 2026-08-03)
- **Status**: extend-existing (REWORKED 2026-08-27 — see § REWORK at the end of
  this file; the merged spec needs a corrected + reordered assertion set and is
  sanctioned-RED on OPEN #1834 / #1835). The original 2026-08-03 pass below is
  kept verbatim as the historical record; where it disagrees with § REWORK,
  **§ REWORK wins** — notably its step 5, which asserted an absence the product
  never produces.

## Preconditions
Same as ELITEA-2212 — own fresh authorization-card instance (own
conversation), do not share resume state across 2212/2213/2214.

## Test Data
Same fixture shape as ELITEA-2211/2212.

## Test Steps
1. Reach the authorization card (own fresh conversation): toolkit added as
   participant, unambiguous delete-file message sent, `sensitive-action-panel`
   visible with Authorize/Block/Block-with-Comment.
2. Click Block (source: `ChatHitlActions.jsx:175-183`, `variant="alarm"` =
   red, **no testid today** — see § Concrete Handles).
   - **Verify**: `handleReject` fires — `onHitlResume({action: 'reject', toolCallId, interruptId})`
     (`ChatHitlActions.jsx:107-109`); the card unmounts once `hitlInterrupt`
     clears.
3. Verify the toolkit tool does NOT execute.
   - **Verify**: the fixture bucket's designated file is STILL present
     (`ArtifactAPI.list_bucket_files`) — backend-verified non-execution, the
     Block-side mirror of ELITEA-2212's execution-proof assertion. A
     UI-only "card closed" signal cannot distinguish Block from a silent
     failure; the file's continued presence is the actual proof.
4. Verify the LLM response indicates the action was blocked.
   - **Verify**: the assistant's follow-up message text is non-empty and
     acknowledges the block (case's own wording: "response indicates action
     was blocked") — **format not verified live** (precondition unreachable
     locally); assert a loose, resilient signal (e.g. response text is
     non-empty and does not claim success) rather than a hardcoded phrase,
     since the exact LLM wording is non-deterministic. Implementer should
     tighten this once run against CI with real observed text.
5. Verify NO tool-execution chip renders for the blocked tool.
   - **Verify**: no toolkit/tool chip (see ELITEA-2212's Concrete Handles —
     the new `chat-answer-tool-chip` testid) appears for `delete_file` in
     this turn's accordion — an ABSENCE assertion
     (`expect(locator).to_have_count(0)`), which per canon ruling #511 IS a
     first-class "reference" to the testid, satisfying the requirement that
     a newly-added testid be exercised on some case's executed path.

## Expected Results
- Block closes the card without executing the tool.
- File remains present in the bucket (backend-verified).
- LLM response acknowledges the block.
- No tool-execution chip for the blocked call.

## Coverage Map

| Case element | Expected result | Covered by (AFS step) | Asserted where | Disposition |
|---|---|---|---|---|
| 1 Buttons visible | visible | step 1 | step 1 setup, this case's OWN test body (see fix round 1 note below) | asserted *(fix round 1, 2026-08-03: originally cited ELITEA-2211 — a same-batch, not-yet-merged spec — as the reuse site for this row; the reviewer contract requires "already-covered"/reuse citations to target a spec merged to base, which ELITEA-2211 is not. This case's own test now independently asserts all three buttons visible before clicking Block, so the row no longer depends on that citation)* |
| 2 Click Block | card closes/updates | step 2 | step 2 | asserted |
| 3 Tool does NOT execute | no execution | step 3 | step 3 (backend file-listing, file still present) | asserted |
| 4 LLM response indicates block | response mentions block | step 4 | step 4 (loose non-empty/non-success signal, see step 4 note) | asserted *(clarification: exact wording not verifiable locally, see note)* |
| 5 No execution chips for blocked tool | no chips shown | step 5 | step 5 (absence assertion on the new tool-chip testid) | asserted |

**Axis 2 — Analyst additions:**
- Backend file-presence check as the ground truth for non-execution —
  *added: a UI-only "no chip" signal could also occur if the tool executed
  but the chip simply failed to render (a rendering bug would then read as
  a false negative for the product); checking the actual file is the only
  way to prove Block genuinely stopped the delete.*

## Cleanup
Same as ELITEA-2211/2212 (remove sensitivity flag once per test-file, delete
toolkit/bucket). Additionally: since the file is expected to SURVIVE this
case, explicit fixture teardown must still delete it (via bucket deletion)
rather than relying on the (already Block-confirmed) tool call.

## Concrete Handles (discovered during exploration)

| Element | Recommended Locator | Fallback |
|---|---|---|
| Block button | **testid needed**: `sensitive-action-block-button` — add via `add-data-testid` to `ChatHitlActions.jsx`'s sensitive-tool "Block" `BaseBtn` (line ~175, currently zero testid) | none |
| Bucket file-listing (non-execution proof) | `ArtifactAPI.list_bucket_files(bucket_name)` | none |
| Toolkit/tool chip (absence check) | same new testid as ELITEA-2212 (`chat-answer-tool-chip`, once added) scoped to THIS turn's accordion, `to_have_count(0)` | none |

## Network Behavior
Resume action `onHitlResume({action: 'reject', ...})` — actual frame shape
not captured live (see ELITEA-2211's Network Behavior note).

## Known Defects Found During Exploration
None found.

## Blocked Steps
None beyond the shared precondition constraint (see ELITEA-2211).

## Automation Hints
- Same markers as ELITEA-2211/2212.
- Own fresh conversation per case (isolation, see ELITEA-2212's note).

---

# REWORK — 2026-08-27 (live re-analysis, analyst slot)

**Status after this pass: `extend-existing`** — this case's spec is already merged
(`automation/tests/ui/chat/test_hitl_sensitive_action_authorization.py::TestSensitiveActionBlock::test_block_prevents_toolkit_tool_from_executing`,
on `automation/base`). The gap is a corrected + reordered assertion set, not a new
spec. Sanctioned-RED on the OPEN defects **#1834** and **#1835**
(`.agents/testing.md` § Merge gate — sanctioned-RED, analysis-time entry): every
corrected assertion states the CORRECT behaviour and flips green unchanged when the
product is fixed.

## Why this pass happened

The merged test failed on 2026-08-27 — but **not on any of its own assertions and not
at the trigger**. It reached the card, saw all three buttons, clicked Block and saw the
card close (count 0), then died at:

```
tests/ui/chat/test_hitl_sensitive_action_authorization.py:562
    chat.wait_for_message_content_stable(stable_duration_ms=3000, timeout=CHAT_RESPONSE_TIMEOUT)
pages/chat_page.py:2500
E   TimeoutError: Timed out waiting for non-transient message content. Last message: ''
```

Because that wait sits **before** the case's primary observable, the run never verified
the one thing ELITEA-2213 exists to verify. A run that never reaches the case's
observable is worse than a red one — hence this pass.

## What was executed live

Two independent runs against `http://localhost:5173` (EliteaUI on `automation/testids`),
2026-08-27, driven through Playwright MCP. Precondition set through the **same** REST
guardrails write the `sensitive_delete_file_toolkit` fixture uses (§ Fidelity
Declaration below); `sensitive_tools` captured as `{}`, restored to `{}` and
**verified by readback** at the end (`#1838` discipline).

| | Run 1 | Run 2 (pristine, single Block click) |
|---|---|---|
| Conversation | 9682 (fresh) | 9683 (fresh) |
| Toolkit / bucket | artifact toolkit 3430 → `autotest-2213-live-790717` | same |
| Seeded file | `autotest-hitl-2213-790717.txt` | same (survived run 1) |
| Observation window after Block | 230 s | 90 s live + page reload + a control message |

Nothing was mocked, injected or intercepted; every observable below was produced by
the real LLM → real tool call → real backend interrupt → real WebSocket frame.

## What this pass established (ground truth)

### Timeline — run 2, single Block click, sampled every 2 s

| t (after Block) | `sensitive-action-panel` | `chat-answer-tool-chip` | `chat-answer-model-chip` | last answer body |
|---|---|---|---|---|
| 0 s (card pending) | 1 | **1** — `autotest-art-2213-790717: delete_file` | 1 | 429 chars (the card's own text) |
| **+4 s** | **0** — the card closes correctly | 1 | 1 | 93 chars → **body EMPTY** (header + chips only) |
| **+6 s** | **1 — the card REAPPEARS, buttons live and `disabled === false`** | 1 | 1 | 429 |
| +24 s … +90 s | 1 (persists) | 1 | 1 | 419-420 |
| after page reload | **0** | **0** | — | assistant message persisted as `"Thought for 3 secs"` with **no body at all** |

Run 1 showed the same shape over a longer window: card closed, **no assistant response
for 230 s**, answer body empty, file present throughout. Run 1's apparent "the first
Block click did nothing" was an observation artifact — the reappearance at ~2 s beat the
first sample, so `panel == 1` was read as "the click was lost". It was not: the second
click merely resolved the *reappeared* card.

### Side channels (both runs)

- **Console: 0 errors.** Only the already-known `unknown message type parallel_hitl_ready`
  **warning** (`# Known defect: #1831`), which is a warning and is not captured by the
  suite's error-only collector.
- **Network: no failed request, no 4xx/5xx, no error frame.** The turn dies *silently*.
- A `beforeunload` guard stays armed on the blocked conversation (navigating away raises
  the browser's unsaved-changes dialog) — the app still believes a generation is in flight.

### Backend ground truth

`ArtifactAPI.list_bucket_files` polled continuously: the seeded file was **present at
every single sample** — run 1 through 197 s, run 2 through 93 s. **Block does prevent the
delete.**

### Control — the conversation is left poisoned

After the blocked turn in run 2 I sent a plainly unrelated message
(`"Reply with exactly the word CONTROL and nothing else."`). The assistant did **not**
answer it: it returned a **fresh `autotest-art-2213-790717.delete_file` Sensitive Action
Authorization card**. The block decision is never committed as a tool outcome, so the
next user turn replays the same pending tool call.

## Q1 — does the Block resolve path drop the turn, like Authorize does?

**Yes. Same root-cause family as #1834 / #1835 — comment on those, do NOT file a third
issue.**

| Symptom | Authorize (#1834/#1835) | Block (this pass) |
|---|---|---|
| Card closes on click | yes | yes (~0.1-4 s) |
| Turn completes / response arrives | **no** — dies silently | **no** — dies silently, answer body empty, 230 s observed |
| Error / failed request / console error | none | none |
| Resolved card re-renders with live buttons | yes, ~90 s | **yes, ~2-6 s**, and it persists until reload |
| Backend effect | file NOT deleted (wrong for Authorize) | file NOT deleted (right for Block — but see below) |

The only reason Block looks less broken than Authorize is that its *intended* outcome
(the tool does not run) is indistinguishable from the failure mode (the turn dies before
anything runs). The response step is what separates them, and that step is red.

**Two additions to report on the existing issues** (exact comment bodies are in the
analyst's return to the lead, not duplicated here):

1. **#1834** — the Block path drops the turn too, and worse: the decision is never
   committed, so the **next** user message re-triggers the identical card instead of
   being answered (control above).
2. **#1835** — the reappearance also happens on Block, at ~2-6 s instead of ~90 s, with
   `disabled === false` buttons. Clicking Block on the phantom card is *accepted* and is
   what finally clears it (run 1) — so a user can issue a second decision, including
   **Authorize**, on an action they already blocked. The phantom is client-side only: a
   page reload shows `sensitive-action-panel` count 0, i.e. the backend does not still
   hold the interrupt pending.

## Q2 — the tool-chip assertion is WRONG (CLARIFICATION, not a defect)

`chat-answer-tool-chip` is a **tool-CALL-ATTEMPT** chip, not an execution chip.

- **(a) While the card is still pending, before Block is clicked:** count = **1**,
  text `autotest-art-2213-790717: delete_file`. Confirmed independently in both runs.
- **(b) After Block:** count = **1** — unchanged. It never disappears during the live turn.
- After a page reload it is 0, because the chip is a live-stream render, not persisted.

Source, `EliteaUI/src/components/Chat/ActionView.jsx:407`:

```jsx
data-testid={toolkitType === 'model' ? 'chat-answer-model-chip' : 'chat-answer-tool-chip'}
```

— on the toolkit badge in the Thought accordion's chip row, rendered from the tool-call
action itself with **no execution predicate**.

⇒ The merged test's final assertion `expect(chat.answer_tool_chip).to_have_count(0)`
asserts a state the product **never enters**. Per the reverse-masking guard this is
**case-text drift, not a product defect**: the case asks for a "tool execution chip"
distinct from a "tool call chip", and this product renders exactly one chip per tool
call, at attempt time. Non-execution is answered by the backend file listing — which is
already this case's own step 3.

**Canon ruling #277 is NOT harmed by dropping the absence assertion.** Shape (b) requires
both branches of the ternary to be referenced on a test's executed path; both already are,
**positively**, on ELITEA-2212's path — `chat-answer-model-chip` (its Step 7) and
`chat-answer-tool-chip` (its Step 8, presence + text). The ELITEA-2213 absence assertion
was never the thing satisfying #277, so removing it leaves the pair compliant. The
module docstring's line *"ELITEA-2213 asserts absence — canon ruling #277 shape (b)"* is
now stale and must be corrected in the same change.

## Q3 — the file-presence assertion is correct but unreachable

- **Correct:** yes, verified — the seeded file was present at every poll, in both runs.
- **Reachable:** **no.** It sits *after* `wait_for_message_content_stable(...)`, which
  times out at 60 s because the answer body never becomes non-empty. The case's primary
  observable is therefore never evaluated.
- **Move it BEFORE the response wait:** **yes** — immediately after the card closes.

**Honesty caveat that must survive into the test docstring:** *file still present* is
**not** proof that Block worked. A dropped turn leaves exactly the same listing. It is
the case's own step-3 observable and must be asserted, but the assertion that actually
distinguishes "blocked" from "died" is the response step (Step E), and that one is red.
A second, later file-presence check is therefore added to catch a *late* execution after
the response window — cheap, and it is what makes the "did not execute" claim time-bounded
rather than instantaneous.

## Corrected assertion set — exact shapes, in order

Setup is unchanged: `_reach_sensitive_action_card(page, conversation_id, artifact_toolkit, artifact_seeded_file)`.

| # | Step | Assertion | Kind | Verified |
|---|---|---|---|---|
| A | Three action buttons visible on this case's own card | `expect(authorize/block/block_with_comment).to_be_visible(timeout=UI_ELEMENT_TIMEOUT)` | **hard** | GREEN — 2/2 runs |
| B | Click Block; the card closes | `chat.sensitive_action_block_button.first.click()` then `expect(chat.sensitive_action_panel).to_have_count(0, timeout=UI_ELEMENT_TIMEOUT)` | **hard** | GREEN — closes at ~0.1-4 s, 2/2 runs |
| C | **PRIMARY OBSERVABLE, moved to here** — the tool did not execute | `assert artifact_seeded_file in artifact_api.list_bucket_files(bucket_name)` | **hard** | GREEN — 2/2 runs |
| D | The resolved card stays gone | `expect.soft(chat.sensitive_action_panel, "Known defect #1835: …").to_have_count(0, timeout=PANEL_STAYS_GONE_TIMEOUT)` + `# Known defect: #1835` | **soft** | **RED** — reappears at ~2-6 s, 2/2 runs |
| E | The LLM response acknowledges the block | wrap `chat.wait_for_message_content_stable(...)` in `try/except TimeoutError` → on timeout append to `soft_failures`; **only if** text arrived, run the existing loose checks (`last_text.strip()` non-empty; `not any(p in lowered for p in _SUCCESS_CLAIM_PHRASES)`) + `# Known defect: #1834` | **soft** (`soft_failures`, drained by `pytest.fail` from a `finally`) | **RED** — no response in 230 s / 90 s |
| F | The blocked call left no *execution* evidence — corrected from the absence assertion | `expect(chat.answer_tool_chip.first).to_be_visible(timeout=UI_ELEMENT_TIMEOUT)` and `expect(chat.answer_tool_chip.first).to_contain_text(f"{toolkit_name}: {SENSITIVE_TOOL_NAME}")`, with a docstring line stating the chip is the CALL-ATTEMPT chip and carries no execution meaning | **hard** | GREEN — count 1, 2/2 runs |
| G | Late-execution guard — the file is *still* present after the response window | `assert artifact_seeded_file in artifact_api.list_bucket_files(bucket_name)` (second read, after E) | **hard** | GREEN — present through 197 s / 93 s |
| H | Side channel — no console/JS errors across the flow | `assert not console_issues and not page_errors` via `utils.console_errors.collect_console_errors(page)` + a `pageerror` listener (this spec does not use them today; ELITEA-2211/2212 do) | **hard** | GREEN — 0 errors, 2/2 runs |

### Implementation note (implementer, 2026-08-27 — shipped truth)

Rows A-H are all implemented as specified, with **one declared deviation in
EVALUATION ORDER** (the assertion, its soft channel and its defect link are
unchanged): **row D is evaluated AFTER row E**, as the test's Step 8. Reason —
`to_have_count(0)` is satisfied the instant the count is already 0, and row C is
a single fast REST read, so at the AFS's position row D would run ~1 s after the
click, inside the 2-6 s window BEFORE the card reappears. It would therefore
pass without asserting anything, silently dropping #1835 from the closed set.
Evaluated after the 60 s response window the reappearance is settled (it
persists until reload), and the assertion fires deterministically — the same
placement `TestSensitiveActionAuthorize` Step 9 already uses.

Shipped step order: **A(4) B(5) C(6) E(7) D(8) F(9) G(10) H(11)**.

Observed signature, 3 of 4 implementer runs (93.45 s / 92.51 s / 95.76 s):
`BaseExceptionGroup` with exactly **2** sub-exceptions — the `pytest.fail` drain
for #1834 (`No assistant response arrived after Block within 60000ms … Last
message: ''`) and the `expect.soft` for #1835 (panel count 1, 14 polls over
5000 ms). Steps 6, 9, 10, 11 passed hard in every one of those runs, so the
primary observable is now genuinely reached and green. The 4th run died upstream
in the shared setup (`chat-answer-thought-accordion` never appeared — the
assistant never started a turn), the known TRIGGER flake, re-run per
`.agents/testing.md` § Unconfirmed.

Structural requirements for the implementer:

- `soft_failures: list[str]` + a `try/finally` that drains it with `pytest.fail`, exactly
  as `TestSensitiveActionAuthorize` already does — so a hard failure later can never
  discard the #1834 evidence, and every member of the closed defect set is reported on
  every run.
- `@pytest.mark.flaky(reruns=0)` on this test, matching ELITEA-2212's reasoning: the spec
  is now sanctioned-RED, so `pytest.ini`'s global `--reruns=2` can only multiply wall
  clock and add retry noise.
- Every step stays wrapped in `with allure.step("Step N — …"):`.
- The module docstring's SANCTIONED-RED block must be extended to name
  `TestSensitiveActionBlock` as a second expected-FAILED spec, with its own closed
  enumerable set (**#1834** — no response, fired 2/2; **#1835** — card reappears, fired
  2/2), and the stale *"ELITEA-2213 asserts absence — canon ruling #277 shape (b)"*
  sentence corrected per Q2.

## Fidelity Declaration

| What is substituted | Transit or terminal | Authority / real observable |
|---|---|---|
| The guardrails sensitivity precondition — `artifact`/`delete_file` marked sensitive via `PUT {api}/admin/plugin_config_values/administration/guardrails` instead of the Admin UI | **transit** | The Admin UI is a separate deployed application `localhost:5173` does not serve (no `/admin` route in `EliteaUI/src/routes.js`, issue #1140). Every observable this case asserts — the card, the buttons, the card closing, the file listing, the chips, the response — is produced end to end by the real LLM → real tool call → real backend interrupt → real WebSocket frame. Nothing is mocked, injected or intercepted. |

No terminal substitution is specified anywhere in this AFS.

## Coverage Map (rewritten to reflect reality)

**Axis 1 — the case's own elements:**

| Case element | Expected result | Covered by (rework step) | Asserted where | Disposition |
|---|---|---|---|---|
| 1 Buttons visible | visible | A | this case's own test body | **asserted** — GREEN |
| 2 Click Block | card closes/updates showing action blocked | B | this case's own test body | **asserted** — GREEN (the card closes; "showing action blocked" is element 4, which is red) |
| 3 Verify toolkit tool does NOT execute | no execution | **C** (moved before the response wait) + **G** (late-execution guard) | backend `list_bucket_files` × 2 | **asserted** — GREEN. *Previously UNREACHABLE: it sat behind a wait that times out.* |
| 4 Verify LLM response indicates action was blocked | response mentions block | E | soft-routed via `soft_failures` → `pytest.fail` | **blocked-on-#1834** — the product emits **no response at all**; asserted as the correct behaviour, sanctioned-RED |
| 5 Verify no tool execution chips for the blocked tool | no chips shown | F | this case's own test body, as a **presence + text** assertion | **CLARIFICATION** — the product renders exactly one chip per tool call, at ATTEMPT time (`ActionView.jsx:407`), and never a separate execution chip. The case asks for a distinction that does not exist; asserting absence would assert a state the product never enters. Non-execution is proven by element 3. |

**Axis 2 — analyst additions beyond the case:**

- **D — the resolved card stays gone.** *Added: without it the #1835-shaped reappearance
  (~2-6 s on the Block path, with live buttons) is completely invisible to this case, even
  though it lets a user re-decide — including Authorize — an action they already blocked.
  ELITEA-2212 already carries the mirror of this assertion.*
- **G — the second, later file-presence read.** *Added: element 3 alone proves only that
  the delete had not happened at that instant. Since the turn dies rather than completing,
  a late execution is exactly the failure this case would otherwise miss; re-reading after
  the response window makes the "does not execute" claim time-bounded.*
- **H — the console/JS side channel.** *Added: this spec is the only one of the four that
  does not collect console errors today. Both runs were clean, which is itself the finding
  that makes "the turn dies SILENTLY" a verified statement rather than an impression —
  no error, no failed request, nothing.*

## Concrete Handles (verified live this pass, 2026-08-27)

| Element | Locator | Provenance | Observed |
|---|---|---|---|
| Sensitive-action card | `LocatorDescriptor(testid="sensitive-action-panel")` | on-main ✓ | count 1 pending → 0 at ~4 s → **1 again at ~6 s** |
| Block button | `LocatorDescriptor(testid="sensitive-action-block-button")` | on-main ✓ | `disabled === false` on the reappeared card too |
| Authorize / Block-with-Comment | `sensitive-action-authorize-button` / `sensitive-action-block-with-comment-button` | on-main ✓ | visible on both the original and the reappeared card |
| Tool-call chip | `LocatorDescriptor(testid="chat-answer-tool-chip")` | on-main ✓ | **count 1 before AND after Block**, text `{toolkit_name}: delete_file`; 0 after a page reload |
| Model chip | `LocatorDescriptor(testid="chat-answer-model-chip")` | on-main ✓ | count 1 throughout |
| Non-execution proof | `ArtifactAPI.list_bucket_files(bucket_name)` | n/a (API) | seeded file present at every sample, 197 s / 93 s |
| Answer body | `ChatPage.get_last_message_text()` / `wait_for_message_content_stable()` | n/a | **never becomes non-empty**; the wait raises `TimeoutError: … Last message: ''` |

No new testid is needed by this rework — every handle above already exists on
`EliteaAI/EliteaUI` `main`.

## Known Defects (this pass)

| ID | State | Symptom on the Block path | Fired |
|---|---|---|---|
| **#1834** | OPEN | The Block resume drops the turn: no assistant response ever arrives, the answer body stays empty, and the decision is never committed — the next user message re-triggers the same card | 2/2 runs |
| **#1835** | OPEN | The resolved card re-renders ~2-6 s later with live, enabled buttons, and persists until a page reload | 2/2 runs |
| #1831 | OPEN | `unknown message type parallel_hitl_ready` console **warning** during the flow — a warning, not an error; the error-only collector must not be widened to swallow it | both runs |

No third issue is filed: both symptoms are the Block-path manifestation of the same
dropped-resume root cause already tracked by #1834/#1835.

## Blocked Steps

None. The case runs end to end; two of its five elements are red on OPEN product
defects and are asserted as the correct behaviour.

## Environment / hygiene

- Guardrails precondition captured as `sensitive_tools == {}`, restored to `{}`,
  **verified by readback** after both runs (`#1838` discipline).
- Conversations 9682 / 9683 and artifact toolkit 3430 deleted.
- **Leftover:** bucket `autotest-2213-live-790717` (1 file) could not be deleted — both
  URL forms `delete_bucket` tries returned 404. This is the already-known unreliable
  bucket deletion (`#636`), not a new finding.
