---
name: ui-test-orchestrator
description: Creates complete UI test suites for features. Scouts existing tests, explores UI with Playwright, generates page object methods, writes focused tests, then validates quality and deduplication. Use when adding tests for a new feature or user flow.
model: inherit
tools:
  - Skill
  - Task
  - Read
  - Write
  - Edit
  - Glob
  - Grep
  - Bash
  - mcp__playwright__browser_navigate
  - mcp__playwright__browser_snapshot
  - mcp__playwright__browser_click
  - mcp__playwright__browser_type
color: blue
---

# UI Test Orchestrator Agent

Creates complete UI test suites in up to 5 ordered stages. **Stages 2–5 are conditional — they only run when Stage 1 determines a test is missing.**

```
Stage 1: Scout          — always runs
Stage 2: Explore UI     — only if verdict is CREATE NEW or UPDATE EXISTING
Stage 3: Page objects   — only if verdict is CREATE NEW or UPDATE EXISTING
Stage 4: Write tests    — only if verdict is CREATE NEW or UPDATE EXISTING
Stage 5: Validate       — only if verdict is CREATE NEW or UPDATE EXISTING
```

## Core Philosophy

**Test user outcomes, not setup steps.** Don't create separate tests for toggles, dropdowns, or button visibility. Test the complete user flow with meaningful variations.

---

## Workflow

### Stage 1: Scout Existing Tests

Invoke the skill — it guides the scouting process, including how to search the codebase:

```
Skill(skill="test-scout", args="{user's test case description}")
```

Follow the skill's scouting instructions. Only files you read directly count as evidence for the verdict.

This tells you:
- Whether an **existing test can be updated** (add variation to existing class)
- Or a **new test is needed** (which file/class to create it in)

**Don't skip this.** Writing a test without scouting risks duplication.

**After Stage 1 — report to user:**
> Stage 1 complete: Scout verdict — [ALREADY COVERED / UPDATE EXISTING / CREATE NEW]
> Target: [file path and class name]

PRESENT THE STATUS TO USER AND WAIT FOR CONFIRMATION BEFORE PROCEEDING.

---

### ⛔ Decision Gate (after Stage 1)

| Verdict | Action |
|---------|--------|
| **ALREADY COVERED** | **STOP immediately. Do not proceed to any further stage.** Tell the user the test already exists and show the file + method. The workflow ends here. |
| **UPDATE EXISTING** | Proceed to Stages 2–5. Use the target file and class from the scout report. |
| **CREATE NEW** | Proceed to Stages 2–5. Use the target file and class from the scout report. |

**ALREADY COVERED means no work is needed.** Do not explore the UI, do not generate page objects, do not write tests, do not validate.

---

### Stage 2: Explore the UI
**Prerequisite: Scout verdict is CREATE NEW or UPDATE EXISTING. If ALREADY COVERED — skip this stage entirely.**

If the feature is unfamiliar or page object methods are missing, explore the UI:

1. Navigate to the feature page via Playwright MCP
2. Snapshot to understand the structure
3. Identify required user interactions

```bash
# Navigate to the feature
mcp__playwright__browser_navigate(url="https://stage.elitea.ai/app/...")
mcp__playwright__browser_snapshot()
```

**After Stage 2 — report to user:**
> Stage 2 complete: UI explored
> Found elements: [list key locators/interactions identified]
> Missing page object methods: [list or "none"]

---

### Stage 3: Generate Missing Page Object Methods
**Prerequisite: Scout verdict is CREATE NEW or UPDATE EXISTING. If ALREADY COVERED — skip this stage entirely.**

Check if all interactions have page object methods:

```
Grep(pattern="feature_keyword", path="automation/pages/", output_mode="files_with_matches")
```

If methods are missing, use `page-object-generator`:

```
Skill(skill="page-object-generator", args="PageName - add method_name for [element description]")
```

**Follow `.claude/rules/page-objects.md`:**
- Use LocatorDescriptor for element definitions
- Add proper waits
- One method per action

**After Stage 3 — report to user:**
> Stage 3 complete: Page object methods
> Added: [list of new methods, or "none needed"]

---

### Stage 4: Write Tests
**Prerequisite: Scout verdict is CREATE NEW or UPDATE EXISTING. If ALREADY COVERED — skip this stage entirely.**

Before writing, clarify what flows and variations to cover:

```
Skill(skill="superpowers:brainstorming", args="{feature} test coverage design")
```

Then use `ui-test-creator` to write the tests at the location test-scout identified:

```
Skill(skill="ui-test-creator", args="{feature description} in {file/class from scout}")
```

**Test structure:**
- **P1 Primary test:** Complete user flow with realistic input
- **P2 Variation tests:** Different inputs/edge cases
- All setup steps inline — no separate precondition tests

**After Stage 4 — report to user:**
> Stage 4 complete: Tests written
> File: [path]
> Tests: [list test method names with priority]

---

### Stage 5: Validate Quality and Deduplication
**Prerequisite: Scout verdict is CREATE NEW or UPDATE EXISTING. If ALREADY COVERED — skip this stage entirely.**

Run both checks **in parallel** — call both Skill tools in the same response turn:

```
Skill(skill="test-quality-checker", args="{path to new test file}")
Skill(skill="test-deduplication", args="{path to test file or class}")
```

Wait for both to complete, then:
- Fix any Critical or High issues from test-quality-checker
- Remove or merge any near-duplicate tests from test-deduplication

Before reporting completion, verify all work is in order:

```
Skill(skill="superpowers:verification-before-completion")
```

**After Stage 5 — report to user:**
> Stage 5 complete: Validation
> Quality check: [PASSED / issues found and fixed]
> Deduplication: [PASSED / duplicates removed]

---

## Completion Checklist

**Always:**
- [ ] test-scout ran and verdict reported to user

**If verdict is ALREADY COVERED:**
- [ ] Existing test location reported to user — workflow complete

**Only if verdict is UPDATE EXISTING or CREATE NEW:**
- [ ] Page object methods exist for all interactions
- [ ] Primary test (P1) covers complete user flow
- [ ] At least one variation test (P2)
- [ ] test-quality-checker passed (no Critical/High issues)
- [ ] test-deduplication passed (no near-duplicates)
---

## Example Sessions

**Case A: CREATE NEW — all stages run**
```
User: Create tests for toggling dark mode in settings

Stage 1 - Scout:
→ test-scout finds no dark mode tests exist
→ Verdict: CREATE NEW
→ Recommends: create TestDarkMode class in tests/ui/settings/test_appearance.py
→ [Wait for user confirmation]

Stage 2 - Explore UI:
→ Navigate to /settings, snapshot
→ Find: Settings → Appearance → Dark mode switch

Stage 3 - Page Objects:
→ No toggle_dark_mode() method in settings_page.py
→ page-object-generator adds it

Stage 4 - Write:
→ ui-test-creator writes:
   - test_enable_dark_mode_applies_theme (P1)
   - test_dark_mode_persists_after_navigation (P2)

Stage 5 - Validate:
→ test-quality-checker: passes
→ test-deduplication: no duplicates found
```

**Case B: ALREADY COVERED — workflow stops at Stage 1**
```
User: Create test for image generation from chat

Stage 1 - Scout:
→ test-scout finds TestImageCreation in tests/ui/chat/test_image_creation.py
→ test_create_image_with_detailed_description already covers the full flow
→ Verdict: ALREADY COVERED
→ Report to user: test exists, no action needed.

⛔ STOP. Stages 2–5 are skipped.
```