---
name: An AFS Coverage-Map row can claim an assertion no handle supports
description: Tick every "Asserted where" cell against the code — an AFS verify with no handle in the suite gets dropped silently, not declared
type: feedback
aliases: [coverage map row drift, asserted where, missing error toast assertion, no error surface]
tags: [area/review, type/triangulation]
created: 2026-08-29
updated: 2026-08-29
---

## The trap

An analyst writes a plausible-sounding verify into the AFS — *"no error
toast/alert appeared"*, *"the section is still `aria-expanded="true"`* — and
puts it in the Coverage-Map "Asserted where" cell. The implementer then finds
that **no handle for that observable exists anywhere in the suite** (no toast
testid, no header testid), and the cheapest path is to drop it quietly: the
test is still green, the step still has *an* assertion, and the AFS still
reads as if the verify shipped.

Found on ELITEA-2383 (settings-w08, PR #1964): the AFS's case-step-5 row
claimed "Save-button count 0 **+ no error surface**". The spec asserted only
the Save-button absence — and `grep -rn "error_toast\|snackbar" pages/ tests/ui/settings/`
returns nothing, so the verify was never implementable as written. Same class,
milder, on ELITEA-2381: the Axis-1 row still said `aria-expanded="true"` and
Axis 2 still said `aria-selected`, both superseded by amendments in the AFS
body (`data-selected`, content-visibility) that never reached the tables.

## What catches it

Read each Coverage-Map row's **"Asserted where" cell as a claim about the diff**
and find that exact assertion in the spec. Existence of *an* assertion at that
step is not the check — the row names a specific observable.

When it is missing, the resolution is almost never "add the assertion": it is an
**AFS docs commit in the same PR** dropping or restating the row, because the
observable usually has no handle for a good reason (the surface never renders).
Silently dropping it is what turns the Coverage Map from a contract into
decoration.

Related: [[teardown_that_reads_a_page_it_may_not_be_on]]
