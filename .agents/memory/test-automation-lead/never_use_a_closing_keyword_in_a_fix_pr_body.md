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

## Recurrence 2026-09-09 (#2112 / PR #2133) — caught by the END-OF-SESSION readback, not before

I opened PR #2133's body with `Fixes #2112.` and merged it. The issue auto-closed, silently —
`gh pr merge` reports nothing, and the board status stayed `Ready`, so **the card looked
perfectly delivered**. It surfaced only because my final verification read `state` back:

```
issue #2112 state=CLOSED status=Ready
```

Recovery (both halves are needed — reopening alone leaves the landmine armed):
```
env -u GITHUB_TOKEN gh api -X PATCH repos/<repo>/issues/<N> -f state=open
env -u GITHUB_TOKEN gh api -X PATCH repos/<repo>/pulls/<P> --input <body-without-keyword>.json
```
…then a correction comment, so nobody reads the close/reopen as a human acceptance.

**Two hardenings for me:**
1. **Grep the body file before `gh pr create`**, not after:
   `grep -inE '\b(close[sd]?|fix(e[sd])?|resolve[sd]?) #[0-9]+' /tmp/pr-body.md` must be empty.
   I write the body to a temp file anyway — the check is free at that moment and expensive later.
2. **Always read `state` back at end-of-session**, not just the board status. Status `Ready` and
   state `CLOSED` coexist happily, and status is the thing I naturally check.
