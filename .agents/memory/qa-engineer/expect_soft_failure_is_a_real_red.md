---
name: expect.soft failure is a REAL red, never a "green with a soft failure"
description: Verified in-venv — pytest-playwright collects soft-assert errors and raises, so a soft-asserted known defect makes the spec FAIL
type: reference
aliases: [expect.soft, soft assertion, sanctioned-RED, soft-asserted known defect]
tags: [area/framework, type/gotcha]
created: 2026-08-22
updated: 2026-08-22
---

## The fact

`expect.soft(...)` in this repo is NOT a "warning". Verified 2026-08-22 by reading
`.venv/lib/python3.13/site-packages/pytest_playwright/pytest_playwright.py:45,101-116`
(pytest-playwright **0.8.0**, playwright 1.61.0): the plugin wraps each test in
`playwright._impl._assertions._soft_scope()`, collects every soft-assertion error, and
raises an `ExceptionGroup("Test and soft assertion failures", [...])` at the end of the
test. **The pytest outcome is FAILED.**

## Why it matters at review time

A spec carrying one `expect.soft()` + `# Known defect: #N` is **sanctioned-RED**
(`.agents/testing.md` § Merge gate): it fails deterministically 3/3 at the lead's gate,
and the lead MUST record the exception in the closure record. Any AFS / run report
sentence of the shape *"this spec is not sanctioned-RED — it is green today except for
one soft failure"* is factually wrong and mis-steers the gate. Caught exactly that
wording while reviewing ELITEA-2421 (PR #1654, `test_support_assistant_attachment_send.py`).

Corollary for the masking hunt: a soft-asserted defect is **not** masking — it is the
project's sanctioned way to keep the red visible. What IS masking is a skip/xfail, or a
soft assert whose defect issue is closed/absent.

Related: [[project_briefing]]
