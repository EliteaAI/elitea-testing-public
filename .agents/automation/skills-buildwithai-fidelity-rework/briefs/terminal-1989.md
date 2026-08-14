# Brief: ELITEA-1989 — replace fabricated draft with a live generate-draft call

**Source:** issue #1399 comment thread (fidelity audit + "🔧 Rework recipe —
skills Build-with-AI", cross-posted from #1298), human directive "yes, let's
fix affected withing this ticket". Case:
`onetest-ai-tm-Elitea/tests/automated-full-regression-ui/skills/build_with_ai/
ELITEA-1989_skill-draft-generated-from-natural-language-description.md`.

**Scope:** `automation/tests/ui/skills/test_skill_build_with_ai.py`, class
`TestSkillBuildWithAIReviewFormEditableFields`, method
`test_loading_state_shows_exact_text_and_review_form_has_no_extra_sections`
(currently lines ~670–738).

Today this test calls `modal.mock_generate_success(GENERATED_DRAFT_PAYLOAD)`
(a `page.route()` fabrication of `generate_skill_draft`'s response — see
`GenerateEntityModalPageBase.mock_generate_success()`,
`pages/generate_entity_modal_page_base.py`), then asserts the loading text and
scans the dialog for forbidden section names. It never asserts the review
form actually reflects the *response* — the "review form has no extra
sections" check is honest (regex over dialog text, not payload-derived), but
the loading-state coverage of "draft generated from a natural-language
description" is entirely a test-authored payload. Per
`.agents/testing.md` § Fidelity policy, generation is the case's own subject
— today's test proves the UI renders JSON the test itself handed it, not that
the platform generated anything.

**Rewrite, entirely:**
1. Delete the `modal.mock_generate_success(GENERATED_DRAFT_PAYLOAD)` call.
2. Replace `modal.expect_generate_response(timeout=GENERATE_RESPONSE_TIMEOUT)`
   + `modal.generate_button.click()` with a live call — same pattern as
   `TestSkillBuildWithAIGeneratedNameNamingRules.
   test_generated_skill_name_adheres_to_naming_rules` (ELITEA-1992, the file's
   one already-live test, lines ~1001–1080): no route mock installed, generous
   timeout for the real LLM-backed call.
3. Bump the timeout for this call to the file's existing
   `UNMOCKED_GENERATE_RESPONSE_TIMEOUT = 30000` constant (already defined at
   module level for ELITEA-1992 — reuse it, do not invent a second constant
   with a different value) — the real endpoint took ~25s in prior AFS
   exploration (see the constant's own comment).
4. The loading-state assertion (`modal.loading_indicator.text_content() ==
   "Generating skill draft..."`) stays structurally the same but now races a
   real request instead of an artificially delayed mock — keep
   `modal.wait_for_loading_visible(timeout=LOADING_STATE_TIMEOUT)` before
   reading the text; a live request cannot resolve faster than the assertion
   reaches it (no `delay_ms` needed to make the state observable, unlike the
   mocked path).
5. **Add** the assertion this case's own subject requires and today's test
   never makes: after `wait_for_review_form()`, capture
   `body = response.json()` and assert
   `modal.get_review_name() == body["name"]`,
   `modal.get_review_description() == body["description"]`,
   `modal.get_review_instructions() == body["instructions"]` — the response is
   the oracle (`.agents/testing.md` § "How to test a NONDETERMINISTIC
   producer"), not a value the test wrote. Also assert the fields are
   non-empty (`body["name"]`, etc. truthy) — the real invariant a live call
   can violate that a mock never can.
6. `REVIEW_PROMPT_TEXT` (used to `fill_prompt` before generating) stays as
   test-authored *input* — filling the prompt is not the observable under
   test, only what comes back from it is.
7. Update the module-docstring's ELITEA-1989 paragraph (lines ~11–14) to
   reflect the live-generate rewrite instead of "extend-existing gap fill" —
   the case is no longer a gap-fill on top of a mock, it fully re-asserts the
   generation-from-description subject live.

**Out of scope:** ELITEA-1988 (modal-open visibility, no generate call at
all — already clean, untouched), ELITEA-1992 (already live — reused as the
pattern reference only, not modified), the CREATE flow (ELITEA-1990/1991,
covered by the sibling MIXED brief), ELITEA-2000/2001 (case text explicitly
asks for simulation — `.agents/testing.md` § Fidelity policy's one
unconditional exception — never touched by this rework).

**Acceptance criteria:**
- Zero `mock_generate_success`/`mock_generate_failure`/`page.route(` call
  remains inside this one test method.
- The review-form assertions compare against `response.json()`, never against
  `GENERATED_DRAFT_PAYLOAD` or any other hand-authored dict.
- The loading-text assertion is unchanged in what it checks (exact string
  `"Generating skill draft..."`), only in how the state is reached (real
  request, not a mocked one).
- The "no extra sections" regex scan is untouched (it was already honest).
- Self-check grep (per `.agents/role-overrides.md` § Implementer slot) run on
  the diff: `git diff <base>...HEAD -- automation/ | grep -nE
  '^[+].*(\.mock_|page\.route\(|route\.fulfill\(|monkeypatch|\.evaluate\()'`
  — zero hits inside this test method (other tests in the same file
  legitimately keep mocks; a hit elsewhere is not this unit's regression).
- Test passes green against the live localhost backend, 3× (lead's own gate).
- If the real generate-draft endpoint cannot produce a usable draft
  deterministically enough to keep this test reliably green (e.g. genuinely
  flaky beyond normal LLM latency) — do NOT reintroduce a mock to force
  green. Report `blocked` with the concrete symptom; the lead routes it.

**Blast radius:** one test method modified in place; no page-object symbol
added, removed, or changed (this unit reuses `click_generate_and_wait_for_response`,
`wait_for_review_form`, `get_review_name/description/instructions`,
`wait_for_loading_visible` — all pre-existing, unmodified). No shared helper
touched, so no other spec in the file or elsewhere is affected. Gate scope:
this one node id.

**Verification:**
`automation/tests/ui/skills/test_skill_build_with_ai.py::TestSkillBuildWithAIReviewFormEditableFields::test_loading_state_shows_exact_text_and_review_form_has_no_extra_sections`,
green 3× in the lead's own gate (N=3 separate invocations,
`.agents/testing.md` § Merge gate). No new specs. Estimate: small (one test
method, no new page-object work — the live-call pattern is copied from
ELITEA-1992, not invented).
