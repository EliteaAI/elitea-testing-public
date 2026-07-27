---
name: MCP pipeline node toolkit/tool switch quirks
description: Pipeline MCP-node config is always inline-expanded (no click-to-open); Toolkit switch resets/repopulates Tool; "Input/Output variables per tool" = a separate per-tool-parameter "Input mapping" accordion, NOT the generic Input/Output state-var dropdowns; missing testids inventory (now added on automation/testids, ELITEA-1955); bare pipeline URL 404 quirk; CORRECTED — MCP-attach popper uses toolkit-menu-item, NOT select-option-{value}
type: feedback
---

Context: ELITEA-1954 analysis session (issue #61), AFS at
`test-specs/pipelines/l2_mcp-node-change-toolkit-and-tool_ELITEA-1954.md`.

## The MCP node config panel is always inline-expanded

On the ReactFlow canvas, an MCP node's config fields (Trigger, Toolkit, Tool,
Input, Output, Interrupt before/after, Structured output) render directly on
the node card — there is **no click-to-open action**. If a TMS case describes
"click the node to open its configuration panel," that's stale case text
against the live UI (reverse-masking guard), not a defect — assert the fields
are visible without a preceding click.

## Two distinct "Input/Output" concepts — don't conflate them

1. **Generic state-variable selectors** — `#simple-select-Input` /
   `#simple-select-Output`. Options are pipeline-state keys (`input`,
   `messages`, ...). These do **NOT** change when the Toolkit/Tool changes —
   they're orthogonal, selecting which pipeline-state key feeds/receives the
   node.
2. **Per-tool "Input mapping (required N)" accordion** — appears/updates only
   after a Tool is selected, and lists the tool's actual parameter names (e.g.
   `ask_question`'s `RepoName`/`Question`) each with a Type (Fixed/...) +
   Value field. **This is what "Input/Output variables update according to
   new tool" means** in case text — asserting the wrong pair (the generic
   selectors) would be a false expectation; the live product's real per-tool
   signal is the mapping accordion.

## Toolkit → Tool reset behavior (confirmed correct, no defect)

Switching the Toolkit combobox immediately resets Tool to empty, and its
listbox repopulates with exactly the newly selected MCP's own tools — no
leakage from the previous MCP's tool set (verified 38 GitHub tools vs 3
DeepWiki tools, zero cross-contamination).

## Missing testids (flag to `add-data-testid`, not yet added as of this session)

- `#simple-select-Toolkit` / `#simple-select-Tool` / `#simple-select-Input` /
  `#simple-select-Output` (all scoped inside `[data-testid="rf__node-{name}"]`)
  — no `data-testid`, only a native MUI `id`.
- Input-mapping "Value" fields — no testid, no unique `name`/`id` per
  parameter row (`name="value"` on every row); located this session via
  positional `getByRole('textbox', {name:'Value'}).nth(i)`, which breaks if
  the tool's parameter order/count changes. Recommend dynamic
  `pipeline-mcp-node-input-mapping-value-{param_name}`.
- The pipeline Tools-section "MCP"/"Agent"/"Pipeline" add-tabs have no
  testid — only "Toolkit" does (`agent-add-toolkit-button`). Inconsistent;
  recommend `agent-add-mcp-button` etc. for parity.
- "Load Tools" button (MCP create/detail form) — no testid; located via
  text-filter locator this session.

Reusable/confirmed-working handles: `[data-testid="rf__node-{node_name}"]`
(ReactFlow node), `[data-testid="select-option-{value}"]` (shared dropdown-
option pattern across Toolkit/Tool/Input/Output AND the MCP-attach search
popper), `[data-testid="agent-save-button"]` (pipeline save, shared with
agent forms), `[data-testid="toolkit-type-card-mcp"]` (Remote MCP type
card, from ELITEA-1922 precedent).

## Environment/test-data gotcha: which MCPs actually have tools

In this environment (localhost DEV backend, project 399), pre-existing MCPs
are mostly dead-end for automation:
- `autotest_remote_mcp_full`, `verify_ttl_*`, `verify_secret_*` — point at
  placeholder URLs (`mcp.example.com`), zero tools ever loadable.
- `Remote Github`, `f` (Figma) — real servers but require an interactive
  OAuth login to reach "Connected" (though `Remote Github`'s tool list stays
  cached/selectable in dropdowns even while disconnected — useful as MCP #1
  without needing to complete OAuth).
- The public, auth-free `https://mcp.deepwiki.com/mcp` (tools:
  `read_wiki_structure`, `read_wiki_contents`, `ask_question`) is a good
  throwaway "real, working MCP with tools" fixture target when a test needs
  one without OAuth — created `autotest_deepwiki_mcp_1954` (id 1266) for
  this purpose; recommend the implementer's fixture do the same rather than
  reuse the placeholder-URL MCPs.

## Bare pipeline URL 404s — filed as clarification #512

`http://localhost:5173/pipelines/all/{id}` (no query params) renders "Page
not found"; only the app's own post-save URL shape
(`?destTab=configuration&name={name}&viewMode=owner`) loads. Unclear if
intentional (client-state-carried routing) or a gap — filed as a `question`,
not a `bug`. Practical implication: any test that reloads a pipeline mid-test
must reuse the full canonical URL (e.g. captured `page.url()`), never
construct a bare `/pipelines/all/{id}`.

## UPDATE 2026-07-18 (ELITEA-1955) — empty-Toolkit-before-attach + corrections

Context: ELITEA-1955 analysis session (issue #162), AFS at
`test-specs/pipelines/l3_mcp-node-without-toolkit-attached-first_ELITEA-1955.md`.
Covers the case this entry's original session didn't: an MCP node added
**before** any MCP is attached in TOOLS, and the transition when one gets
attached afterward.

**CORRECTION to this entry's line "select-option-{value} ... AND the
MCP-attach search popper" above — that's wrong.** Verified live this session
via `document.querySelectorAll('[data-testid="toolkit-menu-item"]')`: the
MCP/Toolkit/Agent/Pipeline "+"-button search popper's result rows all carry
the SAME shared testid `toolkit-menu-item` (`UnifiedDropdown.jsx`), disambiguated
by text filter — not `select-option-{value}` (that pattern belongs only to
`SingleSelectMenuItem.jsx`, used by the node's own Toolkit/Tool comboboxes).
Root cause of the original error: the browser-automation tool's
auto-generated Playwright code defaults to a role-based locator
(`getByRole('menuitem', {name})`) even when a testid exists on the element —
easy to mistake for "no testid present." Verify via `evaluate()` /
`get_attribute('data-testid')`, not the auto-generated code's locator choice.

**The `pipeline-mcp-node-*` testids this entry originally flagged as
missing now exist** — added on `automation/testids` (confirmed
`pipeline-mcp-node-toolkit-select`, `-tool-select`, `-input-mapping-heading`,
`-input-mapping-value-{param}`; still **not on `main`**, so still
`automation/testids`-only provenance). The TOOLS-section add-tabs also now
all have testids except Pipeline: `agent-add-toolkit-button`,
`agent-add-mcp-button`, `agent-add-agent-button` (confirmed on both `main`
and `automation/testids`) — only `agent-add-pipeline-button` is still
missing.

**Empty-Toolkit-dropdown state (before any MCP attached):** opening the
node's Toolkit combobox with zero MCPs in TOOLS renders MUI's own built-in
placeholder (`SingleSelect.jsx`'s `renderMenuItems`, `key="__empty__"`
branch: `<MenuItem value=""><em>None</em></MenuItem>`) — this placeholder
row carries **no `data-testid`** (confirmed via source + live DOM), even
though `SingleSelect.jsx` is first-party (`src/[fsd]/shared/ui/select/`),
not a third-party widget. Recommended assertion does NOT need a new testid:
count `[data-testid^="select-option-"]` == 0 after opening — that's the
existing real-option testid family, and its absence IS the "empty" signal.
Attaching an MCP via TOOLS afterward makes it appear in the SAME
already-rendered node's dropdown immediately — no node re-creation or page
reload needed.

**`open_mcp_node_toolkit_select()` breaks on the empty case.** The existing
page-object method (`pipeline_detail_page.py:798`, from ELITEA-1954) waits
for `[data-testid^="select-option-"]` to appear after clicking — which never
happens when the dropdown is genuinely empty, so it times out. Fix/variant:
wait on the SAME toolkit-select element's own `aria-expanded="true"`
attribute instead (confirmed this flips correctly regardless of option
count) — works for both empty and populated dropdowns.

**No `add_mcp()`-equivalent exists yet on `PipelineDetailPage`.**
`AgentDetailPage.add_mcp()` (`agent_detail_page.py:1108`) already implements
the "+ MCP" attach flow using testids confirmed to work identically on the
pipeline page (`agent-add-mcp-button`, `toolkit-search-input`,
`toolkit-menu-item`, `components.mui.Popper.select_menuitem`) since
`ApplicationTools.jsx`/`ToolMenu.jsx` is one shared component used by both
Agent and Pipeline detail forms. Port or extract to a shared mixin rather
than duplicating — flagged to the lead in the ELITEA-1955 AFS.

**Minor, non-blocking convention note:** `BaseToolNode.jsx`'s Input/Output
select testids are wired via a prop literally named `dataTestId`
(`FlowEditorSelect.InputSelect`/`OutputSelect`), which is the specific
forbidden shape per `.agents/testing.md` § Locator policy (`testId` /
`<part>TestId` only, never a `data` prefix). Pre-existing since ELITEA-1954,
no functional impact, not filed as a fresh defect — noted for a future
cleanup pass only.
