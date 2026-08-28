# Repair brief — ELITEA-2037 · `.MuiPopper-root >> nth=0` resolves to a tooltip, not the "+ MCP" dropdown

- **Issue:** EliteaAI/elitea-testing-public#1891
- **TMS case:** ELITEA-2037 (`test-specs/pipelines/l2_pipeline-mcp-node-integration-fresh-attach_ELITEA-2037.md`)
- **Failing test:** `automation/tests/ui/pipelines_2/test_pipeline_mcp_node_fresh_attach.py::test_mcp_node_fresh_attach`
- **Failing CI run:** GHA 33066098636 — `UI Tests DEV Stable [main] [all]`, job `test / dev-stable - pipelines_2`, user `autotest_user_2`, target `https://dev.elitea.ai`, 2026-08-27
- **Triage class:** **A — UI/framework drift** (locator resolution defect in the shared page-object layer). NOT class B/C (no product defect asserted), NOT class D (no data pollution), NOT class F (all four testids the spec uses are on EliteaUI `main` — verified below).
- **Author:** qa-engineer (analyst slot), 2026-08-28. **This is a brief, not a fix.** No test code was changed.

---

## 1. Root-cause verdict

`components.mui.Popper.wait_for()` resolves `page.locator(".MuiPopper-root").first` — *the first
`.MuiPopper-root` in `document.body` order*, with no scoping to the dropdown that was just opened and
no exclusion of other popper kinds. **A MUI `Tooltip` is also a `.MuiPopper-root`** (its root class list
is `MuiPopper-root MuiTooltip-popper MuiTooltip-popperInteractive`) and it portals to `<body>`, so a
tooltip that mounted *before* the dropdown sorts at `nth=0`. On the pipeline detail page the embedded
chat panel's model-selector button (`LLMModelSelector.jsx:174-182`) is wrapped in
`<Tooltip placement="top" title="Select LLM Model">`; when that tooltip is open at the instant Step 2
clicks "+ MCP", `Popper.wait_for()` returns **the tooltip**. `popper.is_visible()` is legitimately
`True` (the tooltip *is* visible, so a `:visible` filter does not help — it preserves DOM order and
still yields the tooltip), and `popper.locator('[data-testid="toolkit-search-input"]').count()` is
legitimately `0`, producing the exact CI signature `assert 0 > 0 … selector='.MuiPopper-root >> nth=0'`.
The MCP dropdown itself is open, correct, and renders `toolkit-search-input` from its first frame —
the test simply measured the wrong node. **The spec's assertions are right; the page-object's popper
resolution is wrong.**

---

## 2. Live evidence

All runs on `automation/base` HEAD, EliteaUI dev server on `automation/testids`, CI viewport
1366×768, headless.

### 2.1 Baseline — localhost, no tooltip: exactly ONE popper, and it is the dropdown

```
===== AFTER '+ MCP' click (+0ms) :: 1 .MuiPopper-root =====
{"idx":0,"classes":"MuiPopper-root css-1vq0g6h-MuiPopper-root","rect":[373,408,228,130],
 "visibility":"visible","opacity":"1","hasSearchInput":true,"menuItems":0,
 "text":"Create new | Loading...","parentIsBody":true,"parentTag":"BODY."}
[playwright] count=1  first.visible=True  first.searchInputs=1  visible-count=1

===== AFTER '+ MCP' click (+2500ms) =====
{"idx":0,...,"hasSearchInput":true,"menuItems":21,"text":"Create new | autotest_conn_tools_a1 | …"}
```

Confirms the #1890 finding independently: `toolkit-search-input` is present from frame 1;
`toolkit-menu-item` rows arrive ~1–2.5 s later (EL-6351 lazy load).

### 2.2 Tooltip up — the failure reproduces byte-for-byte, and `:visible` does NOT fix it

Same flow, with the "Select LLM Model" tooltip open when "+ MCP" is clicked:

```
===== AFTER hovering model-selector-name :: 1 .MuiPopper-root =====
{"idx":0,"classes":"MuiPopper-root MuiTooltip-popper MuiTooltip-popperInteractive css-tdawq8-…",
 "rect":[1308,878,128,40],"visibility":"visible","opacity":"1",
 "hasSearchInput":false,"menuItems":0,"text":"Select LLM Model","parentIsBody":true}

===== AFTER '+ MCP' click (+0ms) :: 2 .MuiPopper-root =====
{"idx":0,"classes":"MuiPopper-root MuiTooltip-popper …","hasSearchInput":false,"text":"Select LLM Model"}
{"idx":1,"classes":"MuiPopper-root css-1vq0g6h-MuiPopper-root","hasSearchInput":true,"text":"Create new | Loading..."}
[playwright] count=2  first.visible=True  first.searchInputs=0  visible-count=2
```

**Answer to question A, settled:** yes — the "Select LLM Model" MUI `Tooltip` carries `MuiPopper-root`,
it portals to `<body>`, and when it mounts first it sorts **before** the dropdown at `nth=0`.
`visible-count=2` is the reason a `:visible` filter is insufficient.

Note `+600ms`: the tooltip is gone (the click moved the pointer away → `mouseleave` → exit transition),
leaving one popper. The overlap window is short — which is why the assertion at `t≈0` is the one that
catches it and why the *later* `select_mcp_in_popper()` call on the same locator would often recover.

### 2.3 Candidate fix shapes, measured side by side

Real page-object flow (`PipelineDetailPage.navigate → dismiss_banner_if_present → wait_for_canvas →
ensure_toolkits_section_visible → add_mcp_button.click(force=True)`), then each candidate resolved and
measured at the same instant:

```
--- tooltip_up=True :: immediately after '+ MCP' click ---  DOM poppers = 2
  A current  .MuiPopper-root.first            visible=True searchInputs=0 menuItems=0 verdict=FAIL  text='Select LLM Model'
  B :visible .first                           visible=True searchInputs=0 menuItems=0 verdict=FAIL  text='Select LLM Model'
  C :not(.MuiTooltip-popper) .first           visible=True searchInputs=1 menuItems=0 verdict=PASS  text='Create new | Loading...'
  D filter(has=toolkit-search-input) .first   visible=True searchInputs=1 menuItems=0 verdict=PASS  text='Create new | Loading...'
  E .last                                     visible=True searchInputs=1 menuItems=0 verdict=PASS  text='Create new | Loading...'
  [production Popper.wait_for] searchInputs=0 -> step-2 assertion FAILS (CI signature)

--- tooltip_up=False :: immediately after '+ MCP' click ---  DOM poppers = 1
  A/B/C/D/E                                   visible=True searchInputs=1 menuItems=0 verdict=PASS
  [production Popper.wait_for] searchInputs=1 -> step-2 assertion PASSES
```

`E (.last)` is rejected on principle: it only works because the dropdown happens to be the newest
node; a tooltip opening *after* the dropdown breaks it, and nothing in the DOM guarantees ordering.

### 2.4 The CI screenshots — and a THIRD affected spec

Pulled from the run's own allure artifacts (`allure-results-dev-stable-user2-83`, both user2 jobs):

| Spec | Failed assertion | Tooltip in failure screenshot? | Real cause |
|---|---|---|---|
| `test_mcp_node_fresh_attach` (ELITEA-2037) | `search_input_count > 0` | **YES** — "Select LLM Model" over the chat panel | this bug |
| `test_tools_section_mcp_add_view_remove` | `menu_item_count > 0` | **YES** | **this bug** (mis-attributable to #1890) |
| `test_mcp_node_empty_toolkit_before_attach` (ELITEA-1955) | `menu_item_count > 0` | **NO** — dropdown shows "Search mcps… / + Create new / Loading…" | genuinely #1890 (EL-6351 lazy load) — PR #1921 is the correct fix |

Both user2 jobs carry a byte-identical message and attachment for ELITEA-2037 — **deterministic within
that environment, not a flake.**

`test_pipeline_tools_section_mcp_add_view_remove.py::test_tools_section_mcp_add_view_remove` is a
**third casualty that nobody has repaired**: its screenshot shows the tooltip, and its Step 2 counts
menu items immediately after opening with **no** `wait_for_mcp_popper_items()` guard — so it needs
**both** this repair and the already-canonised #1890 guard. Recommend the lead scope it into this
repair (same file-family, same page-object method, one gate).

---

## 3. Question B — why is the tooltip up with no hover from the test?

**Mechanism: proven. Exact CI trigger: not pinned down — reported honestly rather than guessed.**

- The component is a plain MUI `<Tooltip placement="top" title="Select LLM Model">` wrapping the model
  button (`src/[fsd]/widgets/llm-model-selector/ui/LLMModelSelector.jsx:174-182`, prop default
  `modelTooltip = 'Select LLM Model'` at line 31). It is **not** persistently rendered, not
  `keepMounted`, and not controlled — MUI unmounts it when closed. It is therefore standard
  hover/focus-triggered behaviour, **not** an "always visible" element.
- **Two independent triggers reproduce it, both verified live:**
  1. **Hover** — `model-selector-name.hover()` → popper mounts within ~1 s (§2.2).
  2. **Programmatic focus** — `model-selector-name.focus()` → the tooltip opens, because headless
     Chromium reports `document.activeElement.matches(':focus-visible') === true` for a programmatic
     focus, which is exactly the condition MUI's `Tooltip` `onFocus` handler tests:
     ```
     after .focus(): [{'c':'MuiPopper-root MuiTooltip-popper MuiTooltip-popperInteractive …',
                       't':'Select LLM Model'}] | focus-visible: True
     after blur:     []
     ```
     **No hover is required.**
- **What I could NOT establish:** which of the two fires in CI. Six instrumented live runs
  (2 × localhost, 4 × dev.elitea.ai incl. one at 6× CPU throttle to emulate an Azure runner), driving
  the identical page-object flow with capture-phase `focusin`/`mouseover`/`pointerover` listeners and a
  `MutationObserver` on `<body>`, never produced the tooltip unprompted. The only focus the app moves is
  to `chat-message-input`:
  ```
  focusin ts=32995 tgt=chat-message-input
  focusin ts=34739 tgt=agent-add-mcp-button
  focusin ts=34781 tgt=<toolkit-search-input inner input>
  ```
  Ruled out along the way: the `mcp_toolkit_with_tools` fixture (API-only, never touches `page`);
  cross-test mouse/focus carry-over (`context` is function-scoped, `conftest.py:281`); xdist (CI runs
  single-process, `pytest tests/ui/pipelines_2/ -m "not new and not blocked and not flaky" -v --tb=short`);
  a tooltip on the "+ MCP" button itself (`ToolMenu.jsx:604-629` passes `title=''` unless the entity is
  unsaved/locked, so MUI renders no popper for it).
- **Circumstantial support for a page-load-time trigger:** the two specs whose failure screenshots show
  the tooltip both click "+ MCP" as their *first* real mouse interaction, seconds after load; ELITEA-1955
  — whose screenshot shows **no** tooltip — clicks "+ MCP" only after adding a node on the canvas, i.e.
  many seconds and several real mouse events later, by which time any load-time tooltip has closed.

**Recommendation: do NOT file a `bug`.** I cannot demonstrate a product regression — a tooltip that
opens on focus of a focusable button is correct MUI behaviour, and I have no evidence the app
programmatically focuses that button. What I *would* file is a **`question`** card (see §7) recording
that a portal-mounted tooltip can pre-empt any `.MuiPopper-root` lookup, so the suite stops treating
`nth=0` as "the thing I just opened". **The repair must not depend on the tooltip's absence** — that is
the whole point of the recommended shape.

---

## 4. Question C — determinism

| Environment | Runs | Result |
|---|---|---|
| GHA `dev-stable`, project of `autotest_user_2` | 2 independent jobs, run 33066098636 | **FAIL 2/2**, byte-identical message + screenshot |
| dev.elitea.ai, project 399, this workstation | 4 (incl. 1 at 6× CPU throttle) | tooltip never appeared; Step 2 would have **PASSED** 4/4 |
| localhost:5173, project 399 | 2 probes | tooltip never appeared; Step 2 would have **PASSED** 2/2 |
| localhost:5173, tooltip forced up (hover **or** focus) | 2 | **FAIL 2/2**, byte-identical to the CI signature |

So: **conditionally deterministic.** Given the tooltip, the failure is 100 %. The CI environment
reliably produces the tooltip; my environment reliably does not. The repair is therefore validated
against the *condition*, not against the environment — §2.3 is that validation.

### A second, independent defect in the same spec — found while gating

A clean run of the **promoted `main` version** on localhost fails, but one line later:

```
assert pipeline_page.get_mcp_popper_menu_item_count(popper) > 0
E   AssertionError: '+ MCP' popper should list at least one toolkit-menu-item result row …
E   assert 0 > 0
E    +  where 0 = get_mcp_popper_menu_item_count(<Locator … selector='.MuiPopper-root >> nth=0'>)
```

This is the **#1890 / EL-6351 lazy-load race**, and ELITEA-2037 never received the guard — PR #1921
added `wait_for_mcp_popper_items()` to ELITEA-1955's spec **only** (verified:
`git grep -l wait_for_mcp_popper_items origin/main -- automation/tests/` returns exactly
`test_pipeline_mcp_node_empty_toolkit_before_attach.py`). **Fixing the popper scope alone will move the
failure, not clear it.** The repair must add the already-canonised guard call to ELITEA-2037's
Step 2 (and to `test_tools_section_mcp_add_view_remove`'s Step 2). That is a *wait*, not an assertion
change — no weakening, and it has merged precedent on `main`.

---

## 5. Question D — recommended fix shape

### Constraints honoured

- `Popper.wait_for()` has **9 merged callers** (§6) — it is **not modified**. The fix is an **additive
  sibling**, exactly the in-repo precedent set by `Dialog.wait_for_visible()`
  (`components/mui.py:44-73`, added for the `keepMounted` `McpAuthModal` problem — the same class of
  bug, one component up) and by `Popper.select_menuitem_by_testid()`.
- Only the call sites this repair covers are switched.
- `:visible` alone is rejected — measured insufficient (§2.3 row B).
- No new testid is introduced (see the promotion-gap argument below).

### R1 — RECOMMENDED: exclude tooltips, in `components/mui.py`

```python
class Popper:
    # A MUI Tooltip's root is ALSO a `.MuiPopper-root` (class list:
    # `MuiPopper-root MuiTooltip-popper …`) and portals to <body>, so a tooltip
    # already open when a dropdown opens sorts ahead of it and `.first` returns
    # the tooltip. `:visible` does not help — the tooltip is visible too.
    DROPDOWN_POPPER_SELECTOR = ".MuiPopper-root:not(.MuiTooltip-popper)"

    @staticmethod
    def wait_for_dropdown(page: Page, timeout: int = 10000) -> Locator:
        """Additive sibling to :meth:`wait_for` — `wait_for` is NOT modified
        (9 merged callers rely on its plain `.first` behaviour; mui-patterns
        shared-caller rule, same discipline as `Dialog.wait_for_visible`)."""
        popper = page.locator(Popper.DROPDOWN_POPPER_SELECTOR).first
        popper.wait_for(state="visible", timeout=timeout)
        return popper
```

Then switch **only** `PipelineDetailPage.open_mcp_popper()` (`pipeline_detail_page.py:5573`) — and, if
the lead scopes it in, `open_toolkit_popper` / `open_agent_popper` / `open_pipeline_popper` (5713 / 5759 /
5816), which are the same shape on the same page.

**Why this one:** it changes *nothing* about what any spec verifies. Every assertion in ELITEA-2037
Step 2 and ELITEA-1955 Step 7 stays exactly as written and stays capable of failing.

**Its cost, stated plainly — this needs the lead's pre-authorisation in the PR body.** The reviewer's
mechanical grep will flag the added `page.locator(...)` line, and
`.MuiPopper-root:not(.MuiTooltip-popper)` is neither a literal `[data-testid=` selector nor an
UPPER_CASE constant containing one, so **as written it is a mechanical `CHANGES_REQUESTED`**. My
argument for permitting it, offered as a **declared improvisation** under
`.agents/role-overrides.md` § declared-improvisation protocol (first encounter; owed a `question` card
at batch close — §7):

1. The element that must be identified is **MUI's own portal root**, emitted by the library's `Popper`
   component, not by app JSX. `UnifiedDropdown.jsx:188` renders `<Popper …>` with no root-level testid.
   This is the #579 *shape* (a library-internal render node), even though #579's parent-container
   discipline is written for the inverse case (scoping a raw handle *inside* a testid'd parent) — hence
   "declared", not "assumed sanctioned".
2. It could be given a real testid — `UnifiedDropdown` is our code — but `UnifiedDropdown` lives in
   `src/components/` (shared), so per `.agents/testing.md` § Locator policy it would need a
   **caller-supplied `popperTestId` prop** wired at ToolMenu's MCP call site. That is correct work, and
   it is **the wrong tool for this repair**: a new testid cannot reach `dev.elitea.ai` until a human
   cherry-picks it to EliteaUI `main` *and* it deploys, so this already-promoted test would stay red on
   DEV — converting a class-A drift into a self-inflicted class-F promotion gap. Recommend it as a
   **follow-up**, not as this fix.
3. `components/mui.py` is already the designated home for MUI structural selectors
   (`[role="dialog"]`, `.MuiPopper-root`, `li[role="menuitem"]`), so the handle does not leak into
   `pages/` or `tests/`, and the constant is greppable at class level.

### R2 — alternative: scope by content testid (the shape the brief asked me to evaluate)

```python
    DROPDOWN_WITH_SEARCH_SELECTOR = '.MuiPopper-root:has([data-testid="toolkit-search-input"])'
```

Measured equally effective (§2.3 row D) and **mechanically clean** — the added line references an
UPPER_CASE class constant whose definition contains a literal `[data-testid=`, satisfying the reviewer's
one-hop check.

**I do not recommend it for these call sites, and the reason is expected-result integrity.**
ELITEA-2037 Step 2 asserts *"'+ MCP' popper should render a toolkit-search-input search field"*, and
ELITEA-1955 Step 7 asserts the same. If the popper is *selected by* having a `toolkit-search-input`,
that assertion can never fail — it becomes a tautology, and the real verification silently relocates
into a page-object `wait_for` timeout. Per the preserve-the-nature rail that is a change to **what is
verified**, not to **how it is reached**, and it needs explicit human sign-off. I checked for a
different, non-asserted testid inside the popper to scope on and there is none: ToolMenu does not pass
`createNewTestId` to its MCP `UnifiedDropdown` (only `SkillMenu.jsx:213` does), so the "+ Create new"
row renders `data-testid={undefined}`, and `toolkit-menu-item` is both the *other* asserted observable
and absent for the first ~1–2.5 s.

**Decision I am escalating, not taking:** R1 costs one declared non-testid handle in the file that
already owns MUI structural selectors; R2 costs the meaning of one assertion in each of two specs.
I recommend R1 because the rail (what is verified) outranks the grep (how it is located) — but the
grep exception is the lead's to authorise.

### Also required, whichever shape is chosen

Add the already-merged #1890 guard before the menu-item count, identical to
`test_pipeline_mcp_node_empty_toolkit_before_attach.py`'s Step 7:

```python
pipeline_page.wait_for_mcp_popper_items(popper, timeout=UI_ELEMENT_TIMEOUT)
```

- `test_pipeline_mcp_node_fresh_attach.py` — Step 2 (both branch variants), plus the
  `automation/base`-only variant's two extra `open_mcp_popper()` call sites (`Steps 4-6` at base line
  ~356, and the third test's `Setup (transit)` at base line ~555).
- `test_pipeline_tools_section_mcp_add_view_remove.py` — Step 2, if the lead scopes it in.

### Both branch variants must be updated

| Ref | File length | `open_mcp_popper()` call sites |
|---|---|---|
| `origin/main` | 264 lines, 1 test | 1 — Step 2 (line 87) |
| `origin/automation/base` | 674 lines, 3 tests (superset: `main`'s test verbatim + ELITEA-1952 execution + a third) | 3 — lines 106, 356, 555 |

`automation/base` contains `main`'s test byte-for-byte plus two additional tests, so a repair authored
against `automation/base` covers both, provided the two extra call sites are switched too. **Branch the
implementation from `origin/automation/base`** per `.agents/workflow.md` (test PRs never target `main`);
the promoted `main` copy is fixed by the normal `automation/base → main` promotion, not by a direct PR.

---

## 6. Question E — blast radius

**Nothing goes silently green.** A tooltip contains neither `toolkit-search-input` nor
`toolkit-menu-item` nor `li[role="menuitem"]`, so every affected caller fails *loudly* — as a count
assertion (`assert 0 > 0`) or as a `Locator.wait_for` timeout inside `Popper.search()` /
`Popper.select_menuitem*`. The real damage is **misdiagnosis**: the count-assertion form is
indistinguishable at a glance from the #1890 lazy-load race, which is exactly how
`test_tools_section_mcp_add_view_remove` was left unrepaired (§2.4).

### All 9 merged `Popper.wait_for()` callers

| Page object | Line | Method | Specs reaching it |
|---|---|---|---|
| `pipeline_detail_page.py` | 5573 | `open_mcp_popper` | 3 |
| `pipeline_detail_page.py` | 5713 | `open_toolkit_popper` | 3 |
| `pipeline_detail_page.py` | 5759 | `open_agent_popper` | 1 |
| `pipeline_detail_page.py` | 5816 | `open_pipeline_popper` | 3 |
| `agent_detail_page.py` | 1474 | `add_toolkit` | 6 |
| `agent_detail_page.py` | 1525 | `add_mcp` | 1 |
| `agent_detail_page.py` | 1558 | `open_agent_picker` | 1 |
| `agent_detail_page.py` | 2177 | `attach_skill` | 17 |
| `agent_detail_page.py` | 2224 | `open_skill_menu` | 1 |

≈35 merged spec files across `pipelines`, `pipelines_2`, `agents`, `skills`, `chat`, `toolkits`,
`artifacts`, `admin` share this shape. **Recommendation: do NOT switch all 9 in this repair.** The
agent-side call sites (`agent_detail_page.py`) have not been observed failing, they run on a different
page whose tooltip inventory differs, and touching 17+ skills specs turns a targeted repair into an
unbounded gate. Switch the pipeline-side sites now; leave the rest to a follow-up card once the sibling
is merged and proven.

### Regression node-id set to run before merge

**Tier 1 — direct (must be green, or sanctioned-RED with a named reason):**

```
tests/ui/pipelines_2/test_pipeline_mcp_node_fresh_attach.py::test_mcp_node_fresh_attach
tests/ui/pipelines_2/test_pipeline_mcp_node_empty_toolkit_before_attach.py::test_mcp_node_empty_toolkit_before_attach
tests/ui/pipelines_2/test_pipeline_tools_section_mcp_add_view_remove.py::test_tools_section_mcp_add_view_remove
```

(on `automation/base`, ELITEA-2037's file also carries two further tests — run the whole file, not just
the one node id.)

**Tier 2 — same page object, other `open_*_popper()` methods (only if the lead scopes them in):**

```
tests/ui/pipelines_2/test_pipeline_toolkit_node_config_and_input_mapping.py::test_toolkit_node_config_and_input_mapping
tests/ui/pipelines/test_pipeline_create_full_details_persist.py::test_create_pipeline_full_details_persist_after_reload
tests/ui/pipelines/test_pipeline_custom_node_configuration.py::test_custom_node_configuration
tests/ui/pipelines/test_pipeline_agent_node_integration.py::test_agent_node_fresh_attach
tests/ui/pipelines/test_pipeline_attach_pipeline_as_tool.py::test_attach_pipeline_as_tool
tests/ui/pipelines_2/test_pipeline_subgraph_state_isolation.py::test_subgraph_state_sharing_non_common_state_isolation
tests/ui/pipelines_2/test_pipeline_subgraph_state_sharing.py::test_subgraph_state_sharing_common_vars
tests/ui/pipelines_2/test_pipeline_subgraph_state_sharing.py::test_subgraph_state_sharing_node_c_state_propagation
```

**Tier 3 — agent side, run ONLY if `agent_detail_page.py` is touched:**

```
tests/ui/agents/test_mcp_attach_via_tools_section.py
tests/ui/agents/test_agent_self_attachment_blocked.py
tests/ui/skills/test_remove_attached_skill_from_agent.py
```

⚠️ Tier 1 note for whoever gates this: on localhost the ELITEA-2037 file currently fails at the
menu-item assertion for the *lazy-load* reason (§4) — that is expected until the guard is added, and
it is **not** evidence the popper-scope fix failed. Distinguish by reading which assertion fired.

---

## 7. Question F — expected-result integrity

**What ELITEA-2037 verifies (unchanged by this repair):** on a fresh, empty pipeline — that the canvas
holds only `END`; that "+ MCP" opens a picker rendering a search field and ≥1 MCP row; that selecting
the fixture MCP auto-persists via a `PATCH …/tool/prompt_lib/{project}/ → 201`; that the MCP appears as
a flat-list TOOLS card with no console errors; that "Add node → MCP" creates a node with no auto-edge;
that the static config fields (Trigger, Interrupt before/after, Structured output) render *before* a
Toolkit is chosen while the Tool select and Input-mapping accordions stay absent; that choosing a
Toolkit then a Tool reveals the required parameters; that Input-mapping values and the Input/Output
state-variable selects save; and that all of it survives a full page reload.

**Under R1: zero assertion changes.** The repair alters exactly one thing — *which DOM node the popper
locator resolves to*. No assertion is deleted, weakened, made conditional, softened, or reordered; no
count or threshold moves; markers, the `@allure.issue` TMS link, the docstring and the
`allure.step("Step N — …")` structure are preserved verbatim. The added
`wait_for_mcp_popper_items()` is a **wait**, not an assertion change — the menu-item assertion it
precedes keeps its original strictness (`> 0`) and can still fail.

**Under R2: one assertion per spec becomes vacuous** (ELITEA-2037 Step 2 assertion #2, ELITEA-1955
Step 7 assertion #2). That is a *what-is-verified* change and requires the lead's explicit sign-off,
recorded under "Expected-result changes" in the PR body. This is the single reason I rank R1 above R2.

**No TMS case change is needed.** The product behaves exactly as ELITEA-2037 specifies; the case text is
not stale. `automation_test_id` stays as-is.

---

## 8. Testid provenance (fresh fetch — class F ruled out)

`cd ../EliteaUI && git fetch origin` → `c1fe2200..c173c494  main -> origin/main`, then the
closure-record two-stage grep:

```
toolkit-search-input         main:YES  testids:YES
toolkit-menu-item            main:YES  testids:YES
agent-add-mcp-button         main:YES  testids:YES
model-selector-name          main:YES  testids:YES
```

Every testid the spec touches is on EliteaUI `main`. **No promotion gap** — the DEV failure is a genuine
test defect, and the repair needs no new testid (which is also why R1's no-new-testid property matters:
the fix can go green on `dev.elitea.ai` the moment it merges and promotes, with no EliteaUI hop).

---

## 9. For the lead — items to file

1. **`question` card (owed by the declared-improvisation protocol if R1 is chosen).**
   *"`.MuiPopper-root >> nth=0` is not 'the popper I just opened' — MUI Tooltips are poppers too."*
   Proposes the canon addition: a project rule that any `.MuiPopper-root` lookup must be discriminated
   (tooltip-exclusion or content scope), plus the follow-up to give `UnifiedDropdown` a caller-supplied
   `popperTestId` prop so the structural handle can eventually be retired. Include §2.2/§2.3 evidence.
2. **No `bug` card.** I cannot demonstrate a product regression for the tooltip (§3). If the lead wants
   the trigger nailed down, the cheapest next step is a CI-side probe — add a `MutationObserver` dump on
   `.MuiTooltip-popper` mount to a DEV CI run — rather than more local runs; six did not reproduce it.
3. **Scope decision requested:** whether `test_pipeline_tools_section_mcp_add_view_remove` (third
   casualty, needs both fixes) and the three sibling `open_*_popper()` methods ride this repair or a
   follow-up.

## 10. Evidence index

- CI: GHA run 33066098636, job `test / dev-stable - pipelines_2` (databaseId 98546889459); allure
  artifacts `allure-results-dev-stable-user2-83` (ids 9644460016, 9645711376) — failure attachments
  `d7262b38-…-attachment.png` / `4b5e01fd-…-attachment.png` (ELITEA-2037, tooltip visible),
  `4a1ef4e8-…-attachment.png` (tools_section, tooltip visible), `8d812e1d-…-attachment.png`
  (ELITEA-1955, no tooltip).
- Live probes (this workstation, 2026-08-28): popper enumeration on localhost and dev, tooltip
  hover/focus triggers, instrumented focus/mutation trace at 1× and 6× CPU, and the five-candidate
  fix comparison. Raw output is quoted verbatim in §2 and §3; the scratch drivers were throwaway and
  are not committed.
