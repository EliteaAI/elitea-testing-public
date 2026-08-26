---
name: Gate wait-loop pgrep matches its own shell
description: An `until ! pgrep -f <script>` wait loop never exits — the loop's own shell command line contains the pattern
type: feedback
aliases: [pgrep self-match, gate wait loop hangs, until pgrep never exits, background poll hangs]
tags: [area/tooling, type/gotcha]
created: 2026-08-26
updated: 2026-08-26
---

## The trap

Waiting on a detached `gate-case.mjs` run with

```bash
until ! pgrep -f "gate-case.mjs" >/dev/null; do sleep 15; done
```

**never exits.** `pgrep -f` matches the FULL command line of every process — and the
waiting shell's own command line contains the literal string `gate-case.mjs`. The loop
matches itself and spins forever. Two such loops burned ~20 minutes of wall clock on the
settings-w03 gate while the run it was waiting for had already finished in 2m43s.

The symptom is indistinguishable from "the job is still running": `pgrep` reports a hit,
`ps -o etime=` shows a long-lived process — and that process is the poller.

## What to do instead

1. **Time the job first with one `--n 1` foreground call** (`timeout: 600000`). This whole
   batch ran in ~165s; there was never a need to detach. Detaching is for jobs that
   genuinely exceed ~8 minutes — measure before assuming.
2. If a wait loop is unavoidable, key it on something that cannot match the poller:
   the process's **PID** (`kill -0 $pid`) or a **sentinel file** the job writes on exit
   (`until [ -f done.flag ]; do sleep 15; done`), never a `pgrep -f` on the script name.
3. Diagnose a suspiciously long wait by checking for the REAL worker, not the wrapper —
   `pgrep -fl pytest` returning nothing while `pgrep -f gate-case.mjs` hits is the
   signature of exactly this bug.

Related: [[tms_case_file_path_must_be_found_not_guessed]]
