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

- **AMENDED 2026-08-27 (implementer, ELITEA-1891 repair / issue #1873)** — EliteaAI/EliteaUI@cf648e9a
  ("Feat/el 6302/enhancement of version select", PR EliteaAI/EliteaUI#857, merged to EliteaUI `main`
  2026-08-27) deliberately **removed the pinned-first sort tier** and **enriched the option metadata**.
  Everything below marked "AMENDED post-#857" states the SHIPPED truth; the original wording is kept
  inline (struck through as "pre-#857") only where the contrast is load-bearing. Second CLARIFICATION
  filed: [EliteaAI/elitea-testing-public#1877](https://github.com/EliteaAI/elitea-testing-public/issues/1877),
  sibling of #1091.

  **The current product rule:** `[every version by created_at DESCENDING] → [base ALWAYS last]`.
  No pinned tier, no status tier. The pin **icon** was deliberately kept (`VersionIconBlock.jsx`,
  `data-testid="version-option-pin-icon"` + `aria-label="Default version"`) and is now the SOLE
  indicator of the default version — position and pin are fully **decoupled**, so `base` is
  simultaneously *pinned* and *last*. Live-confirmed order for this AFS's own Test Data sequence,
  both before AND after the re-pin: `['v3-latest-draft', 'v2-published', 'v1-early-draft', 'base']`.

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
| 1 (agent creation) | `base` | `create_agent_full()` | Draft | Starting point. **A freshly created agent's `meta.default_version_id` already equals base's own version id** — base is the pinned/default version at this point (see live confirmation below). **AMENDED post-#857:** this is now used to exercise the *decoupling* — base is pinned AND sorts last, which is a strictly stronger statement than the pre-#857 "pinned version sorts first" it replaced. |
| 2 | `v1-early-draft` | Save As Version, edit Instructions first | Draft | An "older" non-default, non-published version — becomes the version the test re-pins later. |
| 3 | `v2-published` | Publish (from whichever version is active) | Published | Confirms Published does NOT get a special sort tier — only its create timestamp and (later) pin status matter. |
| 4 | `v3-latest-draft` | Save As Version again | Draft | The newest version by creation time — used to prove Draft can legitimately outrank a Published version in sort order (case step 7's literal wording is the thing under test/clarified here). |
| — | (re-pin) | `agent-actions-menu-button` → `set-as-a-default-menuitem` → confirm dialog | — | **AMENDED post-#857:** moves the pin ICON from `base` to `v1-early-draft` **without changing the sort order at all**. Exercises step 8 as: (a) the pin icon migrated onto `v1-early-draft`, (b) it left `base`, (c) the dropdown order is byte-identical to the pre-re-pin read. |

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
   - **AMENDED post-#857 — Verify PASSES, and the case's literal "date/time" wording is now
     SATISFIED.** The pre-#857 note recorded here ("no time component is shown, only `DD.MM.YYYY`;
     automate against `{name} - {date}`") is **OBSOLETE** — #857 replaced the `timeFormatter(...,
     DDMMYYYY)` rendering with `version.helpers.jsx`'s `formatVersionMeta()`, which emits
     `"{Mon DD, YYYY, HH:MM} · by {author}"` — i.e. it ADDED both a time of day and an author.
   - The name and the metadata are now **sibling nodes** inside the same `version-option-{name}`
     element (`VersionSelectOption.jsx` renders a name `Typography` and a meta `Typography`), so the
     element's own `text_content()` concatenates them with **NO separator**. Verified live on
     `localhost:5173` at repair time: `"baseAug 13, 2026, 11:15 · by Test Bot"`.
   - Automate against `^{name}{Mon DD, YYYY, HH:MM} · by {author}$`. The author segment always renders
     (`author_name` → `author_email` → the literal `"Author unavailable"`), so requiring it is safe.
     Assert the author is not the `"Author unavailable"` fallback.
   - **The rendered date AND time are asserted against the API's own `created_at` for that version — the
     response is the oracle** (`.agents/testing.md` § Fidelity policy). Do NOT compare against the test
     machine's clock: `formatVersionMeta()` runs `new Date(created_at)` + local getters **without** the
     codebase's own `convertTime()` `Z`-normalizer (`src/common/convertChatConversationMessages.js:25`,
     which the notification and chat renderers DO call), and the backend sends NAIVE stamps — so there is
     no offset to convert from and the getters return the string's own digits. The dropdown therefore
     shows the **server's** wall clock labelled as local, and any clock-based expectation false-fails by
     `|server UTC − machine local|` (up to ±14 h) while passing on UTC CI runners. Mirror the product's
     arithmetic instead: naive stamp → use verbatim; tz-aware stamp → convert to local first.
     (`test_agent_version_selector_order.py::_expected_created_label` is the worked mirror.) The
     UTC-vs-local inconsistency itself is a real product observation, filed separately by the lead — the
     test mirrors it rather than compensating for it, so the filing stays visible.
5. Verify base version appears last.
   - **AMENDED post-#857 — Verify PASSES UNCONDITIONALLY.** The pre-#857 condition recorded here
     ("only once `base` is not itself the pinned/default version") is **OBSOLETE**: the comparator's
     `LATEST_VERSION_NAME` early return sinks `base` regardless of pin state, and there is no longer a
     pinned tier to compete with it. Confirmed live in BOTH configurations — `base` is the LAST (4th)
     option while it is still the pinned/default version, and still last after the pin moves away.
   - This makes the assertion **stronger** than the pre-#857 one: it is now asserted against a PINNED
     base (the case that used to contradict it), not merely against an unpinned one.
   - ⚠️ **Honest limit of this assertion — it does NOT isolate the `LATEST_VERSION_NAME` early return.**
     With this Test Data, `base` is also the OLDEST version by construction, so plain `created_at DESC`
     would sink it anyway. "base last because the comparator special-cases it" and "base last because it
     happens to be oldest" are **indistinguishable** here. This is not fixable within the case: `base` is
     created with the agent, so it is always the oldest — isolating the special case would need a version
     created with a backdated `created_at`, which no UI or API flow in this case's scope can produce. The
     assertion is still worth making (it is the case's own step 5, and it catches any regression that
     moves `base` off the bottom), but it must not be described as pinning down the base-last RULE. The
     rule's other half — that pin state does not affect position — IS isolated, by the Step 8 differential.
6. Verify Draft named versions appear above base.
   - **Verify — PASSES.** Both `v1-early-draft` and `v3-latest-draft` (Draft) render above
     `version-option-base` in every configuration observed this run.
7. If a Published version exists — verify it appears before Draft versions.
   - **Verify — FAILS AS LITERALLY WORDED; live product behavior is correct and is a case-text
     drift (filed as a CLARIFICATION, see below).** With `v3-latest-draft` created AFTER
     `v2-published`, the observed order (**AMENDED post-#857**, before re-pinning) is:
     `v3-latest-draft` (Draft, newest) → `v2-published` (Published, older) → `v1-early-draft` (Draft,
     oldest non-base) → `base` (pinned, but still last). *Pre-#857 the same read put the pinned `base`
     FIRST; #857 removed that tier.* `v3-latest-draft` (Draft) sorts ABOVE `v2-published` (Published) because the
     comparator (`VersionSelect.jsx`'s `versionSelectOptions` sort) has no status tier at all — non-pinned,
     non-base versions sort purely by `created_at` descending, Published and Draft interleaved. **This
     AFS does not assert "Published before Draft"** — it asserts the real rule instead, **AMENDED
     post-#857**: `[every version by created_at descending] → [base ALWAYS last]`.
8. Verify the default/pinned version (if set) appears at the top with a pin icon.
   - **AMENDED post-#857 — the "at the top" half FAILS AS LITERALLY WORDED; the pin-icon half PASSES.
     Live product behavior is correct; this is case-text drift, filed as CLARIFICATION
     [EliteaAI/elitea-testing-public#1877](https://github.com/EliteaAI/elitea-testing-public/issues/1877)**
     (sibling of #1091 — same case, a second stale ordering tier).
   - A freshly created agent's `base` version already IS the pinned/default version
     (`meta.default_version_id` returned `base`'s own version id from
     `GET .../application/prompt_lib/{project}/{agent_id}` immediately after creation) — but post-#857
     it is nonetheless rendered LAST. **Position and pin are decoupled.**
   - After explicitly re-pinning `v1-early-draft` via the overflow menu's "Set as a default" → confirm
     dialog: the `version-option-pin-icon` node MIGRATES onto `v1-early-draft` and DISAPPEARS from
     `base`, while the dropdown order stays **byte-identical** to the pre-re-pin read
     (`['v3-latest-draft', 'v2-published', 'v1-early-draft', 'base']` both times).
   - **This AFS therefore does not assert "pinned version at the top."** It asserts the two real,
     stronger observables: (a) the pin icon's migration on/off the right options, and (b) that
     re-pinning does **not** reorder the dropdown — a differential assertion across two live reads,
     which the pre-#857 "position 1" assertion could never make.
   - *Pre-#857 (removed by EliteaAI/EliteaUI@cf648e9a):* the re-pin moved `v1-early-draft` to position 1
     and dropped `base` from position 1 to position 4.

## EliteaUI testid gaps found this run (CLOSED — both testids are now on EliteaUI `main`)

> **AMENDED post-#857 (2026-08-27):** both gaps below were closed at original implementation time and
> both testids survived EliteaAI/EliteaUI@cf648e9a. Re-verified by two-ref grep on a freshly fetched
> clone: `version-option-pin-icon` main:YES testids:YES · `agent-set-default-version-confirm-button`
> main:YES testids:YES. **No new testid is needed for the repair.** The section is kept for provenance.

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
| Version dropdown option (dynamic) | `version-option-{version_name}` | on-main ✓ | `AgentDetailPage.VERSION_OPTION` template. **AMENDED post-#857:** text = `"{name}{Mon DD, YYYY, HH:MM} · by {author}"` (name and meta are sibling nodes, concatenated with no separator by `text_content()`) |
| Version dropdown option's pin icon (dynamic, scoped) | `version-option-pin-icon` (chain off `VERSION_OPTION.format(name)`) | on-main ✓ (added for this case; two-ref grep re-verified 2026-08-27) | needed for step 8. **AMENDED post-#857:** #857 MOVED it out of `version.helpers.jsx`'s `buildVersionOption()` into the extracted `VersionIconBlock.jsx` — same testid value, same position inside the option. Note it renders only when the default version is NOT published (a published version shows a publish icon in the same slot) |
| Agent actions overflow (three-dot) menu | `agent-actions-menu-button` | yes | pre-existing |
| Set-as-default menu item | `set-as-a-default-menuitem` | yes (confirmed this run) | pre-existing via `DotMenu` generic mechanism; `aria-disabled="true"` when current version already default |
| Set-default confirm dialog's confirm button | `agent-set-default-version-confirm-button` | on-main ✓ (added for this case; two-ref grep re-verified 2026-08-27, survived #857) | needed to actually re-pin `v1-early-draft` in test setup; wired via `confirmButtonTestId` in `useSetDefaultVersion.hooks.jsx` |
| Publish menu item / wizard fields (to build `v2-published`) | `publish-version-menuitem`, `agent-publish-version-name-input`, `agent-publish-category-select`, `agent-publish-agree-checkbox`, `agent-publish-continue-button`, `agent-publish-confirm-button` | yes | all pre-existing (ELITEA-1892) |
| Save As Version dialog (to build `v1-early-draft`, `v3-latest-draft`) | `agent-save-as-version-button`, `agent-version-dialog-name-input`, `agent-version-dialog-save-button` | yes | pre-existing (ELITEA-1888) |
| Instructions field (to differentiate versions' content, not asserted directly by this case) | `agent-instructions-input` | yes | pre-existing |
| Delete agent menu item / confirm | `delete-agent-menuitem`, `delete-confirm-name-input` (scope to inner `#name`), Delete confirm button (role/name, pre-existing gap) | yes | pre-existing, same scoping gotcha documented in ELITEA-1888/1889/1892 |

## Expected Results
**AMENDED post-#857.** Matches the case's Pass/Fail Criteria **with the ordering rule corrected per the
live product** (see steps 5/7/8 and the two filed CLARIFICATIONs #1091 and #1877): all versions are
listed with name + creation-date + time-of-day + author metadata; the list is sorted purely by
`created_at` DESCENDING with `base` ALWAYS last; and the default version is marked by a pin icon whose
position in the list is **independent** of the sort. There is no Published-before-Draft tier and no
pinned-first tier — the only two rules are "created_at descending" and "base last".

## Coverage Map

### Axis 1 — Case element → Coverage
| Case element | Expected result | Covered by | Asserted where | Disposition |
|---|---|---|---|---|
| Precondition: agent with base + Draft + Published versions | Agent detail page reachable, versions exist | Test setup (Test Data table) | dedicated disposable agent, 4 versions built in a specific order | covered |
| Step 1: Navigate to the agent | Page loads | Test Step 1 | `AgentDetailPage.navigate(agent_id)` | covered |
| Step 2: Click version dropdown | Dropdown opens | Test Step 2 | `open_version_selector()`, `role="listbox"` visible | covered |
| Step 3: All versions listed | All 4 present | Test Step 3 | all 4 `version-option-{name}` testids visible | covered |
| Step 4: Each entry shows name + date/time | Both present | Test Step 4 | **AMENDED post-#857:** option text `"{name}{Mon DD, YYYY, HH:MM} · by {author}"` — the case's literal "date/time" wording is now satisfied (#857 added the time of day AND an author); the pre-#857 "no time component" note is obsolete | covered — case text and product now agree |
| Step 5: base appears last | base at bottom | Test Step 5 | **AMENDED post-#857: UNCONDITIONAL** — asserted twice, once against a PINNED base (precondition step) and once after the pin moved away (Step 5) | covered — strengthened, the pre-#857 condition is gone |
| Step 6: Draft versions above base | both Drafts above base | Test Step 6 | `v1-early-draft`/`v3-latest-draft` both render above `version-option-base` | covered |
| Step 7: Published appears before Draft | — | Test Step 7 | **case text does not match live behavior — CLARIFICATION filed** (EliteaAI/elitea-testing-public#1091); this AFS asserts the real rule instead, **AMENDED post-#857** to `[created_at desc] → [base always last]` | disposition: case-text drift, reverse-masking guard applied — NOT a product defect |
| Step 8: pinned version at top with pin icon | pin icon + top position | Test Step 8 | **AMENDED post-#857 — the "top position" half is case-text drift, CLARIFICATION filed (EliteaAI/elitea-testing-public#1877).** Asserted instead: `version-option-pin-icon` migrates ONTO `v1-early-draft` and OFF `base`, AND the order is unchanged from the pre-re-pin read | pin-icon half covered; ordering half: case-text drift, reverse-masking guard applied — NOT a product defect |
| Expected Final State: correct order + metadata | — | Test Steps 3-8 | — | covered, with the ordering rule corrected twice (#1091, #1877) |

### Axis 2 — Observables asserted beyond the case
| Observable | Reason |
|---|---|
| `meta.default_version_id` (via `AgentAPI.get_agent()`) equals `base`'s own version id immediately after agent creation, before any test interaction | Load-bearing for why step 5's "base last" assertion must be sequenced AFTER the re-pin, not asserted against a freshly-created agent directly — a naive implementation asserting "base last" right after agent creation would fail non-deterministically depending on whether a prior test's pin state leaked (it doesn't, since agents are disposable per-run) but more importantly would be asserting against the WRONG initial condition (base pinned, not unpinned) every single run. |
| **AMENDED post-#857:** the dropdown order is byte-identical before and after `v1-early-draft` is re-pinned (`order == order_before_repin`) | The differential replacement for the pre-#857 "base drops from position 1 to 4" observable, which #857 made impossible. It pins down the *new* contract — re-pinning changes the pin icon and nothing else — using two live reads of the real system. A single-snapshot test could not distinguish "sorted by created_at" from "sorted by created_at, and pinning happens not to have been exercised"; this one can. |
| `set-as-a-default-menuitem`'s `aria-disabled` attribute reflects whether the CURRENTLY VIEWED version is already the default | Confirms the menu item's enabled/disabled state is itself a reliable precondition check the implementer can assert before attempting to click it (avoids a flaky "click a disabled item" failure mode). |

## Known Defects / Clarifications Found During Exploration

- **[CLARIFICATION #1091, 2026-08-xx]** ELITEA-1891's steps 5-8 describe a three-tier ordering
  (Pinned → Published → Draft → base) whose **Published/Draft status tier** does not exist in the live
  sort algorithm (`src/[fsd]/entities/version/ui/VersionSelect.jsx`'s `versionSelectOptions`
  comparator). Live product behavior is correct (reverse-masking guard — the case text is what's
  stale/over-specified); does not block automation. Filed:
  [EliteaAI/elitea-testing-public#1091](https://github.com/EliteaAI/elitea-testing-public/issues/1091).
- **[CLARIFICATION #1877, 2026-08-27 — AMENDED post-#857]** The same case's **pinned-first tier** is
  now stale too. EliteaAI/EliteaUI@cf648e9a (PR EliteaAI/EliteaUI#857, merged to EliteaUI `main`
  2026-08-27) deliberately deleted the two `defaultVersionID` early returns from that comparator,
  leaving the source comment *"Default version stays in its chronological position — not pinned to
  top."* The pin **icon** was deliberately kept (`VersionIconBlock.jsx`, still carrying
  `data-testid="version-option-pin-icon"` and `aria-label="Default version"`) and is now the SOLE
  indicator of the default version. So the case's "appears at the top with a pin icon" is half stale
  (position) and half correct (icon). Live product behavior is correct; reverse-masking guard applies
  exactly as for #1091. Filed:
  [EliteaAI/elitea-testing-public#1877](https://github.com/EliteaAI/elitea-testing-public/issues/1877),
  sibling of #1091.
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
- **AMENDED post-#857 — `version-option-` is no longer a safe bare prefix.** #857's `VersionIconBlock`
  added a hover "set as default" affordance carrying `data-testid="version-option-set-default-{name}"`,
  which a naive `[data-testid^="version-option-"]` order-read would count as an option. The
  `AgentDetailPage.VERSION_OPTION_ANY` constant already excludes it (alongside the nested
  `version-option-pin-icon`); any new consumer must reuse that constant rather than re-deriving the
  prefix selector.
