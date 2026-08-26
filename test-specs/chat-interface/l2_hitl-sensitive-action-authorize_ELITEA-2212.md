# Test Case: Chat – HITL Authorization – Click Authorize Executes the Toolkit Tool Directly

## Metadata
- **TMS ID**: ELITEA-2212
- **Linked Story**: none
- **Priority**: l2
- **Environment Explored**: local (`http://localhost:5173`, EliteaUI on `automation/testids`
  → DEV backend, project 399) — **the full case, end to end, executed live.** Every step
  of the case was performed against the real system and its outcome observed; nothing in
  this revision is source-verified-only.
- **User set**: `${TEST_USER}` (dev-token bypass on localhost; `ELITEA_API_TOKEN` for the
  precondition write and for the backend ground-truth reads)
- **Analyst**: qa-engineer
- **Status**: **ready-for-automation (sanctioned-RED)** — see § Classification note
- **Revision**: 2026-08-27 — **RE-ANALYSIS. Supersedes the 2026-08-03 pass entirely.**
  See § Delta vs the 2026-08-03 version.

---

## What this pass established (read this first)

The 2026-08-03 pass could not execute this case: it believed the HITL precondition required
the Admin UI, which localhost does not serve. That belief was retired by ELITEA-2211's
re-analysis — the guardrails config is writable by REST — and this pass therefore executed
ELITEA-2212 live for the first time.

**The case fails on the product side.** Clicking **Authorize** closes the card, and then
nothing happens:

| Case step | Live result |
|---|---|
| 1 — card + Authorize/Block/Block-with-Comment visible | ✅ works |
| 2 — click Authorize → card closes; **toolkit proceeds to execute** | ⚠️ card closes (0.1 s); **the toolkit never executes** |
| 3 — tool execution completes successfully | ❌ never happens — the file is still in the bucket after 90 s |
| 4 — model chip + toolkit/tool chip shown | ❌ **model chip never renders**; tool chip renders but is *not* evidence of execution (see below) |
| 5 — conversation continues normally | ❌ the assistant turn ends as `Thought for less than a second` with no answer, and persists **empty** after reload |

Filed as **#1834** (`bug`). No console errors, no failed HTTP request — the failure is
entirely silent.

**Two live-verified facts that change how this case must be automated:**

1. **The tool chip is already present WHILE the card is still pending.** Observed in every
   run: `chat-answer-tool-chip` reads `{toolkit_name}: delete_file` *before* Authorize is
   clicked. It is rendered from the pending tool-call intent, not from a completed call, so
   **asserting it proves nothing about execution.** The 2026-08-03 AFS specced it as part of
   the execution evidence; that was wrong.
2. **The model chip is the real "the turn completed" signal.** It is absent for the entire
   authorize flow, but a control run of the same toolkit and message with `sensitive_tools`
   unset renders `Anthropic Claude 4.5 Sonnet` and answers normally. So the model chip's
   absence here is meaningful, not a rendering quirk.

**Control — the tool itself is fine.** With guardrails off, the same toolkit + message
completes normally. The defect is specific to the HITL **approve/resume** path, not to
`delete_file`, not to the toolkit wiring, and not to the precondition mechanism.

### Reproduction record (determinism)

| # | Harness | Card appeared | Panel closed on one click | File deleted |
|---|---|---|---|---|
| 1 | Playwright MCP live session | ✅ | 2nd click | ❌ |
| 2 | Playwright MCP live session | ✅ | 2nd click | ❌ |
| 3 | `pytest` — the merged spec itself | ✅ | ✅ | ❌ |
| 4 | Scratch Playwright probe, run A | ✅ | ✅ 0.1 s | ❌ |
| 5 | Scratch Playwright probe, run B | ✅ | ✅ 0.1 s | ❌ (byte-identical to run A) |

**4/4 on the case's own observable** (the tool never executes). Deterministic, single-cause.

> **The "2nd click" column is an MCP-session artifact, NOT product behaviour — do not
> carry it into the test.** In the long-lived Playwright MCP browser context the *first*
> click on any card action (Authorize *and* Block) was swallowed and a second click was
> needed. In both clean Playwright contexts (the merged spec and the scratch probe) a
> single click closed the panel in 0.1 s, 3/3. The implementer should assume a single
> click works; if a future run ever needs two, that is a new finding to file, not this one.

---

## Classification note (why `ready-for-automation` and not `defect-found`)

Per `.agents/testing.md` § Merge gate → *Analysis-time entry* (2026-07-23, #557/ELITEA-1965):
`defect-found` is correct only when the defect **blocks further exploration**. It does not
here — every step of the case was reached and observed, and the defect is isolable to the
execution-related assertions at the tail of the flow.

The defect independently satisfies all three sanctioned-RED criteria:

- **(a) deterministic** — identical failure 4/4 (5 invocations counting the byte-identical probe repeat)
- **(b) single-cause** — one dropped resume; every downstream symptom (no execution, no model chip, no answer) follows from it
- **(c) linked to an OPEN defect** — **#1834**

So this case is `ready-for-automation` with the affected assertions written as the
**correct expected behaviour** under `expect.soft()` + `# Known defect: #1834`. The spec
merges RED and flips green when the product is fixed. Per `.agents/testing.md`
§ Merge gate, an `expect.soft` failure **is** a pytest FAILED, so:

- the spec is **sanctioned-RED** and owes a closure-record entry;
- the TMS case stays **`blocked-on-#1834`**, never `automated`.

---

## Preconditions

Identical to ELITEA-2211 — see
`test-specs/chat-interface/l2_hitl-sensitive-action-card-display_ELITEA-2211.md`
§ Preconditions. In short, and **live-re-verified this pass**:

- An Artifact-type toolkit with `delete_file` in `selected_tools` (`artifact_toolkit`), whose
  bucket contains at least one file (`artifact_seeded_file`).
- **`artifact`/`delete_file` marked sensitive via the guardrails config REST endpoint** —
  **NOT the Admin UI**, which is a separate deployed application localhost does not serve
  (no `/admin` route in `EliteaUI/src/routes.js`; #1140):

  ```
  GET  {ELITEA_API_BASE}/admin/plugin_config_values/administration/guardrails
  PUT  {ELITEA_API_BASE}/admin/plugin_config_values/administration/guardrails
       {"values": {<full GET body>, "sensitive_tools": {"artifact": ["delete_file"]}}}
  ```

  Re-confirmed live this pass with the standard test user's `ELITEA_API_TOKEN`:
  `200 {"saved": true, "requires_restart": []}`, readback
  `sensitive_tools: {"artifact": ["delete_file"]}`. Applies immediately — no restart, no
  re-attach, no fresh conversation. The PUT requires the **full** values object; restore
  the captured original verbatim on teardown (verified: readback returned to `{}`).
- **ORG-WIDE and toolkit-TYPE scoped** — the key is `artifact`, the toolkit *type*. Teardown
  restore is mandatory and must run on failure. Never run this module under `pytest-xdist`
  alongside artifact-toolkit suites.
- **No `pytest.mark.guardrails`** — the marker existed only because the old precondition drove
  the Admin UI. This module runs in the **local loop**. Markers: `ui`, `chat`, `p2`,
  `regression`.
- No agent is used — the toolkit is added directly as a chat participant via `/chat`'s
  "+ > Toolkits" flow.
- **Own fresh conversation per case.** Do not share a conversation or a card instance across
  ELITEA-2212/2213/2214 — each needs its own send-and-pause (isolation precedent: ELITEA-2015,
  pipeline HITL Approve vs Reject). Bare `/chat` restores the user's most recent conversation
  (the `#1082` pollution class) — always navigate to `/chat/{conversation_id}`.

---

## Test Data

Same fixture shape as ELITEA-2211: `artifact_toolkit` + `artifact_seeded_file` +
`conversation_id`, all function-scoped; `sensitive_delete_file_toolkit` module-scoped.

**Message text.** The case's own wording is ambiguous and does not reach a tool call against a
project with many buckets — re-confirmed. Use the explicit form (`_unambiguous_delete_message()`,
already in the merged module), re-verified live this pass **5 of 5 attempts**:

```
Use delete_file toolkit to delete a file named "{file_key}" from bucket "{bucket_name}". Execute the tool now, do not ask for clarification.
```

This is a case-text **CLARIFICATION**, not a product defect (reverse-masking guard).

---

## Test Steps

1. *(setup)* Bucket + toolkit + seeded file; capture the guardrails config and PUT it back with
   `sensitive_tools` additively including `artifact: [delete_file]`; fresh conversation.
2. Navigate to `/chat/{conversation_id}`; add the toolkit via **+ > Toolkits** using the
   **dynamic testid** (`add_toolkit_participant_via_slash_menu`), then
   **`close_plus_menu_popper()`**.
   - **Verify**: the "Toolkits in this conversation" badge (`chat-participants-badge-toolkits`)
     is visible. **Keep this assertion** — without the toolkit attached the model has no tool,
     hallucinates success, and no card ever appears; this pass reproduced that exact failure
     twice when the badge check was omitted (the LLM answered *"has been successfully deleted"*
     with the file untouched and **no tool chip**).
   - **`close_plus_menu_popper()` is load-bearing, not hygiene.** Live this pass, leaving the
     popper open made the plus-menu's tooltip subtree intercept pointer events and the
     Authorize click failed outright with a Playwright interception error. Note it must be a
     neutral click on the message list, **not** Escape (ELITEA-2203 quirk, already documented
     in the page object).
3. Send the unambiguous delete-file message.
   - **Verify**: `chat-answer-thought-accordion` becomes visible. Its text is variable
     ("Thought for less than a second" / "Thought for 2 secs") — assert **visibility only**.
4. **Verify the Sensitive Action Authorization card appears** (`sensitive-action-panel`).
   - Latency live this pass: **3.9 s / 4.0 s / 4.7 s / 6.0 s**. Keep `SENSITIVE_ACTION_TIMEOUT`
     at 30 s.
5. **Verify all three action buttons are visible on this case's own card instance** —
   `sensitive-action-authorize-button` ("Authorize"), `sensitive-action-block-button` ("Block"),
   `sensitive-action-block-with-comment-button` ("Block with Comment"). *(Case step 1.)*
6. **Click Authorize; verify the card closes.** *(Case step 2, first half.)*
   - Live: `to_have_count(0)` satisfied in **0.1 s**, 3/3 in clean contexts. **This is a HARD
     assertion — it passes today.**
7. **Verify the toolkit tool genuinely executed** — the seeded file is gone from the bucket,
   read from the backend (`ArtifactAPI.list_bucket_files`), never from a UI signal.
   *(Case steps 2 second half + 3.)*
   - Live: **FAILS** — file still present after 90 s, 4/4.
   - ⇒ **`expect.soft()` / soft-failure aggregation + `# Known defect: #1834`.**
   - Must be a **real poll** with a timeout (the file disappears asynchronously when the
     product works). See § Rework delta row 1 — the merged test's `expect.poll` does not exist
     in Python Playwright.
8. **Verify the LLM-model chip renders** (`chat-answer-model-chip`) — the signal that the turn
   completed. *(Case step 4, model half.)*
   - Live: **FAILS** — count 0 throughout. Control run with guardrails off renders
     `Anthropic Claude 4.5 Sonnet`, so the expectation itself is correct.
   - ⇒ **`expect.soft()` + `# Known defect: #1834`.**
9. **Verify the toolkit/tool chip renders** (`chat-answer-tool-chip`, text
   `"{toolkit_name}: {tool_name}"`). *(Case step 4, tool half.)*
   - Live: **PASSES** — but it is already present *before* Authorize is clicked. Keep it as a
     hard assertion of case step 4, and **document in the test that it is not execution
     evidence** so nobody later mistakes it for one.
   - Use `.first` (or an explicit count assertion). Only one chip was observed, but the bare
     locator is a strict-mode violation the moment a second tool call renders.
10. **Verify the conversation continues normally** — composer re-enabled, panel stays gone.
    *(Case step 5.)*
    - Live: composer **is** editable and the panel stays gone (both pass), **but** the turn
      produced no answer at all. The composer check alone is therefore a weak reading of "the
      conversation continues normally"; step 8's model chip is what actually carries that
      meaning, and it is soft-asserted.
11. **Side-channel** — no console **errors** across the flow (0 observed, 5/5). The unhandled
    `parallel_hitl_ready` socket message is a console **warning** (#1831) and must **not** be
    filtered into or out of this assertion.
12. *(teardown)* Restore the captured guardrails config in a `finally`; delete toolkit /
    conversation / bucket.

---

## Expected Results

- Authorize closes the card **and the toolkit tool genuinely executes** (backend-verified).
- Model chip + toolkit/tool chip both render; the assistant produces a completion message.
- No console/JS errors.

Today the first bullet's second half and the model chip fail on **#1834**; the spec asserts the
correct behaviour anyway and stays RED until the fix ships.

---

## Coverage Map

**Axis 1 — every element of the TMS case:**

| Case element | Expected result | Covered by (AFS step) | Asserted where | Disposition |
|---|---|---|---|---|
| Precondition: user logged in | — | `auth_state` (dev-token bypass) | fixture | asserted implicitly |
| Precondition: HITL card showing for a sensitive toolkit action | card present | steps 1–4 | steps 1–4 | asserted — **live-verified**, this case reaches its OWN card rather than citing ELITEA-2211 |
| 1 Card shows with Authorize/Block/Block-with-Comment | all visible | step 5 | step 5 | asserted (hard) — independently on this case's own card instance |
| 2 Click Authorize → card closes | card closes | step 6 | step 6 | asserted (hard) — **passes live** |
| 2 …toolkit proceeds to execute | execution proceeds | step 7 | step 7 | asserted **soft** — fails on **#1834** |
| 3 Tool execution completes successfully | execution completes | step 7 | step 7 (backend file-listing) | asserted **soft** — fails on **#1834** |
| 4 Chips shown: LLM model chip | model chip visible | step 8 | step 8 | asserted **soft** — fails on **#1834** |
| 4 Chips shown: toolkit tool chip | tool chip visible | step 9 | step 9 | asserted (hard) — passes; *documented as not being execution evidence* |
| 5 Conversation continues normally / no errors | no errors | steps 10 + 11 | steps 10, 11 | partially asserted — composer + panel + console pass; the "turn actually completed" meaning is carried by step 8's soft assertion |
| Expected Final State: toolkit executes after authorization; chips shown | — | steps 7–9 | steps 7–9 | asserted (mixed hard/soft) |

**Axis 2 — analyst additions (beyond the case):**
- **Backend file-listing as the execution oracle** rather than a UI signal — *added: the case's
  "verify execution completes successfully" is unfalsifiable from the UI. This pass proved why:
  the card closes and the tool chip is present while the tool has demonstrably not run.*
- **Model chip treated as the turn-completed signal** — *added: established live by the
  guardrails-off control; without it, "conversation continues normally" has no observable.*
- **Toolkit-attachment (badge) assertion before sending** — *added: reproduced twice this pass
  that a silently unattached toolkit produces a confident false "deleted" answer and no card.*
- **No console/JS errors** — *added: standard side-channel discipline; HITL rides an async
  WebSocket envelope, exactly the shape that swallows errors silently.*
- **Fresh `conversation_id` rather than bare `/chat`** — *added: `#1082` pollution class.*

**Deliberately NOT specced** (same as ELITEA-2211 — observed but out of case scope, and
speccing them would need testids on elements no test exercises, per `.agents/testing.md`
§ Locator policy blanket-add ban): the `Parameters ▸` expander and the templated policy-message
line (driven by the guardrails config key `sensitive_action_message_template`, so asserting it
would couple the test to org config).

---

## Fidelity Declaration

| What is substituted | Transit or terminal | Authority |
|---|---|---|
| The guardrails **precondition** is configured via `PUT {api}/admin/plugin_config_values/administration/guardrails` instead of through the Admin UI | **Transit** | Every observable this case asserts — that the card closes, that the file is **actually gone from the bucket**, that the model chip and tool chip render, that the composer re-enables, that no console errors occur — is produced end to end by the real system: the real LLM decides to call the real tool, the real backend interrupts it, the real WebSocket frame renders the real card, and the real backend either does or does not delete the file. The substitution only *reaches* the step under test. The Admin UI appears in neither the case's steps nor its expected results (it was a prior analyst's chosen mechanism, not the case's) and is not served on the local target at all. |

**No terminal substitution anywhere in this spec.** Nothing about the card, the execution, or
the chips is mocked, injected, fabricated or routed. `page.route`, `route.fulfill`,
`page.evaluate` and monkeypatching are **not** used and must not be introduced.

*Note for the implementer's Run Report grep:* the required
`\.mock_|page\.route\(|route\.fulfill\(|monkeypatch|\.evaluate\(` self-check should return
**0 hits** on this case's diff. The guardrails PUT is an ordinary `requests` call in the API
client, not a Playwright interception, so it does not appear in that grep — it is declared here.

**In particular, #1834 must not be worked around.** The correct behaviour is asserted as the
expected behaviour; the test goes red. Weakening the file-deletion assertion, dropping the
model-chip assertion, or "verifying execution" via the tool chip (which renders regardless)
would all be masking.

---

## Rework delta for the implementer (the merged test already exists)

Target:
`automation/tests/ui/chat/test_hitl_sensitive_action_authorization.py::TestSensitiveActionAuthorize::test_authorize_executes_toolkit_tool_directly`

| # | Change | Severity |
|---|---|---|
| 1 | **`expect.poll(...)` does not exist in Python Playwright — the test cannot run.** `playwright.sync_api.expect` is an `Expect` instance with no `poll` attribute (`expect.poll` is the **JavaScript** API). Verified in-venv (Playwright 1.61.0): `hasattr(expect, 'poll') is False`, and running the spec fails with `AttributeError: 'Expect' object has no attribute 'poll'` at `test_hitl_sensitive_action_authorization.py:303`. Replace with an explicit deadline poll over `artifact_api.list_bucket_files(bucket_name)` (framework wait on a real backend condition — a `while time.time() < deadline` loop with a short sleep between REST reads is the honest shape here; it is not a UI wait and not a `sleep()` substitute for one). | **blocker** |
| 2 | **Make the execution assertion soft**: `expect.soft`-style / soft-failure aggregation asserting the file IS gone, with `# Known defect: #1834`. It must assert the CORRECT behaviour, never the broken one. | **blocker** |
| 3 | **Make the model-chip assertion soft**, same `# Known defect: #1834`. | **blocker** |
| 4 | **Keep the tool-chip assertion hard, and add a comment that it is NOT execution evidence** — it renders while the card is still pending (live-verified every run). Add `.first` (or an explicit count) so a second tool call cannot cause a strict-mode violation. | important |
| 5 | **Remove the fix-round-1 archaeology from the `allure.step` labels.** The long "the AFS Coverage Map row 1 previously cited ELITEA-2211…" label describes a review exchange, not a test step; it will be the step title in every Allure report forever. Replace with "Step 1 — Verify the card shows Authorize / Block / Block with Comment". | nit |
| 6 | **Renumber the `allure.step` labels.** They currently all read `"Step — …"`; `.agents/testing.md` § Step reporting requires `"Step N — …"`, one per AFS step. | important |
| 7 | The `_reach_sensitive_action_card()` helper, the badge assertion and `close_plus_menu_popper()` are **correct as merged** — all three re-verified live this pass. Do not change them. | — |

**Sanctioned-RED bookkeeping.** Once reworked this spec merges RED with signature
"#1834: file not deleted + model chip absent" — a single cause, two soft failures. Record it in
the closure record; the TMS case goes to `blocked-on-#1834`, **not** `automated`.

### Risk flagged to the lead — ELITEA-2213 (not re-analysed here)

`TestSensitiveActionBlock` asserts `expect(chat.answer_tool_chip).to_have_count(0)` after Block.
This pass established that the tool chip **is present while the card is pending**. Whether Block
removes it was **not** observed (the MCP-session Block attempt did not resolve, and no clean
Block run was made). If it does not, that assertion fails for a reason unrelated to #1834.
ELITEA-2213 should be re-analysed or at least run once before its next gate.

---

## Cleanup

1. Restore the captured guardrails config by PUTting the original verbatim — mandatory,
   org-wide, must run on failure. Re-verified this pass: readback returned to `sensitive_tools: {}`.
2. Delete toolkit (`ToolkitAPI.delete_toolkit`) — worked every time this pass.
3. Delete conversation (`ConversationAPI.delete_conversation`) — worked every time this pass.
4. Delete bucket (`ArtifactAPI.delete_bucket`) — **re-confirmed flaky**: 404 on
   `p--{project_id}.{bucket_name}` for buckets created minutes earlier, **9 of 9** this pass.
   Non-blocking (the fixture swallows it with a warning) but it is the source of the project's
   accumulated bucket pollution. Unchanged tech-debt note.
5. No pending card is left to resolve — Authorize already closed it.

---

## Concrete Handles

Provenance verified after `cd ../EliteaUI && git fetch origin` on **2026-08-27**, two-stage
grep per `.agents/workflow.md` § Closure record.

| Element | Recommended Locator | PROVENANCE |
|---|---|---|
| Sensitive action panel | `LocatorDescriptor(testid="sensitive-action-panel")` — `chat_page.py:986` | **on-main ✓** |
| Authorize button | `LocatorDescriptor(testid="sensitive-action-authorize-button")` — `chat_page.py:997`; live text "Authorize" | **on-main ✓** |
| Block button | `LocatorDescriptor(testid="sensitive-action-block-button")` — `chat_page.py:1002`; live text "Block" | **on-main ✓** |
| Block with Comment button | `LocatorDescriptor(testid="sensitive-action-block-with-comment-button")` — `chat_page.py:1007`; live text "Block with Comment" | **on-main ✓** |
| Model chip | `LocatorDescriptor(testid="chat-answer-model-chip")` — `chat_page.py:923`; live text `Anthropic Claude 4.5 Sonnet` (control run) | **on-main ✓** |
| Toolkit/tool chip | `LocatorDescriptor(testid="chat-answer-tool-chip")` — `chat_page.py:942`; live text `{toolkit_name}: delete_file` | **on-main ✓** |
| Thought accordion | `LocatorDescriptor(testid="chat-answer-thought-accordion")` — text is variable, assert visibility only | **on-main ✓** |
| Message composer | `LocatorDescriptor(testid="chat-message-input")` | **on-main ✓** |
| Message list (neutral click target for `close_plus_menu_popper`) | `chat-message-list` | **on-main ✓** |
| Plus menu button | `plus-menu-button` | **on-main ✓** |
| Toolkits submenu item | `toolkits-menuitem` | **on-main ✓** |
| Toolkit participant row (dynamic) | `toolkits-menu-item-toolkit-{project_id}-{toolkit_id}` — live-confirmed as `toolkits-menu-item-toolkit-399-3405` etc. | **on-main ✓** (runtime-composed in `PlusChatSubmenu.jsx:131`; a bare-substring grep cannot see it — do not re-derive this as "missing") |
| Toolkits participants badge | `chat-participants-badge-toolkits` — via `ChatPage.is_participants_badge_visible(section="toolkits")` | **on-main ✓** (runtime-composed in `CollapsedPerticapantsList.jsx:223`) |
| Execution ground truth | `ArtifactAPI.list_bucket_files(bucket_name)` — backend, no UI fallback | n/a (API) |

**No new testids are needed for this case.** All twelve UI handles exist and are on
`EliteaAI/EliteaUI` `main` — this case is **fully promotable** with zero pending human
cherry-picks.

---

## Network Behavior

- The HITL pause/resume rides the `chat_predict` WebSocket envelope; the frontend disambiguates
  on `guardrail_type` (`sensitive_tool` / `parallel_sensitive_tools`, `ChatHitlActions.jsx:22`).
  Authorize calls `handleApprove` → `onHitlResume({action: 'approve', toolCallId, interruptId})`
  (`ChatHitlActions.jsx:33-35`) → `ChatBox.jsx:1567`'s `onHitlResume`, which early-`return`s
  silently when `pendingHitlMessage` is falsy — a plausible place for the dropped resume, offered
  as a pointer for the fix, not as a diagnosis.
- The precondition write is a plain REST call:
  `PUT /admin/plugin_config_values/administration/guardrails` → `200 {"saved": true, "requires_restart": []}`.
- **No 4xx/5xx is produced anywhere in the failing flow** — network and console are both clean,
  which is what makes #1834 silent. (Per `.agents/role-overrides.md` § 4xx/5xx cross-check: there
  is no status code to classify here; the classification rests on backend ground truth instead.)

---

## Known Defects Found During Exploration

- **#1834 (filed this pass, MAJOR)** — Authorize closes the sensitive-action card but the
  toolkit tool never executes; the turn dies silently (no execution, no model chip, no answer,
  no error). Deterministic 4/4 across two harnesses; guardrails-off control proves the tool and
  toolkit are fine. **This is the case's own subject** — see § Classification note.
- **#1831 (pre-existing, MINOR)** — the backend emits a `parallel_hitl_ready` WebSocket message
  the frontend has no handler for; logs `console.warn('unknown message type', …)` and returns
  early at `src/components/Chat/hooks.js:1658`, skipping the `setChatHistory` update. Re-observed
  on **every** HITL invocation this pass. It is a *warning*, so the errors-only side-channel
  assertion stays green — do **not** weaken or filter that assertion for it. Whether it shares a
  root cause with #1834 is for the dev team.
- **#1140 (pre-existing)** — Guardrails admin route is Page404. Still true, still **not** a
  blocker for this case (the Admin UI is a separate deployed app; the config is reachable by REST).
- Bucket-delete 404 on teardown — pre-existing tech debt, 9/9 this pass, non-blocking.
- Testid gaps: **none**.

---

## Blocked Steps

**None.** Every step of the case was executed and observed live on `http://localhost:5173`.
The case's expected results are not all *met* — but that is a product defect (#1834) with an
observable, not an analyst blocker.

---

## Automation Hints

- Framework: Playwright + pytest, per `.agents/testing.md`.
- Markers: `ui`, `chat`, `p2`, `regression` — **not** `guardrails`.
- Card latency 3.9-6.0 s live; keep `SENSITIVE_ACTION_TIMEOUT` at 30 s. Wait on the panel's
  visibility, never a sleep.
- Guardrails changes are live immediately (`requires_restart: []`) — no restart, no re-attach,
  no fresh conversation.
- Run the module **serially** — the guardrails flag is org-wide while set.
- Total live runtime of the honest flow: ~25 s to the card + up to 90 s of execution polling.
  Budget the poll deadline generously; it is the assertion that will flip green when #1834 is fixed.
- **Do not use the Playwright MCP browser to sanity-check this flow** — its long-lived context
  swallowed the first click on every card action (4/4) while both clean Playwright contexts
  worked first-click (3/3). It will send you chasing a phantom.

---

## Delta vs the 2026-08-03 version

| # | What changed | Why |
|---|---|---|
| 1 | **§ Metadata Environment**: "local for the chip portion; **source-verified** for the Authorize-resume wiring" → **fully executed live, end to end**. | The Authorize-resume path had never been run. It has now been run 5 times, and it fails. Source-reading could not have found that: the source is fine, the runtime behaviour is not. |
| 2 | **§ Preconditions**: "marked sensitive via **Admin UI Guardrails**, `pytest.mark.guardrails`, **CI-only execution**" → REST `administration/guardrails` write, **no `guardrails` marker**, runs in the **local loop**. | Inherited from ELITEA-2211's re-analysis and re-verified independently this pass. The Admin UI is a separate deployed application localhost never served (#1140 re-scoped), so the marker and the CI-only routing were solving a non-problem. |
| 3 | **§ Preconditions**: dropped "chain this test's setup off ELITEA-2211's test body" as an option. | Cross-case chaining was already discouraged; with the card now cheap to reach (≈25 s), the own-fresh-card path is unambiguously right and the alternative only invites shared-state coupling. |
| 4 | **New § Fidelity Declaration** (the 2026-08-03 version had none). | Required by `.agents/role-overrides.md` § Analyst slot for the REST precondition — transit-only, with the real observables named. |
| 5 | **§ Concrete Handles**: gained a **PROVENANCE column** (fresh `git fetch origin`, 2026-08-27) and lost its "Fallback" column. | Project canon: testid-only, provenance verified per handle. There is no fallback ladder here, so a "Fallback" column was misleading by construction. |
| 6 | **Toolkit/tool chip: "testid needed — `chat-answer-tool-chip`"** → **exists, on `main`**, wired at `chat_page.py:942`. | The testid was added by the ELITEA-2211..2214 implementation and has since reached `main`. Verified this pass. |
| 7 | **Tool chip demoted from execution evidence to a step-4 presence check.** | Live-verified: it renders **while the card is still pending**, before Authorize. The old AFS listed it under "verify tool-execution chips", which would have made a passing assertion out of a non-event. |
| 8 | **Model chip promoted to the turn-completed signal**, and made a soft assertion. | Live-verified absent for the whole authorize flow, present on a guardrails-off control run. The old AFS asserted it as "confirmed live via the adjacent ELITEA-2215 flow" — i.e. on a *different* flow, which turns out not to transfer. |
| 9 | **New: the execution assertion, model-chip assertion → `expect.soft()` + `# Known defect: #1834`; status stays `ready-for-automation` (sanctioned-RED); TMS case → `blocked-on-#1834`.** | The defect is deterministic, single-cause and linked, and does not block exploration — `.agents/testing.md` § Merge gate, *Analysis-time entry*. |
| 10 | **New § Rework delta row 1: `expect.poll` is not a Python Playwright API.** | The merged test cannot execute at all: `AttributeError: 'Expect' object has no attribute 'poll'`. The 2026-08-03 AFS specced the assertion in prose, the implementation reached for the JS API, and no gate caught it because the spec had never been run. |
| 11 | **New: `close_plus_menu_popper()` and the participants-badge assertion documented as load-bearing.** | Both were re-derived the hard way this pass — an open popper made the Authorize click fail with a pointer-interception error, and omitting the badge check reproduced the silent non-attach twice (LLM claims success, file untouched, no tool chip). |
| 12 | **New § "2nd click" warning about the Playwright MCP context.** | 4/4 first clicks swallowed in the MCP browser vs 3/3 first clicks working in clean Playwright contexts. Without this note the next analyst will re-derive it, and might file it as a product bug. |
| 13 | **§ Network Behavior**: "implementer should capture the actual websocket frame shape once run against CI" → resolved; plus the note that the failing flow produces **no** 4xx/5xx. | The case no longer needs CI to be observed. |
| 14 | **§ Coverage Map row 1** no longer carries the fix-round-1 citation argument. | It was review archaeology about whether ELITEA-2211 could be cited as a merged target. This case asserts the three buttons on its own card instance; the argument is moot and the row now just states what is asserted. |
