---
name: Triage DEV CI failures against EliteaUI main, never automation/testids
description: automation/testids is ~152 behind main, so a localhost green cannot validate a DEV-env fix; diff main's recent commits first
type: feedback
aliases: [automation/testids stale, DEV failure triage, localhost verification gate, branch divergence]
tags: [area/ci, type/process]
created: 2026-09-29
updated: 2026-09-29
---

## The lesson

The project's documented local verification gate is `localhost:5173` against
EliteaUI **`automation/testids`**. That branch is **~152 commits behind `main`**
(and ~497 ahead). DEV (`dev.elitea.ai`) serves **`main`**. So the two UIs can
disagree about whether an element renders at all.

**First move on any DEV CI red that looks like "element not found":** list
EliteaUI `main` commits touching the component, in the 48h before the run —
not "is the testid on main" (it can be present and still be behind a new
conditional):

```bash
gh api "repos/EliteaAI/EliteaUI/commits?path=<file>&sha=main&per_page=12" \
  --jq '.[]|"\(.commit.author.date)  \(.sha[0:8])  \(.commit.message|split("\n")[0])"'
gh api "repos/EliteaAI/EliteaUI/commits/<sha>" --jq '.files[]|select(.filename|test("<file>"))|.patch'
```

Field case (ELITEA-1826, issue #2377, run #197): `471b753c` landed on `main`
~16h before the run and hid the element behind `!isEmptyFiles`. GitHub code
search still reported the testid as "present on main" — true, and irrelevant.
The AFS's "confirmed live" claim was also true *at authoring time*, because the
analyst explored `automation/testids`, which predates the commit.

**Corollary:** a fix for this class of failure **cannot be verified on
localhost/`automation/testids`** — that branch lacks the change, so a local
green is meaningless. Verification must run against DEV, or `automation/testids`
must first be synced past the commit.

Related: [[artifacts_toolbar_hidden_on_empty_bucket]]
