# Test Case: Build with AI — Cancel from review step does not create a Skill

> ⚠️ **UNDER REVIEW — 2026-08-14 fidelity audit. Do NOT reuse this AFS as a pattern.**
>
> This spec directs the implementer to **substitute the system under test** (mocking
> the generate-draft response) for a TMS case whose text never asks for simulation.
> Classification: **TRANSIT** — the mock only reaches the review step; the cancel observable is real (mirror of agents ELITEA-1918).
>
> **Rework by class:** `TERMINAL` → rewrite against the live flow (the test currently
> proves nothing about the case's subject). `MIXED` → drop the tautological assertions
> and prefer a live draft; the rest of the coverage is sound. `TRANSIT` → cheapest —
> swap the mock for a live generate, or keep it and declare it per
> `.agents/testing.md` § Fidelity policy.
>
> Justifications of the form "the same sanctioned-mocking technique this file already
> uses" or "not a good use of fixture-creation effort" are **not valid authorities**:
> nothing sanctions response mocking, and cost is never a reason to substitute. See
> `.agents/role-overrides.md` § Every role — precedent is not authority.
>
> **`extend-existing` must not inherit this design.** Rework tracked on
> [#1298](https://github.com/EliteaAI/elitea-testing-public/issues/1298) (agents) and
> [#1399](https://github.com/EliteaAI/elitea-testing-public/issues/1399) (skills); full
> chain in `sdlc-skills/bundles/test-automation/incidents/2026-08-14-response-mocking-drift.md`.

## Metadata
- **TMS ID**: ELITEA-1998
- **Source case**: `onetest-ai-tm-Elitea/tests/automated-full-regression-ui/skills/ELITEA-1998_build-with-ai-cancel-from-review-step-does-not-create-a-skill.md`
  (path inferred from the intake snapshot at
  `.agents/automation/skills-remaining-w5/cases/ELITEA-1998.md`; module `skills`, tags `[automated:UI:regression, feat:skills]`)
- **Linked Story**: none
- **Priority**: l2 (case priority: `medium`)
- **Environment Explored**: local (`http://localhost:5173`, EliteaUI `automation/testids` branch → DEV backend), project `Private` / id `399`
- **User set**: `${TEST_USER}` (localhost `auth_state` fixture skips login via `VITE_DEV_TOKEN`; admin-equivalent role, per `.agents/profile.md` § Roles & sample users)
- **Analyst**: qa-engineer (Sage), analyst slot, batch skills-remaining-w5, cluster dispatch with ELITEA-1997
- **Status**: ready-for-automation
- **Tracking issue**: batch tracking issue for skills-remaining-w5 (no per-case board card)
- **Case-gate note**: source case frontmatter carries `status: draft` / `execution_type: manual` — no exclusion per `.agents/testing.md` § TMS case-gate, so this run proceeded normally.
- **Case-text drift filed**: [EliteaAI/elitea-testing-public#1486](https://github.com/EliteaAI/elitea-testing-public/issues/1486) — sibling of #1318 (Agent-entity analog, ELITEA-1918). See § Triangulation below. **The case's literal "Cancel" button does not exist on the review step** — this AFS asserts the live, correct control instead (reverse-masking guard).

## Triangulation — what actually closes the modal from the REVIEW step

`GenerateEntityModal.jsx` (`../EliteaUI/src/[fsd]/entities/generate-entity-with-ai/ui/GenerateEntityModal.jsx`)
is the SAME shared component the Agent "Build with AI" flow uses (confirmed by
`test-specs/skills/_surface.md` § "Build with AI (skill creation)" — "Modal shell
(`GenerateEntityModal.jsx`) is shared with the Agent 'Build with AI' flow ... same
loading/error/retry mechanics, entity-specific testids"). Its `renderActions()` renders a
**different button set per step**, not a fixed "Cancel + Generate/Approve" pair — confirmed live
this run via an accessibility snapshot of the open dialog on the review step:

```yaml
- dialog:
  - heading "Build with AI Close":
    - button "Close"           # generate-skill-close-button — the X icon
  # ... Name / Description / Instructions review fields ...
  - button "Back to prompt"    # generate-skill-back-button
  - button "Create Skill"      # generate-skill-approve-button
```

**There is no "Cancel" button at the REVIEW step at all** — the footer shows exactly two buttons
("Back to prompt", "Create Skill"), matching the Agent entity's identical `renderActions()`
branching (documented in #1318 for ELITEA-1918):
- **"Back to prompt"** (`generate-skill-back-button`) → returns to the INPUT step, `draftData`
  reset to `null`, **modal stays open**. This is ELITEA-1996's separate case
  (`test-specs/skills/l2_build-with-ai-back-to-prompt-returns-to-input-step-preserves-text_ELITEA-1996.md`)
  — a distinct case already covers Back-to-prompt; this AFS does **not** cover it.
- **"Create Skill"** (`generate-skill-approve-button`) → the approval path (ELITEA-1990/1991's
  territory), not this case's concern.

The only way to close the modal from the review step **without creating a Skill** is the modal
header's **X ("Close") icon** (`generate-skill-close-button`) — same mechanism as the INPUT-step
"Cancel" button (both call the shared `handleClose()` in `GenerateEntityModal.jsx`, per the
source-level proof already established for the Agent entity in #1318; not re-traced line-by-line
here since the component is identical, only entity-specific testids differ).

**Why this can't be spliced into an existing covering test (extend-existing doesn't fit):**
`modal.close_button.click()` appears exactly once elsewhere in the suite —
`automation/tests/ui/skills/test_skill_build_with_ai.py`,
`TestSkillBuildWithAIGeneratedNameNamingRules`, line ~1024 — but only as end-of-test **cleanup**
("Close the modal without creating a Skill — this case never clicks 'Create Skill'"), with
**zero assertions before or after it**. Confirmed via `grep -n "close_button"
automation/tests/ui/skills/test_skill_build_with_ai.py` → exactly one hit, that cleanup line. No
test asserts what clicking the X icon from the review step actually DOES (modal removed from DOM,
form untouched, no create call, no skill in the list) — that is this case's entire,
previously-unexercised gap. Same triangulation shape the Agent-entity sibling ELITEA-1918 used for
`close_button` (clicked once, but never verified, before that case).

## Preconditions
- `${TEST_USER}` is authenticated via the `auth_state` fixture (localhost `VITE_DEV_TOKEN`
  bypass — no Keycloak login form on localhost).
- The New Skill creation page (`${BASE_URL}/skills/create`) is reachable, with the "General"
  accordion section expanded by default.
- **A skill draft has been generated and the review/edit form is displayed** — this case's own
  precondition (distinct from ELITEA-1997, which cancels BEFORE generating). Reached live this
  run via a real (unmocked) `generate_skill_draft` call — no `mock_generate_success()` needed;
  the real endpoint responded within ~30s (this run's observed latency; the file's existing
  `UNMOCKED_GENERATE_RESPONSE_TIMEOUT = 30000` constant, already defined for ELITEA-1992's
  real-generation test, covers this). Mocking remains available
  (`GenerateSkillModalPage.mock_generate_success()`) if the implementer prefers a deterministic
  draft payload — either is sound; this AFS does not assert on the draft's specific content, only
  on the close behavior.

## Test Data
### reuse-existing (no fixture creation/teardown needed)
- `${TEST_USER_EMAIL}` / `${TEST_USER_PASSWORD}` via `auth_state`.
- `${ELITEA_PROJECT_ID}` (whichever project is active — the flow is project-agnostic; this run
  used project `Private`/`399`).
- Prompt text: any non-empty natural-language string (case's Test Data table says "(none
  required)" — the case's own precondition already assumes a draft exists, so the prompt text
  used to reach it is incidental). Confirmed live with: `"A skill that summarizes customer
  support tickets into a one-paragraph digest for ELITEA-1998 cancel-from-review verification."`
  — this run's real, unmocked generation returned `name: "support-ticket-digest"`.

No new test data is created or persisted in the product by this case's steps — the draft IS
generated (this case's precondition), but the create-skill call never fires because the X icon is
clicked instead of "Create Skill". See Cleanup.

## Test Steps

1. Navigate to `${BASE_URL}/skills/create`, open the Build with AI modal
   (`generate-skill-open-button`), enter a natural-language description into the prompt textarea
   (`generate-skill-prompt-input`), and click "Generate Draft" (`generate-skill-submit-button`)
   to reach the review step.
   - **Verify**: the review form is displayed with the generated draft's data — confirmed live
     via an accessibility snapshot showing populated Name/Description/Instructions fields (this
     run generated `name: "support-ticket-digest"` from the billing-support-ticket prompt — real,
     unmocked AI output, confirmed live). No Welcome Message/conversation-starter section
     appeared, consistent with `_surface.md`'s documented Skill-vs-Agent review-form field-set
     difference.
2. Click "Cancel" — **the review step has no separate "Cancel" button**; see § Triangulation
   above for why the modal's Close (X) icon (`generate-skill-close-button`) is the correct
   control instead, not case-text drift left unaddressed. ("Back to prompt",
   `generate-skill-back-button`, is a visually-adjacent but functionally distinct control —
   ELITEA-1996's separate case — that returns to the INPUT step rather than closing.)
   - **Verify**: the close action is triggered — confirmed live, resolves synchronously with no
     confirmation dialog / "discard changes?" prompt — none appeared, identical to ELITEA-1997's
     prompt-step Cancel and to the Agent-entity sibling ELITEA-1918's finding.
3. Verify the modal closes.
   - **Verify**: the dialog (`generate-skill-modal`) is no longer present in the DOM — confirmed
     live via accessibility snapshot immediately after the close click: the `dialog` element is
     gone entirely (not merely hidden/inert), the page returns to the plain "New Skill" tab view.
4. Navigate to the Skills list and verify no new Skill was created.
   - **Verify (primary, deterministic)**: no `POST .../elitea_core/skills/prompt_lib/**` (the
     skill CREATE call) fired at any point during this flow — confirmed live via
     `browser_network_requests` filtered to `skill`: exactly one `generate_skill_draft` POST
     (`200 OK`, this case's own precondition — expected, not a Pass-criteria violation) and one
     benign, pre-existing `GET .../upload_skill_icon/...` (icon-picker list, unrelated); **zero**
     matches for the CREATE route.
   - **Verify (secondary, case-literal)**: navigating to `${BASE_URL}/skills/all` and reading the
     20 visible `entity-card-name` skill-card names confirms the generated draft's name
     (`"support-ticket-digest"` this run) is **absent** — confirmed live via `page.evaluate()`
     reading all `entity-card-name` text content. Unlike ELITEA-1997 (where no draft is ever
     generated, so there's no name to search for), this case's precondition DOES generate a real
     draft with a real name — so the list-search here is a genuine, name-specific secondary
     confirmation, not merely an unchanged-set echo.

## Expected Results
Clicking the modal's Close (X) icon on the GenerateSkillModal's review step (after a draft has
been generated) closes the modal (dialog removed from the DOM, not merely hidden) and creates no
skill — the create-skill call never fires, and the generated draft's name never appears in the
Skills list. No console errors observed (`browser_console_messages`, level=error → 0 results,
across the entire open→type→generate→close sequence).

## Coverage Map

### Axis 1 — Case coverage

| Case element | Expected result | Covered by (AFS step) | Asserted where | Disposition |
|---|---|---|---|---|
| 1 Generate a skill draft and enter the review/edit form | The review/edit form is displayed with generated values | AFS Step 1 | `modal.wait_for_review_form()` (existing helper); accessibility snapshot confirms populated Name/Description/Instructions fields | ready-for-automation (new test) |
| 2 Click "Cancel" | The modal closes | AFS Step 2 | **Case-text drift** (filed [#1486](https://github.com/EliteaAI/elitea-testing-public/issues/1486)) — no "Cancel" button exists on the review step; asserted against the live, correct control instead: `modal.close_button.click()` (the modal's X icon, same `handleClose()` semantics as the INPUT-step Cancel button ELITEA-1997 covers) | ready-for-automation (new test) — first assertion-backed `.click()` of `close_button` from the review step; previously only an unasserted cleanup call (ELITEA-1992's test) |
| 3 Verify the modal closes | The modal is no longer visible | AFS Step 3 | `modal.modal.wait_for(state="hidden", ...)` + DOM-absence check (same pattern as ELITEA-1997) — confirmed live: dialog fully removed | ready-for-automation (new test) |
| 4 Navigate to the Skills list and verify no new Skill was created | No new Skill entry corresponding to the cancelled draft appears in the Skills list | AFS Step 4 | Primary: assert no POST fired to the skill CREATE route (`/elitea_core/skills/prompt_lib/`) via `capture_requests_matching()`. Secondary: `SkillsListPage.get_skill_card_names()` does not contain the generated draft's name | ready-for-automation (new test) — network-absence is the deterministic proof; the name-specific list-search is the case-literal echo (stronger than ELITEA-1997's unchanged-set check, because a real name exists here to search for) |

### Axis 2 — Analyst additions

- **Filed case-text drift** ([#1486](https://github.com/EliteaAI/elitea-testing-public/issues/1486),
  sibling of #1318): the review step has no "Cancel" button at all — only "Back to prompt" and
  "Create Skill" — *added: this is the load-bearing finding of this analysis; without it, an
  implementer would search the DOM for a nonexistent "Cancel"-labelled control on the review step
  and either fail or mis-click "Back to prompt" (which does NOT close the modal — see below),
  silently testing the wrong thing.*
- **Confirmed "Back to prompt" is NOT a substitute for this case** — returns to the INPUT step
  with the modal still open, `draftData` cleared; it does not close the modal and does not create
  a skill either, but it is categorically a different outcome than "modal closed" — *added:
  disambiguates the three review-step outcomes (Back, Create, Close-via-X) so no future case
  conflates them, mirroring the Agent-entity sibling's identical disambiguation.*
- Confirmed zero console errors across the full open→type→generate→close sequence
  (`browser_console_messages`, level=error → 0 results) — *added: side-channel check, standard
  practice per this skill's methodology.* Note: unlike the Agent entity's `disableUnderline`
  baseline-noise warning documented in #1318/ELITEA-1906/1913/1916's AFS, this run's Skill-entity
  flow showed **zero** console messages at all levels beyond the app's normal load-time noise —
  no equivalent warning fired for the Skill review form this run.
- Confirmed clicking the X icon produces no confirmation/"discard changes?" interstitial, even
  though a full draft (Name + Description + Instructions) is discarded — *added: a plausible UX
  pattern the case text doesn't rule out ("are you sure you want to lose this draft?"), ruled out
  live, consistent with ELITEA-1997's identical finding for the lighter-weight prompt-step case
  and the Agent-entity sibling ELITEA-1918's identical finding.*
- Confirmed all testids needed already exist as `LocatorDescriptor` fields on
  `GenerateSkillModalPage`/`SkillFormPage`/`SkillsListPage` (see § Concrete Handles) — no
  `add-data-testid` work needed for this case.

## Cleanup
No product state persists from this case's own steps — the generated draft is discarded on
close, and the create-skill call never fires. No `SkillAPI.delete_skill(...)` teardown is needed.
(If the implementer chooses to mock the draft via `mock_generate_success()` instead of using the
real generate endpoint, no cleanup changes — mocking is purely client-side route interception,
nothing persists either way.)

## Concrete Handles (discovered during exploration — all pre-existing)

| Element | Recommended Locator | Provenance |
|---|---|---|
| "Build with AI" open button | `generate-skill-open-button` (`GenerateSkillModalPage.open_button`) | on-main ✓ |
| Modal container | `generate-skill-modal` (`GenerateSkillModalPage.modal`) | on-main ✓ |
| Prompt textarea | `generate-skill-prompt-input` (`GenerateSkillModalPage.prompt_input`) | on-main ✓ |
| Generate Draft button | `generate-skill-submit-button` (`GenerateSkillModalPage.generate_button`) | on-main ✓ |
| **Modal Close (X) icon — this case's core control** | `generate-skill-close-button` (`GenerateSkillModalPage.close_button`) — pre-existing field; previously `.click()`ed only as unasserted test cleanup (ELITEA-1992's test) | on-main ✓ |
| "Back to prompt" button (NOT this case — disambiguation only) | `generate-skill-back-button` (`GenerateSkillModalPage.back_button`) | on-main ✓ |
| "Create Skill" / approve button (NOT this case — disambiguation only) | `generate-skill-approve-button` (`GenerateSkillModalPage.approve_button`) | on-main ✓ |
| Skills list card name | `entity-card-name` (pre-existing on `SkillsListPage`, via `get_skill_card_names()`) | on-main ✓ |
| Skill CREATE route (substring for negative assertion) | `/elitea_core/skills/prompt_lib/` (POST) — used directly with `capture_requests_matching()` | on-main ✓ — used here only for a **negative** (no-call) network assertion |
| Generate-draft route | `**/elitea_core/generate_skill_draft/**` (pre-existing constant `GenerateSkillModalPage.GENERATE_DRAFT_ROUTE`; substring form `/elitea_core/generate_skill_draft/` for `capture_requests_matching()`) | on-main ✓ — expected to fire ONCE (this case's precondition), unlike ELITEA-1997 where it must never fire |

No new testids required. No new page-object locators required. Every handle needed already
exists in `GenerateSkillModalPage`, `SkillFormPage`, and `SkillsListPage`.

## Network Behavior
Confirmed live: across the entire open → type-prompt → generate → click-X sequence, exactly
**one** request matched `/elitea_core/generate_skill_draft/` (`POST`, `200 OK` — this case's own
precondition, generating the review-step draft), and **zero** requests matched
`/elitea_core/skills/prompt_lib/` (`POST`, the CREATE call) — filtering `browser_network_requests`
to `skill` confirmed this exact split (plus one unrelated, benign `GET
.../upload_skill_icon/prompt_lib/399` icon-picker call). Only the page's normal load-time GETs
otherwise, consistent with ELITEA-1997/1996's own Network Behavior notes for this same modal
family.

## Known Defects Found During Exploration
**Case-text drift (not a product defect)** — filed as CLARIFICATION
[#1486](https://github.com/EliteaAI/elitea-testing-public/issues/1486), sibling of #1318: the
review step has no "Cancel" button; the case's Step 2 ("Click 'Cancel'") must be reinterpreted as
"click the modal's Close (X) icon" per the reverse-masking guard (live product behavior is
correct; the case text's control name is stale for this step). See § Triangulation for the full
proof.

No functional product defect found — the modal correctly closes via the X icon from the review
step, discards the generated draft, and creates no skill, exactly matching the case's underlying
intent (Pass criteria: "Modal closes and no Skill is created in the Skills list" — satisfied by
the live, correctly-named control).

## Blocked Steps
None. All case elements were executed live this run against the real local system
(`http://localhost:5173`), including a real (unmocked) `generate_skill_draft` call that produced
a genuine AI-generated draft (`"support-ticket-digest"`).

## Automation Hints
- Framework: Playwright + pytest, per `.agents/testing.md`. Add a new, standalone test class to
  `automation/tests/ui/skills/test_skill_build_with_ai.py` — e.g.
  `TestSkillBuildWithAICancelFromReviewStep` (mirrors `TestSkillBuildWithAICancelFromPromptStep`'s
  naming, ELITEA-1997, and the Agent-entity sibling `TestAgentBuildWithAICancelFromReviewStep`,
  ELITEA-1918). Same file, same imports, same fixtures the file's other tests already use
  (`SkillsListPage`, `GenerateSkillModalPage`, `SkillFormPage` if the implementer wants the
  belt-and-suspenders empty-field check on the outer form).
- **Reuse `BasePage.capture_requests_matching()` / `capture_console_errors()`** — the exact
  infrastructure already used by `TestSkillBuildWithAIBackToPromptFromReviewStep` in this same
  file. No new capture helper needed — only the route filter changes (this case doesn't need to
  assert `generate_skill_draft` is ABSENT; it fires once, expected, as the precondition).
- **Reaching the review step**: either (a) a real, unmocked `generate_button.click()` +
  `wait_for_review_form()` (confirmed reliable this run, real AI response within ~30s — use the
  file's existing `UNMOCKED_GENERATE_RESPONSE_TIMEOUT = 30000` constant), or (b)
  `mock_generate_success(draft)` + `expect_generate_response()` (the pattern this file's
  `TestSkillBuildWithAIBackToPromptFromReviewStep` already uses) for a deterministic, faster
  draft. Either is sound — this case's Pass criteria don't depend on the draft's specific
  content, only on what happens when the X icon is clicked afterward. Mocking is the faster,
  more deterministic choice if the implementer wants to avoid real-AI latency/non-determinism in
  CI.
- **Do not target "Cancel"** — there is no `cancel_button` interaction in this test;
  `close_button` is the control. Do not confuse with `back_button` (a distinct, non-closing
  control — assert its ABSENCE from this test's flow only if the implementer wants an extra
  disambiguation assertion; not required by the case's own Pass criteria).
- Suggested flow (illustrative, not prescriptive):
  ```python
  with allure.step("Step 1 — Generate a draft and reach the review form"):
      skills_list_page.navigate_to_create()
      modal.open_modal()
      modal.fill_prompt(CANCEL_FROM_REVIEW_PROMPT_TEXT)
      modal.mock_generate_success(CANCEL_FROM_REVIEW_DRAFT_PAYLOAD)  # or real click, see hint above
      with modal.expect_generate_response(timeout=GENERATE_RESPONSE_TIMEOUT) as response_info:
          modal.generate_button.click()
      assert response_info.value.status == 200
      modal.wait_for_review_form(timeout=REVIEW_FORM_TIMEOUT)

  with allure.step("Step 2 — Click the modal's Close (X) icon (no 'Cancel' button exists on this step)"):
      create_requests = form_page.capture_requests_matching(
          "/elitea_core/skills/prompt_lib/", method="POST"
      )
      console_capture = form_page.capture_console_errors()
      modal.close_button.click()

  with allure.step("Step 3 — Verify the modal closes"):
      modal.modal.wait_for(state="hidden", timeout=NAVIGATION_TIMEOUT)

  with allure.step("Step 4 — Verify no Skill was created"):
      assert not create_requests, f"got: {list(create_requests)}"
      assert not console_capture, f"got: {list(console_capture)}"
      create_requests.stop()
      console_capture.stop()
      skills_list_page.navigate()
      assert CANCEL_FROM_REVIEW_DRAFT_PAYLOAD["name"] not in skills_list_page.get_skill_card_names()
  ```
- Timeout constants: reuse this file's existing `NAVIGATION_TIMEOUT` (15000),
  `GENERATE_RESPONSE_TIMEOUT` (15000), `REVIEW_FORM_TIMEOUT` (15000), and
  `UNMOCKED_GENERATE_RESPONSE_TIMEOUT` (30000, if using real generation) — all already defined,
  no new constants needed.
- Marker: `@pytest.mark.p2` + `@pytest.mark.regression`, consistent with this file's other
  Build-with-AI cases and this case's own `l2`/`medium` priority.
