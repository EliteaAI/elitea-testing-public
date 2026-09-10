# Waiting on a background job in factory (unattended) mode — the shape that still works

**Verified 2026-09-10** while gating on DEV for card #2192.

The factory-mode brief says: wait INSIDE the turn, in cap-sized slices, one bounded
`sleep <n>; tail <log>` per Bash call. **Two of those mechanics have since broken:**

1. A bare `sleep 200; …` in a Bash call is now **rejected by the harness** ("To wait for a
   condition, use Monitor with an until-loop"). Monitor is session-fatal in factory mode —
   its notification never arrives, because the process exits when the turn ends.
2. `timeout` **does not exist on macOS** (`command not found`; coreutils' is `gtimeout`).

The shape that works — a condition loop with its own iteration cap, entirely in-turn:

```bash
nohup /tmp/job.sh > /tmp/job.log 2>&1 &          # launch detached, log to a file
i=0; until grep -q "COMPLETE" /tmp/job.log || [ $i -ge 104 ]; do sleep 5; i=$((i+1)); done
tail -50 /tmp/job.log                            # 104 x 5s = 520s, under the 540s slice budget
```

Have the job print a unique terminal marker (`########## COMPLETE ##########`) as its last
line, and set the Bash call's `timeout: 600000`. Repeat the loop across calls if the cap is
hit. Keep the job's own output `tail`-ed inside the script (`| tail -45` per run) — a 3-run
pytest log otherwise blows past the tool-result size limit and gets spilled to a file.
