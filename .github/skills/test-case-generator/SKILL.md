---
name: test-case-generator
description: Generates fully structured test case Markdown files from a Functional Testing Checklist and GitHub issue data. Performs a similarity check via OQL before writing files to catch duplicates. Handles suite/folder resolution via Glob, allocates sequential ELITEA-NNNN IDs from index.json, writes .md files to the TMS workspace, creates a git branch, and opens a PR. No SaaS API calls — all storage is file-based in the EliteaAI/onetest-ai-tm-Elitea git repo. Use this skill after a checklist has been produced and reviewed.
argument-hint: "[checklist] [github issue URL]"
---

# Test Case Generator

## OBJECTIVE

Generate fully populated test case Markdown files from a provided Functional Testing Checklist and GitHub issue data. Present them to the user for review, then handle suite resolution, duplicate detection, file writing, and opening a pull request — only after explicit user confirmation at each step.

---

## FIXED CONFIGURATION

- **TM_REPO:** `EliteaAI/onetest-ai-tm-Elitea` — hardcoded, never ask the user for this value.
- **TM_WORKSPACE:** `~/.onetest-workspaces/EliteaAI/onetest-ai-tm-Elitea` — local clone path.
- **SUITE_ROOT:** `tests/elitea-platform/`

---

## INPUT

The following must be provided:

- **Functional Testing Checklist** (from `checklist-generator` skill): full checklist grouped by P0/P1/P2.
- **GitHub Issue Report** (from `reading-github-issue` skill): issue URL, issue number, type, milestone, labels, feature area.

---

## EXECUTION FLOW

### Step 1 — Generate test cases

For every checklist item, produce a fully populated test case following the TEST CASE FILE STRUCTURE below. Cover all fields — do not leave any required field empty.

Present ALL generated test cases to the user in full detail so they can review the complete content before anything is written.

Ask: **"Here are the [N] generated test cases. Would you like me to push them to the TMS repo?"**

STOP and wait for explicit user answer.

---

### Step 2 — Duplicate detection

Once the user approves, search for similar existing test cases across the **entire TMS repo** before asking for any suite details:

- Call `search_test_cases` with `query: "title ~ \"<keyword from each generated title>\"", repo: "EliteaAI/onetest-ai-tm-Elitea"` for each generated test case (run in parallel).
- For each generated test case, compare its title against all returned results — look for semantically similar titles (same feature area, same action, same scenario).
- If similar test cases are found: present a table with the matched `ELITEA-NNNN` ID, its current path/module, and the generated title it resembles. Ask: **"The following similar test cases already exist: [table]. Should I update them in place, skip them and push only new ones, or ignore similarities and push all?"** STOP and wait for explicit user answer.
- Record the decision — it governs Steps 3 and 4.

---

### Step 3 — Suite resolution

Ask the user: **"Please confirm the parent suite name and target suite name where the new test cases should be placed."**

STOP and wait for explicit user answer, then:

1. Use `Glob("tests/elitea-platform/**/*.md")` in the TMS workspace to discover existing suite paths.
2. Check whether the target suite folder already exists:
   - If it **exists**: record the path (e.g. `tests/elitea-platform/artifacts/`).
   - If it **does NOT exist**: present the proposed path, then ask: **"Suite folder 'tests/elitea-platform/<suite>/' does not exist. I will create it. Please confirm (yes/no)."** NEVER create the directory without explicit confirmation.
   - If confirmed: run `Bash("mkdir -p ~/.onetest-workspaces/EliteaAI/onetest-ai-tm-Elitea/tests/elitea-platform/<suite>/")`.

---

### Step 3b — ID allocation

Read `~/.onetest-workspaces/EliteaAI/onetest-ai-tm-Elitea/index.json` to find the highest current `ELITEA-NNNN` sequence number. Increment by 1 for each new test case.

Use format `ELITEA-{seq:04d}` (zero-padded to 4 digits, e.g. `ELITEA-0043`).

---

### Step 4 — Write test case files

For **new** cases — write one Markdown file per test case:

```
~/.onetest-workspaces/EliteaAI/onetest-ai-tm-Elitea/tests/elitea-platform/<suite>/ELITEA-NNNN_<kebab-slug>.md
```

The `<kebab-slug>` is the title converted to lowercase with spaces replaced by hyphens (max 60 chars, strip special characters).

Each file MUST follow the TEST CASE FILE STRUCTURE below.

For **existing** cases (user chose "update in place") — use `Edit` tool on the resolved file path to update fields that differ.

---

### Step 4b — Git PR workflow

Present a preview table of all files to be committed (path, action: create/update).

Ask: **"Ready to commit [N] test cases and open a PR. This is the final step — please confirm (yes/no)."**

STOP and wait for explicit confirmation.

Only after receiving "yes":

```bash
cd ~/.onetest-workspaces/EliteaAI/onetest-ai-tm-Elitea
git checkout -b add-tc/<kebab-slug>
git add tests/elitea-platform/<suite>/
git commit -m "add: ELITEA-NNNN <title>"
git push -u origin add-tc/<kebab-slug>
gh pr create --title "add: ELITEA-NNNN <title>" --body "Adds test cases for <feature> from GitHub issue <URL>.\n\nTest cases: <comma-separated ELITEA-NNNN IDs>"
```

For multiple test cases in a single branch, use the first ID in the branch name and list all IDs in the commit message and PR body.

After the PR is created, present the PR URL to the user.

---

### Step 5 — Post-merge index refresh

After the user merges the PR, instruct them to run:

```
onetest-tms/build_index({ repo: "EliteaAI/onetest-ai-tm-Elitea" })
```

Or offer to run it immediately if they confirm the PR has been merged.

---

## TEST CASE FILE STRUCTURE

Every test case file MUST follow this exact format:

```markdown
---
id: ELITEA-NNNN
title: "Verb-first concise title matching the checklist item"
priority: critical|high|medium|low
type: functional|regression|smoke|integration|exploratory
module: <feature-area-lowercase>
status: draft
execution_type: manual|automated
tags: [feat:X, r-X.Y.Z]
requirements: [EliteaAI/elitea_issues#NNNN]
---

## Preconditions

- User is logged in to `{{base_url}}`
- [Any other pre-conditions required]

## Test Data

| Field | Value |
|-------|-------|
| URL | `{{base_url}}/app/` |
| [field] | [value] |

## Steps

| # | Action | Expected Result |
|---|--------|-----------------|
| 1 | [Atomic action description] | [Concrete, verifiable expected result] |
| 2 | ... | ... |

## Expected Final State

[Describe the final state of the system after all steps are completed successfully.]

## Pass/Fail Criteria

**Pass:**
- [Success condition 1]
- [Success condition 2]

**Fail:**
- [Failure condition 1]
- [Failure condition 2]
```

---

## PRIORITY MAPPING

- Checklist section **P0 (Blocker/Critical)** → `priority: critical`
- Checklist section **P1 (High)** → `priority: high`
- Checklist section **P2 (Medium)** → `priority: medium`
- NEVER upgrade or downgrade a priority from its checklist group.

---

## TAGGING RULES

Tags MUST be derived exclusively from the GitHub issue. Do NOT invent or add generic tags.

Mandatory tags for every test case (all lowercase):

| Tag | Source | Format | Example |
|---|---|---|---|
| Release tag | GitHub issue **Milestone** field | `r-X.Y.Z` | `R-2.0.1` → `r-2.0.1` |
| Feature tag | GitHub issue labels with `feat:` prefix | `feat:X` | `feat:artifacts` |

Additional tags: include all other GitHub issue label values exactly as they appear (lowercased). Only use labels present in the issue.

---

## TRACEABILITY REQUIREMENTS

All traceability fields MUST be filled for every test case:
- `requirements`: GitHub issue reference in format `EliteaAI/elitea_issues#NNNN` — **mandatory, never omit**.
- `module`: feature area (lowercase, hyphens for spaces) — **mandatory, never omit**.

---

## SUITE NAMING RULES

- Suite folder names must be **lowercase with hyphens** (e.g., `agent-toolkits`, `chat-interface`).
- Use the feature name from the GitHub issue as the suite folder name.
- If the folder already exists, use it as-is without creating a duplicate.

---

## CONSTRAINTS

- **Consolidation rule:** If two or more generated test cases would be identical in steps and expected results but differ only in test data (e.g., different file types, bucket names, user roles), they MUST be merged into a single test case. List all data variations in the `## Test Data` section as a table. Do NOT create a separate test case per data variant.
- Always use `{{base_url}}` for all URLs — never hardcode environment-specific URLs.
- NEVER call any write operation (file write, mkdir, git commit, PR creation) without explicit user confirmation ("yes").
- NEVER delete, overwrite, or update any existing test case file without explicit user confirmation.
- NEVER use placeholder or fabricated `ELITEA-NNNN` IDs — always allocate from `index.json`.
- If `index.json` cannot be read, STOP and ask the user to confirm the TM_WORKSPACE path before proceeding.
- Always present a summary table of created/updated file paths and IDs after completion.
- Do NOT reference `product_id`, `folder_id`, `ONE_TEST_TOKEN`, or any SaaS API parameters.
