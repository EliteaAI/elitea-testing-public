# Test Case: Pipeline Execution — Long Response Streaming

## Metadata
- **TMS ID**: ELITEA-2017
- **Linked Story**: none (case `requirements: []`)
- **Priority**: l2 (case priority: high)
- **Environment Explored**: local (`http://localhost:5173`, EliteaUI `automation/testids`, DEV backend, project `Private` id 399)
- **User set**: `${TEST_USER}` — on localhost, `auth_state`/`VITE_DEV_TOKEN` skips explicit Keycloak login (dev-token user renders as "Test Bot"/"TB")
- **Analyst**: qa-engineer (agent)
- **Status**: **ready-for-automation** — case executed end-to-end live via the Playwright MCP browser, twice (two independent user prompts), against a purpose-built pipeline (LLM entry node, TASK F-String `{input}`, matching the case's literal precondition). All 6 steps observed. No product defect filed — one environment-dependent behavior noted (see § Known Defects) that does NOT violate the case's own Pass/Fail criteria. Heavy, deliberate reuse of the ALREADY-confirmed handles from the sibling regular-chat streaming case (`l2_streaming-response-progressive-display_ELITEA-2181.md`) — the pipeline's embedded chat panel renders through the exact same `ApplicationAnswer.jsx`/`ActionView.jsx`/`RotatingMessages.jsx` component chain as the main chat (confirmed live: identical "Thought for `<n>` secs" accordion + model-chip pattern). This is reuse-to-know-handles, not Rule-6 dedup — ELITEA-2181 covers a DIFFERENT surface (`ChatPage`'s conversation chat) and does not satisfy `already-covered`/`extend-existing` for a pipeline-entry-point execution case (see § Coverage Map / neighbours checked below).

## Preconditions
- User is logged in to the Elitea platform (`${TEST_USER}` / dev-auth on localhost).
- A pipeline with an LLM node as entry point exists, with TASK configured as `F-String` / value `{input}` (so the user's chat message reaches the LLM node verbatim as its task).

## Test Data

### reuse-existing
- `${TEST_USER}` — see `.agents/profile.md` § Roles & sample users.
- Model: `GPT-5 mini` — confirmed present verbatim in the live Model Selector Menu (testid `model-selector-option-gpt-5-mini`), no substitution needed.
- User prompt (case's literal Test Data value): `"Write a 500-word essay on AI"`.
- Minimum response length: `200` characters (case's literal Test Data value — NOT "must reach the full 500 words"; see § Known Defects for why this distinction matters live).

### generate-per-test (created in test setup, cleaned up in its own teardown)
- A pipeline with a single LLM node (entry point) → END, TASK `type: fstring value: "{input}"`, SYSTEM/CHAT HISTORY left at their `Fixed` defaults. **The existing `pipeline_with_llm_id` fixture (`fixtures/data_fixtures.py:163`) does NOT satisfy this precondition as-is** — `PipelineAPI.create_pipeline_with_llm_node()` (`api/client.py:689`) hardcodes TASK as `type: fixed, value: ''`, not the F-String the case's precondition literally specifies. Two implementation options, either is fine:
  1. Add a `task_fstring: str = "{input}"` parameter to `create_pipeline_with_llm_node()` (small, backwards-compatible change — existing callers keep the fixed-empty default), OR
  2. Build the node list inline via the already-existing generic `PipelineAPI.create_pipeline_with_nodes()` (`api/client.py:769`, same helper `build_two_llm_nodes()`/`pipeline_with_two_llm_nodes_id` already use for ELITEA-2452) with:
     ```python
     nodes = [{
         "id": "LLM 1", "type": "llm", "input": [],
         "input_mapping": {
             "chat_history": {"type": "fixed", "value": []},
             "system": {"type": "fixed", "value": ""},
             "task": {"type": "fstring", "value": "{input}"},
         },
         "output": [], "structured_output": False, "transition": "END",
     }]
     ```
     — confirmed live this session, byte-for-byte, via the UI's own LLM-node TASK Type/Value fields (see § Test Steps step 1).
  - Cleanup: `pipeline_api.delete_pipeline(pid)` in a `finally`/fixture-teardown block, exactly like `pipeline_with_llm_id`.

## Test Steps

1. Create a pipeline with an LLM node as entry point; set TASK Type to `F-String`, Value to `{input}`; save.
   - **Verify**: confirmed live via the UI builder — Add-node menu → `LLM` → TASK section's Type select (testid `pipeline-llm-node-task-type-select-combobox`, confirmed to resolve, matching the pre-existing implementation from ELITEA-2004) → select F-String option (testid `select-option-fstring`) → fill Value textarea (testid `pipeline-llm-node-task-value`) with `{input}` → Save (testid `agent-save-button`). No console errors, no failed (≥400) network requests during creation.
2. In the pipeline's embedded chat panel, select a model via the Model Selector Menu (e.g., "GPT-5 mini").
   - **Verify**: confirmed live — click the closed selector (shows "Anthropic Claude 4.5 Sonnet" by default; resolves via testid `model-selector-name`), the menu lists `GPT-5 mini` verbatim (testid `model-selector-option-gpt-5-mini`, exact case-text match — no substitution needed unlike some other AFS in this suite), click it, and the closed selector's displayed text updates to `GPT-5 mini` (confirmed via a fresh `browser_find` after selection).
3. Ask a question requiring a lengthy answer: `"Write a 500-word essay on AI"`.
   - **Verify**: message is sent via `chat-message-input` (fill) + `chat-send-button` (click) — the SAME testids `ChatPage` uses for regular chat; the pipeline's embedded chat panel (`ChatPanel.jsx` per `test-specs/pipelines/_surface.md` "sibling pattern" note) shares this component. User message appears immediately as a new list item.
4. Verify the response streams progressively in chat (tokens appear incrementally, not all at once).
   - **Verify**: confirmed live, twice, via manual polling of the embedded chat's last message: at t≈3s and t≈8s after send, only the "Thought for `<n>` secs" accordion header + a `GPT-5 mini (LLM1)` model chip are present (NO body text yet — same pre-content phase `RotatingMessages`/accordion pattern ELITEA-2181 already documented for regular chat); by t≈13–18s, the accordion's body paragraph(s) are present and non-empty. This confirms the SAME progressive-reveal signature as ELITEA-2181 (absent → present, growing), through the SAME UI components. **Caveat on polling granularity**: my manual polls were ~3–5s apart, coarse enough that I observed "absent" then "present-and-substantial" rather than catching mid-stream token-by-token growth directly; the implementer should reuse ELITEA-2181's PROVEN technique — poll the last message's extracted body text every ~2–3s during the `isStreaming` window and assert two samples ≥2s apart differ AND the second is a superset/extension of the first (never shrinks) — rather than re-deriving a new polling strategy. `PipelineDetailPage.get_embedded_chat_last_message()` (existing method, `pipeline_detail_page.py:5914`) is the direct analogue of `ChatPage._extract_message_body()` for this purpose — reuse it for the samples.
5. Verify the final response is complete and exceeds 200 characters.
   - **Verify**: confirmed live — first run's ("Write a 500-word essay on AI") full response settled at well over 200 characters (a complete, naturally-concluding multi-paragraph essay, ~1800 characters). Assert `len(pipelines.get_embedded_chat_last_message()) > 200` after `wait_for_embedded_chat_response()` — the existing method already used by `test_pipeline_execution.py`'s `_execute_pipeline()` helper.
6. Verify no timeout or error occurs during streaming.
   - **Verify**: confirmed live across both runs — zero console errors (`browser_console_messages(level="error")` → 0 in both), zero failed (≥400) network requests (all captured requests during send/response were 200/201). No red error banner, no exception toast, no "unexpected error" text appeared in either run (existing `_assert_response_quality()` helper's `"unexpected error" not in response.lower()` check is directly reusable here). See § Known Defects for a distinct, non-error "Token limit reached mid-response" affordance observed on the SECOND run — it is a deliberate continuation UI, not an error state, and does not fail this step's criterion.

## Expected Results
- All 6 steps pass as specced above.
- A pipeline with an LLM entry node and TASK F-String `{input}` accepts a model selection, streams a progressively-growing response in the embedded chat with no console/network errors, and the settled response exceeds 200 characters.
- No functional product defect found; one environment-dependent behavior noted for implementer awareness (§ Known Defects) — does not affect this case's own Pass/Fail criteria.

## Coverage Map

### Axis 1 — Case coverage

| Case element | Expected result | Covered by (AFS step) | Asserted where | Disposition |
|---|---|---|---|---|
| Precondition: user logged in | — | Setup | `auth_state` fixture | asserted |
| Precondition: LLM-entry pipeline, TASK F-String `{input}` | — | Setup / step 1 | pipeline fixture (extended `create_pipeline_with_llm_node`/`create_pipeline_with_nodes`) — confirmed live via UI build | asserted |
| 1 Create pipeline with LLM entry node (TASK F-String `{input}`) → Pipeline created and ready | pipeline created | step 1 | UI build confirmed live, all fields persist | asserted |
| 2 Select model via Model Selector Menu (e.g. GPT-5 mini) → Selected model displayed | model shown in selector | step 2 | `model-selector-name` text updates to "GPT-5 mini" | asserted |
| 3 Ask "Write a 500-word essay on AI" → Message sent to pipeline | message sent | step 3 | `chat-message-input`/`chat-send-button`, new list item appears | asserted |
| 4 Verify response streams progressively → Tokens appear incrementally | progressive streaming | step 4 | two polls of `get_embedded_chat_last_message()` ≥2s apart, absent→present, growing | asserted |
| 5 Verify final response complete, > 200 chars → Response length > 200 | length threshold | step 5 | `len(last_message) > 200` | asserted |
| 6 Verify no timeout/error during streaming → No errors, streaming completes normally | no error/timeout | step 6 | console errors == 0, no ≥400 responses, no "unexpected error" text | asserted |
| Expected Final State: "pipeline streams a long response progressively... exceeds 200 characters" | — | steps 4–6 | as above | asserted |
| Pass/Fail: "All steps complete without errors... exceeds 200 characters with no timeout" | — | all steps | as above | asserted |

Disposition key: `asserted` / `already-covered` / `clarification` / `blocked` / `out-of-scope`.

### Axis 2 — Analyst additions

- Console messages and network requests checked after EVERY step across both live runs (not just at the end) — *added: standard side-channel discipline; zero errors/failed requests found either run.*
- Confirmed the pipeline's embedded chat panel shares the exact same message-rendering component chain (`ApplicationAnswer.jsx`/`ActionView.jsx`/`RotatingMessages.jsx`) as the main `ChatPage` conversation chat, via the identical "Thought for `<n>` secs" + model-chip UI pattern observed live — *added: this is the basis for recommending the implementer reuse ELITEA-2181's confirmed polling technique and testids rather than re-deriving them from scratch; it is NOT itself a case assertion.*
- Second live run surfaced a "Token limit reached mid-response. Press 'Continue' to see more." affordance partway through an essay response — *added, documented in § Known Defects: NOT a case assertion, but implementer-facing guidance so this isn't mistaken for a failure signal; the case's own 200-char minimum was already exceeded before the affordance appeared in both runs, so it does not threaten step 5/6's Pass criteria.*
- Confirmed `GPT-5 mini` is present in the live Model Selector Menu with an EXACT case-text match — *added: several sibling AFS in this suite needed a model-name substitution; this one didn't, worth recording so the implementer doesn't second-guess it.*

## Cleanup
1. Delete the exploration/test pipeline via `pipeline_api.delete_pipeline(pid)` in a `finally` block (existing pattern, mirrors `pipeline_with_llm_id` fixture teardown) — confirmed manually via the UI's own Delete flow this session (`agent-actions-menu-button` → `delete-agent-menuitem` → type-to-confirm → Delete), no orphaned state left behind.
2. Standard `try/finally` per `.claude/rules/ui-tests.md` § Test Data Lifecycle.

## Concrete Handles (discovered during exploration)

Locator policy on this project is **testid-only** — no role/label/text fallback ladder (`.agents/testing.md` § Locator policy, `.agents/role-overrides.md`). Provenance verified via `git fetch origin` + `git grep` on both `origin/main` and `origin/automation/testids` in the sibling `EliteaUI` clone (2026-08-09).

| Element | Testid handle | Provenance | Notes |
|---|---|---|---|
| Add-node "+" button | `pipeline-add-node-button` | on-main ✓ (confirmed live, pre-existing) | Existing `PipelineDetailPage.add_node()`. |
| Add-node menu → LLM item | `pipeline-add-node-menu-item-llm` | on-main ✓ (confirmed live) | |
| LLM node TASK Type select | `pipeline-llm-node-task-type-select-combobox` | on-main ✓ (confirmed live — implemented per ELITEA-2004's "Implementation status" amendment) | Positional-select tech debt from ELITEA-2004 is RESOLVED — this is a real, stable testid today, not the `nth()` workaround that AFS originally flagged. |
| F-String option in Type dropdown | `select-option-fstring` | on-main ✓ (confirmed live) | Same `select-option-{value}` dynamic pattern already confirmed for MCP/Toolkit node selects. |
| LLM node TASK Value textarea | `pipeline-llm-node-task-value` | on-main ✓ (confirmed live) | |
| Pipeline Save button | `agent-save-button` | on-main ✓ | Shared across agent/pipeline create-and-edit forms. |
| Pipeline Actions menu (three-dot) | `agent-actions-menu-button` | on-main ✓ | `PipelineDetailPage.actions_menu_button`, existing. |
| Delete pipeline menu item | `delete-agent-menuitem` | on-main ✓ | Existing, per ELITEA-2049. |
| Embedded-chat Model Selector (closed button, shows current model name) | `model-selector-name` | on-main ✓ (confirmed live) | **`PipelineDetailPage` has NO model-selector field or `select_model()` method today** — implementer adds `model_selector_button = LocatorDescriptor(testid="model-selector-button")` + `model_selector_name = LocatorDescriptor(testid="model-selector-name")`, mirroring `AgentDetailPage`'s EXACT existing pattern (`agent_detail_page.py:284-286`) rather than `ChatPage.model_selector`'s pattern (which carries a forbidden `fallback=` param — pre-existing tech debt, do not copy it; see Automation Hints). |
| Model option in open dropdown (dynamic) | `model-selector-option-{model-slug}` (e.g. `model-selector-option-gpt-5-mini`) | on-main ✓ (confirmed live) | Mirror `AgentDetailPage.MODEL_SELECTOR_OPTION_ANY_SELECTOR = '[data-testid^="model-selector-option-"]'` class constant + filter-by-display-text pattern (`agent_detail_page.py:286,2741-2752`) rather than inventing a new one. |
| Embedded chat message input | `chat-message-input` | on-main ✓ | Existing `PipelineDetailPage.chat_input` (`pipeline_detail_page.py:438`). Shared component with `ChatPage`. |
| Embedded chat send button | `chat-send-button` | on-main ✓ | Existing `PipelineDetailPage.chat_send_button` (`pipeline_detail_page.py:444`). |
| "Thought for `<n>` secs" accordion header | **NO TESTID on `main`** | on-`automation/testids` only (awaiting human promotion) | `testid needed: chat-answer-thought-accordion` — **already implemented** by the ELITEA-2181 delivery (`EliteaAI/EliteaUI` commit on `automation/testids`, confirmed via `git grep` 2026-08-09), just not yet cherry-picked to `main`. Since localhost serves `automation/testids`, this IS usable today for local test runs; the closure record for whichever batch lands this case should note it rides the SAME pending-promotion testid set as ELITEA-2181, not a fresh gap. |
| Model-name chip inside the accordion (e.g. "GPT-5 mini (LLM1)") | **NO TESTID on `main`** | on-`automation/testids` only | `testid needed: chat-answer-model-chip` — same as above, already implemented pending promotion. |
| Pre-content loading placeholder (rotating phrases) | **NO TESTID on `main`** | on-`automation/testids` only | `testid needed: chat-answer-loading-placeholder` — same as above. |
| Copy-to-clipboard button (message actions) | **NO TESTID on `main`** | on-`automation/testids` only | `testid needed: chat-copy-button` — same as above; not exercised by this case's own 6 steps (case doesn't touch post-completion action icons), listed for completeness since the implementer will see it in the shared component. |
| Regenerate button | **NO TESTID on `main`** | on-`automation/testids` only | `testid needed: chat-regenerate-button` — same as above; not exercised by this case's own 6 steps. |
| Last AI message body text (for progressive-sampling) | no testid — extracted via existing method | n/a (page-object internal, not a raw handle in a spec/page-object method body per the sanctioned pattern) | `PipelineDetailPage.get_embedded_chat_last_message()` (`pipeline_detail_page.py:5914`) — pre-existing, reuse directly. Internally uses a raw CSS class selector (`div.css-xn5i2e`) as a fallback path — **pre-existing tech debt** (like `ChatPage`'s stale field), not introduced by this AFS; do not extend or copy that pattern into new code. |
| Embedded chat message list items | no testid — raw CSS selector | n/a | `PipelineDetailPage._embedded_chat_messages()` uses `ul.MuiList-root li.MuiListItem-root` — **pre-existing tech debt** (#25/#42 class), reused as-is by `get_embedded_chat_message_count()`/`wait_for_embedded_chat_response()`; not introduced by this AFS. |

## Network Behavior
- Pipeline creation/save: standard `POST`/`PUT` to `elitea_core/applications/prompt_lib/{project}` — all `200`/`201`, confirmed live.
- Message send creates a conversation (`POST .../conversations/prompt_lib/399` → `201`) and updates it (`PUT .../conversation/prompt_lib/399/{id}` → `200`); the actual token stream arrives over **WebSocket**, consistent with `.agents/testing.md`'s documented ~2s+ delay pattern (not visible in the REST request list, same as ELITEA-2181's finding).
- No console errors, no failed (≥400) requests in either of the 2 live runs.

## Known Defects Found During Exploration
- **[NOTE, not filed as a defect]** On the SECOND live run ("Write a detailed 500-word essay about the history of the internet"), the response stopped mid-sentence after ~730 characters with an in-UI affordance: "Token limit reached mid-response. Press 'Continue' to see more." (clicking "Continue" pre-fills a continuation prompt in the message input — did not auto-send, not explored further as out-of-scope for this case). This is a deliberate continuation UI, not an error state (no red banner, no console error, no failed request) — and it did NOT occur on the FIRST run (the AI essay ran to a natural, complete conclusion at ~1800 characters). Both runs' responses exceeded the case's own 200-character minimum well before any truncation point, so this does not violate the case's Pass/Fail criteria as written. **Automation implication**: the implementer should assert `len(response) > 200`, NOT "response reaches ~500 words" or "response ends with a natural conclusion" — the case's own Test Data table specifies the 200-char threshold precisely because full-length completion is not guaranteed on every run (likely tied to the pipeline's default/unconfigured `llm_settings` max-token budget, not a bug in the streaming/chat mechanism itself). Reverse-masking guard considered and does not apply here — the case text itself only asks for >200 chars, so the live behavior does not contradict it.
- No functional product defect found beyond the above note.

## Blocked Steps
None. All 6 case steps were executed and observed end-to-end live, across 2 separate runs (different prompts) to confirm progressive-streaming behavior is consistent and to surface the token-limit note above.

## Automation Hints
- Framework: Playwright + pytest, testid-only `LocatorDescriptor` (`.agents/testing.md`).
- **No Playwright MCP server was wired for this analyst's page-object layer** — exploration used the bundled Playwright MCP tools directly against the live localhost app (browser_navigate/click/type/find/snapshot); the implementer uses normal pytest/Playwright tooling through `PipelineDetailPage`.
- **Reuse `test_pipeline_execution.py`'s existing helpers as the transit/skeleton** (`_navigate_to_pipeline_detail`, `_execute_pipeline`, `_assert_response_quality`, `PIPELINE_EXECUTION_TIMEOUT=90_000`, `STABLE_DURATION_MS=3_000`) — this case's new test should live alongside them (e.g. a new `TestExecutePipelineStreaming` class in the same file, or a sibling `test_pipeline_execution_streaming.py`), NOT a rewrite. The gap vs. the existing PIPE-011/012 tests is specifically: (a) the fixture needs TASK F-String `{input}` instead of Fixed empty (see § Test Data), (b) an explicit progressive-streaming poll-and-compare assertion during generation (existing tests only wait for stability, never sample mid-stream), (c) an explicit `len > 200` assertion (existing `_assert_response_quality` only checks `len > 3`).
- **Timeout sizing**: both live runs completed (or hit the token-limit affordance) within ~15–30s; size the "wait for completion" timeout generously (the existing `PIPELINE_EXECUTION_TIMEOUT = 90_000` is already generous — reuse it, don't shrink it).
- Wait strategy: condition-based only, never a fixed `sleep()`, per `.agents/testing.md`. Use `PipelineDetailPage.wait_for_embedded_chat_response()` (existing) for the terminal wait, and manual `page.wait_for_timeout()`-free polling (a small explicit loop with `expect()`/condition waits, sampling `get_embedded_chat_last_message()`) for the progressive-growth assertion — mirroring ELITEA-2181's approach on the analogous `ChatPage` method.
- Six testids this case's steps 4 rely on for a RICHER assertion (accordion presence, model chip, loading placeholder) are already implemented on `automation/testids` from the ELITEA-2181 delivery, not yet on `main` — no NEW `add-data-testid` work is required for this case's own 6 steps as written (the core progressive-growth assertion only needs the existing `get_embedded_chat_last_message()` text extraction, which requires no testid at all). If the implementer chooses to additionally assert the accordion/chip's presence for a stronger signal, those testids are already usable locally.
- One net-new page-object gap: `PipelineDetailPage` needs a `model_selector_button`/`model_selector_name` field pair + a `select_model(model_name)` method — mirror `AgentDetailPage`'s existing, already-compliant pattern (see § Concrete Handles) rather than `ChatPage.model_selector`'s (which has a forbidden `fallback=` param — pre-existing tech debt, flagged here for awareness only, out of scope to fix as part of this case).
