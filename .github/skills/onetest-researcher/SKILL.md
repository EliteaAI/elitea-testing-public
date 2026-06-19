---
name: onetest-researcher
description: Searches the OneTest TMS git repo for existing test cases related to a given feature or topic. Uses OQL queries (keyword, tag, module) across the EliteaAI/onetest-ai-tm-Elitea repository to produce a structured report of what test coverage already exists. Use this skill in parallel with elitea-docs-researcher and elitea-playwright-explorer during the research phase, before generating checklists or test cases.
argument-hint: "[feature name] [derived tags from issue]"
---

# OneTest Researcher

## OBJECTIVE

Search the OneTest TMS repository for existing test cases related to a given feature or topic. Return a structured report that informs the checklist generator about what test coverage already exists, so that new checklist items focus on gaps and avoid duplication.

---

## FIXED CONFIGURATION

- **TM_REPO:** `EliteaAI/onetest-ai-tm-Elitea` — hardcoded, never ask the user for this value.

---

## INPUT

The following must be provided:

- **Feature name / topic** (from `reading-github-issue` skill): the primary feature area the issue is about (e.g., "Artifacts", "Agent Toolkits", "Pipeline execution").
- **Derived tags** (from `reading-github-issue` skill): the label-based tags extracted from the GitHub issue (e.g., `feat:artifacts`, `feat:agents`, `eng:api`). Used as additional search signals.
- **Integration areas** (from `reading-github-issue` skill): other product areas that interact with the feature (e.g., "Agents", "Chat", "Pipelines").

---

## EXECUTION FLOW

### Step 1 — Broad keyword search

Call `search_test_cases` with:
- `query`: `title ~ "<feature name>" OR module = "<feature name>" LIMIT 100`
- `repo`: `EliteaAI/onetest-ai-tm-Elitea`

Results are returned as file paths (e.g. `tests/elitea-platform/artifacts/ELITEA-0042_upload-file.md`). Extract the `ELITEA-NNNN` ID from the path.

Capture all results.

---

### Step 2 — Tag-based search

For each unique feature-related tag from the derived tags (e.g., `feat:artifacts`), call `search_test_cases` with:
- `query`: `tags CONTAINS "<tag>" LIMIT 50`
- `repo`: `EliteaAI/onetest-ai-tm-Elitea`

Run all tag searches in parallel. Collect and de-duplicate results across all calls (deduplicate by `ELITEA-NNNN` ID).

---

### Step 3 — Integration area search

For each integration area identified in the issue (e.g., "Agents", "Chat"), call `search_test_cases` with:
- `query`: `module = "<integration area>" OR title ~ "<integration area>" LIMIT 50`
- `repo`: `EliteaAI/onetest-ai-tm-Elitea`

Run all integration searches in parallel. Collect and de-duplicate results, keeping only those whose title or module plausibly relates to the feature under investigation.

---

### Step 4 — Deduplicate and compile

Merge all results from Steps 1–3. Remove duplicate entries by `ELITEA-NNNN` ID (extracted from the file path). Group the final set by **module** (which corresponds to the suite/folder name in the TMS repo).

---

## OUTPUT FORMAT (STRICT)

Return a structured report in exactly this format:

---

# OneTest Existing Coverage Report for [Feature Name]

## Summary

- **Total existing test cases found:** [N]
- **Suites/modules covered:** [list of module names]
- **Search terms used:** [feature name, tags, integration areas]

---

## Coverage by Component

For each module/suite, list the test cases found:

### [Module / Suite Name]

| ID | Title | Priority | Status |
|----|-------|----------|--------|
| ELITEA-NNNN | [title] | critical/high/medium/low | draft/ready/deprecated |

(Repeat for each module.)

---

## Coverage Gaps Observed

Based on the search results, list topics or scenarios for the feature under investigation that do NOT appear to have any existing test cases. Frame each gap as a short bullet:

- No existing tests found for [topic/scenario]
- No existing tests found for [topic/scenario]

(If no gaps are observable from search results alone, state: "No coverage gaps determinable from search results — full analysis deferred to checklist generation.")

---

## Existing Tests Likely to Be Affected

List test cases that may need to be reviewed or updated as a result of the issue implementation:

| ID | Title | Reason for Potential Impact |
|----|-------|-----------------------------|
| ELITEA-NNNN | [title] | [brief reason] |

(If none, state: "No existing test cases identified as likely to be directly impacted.")

---

## CONSTRAINTS

- Do NOT create, update, or delete any test cases — this skill is read-only.
- Do NOT expose credentials, tokens, or secrets.
- Do NOT hallucinate test case IDs or titles — only report what is returned by `search_test_cases` calls.
- IDs are `ELITEA-NNNN` format, extracted from the file path returned by the tool (e.g. `tests/.../ELITEA-0042_slug.md` → `ELITEA-0042`).
- If all searches return zero results, report that clearly and note the product may have no existing coverage for this feature.
- Return ONLY the formatted report — no preamble or closing remarks.
