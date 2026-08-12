# Test Case: Skill Publishing — Token Invalidation and TTL Expiration

## Metadata
- **TMS ID**: ELITEA-2597
- **Linked Story**: none
- **Priority**: l2 (high, per case)
- **Environment Explored**: local (`http://localhost:5173`, `EliteaAI/EliteaUI`
  `automation/testids`) UI + direct API calls against the DEV backend
  (`https://dev.elitea.ai/api/v2`, same backend localhost proxies to)
- **User set**: `${TEST_USER}` (localhost `auth_state` bypass via `VITE_DEV_TOKEN`)
  for the UI portion; `ELITEA_API_TOKEN` bearer for the direct-API exploration
  probes
- **Analyst**: qa-engineer
- **Status**: ready-for-automation

## Preconditions
- User is logged in to the Elitea platform (localhost `auth_state`).
- A project exists and is accessible (`${ELITEA_PROJECT_ID}` = 399, "Private"
  project used this run).
- User has the `skills.publish` permission (same precondition as ELITEA-2595's
  AFS — `usePublishSkill.hooks.js`'s `platformSettings.is_skill_publish_blocked`
  gate, confirmed unset/false this run).
- Skill reaches `WARN` or `PASS` validation status — **same icon+tag
  prerequisite gap as ELITEA-2595/#1463**: a skill with only 100+-char
  description/instructions still returns `FAIL` (`validation_token: null`) at
  `publish_skill_validate` — the token this case tests is only ever minted on
  a non-`FAIL` result. Add ≥1 tag AND a custom icon before validating (see
  Test Data).
- Two browser tabs/windows on the SAME skill (per case precondition) — this
  run additionally confirmed the mechanism live via direct API calls against
  the SAME skill/version (both approaches trigger identical backend
  behaviour: the server has no concept of "tab", only "skill version modified
  since token was issued").

## Test Data
### generate-per-test (in test setup, cleaned up in its own teardown)
- Skill name: unique per run, e.g. `elitea-2597-token-probe-${uuid}`
- Skill description: ≥50 chars (live-confirmed threshold, same as ELITEA-2595
  — the case's own "100+ characters" figure is not the actual gate)
- Skill instructions: ≥100 chars (live-confirmed threshold)
- **Custom icon** — required to avoid FAIL; pick any existing "Uploaded"
  gallery entry via `SkillFormPage.upload_skill_icon_edit_mode()` (fastest —
  reuses an existing gallery item, no fresh file upload needed) or a fresh
  upload from `test-data/images/skill-fork-test-icon.png`.
- **At least one tag** — required to avoid FAIL; add via
  `skill-tags-input-field` (type + `Enter` — confirmed live this run the tag
  is NOT committed until `Enter` is pressed; a `.fill()`-only leaves an
  uncommitted text fragment and the tag chip never appears).
- Modified instructions text: any string that still exceeds the 100-char
  instructions threshold but differs from the original (case's "Modified
  Instructions" field) — used for Part A's re-save.
- Version name: any string matching `VERSION_NAME_REGEX`
  (`^[a-zA-Z0-9._-]{1,50}$`) — this run used `v1.0-token-probe` / `v1.0-ttl-probe`.
- Category: any option from the live dropdown — this run used `Quality Assurance`.
- Token TTL: **confirmed live = 300 seconds (5 minutes)**, matching the
  case's stated value exactly (see § Concrete Handles — token format).

## Test Steps

### Part A — Token invalidation on modification
1. Create a skill with valid content (description ≥50 chars, instructions
   ≥100 chars, ≥1 tag, custom icon) — see Preconditions/Test Data
   - **Verify**: skill saved successfully (`toast-message` "Skill saved")
2. Open the skill's overflow ("Skill" ⋮) menu → VERSION group → "Publish";
   fill Preparation step (version name, category, Publishing Terms checkbox);
   click "Continue"
   - **Verify**: `POST .../publish_skill_validate/...` returns `200` with
     `status` `WARN` or `PASS` and a non-null `validation_token` string
3. **Without closing the wizard**, open the SAME skill in a second
   tab/context and modify the instructions text; Save
   - **Verify**: second-tab save succeeds (`toast-message` "Skill saved");
     first tab's wizard is untouched (still showing the pre-modification
     Validation-step summary — it does not live-refresh)
4. Return to the first tab/wizard (still on the Validation step, holding the
   now-stale `validation_token`) and click "Publish"
   - **Verify**: `POST .../publish_skill/...` returns **`400`**, body
     `{"error": "validation_token_invalid", "msg": "Agent was modified since
     validation. Please re-validate."}` (see § Known Defects for the
     "Agent"-wording note); the SAME message renders inline in the dialog;
     the "Publish" button becomes **disabled**; the wizard stays on the
     Validation step (does NOT auto-reset to Preparation, does NOT
     auto-refire the validate call)
5. Verify the user cannot proceed without re-validating
   - **Verify**: the only available action is "Cancel" (closes the wizard);
     re-opening Publish from the overflow menu runs a fresh Preparation →
     Validation cycle against the now-current (modified) content

### Part B — Token TTL expiration (5 minutes)
6. Using a skill already at `WARN`/`PASS` (reuse or recreate), open the
   Publish wizard, complete Preparation, click "Continue"
   - **Verify**: `200` response, `validation_token` captured; note the
     token's embedded issuance timestamp (see § Concrete Handles) or the
     wall-clock time of this response
7. Wait **more than 300 seconds (5 minutes)** without touching the skill or
   the wizard
   - **Verify**: no client-side action needed; this is real elapsed
     wall-clock time — see § Automation Hints for why this is NOT a
     `sleep()`/`waitForTimeout()` anti-pattern in this specific case
8. Click "Publish" (still holding the now-expired token, skill unmodified)
   - **Verify**: `POST .../publish_skill/...` returns **`400`**, body
     `{"error": "validation_token_invalid", "msg": "Validation token
     expired. Please re-validate before publishing."}` — same `error` code
     as Part A, **different `msg`**, confirming the backend distinguishes
     "modified" from "expired" as separate causes of the same error family;
     the same message renders inline in the dialog; "Publish" becomes disabled
9. Verify the user must re-validate
   - **Verify**: same as step 5 — Cancel + reopen is the only path forward.

## Expected Results
- Part A: publishing with a token whose skill version was modified after
  validation fails with a clear, user-visible error
  (`validation_token_invalid` / "...modified since validation...");
  Publish is blocked; user must restart validation.
- Part B: publishing with a token older than 300s (5 min) fails with a
  clear, user-visible error (`validation_token_invalid` / "...token
  expired..."); Publish is blocked; user must restart validation.
- Both mechanisms are enforced **server-side** (confirmed via direct
  `publish_skill` calls, independent of which UI tab/context issued the
  request) — not a client-only/spoofable check.

## Coverage Map

| Case element | Expected result | Covered by (AFS step) | Asserted where | Disposition |
|---|---|---|---|---|
| Part A.1 Create skill, valid content | created and saved | step 1 | `step 1`: toast "Skill saved" | asserted, *clarification: icon+tag also required to avoid FAIL — same #1463 gap as ELITEA-2595* |
| Part A.2 Open wizard, reach Validation step | validation passes | step 2 | `step 2`: `200` + `status != FAIL` + non-null `validation_token` | asserted |
| Part A.3 Second tab, modify + save | skill updated | step 3 | `step 3`: toast "Skill saved" in second context | asserted |
| Part A.4 Attempt publish from first tab | error: token invalid due to modification | step 4 | `step 4`: `400` + `error: validation_token_invalid` + exact `msg` text, confirmed **live this run** | **CONFIRMED live**, asserted |
| Part A.5 Restart validation required | user must re-validate | step 5 | `step 5`: Publish disabled, only Cancel available | asserted |
| Part B.6 Create/reach Validation step | validation passes | step 6 | `step 6`: `200` + `validation_token` captured | asserted |
| Part B.7 Wait 5+ minutes | TTL exceeded | step 7 | `step 7`: real elapsed time, no assertion (setup step) | asserted |
| Part B.8 Attempt publish after TTL | error: token expired | step 8 | `step 8`: `400` + `error: validation_token_invalid` + exact `msg` text, confirmed **live this run** (waited 330s) | **CONFIRMED live**, asserted |
| Part B.9 Re-validation required | user must re-validate | step 9 | `step 9`: same as step 5 | asserted |

**Axis 2 — Analyst additions.**
- `step 4`/`step 8` assert on the exact response `error`/`msg` pair, not
  just the HTTP status — *added: the case's Pass criteria say "clear error
  messages", and the two failure causes share the same `error` code
  (`validation_token_invalid`) but different `msg` text — a status-code-only
  assertion can't distinguish "modified" from "expired", so the implementer
  needs the `msg` string as the real assertion surface.*
- `step 4` also asserts the wizard does NOT silently reset to Preparation or
  auto-refire validation — *added: discovered live that "reset to validation
  step" (case's expected result wording) actually means "stays on the
  Validation step showing an inline error with Publish disabled", not a
  visible state transition — the implementer should not build a wait for a
  step-transition that doesn't happen.*
- Direct-API confirmation (bypassing the UI for the token capture / stale
  reuse) is NOT part of the automated test itself (the case is a UI case)
  — *added only to the AFS as exploration evidence that the enforcement is
  server-side, not a UI-only guard a user could bypass via devtools.*

## Concrete Handles (discovered during exploration)

Testid-only per `.agents/testing.md` § Locator policy — every UI handle this
flow touches is **identical to ELITEA-2595's Publish-wizard set** (same
`PublishWizardModal.jsx`, `entityLabel="skill"`); not re-listed in full here,
see `test-specs/skills/l2_skill-publishing-wizard-happy-path_ELITEA-2595.md`
§ Concrete Handles for the complete PROVENANCE table. No NEW testids needed
for this case — Part A/B only exercise the SAME Preparation/Validation-step
elements plus reading the inline error text, which reuses the wizard's
existing error-display node (no separate testid needed beyond what ELITEA-2595
already captured; the implementer asserts on message TEXT via the existing
Validation-step summary region, not a new locator).

### `validation_token` format (new discovery, not in ELITEA-2595's AFS)
Confirmed live (two independent tokens captured, skill 1579/version 1663):
```
eD1D6u5aBVKfspJxEp9dCzlWRNHtUwpckrT6VTssrDE=:1663:51acfab8adc226ce3a160c2e7e5b7f6f23cdd77716df43b4ea35a45dda346ab4:1786516851
m-_qd1DShKkuWpwkY1z6TvzM6HdbLc21awzb24pm7D4=:1663:2aed19f92a176fdfecb52f895170b47107af3d377be7c9790f235a882c6bc596:1786517035
```
Colon-delimited 4-part opaque token: `<base64 signature>:<version_id>:<hex
hash>:<unix timestamp>`. The trailing segment is confirmed (via
`date -u +%s` cross-check at the moment of each `publish_skill_validate`
call) to be the **token issuance Unix timestamp**, matching the response's
wall-clock arrival time to within ~1s both times. This is the mechanism the
TTL check almost certainly uses server-side (issuance time embedded in the
token; publish presumably rejects when `now - issued_at > 300`). Treat this
as an OPAQUE string in automation — never parse/reconstruct it; a forged
token (even with a correct trailing timestamp) would fail the signature
check with the SAME `validation_token_invalid`/generic-invalid error, not a
distinguishable one, since the hash covers the whole payload.

## Network Behavior
- `POST .../publish_skill_validate/prompt_lib/{project}/{skillId}/{versionId}`
  — payload `{version_name, category}`; `422` when `status: "FAIL"` (body
  has `validation_token: null`); `200` when `"WARN"`/`"PASS"` (body has a
  non-null `validation_token` string). Same endpoint/shape as ELITEA-2595.
- `POST .../publish_skill/prompt_lib/{project}/{skillId}/{versionId}` —
  payload `{version_name, category, validation_token}` (per the OpenAPI
  schema `SkillPublishRequest`, `validation_token` is technically optional/
  nullable at the schema level, but the live server still enforces the
  invalidation/TTL check when a stale one IS sent — confirmed this run;
  omitting the field entirely was NOT tested, out of scope for this case
  which only exercises the stale/expired-token paths the case text names).
  **Confirmed responses this run:**
  - Fresh, unmodified, unexpired token → `200` (see ELITEA-2595's AFS for
    the happy-path response shape).
  - Token whose skill version was modified after issuance → `400`
    `{"error": "validation_token_invalid", "msg": "Agent was modified
    since validation. Please re-validate."}`
  - Token older than 300s (confirmed with a 330s wait), skill unmodified →
    `400` `{"error": "validation_token_invalid", "msg": "Validation token
    expired. Please re-validate before publishing."}`

## Known Defects Found During Exploration
- **[MINOR/CLARIFICATION]** The Part-A error message text says **"Agent was
  modified since validation"** on the SKILL publish flow (`msg` field,
  confirmed live verbatim) — a cross-entity copy artifact from the shared
  `PublishWizardModal.jsx`/backend validator being agent-first (same root
  cause noted in ELITEA-2595's AFS for testid naming: `agent-publish-*`
  testids are reused verbatim for skills). This does NOT block or
  mislead the mechanism — the error is still clearly a "your content
  changed, re-validate" message — so it does not fail the case's Pass
  criteria ("clear error messages are shown"), but the wording is
  objectively wrong for the Skill entity. Filed as
  https://github.com/EliteaAI/elitea-testing-public/issues/1465 (MINOR bug,
  not functionally blocking — dedup-checked against the open `bug` list
  first, no existing match for this wording).
- Same icon+tag prerequisite gap already tracked as
  https://github.com/EliteaAI/elitea-testing-public/issues/1463
  (filed during ELITEA-2595's analysis) reproduces identically here — not
  re-filed, this AFS's Preconditions/Test Data account for it directly.

## Blocked Steps
None — both Part A and Part B were executed live to a definitive pass/fail
result this run (see § Network Behavior for the exact captured responses).

## Automation Hints
- Framework: Playwright + pytest (per `.agents/testing.md`).
- Page objects: reuse `SkillDetailPage`'s Publish-wizard methods from
  ELITEA-2595's implementation (`open_publish_wizard()` /
  `fill_publish_preparation_step()` / `click_publish_continue()` /
  `confirm_publish()`) — Part A/B need NO new page-object methods beyond
  possibly a `get_publish_error_message()` reader for the inline Validation-
  step error text (reuse the existing Validation-step summary region locator
  from ELITEA-2595 rather than adding a new testid — the error renders in
  the same node the WARN/PASS summary already occupies).
- Part A (modification): use a **second `BrowserContext`/page** (Playwright
  supports opening a second tab in the same context, or a fresh context if
  isolation from the first tab's auth state matters — this run used a second
  MCP browser tab against the SAME localhost session, which is sufficient
  since both tabs share Keycloak/`auth_state`) to modify the skill while the
  first page's wizard stays open. Do NOT use `SkillAPI` PUT for the
  modification step — this run found the `/skill/{mode}/{project}/{skillId}/
  {versionId}` PUT endpoint's `version.instructions` nested-update did not
  visibly persist via a naive payload in exploratory API probing (the UI
  Save path used instead worked correctly and is what this AFS validates) —
  use the real UI Save action for the modification, exactly like the case's
  own Step 4 describes, rather than trying to shortcut it via API.
- Part B (TTL, 5-minute wait): **this is a declared, deliberate exception to
  the "no sleep/waitForTimeout" convention** (`.agents/conventions.md` §
  Hard don'ts) per the declared-improvisation protocol
  (`.agents/role-overrides.md` § Every role). That rule exists to forbid
  brittle UI-synchronization waits substituting for a proper condition wait
  — it does not and cannot apply to a test whose OWN subject is "does the
  server enforce a 300-second TTL", where waiting real wall-clock time is
  the correct tool, not a workaround. Mark the test
  `@pytest.mark.slow` (existing marker, `.agents/testing.md` § Markers) and
  document the reasoning in the test's docstring, mirroring this AFS
  paragraph. Use `time.sleep(310)` (a small margin over the confirmed 300s
  TTL — this run used 320s/330s successfully) rather than a Playwright wait
  primitive, since no page state changes during the wait (there's nothing to
  condition-wait ON — the "condition" is the wall clock crossing 300s past
  the captured token's issuance moment). Consider running Part B's TTL test
  as its own separate test function (not combined with Part A) so a CI
  timeout budget or `-m "not slow"` filter can exclude it independently.
- Seed via `SkillAPI.create_skill(name, description, instructions)` for the
  base content (same optimization ELITEA-2595's AFS recommends), then use
  the UI for icon/tag/publish exactly as ELITEA-2595 does — this run
  confirmed both flows (UI-created via ELITEA-2595's own fixture skill and a
  fresh `SkillAPI.create_skill()`-seeded skill) reach the same `WARN`
  validation state via the same icon+tag prerequisite.
- Wait strategy for steps 2/4/6/8: `expect_response()` on
  `publish_skill_validate` / `publish_skill`, never a fixed sleep — same
  pattern as ELITEA-2595. Step 7's wait is the sole, deliberate exception
  above.
- Cleanup: `SkillAPI.delete_skill(skill_id)` in a `try/finally` — confirmed
  this run deletes cleanly regardless of the skill's publish/validation
  state (no separate unpublish step required, same as ELITEA-2595's AFS).
