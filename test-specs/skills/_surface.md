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
