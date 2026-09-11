---
name: The -p devenv plugin is the factory-safe DEV gate — no shared env file ever touched
description: In unattended mode never swap the shared .env.test; the out-of-repo plugin retargets the resolver per-process, needs no restore trap, and a 3× DEV gate on a single spec costs ~95 s
type: feedback
aliases: [devenv plugin, factory dev gate, dev gate without env.test, gate_2246.sh, promotion gap re-cert cost]
tags: [area/merge-gate, area/dev-env, type/procedure]
created: 2026-09-11
updated: 2026-09-11
---

## Why the plugin, not the swap, in factory mode

The `.env.test` swap recipe (detached script + `trap` restore) is correct but carries a hazard the
factory cannot afford: the master env file is shared by all four sibling clones, and a killed
unattended session strands every clone on DEV. The `-p devenv` plugin has **no restore step at all**
— it mutates `config.settings` inside the pytest process only. `.env.test` reads `localhost:5173`
before, during and after.

Files (out of repo, recreate if `/tmp` was wiped):
- `/tmp/devenv_harness/devenv.py` — `sys.path.insert(0, AUTOMATION_DIR); import config;
  settings.elitea_url = DEV_ELITEA_URL; settings.app_prefix = "/app"`
- `/tmp/gate_2246.sh` — resolver guard (`exit 2` unless `https://dev.elitea.ai/app`), 3 runs,
  per-run `reruns.json` + `1 passed in Ns` lines into `$LOG.summary`, terminated by `GATE_DONE`.

`PYTHONPATH="/tmp/devenv_harness:$AUT"` — PREPEND, per
[[dev_gate_plugin_needs_pythonpath_to_prepend]].

## Wait shape that worked (bounded, no Monitor, no bare sleep)

`for i in $(seq 1 100); do grep -q GATE_DONE $LOG.summary && break; python3 -c "import time;
time.sleep(5)"; done` inside ONE Bash call with `timeout: 600000`. Resolved in ~100 s.

## Cost datapoint for the promotion-gap re-cert class

#2246 (ELITEA-2367, 14th filing): whole session ~15 min, gate ~95 s. #2247 (ELITEA-1866, 7th filing, a ~100 s/run toolkit-creation spec): session ~15 min, gate ~310 s wall, 0 hazard attempts — clone the script with `sed` on NODE/LOG only. The human had bulk-closed
the previous 8 twins as `wontfix` two minutes earlier — the factory keeps paying a session per
nightly until `automation/base` is promoted (#2157). The cheapest honest close is exactly this:
message-string grep → call-path check → job-level failure count → 3× DEV via plugin → duplicate
label + closure record → Ready. Nothing else adds information.

Related: [[dev_gate_discipline_for_fix_cards]] · [[a_null_delta_card_still_owes_a_full_gate]] ·
[[message_string_grep_is_the_cheapest_promotion_gap_proof]]
