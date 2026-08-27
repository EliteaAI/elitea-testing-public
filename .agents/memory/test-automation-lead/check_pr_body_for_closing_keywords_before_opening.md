# Check the PR body for closing keywords BEFORE opening it

**Learned (the hard way, twice):** 2026-08-27 (#1815) — the note
`pr_fixes_keyword_auto_closes_issue.md` already existed and I still shipped
`Fixes #1815` in the PR body. Merge auto-closed the card's issue.

## Why the existing note didn't fire

It was written as a *fact about GitHub* ("`Fixes #N` auto-closes"), so it only helps if
you happen to recall it while composing prose. The failure is at **authoring time**, in a
long PR body written in one shot, where "Fixes #1815" reads like a helpful cross-reference.

## The check, as an action rather than a fact

Immediately before `gh pr create`, grep your own body:

```bash
grep -inE '\b(close[sd]?|fix(e[sd])?|resolve[sd]?)\b[[:space:]]*:?[[:space:]]*#[0-9]+' <<<"$BODY"
```

Any hit → rewrite as `Refs #N` / `Root cause: #N` / plain prose. The keyword is only safe
on issues a human is happy to see auto-closed — on this board that is **none**, because
`Done` and issue-close are human-only and `Ready` is the agent-terminal state.

Same applies to **commit messages** — the keyword works from there too, and a squash
merge lifts the commit body into the merge commit.

## If it already fired

`gh issue reopen <n>`, then post a self-correction comment saying it was the agent's
error and the card remains `Ready`. Don't quietly reopen — the auto-close is visible in
the timeline and an unexplained reopen reads worse than the mistake.
