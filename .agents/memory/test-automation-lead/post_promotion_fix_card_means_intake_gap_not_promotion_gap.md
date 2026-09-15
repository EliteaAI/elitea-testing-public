---
name: A FIX card whose body already quotes "Known defect #N" after promotion is the intake gap alone — the promotion gap is gone
description: Once the repair is on main, the ancestry check flips to YES and the only generator left is #2064; the closure is still the same 10-min null-delta loop, but say out loud that #2157 no longer applies
type: feedback
aliases: [post-promotion fix card, sanctioned red refiled after promotion, 2064 sole generator]
tags: [area/fix-intake, area/merge-gate, type/procedure]
created: 2026-09-15
updated: 2026-09-15
---

## What changed (#2289, ELITEA-1899, 18th filing)

Seventeen siblings were promotion-gap re-detections (`main` lacked the repair, CI showed `'' != ''`).
#2286 promoted PR #2056 to `main`; the very next nightly (run #152, `d89cb60`) refiled the node id — with
the card body **quoting the repaired signature** (`known isolated product defect #2055`) and the
intake's own summary saying "no new investigation needed".

## What to do differently

- `git merge-base --is-ancestor <repair-sha> <ci-sha>` → **YES** now. Don't reach for the message-string
  grep as "proof of gap" — it's on both branches. The check still runs first; its answer just flips.
- Write the disposition against **#2064** (sanctioned-RED awareness), not #2157 (dedup / already-fixed-on-base).
  #2157 is closed for this node id; naming the wrong generator sends the human to the wrong fix.
- The delivery is unchanged: job-level failure count → own 3× DEV gate via `-p devenv` → allure per-step →
  #2055 at source → duplicate label → Ready. ~10 min, gate ~125 s for this spec.
- Promotability proof is free here: 11/11 non-sanctioned steps passing against the `main` build on DEV
  proves every executed-path handle is on `main` — stronger than the grep, and no fetch needed.

Related: [[a_null_delta_card_still_owes_a_full_gate]] · [[the_devenv_plugin_is_the_factory_safe_dev_gate]] ·
[[a_cross_run_fix_card_is_not_a_duplicate_filing]]
