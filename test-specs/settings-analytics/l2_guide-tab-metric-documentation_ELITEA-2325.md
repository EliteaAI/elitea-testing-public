# Test Case: Guide tab displays explanatory documentation for each metric

## Metadata
- **TMS ID**: ELITEA-2325
- **Linked Story**: none
- **Priority**: l2
- **Environment Explored**: local (`http://localhost:5173`, `EliteaAI/EliteaUI` `automation/testids`)
- **User set**: `${TEST_USER}` (dev-token auth state on localhost)
- **Analyst**: qa-engineer, batch `settings-w06` (cluster ELITEA-2311/2322/2323/2324/2325)
- **Status**: ready-for-automation
- **Case-text drift filed**: elitea-testing-public#1950 (`Calculation` / `Data source` are optional
  per metric — 14 and 7 of 43; the blue highlight is on the VALUE, not the label)

## Preconditions
- User is authenticated (`auth_state` fixture); a project is selected.
- **No data preconditions.** The Guide tab is entirely static: it renders
  `AnalyticsCommonConstants.GUIDE_SECTIONS` and issues **no** network request of its own. It is the
  only tab in this feature that is project- and date-range-independent.

## Test Data
### static-content
Driven by the `GUIDE_SECTIONS` constant (9 sections, 43 metric entries). The test asserts the
case's named section and subsections by exact text and everything else structurally, so a content
edit elsewhere in the constant does not break it.

## Test Steps

1. Navigate to Settings -> Analytics and open the **Guide** tab (`analytics-tab-guide`) —
   case step 1.
   - **Verify**: the tab is selected (`aria-selected="true"`).
2. Verify the tab loads documentation and is not blank (case step 2).
   - **Verify**: at least one `analytics-guide-section` is rendered (live: 9) and at least one
     `analytics-guide-metric` (live: 43).
   - **Verify**: the section titles (`analytics-guide-section-title`) in rendered order are exactly
     `["Overview Tab", "Overview Charts", "Costs Tab", "Tokens Tab", "Agents & Pipelines Tab",
     "Tools Tab", "Users Tab", "Health Tab", "General Concepts"]`.
3. Verify the case's named section and subsections (case step 3).
   - **Verify**: a section whose title is `Overview Tab` exists, and the metric names
     (`analytics-guide-metric-name`) **within that section** include, in order, `TEAM`,
     `AI ACTIVE`, `Adoption Rate`, `LLM CALLS`. (Live the section carries 8 metrics: those four
     plus `TOOL RUNS`, `CHAT MSG`, `AGENT & PIPELINE RUNS`, `COST` — asserted as a superset in the
     given order so the case's four are pinned without freezing the whole list.)
4. Verify each of those four metrics shows description + Calculation + Data source, with the blue
   highlight (case step 4) — **scoped to the four metrics step 3 names**, per #1950.
   - For each of `TEAM`, `AI ACTIVE`, `Adoption Rate`, `LLM CALLS`:
     - **Verify**: its description (`analytics-guide-metric-description`) is non-empty after strip.
     - **Verify**: the metric block's text contains the literal labels `Calculation:` and
       `Data source:`.
     - **Verify**: its `analytics-guide-metric-calculation-value` and
       `analytics-guide-metric-source-value` are visible, non-empty, and each has computed
       `color == rgb(88, 166, 255)` (`#58A6FF`, `styles.guideCalcValue`) — the "highlighted in
       blue" the case describes.
   - **Verify (the general contract, asserted honestly)**: **every** rendered
     `analytics-guide-metric` has a non-empty name and a non-empty description; and for every metric
     block, a `Calculation:` label is present **iff** a `analytics-guide-metric-calculation-value`
     is present (same for `Data source:`), i.e. label and value are never orphaned from each other.
5. Verify the Guide content is readable and not truncated (case step 5, Expected Final State).
   - **Verify**: for every rendered `analytics-guide-metric-description`, the computed
     `text-overflow` is not `ellipsis` and `scroll_height <= client_height + 1` and
     `scroll_width <= client_width + 1` — no clipped text.
   - **Verify**: the guide container is not internally clipped
     (`scroll_height <= client_height + 1` on the section list's parent).
6. No console errors throughout (`utils/console_errors.collect_console_errors`).

## Expected Results
- The Guide tab renders 9 documentation sections with 43 metric entries; the `Overview Tab` section
  documents `TEAM`, `AI ACTIVE`, `Adoption Rate` and `LLM CALLS`, each with a description plus a
  blue `Calculation` and `Data source` value; no description text is clipped or truncated.

## Coverage Map

| Case element | Expected result | Covered by (AFS step) | Asserted where | Disposition |
|---|---|---|---|---|
| 1 Navigate to Analytics -> Guide tab | Page/section loads | step 1 | tab `aria-selected` | asserted |
| 2 Tab loads a documentation page (not blank) | Condition holds | step 2 | ≥1 section and ≥1 metric rendered; exact 9-title tuple | asserted |
| 3 Sections present: Overview Tab, with subsections TEAM, AI ACTIVE, Adoption Rate, LLM CALLS | Condition holds | step 3 | section located by title; the 4 metric names present in order within it | asserted |
| 4 Each metric section shows description, Calculation (blue), Data source (blue) | Condition holds | step 4 | the 4 named metrics fully; all 43 metrics for name + description + label/value pairing | **clarification** — "each metric" is false product-wide: `Calculation` on 14/43, `Data source` on 7/43, and even `COST` inside the case's own section has neither (#1950). The blue is on the VALUE, not the label. |
| 5 / Expected Final State — content is readable and not truncated | Condition holds | step 5 | no `ellipsis`, no clipped scroll box on any description or on the container | asserted |

**Axis 2 — Analyst additions.**
- **Exact 9-section-title tuple** (step 2) — *added: "not blank" is a weak observable that a single
  stray element would satisfy; the title tuple is the cheapest assertion that actually proves the
  documentation rendered, and it is static content so it cannot flake on data.*
- **Label-iff-value pairing across all 43 metrics** (step 4) — *added: this is the honest
  generalisation of the case's "each metric section shows…" intent. It cannot be satisfied
  vacuously and it catches the real regression (a rendered `Calculation:` label with its value
  dropped, or vice versa) that the stale fixed claim was reaching for.*
- **Non-truncation asserted mechanically** (step 5) — *added: "readable and not truncated" is a
  visual-judgment phrase; `text-overflow != ellipsis` plus `scrollHeight <= clientHeight` makes it a
  real, deterministic assertion instead of a screenshot.*
- **Console-error check** (step 6) — *standing project convention.*

## Cleanup
None — read-only, no network, no state.

## Concrete Handles (discovered during exploration)

`AnalyticsGuide.jsx` currently has **ZERO testids** — every handle below except the tab is new work.

| Element | Locator | PROVENANCE |
|---|---|---|
| Guide tab | `analytics-tab-guide` | on-main ✓ |
| Section card (repeated, ×9) | **testid needed: `analytics-guide-section`** | needs-adding — on the `GUIDE_SECTIONS.map()` `<Box sx={styles.chartCard}>` |
| Section title (repeated, ×9) | **testid needed: `analytics-guide-section-title`** | needs-adding — on the `{section.title}` `<Typography>` |
| Metric block (repeated, ×43) | **testid needed: `analytics-guide-metric`** | needs-adding — on the `section.metrics.map()` `<Box sx={styles.guideItem}>` |
| Metric name (repeated, ×43) | **testid needed: `analytics-guide-metric-name`** | needs-adding — on the `{m.name}` `<Typography>` |
| Metric description (repeated, ×43) | **testid needed: `analytics-guide-metric-description`** | needs-adding — on the `{m.description}` `<Typography>` |
| Calculation value (repeated, ×14) | **testid needed: `analytics-guide-metric-calculation-value`** | needs-adding — on the `{m.calculation}` `<Typography sx={styles.guideCalcValue}>` inside the `{m.calculation && …}` branch |
| Data-source value (repeated, ×7) | **testid needed: `analytics-guide-metric-source-value`** | needs-adding — on the `{m.source}` `<Typography sx={styles.guideCalcValue}>` inside the `{m.source && …}` branch |

**Implementer notes on the testid work.**
- The `Calculation:` / `Data source:` **labels** deliberately get **no** testid: the test asserts
  their presence through the metric block's own text content, so a label testid would be an
  unreferenced addition (`.agents/testing.md` § Locator policy — scope is load-bearing; canon #511).
- The two value testids sit inside `{m.calculation && …}` / `{m.source && …}` conditional blocks.
  This is **conditional rendering of a whole subtree**, not a state-switched testid value on a live
  element — the PR #581 anti-pattern does not apply. The step-4 label-iff-value assertion references
  both the present and absent cases (`to_have_count(0)` on metrics that carry no calculation), which
  also satisfies the canon #277 both-branches-referenced discipline.
- All seven are plain attributes on existing nodes — no new DOM node, no new hook, no replaced MUI
  built-in (`add-data-testid` § Step 5.5). `AnalyticsGuide.jsx` is feature-scoped, so
  `analytics-guide-*` naming is correct at the definition site.
- Page object: extend `automation/pages/analytics_page.py` with class-level `LocatorDescriptor`
  fields and an `open_guide_tab()`. **No settle-on-response wait exists or is needed** — the Guide
  tab fires no request; wait on the first section becoming visible.

## Fidelity Declaration
No substitutions. All content is rendered by the live product from its own bundled constant; every
assertion reads the live DOM. No `page.route`, no `route.fulfill`, no injected state.

## Network Behavior
**None.** Opening the Guide tab issues no analytics request (verified live — the tab body is a pure
render of `GUIDE_SECTIONS`). Do not write an `expect_response` wait for this tab; waiting on
`networkidle` is likewise wrong here (#1847). Wait on the first `analytics-guide-section` instead.

## Blocked Steps
None.

## Known Defects
None found on this tab. #1950 is a case-text clarification, not a product defect.

## Live Observations (2026-08-28)

- **9 sections**: `Overview Tab`, `Overview Charts`, `Costs Tab`, `Tokens Tab`,
  `Agents & Pipelines Tab`, `Tools Tab`, `Users Tab`, `Health Tab`, `General Concepts`.
- **`Overview Tab` section — 8 metrics**: `TEAM`, `AI ACTIVE`, `Adoption Rate`, `LLM CALLS`,
  `TOOL RUNS`, `CHAT MSG`, `AGENT & PIPELINE RUNS`, `COST`. The first seven carry both
  `Calculation:` and `Data source:`; **`COST` carries neither**.
- **Whole tab**: `Calculation:` appears 14×, `Data source:` 7×, and exactly 21 elements compute to
  `rgb(88, 166, 255)` — i.e. the blue is on the values (14 + 7), never on the labels.
- Sample content (`TEAM`): description 215 chars; `Calculation: X = Count of distinct user IDs with
  at least one event in the date range. Y = Count of distinct user IDs in the project (all time, no
  date filter).`; `Data source: All event types (api, socketio, llm, tool, agent, rpc).`
- **No truncation**: every Overview-section description has `overflow: visible`,
  `text-overflow: clip`, `white-space: pre-line` and `scrollHeight == clientHeight`; the container
  is not clipped either.
- Zero console errors.


## Implementation notes / AFS amendments (ELITEA-2325, 2026-08-28 — implementer)

- **Shipped as** `automation/tests/ui/admin/test_analytics_guide_tab.py`
  (`TestAnalyticsGuideTab::test_guide_tab_metric_documentation`). All 7 testids added as specced —
  EliteaAI/EliteaUI@bc50bd9d.
- **AMENDED — metric count.** The AFS records 43 metric entries; live is **44** (the constant has
  grown). No assertion depended on the exact number — the spec asserts `>= 1` metric, the exact
  9-title tuple, and the case's four named metrics — so nothing had to change. Recorded here so the
  next reader is not surprised by the discrepancy.
- **AMENDED — step 5's container check.** The AFS asked for a clipping check on "the section list's
  parent". That `<Box>` carries no testid and the case never touches it, so adding one would be an
  unreferenced testid (scope is load-bearing, canon #511). The shipped assertion checks each of the
  9 SECTION CARDS instead (they do carry `analytics-guide-section`) — equivalent evidence that no
  guide content is internally clipped, with no new handle.
- Per-metric `text-overflow` and `scrollHeight`/`clientHeight` are read via read-only
  `Locator.evaluate` (`AnalyticsPage.is_element_clipped`) — the only way to reach those properties;
  it observes what the product laid out and injects nothing.
