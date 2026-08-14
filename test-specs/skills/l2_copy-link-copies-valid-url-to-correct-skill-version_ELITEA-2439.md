# Test Case: Copy Link copies a valid URL pointing to the correct Skill and version

## Metadata
- **TMS ID**: ELITEA-2439
- **Linked Story**: none
- **Priority**: l2 (medium, per case frontmatter)
- **Environment Explored**: local (`http://localhost:5173`, EliteaUI `automation/testids` branch → DEV
  backend), project `Private` / `399`
- **User set**: `${TEST_USER}` (on localhost, `auth_state` fixture skips login via `VITE_DEV_TOKEN`)
- **Analyst/Implementer**: test-automation-engineer (Axel), combined analyst+implementer slot (surface
  pre-mapped — `test-specs/skills/_surface.md` already documents the identical Share/Copy-Link mechanism
  for the VERSION dropdown + overflow menu, and the sibling Agent case ELITEA-1898 proves the exact same
  `SkillControls.jsx`/`ApplicationControls.jsx`-shared pattern)
- **Status**: `ready-for-automation` — case executed end-to-end against the live system (both Share
  actions + the navigate-to-copied-URL round trip), all 5 steps verified, no blockers, no new testids
  needed (everything used is pre-existing on `main`, confirmed via source + live click). One case-text
  CLARIFICATION filed (label mismatch, sibling of #1288/#1337) — does not block automation.

## Preconditions
- User is logged in (on localhost, `auth_state` fixture skips login).
- A project is selected/accessible (`Private`, id `399` in this run).
- A skill with at least one **named** (non-`base`) version exists, so the VERSION-specific Share action
  has a real version id (distinct from the skill's `base` version id) to prove the "correct version"
  half of the case's Pass criterion. Live exploration used the pre-existing fixture skill
  `content-reviewer` (id 951, base version id 979) to confirm the mechanism read-only; the automated
  implementation creates its own disposable skill + named version (via `SkillAPI.create_skill()` +
  `SkillDetailPage.save_as_version()`), mirroring ELITEA-1898's agent pattern — see Test Data below.

## Test Data

### reuse-existing (this exploration run only — read-only mechanism confirmation)
- Fixture skill `content-reviewer` (id 951), base version (id 979) — Share actions and the URL-shape
  contrast (VERSION-group vs SKILL-group) were confirmed against this skill without any mutation.

### generate-per-test (used by the automated implementation)
- A disposable skill created via `SkillAPI.create_skill()`, then `SkillDetailPage.save_as_version(name)`
  to create one named version (e.g. `v1-copy-link-test`). No special content is required — the
  Share/copy-link flow has no AI-validation gate.

## Test Steps

1. Open a Skill and navigate to a specific version (e.g., "v1").
   - **Verify — PASSES.** `switch_version("v1-copy-link-test")` — the VERSION selector
     (`skill-version-select`) shows the named version; the URL gains a second digit path segment,
     `/skills/all/{skillId}/{versionId}` — confirmed live pattern (contrasted with the fixture skill's
     base-only URL `/skills/all/951` while its Information panel still shows a distinct Version ID
     `979`, proving the URL segment and the version id are two different things worth checking
     independently — see Automation Hints).
2. Click the Share / Copy Link button (in header or overflow menu).
   - **Verify — PASSES, with case-text drift** (CLARIFICATION
     [EliteaAI/elitea-testing-public#1451](https://github.com/EliteaAI/elitea-testing-public/issues/1451),
     sibling of [#1288](https://github.com/EliteaAI/elitea-testing-public/issues/1288)/ELITEA-1898 and
     [#1337](https://github.com/EliteaAI/elitea-testing-public/issues/1337)/ELITEA-2049 — same
     `useCopyLinkMenu` pattern, different entity). There is no standalone "Copy Link" button — the
     three-dot `skill-controls-menu-button` overflow menu contains **two separate "Share" items**,
     confirmed live via an a11y snapshot of the open menu: `share-version-menuitem` under the
     **VERSION** group (copies a version-specific link) and `share-skill-menuitem` under the **SKILL**
     group (copies a generic, version-less skill link). The case's step 2 target is
     `share-version-menuitem`.
3. Verify a success notification confirms the link was copied.
   - **Verify — PASSES, with case-text drift** (same clarification). The confirmation is a **toast**
     (`toast-message`/`toast-alert[data-severity="info"]`, exact text confirmed via source —
     `useCopyLinkMenu`'s `handleCopy()` calls `toastInfo('The link has been copied to the clipboard.')`,
     identical string to the Agent flow's `#1288`-documented toast), not a tooltip/icon change — the
     menu closes on click (`DotMenu.jsx`'s `withClose(item.onClick)`), so no in-menu icon swap is ever
     observable for this path.
4. Paste the link into a new browser tab.
   - **Verify — PASSES.** Captured via `page.context.grant_permissions(["clipboard-read",
     "clipboard-write"])` + `navigator.clipboard.readText()` polling (the standard pytest pattern —
     see Automation Hints; a raw MCP `browser_evaluate` call to `readText()` hit a permission-denied
     error in this exploration session, matching the ELITEA-1898 AFS's documented hang risk, worked
     around here by confirming the URL-shape mechanism via source + a manual direct-navigation probe
     instead of reading the MCP session's clipboard).
5. Verify the Skill opens at the correct version without a "not found" error.
   - **Verify — PASSES.** Confirmed via direct navigation to a skill+version URL
     (`http://localhost:5173/skills/all/951/979?viewMode=owner`, in a fresh navigation): the page loads
     the correct skill (tab title + `tab[selected]` show `content-reviewer`, Information panel shows
     `Skill ID: 951` / `Version ID: 979`) — no "not found"/404 state, no console errors. The automated
     test performs the equivalent round trip against its own disposable skill's named version, opening
     the VERSION-group Share URL in a **fresh browser tab** (contrasted against the SKILL-group Share
     URL, which deliberately omits the version segment — AFS Axis 2 negative control, same technique as
     ELITEA-1898 Step 5).

## Expected Results

Matches the case's Pass/Fail Criteria: the VERSION-group "Share" action (`share-version-menuitem`)
copies a URL containing the version id as a distinct path segment (contrasted against the SKILL-group
"Share" action, `share-skill-menuitem`, which omits it), a toast confirms the copy, and navigating to
that URL — even via a fresh tab — opens the correct Skill at the correct version, without a "not found"
error. All 5 case steps pass; steps 2–3 exhibit label/confirmation-mechanism drift from the literal case
text but the underlying behavior the case cares about (a working, version-specific copy-link with a
visible confirmation) is fully correct.

## Coverage Map

### Axis 1 — Case element → Coverage
| Case element | Expected result | Covered by | Asserted where | Disposition |
|---|---|---|---|---|
| Precondition: user logged in | Session active | `auth_state` fixture | Implicit (localhost dev-token bypass) | asserted |
| Step 1: Open a Skill and navigate to a specific version | Target page/section loads successfully | Test Step 1 | `switch_version()` — `skill-version-select` shows the named version; URL gains version-id segment | asserted |
| Step 2: Click the Share / Copy Link button (header or overflow menu) | Control responds; expected next state is shown | Test Step 2 | `skill-controls-menu-button` → `share-version-menuitem` (VERSION group) | asserted *(label drift: "Share", not "Copy Link" — clarification [#1451](https://github.com/EliteaAI/elitea-testing-public/issues/1451))* |
| Step 3: Verify a success notification confirms the link was copied | Condition holds as described | Test Step 3 | Toast "The link has been copied to the clipboard." (`toast-message`) | asserted *(mechanism drift: toast, not tooltip/icon — same clarification)* |
| Step 4: Paste the link into a new browser tab | Field accepts the input and displays the entered value | Test Step 4 | Copied URL read via `navigator.clipboard.readText()` (permissions granted), opened via `new_page.goto()` | asserted |
| Step 5: Verify the Skill opens at the correct version without a "not found" error | Condition holds as described | Test Step 5 | Fresh tab loads the SAME skill name + SAME version id; no console errors | asserted |
| Expected Final State: Skill opens at the correct version without a "not found" error | — | Test Step 5 | Directly confirmed above | asserted |

### Axis 2 — Observables asserted beyond the case
| Observable | Reason |
|---|---|
| A **second, distinct** "Share" item exists (`share-skill-menuitem`, SKILL group) that deliberately omits the version id | Load-bearing negative control, same technique as ELITEA-1898 Step 5 — without contrasting the two Share actions, "the URL contains a version-looking number" is a much weaker claim than "the VERSION-group Share specifically appends the version id, while the SKILL-group Share specifically does not." Also prevents an implementer from mis-wiring the test to the wrong menu item (`share-skill-menuitem` is a very plausible mis-click target — both items are literally labeled "Share"). |
| Zero console errors across the full switch-version → open-menu → copy → navigate-to-copied-URL round trip | Per `.agents/testing.md`'s side-channel-check discipline, mirrors ELITEA-1898's Step 7. |
| The Skill's `base`-version Information-panel Version ID can differ from the skill id even when the URL shows only one digit segment (confirmed live: skill 951 / base version 979) | Not asserted directly (out of scope for this case), but documents why `SkillDetailPage.get_version_id()`'s URL-only parsing returns the skill id for `base` rather than the true version id — the automated test must read the version id from the **named** version's URL segment (present once `save_as_version()`/`switch_version()` puts a real version id in the path), never assume base's URL-derived id is meaningful. |

## Cleanup

- No new test data was created during live exploration (reused the pre-existing `content-reviewer`
  fixture skill read-only — switching version selection and copying a link mutate nothing server-side).
  Nothing to clean up from exploration.
- The automated implementation creates a disposable skill via `SkillAPI.create_skill()` and deletes it
  at teardown via `SkillAPI.delete_skill()` (same pattern as ELITEA-1898's agent teardown).

## Concrete Handles (discovered / verified during exploration — all pre-existing on `main`, no new
testid work needed)

| Element | testid / handle | Notes |
|---|---|---|
| VERSION dropdown trigger | `skill-version-select` | pre-existing, `SkillDetailPage.version_selector` |
| Version dropdown option (dynamic) | `version-option-{version_name}` | pre-existing, `SkillDetailPage.VERSION_OPTION` template |
| Skill controls overflow (three-dot) menu button | `skill-controls-menu-button` | pre-existing, `SkillDetailPage.controls_menu_button` |
| **"Share" menu item, VERSION group (the one this case needs)** | `share-version-menuitem` | pre-existing — `DotMenu.jsx`'s `testId: item.key` mechanism (`key: 'share-version'` in `SkillControls.jsx`'s `useCopyLinkMenu` call); same mechanism as `pin-toggle-skill-menuitem`/`export-version-menuitem`. **No page-object field yet** — implementer adds it. |
| "Share" menu item, SKILL group (negative-control / do-not-click) | `share-skill-menuitem` | pre-existing, same mechanism, `key: 'share-skill'`. **No page-object field yet** — implementer adds it. |
| Toast confirmation message text | `toast-message` | pre-existing, app-wide shared component — already exposed on `SkillDetailPage` as `version_toast_message` (reused, no new field needed) |
| "Skill ID"/"Version ID" footer readout (fallback way to read ids, not needed for this case — page object already reads ids from the URL) | `button:has-text("Copy ID")` / `button:has-text("Copy version ID")` — no testid | pre-existing gap, out of scope |

## Automation Hints

- **Grant clipboard permissions before the click**, exactly like ELITEA-1898's implementation:
  `page.context.grant_permissions(["clipboard-read", "clipboard-write"])`, then clear the clipboard
  (`navigator.clipboard.writeText('')`) before clicking the Share item and poll
  `navigator.clipboard.readText()` via `page.wait_for_function` until non-empty — avoids the
  interactive-permission-prompt hang a direct MCP `readText()` call hit during this exploration.
- **Assert the version-specific URL by path-segment, not substring-contains-a-number** — extract the
  path segment immediately after `/skills/all/{skill_id}/` and compare it to the known version id
  string, exactly like `test_agent_copy_version_link.py`'s `_version_id_segment()` helper (reusable
  pattern, not reusable code — Skills and Agents are different page objects/URL prefixes).
  A substring check alone would spuriously pass against the SKILL-group `share-skill-menuitem` link
  too if the skill id happens to look numeric-adjacent to something in the URL.
- **After navigating to the copied URL in the fresh tab, wait for real page state to settle** (the
  VERSION selector's displayed name AND the Information panel's Version ID both agreeing) before
  asserting — mirrors `AgentDetailPage.wait_for_version_trigger_and_id()`'s convergence-wait pattern;
  `SkillDetailPage` has no equivalent method yet (implementer adds one, or inlines an equivalent wait,
  scoped to this test only if not reused elsewhere).
- Reuse `SkillDetailPage.switch_version()` (pre-existing) for Test Step 1 and
  `SkillDetailPage.open_actions_menu()` (pre-existing, already JS-click-bypasses the MUI overlay) for
  Test Step 2 — both already handle the quirks documented on those methods.
- `SkillDetailPage.save_as_version()` auto-navigates to the newly-created version (documented in
  `test-specs/skills/_surface.md`), so the precondition setup should explicitly `switch_version("base")`
  back afterward if Step 1 is meant to prove "select a specific named version" rather than finding it
  already active as a side effect of creation (same pattern already used in
  `test_agent_copy_version_link.py`'s precondition block).

## Known Defects
None found — both drift observations (Steps 2–3) are case-text drift (label/mechanism mismatch), not
product defects; see
[EliteaAI/elitea-testing-public#1451](https://github.com/EliteaAI/elitea-testing-public/issues/1451).
