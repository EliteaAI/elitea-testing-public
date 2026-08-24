# Test Case: MCP Integration in Pipeline — MCP Node INPUT MAPPING Configuration

## Metadata
- **TMS ID**: ELITEA-1953
- **Linked Story**: none
- **Priority**: l2 (case metadata says `priority: high`; the covering spec and every MCP-node sibling on this suite are `p2` — keep the family marker)
- **Environment Explored**: local (`http://localhost:5173`, EliteaUI `automation/testids`, DEV backend, project `Private` id 399)
- **User set**: `${TEST_USER}` (localhost `auth_state` bypass via `VITE_DEV_TOKEN`)
- **Analyst**: qa-engineer (Sage), batch `mcp-w05`, cluster session with ELITEA-1952, 2026-08-24
- **Status**: extend-existing
- **surface_key**: pipeline-mcp-node
- **Live artifacts used this session**: pipeline `9506` (`autotest_mcp_pipeline_w05`), MCP toolkit `3270` (`autotest_mcp_w05`, DeepWiki fixture)

---

## Extension target

**Covering spec**: `automation/tests/ui/pipelines/test_pipeline_mcp_node_fresh_attach.py`
:: `test_mcp_node_fresh_attach`, merged to `origin/automation/base`
(AFS `l2_pipeline-mcp-node-integration-fresh-attach_ELITEA-2037.md`, TMS ELITEA-2037).

Same file as ELITEA-1952's extension in this batch — the two are separate AFS
(they differ in STEPS, not just data) but land in the same spec module.

### Behavioural overlap (what is already proven — re-confirmed LIVE this session)

| ELITEA-1953 step | Already proven by |
|---|---|
| 1 (open a pipeline with an MCP node that has a Toolkit) | covering spec Steps 1–7 build exactly this state |
| 2 (select a tool from the Tool dropdown) | covering spec Step 8 |
| 3 ("INPUT MAPPING (REQUIRED)" section shown) | covering spec Step 8 — `is_input_mapping_section_visible(2)` on `pipeline-mcp-node-input-mapping-heading` |
| 4, partly (all input parameters listed by NAME) | covering spec Step 8 — `is_mcp_node_input_mapping_value_visible("repoName"/"question")` |
| 8 (configure input-mapping value) | covering spec Step 9 — fills both, reads both back |
| 9/10, partly (Interrupt before, Interrupt after, Structured output toggles PRESENT) | covering spec Step 6 — visibility + `disabled` state of all three |
| 11 (Save succeeds) | covering spec Step 11 — `PUT … 201` |
| 12, partly (values persist after reload) | covering spec Step 12 — re-reads both Fixed values, Toolkit, Tool, Input, Output after a full page reload |

### The gap (why this is NOT `already-covered`)

The case's actual subject — the per-parameter **Type** control and its persistence —
is asserted **nowhere** on the MCP node:

1. **Step 4's "…and their TYPES"** — the covering spec asserts the Value fields exist
   but never reads the per-row **Type** select. Live, each parameter row renders
   `RepoName | Type: Fixed | Value: …`.
2. **Step 7 — change Type from "Fixed" to "Variable"** — not covered. And it is not
   *coverable* today: the MCP node's Type select carries **no testid** (see § Testid
   gaps) — `BaseToolNode.jsx` passes `typeTestIdPrefix` only for `nodeType === Toolkit`.
   ELITEA-2040's `lextend_pipeline-input-mapping-types-…` covers Fixed/F-String/Variable
   on the **LLM/HITL** nodes, a different component with a different DOM.
3. **Step 8's post-Variable value** — switching Type to `Variable` **swaps the Value
   widget** from a text input to a state-variable select; the existing
   `pipeline-mcp-node-input-mapping-value-{param}` testid **disappears** from the DOM
   in that branch. Nothing asserts the Variable-branch value at all.
4. **Steps 9/10's "disabled by default"** — the covering spec asserts the toggles'
   `disabled` *attribute* (which is structural: Interrupt-before is disabled because
   the node is the entry point; Interrupt-after because `transition == END`) but never
   asserts they are **OFF/unchecked**, which is what the case means. `ELITEA-2046`
   asserts default-unchecked for the **LLM** node's structured-output toggle only
   (`test_pipeline_structured_output_toggle_persistence.py:72-73` — `llm_node_…`).
5. **Step 12's persistence of the TYPE** — the covering spec re-reads Values, not Types.

Gap size: one new EliteaUI testid, one page-object method pair, ~6 assertions.
Comfortably an extension, not a rewrite.

### Recommended extension shape

Append a **new sibling test in the same file**,
`test_mcp_node_input_mapping_type_and_toggles_persist`, reusing the same
`pipeline_id` + `mcp_toolkit_with_tools` fixtures and the same
`PipelineDetailPage` navigation/selection methods the covering test already
uses. (A separate function rather than more steps on the existing one: the
covering test is already 12 steps / 264 lines and its subject is the
attach→add→configure flow; this case's subject is the Type control's behaviour
and persistence. Declared per `.agents/role-overrides.md`
§ Declared-improvisation protocol — the implementer may fold it in with reasoning.)

---

## Preconditions

- User authenticated (localhost: automatic via `VITE_DEV_TOKEN`).
- `mcp_toolkit_with_tools` fixture (DeepWiki MCP, 3 real tools).
- `pipeline_id` fixture (fresh empty pipeline).
- Reach the case's precondition state exactly as the covering spec does:
  attach the MCP to TOOLS → add an MCP node → select the Toolkit. **Transit only** —
  every observable this case asserts is read live off the product afterwards.

**Test-data substitution (declared).** The case's Test Data table is empty and its
example tool is `get_auth_user` (a zero-parameter tool — it would render *no* input
mapping at all, making the case unexecutable as literally written). Substituted with
`ask_question` (2 required string params: `repoName`, `question`), the same tool the
covering spec uses. Test data only; the observables are all system-produced.

---

## Test Steps — as EXECUTED live, 2026-08-24

| # | Action performed | Observed result | Verdict |
|---|---|---|---|
| 1 | Open pipeline 9506 with the MCP node, Toolkit `autotest_mcp_w05` selected | Config renders **inline on the node card** (not a right-hand panel — see § Case-text drift); `pipeline-mcp-node-tool-select` present | PASS |
| 2 | Select `ask_question` from the Tool dropdown | Tool combobox reads `ask_question` | PASS |
| 3 | Look for the input-mapping section | `pipeline-mcp-node-input-mapping-heading` appears, text **`Input mapping (required 2)`** (sentence case + a count — the case writes "INPUT MAPPING (REQUIRED)"; CSS uppercases it visually) | PASS |
| 4 | Read every parameter row | Two rows: **`RepoName`** and **`Question`** (capitalized DISPLAY labels of the raw schema keys `repoName`/`question` — the testids use the raw keys). Each row = `HeadingChip(name)` + a **`Type` select reading `Fixed`** + a `Value` field. **No JSON-schema data type (`string`) is displayed anywhere** — the "Type" the UI shows is the *mapping* type, not the parameter's data type (see § Case-text drift) | PASS-with-clarification |
| — | *(case has no steps 5–6; numbering jumps 4 → 7 in the TMS source)* | — | noted, not a gap |
| 7 | Open `RepoName`'s Type select and read the options | `select-option-fstring` ("F-String"), `select-option-variable` ("Variable"), `select-option-fixed` ("Fixed"). **The Type select trigger itself has NO testid** — `id="simple-select-Type"`, duplicated once per row (2 identical ids on this node) ⇒ positional-only today | PASS with **testid gap** |
| 7 | Click "Variable" | `RepoName` row's Type reads `Variable`; the second row still `Fixed` | PASS |
| 8 | Observe the Value widget after the type change | The Value **widget swaps**: `pipeline-mcp-node-input-mapping-value-repoName` **vanishes from the DOM**; in its place a `Select.SingleSelect` (`id="simple-select-[object Object]"`, **no testid**) auto-populated with **`input`**. The `Question` row keeps its text input (`…-value-question`) | PASS with **testid gap** |
| 8 | Fill `Question` = `What is this repository about?` | Value reads back | PASS |
| 9 | Read the interrupt toggles | `pipeline-node-interrupt-before-toggle-MCP 1`: **checked=false**, disabled=true (node is the entry point). `pipeline-mcp-node-interrupt-after-toggle`: **checked=false**, disabled=true (`transition == END`) | PASS |
| 10 | Read the structured-output toggle | `pipeline-mcp-node-structured-output-toggle`: **checked=false**, disabled=**false** | PASS (see § Case-text drift on the word "disabled") |
| 11 | Click Save | `PUT …/application/prompt_lib/399/9506` → **201** | PASS |
| 12 | Full page reload (`page.goto(canonical_url)`) and re-read everything | Types `["Variable", "Fixed"]` ✓ · Variable-branch value `input` ✓ · `Question` value `What is this repository about?` ✓ · Toolkit `autotest_mcp_w05` ✓ · Tool `ask_question` ✓ · heading `Input mapping (required 2)` ✓ · all three toggles unchanged (false/true, false/true, false/false) ✓ | PASS |

**Total: 11/11 authored steps executed (the case skips 5–6). All PASS. No defect.
0 console errors.**

---

## Case-text drift (CLARIFICATIONS — assert the live contract, do NOT file as bugs)

1. **Step 1 "Configuration panel is visible".** There is no separate configuration
   panel for a node — config is always-expanded **inline on the node card** on the
   canvas. Already the documented behaviour for every node type in
   `test-specs/pipelines/_surface.md`.
2. **Step 3 "INPUT MAPPING (REQUIRED)".** Live DOM text is
   `Input mapping (required 2)` — sentence case, with the parameter count. Assert
   with a count-aware matcher (`is_input_mapping_section_visible(2)`), never the
   uppercase literal.
3. **Step 4 "…with their names and types".** The UI shows the parameter NAME and a
   **mapping-Type select** (`Fixed`/`Variable`/`F-String`) — it does **not** display
   the parameter's JSON-schema data type (`string`). Assert name + mapping Type.
4. **Steps 9/10 "toggles are present (disabled by default)".** Live, all three
   toggles are **OFF (unchecked)** by default, which is the intent. Two of them
   additionally carry `disabled=true`, but for structural reasons, not "by default":
   Interrupt-before is disabled *because this node is the entry point*, Interrupt-after
   *because the node's transition is END*. **Structured output is NOT disabled** at
   all — it is simply unchecked. Assert `to_not_be_checked()` for all three, and the
   `disabled` states only with their structural reasons stated (as the covering spec
   already does).

---

## Gap assertions (what the implementer adds)

New sibling test `test_mcp_node_input_mapping_type_and_toggles_persist`:

1. **Type is listed per parameter and defaults to `Fixed`**
   `get_mcp_node_input_mapping_type("repoName") == "Fixed"` and same for `"question"`.
2. **Type options** — opening the Type select offers `Fixed`, `Variable`, `F-String`
   (option testids `select-option-fixed` / `-variable` / `-fstring`, the shared pattern).
3. **Change Type → `Variable`** on `repoName`;
   `get_mcp_node_input_mapping_type("repoName") == "Variable"` while
   `…("question") == "Fixed"` (the change is per-row, not global).
4. **The Value widget swapped, and the Variable-branch select reads `input`.**
   *(AMENDED at implementation, 2026-08-24.* This AFS specified an ABSENCE
   assertion — `…VALUE.format("repoName")` at `to_have_count(0)` — because before
   testid gap 2 landed, the row's value testid vanished in the Variable branch.
   Landing gap 2 gives BOTH widget shapes the same testid, which is the whole
   point of that gap, so the absence assertion is now false by construction and
   was replaced by a strictly stronger one: `text_content()` on that testid reads
   `"input"`. A text `<input>` has no text content, so only the state-variable
   select the Variable branch renders can yield it — the widget swap stays an
   enforced invariant, and the auto-bound value is asserted too.)
5. **All three toggles are unchecked by default** — `to_not_be_checked()` on
   `pipeline-node-interrupt-before-toggle-{node_id}`,
   `pipeline-mcp-node-interrupt-after-toggle`,
   `pipeline-mcp-node-structured-output-toggle`.
6. **Save → full reload → everything above still holds** (Types per row, the
   Variable-branch value, the Fixed value, all three toggle states).

### Testid gaps — `add-data-testid` work on `EliteaAI/EliteaUI`

Both are **one-line widenings of plumbing that already exists**, not new machinery:

| # | Element | Testid to add | File / line (on `origin/automation/testids`) |
|---|---|---|---|
| 1 | Input-mapping row **Type** select | `pipeline-mcp-node-input-mapping-type-{param}` (dynamic) | `src/[fsd]/features/pipelines/flow-editor/ui/nodes/BaseToolNode.jsx:208-212` — widen `typeTestIdPrefix={nodeType === …Toolkit ? \`${testIdPrefix}-input-mapping-type\` : undefined}` to also cover `…PipelineNodeTypes.Mcp`. The comment there explicitly says it was scoped to Toolkit "because the MCP node's equivalent select is untouched by any test" — **this case is that test**, so widening now satisfies canon ruling #511 rather than violating it. `InputMappingItem.jsx:214` already applies `data-testid={typeTestId}`. |
| 2 | Input-mapping **Value** select in the `Variable` branch | reuse the SAME `pipeline-mcp-node-input-mapping-value-{param}` string | `InputMappingItem.jsx` — **CORRECTED at implementation (2026-08-24):** the Variable branch is NOT the final non-enum `Select.SingleSelect` this AFS named. `FlowEditorHelpers.getEnumList('variable', …)` returns the state-variable list (`flowEditor.helpers.js:162`), so `enumList` is non-empty and the row renders the FIRST enum branch (`dataType !== 'array' \|\| type === 'variable'`). The testid went there (EliteaAI/EliteaUI@7a5fce32); the first attempt on the final select never appeared in the DOM. The final select stays untagged — no test references it. Adding it there gives the row's Value control **one stable testid across both widget shapes** — stable identity, exactly what `.agents/testing.md` § "Testid = stable identity" asks for, and NOT a state-switched testid (the value string does not change). |

**Do NOT widen `optionalHeadingTestId`** in the same edit — `ask_question` has zero
optional parameters, so this test never references it, and adding it would be an
unreferenced testid (blanket-add ban, `.agents/testing.md` § Locator policy).

Page-object work (this repo, no EliteaUI change):
`MCP_NODE_INPUT_MAPPING_TYPE = '[data-testid="pipeline-mcp-node-input-mapping-type-{}"]'`
as a class constant + `get_/select_mcp_node_input_mapping_type(param, …)` methods,
mirroring the already-merged `get_/select_toolkit_node_input_mapping_type`
(`pipeline_detail_page.py:5092-5120`) and `…custom_node…` (`:5264-5280`) exactly.

---

## Handles Reference (testid-only per `.agents/testing.md` § Locator policy)

Provenance verified 2026-08-24 with `cd ../EliteaUI && git fetch origin` first.

| Element | Handle (testid) | Provenance | Notes |
|---|---|---|---|
| Node Toolkit select | `pipeline-mcp-node-toolkit-select` (+`-combobox`) | on-`automation/testids` (runtime-composed via `TEST_ID_PREFIX_BY_NODE_TYPE` — a bare-substring grep for the full string finds nothing; verify via the `pipeline-mcp-node` prefix + the prop mechanism) | existing `PipelineDetailPage` field |
| Node Tool select | `pipeline-mcp-node-tool-select` (+`-combobox`) | same | conditionally rendered — absent until a Toolkit is picked |
| Input-mapping heading | `pipeline-mcp-node-input-mapping-heading` | same | text `Input mapping (required 2)` |
| Input-mapping Value (Fixed / F-String branch) | `pipeline-mcp-node-input-mapping-value-{param}` | same | class constant `MCP_NODE_INPUT_MAPPING_VALUE`; params are the RAW keys `repoName` / `question` |
| **Input-mapping Type select** | `pipeline-mcp-node-input-mapping-type-{param}` | **ADDED 2026-08-24** — EliteaAI/EliteaUI@5c24ed30 on `automation/testids` | `BaseToolNode.jsx`'s `typeTestIdPrefix` widened Toolkit → Toolkit\|Mcp |
| **Input-mapping Value (Variable branch)** | `pipeline-mcp-node-input-mapping-value-{param}` (same string as the Fixed branch) | **ADDED 2026-08-24** — EliteaAI/EliteaUI@7a5fce32 | on the enum/variable `Select.SingleSelect` branch — see § Gap assertions' correction |
| Type dropdown options | `select-option-fixed` / `select-option-variable` / `select-option-fstring` | on-main ✓ | shared app-wide `select-option-{value}` pattern |
| Interrupt before toggle | `pipeline-node-interrupt-before-toggle-{node_id}` | on-main ✓ | node_id has a SPACE (`MCP 1`); helper `is_node_interrupt_before_toggle_visible/disabled` exists |
| Interrupt after toggle | `pipeline-mcp-node-interrupt-after-toggle` | on-`automation/testids` (added by ELITEA-2037) | existing field |
| Structured output toggle | `pipeline-mcp-node-structured-output-toggle` | on-`automation/testids` (added by ELITEA-2037) | existing field |
| Save | `agent-save-button` | on-main ✓ | |

---

## Network Behavior

| Action | Request | Status |
|---|---|---|
| Change Type / fill Value | none (pure client state) | — |
| Save | `PUT …/application/prompt_lib/399/9506` | 201 |
| Reload | `GET …/application/prompt_lib/399/9506?…` | 200 — the persisted `input_mapping` (type + value per key) comes back and re-renders the correct widget per row |

---

## Gotchas (for the implementer)

- **The Value testid is branch-dependent TODAY.** ~~Until gap 2 lands, switching a
  row to `Variable` makes `pipeline-mcp-node-input-mapping-value-{param}`
  disappear.~~ **RESOLVED 2026-08-24** — gap 2 landed (EliteaAI/EliteaUI@7a5fce32),
  so the row's Value control carries the same testid in both widget shapes. Read it
  with `get_mcp_node_input_mapping_value()` while Type is Fixed/F-String (an
  `input_value()` read) and `get_mcp_node_input_mapping_variable_value()` while Type
  is Variable (a `text_content()` read) — the two shapes need different readers.
- **The canvas Control Panel intercepts clicks on the Input-mapping rows.** A
  freshly-added node spawns above ReactFlow's bottom-left `rf__controls` panel and,
  once the rows render, extends down over it; the panel's "Fit View" button then
  intercepts the pointer on the Type select's click (live-hit during
  implementation). Remedy: `move_node(node_id, dx=450, dy=0)` right after adding
  the node — same remedy `test_pipeline_interrupt_before_after_toggles.py:87` uses.
- **`id="simple-select-[object Object]"`** on the Variable-branch select is a real
  (cosmetic) id-computation slip in the shared component. It is not a functional
  defect and no assertion should depend on it — it is called out here only so nobody
  builds a positional locator on it.
- **Do not assert the raw schema key as the visible label.** The row heading reads
  `RepoName`/`Question` (display capitalization of `repoName`/`question`); the testid
  suffix is the raw key. Same precedent as ELITEA-1954/1955/2037.
- The case's step numbering skips 5–6 in the TMS source. That is the case text, not a
  missing observation — recorded in the Coverage Map so the reviewer doesn't hunt for
  dropped steps.

---

## Coverage Map

### Axis 1 — every element of the TMS case

| Case element | Expected result | Covered by | Asserted where | Disposition |
|---|---|---|---|---|
| Precondition: logged in | — | `auth_state` | fixture | covered |
| Precondition: pipeline with an MCP node, Toolkit + Tool selected | — | transit: covering spec's Steps 1–8 flow, reused | new test setup | covered (transit — declared) |
| Step 1 open pipeline, config panel visible | panel visible | covering spec Steps 1–7 (inline config) | `test_pipeline_mcp_node_fresh_attach.py` Step 6 | already-covered + **clarification** (inline, not right-hand) |
| Step 2 select a tool | tool selected | covering spec Step 8 | same | already-covered |
| Step 3 "INPUT MAPPING (REQUIRED)" section shown | section visible | covering spec Step 8 | same | already-covered + **clarification** (text is `Input mapping (required 2)`) |
| Step 4 all parameters listed with names… | names listed | covering spec Step 8 (`…value-repoName` / `…value-question` visible) | same | already-covered |
| Step 4 …and TYPES | types listed | **GAP — assertion 1** | new test | new (+ **clarification**: mapping type, not data type) |
| *(steps 5–6 absent from the TMS source)* | — | — | — | n/a — case text skips them |
| Step 7 change Type Fixed → Variable | type selector updates | **GAP — assertions 2 & 3** (+ testid gap 1) | new test | new |
| Step 8 configure input-mapping value | value set | partly covering spec Step 9 (Fixed branch); **GAP — assertion 4** for the Variable branch (+ testid gap 2) | covering spec Step 9 / new test | partial → new |
| Step 9 Interrupt before/after present, disabled by default | both visible + off | partly covering spec Step 6 (visible + `disabled` attr); **GAP — assertion 5** for unchecked | covering spec Step 6 / new test | partial → new |
| Step 10 Structured output present, disabled by default | visible + off | partly covering spec Step 6 (visible + NOT `disabled`); **GAP — assertion 5** for unchecked | covering spec Step 6 / new test | partial → new + **clarification** (control is not `disabled`; it is unchecked) |
| Step 11 Save | saves successfully | covering spec Step 11 | same | already-covered |
| Step 12 reload, input mapping persisted | settings unchanged | partly covering spec Step 12 (Values); **GAP — assertion 6** for Types + Variable-branch value + toggle states | covering spec Step 12 / new test | partial → new |
| § Expected Final State (type, value, toggles all persist) | persisted | GAP — assertion 6 | new test | new |
| § Pass/Fail "without errors" | no errors | `assert not console_errors` | new test | covered pattern |

### Axis 2 — observables asserted BEYOND the case

| Extra observable | Why (grounded) |
|---|---|
| The Type change is **per-row** (`question` stays `Fixed` while `repoName` becomes `Variable`) | The case says "change Type" singular; with two identical `#simple-select-Type` controls on the node, a regression that applied the change to every row would satisfy the case's literal wording and still be wrong. |
| The Fixed-branch Value testid has **count 0** after switching to `Variable` | Makes the widget-swap an enforced invariant instead of a documented assumption; also the reference that keeps both branches' testids honest per #511. |
| `assert not console_errors` | Project convention on this surface (covering spec + ELITEA-2065). |

---

## Blocked Steps

None.

## Known Defects

None found. Zero console errors across all executed steps.

Two **testid gaps** (implementer work via `add-data-testid`, not defects) —
`pipeline-mcp-node-input-mapping-type-{param}` and the Variable-branch reuse of
`pipeline-mcp-node-input-mapping-value-{param}`. Both are one-line widenings of
plumbing that already exists; exact files/lines in § Gap assertions.
