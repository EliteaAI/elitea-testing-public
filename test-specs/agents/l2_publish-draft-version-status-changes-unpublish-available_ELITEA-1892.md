# Test Case: Publish a Draft version — status changes and Unpublish becomes available

## Metadata
- **TMS ID**: ELITEA-1892
- **Linked Story**: none
- **Priority**: l2 (high, per case frontmatter)
- **Environment Explored**: local (`http://localhost:5173`, EliteaUI `automation/testids` branch → DEV
  backend), project `Private` / `${ELITEA_PROJECT_ID}`=399
- **User set**: `${TEST_USER}` (on localhost, `auth_state` fixture skips login via `VITE_DEV_TOKEN`)
- **Analyst**: qa-engineer (Sage), analyst slot
- **Status**: `ready-for-automation` — case executed end-to-end against the live system, all 8 steps
  verified, no blockers. Eight missing testids were discovered and added live this run (see EliteaUI
  changes below) — the wizard could not otherwise be automated per the project's testid-only locator
  policy. One MINOR product defect (console warnings, non-blocking) and one case-text CLARIFICATION were
  filed; neither blocks automation.

## Preconditions
- User is logged in (on localhost, `auth_state` fixture skips login).
- A project is selected/accessible (`Private`, id `399` in this run).
- **`applications.publish` permission — VERIFIED held by `${TEST_USER}`.** Confirmed live: the "Publish"
  menu item rendered enabled in the agent's VERSION actions menu (`usePublishVersion.hooks.js`'s
  `canShowPublish` gate requires `permissions.includes(PERMISSIONS.applications.publish)`). This was the
  case's stated precondition and it holds for this user set — not a `blocked` finding.
- An agent with at least one Draft version exists — **satisfied by creating a dedicated, disposable agent
  per run** (see Test Data below), consistent with the pattern used in
  `l3_agent-icon-change-persists-on-list-card_ELITEA-1899.md` / `lcritical_save-as-version-creates-named-version-visible-in-dropdown_ELITEA-1888.md`
  history. A brand-new agent's default "base" version is Draft (`CollectionStatus.Draft`) — no separate
  setup needed once the agent is created.
- **Platform publish policy** — `usePublishVersion.hooks.js` also gates on
  `platformSettings.is_publish_blocked` (project-whitelist check). Not triggered in this run (Publish
  proceeded normally for project `Private`); flagging in case a future run hits it — if so, that is a
  `blocked` finding, not a defect.

## Test Data

### reuse-existing
- None — this case's steps mutate a version's publish status, so a dedicated disposable agent is required
  (see below); no shared fixture agent is safe to reuse (an accumulated extra published/unpublished
  version, and an extra clone version per publish, would persist on a shared agent — mirrors the
  "no delete-version UI/API, only whole-agent delete" constraint documented in ELITEA-1888's AFS).

### generate-per-test (in test setup, cleaned up in its own teardown)
- A uniquely-named agent, created via the UI's "New Agent" flow (`/agents/create`) or
  `AgentAPI.create_agent_full()` if a raw-payload creation matching UI defaults is preferred. **This run
  used the UI create flow directly** (Name `elitea-1892-publish-test`, Description
  `Disposable agent for ELITEA-1892 publish/unpublish manual analysis`) — no `#524`-style default
  `llm_settings` issue was hit (that defect's fix — "update default settings to match UI-created agent
  defaults", `b60ce389` — is already on this branch).
- **Content required to pass AI publish-validation** (see Test Steps step 5 below for why): the base
  version's Instructions field must contain substantive text (a single word / boilerplate template is
  rejected as "Instructions are missing" / "do not provide concrete behavioral guidance"), and at least
  one Tag must be set. This run used:
  - Instructions: `"You are a helpful QA validation assistant for the ELITEA platform publish/unpublish
    exploration test (ELITEA-1892). You answer general questions about testing status."`
  - Tag: `regression` (an existing tag suggestion — see Automation Hints for the tag-field character
    restriction that bit this run)
  - Welcome message: a short greeting (clears a Warning, not a Critical Issue — optional but keeps the
    AI-validation summary cleaner)
- Version name (per case Test Data table): `v1-release` — typed literally, no case-text drift (regex
  `/^[a-zA-Z0-9._-]*$/` accepts it as-is).
- Category: **not specified by the case's Test Data table but is a hard requirement** to enable
  "Continue" in the non-admin publish wizard (see Test Steps step 2 and the Clarification issue below).
  This run selected `Quality Assurance` from the dropdown (`agent_categories` API); any option value the
  automated test controls deterministically is fine — the assertions in this case don't depend on which
  category is chosen.

## Test Steps

1. Navigate to `${BASE_URL}/agents/all/{agent_id}?viewMode=owner`. Confirm the Draft version is loaded.
   - **Verify**: `VERSION:` combobox shows `base`; version-id textbox shows the new agent's base version
     id. Overflow menu (`agent-actions-menu-button`) → VERSION group shows a **Publish** menu item,
     confirming `applications.publish` permission (precondition) and Draft status are both satisfied.
2. Click `publish-version-menuitem` ("Publish").
   - **Verify — PASSES, with case-text drift** (see CLARIFICATION issue
     [EliteaAI/elitea-testing-public#612](https://github.com/EliteaAI/elitea-testing-public/issues/612)).
     A `role="dialog"` opens, heading **"Publish version"** — but it is a **3-step wizard**
     (`PUBLISH_STEPS = { PREPARATION, VALIDATION, PUBLISHING }`, visible as a `Stepper` at the top: labels
     "Preparation" / "Validation" / "Publishing"), not a single version-name field. The Preparation step
     shows a Version-name input (`agent-publish-version-name-input`), a **Category dropdown**
     (`agent-publish-category-select`, not mentioned in the case) and an **"I agree with the Publishing
     Terms" checkbox** (`agent-publish-agree-checkbox`, also not mentioned) — "Continue" stays disabled
     until all three are filled/checked.
3. (Case: "Verify a dialog appears prompting for a version name.") Confirmed as part of step 2's
   observation — the dialog is visible with the Version-name input present. Case text describes only the
   name field; the dialog in fact also requires Category + Terms acceptance (see step 2's note).
4. Type `v1-release` into `agent-publish-version-name-input`, select a Category option (dynamic testid
   `select-option-{Category Name}`, e.g. `select-option-Quality Assurance` — pre-existing generic
   `SingleSelectMenuItem` pattern, no change needed) from `agent-publish-category-select`, check
   `agent-publish-agree-checkbox`, then click `agent-publish-continue-button` ("Continue").
   - **Verify — PASSES.** `POST /api/v2/elitea_core/publish_validate/prompt_lib/{project}/{versionId}`
     fires. The Stepper visually advances to "Validation".
5. Verify the version status changes / the AI validation gate. (Case: *"Verify the version status
   changes (e.g., 'In Review' or 'Published' depending on moderation)"* — see note below.)
   - **Verify — PASSES, with an important behavioral nuance the case doesn't name.** There is no
     "In Review" `CollectionStatus` value in this codebase (`CollectionStatus = { All, Draft, Published,
     OnModeration, UserApproval, Rejected }`) — the "moderation" the case alludes to is this **AI content
     validation step**, not a human-moderator queue. `publish_validate` returns a summary with
     Critical/Warning/Suggestion counts:
     - **1st attempt** (agent with no tags, no instructions): 2 Critical issues (`tags: No tags defined`,
       `instructions: Instructions are missing`) → `422 Unprocessable Entity`, "Publish" button on the
       Validation step stays **disabled** (`canPublish = validationResult?.status !== 'FAIL'`).
     - **2nd attempt** (after adding real instructions, still no tags): 1 Critical issue remained
       (`tags`) → still `422`/disabled. (Confirms the tag field, not just instructions, is independently
       required.)
     - **3rd attempt** (after adding a tag `regression` + a welcome message): 0 Critical issues, 3
       Warnings (description lacks action verbs / no custom icon / no conversation starters), 1
       Suggestion (semantic versioning) → `200 OK`, "Publish" button (`agent-publish-confirm-button`)
       became **enabled**.
6. Click `agent-publish-confirm-button` ("Publish").
   - **Verify — PASSES.** `POST /api/v2/elitea_core/publish/prompt_lib/{project}/{versionId}` returns
     `200 OK` with a `source_version_id`. The app navigates to
     `/agents/{tab}/{agent_id}/{source_version_id}?viewMode=owner` — **a brand-new version**, not the
     Draft version that was published. The `VERSION:` combobox on this new page shows `v1-release`
     (the name typed in step 4). Opening the VERSION dropdown (`agent-version-selector-trigger`) shows
     **both** `version-option-base` (still Draft — untouched) **and** `version-option-v1-release`
     (`[selected][active]`) — confirming Publish **clones the Draft version into a new version that
     carries the Published status**, rather than flipping the original Draft version's status in place.
     Toast: "The agent has been published."
7. (Case: *"If approved: verify the version appears as Published in the version dropdown."*) Confirmed
   as part of step 6's observation — `version-option-v1-release` is present and selected.
   Verify the "Unpublish" button is available on the published version — open
   `agent-actions-menu-button` on the `v1-release` version.
   - **Verify — PASSES.** The VERSION group of the overflow menu now shows **`unpublish-version-menuitem`**
     ("Unpublish") in place of "Publish" (`useUnpublishVersionMenu.hooks.jsx`'s `canUnpublish` gate:
     `versionStatus === CollectionStatus.Published`). "Set as a default" also becomes enabled at this
     point (it's disabled for a Published version's *sibling*, but this is the version itself, whose
     `disableSetAsADefault` check only special-cases `status === 'published'` for OTHER menu contexts —
     confirmed via DOM: `Set as a default` enabled once this version stopped being the newly-created one
     mid-transition).
8. Click `unpublish-version-menuitem` → confirm dialog appears (heading **"Unpublish Agent"**, matching
   `UnpublishConfirmModal.jsx`) → click `agent-unpublish-confirm-button` ("Unpublish").
   - **Verify — PASSES.** `POST /api/v2/elitea_core/unpublish/prompt_lib/{project}/{versionId}` (targets
     the *published clone's* version id directly — `v1-release`/`5230` in this run, not the original
     Draft) returns success; toast "Agent has been successfully unpublished!". Re-opening the overflow
     menu on this same version shows **`publish-version-menuitem`** again (status reverted to Draft —
     `canShowPublish` is true again), confirming the case's literal assertion *"the version status
     reverts to Draft"* holds — for the version that was actually published (the clone), which is the
     behaviorally-relevant entity even though it's not the same version id as the one originally selected
     in step 1.

## Expected Results

Matches the case's Pass/Fail Criteria with the nuance captured above: publishing a Draft version makes
Unpublish available on the resulting Published version, and clicking Unpublish reverts that version's
status back to Draft. The full publish → unpublish cycle completed without errors (aside from the
expected/intentional `422` validation-FAIL responses while the disposable agent's content didn't yet meet
the AI-validation bar — those are correct product behavior, not failures of the cycle itself).

## Coverage Map

### Axis 1 — Case element → Coverage
| Case element | Expected result | Covered by | Asserted where | Disposition |
|---|---|---|---|---|
| Precondition: User has `applications.publish` permission | Publish menu item available | Test Step 1 | `${TEST_USER}` — Publish menu item enabled on a Draft version | asserted |
| Precondition: agent with a Draft version exists | Agent detail page reachable, Draft loaded | Test Step 1 | New disposable agent's `base` version, `VERSION:` shows "base" | asserted |
| Step 1: Navigate to agent detail, select Draft version | Draft version loaded in editor | Test Step 1 | URL `/agents/all/{id}?viewMode=owner`, `VERSION:` "base" | asserted |
| Step 2: Click "Publish" (requires permission) | Dialog appears prompting for version name | Test Step 2 | `publish-version-menuitem` click → `role="dialog"` "Publish version" opens | asserted *(decomposed: dialog is a 3-step wizard, not a single name field — see step 2's note + clarification #612)* |
| Step 3: Verify dialog appears prompting for version name | Publish dialog with version-name input visible | Test Step 2 (same interaction/observation) | `agent-publish-version-name-input` present in Preparation step | asserted (merged with Step 2) |
| Step 4: Enter version name, click Publish | Publish action submitted | Test Steps 4-6 | `agent-publish-version-name-input` filled "v1-release"; **Category + Terms-checkbox also required** (not in case) → Continue → AI Validation → `agent-publish-confirm-button` click → `POST .../publish/...` 200 | asserted *(decomposed into fill-form / continue / validate / confirm-publish — case's single "click Publish" step maps to a 3-stage wizard interaction)* |
| Step 5: Verify version status changes ("In Review" or "Published" depending on moderation) | Status updated accordingly | Test Step 5 | AI `publish_validate` response (Critical/Warning/Suggestion summary) gates the Publish button; no literal "In Review" `CollectionStatus` exists — the moderation the case alludes to is this AI-validation gate, not a separate status value | asserted, with terminology clarified in step 5's note |
| Step 6: If approved, verify version appears Published in dropdown | Version shows Published status in dropdown | Test Step 6 | `agent-version-selector-trigger` → `version-option-v1-release` `[selected][active]`, distinct from `version-option-base` | asserted |
| Step 7: Verify "Unpublish" button available on published version | Unpublish visible and clickable | Test Step 7 | Overflow menu shows `unpublish-version-menuitem` (not `publish-version-menuitem`) once status is Published | asserted |
| Step 8: Click Unpublish, verify status reverts to Draft | Version status reverts to Draft | Test Step 8 | `agent-unpublish-confirm-button` click → `POST .../unpublish/...` success → overflow menu shows `publish-version-menuitem` again on the same version | asserted |
| Test Data: Version name "v1-release" | literal value | Test Step 4 | Typed as-is via `agent-publish-version-name-input`, no case-text drift (regex `/^[a-zA-Z0-9._-]*$/` accepts it) | covered, no clarification needed |
| Expected Final State: status is Draft again, full cycle completes without errors | — | Test Step 8 | Confirmed — `publish-version-menuitem` reappears; no unexpected errors in the cycle itself (the two `422` validation-FAIL responses during setup are expected AI-gate behavior, not cycle errors) | asserted |

### Axis 2 — Observables asserted beyond the case
| Observable | Reason |
|---|---|
| Publish clones the Draft version into a **new** version rather than flipping the original Draft version's status in place (`base`/5229 stayed Draft throughout; `v1-release`/5230 was the entity that went Published→Draft) | Load-bearing for the automated test's assertion strategy — asserting "the version I selected in step 1 is now Published" would be **wrong**; the implementer must track the `source_version_id` returned by the publish response (or re-open the VERSION dropdown) and assert against that. This is exactly the kind of gap a naive re-implementation of the case text would fall into. |
| AI `publish_validate` Critical-issue gate (tags + substantive instructions required) — confirmed the specific fields checked and that Warnings/Suggestions do NOT block, only Critical does | The disposable-agent test-data strategy depends on this — the automated test must seed enough content to pass validation, or it will hang on a disabled Publish button. Documented exactly which fields are Critical (tags, instructions) vs Warning (description verbs, icon, name-as-identifier, welcome message, conversation starters) vs Suggestion (semantic versioning) from live AI responses (content is LLM-generated per-run and may vary in wording, but the tags/instructions Critical-ness was stable across repeated attempts in this run). |
| Publish-wizard Preparation-step fields (version name, category, agree-checkbox) do **not** persist if the dialog is cancelled/reopened — confirmed by reopening the dialog after Cancel and finding all fields reset | Automation must re-fill the full Preparation step every time the wizard opens; caching a "already filled" assumption across a Cancel+reopen would be a source of flakiness. |
| Tags field character restriction: only alphanumeric, whitespace, comma, underscore — **hyphens are rejected** (`Only alphanumeric characters, white space, comma and underscore allowed`), which is a *different* (stricter) regex than the Version-name field's `/^[a-zA-Z0-9._-]*$/` (which explicitly allows hyphens) | This run's first tag attempt (`elitea-1892`, with a hyphen) silently failed to commit — worth flagging explicitly so an implementer doesn't repeat the same confusion typing a hyphenated tag as test data. |
| Console-error check during the Publish wizard (per `.agents/testing.md` "check console even when UI looks fine") | Found + filed as a MINOR defect (see Known Defects below) — the Stepper's custom step-icon leaks MUI-internal boolean props onto the DOM `<svg>`, producing 4 React console warnings every time the wizard renders. Confirmed isolated to `PublishWizardModal`'s Stepper (a parallel Unpublish-only pass produced 0 console errors). |

## Cleanup

- The disposable agent (`elitea-1892-publish-test`, id `5200` this run, including all 3 versions it
  accumulated — `base`/5229 Draft, `v1-release`/5230 Draft-after-unpublish, `v2-repub`/5231
  Draft-after-unpublish — the extra `v2-repub` version was created live-verifying the newly-added
  testids, see EliteaUI changes below) was **deleted in full** via the UI: overflow menu
  (`agent-actions-menu-button`) → AGENT group → `delete-agent-menuitem` → type-to-confirm dialog (name
  typed into the `#name` input inside `delete-confirm-name-input`) → `Delete`. Verified: the agent no
  longer appears in `/agents/all`'s listing (`document.body.innerText` no longer contains
  `elitea-1892-publish-test`).
- **No shared/long-lived fixture was touched** — this run created and destroyed its own disposable agent
  end-to-end, leaving the project's baseline unchanged. Recommended pattern for the automated test:
  create-fresh-agent-per-run + delete-at-teardown (mirrors ELITEA-1888's superseded/fixed pattern — do
  **not** reuse a shared agent, since publish permanently adds versions with no per-version delete API).
- No other test data was created (no new Skill, no new Toolkit).

## Concrete Handles (discovered / added during exploration)

**All 8 testids below were added live this run** — none existed before (confirmed via
`document.querySelectorAll('[data-testid]')` before editing). Committed to `automation/testids`
(commit `a1914991` on `EliteaAI/EliteaUI`, pushed) and confirmed rendering live via Vite HMR (each was
re-verified present in the DOM after the commit, driving the full flow a second time).

| Element | testid | Mechanism / File | Confirmed live this run? |
|---|---|---|---|
| Publish menu item (VERSION actions overflow) | `publish-version-menuitem` | Added `key: 'publish-version'` to the menu-item object in `src/[fsd]/entities/version/lib/hooks/usePublishVersionMenu.hooks.jsx` — `DotMenu.jsx`'s existing `testId: item.key` → `data-testid={testId}-menuitem` mechanism does the rest (same mechanism already backing the sibling `delete-version` menu item) | yes (added this run) |
| Unpublish menu item (VERSION actions overflow) | `unpublish-version-menuitem` | Added `key: 'unpublish-version'` to `src/[fsd]/entities/version/lib/hooks/useUnpublishVersionMenu.hooks.jsx`, same DotMenu mechanism | yes (added this run) |
| Publish-wizard Version-name input (Preparation step) | `agent-publish-version-name-input` | `src/[fsd]/entities/version/ui/PreparationStep.jsx` — `inputProps={{ maxLength: VERSION_NAME_MAX_LENGTH, 'data-testid': '...' }}` on `Input.InputBase` (same pattern as `agent-version-dialog-name-input` in `SaveNewVersionButton.jsx`) | yes (added this run) |
| Publish-wizard Category select (Preparation step) | `agent-publish-category-select` | `PreparationStep.jsx` — `data-testid="..."` prop directly on `<Select.SingleSelect>` (first-class supported prop, `SingleSelect.jsx` destructures `'data-testid': dataTestId` and forwards it to the underlying MUI `<Select>`) | yes (added this run) |
| Publish-wizard "I agree" checkbox (Preparation step) | `agent-publish-agree-checkbox` | `PreparationStep.jsx` — `data-testid="..."` prop on `<Checkbox.BaseCheckbox>` (spreads `...restProps` onto MUI `<Checkbox>`) | yes (added this run) |
| Publish-wizard Continue button (Preparation step) | `agent-publish-continue-button` | `src/[fsd]/entities/version/ui/PublishWizardModal.jsx`, non-admin PREPARATION-step branch only — admin-only branch and other conditional Publish buttons in this file were **not** touched (out of this run's exercised scope) | yes (added this run) |
| Publish-wizard Publish/confirm button (Validation step) | `agent-publish-confirm-button` | Same file, non-admin VALIDATION-step branch only | yes (added this run) |
| Unpublish confirm-dialog "Unpublish" button | `agent-unpublish-confirm-button` | `src/[fsd]/entities/version/ui/UnpublishConfirmModal.jsx` | yes (added this run) |
| VERSION dropdown trigger | `agent-version-selector-trigger` | pre-existing (added in ELITEA-1888's run) | yes (pre-existing) |
| Version dropdown option (dynamic) | `version-option-{version_name}` | pre-existing template pattern (`buildVersionOption` in `ApplicationControls.jsx`) — page object: `VERSION_OPTION = '[data-testid="version-option-{}"]'`, `.format(name)` at call sites | yes (pre-existing) |
| Category dropdown option (dynamic) | `select-option-{category_label}` | pre-existing generic `SingleSelectMenuItem` default pattern — same shape, `SELECT_OPTION = '[data-testid="select-option-{}"]'` | yes (pre-existing, e.g. `select-option-Quality Assurance`) |
| Agent actions overflow (three-dot) menu button | `agent-actions-menu-button` | pre-existing (`automation/pages/agent_detail_page.py:124`) | yes (pre-existing) |
| Delete agent menu item | `delete-agent-menuitem` | pre-existing | yes (pre-existing) |
| Delete-confirmation name field | `delete-confirm-name-input` (scope to inner `#name`) | pre-existing, same scoping gotcha documented in ELITEA-1888/1889's AFS — testid is on a wrapper, real `<input>` is `#name` inside it | yes (pre-existing) |
| Delete-confirmation confirm button | `getByRole('button', { name: 'Delete' })` scoped to the dialog | pre-existing residual gap (not testid'd) — out of this case's scope to fix, same finding as ELITEA-1888/1889 | pre-existing gap, unchanged |
| Agent Instructions field | `agent-instructions-input` | pre-existing | yes |
| Agent Welcome message field | `agent-welcome-message-input` | pre-existing | yes |
| Agent Save button | `agent-save-button` | pre-existing | yes |
| Agent create-form Name/Description inputs | `agent-name-input` / `agent-description-input` | pre-existing | yes |

**Not touched (out of this run's exercised scope, per the team's "testids only on elements a test
actually touches" ruling):** Cancel buttons in either dialog, the dialog X/close buttons, the
`isAdminPublish` branch's version-name-input/category-select/Publish-button in `PublishWizardModal.jsx`,
the `showReason` Reason textfield in `UnpublishConfirmModal.jsx` (admin-only), the Stepper/step-label
elements, the Publish-wizard Cancel/Close and Unpublish-dialog Cancel/Close buttons. The Tags field on
the Agent form itself (`agent-tags-input` or similar) also has no testid — not touched, since the case
doesn't require asserting on it (only that a valid tag was set to pass AI validation); flagging for
whoever next automates a case that does need to assert Agent Tags directly.

## Network Behavior
- `POST /api/v2/elitea_core/publish_validate/prompt_lib/{project}/{versionId}` — fires on "Continue"
  click. Returns `422 Unprocessable Entity` with a `status: 'FAIL'` body (Critical/Warning/Suggestion
  arrays) when Critical issues exist, `200 OK` (same shape, no FAIL) when only Warnings/Suggestions
  remain or the agent is clean. Automated test should wait for this response before asserting the
  Validation-step summary or the Publish button's enabled state.
- `POST /api/v2/elitea_core/publish/prompt_lib/{project}/{versionId}` — fires on the Validation step's
  "Publish" click. `{versionId}` in the URL is the **original Draft version's id** (the one selected in
  step 1), but the response's `source_version_id` is the **new clone's id** — the automated test needs to
  capture this value (from the response, or from the post-navigation URL / VERSION dropdown) to make
  correct assertions in steps 6-8.
- `POST /api/v2/elitea_core/unpublish/prompt_lib/{project}/{versionId}` — fires on the Unpublish confirm
  dialog's "Unpublish" click. `{versionId}` here is the **published clone's** id (not the original
  Draft's) — the version whose status actually flips back to Draft.
- `GET /api/v2/elitea_core/agent_categories/prompt_lib/{project}` — populates the Category dropdown's
  options; automated test can wait on this before interacting with the Category select to avoid an
  empty-options race.

## Known Defects Found During Exploration

- **[MINOR]** Publish-wizard Stepper's custom step-icon (`CheckedIcon`/`SvgCheckedIcon`,
  `src/assets/checked-icon.svg?react`) leaks MUI-internal boolean props (`completed`, `active`, `error`,
  `ownerState`) onto the DOM `<svg>` element, producing 4 distinct React console warnings every time the
  Publish wizard's Stepper renders (deterministic, 2/2 attempts across separate contexts this run;
  confirmed isolated to `PublishWizardModal.jsx` — a parallel Unpublish-only pass produced 0 console
  errors). No visible UI breakage; the stepper renders and functions correctly. Filed:
  [EliteaAI/elitea-testing-public#611](https://github.com/EliteaAI/elitea-testing-public/issues/611).
  **Automation guidance**: `expect.soft()` on the console-clean assertion for this flow with
  `# Known defect: #611`, don't hard-fail the whole test on it.
- **[CLARIFICATION]** ELITEA-1892's case text (steps 2-4) describes the Publish action as a single dialog
  with just a version-name field; the live product is a 3-step wizard requiring Category selection and
  Publishing-Terms agreement before an AI-validation gate, then Publish. Live product behavior is correct
  (Reverse-masking guard — the case text is what's stale); requested a case-text update. Filed:
  [EliteaAI/elitea-testing-public#612](https://github.com/EliteaAI/elitea-testing-public/issues/612).
  Does not block automation — the AFS's Test Steps above already describe the real flow.
- **[MINOR — amended by implementer, ELITEA-1892 automation pass]** This AFS's own Step 6 narrative ("the
  app navigates to `/agents/{tab}/{agent_id}/{source_version_id}` … the VERSION combobox shows
  `v1-release`") does **not** hold reliably on live re-verification: a network trace shows the app briefly
  navigating to the new Published version (`GET .../version/.../{new_id}` resolves 200) and then silently
  reverting to the previously-active version (`GET .../version/.../{old_id}` fires again immediately after)
  — no error surfaced, underlying data unaffected (confirmed correct via API in every case: the new version
  really is `published`, the original stays `draft`). Reproduced repeatedly with real Playwright-driven
  clicks. This is a live-contract drift from this AFS's own prior observation (reverse-masking guard applies
  to the AFS's text too, not only the TMS case's) — filed:
  [EliteaAI/elitea-testing-public#614](https://github.com/EliteaAI/elitea-testing-public/issues/614).
  **Automation guidance (supersedes the Automation Hints §Wait-strategy bullet below)**: do NOT wait for /
  assert on auto-navigation after Publish. Explicitly re-select the new version by name from the VERSION
  dropdown instead (a normal, reliable user action, confirmed live not to revert) before asserting against
  it — exactly the fallback this AFS's own Axis 2 table anticipated ("...or re-read the VERSION dropdown
  after the post-publish navigation"). The automated test additionally found the overflow menu's
  Publish/Unpublish item can itself lag behind a freshly-selected version's true status by more than one
  render tick (occasionally persisting across several menu re-opens) — a full page reload after selecting
  the version, and a bounded reopen-and-recheck poll on the overflow menu, were both needed for a stable
  automated check; even so, produced a small residual flake rate (~1 run in 9 during implementation) tied to
  this same root cause. Not blocking (the underlying publish/unpublish data is always correct), but noted
  here for whoever revisits this defect or re-tunes the automated test's wait strategy.

## Blocked Steps

None. All 8 case steps executed and verified live; no step required stopping short.

## Automation Hints
- Framework: Playwright + pytest (confirmed from `.agents/testing.md`).
- Page object: extend `automation/pages/agent_detail_page.py` (the `agent-actions-menu-button` /
  `delete-agent-menuitem` fields already live there per ELITEA-1888/1889's AFS) with a new
  `PublishWizardComponent` / `UnpublishConfirmComponent` (or equivalent) covering the 8 testids captured
  above; keep the dynamic `VERSION_OPTION` and `SELECT_OPTION` template constants at class level, per
  `.agents/testing.md` § dynamic testids (never inline f-string `get_by_test_id`).
- Wait strategy: wait for the `publish_validate` response before asserting the Validation-step summary or
  the Publish button's state (never a fixed `sleep`). ~~wait for the post-publish navigation (`wait_for_url`
  matching `/agents/{tab}/{id}/{new_version_id}`) before asserting the VERSION dropdown~~ — **superseded,
  see the `#614` Known Defect above**: auto-navigation after Publish is unreliable; explicitly re-select the
  new version by name from the VERSION dropdown instead, never trust/wait-for a URL-based auto-navigation.
- Test-data generation: seed the disposable agent's Instructions with a real sentence (not a single word)
  and set at least one Tag (alphanumeric/underscore only — avoid hyphens, see Axis-2 gotcha above) so the
  AI-validation gate passes deterministically on the first attempt, avoiding this run's 2 failed
  `publish_validate` round-trips (which are correct product behavior but add avoidable latency/flakiness
  risk to an automated run if not anticipated).
- Consider: since `publish_validate` is an AI-driven check whose exact Warning/Suggestion wording may
  vary run-to-run, assert on the **counts** (Critical Issues == 0, or Critical Issues array is empty) and
  the Publish button's enabled state, not on literal Warning/Suggestion text.
