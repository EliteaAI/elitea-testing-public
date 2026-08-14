# Batch Report — skills-remaining-w2

**Batch ID:** skills-remaining-w2  
**Base branch:** origin/automation/base  
**Integration branch:** tests/batch-skills-remaining-w2

---

## Summary

- **Verdict:** RED (1/3 informational gate run)
- **Cases:** 8 total / 8 blocked
- **Gate failures:** 3 specs
  - 1 new/unclassified: ELITEA-2605 `test_skill_custom_icon_visible_across_ui`
  - 2 sanctioned RED-BY-DESIGN (defect #570, soft-asserted)

---

## Gate Run Results

| Run # | Duration | Status | Notes |
|---|---|---|---|
| 1 (informational) | 172.2s / 94.59s (two specs) | RED | 3 failures; 1 unclassified, 2 sanctioned |

### Failures

#### 1. ELITEA-2605 — NEW/UNCLASSIFIED

**Spec:** `automation/tests/ui/skills/test_skill_custom_icon_visibility_across_ui.py::TestSkillCustomIconVisibilityAcrossUI::test_skill_custom_icon_visible_across_ui`

**Failure:** AssertionError: Not on detail page `http://localhost:5173/agents/create?viewMode=owner` — raised in `pages/agent_detail_page.py:669` `verify_on_detail_page()`, called from test's Step 7 (create disposable agent) immediately after `agent_form_page.save_and_wait_for_navigation()`. URL never settled on `/agents/all/<id>`.

**Classification:** Not one of the two sanctioned RED-BY-DESIGN signatures (#570). New/unclassified.

---

#### 2. ELITEA-2602 — SANCTIONED RED-BY-DESIGN

**Spec:** `automation/tests/ui/skills/test_skill_fork_end_to_end.py::TestSkillForkEndToEnd::test_fork_skill_end_to_end`

**Failure:** Known defect [#570](https://github.com/EliteaAI/elitea-testing-public/issues/570): `validateDOMNesting` <p>-in-<p> console-error on shared Fork Complete dialog. Soft-asserted via `expect.soft()`. Rest of flow (steps 8-11) passed cleanly.

**Classification:** SANCTIONED RED-BY-DESIGN (per dispatch)  
**Defect:** [#570](https://github.com/EliteaAI/elitea-testing-public/issues/570) — OPEN

---

#### 3. ELITEA-2603 — SANCTIONED RED-BY-DESIGN

**Spec:** `automation/tests/ui/skills/test_skill_fork_non_base_version.py::TestSkillForkNonBaseVersion::test_fork_non_base_skill_version`

**Failure:** Known defect [#570](https://github.com/EliteaAI/elitea-testing-public/issues/570): `validateDOMNesting` <p>-in-<p> console-error on shared Fork Complete dialog. Soft-asserted. Rest of flow (steps 8-9) passed cleanly.

**Classification:** SANCTIONED RED-BY-DESIGN (per dispatch)  
**Defect:** [#570](https://github.com/EliteaAI/elitea-testing-public/issues/570) — OPEN

---

## Case Status Summary

| Case ID | Outcome | Note | AFS | Branch | PR |
|---|---|---|---|---|---|
| ELITEA-2439 | BLOCKED | Gate red for batch; spec did not fail | test-specs/skills/l2_copy-link-copies-valid-url-to-correct-skill-version_ELITEA-2439.md | tests/2439-skill-copy-link | #1452 |
| ELITEA-2441 | BLOCKED | Gate red for batch; spec did not fail | test-specs/skills/l3_test-panel-does-not-create-new-chat-conversation_ELITEA-2441.md | tests/ELITEA-2441-test-panel-no-new-conversation | #1453 |
| ELITEA-2442 | BLOCKED | Gate red for batch; spec did not fail | test-specs/skills/l3_test-panel-response-actions-enabled_ELITEA-2442.md | tests/2442-test-panel-response-actions-enabled | #1454 |
| ELITEA-2602 | BLOCKED | Gate red; spec is sanctioned RED-BY-DESIGN (#570) | test-specs/skills/l2_fork-skill-end-to-end_ELITEA-2602.md | tests/2602-2603-fork-skill | #1456 |
| ELITEA-2603 | BLOCKED | Gate red; spec is sanctioned RED-BY-DESIGN (#570) | test-specs/skills/l3_fork-non-base-skill-version_ELITEA-2603.md | tests/2602-2603-fork-skill | #1456 |
| ELITEA-2604 | BLOCKED | Build failed: subagent incomplete | test-specs/skills/l2_skill-custom-icon-upload-and-validation_ELITEA-2604.md | — | — |
| ELITEA-2605 | BLOCKED | Build failed: subagent incomplete | test-specs/skills/l2_skill-custom-icon-visibility-across-ui_ELITEA-2605.md | tests/2605-skill-custom-icon-visibility-across-ui | #1457 |
| ELITEA-2606 | BLOCKED | Gate red for batch; spec did not fail | test-specs/skills/l3_skill-custom-icon-persistence-on-save-as-version_ELITEA-2606.md | tests/ELITEA-2606-skill-icon-persistence-save-as-version | #1458 |

---

## Findings by Category

### Defects (Blocking)

**ELITEA-2605 — URL navigation failure (new/unclassified)**

- **Issue:** Step 7 (create disposable agent) attempts to navigate via `agent_form_page.save_and_wait_for_navigation()`, but the URL never settles on `/agents/all/<id>`. Instead it remains on `/agents/create?viewMode=owner`.
- **Root cause:** Not yet determined. This is not the documented #570 signature; requires investigation.
- **Action:** Escalate to implementer for debug or to orchestrator for routing.

---

### Clarifications / Case-Text Drift (ELITEA-2602, ELITEA-2603)

**Tag validation — hyphen rejection (ELITEA-2602, ELITEA-2603)**

- **Issue:** Case test data uses literal tags `test-tag`, `fork-demo`, `v2-tag` (with hyphens). Live product silently rejects these in the Tags field — 0 network calls, chip never created.
- **Root cause:** Pre-existing, already tracked as [#1445](https://github.com/EliteaAI/elitea-testing-public/issues/1445) (filed for ELITEA-2433).
- **Action:** Commented new occurrence on existing #1445; cases substituted underscores for hyphens in test data.

**Fork wizard — 'Main entity' preview card never renders Tags (ELITEA-2602, ELITEA-2603)**

- **Issue:** Case steps claim fork wizard's expanded entity preview card shows "instructions, tags, etc." Live product shows instructions only; tags absent for all entity types (Agent/Pipeline/Skill share same `IWModalContent.jsx`).
- **Root cause:** UI design does not include tags in the preview.
- **Action:** Filed new clarification issue [#1455](https://github.com/EliteaAI/elitea-testing-public/issues/1455). Not a defect; fork operation itself is correct.

**Default icon representation (ELITEA-2604, ELITEA-2605)**

- **Issue:** Case steps reference a literal `skill-icon.svg` file as the default icon. Live product renders an absent `<img>` element with an inline SVG placeholder (via `EntityTypeIcon`) — no discrete asset/URL ever appears in the DOM.
- **Root cause:** Same reverse-masking pattern as ELITEA-1899 (agents).
- **Action:** Documented in memory; not filed separately as it matches established pattern.

---

### Testid Gaps (Non-Blocking — marked in AFS, not yet added)

**ELITEA-2602, ELITEA-2603 — Entity create form missing testid**

- `EntityIcon` in `CreateSkillForm.jsx` passes no `data-testid` at all.
- Agent's equivalent got `agent-form-icon-button` for ELITEA-1899; Skill never did.
- **Action:** Implementer to add `skill-form-icon-button` via `add-data-testid`.

**ELITEA-2602, ELITEA-2603, ELITEA-2604 — Icon picker upload button missing testid**

- `SelectIconDialog.jsx`'s Upload `IconButton` (shared across Agent/Pipeline/Skill) carries no `data-testid` — only a tooltip accessible name.
- **Action:** Implementer to add via `add-data-testid`.

**ELITEA-2605 — Three custom-icon visibility testids needed**

- `skill-menu-item-icon-img` (SkillMenu.jsx dropdown)
- `skill-card-icon-img` (SkillCard.jsx agent SKILLS-section card)
- `skill-mention-item-icon-img` (MentionSkillList.jsx chat mention item)
- All three: identical `icon_meta?.url ? <EliteAImage/> : <SkillIcon/>` pattern at 3 call sites.
- **Action:** Add via `add-data-testid`; correctly scoped to custom-icon branch only (verified against implementation).

**ELITEA-2604 — Icon picker delete button missing testid**

- Per-uploaded-icon delete button in `UserIconItem.jsx` (shared icon-picker gallery).
- Carries no `data-testid` — only non-unique `className="deleteButton"`.
- Hover-revealed via CSS visibility toggle (element in DOM always).
- **Action:** Implementer-blocking; add via `add-data-testid`.

---

### Known OPEN Defects (Soft-Asserted, Sanctioned RED-BY-DESIGN)

**Issue #570 — validateDOMNesting <p>-in-<p> on Fork/Import Complete dialog**

- **Scope:** Shared `IWModalSucceedContent.jsx` component tree.
- **Confirmed on:** Agent Fork (ELITEA-1857), Pipeline Fork (prior work), **Skill Fork (ELITEA-2602, ELITEA-2603)** — third entity type.
- **Handling:** Soft-asserted via `expect.soft()` + `# Known defect: #570` comment. Rest of flow (steps 8–11, 8–9) passes cleanly.
- **Status:** OPEN; both new tests correctly merge RED until fix ships.

---

### POM-Discipline Findings

**ELITEA-2441 — Inline locator construction (BLOCKING)**

- **Issue:** `chat_page.page.locator(chat_page.CONVERSATION_ITEM_PREFIX)` built inline in spec file (lines 136–138).
- **Violation:** Should call pre-existing `ChatPage.get_conversation_item_rows()` method (automation/pages/chat_page.py:2852–2857), which returns exactly that locator.
- **Rule:** Locators class-level fields only; no inline construction in methods or spec files.
- **Status:** VERIFIED FIXED in PR #1453 — now calls the wrapper method.

---

### Framework & Conventions Notes

**SkillDetailPage.get_version_id() — URL-only parsing limitation**

- Returns the SKILL id (not the real DB version id) when called on base version.
- Correct for existing Save-As-Version callers (URL-only fallback), but would silently produce wrong value for future lineage/parent_version_id comparisons.
- **Documented in memory:** `skill_get_version_id_returns_skill_id_on_base_not_real_db_id.md`
- **Workaround used:** ELITEA-2602/2603 implementer calls `SkillAPI.get_skill()` for lineage assertions instead.

**ELITEA-2604 — Uncommitted work on trunk**

- At dispatch start, `tests/batch-skills-remaining-w2` held uncommitted ELITEA-2604 work (page object diff + test file + AFS notes + 2 memory entries) — apparent prior implementer session that never completed branching/PR.
- **Action:** Quarantined onto `tests/2604-skill-custom-icon-upload-and-validation` (pushed, commit 55ae0f93).

---

## Quality Checks

### Locator Policy (role-overrides.md)

**ELITEA-2439, ELITEA-2441, ELITEA-2602, ELITEA-2603, ELITEA-2606**

- Mechanical grep for non-testid handles added in `automation/pages/` or `automation/tests/`: **0 hits** ✓
- All locators testid-only per policy.

**ELITEA-2605**

- Three new testids (skill-menu-item-icon-img, skill-card-icon-img, skill-mention-item-icon-img) verified against source.
- Correctly scoped to custom-icon (EliteAImage) branch only; default SkillIcon branch untagged.
- Compliant same-element-conditional-pair shape (ruling #277).

---

## Orchestrator Actions Required

1. **ELITEA-2605 URL navigation failure:** Investigate why agent-creation flow does not navigate to `/agents/all/<id>` after save. This blocks the entire batch gate.
2. **Review the two sanctioned-RED specs** (ELITEA-2602, ELITEA-2603) — confirm acceptance of soft-asserted #570 signature and re-assess whether they can merge RED given the documented finding.
3. **Route ELITEA-2604 and ELITEA-2605** — both have build-stage failures (incomplete subagent work). Determine whether to rework or park.
4. **Testid additions** — 5+ new testid gaps across the batch. Gate cannot proceed until these are added to EliteaUI (via `add-data-testid`, pushed to `automation/testids`).

---

## Closure

**Report Date:** 2026-08-12  
**Batch State:** RED (1 unclassified failure blocking gate + infrastructure gaps)  
**Next Step:** Implement fix for ELITEA-2605 navigation issue; address testid gaps; re-run gate.
