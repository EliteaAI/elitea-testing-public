---
name: The workflow's gate verdict is not your merge gate
description: A batch workflow can return verdict green while its own evidence fails the project's sanctioned-RED rule — read failures[], don't read verdict
type: feedback
aliases: [sanctioned red, gate verdict, merge gate, red by design, batch gate]
tags: [area/merge-gate, type/lesson]
created: 2026-08-23
updated: 2026-08-23
---

## The trap

`batch-build` returns `gate.verdict: "green"` when *the failures it saw were the
specs declared red-by-design*. It does **not** check the project's extra
condition: `.agents/testing.md` § Merge gate requires the red be **identical
3/3**, and says a **raw/uncaught exception** at the gate still blocks.

Field case 2026-08-23, artifacts-w04 (#1392): verdict `green`, but `failures[]`
said ELITEA-1810's spec failed runs 1–2 with the declared #1677 soft-assert pair
and **run 3 with a `TimeoutError`** in `navigate_to_artifacts()` →
`wait_for_network()` → `networkidle`. Different cause, aborted before the soft
assertions ran ⇒ sanctioned-RED was **not** established. Accepting the verdict
would have merged an unproven red.

## What to do

1. On any red batch, read `gate.failures[].signature` — never just `verdict`.
2. Run your own 3× gate anyway (you owe it regardless) and **compare signatures
   across runs**, not just pass/fail counts.
3. Identical 3/3 + open ticket linked in-test ⇒ sanctioned-RED, merge red.
   A one-off different failure ⇒ environmental noise (confirm by re-running) or
   a flake that blocks.

In that case my 3 runs + 1 isolated run all reproduced the #1677 pair byte-identically
with zero timeouts, so the run-3 timeout was environmental (the `networkidle` noise
class already in `.agents/testing.md` § Known issues) and the merge was correct —
but only *because it was checked*.

## Consequence for the TMS

An `expect.soft()` failure IS a pytest failure. A sanctioned-RED case is
`blocked-on-#N`, **never** back-written as `automated` — counting it is a hidden green.

Related: [[artifacts_area_backlog_1392]]

## New variant (settings-w04, 2026-08-27): empty `expected_red[]` cascades `blocked` onto the WHOLE batch

This one is not a stalled or crashed gate — the gate **ran correctly, 3×** — and it
still produced a false verdict, so none of the recoveries above apply.

The batch had **two pre-declared sanctioned-REDs** (ELITEA-2289 → #1884,
ELITEA-2291 → #1885): filed OPEN bugs, `# Known defect: #N` in-test, `soft_failures`
aggregation + trailing `pytest.fail()`, and the reviewer's own findings said
"SANCTIONED-RED, two independent signatures — the closure record must reflect both."

But the report came back with **`expected_red: []`**. With nothing declared, the gate
scored both as plain reds → `verdict: red` → and the script marked **all 11 cases**
`blocked`, including 8 that never failed. Its own per-case note said so verbatim:

> "gate red for the batch — this spec did not itself fail"

**The tell is cheap: if `gate.verdict == "red"` but `expected_red` is empty while the
reviewer's findings mention sanctioned-RED, the two disagree and the report is wrong.**

Recovery that worked, in order:

1. **Verify ground truth before touching the label** — defects OPEN + filed, specs
   really carry the known-defect markers, unit PRs really merged.
2. **Run your own gate SPLIT BY NODE-ID**, not by file. Here ELITEA-2289 (vscode) and
   ELITEA-2290 (jetbrains) are two params of ONE spec file — one red, one green — so a
   file-scoped gate literally cannot express the split. Green group 3/3 green; RED
   group 3/3 identical.
3. Rewrite `report.json`: real verdict, per-case outcomes (`automated` /
   `merged-sanctioned-red` / `blocked`), and a **populated `expected_red[]`** so the
   next reader isn't misled the same way.

**Determinism subtlety worth keeping:** #1884's failure message embeds the token
suffix, which differs every run because each run mints a fresh token. That is the
observed *value*, not the cause. Judge "identical signature" on the **cause**
(masked instead of full), never on byte-equality of the message — otherwise a
legitimate sanctioned-RED reads as flaky and blocks forever.
