---
name: A gate that "passed" with reruns is not a clean gate
description: Read reruns.json, not just the pass line — pytest-rerunfailures turns a setup flake into a green
type: feedback
aliases: [reruns.json, rerun tainted gate, gate passed but flaky, 3x gate reruns, hidden gate failure]
tags: [area/merge-gate, type/gotcha]
created: 2026-08-27
updated: 2026-08-27
---

## The trap

`pytest.ini` sets `--reruns=2`, so an invocation that failed twice and passed
on the third attempt still prints `1 passed` and still writes PASS to junit.
A 3×-green gate read only from the pass lines can therefore be **three
invocations of which one was a double failure** — and the evidence exists
**only** in `reports/allure-results/*-result.json` (allure status `broken`)
and in `reports/reruns.json`.

## The rule I now apply

- Every gate run prints **`reruns.json` alongside the pass line**. `{}` is the
  acceptance criterion, not the word "passed".
- A non-empty `reruns.json` ⇒ **re-gate**. Do not accept 2-of-3, and do not
  merge on the tainted run. A rerun failure is almost always at *setup*,
  upstream of every assertion the spec makes, so it can never be a member of a
  sanctioned-RED set (`.agents/testing.md` § Merge gate).
- **Run the matched pristine control BEFORE assigning blame** (the `#1082`
  discipline). When the diff touches exactly one file, swapping that file to
  its `origin/main` version runs the pristine spec against byte-identical
  shared code — a genuine control for one extra invocation. It is what
  converts "my diff broke it" into evidence either way.

Worked on #1811 / ELITEA-1790 (2026-08-27): first gate 3/3 "passed" but run 2
burned both reruns on a `networkidle` TimeoutError; control 2/2 clean;
re-gate 3/3 with `reruns.json == {}`; mechanism filed as #1847.

Related: [[project_briefing]]
