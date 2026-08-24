# Test Case: Remote MCP — Test Settings — View Run History

## Metadata
- **TMS ID**: ELITEA-1940
- **Linked Story**: none
- **Priority**: l3 — TMS frontmatter `priority: medium`; same `medium → l3_`
  precedent this folder's ELITEA-1937 / ELITEA-1947 AFS files set.
- **Environment Explored**: local (`http://localhost:5173`, `EliteaAI/EliteaUI`
  @ `automation/testids`, DEV backend)
- **User set**: `${TEST_USER}` (localhost: no login — `VITE_DEV_TOKEN` auto-auth)
- **Analyst**: qa-engineer (agent), session 2026-08-24, cluster dispatch with
  ELITEA-1938 + ELITEA-1939 (shared session; every case's steps executed and
  observed individually — the other two DIVERGED and are `blocked`; this one is
  fully executable)
- **Status**: ready-for-automation
- **Filed**: #1727 (`question` + `case-text-drift`) — location/container drift
  only; **does not block automation**

## Summary of the drift (assert the LIVE contract, per the reverse-masking guard)

The case's **observable is fully intact**; only *where the button lives* and
*what kind of container opens* are stale. All 6 steps executed green live.

| Case text says | Live product (2026-08-24) |
|---|---|
| "view run history" button **in the test panel header** | Button is in the **MCP detail action bar** (`toolkit-action-bar`), testid `pipeline-history-tab`, aria-label `view run history`, label "Run History". The `/mcps/all/{id}/test` page's column headers carry **no buttons at all**. |
| a run-history **panel/drawer** opens | It **navigates to a full page**: `/toolkits/all/{id}/history?isMCP=true` (`ToolkitRunHistory.jsx` → shared `RunHistoryContainer`). No drawer, no overlay. |
| entries listed with **timestamps** | ✅ confirmed — a **Date** column *and* a **Duration** column |
| clicking an entry shows **input/output** | ✅ confirmed — row flips `data-selected="true"`, detail pane renders input + output |

Root cause (source, `EliteaAI/EliteaUI` after `git fetch origin`): the
`ViewRunHistoryButton` was part of the pre-EL-5947 test-panel header trio
(`TestTools.jsx @ 0cff136d^:196`) that ELITEA-1938/1939/1940 all describe.
**Unlike the other two it was relocated, not removed** —
`ToolkitForm.jsx:562` renders it whenever `isDetailsActionBar`, and
`useToolkitDetailNavigation.hooks.js`'s `goToRunHistory` navigates to
`RouteDefinitions.ToolkitRunHistory` with `?isMCP=${!!isMCP}`. That hook's own
doc comment states the toolkit-namespace URL for an MCP is intended:
*"Run History has only the toolkit route and MCPs reach it via `?isMCP`"*.

## Preconditions

- Authenticated (localhost: automatic via `VITE_DEV_TOKEN`).
- A Remote MCP with **discovered tools** and **at least one completed tool run**.
  - **Fixture** (same precedent as ELITEA-1933/1937): `https://mcp.deepwiki.com/mcp`
    — public, auth-free, 3 tools. Exercised tool `read_wiki_structure` (single
    required plain-string `repoName`; avoids `ask_question`'s `anyOf` shape).
  - The case's precondition is **self-satisfiable**: the test performs the run
    itself in setup (see § Test Steps 1–5), so it does not depend on residue
    from an earlier run. Verified live: a freshly-run execution appeared as the
    top row within seconds.

## Test Data

### generate-per-test (created in setup, deleted in teardown)
- Toolkit Name: `autotest_mcp_run_history` + a per-run unique suffix
  (`MAX_NAME_LENGTH = 32`, silently truncating — compute the suffix against the
  literal base name, digest § Fixtures addendum).
- URL: `https://mcp.deepwiki.com/mcp`
- Tool: `read_wiki_structure`; run TWICE with two different `repoName` values —
  `"AsyncFuncAI/deepwiki-open"` (run 1) and `"facebook/react"` (run 2).
  **Amended by the implementer (2026-08-24):** the two runs must differ, so the
  step-8 "the detail changed" assertion has something row-specific to read; two
  identical runs would render identical detail panes and the assertion would be
  unfalsifiable.

## Test Steps

1. Create a Remote MCP (`autotest_mcp_run_history_<uniq>` /
   `https://mcp.deepwiki.com/mcp`) and open its detail page —
   `McpFormPage`, identical to ELITEA-1933/1937 steps 1–7.
   - **Verify**: detail page loads, `toolkit-detail-title` shows the MCP name
     (not the `"Edit MCP"` placeholder — `_wait_for_detail_data_rendered()`).
2. Click **Load Tools** (`toolkit-load-tools-button`).
   - **Verify**: 3 tool chips render (`toolkit-tool-chip-ask_question`,
     `-read_wiki_contents`, `-read_wiki_structure`); `toolkit-tools-total-count`
     reads `3 / 3`. Confirmed live.
3. Click **Save** (`toolkit-detail-save-button`) and wait for
   `toolkit-test-button` to become **enabled**.
   - **Verify** *(Axis 2 — see Coverage Map)*: before Save, `toolkit-test-button`
     is `disabled` (confirmed live: Load Tools dirties the form and
     `ToolkitForm.jsx` sets `isTestDisabled={dirty}`); after Save it enables.
     **This is a hard sequencing requirement, not a nicety** — skipping the Save
     leaves the Test button permanently disabled.
4. Click **Test** (`toolkit-test-button`, aria-label `Test MCP`).
   - **Verify**: URL becomes `/mcps/all/{id}/test`; the empty-state
     `toolkit-test-empty-tool-select` ("Select Tool") is visible (EL-5947
     gating — the settings form does not mount until a tool is chosen).
5. Select `read_wiki_structure` (`select-option-read_wiki_structure`), fill
   `toolkit-test-param-repoName-input` with `AsyncFuncAI/deepwiki-open`, click
   **Run Test** (`toolkit-test-run-tool-button`), and wait for the result.
   - **Verify**: `[data-testid="chat-message-list"] li.MuiListItem-root`
     contains `✅ read_wiki_structure` — confirmed live at `1.182s`, followed by
     the real DeepWiki page list (proving a genuine remote execution, not a
     canned response).
   - **AMENDED BY THE IMPLEMENTER (2026-08-24, PR #1728 review round 1) — the
     ✅ is load-bearing, assert it explicitly.** `wait_for_tool_result()`
     (`pages/toolkit_test_settings_page.py:441`) polls the `[✅❌]` regex, so it
     resolves on a FAILED run too and returns the text either way; and the
     summary EliteaUI builds (`indexChat.helpers.js:250-264`,
     `` `${status} \`${tool}\`${execTime}` ``) names the tool under BOTH icons.
     A `"read_wiki_structure" in result` check therefore passes on
     `❌ read_wiki_structure (0.4s) MCP error …` — green while the tool errored,
     and Run History then holds a failed execution for steps 7–8 to assert
     against. Assert the **success marker for this tool** plus the absence of
     any `❌` (module-level `is_successful_tool_run()`, unit-pinned in
     `automation/tests/unit/test_mcp_run_history_successful_run_matcher.py`),
     and assert the requested `repoName` appears in the result body — DeepWiki
     answers `Available pages for <repo>: …`, so that is the produced-by-the-
     system proof that the body is the real remote structure, not an empty
     success.
5b. *(Added by the implementer, 2026-08-24.)* Return to the detail page,
   click **Test** again, re-select `read_wiki_structure`, fill
   `repoName = "facebook/react"`, and Run Test a second time.
   - **Why a second Test-route visit and not simply a second Run Test click**:
     one Run History row is one **conversation**, and a conversation is created
     only when the panel has none (`useToolkitChat.executeRunTool`) — two runs
     in one mount produce ONE row. See § Test Steps 8 § Implication for setup.
   - **Verify**: the result message names the executed tool.
6. Navigate back to the MCP detail page (`/mcps/all/{id}`) and click
   **Run History** (`pipeline-history-tab`).
   - **Verify**: URL becomes `/toolkits/all/{id}/history?isMCP=true`.
     *(Case steps 3–4 — the button is in the detail action bar, and this is a
     route navigation rather than a drawer; see § Summary of the drift and
     #1727.)*
   - **Gotcha, confirmed live**: after a client-side navigation back to the
     detail page, `pipeline-history-tab` is not in the DOM immediately — the
     action bar mounts asynchronously (first click attempt failed with
     *"does not match any elements"*, the element appeared on a poll). Rely on
     Playwright auto-waiting / an explicit `wait_for(state="visible")`; never an
     immediate `query_selector`.
7. Verify the run-history list.
   - **Verify** *(case step 5)*: at least one `run-history-list-item` row is
     present, and the most recent row's text matches a **timestamp** pattern —
     confirmed live format `DD-MM-YYYY, hh:mm AM/PM` (e.g. `24-08-2026, 06:17 AM`)
     — plus a **Duration** value (`1.19 s`). Assert the timestamp with a
     `re.compile(r"\d{2}-\d{2}-\d{4},\s*\d{2}:\d{2}\s*(AM|PM)")`-shaped regex,
     **not** an exact string (the value is per-run).
   - Column headers read `Date` / `Duration`. *(For contrast: the Agent surface's
     ELITEA-1876 clarification #1282 recorded `Date`/`Version`/`Duration` — the
     toolkit/MCP variant has no Version column. Assert what this surface renders.)*
8. Click a history entry and verify its input/output detail.
   - **Verify** *(case step 6)*: the clicked row carries
     `data-selected="true"` and the others `"false"` (confirmed live — a
     **testid + state-attribute** filter, exactly the shape
     `.agents/testing.md` § Locator policy requires; **never** a
     state-dependent testid).
   - **Verify**: the detail pane (`chat-message-list`) renders **two**
     `chat-message-item` entries — the **input**
     (`Calling 'read_wiki_structure' with parameters:` + the JSON
     `{ "repoName": "AsyncFuncAI/deepwiki-open" }`) and the **output** (the
     DeepWiki page list). Confirmed live for both rows tested.
   - **AMENDED BY THE IMPLEMENTER (2026-08-24, PR #1728 review round 1) —
     input and output MUST be asserted through SEPARATE handles.** Both
     messages share the `chat-message-item` testid (`UserMessage.jsx:127` /
     `ApplicationAnswer.jsx:578`), and the input echo *already contains the
     tool name and the `repoName`*. So every text assertion made against the
     message LIST (or its `chat-message-list` container) is satisfied by the
     input alone, and `to_have_count(2)` counts **input + error** exactly like
     input + output — i.e. the output would go entirely unverified. The only
     handle that can match the produced result is the answer-content testid
     (`ApplicationAnswer.jsx:710` — `isLastMessage ? 'skill-test-last-response'
     : 'chat-answer-content'`; the run-history answer is the last message, so
     `skill-test-last-response` in practice — confirmed live 2026-08-24 on
     toolkit 2140's history: that node reads
     `Available pages for AsyncFuncAI/deepwiki-open: 1 …` while the input node
     carries only `chat-message-sender-name` / `-avatar`). Assert, per selected
     row: the ANSWER contains that row's own `repoName`, contains no `❌`, and
     does NOT contain the `Calling '<tool>' with parameters` echo (a
     self-check — if the answer handle ever collapsed onto the input, every
     other output assertion would become unfalsifiable), plus the INPUT node
     separately carries the echo and the same `repoName`.
   - **Note on default selection (confirmed live + source)**:
     `RunHistoryContainer.jsx` auto-selects `historyRows[0]` on mount when
     nothing is selected. So on arrival the top row is *already* selected and
     its detail is *already* rendered. **A meaningful step-6 assertion must
     therefore click a DIFFERENT row than the auto-selected one and prove the
     selection AND the detail changed** — otherwise the assertion passes without
     the click doing anything. Executed live exactly this way: clicked row
     index 1, `data-selected` flipped to it, and the detail pane switched from
     the *"less than a minute ago"* run to the *"22 days ago"* run.
   - **Implication for setup**: to exercise this honestly the MCP needs **two**
     history rows.
     **AMENDED BY THE IMPLEMENTER (2026-08-24) — the original route did not
     work.** One Run History row is **one conversation, not one Run Test
     click**: `useToolkitChat.executeRunTool` creates a conversation only when
     `!activeConversation`, so clicking Run Test twice inside a single mount of
     the Test panel appends both runs to the SAME conversation and Run History
     shows **1 row** (measured: the first implementation did exactly this and
     `to_have_count(2)` saw 1). The working route — and the one a real user
     takes for two separate test sessions — is to **re-enter the Test route
     between runs** (detail page -> Test button -> re-select the tool -> Run),
     which remounts the panel, clears `activeConversation`, and produces a
     second row. Use two DIFFERENT `repoName` values so the two rows' detail
     panes are distinguishable.

## Expected Results

- The **Run History** control on an MCP detail page navigates to
  `/toolkits/all/{id}/history?isMCP=true`.
- The page lists one row per past execution, each with a Date timestamp and a
  Duration.
- Selecting a row marks it `data-selected="true"` and renders that execution's
  input (tool name + parameter JSON) and output in the detail pane.

## Coverage Map

### Axis 1 — Case coverage

| Case element | Expected result | Covered by (AFS step) | Asserted where | Disposition |
|---|---|---|---|---|
| Precondition: user logged in | met | Preconditions | — | satisfied |
| Precondition: MCP with ≥1 previous tool execution | met | steps 1–5 | step 5 | asserted — **self-satisfied by the test's own setup**; fixture substituted (DeepWiki), same precedent as ELITEA-1933/1937 |
| 1 Open a Remote MCP detail page | detail page loads | step 1 | step 1 | asserted |
| 2 Run a tool to generate execution history | run completes, history entry created | steps 2–5 | step 5 | asserted — real ✅ result + real DeepWiki content |
| 3 Click "view run history" button in test panel header | history panel/drawer opens | step 6 | step 6 | asserted — **CLARIFICATION #1727: the button is in the MCP DETAIL ACTION BAR, not the test panel header** |
| 4 Verify run history panel/drawer opens | history panel visible | step 6 + 7 | step 6 (URL) + 7 (rows) | asserted — **CLARIFICATION #1727: it is a full PAGE/route, not a drawer** |
| 5 Verify previous executions listed with timestamps | entries show timestamps | step 7 | step 7 | asserted — Date (`DD-MM-YYYY, hh:mm AM/PM`) + Duration |
| 6 Click a history entry → shows input/output details | input + output displayed | step 8 | step 8 | asserted — `data-selected` flip + the INPUT node's echo/`repoName` + the ANSWER node's own `repoName` and absence of `❌`, through **separate handles** (see step 8's implementer amendment: a list-level assertion is satisfied by the input echo alone) |
| Expected Final State: all executions listed with timestamps, entry detail works | — | steps 7–8 | steps 7–8 | asserted |
| Pass/Fail: entries listed with timestamps, detail view works | — | steps 7–8 | steps 7–8 | asserted — no blocking defect |

### Axis 2 — Analyst additions

- **Step 3 asserts `toolkit-test-button` is disabled pre-Save and enabled
  post-Save** — *added: this is not in the case text, but it is a live
  precondition of reaching the Test surface at all (`isTestDisabled={dirty}`),
  and it cost this session a real detour. Guarding it turns a future silent
  "Test button never clickable" hang into a named failure.*
- **Step 8 asserts the clicked row's `data-selected` flips AND the detail pane
  content changes** rather than merely "some detail is visible" — *added: the
  container auto-selects row 0 on mount, so a visibility-only assertion would
  pass even if the click were a complete no-op. Asserting the delta is what
  makes step 6 a real test of "selecting an entry displays its details".*
- **Step 7 asserts the timestamp by regex shape, not exact text** — *added:
  the value is generated per run; an exact match would be unassertable and an
  "is non-empty" check would pass on any garbage string. The shape check catches
  a real regression (a missing/malformed date) while staying deterministic.*
- No console-error assertion added: only the already-tracked pre-existing
  warnings appeared (0 errors observed across the whole flow this session).

## Cleanup

1. The test creates a persistent MCP toolkit entity.
2. Delete it in teardown via `ToolkitAPI.delete_toolkit(toolkit_id)` — same
   pattern as ELITEA-1933/1934/1937. Deleting the MCP disposes of its run
   history with it (the history is keyed on `entityId`).
3. Nothing was created during this analysis session — MCP id **2140**
   (`autotest_mcp_run_tool`, ELITEA-1937 residue) was reused, and it now carries
   one extra run-history row from this session's live execution. Harmless.

## Concrete Handles (discovered during exploration)

**PROVENANCE verified 2026-08-24 with a fresh `cd ../EliteaUI && git fetch origin`
immediately before the check. Every handle this case needs is already on
`origin/main` — this case requires NO `add-data-testid` work.**

| Element | Recommended Locator | PROVENANCE |
|---|---|---|
| MCP detail action bar | `[data-testid="toolkit-action-bar"]` | on-main ✓ |
| **Run History** button | `[data-testid="pipeline-history-tab"]` (aria-label `view run history`, label "Run History") | on-main ✓ |
| **Test** button | `[data-testid="toolkit-test-button"]` (aria-label `Test MCP`) | on-main ✓ |
| Save (detail) | `[data-testid="toolkit-detail-save-button"]` | on-main ✓ |
| Load Tools | `[data-testid="toolkit-load-tools-button"]` | on-main ✓ |
| Tool chip (dynamic) | `[data-testid="toolkit-tool-chip-{tool}"]` | on-main ✓ |
| Tools count | `[data-testid="toolkit-tools-total-count"]` | on-main ✓ |
| Empty-state tool select | `[data-testid="toolkit-test-empty-tool-select"]` | on-main ✓ |
| Tool dropdown option (dynamic) | `[data-testid="select-option-{tool}"]` | on-main ✓ |
| Tool param input (dynamic) | `[data-testid="toolkit-test-param-{key}-input"]` | on-main ✓ |
| Run button | `[data-testid="toolkit-test-run-tool-button"]` (label "Run Test", not "RUN TOOL" — #1087) | on-main ✓ |
| Run result list / item | `[data-testid="chat-message-list"]` / `… li.MuiListItem-root` | on-main ✓ |
| **Run-history row** | `[data-testid="run-history-list-item"]` — same literal testid on **every** row, positionally distinguished (default sort = Date descending ⇒ index 0 = most recent) | on-main ✓ |
| **Run-history row — selected state** | `[data-testid="run-history-list-item"][data-selected="true"]` — testid + **state attribute**, per `.agents/testing.md` § Locator policy (`RunHistoryListItem.jsx:151` sets `data-selected={selectedItem === item.id}`) | on-main ✓ |
| Run-history detail messages | `[data-testid="chat-message-list"]` / `[data-testid="chat-message-item"]` | on-main ✓ |
| **Run-history detail — OUTPUT (answer) content** | `[data-testid="skill-test-last-response"], [data-testid="chat-answer-content"]` scoped inside `chat-message-list` — the ONLY handle that isolates the produced result from the input echo (`ApplicationAnswer.jsx:710` picks the testid by `isLastMessage`; the answer is last here, so `skill-test-last-response`). Already used this way by `PipelineDetailPage` / `AgentDetailPage`. | on-main ✓ (fresh `git fetch origin` 2026-08-24: both testids YES on `origin/main` **and** on `origin/automation/testids`) |
| Per-row overflow menu | `[data-testid="run-history-menu-menu-button"]` | on-main ✓ — present, not needed by this case; **do not wire it** (#511: only what the executed path calls) |

> **Naming note (not a defect, do not "fix"):** `ViewRunHistoryButton.jsx:16`
> defaults `testId = 'pipeline-history-tab'`, so the **MCP** surface renders a
> `pipeline-`-prefixed testid. It is a shared-component naming leak of the kind
> `.agents/testing.md` § Locator policy warns about, but it is stable, already
> on `main`, and already used by `PipelineDetailPage`. Use it as-is; renaming it
> would break the merged pipeline specs. Flagged in #1727 only so nobody reads
> the prefix as a wrong-element match.

## Network Behavior

- MCP creation + Load Tools: same sequence as ELITEA-1933/1934
  (`POST tools/prompt_lib/{project}`, `POST mcp_sync_tools/prompt_lib?await_response=true`).
- Tool run: completion proven by the DOM (`chat-message-list` gaining the ✅
  item), same as ELITEA-1937 — `ToolkitTestSettingsPage.wait_for_tool_result()`
  polls the `[✅❌]` regex, no sleeps.
- Run-history list: `RunHistoryApi.useLazyGetRunHistoryListQuery()` fires on
  mount, keyed on `{source, projectId, entityId, page}` — a **real** fetch, so
  wait on the first `run-history-list-item` row rendering rather than on
  navigation alone (the pipeline page object already does exactly this;
  `pipeline_detail_page.py:6893`).

## Overlap check — why this is `ready-for-automation`, not `already-covered`

The shared `RunHistoryContainer` **is** already automated, on two other
surfaces:

- `automation/tests/ui/pipelines/test_pipeline_run_history_view_executions.py`
  (ELITEA-2011 / ELITEA-2070) — `pipeline-history-tab`,
  `run-history-list-item`, `data-selected`, via `PipelineDetailPage`
  (`pages/pipeline_detail_page.py:57,69-71,6897-7000`).
- `automation/tests/ui/agents/test_agent_run_history_select_past_run.py`
  (ELITEA-1876/1877) — same component via `AgentDetailPage`.

Neither covers this case's observable: **the MCP/toolkit surface** — a
different entry point (the toolkit detail action bar, not a chat-panel header),
a different route (`/toolkits/all/{id}/history?isMCP=true`, a full page rather
than an in-page panel), a different `source`/`entityId` pairing, and a
different column set (Date/Duration, no Version). Same component ≠ same
coverage; a regression in the MCP wiring (wrong `entityId`, missing `isMCP`
flag, action-bar button not rendered) would leave both existing specs green.
**Reuse the page-object pattern, write a new spec.**

## Automation Hints

- **New page object needed for the run-history page on the toolkit/MCP route.**
  Mirror `PipelineDetailPage`'s run-history block verbatim — the constants are
  literally the same shared testids:
  `RUN_HISTORY_LIST_ITEM_SELECTOR`, `RUN_HISTORY_LIST_ITEM_SELECTED_SELECTOR`,
  and the `open_run_history` / `get_run_history_item_count` /
  `get_run_history_item_texts` / `select_run_history_item` /
  `is_run_history_item_selected` / `get_run_history_chat_messages_text` method
  set (`pages/pipeline_detail_page.py:6897-7000`). Whether to extend
  `McpFormPage` or add a small `ToolkitRunHistoryPage` is the implementer's
  call.
  *(Implementer, 2026-08-24: shipped as a new `ToolkitRunHistoryPage`
  (`automation/pages/toolkit_run_history_page.py`) — the run-history page is a
  distinct ROUTE, not a region of the detail form. The action-bar handles
  (`toolkit-test-button`, `pipeline-history-tab`) went onto `McpFormPage`, which
  owns the detail page.)*
  A shared mixin across the three surfaces would be a **declared**
  improvement, not a requirement (`.agents/role-overrides.md` § Declared-improvisation)
  — NOT taken here: it would mean editing two merged page objects for no
  assertion this case makes. Flagged as suite health in the Run Report.
- **Reuse `McpFormPage`** (create / Load Tools / Save / detail waits) and
  **`ToolkitTestSettingsPage`** (`select_tool_from_empty_state`,
  `fill_param_field`, `run_tool`, `wait_for_tool_result`) — both already model
  this flow for ELITEA-1933/1937; no new methods needed on either.
- **`McpFormPage.expand_configuration_section()`** is *not* needed here — this
  case never asserts a `toolkit-field-*` value (digest § MCP DETAIL page:
  configuration fields are COLLAPSED).
- **Sequencing that will bite otherwise** (both confirmed live this session):
  1. Load Tools dirties the form ⇒ **Save**, then wait for
     `toolkit-test-button` to enable, before clicking Test.
  2. After returning to the detail page, the action bar (and therefore
     `pipeline-history-tab`) mounts **asynchronously** — wait for it.
  3. *(Implementer, 2026-08-24)* One Run History row = one **conversation**.
     Two runs in one Test-panel mount = one row; remount the Test route between
     runs to get two (see § Test Steps 8 § Implication for setup).
- Markers: `p2`/`l3`-consistent priority marker + `regression` + the
  `credentials`-style per-feature marker used by the other MCP specs
  (`toolkits`), matching `automation/tests/ui/toolkits/test_mcp_*.py`.
- Every step wrapped in `with allure.step("Step N — …"):`
  (`.agents/testing.md` § Step reporting).

## Blocked Steps

None. All 6 case steps executed to completion against the live local
environment (with the fixture substitution noted in Preconditions and the two
location clarifications filed as #1727).
