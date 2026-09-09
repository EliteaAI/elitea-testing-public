# Test Case: Code Node — elitea_client Access

## Metadata
- **TMS ID**: ELITEA-2448
- **Linked Story**: none
- **Priority**: l3 (medium, as authored in the source TMS case — matches sibling
  ELITEA-2446/ELITEA-2447's own AFS mapping)
- **Environment Explored**: local (`http://localhost:5173`, `EliteaAI/EliteaUI` @
  `automation/testids`, DEV backend)
- **User set**: `${TEST_USER}` (localhost: no login needed — `VITE_DEV_TOKEN` auto-auths)
- **Analyst**: qa-engineer (agent), session 2026-08-09
- **Repair pass**: qa-engineer (agent), session 2026-09-09 — issue
  `EliteaAI/elitea-testing-public#2076` (`[FIX][ELITEA-2448] assertion-failure`,
  CI run 34331579791). Steps 4-5 rewritten; **§ Repair Amendment (2026-09-09)
  below is authoritative where it differs from the original text.** No
  assertion was dropped or weakened.
- **Status**: ready-for-automation

## Preconditions
- User is authenticated (localhost: automatic via `VITE_DEV_TOKEN`; deployed envs:
  standard Keycloak login via `${TEST_USER}`).
- A project with Pipelines access exists (localhost dev project id `399`).
- **Build via API/raw YAML, NOT the Flow Editor's "Add node" clicks** — same
  reason ELITEA-2446/ELITEA-2447 already established
  (`PipelineAPI.create_pipeline()` with a hand-built YAML `instructions` string;
  `create_pipeline_with_nodes()` has no `state:` support). This case needs only
  ONE custom state variable (`user_info`, type `JSON`) and a single Code node as
  the entry point — the simplest topology in this Code-node family, so the
  build-method gotcha (disconnected `-> END` edges, `#1384`) that forced
  ELITEA-2446/2447 into a 2-node fixture doesn't even apply here, but the raw-YAML
  build is kept for consistency with the sibling fixtures and because
  `create_pipeline_with_nodes()` still can't declare the custom `state:` block.

## Test Data

### generate-per-test (in test setup, cleaned up in its own teardown)
- A fresh pipeline built from raw YAML `instructions`, topology `Code 1 (entry) -> END`:
  ```yaml
  entry_point: Code 1
  state:
    user_info:
      type: JSON
  nodes:
    - id: Code 1
      type: code
      code:
        type: fixed
        value: |
          user_info = elitea_client.get_user_data()
          user_info
      input: []
      output: [user_info]
      structured_output: true
      transition: END
  ```
  **CONFIRMED LIVE (4-turn probe, pipeline id `8820`, project 399 "Private"): the
  case's own literal step-2/3 script — `user_info = elitea_client.get_user_data()`
  followed by a bare `user_info` name reference as the LAST statement — works
  exactly as written.** This is a different shape from ELITEA-2446/2447's
  discovery (a plain ASSIGNMENT as the last statement silently drops the state
  update): here the last statement is a bare *expression* (a name reference to a
  dict-valued variable), not an assignment, and the runtime accepts it the same
  way it accepts a bare dict-literal — both are non-assignment expression
  statements. No CLARIFICATION needed for this case; the case text is
  live-correct.
  - `type: JSON` (backend/YAML state-var type, `.claude/skills/elitea-pipeline/
    references/yaml-schema.md:52`) is a DIFFERENT spelling from the STATE panel
    UI's internal type key for the same concept (`dict`, displayed as "Json" —
    `l2_pipeline-state-panel-default-and-custom-variables_ELITEA-2042.md`'s
    Concrete Handles table). Confirmed live: the API accepts `type: JSON` verbatim
    (echoed back unchanged by `GET .../application/prompt_lib/{project}/{id}`),
    and the STATE panel correctly lists the `user_info` row by name. This AFS
    only asserts the row's NAME (matching ELITEA-2446's own String-type
    assertion depth), not its type-icon rendering — a dedicated type-icon
    assertion for the JSON/dict type is out of scope for this case's own text
    and belongs to ELITEA-2042's existing type-selector coverage if ever needed.
- Chat message sent to trigger execution: any short prompt (this session used
  `"hello"`) — content is irrelevant; the Code node takes no chat input (`input: []`).

### reuse-existing
- `${TEST_USER}` — only needed on deployed envs; localhost skips login entirely.
- `${ELITEA_PROJECT_ID}` (`.env.test`) — this session's live-exploration browser
  was on project "Private" (id 399), matching `.env.test`.

## Test Steps

1. Create a pipeline with a Code node (entry point, single node, `Code 1 -> END`).
   - **Verify**: canvas renders one `code`-type node; `wait_for_node_on_canvas("code")`
     returns an id (`"Code 1"`).
2. In Code node script, use `elitea_client` to read user information:
   `user_info = elitea_client.get_user_data()` then a bare `user_info` reference
   as the final statement.
   - **Verify**: `get_code_node_value()` reflects the two-line script exactly;
     `"elitea_client.get_user_data()"` is present verbatim.
3. Set Output to the `user_info` state variable and enable structured output.
   - **Verify**: `get_code_node_output_value() == "user_info"`;
     `code_node_structured_output_toggle.is_checked() == True`.
4. Execute the pipeline (send any chat message in the embedded chat).
   - **Verify** (REWRITTEN 2026-09-09, see § Repair Amendment): (a) the chat
     accepted the message — `wait_for_embedded_chat_message_count(initial+1, ...)`
     (raises on timeout); (b) the run STARTED — a run node appeared on the
     canvas (`run_node_label` visible, budget `PIPELINE_RUN_START_TIMEOUT`),
     failing with *"the pipeline run never started"*; (c) the run COMPLETED —
     open the Run Details panel ONCE and wait for
     `pipeline-run-details-status-badge`'s `data-status` to reach `"Completed"`
     (budget `PIPELINE_EXECUTION_TIMEOUT`), failing with *"the pipeline run did
     not complete — Run Details status is still <x>"*.
   - **Do NOT** call `wait_for_embedded_chat_response()` here: for this pipeline
     it can neither succeed nor fail (§ Repair Amendment § A).
5. Verify Code node executes without errors in Run Details.
   - The panel is ALREADY open from step 4 — do **not** call
     `open_run_details_panel()` a second time: the MUI Dialog overlays the
     canvas and intercepts pointer events, so the second click hangs until
     timeout (confirmed live 2026-09-09).
   - **Verify**: `select_run_details_timeline_step(0, ...)` (index 0 — the ONLY
     timeline entry, this is a single-node pipeline) then
     `get_run_details_timeline_step_status(0) == "completed"`; the selected
     step's label contains `"pyodide"` (the Python-sandbox executor's name — SAME
     Code-node timeline-label convention ELITEA-2446 already established,
     `EliteaAI/elitea-testing-public#1385`, NOT the space-stripped-id convention).
6. Verify Code node output state variable contains the user information.
   - **Verify**: `expand_run_details_state_row("user_info", ...)` then
     `get_run_details_state_after_value("user_info")` — CONFIRMED LIVE this
     session, the After value is the full JSON-serialized user object:
     `{"api_url":"...","email":"testbot@elitea.ai","id":659,"name":"Test Bot",
     "personal_project_id":399,...}`. Assert the parsed JSON contains non-empty
     `email` and `name` keys (the case's own "contains the user information"
     wording — don't pin exact values, since the test-bot's own account fields
     could legitimately change; assert structure + presence, not a literal string).

## Expected Results
- The Code node correctly calls `elitea_client.get_user_data()` and writes the
  full user-data dict into the `user_info` state variable via a bare name
  reference as the script's final statement (no dict-literal rewrap needed).
- Run Details shows ONE timeline step (`Code 1`, labelled `"pyodide"`), completed,
  with `user_info`'s After value containing real account fields (`email`, `name`,
  `id`, `personal_project_id`, etc.) — confirming `elitea_client` resolves to the
  currently-authenticated test user, not a stub/empty object.
- No console errors (excluding the known `#1267` Stepper prop-leak, confirmed to
  recur identically here — same `RunStateDialog.jsx` panel every Run-Details-
  opening case in this suite hits).

## Repair Amendment (2026-09-09 — issue #2076, CI run 34331579791)

_Analyst repair pass. Live-re-executed against `http://localhost:5173`
(`EliteaAI/EliteaUI` @ `automation/testids`, DEV backend) on a throwaway
pipeline built from this AFS's own § Test Data YAML (`sage2448probe`, id
`10398`, project 399 — **deleted at the end of the session**, `DELETE
.../application/prompt_lib/399/10398` 200). Three live executions observed at
250 ms sampling. **Every original assertion survives unchanged; only the WAIT
changes.**_

### A. Why the CI red happened — `wait_for_embedded_chat_response()` cannot fail, and for this pipeline cannot succeed

`PipelineDetailPage.wait_for_embedded_chat_response()`
(`automation/pages/pipeline_detail_page.py:7336-7396`) is a **soft** wait: on
timeout it logs `WARNING Embedded chat response did not stabilise within
timeout` and RETURNS. Two independent mechanisms then make it burn its entire
budget on this pipeline — both confirmed live, not inferred:

1. **The Delete-button wait eats the whole deadline (primary mechanism).**
   After the new-message poll, the helper waits for
   `messages.last.locator('[aria-label="Delete"]')` with
   `timeout = deadline - now` — i.e. **all 90 s of `PIPELINE_EXECUTION_TIMEOUT`
   minus the few seconds already spent**, inside a bare `try/except: pass`. For
   this pipeline that button NEVER appears: the assistant bubble never leaves
   its streaming state (see § C). Measured live — at 130 s after send, and again
   at 165 s on a second run, the answer `<li>` still contained only
   `chat-answer-thought-accordion` + `chat-answer-tool-chip`, **no action bar at
   all, hover included**. So the helper always returns at the deadline, and the
   content-stability loop below it never gets a single iteration.
2. **The stability guard cannot be satisfied while the placeholder is rotating
   (secondary mechanism, would bite even if 1 were fixed).** The pre-answer
   placeholder phrase **rotates every 2.0 s** — measured verbatim at
   t=4.25/6.25/8.25/10.25/12.25/14.25/16.25/18.25 s: `Waking the agent…` →
   `Packing its tools…` → `Wiring integrations…` → `Fetching keys & creds…` →
   `Installing skills…` → `Learning your playbook…` → `Safety checks on…` →
   `Quick sandbox test…`. The loop requires `stable_duration_ms = 3000` of
   *unchanged* text, which a 2 s rotation can never deliver. (`Fetching keys &
   creds …` — the phrase frozen in the CI failure snapshot — is simply the 4th
   entry in that carousel, i.e. the run had not started yet. It is not a hang
   signature by itself.)
   *(The empty-text hypothesis in the dispatch is REFUTED: the message text is
   never empty — `if current and current == last_content` was not the blocker.)*

**Consequence, and the actual defect being repaired:** Step 4 spent exactly its
90 s budget, silently, on EVERY run — including the ones that passed (the
dispatch's local repro measured 90.4 s twice; this session reproduces the same
mechanism). It then asserted `run_node_label` visible with only 10 s left. So
the spec's real budget for "did the run start?" was 90 s of blind waiting + a
10 s window, and its failure message was *"element not found"* — naming the
wrong subsystem, exactly the class the ledger's `#2074` entry warns about.

### B. Timings measured live (why 90 s + 10 s is not enough)

| Run | send → run node appears on canvas | run node → `Completed` | send → `Completed` |
|---|---|---|---|
| 1 (fresh page) | **4.5 s** | 31.0 s | 35.5 s |
| 2 (same page, 2nd message) | **never** (abandoned at 100 s) | — | — |
| 3 (fresh page load) | **89.3 s** | 31.7 s | **121.0 s** |

The node-execution phase is stable at ~31 s (pyodide sandbox). **The variance is
entirely in how long the DEV backend takes to START the run** — 4.5 s to 89 s+
on the same pipeline within one hour. Run 3 alone would have failed the spec as
written even on a perfectly healthy CI box: the run node appeared at 89.3 s,
inside the blind 90 s wait, leaving ~0.7 s of the 10 s assertion window, and it
did not reach `Completed` until 121 s. **This, not the DEV gateway-500 outage,
is sufficient to explain `#2076`** (the outage plausibly contributed on that
particular CI run — 8/10 jobs failed there, `#2074` — but the spec is fragile
without it).

### C. Product-bug verdict: **(i) test-wait defect + backend start latency — no product defect blocks this case**

- The pipeline itself executes correctly and completely: run status `Completed`,
  timeline step 0 `data-status="completed"`, label `pyodide`, and `user_info`'s
  After value = `{"email":"testbot@elitea.ai","id":659,"last_login":"Wed, 09 Sep
  2026 08:49:19 GMT","name":"Test Bot","personal_project_id":399,
  "suspended":false}` — the case's own observable, produced by the system.
- **Separate live observation, NOT part of this case and NOT filed by this pass
  (reported to the lead instead):** the embedded-chat assistant bubble never
  finalises for this Code-node-only pipeline. Long after the run reads
  `Completed`, the message still renders only the thought accordion + tool chip
  — no answer body (`skill-test-last-response` never appears), no message action
  bar even on hover (observed ≥130 s and ≥165 s on two separate runs). This may
  be correct-by-design (a pipeline whose only node writes to a state variable
  emits no chat answer) or a UI finalisation gap; distinguishing them needs a
  control run on an LLM-node pipeline, which is out of this card's scope. It
  does not affect any assertion in this case.
- Also observed, informational: navigating away from the pipeline page raises a
  `beforeunload` dialog (page considered dirty although nothing was edited).
  Not asserted here; not investigated.

### D. Corrected Step 4 — the honest observable (verified, zero new testids)

The completion signal is **the run's own status**, read off testids that are
**already on EliteaUI `main`** (verified this session, § Concrete Handles) —
critical, because this card exists to fix a **deployed-env CI** red: a repair
depending on a brand-new attribute sitting only on `automation/testids` would
keep CI red until a human cherry-picks it.

Verified live: with the Run Details panel opened **while the run was still In
progress**, `pipeline-run-details-status-badge`'s `data-status` updated in place
`"In progress"` (t=108.8 s) → `"Completed"` (t=121.0 s), and the panel then
rendered timeline step 0 (`data-status="completed"`, `aria-label="pyodide"`),
the `Timeline step:pyodide` section text, and the `user_info` state row with its
full After JSON — i.e. **Steps 5 and 6 work unchanged on a panel that was opened
during the run.**

Spec for the implementer (a NEW page-object method used only by this spec is
in-contract; the shared `wait_for_embedded_chat_response` contract must NOT be
touched — it has 20 caller files):

```python
# constants (spec module level)
PIPELINE_RUN_START_TIMEOUT = 150_000   # send -> run node on canvas; measured 4.5 s .. 89.3 s
PIPELINE_EXECUTION_TIMEOUT =  90_000   # run node -> Completed; measured ~31 s, unchanged

# Step 4
initial_count = pipeline_page.get_embedded_chat_message_count()
pipeline_page.send_message_in_embedded_chat(_CHAT_MESSAGE, timeout=UI_ELEMENT_TIMEOUT)

# (a) the chat accepted the message — existing helper, RAISES on timeout
pipeline_page.wait_for_embedded_chat_message_count(initial_count + 1, timeout=UI_ELEMENT_TIMEOUT)
# ...and KEEP the original explicit assertion verbatim — the wait makes it
# deterministic, it does not replace it:
assert pipeline_page.get_embedded_chat_message_count() > initial_count, (
    "Embedded chat should show at least one new message after the run completes"
)

# (b) the run STARTED — honest message naming the real subsystem
pipeline_page.wait_for_run_node_on_canvas(timeout=PIPELINE_RUN_START_TIMEOUT)

# (c) the run COMPLETED — open the panel ONCE, wait on the system's own status
pipeline_page.open_run_details_panel(timeout=UI_ELEMENT_TIMEOUT)
pipeline_page.wait_for_run_details_status("Completed", timeout=PIPELINE_EXECUTION_TIMEOUT)
```

New page-object methods (both new, both spec-local in usage; neither changes an
existing signature):

```python
def wait_for_run_node_on_canvas(self, timeout: int = 150_000) -> None:
    """Wait until a run node appears above the Flow canvas (the backend has
    BEGUN executing the run). Raises AssertionError naming the real cause."""
    try:
        self.run_node_label.first.wait_for(state="visible", timeout=timeout)
    except PlaywrightTimeoutError as err:
        raise AssertionError(
            f"The pipeline run never started — no run node appeared on the "
            f"canvas within {timeout} ms after sending the chat message "
            f"(the backend did not begin executing the run)."
        ) from err

def wait_for_run_details_status(self, expected: str, timeout: int = 90_000) -> None:
    """Wait until the OPEN Run Details panel's status badge reaches *expected*
    (read from `data-status`, the app's own state attribute)."""
    try:
        expect(self.run_details_status_badge).to_have_attribute(
            "data-status", expected, timeout=timeout
        )
    except AssertionError as err:
        raise AssertionError(
            f"The pipeline run did not complete — Run Details status is still "
            f"{self.get_run_details_status()!r} after {timeout} ms "
            f"(expected {expected!r})."
        ) from err
```

**Rules the implementer must not break:**

1. **Never re-open the panel in Step 5.** Confirmed live: with the Run Details
   MUI Dialog open, a click on `pipeline-run-node-label` is intercepted
   (`MuiDialog-container … subtree intercepts pointer events`) and retries until
   timeout. Step 5 keeps `expect(pipeline_page.run_details_panel).to_be_visible()`
   and `get_run_details_status() == "Completed"` — both now guaranteed by (c),
   no longer a race — and drops only the `open_run_details_panel()` call.
2. **Drop `wait_for_embedded_chat_response()` from THIS spec only.** It asserted
   nothing (§ A); the replacement is strictly stronger. Do not change the helper
   itself — that is framework-scale work across 20 caller files and is out of
   scope for this card (escalated to the lead as an observation).
3. **`allure.step` wrapping, the `#1267` console filter, and every Step 1/2/3/5/6
   assertion stay byte-for-byte as they are.** No assertion may be softened,
   removed, or converted to a soft assert by this repair.
4. Timeouts are *budgets for an honest failure*, not sleeps: every wait above is
   a condition wait that FAILS when the condition is not met.

## Coverage Map

### Axis 1 — Case coverage

| Case element | Expected result | Covered by (AFS step) | Asserted where | Disposition |
|---|---|---|---|---|
| Precondition: user logged in | met | Preconditions | n/a (localhost auto-auth) | asserted — no drift |
| 1 Create a pipeline with a Code node | node exists on canvas | step 1 | step 1: `wait_for_node_on_canvas("code")` | asserted |
| 2 Code node script uses `elitea_client.get_user_data()` | script accepted | step 2 | step 2: `get_code_node_value()` | asserted — **live-correct as literally written, no CLARIFICATION needed (see Test Data note — distinct from ELITEA-2446's plain-assignment CLARIFICATION, since this script's last statement is a bare expression, not an assignment)** |
| 3 Set Output to a state variable and enable structured output | Output=`user_info`, toggle checked | step 3 | step 3: `get_code_node_output_value()` / `.is_checked()` | asserted |
| 4 Execute the pipeline | completes without error | step 4 | step 4 (REPAIRED 2026-09-09): `wait_for_embedded_chat_message_count()` + `wait_for_run_node_on_canvas()` + `wait_for_run_details_status("Completed")` | asserted — same observable, now on a wait that can actually FAIL, with a message naming the run rather than "element not found" (§ Repair Amendment § D) |
| 5 Verify Code node executes without errors in Run Details | timeline step `completed` | step 5 | step 5: `get_run_details_timeline_step_status(0)` (panel already open from step 4) | asserted — unchanged |
| 6 Verify Code node output state variable contains the user information | After value = user dict | step 6 | step 6: `get_run_details_state_after_value("user_info")` parsed as JSON, asserted for `email`/`name` presence | asserted |
| Expected Final State / Pass-Fail criteria | all steps complete, no errors | all steps | all steps | asserted |

### Axis 2 — Analyst additions

- Step 5's label assertion (`"pyodide"` substring, not `"Code1"`) — *added: same
  confirmed-live Code-node timeline-label convention ELITEA-2446 already
  established; omitting it would leave the step's own verification incomplete
  (index-only, no label check).*
- Step 6's assertion parses the After value as JSON and checks key PRESENCE
  (`email`, `name`) rather than pinning exact field values — *added: the test-bot
  account's own fields (`last_login`, etc.) are time-varying and its non-identity
  fields could change between environments; the case's own text ("contains the
  user information") is a presence claim, not an exact-value claim.*
- Console-error assertion excluding the known `#1267` signature — *added: same
  reasoning as every other Run-Details-opening case in this suite
  (ELITEA-2446/2447/2450/2451/2452/2453) — confirmed live this session to recur
  identically (same `RunStateDialog.jsx` stack trace).*

## Cleanup

0. **2026-09-09 repair session:** created one throwaway pipeline
   (`sage2448probe`, id `10398`, project 399 "Private") from this AFS's own
   § Test Data YAML, executed it three times live, then **deleted it**
   (`PipelineAPI.delete_pipeline(10398)` → `DELETE
   .../application/prompt_lib/399/10398`, confirmed). No residue.
1. This session created one throwaway pipeline during live exploration
   (`autotest_2448_probe_test_scratch_probe`, id `8820`, project 399 "Private") to
   confirm `elitea_client.get_user_data()`'s live behavior (1 probe run, via a
   scratch pytest test using the project's own `pipeline_api`/`page` fixtures —
   deleted in the probe's own `finally:` block via
   `PipelineAPI.delete_pipeline()`, confirmed `DELETE .../application/prompt_lib/
   399/8820` succeeded). No residue left behind; the scratch test file itself was
   removed (never committed).
2. Implementer teardown: new fixture (see Automation Hints) built via
   `PipelineAPI.create_pipeline()` in setup, `PipelineAPI.delete_pipeline(pid)` in
   teardown — same pattern as `pipeline_llm_reads_state_via_code`/
   `pipeline_code_node_multi_var_dict_return`.

## Concrete Handles (discovered during exploration)

**Zero new testids needed — every element this case touches already has one from
ELITEA-2009 (Code node config) and ELITEA-2450/2451/2452 (Run Details panel) —
same zero-new-testid finding as ELITEA-2446/2447, which touch the identical Code
node config controls and Run Details panel. The 2026-09-09 repair adds NO new
testid either, by design: it reads the run's status off
`pipeline-run-details-status-badge`, which is already on EliteaUI `main`.**

**Provenance re-verified 2026-09-09 after `cd ../EliteaUI && git fetch origin`
(two-stage grep per `.agents/workflow.md` § Closure record):**

```
pipeline-run-node-label                        main:YES  testids:YES
pipeline-run-details-status-badge              main:YES  testids:YES
pipeline-run-details-panel                     main:YES  testids:YES
pipeline-run-details-timeline-step-            main:YES  testids:YES
pipeline-run-details-state-row-                main:YES  testids:YES
pipeline-run-details-state-value-after-        main:YES  testids:YES
pipeline-code-node-value                       main:YES  testids:YES
pipeline-code-node-output-select               main:YES  testids:YES
pipeline-code-node-structured-output-toggle    main:YES  testids:YES
pipeline-state-drawer-toggle-button            main:YES  testids:YES
chat-message-input                             main:YES  testids:YES
```

⚠️ The original table's `pipeline-code-node-output-select-combobox` and the
`on-automation/testids only` claim for `pipeline-state-drawer-toggle-button`
were both wrong: the real testid is `pipeline-code-node-output-select` (no
`-combobox` suffix — that was a role name), and every testid this case uses is
on **`main`**. Corrected here from the verified output above.

| Element | Recommended Locator | Provenance | Fallback |
|---|---|---|---|
| Code node Output select, Value field, Structured output toggle | `pipeline-code-node-output-select-combobox` / `pipeline-code-node-value` / `pipeline-code-node-structured-output-toggle` | **on-`automation/testids` ✓** — added by ELITEA-2009, reused unmodified via `PipelineDetailPage.get_code_node_output_value()` / `get_code_node_value()` / `code_node_structured_output_toggle`. Confirmed live this session (1 probe run). | none needed |
| **Run status badge (the repair's completion observable)** | `pipeline-run-details-status-badge` — state read from its `data-status` attribute (`In progress` / `Completed`), never from its text | **on-`main` ✓ and on-`automation/testids` ✓** (verified 2026-09-09, block above). `RunStatus.jsx:15-16` renders `data-testid` + `data-status={status}` — the sanctioned "testid = identity, state via `data-*`" shape (`.agents/testing.md` § Locator policy). Confirmed live: updates IN PLACE while the panel is open, `In progress` → `Completed`. Existing page-object field `run_details_status_badge`. | none — no fallback is permitted, and none is needed |
| **Run node label (the repair's run-STARTED observable)** | `pipeline-run-node-label` | **on-`main` ✓ and on-`automation/testids` ✓** (verified 2026-09-09). `RunStateNode.jsx:93`. ⚠️ **Semantics correction:** this element appears when the run STARTS (`AgentStart`/`StartTask` socket event → `parseRunsByEvent.helpers.js:69-81`), NOT when it finishes — it is present throughout `In progress`. Its visibility is therefore a run-STARTED signal only; the original spec used it as a proxy for completion, which it never was. | none needed |
| Run Details panel, timeline step selector (index 0), state row/value boxes | `pipeline-run-details-panel`, `pipeline-run-details-timeline-step-0`, `pipeline-run-details-state-row-user_info`, `pipeline-run-details-state-value-after-user_info` | **on-`automation/testids` ✓** — added by ELITEA-2450/2451/2452, reused unmodified via `PipelineDetailPage.open_run_details_panel()` / `select_run_details_timeline_step(0)` / `expand_run_details_state_row()` / `get_run_details_state_after_value()`. Confirmed live: `user_info`'s row correctly renders and expands with the full user-data JSON. | none needed |
| STATE panel toggle / variable-name text | `pipeline-state-drawer-toggle-button` / (row name text via `get_state_variable_name_text`) | **on-`automation/testids` only** (awaiting human promotion to `main`) — pre-existing (ELITEA-2042), reused unmodified. Confirmed live: `user_info` row name renders correctly for the JSON-typed state variable. | none needed |

## Network Behavior
- `POST .../elitea_core/applications/prompt_lib/{project}` — pipeline creation.
- Pipeline execution and all Run Details data (timeline, per-step state) arrive
  entirely over Socket.IO, same as every other Run Details case in this suite
  (ELITEA-2446/2450/2451/2452/2453) — no dedicated REST endpoint for
  timeline/state observed for this pipeline either.
- `DELETE .../elitea_core/application/prompt_lib/{project}/{pipeline_id}` —
  fires on pipeline deletion; confirmed live (probe cleanup, this session).
- `elitea_client.get_user_data()` itself is a Code-node-internal (sandbox-side)
  call — it does NOT appear as a separate browser-visible network request; its
  result only becomes observable via the Run Details state panel after the run
  completes, exactly as for `elitea_state.get(...)` in ELITEA-2446.

## Known Defects Found During Exploration

**2026-09-09 repair pass:** still **no product defect blocking this case** — the
run executes and completes correctly, and the case's own observable
(`user_info` = the authenticated user's data) is produced by the system. The
`#2076` CI red is a **test-wait defect** amplified by **DEV run-start latency**
(§ Repair Amendment § A/B/C). One unrelated product-side observation (the
embedded-chat answer bubble never finalises for this Code-node-only pipeline)
is recorded in § Repair Amendment § C and reported to the lead — **not filed by
this pass**, because distinguishing "correct: no chat answer to emit" from "UI
finalisation gap" needs an LLM-node control run that is outside this card.

**Original 2026-08-09 finding (unchanged): No product defect found. No case-text
CLARIFICATION needed** — unlike
ELITEA-2446/2447, this case's own literal script text (a bare name-reference last
statement, not an assignment) is confirmed live to work exactly as written; see
the Test Data note for why this differs from ELITEA-2446/2447's plain-assignment
CLARIFICATION.

`elitea_client.get_user_data()` (the case's literal spelling) IS confirmed valid —
NOT a case-text drift. `.claude/skills/elitea-pipeline/references/workflows.md`
§ "Code Node Special Capabilities" documents `alita_client.get_user_data()` (the
`alita_`-prefixed alias) under **User:**; this session's live exploration used the
case's own `elitea_client.get_user_data()` spelling and it correctly resolved and
returned the authenticated test user's full data dict (`email`, `name`, `id`,
`personal_project_id`, `api_url`, `default_context_management`,
`default_summarization`, `personalization`, `suspended`, `last_login`) — both
spellings are aliases of the same runtime-injected client, matching
`.claude/skills/elitea-pipeline/SKILL.md`'s own note ("`alita_client` is an alias
for some operations... prefer `elitea_*`") and the bundled
`examples/getuserdetails.yaml` reference pipeline (which uses the `elitea_client`
spelling identically).

## Blocked Steps

None. All 6 case steps were exercised live this session (1 probe run, pipeline id
`8820`) — the script worked on the first attempt with no iteration needed, unlike
ELITEA-2446/2447's multi-probe discovery process.

## Automation Hints

- Framework: Playwright + pytest, testid-only `LocatorDescriptor`. Zero new
  testids needed (see Concrete Handles).
- **New fixture needed**: no existing fixture builds a single-Code-node pipeline
  calling `elitea_client.get_user_data()`. Recommend
  `pipeline_code_node_elitea_client_user_info` (or similar) in
  `automation/fixtures/data_fixtures.py`, built via `PipelineAPI.create_pipeline()`
  with the raw YAML `instructions` string in this AFS's § Test Data — mirrors
  `pipeline_llm_reads_state_via_code`'s create/yield/delete pattern (NOT
  `create_pipeline_with_nodes()`, which has no `state:` support). This is the
  SIMPLEST fixture in the Code-node family so far — one node, no chained
  transition to get wrong, no LLM-nondeterminism to route around.
- **Code node script convention for THIS case**: a bare NAME-reference expression
  (`user_info`) as the last statement works identically to a bare dict-LITERAL
  expression (ELITEA-2446/2447's convention) — both are non-assignment expression
  statements, and the runtime routes either into the declared `output:` variable
  when `structured_output: true`. Do NOT rewrap this case's script into a dict
  literal "to be safe" — the case's own two-line form (`user_info = ...` then
  bare `user_info`) is the live-correct, already-confirmed shape; keep it as
  specified.
- **Parse the After value as JSON** (`json.loads(get_run_details_state_after_value(...))`)
  before asserting on individual keys — the panel renders it as a JSON-serialized
  string, not a pretty-printed dict repr (confirmed live: the raw string starts
  with `{"api_url":...`).
- **Reuse ELITEA-2452's Run Details Before/After methods unmodified**:
  `open_run_details_panel()`, `select_run_details_timeline_step(0)` (index 0 —
  the ONLY timeline entry for this single-node pipeline, unlike ELITEA-2446/2447's
  2-node pipelines which use index 1), `get_run_details_selected_timeline_step_id()`,
  `expand_run_details_state_row()`, `get_run_details_state_after_value()`,
  `get_run_details_timeline_step_status(0)`.
- Wait strategy (**SUPERSEDED 2026-09-09** — the original bullet below was the
  direct cause of `#2076`; kept for traceability):
  ~~`wait_for_embedded_chat_response()` after sending the chat message, then
  `expect(pipeline_page.run_node_label).to_be_visible()` before opening Run
  Details.~~ Use the three-part wait in § Repair Amendment § D instead — the
  run's own state, read off testids that are already on EliteaUI `main`.
- `_surface.md` NOT updated with a new section this session — the confirmed
  behavior (bare name-reference last statement works; `elitea_client`/
  `alita_client` are aliases) is narrow enough to live in this AFS alone; nothing
  here contradicts or extends the existing Code-node-execution gotchas already
  documented against ELITEA-2446/2447 (which this AFS cites directly instead of
  duplicating).
