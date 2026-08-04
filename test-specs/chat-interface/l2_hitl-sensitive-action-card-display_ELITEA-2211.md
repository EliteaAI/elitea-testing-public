# Test Case: Chat – HITL Authorization – Sensitive Action Authorization Card Displays When Toolkit Called Directly

## Metadata
- **TMS ID**: ELITEA-2211
- **Linked Story**: none
- **Priority**: l2
- **Environment Explored**: local (`http://localhost:5173`) for the toolkit-participant / message / chip flow; **source-verified** (`EliteaUI/src/[fsd]/features/chat/ui/chat-hitl-actions/ChatHitlActions.jsx`) for the sensitive-action card itself, since the trigger precondition cannot be set up on localhost — see § Preconditions
- **User set**: `${TEST_USER}` (dev-token bypass on localhost)
- **Analyst**: qa-engineer (cluster run, ELITEA-2211..2215, 2026-08-03)
- **Status**: ready-for-automation

## Preconditions
- An Artifact-type toolkit exists with `delete_file` in its `selected_tools`
  (`ToolkitAPI.create_artifact_toolkit()` already includes it — no new
  fixture shape needed, reuse `artifact_toolkit`).
- **`artifact` toolkit-type's `delete_file` tool is marked as a Sensitive
  Action Tool** via Admin UI Guardrails (`GuardrailsAdminPage.add_sensitive_tool("artifact", "delete_file")`
  + `save_configuration()` — exact pattern already used by
  `tests/ui/admin/test_guardrails_live_reload.py::TestSensitiveToolLiveReload`
  for the `github`/`get_issue` pair).
- **CONFIRMED ENVIRONMENT LIMITATION (not a defect — pre-existing, already
  documented in this repo):** the Admin Guardrails route
  (`${ELITEA_URL}/admin/app/configuration#guardrails`) returns **"Page not
  found"** on `localhost:5173` — verified live this pass (`page.goto(...)`,
  body text literally `"Page not found. Try Home page"`, screenshot on
  file). This matches the EXISTING suite's own annotation:
  `tests/ui/admin/test_guardrails_cleanup_only.py` and
  `test_guardrails_live_reload.py` are both tagged `pytest.mark.guardrails`
  specifically because "the Admin UI isn't served on localhost" (verbatim
  comment, `test_guardrails_cleanup_only.py:15-19`). **This case's
  precondition requires the same marker and the same CI-targets-a-deployed-env
  execution path as that existing suite — it is not a new gap, it is the
  identical established gap the project already has a marker for.**
  Implementer: mark the new test(s) `pytest.mark.guardrails` (excluded from
  the local dev loop via `-m "not guardrails"`, runs in CI against a
  deployed env where the Admin UI IS served) and follow
  `TestSensitiveToolLiveReload`'s `admin_page` fixture pattern.
- **Sensitivity is toolkit-TYPE scoped, not per-toolkit-instance** — `add_sensitive_tool("artifact", "delete_file")`
  marks `delete_file` sensitive for **every** artifact toolkit in the
  project, not just this case's fixture toolkit. This is a real,
  project-wide side effect: any other suite that calls `delete_file` on
  ANY artifact toolkit while this flag is set will unexpectedly hit the
  authorization card. Cleanup (`remove_sensitive_tool` + `save_configuration`)
  in a `finally`/fixture-teardown is not optional — see
  `TestSensitiveToolLiveReload`'s own Step 7 for the exact pattern to copy.
- No agent is used — the toolkit is added directly as a chat participant
  (main `/chat` page, "+ > Toolkits" flow, not `/` slash-mention).

## Test Data
### generate-per-test (in test setup, cleaned up in its own teardown)
- Artifact bucket: `ArtifactAPI.create_bucket(f"autotest-hitl-{run_id}")`
- Artifact toolkit: `ToolkitAPI.create_artifact_toolkit(name=f"autotest-hitl-tk-{run_id}", bucket_name=<above>)`
  — confirmed live this pass (bucket `p--{project_id}.autotest-hitl-749815`,
  toolkit id `2334`; both created via `ArtifactAPI`/`ToolkitAPI` using the
  Bearer-token fallback, no browser cookies needed — `ELITEA_API_TOKEN` is
  populated in `.env.test`).
- Message: `"use delete_file toolkit to remove from the bucket all files"`
  (case's literal text) — **CONFIRMED CASE-TEXT AMBIGUITY, not a defect**:
  live-tested this exact string against a toolkit connected to a single,
  empty bucket and the LLM did **not** attempt the tool call at all — it
  asked a clarifying question instead ("You have 588 buckets in your
  project... which bucket(s)?"), because "the bucket" is ambiguous when the
  project has many buckets (**test-data-hygiene finding**: 588 buckets is
  itself accumulated pollution — see Automation Hints). **Implementer must
  use an unambiguous message that names the bucket explicitly**, e.g.
  `f'Use delete_file toolkit to delete a file named "{filename}" from bucket "{bucket_name}". Execute the tool now, do not ask for clarification.'`
  — confirmed live this pass to reach a real tool-call attempt (see
  ELITEA-2215's AFS, same message shape, same toolkit).

## Test Steps
1. Create the artifact bucket + toolkit (setup, not a case step).
2. Mark `artifact`/`delete_file` sensitive via Admin UI Guardrails; save.
3. Navigate to `/chat` (new conversation), add the toolkit as a participant
   via "+ > Toolkits" (`ChatPage.add_toolkit_participant(toolkit_name)` —
   existing legacy method, confirmed live this pass).
   - **Verify**: toolkit appears in PARTICIPANTS (confirmed live: toolkit
     name shows in the "+" menu's popper and the message composer's model
     row after selection).
4. Send the unambiguous delete-file message naming the bucket explicitly.
   - **Verify**: "Thought for X secs" accordion appears (`chat-answer-thought-accordion`,
     confirmed live, e.g. "Thought for 14 secs").
5. Verify the Sensitive Action Authorization card appears.
   - **Verify**: `[data-testid="sensitive-action-panel"]` becomes visible
     (source-confirmed testid — `ChatHitlActions.jsx:132`; the card ONLY
     renders this testid when `guardrail_type` is `sensitive_tool` /
     `parallel_sensitive_tools` — its mere presence, vs the OTHER container
     testid `chat-hitl-actions-panel`, IS the "sensitive" signal; no need to
     assert the orange CSS border by computed style).
6. Verify the heading text.
   - **Verify**: panel's text contains "Sensitive Action Authorization
     Required" (source-confirmed literal string, `ChatHitlActions.jsx:139`
     — rendered with a leading "⚠️" emoji, in `palette.warning.main` color
     via inline `sx`, not a CSS class name to assert on).
7. Verify "Agent is about to perform:" + the tool name.
   - **Verify**: panel's text contains "Agent is about to perform:"
     (literal, `ChatHitlActions.jsx:146`) and the resolved action name
     (`hitlInterrupt.action_label || hitlInterrupt.tool_name`,
     `ChatHitlActions.jsx:152`). **Format unverified live** (precondition
     could not be reproduced locally — see § Preconditions) — do not
     hardcode the case's illustrative `"aaa.delete_file"` dotted format;
     assert the fixture's actual `tool_name` (`"delete_file"`) is present
     as a substring instead of the exact literal case example.
8. Verify all three buttons render.
   - **Verify**: Authorize (testid `sensitive-action-authorize-button`,
     source-confirmed, `ChatHitlActions.jsx:166`, `variant="positive"` =
     green), Block (**no testid today** — `ChatHitlActions.jsx:175`,
     `variant="alarm"` = red; needs `add-data-testid`, see § Concrete
     Handles), Block with Comment (**no testid today** — collapsed-state
     trigger button in `BlockWithCommentControl.jsx:73`, `variant="secondary"` =
     gray; needs `add-data-testid`).

## Expected Results
- HITL authorization card (`sensitive-action-panel`) appears with the
  correct heading, action-name block, and exactly three action controls.
- No console/JS errors during the flow.

## Coverage Map

| Case element | Expected result | Covered by (AFS step) | Asserted where | Disposition |
|---|---|---|---|---|
| Precondition: toolkit configured with HITL authorization | sensitivity applies | setup steps 1–2 | `GuardrailsAdminPage.add_sensitive_tool` + `save_configuration` | asserted *(env-gated, see § Preconditions)* |
| 1 Add toolkit via + > Toolkits (no agent) | toolkit in PARTICIPANTS | step 3 | step 3 | asserted |
| 2 Send message triggering sensitive action | "Thought for X secs" appears | step 4 | step 4 | asserted |
| 3 Verify authorization card with orange/warning border | card shown | step 5 | step 5 (testid presence used as the signal, not computed CSS color) | asserted *(clarification: asserting the testid, not the literal color, is the stable equivalent — see step 5 note)* |
| 4 Heading text | correct heading | step 6 | step 6 | asserted |
| 5 "Agent is about to perform:" + tool name | tool name shown | step 7 | step 7 | asserted *(clarification: case's `"aaa.delete_file"` is illustrative, not literal — see step 7 note)* |
| 6 Three buttons visible | all three shown | step 8 | step 8 | asserted |

**Axis 2 — Analyst additions:**
- Assert no console/JS errors across the whole flow — *added: standard
  side-channel check per the skill's discipline; HITL websocket frames are
  exactly the kind of async flow that silently swallows errors.*
- Assert the message-ambiguity fallback is avoided by using an explicit
  bucket name — *added: the case's literal message text was confirmed live
  to NOT reach a tool-call attempt at all against a project with 588
  buckets; without this the test would flake on shared/dirty project state.*

## Cleanup
1. Remove `artifact`/`delete_file` from the Sensitive Action Tools list +
   save (project-wide side effect — mandatory, not optional; see
   § Preconditions).
2. Delete the toolkit (`ToolkitAPI.delete_toolkit`) — confirmed working live.
3. Delete the bucket (`ArtifactAPI.delete_bucket`) — **CONFIRMED FLAKY this
   pass**: both the bucket-name and the `p--{project_id}.{bucket_name}`
   fallback path 404'd on a fresh bucket immediately after creation. Not
   blocking for this case (bucket content isn't asserted), but see
   Automation Hints — likely contributor to the 588-bucket project-data
   pollution observed live.

## Concrete Handles (discovered during exploration)

| Element | Recommended Locator | Fallback |
|---|---|---|
| Sensitive action panel | `[data-testid="sensitive-action-panel"]` (exists — source-confirmed; **not yet a `ChatPage` field**, only exists on `AgentDetailPage`, must be added as a new `LocatorDescriptor` on `ChatPage`) | none — testid-only |
| Authorize button | `[data-testid="sensitive-action-authorize-button"]` (exists, same add-to-ChatPage note) | none |
| Block button | **testid needed**: `sensitive-action-block-button` — add via `add-data-testid` to `ChatHitlActions.jsx`'s `isSensitiveTool` branch "Block" `BaseBtn` (currently no `data-testid` at all, confirmed by full-file read) | none |
| Block with Comment (collapsed trigger) | **testid needed**: `sensitive-action-block-with-comment-button` — `BlockWithCommentControl.jsx`'s `!open` return branch (no testid today) | none |
| Toolkit participant add flow | `ChatPage.add_toolkit_participant(toolkit_name)` (existing method, confirmed live) | none needed — already works |

## Network Behavior
- HITL pause/resume rides the same `chat_predict` websocket envelope the
  pipeline HITL flow uses (`type` field disambiguates), confirmed by
  reused pattern in `test_pipeline_hitl_node_runtime_behavior.py` — this
  case's own `agent_hitl_interrupt`/`sensitive_tool` payload was NOT
  captured live (precondition unreachable locally); implementer should
  capture it once run against the deployed CI env and record the actual
  `guardrail_type`/`available_actions` shape here for the next reader.

## Known Defects Found During Exploration
None found. (Testid gaps below are implementer work, not product defects —
per `.agents/role-overrides.md` § Analyst slot, a missing testid is never
softened into a defect.)

## Blocked Steps
None outright blocked — the toolkit-participant / message / accordion
portion of the flow (steps 3–4) was fully executed live on localhost. Only
the HITL-trigger precondition itself (marking `delete_file` sensitive) could
not be exercised locally; this is handled via the existing `guardrails`
marker + deployed-env CI path, matching established project precedent
(`TestSensitiveToolLiveReload`), not a fresh blocker.

## Automation Hints
- Framework: Playwright + pytest, per `.agents/testing.md`.
- Marker: `pytest.mark.guardrails` (excludes from local dev loop, matches
  `test_guardrails_live_reload.py`) + `pytest.mark.p2` (priority) +
  `pytest.mark.chat` + `pytest.mark.regression`.
- Reuse `GuardrailsAdminPage` (`pages/guardrails_admin_page.py`) exactly as
  `TestSensitiveToolLiveReload` does, including its locally-defined
  `admin_page` fixture pattern (own `Browser` context via `auth_state`).
- New page-object work on `ChatPage` (not `AgentDetailPage` — this flow uses
  the main chat, no agent): add `sensitive_action_panel`,
  `sensitive_action_authorize_button` `LocatorDescriptor`s (same testids
  `AgentDetailPage` already has — same underlying React component renders
  in both contexts) plus a `wait_for_sensitive_action_authorization()`-style
  method mirroring `AgentDetailPage`'s (currently ChatPage has ZERO
  HITL/sensitive-action locators — confirmed via grep).
- **Test-data-hygiene finding (not blocking this case, flag to the lead):**
  the project has 588 artifact buckets at time of this analysis, and this
  session's own throwaway bucket failed to delete via
  `ArtifactAPI.delete_bucket()` (both the direct and `p--{project_id}.`
  fallback paths 404'd immediately after creation) — `artifact_bucket`
  fixture's teardown swallows this exception
  (`fixtures/data_fixtures.py:487-489`, `logger.warning`, non-fatal), so
  failures accumulate silently. Worth a dedicated investigation outside
  this cluster's scope.
