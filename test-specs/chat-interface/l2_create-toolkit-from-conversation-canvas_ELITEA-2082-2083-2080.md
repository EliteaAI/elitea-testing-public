# Test Case (FAMILY): Chat – Create Toolkit from Conversation – Save / Close-and-Verify-Participant / Discard

Family AFS for three flow-variant cases sharing one surface — the in-chat
"New Toolkit" canvas opened from a conversation's `+` menu. All three were
explored in ONE live session (cluster dispatch); each case's own steps were
executed and observed individually — see the per-case Coverage Maps below.

## Metadata
- **TMS IDs**: ELITEA-2082 (save), ELITEA-2083 (close & verify participant,
  continues from ELITEA-2082), ELITEA-2080 (discard)
- **Linked Story**: none (all three cases carry `requirements: []`)
- **Priority**: l2 (case priority: high, all three)
- **Environment Explored**: local (`http://localhost:5173`, EliteaUI
  `automation/testids`, DEV backend; project "Private", observed live as
  `projectId=399`, matches `${ELITEA_PROJECT_ID}`)
- **User set**: `${TEST_USER}` — dev-auth (`VITE_DEV_TOKEN`) skips Keycloak
  login on localhost
- **Analyst**: qa-engineer (agent), batch `cov60`
- **Status**: **ready-for-automation** (all three). No product defects found.
  Two CASE-TEXT-DRIFT clarifications filed (reverse-masking guard — the live
  product is correct, the case wording is stale): `#1010` (ELITEA-2080 step 4's
  literal search string "Artifacts" filters out the card step 5 needs) and
  `#1011` (ELITEA-2082 step 6 calls the button "Save"; it is labeled "Create"
  at the moment it must be clicked). Neither blocks automation — the AFS below
  asserts the live, correct contract in both cases.
- **New page-object surface required**: no existing `ChatPage`/page-object
  method drives the in-chat "New Toolkit" canvas (confirmed: `grep` for
  "Create New Toolkit" / `ToolkitEditor` / `toolkits-create-new-button` in
  `automation/pages/` returns nothing before this AFS — only the UNRELATED
  standalone `/toolkits/create` wizard is covered, by `ToolkitCreationPage`).
  A directly analogous surface (in-chat "Create New Agent" canvas) was
  already automated for ELITEA-2166 via a small dedicated `AgentCanvasPage`
  that composes with the pre-existing form page object rather than
  redeclaring fields — see § Automation Hints for the mirrored recommendation.

## Preconditions (shared by all three cases)
- User is logged in to the Elitea platform (`${TEST_USER}` / dev-auth on
  localhost).
- User has an open conversation in the Chats section (any existing
  conversation with at least the composer visible works; the case text
  doesn't require a specific conversation).
- Exploration ran in the account's own **Private** project (`399`); the case
  text names no specific project and toolkit-creation-from-chat was not
  observed to be project-gated, but this hasn't been independently verified
  against a Team project in this session — implementer note only, not a
  blocker.

## Test Data — parameter table (one row per case)

| Case | Toolkit type | Toolkit Name | Bucket | Terminal action | Expected outcome |
|---|---|---|---|---|---|
| ELITEA-2082 | Artifact | `test1` | `test1` | Click the create-mode action button (case calls it "Save"; live label is **"Create"** — clarification `#1011`) | Success toast "The toolkit has been created successfully"; canvas header shows "test1"; toolkit persisted (button flips to "Save", entering edit mode) |
| ELITEA-2083 | *(continues from ELITEA-2082's saved "test1")* | `test1` | `test1` | Click the canvas's X (close) button | Canvas closes; PARTICIPANTS panel, once expanded, shows a "TOOLKITS" section containing "test1" with a toolkit icon |
| ELITEA-2080 | Artifact | `test` | `test` | Click Discard → confirm "Discard" in the warning dialog | Dialog "Are you sure you want to discard changes?" appears; confirming resets the canvas all the way back to the "Choose the toolkit type" step; canvas stays open; nothing is persisted |

## Test Steps

### Shared setup (all three cases)
1. Navigate to Chats, open an existing conversation.
   - **Verify**: conversation view is displayed (message input + history visible).
2. Click the `+` (plus) icon (`plus-menu-button`) → hover "Toolkits"
   (`toolkits-menuitem` — reveals the Toolkits submenu via `onMouseEnter`,
   same mechanism as the already-automated `agents_menuitem`/
   `open_create_new_agent_canvas()` precedent) → click "+ Create New Toolkit"
   (`toolkits-create-new-button`).
   - **Verify**: "New Toolkit" canvas opens on the right (title = "New
     Toolkit"; "Choose the toolkit type" heading + search field; Discard and
     Create both disabled/greyed-out pre-selection).

### ELITEA-2080 — discard flow
3. **[2080 step 4]** Type into the type-search field
   (`toolkit-wizard-type-search-input`). **Clarification `#1010`**: the
   case's literal text is `"Artifacts"` (plural) — typing that produces
   exactly ONE match, `Elitea Artifacts` under the **MCP** category
   (`toolkit-type-card-mcp_Elitea Artifacts`), because the search is a
   substring match against each card's own label and `"Artifacts"` is not a
   substring of the label `"Artifact"`. Typing `"Artifact"` (singular)
   instead correctly surfaces BOTH cards: `MCP > Elitea Artifacts` AND
   `Storage > Artifact` (`toolkit-type-card-artifact`) — the one the case's
   own step 5 needs. This AFS asserts the live, reachable contract: search
   `"Artifact"` (no trailing s).
   - **Verify**: exactly 2 type cards render, one of them
     `toolkit-type-card-artifact`.
4. **[2080 step 5]** Click `toolkit-type-card-artifact`.
   - **Verify**: canvas heading becomes "New Artifact Toolkit"; CONFIGURATION
     section shows Toolkit Name* / Description / Pgvector Configuration /
     Embedding Model / Bucket*; TOOLS section shows the toolkit's tool chips.
5. **[2080 step 6]** Type `test` into `toolkit-form-name-input`.
   - **Verify**: `input_value()` == "test"; canvas header title live-updates
     to "test" (this happens on type, before any save — noted so the
     implementer doesn't mistake it for a save side-effect); Discard/Create
     both become enabled (form now dirty).
6. **[2080 step 7]** Type `test` into `toolkit-field-bucket-input`.
   - **Verify**: `input_value()` == "test".
7. **[2080 step 8]** Click the Discard button (no testid — see § Concrete
   Handles, `needs-adding`).
   - **Verify**: a "Warning" dialog appears with body text "Are you sure you
     want to discard changes?" and two buttons, "Cancel" / "Discard" (exact
     char-for-char match to the case's expected text; neither button nor the
     dialog itself carries any testid — confirmed via DOM query, zero hits).
8. **[2080 step 9]** Click the dialog's "Discard" (confirm) button.
   - **Verify**: dialog closes.
9. **[2080 step 10]** Verify the canvas state after discard.
   - **Verify**: canvas remains open; ALL entered data is cleared and the
     canvas resets to the "Choose the toolkit type" step (title back to
     "New Toolkit", search field empty, Discard/Create disabled again) — a
     more thorough reset than the case's ambiguous "empty/default fields"
     wording literally requires, but it satisfies the stated Pass criteria
     ("Discard clears all entered data and canvas remains open") exactly.

### ELITEA-2082 — save flow (fresh pass through the shared setup; no discard first)
10. **[2082 step 2–3]** From the "Choose the toolkit type" step, click
    `toolkit-type-card-artifact` directly (this case's own text never
    requires searching first).
    - **Verify**: canvas heading becomes "New Artifact Toolkit".
11. **[2082 step 4]** Type `test1` into `toolkit-form-name-input`.
    - **Verify**: `input_value()` == "test1"; header live-updates to "test1".
12. **[2082 step 5]** Type `test1` into `toolkit-field-bucket-input`.
    - **Verify**: `input_value()` == "test1".
13. **[2082 step 6]** Click the create-mode action button. **Clarification
    `#1011`**: the case calls this the "Save" button; the live label at the
    moment of this click is **"Create"** (`CreateToolkitButton.jsx`,
    hardcoded text, currently zero testid). This AFS locates it by role
    (`getByRole('button', {name: 'Create'})` until `needs-adding` testid
    lands) and documents the live label so the implementer isn't confused
    searching for "Save".
    - **Verify**: `POST /api/v2/elitea_core/tools/prompt_lib/{project_id}`
      resolves `201 Created` (mirror the existing network-capture idiom in
      `test_toolkit_creation_create_bucket_verify_list_files.py` — filter
      responses by URL containing `/tools/prompt_lib/`). Success toast
      renders with text "The toolkit has been created successfully"
      (shared `[data-testid="toast-message"]`, ~3s auto-dismiss — assert
      immediately after the click resolves, no intermediate waits). The
      canvas's action button flips from "Create" to "Save"
      (`SaveToolkitButton.jsx`) confirming the transition out of create mode;
      Discard becomes disabled again (form clean).
14. **[2082 step 7]** Verify the canvas header.
    - **Verify**: canvas header (no testid yet — see `needs-adding`) shows
      "test1" (this was already true from step 11's live-typing echo; this
      step confirms it's STILL true post-save, i.e. reflects the persisted
      name, not merely an unsaved draft).

### ELITEA-2083 — close & verify participant (continues from ELITEA-2082's saved "test1", canvas still open)
15. **[2083 step 1]** Verify the canvas still shows "test1" in the header
    and is still open (carried-over precondition from ELITEA-2082).
16. **[2083 step 2]** Click the canvas's X (close) button (no testid — see
    § Concrete Handles).
    - **Verify**: canvas panel is gone entirely; the conversation view
      (message input + history) is shown. A collapsed participants rail
      appears on the far right showing a toolkit/wrench icon with a badge
      reading "1".
17. **[2083 step 3]** Click `chat-participants-panel-toggle-button` to
    expand the PARTICIPANTS panel (skip this click if the panel is already
    expanded).
    - **Verify**: PARTICIPANTS panel is visible, expanded.
18. **[2083 step 4]** Verify a "TOOLKITS" section is present.
    - **Verify**: an accordion section with header text "TOOLKITS" is
      rendered (no testid on the accordion header itself — see
      `needs-adding`; assert via the parent panel's structure / text, not a
      free-floating page-level text locator — see § Automation Hints for the
      compliant scoping).
19. **[2083 step 5]** Verify "test1" is listed under TOOLKITS with a toolkit icon.
    - **Verify**: a row with testid
      `chat-participant-row-toolkit_{toolkit_id}_{project_id}` (dynamic;
      `toolkit_id` = the id captured from step 13's `201` create response,
      `project_id` = `${ELITEA_PROJECT_ID}`) is present under the TOOLKITS
      section, its text content is "test1", and it renders the generic
      toolkit `EntityIcon`.

## Expected Results
- ELITEA-2082: toolkit "test1" is created (`201`); success toast shown;
  canvas header shows "test1"; button flips Create→Save.
- ELITEA-2083: closing the canvas reveals a PARTICIPANTS panel whose
  TOOLKITS section lists "test1" with a toolkit icon.
- ELITEA-2080: Discard, confirmed, clears all entered data; canvas stays
  open (reset to the type-picker step); nothing is persisted server-side.
- No new console errors beyond the already-tracked `#291` (React key-prop
  warning on the type-selector grid — fires on EVERY visit to "Choose the
  toolkit type", not specific to this flow).

## Coverage Map

### ELITEA-2082 — Axis 1 (case coverage)

| Case element | Expected result | Covered by (AFS step) | Asserted where | Disposition |
|---|---|---|---|---|
| 1 Navigate to Chats, open a conversation | Conversation view displayed | shared step 1 | step 1 | asserted |
| 2 Click + icon, select Toolkits, click + Create New Toolkit | New Toolkit canvas opens | shared step 2 | step 2 | asserted |
| 3 Select "Artifact" toolkit type | New Artifact Toolkit canvas opens | step 10 | step 10 | asserted |
| 4 Type "test1" in Toolkit Name | Name entered correctly | step 11 | step 11 | asserted |
| 5 Type "test1" in Bucket | Bucket entered correctly | step 12 | step 12 | asserted |
| 6 Click the "Save" button | Success notification "The toolkit has been created successfully" | step 13 | step 13 | asserted *(clarification: live button reads "Create", not "Save" — `#1011`; functional outcome matches exactly)* |
| 7 Verify canvas header shows "test1" instead of "New Artifact Toolkit" | Header updated to toolkit name | step 14 | step 14 | asserted |

### ELITEA-2082 — Axis 2 (analyst additions)
- Step 13 asserts the underlying `POST .../tools/prompt_lib/{project_id}`
  resolves `201` — *added: matches this suite's existing pattern
  (`test_toolkit_creation_create_bucket_verify_list_files.py`) of confirming
  creation via the API, not just a DOM toast.*
- Step 13 also asserts the button's own text flips "Create" → "Save" —
  *added: this is the most reliable independent confirmation that the app
  actually transitioned out of create mode (the toast alone auto-dismisses
  in ~3s and could be missed by a slow assertion).*
- Console checked after every step — *added: standard side-channel
  discipline; only the pre-existing, already-tracked `#291` warning observed.*

### ELITEA-2083 — Axis 1 (case coverage)

| Case element | Expected result | Covered by (AFS step) | Asserted where | Disposition |
|---|---|---|---|---|
| Precondition: toolkit "test1" saved, canvas still open (following ELITEA-2082) | — | step 15 | step 15 | asserted |
| 1 Verify toolkit "test1" is saved and canvas is open | Canvas shows "test1" in header | step 15 | step 15 | asserted |
| 2 Click the X button to close the canvas | Canvas closes completely | step 16 | step 16 | asserted |
| 3 Observe the PARTICIPANTS panel | PARTICIPANTS panel is visible | step 17 | step 17 | asserted |
| 4 Verify a TOOLKITS section is present | TOOLKITS section is displayed | step 18 | step 18 | asserted |
| 5 Verify "test1" toolkit is listed with a toolkit icon | Toolkit is listed with icon | step 19 | step 19 | asserted |

### ELITEA-2083 — Axis 2 (analyst additions)
- Step 16 also asserts the collapsed participants rail's badge count reads
  "1" immediately after close, before the panel is expanded — *added: an
  earlier, cheaper confirmation that the participant was actually attached,
  independent of the later expanded-panel assertion.*
- The participant row's dynamic testid is asserted by its FULL composed
  form (`chat-participant-row-toolkit_{id}_{project_id}`), not a partial/
  text-only match — *added: ties the assertion to the real created entity's
  id (captured from ELITEA-2082's create response) rather than a fragile
  text-content-only locator.*

### ELITEA-2080 — Axis 1 (case coverage)

| Case element | Expected result | Covered by (AFS step) | Asserted where | Disposition |
|---|---|---|---|---|
| 1 Navigate to Chats, open a conversation | Conversation view displayed | shared step 1 | step 1 | asserted |
| 2 Click + icon, select Toolkits | Toolkits submenu opens | shared step 2 | step 2 | asserted |
| 3 Click + Create New Toolkit | New Toolkit canvas opens, "Choose toolkit type" shown | shared step 2 | step 2 | asserted |
| 4 Type "Artifacts" in search, verify filtered to Artifact-related toolkits | Only Artifact-related toolkits shown | step 3 | step 3 | asserted *(clarification `#1010`: asserts the reachable contract — searching "Artifact", singular — rather than the case's literal "Artifacts" string, which would exclude the very card step 5 needs)* |
| 5 Click "Artifact" toolkit type | New Artifact Toolkit canvas opens | step 4 | step 4 | asserted |
| 6 Type "test" in Toolkit Name | Name appears in field | step 5 | step 5 | asserted |
| 7 Type "test" in Bucket | Bucket value appears in field | step 6 | step 6 | asserted |
| 8 Click Discard | Warning dialog "Are you sure you want to discard changes?" | step 7 | step 7 | asserted |
| 9 Click Discard in dialog to confirm | Canvas cleared; data removed | step 8 | step 8 | asserted |
| 10 Verify canvas remains open with empty/default fields | Canvas open but cleared | step 9 | step 9 | asserted |

### ELITEA-2080 — Axis 2 (analyst additions)
- Step 9 asserts the reset goes all the way back to the type-PICKER step
  (not merely blanked Name/Bucket fields on the same config form) — *added:
  this is what was actually observed live; documenting the exact reset
  target avoids the implementer under- or over-asserting.*
- Step 7 asserts the dialog/buttons carry NO testid at all (a `count()==0`
  style structural fact, not a functional assertion) — *added: this is the
  evidence backing the `needs-adding` handles row below; saves the
  implementer from re-discovering it.*

## Cleanup
1. Toolkit "test1" (real, persisted entity created by ELITEA-2082/2083,
   `toolkit_id=1755` in this exploration session) — delete via
   `DELETE {ELITEA_API_BASE}/elitea_core/tool/prompt_lib/{project_id}/{toolkit_id}`
   (confirmed `204` in this session; already cleaned up post-exploration —
   project `399` is left clean). The automated test's own teardown should
   capture the id from the create response and delete it the same way.
2. ELITEA-2080's "test" toolkit — never persisted (Discard fires before any
   Create/Save click), no cleanup needed.
3. Standard `try/finally` per `.claude/rules/ui-tests.md` § Test Data Lifecycle.

## Concrete Handles (discovered during exploration)

Locator policy on this project is **testid-only** — no role/label/text
fallback ladder (`.agents/testing.md` § Locator policy,
`.agents/role-overrides.md`). Provenance verified via
`cd EliteaUI && git fetch origin` (this session) then `git grep` on both
`origin/main` and `origin/automation/testids` — dynamic (templated) testids
verified by grepping the TEMPLATE STRING, not the resolved value (bare-
substring grep on the resolved string returns false negatives for these —
same gotcha as the credentials-surface digest documents).

| Element | Testid handle | Provenance | Notes |
|---|---|---|---|
| Composer `+` (plus) menu button | `plus-menu-button` | on-main ✓ | Existing `ChatPage.plus_menu_button`. |
| `+` menu → "Toolkits" menuitem | `toolkits-menuitem` | on-`automation/testids` only | **New page-object field needed.** `PlusChatButton.jsx`'s `EXPANDABLE_ITEMS` array already wires this per-item testid on `automation/testids`; ELITEA-2166 precedent already added the sibling `agents-menuitem` field to `chat_page.py` — mirror it for `toolkits_menuitem`. |
| Toolkits submenu → "+ Create New Toolkit" item | `toolkits-create-new-button` | on-`automation/testids` only | Template `${sectionKey}-create-new-button` in `PlusChatSubmenu.jsx`, `sectionKey='toolkits'` at `PlusChatButton.jsx`'s call site — same mechanism ELITEA-2166 already used for `agents-create-new-button`. **New page-object field needed** — mirror `agents_create_new_button`. |
| Toolkits submenu search field | `toolkits-search-input` | on-`automation/testids` only | Template `${sectionKey}-search-input`, same component — not exercised by any of these 3 cases (none searches the Toolkits SUBMENU, only the type-picker's OWN search below), listed for completeness only. |
| Type-picker search field | `toolkit-wizard-type-search-input` | on-`automation/testids` only | Existing `ToolkitCreationPage.type_search_input` (ELITEA-1868) — SAME shared `ToolkitTypeSelector.jsx` component renders in the chat canvas; confirmed live-working in this context too (`isMCP=false`/`isApplication=false` → testid present). |
| Type card (dynamic, "Artifact") | `toolkit-type-card-artifact` | on-`automation/testids` only | Template `toolkit-type-card-${itemKey}` (`CategoryItemCard.jsx`) — existing `ToolkitCreationPage.TOOLKIT_TYPE_CARD.format('artifact')`. |
| Type card (dynamic, "Elitea Artifacts" MCP — the DISTRACTOR card from clarification `#1010`) | `toolkit-type-card-mcp_Elitea Artifacts` | on-`automation/testids` only | Same template, `itemKey='mcp_Elitea Artifacts'`. Only needed to assert it's a DIFFERENT match than the target, if the implementer chooses to assert the 2-card search-result count from step 3. |
| Toolkit Name field | `toolkit-form-name-input` | on-`automation/testids` only | Existing `ToolkitCreationPage.name_input` — SAME `NameDescriptionInput.jsx`, confirmed live-working in the chat canvas. |
| Bucket field (dynamic) | `toolkit-field-bucket-input` | on-`automation/testids` only | Template `toolkit-field-${k}-input` (`ToolBaseProperty.jsx`), `k='bucket'` — existing `ToolkitCreationPage.TOOLKIT_FIELD_INPUT.format('bucket')`. |
| Canvas create-mode action button (case: "Save"; live: "Create") | **NO TESTID** | needs-adding | `testid needed: toolkit-form-create-button`. `CreateToolkitButton.jsx` renders `<Button.BaseBtn>` with zero testid/props threading (confirmed via source read AND a live DOM query — 0 matches for any `[data-testid]` on this element). Currently only resolvable via `getByRole('button', {name: 'Create'})` — not testid-only compliant; blocks step 13 without this addition. |
| Canvas edit-mode action button (post-save, reads "Save") | **NO TESTID** | needs-adding | `testid needed: toolkit-form-save-button` (or reuse a shared name if one already exists for `SaveToolkitButton.jsx` elsewhere — not checked in this session since none of these 3 cases click it; only its label-flip is asserted as evidence of the state transition). Flag for completeness; not a hard blocker for these 3 cases. |
| Toast (success) | `toast-message` | on-main ✓ | Shared `Toast.jsx` component, already used by 3 other page objects under their own named field (per-page-object-field convention) — declare a new named field (e.g. `toolkit_created_toast_message`) rather than cross-importing another page object's field. |
| Canvas title (header text — "New Toolkit" / "New Artifact Toolkit" / "test1") | **NO TESTID** | needs-adding | `testid needed: toolkit-canvas-title`. Mirrors the ALREADY-IMPLEMENTED `agent-canvas-title` (`AgentEditor.jsx` passes `titleTestId="agent-canvas-title"` to `BaseEditor`) — `ToolkitEditor.jsx`'s own `<BaseEditor>` call currently passes NEITHER `titleTestId` NOR `closeButtonTestId` NOR `subtitleTestId` at all (confirmed via source read: zero occurrences in the file). Needed for steps 5, 11, 14, 15. |
| Canvas X (close) button | **NO TESTID** | needs-adding | `testid needed: toolkit-canvas-close-button`. Mirrors the already-implemented `agent-canvas-close-button`. `EditorHeader.jsx`'s close `IconButton` renders `data-testid={closeButtonTestId}` — `undefined` here since `ToolkitEditor.jsx` never supplies it. Currently only resolvable by DOM position (confirmed live: the correct button is index 24 among page-wide `button` elements at this state, NOT distinguishable via `aria-label` — a DIFFERENT, unrelated icon elsewhere on the page also has `aria-label="close"`, a live trap worth flagging). Blocks step 16 without this addition. |
| Discard button (canvas header) | **NO TESTID** | needs-adding | `testid needed: toolkit-canvas-discard-button`. `EditorHeader.jsx`'s `<Button.DiscardButton onDiscard={discardApplicationChanges} .../>` call passes NONE of the THREE testid props `DiscardButton.jsx` itself already natively supports (`dataTestId`, `modalDataTestId`, `confirmButtonDataTestId`) — this is a threading gap, not a missing-capability gap. Confirmed live: 0 testid matches anywhere in the Discard button + its warning dialog + both its buttons. Blocks step 7 without this addition. |
| Discard confirm dialog (the "Warning" modal) | **NO TESTID** | needs-adding | `testid needed: toolkit-canvas-discard-confirm-dialog` — thread `modalDataTestId` (already supported by `DiscardButton.jsx` → `Modal.BaseModal`'s own `data-testid` prop). |
| Discard dialog's "Discard" (confirm) button | **NO TESTID** | needs-adding | `testid needed: toolkit-canvas-discard-confirm-button` — thread `confirmButtonDataTestId` (already supported, lands on `BaseModal`'s `confirmButtonTestId` → the confirm `Button.BaseBtn`'s `data-testid`). Blocks step 8 without this addition. |
| Participants panel toggle (collapse/expand) | `chat-participants-panel-toggle-button` | on-`automation/testids` only | Existing (ELITEA-2098). |
| PARTICIPANTS "TOOLKITS" section accordion header | **NO TESTID** | needs-adding (low priority) | `ParticipantsAccordion.jsx` accepts no testid prop at all currently — `testid needed: chat-participants-section-{key}` (dynamic; `key='toolkits'` here), mirroring the pattern already used elsewhere for dynamic per-key testids. Not a hard blocker: step 18 can instead be verified INDIRECTLY via step 19's row testid being present (its mere existence proves the TOOLKITS section rendered, since `ParticipantSection` only renders when its group is non-empty) — recommend this as the pragmatic default and treat the header-text assertion as a nice-to-have once the testid lands. |
| Toolkit participant row (dynamic) | `chat-participant-row-toolkit_{id}_{project_id}` | on-main ✓ (base pattern; entity_name literal is `"toolkit"`, confirmed live e.g. `chat-participant-row-toolkit_1755_399`) | Existing pattern (`getChatParticipantUniqueId()` composition) — no new page-object field exists yet for the TOOLKIT variant specifically; existing `chat_page.py` participant-row helpers are agent/pipeline-scoped, a toolkit-flavored accessor needs adding (page-object work, not a testid gap). |
| Collapsed participants rail badge (toolkit count) | *(not individually inspected — icon + numeric badge observed only via screenshot)* | not verified | Only asserted structurally in step 16 as an Axis-2 addition; if no compliant testid is found during implementation, downgrade this specific sub-assertion rather than block the step — the expanded-panel assertion (step 19) is the case's actual Pass criterion. |

## Network Behavior
- `POST /api/v2/elitea_core/tools/prompt_lib/{project_id}` → `201 Created` on
  the create-mode button click (ELITEA-2082 step 13). Mirror the existing
  network-capture idiom already in
  `test_toolkit_creation_create_bucket_verify_list_files.py` (filters
  responses by URL containing `/tools/prompt_lib/`).
- No network call fires on Discard (ELITEA-2080) — confirmed nothing is
  persisted; the reset is entirely client-side (Formik `resetForm()` +
  local `editToolDetail`/`formikInitialValues` state reset).
- No new network call fires on canvas close (ELITEA-2083 step 16) — the
  participant is already attached as a side effect of ELITEA-2082's create
  call; closing the canvas is a pure UI-state transition.

## Known Defects Found During Exploration
None. Two CASE-TEXT-DRIFT clarifications were filed (reverse-masking guard —
live product is correct, case wording is stale), neither blocking automation:
- **`#1010`** — ELITEA-2080 step 4's literal search text "Artifacts" (plural)
  filters OUT the "Artifact" (Storage) card step 5 needs, because the search
  does a substring match and "Artifacts" isn't a substring of the label
  "Artifact". Searching "Artifact" (singular) instead reaches both cards correctly.
- **`#1011`** — ELITEA-2082 step 6 calls the button "Save"; its live label at
  click-time is "Create" (flips to "Save" only after the toolkit is
  persisted). Toast text, created-toolkit side effect, and header update all
  match the case exactly — only the button's own label is a naming mismatch.

## Blocked Steps
None. All steps across all three cases were executed and observed live.

## Automation Hints
- Framework: Playwright + pytest, testid-only `LocatorDescriptor`
  (`.agents/testing.md`). Locator policy: testid-only
  (`.agents/role-overrides.md` + `.agents/testing.md` § Locator policy) — the
  workflow skill's example ladder does not apply; new non-testid handles are
  `CHANGES_REQUESTED`.
- **New page object recommended: `ToolkitCanvasPage`**, mirroring the
  already-merged `AgentCanvasPage` (ELITEA-2166) shape exactly: it should own
  ONLY the canvas-specific chrome with no existing equivalent — `close_button`
  (`toolkit-canvas-close-button`), `title` (`toolkit-canvas-title`),
  `create_button` (`toolkit-form-create-button`), `discard_button`
  (`toolkit-canvas-discard-button`), `discard_confirm_dialog`
  (`toolkit-canvas-discard-confirm-dialog`), `discard_confirm_button`
  (`toolkit-canvas-discard-confirm-button`). It should NOT redeclare the
  type-picker/form fields that `ToolkitCreationPage` already owns
  (`type_search_input`, `TOOLKIT_TYPE_CARD`, `name_input`,
  `TOOLKIT_FIELD_INPUT`) — confirmed live-working as-is in the chat-canvas
  context (same underlying `ToolkitTypeSelector.jsx`/`ToolkitForm`
  components) — compose `ToolkitCreationPage(page)` on the same `page`
  instance for those, exactly as `AgentCanvasPage`'s own docstring directs
  for `AgentFormPage`.
- **New `ChatPage` fields/method** mirroring the ELITEA-2166 precedent
  1:1: `toolkits_menuitem` (testid `toolkits-menuitem`) +
  `toolkits_create_new_button` (testid `toolkits-create-new-button`) +
  `open_create_new_toolkit_canvas()` (click `plus_menu_button` → hover
  `toolkits_menuitem` → click `toolkits_create_new_button` — same
  click→hover→click chain as `open_create_new_agent_canvas()`). Do NOT
  confuse this with the PRE-EXISTING `add_toolkit_participant()` method
  (`chat_page.py:3151`) — that one ADDS AN EXISTING toolkit as a
  participant via a raw `get_by_role`/CSS locator (pre-existing tech debt,
  out of scope for this AFS, don't touch it) and is functionally unrelated
  to this family's CREATE-a-new-toolkit flow.
- **`add-data-testid` work required — 6 additions, scoped ONLY to elements
  this family's tests touch** (per `.agents/role-overrides.md` § locator
  policy scope discipline — do not blanket-add to `PipelineEditor`/
  `ArtifactEditor`/other editors sharing the same components, since no case
  here touches those):
  1. `ToolkitEditor.jsx`'s `<BaseEditor>` call: add `titleTestId="toolkit-canvas-title"`
     and `closeButtonTestId="toolkit-canvas-close-button"` (mirrors
     `AgentEditor.jsx`'s existing `titleTestId`/`closeButtonTestId` props
     verbatim). Omit `subtitleTestId` — no case in this family reads a
     subtitle.
  2. `CreateToolkitButton.jsx`: add `data-testid="toolkit-form-create-button"`
     to its `<Button.BaseBtn>`.
  3. `EditorHeader.jsx`'s `<Button.DiscardButton>` call: thread 3 NEW props
     down from `BaseEditor` (which already receives `titleTestId` etc. the
     same way) — e.g. `discardButtonTestId`/`discardModalTestId`/
     `discardConfirmButtonTestId` — into `DiscardButton.jsx`'s EXISTING
     `dataTestId`/`modalDataTestId`/`confirmButtonDataTestId` props (no
     change needed inside `DiscardButton.jsx` itself, it already accepts
     them). Wire ONLY `ToolkitEditor.jsx`'s own call site with
     `toolkit-canvas-discard-button` / `toolkit-canvas-discard-confirm-dialog`
     / `toolkit-canvas-discard-confirm-button` — leave every other editor's
     Discard button exactly as-is (untouched, no testid), since this is a
     SHARED component and no case here exercises Agent/Pipeline/Artifact's
     own Discard flow.
- **Toast**: reuse the existing shared `[data-testid="toast-message"]`
  pattern (already used by 3 other page objects, each under its own named
  field) — declare a new named field on whichever page object ends up
  owning it (recommend `ToolkitCanvasPage.success_toast_message`).
- **Dynamic participant-row testid**: capture the toolkit's `id` from the
  `201` create response body (step 13) rather than parsing a URL — this is
  an embedded canvas, not a route, so there is no URL change to extract an
  id from (unlike the standalone `/toolkits/create` wizard's own flow).
- **Recommended test-module shape**: ONE spec module (e.g.
  `test_create_toolkit_from_conversation.py`) with 2 test methods —
  `test_discard_clears_new_toolkit_canvas` (ELITEA-2080, fully standalone)
  and `test_save_toolkit_and_verify_participant_added` (ELITEA-2082 +
  ELITEA-2083 as ONE continuous flow — ELITEA-2083's own precondition text
  literally continues from ELITEA-2082's saved state, so splitting them into
  two independent tests would mean re-deriving the "test1 already saved,
  canvas already open" precondition a second time for no benefit). Tag
  `automation_test_id` per `.agents/test-automation.yaml` — the
  save-and-verify test lists BOTH `ELITEA-2082` and `ELITEA-2083` in the
  TMS back-write (a case may list several tests; one test may also cover
  several cases), the discard test lists `ELITEA-2080` alone.
- **Console noise to exclude**: the React key-prop warning at
  `ToolkitTypeSelector.jsx`/`CategorySection.jsx`/`GroupedCategory.jsx`
  (already tracked, `#291`) fires on every visit to the "Choose the toolkit
  type" step — do not treat it as a new-console-error regression signal for
  this flow specifically.
