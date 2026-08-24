# AFS — ELITEA-1949: MCP Type Selection — Local vs Remote Display

| Field | Value |
|---|---|
| **TMS case** | ELITEA-1949 |
| **Status** | `ready-for-automation` |
| **Priority** | medium (`p2`) |
| **Surface** | UI — MCP **type picker** (`/mcps/create`), `ToolkitTypeSelector` → `GroupedCategory` → `CategoryFilter` |
| **Feature dir** | `test-specs/mcp/` · suite dir `automation/tests/ui/toolkits/` |
| **Analysed** | 2026-08-24, live against `http://localhost:5173/mcps/create`, project 399 |
| **Analyst** | qa-engineer (Sage), batch `mcp-w03` |
| **Case snapshot** | `.agents/automation/mcp-w03/cases/ELITEA-1949.md` |
| **Defects filed** | **#1742** — `[Clarification][ELITEA-1949]` (`question` + `case-text-drift`): step 7's Expected Result does not match the live product. |

---

## Verdict in one line

**Steps 1-6 and 8 pass verbatim. Step 7 diverges** — selecting the `Local` filter does
not leave "only the Local section visible"; it unmounts the Local section entirely
(heading, empty-state message and Documentation link) and renders the generic catalog
`No MCPs found` state instead. The product is coherent-by-design here, so this is
**case-text drift, not a defect** (reverse-masking guard) — the spec asserts the **live**
contract and #1742 records the wording fix.

---

## Why this is NOT already covered

| Merged spec | What it proves | Why it is not this case |
|---|---|---|
| `automation/tests/ui/toolkits/test_mcp_type_filter.py` (ELITEA-1942) | The MCP **dashboard**'s right-hand "Types" panel (`tags-panel-chip-{Type}`) filters the **MCP list** server-side | Completely different surface and different component. `/mcps/all`'s `Categories.jsx` panel vs `/mcps/create`'s `CategoryFilter.jsx` chip row. Different testids, different mechanics (server query vs pure client-side grouping), different empty states. |
| `automation/tests/ui/toolkits/test_mcp_create_validation.py`, `test_mcp_create_remote.py` | Reach `/mcps/create` and click `toolkit-type-card-mcp` as **transit** | They use the type picker to get to the form; nothing asserts the picker's own heading, sections, Documentation link or filter chips. |

⇒ `ready-for-automation` (fresh spec).

---

## Preconditions

- Logged in (localhost `auth_state` bypass via `VITE_DEV_TOKEN`).
- **URL:** the case writes `/app/mcps/create`. `APP_PREFIX` is **empty on localhost** —
  navigate with the bare path `/mcps/create` and let `settings.app_base_url` inject the
  prefix per environment. Do **not** hardcode `/app`.
- **Read-only case** — nothing is created, nothing is mutated, no cleanup needed.

### Environment fact this case sits on top of

`GET /toolkit_types/prompt_lib/{project}?mcp=true` → `{"rows": ["mcp"], "total": 1}`, so
the **Local category is genuinely empty and no Local MCP can be created here**
(question **#1738**, OPEN, now gating a fourth case). That is *why* the Local section
renders its empty-state placeholder at all — the case is written for exactly this state,
so it is automatable as written. If a Local MCP ever appears in DEV, steps 3, 4 and 7
change meaning and this AFS must be re-run.

---

## Execution log — case steps as executed (all live, 2026-08-24)

| # | Case action | Case expected | **Observed live** | Verdict |
|---|---|---|---|---|
| 1 | Navigate to `/app/mcps/create` | Page loads at the correct URL | `http://localhost:5173/mcps/create` loads; document title becomes `MCPs - project_user_659` | ✅ |
| 2 | Verify heading "Choose the MCP type" | Heading visible | Rendered by `CategoryFilter.jsx:33-39` (`Typography variant="headingSmall"`), text exactly `Choose the MCP type`. **No testid** → work order below | ✅ (testid needed) |
| 3 | Verify Local section message | Correct message displayed | `mcp-type-picker-local-empty-state` text = `Still no local MCP available. Follow creation guides in our Documentation.` | ✅ |
| 4 | Verify "Documentation" is a link to `https://docs.elitea.ai/integrations/mcp/create-and-use-server-stdio` | Link present, correct URL | `<a>` inside the empty state: `href` = exactly that URL, text `Documentation`, `target="_blank"`, `rel="noopener noreferrer"`. **No testid** → work order below | ✅ (testid needed) |
| 5 | Verify Remote section shows "Remote MCP" card with icon | Remote MCP card visible | `toolkit-type-card-mcp` visible, text `Remote MCP`. Section heading `Remote` renders above it. Icon is an untestid'd `<Box>` inside the card — see Coverage Map | ✅ |
| 6 | Verify type filter buttons "Local" and "Remote" present | Both filter buttons shown | Exactly 2 chips, labels `Local` and `Remote`. **Both share the SAME testid `category-filter-tab`** and carry **no state attribute** → work order below | ✅ (testid needed) |
| 7 | Click "Local" filter — only Local section content shown | **Only Local section is visible** | ❌ **DIVERGES.** Local chip lights up (background `rgb(0,109,209)`), but: `mcp-type-picker-local-empty-state` count **0**, `toolkit-type-card-mcp` count **0**, no section headings at all, and the catalog renders `catalog-no-results-title` = `No MCPs found` / `catalog-no-results-description` = `Try adjusting your search terms`. Evidence: `test-results/screenshots/ELITEA-1949-step-07-local-filter-no-results.png` | ⚠️ **clarification #1742** — assert the live contract |
| 8 | Click "Remote" filter — only Remote section content shown | Only Remote section is visible | ✅ Remote section renders with `toolkit-type-card-mcp`; `mcp-type-picker-local-empty-state` count 0. **Note: the chips are MULTI-SELECT** — after the case's own 7→8 sequence *both* chips are lit, and the result still holds (Local has no items to contribute). Deselecting `Local` afterwards leaves Remote-only selected and the same single Remote section | ✅ |
| — | Expected Final State: Remote filter shows only the Remote MCP card; Local section hidden | | Holds in both the case's literal sequence (Local+Remote selected) and the clean Remote-only state | ✅ |

**Why step 7 is a clarification and not a bug** (`.agents/testing.md` reverse-masking
guard + `.agents/role-overrides.md` § interaction-discovery ladder — step 6, read the
source, is decisive): `ToolkitTypeSelector.jsx` passes `allowEmptyCategory={isMCP}`, and
`GroupedCategory.jsx:56-62` keeps an empty category **only while nothing is selected**:

```js
allCategories.filter(category =>
  (allowEmptyCategory && !selectedCategories.length) ||
  (groupedItems[category] && groupedItems[category].length > 0),
)
```

The Local empty-state placeholder is deliberately an unfiltered-view affordance. The
filter itself *works* (it hides Remote). The case's Expected Result wording is what is
stale. Full reasoning + the UX observation (selecting `Local` hides the only guidance on
how to obtain a local MCP) is in **#1742**.

**Console:** exactly **1** error on `/mcps/create`, and it is the already-tracked
**#656** React dev-mode warning
(`Each child in a list should have a unique "key" prop` from
`src/[fsd]/shared/ui/category/CategorySection.jsx` via `ToolkitTypeSelector.jsx`).
No other console error at any point in the flow, including both filter clicks.

---

## Handles Reference

Locator policy is **testid-only** (`.agents/testing.md` § Locator policy). Provenance
verified 2026-08-24 with `cd ../EliteaUI && git fetch origin` first.

| Element | Testid (primary, the ONLY handle) | Provenance | Notes |
|---|---|---|---|
| Local empty-state message | `mcp-type-picker-local-empty-state` | **on-main ✓** | `ToolkitTypeSelector.jsx:176`. Unmounted (not hidden) when filtered out → `to_have_count(0)` |
| Remote MCP type card | `toolkit-type-card-mcp` | **on-main ✓** (runtime-composed ``toolkit-type-card-${itemKey}``, `CategoryItemCard.jsx:14` — the literal string is not greppable; the template is on `main`) | ⚠️ **mounts asynchronously — up to 3.5 s** after `goto('/mcps/create')`. Framework auto-waiting only; never an immediate DOM read |
| No-results title | `catalog-no-results-title` | **on-main ✓** | `NoResultsMessage.jsx`; text `No MCPs found` |
| No-results description | `catalog-no-results-description` | **on-main ✓** | text `Try adjusting your search terms` |
| **Page heading "Choose the MCP type"** | **`mcp-type-picker-heading`** | **ADDED** — EliteaAI/EliteaUI@f4ce7128 + EliteaAI/EliteaUI@989db4f0 on `automation/testids`, **NOT yet on `main`** | |
| **Type filter chips** | **`mcp-type-picker-filter-chip-local` / `-remote`** + `data-selected="true|false"` | **ADDED** — same two commits, **NOT yet on `main`** | `category-filter-tab` is retained as the no-prefix fallback and is still what the in-chat MCP canvas renders |
| **Documentation link** | **`mcp-type-picker-local-documentation-link`** | **ADDED** — EliteaAI/EliteaUI@f4ce7128, **NOT yet on `main`** | |

### Testid work orders — `add-data-testid`, on `EliteaAI/EliteaUI` `automation/testids`

Every one is **additive props / attributes only**: no new DOM node, no new hook, no
render-prop change, no removed line. (Zero-functional-impact check, `add-data-testid`
§ 5.5.)

**A — page heading.** `src/[fsd]/shared/ui/filter/CategoryFilter.jsx` is a **shared**
component, so it must not hardcode a feature-scoped testid: add a `titleTestId` prop and
put it on the existing title `<Typography>` (`:33-39`). Plumb it through
`src/[fsd]/shared/ui/category/GroupedCategory.jsx` (destructure + forward, alongside the
`searchInputTestId` prop it **already forwards this exact way** — copy that line). Call
site **`src/pages/Toolkits/CreateToolkit.jsx`** (not `ToolkitTypeSelector.jsx`):
`titleTestId={isMCP ? 'mcp-type-picker-heading' : undefined}` — MCP only, per #511.
`ToolkitTypeSelector` merely destructures and forwards `titleTestId`.

> **AMENDED AT IMPLEMENTATION (2026-08-24, ELITEA-1949).** The AFS originally put the
> `isMCP ? …` decision *inside* `ToolkitTypeSelector`. That component has **two** call
> sites that both pass `isMCP` — the standalone `/mcps/create` page
> (`CreateToolkit.jsx`) **and the in-chat MCP canvas**
> (`src/[fsd]/features/chat/ui/editors/ToolkitEditor.jsx:304`) — so deciding there also
> renamed the canvas chips away from `category-filter-tab`, which two merged specs bind
> to (`tests/ui/chat/test_create_mcp_from_conversation.py` and
> `…_discard_changes.py`, via `McpFormPage.select_remote_category_tab`). Hoisting the
> decision to `CreateToolkit.jsx` leaves the canvas byte-identical. Both chat specs
> re-ran green against the shipped change (evidence in the PR description).
> Shipped as EliteaAI/EliteaUI@f4ce7128 + EliteaAI/EliteaUI@989db4f0.

**B — per-chip testid + state attribute.** Same file, the chip map at `:66-81`. There is
an **exact in-repo precedent to mirror**: the sibling `CategoryRail.jsx:5-30` already has
a `chipTestIdPrefix` prop, a `slugifyCategory()` helper and a
`data-selected={selected ? 'true' : 'false'}` attribute. Lift both onto `CategoryFilter`'s
`<Chip>`:

```jsx
data-testid={chipTestIdPrefix ? `${chipTestIdPrefix}-${slugifyCategory(category)}` : 'category-filter-tab'}
data-selected={selectedCategories.includes(category) ? 'true' : 'false'}
```

**Keep `category-filter-tab` as the no-prefix fallback** — other surfaces rely on it;
removing it would be a functional change. Plumb `chipTestIdPrefix` through
`GroupedCategory` **and `ToolkitTypeSelector`** the same way as A, and pass
`chipTestIdPrefix={isMCP ? 'mcp-type-picker-filter-chip' : undefined}` at the
**`CreateToolkit.jsx`** call site (see the amendment note under A) →
`mcp-type-picker-filter-chip-local` /
`mcp-type-picker-filter-chip-remote`. Both branches are referenced on the executed path
(both asserted present in step 6, both clicked), so #511 is satisfied.

**State is an attribute, never a testid** (`.agents/testing.md` § Locator policy, PR #581):
selection is asserted as
`'[data-testid="mcp-type-picker-filter-chip-local"][data-selected="true"]'` — a class
constant. Today the *only* selected-state signal is an emotion CSS class hash
(`css-5yxssv` selected vs `css-1n8j5hf` idle) / computed background colour, and **neither
may be bound to**.

**C — Documentation link.** `src/pages/Toolkits/ToolkitTypeSelector.jsx:179-186` — this is
our own feature JSX, so a direct attribute on the existing `<Link>`:
`data-testid="mcp-type-picker-local-documentation-link"`. (#579's third-party waiver does
not apply — the element is ours.)

**Deliberately NOT added** (#511 — testids go only on elements the test touches):
- a section-container / section-heading testid for `Local` / `Remote` — no assertion on
  the executed path needs one. Section presence is asserted through the section's own
  content (`mcp-type-picker-local-empty-state`, `toolkit-type-card-mcp`), both of which
  already have testids.
- a testid on the type-card **icon** `<Box>` (`CategoryItemCard.jsx:19`) — see Coverage Map.
- `searchInputTestId` for the MCP search box — this case never searches.

**Promotability:** all three new testids will land on `automation/testids` only; the spec
will be green on localhost and **red on any deployed env** until a human cherry-picks them
to EliteaUI `main`.

---

## Page-object work — `automation/pages/mcp_form_page.py`

`navigate_to_create()` and `select_remote_mcp_type()` already exist. Add, as class-level
fields / constants (never built in a method body):

```python
type_picker_heading      = LocatorDescriptor(testid="mcp-type-picker-heading")
local_documentation_link = LocatorDescriptor(testid="mcp-type-picker-local-documentation-link")
no_results_title         = LocatorDescriptor(testid="catalog-no-results-title")
no_results_description   = LocatorDescriptor(testid="catalog-no-results-description")

TYPE_FILTER_CHIP          = '[data-testid="mcp-type-picker-filter-chip-{}"]'
TYPE_FILTER_CHIP_SELECTED = '[data-testid="mcp-type-picker-filter-chip-{}"][data-selected="true"]'
```

plus `type_filter_chip(slug)` / `selected_type_filter_chip(slug)` /
`click_type_filter(slug)` / `is_type_filter_selected(slug)` helpers that `format()`
those constants. Mirror `McpListPage.type_filter_chip()` (ELITEA-1942) for shape.

**Shipped as written**, minus two rows that already existed on `McpFormPage` and were
reused unchanged: `local_empty_state` (added ELITEA-1921) and `remote_mcp_type_card`
(the AFS's `remote_type_card`).

---

## Automation hints

1. **`goto('/mcps/create')` → the type card mounts up to 3.5 s later.** Wait on
   `toolkit-type-card-mcp` (or the heading) with framework auto-waiting before any read.
   A known-noise entry already exists for a 10 s timeout on exactly this
   (`.agents/testing.md`, mcp wave-01).
2. **Filtering is pure client-side re-grouping — there is NO network request.** Do not
   wait for a response after a chip click (unlike the dashboard filter, ELITEA-1942).
   Wait on the DOM outcome: `catalog-no-results-title` visible (step 7) /
   `toolkit-type-card-mcp` visible (step 8).
3. **The chips are MULTI-SELECT and there is no "clear all"** on this surface. Execute
   the case's literal 7→8 sequence, and assert the multi-select fact explicitly (Axis 2)
   so a future switch to single-select turns this red instead of silently changing what
   step 8 means.
4. **Never bind to the emotion CSS class or the background colour** for chip selection —
   use `data-selected` (work order B).
5. **Assert the Documentation link's `href`; never click it.** It is `target="_blank"` to
   an external site; the case only asks that it points at the right URL.
6. **Console listener:** `/mcps/create` emits the known **#656** React `key` warning on
   every mount. Filter it exactly (message contains `unique "key" prop`) and hard-fail on
   anything else — do not blanket-disable the console assertion.
7. **Empty-state / card elements are UNMOUNTED, not hidden**, when filtered out →
   `to_have_count(0)`, never `not_to_be_visible()`.

---

## Coverage Map

### Axis 1 — every element of the case

| Case element | Expected result | Covered by | Asserted where | Disposition |
|---|---|---|---|---|
| Precondition: logged in | — | `auth_state` | setup | covered |
| Precondition: on the MCP creation page | — | `navigate_to_create()` (bare `/mcps/create`, prefix injected by config) | Step 1 | covered |
| Test Data: Documentation URL | — | module constant `DOCUMENTATION_URL` | Step 4 | covered |
| Step 1 — navigate to the creation page | Page loads at the correct URL | Step 1 | `expect(page).to_have_url(re.compile(r"/mcps/create$"))` + heading visible | covered |
| Step 2 — heading "Choose the MCP type" | Heading visible | Step 2 | `expect(type_picker_heading).to_have_text("Choose the MCP type")` | covered (needs testid A) |
| Step 3 — Local section message | Correct message displayed | Step 3 | `expect(local_empty_state).to_have_text("Still no local MCP available. Follow creation guides in our Documentation.")` | covered |
| Step 4 — Documentation is a clickable link to the doc URL | Link present, correct URL | Step 4 | `to_have_attribute("href", DOCUMENTATION_URL)` + `to_have_text("Documentation")` + `to_have_attribute("target", "_blank")` | covered (needs testid C) |
| Step 5 — Remote section shows "Remote MCP" card | Remote MCP card visible | Step 5 | `expect(remote_type_card).to_be_visible()` + `to_have_text("Remote MCP")` | covered |
| Step 5 — "…with icon" | (no separate Expected Result) | — | not asserted | **out-of-scope, declared.** The icon is an untestid'd `<Box>{icon}</Box>` inside `CategoryItemCard.jsx:19`. The step's *Expected Result* column is "Remote MCP card is visible" — the icon appears only in the Action prose. Adding a shared-component testid no expected result demands would violate #511's blanket-add ban. Recorded here rather than silently dropped. |
| Step 6 — both filter buttons present | Both shown | Step 6 | both chips `to_be_visible()`, `to_have_text("Local")` / `("Remote")`, and both `data-selected == "false"` initially | covered (needs testid B) |
| Step 7 — click Local; only Local content shown | *Only Local section is visible* | Step 7 (**live contract, not case text**) | Local chip `data-selected=="true"`; `remote_type_card.to_have_count(0)`; `local_empty_state.to_have_count(0)`; `no_results_title.to_have_text("No MCPs found")`; `no_results_description.to_have_text("Try adjusting your search terms")` | **clarification #1742** — asserted against live product |
| Step 8 — click Remote; only Remote content shown | Only Remote section is visible | Step 8 | `remote_type_card.to_be_visible()` + `to_have_text("Remote MCP")`; `local_empty_state.to_have_count(0)`; `no_results_title.to_have_count(0)` | covered |
| Expected Final State | Remote filter shows only the Remote MCP card; Local section hidden | Step 8 tail + Axis-2 clean-state check | as above, plus the Remote-only re-check | covered |
| Pass criterion "no errors" | — | Axis 2 console assertion | end of test | covered |

### Axis 2 — assertions beyond the case, each grounded

| Extra observable | Why |
|---|---|
| Both chips `data-selected == "false"` on first load | Establishes the unfiltered baseline. Without it, steps 7/8 could pass on a page that arrived pre-filtered, and step 3's Local placeholder only renders while nothing is selected — so the baseline is load-bearing for step 3 too. |
| Chips are **multi-select**: after the case's 7→8 sequence, `Local` **and** `Remote` are both `data-selected="true"` | Discovered live and invisible in the case text. Pins the semantics of step 8: today it passes with two filters active only because Local contributes no items. If the product ever switches to single-select, or a Local MCP appears, this assertion turns red and forces a re-read instead of letting step 8 quietly change meaning. |
| After deselecting `Local`, the Remote-only state renders the same single Remote section | Proves step 8's outcome is genuinely "Remote filter shows the Remote section", not an artefact of the two-chip state. This is the Expected Final State asserted in its clean form. |
| `catalog-no-results-title` / `-description` exact texts at step 7 | The live contract the clarification (#1742) documents. Asserting the *exact* strings — not merely "the Local placeholder is gone" — is what makes the spec a real oracle for the wording the product actually shows. |
| Console errors == 0 after filtering out the known #656 `key` warning | Case Pass criterion is "All steps complete without errors". #656 is pre-existing and tracked; anything else is a regression this case should catch. |

---

## Known Defects / clarifications touching this case

- **#1742** (`question` + `case-text-drift`, OPEN, **filed by this analysis**) — step 7's
  Expected Result vs the live product. Does not block automation.
- **#1738** (`question`, OPEN) — no Local MCP exists or can be created in DEV. This case is
  *written for* that state, so it is automatable; but the AFS must be re-run if it changes.
- **#1737** (`bug`, OPEN) — the **dashboard** `Local` type filter does not filter. Different
  surface and different symptom; **sibling, not duplicate** (cross-linked in #1742).
- **#656** (OPEN) — `/mcps/create` React `key` warning; filter it in the console assertion.

## Blocked Steps

None.

## Fidelity Declaration

**No substitution of any kind.** This case is read-only: it navigates, reads rendered text
and attributes, and clicks two chips. No `page.route`, no `route.fulfill`, no
`page.evaluate`, no `monkeypatch`, no API seeding, no injected state. Every asserted value
— heading text, empty-state text, `href`, card label, chip `data-selected`, no-results
strings — is produced by the live product.

## Suggested spec location

`automation/tests/ui/toolkits/test_mcp_type_picker_local_vs_remote.py`
→ `TestMcpTypePickerLocalVsRemote::test_type_picker_sections_documentation_link_and_filters`
Markers: `ui`, `toolkits`, `mcp`, `p2`, `regression`.
