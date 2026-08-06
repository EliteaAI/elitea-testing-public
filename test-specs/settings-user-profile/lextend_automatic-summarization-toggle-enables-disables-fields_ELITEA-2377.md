# Test Case: Summarization toggle enables and disables summarization fields

## Metadata
- **TMS ID**: ELITEA-2377
- **Linked Story**: EliteaAI/elitea-testing-public#885
- **Priority**: l3
- **Environment Explored**: local (`http://localhost:5173`, `EliteaAI/EliteaUI` `automation/testids`, DEV backend)
- **User set**: `${TEST_USER}` (localhost `auth_state` bypass via `VITE_DEV_TOKEN`)
- **Analyst**: test-automation-engineer (combined analyst+implementer slot), batch `elitea-2377-summarization-toggle`
- **Status**: extend-existing

## Extension target

- **Covering spec**: `automation/tests/ui/settings/test_context_management_toggle.py:73`
  (`class TestContextManagementToggle`, existing method
  `test_context_management_toggle_enables_disables_fields` at line 76).
- **Covering AFS**: `test-specs/settings-user-profile/l3_context-management-toggle-enables-disables-fields_ELITEA-2374.md`
- **Behavioural overlap**: the covering spec already exercises the SAME
  `/settings/memory` page, the same `UserProfileSettingsPage` page object, and
  already asserts that the Automatic Summarization sub-section (including its
  own `automatic-summarization-toggle`) mounts/unmounts as a unit with its
  *parent* Context Management toggle (covering spec steps 6–8). What it does
  **not** cover is this case's actual observable: the Automatic Summarization
  toggle's effect on **its own** children (Summarization Instructions
  textarea, Target Summary Tokens input) — a *different* disable mechanism
  (`disabled` prop, not conditional unmount — see § Gap assertions) that the
  covering spec never exercises because it only ever drives the parent
  toggle.
- **Extension mechanic**: additive — a new `test_automatic_summarization_toggle_enables_disables_own_fields`
  method appended to the same `TestContextManagementToggle` class, sharing the
  same module-level autosave-wait helpers (`_is_autosave_put_response`,
  `_is_autosave_get_response`) and the same `UserProfileSettingsPage` page
  object. The existing test method is byte-identical after this change.

## Preconditions
- User is logged in to the Elitea platform (`auth_state` fixture).
- No project-level precondition — this is a per-user profile setting.
- Context Management (the parent toggle) must be ON for the Automatic
  Summarization sub-section to be reachable at all (confirmed:
  `isSummarizationDisabled = !values.context_enabled || !values.enable_summarization`
  in `MemorySummarization.jsx` — with the parent OFF the whole sub-section is
  unmounted, per the covering AFS).

## Test Data
### reuse-existing
- No fixed test data required. The shared `${TEST_USER}` account currently
  has Automatic Summarization ON with Target Summary Tokens = `4096` and an
  empty Summarization Instructions field (placeholder text only, no saved
  value). **Do not hard-assert the literal `4096`** as a schema/fresh-account
  default — per the surface digest's Test data gotcha (and the covering
  AFS's identical caution for Max Context Tokens / Preserve Recent Messages),
  this account carries whatever was last saved by earlier sessions. Read the
  current value and capture-and-compare instead. (It happens to equal the
  case text's literal `4096` on this account today — noted for information,
  not asserted as a platform default.)

## Test Steps
1. Navigate to `${BASE_URL}/settings/memory` (Settings → Memory tab).
   - **Verify**: the "Context Management" accordion section
     (`context-management-section`) is visible and expanded by default.
   - *(Reused from the covering spec's own step 1 — same navigation, no new
     assertion needed here since the covering test already proves this.)*
2. Ensure Context Management is enabled (precondition for the rest of the
   flow — Automatic Summarization is unreachable while it's OFF). If OFF,
   turn it ON via the Context Management toggle (`context-management-toggle`)
   and wait for the autosave round-trip (`PUT /api/v2/social/author/` → 200).
3. Verify the Automatic Summarization toggle (`automatic-summarization-toggle`)
   is present and visible. If it is currently OFF, turn it ON first
   (precondition for the rest of the flow) and wait for the autosave
   round-trip.
4. With the toggle ON, verify Summarization Instructions
   (`summarization-instructions-textarea`) and Target Summary Tokens
   (`target-summary-tokens-input`) are **visible and enabled** (not
   `disabled`).
5. Read the current value of Target Summary Tokens and assert it is a
   non-empty positive integer. **Do not assert the literal `4096`** — see
   Test Data note above. Store the value as `original_target_tokens` for the
   restore-verification in step 8.
6. Click the Automatic Summarization toggle (`automatic-summarization-toggle`)
   to turn it OFF. Wait for the autosave round-trip
   (`PUT /api/v2/social/author/` → 200; UI shows a "Settings saved
   successfully" toast).
7. Verify Summarization Instructions (`summarization-instructions-textarea`)
   and Target Summary Tokens (`target-summary-tokens-input`) become
   **disabled** (`to_be_disabled()`). **This is a genuinely different
   mechanism from the parent Context Management toggle** (which conditionally
   *unmounts* its children, per the covering AFS): confirmed live and in
   source (`MemorySummarization.jsx`) that the Automatic Summarization
   toggle instead sets a `disabled` prop on its own two children — they stay
   mounted in the DOM, just non-interactive. The case text's "grayed out /
   uneditable" wording is **literally accurate here** (unlike the parent
   toggle case, where the same wording described an unmount and needed a
   clarification — EliteaAI/elitea-testing-public#1238).
8. Click the Automatic Summarization toggle (`automatic-summarization-toggle`)
   back ON. Wait for the autosave round-trip.
   - **Verify**: Summarization Instructions and Target Summary Tokens
     re-enable (`to_be_enabled()`).
   - **Verify**: Target Summary Tokens' value equals `original_target_tokens`
     from step 5 (state is preserved across the disable/enable cycle, not
     reset). Summarization Instructions is not value-compared — the field is
     empty (placeholder-only) on this account, so there is no meaningful
     value to round-trip; the enabled-state check above is sufficient
     coverage for that field's restore behaviour.

## Expected Results
- Toggling Automatic Summarization OFF disables (via the `disabled` prop —
  does NOT unmount) the Summarization Instructions and Target Summary Tokens
  fields.
- Toggling back ON re-enables both fields with their prior values intact.
- Each toggle click triggers `PUT /api/v2/social/author/` → 200 (autosave;
  no explicit Save button on this page) — same autosave mechanism as the
  parent Context Management toggle, confirmed via live network capture.
- No console errors during the flow beyond the one pre-existing, unrelated
  console error already noted in the covering AFS's exploration.

## Coverage Map

### Axis 1 — Case coverage

| Case element | Expected result | Covered by (AFS step) | Asserted where | Disposition |
|---|---|---|---|---|
| 1 Navigate to Personalization → DEFAULT SUMMARIZATION | Target page/section loads | AFS step 1 | step 1: `context-management-section` visible (reused from covering spec) | clarification *(route is Settings → Memory, not Personalization; "DEFAULT SUMMARIZATION" is the "Automatic Summarization" sub-section — same stale case-text pattern as the sibling ELITEA-2374 case, covered by the existing clarification EliteaAI/elitea-testing-public#1238, no new ticket needed)* |
| 2 Ensure Context Management is enabled | Condition holds | AFS step 2 | step 2: `context-management-toggle` ON (enable if needed) + autosave PUT 200 | asserted |
| 3 Verify "Enable automatic summarization" toggle is present | Toggle visible | AFS step 3 (partial) | step 3: `automatic-summarization-toggle` visible | asserted |
| 4 Verify toggle ON: Summarization Instructions + Target Summary Tokens editable | Fields editable | AFS steps 3 (turn ON if needed) + 4 | step 4: both fields visible + enabled | asserted |
| 5 Verify default value: Target Summary Tokens = 4096 | Specific default shown | AFS step 5 (partial) | step 5: field is a non-empty positive integer | blocked *(exact literal default unverifiable as a platform default on the shared `${TEST_USER}` account, which already carries a persisted value — happens to read `4096` today, same test-data caveat as the sibling ELITEA-2374 case; see § Blocked Steps)* |
| 6 Click the toggle to turn it OFF | Toggle responds | AFS step 6 | step 6: toggle unchecked + autosave PUT 200 | asserted |
| 7 Verify Summarization Instructions and Target Summary Tokens become grayed out / uneditable | Fields disabled | AFS step 7 | step 7: both fields `to_be_disabled()` | asserted *(case text is literally accurate here — genuine `disabled` prop, not the unmount mechanism seen on the parent toggle)* |
| 8 Toggle back ON — verify fields are editable again | Fields restored, editable | AFS step 8 | step 8: both fields `to_be_enabled()` + Target Summary Tokens value round-trip | asserted |

### Axis 2 — Analyst additions
- AFS steps 6/8 assert the `PUT /api/v2/social/author/` → 200 autosave
  round-trip explicitly — *added: confirmed via live network capture that
  the Automatic Summarization toggle autosaves through the same endpoint as
  the parent Context Management toggle.*
- AFS step 7 explicitly documents and asserts the **mechanism difference**
  from the parent toggle (disable via `disabled` prop vs. conditional
  unmount) — *added: this is the actual reason this case needs its own test
  rather than being folded into the covering spec's existing assertions; the
  covering spec's steps 6–8 only ever observe the Automatic Summarization
  sub-section from the OUTSIDE (its own toggle unmounting/remounting as a
  unit with the parent), never exercise the sub-section's OWN toggle.*
- AFS step 8 asserts the Target Summary Tokens value is **preserved**, not
  reset, across the disable/enable cycle — *added: natural counterpart to
  step 7's finding, guards against a future regression that resets the value
  on re-enable.*

## Cleanup
- None required beyond the test's own flow. Context Management and Automatic
  Summarization both start and end this test ON (steps 2/3 establish the
  precondition; steps 6→8 is a full disable/enable round-trip back to the
  starting state). No persistent mutation beyond what already existed.

## Concrete Handles (discovered during exploration)

| Element | Testid | PROVENANCE | Notes |
|---|---|---|---|
| Automatic Summarization toggle | `automatic-summarization-toggle` | on-automation/testids only (awaiting human promotion to main) | Pre-existing — added in the ELITEA-2374 session, `EliteaAI/EliteaUI@b8155bda`. Already declared on the page object; reused here, not re-added. |
| Summarization Instructions textarea | `summarization-instructions-textarea` | on-automation/testids only (awaiting human promotion to main) | **NEW** — added this session, `EliteaAI/EliteaUI@be73caea`, `MemorySummarization.jsx` (via `inputProps['data-testid']` on `Input.StyledInputEnhancer`, forwarded to the underlying `<textarea>` through MUI's `htmlInput` slot). |
| Target Summary Tokens input | `target-summary-tokens-input` | on-automation/testids only (awaiting human promotion to main) | **NEW** — added this session, `EliteaAI/EliteaUI@be73caea`, same file/mechanism as above. Verified unique — a differently-scoped `context-modal-target-summary-tokens-input` exists in a sibling widget (`ContextStrategySummarization.jsx`, the chat-side Context Budget panel), not a collision. |
| Context Management section, Context Management toggle | `context-management-section`, `context-management-toggle` | on-main ✓ | Reused from the covering spec — no change. |

State assertion (per `.agents/testing.md` § Locator policy — state via
`data-*`, not testid-value-switching): N/A here — this case's "disabled"
state is asserted via Playwright's `to_be_disabled()` / `to_be_enabled()`
against the standard HTML `disabled` attribute the product already sets
(`disabled={isSummarizationDisabled}` in `MemorySummarization.jsx`), not a
custom `data-*` state filter. This is the correct compliant shape for a
genuine `disabled`-prop mechanism (contrast with the parent Context
Management toggle, whose "disabled" state is actually a conditional unmount
and is asserted via absence, per the covering AFS).

## Network Behavior
- `PUT /api/v2/social/author/` — fires immediately on every Automatic
  Summarization toggle click (both directions); 200 on success. Same
  autosave endpoint as the parent Context Management toggle — confirmed via
  live network capture (`browser_network_requests` during exploration).
- `GET /api/v2/social/author/` — refetches after the PUT, same pattern as
  the covering spec's `_is_autosave_get_response` already documents. Reuse
  the existing module-level helpers, not new ones.

## Known Defects Found During Exploration
- None found that block this case. The existing clarification
  **[EliteaAI/elitea-testing-public#1238]** already covers this case's route
  drift (Personalization → DEFAULT SUMMARIZATION doesn't exist; live route
  is Settings → Memory) — no new ticket needed, same root cause as the
  sibling ELITEA-2374 case.
- The existing OPEN bug **[EliteaAI/elitea-testing-public#1129]** (numeric
  fields don't autosave when typed into directly) is not exercised by this
  case — it only reads Target Summary Tokens' value and clicks the parent
  Automatic Summarization toggle, never types into the numeric field.

## Blocked Steps
- Case step 5's literal default value (`4096`) could not be verified against
  a pristine account — the shared `${TEST_USER}` account already has a
  persisted value from earlier sessions (test data pollution, not a product
  issue). It happens to read `4096` today, consistent with the case text,
  but automating a hard-coded assertion on that literal would be flaky
  against this shared account's real (mutable) state. AFS step 5 instead
  asserts "a non-empty positive integer" and captures the value for the
  step-8 round-trip check — same treatment as the sibling ELITEA-2374 case's
  identical blocker for Max Context Tokens / Preserve Recent Messages. Not
  filed as a new ticket (test-design/test-data consideration, not a
  case-text-vs-product disagreement).

## Automation Hints
- Framework: Playwright + pytest (`.agents/testing.md`).
- Page object: `automation/pages/user_profile_settings_page.py` — **extend,
  don't duplicate**. Additions made this session:
  1. Two new `LocatorDescriptor` fields: `summarization_instructions_textarea`
     (testid `summarization-instructions-textarea`) and
     `target_summary_tokens_input` (testid `target-summary-tokens-input`).
  2. New helper methods mirroring the existing Context Management ones:
     `is_automatic_summarization_enabled()`, `enable_automatic_summarization()`,
     `disable_automatic_summarization()`, `get_target_summary_tokens()`.
- Test file: `automation/tests/ui/settings/test_context_management_toggle.py`
  — append a new test method to the existing `TestContextManagementToggle`
  class (same file, same class, same module-level autosave-wait helpers).
  Do NOT create a new file or a new test class — this is additive-only per
  the extend-existing mechanics (`.claude/skills/test-automation-implementation/SKILL.md`
  § Phase 3 for extend-existing). Verify with
  `git diff <base>... -- automation/tests/ui/settings/test_context_management_toggle.py | grep -E '^-[^-]'`
  → empty (no modification to the existing test method).
- Use the same dual PUT+GET autosave-wait pattern as the existing test
  (`_is_autosave_get_response` / `_is_autosave_put_response` module-level
  helpers) around every toggle click — the covering test's docstring
  explains why the GET refetch wait matters (race with a second click before
  the first click's refetch resolves).
