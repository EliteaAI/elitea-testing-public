# Test Case: MCP Integration in Pipeline — Add MCP to Tools, Configure MCP Node, EXECUTE

## Metadata
- **TMS ID**: ELITEA-1952
- **Linked Story**: none
- **Priority**: l2 (case metadata says `priority: high`; the covering spec and every MCP-node sibling on this suite are `p2` — keep the family marker)
- **Environment Explored**: local (`http://localhost:5173`, EliteaUI `automation/testids`, DEV backend, project `Private` id 399)
- **User set**: `${TEST_USER}` (localhost `auth_state` bypass via `VITE_DEV_TOKEN`)
- **Analyst**: qa-engineer (Sage), batch `mcp-w05`, cluster session with ELITEA-1953, 2026-08-24
- **Status**: extend-existing
- **surface_key**: pipeline-mcp-node
- **Evidence**: `test-results/screenshots/ELITEA-1952-step-21-mcp-node-execution-output.png`
- **Live artifacts used this session**: pipeline `9506` (`autotest_mcp_pipeline_w05`), MCP toolkit `3270` (`autotest_mcp_w05`, DeepWiki fixture)

---

## Extension target

**Covering spec**: `automation/tests/ui/pipelines/test_pipeline_mcp_node_fresh_attach.py`
:: `test_mcp_node_fresh_attach` (264 lines), merged to `origin/automation/base`
(AFS `test-specs/pipelines/l2_pipeline-mcp-node-integration-fresh-attach_ELITEA-2037.md`,
TMS ELITEA-2037).

Secondary, same-surface merged spec (do NOT duplicate its assertions):
`automation/tests/ui/pipelines/test_pipeline_tools_section_mcp_add_view_remove.py`
:: `test_tools_section_mcp_add_view_remove` (ELITEA-2065) — owns the Tools-section
card lifecycle (attach → "Show tools" expand → remove → persist).

### Behavioural overlap (what is already proven — re-confirmed LIVE this session)

Every one of these was re-executed live against `localhost:5173` on pipeline `9506`
this session and behaved exactly as the covering spec asserts:

| ELITEA-1952 step | Already proven by |
|---|---|
| 1 (pipeline canvas loads) | covering spec Step 1 (`wait_for_canvas`, `configuration_tab` visible, `get_node_ids() == ["END"]`) |
| 2 (TOOLS section visible) | covering spec Step 2 (`open_mcp_popper()` requires it) |
| 4 (click "+ MCP" → picker opens) | covering spec Step 2 |
| 5 (picker lists project MCPs) | covering spec Step 2 (`get_mcp_popper_menu_item_count(popper) > 0`) |
| 6 (select a Remote MCP) | covering spec Step 3 (`select_mcp_in_popper`, hard-blocks on the attach `PATCH … 201`) |
| 8–9 ("Add node" menu opens, lists MCP) | covering spec Step 5 + ELITEA-2030's add-node-menu spec |
| 10–11 (MCP node added to canvas) | covering spec Step 5 (`wait_for_node_on_canvas("mcp")`) |
| 12–13 (config panel fields: Trigger / Toolkit / Input / Output / interrupt+structured toggles) | covering spec Step 6 — including the *absence* assertions for Tool + Input-mapping before a Toolkit is picked |
| 14 (select Toolkit) | covering spec Step 7 |
| 15 (Tool dropdown populates) | covering spec Steps 7–8 |
| 16 (select a tool) | covering spec Step 8 |
| 17 (Input/Output variable values) | covering spec Step 10 (`get_mcp_node_input_value() == "input"`, `…output_value() == "messages"`) |
| 19 (Save succeeds) | covering spec Step 11 (`save_and_wait_for_update` → `201`) |

That is 13 of the case's 21 steps, asserted with the same observables and the same
expected results, on the same surface, by a spec merged to `origin/automation/base`.
Writing a fresh spec would duplicate all of it.

### The gap (why this is NOT `already-covered`)

Four observables this case demands that **no merged spec asserts**:

1. **Step 3 — all FOUR tool-attachment buttons present.** The covering spec only
   clicks `agent-add-mcp-button`. Nothing asserts that "+ Toolkit", "+ MCP",
   "+ Agent", "+ Pipeline" are *all* visible in the TOOLS section. Confirmed live:
   all four render, all four already carry testids.
2. **Step 7 — the attached-MCP card's composition.** The covering spec asserts only
   that a card for the MCP exists (`is_toolkit_attached(name)`). It does not assert
   the card's *name text*, its "Show tools" toggle, or its **connection status**
   control. ELITEA-2065 expands "Show tools" but likewise asserts neither the name
   element nor connection status.
3. **Steps 20–21 — PIPELINE EXECUTION (the big one).** No merged spec on this suite
   executes a pipeline whose MCP node invokes a real MCP tool and asserts the tool
   output comes back. `test_pipeline_execution.py` executes pipelines, but only
   `pipeline_with_llm_id` (a single LLM node). This is the case's whole point per
   its § Expected Final State, and it is the assertion that would catch a real
   MCP-execution regression. Confirmed live and clean this session (see Test Steps).
4. **Step 18 — node connection** is a *clarification*, not a gap (see § Case-text
   drift). Recorded so the implementer does not try to build it.

Gap size: 3 assertion clusters appended to a 12-step spec. Not a near-rewrite ⇒
`extend-existing`, not `ready-for-automation`.

### Recommended extension shape (DECLARED — implementer may overrule with reasoning)

Append gaps **1 and 2 to the existing `test_mcp_node_fresh_attach` test** (they are
cheap, deterministic, and sit exactly where that test already is in the flow —
Step 2 and Step 4 respectively).

Add gap **3 as a SEPARATE test function in the SAME file**
(`test_mcp_node_executes_selected_tool`), reusing the same `pipeline_id` +
`mcp_toolkit_with_tools` fixtures and the same `PipelineDetailPage` methods.

Reasoning (canon has no rule for this, so it is declared per
`.agents/role-overrides.md` § Declared-improvisation protocol): the covering test is
currently fully deterministic and fast; a live MCP+LLM execution took **~11 s of
"Thought" plus streaming** this session and is the one part of this flow with genuine
latency/variance. Folding it into the existing test would put a currently-stable
merge-gate participant behind a live LLM round-trip. A sibling test in the same file
keeps the shared page objects/fixtures (the point of `extend-existing`) while
isolating the flake surface. If the implementer prefers one test, that is defensible —
say so in the Run Report.

---

## Preconditions

- User authenticated (localhost: automatic via `VITE_DEV_TOKEN`).
- A **Remote MCP with a real, non-empty tool list** exists in the project.
  Use the existing `mcp_toolkit_with_tools` fixture
  (`automation/fixtures/data_fixtures.py:2085`) — it syncs
  `https://mcp.deepwiki.com/mcp` and bakes `selected_tools` /
  `available_mcp_tools` into the toolkit, which is what makes the node's Tool
  dropdown non-empty.
- A **fresh, empty pipeline** — the `pipeline_id` fixture (as the covering spec uses).

**Test-data substitution (declared).** The case names MCP "EliteaMCP" and tool
`get_auth_user`, output var `user_info`. Neither the MCP nor that tool exists in this
project; `get_auth_user` is a zero-parameter tool, so it would additionally skip the
Input-mapping surface entirely. Substituted with the DeepWiki fixture MCP and its
`ask_question` tool (2 required params), and Output `messages` — the same substitution
precedent already set and merged by ELITEA-2037/2065/1954/1955. This is **test data**,
not the observable: the case's observable ("the MCP node executes the selected tool and
returns output") is still produced entirely by the system.

---

## Test Steps — as EXECUTED live, 2026-08-24

| # | Action performed | Observed result | Verdict |
|---|---|---|---|
| 1 | Sidebar `+` → create form → Name `autotest_mcp_pipeline_w05`, **Description** (required), Save | `POST …/prompt_lib` → `201`; lands on `/pipelines/all/9506?destTab=configuration&…`; canvas renders with a single `END` node | PASS |
| 2 | Scroll to TOOLS | TOOLS section renders with the four ADD buttons | PASS |
| 3 | Inspect the four buttons | `agent-add-toolkit-button` ("Toolkit"), `agent-add-mcp-button` ("MCP"), `agent-add-agent-button` ("Agent"), `agent-add-pipeline-button` ("Pipeline") — all 4 present, count 1 each. **Visible label text carries no leading "+"** (the "+" is an icon) | PASS (assert on testid presence, not on a `"+ MCP"` string) |
| 4 | Click "+ MCP" | One MUI popper opens; `toolkit-search-input` ×1; `toolkit-menu-item` ×21 | PASS |
| 5 | Read the popper rows | Project MCPs listed by name, incl. `autotest_mcp_w05` | PASS |
| 6 | Click the `autotest_mcp_w05` row | `PATCH …/elitea_core/tool/prompt_lib/399/` → **201** fires immediately (auto-persist, per the ELITEA-2037 correction) | PASS |
| 7 | Inspect the TOOLS card | `agent-toolkit-card` ×1. Card text = `autotest_mcp_w05` + `Show tools` + **`Log in`**. Children: name `<div class="MuiTypography-…">` (**no testid**), `toolkit-card-tools-toggle` ("Show tools"), `toolkit-open-button`, `agent-toolkit-delete-button`, plus 4 `<svg>` (the MCP icon is the first, **no testid**), and a **`Log in` `<button>` (no testid)** = the connection-status control | PASS with 2 testid gaps (see § Handles) |
| 8 | Click `pipeline-add-node-button` | Node-type menu opens | PASS |
| 9 | Read menu items | 11 items, incl. `pipeline-add-node-menu-item-mcp` ("MCP") | PASS |
| 10 | Click "MCP" | Node added | PASS |
| 11 | Inspect the canvas | Nodes = `["END", "MCP 1"]`. `MCP 1` has `.react-flow__handle-top` (**target = Input port**) and `.react-flow__handle-bottom` (**source = Output port**). **No edge is auto-created at add time** (`.react-flow__edge` count 0) | PASS |
| 12 | (no click needed) | The config panel is **always-expanded INLINE on the node card**, not a right-hand panel — see § Case-text drift | PASS-with-clarification |
| 13 | Inventory the node's testids | `pipeline-entry-point-trigger-select` (+`-combobox`), `pipeline-mcp-node-toolkit-select` (+`-combobox`), `pipeline-mcp-node-input-select` (+`-combobox`), `pipeline-mcp-node-output-select` (+`-combobox`), `pipeline-node-interrupt-before-toggle-MCP 1`, `pipeline-mcp-node-interrupt-after-toggle`, `pipeline-mcp-node-structured-output-toggle`, `node-menu-menu-button`. **`pipeline-mcp-node-tool-select` is ABSENT** — Tool is conditionally rendered | PASS (matches the covering spec's Step-6 absence assertions) |
| 14 | Open Toolkit select → click `select-option-autotest_mcp_w05` | Toolkit combobox reads `autotest_mcp_w05`; `pipeline-mcp-node-tool-select` **appears** | PASS |
| 15 | Open the Tool select | Options `select-option-ask_question`, `select-option-read_wiki_contents`, `select-option-read_wiki_structure` — the fixture MCP's real 3 tools | PASS |
| 16 | Click `select-option-ask_question` | Tool combobox reads `ask_question` | PASS |
| 17 | Set Input=`input`, Output=`messages` (multi-selects) | Both render as MUI **chips**: `inputChips=["input"]`, `outputChips=["messages"]`. Handles: `pipeline-mcp-node-input-select-combobox` / `…-output-select-combobox`; chips are `.MuiChip-root` inside them | PASS |
| 18 | (attempt to connect START → MCP 1 → END) | **There is no START node.** Canvas holds only `END` + the added node; "start" is a *property* (`Trigger`/entry point) of the node, not a node. After Save+reload the edge `rf__edge-xy-edge__MCP 1---EliteAPipelineEnd` **exists automatically** (the node's default `transition` is END) | CLARIFICATION — no user action required |
| 19 | Click Save | `PUT …/application/prompt_lib/399/9506` → **201** | PASS |
| 20 | Type `AsyncFuncAI/deepwiki-open` in the embedded chat and click **`chat-send-button`** | User message renders; assistant bubble shows "Waking the agent…" then streams. **Enter does NOT send** in this composer — the send button is required (see § Gotchas) | PASS |
| 21 | Wait for the response to settle | Assistant message contains `chat-answer-thought-accordion` → **`chat-answer-tool-chip` with text `autotest_mcp_w05: ask_question (MCP1)`**, and `skill-test-last-response` holding the real DeepWiki answer ("This repository, DeepWiki-Open, is an automated documentation engine…", ~1 kB). `chat-delete-button` present = response complete. **0 console errors across the whole flow** | PASS |

**Total: 21/21 steps executed. 19 PASS, 2 clarifications (steps 12, 18). No defect.**

---

## Case-text drift (CLARIFICATIONS — assert the live contract, do NOT file as bugs)

Per the reverse-masking guard, the live product is correct and the case text is stale
in three places:

1. **Step 12 — "Click on the MCP node to open its configuration panel … opens on the
   right".** No node type in this product has a click-to-open right-hand config panel;
   every node's config is rendered **always-expanded inline on the node card itself**
   (already documented for every node type in `test-specs/pipelines/_surface.md`).
   The covering spec correctly asserts inline presence with no opening click. Do not
   add a click-to-open step.
2. **Step 18 — "Connect nodes: START → MCP 1 → END".** There is **no START node** in
   the ReactFlow canvas — a fresh pipeline renders only `END`, and "start" is expressed
   as the node's `Trigger`/entry-point property (`pipeline-entry-point-trigger-select`,
   value "Chat Message", which the freshly-added sole node auto-acquires). The
   `MCP 1 → END` edge is created automatically from the node's default `transition`,
   not by the user. Nothing to drag. The assertion that *does* carry the case's intent:
   after Save+reload, an edge with `data-id`
   `rf__edge-xy-edge__MCP 1---EliteAPipelineEnd` exists.
3. **Step 3 — button labels `"+ Toolkit" / "+ MCP" / …`.** The visible text is
   `Toolkit` / `MCP` / `Agent` / `Pipeline`; the `+` is a separate icon. Locate by
   testid (all four already exist on `main`), never by the `"+ X"` string.

Also cosmetic, worth knowing: the case's Test Data (`EliteaMCP`, `get_auth_user`,
`user_info`) does not exist in this environment — see § Preconditions substitution.

---

## Gap assertions (what the implementer adds)

### Gap 1 — TOOLS section exposes all four attachment triggers
Append to the covering spec's **Step 2**, before opening the popper:

```
expect(pipeline_page.add_toolkit_button).to_be_visible()
expect(pipeline_page.add_mcp_button).to_be_visible()
expect(pipeline_page.add_agent_button).to_be_visible()
expect(pipeline_page.add_pipeline_button).to_be_visible()
```

All four `LocatorDescriptor` fields already exist on `PipelineDetailPage`
(lines 1374/1399/1408/1420). **No EliteaUI work.**

### Gap 2 — the attached MCP card renders name + "Show tools" + connection status
Append to the covering spec's **Step 4**, alongside the existing
`is_toolkit_attached(...)`:

- the card's **name element** reads exactly the fixture MCP's display name;
- the card's **"Show tools"** toggle is visible (`toolkit-card-tools-toggle`,
  already on `main` — reuse; ELITEA-2065 already has a click helper for it);
- the card's **connection-status control** is visible and reads `Log in`
  for a not-yet-authenticated Remote MCP.

Needs **2 new testids** (see § Handles Reference — `pipeline-tools-card-name`,
`pipeline-tools-card-connection-status`). The MCP *icon* (step 7's fourth element)
is a decorative `<svg>` with no accessible identity; assert the three above and note
the icon as not-asserted in the Coverage Map rather than adding a testid to an
`<svg>` nobody can meaningfully verify.

### Gap 3 — the pipeline EXECUTES and the MCP node returns its tool's output
New sibling test in the same file (see § Recommended extension shape). Flow:

1. Reach the same saved state as the covering spec (attach MCP → add node → select
   Toolkit `autotest_mcp_*` → Tool `ask_question` → fill Input-mapping → Input
   `input` / Output `messages` → Save).
   *For a self-contained execution, set `repoName`'s Input-mapping **Type = Variable**
   (bound to `input`) so the chat message supplies the repo, and leave `question`
   Fixed — that is exactly what this session ran. A fully-Fixed variant works too;
   then the chat message content is irrelevant.*
2. `pipeline_page.send_message_in_embedded_chat("AsyncFuncAI/deepwiki-open")` —
   **must use the send button**; Enter does not submit.
3. `pipeline_page.wait_for_embedded_chat_response(initial_count=…, timeout=180_000)`.
4. Assertions (all against system-produced values):
   - the last assistant message contains a **`chat-answer-tool-chip`** whose text is
     `f"{mcp_toolkit_name}: ask_question (MCP1)"` — this IS the proof the MCP node
     executed the selected tool;
   - `skill-test-last-response` text is non-empty and longer than, say, 200 chars
     (the tool's real answer came back);
   - `assert not console_errors`.
   Do **not** assert exact answer prose — the answer is LLM/DeepWiki-generated. Assert
   the correlation (tool chip names the selected tool) and the shape (non-empty
   output), per `.agents/testing.md` § How to test a NONDETERMINISTIC producer.

`chat-answer-tool-chip` already exists on `main` and is already wired on
`ChatPage` / `AgentDetailPage`; `PipelineDetailPage` needs an equivalent
class-level field/constant — **page-object work, no EliteaUI change.**

---

## Handles Reference (testid-only per `.agents/testing.md` § Locator policy)

Provenance verified 2026-08-24 with `cd ../EliteaUI && git fetch origin` first.

| Element | Handle (testid) | Provenance | Notes |
|---|---|---|---|
| TOOLS "+ Toolkit" | `agent-add-toolkit-button` | on-main ✓ | already a `PipelineDetailPage` field |
| TOOLS "+ MCP" | `agent-add-mcp-button` | on-main ✓ | already a field |
| TOOLS "+ Agent" | `agent-add-agent-button` | on-main ✓ | already a field |
| TOOLS "+ Pipeline" | `agent-add-pipeline-button` | on-main ✓ | already a field |
| MCP picker search | `toolkit-search-input` | on-main ✓ | |
| MCP picker row | `toolkit-menu-item` | on-main ✓ | filter by text |
| Attached tool card | `agent-toolkit-card` | on-main ✓ | ONE flat list for all 4 types (no sub-tabs — `#1149`) |
| Card "Show tools" | `toolkit-card-tools-toggle` | on-main ✓ | |
| **Card name text** | **testid needed: `pipeline-tools-card-name`** | needs-adding | `<div class="MuiTypography-root MuiTypography-bodyMed">` inside `agent-toolkit-card`; shared `ApplicationTools.jsx`/tool-card component — name it for the CALL SITE per the shared-component rule, or accept a generic `tools-card-name` |
| **Card connection status ("Log in")** | **testid needed: `pipeline-tools-card-connection-status`** | needs-adding | `<button>` reading `Log in` for an unauthenticated Remote MCP. **Distinct from `toolkit-connection-status`** (that one lives on the MCP *detail* page, `McpAuthStatus.jsx`) |
| Add-node button | `pipeline-add-node-button` | on-main ✓ | |
| Add-node MCP item | `pipeline-add-node-menu-item-mcp` | on-main ✓ | |
| Node entry-point Trigger | `pipeline-entry-point-trigger-select` (+`-combobox`) | on-main ✓ | |
| Node Toolkit select | `pipeline-mcp-node-toolkit-select` (+`-combobox`) | on-`automation/testids` (runtime-composed via `TEST_ID_PREFIX_BY_NODE_TYPE` — a bare-substring grep for the full string finds nothing; verify via the `pipeline-mcp-node` prefix) | already a field |
| Node Tool select | `pipeline-mcp-node-tool-select` (+`-combobox`) | same | conditionally rendered |
| Node Input / Output selects | `pipeline-mcp-node-input-select` / `-output-select` (+`-combobox`) | same | chips are `.MuiChip-root` scoped inside |
| Input-mapping heading | `pipeline-mcp-node-input-mapping-heading` | same | text `Input mapping (required 2)` |
| Input-mapping Value (Fixed) | `pipeline-mcp-node-input-mapping-value-{param}` | same | class constant `MCP_NODE_INPUT_MAPPING_VALUE` |
| Interrupt before | `pipeline-node-interrupt-before-toggle-{node_id}` | on-main ✓ | node_id contains a SPACE (`MCP 1`) |
| Interrupt after / Structured output | `pipeline-mcp-node-interrupt-after-toggle` / `pipeline-mcp-node-structured-output-toggle` | on-`automation/testids` (added by ELITEA-2037) | |
| Dropdown option (dynamic) | `select-option-{value}` | on-main ✓ | shared app-wide pattern |
| Save | `agent-save-button` | on-main ✓ | |
| Embedded chat input | `chat-message-input` | on-main ✓ | |
| Embedded chat send | `chat-send-button` | on-main ✓ | **required — Enter does not send** |
| Assistant tool-call chip | `chat-answer-tool-chip` | on-main ✓ | text `"{toolkit}: {tool} (MCP1)"` — the execution observable |
| Assistant answer body | `skill-test-last-response` | on-main ✓ | |
| Assistant thought accordion | `chat-answer-thought-accordion` | on-main ✓ | wraps the tool chip |

Canvas node/edge identity uses ReactFlow's own `data-id` attributes
(`.react-flow__node[data-id="MCP 1"]`, edge `rf__edge-xy-edge__MCP 1---EliteAPipelineEnd`)
— these are **third-party library internals** (#579 exception 1) and are already the
established mechanism in `PipelineDetailPage.get_node_ids()` /
`wait_for_node_on_canvas()`. Reuse those methods; do not add new raw handles.

---

## Network Behavior

| Action | Request | Status |
|---|---|---|
| Create pipeline (form Save) | `POST …/application/prompt_lib/399` | 201 |
| Attach MCP in the "+ MCP" popper | `PATCH …/elitea_core/tool/prompt_lib/399/` | **201 — auto-persists on selection** (ELITEA-2037's corrected finding, re-confirmed) |
| Pipeline Save | `PUT …/application/prompt_lib/399/9506` | 201 |
| Execute (chat send) | WebSocket-driven; response settles in ~11 s "Thought" + streaming | — |

---

## Gotchas (for the implementer)

- **The pipeline CREATE form requires Description as well as Name** — Save
  (`agent-save-button`) stays `disabled` until both are filled (the form is
  formik-dirty + required-gated). The covering spec sidesteps this by creating via
  `pipeline_id` (API); keep doing that.
- **Enter does not send in the embedded chat composer.** Filling
  `chat-message-input` and pressing Enter leaves the text in the field and posts
  nothing. `chat-send-button` must be clicked — which is exactly what
  `PipelineDetailPage.send_message_in_embedded_chat()` already does. Do not
  "simplify" it to a keypress.
- **Node id contains a space** (`MCP 1`), so the interrupt-before testid is
  literally `pipeline-node-interrupt-before-toggle-MCP 1`. Existing helper
  `is_node_interrupt_before_toggle_visible(node_id)` handles it.
- Live MCP execution took **~40 s wall-clock** end to end this session; budget a
  180 s timeout, wait on the response-complete marker (`chat-delete-button` on the
  last message), never a sleep.

---

## Coverage Map

### Axis 1 — every element of the TMS case

| Case element | Expected result | Covered by | Asserted where | Disposition |
|---|---|---|---|---|
| Precondition: logged in | — | `auth_state` | fixture | covered |
| Precondition: a Remote MCP available | — | `mcp_toolkit_with_tools` fixture | fixture | covered (substituted MCP — declared) |
| Step 1 create pipeline, canvas loads | canvas loads | covering spec Step 1 (API-created pipeline + canvas assertions) | `test_pipeline_mcp_node_fresh_attach.py` Step 1 | already-covered |
| Step 2 TOOLS section visible | visible | covering spec Step 2 | same | already-covered |
| Step 3 four attach buttons present | all four present | **GAP 1** | new assertions, covering spec Step 2 | new |
| Step 4 click "+ MCP" | picker appears | covering spec Step 2 | same | already-covered |
| Step 5 picker lists MCPs | MCPs listed | covering spec Step 2 | same | already-covered |
| Step 6 select a Remote MCP | selected | covering spec Step 3 (+ PATCH 201) | same | already-covered |
| Step 7 card shows icon, name, "Show tools", connection status | all present | partly covering spec Step 4 (card exists); **GAP 2** for name + status; "Show tools" via ELITEA-2065 | new assertions, covering spec Step 4 | partial → new (icon: not asserted — decorative `<svg>`, no meaningful observable) |
| Step 8 click "Add node" | menu opens | covering spec Step 5 | same | already-covered |
| Step 9 menu lists MCP | MCP listed | covering spec Step 5 / ELITEA-2030 | same | already-covered |
| Step 10 click MCP | node added | covering spec Step 5 | same | already-covered |
| Step 11 node "MCP 1" with Input/Output ports | label + ports | covering spec Step 5 (node id `MCP 1` via `wait_for_node_on_canvas`); ports observed live as ReactFlow target/source handles | same | already-covered (ports implicit in the node id + the auto edge; not separately asserted — accepted, they are library internals) |
| Step 12 open config panel | panel opens | covering spec Step 6 (inline, no click) | same | already-covered + **clarification** (no right-hand panel) |
| Step 13 panel shows Trigger/Toolkit/Tool/Input/Output | all present | covering spec Step 6 (with Tool correctly asserted ABSENT pre-Toolkit, present post-Toolkit at Step 7) | same | already-covered |
| Step 14 select Toolkit | selected | covering spec Step 7 | same | already-covered |
| Step 15 Tool dropdown populates | tools listed | covering spec Steps 7–8 | same | already-covered |
| Step 16 select tool | selected | covering spec Step 8 | same | already-covered |
| Step 17 Input/Output variable chips | chips displayed | covering spec Step 10 | same | already-covered |
| Step 18 connect START → MCP 1 → END | nodes connected | — | — | **clarification** — no START node exists; MCP 1→END edge is auto-created from the default transition |
| Step 19 Save | saves | covering spec Step 11 | same | already-covered |
| Step 20 execute with a test message | execution triggered | **GAP 3** | new sibling test | new |
| Step 21 MCP node executes tool and returns output | output returned | **GAP 3** (`chat-answer-tool-chip` == `"{toolkit}: ask_question (MCP1)"` + non-empty `skill-test-last-response`) | new sibling test | new |
| § Expected Final State | pipeline executes, MCP tool output returned | GAP 3 | new sibling test | new |
| § Pass/Fail "without errors" | no errors | `assert not console_errors` (covering spec already registers the listener) | both tests | already-covered pattern |

### Axis 2 — observables asserted BEYOND the case

| Extra observable | Why (grounded) |
|---|---|
| The tool chip's text **correlates** the configured Toolkit+Tool with the executed one | The case says only "returns output". A non-empty answer alone would also pass if the pipeline silently fell back to a plain LLM answer with no MCP call — the chip is what proves the MCP node ran the *selected* tool. |
| `assert not console_errors` across the whole flow | Project convention on this surface (covering spec + ELITEA-2065 both do it); silent console errors during a WebSocket execution are exactly the class that ships. |
| Edge `MCP 1 → END` exists after Save+reload | Converts the case's unbuildable step 18 into the assertion that actually carries its intent (the node IS wired to END), instead of dropping it. |

---

## Blocked Steps

None.

## Known Defects

None found. Zero console errors across all 21 steps.

Two **testid gaps** (implementer work via `add-data-testid`, not defects):
`pipeline-tools-card-name`, `pipeline-tools-card-connection-status`.
