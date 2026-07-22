---
name: sync-guard should cross-check ps aux for a live process, and the post-merge dev-server restart is itself a guarded step
description: Recency-by-mtime can be ambiguous (files written minutes ago but no way to tell if the writer is still running); `ps aux` for a still-alive agent process attached to the same tree is a stronger, definitive signal. Separately, "never sync over someone's in-flight work" doesn't stop at the merge/push — `sync-base-branches`' own post-merge `pkill -f vite && npm run dev` restart step can just as easily clobber a live session that depends on the running dev server.
type: feedback
---

## What happened (2026-07-22, unattended sync run, issue #724)

Guard check on `automation/base` (elitea-testing-public, tree correctly
checked out on `automation/base` itself, not a foreign case branch this
time): dirty `automation/conftest.py` (an uncommitted, explicitly-WIP V8/CDP
coverage-instrumentation change) plus a 1.4GB `coverage/.v8/` fragment
directory whose newest file was written 4-5 minutes before the check. Mtime
recency alone says "very recent" but can't distinguish "a process is
actively writing this right now" from "a process wrote this 5 minutes ago
and has since exited/crashed" — both look identical from `stat` output.

Added a definitive check: `ps aux | grep -i claude` (and specifically
looked for `--agent scout`). Found PID 13551, `claude --agent scout`,
running continuously since 16:44 (~2h50m elapsed, state `S+` — attached to
a terminal, still foreground) — a real, currently-alive agent process, not
a ghost of one that already finished. That upgraded the finding from
"probably live" to "confirmed live," which is what justified skipping Part
1 entirely with confidence rather than hedging.

Separately: EliteaUI's `automation/testids` merge itself was judged safe
(dirty tree there was inert mode-bit noise, no recency red flags) and
proceeded normally. But the skill's own next step after a testids merge —
`pkill -f "vite" ; npm run dev &` to restart the dev server, because HMR
doesn't survive a branch-level merge — is *also* covered by the same
"never sync over someone's in-flight work" intent, and it's easy to miss
because the literal guard text only talks about the merge/checkout step,
not this follow-on one. The same scout process almost certainly has a
Playwright/CDP session attached to the currently-running dev-server
instance (its coverage captures need a live page to instrument) — killing
that process to restart Vite would drop that in-flight browser session
exactly like a bad checkout would drop in-flight file state.

## Rule going forward

1. When mtime recency alone feels ambiguous (a handful of minutes, not
   clearly stale but not a smoking gun either), check `ps aux` for a
   still-running agent/process plausibly attached to the same tree before
   committing to a stale-vs-live verdict. A live PID is stronger evidence
   than any mtime.
2. The "don't sync over in-flight work" guard applies to every write-ish
   step in the routine, not just the git merge/checkout: a dev-server
   restart, a `pkill`, anything that could terminate another session's
   live process, gets the same live-work check before it runs — even when
   the git-level merge that preceded it was itself judged perfectly safe.
3. When skipping a step for this reason, still do the rest of the
   day's-job verification you can safely do without it (this run still
   ran the smoke suite against the unrestarted server rather than skipping
   verification outright) and say explicitly in the report what was
   skipped and why, so a human can do the restart manually once it's safe.
