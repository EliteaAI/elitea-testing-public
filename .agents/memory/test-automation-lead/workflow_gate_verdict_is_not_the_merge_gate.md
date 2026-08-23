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
