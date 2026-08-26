# Test Case: Remote MCP — Deselect/Select Specific Tools

## Metadata
- **TMS ID**: ELITEA-1935
- **Linked Story**: none
- **Priority**: l1 — TMS frontmatter says `priority: high` (the case body's own
  "Priority: medium" line contradicts its own frontmatter — the same
  frontmatter-vs-body drift already flagged in the ELITEA-1934 and ELITEA-1921
  AFS files). Filed `l1_` to match the *raw-JSON-edit family* this case is
  mechanically part of (`l1_edit-remote-mcp-modify-configuration-via-raw-json_ELITEA-1927`,
  `l1_edit-remote-mcp-modify-headers-json_ELITEA-1931`), all of which are `l1_`.
  Flagging, not resolving — does not block automation.
- **Environment Explored**: local (`http://localhost:5173`, `EliteaAI/EliteaUI`
  @ `automation/testids`, DEV backend, project id `399`)
- **User set**: `${TEST_USER}` (localhost: no login needed — `VITE_DEV_TOKEN`
  auto-auths the dev server)
- **Analyst**: qa-engineer (agent), session 2026-08-24, cluster dispatch with
  ELITEA-1936 (shared login/navigation/discovery only — **every step of this
  case was executed and observed individually**)
- **Status**: ready-for-automation

## Preconditions
- User is authenticated (localhost: automatic via `VITE_DEV_TOKEN`).
- Project context is set (project id `399` this session).
- A Remote MCP **with discovered tools** exists. The case's own precondition
  names a Tavily-based fixture ("Web Search" with `tavily_crawl`); **Tavily
  requires an API-key credential that is not provisioned in this environment**,
  so this AFS substitutes the project's standard public MCP fixture, exactly as
  ELITEA-1933/1934 already do:
  `https://mcp.deepwiki.com/mcp` → 3 tools
  (`ask_question`, `read_wiki_contents`, `read_wiki_structure`).
  The case's "Tool to deselect: `tavily_crawl`" therefore maps to
  **`ask_question`** — see § Test Data for why that specific tool.

## Test Data

### generate-per-test (seed in setup, delete in teardown)
- Toolkit Name: `autotest_conn_tools_<uuid4-hex-4>` — the toolkit-name field
  enforces `MAX_NAME_LENGTH = 32` as `inputProps.maxLength` and **silently
  truncates**, so compute the suffix against the literal base
  (`autotest_conn_tools_` = 20 chars → a 4-hex suffix lands at 24 ✓).
- Url: `https://mcp.deepwiki.com/mcp` (real, reachable, auth-free — must be
  dialled for real because this case's whole precondition is *discovered tools*).
- **Tool to deselect: `ask_question`.** This choice is load-bearing, not
  arbitrary: `selected_tools` renders one array element per line and
  `ask_question` sorts **first**, so it is a non-last element. Removing the
  **last** element (`read_wiki_structure`) would leave the preceding line's
  trailing comma dangling → invalid JSON → Save is refused. Any non-last
  element works; `ask_question` is the deterministic first one.

## Test Steps

> Setup (transit, not part of the case's own assertions — declare it as such):
> create the Remote MCP, click Load Tools, and Save, so the case starts from its
> stated precondition. Seeding via `ToolkitAPI` + a UI Load Tools click is the
> established pattern (`test_mcp_edit_raw_json_description.py`); a full UI create
> also works and is what the analyst drove this session.

1. Open the seeded Remote MCP's detail page
   (`${BASE_URL}/mcps/all/{toolkit_id}`) and wait for it to render.
   - **Verify**: `[data-testid="toolkit-detail-title"]` shows the toolkit's own
     name — **not** the placeholder `Edit MCP`. Use
     `McpFormPage.wait_for_page_load()`, which already excludes both
     `Edit Toolkit` and `Edit MCP` placeholders.
   - **Verify**: the detail page opens in Form view
     (`[data-testid="toolkit-form-view-toggle"]` has `aria-pressed="true"`).

2. Switch to Raw Json view by clicking
   `[data-testid="toolkit-raw-json-view-toggle"]`.
   - **Verify**: `[data-testid="toolkit-raw-json-editor-content"]` is visible.

3. Read `settings.selected_tools` from the Raw Json payload and note every tool
   name present.
   - **Verify**: `set(settings["selected_tools"]) == {"ask_question",
     "read_wiki_contents", "read_wiki_structure"}` and `len(...) == 3` (no
     duplicates). All three discovered tools start selected — confirmed live.
   - **Verify (analyst addition, Axis 2)**: `settings["available_mcp_tools"]`
     **is present** and holds one entry per discovered tool. See § Known
     Defects — this corrects the blanket claim in issue #574.
   - ⚠️ **Use `get_raw_json_full()`, never `get_raw_json()`.** With tools
     loaded the document is ~120 lines (the `args_schema` blocks) and CodeMirror
     **virtualizes** — a plain read returns a truncated, unparseable payload.

4. In the Raw Json editor, **delete the whole line** `"ask_question",` from the
   `selected_tools` array.
   - **Verify**: the `selected_tools` array in the editor no longer contains
     `ask_question`; the remaining two entries are untouched.
   - **Automation hint — this needs a NEW page-object helper**, see
     § Automation Hints. Deleting the line leaves the line's leading indentation
     behind (CodeMirror's `Home` is *smart-home*: it moves to the first
     non-whitespace character, so `Home` → `Shift+End` → `Backspace` clears the
     content but not the indent). That whitespace-only line is **valid JSON** and
     the server normalises it away on save — confirmed live.

5. Click Save (`[data-testid="toolkit-detail-save-button"]`).
   - **Verify**: `PUT /api/v2/elitea_core/tool/prompt_lib/{project}/{id}`
     returns **200** (observed live). Use
     `McpFormPage.save_and_wait_for_updated()`.
   - **Verify**: Save becomes disabled again once the form is no longer dirty.
   - ⚠️ **No success toast is rendered on the MCP detail Save** — do not wait on
     `toast-message` here (already documented in `_surface.md`).

6. Switch to Form view (`[data-testid="toolkit-form-view-toggle"]`) and inspect
   the Tools section.
   - **Verify**: `[data-testid="toolkit-tool-chip-ask_question"]` is **still
     present** but carries `data-selected="false"`.
   - **Verify**: `toolkit-tool-chip-read_wiki_contents` and
     `toolkit-tool-chip-read_wiki_structure` still carry `data-selected="true"`.
   - **Verify**: the chip count is still **3** — deselecting removes the tool
     from `selected_tools`, it does **not** remove the chip (the chip list is
     driven by `available_mcp_tools`). Asserting chip *absence* here would fail.
     Use `McpFormPage.is_tool_chip_selected(name)`.

7. Switch back to Raw Json and **re-add** `ask_question` to `selected_tools`.
   - **Verify**: `selected_tools` in the editor contains all three names again.
   - **Automation hint**: after the round-trip the array is back to two clean
     lines. Re-add with a **single-line replacement** using the existing
     `McpFormPage.fill_raw_json_line()`:
     `fill_raw_json_line('"read_wiki_contents",', '"ask_question", "read_wiki_contents",')`.
     JSON is whitespace-insensitive, so two names on one line is valid and the
     server normalises the formatting. **Verified live end-to-end.**

8. Click Save, then switch to Form view and verify the tool is selected again.
   - **Verify**: `PUT .../tool/prompt_lib/{project}/{id}` returns **200**.
   - **Verify**: all three chips carry `data-selected="true"`.
   - **Verify (analyst addition, Axis 2 — persistence)**: reload the page,
     re-open Raw Json, and confirm
     `settings["selected_tools"] == ["ask_question", "read_wiki_contents",
     "read_wiki_structure"]` server-side. Confirmed live via
     `get_raw_json_full()` after a full `page.reload()`.

## Expected Results

- `selected_tools` membership is fully controllable through Raw JSON edits.
- Removing a tool name deselects its chip in Form view **without removing the
  chip**; re-adding the name re-selects it.
- Both edits round-trip through a `200 PUT` and survive a reload.

## Coverage Map

### Axis 1 — Case coverage

| Case element | Expected result | Covered by | Asserted where | Disposition |
|---|---|---|---|---|
| Precondition: Remote MCP with discovered tools | fixture exists | Setup (seed + Load Tools + Save) | Setup | covered — **fixture substituted**: DeepWiki for Tavily (no Tavily credential in this env; same precedent as ELITEA-1933/1934) |
| Test Data: tool to deselect = `tavily_crawl` | — | § Test Data | — | mapped to `ask_question` (fixture substitution + must be a non-last array element) |
| 1 Open a Remote MCP that has discovered tools | Detail page loads | step 1 | step 1 | asserted |
| 2 Switch to Raw Json view | JSON editor is visible | step 2 | step 2 | asserted |
| 3 Locate `selected_tools` — note all tool names | All current tool names are noted | step 3 | step 3 | asserted (exact set + no duplicates) |
| 4 Remove one tool name from `selected_tools` | Editor shows array without that tool | step 4 | step 4 | asserted |
| 5 Click Save | Operation completes successfully | step 5 | step 5 | asserted (PUT 200 + Save re-disabled) |
| 6 Form view — removed tool no longer active as selected | Removed tool is no longer selected | step 6 | step 6 | asserted (`data-selected="false"`, chip still present) |
| 7 Raw Json — add the tool name back | Editor shows the tool re-added | step 7 | step 7 | asserted |
| 8 Save — verify tool reappears | Tool is selected again in Form view | step 8 | step 8 | asserted |
| Expected Final State: selection managed via Raw JSON, Form reflects state | — | steps 6 + 8 | steps 6 + 8 | asserted |

### Axis 2 — Analyst additions

- `step 3` asserts `available_mcp_tools` is **present** — *added: it is the
  companion field that makes the chip list render, and this session proved it
  appears once tools are discovered (correcting #574's blanket "never rendered").
  A regression that populated `selected_tools` but dropped `available_mcp_tools`
  would render zero chips while step 3's literal assertion still passed.*
- `step 6` asserts the chip **count stays 3** and the untouched chips stay
  selected — *added: the case only asks about the removed tool. Without this, a
  regression that wiped the whole array (or the whole chip list) would satisfy
  "removed tool is no longer selected" and pass.*
- `step 8` adds a **reload-and-reread** persistence check — *added: the case
  stops at the Form view, which reads from client-side Formik state. Without a
  reload the test cannot distinguish "saved" from "optimistically rendered", and
  the whole point of the case is that the edit reaches the server.*
- `step 5` asserts the **PUT status code** — *added: the case says "Operation
  completes successfully" with no observable; the 200 is the only honest
  system-produced signal, since this surface renders no success toast.*

## Cleanup

Delete the seeded toolkit in teardown (`ToolkitAPI` delete, or the UI
`controls-menu-button` → `toolkit-actions-delete-menuitem` →
`delete-confirm-dialog` flow already wired in `McpFormPage`). The MCP list is
already carrying ~18 `autotest_*` leftovers from prior sessions — do not add to
the pile.

## Concrete Handles (discovered during exploration)

All handles below were exercised live this session. **PROVENANCE verified
2026-08-24 with a fresh `git fetch origin` in `../EliteaUI`.**

| Element | Handle (testid-only) | Provenance | Notes |
|---|---|---|---|
| Detail title | `toolkit-detail-title` | on-main ✓ | shows `Edit MCP` placeholder until data lands |
| Form view toggle | `toolkit-form-view-toggle` | on-main ✓ | `aria-pressed` carries active state |
| Raw Json view toggle | `toolkit-raw-json-view-toggle` | on-main ✓ | |
| Raw Json editor content | `toolkit-raw-json-editor-content` | on-main ✓ | CodeMirror; **virtualized** — `get_raw_json_full()` only |
| Discovered tool chip (dynamic) | `toolkit-tool-chip-{tool_name}` | on-main ✓ | selection state is the **`data-selected`** attribute (`"true"`/`"false"`), NOT presence/absence. Class constant `McpFormPage.TOOL_CHIP` already exists. Chip `innerText` is empty — never assert on chip text. |
| Load Tools button (setup) | `toolkit-load-tools-button` | on-main ✓ | |
| Detail Save button | `toolkit-detail-save-button` | on-main ✓ | **not** `toolkit-form-save-button` — that one is create-form-only and does not exist here (cost the analyst one failed probe) |
| Remote MCP type card (setup) | `toolkit-type-card-mcp` | on-main ✓ | mounts **asynchronously — observed 3.5 s** this session (previously logged at ~1 s); rely on framework auto-waiting, never an immediate `query_selector` |
| Toolkit Name input (setup) | `toolkit-form-name-input` | on-main ✓ | |
| Url input (setup) | `toolkit-field-url-input` | on-main ✓ | inline on the create form; **collapsed** on the detail page behind `toolkit-configuration-show-more` |

**No new testid is required by this case** — every element it touches already
carries one, and all are on `origin/main`. This case is deployed-env promotable
on the testid axis the moment its test merges.

## Network Behavior

| Trigger | Request | Observed |
|---|---|---|
| Detail page open | `GET /api/v2/elitea_core/tool/prompt_lib/399/{id}?` | 200 |
| Save (step 5, step 8) | `PUT /api/v2/elitea_core/tool/prompt_lib/399/{id}` | 200, followed by a `GET` refetch |
| Load Tools (setup) | socket `test_mcp_connection` / `mcp_sync_tools` | tools returned in ~2 s |

## Known Defects Found During Exploration

**No product defect found.** All 8 case steps completed successfully against the
live local environment; the product behaved exactly as the case text describes.

Two **non-defect** findings were recorded:

1. **`available_mcp_tools` is conditional, not absent** — issue
   [#574](https://github.com/EliteaAI/elitea-testing-public/issues/574) records
   it as "the live product never renders it". That reading came from toolkits
   explored **before Load Tools**. Once tools are discovered the field is present
   and fully populated (confirmed here both in the editor and via
   `get_raw_json_full()`). Commented on #574 rather than filing a new issue.
   No change needed to `test_mcp_edit_raw_json_description.py` — its fixture
   legitimately has no tools loaded.
2. **`fill()` destroys the Raw Json document** — see § Automation Hints. An
   analyst tooling lesson, not a product issue.

## Blocked Steps

None.

## Automation Hints

- **New page-object helper required: `McpFormPage.delete_raw_json_line(current_line_text)`.**
  The existing `fill_raw_json_line()` *replaces* a line's content and cannot
  produce a deletion (`keyboard.type("")` is a no-op, leaving the selection
  intact). The shape verified live this session is the same select-then-act
  discipline, ending in a delete instead of a type:

  ```
  line = self.raw_json_editor_content.get_by_text(current_line_text, exact=True)
  line.click()
  self.page.keyboard.press("Home")        # smart-home → first non-whitespace
  self.page.keyboard.press("Shift+End")
  self._wait_for_line_selection_applied(line)
  self.page.keyboard.press("Backspace")
  self._wait_for_text_content_stable(self.raw_json_editor_content)
  ```

  It inherits `fill_raw_json_line`'s **declared #579 exception** verbatim
  (CodeMirror per-line `<div>`s are library-internal render nodes, scoped inside
  the testid-anchored `raw_json_editor_content` parent) — copy that docstring
  block across; do not re-derive the justification.

  **AMENDED at implementation (2026-08-24, implementer):** the shape above
  fails on *this* document. The moment the `Home`/`Shift+End` selection lands,
  CodeMirror's **selectionMatch** extension decorates every OTHER occurrence of
  the selected text with `cm-selectionMatch` `<span>`s — and `"ask_question",`
  occurs again inside `available_mcp_tools` as a `"value"` entry — so
  re-resolving the same `get_by_text()` locator for the selection wait raises
  `strict mode violation: ... resolved to 3 elements`. The **shipped** shape
  resolves the `ElementHandle` BEFORE the click and waits on that handle:

  ```
  line_handle = self.raw_json_editor_content.get_by_text(
      current_line_text, exact=True
  ).element_handle()
  line_handle.click()
  self.page.keyboard.press("Home")
  self.page.keyboard.press("Shift+End")
  self._wait_for_line_selection_applied_handle(line_handle)
  self.page.keyboard.press("Backspace")
  self._wait_for_text_content_stable(self.raw_json_editor_content)
  ```

  The same latent bug hit **step 7's `fill_raw_json_line`** call
  (`"read_wiki_contents",` also recurs as an `available_mcp_tools` `"value"`),
  so that pre-existing shared method was fixed the same way. It has exactly one
  merged caller (`test_mcp_edit_raw_json_description.py`), re-run green
  alongside both new specs — see the PR description.

- **A second new helper was required: `McpFormPage.scroll_raw_json_to_top()`.**
  The AFS's "do the per-line edit BEFORE any `get_raw_json_full()` call" hint
  cannot be honoured as written, because the case's own step order is read
  (step 3) *then* edit (step 4). The helper re-uses `get_raw_json_full()`'s
  scrollable-ancestor walk and sets `scrollTop = 0`; it is called before every
  per-line edit that follows a full read (steps 4 and 7).

- **Order matters: do the per-line edit BEFORE any `get_raw_json_full()` call.**
  `get_raw_json_full()` scrolls the CodeMirror viewport to the bottom to defeat
  virtualization and **leaves it there**. A `fill_raw_json_line()` immediately
  afterwards fails with `Locator.click: Timeout` because the target line has been
  virtualized out of the DOM. The analyst hit this exact failure; reordering the
  probe fixed it with no other change. If a read must precede an edit, scroll the
  editor back to the top first.

- **Never call `.fill()` on `toolkit-raw-json-editor-content`.** It is a
  contenteditable CodeMirror root, so `fill()` replaces the **entire document**
  with the argument (observed live: 29 lines collapsed to 1). Per-line editing is
  the only safe path. Nothing was saved in that state — Save correctly went
  disabled — but the editor had to be recovered with a reload.

- **`is_save_button_disabled()` targets the create-form Save** (`toolkit-form-save-button`).
  On the detail page use `detail_save_button` — the analyst lost one probe to a
  10 s timeout here.

- Wrap each step in `with allure.step("Step N — …"):` per
  `.agents/testing.md` § Step reporting.
- Markers: `ui`, `toolkits`, `mcp`, `p0`, `regression` (mirroring the sibling
  raw-JSON specs).
- Suggested spec: `automation/tests/ui/toolkits/test_mcp_toggle_selected_tools.py`.
- **Fidelity**: no substitution is specced. The Tavily→DeepWiki swap is a
  **fixture substitution in the precondition** (transit), not of the observable —
  every asserted value (`selected_tools` payload, chip `data-selected`, PUT
  status) is produced by the real system against a real MCP server.
