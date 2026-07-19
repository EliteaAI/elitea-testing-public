---
name: Artifacts context fixture viewport defaults are both too narrow
description: Neither this project's headed nor headless context fixture default guarantees the Artifacts file table's "Last update" column is visible; set the viewport explicitly before asserting on it
type: feedback
---

## Neither context default meets the ≥1600px requirement

ELITEA-1808 first found (and ELITEA-1826 reconfirmed) that the Artifacts
file table's "Last update" timestamp column is present in the DOM but
visually clipped/hidden below roughly 1600px viewport width — a responsive
layout artifact, not conditional rendering. `automation/conftest.py`'s
`context` fixture sets:

- **Headed** (`HEADLESS=false`, the project default): `no_viewport=True` —
  the page fits the actual OS browser window. Not guaranteed to be ≥1600px
  wide (depends on the machine/monitor running the test).
- **Headless** (`HEADLESS=true`, used for quiet/CI-style runs): a **fixed
  1366×768** viewport — confirmed too narrow, every time.

So a test that asserts the "Last update" segment cannot rely on either
default and must not assume the headed default is "probably wide enough."

## Fix: set the viewport explicitly, as a raw `page` call

```python
page.set_viewport_size({"width": 1600, "height": 900})
```

Call this early in the test (before navigating, or at least before the
first row-text/timestamp assertion) — it works regardless of whether the
context was created with a fixed viewport or `no_viewport=True`; Playwright
simply pins the page to the given size from that point on.

This is a raw `page.*` call, not a locator or DOM interaction, so it is
**not** a testid-policy violation — same class as this project's existing
convention of registering `page.on("console", ...)` directly in test files
(browser/context-level concerns bypass the page-object locator layer by
design, they're not "finding an element"). No page-object wrapper method is
needed or expected for this.

## Before assuming a fixture/CLARIFICATION is safe, read the actual default

Don't infer "the default viewport is probably fine" from the fact that a
sibling test also asserts the timestamp and passed — check what viewport
that sibling test actually ran under (headed vs headless can silently flip
which default applies from one CI/local run to the next). Read
`conftest.py`'s `context` fixture directly rather than assuming either
branch is wide enough; this is the same "verify, don't infer" discipline as
the sibling entry on analyst absence claims needing normal-viewport
reverification.

(from ELITEA-1826)
