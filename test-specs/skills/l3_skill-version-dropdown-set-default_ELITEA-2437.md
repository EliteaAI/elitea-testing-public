# Test Case: Version dropdown shows pin/set-as-default button and confirmation message

## Metadata
- **TMS ID**: ELITEA-2437
- **Linked Story**: none
- **Priority**: l3 (case frontmatter/body: `medium`)
- **Environment Explored**: local (`http://localhost:5173`, EliteaUI
  `automation/testids` branch → DEV backend, project `Private` /
  `${ELITEA_PROJECT_ID}`=399)
- **User set**: `${TEST_USER}` (localhost `auth_state` fixture skips login via
  `VITE_DEV_TOKEN`)
- **Analyst**: qa-engineer (Sage), analyst slot
- **Status**: ready-for-automation
- **Case-gate note**: case frontmatter carries `status: draft`,
  `execution_type: manual` — per `.agents/test-automation.yaml` § `intake`,
  `status: draft` is the intake-eligible value, not an exclusion. Proceeded
  to full execution.
- **Distinct feature — do not confuse with ELITEA-2435.** ELITEA-2435
  (`l3_skill-pin-unpin-flow_ELITEA-2435.md`) covers **entity-level list
  pinning** ("Pin to top" — `POST/DELETE .../social/pin/prompt_lib/{project}/
  skill/{id}`, moves the whole skill card to the top of `/skills/all`).
  ELITEA-2437 covers a **completely different feature**: the per-skill
  **VERSION dropdown**'s pin/"set as default" control, which marks one
  *version* of a single skill as its default (`PATCH .../elitea_core/
  skill_default_version/prompt_lib/{project}/{skill_id}`). Same "pin" icon
  visual language, unrelated backend mechanism, unrelated UI surface
  (`SkillTabBar.jsx` + `version.helpers.jsx`, not `SkillControls.jsx` +
  `usePinMenu.hooks.jsx`). No existing merged spec covers version-level
  default-setting — grepped `test-specs/skills/` and
  `automation/tests/ui/skills/` for `default`, `set_default`,
  `handleSetDefaultVersion`; only sibling references are the *agent*-side
  equivalent (out of this case's `skills` module scope) and this case's own
  future implementation.

## Preconditions
- User is logged in to Elitea (on localhost, `auth_state` fixture skips
  login).
- A project is selected/accessible (`Private`, id `399` in this run).
- The Skills section is accessible (`/skills/all`).
- **A skill with at least 2 versions exists** — a fresh skill only has
  `base`; a second version must be created via the existing "Save As
  Version" flow (`SkillDetailPage.save_as_version()`,
  `automation/pages/skill_detail_page.py:446`, already implemented and
  reused by other skill-version cases in this suite) before the version
  dropdown has anything to set-as-default against.

## Test Data

### generate-per-test (created in test setup, cleaned up in teardown)
- Skill: `SkillAPI.create_skill(name="autotest-verdefault-skill-<ts>",
  description="...", instructions="...")` (`automation/api/client.py:1427`).
- Second version: created live via `SkillDetailPage.save_as_version("ver_1")`
  as part of test setup (not a numbered case action — mirrors how ELITEA-2435
  seeds its two skills in Test Data, not as case steps). Version name must
  satisfy the "Create version" dialog's Name-field constraints (confirmed
  live this run accepts a plain lowercase-hyphen name, e.g. `ver-1` /
  `elitea-2437-ver1`).
- `SkillAPI.create_skill()` / `SkillAPI.delete_skill()`
  (`automation/api/client.py:1427,1460`) reused directly for setup/teardown.
- No shared/reused fixture applies — default-version state is a per-record
  mutation; reusing a shared skill across parallel/retried runs risks state
  bleed for tests asserting default-version display.

## Test Steps

1. Navigate to the Skills list (`${BASE_URL}/skills/all`), open the seeded
   skill (2 versions: `base` + `ver_1`, `base` implicit-default since no
   explicit default has been set yet).
   - **Verify**: skill detail page loads
     (`SkillDetailPage.wait_for_page_load()`), URL pattern
     `/skills/all/{skillId}/{versionId}` (or `/skills/all/{skillId}` if the
     newly-created version auto-navigated back to base — confirmed live this
     run: creating a version navigates the URL to the **new** version's id,
     e.g. `/skills/all/1287/1332`).

2. Open the VERSION dropdown
   (`page.get_by_test_id("skill-version-select")` /
   `SkillDetailPage.version_selector` — **confirmed live, existing testid**,
   already wired via the ELITEA-1738 rework; the concrete clickable
   `role=combobox` node inside it resolves as
   `[data-testid="skill-version-select-combobox"]` — confirmed live this
   run by direct click).
   - **Verify**: dropdown opens; both versions listed
     (`option "base - 06.08.2026"`, `option "ver_1 - 06.08.2026"` pattern
     confirmed live), each with its own `version-option-{name}` testid
     row — **confirmed live, existing dynamic testid** (page object
     `VERSION_OPTION` template, `automation/pages/skill_detail_page.py:122`).

3. Verify each version row shows a pin/set-as-default control.
   - **Verify** (two distinct behaviours, confirmed live, split by whether
     the row IS or ISN'T the current default):
     (a) the **default** version's row (initially `base`, the implicit
     default per `SkillTabBar.jsx`'s `effectiveDefaultId` fallback) shows a
     **static, always-visible** pin icon —
     `data-testid="version-option-pin-icon"` (**confirmed live, existing
     testid**, `version.helpers.jsx`: `if (defaultVersionID === id) return
     <PinIcon data-testid="version-option-pin-icon" />` — unconditional, no
     hover gating);
     (b) a **non-default, non-published** version's row (`ver_1`) shows a
     **hover-revealed** pin/"set as default" icon-button — **CONFIRMED LIVE
     GAP: no `data-testid` on this element.** Source:
     `../EliteaUI/src/[fsd]/entities/version/lib/helpers/version.helpers.jsx`
     — the clickable `<Box id="show-on-hover" onClick={() =>
     handleSetDefaultVersion(id)}><PinIcon /></Box>` carries no
     `data-testid` at all (only a non-unique CSS `id="show-on-hover"` used
     purely for the parent-hover-reveal styling — not a locator-policy-
     compliant handle). Confirmed by driving it live anyway (via a
     temporarily-scoped raw selector, exploration-only) — hovering the
     `ver_1` row and clicking this element correctly opened the "Set as
     default?" dialog. See Concrete Handles for the required fix.

4. Click the pin/set-as-default control on the named non-default version
   (`ver_1`).
   - **Verify**: the "Set as default?" confirmation dialog opens
     (`BaseModal` via `SetDefaultVersionDialog.jsx`) — confirmed live,
     `heading "Set as default?"`, body text `Once set as default, ver_1 will
     be automatically used whenever this skill is added to new or existing
     agents, pipelines, or conversations.`, `Cancel` / `Set as a default`
     buttons. **CONFIRMED LIVE GAP: the "Set as a default" confirm button
     carries no `data-testid`** — `SetDefaultVersionDialog.jsx` accepts an
     optional `confirmButtonTestId` prop and forwards it to the button, but
     `EditSkill.jsx`'s call site (`src/[fsd]/pages/skills/EditSkill.jsx:271`)
     never passes it (unlike the parallel **Agent** flow,
     `useSetDefaultVersion.hooks.jsx:104`, which sets
     `confirmButtonTestId="agent-set-default-version-confirm-button"`). See
     Concrete Handles for the required fix.

5. Confirm the dialog ("Set as a default").
   - **Verify**: `PATCH /api/v2/elitea_core/skill_default_version/
     prompt_lib/{project_id}/{skill_id}` fires and returns **200 OK**
     (confirmed live via `browser_network_requests`:
     `PATCH http://localhost:5173/api/v2/elitea_core/skill_default_version/
     prompt_lib/399/1287 => [200] OK`). Dialog closes.

6. Verify a confirmation message or indicator is shown.
   - **Verify** (confirmed live, two independent signals — either is
     sufficient per the case's "message **or** indicator" wording, both
     asserted for a stronger spec):
     (a) **toast message** — reuses the app-wide toast component, existing
     testid `toast-message` (`SkillDetailPage.version_toast_message`,
     already in the page object). Exact text confirmed live: **"Default
     version has been set successfully"**.
     (b) **persistent indicator** — re-opening the VERSION dropdown shows
     `ver_1` now carrying `version-option-pin-icon` (moved from `base`) and
     sorted to the **top** of the option list (confirmed live —
     `buildVersionOption`'s consumers all sort `defaultVersionID` first);
     the collapsed trigger's summary label also gained a small pin glyph
     next to `ver_1` (confirmed live via screenshot; this glyph is rendered
     by `SkillTabBar.jsx`'s own `renderVersionValue` callback with **no
     testid** — out of scope for this case since the toast + list-level
     `version-option-pin-icon` already satisfy the case's pass criterion;
     not requested as a gap here per the "only what this test touches"
     scoping rule).

**Side-channel check:** zero console errors observed across the full
open-dropdown → click-set-default → confirm-dialog → toast flow (confirmed
via `browser_console_messages`, filtered to errors).

## Expected Results
Matches the case's Pass criteria exactly, live-verified end-to-end: the
VERSION dropdown shows a pin/set-as-default control per row (static for the
current default, hover-revealed for eligible non-default rows), clicking it
opens a confirmation dialog, confirming fires the
`skill_default_version` PATCH and returns 200, and a confirmation toast +
persistent pin-icon/reorder indicator are both shown. No functional product
defect found — the flow behaves per the case's expectation. Two **testid
gaps** (not defects) were found and must be closed by the implementer via
`add-data-testid` before this case can ship testid-only (see Concrete
Handles).

## Coverage Map

### Axis 1 — Case coverage

| Case element | Expected result | Covered by (AFS step) | Asserted where | Disposition |
|---|---|---|---|---|
| Precondition: user logged in | — | AFS Preconditions | `auth_state` fixture | asserted |
| Precondition: skill with multiple versions | — | AFS Preconditions + Test Data | seeded skill + `save_as_version("ver_1")` | asserted |
| 1 Open a Skill with multiple versions | page/section loads | step 1 | step 1: detail page loads, URL pattern | asserted |
| 2 Open the version selector dropdown | page/section loads | step 2 | step 2: `skill-version-select` opens, both versions listed | asserted |
| 3 Verify each version row shows a pin/set-as-default control | condition holds | step 3 | step 3a (default row — static `version-option-pin-icon`) + step 3b (non-default row — hover-revealed control, **testid gap flagged**) | asserted *(decomposed — the case's single expected result implies two distinct per-row behaviours the analysis found and split out)* |
| 4 Click pin/set-as-default on a named version | control responds; next state shown | step 4 | step 4: "Set as default?" dialog opens (**testid gap on confirm button flagged**) | asserted |
| 5 Verify a confirmation message or indicator is shown | condition holds | steps 5–6 | step 5: `PATCH .../skill_default_version/...` 200 OK; step 6a: toast text; step 6b: `version-option-pin-icon` moved + list reorder | asserted |
| Expected Final State: confirmation message or indicator shown | — | step 6 | toast + persistent indicator, both confirmed live | asserted |

### Axis 2 — Analyst additions

- step 1 documents the exact URL-segment behavior after "Save As Version"
  (new version id appended) — *added: implementer needs this to know which
  version is "current" right after setup, since it isn't necessarily
  `base`.*
- step 5 documents the underlying `PATCH .../skill_default_version/
  prompt_lib/{project}/{skill_id}` network call and its 200 status —
  *added: gives the implementer a wait-on-response hook instead of a fixed
  sleep, same reasoning as the `save_as_version()` method's existing
  `POST` wait pattern.*
- step 6b (list-reorder + `version-option-pin-icon` relocation) — *added: a
  second, independent, data-level confirmation beyond the toast, so the
  implementer's test isn't solely dependent on toast timing/text for the
  case's pass criterion.*
- "zero console errors across the flow" — *added: side-channel check per
  this skill's standard discipline; not itself a case requirement.*
- Metadata note distinguishing this case from ELITEA-2435 — *added: same
  "pin" terminology, adjacent UI surface, genuinely different feature and
  backend endpoint; flagged explicitly so a future reader (or a dedup pass)
  doesn't collapse the two.*

## Cleanup
1. Delete the skill created in Test Data via `SkillAPI.delete_skill(skill_id)`
   in test teardown (regardless of pass/fail) — this also removes the
   second version and any default-version state, no separate cleanup call
   needed (`skill_default_version` is a field on the skill's `meta`, not a
   standalone record).
2. **This run's exploration used a stale, orphaned pre-existing skill**
   (`elitea-1889-versioned-skill`, id `1287`, leftover from an incomplete
   `test_agent_save_as_version_preserves_skills.py` run whose `finally:
   skill_api.delete_skill(...)` apparently didn't fire) instead of a
   freshly API-seeded one, since it was found already carrying only a
   `base` version and was faster to reuse for exploration. A second version
   (`elitea-2437-ver1`) was created on it and set as default during this
   analysis. **Fully cleaned up before this run ended**: the whole skill
   (both versions) was deleted via the UI's "Delete skill" flow
   (type-to-confirm dialog), removing all state this run introduced. The
   implementer's actual automated test should use the seeded
   `SkillAPI.create_skill()` + `save_as_version()` pattern above (own data,
   own cleanup), not a pre-existing skill.
3. **Orphaned-fixture note (informational, not filed as a defect):** the
   pre-existing `elitea-1889-versioned-skill` (id 1287) found live suggests
   `test_agent_save_as_version_preserves_skills.py`'s `finally` cleanup
   didn't run to completion on some prior run (interrupted process, failed
   assertion before the `finally` block, etc.) — worth a glance if that
   test shows flakiness, but out of scope to investigate further here since
   this case's own cleanup fully resolved it.

## Concrete Handles (discovered during exploration)

| Element | Recommended Locator | Fallback |
|---|---|---|
| VERSION dropdown trigger (`SkillTabBar.jsx`) | `page.get_by_test_id("skill-version-select")` — **confirmed live, existing testid**, already `SkillDetailPage.version_selector` | n/a — testid already present |
| Version option row, keyed by name (`buildVersionOption()`, shared by skill/agent/pipeline consumers, `version.helpers.jsx`) | `page.locator('[data-testid="version-option-{}"]'.format(name))` — **confirmed live, existing dynamic testid**, already `SkillDetailPage.VERSION_OPTION` | n/a — testid already present |
| Default-version indicator icon on the current-default row (`version.helpers.jsx`, unconditional when `defaultVersionID === id`) | `page.get_by_test_id("version-option-pin-icon")` — **confirmed live, existing testid** (fixed literal, only one instance rendered at a time since only one version can be default) | n/a — testid already present |
| **Set-as-default hover control on a non-default, non-published version's row** (`version.helpers.jsx`'s `<Box id="show-on-hover" onClick={... handleSetDefaultVersion(id)}><PinIcon /></Box>`) | **TESTID NEEDED — confirmed live gap.** No `data-testid` at all; only a non-unique `id="show-on-hover"` (CSS-only, used for the parent-hover `display` toggle, not a valid locator-policy handle). **Fix**: add a name-keyed dynamic testid to this Box, mirroring the sibling `version-option-{name}` convention already established in the same function — e.g. `data-testid={`version-option-set-default-${name}`}`. Route through `add-data-testid` on `../EliteaUI/src/[fsd]/entities/version/lib/helpers/version.helpers.jsx` (shared by skill/agent/pipeline version selects — adding the testid here benefits all three, but per this project's scope discipline only the skill-version-dropdown code path this case exercises is "touched"; do not blanket-verify the other consumers as part of this case). New page-object class constant on `SkillDetailPage`: `VERSION_OPTION_SET_DEFAULT = '[data-testid="version-option-set-default-{}"]'`. | none — per this project's testid-only locator policy, do not ship using the raw `#show-on-hover` id or a positional/hover-based fallback; land the testid fix first. |
| **"Set as a default" confirm button in the "Set as default?" dialog, Skill flow** (`SetDefaultVersionDialog.jsx` via `EditSkill.jsx:271`) | **TESTID NEEDED — confirmed live gap.** `SetDefaultVersionDialog` already accepts an optional `confirmButtonTestId` prop (forwarded straight to the button, `SetDefaultVersionDialog.jsx:64`) and the **Agent** flow already wires it (`useSetDefaultVersion.hooks.jsx:104`, `confirmButtonTestId="agent-set-default-version-confirm-button"`) — but `EditSkill.jsx`'s `<SetDefaultVersionDialog ...>` call site (line 271) never passes the prop. **Fix (one-line)**: add `confirmButtonTestId="skill-set-default-version-confirm-button"` to that call site, mirroring the Agent naming convention. New page-object descriptor: `set_default_version_confirm_button = LocatorDescriptor(testid="skill-set-default-version-confirm-button")`. | none — per this project's testid-only locator policy, do not ship using `get_by_role("button", { name: "Set as a default" })`; land the testid fix first. |
| Confirmation toast (app-wide `Toast` component, reused across skill-version flows) | `page.get_by_test_id("toast-message")` — **confirmed live, existing testid**, already `SkillDetailPage.version_toast_message` | n/a — testid already present |

**Summary for the implementer / `add-data-testid`:** two testid gaps found
this run, both in `../EliteaUI/src/[fsd]/entities/version/`:
1. `version.helpers.jsx` — the hover-revealed "set as default" icon-button
   per version-dropdown row needs a name-keyed dynamic testid (no fix
   landed yet for any consumer — skill, agent, or pipeline).
2. `EditSkill.jsx:271` — the Skill flow's `SetDefaultVersionDialog` call
   site needs to wire the already-existing `confirmButtonTestId` prop (the
   Agent flow already does this at `useSetDefaultVersion.hooks.jsx:104` —
   pure precedent to copy).

## Network Behavior
- `PATCH /api/v2/elitea_core/skill_default_version/prompt_lib/{project_id}/
  {skill_id}` — fires on confirming "Set as a default", returns `200 OK`.
  Body not independently inspected beyond status code this run.
- `POST /api/v2/elitea_core/skills/prompt_lib/{project_id}` (create,
  Test Data setup) / `DELETE .../skill/prompt_lib/{project_id}/{id}`
  (cleanup) — both via `SkillAPI`, not asserted as part of this case.
- Version creation ("Save As Version", test setup) —
  documented in `test-specs/skills/_surface.md` § Build with AI /
  `save_as_version()`'s own docstring; not re-documented here.

## Known Defects / Observations Found During Exploration

No functional product defect was found. The set-default-version flow works
correctly end-to-end: dialog opens, PATCH fires and returns 200, toast
shows the exact expected text, the default indicator and dropdown sort
order both update correctly and persist across a dropdown re-open. Two
**testid gaps** (informational, implementer work — not filed as bugs, per
`.agents/role-overrides.md` § Analyst slot: "Do not soften a testid demand
into a MINOR defect or a note; it is implementer work") are documented
above in Concrete Handles.

## Blocked Steps
None. All 5 case steps (plus the version-dropdown's two distinct per-row
behaviours in step 3) were executed end-to-end live against the real DEV
backend, including creating a second version, opening the dropdown,
clicking the (currently testid-less) set-default control, confirming the
dialog, and verifying both the toast and the persistent indicator —
followed by full cleanup.

## Automation Hints
- Framework: Playwright + pytest, per `.agents/testing.md`. Likely home:
  `automation/tests/ui/skills/test_skill_version_set_default.py` (new
  file — grep of `automation/tests/ui/skills/` found no existing test
  exercising the version-dropdown's set-default control; the file that
  DOES touch a version selector, `test_skill_agent_version_selector.py`,
  covers ELITEA-1789's *agent-attach* version selector, a different
  component with no pin/set-default control at all).
- **Land both testid gaps via `add-data-testid` BEFORE implementing** — per
  this project's testid-only locator policy (`.agents/testing.md` §
  Locator policy, `.agents/role-overrides.md`). Do not ship using the
  `#show-on-hover` raw id or the confirm button's accessible-name fallback.
- `SkillAPI.create_skill()` / `SkillAPI.delete_skill()`
  (`automation/api/client.py:1427,1460`) already exist — reuse for
  setup/teardown, same pattern as ELITEA-2435 and other API-seeded skill
  cases in this suite.
- `SkillDetailPage.save_as_version(version_name)`
  (`automation/pages/skill_detail_page.py:446`) already exists and is the
  correct way to create the second version in test setup — reuse directly,
  no new "create version" logic needed.
- New page-object surface needed on `SkillDetailPage`:
  - `VERSION_OPTION_SET_DEFAULT` dynamic-testid template constant (once the
    testid gap lands), mirroring the existing `VERSION_OPTION` pattern.
  - `version_option_pin_icon` `LocatorDescriptor` (testid
    `version-option-pin-icon`, already present in the DOM — just not yet
    exposed as a page-object field).
  - `set_default_version_confirm_button` `LocatorDescriptor` (testid
    `skill-set-default-version-confirm-button`, once the second testid gap
    lands).
  - An action method, e.g. `set_version_as_default(version_name, timeout=...)`
    mirroring `save_as_version()`'s shape: open the VERSION dropdown, hover
    + click the named version's set-default control, wait for the "Set as
    default?" dialog, click confirm, wait on the `PATCH
    .../skill_default_version/...` response and the `toast-message` text.
- Wait strategy: wait on the `PATCH .../skill_default_version/...` network
  response (`page.wait_for_response`) rather than a fixed sleep before
  asserting the toast/indicator — mirrors `save_as_version()`'s existing
  `POST`-wait pattern for the sibling "create version" toast.
- Assertion for "moved to top of the dropdown list" / "pin icon relocated":
  re-open the VERSION dropdown after confirming and assert
  `version-option-pin-icon` now resolves inside the row for the
  newly-set-default version's `version-option-{name}` container (scoped
  child lookup), not a separate free-floating locator.
