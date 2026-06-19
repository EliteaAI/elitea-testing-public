---
name: checklist-generator
description: Generates a structured Functional Testing Checklist grouped by priority (P0/P1/P2) based on combined inputs from a GitHub issue report, ELITEA documentation research, a Playwright UI exploration report, and an OneTest existing coverage report. Use this skill when you have gathered issue, docs, UI, and existing test coverage data and need to produce a ready-to-review QA checklist before creating test cases.
---

# Checklist Generator

## OBJECTIVE

Act as a Senior QA / Test Architect. Generate a strictly formatted Functional Testing Checklist based on the combined research inputs provided. Focus on how the implementation of the GitHub issue may negatively affect the product. Assume existing functionalities work correctly. Your output must identify what needs to be rechecked after the implementation.

---

## INPUT

The following structured inputs must be provided:

- **GitHub Issue Report** (from `reading-github-issue` skill): title, type, milestone, labels, issue number, steps to reproduce, expected/actual results, feature area, integration areas.
- **Documentation Report** (from `elitea-docs-researcher` skill): feature overview, functionality, configuration, integration points, constraints, recent changes.
- **UI Exploration Report** (from `elitea-playwright-explorer` skill): observed UI elements, workflows, navigation, behaviors, edge cases seen in the product.
- **OneTest Coverage Report** (from `onetest-researcher` skill): existing test cases in OneTest grouped by component/suite, identified coverage gaps, and test cases likely to be affected by the issue implementation.

---

## SEVERITY DEFINITIONS (STRICTLY FOLLOW)

- *P0 (Blocker/Critical):* Completely prevents users from using core functionality, or key system functionality is broken/produces unsafe behavior. Includes full system/workflow shutdown, data corruption, authentication failures, agent creation failures, system crashes, incorrect pipeline execution, credential update failures, intermittent integration (toolkit/MCP) failures, artifact indexing issues causing hallucinations, and UI sections (tabs, settings panels) failing to load. A workaround may or may not exist.
- *P1 (High):* Important features are disrupted but the platform remains usable. Includes inaccurate agent analytics, misleading progress indicators, performance degradation during agent execution, model-switching issues requiring retries, and custom instruction templates not applied correctly.
- *P2 (Medium):* Non-critical bugs affecting usability, display, or secondary features without interrupting main workflows. Includes UI misalignment or styling issues, logs not updating in real time, typos or inaccurate labels, and non-blocking API warnings.

DO NOT generate Low priority checklist items.

---

## ANALYSIS SCOPE

Based on all provided inputs, analyze and cover:

- Main functionalities of the affected feature
- Core workflows (create, edit, delete, configure, execute)
- File handling behavior (if applicable)
- Navigation and UI stability
- Permissions and access control
- Error handling and validation
- Edge cases and boundary conditions
- Large/small data scenarios
- **Integration scenarios:** how the affected feature is used by or interacts with other product areas (e.g., Agents, Chat, Pipelines, Toolkits, other menus). Include scenarios that verify the feature still works correctly from those consumer perspectives.
- Other appropriate test scenarios derived from the documentation and UI reports
- **Existing coverage awareness:** use the OneTest Coverage Report to identify gaps not yet tested, and to flag scenarios where existing test cases must be re-validated after the issue implementation. Do NOT generate new checklist items that perfectly duplicate already-existing test cases; instead, generate a re-validation item referencing the existing test if a regression risk is identified.

---

## CHECKLIST REQUIREMENTS

Each checklist item MUST:

- Be independent and executable on its own
- Be clear for someone unfamiliar with the system
- Use explicit step-by-step validation
- Include realistic test data when needed
- Avoid internal jargon unless explained
- Avoid repetition between priority levels
- Cover positive and negative validation flows where relevant
- Avoid business impact explanation
- Avoid expected result section
- Avoid risk description
- Avoid low-level cosmetic-only issues

DO NOT include items that do not correlate with the issue.

**Consolidation rule:** If two or more candidate checklist items cover the same verification objective and the same validation steps but differ only in input values or test data (e.g., different file types, different bucket names, different user roles), they MUST be merged into a single checklist item. List the data variations as a table or bullet list in the **Validation Steps** section. Do NOT create a separate item per data variant.

---

## OUTPUT FORMAT (STRICT)

Return the checklist in exactly this format:

---

# Functional Testing Checklist for [Feature Name]

## Pre-Testing Setup (if applicable)

- Required environment configuration
- Required test data
- Required permissions
- Any setup actions

---

Repeat the following structure for each priority section — **P0 (Blocker/Critical)**, **P1 (High)**, **P2 (Medium)**:

## 📌 P[N] ([Label])

### [ ] [Checklist Item Title]

**Verification Objective:**  
Short description of what is being verified.

**Preconditions:**  
(Only if required. Otherwise omit.)

**Validation Steps:**  
1. Step-by-step instructions
2. ...

---

## CONSTRAINTS

- Do NOT include analysis commentary in the checklist output.
- Do NOT include expected results sections in checklist items.
- Do NOT include business impact in the checklist output.
- Do NOT include Low priority items.
- Do NOT fabricate test scenarios not supported by the provided inputs.
- Do NOT duplicate test scenarios that already exist in OneTest with identical coverage scope — reference them as re-validation items instead.
- Return ONLY the formatted checklist — no preamble or closing remarks.
