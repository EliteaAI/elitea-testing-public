---
name: The -p devenv plugin is the factory-safe DEV gate — no shared env file ever touched
description: In unattended mode never swap the shared .env.test; the out-of-repo plugin retargets the resolver per-process, needs no restore trap, and a 3× DEV gate on a single spec costs ~95 s
type: feedback
aliases: [devenv plugin, factory dev gate, dev gate without env.test, gate_2246.sh, promotion gap re-cert cost]
tags: [area/merge-gate, area/dev-env, type/procedure]
created: 2026-09-11
updated: 2026-09-16
---

## Why the plugin, not the swap, in factory mode

The `.env.test` swap recipe (detached script + `trap` restore) is correct but carries a hazard the
factory cannot afford: the master env file is shared by all four sibling clones, and a killed
unattended session strands every clone on DEV. The `-p devenv` plugin has **no restore step at all**
— it mutates `config.settings` inside the pytest process only. `.env.test` reads `localhost:5173`
before, during and after.

Files (out of repo, recreate if `/tmp` was wiped — **it was, 2026-09-16 / #2311: only `__pycache__`
survived; the gate scripts `/tmp/gate_*.sh` did**). Verbatim body, paste it:
```python
# /tmp/devenv_harness/devenv.py — load with `-p devenv`, PYTHONPATH="/tmp/devenv_harness:$AUT" (prepend)
import os, sys
AUTOMATION_DIR = os.environ["AUTOMATION_DIR"]
if AUTOMATION_DIR not in sys.path:
    sys.path.insert(0, AUTOMATION_DIR)
import config  # noqa: E402
config.settings.elitea_url = os.environ.get("DEV_ELITEA_URL", "https://dev.elitea.ai")
config.settings.app_prefix = os.environ.get("DEV_APP_PREFIX", "/app")
```
`elitea_api_base` already points at the DEV backend in `.env.test`, so only those two fields move.
Verify before launching: `AUTOMATION_DIR=$PWD … python -c "import devenv, config; print(config.settings.app_base_url)"`
→ must print `https://dev.elitea.ai/app`.
- `/tmp/devenv_harness/devenv.py` — as above
- `/tmp/gate_<card>.sh` — **the newest surviving clone is the template** (`/tmp/gate_2246.sh` is GONE — 2026-09-16 / #2314 cloned from a missing path, got an empty script and launched a no-op pid; use `SRC=$(ls -t /tmp/gate_*.sh | head -1)` and `wc -l` the clone before `nohup`). Resolver guard (`exit 2` unless `https://dev.elitea.ai/app`), 3 runs,
  per-run `reruns.json` + `1 passed in Ns` lines into `$LOG.summary`, terminated by `GATE_DONE`.

`PYTHONPATH="/tmp/devenv_harness:$AUT"` — PREPEND, per
[[dev_gate_plugin_needs_pythonpath_to_prepend]].

## Wait shape that worked (bounded, no Monitor, no bare sleep)

`for i in $(seq 1 100); do grep -q GATE_DONE $LOG.summary && break; python3 -c "import time;
time.sleep(5)"; done` inside ONE Bash call with `timeout: 600000`. Resolved in ~100 s.

## Cost datapoint for the promotion-gap re-cert class

#2318 (ELITEA-2063, cross-run re-detection of #2077, promoted to `main` via the #2316 cherry-pick shape rather than re-certified): session ~50 min, gate ~100 s (34/30/30 s), 0 hazard attempts; `pipeline_detail_page.py` 3-way-merged cleanly onto a `main` that #2322 had touched the same day. ⚠️ zsh `rm -f $LOG.run*.log` with no match aborts the `&&` chain BEFORE `nohup` — `setopt nullglob` first, and confirm the summary file exists after launch.
#2315 (ELITEA-2453, 10th+ filing, ~40 s/run pipeline spec): session ~12 min, gate ~120 s, 0 hazard attempts. #2246 (ELITEA-2367, 14th filing): whole session ~15 min, gate ~95 s. #2247 (ELITEA-1866, 7th filing, a ~100 s/run toolkit-creation spec): session ~15 min, gate ~310 s wall, 0 hazard attempts — clone the script with `sed` on NODE/LOG only. The human had bulk-closed
the previous 8 twins as `wontfix` two minutes earlier — the factory keeps paying a session per
nightly until `automation/base` is promoted (#2157). The cheapest honest close is exactly this:
message-string grep → call-path check → job-level failure count → 3× DEV via plugin → duplicate
label + closure record → Ready. Nothing else adds information.

Related: [[dev_gate_discipline_for_fix_cards]] · [[a_null_delta_card_still_owes_a_full_gate]] ·
[[message_string_grep_is_the_cheapest_promotion_gap_proof]]
