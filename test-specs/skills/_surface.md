# Skills surface — exploration digest

Confirmed handles/quirks from live runs on `http://localhost:5173`
(`automation/testids` branch). Cache only — verify a handle as you use it,
don't take it on faith. One writer at a time (whoever is the active
analyst); update in place, don't append duplicate entries.

## Pin/unpin — `/skills/all` list + `/skills/all/{id}` detail overflow menu

- List-view "Pin to top" / "Unpin from top" icon button (`PinButton.jsx`,
  shared across entity types via `DataTableRow.jsx`) — **confirmed live,
  PRE-EXISTING testid**: `data-testid="skill-pin-toggle-button-{id}"`
  (`getPinTestIdSlug()` maps skill cards → `'skill'`). Appears to have
  landed generically for all entity types when `EliteaAI/EliteaUI#569`
  fixed the credential-specific gap (ELITEA-1974) — no separate
  `add-data-testid` round-trip needed for this element.
- Detail page → three-dot overflow menu button:
  `data-testid="skill-controls-menu-button"` (`SkillControls.jsx`'s
  `anchorButtonProps`) — pre-existing, already wired as
  `SkillDetailPage.controls_menu_button`.
- Detail page → pin-toggle menu item ("Pin to top" / "Unpin from top",
  `usePinMenu.hooks.jsx` rendered via `DotMenu`'s `BasicMenuItem`) —
  **CONFIRMED LIVE GAP, no `data-testid`.** `SkillControls.jsx`'s
  `menuItems` array spreads `pinMenuItem` with no `key:` field (unlike the
  sibling `delete-skill` item), and `DotMenu.jsx` derives
  `testId: item.key` per entry — no key ⇒ no testid. Same shape as the
  credential case's pre-#569 gap. Fix: add `key: 'pin-toggle-skill'` to the
  spread → produces `data-testid="pin-toggle-skill-menuitem"` via
  `DotMenu`'s `${testId}-menuitem` convention. Not yet fixed as of this run
  (ELITEA-2435 analysis) — implementer work via `add-data-testid`.
- Pin endpoint: `POST /api/v2/social/pin/prompt_lib/{project_id}/skill/{id}`
  → `201 Created`. Unpin: `DELETE` same path → `204 No Content`. (Note the
  path segment is `skill`, not `configuration` as for credentials —
  `PinEntityType.Skill` drives this.)
- List response (`GET .../elitea_core/skills/prompt_lib/{project}/...`)
  carries `is_pinned: bool` per row — usable for a data-level assertion
  alongside the visual one.
- `usePin()` for Skills runs the **local-state branch** (no `formikContext`
  passed from `EditSkill.jsx`'s `<SkillControls initialPinned={data?.is_pinned}>`),
  unlike Credentials which drives `isPinned` off Formik values. No dead-prop
  typo bug here (unlike the harmless Cyrillic-`ш` one documented in
  ELITEA-1974's AFS for `CredentialsControls.jsx`) — confirmed functionally
  correct live both ways.
- **Gotcha:** pinning a skill that's already the list's newest/topmost item
  (sorted `created_at desc`) produces no visible reordering — only the
  icon/menu-label flips. To prove actual reordering, pin/observe a
  **bottom-ranked** skill instead (confirmed live: `changelog-editor`, the
  oldest of 10 skills, moved from last to first on pin).
  Full details: `test-specs/skills/l3_skill-pin-unpin-flow_ELITEA-2435.md`.

## VERSION dropdown — set-as-default (ELITEA-2437) — `SkillTabBar.jsx` (`skill-version-select`)

**Distinct from the entity-level "Pin to top" flow above** — same "pin"
visual language, unrelated mechanism. This is per-*version* default-setting
within one skill, not per-*skill* list pinning.

- Trigger: `data-testid="skill-version-select"` (`SkillTabBar.jsx`) — the
  live clickable `role=combobox` node inside it resolves as
  `[data-testid="skill-version-select-combobox"]`.
- Dropdown options: `data-testid="version-option-{name}"` (existing
  `VERSION_OPTION` template, shared by skill/agent/pipeline consumers via
  `buildVersionOption()` in `entities/version/lib/helpers/version.helpers.jsx`).
- Current-default row: static `data-testid="version-option-pin-icon"`
  (**confirmed live, existing testid** — unconditional whenever
  `defaultVersionID === id`, no hover needed).
- Non-default/non-published row: hover-revealed "set as default" icon
  button — **CONFIRMED LIVE GAP, no `data-testid`.** Only a non-unique CSS
  `id="show-on-hover"` (styling-only, not a valid handle). Clicking it opens
  a `SetDefaultVersionDialog` ("Set as default?") confirmation dialog.
  Fix: add a name-keyed dynamic testid in `version.helpers.jsx`, e.g.
  `data-testid={`version-option-set-default-${name}`}` — mirrors the
  sibling `version-option-{name}` convention in the same function. Shared
  by skill/agent/pipeline consumers; not yet fixed for any of them as of
  this run (ELITEA-2437 analysis).
- Confirm dialog's "Set as a default" button — **CONFIRMED LIVE GAP for the
  Skill flow only.** `SetDefaultVersionDialog.jsx` already supports an
  optional `confirmButtonTestId` prop (forwarded to the button), and the
  **Agent** flow already wires it
  (`useSetDefaultVersion.hooks.jsx:104` →
  `confirmButtonTestId="agent-set-default-version-confirm-button"`) — but
  `EditSkill.jsx`'s call site (line ~271) never passes it. One-line fix:
  add `confirmButtonTestId="skill-set-default-version-confirm-button"` at
  that call site, copying the Agent precedent exactly.
- Endpoint: `PATCH /api/v2/elitea_core/skill_default_version/prompt_lib/
  {project_id}/{skill_id}` → `200 OK`.
- Confirmation toast: reuses the app-wide `toast-message` testid (same one
  `save_as_version()` waits on for "Version created"). Exact text confirmed
  live: **"Default version has been set successfully"**.
- After confirming, the newly-default version's dropdown row gains
  `version-option-pin-icon` and the option list re-sorts it to the top
  (all `buildVersionOption` consumers sort `defaultVersionID` first) — a
  second, data-independent confirmation signal beyond the toast.
- The VERSION dropdown's own collapsed-trigger summary (`SkillTabBar.jsx`'s
  `renderVersionValue`) also renders its own small pin glyph next to the
  default version's name — **no testid on this one either**, but out of
  scope for ELITEA-2437 since the toast + list-level `version-option-pin-icon`
  already satisfy the case's pass criterion (only what a test's own code
  path touches gets a testid request, per `.agents/testing.md` § Locator
  policy).
  Full details: `test-specs/skills/l3_skill-version-dropdown-set-default_ELITEA-2437.md`.

## Build with AI (skill creation) — `/skills/create` → `GenerateSkillModal`

- Modal shell (`GenerateEntityModal.jsx`) is shared with the Agent "Build
  with AI" flow via `GenerateEntityModalPageBase` — same loading/error/retry
  mechanics, entity-specific testids (`generate-skill-*` vs `generate-agent-*`).
- Steps: `input` (prompt) → `loading` → `review` (Name/Description/
  Instructions only — no Welcome Message/conversation starters, unlike Agent).
- Generate-draft endpoint: `POST /api/v2/elitea_core/generate_skill_draft/prompt_lib/{projectId}`.
- Create endpoint: `POST /api/v2/elitea_core/skills/prompt_lib/{projectId}`
  → `201`, payload `{name, description, versions: [{name: "base"|"latest", instructions}]}`
  — no `temperature`/`reasoning_effort` fields (unaffected by bug #524, which
  is Agent-only via a different endpoint/payload shape).
- Review-form fields are fully client-validated, synchronously, no network
  call: `validateSkillDraft()` in
  `../EliteaUI/src/[fsd]/features/skill/lib/helpers/skillDraftValidation.helpers.js`.
  Name regex: `/^[a-z0-9]([a-z0-9-]*[a-z0-9])?$/` (lowercase/digits/hyphens,
  no leading/trailing hyphen), max 64 chars — **and the Name `<input>` also
  carries a native HTML `maxlength="64"`, so an over-64-char value can never
  actually be entered manually (typed or `.fill()`'d) — it silently truncates
  at 64 before validation ever runs.** The `Create <Entity>` button's
  `disabled` prop is `isApproving || !isDraftValid`
  (`GenerateEntityModal.jsx:189`) — `isDraftValid` flows from
  `onValidationChange` in the review-form component.
- Testids (all `generate-skill-*`): `open-button`, `modal`, `close-button`,
  `prompt-input`, `error-alert`, `loading-indicator`, `submit-button`
  (Generate, also the retry control), `cancel-button`, `back-button`,
  `approve-button` (Create Skill), `review-name-input`,
  `review-description-input`, `review-instructions-input` (all pre-existing
  as of ELITEA-1990), plus **`review-name-helper-text`** (added ELITEA-1993,
  commit `8e78723b` on `automation/testids`) — the Name field's validation-
  error / `{len}/64`-counter helper text; only the Name field's helper text
  has a testid so far (Description/Instructions helper text untouched — no
  case has asserted them yet).
- Page object: `automation/pages/generate_skill_modal_page.py`
  (`GenerateSkillModalPage`, extends `GenerateEntityModalPageBase`).
  `set_review_name()`/`set_review_description()`/`set_review_instructions()`
  all use plain `.click()` + `.fill()` — confirmed live this correctly
  triggers React's controlled-component `onChange` (the testid resolves to
  the native `<input>`/`<textarea>` via MUI `slotProps.htmlInput`), unlike
  the general MUI-fill gotcha documented in `.claude/rules/mui-patterns.md`.
- Test file: `automation/tests/ui/skills/test_skill_build_with_ai.py` —
  covers ELITEA-2001 (generation failure/retry), ELITEA-1990 (fields
  editable, create with edits), ELITEA-1991 (create with no edits, keeps
  generated values), ELITEA-1989 (loading text + no extra sections),
  ELITEA-1988 (modal open + static elements), ELITEA-1993 (Name-field
  validation on invalid manual edits, pending implementation).
- Skill cleanup: `SkillAPI.delete_skill(skill_id)` (cookie-auth,
  `automation/api/client.py:1270`) in a `try/finally`; get `skill_id` from
  the post-create redirect URL regex `/skills/all/(\d+)$`. Never use a raw
  `fetch()`-from-page-JS-context DELETE — CORS-fails on this app's DEV
  backend (redirects through a Keycloac forward-auth path with no
  `Access-Control-Allow-Origin`); use the UI delete flow or the API client
  instead.

**Resolved/added during ELITEA-2435 implementation:** the AFS-flagged
`pin-toggle-skill-menuitem` testid gap is now landed —
`SkillControls.jsx`'s `pinMenuItem` spread got the same one-line `key`
fix already used for Credentials (`{ ...pinMenuItem, key:
'pin-toggle-skill' }`, matching `EliteaAI/EliteaUI#569`'s shape), pushed
to `automation/testids` (commit `292fcd02`). `SkillDetailPage` now exposes
`pin_toggle_menuitem` (`LocatorDescriptor(testid="pin-toggle-skill-menuitem")`)
+ `get_pin_toggle_menu_label()` / `click_pin_toggle_menu_item()` (waits on
`POST`/`DELETE .../social/pin/prompt_lib/{project}/skill/{id}`, mirrors
`CredentialDetailPage`'s pin-toggle methods). `SkillsListPage` gained the
list-row pin toggle (pre-existing testid, no gap): `SKILL_PIN_TOGGLE_BUTTON`
template + `pin_toggle_button()` / `get_pin_toggle_label()` /
`click_pin_toggle()`, plus `click_skill_card(name)` (was missing — no prior
skills-list page object exposed a click-through-to-detail method by name).
Existing `open_actions_menu()` (JS-click bypass, waits on
`skill-delete-menu-item`) is reused to open the overflow menu for the
pin-toggle flow — no new "open menu" method needed. Test:
`automation/tests/ui/skills/test_skill_pin_unpin.py`.

## Import — invalid-file validation error (ELITEA-2438) — `useSkillImport.hooks.js`

Distinct from the valid-import round trip (ELITEA-1737/1738, above the
`Concrete Handles` sections of those AFS — not duplicated here).

- Uploading a `.md` file whose frontmatter block IS present but is
  **missing `name` and/or `description`** never opens the "Import
  parameters" dialog. Instead `stageFile()`
  (`useSkillImport.hooks.js:31-63`) shows an error toast and returns
  before the import mutation is ever called — **confirmed live: zero
  `POST .../skill_import/...` requests fire**, validation is 100%
  client-side.
- Error toast reuses the app-wide `toast-alert` (root, carries
  `data-severity="error"`) / `toast-message` (text) testids — **both
  pre-existing, no new testid needed.** `SkillsListPage` currently only
  exposes `import_success_toast_message` (unscoped `toast-message`); it
  does NOT yet have the `toast_alert` / `TOAST_ALERT_SEVERITY` /
  `get_toast_alert(severity)` trio that `ChatPage`
  (`automation/pages/chat_page.py:965-972,1946-1955`) and
  `PipelineDetailPage` already have — implementer should copy that
  pattern onto `SkillsListPage` verbatim rather than add a new testid.
- Exact live message text: `The [<filename>.md] is missing required
  metadata: frontmatter must contain "name" and "description".` — names
  the uploaded filename and both required keys verbatim.
- **`SkillsListPage.import_skill()` is NOT reusable for the invalid-file
  path** — it unconditionally calls `Dialog.wait_for(...)` after upload,
  which times out when no dialog appears. A separate upload-only method
  (click Import + handle file chooser + set file, no dialog wait) is
  needed so both valid- and invalid-file tests can share the upload step.
- Distinct, out-of-scope adjacent case: a `.md` file that doesn't start
  with a valid `---` frontmatter block at all (vs. one that has a
  frontmatter block missing a required key) hits a different parser path
  (`importWizardParser.helpers.js:20-24`) and shows a differently-worded
  `Not supported file [<filename>]: <parser error>` toast — not the same
  code path, not covered by ELITEA-2438.
- No skill entity is ever created by the invalid-file path — confirmed via
  the page-header "Skills: N" stat unchanged (`11` before/after in this
  run) and zero `skill_import` network calls.
  Full details: `test-specs/skills/l3_import-skill-missing-frontmatter_ELITEA-2438.md`.

## Test panel + version instructions (ELITEA-2440) — SkillTestPanel reflects the currently selected version

- **Confirmed live: no testid gaps anywhere in this flow** — create form,
  Save As Version dialog, VERSION dropdown, test panel input/send/response,
  and the delete-confirmation dialog are all already testid'd.
- Create-skill form (`/skills/create`): `skill-name-input-field` /
  `skill-description-input-field` / `skill-instructions-editor-content` /
  `skill-save-button`. Save navigates straight to
  `/skills/all/{skillId}` — **no separate creation-confirmation toast**;
  navigation itself is the confirmation signal (matches
  `test_skill_management.py::TestCreateSkill`).
  Create endpoint: `POST /api/v2/elitea_core/skills/prompt_lib/{project}` →
  `201 Created`.
- **`save_as_version(name)` saves the CURRENT (possibly just-edited)
  instructions-editor content as the new version — `base`'s own stored
  instructions are untouched.** To make a version whose instructions differ
  from `base`, call `fill_instructions(new_text)` BEFORE
  `save_as_version(name)`, not after. Endpoint:
  `POST /api/v2/elitea_core/skill/prompt_lib/{project}/{skillId}` →
  `201 Created`. Toast text confirmed live: `Version "{name}" created`
  (exact match, no variation seen). **`save_as_version()` auto-navigates to
  the newly-created version** — the URL gains the new version's id segment
  immediately, so a subsequent explicit `switch_version(name)` to the
  version you just created is a confirmed-live no-op (safe to call anyway
  for 1:1 step-fidelity with a TMS case, just doesn't change any state).
- Switching versions (`switch_version(name)` / clicking a
  `version-option-{name}` row) re-fetches
  `GET /api/v2/elitea_core/skill/prompt_lib/{project}/{skillId}/{versionId}`
  → `200 OK`, and the instructions-editor content updates to that version's
  stored instructions (confirmed both directions: `v1`'s edited text and
  `base`'s original text both reload correctly after switching away and
  back).
- SkillTestPanel correctly runs against the **currently selected version's**
  instructions, not a stale/cached one — confirmed live with a minimal
  "Always say X" instruction pair (`base`="Always say BASE",
  `v1`="Always say V1"): sending the identical prompt
  ("What should you say?") on each version returned the bare word `"V1"`
  or `"BASE"` respectively, exact match, no other content. Test panel
  testids used: `chat-message-input` / `chat-send-button` (both already
  wired inline in `SkillDetailPage.send_test_message()`) and
  `skill-test-last-response` (`get_last_test_response()`).
- Delete-skill flow (used for this run's cleanup, already
  `SkillDetailPage.delete_skill_via_menu()`): overflow menu
  (`skill-controls-menu-button` → `skill-delete-menu-item`) opens a
  type-to-confirm dialog (`delete-confirm-name-input`, must match the
  skill's exact name to enable `delete-confirm-button`). Delete endpoint:
  `DELETE /api/v2/elitea_core/skill/prompt_lib/{project}/{skillId}` →
  `204 No Content`. **Gotcha:** deleting a skill while its detail page is
  still mid-refetch produces one benign `404` console error on the
  now-stale in-flight `GET .../skill/.../{skillId}/{versionId}` request —
  harmless (fires after the entity is already gone), not a product defect,
  but don't be alarmed if a post-delete console-error check catches it;
  scope the console-error assertion to the case's own steps, not through
  cleanup.
  Full details: `test-specs/skills/l3_test-panel-uses-selected-skill-version-instructions_ELITEA-2440.md`.

## Card view — per-card fields (ELITEA-2428) — `Card.jsx` (shared, `/skills/all`)

- Card view is the **default** view on fresh `/skills/all` load — no click
  needed; the toggle's Card-view button is `[pressed]` immediately.
  Confirmed live via a11y snapshot: no interaction required to see the
  card grid.
- View-toggle buttons carry `agent-*`-prefixed testids
  (`agent-card-view-button` / `agent-table-view-button`) even on the Skills
  page — **not a defect**, `ViewToggle.jsx`'s default prop values, no
  override at `Skills.jsx:70`'s `<ViewToggle />` call site. Same naming
  quirk already documented for `search_input` (`agent-search-input`). Both
  testids on `main`.
- Card fields and their testids: icon = `entity-card-icon` (outer) /
  `entity-card-icon-img` (inner `<img>`) — **on `automation/testids` only**
  (ELITEA-1899, awaiting human cherry-pick to `main`), no page-object field
  on `SkillsListPage` yet (only `AgentsListPage` has one — same shared
  component, straightforward to mirror). Name = `entity-card-name` (on
  main ✓, existing `SkillsListPage.skill_card_name`). Tags =
  `entity-card-tag-chip` (on main ✓, existing
  `SkillsListPage.get_card_tags()`).
- **Description is NEVER shown on the un-hovered card** — it renders ONLY
  inside a hover tooltip (MUI `Tooltip`, `role="tooltip"`, ~1s
  `enterDelay`) triggered by hovering the card's name/title area. Tooltip
  content = two app-owned `<Typography>` nodes (name, then description),
  both inside `Card.jsx`'s own `StyledTooltip` `title` JSX — **confirmed
  live gap: zero `data-testid` on either node**, neither on `main` nor
  `automation/testids`. This is NOT the #579 third-party-render-node
  exception (the JSX is app-owned, MUI's `Tooltip` renders arbitrary
  `title` content verbatim) — a `data-testid="entity-card-description-tooltip"`
  can and should be added directly to the description `Typography` (only
  that one; the sibling name/title node doesn't need one yet since no case
  has asserted it independently of `entity-card-name`). Not yet fixed as
  of this run (ELITEA-2428 analysis) — implementer work via
  `add-data-testid`.
  Full details: `test-specs/skills/l2_skills-card-view-fields_ELITEA-2428.md`.

## Back button (skill editor header) — `back-button` (ELITEA-2429)

- The skill editor's Back button is the shared `BackButton.jsx` component
  (`EliteaUI/src/components/BackButton.jsx`, rendered via `StyledTabs.jsx`'s
  `leftButton` slot) — **pre-existing testid, `data-testid="back-button"`**,
  same element already exposed as `AgentDetailPage.back_button` on the Agent
  detail page. Confirmed live: clicking it from `/skills/all/{id}` navigates
  straight to `/skills/all` (Skills list) — never `/chat`.
- Source-traced root cause of *why* this is a meaningful regression guard
  (not asserted in the test, informational): `BackButton.jsx`'s `onBack()`
  falls back to `gotoListPage()` →
  `NavigationHelpers.getListRouteByPageType(pageType, RouteDefinitions.Chat)`
  whenever `useBackPath()` (`EliteaUI/src/hooks/useBackPath.js`) has no
  `prevPath` for the current route — true for the Skills editor, since
  `useBackPath.js`'s `hasMultiplePaths`/`getPrevPath` have no case for the
  Skills route prefix (unlike Applications/Pipelines/Toolkits/Apps). `Chat`
  is only the **fallback** when `pageType` is unmapped in
  `navigation.helpers.js`'s `pageTypeToListRoute`; that map DOES include
  `SkillDetails: RouteDefinitions.Skills`, so the fallback is never actually
  reached for Skills today — but the code shape for a fallback-to-Chat
  regression genuinely exists (an unmapped `pageType` would hit it), making
  this a real, well-targeted guard.
- **CONFIRMED LIVE GAP, now fixed**: `SkillsListPage.page_header`
  (`testid="skills-page-header"`) was a pre-existing page-object field
  pointing at a testid that did not exist anywhere in EliteaUI src (neither
  `main` nor `automation/testids`) — `Skills.jsx`'s `<StickyTabs>` call never
  passed a `titleTestId` prop, unlike `Applications.jsx` (Agents page),
  which passes `titleTestId="agents-page-header"` to the same shared
  component (`StickyTabs.jsx` already renders `data-testid={titleTestId}`
  unconditionally). Fixed via `add-data-testid`: one-line
  `titleTestId="skills-page-header"` addition to `Skills.jsx`'s
  `<StickyTabs>` call, pushed to `automation/testids` (commit `b29c9b03`).
  This was dead tech debt in the page object (the field had zero other
  usages before this run) — not a new element, just newly exercised.
- Page object additions (additive-only, no existing method bodies touched):
  `SkillDetailPage.back_button` + `click_back_button()` (mirrors
  `AgentDetailPage.click_back_button()` exactly);
  `SkillsListPage.verify_dashboard_header_visible()` +
  `get_skill_card_names()` (mirror `AgentsListPage`'s equivalents).
  Test: `automation/tests/ui/skills/test_skill_back_navigation.py`.
  Full details: `test-specs/skills/l2_skill-editor-back-button-returns-to-skills-list_ELITEA-2429.md`.

## Edit existing skill — Name/Description/Instructions persistence (ELITEA-2431) — `EditSkill.jsx` (`SkillDetailPage`, extends `SkillFormPage`)

- **Confirmed live, no testid gaps.** The detail/edit page reuses every
  field handle already wired on `SkillFormPage` — `skill-name-input-field`,
  `skill-description-input-field`, `skill-instructions-editor-content`,
  `skill-save-button`.
- **The edit-flow Save button is the SAME `skill-save-button` testid as the
  create-flow Save, but a DIFFERENT hook and outcome — do not reuse
  `save_and_wait_for_navigation()` for an edit.** Editing an existing skill
  drives `useSaveSkill.hooks.js`'s `onSave()`: `PUT
  /api/v2/elitea_core/skill/prompt_lib/{project}/{skillId}` (no
  `versionId` segment — updates name/description AND the currently
  selected version's instructions in one call) → `200 OK`, then
  `resetForm()` + `toastSuccess('Skill saved')` — **no navigation**. The
  create-flow's `save_and_wait_for_navigation()` completion check
  (`"/skills/all/" in url and "/create" not in url`) is already true
  *before* the click on a detail page, so calling it for an edit-save
  would return immediately without ever waiting for the PUT — a silent
  false pass, not a real wait.
- New method `SkillDetailPage.save_edits()` added for this (additive-only,
  no existing method body touched): waits on the PUT response
  (URL-ends-with-skillId + method PUT) and the reused `toast-message`
  testid (`SkillDetailPage.version_toast_message`, already wired for the
  Save-As-Version flow) showing exact text `"Skill saved"`.
- Confirmed live: editing Name/Description/Instructions and clicking Save
  persists all three; navigating away (Skills list) and re-opening the
  skill (list card click by its NEW name — `SkillsListPage.
  click_skill_card()`, pre-existing from ELITEA-2435) shows the updated
  values, not the originals.
  Full details: `test-specs/skills/l3_skill-edit-name-description-instructions_ELITEA-2431.md`.

## Instructions Edit/Preview toggle (ELITEA-2432) — `CreateSkillForm.jsx` (`skill-instructions-*`)

- Shared by both `/skills/create` and `/skills/all/{id}` (edit) — same
  `CreateSkillForm.jsx` renders the Instructions accordion's
  summary-action toggle (`TabGroupButton` fed a 2-entry `modeButtons`
  array, `value: 'edit' | 'preview'`, local `useState('edit')` — 100%
  client-side, zero network calls on toggle).
- **CONFIRMED LIVE GAP, now fixed**: neither toggle button nor the
  rendered-preview wrapper `<Box>` had a `data-testid`. `TabButtonItem.jsx`
  (the shared component under `modeButtons`) already spreads
  `{...item.buttonProps}` onto the underlying MUI `ToggleButton`, so the
  fix is caller-side only — `CreateSkillForm.jsx`'s `modeButtons` array
  entries each gained `buttonProps: { 'data-testid': '...' }`; no change to
  the shared `TabButtonItem.jsx`/`TabGroupButton.jsx` components. Fixed via
  `add-data-testid`, pushed to `automation/testids` (commit `b6e1c7c9`):
  `skill-instructions-edit-mode-button`, `skill-instructions-preview-mode-button`,
  and `skill-instructions-preview-content` (the preview wrapper `<Box>`,
  wraps either `<Markdown>{instructions}</Markdown>` or the "No
  instructions yet." empty state).
- Preview renders via the app's shared `Markdown` component (`marked`-based
  lexer, same renderer as chat messages) — confirmed live:
  `**Bold text**` → `<strong>Bold text</strong>`, `- Item one` / `- Item two`
  → a real `<ul><li>` list, both with the raw Markdown syntax characters
  (`**`, `- `) stripped from the rendered/accessible text. This is what
  makes a content-based `text_content()` assertion on the one preview-content
  testid sufficient — no need to address the rendered `<strong>`/`<li>`
  nodes individually (and thus no need for the `#579` scoped-raw-handle
  exception here).
- Switching Edit → Preview → Edit does not mutate the stored/typed Markdown
  source — confirmed live: the CodeMirror content after the round trip is
  byte-identical to what was typed before switching to Preview.
- **Two confirmed-live automation-technique gotchas for MULTI-LINE
  instructions content (single-line instructions, every other caller's
  usage, are unaffected):**
  1. This editor's markdown language mode
     (`@codemirror/lang-markdown`) auto-continues an unordered list on
     Enter — typing `"- Item one\n- Item two"` via
     `page.keyboard.type()` (discrete Enter keydown per `\n`) renders as
     `"- Item one\n- - Item two"` (a real editor UX feature, not a
     product bug). Fix: `page.keyboard.insert_text()` instead of
     `.type()` for the insertion step — one atomic op, no discrete Enter
     keydown, continuation keymap never fires. New method:
     `SkillFormPage.fill_instructions_markdown()`.
  2. `get_instructions()`'s `text_content()` concatenates CodeMirror's
     per-line `<div class="cm-line">` elements with no separator —
     silently flattens multi-line content into one unbroken string. Fix:
     `inner_text()` instead (layout-aware, inserts a newline between
     block-level elements). New method:
     `SkillFormPage.get_instructions_multiline()`.
  3. A blank line (`"\n\n"`) between two content lines produces one EXTRA
     `"\n"` via `inner_text()` (an empty `cm-line`'s inner `<br>` seems to
     contribute its own break beyond the block-separator one) — sidestep
     rather than fight it: use single `"\n"` line breaks in multi-line
     test data. `marked` (the Preview renderer) still parses a list
     correctly without a blank-line paragraph separator.
- Page object: new `SkillFormPage.instructions_edit_mode_button` /
  `instructions_preview_mode_button` / `instructions_preview_content`
  `LocatorDescriptor` fields (Instructions accordion is shared, so these
  live on the base form page like the other Instructions handles) +
  `click_edit_mode()` / `click_preview_mode()` / `get_preview_content()`
  / `fill_instructions_markdown()` / `get_instructions_multiline()`
  methods. `fill_instructions()` / `get_instructions()` / `save_edits()`
  themselves are unchanged (additive-only) — still correct for every
  other caller's single-line instructions.
  Full details: `test-specs/skills/l3_skill-instructions-markdown-edit-preview-toggle_ELITEA-2432.md`.

## Create form — Save-button mandatory-field gating (ELITEA-2430) — `CreateSkillForm.jsx`

- **Confirmed live, no testid gaps.** Every element the case needs
  (`skill-name-input-field`, `skill-description-input-field`,
  `skill-instructions-editor-content`, `skill-save-button`) is already
  wired on `SkillFormPage` — no `add-data-testid` round-trip needed.
- Save-state gating (`Name` and `Description` both required, `Instructions`
  required but held constant/filled throughout the case) is 100%
  client-side, synchronous Formik/yup validation
  (`skillValidationSchema.validation.js`) — confirmed live, zero network
  calls fire on field edit; the Save button's `disabled` attribute flips
  immediately.
- Per-field MUI helper text ("Name is required" / "Description is
  required") renders live but carries **no `data-testid`**
  (`CreateSkillForm.jsx`'s `helperText={formik.touched?.x && formik.errors.x}`
  — a plain MUI helper-text string, not a dedicated node like the
  Build-with-AI review form's `review-name-helper-text`). Out of scope for
  ELITEA-2430 — the case only asserts the Save button's enabled/disabled
  state, never the helper text's content, so no testid was requested.
- **Page-object gap (implementer work, not a testid gap):**
  `SkillFormPage` has `set_description()` (click + `select_text()` +
  Backspace + type — reliably clears a *populated* field) but no
  symmetric `set_name()`. `fill_form()`'s internal `_fill_text_input()`
  (Ctrl+A + type) does NOT reliably clear a populated field to empty (an
  empty `type("")` after Ctrl+A leaves the field's prior value in place).
  ELITEA-2430 needs to clear a *populated* Name field (case step 6) — add
  `SkillFormPage.set_name(name: str)` mirroring `set_description()`
  exactly.

## Tags — add/remove on an existing Skill (ELITEA-2433) + multiple tags on create+edit (ELITEA-2434)

- **Tags field validation — hyphens are REJECTED, confirmed live.**
  `TagEditor.jsx` → `AutoCompleteDropDown.jsx` validates every freeSolo tag
  value against `NormalTagNameInputRegExp = /^[\w,\s]+$/g` (input-level
  error state) and, decisively, `onChangeMulti` filters the committed value
  against `NormalSingleTagNameInputRegExp = /^[ \t]*[\w]*[ \t]*$/g`
  (`EliteaUI/src/common/constants.js:92-93`) before adding it to the tag
  list — both allow only word chars (letters/digits/underscore), comma,
  whitespace. Typing `regression-v1` + Enter clears the input but adds
  **no chip** (silently filtered, zero network calls). `regression_v1`
  (underscore) commits normally. This is case-text drift for ELITEA-2433's
  literal test data (case says `"regression-v1"`) — filed as a
  CLARIFICATION, not a bug: `EliteaAI/elitea-testing-public#1445`. Use
  `regression_v1` in automation. Sibling pattern to issue #20 (Skill
  *Name* field — opposite direction: Name REQUIRES hyphens/kebab-case,
  Tags FORBIDS them).
- **CONFIRMED LIVE GAP — tag-chip delete icon has no testid.**
  `AutoCompleteDropDown.jsx`'s `renderValue()` supports a `chipDeleteTestId`
  prop (function or string, same pattern as `chipTestId`/`getOptionTestId`)
  on the MUI `Chip`'s `deleteIcon` (`RemoveIcon`), but
  `CreateSkillForm.jsx`'s `<TagEditor>` call site (`skill-tags-input`
  section, ~line 249) never passes it — only `chipTestId="skill-tag-chip"`
  and `getOptionTestId` are wired. The rendered delete `<img>`/SVG inside
  each committed-tag chip is therefore unaddressable by testid today.
  Fix (`add-data-testid`, one-line, mirrors the existing
  `getOptionTestId={option => 'skill-tag-option-${option?.name}'}` shape):
  add `chipDeleteTestId={option => 'skill-tag-chip-delete-${option?.name}'}`
  to the same `<TagEditor>` call site. Dynamic testid, name-keyed (same
  convention as `SKILL_TAG_OPTION`). **Confirmed live: only the delete
  icon itself removes the tag — clicking elsewhere on the chip (its label
  text / the chip body) does NOT** (verified directly: a click centered on
  the chip button, away from the icon's bounding box, left the tag intact
  and Save stayed disabled; a click on the icon's own `<img>`/SVG node
  removed it and dirtied the form). MUI's `onDelete` only wires to the
  `deleteIcon` sub-element, not the whole `Chip`. **Workaround confirmed
  live in the meantime (until the fix lands):** scope to the specific
  chip via `page.get_by_test_id("skill-tag-chip").filter(has_text=tag_name)`
  then click that chip's only child element (the icon `<img>`/SVG,
  addressed positionally — no other child exists inside a `skill-tag-chip`
  node) — not a `#579` scoped-raw-handle exception (this is 100%
  app-owned JSX, addressable via `add-data-testid`), just the interim
  shape.
- **Edit-flow tag add/remove round-trips through `SkillDetailPage.save_edits()`**
  (existing method, PUT `.../skill/prompt_lib/{project}/{skillId}` → 200,
  "Skill saved" toast, no navigation) — same mechanism as any other field
  edit. No new endpoint.
- **Create-flow: Tags field is available and committable BEFORE the first
  Save** (confirmed live — `/skills/create`'s `CreateSkillForm.jsx` renders
  the same `TagEditor` pre-save; tags added pre-save ride the `POST
  .../skills/prompt_lib/{project}` payload's top-level `tags` field intact).
  Adding MORE tags after the skill exists (edit mode) uses the same PUT as
  above — confirmed live, all 4 tags (2 pre-save + 2 post-save) persist
  through a full page navigate-away-and-back reload, not just client state.
- **Skill card + list-level tag rendering**: `SkillsListPage.get_card_tags()`
  / `CARD_TAG_CHIP` (`entity-card-tag-chip`) already covers "tag appears on
  the card" / "tag no longer appears on the card" assertions — no new
  page-object work needed there, reused as-is from ELITEA-1740.
- Test files: `automation/tests/ui/skills/test_skill_tag_add_remove.py`
  (ELITEA-2433), `automation/tests/ui/skills/test_skill_tag_multiple.py`
  (ELITEA-2434) — pending implementation.
  Full details: `test-specs/skills/l3_add-save-remove-skill-tag_ELITEA-2433.md`,
  `test-specs/skills/l3_multiple-tags-persist-on-creation-and-edit_ELITEA-2434.md`.
  Full details: `test-specs/skills/l3_skill-creation-mandatory-fields-validation_ELITEA-2430.md`.

## Test panel — model selector + Model Settings dialog (ELITEA-2436)

The Skill test panel (`SkillTestPanel.jsx`) embeds the SAME
`NewChatInput`/`llm-model-selector` shared widget the Agent detail page
uses (ELITEA-1880) — **confirmed live: every testid ELITEA-1880 added to
that shared widget resolves correctly on `/skills/all/{id}` with zero new
`add-data-testid` work**, even though `SkillDetailPage` has no
model-selector/model-settings methods yet (new page-object surface, not an
extension of `AgentDetailPage`'s):

- `model-selector-button` / `model-selector-name` — model picker trigger +
  current-name display. Dropdown options: `model-selector-option-{name}`
  (dynamic, API `name` suffix — same 12-model catalog as agents/pipelines).
- `model-settings-button` (aria-label `"model settings menu"`, gear icon)
  → opens `model-settings-dialog` (MUI dialog, title "Model settings").
- Dialog contents are MODEL-TYPE CONDITIONAL
  (`model?.supports_reasoning ? <ReasoningSlider/> : <CreativitySlider/>`,
  `LLMSettings.jsx:119`):
  - Reasoning-capable model (e.g. `gpt-5.2`, `Anthropic Claude 4.5 Sonnet`)
    → `model-settings-reasoning-slider`, 3 discrete positions
    `model-settings-reasoning-level-{1,2,3}`, rendered labels lowercase
    `low`/`medium`/`high`.
  - Non-reasoning model (e.g. `gpt-5-mini`) → Creativity slider instead,
    **NO testid** on this branch (`CreativitySlider.jsx` never got the
    `testId` prop-threading `ReasoningSlider.jsx` did) — `add-data-testid`
    gap: `model-settings-creativity-slider`, same
    `DiscreteSlider.jsx`-threading pattern. Underlying range input in the
    meantime: `[aria-label="Creativity level"]`.
  - `model-settings-max-tokens-section` — always rendered regardless of
    model type (Default/Custom toggle).
  - `model-settings-capabilities-section` — chips per model capability
    (`Reasoning`, `Image analysis`; a model can show both).
  - `model-settings-cancel-button` / `model-settings-apply-button` — **NEW
    FINDING (2026-08-11, ELITEA-2436 run): Apply now HAS a testid.** At
    ELITEA-1880 analysis time it did not (`agent_detail_page.py`'s
    `model_settings_*` comment block explicitly says "Apply button
    intentionally has NO testid here... do not add unless a future case
    needs it") — someone added it since. `AgentDetailPage` has no
    `LocatorDescriptor` field for it yet; back-fill when convenient.
- **Discrete-slider interaction — MUI quirk, confirmed live:** clicking the
  visual `<span class="MuiSlider-thumb">` directly times out (intercepts
  pointer events over the underlying `<input type="range">`). Working
  pattern: `page.locator('[aria-label="<Slider> level"]').focus()` then
  `page.keyboard.press("ArrowRight"/"ArrowLeft")` — mirrors
  `user_profile_settings_page.py`'s `set_speed()`
  (`automation/pages/user_profile_settings_page.py:690-714`). A value
  change enables the dialog's Apply button.
- **Model selection + Settings-dialog edits are pure client-side state on
  the Skill test panel — ZERO network calls** (confirmed via
  `browser_network_requests` across a full run: no `PUT`/`PATCH` to the
  skill entity). Different from the Agent detail page instance, where a
  real Save PUTs the change to the entity — the Skill test panel has no
  persistent "Save" for these settings at all, so **any existing skill is
  safe to reuse for this kind of case** without disposable-fixture/cleanup
  concerns.
  Full details: `test-specs/skills/l3_llm-model-settings-configurable_ELITEA-2436.md`.
  Clarification filed: [EliteaAI/elitea-testing-public#1447](https://github.com/EliteaAI/elitea-testing-public/issues/1447)
  (step 2's "gpt5-mini ... reasoning slider" case-text drift — gpt-5-mini
  isn't reasoning-capable; sibling of ELITEA-1880's Clarification 1 on the
  Agent detail page).
