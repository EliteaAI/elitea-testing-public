# Test Case: Switching between versions updates form fields correctly

## Metadata
- **TMS ID**: ELITEA-1890
- **Linked Story**: none
- **Priority**: critical (per case frontmatter; body table header says "high" —
  frontmatter is authoritative, same reconciliation as ELITEA-1888)
- **Environment Explored**: local (`http://localhost:5173`, EliteaUI `automation/testids`
  branch → DEV backend), project `Private` / `${ELITEA_PROJECT_ID}`=399
- **User set**: `${TEST_USER}` (on localhost, `auth_state` fixture skips login via
  `VITE_DEV_TOKEN` — no login step needed, confirmed by navigating directly)
- **Analyst**: qa-engineer (Sage), analyst slot
- **Status**: `ready-for-automation` — case executed end-to-end against the live
  system (all 6 steps), no product defects hit. **Zero testid gaps** — every
  handle this case needs was added by prior cases (ELITEA-1888/1889/1892) and is
  now confirmed **on `main`** (see Handles Reference provenance column); no
  `add-data-testid` work is required for this case.

## Preconditions
- User is logged in (on localhost, `auth_state` fixture skips login).
- A project is selected/accessible (`Private`, id `399` in this run).
- An agent exists with **at least 2 versions carrying distinct Instructions
  content** — **not naturally present in the environment**; created as
  disposable test data for this run (see Test Data below). This mirrors the
  exact setup ELITEA-1888/1889 already established as the project's standard
  pattern for version-bearing agent fixtures.

## Test Data

### generate-per-test (in test setup, cleaned up in its own teardown)
Dedicated, uniquely-named agent created via `AgentAPI.create_agent_full()` with
the same `reasoning_effort: "none"` / no-`temperature` workaround payload
`test_agent_save_as_version.py::_build_dedicated_agent_payload()` (ELITEA-1888)
already uses — avoids the open, unrelated
[EliteaAI/elitea-testing-public#524](https://github.com/EliteaAI/elitea-testing-public/issues/524)
defect (`temperature` + non-`"none"` `reasoning_effort` 400s on the project's
reasoning-capable default model). **Do NOT** use the plain `AgentAPI.create_agent()`
helper or the shared `agent_id` fixture for this case's fixture data — both still
hit #524 (reconfirmed as recently as the ELITEA-1889 pass; not re-verified again
this run since this case's setup used `create_agent_full()` directly).

Literal values used this run (any distinguishable pair works — the case does
not assert exact wording, only that the two versions' Instructions differ and
that switching reproduces each verbatim):
| Field | Value |
|---|---|
| Agent name | `elitea-1890-ver-<uuid8>` (32-char API limit — keep prefix short, same constraint noted in ELITEA-1888's AFS) |
| Base version Instructions | `"BASE VERSION INSTRUCTIONS - ELITEA-1890."` |
| Second version name | `v2-distinct` |
| Second version Instructions | Base text with additional distinguishing text appended via the Instructions field before "Save As Version" (this run: full field content became `"BASE VERSION INSTRUCTIONS - ELITEA-1890.V2 DISTINCT INSTRUCTIONS - ELITEA-1890 SWITCHED."` — any append works; the point is the two versions' Instructions differ) |

**Setup procedure (not case steps — establishes the precondition; matches the
existing `AgentDetailPage` methods 1:1, no new page-object work needed):**
1. `AgentAPI.create_agent_full(payload)` → agent id (base version = "base",
   Instructions = the literal above).
2. `AgentDetailPage.navigate(agent_id)` → lands on "base" (confirmed: bare
   `/agents/all/{id}?viewMode=owner`, no version segment, defaults to "base" —
   same behavior ELITEA-1888 documented).
3. Edit the Instructions field (`instructions_input.click()` → `.clear()` →
   `.press_sequentially(new_text, delay=50)` — **MUI/React onChange
   requirement, `fill()` will not work**, `.claude/rules/mui-patterns.md`).
4. `open_save_as_version_dialog()` → `confirm_new_version("v2-distinct")` —
   creates the second version, auto-navigates to it (`agent_detail_page.py:506-572`,
   pre-existing, reused unchanged from ELITEA-1888).

No `reuse-existing` fixture applies — this is fresh-state-per-run, cleaned up
in full at teardown (whole-agent delete, which removes all its versions in one
action).

## Test Steps

1. Navigate to the agent's detail page fresh (bare `?viewMode=owner`, no
   version segment) and note the active version + its Instructions content.
   - **Verify — PASSES.** `agent-version-selector-trigger` reads `"base"`;
     `copy-version-id` reads the base version's numeric id (`5774` this run);
     Instructions field (`agent-instructions-input`) reads the base literal
     verbatim (`"BASE VERSION INSTRUCTIONS - ELITEA-1890."`).
2. Open the VERSION dropdown (`agent-version-selector-trigger`) and select the
   other version (`v2-distinct`) via its dynamic option
   (`version-option-v2-distinct`, the `VERSION_OPTION` template pattern).
   - **Verify — PASSES.** Dropdown (`role="listbox"`) shows exactly 2 options
     — `"base - <date>"` (`Mui-selected` before the click) and
     `"v2-distinct - <date>"` — confirming both versions are present and
     distinguishable, satisfying the case's own precondition as an
     observable, not just an assumed setup fact. After the click: URL updates
     to `/agents/all/{id}/{v2_version_id}` (`5775` this run),
     `agent-version-selector-trigger` reads `"v2-distinct"`, `copy-version-id`
     reads `5775` — all three agree (no #614-style staleness observed this
     run; see Known Defects for context on why the implementer should still
     use `select_version_by_name()` rather than a raw dropdown click).
     **Instructions field immediately reflects the newly-selected version's
     content** — reads the full `v2-distinct` literal verbatim, distinct from
     the base text read in Step 1. This is the case's core assertion and it
     PASSES.
3. Switch back to the original version ("base") via the same dropdown
   mechanism (`version-option-base`).
   - **Verify — PASSES.** URL reverts to `/agents/all/{id}/{base_version_id}`
     (`5774`), `agent-version-selector-trigger` reads `"base"` again,
     `copy-version-id` reads `5774` again — all three agree. **Instructions
     field returns to the exact original content read in Step 1**
     (`"BASE VERSION INSTRUCTIONS - ELITEA-1890."`, byte-for-byte). This is
     the case's second core assertion (switch-back restores original content)
     and it PASSES.

No console errors or warnings observed at any point across all 3 steps
(checked after every interaction, not just at the end).

## Expected Results

Matches the case's own Pass/Fail Criteria exactly: the Instructions field
updates to reflect each version's own content when switching in either
direction, byte-for-byte, with no console errors. **Confirmed live, no
discrepancy, no defect.**

## Coverage Map

### Axis 1 — Case element → Coverage
| Case element | Expected result | Covered by (AFS step) | Asserted where | Disposition |
|---|---|---|---|---|
| Precondition: agent with ≥2 versions, distinct Instructions each | Such an agent is reachable | Setup (not a numbered case step) | Dedicated agent created via API + one "Save As Version" with edited Instructions; both versions' distinct Instructions content independently read in Steps 1/2 | asserted (via setup + Step 1/2 readback) |
| Step 1: Navigate to an agent with ≥2 versions | Agent detail page loads | AFS Step 1 | Page loaded, `agent-version-selector-trigger` + Instructions field both readable | asserted |
| Step 2: Note the active version and its Instructions content | Version name + Instructions text recorded | AFS Step 1 | `"base"` / base literal recorded as the baseline for Step 3's restore-check | asserted |
| Step 3: Open the version dropdown and select the other version | The version is switched | AFS Step 2 | Dropdown opened, both options visible, `v2-distinct` clicked, URL/trigger/version-id all updated to the new version | asserted |
| Step 4: Verify the Instructions field updates to reflect the selected version's content | Instructions field shows the newly selected version's content | AFS Step 2 | Instructions field read immediately after the switch — matches the v2-distinct literal, differs from Step 1's base literal | asserted |
| Step 5: Switch back to the original version | The original version is re-selected | AFS Step 3 | Dropdown opened again, `base` option clicked, URL/trigger/version-id all revert to the base version's values | asserted |
| Step 6: Verify the Instructions field returns to the original version's content | Instructions field shows the original version's content | AFS Step 3 | Instructions field read after switching back — matches Step 1's base literal byte-for-byte | asserted |

### Axis 2 — Observables asserted beyond the case
| Observable | Reason |
|---|---|
| Three-way consistency (VERSION trigger text ⇄ `copy-version-id` ⇄ URL version-id segment) after each switch, not just the Instructions field | This is exactly the convergence condition `AgentDetailPage.select_version_by_name()` already polls for (documented issue #614 — client-side status staleness can otherwise leave stale UI state momentarily) — asserting all three gives the automated test the same robustness guarantee the existing helper already encodes, and catches a partial-navigation regression the Instructions-field check alone might miss |
| VERSION dropdown lists exactly 2 options with correct `Mui-selected`/active state on the currently-active one, both before AND after each switch | Directly grounds the case's implicit "the version really did change, not just the field" — an implementer who only reads the Instructions field text could theoretically pass on a coincidental match; cross-checking the dropdown's own selected-state removes that gap |
| No console errors/warnings across all 3 steps | Silent errors are the worst bugs (`test-case-analysis` discipline) — explicitly checked after every interaction |

## Cleanup

- Dedicated agent (id `5657` this run, `elitea-1890-ver-<uuid8>`) deleted in
  full via `AgentAPI.delete_agent(agent_id)` — removes both versions (base +
  `v2-distinct`) in one action, no separate per-version cleanup needed.
  Verified via a follow-up `get_agent()` call returning an error for the
  deleted id (API returns `400`, not `404`, for a since-deleted agent id — a
  pre-existing API quirk, not something this case needs to assert on; the
  absence of the id from `list_agents()` is the authoritative check if the
  implementer wants a stronger assertion than the error alone).
- No other test data created or left behind.

## Concrete Handles (discovered during exploration)

**Locator policy note:** this project is testid-only (`.agents/testing.md` §
Locator policy, `.agents/role-overrides.md`) — the generic
role/label/text/CSS ladder does not apply here. All handles below are
`data-testid`-based, matching existing `LocatorDescriptor` fields already on
`AgentDetailPage`/`AgentFormPage`. **Zero new testids needed — every handle
below is already wired as a page-object field and confirmed on `main`.**

| Element | testid | Page-object field / method | Provenance (fresh `git fetch origin` this run) |
|---|---|---|---|
| Instructions field | `agent-instructions-input` | `AgentFormPage.instructions_input` / `get_instructions()` | **on-main ✓** — `src/[fsd]/features/agent/ui/agent-details/configurations/input/InstructionsInput.jsx` |
| VERSION dropdown trigger | `agent-version-selector-trigger` | `AgentDetailPage.version_selector_trigger` / `get_version_selector_value()` | **on-main ✓** — `src/[fsd]/entities/application-tab-bar/ui/ApplicationVersionSelect.jsx` |
| Version dropdown option (dynamic) | `version-option-{version_name}` | `AgentDetailPage.VERSION_OPTION` template constant (`.format(name)`) | **on-main ✓** — `src/[fsd]/entities/version/lib/helpers/version.helpers.jsx` |
| Version ID readout | `copy-version-id` | `AgentDetailPage.copy_version_id_button` / `get_version_id()` | **on-main ✓** — `src/pages/Applications/Components/Applications/ApplicationInformation.jsx` |
| Save As Version button (setup only) | `agent-save-as-version-button` | `AgentFormPage.save_as_version_button` (inherited); **note — this field carries a `fallback=` param that is forbidden by `.agents/testing.md` § Locator policy; pre-existing violation flagged again here, same finding as ELITEA-1888/1889 — strip it whenever this file is next touched, out of scope to fix as part of this case** | **on-main ✓** — `src/pages/Applications/Components/Applications/SaveNewVersionButton.jsx` |
| Create-version dialog Name input (setup only) | `agent-version-dialog-name-input` | `AgentDetailPage.create_version_name_input` | **on-main ✓** — `src/pages/Applications/Components/Applications/SaveNewVersionButton.jsx` |
| Create-version dialog Save button (setup only) | `agent-version-dialog-save-button` | `AgentDetailPage.create_version_save_button` | **on-main ✓** — same file |

**Recommended implementation method — use `select_version_by_name()`, not a
raw dropdown click.** `AgentDetailPage.select_version_by_name(version_name)`
(`automation/pages/agent_detail_page.py:2936-3063`) already encapsulates
open-dropdown → click-option → poll-for-three-way-convergence
→ (if needed) reload-and-repoll, up to 2 full cycles, specifically to absorb
the documented issue #614 staleness. This run's manual exploration (CDP-driven,
not through this helper) converged immediately with no retry needed both
directions, but the automated test should still go through the helper for the
same durability guarantee the project's other version-switching tests
(`test_agent_publish_unpublish_version.py`) already rely on — reimplementing
the raw click in a new test would silently drop that hardening.

## Network Behavior

Not captured this run — `browser-verify`'s per-session network log returned
empty for the SPA route-level version switches (client-side-routed, no full
navigation event resets the capture the same way `navigate()` does). Not
load-bearing for this case: the Instructions field content is the case's own
assertion surface, and it was verified directly via the DOM (`get-value`), not
inferred from network traffic. **Automation hint:** if the implementer wants a
network-level assertion, `test_agent_publish_unpublish_version.py` and
`confirm_new_version()`'s own wait strategy show the pattern of waiting on the
version-scoped `GET .../application/prompt_lib/{project}/{agent_id}` (or
equivalent per-version fetch) — not required for this case's own pass/fail
criteria.

## Known Defects Found During Exploration

None hit or newly filed by this run. For context only:
- [EliteaAI/elitea-testing-public#524](https://github.com/EliteaAI/elitea-testing-public/issues/524)
  (OPEN) — constrains this case's test-data strategy (see Test Data above);
  not triggered this run since `create_agent_full()` with the workaround
  payload was used from the start.
- Issue #614 (client-side status staleness after version-scoped actions,
  documented in `select_version_by_name()`'s own docstring) — **not
  reproduced this run** (both switches converged immediately, no reload
  needed), mentioned only because it directly motivates using
  `select_version_by_name()` over a raw dropdown click in the automated test
  (see Concrete Handles above).

## Blocked Steps

None. All 6 case steps executed and verified live, no defects encountered, no
testid gaps, no ambiguous handles.

## Automation Hints

- Framework: pytest + Playwright, project's existing page-object model
  (`automation/pages/agent_detail_page.py`, `AgentDetailPage(AgentFormPage)`).
- Closest sibling implementation to model this test on:
  `tests/ui/agents/test_agent_save_as_version.py` (ELITEA-1888) for the
  dedicated-agent-fixture pattern (`_build_dedicated_agent_payload()`,
  `create_agent_full()`, `delete_agent_via_menu()`-equivalent teardown via
  `AgentAPI.delete_agent()`) and the Instructions-edit-then-Save-As-Version
  flow used here purely as setup. `tests/ui/agents/test_agent_publish_unpublish_version.py`
  is the closest sibling for the actual version-switch mechanics
  (`select_version_by_name()` usage pattern, including its bounded-retry
  rationale re: issue #614).
- This case's assertion surface (Instructions field content per version, both
  directions) is NOT covered by either sibling test — `test_agent_save_as_version.py`
  only checks the dropdown lists the new version and is active; it never
  switches back to "base" nor re-reads Instructions after a switch.
  `test_agent_publish_unpublish_version.py` switches versions via the same
  helper but never asserts Instructions content per version. Neither
  qualifies as `already-covered`/`extend-existing` under the merged-target
  rule — this is fresh implementation, reusing existing infra with zero new
  page-object or testid work.
- Wait strategy: `select_version_by_name()`'s own internal wait (VERSION
  trigger text + `copy-version-id` + URL segment three-way match) is
  sufficient — no additional sleep/timeout needed before reading
  `get_instructions()` after a switch.
- MUI/React gotcha for the setup step: instructions edit must use
  `.click()` + `.clear()` + `.press_sequentially(text, delay=50)` —
  `fill()` does not trigger React's `onChange` and the Save/Save As Version
  buttons will not enable (`.claude/rules/mui-patterns.md`).
