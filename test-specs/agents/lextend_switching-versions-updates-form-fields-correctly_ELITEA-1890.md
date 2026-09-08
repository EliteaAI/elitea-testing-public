# Test Case: Switching between versions updates form fields correctly

## Metadata
- **TMS ID**: ELITEA-1890
- **Linked Story**: none
- **Priority**: critical (per case frontmatter; body table says "high" — frontmatter is authoritative,
  same convention already used by ELITEA-1888's AFS)
- **Environment Explored**: local (`http://localhost:5173`, EliteaUI `automation/testids` branch → DEV
  backend), project `Private` / `${ELITEA_PROJECT_ID}`=399
- **User set**: `${TEST_USER}` (on localhost, `auth_state` fixture skips login via `VITE_DEV_TOKEN`)
- **Analyst**: qa-engineer (Sage), analyst slot — cluster dispatch with ELITEA-1891 (shared
  session/discovery, each case executed and classified individually — see that AFS for the sibling
  case; not merged into one family AFS because the two cases assert different observables: this one
  asserts Instructions-field content across a switch round-trip, ELITEA-1891 asserts dropdown ordering
  + metadata — "differ in steps", not "differ only in data")
- **Status**: `extend-existing` — all 6 case steps executed and verified live against the real system, no
  blockers, no defects. An existing MERGED spec
  (`automation/tests/ui/agents/test_agent_save_as_version.py`, ELITEA-1888,
  `origin/automation/base@2b03f6c0`) already covers this case's steps 1-4 verbatim (navigate, note active
  version + Instructions, Save As Version to create a second version with distinct Instructions, verify
  the new version's Instructions). **The gap is steps 5-6**: switching BACK to the original version and
  verifying the Instructions field reverts to the original content — that specific "switch back" round
  trip is not exercised anywhere in the existing spec. No new testids were needed — every handle this
  extension touches is already live (added in ELITEA-1888's run) and already declared on
  `AgentDetailPage`/`AgentFormPage`.

## Preconditions
- User is logged in (on localhost, `auth_state` fixture skips login).
- A project is selected/accessible (`Private`, id `399` in this run).
- An agent with at least 2 versions (base + named version) exists, with distinct Instructions in each
  version. **Already satisfied by the covering spec's own precondition/setup** — it creates a dedicated
  disposable agent via `AgentAPI.create_agent_full()` (payload `_build_dedicated_agent_payload()`, base
  Instructions = `"You are a helpful assistant."`) and, by its own Steps 2-5, produces a second named
  version (`"v2-test"`, Instructions = base + `" Additionally."`) — this is exactly this case's stated
  precondition, already built by the covering test before the point where the extension's new assertions
  need to run.

## Test Data

### reuse-existing (extension of ELITEA-1888's covering spec)
- No new test data. The extension reuses the SAME dedicated disposable agent the covering spec already
  creates and tears down (`agent_api.create_agent_full()` at setup, `delete_agent_via_menu()` /
  `agent_api.delete_agent()` at teardown) — appending assertions after the covering spec's existing Step
  7 (`close_version_selector()`), before its `finally` cleanup block. No separate agent, no separate
  fixture.
- Literal values already established by the covering spec, reused as-is:
  - `BASE_INSTRUCTIONS = "You are a helpful assistant."`
  - `INSTRUCTION_APPEND = " Additionally."` → `expected_instructions = BASE_INSTRUCTIONS + INSTRUCTION_APPEND`
  - `VERSION_NAME = "v2-test"`

## Test Steps

_Steps 1-4 below are the EXISTING covering spec's Steps 1-7 (already merged, already passing — cited for
traceability, not re-implemented). Steps 5-6 are the GAP this extension adds._

1. Navigate to an agent that has at least 2 versions (base + named version) with distinct instructions.
   — **Covered by** `test_save_as_version_creates_named_version_visible_in_dropdown`'s existing Step 1
   (`detail_page.navigate(agent_id)`, asserts `get_version_selector_value() == "base"`).
2. Note the active version and its Instructions content. — **Covered by** the covering spec's existing
   Step 1 (`original_instructions = detail_page.get_instructions()`).
3. Open the version dropdown and select the other version. — **Covered by** the covering spec's existing
   Steps 2-5 (edits Instructions, clicks Save As Version, confirms — this IS how the "other version" with
   distinct content comes to exist and become active; the covering spec's flow creates-then-switches-to
   the second version rather than switching between two pre-existing ones, which is a normal, equivalent
   way to reach the same state per Rule-6 behavioral equivalence — the case only requires two versions
   with distinct content and the Instructions field reflecting whichever is currently selected).
4. Verify the Instructions field updates to reflect the selected version's content. — **Covered by** the
   covering spec's existing Step 5 assertion: `detail_page.get_instructions() == expected_instructions`
   (i.e. the new version's Instructions, confirmed distinct from the base version's).
   - **Verify — PASSES (re-confirmed live this run).**
5. Switch back to the original version. — **GAP. New step, appended after the covering spec's existing
   Step 7** (`close_version_selector()`), before cleanup:
   ```python
   with allure.step("Step 8 — Switch back to the original 'base' version"):
       detail_page.open_version_selector()
       detail_page.page.locator(detail_page.VERSION_OPTION.format("base")).click()
       detail_page.page.wait_for_function(
           """() => {
               const el = document.querySelector('[data-testid="agent-version-selector-trigger"]');
               return el && el.innerText.trim() === 'base';
           }""",
           timeout=10000,
       )
   ```
   (Mirrors the wait-condition shape already used by `AgentDetailPage.select_version_by_name()` — see
   Handles Reference below for why this extension uses the raw open+click+wait sequence rather than that
   method directly.)
   - **Verify — PASSES.** `agent-version-selector-trigger` text becomes `"base"`.
6. Verify the Instructions field returns to the original version's content. — **GAP. New assertion,
   same step:**
   ```python
       assert detail_page.get_instructions() == original_instructions, (
           "Instructions field should revert to the original 'base' version's "
           "content after switching back"
       )
   ```
   - **Verify — PASSES.** Confirmed live this run: after round-tripping base → v2-test → base, the
     Instructions field read back byte-identical to `original_instructions` (`"You are a helpful
     assistant."`) — no drift, no stale cached value from the intermediate version.

### Live confirmation (independent probe, same flow, disposable agent)
Re-verified the full switch/switch-back mechanic end-to-end on a separate disposable agent before writing
this AFS (agent id 6589, deleted after): base → edited+Save-As-Version `"v1-early-draft"` (Instructions
gained a `" DRAFT-1 marker."` suffix) → switched to `"base"` (Instructions read back exactly the
pre-edit base text) → switched to `"v1-early-draft"` (Instructions showed the marker text) → switched
back to `"base"` again (Instructions matched the original exactly). All four transitions updated the
Instructions field correctly and immediately — no defect, no case-text drift.

## Handles Reference

All handles below are **pre-existing and already declared** on `AgentFormPage`/`AgentDetailPage` — no
`add-data-testid` work needed for this extension.

| Element | testid | Declared at | Confirmed live this run? |
|---|---|---|---|
| Instructions field | `agent-instructions-input` | `AgentFormPage.instructions_input` | yes |
| VERSION dropdown trigger | `agent-version-selector-trigger` | `AgentDetailPage.version_selector_trigger` | yes |
| Version dropdown option (dynamic) | `version-option-{version_name}` | `AgentDetailPage.VERSION_OPTION` (template constant) | yes |
| Save As Version button | `agent-save-as-version-button` | `AgentFormPage.save_as_version_button` | yes — **no longer carries a `fallback=` param** (the ELITEA-1888/1889 AFS's flagged pre-existing violation on this exact field has since been cleaned up; confirmed by reading the current `agent_form_page.py:163-166`) |
| Save button (read-only, for `is_save_enabled()`) | `agent-save-button` | `AgentFormPage.save_button` | yes — **still carries a `fallback=` param** (pre-existing violation, NOT introduced by this extension and not touched by it; same finding pattern as ELITEA-1888/1889, now narrowed to `save_button`/`cancel_button`/`discard_button` only) |

### Existing page-object methods reused (no new methods required)
- `AgentDetailPage.navigate(agent_id)`
- `AgentFormPage.get_instructions()` / `instructions_input`
- `AgentDetailPage.open_save_as_version_dialog()` / `confirm_new_version()` / `save_as_version()`
- `AgentDetailPage.open_version_selector()`, `VERSION_OPTION` template, `get_version_selector_value()`,
  `is_version_option_active()`, `close_version_selector()`

**Why the extension doesn't call `select_version_by_name()`.** `AgentDetailPage.select_version_by_name()`
(added for ELITEA-1892) is the hardened, retry-with-reload version-switch method built to work around
issue #614's overflow-menu/status staleness. This case's Step 5 only needs the VERSION selector's own
trigger text to update (no Publish/Unpublish menuitem involved, no `#614` surface touched) — the simpler
open+click+wait-for-trigger-text sequence used by the covering spec's own existing pattern is sufficient
and was confirmed live not to need a reload or retry. The implementer may use
`select_version_by_name("base")` instead if preferred for consistency (it is a superset — the extra
reload/retry is harmless overhead here, just unnecessary) — noted as an implementation choice, not a
requirement.

## Coverage Map

### Axis 1 — Case element → Coverage
| Case element | Expected result | Covered by | Asserted where | Disposition |
|---|---|---|---|---|
| Precondition: agent with ≥2 versions, distinct Instructions | Agent detail page reachable, two distinct-content versions exist | Covering spec's setup + Steps 1-5 | `test_agent_save_as_version.py` (ELITEA-1888), merged `origin/automation/base@2b03f6c0` | covered (existing) |
| Step 1: Navigate to agent with ≥2 versions | Agent detail page loads | Covering spec's Step 1 | `detail_page.navigate(agent_id)`, `get_version_selector_value() == "base"` | covered (existing) |
| Step 2: Note active version + Instructions | Current version name + Instructions recorded | Covering spec's Step 1 | `original_instructions = detail_page.get_instructions()` | covered (existing) |
| Step 3: Open dropdown, select the other version | Version is switched | Covering spec's Steps 2-5 (reaches the second version via create-then-active, a Rule-6-equivalent path to switching between two pre-existing versions) | `confirm_new_version()` → `get_version_selector_value() == VERSION_NAME` | covered (existing) |
| Step 4: Instructions field updates to selected version's content | Field shows the new version's content | Covering spec's Step 5 | `get_instructions() == expected_instructions` | covered (existing) |
| Step 5: Switch back to the original version | Original version re-selected | **New — appended Step 8** | `VERSION_OPTION.format("base")` click + `wait_for_function` on trigger text | **gap, now covered by this extension** |
| Step 6: Instructions field returns to original content | Field shows original version's content | **New — appended Step 8** | `get_instructions() == original_instructions` | **gap, now covered by this extension** |
| Expected Final State: switching updates fields both directions | — | Covering spec (forward direction) + this extension (return direction) | — | covered (existing + extension) |

### Axis 2 — Observables asserted beyond the case
| Observable | Reason |
|---|---|
| Round-trip byte-identity of `original_instructions` after base → v2-test → base | The case only asks that the field "returns to the original content" — asserting exact string equality (not just non-empty / not-equal-to-intermediate) is the strongest form of that check and catches any silent truncation/whitespace drift a looser assertion would miss. |
| Independent live re-probe on a second disposable agent, including a THIRD hop (base → v1-early-draft → base again) | Confirms the mechanic isn't a one-shot fluke tied to this specific agent/version pair — same page-object handles, same wait condition, reproduced cleanly twice. |

## Known Defects
None hit or newly filed by this run. The covering spec's own known pre-existing gaps (Discard-button
testid not live, `save_button`/`cancel_button`/`discard_button` still carrying a `fallback=` param) are
unchanged and out of this extension's scope — this extension does not touch Discard, Save, or Cancel.

## Cleanup
No new cleanup — the extension appends into the covering spec's existing `try/finally` block, before its
existing `finally` cleanup (`delete_agent_via_menu()` / `agent_api.delete_agent()`), so the same
dedicated disposable agent used for Steps 1-4 is reused and deleted exactly once, same as today.

## Blocked Steps
None. All 6 case steps executed and verified live (4 via the existing covering spec's already-passing
assertions, 2 via this run's new live verification of the switch-back gap).

## Automation Hints
- Framework: Playwright + pytest.
- **Implementation shape: extend, don't duplicate.** Add a new `allure.step("Step 8 — …")` block (or two,
  matching the case's own step numbering if the implementer prefers to renumber to match ELITEA-1890's
  6 steps exactly) directly after
  `test_agent_save_as_version.py::TestAgentSaveAsVersion::test_save_as_version_creates_named_version_visible_in_dropdown`'s
  existing Step 7 (`close_version_selector()`), inside the same `try` block, before the `finally`. Do **not**
  create a second test method or a second disposable agent for this case — the gap is two assertions on
  data the covering spec already has in scope (`original_instructions`, the same `detail_page`).
- Consider renaming/re-annotating the test's module docstring and `@allure.issue` reference to note it
  now also covers ELITEA-1890 (both TMS IDs), matching how other multi-case-covering specs in this suite
  are documented (e.g. cite both case links) — implementer's call on exact form, not load-bearing for the
  assertions themselves.
- No new testid, no new page-object method required (see Handles Reference above).

---

## Adjustment — 2026-09-09 (issue #2052, triage class A: UI drift)

**Trigger.** The covering spec went red on the nightly `UI Tests DEV Stable`
(GHA run 34244735426, shard `dev-stable-user3-110`) at Step 8, with
`Locator.click: Timeout 10000ms exceeded` on `agent-version-selector-trigger`:
the VERSION dropdown from Step 6/7 was still open, and MUI's invisible
`MuiBackdrop-root` (`id="menu-"`) intercepted every click for the full 10 s.

**What drifted.** EliteaAI/EliteaUI@cf648e9a (PR #857) gave the VERSION dropdown
a search field. `SingleSelectDropdown.jsx` mounts it as
`<SimpleSearchBar onKeyDown={e => e.stopPropagation()} />`, and `SimpleSearchBar`
autofocuses itself and maps Escape to "clear the search box" before calling that
external handler. So whenever focus sits in that search field, the page-level
Escape the spec used to close the dropdown is **consumed and stopped** — the MUI
`Modal` never sees it and the menu stays open. Confirmed live 2026-09-08: from
that state two consecutive page-level Escapes left `aria-expanded="true"` with
every option still rendered; one Escape pressed **on an option** closed it, URL
unchanged.

**Expected-result changes: NONE.** Every assertion, step, count and comparison in
this AFS is unchanged. The mechanism the spec uses to dismiss the dropdown
changed (and see the second change recorded below): `close_versions_menu()` (bare, unconfirmed Escape — still correct for the
skill card's Versions menu, which has no search field) →
`AgentDetailPage.close_version_selector()`, which presses Escape on an option and
then **confirms** closure via the trigger's own `aria-expanded="false"`
(`agent-version-selector-trigger-combobox`, a pre-existing testid present on
EliteaUI `main`), raising with the live `aria-expanded` value if it cannot.

**Second change in the same diff — `open_version_selector()`, and its blast radius.**
The dismissal mechanism is not the only thing that moved.
`AgentDetailPage.open_version_selector()` also changed, in three ways: it gained a
`timeout` parameter, a post-condition wait on the trigger's `aria-expanded="true"`
(a **new raise point** — previously it returned with nothing checked), and it now
clicks the trigger only while the dropdown is collapsed, because clicking it while
open cannot succeed (MUI's invisible backdrop intercepts the pointer event — the
very failure this repair addresses).

That method is **shared, with five `AgentDetailPage` callers**:
`select_version_by_name()` (`pages/agent_detail_page.py:4146`),
`test_agent_publish_unpublish_version.py:538`, `test_agent_save_as_version.py:189`,
and `test_agent_version_selector_order.py:290` + `:336`. (Counted with
`grep -rn "open_version_selector()"`: the **three** `tests/ui/skills/` call sites in
two files — `test_skill_fork_non_base_version.py:167`, `test_skill_version_set_default.py:80`
and `:129` — are `SkillDetailPage`, which has its own `open_version_selector` at
`pages/skill_detail_page.py:1167`; and the **three** `tests/ui/pipelines/` call sites in
two files — `test_pipeline_create_version.py:133`, `test_pipeline_delete_version.py:86`
and `:149` — are `PipelineDetailPage`, own definition at `pages/pipeline_detail_page.py:2060`.
Both classes are genuinely untouched by this diff.)

The one worth naming: the `select_version_by_name()` call site sits **inside its
retry loop but outside the loop's `try:`**, so the new raise is *not* retried by
that loop — it aborts the whole call. This does not change the abort *behaviour*,
only the message: before the change, the same conditions failed one or two lines
later at `option.wait_for(state="visible")` (or at the intercepted `.click()`),
equally unretried. It is recorded here because the raise point moved, and because
a reader tracing a `select_version_by_name` failure should know the loop cannot
absorb it.

The close post-condition is likewise two-part, not one: `aria-expanded="false"`
**and** zero `version-option-*` nodes remaining — and the method has **no early
return**, so that conjunction gates every exit whatever state the dropdown was in
on entry. (Review round 2: an earlier `if collapsed.count() > 0: return` entry guard
turned a `to_have_count` timeout on one attempt into a silent success on the next,
making the raise unreachable on precisely the state the count term exists to detect.
The loop now presses Escape only while `aria-expanded` is still `"true"`, and simply
waits out the closing window otherwise — pressing into a detaching subtree is its own
hazard.) `aria-expanded` tracks React
`open` state and flips before `MuiBackdrop-root` unmounts at the end of the `Grow`
exit transition, so on its own it is a leading indicator; the options unmount with
the Menu subtree, so their absence is what proves the backdrop is gone.

**Handles.** No new testid. `agent-version-selector-trigger-combobox` is
`SingleSelect.jsx:663`'s `SelectDisplayProps` testid — PROVENANCE: `on-main ✓`.
