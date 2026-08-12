---
name: A unit PR's self-reported testid list can drift from the actual committed attribute names
description: verify each testid name in a PR body against `git show <sha> --stat`/the diff itself before citing it in a closure record's promotability grep — the PR shorthand can be a transcription slip, not a syntax-detection miss
type: feedback
---

## What happened

ELITEA-2034 (issue #471), unit PR #1147's body listed two testids as:

```
pipeline-state-drawer-add-variable-button, pipeline-state-drawer-add-variable-name-input
```

The actual `add-data-testid` commit (`EliteaUI@1119c916`) added them as:

```
pipeline-state-add-variable-button, pipeline-state-add-variable-name-input
```

— no `-drawer-` infix. Caught only because the closure-record promotability
grep (fresh `git fetch origin` + `git grep` on `origin/automation/testids`)
came back **empty** for the `-drawer-add-variable-*` spelling, which is
suspicious enough on a testid the gate had just proven working (same shape
as `promotability_grep_false_negative.md`'s "empty means investigate, not
absent" rule) — but the root cause here was different: not a grep-syntax
gap, just the PR body itself being wrong. `git show 1119c916 --stat` showed
the real commit message with the correct names.

## Rule going forward

Don't copy a unit PR's "testids added" list verbatim into the trunk PR body
or the closure record. Before citing any testid name:
1. Grep it against the actual ref (`git grep -- "<name>" origin/automation/testids -- src/`).
2. If empty, don't assume absence — pull the real names from the adding
   commit's message/diff (`git show <sha> --stat` or the commit body,
   which `add-data-testid` writes with the accurate list) and re-verify
   with the corrected name.
3. If the trunk PR/closure record already shipped the wrong name, fix it
   (`gh pr edit`) rather than leaving a permanently wrong artifact — a
   closure record is read by humans and by future promotability checks.

This is a distinct trap from `promotability_grep_false_negative.md` (syntax
detection) — that entry's rule ("grep the bare value, then read the line")
still won't save you here, because the bare value itself is wrong. The
only fix is checking the PR's claimed names against the actual commit
before trusting them.
