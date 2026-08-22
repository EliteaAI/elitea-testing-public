---
name: A soft-asserted spec is RED — report the verdict as RED, never "green except one soft failure"
description: pytest-playwright 0.8.0 re-raises collected expect.soft errors, so the pytest outcome is FAILED; the Run Report verdict and the AFS must both say sanctioned-RED
type: reference
aliases: [expect.soft, soft assertion, sanctioned-RED, known defect verdict, RED by design]
tags: [area/framework, type/gotcha]
created: 2026-08-22
updated: 2026-08-22
---

## The fact

`expect.soft(...)` is not a warning in this repo. pytest-playwright **0.8.0** wraps each
test in `playwright._impl._assertions._soft_scope()`, collects every soft-assertion error
and re-raises it at the end of `pytest_runtest_call` — `raise errors[0]` for a single
error, `ExceptionGroup("Soft assertion failures", errors)` for several
(`.venv/lib/python3.13/site-packages/pytest_playwright/pytest_playwright.py:45,101-119`).
**The pytest outcome is FAILED.**

Verified empirically 2026-08-22 on `test_support_assistant_attachment_send.py`
(ELITEA-2421, one soft assert for #1653): `1 failed, 1 warning in 57.73s`, traceback
rooted at `pytest_playwright.py:119: raise errors[0]`.

## What it means for my slot

- **Run Report verdict:** `RED N/M` for any spec carrying a soft-asserted known defect.
  Never "GREEN with a soft failure" — that reads as a clean pass to the lead's gate.
- **The spec IS sanctioned-RED** (`.agents/testing.md` § Merge gate): it fails 3/3 on the
  identical signature, merges RED, and **owes a closure-record entry**. Its case is
  `blocked-on-#N`, not `automated`.
- **Doc-sync it both ways.** The AFS § Known Defects and the test docstring must agree
  with the shipped outcome. ELITEA-2421's AFS said the opposite ("not sanctioned-RED — it
  is green today except for one soft failure") while the docstring correctly said RED BY
  DESIGN; the reviewer blocked on exactly that contradiction (PR #1654, fix round 1).
- **"Re-run it green" is not achievable** for such a spec. The honest equivalent is: re-run
  and confirm the ONLY failure is the declared soft assertion, with the count pasted.

Canon note added to `.agents/testing.md` § Merge gate (sanctioned-RED bullet) so every
role reads it.

Related: [[support_assistant_attachment_oracle]] · [[project_briefing]]
