---
name: gh pr merge squash flag required
description: gh pr merge defaults to whatever the repo UI default is, NOT the project's squash policy — always pass --squash explicitly on automation PRs into automation/base
type: feedback
---

## What happened (issue #60 / ELITEA-1922, PR #292)

Merged an automation PR with `gh pr merge 292 --repo ... --merge --delete-branch`
— explicitly passed `--merge` (merge commit, preserving all individual commits)
instead of `--squash`. `.agents/profile.md` § Automation PR policy states:
"**Squash / rebase / merge**: squash (default) for small PRs into
`automation/base`." I typed `--merge` out of habit/autocomplete-adjacent
muscle memory from other merge flows, not because I checked the policy line
first.

## Why it slipped through

`gh pr merge` requires *some* strategy flag (or an interactive prompt) — it
doesn't silently fall back to a project-configured default the way a
squash-only repo setting might. Passing the wrong flag succeeds cleanly (exit
0, PR shows MERGED) with no warning that a *different* strategy was expected.
Nothing in the merge-gate checklist explicitly said "read the merge-strategy
line right before typing the `gh pr merge` command" — the policy is known
generally but wasn't re-checked at the point of the actual keystroke.

## Why I didn't try to fix it after the fact

`automation/base` is a shared branch (multiple concurrent sessions build off
it in this factory). Rewriting the merge commit into a squash after the fact
means either a force-push (forbidden — "plain push. If this needs --force,
STOP: something is wrong") or leaving the branch in a state other sessions
have already possibly built on top of. The safe move was: don't touch
history, declare the deviation transparently in the issue thread, log it
here. No functional harm — the 3 preserved commits (test, AFS amendment,
fixup) are each individually clean and legitimate; a merge commit vs. squash
only affects `automation/base`'s commit-graph shape, not correctness.

## Fix going forward

Before every `gh pr merge` call on an automation PR, say the merge-strategy
line out loud (re-read `.agents/profile.md` § Automation PR policy, not just
recall it) and pass the flag it names explicitly:
`gh pr merge <N> --repo <repo> --squash --delete-branch`. Treat "which flag"
as a checklist item in the merge gate, not a thing memory alone reliably
supplies under the pressure of "just get this merged."
