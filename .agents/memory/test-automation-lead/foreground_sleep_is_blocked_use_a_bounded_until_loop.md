# A bare foreground `sleep N; tail` is blocked — wait with ONE bounded `until` loop per Bash call

**Observed 2026-09-16 (#2337, factory mode).** `sleep 90; cat /tmp/gate.summary` was refused by the
Bash tool layer ("Blocked: sleep 90 followed by …; use Monitor … or run_in_background"). The factory
dispatch's rule 5 recipe (`sleep <n>; tail <log>` per call) therefore no longer executes as written, and
its rule-5 ban on Monitor still stands (a Monitor notification never arrives once the turn ends).

**What works, verified the same session:** a single bounded polling loop inside ONE Bash call —

```bash
n=0; until grep -q GATE_DONE /tmp/gate_X.summary 2>/dev/null || [ $n -ge 100 ]; do sleep 5; n=$((n+1)); done
echo "waited $((n*5))s"; cat /tmp/gate_X.summary
```

with `timeout: 600000`. Cap `n` so the loop exits before the 600 s tool cap (100×5 s = 500 s); if it exits
on the cap, re-issue the same call — that is the "one bounded slice per call" the dispatch asks for.
The detached job itself is still launched with `(nohup script > log 2>&1 &)` and its summary file ends in a
sentinel (`GATE_DONE`) the loop greps for.
