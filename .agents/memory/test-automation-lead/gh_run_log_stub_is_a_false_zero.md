---
name: gh run view --log returns a stub while a run is in progress
description: An in-progress run yields an 81-byte notice, so any grep -c over it reports 0 — a false negative that reads exactly like a fixed bug
type: feedback
---

`gh run view --repo <r> --job <id> --log` does **not** fail while the run is still
in progress. It exits 0 and writes an 81-byte file:

```
run <id> is still in progress; logs will be available when it is complete
```

So `grep -c '<signature>' job.log` returns **0** — indistinguishable from "the
signature is gone". This is a false-zero generator aimed precisely at the moment
you most want a zero: validating that a fix removed a failure signature.

Field case 2026-09-07 (#2023): I reported "race signature eliminated, 0 hits in all
three jobs" off three such stubs, minutes before the run had finished. The real
measurement (after completion) happened to agree — but it did not have to, and I
had already written the claim down.

**Guard, always: assert the log is real before you trust a count.**

```bash
env -u GITHUB_TOKEN gh run view --repo <r> --job <id> --log > job.log
[ "$(wc -c < job.log)" -gt 10000 ] || { echo "STUB — run not finished"; exit 1; }
grep -c 'Execution context was destroyed' job.log
```

A real per-suite job log here is 74–120 KB. Also: `gh run view --json status` can say
a *job* is `completed` while the **run** is still `in_progress` (a later publish job is
running) — and log availability follows the RUN, not the job. Wait for
`status == completed` at the run level, then fetch.

Note this cuts the other way too: `gh run view --log` **truncates** very large job logs,
so a count off a completed-but-truncated log undercounts. When the number has to be
right, parse the JUnit XML from the run artifacts instead of grepping logs — it is the
authoritative record (`gh run download <run> -n test-results-<env>-user<N>-<runNumber>`;
note the artifact suffix is the **run number**, not the run id).
