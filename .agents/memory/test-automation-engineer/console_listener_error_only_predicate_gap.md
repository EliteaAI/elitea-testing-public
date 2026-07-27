---
name: Console listener error-only predicate gap
description: When an AFS/case's Expected Results say "no console errors or warnings", check the console-listener predicate literally matches both msg.type values — "error"-only filters are an easy first-pass miss
type: feedback
---

Pattern observed across ELITEA-1929 (R1, a NEW MUI-Tabs warning surfaced only
once a console listener was actually added) and ELITEA-1881 (reviewer caught
a shipped `msg.type == "error"` filter when the AFS's own Expected Results
said "no console errors or warnings").

**The mistake:** writing `page.on("console", lambda msg: issues.append(msg)
if msg.type == "error" else None)` when the case/AFS text says "errors or
warnings" (or "0 errors/warnings"). Playwright's `ConsoleMessage.type` values
include `"error"`, `"warning"`, `"log"`, `"info"`, etc. — an error-only
predicate silently drops every warning, so the assertion technically runs
but never catches what the spec asked for.

**Fix:** when writing any console-capture assertion, re-read the exact
Expected-Results wording first. If it says "errors" only, `msg.type ==
"error"` is correct and warnings are legitimately out of scope — don't
over-broaden speculatively. If it says "errors and/or warnings" (or "0
console issues" generically), the predicate must be `msg.type in ("error",
"warning")`. Naming the accumulator list `console_issues` (not
`console_errors`) when it holds both types keeps the variable name honest
and makes this exact review finding harder to reintroduce on the next case.

Also worth remembering: adding ANY real console listener for the first time
on a page that's been live a while can surface a genuinely new,
previously-unobserved defect (ELITEA-1929's #549) — that's a feature of the
check working, not a sign something is wrong with the listener.
