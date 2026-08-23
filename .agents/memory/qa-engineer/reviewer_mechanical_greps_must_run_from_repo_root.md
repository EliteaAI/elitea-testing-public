---
name: Reviewer mechanical greps must run from the repo root
description: `cd automation && git diff <base>...<head> -- automation/` silently matches nothing — the pathspec is repo-relative, so the grep prints a false "0 hits"
type: feedback
aliases: [0 hits false negative, mechanical grep pathspec, locator grep empty]
tags: [area/review, type/gotcha]
created: 2026-08-22
updated: 2026-08-22
---

## The trap

The locator / fidelity mechanical greps in `.agents/role-overrides.md` § Reviewer
slot use the pathspec `-- automation/`. That pathspec is **repo-root relative**.
Run the same command after `cd automation`, and git matches zero files, the pipe
carries nothing, and `|| echo "0 hits"` prints a clean, entirely false
**0 hits** — the exact evidence the contract asks you to paste.

Caught during the ELITEA-1964 review (2026-08-22): three greps "passed" from
`automation/` before the mistake surfaced; re-run from the repo root they still
passed, but the first result proved nothing.

## Guard

Always run the greps from the repo root, and sanity-check with
`git diff --stat <base>...<head> -- automation/` in the same call — a non-empty
diffstat is what makes a `0 hits` meaningful.
