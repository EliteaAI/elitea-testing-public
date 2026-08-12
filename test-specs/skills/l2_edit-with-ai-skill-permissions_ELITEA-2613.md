
# Test Case: Edit with AI — Skill Permissions (role-gated CTA visibility + optional character limit)

## Metadata
- **TMS ID**: ELITEA-2613
- **Linked Story**: none
- **Priority**: l2
- **Environment Explored**: local (`http://localhost:5173`, EliteaUI `automation/testids`, DEV backend)
- **User set**: `${TEST_USER}` (admin-equivalent in every project it belongs to — see § Blocked Steps;
  **no editor/viewer-role credential exists**, same missing-fixture-primitive already tracked by
  `EliteaAI/elitea-testing-public#1314` for ELITEA-1903/1904)
- **Analyst**: qa-engineer (analyst slot, batch skills-remaining-w4)
- **Status**: ready-for-automation
  (admin-role half — Part A (CTA visible/click/close) and Part D (character-limit enforcement) — fully
  explored and automatable end-to-end; Editor-role half (Part B) and Viewer-role half (Part C) are a
  genuine test-data/environment gap, identical in shape to the already-accepted ELITEA-1903/1904
  precedent. Per SKILL.md, `blocked` is reserved for when the analyst cannot complete meaningful
  automation at all; here the RBAC-gating mechanism plus the character-limit contract are both fully
  provable on the reachable role, and the gap for the other two roles is scoped and tracked, not
  silently skipped.)

## Preconditions
- `${TEST_USER}` is authenticated via the `auth_state` fixture (localhost `VITE_DEV_TOKEN` bypass — no
  Keycloak login form on localhost).
- Acting project: `${ELITEA_PROJECT_ID}` (Private, id `399`) — where `${TEST_USER}` is admin-equivalent.
- At least one existing, published skill accessible to `${TEST_USER}` in that project (case's
  `permission-test-skill` fixture doesn't exist; any existing skill serves the identical assertion —
  live-verified against `test-publish-skill-7461bfae`, skill id `1788`).

## Test Data
### reuse-existing
- `${TEST_USER_EMAIL}` / `${TEST_USER_PASSWORD}` — admin-equivalent (owner) in the default private
  project; used for Part A and Part D.
- `${ELITEA_PROJECT_ID}` = `399` (Private) — where Part A/D run.
- Any existing skill in that project (no dedicated `permission-test-skill` fixture is required — the
  CTA-visibility mechanism is identical for any skill the role can view).

### missing (blocks Part B / Part C — see § Blocked Steps)
- No `EDITOR_TEST_USER_EMAIL`/`EDITOR_TEST_USER_PASSWORD` or `VIEWER_TEST_USER_EMAIL`/
  `VIEWER_TEST_USER_PASSWORD` (or equivalent) exists in `.env.test` or `.agents/profile.md` § Roles &
  sample users. Same gap tracked by `EliteaAI/elitea-testing-public#1314`.

## Test Steps

### Part A — Admin Role — CTA Visible (live-executed)

1. Authenticate as `${TEST_USER}` via `auth_state` (admin-equivalent role).
   - **Verify**: dashboard/app shell loads (`Elitea is connected` status, side-bar visible).
2. Navigate to `/skills/all`, open any existing skill's detail page.
   - **Verify**: `/skills/all/{id}?viewMode=owner&name={name}` loads; the General section is present.
3. Verify "Edit with AI" CTA/button is visible in the General section header.
   - **Verify**: `edit-skill-with-ai-button` is visible.
4. *(same as case step 4)* Click "Edit with AI".
   - **Verify**: `ai-edit-skill-modal` opens, heading "Edit with AI" is present, prompt phase shown
     (`Generate Draft` initially disabled — empty prompt).
5. *(same as case step 5, folded into step 4's verification above — see Coverage Map)*
6. Close the wizard.
   - **Verify**: pressing `Escape` (or `ai-edit-skill-close-button`) dismisses `ai-edit-skill-modal`;
     zero console errors after close (checked live: 0 errors/8 total messages).

### Part B — Editor Role — CTA Visible

7–11. *(Blocked — no live editor-role login path. See § Blocked Steps.)*

### Part C — Viewer Role — CTA Hidden

12–15. *(Blocked — no live viewer-role login path. See § Blocked Steps.)*

### Part D — (Optional) Character Limit Enforcement (live-verified via source + existing wizard handles)

16. Log in as Admin (`${TEST_USER}`).
    - **Verify**: same as step 1.
17. Open "Edit with AI" for a skill with existing instructions, fill a non-empty prompt, click
    `Generate Draft`.
    - **Verify**: `ai-edit-skill-generate-button` triggers `POST
      /api/v2/elitea_core/generate_skill_draft/prompt_lib/{projectId}` → `200`, wizard phase reached
      (reuse `AIEditSkillModalPage.click_generate_and_wait_for_response()` from ELITEA-2611's page
      object — already exercises this exact call).
18. Advance through General → Instructions → Summary (`ai-edit-skill-wizard-next-button`).
    - **Verify**: `ai-edit-skill-step-indicator` shows "3. Summary"; `ai-edit-skill-summary-instructions-input`
      is visible and editable.
19. Fill `ai-edit-skill-summary-instructions-input` with 5,010 characters (10 over the ACTUAL live limit
    — see Clarification below).
    - **Verify**: `.input_value()` length is exactly **5,000**, not 5,010 — the field silently truncates
      at the browser/DOM level via a native `maxLength` attribute (`SummaryStep.jsx:99`,
      `inputProps={{ maxLength: MAX_INSTRUCTIONS_LENGTH, ... }}`).
20. Attempt to save (`ai-edit-skill-wizard-save-button`).
    - **Verify**: Save succeeds with the truncated (≤5,000-char) value — there is no separate
      over-limit error/block path; the truncation itself IS the enforcement (no distinct "Apply/Save is
      blocked" state to assert, per source read — see Clarification).

## Expected Results
- Part A: the "Edit with AI" button is present, visible, and functional for the admin-equivalent
  `${TEST_USER}` — **live-confirmed** this run (button click resolved to
  `page.getByTestId('edit-skill-with-ai-button')`, opened `ai-edit-skill-modal` with heading "Edit with
  AI").
- Part B/C (editor/viewer): per source-code confirmation only (NOT live-verified — same inference class
  as ELITEA-1903/1904): the CTA's visibility is gated by `checkPermission(...)` reading
  `GET /api/v2/auth/permissions/prompt_lib/{project_id}`; editor conventionally holds the update
  permission and sees the button, viewer conventionally lacks it and doesn't. This is an inference, not
  an executed observation — flagged explicitly so it is never reported as asserted.
- Part D: **Clarification, not a defect** (case-text drift — filed
  [elitea-testing-public#1480](https://github.com/EliteaAI/elitea-testing-public/issues/1480)). The
  ACTUAL character limit is **5,000**, not 2,500 as the case text states
  (`MAX_INSTRUCTIONS_LENGTH = 5000`, `EliteaUI/src/common/constants.js:68`), and enforcement is
  **silent truncation via a native HTML `maxLength` attribute**, not a validation error message or a
  blocked Save — confirmed identical at both the wizard's editable Instructions field
  (`AIEditSkillModal.jsx:215`) and the Summary step's merged input (`SummaryStep.jsx:99,107`). The
  live product is correct; the case's numeric threshold and "error message" framing are stale.

## Coverage Map

| Case element | Expected result | Covered by (AFS step) | Asserted where | Disposition |
|---|---|---|---|---|
| 1 Log in as Admin | Login successful | step 1 | side-bar + connected status visible | asserted |
| 2 Navigate to project + Skills section | Skills list loads | step 2 | `/skills/all` loads, skill cards render | asserted |
| 3 Open skill's detail page | Skill detail page loads | step 2 | `/skills/all/{id}` loads, General section visible | asserted |
| 4 Verify "Edit with AI" CTA visible (Admin) | Button present and enabled | step 3 | `edit-skill-with-ai-button` visible | asserted |
| 5 Click "Edit with AI" | Wizard opens successfully | step 4 | `ai-edit-skill-modal` visible, heading "Edit with AI" | asserted |
| 6 Close the wizard | Wizard closes | step 6 | modal dismissed via Escape/close button; 0 console errors | asserted |
| 7 Log out, log in as Editor | Login successful | — | — | blocked *(no editor credential exists — § Blocked Steps)* |
| 8 Navigate to same project/skill (Editor) | Skill detail page loads | — | — | blocked *(depends on 7)* |
| 9 Verify CTA visible (Editor) | Button present and enabled | — | — | blocked *(depends on 7)* |
| 10 Click "Edit with AI" (Editor) | Wizard opens | — | — | blocked *(depends on 7)* |
| 11 Close the wizard (Editor) | Wizard closes | — | — | blocked *(depends on 7)* |
| 12 Log out, log in as Viewer | Login successful | — | — | blocked *(no viewer credential exists — § Blocked Steps)* |
| 13 Navigate to same project/skill (Viewer) | Skill detail page loads read-only | — | — | blocked *(depends on 12)* |
| 14 Verify CTA NOT visible (Viewer) | Button hidden/absent | — | — | blocked *(depends on 12)* |
| 15 Verify no edit capabilities available (Viewer) | Page is view-only | — | — | blocked *(depends on 12)* |
| 16 Log in as Admin/Editor (Part D) | Login successful | step 16 | same as step 1 | asserted (Admin half only) |
| 17 Open "Edit with AI", generate suggestions | Suggestions displayed | step 17 | `generate_skill_draft` 200, wizard phase reached | asserted |
| 18 Manually edit Suggested instructions field | Field is editable | step 18 | `ai-edit-skill-summary-instructions-input` visible/editable | asserted |
| 19 Enter text exceeding limit | Text is entered | step 19 | `.input_value()` — asserted TRUNCATED, not entered raw (see Clarification) | asserted, with clarified expected value |
| 20 Verify character limit is enforced | Error message or truncation at 2,500 chars | step 19 | truncated at **5,000**, not 2,500 — clarification [#1480](https://github.com/EliteaAI/elitea-testing-public/issues/1480) | asserted, with clarified limit |
| 21 Verify cannot proceed with over-limit content | Apply/Save blocked or error shown | step 20 | no such block exists — truncation IS the enforcement, Save succeeds with the truncated value (see Clarification) | asserted, with clarified mechanism |

**Axis 2 — Analyst additions:**
- Part A step 6 also asserts zero new console errors after closing the wizard — *added: a silent
  console error on dismissal (e.g. an unhandled state-reset exception) would pass a bare "modal is
  gone" check but still be a real regression signal.*
- Part D step 19 asserts the exact truncated length (`== 5000`) rather than a vague "is truncated" —
  *added: an off-by-one truncation boundary (4999/5001) would slip through a loose
  `len(value) < 5010` check.*

## Cleanup
- Part A: modal closed via Escape without generating a draft or saving — no skill mutation.
- Part D: the wizard's Save is exercised with a throwaway 5,000-char instructions block on the target
  skill's CURRENT version — **implementer must restore the skill's original instructions afterward**
  (`PUT /api/v2/elitea_core/skill/prompt_lib/{projectId}/{skillId}` with the pre-test value, or use a
  dedicated disposable skill created and deleted within the test rather than mutating a shared fixture
  skill). Not yet executed live this run (Part D step 20's Save was not clicked during analysis — see
  Automation Hints) so no live mutation occurred in this pass; flagged for the implementer regardless.

## Concrete Handles (discovered during exploration)

| Element | Locator (testid-only) | PROVENANCE | Fallback |
|---|---|---|---|
| Skill detail — "Edit with AI" open button | `LocatorDescriptor(testid="edit-skill-with-ai-button")` — **existing field**, `ai_edit_skill_modal_page.py` `open_button` | on-main ✓ (confirmed live 2026-08-12, `page.getByTestId('edit-skill-with-ai-button')` resolved and clicked) | none — testid-only |
| Edit with AI modal | `LocatorDescriptor(testid="ai-edit-skill-modal")` — existing field, `modal` | on-main ✓ | none |
| Modal close button | `LocatorDescriptor(testid="ai-edit-skill-close-button")` — existing field, `close_button` | on-main ✓ (per ELITEA-2611 AFS) | none |
| Generate Draft button | `LocatorDescriptor(testid="ai-edit-skill-generate-button")` — existing field, `generate_button` | on-main ✓ | none |
| Wizard step indicator | `LocatorDescriptor(testid="ai-edit-skill-step-indicator")` — existing field, `step_indicator` | on-main ✓ (ELITEA-2611/2612) | none |
| Wizard Next button | `LocatorDescriptor(testid="ai-edit-skill-wizard-next-button")` — existing field, `next_button` | on-main ✓ | none |
| Wizard Save button | `LocatorDescriptor(testid="ai-edit-skill-wizard-save-button")` — existing field, `wizard_save_button` | on-main ✓ | none |
| Summary step — merged Instructions input | `LocatorDescriptor(testid="ai-edit-skill-summary-instructions-input")` — existing field, `summary_instructions_input` | on-main ✓ — **already carries the native `maxLength=5000` HTML attribute** (`SummaryStep.jsx:99`), so Part D needs NO new testid work | none |

No new testid work is required for this case (Part A + Part D) — every handle touched already exists
as a page-object field, including the character-limit assertion target.

## Network Behavior
- Skill detail load / project switch triggers `GET /api/v2/auth/permissions/prompt_lib/{project_id}` —
  the authoritative source for whether `edit-skill-with-ai-button` renders at all. Not independently
  re-confirmed for the Skill entity this run (ELITEA-1903 confirmed the identical mechanism for the
  Agent entity's sibling button, same permission-array-driven `checkPermission` pattern) — implementer
  should treat as `blocked`-if-flaky rather than assume without checking, though no divergence is
  expected (same `entities/edit-entity-with-ai/` shell backs both).
- `POST /api/v2/elitea_core/generate_skill_draft/prompt_lib/{projectId}` — Part D's generate call,
  already exercised and documented by ELITEA-2611's AFS (same endpoint, edit-mode payload shape).
- `PUT /api/v2/elitea_core/skill/prompt_lib/{projectId}/{skillId}` — Part D's Save call (`useSaveSkill`)
  — not live-exercised this analysis pass; implementer confirms on first automation run.

## Known Defects Found During Exploration
None found. Part D's character-limit number/mechanism mismatch is a CLARIFICATION (case-text drift),
not a defect — filed as
[elitea-testing-public#1480](https://github.com/EliteaAI/elitea-testing-public/issues/1480). Reverse-
masking guard applies: assert the live 5,000-char/silent-truncation contract, not the stale 2,500/error-
message case text.

## Blocked Steps

**Steps 7–15 (Editor-role and Viewer-role verification) are blocked — no live editor/viewer-role login
path exists**, identical gap and identical remediation to `EliteaAI/elitea-testing-public#1314`
(ELITEA-1903/1904):

1. **Credential gap confirmed still current** (re-checked fresh this session, not carried over
   unchecked). `grep -iE "viewer|editor|role"` over `automation/.env.test` and `.agents/profile.md` §
   Roles & sample users returns nothing beyond `${TEST_USER}` (admin-equivalent). No
   `EDITOR_TEST_USER_*`/`VIEWER_TEST_USER_*` pairs, and no Keycloak-admin credential to provision one
   out-of-band.
2. Settings → Users on project `400` carries leftover pending-invite `editor`/`viewer` rows from an
   unrelated batch-edit-user-role fixture (per ELITEA-1903's prior finding) — never accepted, no known
   password, not usable as a real login. Not re-verified live this pass (ELITEA-1903 already
   established this dead end exhaustively for the identical rows; re-treading it would not surface new
   information).
3. Self-downgrading `${TEST_USER}`'s own role, or mutating shared project-role state, rejected for the
   same reason as ELITEA-1903/1904: no verified rollback path, and project `400` is shared fixture data
   another merged suite depends on.
4. **What unblocks this:** a dedicated `EDITOR_TEST_USER_EMAIL`/`EDITOR_TEST_USER_PASSWORD` and
   `VIEWER_TEST_USER_EMAIL`/`VIEWER_TEST_USER_PASSWORD` fixture pair — real Keycloak accounts
   provisioned with fixed roles in a stable, non-shared project — added to `.env.test` +
   `.agents/profile.md` § Roles & sample users. Tracked centrally at
   `EliteaAI/elitea-testing-public#1314` (commented this run to link ELITEA-2613 as a third blocked
   case). Once unblocked, Part B/C are a straightforward extension of the same
   `test_skill_edit_with_ai_role_visibility.py` module Part A lands in: login as editor/viewer → open
   the same skill → assert `edit-skill-with-ai-button` visible (editor) / `not_to_be_visible()`
   (viewer).
5. **What is NOT blocked:** the case's core mechanism — RBAC-gated visibility of the "Edit with AI"
   button — is fully verified for the admin-equivalent role via live UI observation (Part A), and the
   character-limit contract (Part D) is fully verified via source + an existing, already-testid'd
   handle. Automating Part A + Part D now is real, honest coverage of two authenticated points on this
   case's contract, not a stand-in for the whole case.

## Automation Hints
- Framework: Playwright + pytest (per `.agents/testing.md`).
- Page objects: `SkillDetailPage` (navigate to `/skills/all/{id}`) + `AIEditSkillModalPage`
  (`open_button`, `modal`, `close_button`, `generate_button`, `step_indicator`, `next_button`,
  `wizard_save_button`, `summary_instructions_input`, `click_generate_and_wait_for_response()`) — all
  pre-existing from ELITEA-2611/2612, no new fields needed.
- Suggested test module: new file `tests/ui/skills/test_skill_edit_with_ai_role_visibility.py` — mirrors
  the naming/structure ELITEA-1903/1904 recommended for the Agent-entity sibling
  (`test_agent_build_with_ai_role_visibility.py`), keeping RBAC-visibility concerns separate from the
  happy-path/navigation-error modules already covering the same page object.
- Part D can be a second test in the same module, or its own
  `test_skill_edit_with_ai_character_limit.py` — it shares no assertions with the RBAC-visibility tests
  beyond the shared page objects.
- Part D's fill-5010-chars step: use `.fill()` on `summary_instructions_input` with a 5,010-char string,
  then read `.input_value()` — Playwright's `.fill()` on a native `<input maxlength=...>` respects the
  browser's own truncation, so no manual slicing is needed in the test; the assertion IS the truncation
  proof.
- Wait strategy: no network wait needed for the CTA-visibility assertion itself —
  `expect(open_button).to_be_visible()` after skill-detail page load is sufficient (Playwright
  auto-wait covers the post-permissions-fetch render, same as ELITEA-1903's admin-role button).
- If the lead/implementer decides to pursue an API-level editor/viewer substitute (mirroring
  ELITEA-1903 § Blocked Steps option b — asserting a role's `GET
  /api/v2/auth/permissions/prompt_lib/{id}` response for the update permission), that would live in
  `tests/api/`, not this UI module.
