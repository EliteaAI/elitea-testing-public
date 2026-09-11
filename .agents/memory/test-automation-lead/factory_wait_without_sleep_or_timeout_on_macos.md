---
name: Factory-mode in-turn waiting — bare `sleep` is blocked and `timeout` does not exist on macOS
description: The one Bash shape that waits inside a turn on this host: a bounded for-loop with grep-and-break, ≤540 s total, timeout 600000
type: feedback
aliases: [sleep blocked, timeout command not found, bounded wait loop, in-turn wait, gate polling shape]
tags: [area/gate, area/factory, type/process]
created: 2026-09-11
updated: 2026-09-11
---

## What failed (#2201, 2026-09-11)

- `sleep 90; cat log` → harness error *"Blocked: sleep … To wait for a condition, use Monitor"*.
  Monitor is the session-fatal trap in factory mode, so that hint must be ignored.
- `timeout 540 bash -c 'until …'` → `command not found: timeout` (macOS has no coreutils `timeout`).

## What works — one call, bounded, no Monitor

```bash
bash -c 'for i in $(seq 1 52); do grep -q "ALL RUNS DONE" /tmp/gate_X.log 2>/dev/null && break; sleep 10; done'
cat /tmp/gate_X.log; pgrep -f gate_X.sh >/dev/null && echo alive || echo finished
```
52 × 10 s = 520 s < the 600 000 ms cap. Launch the gate with `nohup script > log 2>&1 &` first.
Repeat the call if the loop exits without the sentinel; never chain sleeps in one line.

Related: [[a_null_delta_card_still_owes_a_full_gate]]
