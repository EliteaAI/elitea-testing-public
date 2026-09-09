# Test Case: Pipeline Dashboard — Search filters the grid and Clear restores it

## Metadata
- **TMS ID**: ELITEA-2023
- **Linked Story**: none
- **Priority**: l2
- **Environment Explored**: local (`http://localhost:5173`, EliteaUI `automation/testids`,
  DEV backend — the SAME data plane, auth and product build `dev.elitea.ai` serves;
  project `Private` id 399)
- **User set**: `${TEST_USER}` (localhost `auth_state` bypass via `VITE_DEV_TOKEN`)
- **Analyst**: qa-engineer (Sage) — original batch
  `elitea-2023-pipeline-dashboard-search` (2026-08-07); **repair pass 2026-09-10**
- **Status**: extend-existing (repair amendment — the test is already merged)

---

## ⚠️ REPAIR AMENDMENT — 2026-09-10, board `#2119`, CI run 34331579791 (DEV Stable #114)

**This AFS previously specified an ambient-data precondition. That was the defect.**
The rest of the document below is the amended spec; this section is the record of
what changed and why, so nobody re-derives it.

### What failed

`tests/ui/pipelines_2/test_pipeline_management.py::TestSearchPipeline::
test_search_placeholder_and_dashboard_grid_filters_and_clears`, red in CI with
`StopIteration` at `test_pipeline_management.py:614`:

```python
existing_rows = pipeline_api.list_pipelines().get("rows", [])
non_matching_name = next(
    row["name"] for row in existing_rows
    if "yaml" not in row.get("name", "").lower()
)
```

The generator was empty. The CI matrix project (`prompt_lib/573`, "Private") holds
**no pipeline other than the one this test had just created**.

### Root cause — an ambient-data precondition

The test **established** its matching ("YAML") pipeline via `pipeline_api`, but
**harvested** the non-matching one from whatever the project happened to contain.
The case's Preconditions section only names the matching pipeline, and the original
analysis (project 399, 14 ambient pipelines) read the second one as "obviously
present" rather than as a precondition to establish.

A test that reads shared state it never established passes exactly where that state
happens to exist. Localhost has 16 pipelines; the CI project has 0 of its own. Same
product, same build, opposite result — and the failure named the wrong subsystem
(`StopIteration` in a `next()`, three steps before anything about search is
asserted).

This is the **identical class** as sibling card `#2118` / ELITEA-2024, repaired in
`6855dc3f4` (PR #2148) in the same file. `#2118`'s digest entry states the general
rule this amendment now obeys:

> **Any dashboard-content case MUST establish its own ≥1-entity precondition, never
> inherit whatever the ambient project holds.**

Both halves of this case's precondition are now established by the test itself.

### What changed in this AFS

| # | Change | Why |
|---|---|---|
| 1 | § Test Data: **two** API-created pipelines (matching + non-matching), controlled names, both torn down | the defect — no ambient harvest survives |
| 2 | § Test Data: **neither description may contain "yaml"** | live-proven: the search matches DESCRIPTION as well as name (§ Live Findings F3) — an ambient-safe name is not enough on its own |
| 3 | Step 2 → waiting **positive** assertion on `get_card_names(timeout=10000)` containing **both** names | this class of failure now reports **at the precondition**, naming the precondition, instead of at an unrelated assertion later |
| 4 | Step 5 → `empty_state_title.count() == 0` guard inserted between the positive and the absence assertion | discriminates "a populated grid that excludes the non-match" from "nothing mounted at all" |
| 5 | Step 7 → migrated from page-wide `pipeline_exists_in_list()` to grid-scoped `get_card_names()` + empty-state guard + `len(restored) > len(filtered)` | the old restore assertion was **not grid-scoped** and did not state that the list actually grew back (§ Vacuity Audit V2) |
| 6 | Step 3 → visibility assertion added alongside the placeholder read | the case's Step-2 expected result is *"Search textbox is visible"*; the test only read an attribute (§ Vacuity Audit V3) |
| 7 | Axis-2 console check → `utils.console_errors.collect_console_errors()` | the hand-rolled `page.on("console", …)` shape discards `msg.location`, so this suite's recurring background-noise class arrives anonymous (`.agents/testing.md` § Unconfirmed — standing migration ask, this spec is being touched) |
| 8 | § Network Behavior **corrected** — filtering is **server-side**, not client-side | the original claim was wrong; see § Live Findings F4 |
| 9 | § Fidelity Declaration added | the API-created preconditions are transit substitution and must be declared |

**No expected result was dropped or weakened.** Every Coverage-Map row the case
carries is still asserted, and four of them are asserted more strongly than before.

### Repair-pass live verification (2026-09-10, `http://localhost:5173`)

Executed end-to-end against the live app with two purpose-created probe pipelines
(`autotest_YAML_search_542cc7` id 10498, `autotest_nomatch_srch_542cc7` id 10499,
both deleted afterwards — re-query for `542cc7` returned `total: 0`).

| Probe | Observed |
|---|---|
| Unfiltered dashboard | `entity-card-name: 16`, `empty-state-title: 0`, both probes at the top (grid sorts `created_at desc`, same as `list_pipelines()`) |
| Placeholder | exactly `Let's find something amazing!` |
| Type "YAML", wait 2.5 s (past the 500 ms suggestion debounce), **no Enter** | grid **unchanged at 16** — typing alone does not filter (re-confirms the 2026-08-07 finding) |
| Press **Enter** | grid narrows to **1** (`autotest_YAML_search_542cc7`), `empty-state-title: 0`; card name split into 3 `<span>`s by the highlighter (confirms the `get_card_names()` rationale) |
| Click Clear (X) | input empty, grid back to **16**, `empty-state-title: 0`, URL stays `/pipelines/all` |
| Search `ELITEA-2023` (a token present ONLY in both probes' **descriptions**) | grid = **2** — both probes. **The search matches description.** |
| Search `zzzz_nonexistent_pipeline_12345` (zero matches) | `entity-card-name: 0`, `empty-state-title: 1` ("No pipelines yet") — the discriminator fires |
| Clear from that zero-match state | grid restored to 16, stays on `/pipelines/all` — the `#585`/`#551` sibling redirect defect still does **not** reproduce on Pipelines |
| Console (whole session, `level=error`) | **0 errors** |

---

## Extension target

**Covering spec**: `automation/tests/ui/pipelines_2/test_pipeline_management.py`,
class `TestSearchPipeline` — merged; this case's own test
(`test_search_placeholder_and_dashboard_grid_filters_and_clears`) is merged too and
is what this amendment repairs.

**Behavioural overlap (what the two older tests already prove).**
- `test_search_pipeline_by_name` — a fresh `pipeline_api` pipeline is discoverable
  via `search_and_wait_for_results(name)`.
- `test_search_pipeline_no_results` — a nonsense term produces no visible match.

**The mechanism gap those two do not cover** (still true, re-confirmed 2026-09-10):
`SearchBar.jsx` (shared by Pipelines/Agents/MCP/Credentials/Toolkits/Skills)
handles `onChange` (typing) by updating local input state and opening an API-backed
**suggestions popover** (`SuggestionList.jsx`, 500 ms debounce). The dispatch that
narrows the **dashboard grid** (`onSearch()` → redux `setQuery` → the applications
query's `query` param) fires **only** on `onKeyDown === 'Enter'` or a click on
`data-testid="search-send-button"`. `PipelinesListPage.search()` has since been
fixed to press Enter (merged), so the two older tests now exercise the real filter
as well.

Case-text drift on this point is already filed as a clarification —
`EliteaAI/elitea-testing-public#1302`. Not a defect.

---

## Preconditions

- User is logged in (`auth_state` on localhost).
- **Both of the following are established BY THE TEST, via `pipeline_api`. Neither
  is inherited from the project.**
  1. A pipeline whose **name contains "YAML"** (the case's own declared
     precondition).
  2. A pipeline that provably matches **neither by name nor by description**, used
     for the "only matching pipelines are shown" / "full list restored" assertions.
- No assumption whatsoever about how many other pipelines the project holds. The
  spec is correct on a project holding exactly these two and on one holding
  hundreds.

---

## Test Data

### generate-per-test (created in the test, deleted in its own `finally`)

Both created with `pipeline_api.create_pipeline(name=..., description=...)`
directly (**not** the `pipeline_id` fixture: that fixture derives the name from
`f"autotest_{request.node.name}"[:32]`, and this test's function name truncates to
32 chars long before reaching anything usable — the match term would be lost).

| Role | Name shape | Constraint |
|---|---|---|
| Matching | `autotest_YAML_search_<hex6>` (26 chars) | must contain `YAML`; ≤32 chars (API max) |
| Non-matching | `autotest_nomatch_srch_<hex6>` (28 chars) | must contain **no** case-insensitive `yaml`, in **name or description**; ≤32 chars |

- **Use ONE `uuid4().hex[:6]` suffix for both**, so a leaked pair from a crashed run
  is greppable as a unit.
- **Descriptions must not contain "yaml" either.** Live-proven (§ Live Findings F3):
  the backend `query` matches description as well as name, so a pipeline with a
  clean name and a "YAML" description would appear in the filtered grid and break
  the Step-5 absence assertion. `"ELITEA-2023 dashboard search filter and clear"`
  is a safe description for both.
- **Cleanup**: delete BOTH ids in a single `finally`, each guarded so the second
  delete still runs if the first raises. Same pattern as
  `TestPipelineIsolation::test_fixture_cleanup_cycle`.
- **Page-1 visibility is guaranteed, not assumed**: the grid requests
  `sort_by=created_at&sort_order=desc&limit=20&offset=0`, so the two
  just-created pipelines are the two newest and are always on the first page.

---

## Test Steps

> Assertion ordering is load-bearing throughout: **a waiting positive assertion
> first, absence/count guards after.** During the dashboard's loading window (~4 s
> locally, ~10 s in CI) *both* `entity-card-name` and `empty-state-title` read `0`,
> so a bare count taken first is as vacuous as the bug this repair closes
> (`#2118` digest entry, § Dashboard view toggle).

1. **Create both preconditions via the API.**
   Create the matching and the non-matching pipeline per § Test Data; keep both ids
   for teardown. Everything from here to the end runs inside the `try` whose
   `finally` deletes them.

2. **Navigate to `/pipelines/all` and assert the precondition landed.**
   `PipelinesListPage.navigate()`, then
   `baseline_names = list_page.get_card_names(timeout=UI_ELEMENT_TIMEOUT)`.
   - **Verify** (waiting, positive): **both** created names are in `baseline_names`.
     One assertion per name so the message says which one is missing.
   - This is the step that must fail if the precondition is not real. `10000 ms`,
     not `get_card_names()`'s 5 s default — 5 s is exactly what expired in CI.
   - Keep `baseline_names` for Step 7's diagnostics.

3. **Assert the search textbox is present, visible, and correctly labelled** (case
   Step 2).
   - **Verify**: `list_page.search_input.is_visible()` is true.
   - **Verify**: its `placeholder` attribute equals exactly
     `Let's find something amazing!`.

4. **Type `YAML` into the search box and press Enter** (`PipelinesListPage.search()`
   — it presses Enter; typing alone does not filter, § Extension target).
   - **Verify**: `search_input.input_value() == "YAML"` (case Step 3).

5. **Assert the grid narrowed to matching pipelines only** (case Step 4). In this
   order:
   1. `filtered_names = list_page.get_card_names(timeout=UI_ELEMENT_TIMEOUT)`
      — **Verify** (waiting, positive): the matching name IS in `filtered_names`.
        This is also what makes 5.2 and 5.3 non-vacuous: it cannot pass on an empty
        grid.
   2. **Verify**: `list_page.empty_state_title.count() == 0` — the dashboard is not
      showing "No pipelines yet". Redundant with 5.1 by construction, kept because
      it names the actual failure mode when the grid does not render, instead of
      reporting a missing pipeline (`#2118` precedent).
   3. **Verify**: the non-matching name is **NOT** in `filtered_names`.
   - Use `get_card_names()`, never `pipeline_exists_in_list()`, in the filtered
     state: the active search highlights the matched substring by splitting the card
     name across nested `<span>` fragments, and Playwright's exact `text="…"` engine
     does not match the parent's concatenated text in that case (re-confirmed live
     2026-09-10 — see the `innerHTML` capture in § Live Findings F2).
   - ⚠️ **Do NOT assert "every visible card name contains yaml".** It looks like the
     case's wording and it is wrong: the backend matches description too, so a
     pipeline with a "YAML"-free name and a "YAML" description legitimately appears.
     Ambient data would make that assertion a false red (§ Live Findings F3).

6. **Click the search Clear (X) icon** (`PipelinesListPage.clear_search()`).
   - **Verify**: `search_input.input_value() == ""` (case Step 5).

7. **Assert the full list is restored** (case Step 6). In this order:
   1. `restored_names = list_page.get_card_names(timeout=UI_ELEMENT_TIMEOUT)`
      — **Verify** (waiting, positive): the matching name IS in `restored_names`.
   2. **Verify**: the previously-hidden non-matching name IS in `restored_names`.
      This is the assertion that proves the *filter released* — it was absent from
      the grid one step ago, by Step 5.3.
   3. **Verify**: `list_page.empty_state_title.count() == 0`.
   4. **Verify**: `len(restored_names) > len(filtered_names)` — the grid genuinely
      grew back rather than merely still containing the match. Include
      `len(baseline_names)` in the failure message for diagnosis.
      *Not* `restored_names == baseline_names`: this runs against a shared DEV
      project, and strict equality would flake on any concurrent create/delete
      (`#1082` class). `>` is ambient-proof — `restored ⊋ filtered` holds by
      construction on any project, because the non-match is in one and not the
      other.
   5. **Verify**: `urlparse(page.url).path` ends with `/pipelines/all` — no redirect
      (regression guard for the `#585`/`#551` sibling defect, Axis 2).

8. **Side-channel — no console errors across the whole flow** (Axis 2).
   Collect with `utils.console_errors.collect_console_errors(page)` registered
   before Step 2, asserted here. **No URL filter is applied** — this flow performs
   no project switch, so `#1971` is not expected; if a background-noise message does
   appear, the helper now records its URL, which is the entire point.

---

## Expected Results

- Search input is visible and its placeholder is exactly
  `Let's find something amazing!`.
- Typing alone (no Enter / send-icon click) does **not** narrow the dashboard grid —
  it only opens the suggestions popover. Informational; not asserted by this AFS.
- After Enter, the grid narrows: the matching pipeline is present, the non-matching
  pipeline is gone, and the dashboard is **not** in its empty state.
- After Clear, the grid is restored: both pipelines are visible again, the card count
  strictly exceeds the filtered count, and the page stays on `/pipelines/all`.
- Zero console errors across the flow.

---

## Fidelity Declaration

`.agents/testing.md` § Fidelity policy · `.agents/role-overrides.md` § Analyst slot.

| Substituted | Transit or terminal | Authority / real observable |
|---|---|---|
| Both precondition pipelines are created through `pipeline_api.create_pipeline()` instead of the UI create form | **Transit** | The case's Preconditions section states only that the dashboard *contains* a "YAML" pipeline — it does not specify how it got there, and pipeline creation is not this case's subject (ELITEA-2020/2022 own it). Every value this test asserts on — which cards the grid renders after Enter, after Clear, whether the empty state mounts, the input's value and placeholder, the URL — is produced by the live application in response to real typing, a real `Enter` keypress and a real click. Nothing is fabricated, injected, or intercepted. |

No terminal substitution. No `route.fulfill`, no `page.evaluate` state injection, no
replaced client anywhere in this spec.

---

## Vacuity Audit — could this assertion pass because nothing rendered?

Run against **every** absence/negative assertion in the spec, per the dispatch's
standing question. `CardList.jsx:40-44` is the reason it must be asked at all:

```js
const showEmptyOrError = !rest.isLoading && (isError || isEmptyList);
const showTable = !showEmptyOrError && shouldRenderTable;
const showCards = !showEmptyOrError && !shouldRenderTable;
```

An empty list short-circuits **both** render branches, so "no card matched" and "no
card mounted" are the same DOM.

| # | Assertion | Verdict | Disposition |
|---|---|---|---|
| **V1** | Step 5.3 — `non_matching_name not in filtered_names` | **Guarded, but only by ordering.** `get_card_names()` returns `[]` on timeout, so on an empty grid this absence passes trivially — *except* that Step 5.1 reads the SAME `filtered_names` snapshot and requires the match to be in it, so it raises first. The guard is real but implicit and one refactor away from being lost. | Made explicit: `empty_state_title.count() == 0` inserted as 5.2, and the ordering requirement written into the step. |
| **V2** | Step 7 — the restore assertions | **Was genuinely weak.** The merged code used `pipeline_exists_in_list()`, a **page-wide** `text="{name}"` locator: it is not scoped to the grid, so any occurrence of the name elsewhere in the DOM (a still-open suggestions popover, a toast) satisfies it, and it says nothing about the grid having mounted. It also never stated that the list *grew back*. | Migrated to grid-scoped `get_card_names()` + `empty_state_title.count() == 0` + `len(restored) > len(filtered)`. Both steps now read the same testid-scoped source. |
| **V3** | Step 3 — the placeholder read | **Not vacuous, but incomplete.** `get_attribute()` auto-waits and raises if the element never resolves, so it cannot pass on nothing. But the case's Step-2 expected result is *"Search textbox is **visible**"*, and an attribute read is satisfied by an element that exists while hidden. | `is_visible()` added; placeholder equality kept. |
| **V4** | Step 5 — the (rejected) "all visible names contain yaml" universal | **Would have been a false red**, not vacuous. Rejected on evidence — the backend matches description (F3). | Not specced; the trap is documented inline at Step 5 so a future strengthening pass does not re-introduce it. |
| **V5** | Step 2 — the precondition itself | Previously **absent**: the test navigated and immediately asserted two page-wide text matches, and its real dependency (a second, non-matching pipeline existing) was never asserted at all — it surfaced as `StopIteration` in a `next()` before the browser was even involved. | Waiting positive assertion on both names, at Step 2, naming the precondition in its message. |

---

## Coverage Map

**Axis 1 — Case coverage**

| Case element | Expected result | Covered by (AFS step) | Asserted where | Disposition |
|---|---|---|---|---|
| Precondition: dashboard contains a pipeline whose name contains "YAML" | present before the search | step 1 + step 2 | step 2: waiting `get_card_names()` membership | asserted (**established, not inherited**) |
| 1 Navigate to Pipelines dashboard | Full list loads | step 2 | step 2: both created names in the card grid | asserted |
| 2 Locate search textbox, placeholder "Let's find something amazing!" | Textbox is visible | step 3 | step 3: `is_visible()` **and** placeholder equality | asserted |
| 3 Type "YAML" in the search box | Input populated with "YAML" | step 4 | step 4: `input_value()` | asserted |
| 4 Verify filtered results show only pipelines containing "YAML" | Only matching pipelines shown | step 5 | step 5.1 match present · 5.2 not the empty state · 5.3 non-match absent | asserted |
| 5 Clear search text | Search field is empty | step 6 | step 6: `input_value() == ""` | asserted |
| 6 Verify full pipeline list is restored | All pipelines visible again | step 7 | step 7.1–7.4: both names back, not the empty state, card count strictly grown | asserted |

**Axis 2 — Analyst additions**

- **Console-error check across the whole flow** — *silent failures are the worst
  bugs; the live session is already open, so it is free. Now URL-annotated via
  `collect_console_errors()`.*
- **URL stays on `/pipelines/all` after Clear** — *the sibling MCP (`#585`) and
  Credentials (`#551`) list pages have a confirmed defect where clearing a
  zero-match search redirects to their `/…/create` page. Pipelines does not
  reproduce it (re-verified 2026-09-10 from the zero-match state), so this is a
  regression guard on a shared component, not a bug reproduction.*
- **`empty-state-title` absence guards (steps 5.2, 7.3)** — *`CardList.jsx`'s
  `showEmptyOrError` makes "filtered to nothing" and "rendered nothing"
  indistinguishable by card count alone; this is the handle that separates them.
  Same guard the `#2118` repair added to the sibling test.*
- **`len(restored) > len(filtered)` (step 7.4)** — *"all pipelines are visible
  again" needs a statement about the list as a whole, not just about two known
  names; this is the strongest such statement that stays correct on a shared
  project.*

---

## Cleanup

1. `pipeline_api.delete_pipeline(match_id)` and
   `pipeline_api.delete_pipeline(nomatch_id)` in a single `finally`, each guarded so
   the second runs even if the first raises.
2. Nothing else is mutated — no project settings, no defaults, no shared
   configuration. Per `.agents/testing.md` § Teardown-guard ordering, there is no
   flag to set: teardown is unconditional and both ids exist from Step 1, before any
   assertion can fail.

---

## Concrete Handles (discovered during exploration)

Locator policy is **testid-only** (`.agents/role-overrides.md` /
`.agents/testing.md` § Locator policy). Every handle below is a `data-testid` and
**every one already exists as a `LocatorDescriptor` class field on
`PipelinesListPage`** — provenance re-verified 2026-09-10 after
`cd ../EliteaUI && git fetch origin`:

```
pipeline-search-input        main:YES  testids:YES
search-clear-button          main:YES  testids:YES
entity-card-name             main:YES  testids:YES
empty-state-title            main:YES  testids:YES
pipelines-page-header        main:YES  testids:YES
search-send-button           main:YES  testids:YES
```

| Element | Testid | `PipelinesListPage` field | PROVENANCE |
|---|---|---|---|
| Search input | `pipeline-search-input` | `search_input` | **on-main ✓** (`SearchBar.jsx`; resolved live 2026-09-10) |
| Search Clear (X) icon | `search-clear-button` | `search_clear_button` | **on-main ✓** (`src/components/SearchBar.jsx:274`; clicked live 2026-09-10) |
| Card name (collection locator) | `entity-card-name` | `entity_card_name` + `get_card_names()` | **on-main ✓** (shared `Card.jsx`; 16/1/16 counts read live) |
| Empty-state title | `empty-state-title` | `empty_state_title` | **on-main ✓** (`EmptyStatePage.jsx:49`; read `1` / "No pipelines yet" on a zero-match grid live) |
| Page header (load proxy) | `pipelines-page-header` | `page_header` | **on-main ✓** (used by `wait_for_page_load()`) |
| Search send icon | `search-send-button` | — (not used) | **on-main ✓** — alternate activation; Enter is what this spec uses |

**No new testid is required by this repair.** `empty_state_title` — the one handle
this amendment newly depends on — landed on `automation/base` in `6855dc3f4` (the
`#2118` repair) and its testid has been on EliteaUI `main` all along, so nothing
here is gated on a human cherry-pick.

**Pre-existing, out of scope, do not fix here:** `search_input`, `page_header`,
`table_view_button` and `card_view_button` still carry dead `fallback=` lambdas
(forbidden in new code per `.claude/rules/page-objects.md`; tracked tech debt
`#25`/`#42`). Removing them is a safe but unrelated change and must not ride a
CI-red repair.

---

## Network Behavior

**⚠️ Corrected 2026-09-10 — the previous claim in this AFS ("no new XHR observed
firing on Enter — filtering appears client-side") was wrong.**

Filtering is **server-side**. `useLoadApplications` passes redux `search.query`
straight into the applications query. Captured live on Enter:

```
GET /api/v2/elitea_core/applications/prompt_lib/399?tags=&query=YAML&agents_type=pipeline&limit=1&offset=0                                   200
GET /api/v2/elitea_core/applications/prompt_lib/399?tags=&sort_by=created_at&sort_order=desc&query=YAML&agents_type=pipeline&limit=20&offset=0  200
```

and on Clear the same pair with `query=`. The `limit=20` request is the grid; the
`limit=1` one is the total-count query. Page size is **20**.

The suggestions popover fires its own debounced XHR while typing (before Enter) —
irrelevant to these assertions, noted so nobody mistakes it for the filter.

### Optional hardening — NOT required by this repair

`PipelinesListPage.search()` and `clear_search()` currently wait with
`wait_for_network()` (`page.wait_for_load_state("networkidle")`) plus a 1 s settle.
That is the **`#1847`** mechanism: this app holds a persistent
`/socket.io/?EIO=4&transport=polling` transport open, which is in direct tension
with a "500 ms of network silence" wait. Now that the filter is known to be a real
request, `#1847`'s own prescribed fix is available — wait on the response the caller
actually needs:

```python
with self.page.expect_response(
    lambda r: "/elitea_core/applications/" in r.url
    and f"query={query}" in r.url
    and "limit=20" in r.url
):
    self.search_input.press("Enter")
```

Strictly better and faster for the two sibling tests as well. **It is deliberately
not part of this repair's scope** — the CI red was the data precondition, and
`search()` has three callers. Raise it separately if it starts costing gate time.

---

## Known Defects Found During Exploration

- **None.** Re-verified 2026-09-10, including the specific sibling pattern:
  `EliteaAI/elitea-testing-public#585` (MCP list) and `#551` (Credentials list) —
  clearing a **zero-match** search redirects to the entity's `/create` page. The
  identical trigger was reproduced here (searched
  `zzzz_nonexistent_pipeline_12345` → "No pipelines yet" empty state → clicked
  Clear) and the Pipelines dashboard restored the full 16-card grid and stayed on
  `/pipelines/all`. **Not reproduced.** Step 7.5 keeps asserting the URL as a
  regression guard.
- **Case-text drift (not a defect)** — already filed as clarification
  `EliteaAI/elitea-testing-public#1302`: the case's Steps 3–4 imply typing alone
  filters; the product requires Enter or the send-icon click. Same `SearchBar.jsx`
  mechanism as `#1114` on the Chats surface. Unchanged by this repair.
- **The CI failure itself is a TEST defect, not a product defect.** Nothing about
  ELITEA-2023's behaviour has changed; the product behaves identically on the
  localhost dev server and on the CI project. Only the test's assumption about
  ambient data differed.

## Blocked Steps

None.

---

## Automation Hints

- Framework: Playwright + pytest. The test to repair is
  `automation/tests/ui/pipelines_2/test_pipeline_management.py::TestSearchPipeline::
  test_search_placeholder_and_dashboard_grid_filters_and_clears` — **repair in
  place**, do not add a new test.
- **Delete the `pipeline_api.list_pipelines()` / `next(...)` harvest entirely.** It
  is the defect; nothing about it is salvageable.
- Reuse `PipelinesListPage.empty_state_title` and `get_card_names()` — both already
  exist (`get_card_names()` from this case's own first pass, `empty_state_title`
  from `#2118`). Add no page-object fields; add no testids.
- Pass `timeout=UI_ELEMENT_TIMEOUT` (10 s) to every `get_card_names()` call. The
  helper's 5 s default is exactly what expired in CI.
- Update the test docstring: name the repair (board `#2119`, CI run 34331579791),
  state the transit substitution per § Fidelity Declaration and
  `.agents/role-overrides.md` § Implementer slot, and keep the existing note
  explaining why `get_card_names()` is used instead of `pipeline_exists_in_list()`
  in the filtered state.
- Every step stays wrapped in `with allure.step("Step N — …"):`.
- **Gate on localhost** (`http://localhost:5173`) — it is the same DEV data plane,
  auth and product build that `dev.elitea.ai` serves, and the repair's mechanism is
  a self-established data precondition plus app-DOM assertions, both environment
  independent. Do **not** edit `automation/.env.test` (symlink to the shared master
  file). The repaired spec is by construction correct on a project holding only its
  own two pipelines, which is precisely the CI condition that broke it.
