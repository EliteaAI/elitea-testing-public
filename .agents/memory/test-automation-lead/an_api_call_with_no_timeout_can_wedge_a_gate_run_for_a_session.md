---
name: An API call with no timeout can wedge a gate run for a whole session
description: requests.Session calls in automation/api/client.py carry no timeout=, so a half-open DEV connection stalls the run until the peer resets it (~16 min observed); kill + re-gate from scratch, and know the tell
type: feedback
aliases: [ConnectionResetError gate stall, requests no timeout, wedged API tie-breaker, gate run stuck 16 min]
tags: [area/merge-gate, area/dev-env, area/framework, type/hazard]
created: 2026-09-16
updated: 2026-09-16
---

## What it looked like

#2312 (ELITEA-1899, 25th [FIX] re-detection), first 3× DEV gate attempt: run 1 = the expected
signature in 36.89 s; run 2 completed every UI step (`Navigated to agents dashboard`) and then
went silent. Log mtime stopped advancing; after ~16 min one line appeared —
`urllib3 … Retrying (Retry(total=2 …)) after connection broken by 'ConnectionResetError(54 …)':
/api/v2/elitea_core/application/prompt_lib/399/10891` — and the next retry would have hung the
same way. `curl` to DEV answered in 0.5 s at that moment: the *env* was up, one TCP connection
was dead.

## Why: `APIClient` has no `timeout=`

`grep -n timeout automation/api/client.py` finds only MCP-sync payload fields. Every
`self._session.get/post(...)` inherits `requests`' default of **no** timeout. Playwright waits
are all bounded; the API client is the one unbounded wait in a run. `--reruns` cannot help —
a rerun fires only after the attempt ends. Filed as **#2313** (framework, small: default
`(connect, read)` timeout on the session, per-call override for the long ones).

## The tells, and the response

- Log file mtime frozen for minutes while the pytest process is alive and the last logged step is
  an API-backed one (tie-breaker GET, cleanup DELETE, create POST).
- `curl` to the target answers normally → not an outage, a dead connection.
- Response: `pkill` the pytest + the gate script, archive the attempt's logs
  (`/tmp/gate_<n>.attempt1.*`), **re-gate from scratch** — it is a raw stall at a precondition,
  never a member of the closed set, so 2-of-3 is not acceptable. The session-scoped cleanup fixture
  swept the orphaned agent on the next run (`0 autotest agents remaining`), so no manual cleanup.
- Wait loop shape: the bounded `for … grep -q GATE_DONE … sleep 5` loop hit its 600 s cap once
  while the run was wedged — that cap firing is itself a tell for a ~45 s spec.

## Also: zsh `rm -f glob` aborts the chain

`rm -f /tmp/gate_2312.run*.log && …` with no matching files → zsh `no matches found` → exit 1 →
the `&&`-chained launch never ran. Use `rm -f … 2>/dev/null; ` or `setopt nullglob`. Cost one
launch.

Related: [[the_devenv_plugin_is_the_factory_safe_dev_gate]] · [[a_null_delta_card_still_owes_a_full_gate]]
