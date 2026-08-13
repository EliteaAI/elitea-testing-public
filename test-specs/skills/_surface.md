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

## Subagent skill isolation (ELITEA-2608) — nested-accordion chip is the deterministic signal

- **The isolation mechanism itself is correct, confirmed live twice.** A
  subagent invoked via the master's "+ Agent" Tools attach (`agent-add-agent-button`)
  only ever shows ITS OWN attached skill's `chat-answer-tool-chip`
  (`"Skill: {skill-name}"`) inside ITS OWN nested accordion details
  (`chat-answer-nested-agent-accordion-details-{agent_name}`, ELITEA-1951's
  existing testids/methods) — the master's skill never appears there, and a
  skill-free subagent's nested details container shows zero
  `chat-answer-tool-chip` elements.
- **Confound to avoid when writing this style of test: an unconditionally-
  triggered master-level skill can fire on the master's OWN top-level turn,
  independent of subagent delegation, and visually confuses the
  whole-message-text signal.** If the master agent has its OWN skill attached
  (as this case's Test Data requires) and that skill's description has no
  scoping condition ("Format all output in UPPERCASE" reads as "always" to the
  LLM), the master can autonomously invoke it on a turn that ALSO delegates to
  a subagent — producing an all-uppercase final rendered message even though
  the subagent's own nested execution stayed correctly skill-free. This chip
  shows up in the OUTER thought-accordion region (sibling to the nested
  accordion's summary heading), NOT inside the nested details container — that
  placement IS the disambiguator. **Fix: give skill descriptions used in this
  kind of multi-agent test a narrow, intent-scoped trigger** (mirroring
  ELITEA-2607's `"Use this skill ONLY when..."` convention), and always assert
  isolation via the nested-accordion chip (deterministic) rather than the
  whole-message text (confoundable) as the PRIMARY signal.
  Full details: `test-specs/skills/l3_subagent-skills-isolation_ELITEA-2608.md`.

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
  validation on invalid manual edits, pending implementation), ELITEA-1996
  (Back to prompt returns to input step, preserves prompt text, no
  draft-data leak — pending implementation; `back_button` was previously
  never referenced anywhere in this test file).
- **`back_button` (`generate-skill-back-button`) — ELITEA-1996 confirmed live.**
  Wired to `handleBack()` in the SAME shared `GenerateEntityModal.jsx` the
  Agent modal uses (entity-agnostic component, no skill-vs-agent branching):
  resets `step` to INPUT and clears `draftData`, but never clears
  `description` — the prompt text survives the Back click verbatim, and
  none of the review-form field testids remain in the DOM afterward. Zero
  new network requests (`generate_skill_draft`/`skills/prompt_lib` both
  unchanged) and zero console errors across the round trip. Identical
  mechanism to ELITEA-1919 (Agent entity) — see
  `test-specs/agents/l2_build-with-ai-back-to-prompt-returns-to-input-step-preserves-text_ELITEA-1919.md`
  for the shared source-level triangulation. Full AFS:
  `test-specs/skills/l2_build-with-ai-back-to-prompt-returns-to-input-step-preserves-text_ELITEA-1996.md`.
- **`cancel_button` (input step) and `close_button` (review step) — ELITEA-1997/1998
  confirmed live.** Same `GenerateEntityModal.jsx` shell/mechanics as the Agent
  entity's ELITEA-1917/1918 pair — see `test-specs/agents/l2_build-with-ai-cancel-*`
  for the source-level `renderActions()` proof; not re-traced here since the
  component is identical, only entity-specific testids differ.
  - **Input step**: clicking `generate-skill-cancel-button` (previously only
    `.is_visible()`-checked by ELITEA-1988) closes the modal, leaves
    `skill-name-input-field`/`skill-description-input-field` empty, fires
    **zero** `generate_skill_draft`/`skills/prompt_lib` requests. No
    confirmation interstitial.
  - **Review step has NO "Cancel" button** — only "Back to prompt"
    (`generate-skill-back-button`) and "Create Skill"
    (`generate-skill-approve-button`); confirmed live via accessibility
    snapshot of the open dialog. The modal's Close (X) icon
    (`generate-skill-close-button`) is the only control that discards a
    generated draft without creating a skill — previously `.click()`ed only
    as unasserted cleanup (the naming-rules test, ELITEA-1992's test class).
    **Case-text drift filed**: [#1486](https://github.com/EliteaAI/elitea-testing-public/issues/1486)
    (sibling of the Agent-entity #1318) — the TMS case ELITEA-1998 says
    "Click Cancel" for this step; no such button exists.
  - Confirmed live this run with a real, unmocked draft (`name:
    "support-ticket-digest"`): closing via the X icon fires zero
    `skills/prompt_lib` CREATE POSTs, and the draft's name never appears in
    the Skills list afterward.
  - Zero console errors across both flows this run (unlike the Agent
    entity's documented `disableUnderline` baseline-noise warning — no
    equivalent fired for the Skill review form this run).
  Full details: `test-specs/skills/l2_build-with-ai-cancel-from-prompt-step-closes-modal-without-creating-a-skill_ELITEA-1997.md`,
  `test-specs/skills/l2_build-with-ai-cancel-from-review-step-does-not-create-a-skill_ELITEA-1998.md`.
- **RBAC gating (ELITEA-1986/1987, confirmed live):** `generate-skill-open-button` is gated by
  `PERMISSIONS.applications.update` — `GenerateSkillButton.jsx` passes it into the shared
  `GenerateEntityButton.jsx`, the SAME gate/permission as the Agents "Build with AI" button
  (`GenerateAgentButton.jsx`). Confirmed live this run: button renders with text "Build with AI"
  for `${TEST_USER}` (admin-equivalent) on project `399`. Editor/viewer-role halves are **not**
  live-verifiable — no `EDITOR_TEST_USER_*`/`VIEWER_TEST_USER_*` credential exists in
  `.env.test`/`profile.md`, tracked in `EliteaAI/elitea-testing-public#1314` (opened for the Agents
  analog ELITEA-1903/1904; ELITEA-1986/1987 hit the identical gap on this second entity type — do
  not re-file, comment on #1314 instead).
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

**Generated-name naming-rule compliance (ELITEA-1992, confirmed live).**
Every sibling Build-with-AI test in `test_skill_build_with_ai.py` mocks
`generate_skill_draft` with an analyst-chosen, already-compliant `name` —
none of them prove the **real** AI/backend output is well-formed. Live,
unmocked generation this run (`POST generate_skill_draft/prompt_lib/399`
→ `200`) returned `name: "english-to-spanish-feedback"` — confirmed
byte-identical between the raw API response body and the review form's
`generate-skill-review-name-input.input_value()` (no client-side
sanitization step exists between the two; compliance is enforced upstream
of `validateSkillDraft()`, not merely by it). Matches the source regex
already documented above (`^[a-z0-9]([a-z0-9-]*[a-z0-9])?$`, ≤64 chars via
native `maxlength`). **A test for this case must NOT mock the draft
response** — mocking a pre-chosen compliant name would make the assertion
tautological instead of proving anything about actual AI output.
Full details: `test-specs/skills/l2_generated-skill-name-adheres-to-naming-rules_ELITEA-1992.md`.

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

## Copy Link / Share (ELITEA-2439) — `SkillControls.jsx` (`share-version-menuitem` / `share-skill-menuitem`)

- **Confirmed live, no testid gaps.** `SkillControls.jsx` wires the exact same
  `useCopyLinkMenu()` hook the Agent flow uses (ELITEA-1898) — two "Share" menu
  items inside the `skill-controls-menu-button` overflow menu:
  `share-version-menuitem` (VERSION group, `useProjectEntityLink({ versionId:
  currentVersionId })` → URL gains `/{versionId}`) and `share-skill-menuitem`
  (SKILL group, no `versionId` override → generic skill URL, no version
  segment). Confirmed live via a11y snapshot of the open menu on skill 951
  (`content-reviewer`) — both items present and clickable.
- Confirmation toast: same `toast-message`/`toast-alert[data-severity="info"]`
  mechanism, exact text `"The link has been copied to the clipboard."`
  (source-confirmed, `useCopyLinkMenu`'s `handleCopy()` → `toastInfo(...)`) —
  identical string to the Agent flow's ELITEA-1898/#1288 toast.
- Direct navigation to a skill+version URL (confirmed live:
  `/skills/all/951/979?viewMode=owner`) opens the correct skill (tab title +
  selected tab both show the skill name, Information panel shows matching
  Skill ID/Version ID) — no "not found"/404 state.
- **`SkillDetailPage` has no page-object fields for either Share menuitem
  yet** — implementer work (additive `LocatorDescriptor`s), no `add-data-testid`
  round trip needed.
- **Gotcha:** the base version's Information-panel "Version ID" can differ
  from the Skill ID even though the URL shows only one digit segment while on
  `base` (confirmed live: skill 951 shows Version ID 979 in the Information
  panel while its URL is just `/skills/all/951`) —
  `SkillDetailPage.get_version_id()`'s URL-only parsing returns the skill id
  for `base`, not the true version id. Not a bug for THIS case (it only
  matters for a **named**, non-base version, where the URL always carries the
  real version id as its second digit segment), but a trap for any future case
  that wants "the base version's real version id" — read it from the
  Information panel's `Copy version ID` button text instead of the URL in
  that specific scenario.
  Clarification filed: [EliteaAI/elitea-testing-public#1451](https://github.com/EliteaAI/elitea-testing-public/issues/1451)
  (case text says a standalone "Copy Link" button — live product has two
  separate "Share" menu items instead; sibling of #1288/ELITEA-1898 and
  #1337/ELITEA-2049, same pattern, different entity).
  Full details: `test-specs/skills/l2_copy-link-copies-valid-url-to-correct-skill-version_ELITEA-2439.md`.

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

## SkillTestPanel does NOT create a Chat conversation (ELITEA-2441) — confirmed live

- Running a prompt through the SkillTestPanel produces **zero** requests to
  any `elitea_core/conversations*` endpoint — confirmed via
  `browser_network_requests` across a full create-skill + send-test-message
  + wait-for-response cycle. The only "conversation"-shaped traffic seen is
  the unrelated `support_assistant/conversations/` widget (Support Bot, not
  Chat) plus the skill's own `elitea_core/skills*`/`elitea_core/
  skill_categories*` calls.
- **Two ground truths for "conversation count", confirmed to agree exactly:**
  `ConversationAPI.list_conversations()` (`{"total": int, "rows": [...]}`,
  fixture `conversation_api` in `automation/fixtures/api_fixtures.py:115`)
  and the Chat sidebar's DOM count of `ChatPage.CONVERSATION_ITEM_PREFIX`
  (`'[data-testid^="chat-conversation-item-"]'`) — both read `1` (same
  conversation id `7929`) before and after a full skill-create +
  test-panel-run + skill-delete cycle, in a project (`Private`/399) with a
  dozen leftover `ELITEA2459RenameTest`/`ABC` **folders** cluttering the
  sidebar.
- **Gotcha — don't count sidebar `<button>`/`<heading>` elements broadly.**
  Those leftover folders render as `heading > button` pairs in the a11y
  snapshot and look, at a glance, like a much larger conversation list (~2
  dozen buttons). They are folders, not conversations — `ChatPage`'s own
  `get_conversation_list_items()` (a pre-testid-policy `:has(h6) > button`
  CSS selector, tracked tech debt) would very likely miscount here too.
  Always scope conversation-count assertions to the testid-based
  `CONVERSATION_ITEM_PREFIX`/`CONVERSATION_ITEM` constants, never a raw
  structural selector or a bare visual count.
  Full details: `test-specs/skills/l3_test-panel-does-not-create-new-chat-conversation_ELITEA-2441.md`.

## Test panel response action buttons — Read aloud / Copy to clipboard (ELITEA-2442) — `ApplicationAnswer.jsx` (shared with Chat)

- **Confirmed live, no testid gaps** — both buttons already carry testids on
  the SAME shared `ApplicationAnswer.jsx` component the Chat `ChatBox.jsx`
  uses (per the ELITEA-2436 precedent above: SkillTestPanel embeds the same
  message-rendering tree). `chat-read-out-button` (aria-label `"Read out"`)
  and `chat-copy-button` — both resolve to exactly one element scoped to the
  last (AI) response.
- **Gap is page-object wiring, not testids**: `ChatPage` already exposes
  these as `read_out_button` (`chat_page.py:526`) and `copy_action_button`
  (`chat_page.py:481`), but `SkillDetailPage` (extends `SkillFormPage`, no
  shared base with `ChatPage`) has neither field yet — implementer adds
  both, mirroring `ChatPage`'s exactly.
- **Enabled-state gating, source-confirmed**: Read out disables on
  `VOICE_FEATURES_TEMPORARILY_DISABLED || isProcessing || !realAnswer ||
  !!speakingMessageId`; Copy disables on `isProcessing || !realAnswer`. Both
  clear the instant a response finishes streaming — confirmed live via
  `.disabled === false` on both testids once `wait_for_test_response()`
  completes.
- **Voice features are ON by default on localhost**: `VOICE_FEATURES_ENABLED`
  defaults `true`, `VOICE_FEATURES_TEMPORARILY_DISABLED` defaults `false`
  (`common/constants.js`, both env vars unset in `EliteaUI/.env`) —
  confirmed live via the test-panel input bar's "enter speaking mode" /
  "start voice input" controls rendering, and the Read-out button rendering
  at all (it's conditionally rendered on `VOICE_FEATURES_ENABLED`, not just
  disabled).
- **Click-through, not just `disabled` state, confirmed live**: clicking
  `chat-copy-button` produces the toast `"The message has been copied to
  the clipboard."`; clicking `chat-read-out-button` opens
  `chat-voice-mini-player` (pre-existing `ChatPage.voice_mini_player`
  `OptionalLocatorDescriptor`) with a live `chat-voice-play-stop-button`.
  Both actions are 100% client-side — zero network requests fired by either
  click (confirmed via `browser_network_requests`).
- **Don't match "Copy to clipboard" by text/role** — the user's own message
  row ALSO renders a same-labelled "Copy to clipboard" button
  (`UserMessage.jsx`, inline `title` prop) but with NO `chat-copy-button`
  testid — a text-based selector would be ambiguous; the testid scopes
  correctly to just the AI response.
  Full details: `test-specs/skills/l3_test-panel-response-actions-enabled_ELITEA-2442.md`.

## Fork wizard — skill entity (ELITEA-2602/ELITEA-2603)

- **Skill Fork reuses the SAME shared `ImportWizardModal`/`IWModal*` tree
  Agent Fork (ELITEA-1893) and Pipeline Fork (ELITEA-2051) already use** —
  literal `agent-` prefix on nearly every handle is naming tech debt, not
  entity scoping. Confirmed live, zero new testids needed for the wizard
  body itself: `agent-import-preview-dialog` / `agent-import-complete-dialog`,
  `agent-import-wizard-project-select-combobox`, `select-option-{projectId}`
  (dynamic), `agent-import-preview-name`, `agent-import-preview-card-toggle`,
  `agent-fork-confirm-button`, `agent-import-complete-got-it-button`.
- **Only the Fork MENUITEM is entity-scoped, and it's NOT the shared
  `ForkEntityButton.jsx`/`useForkEntityMenu()` hook Agent/Pipeline/Toolkit
  use.** `SkillControls.jsx` implements Fork as its own menu item
  (`key: 'fork'`, wired via a dedicated `useForkSkill()` hook that still
  dispatches into the same shared `importWizard` Redux slice) — confirmed
  via source read. Result: the skill Fork menuitem's testid is the GENERIC
  `fork-menuitem` (not `agent-actions-fork-menuitem`/
  `pipeline-actions-fork-menuitem` — those come from the shared hook's
  `FORK_MENU_ITEM_KEY_BY_ENTITY` map, which Skill never uses). Still unique
  and functionally sufficient within the skill controls menu (only one Fork
  item), just don't assume naming parity with Agent/Pipeline when writing
  new tests.
- **The Fork wizard's "Main entity" card NEVER shows Tags** — confirmed
  live via DOM text-content check with two tags present on the source. Only
  Name, "Type: {entity}", Description, Instructions render. Same omission
  applies to Agent/Pipeline Fork (their AFS/memory files never document
  tags in the preview either) — consistent shared-component behavior, not
  a skill-specific gap. Filed as clarification (case-text overstatement,
  ELITEA-2602 step 7 promised "tags, etc."):
  https://github.com/EliteaAI/elitea-testing-public/issues/1455.
- **Version-scoped Fork**: forking a NON-base version correctly captures
  THAT version's instructions/tags (confirmed via `skill_export_fork` GET
  firing with the active version's id, and the resulting fork's
  `meta.parent_version_id` pointing at the SOURCE's non-base version id,
  not its base version id). The forked copy's own version is always named
  `"base"` in the target project regardless of which source version was
  forked — confirmed live (`versions` array has exactly one entry,
  `name: "base"`).
- **Icon is preserved by reference, not re-uploaded per fork** — the
  forked skill's `meta.icon_meta.url` is byte-identical to the source's
  (same file path under the SOURCE project's `skill_icon/{sourceProjectId}/`
  folder), confirmed live across a cross-project fork (399→400). Not a
  defect — the icon renders correctly in the target project regardless of
  which project's storage path it physically lives under.
- **Skill icon upload — the two gaps below were FIXED during ELITEA-2602's
  implementation** (`skill-form-icon-button`/`skill-form-icon-img` and
  `agent-icon-picker-upload-button` all confirmed LIVE and in active use by
  `SkillFormPage` as of ELITEA-2604's analysis run, 2026-08-12 — do not
  re-add or re-request them):
  1. ~~`EntityIcon` in `CreateSkillForm.jsx` passes no `data-testid`~~ — FIXED,
     `skill-form-icon-button`/`skill-form-icon-img` live on both
     `/skills/create` and `/skills/all/{id}` (same shared component, both
     modes confirmed).
  2. ~~`SelectIconDialog.jsx`'s Upload `IconButton` has no testid~~ — FIXED,
     `agent-icon-picker-upload-button` live (entity-agnostic, shared dialog).
  3. Same TWO-CLICK quirk as the Agent icon avatar (first click only mounts
     the hover-triggered edit-pencil overlay; second click actually opens
     the dialog) — confirmed live, same as
     `.agents/memory/qa-engineer/agent_form_dual_component_and_icon_picker_quirks.md`,
     automation-only artifact, not a product defect. Still applies as of
     2026-08-12.
  4. **NEW GAP found during ELITEA-2604 (icon upload/validation case,
     2026-08-12), NOT yet fixed**: the per-uploaded-icon delete `IconButton`
     inside `UserIconItem.jsx`
     (`../EliteaUI/src/[fsd]/features/settings/ui/project-general/general/
     select-project-icon/UserIconItem.jsx`) has NO `data-testid` at all —
     only a non-unique `className="deleteButton"`. It's hover-revealed
     (`visibility:hidden` → `visible` on `:hover`, the button IS in the DOM
     the whole time). Needed for automating "delete an uploaded icon"
     (reverts to default if it was the selected one, confirmed live —
     `DELETE .../upload_skill_icon/prompt_lib/{project}/{icon_name}` → 200).
     Recommended fix: forward a `deleteButtonTestId` prop from
     `SelectIconDialog.jsx`'s existing per-item
     `data-testid={`agent-icon-picker-uploaded-${index}`}` call site →
     `agent-icon-picker-uploaded-{index}-delete-button`. Full detail:
     `test-specs/skills/l2_skill-custom-icon-upload-and-validation_ELITEA-2604.md`
     Part D step 17.
  5. **The "Default" tile (`agent-icon-picker-default-icon`) is a SECOND,
     already-testid'd revert-to-default mechanism** distinct from deleting
     an uploaded icon — in edit mode it fires
     `PUT .../upload_skill_icon/prompt_lib/{project}/{versionId}` with
     `{name: "", url: ""}`, toast "The icon has been reset to default icon"
     (vs the delete path's "The icon has been successfully deleted."). Both
     confirmed live to revert `skill-form-icon-img` to ABSENT (no `<img>`
     element — the live product's default state, NOT a literal
     `skill-icon.svg` file reference despite what some case text says), and
     both confirmed to persist across a full page reload.
  6. **Create mode vs edit mode upload persistence differs** (case-relevant
     for any icon-upload test, not just ELITEA-2604): create mode (no
     `entityId` yet) fires ONE `POST .../upload_skill_icon/prompt_lib/
     {project}` → 200 and applies the icon to local form state only (persists
     when the skill itself is saved). Edit mode (entityId present) fires the
     SAME `POST` (still 200) **followed by** a second `PUT
     .../upload_skill_icon/prompt_lib/{project}/{versionId}` → 200 that
     applies+persists the icon to that skill version immediately,
     independent of the main Save button (which stays disabled after an
     icon-only edit-mode change — same mechanism as `AgentDetailPage`/
     ELITEA-1899). A test asserting the upload-success toast text must
     account for this: create mode shows exactly one toast ("The image has
     been uploaded"); edit mode shows that toast followed by a second one
     ("The icon has been changed") from the replace call.
  7. **The oversized-file (>500KB) rejection is 100% server-side** — no
     client pre-flight size check exists in `useUploadSkillIconMutation`.
     Confirmed live: `POST` with a ~1.25MB valid PNG → **400 Bad Request**,
     body `{"error": "File size exceeds 512 KB"}` (note: the picker
     dialog's own tooltip says "less than 500KB" — same limit, inconsistent
     unit-label string, cosmetic only). The dialog stays open and the
     previous icon is retained (unchanged `skill-form-icon-img` src) on
     rejection.
- **Cross-project direct-URL navigation 404s** — `GET
  .../skill/prompt_lib/{currentlySelectedProjectId}/{skillId}` uses the
  SIDEBAR's currently-selected project, not any project encoded in the
  visited URL path (`/skills/all/{id}` carries no project segment). A test
  navigating between a fork's source and target projects MUST switch the
  sidebar project selector (`project-selector-trigger-combobox` →
  `select-option-{projectId}`) BEFORE navigating to a detail page in the
  other project — confirmed live (a naive direct nav 404s and shows a
  blank/error state).
- **Tags field silently rejects hyphens** (see
  `skill_tags_field_hyphen_rejected_and_chip_delete_icon_only.md` for the
  full regex detail) — reconfirmed for THIS case's literal test data
  (`test-tag`, `fork-demo`, `v2-tag` all rejected; `enhanced` accepted, no
  hyphen). The Create-Version dialog's Name field does NOT share this
  restriction — `v2-enhanced` (with hyphen) is accepted there, confirmed
  live. Don't assume all text fields on the skill surface share one
  validation ruleset.
- **Custom skill icon renders consistently across all 5 UI surfaces that show a
  skill** (ELITEA-2605, 2026-08-12, confirmed live end-to-end with one
  freshly-uploaded icon): Skills list card, Skill detail/edit page, Agent
  "+ Skill" SkillMenu attach-dropdown, Agent SKILLS-section `SkillCard`, and the
  chat/instructions `~mention` autocomplete. All five render the byte-identical
  uploaded-icon `src` — no product defect, but only 2 of the 5 have a usable
  testid chain today:
  - **List card**: `entity-card-icon-img` (inner `<img>`) EXISTS (ELITEA-2428)
    but has no `SkillsListPage` field yet — page-object plumbing only, no
    `add-data-testid` needed.
  - **Detail page**: `skill-form-icon-img` fully wired already (ELITEA-2602/2604).
  - **SkillMenu dropdown item, Agent SkillCard, mention-autocomplete item — ALL
    THREE have zero `data-testid` on the icon `<img>` itself**, confirmed via
    source read: `SkillMenu.jsx`, `SkillCard.jsx`
    (`src/[fsd]/features/skill/ui/SkillCard.jsx`), and `MentionSkillList.jsx`
    each independently implement the SAME `icon_meta?.url ? <EliteAImage/> :
    <SkillIcon/>` ternary with no testid prop on either branch — three separate
    JSX call sites of one shared pattern, each needs its OWN fix (not one shared
    testid). Recommended names: `skill-menu-item-icon-img`, `skill-card-icon-img`,
    `skill-mention-item-icon-img` (custom-icon branch only — leave `SkillIcon`
    untagged, per the same-element-conditional-pair "only the used branch is
    named" convention). Full detail:
    `test-specs/skills/l2_skill-custom-icon-visibility-across-ui_ELITEA-2605.md`.
  - Note: `EliteAImage` (`src/components/EliteAImage.jsx`) DOES accept a
    `data-testid` prop already — it's the three call sites above that never pass
    one, not a limitation of the shared image component itself.

## Custom icon persists across "Save As Version" (ELITEA-2606) — confirmed live

- **The "create version" endpoint copies `meta.icon_meta` forward into the
  new version at creation time — server-side, not a client-state
  carryover.** Confirmed via the `POST /api/v2/elitea_core/skill/
  prompt_lib/{project}/{skillId}` response body itself (fired by
  `SkillDetailPage.save_as_version()`): the new version's `meta.icon_meta`
  is present in that SAME response, `url` byte-identical to the base
  version's icon, before any subsequent GET/reload. Verified further by a
  full hard reload of the new version's URL (`/skills/all/{skillId}/
  {newVersionId}`) — `skill-form-icon-img`'s `src` unchanged, ruling out
  "looked persisted only because the client never re-fetched" as a false
  positive.
- **The base version's icon is unaffected** by creating a new version —
  switching back to `base` after creating `v2` shows the identical icon
  `src`, confirmed live (not merely assumed from "nothing touched it").
- **Same `meta.icon_meta` shape and "preserved by reference" guarantee as
  Fork** (ELITEA-2602/ELITEA-2603, above) — but a DIFFERENT endpoint. Fork's
  copy happens via `skill_export_fork`; Save-As-Version's copy happens via
  the plain `POST skill/prompt_lib/{project}/{skillId}` "create version"
  call. Corroborating precedent, not the same code path — don't assume a
  fix/regression in one automatically implies the same for the other.
  Full detail:
  `test-specs/skills/l3_skill-custom-icon-persistence-on-save-as-version_ELITEA-2606.md`.
- **No testid gaps** — every element this flow touches (`skill-form-icon-
  img`, `skill-save-as-version-button`, `skill-create-version-dialog`/
  `-name-input-field`/`-save-button`, `skill-version-select`(-combobox),
  `version-option-{name}`, `toast-message`) is pre-existing, reused from
  ELITEA-1738/ELITEA-2437/ELITEA-2604 rework.
- **`SkillAPI.get_skill(skill_id)` cannot target a specific version's icon**
  — it always hits the bare `/skill/prompt_lib/{project}/{skillId}`
  endpoint (no `versionId` segment). An API-level per-version assertion
  needs a small additive extension (optional `version_id` param appending
  `/{version_id}` to the URL) — not yet added as of this run; the DOM-level
  `skill-form-icon-img` src read is sufficient and was this run's primary
  evidence.

## Publish wizard — skill entity (ELITEA-2595/ELITEA-2596/ELITEA-2598) — `PublishWizardModal.jsx` (shared with agents, `entityLabel="skill"`)

Confirmed live (skills 1560/1561/1562/1563/1564, project 399). The wizard
is the SAME `entities/version/ui/PublishWizardModal.jsx` component the
agent Publish flow uses (ELITEA-1892, `test_agent_publish_unpublish_version.py`)
— `entityLabel="skill"` swaps copy only; every `agent-publish-*` testid is
reused verbatim for skills (not agent-scoped despite the literal name —
existing product naming, not something to "fix" via `add-data-testid`).

- **Trigger is a MENU ITEM, not a standalone button** — skill detail page's
  overflow ("Skill" ⋮) menu → VERSION group → "Publish". Testid
  `publish-menuitem` — constructed at RUNTIME as `${item.key}-menuitem` by
  `DotMenu.jsx` (`SkillControls.jsx` sets `key: 'publish'` on the menu-item
  object at the call site) — **not a literal string anywhere in JSX**, so a
  plain `git grep -- "publish-menuitem"` finds nothing; verify by reading
  `SkillControls.jsx`'s `key: 'publish'` line + `DotMenu.jsx`'s
  `` data-testid={testId ? `${testId}-menuitem` : undefined} `` instead of
  grepping the literal string. `skill-controls-menu-button` opens the menu.
- **3-step wizard**: Preparation (version name + category + Publishing
  Terms checkbox) → Validation (AI/deterministic content check) → Publishing.
  Reuse `agent-publish-version-name-input`, `agent-publish-category-select-
  combobox` (+ dynamic `select-option-{category}`), `agent-publish-agree-
  checkbox` (role-based `checkbox[name="I agree with the Publishing Terms."]`
  resolves it — has the `agent-publish-agree-checkbox` testid per
  `PreparationStep.jsx` source, MCP's role locator just doesn't surface it
  in generated code), `agent-publish-continue-button`, `agent-publish-
  confirm-button` ("Publish" on the Validation step).
- **Validation endpoint**: `POST .../publish_skill_validate/prompt_lib/
  {project}/{skillId}/{versionId}` — `422` when `status: "FAIL"`, `200`
  when `status: "WARN"` or `"PASS"`. Response body:
  `{status, critical_issues[], warnings[], recommendations[], counts,
  summary, ai_validation_available, validation_token}`. Each issue entry
  carries `"source": "deterministic"` (rule-based, reproducible) or
  `"source": "ai"` (LLM-generated wording — same underlying detection is
  reliable across runs but exact phrasing may vary; assert on `field` +
  membership in `critical_issues`/`warnings`, not exact wording, for
  `source: "ai"` entries).
- **Deterministic CRITICAL gates confirmed** (any one of these alone ⇒
  `status: "FAIL"`, Publish button disabled — `canPublish = status !==
  'FAIL'` in `PublishWizardModal.jsx`):
  - `icon` — "No custom icon set" — **confirmed CRITICAL, not WARN**,
    contradicting ELITEA-2598's premise (filed as clarification #1463).
  - `tags` — "No tags defined" (skill has zero tags).
  - `description` — "Description is too short (min 50 chars)".
  - `instructions` — "Instructions are too short (min 100 chars)".
  (Live thresholds: description 50 chars, instructions 100 chars — NOT the
  "100 characters" the ELITEA-2595/2596/2598 case text uses for both
  fields.)
- **AI-sourced CRITICAL gates confirmed** (also block, `source: "ai"`):
  placeholder-text markers (`[replace this]`, `TODO:`) in description OR
  instructions; hardcoded secrets/API-keys/passwords in instructions.
- **WARN-level (does NOT block)**: generic/placeholder-like name (e.g.
  literal `"skill"`) — `source: "ai"`; "description lacks action verbs" —
  `source: "deterministic"`.
- **Happy-path prerequisite gap vs ELITEA-2595's Test Data**: description/
  instructions ≥ the thresholds above is NOT sufficient — the skill also
  needs a custom icon AND ≥1 tag, or Validation returns FAIL (confirmed:
  same 100+-char content, no icon/no tag ⇒ 2 critical issues; add 1 tag ⇒
  1 critical issue (icon only, still FAIL); add icon too ⇒ `WARN`, Publish
  enabled). Icon upload reuses `SkillFormPage.upload_skill_icon_edit_mode()`
  (ELITEA-2604) — pick any existing gallery entry (project-scoped
  "Uploaded" tab) to skip a fresh file upload.
- **Known defect #614 (agent Publish, `ELITEA-1892`) REPRODUCES for skills
  too**: after a successful `publish_skill` (200), the VERSION dropdown
  does not auto-select the newly published version — it stays showing
  `base` until the dropdown is opened and the new version name is picked
  explicitly (confirmed live: skill 1560, dropdown showed `base` active
  post-publish, `v1.0 - <date>` present but not selected). Automation must
  re-select by name after Publish, exactly as `AgentDetailPage.
  select_version_by_name()` already does — do not assert on auto-navigation.
- **Catalog verification**: published skill appears under `/elitea-catalog
  ?tab=skills`, grouped by its selected Category (`catalog-skills-tab`
  testid switches the tab; confirmed skill card renders with its custom
  icon and under the "Quality Assurance" category group after publishing
  with that category).
- **Known defect #611 (agent Publish, Stepper icon console warnings)
  likely reproduces too** (same `PublishWizardModal.jsx` Stepper) — not
  independently re-verified against the console this run; treat as the
  same signature if seen (`SvgCheckedIcon` + "non-boolean attribute"/"does
  not recognize the" text), per `test_agent_publish_unpublish_version.py`'s
  existing filter.

### `validation_token` mechanics — invalidation-on-modify + 5-min TTL (ELITEA-2597)

Confirmed live end-to-end this run (skill 1579/version 1663, `publish_skill`/
`publish_skill_validate` — both direct-API and real two-tab UI repro):

- `validation_token` (from `publish_skill_validate`'s response) is a
  colon-delimited opaque 4-part string: `<base64 sig>:<version_id>:<hex
  hash>:<unix timestamp>` — the trailing segment IS the token's issuance
  Unix time (cross-checked against wall-clock `date -u +%s` at capture,
  twice, both matched to within ~1s). Treat as fully opaque in automation —
  never parse/reconstruct.
- **Modified-after-validation**: `publish_skill` with a token whose skill
  version changed since issuance → `400`
  `{"error": "validation_token_invalid", "msg": "Agent was modified since
  validation. Please re-validate."}` — note the **"Agent" wording bug on the
  Skill flow**, filed as
  https://github.com/EliteaAI/elitea-testing-public/issues/1465 (MINOR,
  cosmetic only — mechanism itself is correct).
- **TTL expiration**: confirmed **300s (5 min) exactly**, matching the case
  text. `publish_skill` with an unmodified skill but a token older than 300s
  (confirmed with a 330s real wait) → `400`
  `{"error": "validation_token_invalid", "msg": "Validation token expired.
  Please re-validate before publishing."}` — same `error` code as the
  modified-content case, **different `msg`**, so automation must assert on
  `msg` text, not just `error`/status code, to distinguish the two causes.
- Both errors render inline in the wizard's Validation-step summary area
  (same node the WARN/PASS summary already occupies — no new testid needed)
  and disable the "Publish" button; the wizard does NOT auto-reset to
  Preparation or auto-refire validation — user must Cancel and reopen.
  Full details: `test-specs/skills/l2_skill-publishing-token-invalidation-and-ttl-expiration_ELITEA-2597.md`.

## Unpublish + republish lifecycle, version coexistence (ELITEA-2599) — `UnpublishConfirmModal.jsx` (shared with agents, `entityLabel="skill"`)

Confirmed live end-to-end this run (skill 1595, project 399).

- **Trigger**: overflow (⋮) menu → VERSION group → "Unpublish" — testid
  `unpublish-menuitem`, same runtime-constructed `${item.key}-menuitem`
  pattern as `publish-menuitem` (`SkillControls.jsx` sets `key: 'unpublish'`
  at the call site — `useUnpublishSkillMenu.hooks.jsx`'s `canUnpublish` gate
  requires `versionStatus === Published`, so this menu item only appears
  when viewing a Published version, never the draft `base`).
- **Confirm dialog**: `UnpublishConfirmModal.jsx`, title "Unpublish Skill",
  body (non-admin/no-reason branch, confirmed verbatim): "Are you sure you
  want to unpublish {name} (version: {version})? The skill will be removed
  from ELITEA Catalog immediately. Existing conversations using this skill
  version may be affected." Confirm button testid
  `agent-unpublish-confirm-button` — **same cross-entity naming artifact as
  `agent-publish-*`** (component hardcodes this testid regardless of the
  `entityLabel` prop it receives) — not a defect, matches the already-
  accepted Publish-side pattern.
- **Endpoint**: `POST unpublish_skill/prompt_lib/{project}/{skillId}/
  {versionId}` → `200 {msg: "Successfully unpublished", status: "deleted"}`.
  Invalidates the SAME RTK tags as `publishSkill`
  (`TAG_TYPE_PUBLIC_SKILLS`/`TAG_TYPE_PUBLIC_SKILL_DETAILS`) — Catalog
  reflects the removal on a fresh navigation, no reload/wait needed.
- **Post-unpublish, the version is fully re-editable/re-publishable** — the
  overflow menu flips back to showing "Publish" (not "Unpublish") the
  moment `versionStatus !== Published`. No separate "restore" flow exists;
  republish is a normal Publish-wizard pass on the same version.
- **`public_skill_id` behavior is the crux of "version coexistence" — read
  carefully, this is easy to get backwards:**
  - Publish → Unpublish → Republish (of the SAME or a different version of
    the same skill) allocates a **brand-new `public_skill_id`**. Unpublish
    is a real deletion (`status: "deleted"`) of that catalog entity, not a
    toggle. Confirmed live: `v1.0` published → `public_skill_id=51` →
    unpublished → `v2.0` published (different version, same underlying
    skill 1595) → `public_skill_id=52` (NEW, not 51 reused).
  - Publishing a SIBLING version of the same skill **while an existing
    published version stays live (never unpublished)** REUSES the same
    `public_skill_id` and only allocates a new `public_version_id`. This
    is the actual coexistence mechanism the TMS case means by "up to 3
    versions can coexist". Confirmed live: with `v2.0` live at
    `public_skill_id=52, public_version_id=56`, publishing the skill's
    `base` draft as `v3.0` (WITHOUT unpublishing v2.0 first) produced
    `public_skill_id=52, public_version_id=57` — same 52. A further `v4.0`
    (published from the previously-unpublished `v1.0`'s now-reusable
    version) produced `public_skill_id=52, public_version_id=58` — still
    52, bringing the total to 3 coexisting versions (56/57/58) under one
    public entry. No rejection or cap enforcement was observed publishing
    up to 3 coexisting versions this way.
  - A true "4th version beyond 3 coexisting" publish was NOT exercised
    (turn-budget boundary this run) — unconfirmed whether the platform
    enforces a hard cap at that point or keeps accepting them. The TMS
    case's own language for this edge is non-prescriptive ("handled
    appropriately"), so don't treat an accepted 4th-beyond-3 publish as a
    defect without a more specific spec to check it against.
- **Catalog card**: one card per ACTIVE `public_skill_id`, testid
  `catalog-skill-card-{public_skill_id}` (confirmed `catalog-skill-card-52`
  live). Opening it shows only the current (latest-published) content —
  no version-history/selector UI exposed to Catalog viewers. "Only latest
  shown" is therefore a structural property (one entry, not a filtered
  list of many), not something the test computes by comparing versions.
- **Agent-attachment independence (EntitySkillMapping)**: read (not
  independently re-executed live this run — see the AFS's Coverage Map
  Axis 2 gap) — `ApplicationSkills.jsx`'s `useGetApplicationSkillsQuery`
  keys an agent's attached skills by project-scoped `skill_id` alone, with
  no dependency on that skill's Catalog/publish status anywhere in the
  query or its cache tags. Attaching a skill to an agent should therefore
  survive an unpublish of that skill untouched — implementer must still
  assert this live, the code reading is strong evidence, not a substitute.
- **Transient infra flakiness observed, not a product defect**: one
  `publish_skill_validate` call 502'd, then 503'd, then succeeded on a 3rd
  immediate retry with no code-side change — in the same window,
  unrelated `socket.io` polling also 502/503'd and a CORS failure hit
  `dev.elitea.ai` directly. Treat an isolated 502/503 on this endpoint as
  environment noise (bounded retry acceptable), not evidence against the
  coexistence claim — but don't silently swallow a REPEATED failure.
  Full details: `test-specs/skills/l3_skill-unpublish-republish-lifecycle_ELITEA-2599.md`.

## Agent publish with attached Skills — embedded, not independently catalog-listed, visible in thought process (ELITEA-2600)

Confirmed live end-to-end this run (agent 9131 `multi-skill-agent-2600`,
skills 1605/1606/1607, project 399). Distinct flow from the Skill-entity
Publish wizard above — this is the **AGENT** Publish wizard
(`ELITEA-1892`'s `PublishWizardModal.jsx`, `entityLabel="agent"`) exercised
on an agent that has 3 Skills attached.

- **Agent-publish validation ALSO inspects each attached skill's own
  content — new information beyond ELITEA-1892's AFS** (which only
  exercised agents with zero attached skills). `POST publish_validate/
  prompt_lib/{project}/{versionId}`'s `critical_issues[]` includes a
  `field: "skills"` entry — `"skills [skill: <name>]: Skill content is too
  short (min 100 chars)"` — when ANY attached skill's instructions are
  under 100 chars, blocking the whole AGENT's publish (not just that
  skill). Confirmed live: skill `summarizer-2600` at 84 chars produced this
  Critical issue; lengthening to 179 chars cleared it (`Critical: 0`).
  Seed all attached skills' instructions ≥100 chars to avoid this in
  automation.
- **Publishing Terms text confirms the case's core premise verbatim**
  (Preparation step, "1 - Exclusions Notice" section): *"Exception:
  attached Skills and sub-agents are not stripped — their instructions
  are embedded in the published agent. Retained Skills are never listed
  as separate entries in the catalog."* — a platform-documented guarantee,
  not just inferred behavior.
- **Confirmed functionally, not just per the disclosure text**: after
  publishing, `/elitea-catalog?tab=skills` search for each attached
  skill's name returns **"No skills found"** — the skills are NOT
  independently searchable/listed, even though the agent that embeds them
  IS published and visible under `/elitea-catalog?tab=agents` (grouped by
  its selected Category, same `catalog-agent-card-{id}` /
  `catalog-category-heading-{slug}` pattern as any other published agent).
- **Skill invocation in the "Thought for N secs" accordion reuses the
  SAME `chat-answer-tool-chip` testid already documented above (Test panel
  section) for external toolkit calls** — confirmed live for a genuinely
  different text shape: `"Skill: {skill_name}"` (e.g. `"Skill:
  word-counter-2600"`), NOT the `"{toolkit_name}: {tool_name}"` shape the
  page object's docstring currently describes for toolkit chips. Skills
  hardcode `toolkitName` to the literal string `"Skill"` under the hood.
  Confirmed for TWO separate skills in the same conversation
  (`word-counter-2600` → response `"Word count: 10"`;
  `format-uppercase-2600` → response fully upper-cased) — both produced
  their own `chat-answer-tool-chip`, and the accordion auto-expands by
  default (no separate "expand" click is needed to see it, contra the
  case text's step 12 implying a manual expand action).
- **`~<skill-name>` mention mechanics**: typing `~` opens the
  `skill-mention-list` popper immediately (no debounce); the reusable
  `ChatPage.send_message_with_skill_mention()` page-object method already
  handles this correctly via `press_sequentially` throughout — **do NOT
  use `.fill()` for the trailing prompt text**, it replaces the whole
  textbox value and destroys the inserted mention chip (confirmed by
  hitting this live in this run: a `fill()` after selecting the mention
  silently reset the message to plain text with no `~mention`, and the
  skill did not fire).
  Full details: `test-specs/skills/l2_agent-with-skills-publishing-flow_ELITEA-2600.md`.

## Agent-level publish validation — per-skill attribution + Agent-vs-Skill token invalidation (ELITEA-2601)

- **`publish_validate`'s Critical-issue rules for attached skills are INDEPENDENT per
  rule, not one combined "content quality" check.** Confirmed live: a skill with SHORT
  content AND placeholder text produces TWO separate `critical_issues[]` entries, both
  prefixed `skills [skill: <name>]:` — `"Skill content is too short (min 100 chars)"`
  and `"Skill content contains placeholder text"` — not one merged message. A skill
  with clean, valid content shows up ONLY in the non-blocking `Suggestions` section
  (never Critical/Warning) — the correct way to assert "no errors for this skill".
- **Removing an attached skill entirely (not just fixing its content) also clears its
  Critical issues on re-validation** — confirmed live: `Critical: 2` → remove the
  offending skill (`AgentDetailPage.remove_skill()`, already exists) → re-open the
  Publish wizard (always starts a FRESH empty Preparation step, never resumes) →
  `Critical: 0`, Publish enabled.
- **`skill-card-remove-button` testid is NOT unique across attached-skill cards** — it
  repeats per card; scope it inside the card's own `[data-testid="skill-card-{id}"]`
  container. Hover-revealed (`aria-label="remove skill"`), confirmation dialog reuses
  the generic `delete-confirm-button` testid.
- **The AGENT-entity publish-token-invalidation mechanism exists and mirrors the SKILL
  entity's (ELITEA-2597), but with a DIFFERENT `error` code.** Confirmed live: holding
  a validated (`Critical: 0`) Publish wizard open in one tab, then attaching a skill to
  the SAME agent version in a second tab, then clicking Publish in the first tab →
  `400 {"error": "validation_failed", "msg": "Agent was modified since validation.
  Please re-validate."}`. ELITEA-2597's AFS documents `"validation_token_invalid"` for
  the analogous SKILL-entity case — **the two entities use different `error` codes for
  the same underlying "stale token" condition**; assert on both `error` and `msg`, not
  `msg` alone. The `msg` text itself ("Agent was modified...") is CORRECT here (it's a
  real agent) — this also explains why ELITEA-2597's Skill flow shows the SAME
  "Agent"-worded message as a (separately filed, MINOR, #1465) copy-paste artifact: the
  shared `PublishWizardModal.jsx`/backend validator is agent-first and was never
  re-templated for the Skill entity.
- Reuses the SAME `publish-wizard-error-alert` testid ELITEA-2597's implementer added
  (`EliteaAI/EliteaUI@2dafb537`, shared component) — confirmed live it renders
  unmodified for the Agent flow too, no new testid needed.
- **Second-tab navigation to an agent's config/Skills panel MUST include
  `?destTab=configuration&viewMode=owner`** — a bare `/agents/all/{id}` URL lands on
  the Chat tab instead, silently hiding the Skills section a test needs.
- **Not yet confirmed live**: whether *removing* a skill in the second tab (rather than
  attaching one) triggers the identical `400 validation_failed` invalidation — the
  mechanism is very likely the same (`remove_skill()` persists immediately, same as
  `attach_skill()`, which IS confirmed to trigger it), but this run's attempt was
  confounded by reusing an already-invalid skill as the attach/detach probe (produced
  a real `Critical: 2` FAIL instead of a clean stale-token scenario). Next analyst/
  implementer touching this flow: seed a dedicated, content-VALID third skill for the
  attach/detach probe to isolate this cleanly.
  Full details: `test-specs/skills/l2_agent-with-skills-validation-attribution-and-token-invalidation_ELITEA-2601.md`.

**Resolved during ELITEA-2601 implementation (test-automation-engineer):**
- **The removal direction IS confirmed** — seeding a THIRD, dedicated, content-valid
  `extra-skill` for the attach/detach probe (as suggested above) removed the confound:
  attaching it (2nd tab) → `400 validation_failed` in the 1st tab (addition direction,
  as already documented); restart validation → `Critical: 0` again (extra-skill
  content-valid) → REMOVE it (2nd tab) → attempt Publish (1st tab) → the SAME
  `400 {"error": "validation_failed", "msg": "...modified since validation..."}`. Both
  directions of the mechanism are now live-confirmed, not just inferred.
- **Gotcha, also affects this flow (already documented for ELITEA-2600 in the section
  above):** the AGENT's own `instructions` field is independently subject to the same
  ≥100-char "too short" Critical rule a skill's content is — an agent instructions
  fixture under 100 chars adds a 3rd, agent-level `critical_issues[]` entry
  (`context: None`) alongside the 2 skill-attributed ones this case's Part A targets,
  breaking a `counts.critical == 2` assertion. Seed the agent's own instructions at
  ≥100 chars too. (This AFS's own Test Data section originally claimed
  Description/Instructions are "Warning-level gates only, not Critical" — that claim
  is WRONG for Instructions and has been corrected in the AFS file itself.)
- **Menu-item attach-by-name gotcha (new, not previously documented on this surface):**
  `Popper.select_menuitem_by_testid()` resolves via `.filter(has_text=name).first` — a
  SUBSTRING match. Seeding a "valid-skill-<x>" and an "invalid-skill-<x>" in the SAME
  test means attaching "valid-skill-<x>" ambiguously matches BOTH menu items (the
  second contains the first as a literal substring) and silently attaches the WRONG
  one — no error, just a downstream assertion failure. Pick skill-fixture names with no
  substring containment between any pair (e.g. "valid-skill"/"broken-skill", not
  "valid-skill"/"invalid-skill"). Full detail:
  `.agents/memory/test-automation-engineer/popper_select_menuitem_substring_collision_attaches_wrong_item.md`.

## Published/embedded agent version — immutability mechanism (ELITEA-2614)

- **Two distinct enforcement mechanisms on a locked version — don't assume one covers both.**
  General-section fields (Name/Description/Instructions/Tags) are **NOT disabled/read-only** on a
  published version — they stay freely editable, and `Save` re-enables the moment you type. The lock
  is enforced server-side: `PUT /api/v2/elitea_core/application/prompt_lib/{project}/{agent_id}`
  returns `400 {"error": "Version id {versionId} is published and can not be updated"}`. Skill/Tool
  attachment controls (Steps 14-19 of ELITEA-2614), by contrast, ARE disabled pre-emptively via a
  client-side `isVersionLocked = versionStatus === 'published' || versionStatus === 'embedded'` prop
  (`ApplicationSkills.jsx`/`ApplicationTools.jsx`) — no request fires at all when blocked this way.
- **Tooltip coverage for "why disabled" is inconsistent — confirmed, filed as
  [#1470](https://github.com/EliteaAI/elitea-testing-public/issues/1470) (MINOR).** The Tools
  section's 4 add buttons (`ToolMenu.jsx`'s `lockedTooltip`, exact text "This agent version is
  published and can not be modified") and the Skill "+Skill" add button (`SkillMenu.jsx`, "...or
  embedded...") correctly show an immutability tooltip when disabled. `SkillCard`'s remove button
  (`skill-card-remove-button`, pre-existing testid — confirmed present, do NOT re-add it) keeps a
  static, unconditional "Remove skill" tooltip even when locked; `SkillVersionSelector`'s trigger
  (`skill-version-selector-trigger-{skill_id}`, pre-existing) has **no `Tooltip` wrapper at all**.
  Assert the correct 3 hard, the missing 2 soft + `# Known defect: #1470`.
- **Failed Save does not auto-revert the form.** After a rejected edit (400), the input keeps showing
  the rejected value until `Discard` is clicked — and `Discard` itself opens a confirm dialog ("Are
  you sure you want to discard changes?", `discard-confirm-button`) before reverting. Don't assume a
  failed Save silently resets state between per-field assertions.
  Full details: `test-specs/skills/l2_published-agent-version-cannot-be-modified_ELITEA-2614.md`.

## Autonomous skill invocation + thought-process visibility (ELITEA-2607)

- **`agent-add-skill-button` is now on-main, confirmed live.** The ELITEA-1735
  AFS (2026-07-14 pass) logged this as a gap ("no testid, recommend
  `add-data-testid`"). Confirmed live 2026-08-12: the button IS wired
  (`data-testid="agent-add-skill-button"`) — the UI team added it since that
  earlier pass. Stop citing the ELITEA-1735 gap note for this element; use the
  testid directly.
- **Skill invocation is visible in the thought process as a `chat-answer-tool-chip`
  reading `"Skill: {skill-name}"`.** `ActionView.jsx`
  (`../EliteaUI/src/components/Chat/ActionView.jsx:196-217`) special-cases
  `action.toolMeta.toolkit_name === 'skills'`: the chip title becomes
  `` `Skill${separator}${loadedSkillName}` `` instead of the usual
  `"{toolkit}: {tool}"` form. Confirmed live: attaching one skill to a fresh
  agent and sending a message matching that skill's description trigger (no
  `~mention`) produces a `"Thought for N secs"` accordion (auto-expanded) whose
  chip row reads exactly `"Skill: {skill-name}"` next to the model chip. Existing
  page-object handles (`AgentDetailPage.CHAT_ANSWER_THOUGHT_ACCORDION_SELECTOR` /
  `CHAT_ANSWER_TOOL_CHIP_SELECTOR`, `automation/pages/agent_detail_page.py:189-191`)
  already scope correctly — no new testid needed for this assertion.
- **Autonomous (V2, no `~mention`) invocation and the plain-message
  non-invocation path both already work correctly live** — same mechanism
  ELITEA-1735's merged test already exercises
  (`automation/tests/ui/skills/test_skill_agent_interaction.py`). Re-confirmed
  this run on a fresh single-skill topology (not just the merged test's
  two-skill topology).
- **Unattached skills are never invoked — confirmed live, no defect.** Created a
  second skill with a distinctive canary-marker instruction (a string that could
  ONLY appear in the response if that skill's own instructions fired), left it
  unattached, then sent an adversarial prompt explicitly inviting it by name/intent
  ("...use your translator skill if you have one"). Result: no
  `chat-answer-tool-chip` for the unattached skill anywhere in the thought
  accordion; response opens with "I don't have a translator skill available...";
  canary marker never appears. **Gotcha for anyone writing this assertion**: don't
  use a plausible real transform (e.g. an actual translation) as the unattached
  skill's instructions — a correct real transform is indistinguishable from the
  base LLM answering the same prompt with ZERO skill involvement, so it can't
  prove non-invocation either way. Use an unmistakable canary marker instead.
  Full details:
  `test-specs/skills/lextend_skill-autonomous-invocation-core-functionality_ELITEA-2607.md`.

## Explicit `~mention` + autonomous context-match on the SAME message — no double-injection (ELITEA-2609)

- **Confirmed live, no defect.** Sending `~{skill-name} {text that ALSO
  independently matches that skill's own description trigger}` — i.e. an
  explicit mention AND a context match co-occurring on one message — invokes
  the skill exactly ONCE: exactly one `chat-answer-tool-chip` reading
  `"Skill: {skill-name}"` inside the outer `chat-answer-thought-accordion`,
  and a single, clean, non-duplicated response (no repeated/concatenated
  output block). Explicit mention does not "stack" with a coincidental
  autonomous trigger match.
- **Assertion shape that actually falsifies double-injection**: assert
  `get_outer_thought_accordion().locator(CHAT_ANSWER_TOOL_CHIP_SELECTOR)` has
  `.count() == 1` (not merely `.to_be_visible()` — a duplicate-invocation
  defect would still leave "a chip visible" true even with 2 chips present).
  Also prefer a markdown/structured skill transform (heading + list) over a
  flat prose transform (e.g. plain uppercase) as the deterministic-transform
  test data for this specific assertion — a double-injection defect on a
  structured response shows up as a duplicated heading/list block, which is
  far more visually/structurally distinctive than "still all-uppercase"
  (compatible with either 1 or 2 invocations on a prose transform).
  Full details:
  `test-specs/skills/lextend_skill-explicit-autonomous-invocation-coexistence_ELITEA-2609.md`.

## Agent-attached skill: SELECTING a non-base version actually changes chat behaviour (ELITEA-2610)

- **New ground vs ELITEA-1789**: that AFS's skill only ever had ONE saved
  version (`base`), so it confirmed the version-selector trigger/menu render
  and open correctly, but never confirmed that clicking a non-base
  `skill-version-option-{name}` menu item (a) actually re-PATCHes the
  attachment, or (b) changes the AGENT's live-chat behaviour when the skill is
  autonomously invoked. Both confirmed live this run, 3/3 (casual →
  technical → base), with the change taking effect on the VERY NEXT chat
  turn — same conversation, no page reload, no new chat, no explicit
  agent-level Save.
- **All three `skill-version-selector-trigger-{skill_id}` /
  `skill-version-selector-menu-{skill_id}` / `skill-version-option-{version_name}`
  testids are now `on-main ✓`** (promoted since the ELITEA-1789 rework, which
  recorded them as `automation/testids`-only). Re-verify PROVENANCE fresh on
  your own run regardless — this is a snapshot, not a standing guarantee.
- **Real click required, same gotcha as ELITEA-1789**: an accessibility-tree/
  `ref=`-resolved click on the trigger still silently no-ops (issue #46's a11y
  half, `tabIndex=-1`/no ARIA role, reconfirmed live this run). Use a real
  Playwright/CDP click (or `browser_evaluate` + `querySelector(...).click()`)
  on the testid-scoped element.
- **Gotcha for deterministic assertions**: don't use the case's literal
  subjective tone descriptions ("formal"/"casual with emojis"/"technical") as
  the skill's actual instructions — "is this response casual" isn't a
  scriptable assertion. Use a `"Start every response with the exact tag
  [X-STYLE]:"` marker-tag instruction per version (mirrors ELITEA-2440's
  `"Always say BASE"` pattern) so the automated assertion is an exact-prefix
  check, not a vibe check.
- **No page-object method exists yet to CLICK a specific version option** —
  only open/read/close the menu (`open_skill_version_selector`,
  `get_versions_menu_item_names`, `close_versions_menu`). The
  `SKILL_VERSION_OPTION_SELECTOR` template constant (`agent_detail_page.py:259`)
  is already defined but never called from a public method — implementer adds
  `select_skill_version(skill_name, version_name)`.
  Full details:
  `test-specs/skills/l3_skill-version-selection-behavior_ELITEA-2610.md`.

## Edit with AI (skill editing, not creation) — `/skills/all/{id}` → `AIEditSkillModal`

- **Shared shell, skill-specific wiring.** `entities/edit-entity-with-ai/`
  (`EditEntityButton`/`EditEntityModal`/`EditEntityComparisonLayout`/
  `EditEntityStepIndicator`/`GeneralStep`/`InstructionsStep`/`TextDiffHighlight`)
  is the SAME shell consumed by Skill (`features/skill/ui/ai-edit-skill-modal/`),
  Agent (`features/agent/ui/ai-edit-agent-modal/`), and Project Context
  (`features/settings/ui/project-context/ai-edit/`) — Edit-with-AI, distinct
  from the "Build with AI" skill-CREATION flow documented above (different
  button: `edit-skill-with-ai-button` vs `generate-skill-open-button`;
  different endpoint call shape — see below).
- Trigger: `edit-skill-with-ai-button` (sparkle-icon button next to
  Name/Description in `CreateSkillForm`'s `summaryEditAction` slot,
  `EditSkill.jsx:241`). Modal: `ai-edit-skill-modal`. Prompt-phase testids
  (`ai-edit-skill-prompt-input`/`-generate-button`/`-cancel-button`/
  `-close-button`/`-error-alert`/`-loading-indicator`) all pre-existing,
  on-main.
- Loading text confirmed live: **"Generating skill draft..."**.
- Wizard has up to 3 steps computed by
  `features/skill/lib/helpers/skillAIEditionSteps.helpers.js:computeVisibleSteps()`:
  General (Name+Description) shown if either changed OR nothing changed at
  all; Instructions shown if it changed OR nothing changed; **Summary is
  ALWAYS shown** (last step, `EDIT_STEP_KEYS.SUMMARY`). "Nothing changed"
  branch exists so the wizard doesn't just vanish when the AI echoes the
  input back unmodified — not yet exercised by any case as of this run.
- Each step: `EditEntityComparisonLayout` renders CURRENT (read-only) /
  SUGGESTED (contentEditable, per-field "Apply changes" checkbox, **checked
  by default**) columns. `TextDiffHighlight.jsx` computes a word-level diff
  and renders added/removed segments as styled spans — CSS-only, no testid on
  the segments (first-party code, not a #579 exception if you want to assert
  the highlight itself — see the AFS's Automation Hints for why the data-level
  "text differs" assertion is preferred instead).
- **UPDATE (ELITEA-2612 run, superseding the "zero testid coverage" note
  below as of this run):** the wizard-phase gap WAS fixed for ELITEA-2611 —
  the step indicator, all 3 "Apply changes" checkboxes, Previous/Next/Save,
  and the 3 Summary-step inputs are now wired and on `main`
  (`EliteaAI/EliteaUI@cddfd6d4`, fix-round-1 additions
  `EliteaAI/EliteaUI@3e1e5c73`). **Still unwired: "Refine Prompt" and "Save as
  Version"** — `AIEditSkillModal.jsx`'s `<EditEntityModal>` call site leaves
  `refinePromptButtonTestId`/`saveAsVersionButtonTestId` unset (canon #511:
  ELITEA-2611 never clicked either control, so wiring them then would have
  been an orphan testid). ELITEA-2612 DOES exercise "Refine Prompt" (its
  "Back" equivalent — there is no separate "Back" button, confirmed via
  source read) — see `l3_edit-with-ai-navigation-error-handling_ELITEA-2612.md`
  § Concrete Handles for the exact prop-wiring + naming
  (`ai-edit-skill-wizard-refine-prompt-button`). "Save as Version" remains
  unwired/unexercised as of this run — original text preserved below for
  the historical "zero coverage" framing, now stale in its "no testid on
  ANY of" claim but still accurate on which specific 2 controls are gapped.
- ~~**CONFIRMED LIVE GAP — the entire wizard PHASE has zero testid coverage.**
  Only the prompt phase (table above) is wired. No testid on: the step
  indicator ("1. General"/"2. Instructions"/"3. Summary"), any of the 3
  "Apply changes" checkboxes, the 4 wizard-footer buttons (Refine Prompt /
  Previous / Next / Save / Save as Version — 5 buttons, Save+SaveAsVersion
  both only on the last step), or the 3 Summary-step merged-value inputs.
  Full component/prop/testid-name breakdown:
  `test-specs/skills/l2_edit-with-ai-skill-happy-path_ELITEA-2611.md` §
  Concrete Handles. Not yet fixed as of this run — implementer work via
  `add-data-testid`, threaded the same `xxxTestId`-prop way the prompt phase
  already is.~~ *(superseded — see UPDATE above)*
- **Wizard-phase-only-has-Close, no-Cancel (ELITEA-2612 finding).**
  `EditEntityModal.jsx`'s `renderActions()` — which renders the "Cancel"
  button (`ai-edit-skill-cancel-button`) — returns `null` whenever
  `phase !== PHASES.PROMPT`. Once generation succeeds and the wizard phase is
  reached, "Cancel" no longer exists in the DOM at all; the ONLY dismissal
  control from that point on is the modal-level Close (X),
  `ai-edit-skill-close-button`. A case asking to "Cancel or close the wizard"
  from a wizard step must use Close, not Cancel.
- **"Refine Prompt" (`handleRefinePrompt`) preserves the prompt text;
  "Close"/"Cancel" (`handleClose`, and the `!open` effect) do NOT — confirmed
  live (ELITEA-2612).** Both handlers reset `phase`/`draftData`/
  `activeStepIndex`; only `handleClose` additionally resets `description`
  (the prompt state) and calls `resetGenerate()`. This asymmetry is
  intentional per the case's own intent (Refine Prompt lets you tweak and
  resend the SAME prompt; Cancel/Close abandons the whole attempt) — not a
  bug either way it currently isn't.
- **Generation-failure error text is genuinely the backend's own message,
  round-tripped verbatim** (`generateError?.data?.error ||
  generateError?.data?.detail || 'Failed to generate. Please try again.'`).
  No product-side lever exists to force a real failure on demand — automate
  via `page.route()` intercepting exactly one `generate_skill_draft` POST
  with a mocked `5xx` + JSON body, same interception class already used
  elsewhere in this page object for reading POST bodies. There is no
  separate "Retry" control — "Generate Draft" itself, still present/enabled
  in the (already-current) prompt phase after a failure, IS the retry path.
- **Empty/whitespace-prompt validation is disable-only, no message
  (ELITEA-2612 finding — case-text drift, clarification filed:
  [elitea-testing-public#1478](https://github.com/EliteaAI/elitea-testing-public/issues/1478)).**
  `disabled={!description.trim()}` on the Generate Draft button covers BOTH
  empty and whitespace-only prompts (`.trim()` on either is falsy) — no
  `ai-edit-skill-error-alert` or any other validation-message element is ever
  rendered for this path. Assert via the button's `disabled` state, not a
  message.
- **Partial-apply mechanism confirmed correct, live.** Unchecking a field's
  "Apply changes" checkbox at any wizard step and navigating away/back
  preserves that per-field checked state (`fieldApplyFlags` in
  `AIEditSkillModal.jsx`, lifted above the per-step components). The Summary
  step is NOT an itemized "these will change" list as case text implies — it's
  ONE merged, directly-editable form per field, where each field's value is
  either CURRENT or SUGGESTED depending on that field's checkbox state. Same
  guarantee, different presentation — not a defect, just a case-text
  imprecision worth knowing before you go looking for a bullet list.
- **Save vs Save as Version**: "Save" (wizard) calls `useSaveSkill` →
  `PUT /api/v2/elitea_core/skill/prompt_lib/{projectId}/{skillId}`
  (`skillsApi.js:187-200`, `skillUpdate` mutation) — mutates the CURRENT
  version in place, toast "Skill saved". "Save as Version" instead opens a
  "Create version" name dialog (`ai-edit-skill-version-dialog-*` testids,
  pre-existing/on-main) and creates a NEW version via `useSaveSkillVersion` —
  not exercised by the happy-path AFS above (out of scope, noted for a sibling
  case).
- Generate endpoint: `POST /api/v2/elitea_core/generate_skill_draft/prompt_lib/{projectId}`
  — **same URL as skill-creation's Build-with-AI**, disambiguated by payload:
  edit-mode body carries `skill_id`+`version_id`, create-mode omits both.
  `200 OK` either way.
  Full details:
  `test-specs/skills/l2_edit-with-ai-skill-happy-path_ELITEA-2611.md`.
- **Role-gated visibility (ELITEA-2613) — `edit-skill-with-ai-button` confirmed live for the
  admin-equivalent `${TEST_USER}`.** Clicking the button (`getByTestId('edit-skill-with-ai-button')`)
  opens `ai-edit-skill-modal` with heading "Edit with AI"; 0 console errors on close. Editor/Viewer
  halves are BLOCKED — same missing `EDITOR_TEST_USER_*`/`VIEWER_TEST_USER_*` fixture gap already
  tracked by `EliteaAI/elitea-testing-public#1314` for the Agent-entity sibling (ELITEA-1903/1904).
  The button's render gate is presumed (not live-verified for Skill specifically) to be the same
  `GET /api/v2/auth/permissions/prompt_lib/{project_id}`-driven `checkPermission(...)` mechanism
  ELITEA-1903 confirmed for Agent's `generate-agent-open-button` — same `entities/edit-entity-with-ai/`
  shell backs both, so no divergence is expected, but flag if a future run finds otherwise.
- **Character limit is 5,000, not 2,500 (ELITEA-2613 finding — case-text drift, clarification filed:
  [elitea-testing-public#1480](https://github.com/EliteaAI/elitea-testing-public/issues/1480)).**
  `MAX_INSTRUCTIONS_LENGTH = 5000` (`EliteaUI/src/common/constants.js:68`), applied identically at the
  wizard's editable Instructions field (`AIEditSkillModal.jsx:215` → `InstructionsStep`'s
  `TextDiffHighlight`, silent JS-level slice, `TextDiffHighlight.jsx:64,74-79`) and the Summary step's
  merged Instructions input (`SummaryStep.jsx:99,107`, native HTML `maxLength` attribute, existing
  testid `ai-edit-skill-summary-instructions-input` — **no new testid needed** to assert this). Same
  silent-truncation shape as the already-documented Name-field `maxlength=64` pattern above — no
  validation-error/blocked-Save path exists for over-limit Instructions text either.
  Full details:
  `test-specs/skills/l2_edit-with-ai-skill-permissions_ELITEA-2613.md`.
