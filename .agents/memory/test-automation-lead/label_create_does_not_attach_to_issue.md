---
name: gh label create does not attach the label to the issue
description: control-audit completion signal is the label ON the issue, not the label's existence repo-wide — the two are separate gh calls and an interrupted turn can post the verdict but skip attaching the label
type: feedback
---

## What happened (#268/PR#678, 2026-07-20)

The control-audit protocol's idempotent setup step is:

```bash
env -u GITHUB_TOKEN gh label create control:audited -d "..." -c 0E8A16
```

This **only registers the label definition in the repo** (or no-ops if it
already exists). It does **not** apply the label to any issue. Attaching it
requires a separate, distinct write:

```bash
env -u GITHUB_TOKEN gh issue edit <N> --add-label control:audited
```

On #268, the turn ran `gh label create` (idempotent, already existed — ignored),
then posted the full PASS verdict comment, then got interrupted before the
`--add-label` call ever ran. The verdict comment was live on the issue; the
completion signal (the label) was not. Per the control-audit contract, an
unlabeled exit reads as a **failed attempt** — the loop's queue filter
excludes labeled cards, so an audited-but-unlabeled card would be silently
re-picked and re-audited by a future run, wasting a full re-verification pass
(or worse, if the re-run's mechanical checks land differently against moved
ground truth, could produce a confusing second verdict on an already-settled
card).

## Recovery

On session resume after an interrupt, **don't trust memory that "the audit
finished" — re-read the issue's current labels before doing anything else**:

```bash
env -u GITHUB_TOKEN gh issue view <N> --repo <owner/repo> --json labels,comments \
  --jq '{labels: [.labels[].name], lastComments: [.comments[-3:][] | {id, createdAt, body: .body[0:120]}]}'
```

If the verdict comment is present but `labels` is empty, the fix is exactly
one call — `gh issue edit <N> --add-label control:audited` — then verify the
label actually landed (`--jq '[.labels[].name]'`), don't just trust the exit
code.

## The generalizable lesson

**`X create` (idempotent, global) and `X attach-to-this-record` (the actual
completion signal) are almost always two separate API calls, even when they
feel like one step in the protocol prose.** Any two-part write like this
(label create + label apply, or the same shape for milestones/assignees/
project-field values that need a "does the option exist" register step before
a "set on this item" step) deserves the same discipline: verify the
second, record-scoped write landed — independently of whether the first,
global-scoped write succeeded — before considering a multi-step protocol
complete.
