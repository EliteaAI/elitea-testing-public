---
name: A pipe inside gate-case.mjs --cmd masks pytest's exit code
description: Piping pytest through tail/head inside --cmd makes the gate report GREEN on a red run — never pipe, redirect instead
type: feedback
aliases: [gate-case pipe, gate false green, tail masks exit code, gate --cmd redirect]
tags: [area/gating, type/gotcha]
created: 2026-08-27
updated: 2026-08-27
---

## What happened

Gating batch `settings-w04` I tried to keep transcript output lean by writing
`--cmd 'cd automation && ... pytest {spec} -q | tail -30'`. `gate-case.mjs`
runs the command via `execSync`, so the shell reports the **last** command's
status — `tail` exits 0 — and the script printed `verdict: green` for a run
whose pytest tail plainly showed `2 failed, 10 passed`.

The two neighbouring runs (same set, no pipe) both returned `verdict: red`.
Only the pytest summary line revealed the "green" was bogus.

## The rule

Inside `--cmd`, **never pipe pytest into anything**. To keep output small,
**redirect to a file** and grep it afterwards:

```
--cmd 'cd automation && HEADLESS=true ../.venv/bin/pytest {spec} -q -p no:cacheprovider > /tmp/gate_runN.log 2>&1'
```

`set -o pipefail` would also work in bash, but the shell `execSync` picks is
not guaranteed — redirect is the shape that cannot go wrong.

Corollary for any gate report: **cross-check the script's verdict against the
runner's own summary line** before trusting it. A verdict that disagrees with
`N failed, M passed` is a harness artifact, not a test result.
