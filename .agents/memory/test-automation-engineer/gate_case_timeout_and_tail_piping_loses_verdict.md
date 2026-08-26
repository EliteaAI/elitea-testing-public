---
name: gate-case.mjs timeout and tail-piping loses verdict
description: gate-case.mjs --timeout too short + piping through tail silently discards the JSON verdict
type: feedback
---

`scripts/gate/gate-case.mjs` (`.claude/skills/test-automation-workflow/scripts/gate/`)
runs the spec via Node's `execSync` with `stdio: 'inherit'` for the pytest child. Two
traps compound on a large/slow batch (5 UI specs, ~16 min real runtime observed
2026-08-12, skills-remaining-w3):

1. **`--timeout` (seconds) must comfortably exceed the REAL suite runtime, not a
   guess.** `execSync`'s timeout kills the immediate shell child on expiry, but does
   NOT reliably kill the grandchild pytest/Playwright process tree (no process-group
   kill) — the orphaned pytest kept running and writing to the inherited stdout fd for
   ~400s past the node timeout in one observed run (570s configured, 964.89s actual).
   Node exits early (ETIMEDOUT) but the pipe stays open until the orphan truly exits.

2. **Never pipe gate-case.mjs's output through `| tail -N`.** `tail` buffers until
   EOF, so nothing appears in the redirected file until the WHOLE piped stream ends —
   including the orphan's post-timeout output. Once EOF finally arrives, `tail -N`
   keeps only the last N lines, and the orphan's late output (megabytes of inlined
   page HTML/minified JS from Playwright's failure-context, then pytest's real final
   summary line) pushes node's own `--json` verdict block entirely out of the
   captured window — `grep '"verdict"'` finds zero hits even though the run
   genuinely completed.

**Fix / practice:** set `--timeout` generously (e.g. 2-3x the last known runtime, or
0 to disable), and redirect raw to a file (`> out.log 2>&1 &`) instead of `| tail`.
If you still lose the JSON block, the ground truth is `automation/reports/junit.xml`
(freshest by mtime) — parse it directly for pass/fail per testcase; the pytest
summary line at the true tail of the log (`N failed, ... in Ns`) is also reliable.

**Third trap, distinct from the above (2026-08-15, chat-remaining-w04 gate):** the
script's own `--timeout` flag is a SEPARATE knob from the Bash-tool's own `timeout`
parameter on the invoking call. Passing `--timeout 480` to gate-case.mjs does nothing
to protect against the Bash tool's own 120s default — 2 straight attempts got killed
at exactly 2 minutes (exit 143, "Command timed out after 2m 0s") before the script's
internal timeout ever had a chance to matter, because the OUTER tool call itself
had no `timeout` param set. Set BOTH: the tool call's `timeout` (e.g. 600000ms) AND,
if desired, the script's `--timeout` (seconds) as a secondary guard. Good news: an
outer-tool kill took the whole process tree with it both times — no orphaned pytest
survived (checked via `ps aux | grep pytest`), so no cleanup was needed beyond
`git checkout <branch>` to leave the detached-HEAD state gate-case.mjs left behind.
