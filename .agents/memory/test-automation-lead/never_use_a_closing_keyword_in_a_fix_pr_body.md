# Never use "Fixes #N" in a PR body — it bypasses the human close gate silently

**Date:** 2026-08-28 · **Evidence:** PR #1927 auto-closed issue #1893 on merge.

On this board, `Done` and issue-close are **human-only**, symmetric with human-only
`Approved` on the way in. The agent-terminal state is card → `Ready` with the issue
left **OPEN** (`.agents/profile.md` § Issue tracker, `.agents/workflow.md` § Closure
record).

A `Fixes #N` / `Closes #N` / `Resolves #N` keyword anywhere in a PR **body** makes
GitHub close the issue the moment the PR merges. That silently performs the exact
action the policy reserves for a human — and **nothing in `gh pr merge`'s output says
it happened**. I only caught it because the end-of-session check re-reads the issue
state instead of trusting that I never called `gh issue close`.

**Rule: in a PR body write a plain reference — "Tracking card: #N" — never a closing
keyword.** Same for commit messages, which carry the keyword into the squash commit.

**And keep `gh issue view <N> --json state` in the end-of-session check.** "I never ran
a close command" is not evidence the issue is open; a side effect you did not issue
directly is still your responsibility. This is the only check that would have caught it.
