---
name: Gate a suspected flake with --reruns 0
description: pytest.ini carries --reruns=2 in addopts, so a green gate line can be rerun-rescued — disable reruns to see the truth
type: feedback
aliases: [flaky gate, rerun rescued, reruns 0, merge gate flake]
tags: [area/merge-gate, type/feedback]
created: 2026-08-24
updated: 2026-08-24
---

## The trap

`automation/pytest.ini` sets `--reruns=2 --reruns-delay=5` in `addopts`, project-wide. So a merge-gate
invocation that prints `3 passed` may actually have failed a test on its first attempt and been rescued
by pytest-rerunfailures. The tell is the summary line: `3 passed, 1 rerun` — and `reports/reruns.json`
names the test (its `messages` array is often empty, so it does not tell you WHY).

## What to do

When a spec is *suspected* flaky — it failed at least once in a gate — do not accept rerun-rescued
greens as the gate. Re-run with reruns disabled:

```bash
cd automation && HEADLESS=true ../.venv/bin/pytest <spec> -v -p no:cacheprovider --reruns 0
```

Three consecutive clean invocations under `--reruns 0` is a real gate; three under the default is not,
for a spec you already have reason to doubt.

Worked case: mcp wave-05 (#1396, PR #1751). Gate runs 1 and 5 failed 2-of-5 on a post-save ReactFlow
canvas race. After the fix, runs 6/7 were clean but 8/9 were rerun-rescued — which is what prompted
runs 10/11/12 under `--reruns 0`, all clean. Without that check the residual flake would have been
invisible in the closure record.

Related: [[.agents/testing.md § Merge gate]]
