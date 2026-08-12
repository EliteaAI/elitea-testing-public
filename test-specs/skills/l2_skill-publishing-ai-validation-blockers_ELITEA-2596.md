# Test Case: Skill Publishing — AI Validation Blockers

## Metadata
- **TMS ID**: ELITEA-2596
- **Linked Story**: none
- **Priority**: l2 (high, per case)
- **Environment Explored**: local (`http://localhost:5173`, `EliteaAI/EliteaUI` `automation/testids`)
- **User set**: `${TEST_USER}` (localhost `auth_state` bypass via `VITE_DEV_TOKEN`)
- **Analyst**: qa-engineer
- **Status**: ready-for-automation

## Preconditions
- User is logged in to the Elitea platform (localhost `auth_state`).
- A project exists and is accessible.
- User has the `skills.publish` permission.

## Test Data
### generate-per-test (in test setup, cleaned up in its own teardown), one skill per scenario
- **Short Content Skill**: Name `short-skill-${uuid}` (unique per run — case's
  literal `short-skill` collides across repeat runs), Description `"Short"`,
  Instructions `"Do it"`
- **Placeholder Skill**: Name `placeholder-skill-${uuid}`, Description
  `"[replace this with actual description]"`, Instructions `"TODO: add
  instructions"` — live-confirmed these ALSO trip the length gate (both are
  under the 50/100-char thresholds — see § Automation Hints), so the
  response includes BOTH a length `critical_issues` entry AND the
  placeholder-marker one; pad both fields with extra prose around the
  placeholder marker if the test wants to isolate the placeholder detection
  from the length gate (this run tested with padding — see § Known Defects
  for the exact response observed)
- **Secrets Skill**: Name `secrets-skill-${uuid}`, Description `"Valid
  description text here"` (padded to ≥50 chars live), Instructions `"Use API
  key: sk-1234567890abcdef and password: MySecretPass123"` (padded to ≥100
  chars live, e.g. appended with unrelated prose, so only the secrets
  detection fires, not also the length gate)

## Test Steps
1. Create a skill with short content (Description `"Short"`, Instructions
   `"Do it"` — both well under the live length thresholds)
   - **Verify**: skill created successfully (Save enabled once Name+
     Description non-empty per ELITEA-2430 — short content is NOT rejected
     at creation time, only at publish-validation time)
2. Open the skill's overflow menu → "Publish" → fill Preparation step
   (version name, category, accept terms) → click Continue
   - **Verify**: `POST .../publish_skill_validate/...` fires
3. Verify the validation error message indicates content is too short
   - **Verify**: response `status` is `"FAIL"`; `critical_issues` contains
     an entry with `field: "description"` whose `issue` text references
     "too short" and the minimum length (live: `"Description is too short
     (min 50 chars)"`), AND an entry with `field: "instructions"` (live:
     `"Instructions are too short (min 100 chars)"`)
4. Verify the "Next" or "Publish" button is disabled
   - **Verify**: the Validation step's "Publish" button (`agent-publish-
     confirm-button`) is disabled (`canPublish = status !== "FAIL"` is
     `false`)
5. Create a second skill with placeholder text (`[replace this]`, `TODO`) in
   description or instructions
   - **Verify**: skill created successfully
6. Repeat step 2's wizard flow for the placeholder skill
   - **Verify**: `POST .../publish_skill_validate/...` fires
7. Verify the validation error message indicates placeholder text detected
   - **Verify**: response `status` is `"FAIL"`; `critical_issues` contains
     an entry (`source: "ai"`) whose `issue` text references a placeholder/
     draft marker (live: `'Contains a draft placeholder marker indicating
     unfinished content ("[replace this with actual description]")'` /
     similar for the TODO instructions) — assert on `field` + `source: "ai"`
     + issue text CONTAINS a placeholder-related phrase, not an exact string
     match (AI-generated wording may vary between runs)
8. Verify the "Next" or "Publish" button is disabled
   - **Verify**: same as step 4
9. Create a third skill with hardcoded secrets/API keys in instructions
   - **Verify**: skill created successfully
10. Repeat step 2's wizard flow for the secrets skill
    - **Verify**: `POST .../publish_skill_validate/...` fires
11. Verify the validation error message indicates secrets/credentials
    detected
    - **Verify**: response `status` is `"FAIL"`; `critical_issues` contains
      an entry (`field: "instructions"`, `source: "ai"`) whose `issue` text
      references credentials/secrets in plain text (live: `"Contains inline
      credentials/secrets in plain text (API key and password), which is
      unsafe and disallowed."`) — same CONTAINS-not-exact-match caveat as
      step 7
12. Verify the "Next" or "Publish" button is disabled
    - **Verify**: same as step 4

## Expected Results
- All three scenarios return `status: "FAIL"` with a `critical_issues` entry
  whose `field`/`issue` matches the case's named defect category.
- The Validation step's "Publish" button is disabled in all three cases.
- Each response ALSO includes `icon`/`tags` critical issues (missing icon,
  missing tags — the fixture skills have neither) — this does not
  contradict the case; assert on the SPECIFIC issue the case names being
  PRESENT in `critical_issues`, not that it's the only entry.

## Coverage Map

| Case element | Expected result | Covered by (AFS step) | Asserted where | Disposition |
|---|---|---|---|---|
| 1 Create short-content skill | created successfully | step 1 | `step 1`: skill detail URL reached | asserted |
| 2 Publish short-content skill → Validation | FAIL status | step 2–3 | `step 3`: response `status == "FAIL"` | asserted |
| 3 Error references min content length | length-requirement text present | step 3 | `step 3`: `critical_issues` field=description/instructions, issue contains "too short" | asserted |
| 4 Next/Publish disabled | button disabled | step 4 | `step 4`: `is_disabled()` on confirm button | asserted |
| 5 Create placeholder skill | created successfully | step 5 | `step 5`: skill detail URL reached | asserted |
| 6 Publish placeholder skill → Validation | FAIL status | steps 6–7 | `step 7`: response `status == "FAIL"` | asserted |
| 7 Error references placeholder text | placeholder-pattern text present | step 7 | `step 7`: `critical_issues` field=description/instructions, `source: "ai"`, issue mentions placeholder | asserted |
| 8 Next/Publish disabled | button disabled | step 8 | `step 8`: same as step 4 | asserted |
| 9 Create secrets skill | created successfully | step 9 | `step 9`: skill detail URL reached | asserted |
| 10 Publish secrets skill → Validation | FAIL status | steps 10–11 | `step 11`: response `status == "FAIL"` | asserted |
| 11 Error references secrets detected | secrets/credentials text present | step 11 | `step 11`: `critical_issues` field=instructions, `source: "ai"`, issue mentions credentials | asserted |
| 12 Next/Publish disabled | button disabled | step 12 | `step 12`: same as step 4 | asserted |

**Axis 2 — Analyst additions.**
- Every scenario's response ALSO carries icon/tags critical issues (fixture
  skills have neither) — *added: documented so the implementer's assertion
  targets the SPECIFIC named issue via list membership, not response
  equality/exact-count, avoiding a brittle test that breaks if the
  icon/tags rule changes independently of this case's actual scope.*
- `source: "deterministic"` vs `source: "ai"` distinction on each
  `critical_issues` entry — *added: this determines whether an exact-text
  or a contains/field-based assertion is appropriate; the short-content
  gate is deterministic (stable exact-ish text), placeholder/secrets
  detection is AI-generated (assert loosely).*

## Cleanup
1. Delete all three fixture skills via `SkillAPI.delete_skill(skill_id)`
   (they never reach Published status, so no separate unpublish step).

## Concrete Handles (discovered during exploration)

Same wizard component/testids as ELITEA-2595 — see that AFS's Handles table
for the full PROVENANCE-verified list (`skill-name-input-field`,
`skill-description-input-field`, `skill-instructions-editor-content`,
`skill-save-button`, `skill-controls-menu-button`, `publish-menuitem`,
`agent-publish-version-name-input`, `agent-publish-category-select`
(*docs(afs) correction, PR #1464 review — no `-combobox` suffix; live source
confirms this per the ELITEA-2595 AFS's own implementer correction*),
`agent-publish-agree-checkbox`, `agent-publish-continue-button`,
`agent-publish-confirm-button`). No additional handles needed for this case
— it never proceeds past the Validation step.

## Network Behavior
- `POST .../publish_skill_validate/prompt_lib/{project}/{skillId}/{versionId}`
  — `422` in all three scenarios (status `"FAIL"`). Same endpoint/shape as
  ELITEA-2595 — see that AFS's § Network Behavior.
- No `publish_skill` request fires in any of the three scenarios (Publish
  stays disabled, case never reaches the Publishing step).

## Known Defects Found During Exploration
None found — all three scenarios behaved exactly per the case's
expectations (FAIL status, specific critical issue present, Publish
disabled). The only cross-cutting note is the SAME icon/tags-are-critical
finding documented in ELITEA-2595's AFS / issue #1463 — it does not affect
THIS case's own assertions (short-content/placeholder/secrets all
independently trigger FAIL regardless of icon/tags state), so it's
informational here, not a blocker.

## Blocked Steps
None.

## Automation Hints
- Framework: Playwright + pytest.
- Page objects/methods: identical to ELITEA-2595 — `open_publish_wizard()`,
  `fill_publish_preparation_step()`, `click_publish_continue()` (returns
  the validate response's status code, mirroring
  `AgentDetailPage.click_publish_continue()`). This case never calls
  `confirm_publish()` — it stops at asserting the Validation step's state.
- Seed the 3 fixture skills via `SkillAPI.create_skill()` for speed and
  determinism (short/placeholder/secrets content is exactly what the case
  specifies, no UI-typing needed) — the case's own steps ("Create a skill
  with...") don't mandate UI creation the way ELITEA-2595's step 1 does.
- Assert on the response BODY (`critical_issues` list, `field`/`source`/
  `issue` keys) captured via `page.expect_response()`, not on the rendered
  DOM text — more stable, and the DOM groups all critical issues into one
  list without a clean per-field selector anyway.
- For the placeholder/secrets `source: "ai"` assertions, use a
  case-insensitive substring match on the KEY phrase (e.g. "placeholder"/
  "TODO", "credential"/"secret"/"API key") rather than exact string
  equality — AI-generated wording is stable in content but not guaranteed
  byte-identical across runs.
