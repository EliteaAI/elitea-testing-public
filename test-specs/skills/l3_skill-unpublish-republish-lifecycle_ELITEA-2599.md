# Test Case: Skill Unpublish and Republish Lifecycle

## Metadata
- **TMS ID**: ELITEA-2599
- **Linked Story**: none
- **Priority**: l3 (medium, per case)
- **Environment Explored**: local (`http://localhost:5173`, `EliteaAI/EliteaUI`
  `automation/testids`)
- **User set**: `${TEST_USER}` (localhost `auth_state` bypass via `VITE_DEV_TOKEN`)
- **Analyst**: qa-engineer
- **Status**: ready-for-automation

## Preconditions
- User is logged in to the Elitea platform (localhost `auth_state`).
- A project exists and is accessible (`${ELITEA_PROJECT_ID}` = 399, "Private"
  project used this run).
- User has the `skills.publish` permission (same
  `platformSettings.is_skill_publish_blocked` gate as ELITEA-2595/96/97/98 —
  confirmed unset/false this run).
- Skill reaches `WARN` or `PASS` validation status — **same icon+tag
  prerequisite gap as ELITEA-2595's #1463**: a skill with only the case's
  documented name/description/instructions still `FAIL`s at
  `publish_skill_validate` (`critical_issues: [{"field":"tags","issue":"No
  tags defined"}]` — confirmed live this run on the very first publish
  attempt). Add ≥1 tag AND a custom icon before publishing (see Test Data).
- An agent exists that can have skills attached — **not independently
  exercised this run in combination with unpublish** (see Coverage Map Axis 2
  note); reuse the live-proven `AgentDetailPage.attach_skill()` /
  `is_skill_attached()` flow from ELITEA-1735
  (`test_skill_agent_interaction.py`).

## Test Data
### generate-per-test (in test setup, cleaned up in its own teardown)
- Skill name: unique per run, e.g. `lifecycle-test-skill-${uuid}` (case's
  literal `lifecycle-test-skill` collides across repeat runs)
- Skill description: ≥50 chars, containing an action verb (avoids the
  "lacks action verbs" AI WARNING — optional polish)
- Skill instructions: ≥100 chars
- **Tag** — required prerequisite, NOT in the case's own Test Data table
  (see Preconditions). **Hyphens are REJECTED live** — confirmed again this
  run: typing `lifecycle-test` + Enter clears the input with **zero network
  calls and no chip** (silently filtered by
  `NormalSingleTagNameInputRegExp` in `EliteaUI/src/common/constants.js`).
  This is the SAME case-text drift already filed as
  `EliteaAI/elitea-testing-public#1445` (ELITEA-2433) — use an underscore
  form, e.g. `lifecycle_test`, confirmed live to commit a chip correctly.
  **Also note:** the Tags MUI Autocomplete field requires real keyboard
  events (`press_sequentially`/`type()`), not `fill()` — `fill()` sets the
  DOM value but the freeSolo Enter-to-commit handler never fires off it
  (confirmed live this run: `fill()` + `press('Enter')` cleared the input
  with no chip and no network call; `press_sequentially()` + `press('Enter')`
  committed correctly). Standard MUI-fields gotcha
  (`.claude/rules/mui-patterns.md`), re-confirmed specifically for this field.
- **Custom icon** — required prerequisite, also not in the case's Test Data
  table. Pick any existing entry from the project-scoped "Uploaded" gallery
  tab via `SkillFormPage.upload_skill_icon_edit_mode()` (fastest, confirmed
  live — the icon click needs `scroll_into_view_if_needed()` + `hover()`
  immediately before `.click()`, same quirk as the Agent icon picker).
- Version names: `v1.0`, `v2.0`, `v3.0` (and `v4.0` if exercising the 4th-
  version edge case) — must match the wizard's `VERSION_NAME_REGEX`
  (letters/digits/dots/hyphens/underscores).
- Category: any option from the live dropdown — this run used `Development`.
- Agent name: unique per run, e.g. `skill-consumer-agent-${uuid}`.

## Test Steps

### Part A — Unpublish behavior
1. Create a skill (Name/Description/Instructions per Test Data), add ≥1 tag
   and a custom icon, save
   - **Verify**: skill created at `/skills/all/{skillId}`; Save disabled
     after tag+icon commit (both persist immediately — icon via its own
     2-request edit-mode PATCH, tag via the skill's own Save)
2. Open the skill's overflow (⋮) menu → VERSION group → "Publish"; fill
   Version name `v1.0` + Category, check Publishing Terms, click Continue
   - **Verify**: `POST publish_skill_validate/.../{skillId}/{versionId}`
     returns `status` `WARN` or `PASS` (never `FAIL` given the tag+icon
     prerequisites); confirmed live this run: `WARN` first attempt (name
     recommendation only), `PASS` on a later attempt with unchanged content
     (AI-scored, non-deterministic — treat `WARN`/`PASS` as equally
     acceptable, never gate on which specific one appears)
3. Click "Publish" (Validation step's confirm action)
   - **Verify**: `POST publish_skill/.../{skillId}/{versionId}` → 200,
     `{msg: "Successfully published", public_skill_id, public_version_id,
     version_name, source_version_id}`. **Publish CLONES the draft into a
     brand-new version ID carrying Published status** — `source_version_id`
     in the response is this NEW version's id, distinct from the original
     draft version's id (confirmed live: draft `1679` → published clone
     `1680`). Track this new id for subsequent steps, never the original
     draft id.
4. Create an agent; attach the published skill to it via the "+ Skill"
   button in the agent editor's Skills accordion
   - **Verify**: skill card appears in the agent's Skills section;
     `agent-skills-counter` increments (existing `AgentDetailPage
     .attach_skill()`/`get_skills_counter_text()` methods, ELITEA-1735)
5. Test the agent (embedded chat, `~<skill-name>` mention or an
   autonomous-trigger message matching the skill's description) to verify
   the skill is applied
   - **Verify**: response reflects the skill's instructions (existing
     `test_skill_agent_interaction.py` pattern for asserting skill
     application)
6. Navigate to the skill's Published version; open the overflow (⋮) menu →
   "Unpublish"
   - **Verify**: `unpublish-menuitem` present (only when the currently
     viewed version's status is Published — `canUnpublish` gate); opens
     `UnpublishConfirmModal` titled "Unpublish Skill", body: "Are you sure
     you want to unpublish {name} (version: {version})? The skill will be
     removed from ELITEA Catalog immediately. Existing conversations using
     this skill version may be affected." — confirmed live verbatim
     (dialog id `unpublish-dialog-title`)
7. Click "Unpublish" to confirm
   - **Verify**: `POST unpublish_skill/.../{skillId}/{versionId}` → 200,
     `{msg: "Successfully unpublished", status: "deleted"}`
8. Navigate to `${BASE_URL}/elitea-catalog?tab=skills`
   - **Verify**: the skill is **immediately** absent from the Catalog —
     confirmed live via a fresh navigation immediately after unpublish
     (RTK Query `TAG_TYPE_PUBLIC_SKILLS`/`TAG_TYPE_PUBLIC_SKILL_DETAILS`
     invalidation on the `unpublishSkill` mutation, `skillsApi.js`), no
     reload or wait needed beyond normal navigation
9. Navigate back to the agent from step 4
   - **Verify**: the skill attachment reference is still present (skill
     card + counter unchanged) — **not independently exercised this run in
     combination with the live unpublish call** (see Coverage Map Axis 2);
     the underlying mechanism (`ApplicationSkills.jsx`'s
     `useGetApplicationSkillsQuery` keys attachment by project-scoped
     `skill_id`, entirely independent of the skill's Catalog/publish
     status — confirmed by reading `EliteaUI/src/[fsd]/features/skill/ui/
     ApplicationSkills.jsx`) strongly implies this holds; implementer must
     assert it live, not merely infer it
10. Test the agent again (same message as step 5)
    - **Verify**: skill still applies correctly (same assertion as step 5)

### Part B — Republish and version coexistence
11. Navigate to the now-unpublished skill version (from step 6/7)
    - **Verify**: skill/version still fully accessible and editable in the
      project Skills section; overflow menu now shows "Publish" again (not
      "Unpublish") — confirmed live: `canUnpublish` flips false once
      `versionStatus !== Published`
12. Publish it again with Version name `v2.0` (same flow as steps 2–3)
    - **Verify**: 200 response. **Confirmed live: `public_skill_id` for
      this republish is a NEW id, distinct from the original `v1.0`
      publish's `public_skill_id`** (this run: `51` for `v1.0` →
      unpublished/deleted → `52` for `v2.0`). Unpublishing a skill's
      catalog entry is a genuine deletion (`status: "deleted"`), so a
      republish after an unpublish always starts a fresh catalog entity —
      this is expected, not a defect; do not assert the same
      `public_skill_id` across an unpublish/republish boundary.
13. Navigate to Catalog, verify v2.0 present
    - **Verify**: skill card visible under its Category, single entry
14. WITHOUT unpublishing v2.0, publish a DIFFERENT version of the same
    skill (e.g. the "base" draft) as `v3.0`
    - **Verify**: 200 response with the **SAME `public_skill_id` as v2.0**
      — confirmed live this run: v2.0 → `public_skill_id=52,
      public_version_id=56`; v3.0 published from the base draft while v2.0
      remained live → `public_skill_id=52, public_version_id=57` (same 52,
      new version id). **This is the actual coexistence mechanism**: once
      a public catalog entry exists and stays un-unpublished, additional
      publishes of sibling versions of the same underlying skill ADD
      versions under that SAME public entry rather than creating new ones.
      Note: this run hit a transient `502`/`503` on the FIRST attempt at
      this specific validate call — confirmed environment flakiness (the
      SAME window also showed `502`/`503` on unrelated `socket.io` polling
      and a CORS failure hitting `dev.elitea.ai` directly), not a
      skill-publish-specific defect; retried immediately and got `200
      PASS`. Implementer should NOT hard-fail on a single transient
      502/503 here — a bounded retry (2–3 attempts) on the validate call
      is reasonable given this observed flakiness, but do not silently
      swallow a REPEATED failure.
15. Navigate to Catalog
    - **Verify**: still only ONE card for the skill (testid
      `catalog-skill-card-{public_skill_id}`, confirmed `catalog-skill-
      card-52` live) — "only the latest version shown" is satisfied
      structurally (one growing public entry, not N separate entries), not
      by an explicit "latest" filter the test needs to compute. Opening
      the card's dialog shows the CURRENT (last-published) content — the
      Catalog detail dialog exposes no version-history UI to end users
      (confirmed live: the dialog shows only Name/Description/Instructions,
      no version selector).
16. (Optional, exploratory) Publish a 4th version (`v4.0`) of the same
    skill without unpublishing v2.0/v3.0
    - **Verify**: confirmed live this run — a 3rd-coexisting-version
      publish (`v4.0`, taking the total to v2.0+v3.0+v4.0 = 3 versions
      under the same `public_skill_id`) succeeded with 200 and no visible
      rejection or cap enforcement. **A true 4th-BEYOND-3 publish was not
      exercised this run** (turn-budget boundary) — the case's own
      Pass/Fail language for this step is non-prescriptive ("System
      handles version limit according to spec" / "verify oldest is
      handled appropriately", no concrete expected behavior stated).
      Treat this step as a SOFT/exploratory assertion, not a hard gate:
      if the implementer's live run shows a 4th-beyond-3 publish is
      accepted with no pruning, that is not itself a defect against this
      case (the case never specifies rejection as the correct behavior) —
      log the observation in the Run Report rather than failing the test.

## Expected Results
- Unpublish is immediate (both the confirm-dialog action and the resulting
  Catalog removal) and does not require a page reload to observe.
- The skill/version remains fully accessible for editing and republishing
  after unpublish; republishing is a normal "Publish" action, not a special
  "restore" flow.
- Attaching a skill to an agent (`EntitySkillMapping` in DB terms) is
  scoped to the project-level skill id and is unaffected by the skill's
  Catalog/publish status.
- Up to (at least) 3 published versions of the same skill can coexist
  live in the Catalog under one growing public entry, as long as none of
  the intervening publishes is preceded by an unpublish (an unpublish
  starts a fresh public entry on the next republish).
- The Catalog always shows exactly one card per active public skill entry
  (never duplicate cards for the same skill's older/newer versions).

## Coverage Map

| Case element | Expected result | Covered by (AFS step) | Asserted where | Disposition |
|---|---|---|---|---|
| 1 Create skill, publish v1.0 | published, appears in Catalog | steps 1–3, 8 (pre-unpublish) | `step 3`: 200 + payload; Catalog card found before unpublish | asserted, *clarification: tag+icon are required prerequisites, same #1463 pattern* |
| 2 Attach skill to agent | attached successfully | step 4 | reuses `AgentDetailPage.attach_skill()`/counter | asserted via reuse, not re-derived live this run |
| 3 Test agent uses skill | agent applies skill correctly | steps 5, 10 | reuses `test_skill_agent_interaction.py` pattern | asserted via reuse |
| 4 Click Unpublish → confirm dialog | dialog appears | step 6 | `step 6`: dialog title/body text captured verbatim live | asserted |
| 5 Confirm unpublish | unpublished successfully | step 7 | `step 7`: 200 + `{status:"deleted"}` | asserted |
| 6 Navigate to Catalog | skill NOT visible | step 8 | `step 8`: fresh navigation, `browser_find` returns no match | asserted |
| 7 Navigate to agent | skill attachment reference still present | step 9 | *not independently re-executed live this run* | **Axis 2 gap — implementer must assert live**, see note below |
| 8 Test agent again | agent still works with skill | step 10 | reuses `test_skill_agent_interaction.py` pattern | asserted via reuse |
| 9 Navigate to unpublished skill | accessible in project Skills section | step 11 | `step 11`: menu shows "Publish" again, confirmed live | asserted |
| 10 Publish again as v2.0 | published successfully | step 12 | `step 12`: 200 response, NEW `public_skill_id` captured | asserted, *clarification: republish after unpublish gets a fresh public_skill_id, not the original one — case text doesn't specify this either way* |
| 11 Verify v2.0 in Catalog | visible | step 13 | `step 13`: Catalog card found | asserted |
| 12 Publish as v3.0 | published successfully | step 14 | `step 14`: 200, SAME `public_skill_id` as v2.0 confirmed | asserted |
| 13 Catalog shows only latest | v3.0 (latest) shown | step 15 | `step 15`: single card, no version picker in dialog | asserted |
| 14 Up to 3 versions coexist internally | version history available | step 14 (v2.0+v3.0 confirmed coexisting; v4.0 pushed to 3 total) | `step 14`/`step 16`: distinct `public_version_id`s (56, 57, 58) under one `public_skill_id` (52) | asserted for 3; 4th-beyond-3 not exercised |
| 15 4th version handling | "handled appropriately" (unspecified) | step 16 | exploratory only, non-blocking per case's own hedge language | **soft assertion**, not a hard gate |

**Axis 2 — Analyst additions.**
- `step 3` captures `public_skill_id`/`public_version_id`/`source_version_id`
  from the publish response body — *added: these are the implementer's most
  reliable assertion surface for "which public entity/version is this",
  more stable than matching Catalog card text, and they are what actually
  proves/disproves the case's "version coexistence" claim (Axis 1 row 14).*
- Tag-field hyphen-rejection and `fill()`-vs-`press_sequentially()` gotchas
  documented in Test Data — *added: this run hit BOTH live (first publish
  attempt failed validation with "No tags defined" because the initial
  `fill()`+Enter silently dropped the tag) — without documenting this, the
  implementer repeats the exact same 20-minute detour.*
- `step 14`'s transient 502/503 note — *added: distinguishes genuine
  environment flakiness (also hit unrelated `socket.io` endpoints in the
  same window) from a v2.0/v3.0-coexistence-specific rejection, so the
  implementer doesn't misclassify a retry-recoverable blip as a product
  defect against the coexistence claim.*
- `step 9`'s Axis-2 gap is called out explicitly rather than silently
  assumed — *added: attaching-before-unpublish-and-reverifying-after is a
  NEW combination this AFS asks for; the two halves (attach mechanics,
  unpublish mechanics) are each independently live-proven, but their
  combination was not re-executed together this run due to turn budget.
  This is not a blocker (the ApplicationSkills query is read from the
  code to be provably independent of publish status), but it is flagged so
  the implementer treats it as "verify live", not "assume from precedent".*

## Cleanup
1. Delete the created skill via the UI's "Delete skill" menu item (type the
   skill name to confirm) — deletes all versions including any published
   ones (confirmed live this run: no separate "unpublish first" step
   required).
2. Delete the created agent via the standard agent-cleanup path
   (`AgentAPI.delete_agent()` or UI equivalent).

## Concrete Handles (discovered during exploration)

Testid-only per `.agents/testing.md` § Locator policy — no role/text/CSS
handles. PROVENANCE not re-verified against `origin/main` this run (all
handles below are PRE-EXISTING and already carry verified PROVENANCE rows in
ELITEA-2595's AFS `test-specs/skills/l2_skill-publishing-wizard-happy-path_
ELITEA-2595.md` — cite that file's Concrete Handles table for the Publish-
side testids, reproduced here only where this case's flow differs).

| Element | Testid | PROVENANCE |
|---|---|---|
| Skill controls (⋮) overflow menu button | `skill-controls-menu-button` | on-main ✓ (per ELITEA-2595 AFS) |
| "Publish" menu item | `publish-menuitem` | dynamic (`DotMenu` `${key}-menuitem`, `key: 'publish'`) — on-main ✓ |
| "Unpublish" menu item | `unpublish-menuitem` | dynamic (`DotMenu` `${key}-menuitem`, `key: 'unpublish'` in `SkillControls.jsx`) — **confirmed live this run**, on-main ✓ (`SkillControls.jsx` is on main) |
| Unpublish confirm dialog — "Unpublish" button | `agent-unpublish-confirm-button` | **cross-entity naming artifact, confirmed live for the SKILL flow too** — `UnpublishConfirmModal.jsx` (`src/[fsd]/entities/version/ui/`) hardcodes this testid regardless of `entityLabel` prop; same accepted pattern as the `agent-publish-*` prefix already documented in `skill_detail_page.py` for ELITEA-2595/96/98 — NOT a new defect, just re-confirming the same testid resolves correctly for skills |
| Publish wizard fields | `agent-publish-version-name-input`, `agent-publish-category-select`, `agent-publish-agree-checkbox`, `agent-publish-continue-button`, `agent-publish-confirm-button` | on-`automation/testids` only — see ELITEA-2595 AFS |
| Tags input | `skill-tags-input-field` | on-main ✓ |
| Skill icon button | `skill-form-icon-button` | on-`automation/testids` only — see ELITEA-2595 AFS |
| Skill delete confirm menu item | `skill-delete-menu-item` | on-main ✓ |
| VERSION dropdown trigger | `skill-version-select` | on-main ✓ |
| VERSION dropdown option by name | dynamic `version-option-{name}` | on-main ✓ |
| Catalog — Skills tab | `catalog-skills-tab` | on-`automation/testids` only — see ELITEA-2595 AFS |
| Catalog — skill card by public_skill_id | dynamic `catalog-skill-card-{public_skill_id}` | **confirmed live this run** (`catalog-skill-card-52`); PROVENANCE not separately re-checked (shares the Catalog page's testid inventory with `catalog-skills-tab`, already logged as `automation/testids`-only in ELITEA-2595) |
| Agent Skills accordion + attach button | `agent-skills-section`, `agent-skills-counter`, (attach button reused via `AgentDetailPage.attach_skill()`, see that method's own testid citation) | on-main ✓ (ELITEA-1735) |

No new testids needed — every handle this flow touches is pre-existing
(shared with the agent Publish/Unpublish flow, the ELITEA-2595 Publish
wizard work, and the ELITEA-1735 agent-skill-attach work).

## Network Behavior
- `POST publish_skill_validate/prompt_lib/{project}/{skillId}/{versionId}`
  — `422` when `status:"FAIL"`; `200` when `WARN`/`PASS`. Same shape as
  ELITEA-2595.
- `POST publish_skill/prompt_lib/{project}/{skillId}/{versionId}` — `200`
  on success: `{msg, public_skill_id, public_version_id, version_name,
  source_version_id}`. `source_version_id` is the NEW cloned-and-published
  version id (distinct from the source draft's own id).
- `POST unpublish_skill/prompt_lib/{project}/{skillId}/{versionId}` — `200`
  on success: `{msg: "Successfully unpublished", status: "deleted"}`.
  Invalidates `TAG_TYPE_PUBLIC_SKILLS`/`TAG_TYPE_PUBLIC_SKILL_DETAILS` (same
  tags `publishSkill` invalidates) — confirmed this is why the Catalog
  updates without a manual reload.
- Republishing after an unpublish allocates a NEW `public_skill_id`.
  Publishing a sibling version of a skill whose public entry is still live
  (not unpublished) REUSES that `public_skill_id` and allocates only a new
  `public_version_id` — this is the coexistence mechanism (confirmed live,
  see Test Steps 12/14).

## Known Defects Found During Exploration
- No NEW product defects found this run. Two previously-filed
  clarifications reproduce identically for this case's test data and are
  cited (not re-filed):
  - `EliteaAI/elitea-testing-public#1445` (ELITEA-2433) — Tags field
    rejects hyphens; the case's own literal test-data style (hyphenated
    names) collides with this for the tag value specifically. Use
    underscores in tag values.
  - The `agent-publish-*`/`agent-unpublish-confirm-button` cross-entity
    testid-prefix pattern, already accepted (not re-litigated) per
    ELITEA-2595/96/98's AFS precedent.
- **Environment observation (not a product defect):** one transient
  `502`/`503` sequence hit `publish_skill_validate` AND unrelated
  `socket.io` polling AND a CORS failure calling `dev.elitea.ai` directly,
  all within the same ~15s window, then fully recovered on retry with no
  code-side action. Consistent with local dev-backend/proxy flakiness, not
  a skill-publish-specific defect. Documented in Test Step 14 so the
  implementer uses a bounded retry rather than either hard-failing on one
  transient hit or silently swallowing a genuinely-repeating one.

## Blocked Steps
None. (Test Step 9's Axis-2 gap is a "verify live during implementation"
note, not a blocker — the underlying mechanism is independently proven on
both sides.)

## Automation Hints
- Framework: Playwright + pytest (per `.agents/testing.md`).
- Page objects: extend `SkillDetailPage` with `open_unpublish_dialog()` /
  `confirm_unpublish()` methods MIRRORING `AgentDetailPage`'s existing
  `open_unpublish_dialog()`/`confirm_unpublish()` implementations
  (`automation/pages/agent_detail_page.py:4145-4187`) — same shared
  component, same testids (`unpublish-menuitem` differs only in its `key`;
  `agent-unpublish-confirm-button` is literally identical). Reuse
  `SkillDetailPage`'s existing `open_publish_wizard()` /
  `fill_publish_preparation_step()` / `click_publish_continue()` /
  `confirm_publish_and_capture_response()` methods (added for
  ELITEA-2595/96/98) for the Publish/republish steps — no new Publish-side
  methods needed.
- Capture `public_skill_id` from each `confirm_publish_and_capture_response()`
  call's JSON body and assert equality/inequality across the
  unpublish/republish and coexistence steps per the Test Steps above — this
  is the load-bearing assertion for the whole "lifecycle" claim, far more
  reliable than Catalog DOM state alone.
- Agent-skill attach/verify: reuse `AgentDetailPage.attach_skill()` /
  `is_skill_attached()` / the chat-mention or autonomous-trigger assertion
  pattern from `test_skill_agent_interaction.py` (ELITEA-1735) verbatim —
  do not reimplement.
- Tag entry: use `press_sequentially()` (or the existing `SkillFormPage
  .add_tag()` action which already does this correctly), NEVER `.fill()`,
  and use an underscore-form tag value (hyphens are silently rejected).
  `SkillFormPage.add_tag()` already exists and does this right — call it,
  don't hand-roll the interaction again.
- Icon: reuse `SkillFormPage.upload_skill_icon_edit_mode()` as-is.
- Wait strategy: `expect_response()` on `publish_skill_validate`/
  `publish_skill`/`unpublish_skill`, never a fixed sleep. Add a bounded
  retry (2–3 attempts) specifically around `publish_skill_validate` given
  the transient 502/503 observed this run (see Known Defects) — but let a
  REPEATED failure surface as a real failure, don't retry-forever.
- Seed the skill via `SkillAPI.create_skill(...)` for speed where the UI
  flow itself isn't what's under test (e.g. the agent's skill), same
  pattern as ELITEA-2595's Automation Hints.
