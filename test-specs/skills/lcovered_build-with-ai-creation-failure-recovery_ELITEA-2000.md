# ELITEA-2000: Build with AI — Skill creation failure stays on review step for correction

**Status:** `already-covered`  
**Priority:** medium  
**Module:** skills  
**Type:** functional

---

## Dedup Proof — Behavioural Equivalence

This case is **fully covered** by an existing merged spec on `automation/base`:

**Covering spec:**  
`automation/tests/ui/skills/test_skill_build_with_ai.py::TestSkillBuildWithAICreationFailureRecovery::test_creation_failure_stays_on_review_step_and_retry_succeeds`  
Lines 1603-1751

**Automation test ID (Form C):**  
`tests.ui.skills.test_skill_build_with_ai.TestSkillBuildWithAICreationFailureRecovery.test_creation_failure_stays_on_review_step_and_retry_succeeds`

**Git history:**  
- Merged to `automation/base` in commit `5d353321c` (2025-01-14)
- Part of PR #1491 bundling 9 skills-area Build with AI cases

---

## Behavioural Equivalence Argument

The existing test proves **identical observable behavior** to ELITEA-2000:

| ELITEA-2000 Step | Covered by existing test |
|---|---|
| 1. Generate skill draft, review, click "Create Skill" | Lines 1609-1631: modal opened, draft generated, review form shown |
| 2. Simulate/trigger creation API failure | Lines 1637-1661: `modal.mock_create_failure(status=500)`, mocked POST returns 500 |
| 3. Verify error messages displayed | Lines 1671-1679: error toast verified (`data-severity="error"`, message content matched) |
| 4. Verify user stays on review/edit step | Lines 1686-1693: modal remains visible, back/approve buttons present (not reverted to prompt step) |
| 5. Verify draft data preserved and editable | Lines 1699-1710: name, description, instructions all match draft values |
| 6. Correct issue, retry, verify success | Lines 1718-1748: mock cleared, retry succeeds (201), navigation to detail page, all fields preserved |

**Observable:** On creation failure, the user remains on the Build with AI modal's review step with:
- All draft data (name, description, instructions) preserved
- Error notification shown (app-wide toast, not inline form message)
- Same "Create Skill" button re-enabled for retry (no separate retry control)
- Successful retry creates the skill and navigates to detail page

**Expected result:** The test asserts every numbered step and expected outcome in ELITEA-2000.

**Known defect coverage:** The test documents (lines 1663-1669) that error feedback is an **app-wide toast** (Toast.jsx), not an inline/embedded form message — matching ELITEA-2000's precondition that assumed inline error display. This is the same UX inconsistency documented in ELITEA-1916 AFS (agent-entity sibling) — the test asserts the LIVE contract per reverse-masking guard, and both AFSs note it as a clarification, not a product defect.

**Simulation authorization:** ELITEA-2000 step 2 explicitly requests "simulate or trigger a creation API failure" — the covering test uses Playwright's `route.fulfill()` to mock a 500 response, which is case-authorized terminal substitution.

---

## TMS Case Link

**Source case:**  
`../onetest-ai-tm-Elitea/tests/automated-full-regression-ui/skills/build_with_ai/ELITEA-2000_build-with-ai-skill-creation-failure-stays-on-review-step.md`

**Case metadata:**
- Title: "Build with AI — Skill creation failure stays on review step for correction"
- Module: skills
- Priority: medium
- Type: functional
- Tags: `automated:UI:regression`, `feat:skills`

---

## Rationale — Why No Separate Implementation

1. **Complete coverage:** The existing test exercises every step and assertion ELITEA-2000 requires.
2. **Identical observable:** Both verify the review-step persistence, draft-data preservation, error display, and retry success.
3. **Merged to base:** The covering spec is on `automation/base` (not in-flight), satisfying the merged-target rule for `already-covered` status.
4. **No gap:** ELITEA-2000 adds no new assertions or edge cases beyond what the existing test proves.

A second implementation would duplicate assertions without adding coverage.

---

## Evidence

Test source reviewed 2026-08-18:
- Class: `TestSkillBuildWithAICreationFailureRecovery`
- Method: `test_creation_failure_stays_on_review_step_and_retry_succeeds`
- File: `automation/tests/ui/skills/test_skill_build_with_ai.py`
- Lines: 1603-1751
- Markers: `@pytest.mark.p2`, `@pytest.mark.regression`
- Allure link: References ELITEA-2000 TMS case in decorator (lines 1596-1600)

---

## Analyst Notes

- **Naming:** The test explicitly references ELITEA-2000 in its docstring, constant names (`SIMULATED_CREATE_ERROR_MESSAGE`), and allure decorator.
- **Sibling entity:** The class docstring notes this is the skill-entity sibling of ELITEA-1916 (agent creation failure), implementing identical error-recovery UX.
- **Error mechanism:** Test documents that error display uses app-wide Toast.jsx (lines 1663-1669), not inline form errors — same as case precondition noted.
- **Distinct from generation failure:** Class docstring clarifies this tests CREATE-time failure (base-create POST), distinct from ELITEA-2001's generate-DRAFT failure.

**Analysis date:** 2026-08-18  
**Analyst:** qa-engineer (Sage)
