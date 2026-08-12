# Test Case: Agent with Skills — Validation Attribution and Token Invalidation

## Metadata
- **TMS ID**: ELITEA-2601
- **Linked Story**: none
- **Priority**: l2 (high, per case frontmatter)
- **Environment Explored**: local (`http://localhost:5173`, EliteaUI `automation/testids`
  branch → DEV backend, project `Private` / `${ELITEA_PROJECT_ID}`=399), model:
  Anthropic Claude 4.5 Sonnet
- **User set**: `${TEST_USER}` (on localhost, `auth_state` fixture skips login via
  `VITE_DEV_TOKEN`)
- **Analyst**: qa-engineer (Sage), analyst slot
- **Status**: `ready-for-automation` — case executed end-to-end live against the real
  system. **Not `extend-existing`**: this case's two behaviours are each genuinely new
  scenarios relative to the two closest merged/trunk siblings — `ELITEA-2600` (agent +
  skills publishing flow) seeds all 3 skills with valid ≥100-char content and never
  exercises a mixed valid/invalid skill set, per-skill error attribution, or
  skill-removal-fixes-validation; `ELITEA-2597` (skill publish token invalidation) tests
  the **SKILL** entity's own content-edit trigger, never the **AGENT** entity's
  skill-attach/detach trigger. Both are close analogues (reused directly for handles and
  the underlying "modified since validation" mechanism) but neither's merged test
  asserts what this case asserts — see Coverage Map disposition column and the
  boundary-call note in `test-case-analysis` § Classify findings ("if the gap is large
  enough that the extension would be a near-rewrite... treat as ready-for-automation").
  **One sub-step NOT independently confirmed live** — see § Blocked Steps / Automation
  Hints: Part B's *removal*-triggers-invalidation direction (case steps 17–18) was not
  cleanly isolated this run (a test-data confound — see below); the *addition*-triggers-
  invalidation direction (steps 13–15) **was** confirmed live with full evidence
  (network status + exact response body). No product defects found; two genuinely new
  discoveries beyond ELITEA-2600/2597's AFS documented below.

## Preconditions
- User is logged in to the Elitea platform with Admin or Editor role (on localhost,
  `auth_state` fixture skips login).
- A project exists and is accessible (`Private`, id `399` in this run).
- The Skills and Agents sections are available in the project.
- User has publishing permissions for agents — confirmed live (same as ELITEA-1892/2600):
  the "Publish" menu item rendered enabled in the agent's VERSION actions menu.
- Two browser tabs/windows available for testing (Part B) — this run used two Playwright
  MCP tabs against the SAME localhost session (shared `auth_state`), matching the
  pattern ELITEA-2597's AFS already validated as sufficient (no separate browser context
  needed — the backend has no concept of "tab", only "version modified since token was
  issued").

## Test Data

### generate-per-test (in test setup, cleaned up in its own teardown)
- Valid skill name: kebab-case, e.g. `valid-skill-2601` (or with a random suffix per
  ELITEA-2600's pattern to avoid cross-run collisions). Description: any non-empty
  string. Instructions: **≥100 characters, no placeholder text** — this run used a
  169-char instructions string that also proves invocation (`"...reply with the single
  word CONFIRMED..."`), reusable as an optional chat-mention checkpoint if the
  implementer wants extra confidence, though this case's Pass criteria don't require it.
- Invalid skill name: e.g. `invalid-skill-2601`. Description: a placeholder string, e.g.
  `[TODO]`. Instructions: **short (well under 100 chars) AND containing placeholder
  text**, e.g. `"[TODO] short."` (13 chars, this run) — **deliberately trips BOTH
  Critical rules at once** (see Test Steps step 4/Axis 2 below: this is a NEW discovery
  beyond ELITEA-2600's AFS, which only ever tripped the length rule alone). Skill
  **creation itself does not validate content quality** — confirmed live this run: the
  invalid skill saved successfully with no client or server-side rejection; only the
  AGENT-level publish validation gate inspects it.
- Additional skill name (`extra-skill` in the case text): any valid skill with the same
  ≥100-char / no-placeholder content shape as the "valid" skill above. **This run reused
  the already-created invalid skill as the attach/detach probe for economy** — this is
  a defensible substitution for Part B's *addition*-triggers-invalidation direction
  (step 13–15), since the mechanism under test is agent-version-modification generically,
  not skill content quality — but it produces a **confound for the *removal* direction**
  (steps 17–18): re-validating with the reused invalid skill still attached returns
  `Critical: 2` (validation FAIL) rather than a clean pass, so a subsequent "Publish
  disabled because of a stale token" observation can't be cleanly distinguished from
  "Publish disabled because validation itself failed." **Automation should seed a
  DEDICATED, separately-valid `extra-skill` (its own ≥100-char, no-placeholder content)
  for the attach/detach probe** to avoid this confound and let the removal direction be
  asserted cleanly — this AFS's own live run did not re-attempt it with a fresh valid
  skill (turn-budget cutoff), so **the implementer's Execute phase must confirm step
  17–18 live** before asserting it in code (see § Blocked Steps).
- Agent name: e.g. `validation-test-agent-2601`. Description: any non-empty,
  substantive text (Warning-level gate only, not Critical). **Instructions:
  CORRECTION (implementer, confirmed live this dispatch — this AFS's original
  claim that Description/Instructions are "Warning-level gates only, not
  Critical" is WRONG for Instructions specifically):** the agent's OWN
  `instructions` field is independently subject to the SAME ≥100-char
  "too short" Critical rule a skill's content is (memory:
  `skill_publish_ai_gate_rejects_blanket_reply_instructions.md` § "The
  ≥100-char length gate applies to the AGENT's OWN instructions too" —
  ELITEA-2600 already confirmed this finding; this AFS repeated the stale
  claim). An 88-char Instructions string tripped a THIRD, agent-level
  Critical issue (`context: None`) alongside the 2 skill-attributed ones this
  case's Part A targets, muddying the per-skill-attribution count. Seed
  Instructions at ≥100 chars, same threshold as any skill fixture. At least 1
  Tag (e.g. `automation`) — **Critical** gate (same ELITEA-1892/2600 finding:
  `tags: No tags defined` blocks Publish).
- Publish wizard Version name: any string matching `VERSION_NAME_REGEX`
  (`^[a-zA-Z0-9._-]{1,50}$`), unique per publish attempt in the same session (this run
  used `v1-elitea-2601` / `v2-elitea-2601` / `v3-elitea-2601` across three wizard
  openings — **confirmed live: re-opening the wizard always starts a fresh, EMPTY
  Preparation step**, not a resumed one, matching ELITEA-2597's AFS finding for the
  Skill flow). Category: any option (this run used `Quality Assurance`).

## Test Steps

### Part A — Validation Attribution to Skill Context

1. Create a valid skill with proper content (≥100 chars instructions, no placeholders).
   - **Verify**: skill created successfully, redirected to `/skills/all/{id}`.
2. Create an invalid skill with validation issues (short content AND placeholder text
   in the SAME instructions field).
   - **Verify**: skill created successfully — confirmed live, **skill creation itself
     performs NO content-quality validation**; the invalid skill saves exactly like a
     valid one, redirected to `/skills/all/{id}`.
3. Create an agent, add ≥1 tag (Critical publish gate, same as ELITEA-1892/2600), attach
   both the valid and invalid skills via the "+ Skill" popper (one at a time — the
   popper closes after each selection and the `N/5 skills added.` counter must be
   polled until it changes before reopening for the next attach, per the existing
   `AgentDetailPage.attach_skill()` pattern).
   - **Verify**: agent created with 2 skills attached; `Skills` counter reads `2/5
     skills added.` and lists both skill names with `base` version.
4. Open the agent publish wizard (overflow menu → VERSION group → "Publish"); fill
   Version name + Category, accept Publishing Terms, click "Continue" to proceed to the
   Validation step.
   - **Verify**: `POST publish_validate/prompt_lib/{project}/{versionId}` fires;
     Validation step renders a `SUMMARY:` panel.
5. Review the validation findings.
   - **Verify — CONFIRMED LIVE, new discovery beyond ELITEA-2600's AFS.** Validation
     returned `Critical Issues (2)` — **TWO distinct Critical issues, both attributed to
     the SAME invalid skill by name**, not one: `"skills [skill: invalid-skill-2601]:
     Skill content is too short (min 100 chars)"` (Fix: expand instructions, currently
     13 chars) AND `"skills [skill: invalid-skill-2601]: Skill content contains
     placeholder text"` (Fix: replace placeholder text with actual instructions).
     ELITEA-2600's AFS only ever tripped the length rule in isolation (its skill was
     short but not placeholder-text); this run confirms the placeholder-text rule is a
     **separate, independently-attributed** Critical check, not a variant wording of the
     length rule. `Publish` button (`agent-publish-confirm-button`) disabled.
6. Verify the error is attributed to the specific skill with issues.
   - **Verify — CONFIRMED, same evidence as step 5**: both Critical issue lines carry
     the literal `skills [skill: invalid-skill-2601]:` prefix — exact attribution
     format the case's Pass criteria require (`context: skill: <name>`).
7. Verify the valid skill does not show validation errors.
   - **Verify — CONFIRMED LIVE.** `valid-skill-2601` appears ONLY in the non-blocking
     `Suggestions (2)` section (`"skills [skill: valid-skill-2601]: Consider making
     skill names and instructions more descriptive..."`) — zero Critical or Warning
     entries reference it. A Suggestion is informational, not an error; this satisfies
     the case's "no errors attributed to the valid skill" checkpoint precisely (an
     implementation should assert absence from Critical/Warning text, not absence from
     the summary entirely, since a Suggestion mentioning the valid skill by name IS
     expected and correct).
8. Remove the invalid skill from the agent (hover the skill card → `aria-label="remove
   skill"` icon button, testid `skill-card-remove-button` scoped inside the
   `skill-card-{id}` container — **this testid is NOT unique across cards, must be
   scoped by the parent `skill-card-{skill_id}` container**; a confirmation dialog
   follows, "Are you sure to remove the {name} skill from agent?", confirmed via the
   shared `delete-confirm-button` testid). The existing `AgentDetailPage.remove_skill(
   skill_name)` page-object method already implements this exact flow — reuse it
   directly, no new method needed.
   - **Verify — CONFIRMED LIVE.** Removal is immediately persisted server-side (the
     `Save` button stays disabled after removal — confirmed live, it is NOT a
     pending-edit that needs an explicit Save, same "live-persisted" shape
     `attach_skill()` already has); `Skills` counter drops to `1/5 skills added.`
9. Re-run validation (reopen the Publish wizard from the overflow menu — this always
   starts a fresh Preparation step per the Test Data note above).
   - **Verify — CONFIRMED LIVE.** With only `valid-skill-2601` attached, validation now
     returns `Critical: 0` / `Warnings: 4` / `Suggestions: 2` (the same non-blocking
     agent-level gaps ELITEA-2600's AFS documents: no action-verb description, no
     custom icon, empty welcome message, no conversation starters); `Publish` button
     becomes **enabled**.

### Part B — Token Invalidation on Skill Changes

10. With the agent's Publish wizard open on the Validation step (from step 9, holding a
    valid, non-expired `Critical: 0` token), do **not** close it.
    - **Verify**: wizard remains open, `Publish` enabled (state carried over from step 9).
11. In a **second browser tab**, open the same agent (`/agents/all/{agent_id}?destTab=
    configuration&viewMode=owner` — the `destTab=configuration` query param is REQUIRED;
    navigating to the bare `/agents/all/{id}` URL loads the Chat tab, not the
    configuration/Skills panel — confirmed live, a genuine gotcha for automation).
    - **Verify**: agent editor opens with the current skill list (`1/5 skills added.`,
      only `valid-skill-2601`).
12. Attach an additional skill to the agent from the second tab (`extra-skill` in the
    case text — see Test Data note on using a dedicated, valid-content skill rather
    than reusing the invalid one).
    - **Verify**: skill attached successfully; `Skills` counter increments in the
      SECOND tab (`2/5 skills added.`). **The FIRST tab's background page does NOT
      live-refresh** — confirmed live, it still shows `1/5 skills added.` and the stale
      wizard summary; this is expected (case's own step 14 "Wizard is still showing"),
      not a defect.
13. Return to the first tab (publish wizard still open on the Validation step) and
    attempt to click "Publish".
    - **Verify — CONFIRMED LIVE, full evidence captured.** `POST publish/prompt_lib/
      {project}/{versionId}` returns **`400`**, body `{"error": "validation_failed",
      "msg": "Agent was modified since validation. Please re-validate."}` — **new
      discovery beyond ELITEA-2597's AFS: the AGENT entity's "modified since
      validation" error code is `validation_failed`, NOT `validation_token_invalid`**
      (the code ELITEA-2597 documented for the SKILL entity's equivalent case).
      ELITEA-2597 separately filed a MINOR defect
      (https://github.com/EliteaAI/elitea-testing-public/issues/1465) about the SKILL
      flow's error `msg` wrongly saying "Agent" instead of "Skill" — this run confirms
      the wording is in fact CORRECT for the AGENT entity (this is genuinely an agent,
      so "Agent was modified..." is accurate here), which also explains WHY that
      wording exists: the shared `PublishWizardModal.jsx`/backend validator is
      agent-first, and the Skill flow's `msg` was never re-templated for the Skill
      entity. The same message renders inline via the `alert` role /
      `publish-wizard-error-alert` testid (pre-existing, shared with the Skill flow —
      `EliteaAI/EliteaUI@2dafb537` on `automation/testids`, added by ELITEA-2597's
      implementer, confirmed still present and reused unmodified for the Agent flow).
      `Publish` button becomes **disabled** (`agent-publish-confirm-button[disabled]`).
14. Verify the wizard behaviour on rejection.
    - **Verify — CONFIRMED LIVE.** The wizard stays on the Validation step (does NOT
      auto-reset to Preparation, does NOT auto-refire validation) — same shape
      ELITEA-2597's AFS documents for the Skill flow's Part A.
15. Restart the validation process (Cancel, reopen Publish from the overflow menu).
    - **Verify — CONFIRMED LIVE.** Reopening always starts a fresh, EMPTY Preparation
      step (Version-name input empty) — a NEW `publish_validate` call fires on the next
      "Continue" click, evaluating the agent's CURRENT (post-modification) state.
16. **NOT independently confirmed this run — implementer must verify live before
    asserting in code (see Test Data confound note + § Blocked Steps).** After
    validation passes again (Critical: 0, with the additional skill now genuinely
    attached and counted), in the second tab REMOVE a skill from the agent (via
    `AgentDetailPage.remove_skill()`, same method as step 8).
    - **Expected** (per the case text and the SAME "any modification since validation"
      mechanism confirmed for addition in step 13 — the trigger is almost certainly
      version-modification-generic, not addition-specific, since `remove_skill()`
      persists immediately just like `attach_skill()` does): attempting Publish from
      the first tab should return the SAME `400` `validation_failed` /"Agent was
      modified since validation" response. **This inference is grounded in the
      confirmed mechanism, not independently observed** — flag as such if reused
      verbatim; re-run live during implementation.
17. Verify the user must re-validate (same as step 15).

## Expected Results
- Part A: validation errors for a skill with content-quality issues are attributed to
  that specific skill BY NAME, in the literal format `skills [skill: <name>]: <issue>`
  — confirmed for BOTH the "too short" and "contains placeholder text" rules
  independently. A valid skill attached to the same agent shows zero Critical/Warning
  entries (Suggestions naming it by name are expected and non-blocking). Removing the
  invalid skill and re-validating clears the Critical issues and enables Publish.
- Part B: a `validation_token`-bearing wizard held open in one tab is invalidated by a
  skill attachment made to the SAME agent version in a second tab — confirmed via a
  real `400 validation_failed` response with an exact, inline-rendered error message.
  The wizard does not auto-recover; the user must Cancel and restart Preparation→
  Validation from scratch. The removal direction is expected (not yet independently
  confirmed) to behave identically.

## Coverage Map

### Axis 1 — Case coverage

| Case element | Expected result | Covered by (AFS step) | Asserted where | Disposition |
|---|---|---|---|---|
| 1 Create valid skill | Skill created | step 1 | redirect to `/skills/all/{id}` | asserted |
| 2 Create invalid skill | Skill created (creation itself does not validate content) | step 2 | redirect to `/skills/all/{id}`, no client/server rejection | asserted |
| 3 Create agent, attach both skills | Agent created with 2 skills attached | step 3 | `2/5 skills added.` counter | asserted |
| 4 Open publish wizard, reach Validation | Validation runs | step 4 | `publish_validate` fires, `SUMMARY:` panel renders | asserted |
| 5 Review validation findings | FAIL status (Critical issues present) | step 5 | `Critical Issues (2)`, both named | asserted, *with a discovery: 2 independently-attributed Critical rules, not 1 (Axis 2)* |
| 6 Error attributed to specific skill | `skill: invalid-skill-2601` in the message | step 6 | literal `skills [skill: invalid-skill-2601]:` prefix on both Critical lines | **CONFIRMED live**, asserted |
| 7 Valid skill shows no errors | No errors for `valid-skill-2601` | step 7 | zero Critical/Warning entries; only a Suggestion names it | **CONFIRMED live**, asserted |
| 8 Remove invalid skill | Skill detached | step 8 | counter drops to `1/5 skills added.` | asserted |
| 9 Re-run validation | Validation passes | step 9 | `Critical: 0`, Publish enabled | **CONFIRMED live**, asserted |
| 10 Valid skill(s) only, validation passes | Validation passes | step 9 (reused) | same as above | asserted |
| 11 Keep wizard open | Wizard remains open | step 10 | wizard state unchanged across tab switch | asserted |
| 12 Open agent in new tab | Agent editor opens | step 11 | second tab shows agent config with current skill list | asserted, *gotcha noted: requires `destTab=configuration` (Axis 2)* |
| 13 Attach a new skill (second tab) | Skill attached | step 12 | second tab's counter increments; first tab does NOT live-refresh | asserted |
| 14 Return to first tab, wizard still showing | Wizard is still showing | step 12 (verify) | first tab unchanged, stale summary still visible | asserted |
| 15 Attempt to publish (first tab) | Token-invalid error | step 13 | `400` + exact `{error, msg}` body, confirmed live | **CONFIRMED live**, asserted |
| 16 Restart validation | New validation runs | step 15 | reopened wizard starts fresh Preparation | **CONFIRMED live**, asserted |
| 17 Remove a skill (second tab), after re-validation passes | Skill detached | step 16 | *(not independently confirmed this run — inferred from steps 8+13's confirmed mechanisms)* | **NOT independently confirmed** — implementer must verify (see Blocked Steps) |
| 18 Attempt to publish (first tab) after removal | Token-invalid error (removal cause) | step 16/17 | *(same as above)* | **NOT independently confirmed** — implementer must verify |

### Axis 2 — Analyst additions

- `step 5` asserts the "content is too short" and "contains placeholder text" rules
  fire as TWO SEPARATE, independently-attributed Critical issues on the same skill —
  *added: ELITEA-2600's AFS only ever tripped the length rule; this run's deliberately
  dual-failing test data (short AND placeholder) proves the placeholder-text detector
  is a genuinely distinct rule, not a wording variant, which is load-bearing for the
  implementer's assertion shape (assert on BOTH issue texts, not just one).*
- `step 11`'s exact navigation URL (`?destTab=configuration&viewMode=owner`) is
  asserted as a precondition, not just descriptive prose — *added: a bare
  `/agents/all/{id}` navigation lands on the Chat tab, silently NOT showing the Skills
  section the test needs to interact with; an implementer following the case text
  literally ("open the same agent") would hit this gap.*
- `step 13` asserts the exact response `error` CODE (`validation_failed`) in addition
  to the `msg` text — *added: this is a genuinely new data point vs ELITEA-2597's AFS,
  which documented `validation_token_invalid` for the analogous SKILL-entity case. The
  two entities use DIFFERENT error codes for functionally the same "stale token"
  condition — asserting only the msg text (as ELITEA-2597 does) would miss this; the
  implementer should assert both.*
- `step 13` also cross-references and CONTEXTUALIZES ELITEA-2597's already-filed MINOR
  defect (#1465, the Skill flow's `msg` wrongly saying "Agent") — *added: this run's
  confirmation that "Agent was modified..." is the CORRECT/native wording for the
  actual Agent entity closes the loop on why that copy-paste artifact exists; no new
  defect filed, this is explanatory cross-linking only.*

## Cleanup
1. Delete the agent via `AgentAPI.delete_agent(agent_id)` (cookie-auth) in a
   `try/finally`.
2. Delete the 2 (or 3, if a dedicated `extra-skill` is seeded per the Test Data note)
   skills via `SkillAPI.delete_skill(skill_id)` (cookie-auth), same `try/finally`.
3. This run's scratch entities (left on the DEV backend, not cleaned up by the analyst
   — same precedent as ELITEA-2600's AFS, `.agents/testing.md` § Test data strategy):
   skill `1626` (`valid-skill-2601`), skill `1627` (`invalid-skill-2601`), agent `9135`
   (`validation-test-agent-2601`, base version id `9409`, never actually published —
   Publish was rejected both times it was attempted (Part B's whole point), so the
   agent remains in Draft state with no published Catalog entry to also clean up).

## Concrete Handles (discovered during exploration)

Locator policy: testid-only (`.agents/testing.md` § Locator policy,
`.agents/role-overrides.md`). **All rows below are pre-existing testids — no
`add-data-testid` work needed for this case.**

| Element | Testid | Provenance | Notes |
|---|---|---|---|
| Skill Name input | `skill-name-input-field` | on-`automation/testids` (pre-existing) | `SkillFormPage` |
| Skill Description input | `skill-description-input-field` | on-`automation/testids` (pre-existing) | |
| Skill Instructions editor | `skill-instructions-editor-content` | on-`automation/testids` (pre-existing) | CodeMirror content node |
| Skill Save button | `skill-save-button` | on-`automation/testids` (pre-existing) | |
| Agent Name input | `agent-name-input` | on-`automation/testids` (pre-existing) | `AgentFormPage` |
| Agent Description input | `agent-description-input` | on-`automation/testids` (pre-existing) | |
| Agent Instructions input | `agent-instructions-input` | on-`automation/testids` (pre-existing) | |
| Agent Tags input | `agent-tags-input` | on-`automation/testids` (pre-existing) | type + Enter commits the tag chip (same as ELITEA-2597's finding for the Skill Tags field) |
| Agent Save button | `agent-save-button` | on-`automation/testids` (pre-existing) | |
| Skills section container | `agent-skills-section` | on-`automation/testids` (pre-existing) | |
| "+ Skill" button | `agent-add-skill-button` | on-`automation/testids` (pre-existing) | |
| Skill-attach popper item | `[data-testid="toolkit-menu-item"]` scoped inside the popper, filtered by name | on-`automation/testids` (pre-existing) | same shared popper as toolkit attach |
| Skills counter text | `agent-skills-counter` | on-`automation/testids` (pre-existing) | `N/5 skills added.` |
| Attached skill card (dynamic) | `[data-testid="skill-card-{skill_id}"]` | on-`automation/testids` (pre-existing) | already used by `AgentDetailPage.is_skill_attached()`/`remove_skill()` |
| Skill card remove button | `skill-card-remove-button` (`aria-label="remove skill"`) | on-`automation/testids` (pre-existing) | **NOT unique across cards** — must be scoped inside its parent `skill-card-{id}` container; hover-revealed (not visible until the card is hovered) |
| Remove-confirmation dialog confirm button | `delete-confirm-button` (shared, generic confirm-dialog testid) | on-`automation/testids` (pre-existing) | dialog text: `"Are you sure to remove the {name} skill from agent?"` |
| Agent actions overflow menu | `agent-actions-menu-button` | on-`automation/testids` (pre-existing) | |
| Publish menu item | `publish-version-menuitem` | on-`automation/testids` (pre-existing, runtime-constructed) | |
| Publish wizard version-name input | `agent-publish-version-name-input` | on-`automation/testids` (pre-existing) | |
| Publish wizard category select | `agent-publish-category-select-combobox` | on-`automation/testids` (pre-existing) | dynamic option: `select-option-{Category Name}` |
| Publish wizard agree checkbox | `agent-publish-agree-checkbox` | on-`automation/testids` (pre-existing) | |
| Publish wizard Continue button | `agent-publish-continue-button` | on-`automation/testids` (pre-existing) | |
| Publish wizard Publish/confirm button | `agent-publish-confirm-button` | on-`automation/testids` (pre-existing) | disabled both on validation-FAIL and on a rejected-publish attempt (confirmed live both states) |
| Publish wizard inline error alert | `publish-wizard-error-alert` | on-`automation/testids` (pre-existing — `EliteaAI/EliteaUI@2dafb537`, added by ELITEA-2597's implementer for the shared `PublishWizardModal.jsx`) | **confirmed live this run: reused unmodified for the Agent flow** — same component, no new testid needed |

## Network Behavior
- `POST .../elitea_core/publish_validate/prompt_lib/{project}/{versionId}` — fires on
  wizard "Continue". `critical_issues[]` entries carry `field: "skills"` with a
  `[skill: <name>]` prefix in the rendered text when an attached skill's own content
  fails a quality rule. **Confirmed live this run: the "too short" and "contains
  placeholder text" checks are independent Critical rules** — a skill failing both
  produces two separate `critical_issues[]` entries, not one combined message.
- `POST .../elitea_core/publish/prompt_lib/{project}/{versionId}` — `200` on success
  (not exercised to success in this run — both publish attempts were deliberately
  against a stale/modified token). **`400` when the version was modified since the
  validation token was issued**, body `{"error": "validation_failed", "msg": "Agent
  was modified since validation. Please re-validate."}` — **confirmed live, exact
  response body captured via `browser_network_request`**. Note the `error` code
  (`validation_failed`) DIFFERS from the SKILL entity's equivalent case
  (`validation_token_invalid`, per ELITEA-2597's AFS) — see Axis 2.
- Skill attach/detach on an agent (`AgentDetailPage.attach_skill()`/`remove_skill()`)
  persists immediately server-side — no separate agent Save needed, confirmed live
  both directions (Save button stays disabled after either action).

## Known Defects Found During Exploration
None. Both discoveries in this AFS (dual independent Critical rules; the
`validation_failed` vs `validation_token_invalid` error-code split between entities)
are the platform behaving correctly and consistently, documented here as
automation-relevant test-data/assertion guidance, not defects. ELITEA-2597's
already-filed MINOR wording defect (#1465) is cross-referenced, not duplicated or
re-filed.

## Blocked Steps
**Part B steps 16–18 (removal-triggers-invalidation) — NOT independently confirmed
live this run.** This run's attempt to isolate the removal direction was confounded by
reusing the same content-invalid skill as both the Part A probe AND the Part B
attach/detach probe: re-attaching it in the second tab meant the subsequent
re-validation returned `Critical: 2` (a genuine FAIL) rather than a clean pass, so a
"Publish disabled" observation at that point can't be attributed specifically to
token staleness vs validation failure. Not a product blocker — the *addition* direction
of the identical mechanism IS confirmed with full live evidence (step 13), and
`remove_skill()` is confirmed to persist immediately (step 8), which is the same
persistence shape `attach_skill()` has (confirmed to trigger invalidation in step 13) —
so the removal direction is very likely to behave identically. **The implementer's
Execute phase (Phase 3 of `test-automation-implementation`) must re-run this specific
sub-flow live** (seed a dedicated, content-valid `extra-skill`, validate-passes, attach
it, re-validate-passes-again, THEN remove it in the second tab, THEN attempt publish
from the first tab) before asserting the `400`/`validation_failed` result in code —
this is a live-verification obligation carried forward, not a guess to codify blind.

## Automation Hints
- Framework: Playwright + pytest (per `.agents/testing.md`).
- Page objects: `SkillFormPage` (skill create), `AgentFormPage`/`AgentDetailPage` (agent
  create, `attach_skill()`, `remove_skill()` — BOTH already exist and were used/
  confirmed live this run, no new page-object methods needed for Part A).
- **Part B needs NEW `AgentDetailPage` methods, mirroring `SkillDetailPage`'s existing
  ELITEA-2597 additions exactly** (same shared `PublishWizardModal.jsx` component, same
  testids):
  - `is_publish_confirm_enabled()` — `SkillDetailPage` has this, `AgentDetailPage`
    currently only has `is_publish_continue_enabled()` (Preparation step) — no
    equivalent for the Validation/Publishing step's Publish button.
  - `close_publish_wizard()` — exists on `SkillDetailPage`, not on `AgentDetailPage`.
  - `confirm_publish_and_capture_response()` — `AgentDetailPage.confirm_publish()`
    currently returns only the HTTP status int (sufficient for a 200 assertion, but
    Part B needs the response BODY too, for the `error`/`msg` pair) — either extend
    `confirm_publish()` to optionally return the full response, or add a sibling
    method mirroring `SkillDetailPage.confirm_publish_and_capture_response()` verbatim.
  - `get_publish_error_message()` — reuse the EXISTING `publish-wizard-error-alert`
    testid (already on `automation/testids`, confirmed live this run to render
    unmodified for the Agent flow) — no new testid, purely an additive page-object
    method mirroring `SkillDetailPage`'s.
  All four are additive-only (no existing method body touched), same low-risk shape
  ELITEA-2597's implementer amendment used for the Skill side.
- **Second-tab navigation must include `?destTab=configuration&viewMode=owner`** — a
  bare `/agents/all/{id}` URL lands on the Chat tab, not the Skills-editing panel
  (confirmed live gotcha, Axis 2).
- Wait strategy: `publish_validate` is AI-backed, variable latency — this run observed
  up to ~25s; use `expect_response()` with a generous timeout (30s, matching
  ELITEA-2600's `VALIDATE_TIMEOUT` constant), never a fixed sleep.
- Reopening the Publish wizard ALWAYS starts a fresh, empty Preparation step —
  confirmed live 3 times this run; do not attempt to resume a stale Validation-step
  state after Cancel.
- Seed both skills via `SkillAPI.create_skill()` for speed (same optimization
  ELITEA-2597's AFS recommends) rather than the UI create flow used during this
  analysis run — the UI flow was used here only because Playwright MCP browser
  actions were the fastest available tool for live observation, not because it's the
  implementation's intended data-seeding path.
- Seed a genuinely THIRD, dedicated `extra-skill` (own valid ≥100-char content) for
  the Part B attach/detach probe rather than reusing the Part A invalid skill — see
  Test Data / Blocked Steps for why the reuse confounds the removal direction.
