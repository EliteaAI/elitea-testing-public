# Test Case (family): Hovering a bar in an Analytics bar chart shows that entity's name and metric value

## Metadata
- **TMS IDs**: ELITEA-2327 (Agents & Pipelines tab), ELITEA-2328 (Tools tab)
- **Family AFS**: yes — the two cases differ **only in data** (which tab, which testids, which
  series name, which response fields). Every action, in the same order, with the same oracle shape.
  Downstream this is ONE parameterized spec with one row per case id.
- **Linked Story**: none
- **Priority**: l2
- **Environment Explored**: local (`http://localhost:5173`, `EliteaAI/EliteaUI` `automation/testids`)
- **User set**: `${TEST_USER}` (dev-token auth state on localhost)
- **Analyst**: qa-engineer, batch `settings-w06` (cluster ELITEA-2326/2327/2328/2329)
- **Status**: ready-for-automation (both members)
- **Case-text clarification filed**: elitea-testing-public#1955 for ELITEA-2327 only (chart is
  "Most Active Agents **& Pipelines**"; the tooltip metric is `Runs`, not an "event count").
  ELITEA-2328's text matches the live product exactly — no drift.

## Parameter table (one row per TMS case)

| | **ELITEA-2327** | **ELITEA-2328** |
|---|---|---|
| Tab | Agents & Pipelines | Tools |
| Tab testid | `analytics-tab-agents-pipelines` | `analytics-tab-tools` |
| Page-object entry | `open_agents_pipelines_tab()` | `open_tools_tab()` |
| Response captured | `analytics_agents/prompt_lib/` | `analytics_tools/prompt_lib/` |
| Chart title (live) | `Most Active Agents & Pipelines` | `Most Popular Tools` |
| Title testid | `analytics-agents-chart-title` | `analytics-tools-chart-title` |
| Container testid | `analytics-agents-chart-container` | `analytics-tools-chart-container` |
| Tooltip testid (**to add**) | `analytics-agents-chart-tooltip` | `analytics-tools-chart-tooltip` |
| Chart-render guard | `agentChartData.length > 0` (`AnalyticsAgents.jsx:102`) | `toolChartData.length > 0` (`AnalyticsTools.jsx:80`) |
| Tooltip **label** source | `rows[i].entity_name \|\| "Agent #" + rows[i].entity_id` (`AnalyticsAgents.jsx:57-64`, `XAxis dataKey="name"`) | `rows[i].tool_name` (`AnalyticsTools.jsx:37-45`, `XAxis dataKey="tool_name"`) |
| Series **name** | `Runs` (`<Bar name="Runs">`, `:156`) | `Calls` (`<Bar name="Calls">`, `:126`) |
| Series **value** source | `rows[i].events` (mapped onto `runs`) | `rows[i].calls` |
| Live example, bar 0 | `Reflexion` / `Runs: 24` | `load_skill` / `Calls: 188` |
| Live example, bar 1 | `User Story Creator` / `Runs: 19` | `pyodide_sandbox` / `Calls: 173` |

Both charts plot `rows.slice(0, 20)` — bar `i` is response row `i`, in response order.

## Preconditions
- User is authenticated (`auth_state` fixture); a project is selected.
- **The chart is conditionally rendered** — a project with no agent/pipeline runs (2327) or no tool
  calls (2328) in the range renders no chart at all, and the case is unrunnable there. This is real:
  live on 2026-08-28, project "Elitea Testing Team" over `Last 30d` had **`0 agents & pipelines`**
  and therefore **no bar chart** on the Agents tab, while project "Private" had 899. The spec must
  assert the precondition against the captured response (`len(response["rows"]) >= 2` — two, because
  step 4 needs a second bar to move to) so an unsuitable fixture project fails loudly with a clear
  message instead of a confusing locator timeout.
- **Neither bar chart renders a Legend** (live-confirmed: `.recharts-legend-wrapper` absent on
  both). The series NAME (`Runs` / `Calls`) therefore exists in the DOM **only inside the hover
  tooltip** — the same property that made the Health chart's tooltip assertion load-bearing.

## Test Data
### reuse-existing
Whatever agent/pipeline and tool activity the fixture project already has. Live 2026-08-28, project
"Private", `Last 30d`: 899 agents & pipelines (20 plotted, subtitle `Top 20 by runs`), 34 tools
(20 plotted, subtitle `Top 20 by usage`).

## Test Steps

1. Navigate to Settings -> Analytics, select `Last 30d`, then open the parameterized tab,
   **capturing that tab's response body** as the oracle for every value asserted below — case step 1.
   - **Verify**: the tab is selected (`aria-selected="true"`), the response is 200, and the tab's
     loading indicator has settled.
   - **Verify (precondition)**: `len(response["rows"]) >= 2`.
   - **Verify**: the chart container is visible and the chart title has the parameterized live text.
2. Hover **bar 0** — case step 2.
   - Read bar 0's own bounding box from the Recharts bar `<path>` nodes scoped inside the chart
     container, and drive a **real `page.mouse.move()`** to its centre. Targeting the bar's own box
     (rather than a fraction of the container) is what makes the index->row mapping in step 3 exact.
   - **Verify**: the parameterized tooltip testid becomes visible.
3. Verify the tooltip names the entity and its metric value — case step 3.
   - The tooltip is two lines: line 1 is the **label**, line 2 is `"{series name}: {value}"`.
   - **Verify**: line 1 equals the parameterized label for `rows[0]`
     (`entity_name || "Agent #"+entity_id` / `tool_name`).
   - **Verify**: line 2 equals `f"{series_name}: {fmt_num(rows[0][value_field])}"` — i.e. the
     literal series name (`Runs` / `Calls`) AND the value the backend reported for that row.
4. Move to a **different bar** (bar 1) and verify the tooltip updates — case step 4 /
   Expected Final State.
   - Drive a second real `page.mouse.move()` to bar 1's own bounding-box centre.
   - **Verify**: the tooltip is still visible and its full text **differs** from step 3's.
   - **Verify**: its label equals `rows[1]`'s parameterized label and its value line equals
     `f"{series_name}: {fmt_num(rows[1][value_field])}"`.
   - ⚠️ **Do NOT assert that the two labels differ.** Live-confirmed on the Agents chart: the
     top-20 x-axis categories are **not unique** — `guardrails_test_agent` appeared 3× and
     `elitea-1735-skills-agent` 6× (distinct entities sharing a name). Two adjacent bars can
     legitimately carry the same label. Keying every assertion on the bar **index** against
     `rows[i]` is what keeps this correct; comparing the full tooltip text (label + value) is the
     honest "it updated" check.
5. Move the cursor off the chart — **Axis 2**, beyond the case text.
   - **Verify**: the tooltip reaches **count 0** (`ChartTooltip` returns `null` when `!active`, so
     the node unmounts). Live-confirmed on both charts.
   - **Implementer amendment (2026-08-28): the pointer must TRAVEL, not teleport.** A single-jump
     `page.mouse.move()` off either bar chart left the tooltip stuck active (verified twice, with
     screenshots showing the cursor demonstrably landed in the table below / the sibling chart).
     `AnalyticsPage.move_mouse_off_chart()` moves with `steps=20` to the page header — the stream of
     intermediate `mousemove`s a real mouse emits, so it is a MORE faithful gesture, not a workaround.
6. No console errors throughout (`utils/console_errors.collect_console_errors`).

## Expected Results
- Hovering any bar raises a tooltip naming that bar's entity and its metric value, both matching the
  captured response row at the same index.
- Hovering a different bar re-renders the tooltip against that row.
- Moving off the chart removes the tooltip from the DOM.
- No console errors.

## Coverage Map

### Axis 1 — every element of the TMS cases
| Case element | Expected result | Covered by | Asserted where | Disposition |
|---|---|---|---|---|
| **2327/2328** Precondition: user logged in | — | `auth_state` fixture | fixture | covered |
| **2327** Step 1 — Navigate to Settings -> Analytics -> Agents tab | page loads | step 1 | tab `aria-selected`, 200, chart visible | covered (tab is live-named "Agents & Pipelines" — #1955) |
| **2328** Step 1 — Navigate to Settings -> Analytics -> Tools tab | page loads | step 1 | tab `aria-selected`, 200, chart visible | covered |
| **2327** Step 2 — Hover any bar in Most Active Agents chart | no error, expected UI state | step 2 | tooltip visible | covered (chart is live-titled "Most Active Agents & Pipelines" — #1955) |
| **2328** Step 2 — Hover any bar in Most Popular Tools chart | no error, expected UI state | step 2 | tooltip visible | covered |
| **2327** Step 3 — Tooltip shows agent name and its event count | condition holds | step 3 | label == `rows[0]` entity name; value line == `Runs: {fmt_num(rows[0].events)}` | covered **with clarification #1955** — the metric is labelled `Runs`, not "events"; the underlying response field IS `events`, so the value the case means is asserted, under the label the product actually renders |
| **2328** Step 3 — Tooltip shows tool name and its usage/call count | condition holds | step 3 | label == `rows[0].tool_name`; value line == `Calls: {fmt_num(rows[0].calls)}` | covered — case text matches live exactly |
| **2327** Step 4 / final — Different bar, tooltip updates with the correct agent and value | no error, expected UI state | step 4 | full text differs AND matches `rows[1]` | covered |
| **2328** Step 4 / final — Different bar, tooltip updates accordingly | no error, expected UI state | step 4 | full text differs AND matches `rows[1]` | covered |

### Axis 2 — observables asserted beyond the cases
| Observable | Why |
|---|---|
| Tooltip label/value equal the captured response row at the same index | The cases say "the correct agent and value" without an oracle. The response is the only honest one; asserting mere presence would pass on a tooltip showing the wrong row. |
| The series name literal (`Runs` / `Calls`) | Neither chart renders a legend, so the tooltip is the ONLY place these names exist in the DOM — a silent rename would otherwise go uncaught. |
| Tooltip unmounts on mouse-out (step 5) | ELITEA-2326 asserts this explicitly for the Overview chart; it is the same shared `ChartTooltip` mechanism, costs one mouse move, and catches a stuck-tooltip regression. Verified live on both bar charts. |
| No console errors | Standing convention on this surface. |

## Cleanup
None — read-only.

## Concrete Handles (discovered during exploration)

| Element | Handle (testid) | PROVENANCE | Notes |
|---|---|---|---|
| Agents & Pipelines tab | `analytics-tab-agents-pipelines` | on `automation/testids` only | already in `AnalyticsPage` |
| Tools tab | `analytics-tab-tools` | on `automation/testids` only | already in `AnalyticsPage` |
| Agents chart title | `analytics-agents-chart-title` | **on `main` ✓** | already in `AnalyticsPage` |
| Agents chart container | `analytics-agents-chart-container` | **on `main` ✓** | already in `AnalyticsPage` |
| Tools chart title | `analytics-tools-chart-title` | on `automation/testids` only | already in `AnalyticsPage` |
| Tools chart container | `analytics-tools-chart-container` | on `automation/testids` only | already in `AnalyticsPage` |
| Agents chart tooltip | `analytics-agents-chart-tooltip` | **added 2026-08-28 — EliteaAI/EliteaUI@c926ba66, on `automation/testids`** (awaiting human cherry-pick to `main`) | below |
| Tools chart tooltip | `analytics-tools-chart-tooltip` | **added 2026-08-28 — EliteaAI/EliteaUI@c926ba66, on `automation/testids`** (awaiting human cherry-pick to `main`) | below |

_All PROVENANCE rows verified 2026-08-28 with a fresh `cd ../EliteaUI && git fetch origin` plus the
two-stage grep from `.agents/workflow.md` § Closure record._

### testids needed
`components/ChartTooltip.jsx` **already has a `testId` prop** — both additions are **call-site-only,
no shared-component change**:

```jsx
// AnalyticsAgents.jsx:153
<RechartsTooltip content={<ChartTooltip testId="analytics-agents-chart-tooltip" />} />
// AnalyticsTools.jsx:123
<RechartsTooltip content={<ChartTooltip testId="analytics-tools-chart-tooltip" />} />
```

Same shape as the already-merged `analytics-user-detail-chart-tooltip` (`AnalyticsUserDetailed.jsx:246`,
on `main`) and `analytics-health-chart-tooltip`. Wire them **only** at these two call sites —
`ChartTooltip` is shared with Overview, Costs, Tokens, UserDetailed and AgentDetailed. Note
`AnalyticsAgents.jsx` has a **second** `<RechartsTooltip>` at `:218` for the *Chat Messages* area
chart — that one is out of scope for these cases; do not testid it.

### Bar bounding boxes (for steps 2 and 4)
Recharts' bar `<path>` nodes are library-internal DOM that cannot carry an app testid, so a **scoped
raw handle under the real testid parent** is used — the already-declared `.agents/testing.md`
§ Locator policy #579 exception 1, with the constant already owned by the page object:

- `RECHARTS_BAR_FILL = ".recharts-bar-rectangle path"` (`pages/analytics_page.py:192`), used as
  `self.<chart>_container.locator(RECHARTS_BAR_FILL)` — exactly the shape merged for
  `get_tools_chart_bar_fills()`. **No new exception is being introduced.**
- The bar paths mount **one animation tick after the container becomes visible** (already documented
  for this chart) — wait on `.first` being attached, never a sleep.
- **Implementer amendment (2026-08-28): capture EVERY bar's box in ONE pass BEFORE the first hover.**
  Hovering changes Recharts' active index, re-renders the `<Bar>` series and re-runs its grow
  animation, so a box read *after* a hover can come back `None` — this failed a full run on the Agents
  chart. `AnalyticsPage.get_chart_bar_boxes()` does the single pass and
  `hover_chart_bar_box()` moves to a captured box. A zero-valued row also renders a zero-height path
  with no usable box, so the two bars hovered are the first two WITH a box — the assertions still key
  on that bar's **index** against `rows[i]`, so the mapping stays exact (live: the Agents chart's
  hovered pair was not 0/1).

### Number formatting
Values render through `AnalyticCommonHelpers.fmtNum` (no `formatter` prop at either call site). The
Python port `fmt_num()` lived in `tests/ui/admin/test_analytics_overview_kpi_cards.py:62` on this
batch trunk; with this spec and ELITEA-2326 it passed its third consumer, so per Hard Rule 7 it was
**extracted to `automation/utils/analytics_format.py` (2026-08-28)** and every consumer imports it.

## Fidelity Declaration
**No substitutions.** The tooltip text is produced by the product in response to a **real
`page.mouse.move()`** (a genuine CDP input event), and every asserted value is compared against the
live `analytics_agents/` / `analytics_tools/` response body captured off the wire. No `page.route`,
no `route.fulfill`, no `page.evaluate`-dispatched events, no injected state.

## Network Behavior
- 2327: `GET /api/v2/elitea_core/analytics_agents/prompt_lib/{project_id}?date_from=...&date_to=...&limit=...&offset=...&search=...&sort_by=events&sort_order=desc`
- 2328: `GET /api/v2/elitea_core/analytics_tools/prompt_lib/{project_id}?...`
- Both fire on tab mount; 200 OK. **Hovering fires no request** — the tooltip is a pure client-side
  render over cached data. Never wait on `networkidle` (#1847).

## Blocked Steps
None. Both cases were executed live end-to-end (project "Private", `Last 30d`).

## Known Defects
None found for these cases. One case-text clarification: elitea-testing-public#1955 (ELITEA-2327),
cross-linked as a sibling of #1195.

## Live Observations (2026-08-28, localhost:5173, project "Private", `Last 30d`)
- **Agents & Pipelines** — title `Most Active Agents & Pipelines`, subtitle `Top 20 by runs`, count
  `899 agents & pipelines`, 20 bar paths, no legend, container `1212x200`.
  - bar 0 -> `Reflexion` / `Runs: 24`
  - bar 1 -> `User Story Creator` / `Runs: 19`  (tooltip updated)
  - mouse off the chart -> tooltip wrapper not visible, empty
  - x-axis categories NOT unique: `guardrails_test_agent` ×3, `elitea-1735-skills-agent` ×6
- **Tools** — title `Most Popular Tools`, subtitle `Top 20 by usage`, count `34 tools`, 20 bar
  paths, no legend.
  - bar 0 -> `load_skill` / `Calls: 188`  (cross-checks against Tool Details row 1: `load_skill | 188`)
  - bar 1 -> `pyodide_sandbox` / `Calls: 173`  (row 2: `pyodide_sandbox | 173`)
  - mouse off the chart -> tooltip not visible
- **Negative branch confirmed**: project "Elitea Testing Team" over `Last 30d` shows
  `0 agents & pipelines` and NO bar chart on the Agents tab — the `agentChartData.length > 0` guard
  is live-reachable, which is why the response-derived precondition in step 1 matters.
- Zero console errors across the whole walk.

## Implementation notes (2026-08-28, test-automation-engineer)
- One parameterized spec as specced:
  `automation/tests/ui/admin/test_analytics_bar_chart_tooltip.py`
  (`TestAnalyticsBarChartTooltip::test_bar_chart_hover_tooltip[ELITEA-2327-agents-pipelines]` and
  `[ELITEA-2328-tools]`).
- Step 1 selects `Last 30d` BEFORE opening the tab, so the tab query is issued for that range and the
  captured body is the oracle for the range under test.
