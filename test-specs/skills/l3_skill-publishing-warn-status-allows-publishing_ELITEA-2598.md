# Test Case: Skill Publishing — WARN Status Allows Publishing with Warnings

## Metadata
- **TMS ID**: ELITEA-2598
- **Linked Story**: none
- **Priority**: l3 (medium, per case)
- **Environment Explored**: local (`http://localhost:5173`, `EliteaAI/EliteaUI` `automation/testids`)
- **User set**: `${TEST_USER}` (localhost `auth_state` bypass via `VITE_DEV_TOKEN`)
- **Analyst**: qa-engineer
- **Status**: ready-for-automation

## Preconditions
- User is logged in to the Elitea platform (localhost `auth_state`).
- A project exists and is accessible.
- User has the `skills.publish` permission.

## Test Data

> **Case-text drift (filed as clarification, issue #1463 — see § Known
> Defects): live-confirmed the "No Icon Skill" half of the case's premise
> is FALSE.** A skill missing a custom icon returns `status: "FAIL"`
> (`critical_issues`, `source: "deterministic"`), not `"WARN"` — the
> Publish button is DISABLED, contradicting case steps 4/7. Only the
> "Generic Name Skill" half is confirmed live as genuinely WARN-level. This
> AFS automates the LIVE CONTRACT: a single fixture skill with a generic
> name (WARN-level, matches the case) that DOES have a custom icon and a
> tag (both required to avoid FAIL per ELITEA-2595's finding), demonstrating
> the case's actual thesis — a WARN-only issue does not block Publish.

### generate-per-test (in test setup, cleaned up in its own teardown)
- Generic Name Skill: Name `"skill"` (matches case's own example — live-
  confirmed this exact literal string is accepted, no uniqueness collision
  observed this run, but generate a fresh skill each run regardless), valid
  Description (≥50 chars live threshold), valid Instructions (≥100 chars
  live threshold), **one tag** (e.g. `automation`) and **a custom icon**
  (required prerequisites — see the drift note above; pick from the
  project's "Uploaded" gallery via `SkillFormPage.upload_skill_icon_edit_mode()`)
- Version name: `v1.0`; Category: any valid option (`Quality Assurance`
  used this run)

## Test Steps
1. Create a skill with a generic/non-descriptive name (`"skill"`) but valid
   description, instructions, a tag, and a custom icon
   - **Verify**: skill created successfully
2. Ensure the skill has a custom icon set (required — see Test Data drift
   note) and at least one tag (also required)
   - **Verify**: icon `<img>` renders a non-placeholder `src`; tag chip
     visible in the Tags field
3. Open the publish wizard and proceed to Validation step (fill version
   name + category, accept Publishing Terms, click Continue)
   - **Verify**: `POST .../publish_skill_validate/...` fires and resolves
4. Verify validation returns WARN status (not FAIL)
   - **Verify**: response `status` is `"WARN"` — live-confirmed: with a
     valid icon+tag present, only the generic-name issue and the
     "description lacks action verbs" issue remain, both `warnings`, zero
     `critical_issues`
5. Verify warning message mentions generic/non-descriptive name
   - **Verify**: `warnings` list contains an entry with `field: "name"`
     whose `issue` text references the name being generic/placeholder-like
     (live: `"The name is too generic to convey the skill's purpose."` —
     `source: "ai"`, assert via CONTAINS "generic", not exact match)
6. *(Case's original step: "Verify warning message mentions missing custom
   icon" — SKIPPED/replaced.)* Given the icon IS present (required to reach
   WARN at all, per the drift note), there is no "missing icon" warning to
   assert here. Instead, verify the response's `critical_issues` array is
   EMPTY (confirming the fixture correctly cleared the icon/tags CRITICAL
   gates) — this is the corrected assertion that proves the same intent
   the case's original step was after (icon-related state is clean).
7. Verify the "Next" or "Publish" button is still ENABLED
   - **Verify**: the Validation step's "Publish" button (`agent-publish-
     confirm-button`) is enabled (`canPublish = status !== "FAIL"` is
     `true` for `"WARN"`)
8. Proceed to the Publishing step
   - **Verify**: click "Publish"; `POST .../publish_skill/...` fires
9. Complete the publishing process
   - **Verify**: response is 200; wizard closes; success toast shown
10. Verify the skill appears in the Catalog
    - **Verify**: `${BASE_URL}/elitea-catalog?tab=skills` shows the skill
      under its selected Category, after re-selecting the new version by
      name in the VERSION dropdown first (known defect #614 — see AFS
      ELITEA-2595 § Known Defects, reproduces identically here)

## Expected Results
- The fixture skill (generic name, valid content, icon present, tag
  present) returns `status: "WARN"` with zero `critical_issues` and at
  least one `warnings` entry referencing the generic name.
- The Validation step's "Publish" button stays ENABLED throughout.
- Publishing completes successfully (200) and the skill is visible in the
  Catalog afterward.

## Coverage Map

| Case element | Expected result | Covered by (AFS step) | Asserted where | Disposition |
|---|---|---|---|---|
| 1 Create generic-name skill, valid desc/instructions | created successfully | step 1 | `step 1`: skill detail URL reached | asserted |
| 2 Ensure NO custom icon (default) | skill shows default icon | — | — | **clarification** — inverted: live requires icon PRESENT to reach WARN at all; case's "no icon" premise is FALSE (issue #1463) |
| 3 Open publish wizard, proceed to Validation | validation runs and completes | step 3 | `step 3`: validate response captured | asserted |
| 4 Validation returns WARN (not FAIL) | status WARN | step 4 | `step 4`: `status == "WARN"` | asserted |
| 5 Warning mentions generic name | name-related warning text | step 5 | `step 5`: `warnings` field=name, contains "generic" | asserted |
| 6 Warning mentions missing custom icon | icon-related warning text | step 6 | `step 6`: `critical_issues` is empty (corrected — see step 6 note) | **clarification** — case's literal assertion is unautomatable as written (no such warning exists when the icon is present, and the icon must be present to reach WARN); replaced with the equivalent-intent check |
| 7 Next/Publish still enabled | button enabled | step 7 | `step 7`: `is_enabled()` on confirm button | asserted |
| 8 Proceed to Publishing step | user advances | step 8 | `step 8`: publish request fires | asserted |
| 9 Complete publishing | skill published successfully | step 9 | `step 9`: 200 response + toast | asserted |
| 10 Skill appears in Catalog | visible in Skills Studio/Catalog | step 10 | `step 10`: catalog card visible | asserted, *decomposed: version re-select needed first due to #614* |

**Axis 2 — Analyst additions.**
- `step 6` asserts `critical_issues` is empty as the corrected, live-true
  equivalent of the case's "missing icon warning" check — *added: the
  case's literal assertion can never be satisfied (the scenario that would
  produce it — no icon — produces FAIL, not WARN, so the wizard never
  reaches this Validation-step render with that combination); an empty
  `critical_issues` list is the closest same-intent assertion that still
  exercises the icon/tags gate meaningfully.*
- `step 2` note documents the INVERTED prerequisite (icon must be PRESENT)
  — *added: silently keeping the case's literal "no icon" step would either
  desync the test from a passing run (icon absent ⇒ FAIL ⇒ steps 4/7 never
  hold) or require masking, which is forbidden; the AFS states the
  correction explicitly instead.*

## Cleanup
1. Delete the published skill via `SkillAPI.delete_skill(skill_id)` (deletes
   all versions).

## Concrete Handles (discovered during exploration)

Same wizard component/testids as ELITEA-2595 — see that AFS's Handles table
for the full PROVENANCE-verified list. This case additionally uses
`skill-form-icon-button` (icon picker trigger, on `automation/testids`
only) and the icon-gallery "Uploaded" tile selection (no dedicated testid
on gallery tiles observed this run — selected via the existing
`upload_skill_icon_edit_mode()` page-object method's file-chooser path, or
manually via the gallery's first "Uploaded" image if reusing an existing
project icon), plus `catalog-skills-tab` (on `automation/testids` only) for
step 10, plus `catalog-category-section-{slug}` (container testid,
**new — added this round**, EliteaAI/EliteaUI@c80de351, on
`automation/testids` only) — this case's Catalog verification also calls
`get_skill_card(skill_name, category=CATEGORY_NAME)`, the same
category-scoped card check ELITEA-2595 uses, so it shares that testid too.

## Network Behavior
- `POST .../publish_skill_validate/prompt_lib/{project}/{skillId}/{versionId}`
  — `200` (not `422`) for this scenario, `status: "WARN"` in the body. Same
  endpoint/shape as ELITEA-2595 — see that AFS's § Network Behavior.
- `POST .../publish_skill/prompt_lib/{project}/{skillId}/{versionId}` —
  fires on the Validation step's "Publish" click since the button is
  enabled for `WARN`. `200` on success.

## Known Defects Found During Exploration
- **[CLARIFICATION]** filed as
  https://github.com/EliteaAI/elitea-testing-public/issues/1463 — the
  case's "No Icon Skill" scenario is unautomatable as literally written:
  missing a custom icon returns `status: "FAIL"` (blocks Publish), not
  `"WARN"`. This AFS substitutes a corrected fixture (icon present, tag
  present, generic name only) that demonstrates the case's actual thesis
  (a WARN-level issue doesn't block Publish) using the ONE example
  (generic name) that's genuinely WARN-level live. The "missing icon"
  half of the case should be updated in the TMS per the filed
  clarification, or a separate case authored for "missing icon is
  CRITICAL" if that's confirmed as the intended, documented behavior.
- **[MINOR, already tracked]** Known defect #614 reproduces here too — see
  ELITEA-2595's AFS for the full note; automation must re-select the
  published version by name after Publish.

## Blocked Steps
None — the case is automatable via the corrected fixture described above;
nothing is unautomatable, only re-scoped per the live contract.

## Automation Hints
- Framework: Playwright + pytest.
- Page objects/methods: identical to ELITEA-2595 — reuse
  `open_publish_wizard()`, `fill_publish_preparation_step()`,
  `click_publish_continue()`, `confirm_publish()`, plus
  `SkillFormPage.upload_skill_icon_edit_mode()` for the icon and the Tags
  combobox pattern for the tag — this case is effectively ELITEA-2595's
  happy path with an intentionally generic Name substituted in, so most of
  the implementation is shared/extended, not duplicated.
- If the team later re-scopes ELITEA-2598 in the TMS (per the filed
  clarification) to drop the "no icon" example entirely and test ONLY the
  generic-name WARN case, this AFS's steps 1–2 simplify accordingly — no
  structural change needed to steps 3–10.
