# Test Case: Edit Remote MCP — Discard Changes

## Metadata
- **TMS ID**: ELITEA-1928
- **Linked Story**: none
- **Priority**: l1 (case frontmatter: `priority: critical`; case body says
  "medium" — same pre-existing inconsistency recorded in the ELITEA-1929 /
  ELITEA-1926 AFS; frontmatter authoritative)
- **Environment Explored**: local (`http://localhost:5173`, `EliteaAI/EliteaUI` @
  `automation/testids`, DEV backend), project 399
- **User set**: `${TEST_USER}` (localhost: `VITE_DEV_TOKEN` auto-auth)
- **Analyst**: test-automation-engineer (combined analyst+implementer slot), session 2026-08-24
- **Status**: ready-for-automation

## Preconditions
- User is authenticated; project id from `${ELITEA_PROJECT_ID}`.
- A Remote MCP exists and its detail page is open in Form view.
- The MCP has a **non-empty** description, so "reverts to the original value"
  is an observable revert and not a revert-to-empty (see § Test Data).

## Test Data

### generate-shared-with-cleanup

Same reasoning as ELITEA-1925 / ELITEA-1926: no discoverable pre-existing Remote
MCP (`ToolkitAPI.list_all_toolkits()` returns empty on this environment
regardless of auth method), and editing a description is destructive to whatever
toolkit is used → the test seeds its own disposable Remote MCP through the real
UI create flow and deletes it in teardown.

| Field | Value | Why |
|---|---|---|
| Seed name | `autotest_mcp_discard_<6hex>` (27 chars) | ≤ `MAX_NAME_LENGTH = 32` |
| Seed (original) description | `Original description for discard case` | the case's step 2 "original description" — seeded non-empty so step 6's revert is observable |
| Url | `https://mcp.example.com/sse` | stored only; never dialled (no Load Tools in this case) |
| Temporary Description | `This should be discarded` | **verbatim from the case's Test Data table** |

## Test Steps

Live-executed 2026-08-24 against `http://localhost:5173` (seeded toolkit id 3029,
deleted after the run).

| # | Action | Expected (case) | Observed live |
|---|--------|-----------------|---------------|
| 1 | Open the Remote MCP detail page in Form view | Detail page loads in Form view | `toolkit-form-view-toggle` `aria-pressed == "true"`; `toolkit-detail-title` == seeded name |
| 2 | Note current description value | Original description is observed | `toolkit-form-description-input` value == `Original description for discard case`. **The description field is rendered INLINE on the detail page** — unlike the schema-driven `toolkit-field-*` fields it is NOT behind `toolkit-configuration-show-more` (it renders through `NameDescriptionInput.jsx`, not `ToolBaseProperty.jsx`). Baseline also captured here: Save AND Discard are both **disabled** on the pristine form. |
| 3 | Change description to "This should be discarded" | Field displays the temporary value | value == `This should be discarded` |
| 4 | Verify Save and Discard buttons become enabled | Both buttons are active | `toolkit-detail-save-button.disabled is False` and `toolkit-detail-discard-button.disabled is False` (both gate on `isFormDirtyExcluding` — `ToolkitsTabBarContainer.jsx:150,158-161`) |
| 5 | Click Discard | Discard action is triggered | **A confirmation modal opens** — `Warning` / `Are you sure you want to discard changes?` / `Cancel` / `Discard`. The case text does not mention it (see § Known Defects → clarification). Nothing is reverted until its `Discard` is confirmed: immediately after the first click the description still reads `This should be discarded` and both buttons are still enabled. |
| 6 | Verify description reverts to original value | Description shows the original text | after confirming in the modal: modal detaches from the DOM, value == `Original description for discard case` |
| 7 | Verify Save and Discard buttons return to disabled state | Both buttons are disabled again | both `.disabled is True` |

## Expected Results
- The pristine detail form has Save and Discard disabled; editing the description
  enables both.
- Clicking Discard raises a confirmation modal carrying the exact text
  `Are you sure you want to discard changes?`; the revert happens only on confirm.
- After confirming, the description holds its original value and both buttons
  return to disabled.
- **Nothing is persisted**: no `PUT /tool/prompt_lib/{project}/{id}` is issued
  anywhere in the flow, and a full page reload still shows the original
  description (server-side proof that the discard did not save).

## Coverage Map

### Axis 1 — Case coverage

| Case element | Disposition | Where asserted |
|---|---|---|
| Precondition: logged in | precondition | framework `auth_state` |
| Precondition: existing Remote MCP open on its detail page in Form view | precondition (substituted seed) | seeded via the UI create flow — § Test Data; Form view asserted in step 1 |
| Step 1 — detail page loads in Form view | asserted | `form_view_toggle` `aria-pressed == "true"` + `detail_title` == seeded name |
| Step 2 — original description observed | asserted | `description_input.input_value() == original_description` |
| Step 3 — description shows the temporary value | asserted | `description_input.input_value() == "This should be discarded"` |
| Step 4 — Save and Discard become enabled | asserted | both `.is_disabled() is False` |
| Step 5 — Discard action triggered | asserted | confirm modal visible + its text contains `Are you sure you want to discard changes?`; then confirm clicked |
| Step 6 — description reverts to original | asserted | `expect(description_input).to_have_value(original_description)` |
| Step 7 — both buttons disabled again | asserted | both `.is_disabled() is True` |
| Expected Final State — all unsaved changes discarded | asserted | steps 6+7 + the no-PUT / post-reload assertions below |
| Pass criterion: no errors during the flow | asserted | console-error listener (known #291 filtered, #549 soft — sibling-spec pattern) |

### Axis 2 — Analyst additions

| Addition | Why grounded |
|---|---|
| Pristine baseline (both buttons disabled) captured at step 2 | Step 4 asserts the buttons *become* enabled — without a baseline it proves nothing. The gate (`isFormDirtyExcluding`) was read in source and confirmed live. |
| Confirmation-modal assertions (visible + exact warning text + confirm click) | The modal is an unavoidable part of the live "Click Discard" step; asserting its text pins the product behaviour the case text silently assumes away. |
| "No `PUT` was issued" assertion | The case's Expected Final State is "all unsaved changes are discarded" — a UI revert alone does not prove nothing was persisted. |
| Post-reload description assertion | Same reason: proves the discard was not a client-only revert masking a save. |
| Console-error monitoring | Case Pass criterion "All steps complete without errors". |

## Cleanup
The seeded toolkit is deleted in a `finally:` block via
`ToolkitAPI.delete_toolkit(id)`. Nothing else is mutated — the discard is, by
definition, a no-op against the server.

## Concrete Handles (discovered during exploration)

| Element | Handle | Provenance |
|---|---|---|
| Description textarea (detail + create) | `toolkit-form-description-input` | on-main ✓ |
| Toolkit Name input | `toolkit-form-name-input` | on-main ✓ |
| Detail Save button | `toolkit-detail-save-button` | on `automation/testids` (ELITEA-1929, EliteaUI PR #572) |
| Detail Discard button | `toolkit-detail-discard-button` | on `automation/testids` (ELITEA-1929, EliteaUI PR #572) |
| Discard-confirm modal | `toolkit-detail-discard-confirm-modal` | **needs-adding → ADDED this session**, EliteaAI/EliteaUI@a51c9318 on `automation/testids`, **not yet on `main`** |
| Discard-confirm "Discard" button | `toolkit-detail-discard-confirm-button` | **needs-adding → ADDED this session**, same commit |
| Form view toggle | `toolkit-form-view-toggle` | on-main ✓ |
| Detail title | `toolkit-detail-title` | on-main ✓ |

The two new testids are **not new DOM**: `Button.DiscardButton`
(`src/[fsd]/shared/ui/button/DiscardButton.jsx`) already accepts
`modalDataTestId` / `confirmButtonDataTestId` and the credentials tab bar already
passes them (`credential-discard-confirm-modal` / `-button`). The toolkit-detail
call site simply did not. Two additive props, no new node, no hook, no behaviour
change. Per #511 only the two handles the test calls on its executed path were
added — `cancelButtonTestId` / `closeButtonTestId` / `modalTitleTestId` were left
unpassed.

## Network Behavior
- `POST /tools/prompt_lib/{project}` → 201 (seed).
- `GET /tool/prompt_lib/{project}/{id}` on detail load.
- **No `PUT`** anywhere in the discard flow — verified live on the network log
  (only the seed POST and the detail GETs were recorded across the whole run).

## Known Defects Found During Exploration

None (no product defect).

**Case-text clarification (not a bug):** the case's step 5 reads
`Click Discard → Discard action is triggered` and its step 6 expects the revert,
with no mention of the intervening confirmation modal that the product actually
shows. The product behaviour is reasonable and matches the Credentials surface
(ELITEA-1971 has the same modal, already automated). The case text should name
the modal step. Filed as a clarification per `.agents/profile.md` § Bug filing.

## Blocked Steps
None.

## Automation Hints
- The description field needs **no** `expand_configuration_section()` — it is
  inline. Only `toolkit-field-*` handles are collapsed.
- After clicking Discard, wait for `toolkit-detail-discard-confirm-modal` to be
  **visible**, and after confirming wait for it to be **detached** (it unmounts,
  same as `credential-discard-confirm-modal`).
- The modal testid lands on the MUI `Dialog` root, so its `text_content()`
  includes the title and both button labels — assert with `in`, not `==`.
- Do not assert the detail header here — nothing renames, and the header is a
  known laggy element on this surface.
