---
name: MUI Collapse interrupted enter-transition strands the subtree
description: A click during a ~300ms MUI Collapse enter transition kills onExited, so unmountOnExit never fires and the section stays open forever
type: feedback
aliases: [collapse does not collapse, expand collapse flake, unmountOnExit stuck, tree click lost]
tags: [area/ui, type/gotcha]
created: 2026-08-21
updated: 2026-08-21
---

## What happens

A toggle click that lands **inside** MUI `Collapse`'s enter transition (~300 ms
default) interrupts it. `onExited` then never fires, so `unmountOnExit` never
unmounts the children — the section stays expanded **permanently**, not for a
moment. A 10 s auto-retrying `to_have_count(0)` never goes green.

Measured on the Artifacts left-panel file tree (ELITEA-1836, 2026-08-21):
**3/3** failures with the second click inside the window, **18/18** successes
once the transition had finished. A ~200 ms gap is borderline (1/2), 500 ms+
reliable. **Zero network requests** in the window — do not chase a refetch
theory (I did, and `page.wait_for_load_state("networkidle")` did not fix it,
because there is no request to wait for).

## What to do instead of a sleep

Wait for the expanded subtree's **geometry** to stop moving, polled — the shape
already merged in `artifacts_page.py` as `wait_until_bucket_row_within_panel`:

```python
item = self.page.locator(self.SOME_TESTID_TEMPLATE.format(key))   # last child settles last
# poll bounding_box() until two consecutive reads match, bounded by a deadline
```

Shipped as `ArtifactsPage.wait_for_tree_item_stable(item_key)`.

## Debugging lesson worth keeping

My first two fixes were guesses (a refetch race, then `networkidle`), and both
cost a full spec run. The probe that actually settled it took one run: log the
child count every 100 ms **and** every request with a timestamp, then bisect the
gap between the two clicks. Instrument before patching.

Also: a probe that "reproduces a product bug" can be a bug in the probe — my
"baseline collapse fails" reading came from a helper that polled for a collapse
**without ever clicking**. Re-read the probe before believing a surprising
result about the product.

Related: [[no_playwright_mcp_use_sync_playwright_script]]
