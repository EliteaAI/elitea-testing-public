# Test Case: Version selector lists all versions in correct order with expected metadata

## Metadata
- **TMS ID**: ELITEA-1891
- **Linked Story**: none
- **Priority**: l2 (high, per case frontmatter)
- **Environment Explored**: local (`http://localhost:5173`, EliteaUI `automation/testids` branch → DEV
  backend), project `Private` / `${ELITEA_PROJECT_ID}`=399
- **User set**: `${TEST_USER}` (on localhost, `auth_state` fixture skips login via `VITE_DEV_TOKEN`)
- **Analyst**: qa-engineer (Sage), analyst slot — cluster dispatch with ELITEA-1890 (shared
  session/discovery; each case executed and classified individually, not merged into one family AFS —
  see ELITEA-1890's AFS for why: the two cases assert different observables)
- **Status**: `ready-for-automation` — all 8 case steps executed end-to-end against the live system.
  Neighbour search (`grep -rn "is_version_option\|version_selector" automation/tests/ui/agents/`) found
  no existing merged spec asserting dropdown **ordering** or **pin-icon** behavior — the two specs that
  touch the VERSION dropdown (`test_agent_save_as_version.py`, `test_agent_publish_unpublish_version.py`)
  only assert that specific named options are *present* and *active*, never their relative order or icon
  content, so this is fresh coverage, not `extend-existing`. **Two testid gaps were found and need
  closing before the ordering/pin assertions can be implemented testid-only** (see § EliteaUI testid gaps
  below) — the implementer runs `add-data-testid` for both before writing the test, per the project's
  testid-only locator policy. One CLARIFICATION was filed on case-text drift (the case's implied
  Pinned→Published→Draft→base three-tier ordering does not match the live sort algorithm); it does not
  block automation — this AFS's Test Steps already describe the real rule.

## Preconditions
- User is logged in (on localhost, `auth_state` fixture skips login).
- A project is selected/accessible (`Private`, id `399` in this run).
- An agent with base version, at least one Draft named version, and optionally a Published version
  exists — **satisfied by creating a dedicated, disposable agent per run**, consistent with the pattern
  used in ELITEA-1888/1889/1892's AFS history. No shared/long-lived agent is safe to reuse: this case
  needs a specific, deliberately-ordered set of version creation timestamps (see Test Data), and Publish
  has no per-version delete API (only whole-agent delete, same constraint as ELITEA-1892).

## Test Data

### generate-per-test (created in test setup, deleted in teardown)
A uniquely-named disposable agent, created via `AgentAPI.create_agent_full()` with `reasoning_effort:
"none"` (avoids the open #524 defect, same pattern as ELITEA-1888/1892's tests), **and** with a Tag set +
substantive Instructions from creation (see Automation Hints — Test-data generation) so the Publish
AI-validation gate passes on the first attempt without the two throwaway `422` round-trips ELITEA-1892's
manual run needed.

The test then builds exactly this version sequence, **in this order**, to exercise every ordering rule
in one pass:

| Order created | Version name | How | Status | Purpose |
|---|---|---|---|---|
| 1 (agent creation) | `base` | `create_agent_full()` | Draft | Starting point. **A freshly created agent's `meta.default_version_id` already equals base's own version id** — base is the pinned/default version at this point (see live confirmation below), which the test uses to exercise the "pinned version sorts first, with a pin icon" rule using base itself before re-pinning anything. |
| 2 | `v1-early-draft` | Save As Version, edit Instructions first | Draft | An "older" non-default, non-published version — becomes the version the test re-pins later. |
| 3 | `v2-published` | Publish (from whichever version is active) | Published | Confirms Published does NOT get a special sort tier — only its create timestamp and (later) pin status matter. |
| 4 | `v3-latest-draft` | Save As Version again | Draft | The newest version by creation time — used to prove Draft can legitimately outrank a Published version in sort order (case step 7's literal wording is the thing under test/clarified here). |
| — | (re-pin) | `agent-actions-menu-button` → `set-as-a-default-menuitem` → confirm dialog | — | Moves `v1-early-draft` from "oldest non-default" to "pinned, sorts first" — exercises both halves of step 8 and confirms `base` drops out of the pinned slot and moves to last (step 5's rule, now correctly conditional). |

## Test Steps

1. Navigate to an agent with base + Draft + Published versions (built per Test Data above).
   - **Verify — PASSES.** Agent detail page loads, `VERSION:` combobox shows the currently-active
     version's name.
2. Click the version dropdown in the toolbar (`agent-version-selector-trigger`).
   - **Verify — PASSES.** A `role="listbox"` opens with one `role="option"` per version (4, per the
     Test Data table above).
3. Verify all versions are listed.
   - **Verify — PASSES.** All 4 `version-option-{name}` testids are present:
     `version-option-base`, `version-option-v1-early-draft`, `version-option-v2-published`,
     `version-option-v3-latest-draft`.
4. Verify each entry shows version name and creation date/time.
   - **Verify — PASSES, with a naming nuance.** Each option's own text content is
     `"{name} - {DD.MM.YYYY}"` (e.g. `"v2-published - 01.08.2026"`) — the date is **not** a separate DOM
     node/testid, it's baked into the SAME element's text by `buildVersionOption()`
     (`timeFormatter(created_at, TIME_FORMAT.DDMMYYYY)`) and rendered by `SingleSelectMenuItem`'s
     `renderTextBlock()` as `${option.label}${option.date ? ' - ' + option.date : ''}`. No time-of-day
     component is shown despite the case saying "date/time" — only the date (`DD.MM.YYYY`). This is a
     minor case-text imprecision (not filed separately — same reverse-masking-guard family as the
     ordering clarification below, low-severity enough to fold into this AFS's own note rather than a
     second issue) — automate against the observed `"{name} - {date}"` text pattern, not a literal "time"
     assertion.
5. Verify base version appears last.
   - **Verify — PASSES, but ONLY once `base` is not itself the pinned/default version** (see step 8 and
     the Known Defects/Clarification section — this is the case-text drift this AFS's Test Data
     deliberately sequences around: build the versions with base still pinned first, THEN re-pin
     `v1-early-draft`, THEN assert base-last). Confirmed live: after re-pinning `v1-early-draft`, opening
     the dropdown shows `base` as the LAST (4th) option.
6. Verify Draft named versions appear above base.
   - **Verify — PASSES.** Both `v1-early-draft` and `v3-latest-draft` (Draft) render above
     `version-option-base` in every configuration observed this run.
7. If a Published version exists — verify it appears before Draft versions.
   - **Verify — FAILS AS LITERALLY WORDED; live product behavior is correct and is a case-text
     drift (filed as a CLARIFICATION, see below).** With `v3-latest-draft` created AFTER
     `v2-published`, the observed order (before re-pinning) was: `base` (pinned) →
     `v3-latest-draft` (Draft, newest) → `v2-published` (Published, older) → `v1-early-draft` (Draft,
     oldest non-base). `v3-latest-draft` (Draft) sorts ABOVE `v2-published` (Published) because the
     comparator (`VersionSelect.jsx`'s `versionSelectOptions` sort) has no status tier at all — non-pinned,
     non-base versions sort purely by `created_at` descending, Published and Draft interleaved. **This
     AFS does not assert "Published before Draft"** — it asserts the real rule instead: `[pinned] →
     [everything else, by created_at descending] → [base, unless base is pinned]`.
8. Verify the default/pinned version (if set) appears at the top with a pin icon.
   - **Verify — PASSES, with the same case-text nuance folded into step 5's note: a freshly created
     agent's `base` version already IS the pinned/default version** (`meta.default_version_id` returned
     `base`'s own version id from `GET .../application/prompt_lib/{project}/{agent_id}` immediately after
     creation, before this test does anything) — so "the pinned version at the top with a pin icon" is
     initially `base` itself, not a separate/absent state. After explicitly re-pinning `v1-early-draft`
     via the overflow menu's "Set as a default" → confirm dialog, `v1-early-draft` moved to the FIRST
     dropdown position and rendered a `<svg>` inside its option (confirmed via
     `option.locator('svg').count()`, before/after: `1` → still present, this is the same PinIcon that
     `base` carried when IT was pinned) — **and `base` simultaneously dropped from position 1 to
     position 4 (last)**, live-proving steps 5 and 8 are the SAME rule, not two independent ones.

## EliteaUI testid gaps found this run (need closing before implementation)

Both confirmed **absent live** via `.inner_html()` inspection of the rendered option/dialog (no
`data-testid` on either node, only the surrounding elements' own pre-existing testids):

| testid needed | Element | File | Why required for THIS case |
|---|---|---|---|
| `version-option-pin-icon` | The `<PinIcon />` rendered inside `buildVersionOption()`'s `IconBlock` (`version.helpers.jsx:47`, `if (defaultVersionID === id) return <PinIcon />;`) — inside the SAME element already carrying `version-option-{name}` | `src/[fsd]/entities/version/lib/helpers/version.helpers.jsx` | Step 8 literally requires asserting "a visible pin icon", not just position — position alone (first in DOM order) doesn't distinguish "pinned" from "just happens to sort first". Scope: chain off the ALREADY-testid'd `version-option-{name}` parent (`VERSION_OPTION.format(name)`), e.g. `self.page.locator(self.VERSION_OPTION.format(name)).locator('[data-testid="version-option-pin-icon"]')` — compliant scoped sub-selector, no new page-level handle. |
| — (confirm button) — on `SetDefaultVersionDialog.jsx`'s primary action button (currently plain text-matched `"Set as a default"`, no testid at all — same component, Cancel button also untested but NOT touched by this case) | `src/[fsd]/entities/version/ui/SetDefaultVersionDialog.jsx` | The test must actively re-pin `v1-early-draft` (Test Data table) to exercise step 8's "pinned version that ISN'T base" case — `useSetDefaultVersion.hooks.jsx`'s `handleSetDefaultVersion` opens this confirmation dialog first; without a testid the confirm click has no compliant handle. Suggested name: `agent-set-default-version-confirm-button` (mirrors the existing `agent-publish-confirm-button` / `agent-unpublish-confirm-button` naming already used for this same family of confirm dialogs). |

**Already live, no change needed** (confirmed this run):
- `set-as-a-default-menuitem` — the overflow menu's "Set as a default" item **already carries a testid**
  via the SAME generic `DotMenu.jsx` mechanism as `publish-version-menuitem`/`unpublish-version-menuitem`
  (`testId: item.key` → `data-testid={testId}-menuitem`, `ApplicationControls.jsx`'s
  `key: 'set-as-a-default'`). Confirmed live: present in the DOM, and correctly `aria-disabled="true"`
  when the currently-viewed version IS already the default (matches `disableSetAsDefault`'s logic).
- `version-option-{name}` (dynamic, pre-existing template) — text content already includes the date, no
  separate handle needed for step 4.
- `agent-version-selector-trigger`, `agent-actions-menu-button` — pre-existing.

## Handles Reference

| Element | testid | Confirmed live this run? | Notes |
|---|---|---|---|
| VERSION dropdown trigger | `agent-version-selector-trigger` | yes | pre-existing (ELITEA-1888) |
| Version dropdown option (dynamic) | `version-option-{version_name}` | yes | `AgentDetailPage.VERSION_OPTION` template; text = `"{name} - {DD.MM.YYYY}"` |
| Version dropdown option's pin icon (dynamic, scoped) | `version-option-pin-icon` (chain off `VERSION_OPTION.format(name)`) | **no — testid gap, see above** | needed for step 8 |
| Agent actions overflow (three-dot) menu | `agent-actions-menu-button` | yes | pre-existing |
| Set-as-default menu item | `set-as-a-default-menuitem` | yes (confirmed this run) | pre-existing via `DotMenu` generic mechanism; `aria-disabled="true"` when current version already default |
| Set-default confirm dialog's confirm button | none yet — suggest `agent-set-default-version-confirm-button` | **no — testid gap, see above** | needed to actually re-pin `v1-early-draft` in test setup |
| Publish menu item / wizard fields (to build `v2-published`) | `publish-version-menuitem`, `agent-publish-version-name-input`, `agent-publish-category-select`, `agent-publish-agree-checkbox`, `agent-publish-continue-button`, `agent-publish-confirm-button` | yes | all pre-existing (ELITEA-1892) |
| Save As Version dialog (to build `v1-early-draft`, `v3-latest-draft`) | `agent-save-as-version-button`, `agent-version-dialog-name-input`, `agent-version-dialog-save-button` | yes | pre-existing (ELITEA-1888) |
| Instructions field (to differentiate versions' content, not asserted directly by this case) | `agent-instructions-input` | yes | pre-existing |
| Delete agent menu item / confirm | `delete-agent-menuitem`, `delete-confirm-name-input` (scope to inner `#name`), Delete confirm button (role/name, pre-existing gap) | yes | pre-existing, same scoping gotcha documented in ELITEA-1888/1889/1892 |

## Expected Results
Matches the case's Pass/Fail Criteria **with the ordering rule corrected per the live product** (see
step 7's note and the filed CLARIFICATION): all versions are listed with name+date metadata, Draft
versions above an unpinned base, base last **when base is not itself pinned**, and the pinned/default
version at the top with a pin icon — but there is no independent Published-before-Draft tier; Published
and Draft versions interleave purely by creation date once the pinned slot and the base-last slot are
accounted for.

## Coverage Map

### Axis 1 — Case element → Coverage
| Case element | Expected result | Covered by | Asserted where | Disposition |
|---|---|---|---|---|
| Precondition: agent with base + Draft + Published versions | Agent detail page reachable, versions exist | Test setup (Test Data table) | dedicated disposable agent, 4 versions built in a specific order | covered |
| Step 1: Navigate to the agent | Page loads | Test Step 1 | `AgentDetailPage.navigate(agent_id)` | covered |
| Step 2: Click version dropdown | Dropdown opens | Test Step 2 | `open_version_selector()`, `role="listbox"` visible | covered |
| Step 3: All versions listed | All 4 present | Test Step 3 | all 4 `version-option-{name}` testids visible | covered |
| Step 4: Each entry shows name + date/time | Both present | Test Step 4 | option text `"{name} - {date}"` — **"time" not literally shown, date only; folded as a low-severity note, not a separate filed issue** | covered, with a noted case-text imprecision |
| Step 5: base appears last | base at bottom | Test Step 5 | **conditional on base not being pinned** — asserted AFTER the test's own re-pin step, matching real product behavior | covered, condition documented |
| Step 6: Draft versions above base | both Drafts above base | Test Step 6 | `v1-early-draft`/`v3-latest-draft` both render above `version-option-base` | covered |
| Step 7: Published appears before Draft | — | Test Step 7 | **case text does not match live behavior — CLARIFICATION filed** (EliteaAI/elitea-testing-public#1091); this AFS asserts the real pinned→date-desc→base-last rule instead | disposition: case-text drift, reverse-masking guard applied — NOT a product defect |
| Step 8: pinned version at top with pin icon | pin icon + top position | Test Step 8 | re-pin `v1-early-draft` via `set-as-a-default-menuitem` + confirm dialog; assert position 1 + `version-option-pin-icon` present; assert `base` simultaneously moves to position 4 | covered — **requires 2 new testids, see gaps above** |
| Expected Final State: correct order + metadata | — | Test Steps 3-8 | — | covered, with the corrected ordering rule |

### Axis 2 — Observables asserted beyond the case
| Observable | Reason |
|---|---|
| `meta.default_version_id` (via `AgentAPI.get_agent()`) equals `base`'s own version id immediately after agent creation, before any test interaction | Load-bearing for why step 5's "base last" assertion must be sequenced AFTER the re-pin, not asserted against a freshly-created agent directly — a naive implementation asserting "base last" right after agent creation would fail non-deterministically depending on whether a prior test's pin state leaked (it doesn't, since agents are disposable per-run) but more importantly would be asserting against the WRONG initial condition (base pinned, not unpinned) every single run. |
| `base` drops from position 1 to position 4 in the SAME dropdown-open, immediately after `v1-early-draft` is re-pinned | Proves steps 5 and 8 are one rule (pin-priority always wins, base-last is the fallback when nothing is pinned there), not two independently-implemented behaviors — worth asserting together in one step rather than two separate tests that could each pass while the underlying rule was actually different (e.g. "base is hardcoded position N" would pass a single-snapshot test but fail this differential one). |
| `set-as-a-default-menuitem`'s `aria-disabled` attribute reflects whether the CURRENTLY VIEWED version is already the default | Confirms the menu item's enabled/disabled state is itself a reliable precondition check the implementer can assert before attempting to click it (avoids a flaky "click a disabled item" failure mode). |

## Known Defects / Clarifications Found During Exploration

- **[CLARIFICATION]** ELITEA-1891's steps 5-8 describe a three-tier ordering (Pinned → Published → Draft
  → base) that does not match the live sort algorithm
  (`src/[fsd]/entities/version/ui/VersionSelect.jsx`'s `versionSelectOptions` comparator): the real rule
  is `[pinned] → [everything else by created_at descending, Published/Draft interleaved, no status tier]
  → [base, only if base is not itself pinned]`. Live product behavior is correct (Reverse-masking guard —
  the case text is what's stale/over-specified); does not block automation, this AFS's Test Steps above
  already describe and assert the real rule. Filed:
  [EliteaAI/elitea-testing-public#1091](https://github.com/EliteaAI/elitea-testing-public/issues/1091).
- No product bugs found. The known #611 (Publish-wizard Stepper console warnings) and #614 (version-status
  client-side staleness after Publish) defects, both already filed against ELITEA-1892, were reproduced
  again incidentally while building `v2-published` for this case's Test Data (same Publish flow) — not
  new, not re-filed, not this case's concern (this case doesn't assert anything about Publish/Unpublish
  itself, only about the resulting version's position in the dropdown once it exists).

## Cleanup
- The dedicated disposable agent (all 4 versions: `base`, `v1-early-draft`, `v2-published`,
  `v3-latest-draft`) is deleted in full at teardown via `delete_agent_via_menu()` /
  `agent_api.delete_agent()` — **must `unpublish_version()` the Published clone FIRST** (same constraint
  documented in ELITEA-1892: `delete_agent()` 400s with "Cannot delete application with published or
  embedded versions. Unpublish first." while any version is still Published).
- No other test data was created.

## Blocked Steps
None. All 8 case steps executed and verified live; step 7 required a case-text clarification (filed) but
did not block execution — the live behavior was fully observed and is asserted as-is.

## Automation Hints
- Framework: Playwright + pytest.
- Page object: extend `automation/pages/agent_detail_page.py` with the two new testids once added
  (`version-option-pin-icon` as a scoped sub-selector chained off the existing `VERSION_OPTION` template;
  `agent-set-default-version-confirm-button`, or whatever name the implementer/UI-team settles on, as a
  new `LocatorDescriptor` field), plus a small helper to read the dropdown's option order, e.g.
  `get_version_option_order() -> list[str]` (reads all `[data-testid^="version-option-"]` elements' own
  `data-testid` attribute in DOM order, matching the pattern this AFS's live probes used) — reusable by
  any future version-ordering case.
- Test-data generation: seed the agent's base version with a real Tag + substantive Instructions from
  creation (via the API payload's `tags`/`instructions` fields directly) so the Publish AI-validation
  gate passes on the FIRST `publish_validate` round-trip — this run's live probe did exactly that and hit
  `critical_issues: []` immediately, avoiding ELITEA-1892's manual-run pattern of 2 failed attempts
  (correct product behavior, but unnecessary latency/flakiness risk to build into a fixture on purpose).
- Wait strategy: after Publish, do NOT rely on auto-navigation (issue #614, same as ELITEA-1892) —
  explicitly navigate/select versions by name. After the re-pin confirm click, wait for the confirm
  dialog to close (`wait_for(state="hidden")`) before re-opening the VERSION dropdown to read the new
  order — a toast ("Default version has been set successfully") also fires and can be used as an
  additional settle signal if the implementer wants belt-and-braces.
- Order-reading helper should assert list length == 4 as a sanity check before indexing into it, so a
  future regression that drops a version from the dropdown fails clearly rather than raising an
  off-by-one IndexError.
