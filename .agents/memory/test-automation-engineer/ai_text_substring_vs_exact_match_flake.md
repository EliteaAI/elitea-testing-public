---
name: AI-generated text — substring-vs-exact-match mismatch masquerades as a DOM flake
description: A set/equality assertion mixing substring lookup with exact-match subtraction on AI-generated text looks flaky (passes/fails by luck of wording) but is a deterministic test-code bug — check match semantics before blaming virtualization/timing.
type: feedback
---

## Rule

When a test locates an AI-generated row/cell by **substring** (`:has-text()`,
`in`) but later math against the same data uses **exact** match (`set() -
{CONSTANT}`, `==`), the two can silently disagree whenever the AI's wording
varies (`"Microsoft"` vs `"Microsoft Corporation"`). The failure LOOKS random
across runs — it passes when the AI happens to emit the exact constant, fails
otherwise — but it's fully deterministic given that run's AI output. Don't
reach for "flaky DOM read" / "virtualization" / "race condition" diagnoses
until you've checked whether every comparison against the same AI-authored
string uses the SAME match semantics (all substring or all exact, consistently).

**Diagnostic tell:** the failure message shows the "missing" item as a longer
variant of the search constant, and the count/length assertions around it
(`len(rows) == N`) all passed — i.e., the DOM was read correctly, only the
math was wrong.

## Fix

Capture the actual matched string once (`next(v for v in items if
CONSTANT in v)`) and reuse THAT for every subsequent comparison, instead of
re-matching against the bare constant with different semantics each time.

## Seen 1×

- ELITEA-2087, `test_edit_table_canvas_modify_cell_and_save.py` Step 10
  (hardening-gate flake, 2026-08-04, fixed on `tests/batch-wave-02-05-merged`
  commit `26ba6537`). Dispatch hypothesized the DataGrid row-virtualization
  hazard documented for ELITEA-2086's `_scroll_grid_full_scan` — wrong
  diagnosis (that read path is `chat.get_rendered_table_data()`, a plain
  `<table>`/`table tbody tr` read, not the DataGrid; the virtualization
  technique doesn't even apply here). Real cause:
  `set(pre_edit_companies) - {ORIGINAL_VALUE}` used exact-match against the
  literal `"Microsoft"` constant while cell lookup elsewhere used
  `:has-text()` substring match; AI generated `"Microsoft Corporation"` that
  run, stranding it in `expected_unchanged`. Confirmed via the archived
  JUnit failure's full diff (`reports/archive/junit_20260804_065552.xml`)
  showing `len(...) == 10` passed cleanly on both reads — only the set
  arithmetic was wrong.
