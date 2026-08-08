# Test Case: Pipeline — Export (verify downloaded file's structural content)

## Metadata
- **TMS ID**: ELITEA-2050
- **Linked Story**: none
- **Priority**: l2 (medium)
- **Environment Explored**: local (`http://localhost:5173`, `EliteaAI/EliteaUI` @ `automation/testids`, DEV backend, project `Private` id 399)
- **User set**: `${TEST_USER}` (localhost: no login needed — `VITE_DEV_TOKEN` auto-auths)
- **Analyst**: qa-engineer, batch `pipelines-remaining-w2`
- **Status**: extend-existing

## Extension target

**Covering spec**: `automation/tests/ui/pipelines/test_pipeline_import_via_file.py`,
function `test_pipeline_import_via_file` (bare function, no class),
Step 2 block at **lines 178–217**, merged onto this batch's trunk
`tests/batch-pipelines-remaining-w2` (originating commits `ff1ad9c9`,
`20c8cf0c` — ELITEA-2012).

**Behavioural overlap (what's already proven), live-reconfirmed this
session on a second pipeline** (`FullDetailsPipe_probe2`, id `6754`, three
export-menu clicks total across both sessions):
- Open an existing pipeline with nodes in the editor — case Step 1. Covering
  spec creates one via UI in its own Step 1 (name/description/chat
  starter/LLM node); reused live-reconfirmed this session by opening a
  pre-existing pipeline directly instead (transit, not a substitute for the
  case's own step — see below).
- Click the three-dot Actions menu → "Export" (`agent-actions-export-menuitem`,
  testid-based, via `PipelineDetailPage.export_pipeline_via_menu_and_download()`)
  — case Step 2.
- A file download fires (`page.expect_download()`, asserted at
  `test_pipeline_import_via_file.py:185-192`) and is non-empty
  (`:196-199`) — case Step 3. **CLARIFICATION (case-text drift, already
  filed** [#1334](https://github.com/EliteaAI/elitea-testing-public/issues/1334)
  **from ELITEA-2012, reconfirmed — not re-filed, see § Known Defects
  below): the case says "JSON file"; live product always downloads a
  `.pipeline.md` Markdown file with YAML frontmatter, confirmed live on
  BOTH the covering test's own pipeline and this session's
  `FullDetailsPipe_probe2` probe.**
- The downloaded file's content is parsed as YAML frontmatter and a subset
  of top-level fields is asserted: `name`, `description`, `agent_type`,
  `conversation_starters` (`:201-217`) — partial coverage of case Step 4
  ("Verify downloaded file contains pipeline structure (name, nodes,
  state, etc.)").

**The gap (why this isn't `already-covered`).** Case Step 4 explicitly
calls out **`nodes`** and **`state`** as required structural fields the
downloaded file must contain, in addition to `name`. The covering spec's
Step 2 parses the frontmatter and asserts `name`/`description`/
`agent_type`/`conversation_starters` — it never asserts anything about the
`nodes`/`entry_point`/`pipeline_settings` keys, even though the pipeline it
exports genuinely has an LLM node and those keys are genuinely present in
the downloaded content (confirmed live both sessions — see the raw content
captured below). This is a real, narrow automation gap: a future regression
that stripped node data from the export (e.g. a backend serialization bug
that emits only pipeline-level metadata) would not be caught by the
existing assertions.

**No literal top-level `state` key exists** — confirmed via source read
(`EliteaUI/src/pages/Common/Components/useExport.js`: pipelines/applications
export is server-rendered YAML at `GET .../export_import/prompt_lib/{project}/{id}?format=md`,
no client-side "state" concept) and via two live downloads. The case's
"name, nodes, state" wording maps onto the export's actual top-level shape:
`nodes:` (list of node definitions, present whenever the pipeline has
non-END nodes) + `pipeline_settings:` (canvas nodes/edges/positions — the
closest analogue to "state" in the case's loose wording). Not case-text
drift requiring a ticket (the case doesn't get a *wrong* answer, it just
uses the generic word "state" for what the product calls
`pipeline_settings`) — noted here for the implementer, not filed.

**Why case Step 1 (open an *existing* pipeline) doesn't require new
interaction code.** The covering spec creates its own pipeline via UI
immediately before exporting it (its own Step 1) — this already satisfies
"a pipeline with nodes is open" more strongly than the case's precondition
requires (a freshly-created, UI-verified pipeline vs. an arbitrary
pre-existing one). Re-driving navigation to a *different* pre-existing
pipeline would not add coverage, only test-data fragility (a fixture
pipeline could be deleted by another test). This session additionally
transited to a real pre-existing pipeline (`FullDetailsPipe_probe2`, id
`6754`) purely to cross-check the export content shape on a second,
independently-created pipeline — not proposed as the implementation's setup
path.

## Preconditions
- User is logged in (`auth_state` bypass on localhost via `VITE_DEV_TOKEN`).
- A pipeline with at least one non-END node exists and is open in the editor
  (covering spec's existing Step 1 setup — LLM node, System filled, Task
  mapped `Type=Variable/Value=input`).

## Test Data
- Reuses the covering spec's existing per-test pipeline (`pipeline_name`,
  `pipeline_description`, one chat starter, one LLM node) — no new fixture
  needed. This AFS adds assertions to an already-created download, it does
  not need its own pipeline.

## Test Steps

(Steps map onto the *existing* test's flow — the implementer inserts the new
assertions inside the existing Step 2 block, right after the current
`conversation_starters` assertion at line 217; steps upstream and downstream
are unchanged.)

1. Open an existing pipeline with nodes (covering spec's existing Step 1 —
   pipeline created via UI with an LLM node; `wait_for_node_on_canvas("llm")`
   confirms the node is present on the canvas before export). **Verify**:
   pipeline is loaded in the editor (case Step 1, already satisfied).
2. Click the three-dot Actions menu → "Export" (covering spec's existing
   `export_pipeline_via_menu_and_download()` call, `agent-actions-export-menuitem`).
   **Verify**: a file download fires and is non-empty (case Steps 2–3,
   already satisfied at lines 185–199).
3. **[GAP — new assertions, not currently in the covering spec]**
   Immediately after the existing `frontmatter.get("conversation_starters")`
   assertion (line 217), parse the same already-loaded `frontmatter` dict
   further:
   - `frontmatter.get("nodes")` is a non-empty list.
   - Exactly one entry in that list has `type == "llm"` (matching the
     pipeline's single LLM node) and that entry's `id` is non-empty
     (confirmed live: `id: LLM 1`, matching the canvas label).
   - `frontmatter.get("entry_point")` equals the LLM node's `id` (confirmed
     live: both `LLM 1`).
   - `frontmatter.get("pipeline_settings")` is a dict containing a `nodes`
     key whose value is a list with at least 2 entries (the LLM node +
     `END`, confirmed live) — this is the canvas-state structure the case's
     "state" wording maps onto.
   **Verify**: all four assertions pass (case Step 4).

## Expected Results
- Steps 1–2: unchanged from the existing covering spec — still pass.
- Step 3 (the gap): the downloaded `.pipeline.md` file's YAML frontmatter
  contains a non-empty `nodes` list with the pipeline's real node(s), a
  matching `entry_point`, and a `pipeline_settings` block with canvas node
  data — confirmed live on two independently-created pipelines this
  session, no product defect.

## Coverage Map

**Axis 1 — Case coverage**

| Case element | Expected result | Covered by (AFS step) | Asserted where | Disposition |
|---|---|---|---|---|
| Precondition: existing pipeline with nodes is open | Pipeline is loaded in the editor | step 1 | covering spec's existing UI-creation Step 1 + `wait_for_node_on_canvas("llm")` | asserted (existing) |
| 1 Open an existing pipeline with nodes | Pipeline is loaded in the editor | step 1 | covering spec's existing Step 1 | asserted (existing) |
| 2 Click three-dot menu → "Export" | Export action is triggered | step 2 | covering spec's existing `export_pipeline_via_menu_and_download()` call | asserted (existing) |
| 3 Verify a JSON file download starts | Browser initiates a file download | step 2 | covering spec's existing `page.expect_download()` + non-empty check | asserted (existing) — **CLARIFICATION: file is `.pipeline.md` (YAML frontmatter), not JSON; reconfirmed against already-filed #1334, not re-filed** |
| 4 Verify downloaded file contains pipeline structure (name, nodes, state, etc.) | JSON file content includes pipeline definition fields | step 3 | covering spec's existing `name`/`description`/`agent_type`/`conversation_starters` checks (partial) **+ NEW `nodes`/`entry_point`/`pipeline_settings` checks (gap)** | **gap — needs new assertions for `nodes`/`entry_point`/`pipeline_settings`; `name` already asserted** |
| Expected Final State: exported downloadable file with complete pipeline structure | — | steps 2–3 | steps 2–3 | asserted once the gap assertions land |
| Pass/Fail: all steps complete without errors; file downloaded; contains valid pipeline structure | — | all steps | all steps | asserted once the gap assertions land |

**Axis 2 — Analyst additions**

- Live cross-check on a SECOND, independently-created pipeline
  (`FullDetailsPipe_probe2`, id `6754`, zero non-END nodes) — *added: this
  pipeline's export has an EMPTY top-level `nodes:` key (omitted entirely,
  since it has no non-END node) while `pipeline_settings.nodes` still lists
  the `END` node — confirms the gap assertions' shape is genuinely dependent
  on the pipeline having a real node, i.e. the covering spec's own
  LLM-node pipeline is the right setup to assert `nodes` against (a
  bare/empty pipeline would make the "non-empty `nodes` list" assertion
  meaningless).*
- Console-error check across the export flow — *added: zero-cost, both
  sessions confirmed 0 errors (`browser_console_messages(level="error")`).*
- Source-level confirmation there is no literal `state` field (see §
  Extension target) — *added: prevents the implementer from asserting a
  key that doesn't exist and misreading that as a regression.*

## Cleanup
- Covering spec's existing cleanup (`pipeline_api.delete_pipeline(...)` in a
  `finally` block for both the original and imported pipeline ids) is
  unchanged and unaffected by this extension.
- This session's own probe export (`FullDetailsPipe_probe2`, id `6754`) was
  a read-only Export action on a pre-existing pipeline — no new pipeline was
  created, nothing to clean up. Downloaded files
  (`.playwright-mcp/fulldetailspipe-probe2-pipeline.md`) are local scratch
  artifacts, not test data.

## Concrete Handles (discovered during exploration)

No new testid work needed — this extension adds assertions on data already
captured by the existing `page.expect_download()` + `yaml.safe_load()` flow;
no new element interaction.

| Element | Testid | Provenance |
|---|---|---|
| Three-dot Actions menu button | `agent-actions-menu-button` | **on-main ✓** — reused unmodified from the covering spec / `PipelineDetailPage.actions_menu_button` |
| Actions menu "Export" item | `agent-actions-export-menuitem` | **on-main ✓** — reused unmodified from the covering spec / `PipelineDetailPage.export_menuitem` + `export_pipeline_via_menu_and_download()` |

## Network Behavior
- Export triggers a client-side `fetch()` to
  `GET /elitea_core/export_import/prompt_lib/{project}/{pipeline_id}?format=md`
  (confirmed via source read, `EliteaUI/src/pages/Common/Components/useExport.js`)
  which returns the raw `.pipeline.md` blob; the browser download is built
  client-side from the response blob (`URL.createObjectURL`), not a
  server-redirected navigation — no new network assertion needed beyond
  what the covering spec's `page.expect_download()` already captures.

## Known Defects Found During Exploration

**No new defect.** Case-text drift ("JSON file" vs. the actual `.pipeline.md`
Markdown/YAML-frontmatter file) is the SAME underlying pattern already filed
as [EliteaAI/elitea-testing-public#1334](https://github.com/EliteaAI/elitea-testing-public/issues/1334)
during ELITEA-2012's analysis (same object — `useExport.js`'s `doExport`
hard-codes `format=md` for both `pipelines` and `applications`; same
trigger — Export menu click; same expected/actual — case text says JSON,
product always emits MD). Per the dedup rule (same object + same trigger +
same expected/actual = duplicate), **not filed as a new issue** — instead
commented on #1334 confirming ELITEA-2050 independently reproduces the same
drift (see the issue for the full note, including the confirmed export YAML
top-level shape). Reconfirmed live on `FullDetailsPipe_probe2` (id `6754`,
filename `fulldetailspipe_probe2.pipeline.md`).

## Blocked Steps
None. All case elements were executed live this session (a fresh Export
click + content inspection on a second, independently-created pipeline,
cross-checked against the covering spec's own already-passing Step 2
assertions read from source).

## Automation Hints
- Framework: Playwright + pytest (confirmed, matches covering spec).
- Extend `test_pipeline_import_via_file`'s existing Step 2 `allure.step`
  block in-place — insert immediately after the current
  `conversation_starters` assertion (line 217), inside the same
  `with allure.step(...)` block (same allure step, no new step needed —
  these are still verifications of "the export produced correct content"):
  ```python
  nodes = frontmatter.get("nodes")
  assert isinstance(nodes, list) and len(nodes) > 0, (
      f"Exported frontmatter should contain a non-empty 'nodes' list, got: {nodes!r}"
  )
  llm_nodes = [n for n in nodes if n.get("type") == "llm"]
  assert len(llm_nodes) == 1 and llm_nodes[0].get("id"), (
      f"Exported frontmatter should contain exactly one LLM node with a "
      f"non-empty id, got nodes: {nodes!r}"
  )
  assert frontmatter.get("entry_point") == llm_nodes[0]["id"], (
      "Exported frontmatter entry_point should match the LLM node's id, got: "
      f"{frontmatter.get('entry_point')!r} vs node id {llm_nodes[0]['id']!r}"
  )
  pipeline_settings = frontmatter.get("pipeline_settings")
  assert isinstance(pipeline_settings, dict) and isinstance(
      pipeline_settings.get("nodes"), list
  ) and len(pipeline_settings["nodes"]) >= 2, (
      "Exported frontmatter pipeline_settings.nodes should list at least "
      f"the LLM node + END, got: {pipeline_settings!r}"
  )
  ```
- No new fixtures, no new page-object methods, no new testids — this is a
  pure assertion-insertion extension.
