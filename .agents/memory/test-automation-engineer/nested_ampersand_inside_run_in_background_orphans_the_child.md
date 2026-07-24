---
name: Nested `&` inside a run_in_background Bash call orphan-kills the real command
description: Backgrounding a shell script that ITSELF backgrounds the actual command with a trailing `&` returns "completed, exit 0" almost instantly while the real command is still mid-flight — the wrapper script exits and typically takes the orphaned child down with it, producing a truncated log with no final summary line.
type: feedback
---

## What happened (cov60 foundation pass, ELITEA/GAP-020/054/073/077)

Wanted a long `pytest -m smoke` run to happen in the background so I could
keep working. Wrote:

```bash
cd automation && HEADLESS=true ../.venv/bin/pytest -m smoke ... > /tmp/log 2>&1 &
echo "started pid $!"
```

...and passed that whole script to Bash with `run_in_background: true`. The
tool reported the wrapper **completed with exit code 0** within a second (it
only had to background the real command and echo a line — that's genuinely
fast), but the log file was left truncated mid-test (12 lines, no PASSED/
FAILED for the in-progress test, no final "N passed" summary). The real
`pytest` process had been started but was orphaned the moment its parent
shell exited, and did not survive to completion.

**Root cause:** `run_in_background: true` already backgrounds the *entire*
command I hand it. Adding my own trailing `&` backgrounds the real work
*inside* that already-backgrounded shell, so the visible "job" the harness is
tracking is the trivial wrapper (which finishes in ~0s), not the actual
pytest run. When the wrapper's own shell process exits, orphaned background
children typically get cut off (no controlling terminal to keep them alive).

## The fix

Never nest `&`/`echo $!` inside a command passed to `run_in_background:
true`. Just pass the real, long-running foreground command directly:

```bash
cd automation && HEADLESS=true ../.venv/bin/pytest -m smoke -v -p no:cacheprovider
```

with `run_in_background: true` on the Bash call itself. The harness handles
the backgrounding; let it run in the foreground of its own managed process.

## How to catch it happening again

- "Completed, exit 0" arriving within a couple seconds for a command you
  expect to take minutes is the tell — sanity-check the output file length/
  final summary line before trusting the exit code.
- A truncated log missing pytest's final `"N passed/failed in Xs"` line (or
  any tool's equivalent terminal summary) after a background task reports
  "completed" means the child was cut short, not that the run was short.
