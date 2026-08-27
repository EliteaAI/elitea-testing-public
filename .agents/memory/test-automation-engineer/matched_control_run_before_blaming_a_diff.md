---
name: Run the matched control before blaming (or clearing) your diff for a blast-radius red
description: One extra invocation on the pristine file converts "my change broke it" into evidence — cost ~45s, worth it every time
type: feedback
aliases: [control run, pristine HEAD control, blast radius red, did my diff break it]
tags: [area/gates, type/discipline]
created: 2026-08-27
updated: 2026-08-27
---

## What to do

When a blast-radius spec goes red after you modify a shared page-object method,
**do not reason about whether your change could plausibly cause it.** Restore the
pristine file at the same path and re-run the same spec:

```bash
git show origin/main:automation/pages/<file>.py > automation/pages/<file>.py
# run the spec
git checkout HEAD -- automation/pages/<file>.py   # after committing your own work first
```

Commit your own work **before** doing this, so the restore is a one-liner and
nothing of yours can be lost. Never `git stash --include-untracked` / `git clean`
to get there.

## Why it is worth an extra invocation

On ELITEA-1888/#1872, `test_agent_version_selector_order.py` failed right after a
shared `confirm_new_version()` change — exactly the shape of a regression. The
control run on the pristine page object failed with a **byte-identical assertion
and order list**, proving the red was pre-existing. Without it the honest options
were "spend a session bisecting" or "assert innocence without evidence"; the
control cost 44.78s and produced a fact a reviewer can check.

This is the project's own documented discipline (`.agents/testing.md` § `#1082`
pollution class — first matched control pair) applied to a shared-method change
rather than to a flaky suite. It cuts **both** ways: it also stops you clearing
your diff when the diff really is at fault.

Related: [[version_flow_url_vs_formik_read_race]]
