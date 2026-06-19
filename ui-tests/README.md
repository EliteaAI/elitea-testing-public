# UI Tests

This directory contains test cases and scenarios for testing the Elitea AI platform user interface.

## Test Management

Test cases are managed in **OneTest TMS** — a git-native test management system backed by GitHub.

**Repository:** [EliteaAI/onetest-ai-tm-Elitea](https://github.com/EliteaAI/onetest-ai-tm-Elitea)

Test cases live under `tests/` in that repository. The directory tree is the suite structure:

```
tests/<suite>/<sub>/<ID>_<slug>.md
# e.g. tests/elitea-platform/agents/ELITEA-0001_valid-login.md
```

## Test Case Format

Each test case is a Markdown file with YAML front-matter. IDs are allocated by the TMS (`allocate-id`) — never hand-set.

```markdown
---
id: ELITEA-XXXX
title: "Short descriptive title"
priority: critical | high | medium | low
type: regression | functional | ...
module: <feature-area>
status: draft | ready | deprecated
execution_type: manual | automated
tags: [feat:some-feature]
requirements: [EliteaAI/elitea_issues#NNN]
---

# ELITEA-XXXX: <title>

**Module:** <module> · **Priority:** <priority> · **Type:** <type>

## Preconditions

- Logged in to ELITEA (`{{base_url}}`)
- ...

## Test Data

| Field | Value |
|-------|-------|
| ...   | ...   |

## Steps

| # | Action | Expected Result |
|---|--------|----------------|
| 1 | ...    | ...             |

## Expected Final State

...

## Pass/Fail Criteria

**Pass:**
- ...

**Fail:**
- ...
```

### Front-matter fields

| Field | Required | Values |
|-------|----------|--------|
| `id` | yes | `ELITEA-NNNN` — allocated by TMS |
| `title` | yes | descriptive string |
| `priority` | yes | `critical`, `high`, `medium`, `low` |
| `status` | yes | `draft`, `ready`, `deprecated` |
| `execution_type` | yes | `manual`, `automated` |
| `type` | yes | e.g. `regression`, `functional` |
| `module` | yes | feature area slug |
| `tags` | no | array, e.g. `[feat:agents, eng:backend]` |
| `requirements` | no | linked issue refs |
| `size` | no | `S`, `M`, `L` — set by test-sizer agent |
| `automation_test_id` | no | list of automation test IDs (when `execution_type: automated`) |

Use `{{base_url}}` for URLs in steps — substituted at run time to keep cases environment-agnostic.

## Guidelines

- Author test cases in the [onetest-ai-tm-Elitea](https://github.com/EliteaAI/onetest-ai-tm-Elitea) repo, not here
- Use the `test-author` agent (or `/test-author` skill) to create well-formed cases from rough descriptions
- Use the `test-sizer` agent to assign `size:` before authoring to catch cases that should be split
- IDs are assigned by `allocate-id` — never pick or reuse them manually
- Group cases under `tests/elitea-platform/<feature-area>/`