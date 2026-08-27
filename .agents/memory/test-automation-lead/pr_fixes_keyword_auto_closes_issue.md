---
name: A PR body saying "Fixes #N" auto-closes the issue on merge
description: Never put a closing keyword in an automation PR body — Done and issue-close are human-only here
type: feedback
aliases: [fixes keyword, closes keyword, auto-close, issue closed on merge, gh pr merge closed my card]
tags: [area/tracker, type/gotcha]
created: 2026-08-27
updated: 2026-08-27
---

## The trap

GitHub closes an issue automatically when a merged PR's body contains
`Fixes #N` / `Closes #N` / `Resolves #N`. On this project that silently
violates the board contract: **`Done` and issue-close are HUMAN-ONLY**
(`.agents/profile.md` § Issue tracker). The agent-terminal state is
**`Ready`** — delivered, issue still OPEN, awaiting human acceptance.

Hit for real on #1811 (2026-08-27): the PR body opened with `Fixes #1811.`,
`gh pr merge` closed the issue, and it had to be reopened before the closure
record could be posted.

## What to do instead

- Write **`Refs #N`** or plain **`#N`** in the PR body, never a closing keyword.
- If it already merged with one: `env -u GITHUB_TOKEN gh issue reopen <N>`
  immediately, then continue with the closure record and card → `Ready`.
- Verify after every merge — it is one cheap read:
  `env -u GITHUB_TOKEN gh issue view <N> --json state -q .state` must print `OPEN`.

The failure is silent from the merge's side: nothing in `gh pr merge`'s output
mentions that it closed an issue.

Related: [[project_briefing]]
