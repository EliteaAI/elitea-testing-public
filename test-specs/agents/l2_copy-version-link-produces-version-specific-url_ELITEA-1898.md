# Test Case: Copy version link produces a version-specific URL

## Metadata
- **TMS ID**: ELITEA-1898
- **Linked Story**: none
- **Priority**: l2 (medium, per case frontmatter)
- **Environment Explored**: local (`http://localhost:5173`, EliteaUI `automation/testids` branch → DEV
  backend), project `Private` / `399`
- **User set**: `${TEST_USER}` (on localhost, `auth_state` fixture skips login via `VITE_DEV_TOKEN`)
- **Analyst**: qa-engineer (Sage), analyst slot
- **Status**: `ready-for-automation` — case executed end-to-end against the live system (both the copy
  action and the subsequent navigate-to-copied-URL round trip), all 6 steps verified, no blockers, no
  new testids needed (everything used is pre-existing on `main`). One case-text CLARIFICATION filed
  (label mismatch — see below); does not block automation.

## Preconditions
- User is logged in (on localhost, `auth_state` fixture skips login).
- A project is selected/accessible (`Private`, id `399` in this run).
- An agent with at least one **named** (non-`base`) version exists. This run reused the pre-existing
  fixture agent `elitea-1889-versioning-agent` (id `7598`, created by the ELITEA-1889 case run), which
  already carries a named version `v1` (id `7820`) alongside its `base` version (id `7819`) — no new
  agent/version needed to be created. A fresh implementation should still create its own disposable
  agent + named version (via `AgentAPI` + `save_as_version()`) rather than depend on this specific
  fixture surviving across runs — see Test Data below.

## Test Data

### reuse-existing (this exploration run only — see note above re: automated-test strategy)
- Fixture agent `elitea-1889-versioning-agent` (id `7598`), named version `v1` (id `7820`).

### generate-per-test (recommended for the automated implementation)
- A disposable agent created via `AgentAPI.create_agent()` (mirrors the pattern in
  `l2_publish-draft-version-status-changes-unpublish-available_ELITEA-1892.md` /
  `lcritical_save-as-version-creates-named-version-visible-in-dropdown_ELITEA-1888.md`), then
  `save_as_version_by_name()`/equivalent to create one named version (any valid name, e.g.
  `v1-copy-link-test`). No special content is required — the Share/copy-link flow has no AI-validation
  gate (unlike Publish).

## Test Steps

1. Navigate to `${BASE_URL}/agents/all/{agent_id}?viewMode=owner`, open the `agent-version-selector-trigger`
   VERSION dropdown, and click `version-option-{version_name}` for the named version.
   - **Verify — PASSES.** `VERSION:` combobox shows the named version (`v1`); the URL updates client-side
     (via `history.replaceState`, no full reload) to
     `/agents/all/{agent_id}/{version_id}?viewMode=owner&name={agent_name}` — confirmed live:
     `/agents/all/7598/7820?viewMode=owner&name=elitea-1889-versioning-agent`.
2. Open the three-dot Agent Actions overflow menu (`agent-actions-menu-button`).
   - **Verify — PASSES, with case-text drift** (see CLARIFICATION issue
     [EliteaAI/elitea-testing-public#1288](https://github.com/EliteaAI/elitea-testing-public/issues/1288)).
     There is no standalone "Copy Link" button — the menu (`agent-actions-menu`) contains **two separate
     "Share" items**: `share-version-menuitem` under the **VERSION** group (copies a version-specific
     link) and `share-agent-menuitem` under the **AGENT** group (copies a generic, version-less agent
     link). The case's step 2 target is `share-version-menuitem`.
3. Click `share-version-menuitem`. Verify a visual confirmation appears.
   - **Verify — PASSES, with case-text drift** (same clarification issue). The confirmation is a
     **toast**, not a tooltip/icon change — the menu closes on click (`DotMenu.jsx`'s
     `withClose(item.onClick)`), so no in-menu icon swap is ever observable for this path. Confirmed
     live: toast text "The link has been copied to the clipboard."
     (`toast-message`/`toast-alert[data-severity="info"]`).
4. Paste the copied URL and inspect it.
   - **Verify — PASSES.** Captured via a monkey-patched `navigator.clipboard.writeText` (the direct
     `navigator.clipboard.readText()` MCP call hung on a permission prompt in this session — see
     Automation Hints). Copied value: `http://localhost:5173/399/agents/all/7598/7820?viewMode=owner&name=elitea-1889-versioning-agent`.
5. Verify the URL contains the version ID (not just the agent URL).
   - **Verify — PASSES.** The URL contains `/agents/all/7598/7820` — the trailing `/7820` segment is the
     **version id**, distinct from the agent id `7598` immediately before it. Confirmed by contrast: the
     `share-agent-menuitem` (AGENT-group "Share") on the same page/version produced
     `http://localhost:5173/399/agents/all/7598?viewMode=owner&name=elitea-1889-versioning-agent` — no
     trailing version segment — proving the version segment is specifically attributable to the
     VERSION-group Share action, not incidental. (Code confirms the mechanism:
     `useProjectEntityLink({ versionId })` in `ApplicationControls.jsx` appends `/${versionId}` only for
     `shareVersionMenuItem`; `shareAgentMenuItem` calls the hook with no `versionId` override.)
6. Navigate to the copied URL — verify it opens the correct agent at the correct version.
   - **Verify — PASSES.** Opened the copied URL in a new browser tab (with the current in-app version
     switched away from `v1` beforehand is unnecessary to prove this, since the URL is opened in a
     fresh tab/session context). The route param name is `version` (not `versionId` — see Automation
     Hints), consumed by `VersionSelect.jsx`'s `versionFromParams` (`urlParams.version ||
     urlParams.versionId`) which fires `getVersionDetailQuery` for that specific version id on mount.
     Confirmed: the new tab loaded the agent `elitea-1889-versioning-agent`, sidebar shows
     `Project: Private`, and the `VERSION:` combobox shows **`v1`** (id `7820`) as the active/selected
     version — the exact agent and exact version the link was copied from. Zero console errors during
     the whole navigate+load.
   - **Note on the leading `/{projectId}` URL segment**: the copied link is
     `http://localhost:5173/399/agents/all/...` (a `/399` project-id prefix baked in by
     `useProjectEntityLink`'s `projectPath` — see `PROJECT_ID_URL_PREFIX` in `common/utils.jsx`). This
     segment is **not** a real matched route on its own; a catch-all `/:projectId/*` route
     (`ProtectedRoutes.jsx`) renders `<ProjectSwitcher/>`, which validates the id is one of the current
     user's available projects, dispatches a project switch, strips the `/{projectId}` prefix from the
     path, and does a **hard `window.location.replace()`** reload at the stripped path
     (`/agents/all/7598/7820?...`). This is expected, pre-existing, cross-cutting behavior (not specific
     to Copy Link — every `useProjectEntityLink`-based Share link on any entity type carries the same
     prefix) — not a defect, but worth the implementer knowing: the round trip in step 6 involves one
     extra hard navigation before the agent page settles, so the automated assertion needs a real wait
     (page load / `VERSION:` combobox text), never an immediate check right after `page.goto()`.

## Expected Results

Matches the case's Pass/Fail Criteria: the VERSION-group "Share" action (`share-version-menuitem`)
produces a URL containing the version id as a distinct path segment (contrasted against the AGENT-group
"Share" action, which omits it), and navigating to that URL — even via a fresh tab, through the
project-switch redirect hop — opens the correct agent at the correct named version. All 6 case steps
pass; two steps (2, 3) exhibit label/confirmation-mechanism drift from the literal case text but the
underlying behavior the case cares about (a working, version-specific copy-link with a visible
confirmation) is fully correct.

## Coverage Map

### Axis 1 — Case element → Coverage
| Case element | Expected result | Covered by | Asserted where | Disposition |
|---|---|---|---|---|
| Precondition: agent with a named version exists | Named version selectable | Test Step 1 | Reused fixture agent 7598, version `v1`/7820 | asserted |
| Step 1: Navigate to agent detail, select named version | Named version is active | Test Step 1 | `VERSION:` shows `v1`; URL updates to `/agents/all/7598/7820?...` | asserted |
| Step 2: Locate Copy Link button in toolbar/three-dot menu | Copy Link button visible | Test Step 2 | `agent-actions-menu-button` → `share-version-menuitem` (VERSION group) | asserted *(label drift: "Share", not "Copy Link" — clarification [#1288](https://github.com/EliteaAI/elitea-testing-public/issues/1288))* |
| Step 3: Click it, verify visual confirmation | Tooltip/icon-change confirmation shown | Test Step 3 | Toast "The link has been copied to the clipboard." (`toast-message`) | asserted *(mechanism drift: toast, not tooltip/icon — same clarification)* |
| Step 4: Paste copied URL and inspect | URL available for inspection | Test Step 4 | Captured via patched `navigator.clipboard.writeText` — `http://localhost:5173/399/agents/all/7598/7820?viewMode=owner&name=...` | asserted |
| Step 5: Verify URL contains version ID, not just agent URL | URL includes version identifier | Test Step 5 | `/agents/all/7598/7820` trailing segment = version id 7820; contrasted against `share-agent-menuitem`'s `/agents/all/7598` (no version segment) | asserted |
| Step 6: Navigate to copied URL, verify correct agent+version opens | Agent opens at expected version | Test Step 6 | New tab → project-switch redirect → `VERSION:` shows `v1`/7820, sidebar Project = Private, agent name matches | asserted |
| Expected Final State: URL is version-specific and opens correct version | — | Test Steps 5–6 | Both directly confirmed above | asserted |

### Axis 2 — Observables asserted beyond the case
| Observable | Reason |
|---|---|
| A **second, distinct** "Share" item exists (`share-agent-menuitem`, AGENT group) that deliberately omits the version id | Load-bearing negative control for Step 5's assertion — without contrasting the two Share actions, "the URL contains a number that looks like a version id" is a much weaker claim than "the VERSION-group Share specifically appends the version id, while the AGENT-group Share specifically does not." Also prevents an implementer from accidentally wiring the test to the wrong menu item (`share-agent-menuitem` is a very plausible mis-click target, being visually identical — both are literally labeled "Share"). |
| The leading `/{projectId}` URL segment and the `ProjectSwitcher` redirect hop it triggers | Not mentioned by the case at all, but directly affects HOW the automated test must wait after navigating to the copied URL — asserting immediately post-`goto()` would race the hard `window.location.replace()` reload. Root-caused via source (`ProtectedRoutes.jsx`'s catch-all `/:projectId/*` route + `ProjectSwitcher.jsx`), not guessed. |
| Route param name mismatch: registered as `:version` (`ProtectedRoutes.jsx`'s nested child route under `:agentId`/`:skillId`), not `:versionId` despite `BLOCK_NAV_PATTERNS`' `${RouteDefinitions.ApplicationsDetail}/:versionId` string literal implying otherwise | Explains why `VersionSelect.jsx` defensively reads `urlParams.version \|\| urlParams.versionId` — confirms the mechanism is intentional and robust, not a hidden fragility, and prevents an implementer from being confused if they inspect `BLOCK_NAV_PATTERNS` and expect a `versionId` param. |
| Zero console errors across the full select-version → open-menu → copy → navigate-to-copied-URL round trip | Per `.agents/testing.md`'s side-channel-check discipline — confirmed clean via `browser_console_messages(level="error")` after the full flow. |

## Cleanup

- No new test data was created this run (reused the pre-existing `elitea-1889-versioning-agent` fixture
  read-only — selecting a version and copying a link mutate nothing server-side). Nothing to clean up.
- The automated implementation, if it follows the "generate-per-test" strategy above, should delete its
  disposable agent at teardown (same pattern as ELITEA-1892's AFS).

## Concrete Handles (discovered / verified during exploration — all pre-existing on `main`, no new
testid work needed)

| Element | testid / handle | Notes |
|---|---|---|
| VERSION dropdown trigger | `agent-version-selector-trigger` | pre-existing |
| Version dropdown option (dynamic) | `version-option-{version_name}` | pre-existing, `AgentDetailPage.VERSION_OPTION` template |
| Agent actions overflow (three-dot) menu button | `agent-actions-menu-button` | pre-existing |
| Agent actions overflow menu container | `agent-actions-menu` | pre-existing |
| **"Share" menu item, VERSION group (the one this case needs)** | `share-version-menuitem` | pre-existing — `DotMenu.jsx`'s `testId: item.key` mechanism (`key: 'share-version'` in `ApplicationControls.jsx`'s `useCopyLinkMenu` call); same mechanism as `publish-version-menuitem`/`unpublish-version-menuitem`/`set-as-a-default-menuitem` |
| "Share" menu item, AGENT group (negative-control / do-not-click) | `share-agent-menuitem` | pre-existing, same mechanism, `key: 'share-agent'` |
| Toast confirmation container | `toast-alert` (+ `[data-severity="info"]` state filter) | pre-existing, app-wide shared component (`Toast.jsx`) — already used by `chat_page.py`/`pipeline_detail_page.py`; **not yet a field on `agent_detail_page.py`**, implementer needs to add `toast_message`/`toast_alert` `LocatorDescriptor`s there (no new EliteaUI testid work, just a page-object field) |
| Toast message text | `toast-message` | pre-existing, same file |
| "Agent ID" footer readout (fallback way to read the agent id, not needed for this case) | `button:has-text("Copy ID")` — no testid | pre-existing gap, out of scope |
| "Version ID" footer readout (fallback way to read the version id, not needed for this case) | `button:has-text("Copy version ID")` — no testid | pre-existing gap, out of scope |

## Automation Hints

- **Reading the clipboard directly via Playwright's `navigator.clipboard.readText()` can hang on a
  permission prompt** in an MCP-driven browser session (observed this run — a raw `browser_evaluate`
  call to `readText()` never returned and had to be aborted after the tool's idle timeout). The pytest
  implementation should instead grant the `clipboard-read`/`clipboard-write` permissions on the
  `BrowserContext` (`context.grant_permissions(["clipboard-read", "clipboard-write"])`) **before** the
  click, which is the standard Playwright pattern and avoids the interactive-prompt hang entirely. (This
  exploration run worked around it by monkey-patching `navigator.clipboard.writeText` via
  `page.evaluate()` before clicking, capturing the copied string into a `window` variable instead of
  reading the clipboard back — a valid fallback if permission-granting is ever unavailable in CI, but
  the `grant_permissions` route is preferred for a real pytest fixture.)
- **Assert the version-specific URL by regex/segment-split, not substring-contains-a-number**: extract
  the path segments after `/agents/all/{agent_id}/` and assert the first segment equals the known
  version id (as a string) — a substring check alone would also spuriously pass against the AGENT-group
  `share-agent-menuitem` link if the agent id itself happens to look numeric-adjacent to something.
- **After navigating to the copied URL, wait for the `VERSION:` combobox text to settle** (real wait,
  not `page.goto()` + immediate assert) — the `ProjectSwitcher` redirect (see Test Step 6 note) performs
  a hard reload before the agent page mounts.
- Reuse `AgentDetailPage.select_version_by_name()` (pre-existing, `agent_detail_page.py:3425`) for Test
  Step 1, and `AgentDetailPage.open_actions_menu()` (pre-existing, `agent_detail_page.py:3113`) for Test
  Step 2 — both already handle the JS-click MUI-overlay-bypass quirk documented on `open_actions_menu()`.

## Known Defects
None found — both drift observations (Steps 2–3) are case-text drift (label/mechanism mismatch), not
product defects; see [EliteaAI/elitea-testing-public#1288](https://github.com/EliteaAI/elitea-testing-public/issues/1288).
