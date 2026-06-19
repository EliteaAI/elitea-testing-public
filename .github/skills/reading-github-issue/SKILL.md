---
name: reading-github-issue
description: Reads and summarizes GitHub issues. Use this skill when the user provides a GitHub issue URL or issue number and wants to understand the issue details, reproduce steps, acceptance criteria, or needs to start working on a fix or feature described in the issue.
argument-hint: "GitHub issue URL or issue number"
---

# Reading GitHub Issues

## Purpose

This skill fetches and interprets GitHub issues so you can understand the problem, requirements, and context before writing code or providing guidance.

## When to use

- The user pastes a GitHub issue URL (e.g. `https://github.com/owner/repo/issues/42`)
- The user references an issue by number and repository (e.g. "issue #42 in owner/repo")
- The user says "look at this issue", "fix this issue", "implement this issue", or similar

## Steps

1. **Extract the issue reference** from the user's message — either a full URL or an owner/repo + issue number.
2. **Fetch the issue** using the available GitHub tools (e.g. `get_issue`) or by fetching the URL directly.
3. **Parse the issue** and extract:
   - **Title** — one-line summary of what is being requested
   - **Type** — bug, feature request, enhancement, documentation, etc.
   - **Description** — the full problem statement or feature description
   - **Steps to reproduce** (for bugs) — numbered list exactly as written
   - **Expected vs actual behavior** (for bugs)
   - **Acceptance criteria** — what "done" looks like, derived from the issue body or comments
   - **Labels / milestone / assignees** — relevant metadata
   - **Linked PRs or related issues** — context from the issue timeline
4. **Summarize the issue** in a structured, concise format (see Output Format below).
5. **Propose next steps** — suggest what code changes, files, or approach would address the issue.

## Output Format

Present the issue summary using this structure:

```
### Issue #<number>: <title>
**Type:** <bug | feature | enhancement | docs | ...>
**Repo:** <owner/repo>
**Labels:** <label1>, <label2>

#### Summary
<2-4 sentence description of the issue>

#### Steps to Reproduce (if bug)
1. ...
2. ...

#### Expected Behavior
...

#### Actual Behavior
...

#### Acceptance Criteria
- [ ] ...
- [ ] ...

#### Suggested Approach
<Brief notes on files/areas likely involved and possible fix or implementation strategy>
```

## Notes

- If the issue cannot be fetched, ask the user to paste the issue body directly.
- Preserve the original wording of acceptance criteria and reproduction steps — do not paraphrase them.
- If the issue references other issues or PRs, note them but do not fetch them unless the user asks.