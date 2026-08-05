---
name: Testid provenance claim — verify commit timestamp vs AFS commit
description: Before writing "predates this session"/"AFS drift" in a testid-provenance narrative, diff the testid commit's timestamp against the AFS commit's timestamp
type: feedback
---

## What happened (ELITEA-2338, fix round 1)

The original PR #1221 body + `secrets_page.py` docstring claimed
`secret-row-actions-button` / `secret-actions-menu-edit-value` / `-hide` /
`-delete` "already carried real `data-testid`s ... predating this
test-automation-engineer session" and that the AFS's "testid needed" claim
was drift. This was false and shipped unverified.

Git evidence: `EliteaAI/EliteaUI@dd47b184` (the testid commit, titled "add
data-testid for secret row actions button + menu items (delete flow)") is
dated `2026-08-05 19:10:04`, and this case's own AFS commit (`887271e3`) is
dated `2026-08-05 19:07:48` — the testid commit landed **~2 minutes AFTER**
the AFS, in the same session, correctly fulfilling the AFS's accurate
"testid needed" request. There was no drift; the "predates this session"
claim was simply never checked against the commit's own timestamp.

## Rule going forward

Before writing ANY testid-provenance sentence that asserts timing
("pre-existing", "predates this session", "the AFS drifted") — even one
that *feels* obviously true because you don't remember adding the testid
yourself — run the one-line check and cite its output:

```bash
git -C ../EliteaUI log -1 --format='%H %ad %s' --date=iso <the-testid-commit-sha>
git log -1 --format='%H %ad %s' --date=iso <the-AFS-commit-sha>   # this repo
```

If the testid commit's timestamp is close to (same session as) or after the
AFS commit's timestamp, it was added THIS session — say so, don't claim
pre-existing/drift. A commit *message* naming the exact case (e.g. "delete
secret row actions button + menu items (delete flow)") is itself a strong
signal it's this-session work, independent of the timestamp check.

This is the same discipline as the closure-record "fresh ground truth" rule
(`.agents/role-overrides.md`) — a provenance claim without a paste of the
verifying command's output is not a verification, it's a guess that reads
as a fact.
