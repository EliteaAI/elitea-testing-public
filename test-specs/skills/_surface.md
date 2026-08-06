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
