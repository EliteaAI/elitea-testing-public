---
name: LocatorDescriptor.description is docs-only — safe to edit regardless of caller count
description: PR #647/ELITEA-1826 reviewer pass — confirmed LocatorDescriptor's description= param has no functional consumer, so a description-only edit on a shared field is always additive-safe even with many callers
type: feedback
---

## What I confirmed

PR #647 (ELITEA-1826) touched `automation/pages/artifacts_page.py`'s
`success_toast_message` `LocatorDescriptor` — only its `description=` text
changed (recording both ELITEA-1832's confirmed toast-ABSENCE finding and
ELITEA-1826's confirmed toast-PRESENCE finding). The `testid="toast-message"`
value was byte-identical before/after.

Read `LocatorDescriptor.__init__` (`automation/pages/locator_descriptor.py:31-51`)
directly rather than assuming: `description` is stored as `self.description`
and the docstring says "Human-readable description for docs" — it is never
read anywhere else in the descriptor's `__get__`/resolution logic, and no
test file reads `.description` off a page-object attribute (confirmed via
`grep -rn "\.description" automation/tests/ automation/pages/` — the only
hits are the field's own declarations, never a `.description` access in a
test or method body).

## Why this matters for future reviews

`success_toast_message` had 4 other call sites across 3 test files
(`test_artifacts_create_bucket_upload_file.py`,
`test_artifacts_upload_duplicate_cancel.py`,
`test_artifacts_download_multiple_files_zip.py`) at review time. Normally a
shared-caller-file edit (Hard Rule 3 / additive-only discipline) needs the
"enumerate every affected caller, re-run them" treatment. **A `description=`
-only change is the one exception that needs none of that** — it's pure
documentation, never consumed at runtime by anything. Verify this
generalizes to any `LocatorDescriptor` field edit: if a diff on a shared
locator changes ONLY `description=` (never `testid=`), it's safe by
construction — check the diff hunk shows exactly that (no `testid=` line
touched) and move on, don't spend review budget re-running unrelated
callers for a docstring change.

This does NOT extend to any other param on the same descriptor (`testid=`
changes are exactly the kind of thing that DOES need full caller
re-verification).
