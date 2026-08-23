---
name: Soft-assert timeout budget review lens
description: A sanctioned-RED soft assert whose wait is shorter than the project's own timeout for the same request can fire falsely and double-act once the defect ships
type: feedback
aliases: [sanctioned red soft assert timeout, expect_response soft assert budget, known defect flip-green risk]
tags: [area/review, type/pattern]
created: 2026-08-23
updated: 2026-08-23
---

## The lens

When a spec is sanctioned-RED and phrases the defect as "the CORRECT behaviour SHOULD have
happened" inside a short `page.expect_response(...)`, check the **budget** against what the
same project gives that request elsewhere.

Worked example (ELITEA-1818, PR #1684): step 7a soft-asserts a bucket-creation `POST` within
`SINGLE_CLICK_SAVE_TIMEOUT = 5_000`, while the very same spec's honest path allows
`CREATE_RESPONSE_TIMEOUT = 25_000` for that POST. Today defect #1080 means no request fires at
all, so the short budget is free. The day the defect ships, a POST that merely takes >5 s
produces (a) a FALSE known-defect soft failure and (b) a **second** Save click in the transit
step — a duplicate create, a leaked bucket (#636), and a red for the wrong reason.

## What to ask at review

1. Is the soft-assert wait ≥ the project's own timeout for that request? If not, say why.
2. Does the transit/recovery step that runs after the soft failure re-perform a **mutating**
   action? If yes, it needs a guard (form still open / URL still the create route) so it cannot
   double-submit.
3. Does the spec still behave correctly on the flip-green day? A sanctioned-RED spec is written
   to be revisited exactly once — when it goes green — and that is when this bites.

Related: [[[flaky]]] · `.agents/testing.md` § Merge gate (sanctioned-RED exception)
