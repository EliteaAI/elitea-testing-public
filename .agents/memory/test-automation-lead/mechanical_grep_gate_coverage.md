---
name: Mechanical grep gate coverage
description: A mechanical self-check grep alternation must cover every clause of the policy it's enforcing, not just the clause the immediate task was framed around — an incomplete alternation lets a real violation slip through self-verification
type: feedback
---

## What happened

Issue #19, PR #56 (2026-07-14 testid-only rework). The implementer's own mechanical
self-check grep was:

```bash
grep -nE '^\+.*(get_by_role|get_by_label|get_by_text|get_by_placeholder|get_by_title|get_by_alt_text|page\.locator|\.locator\()'
```

This alternation targets "raw/chained non-testid handles" — the violation class the
task was originally framed around (raw CSS chains, role/text locators). It came back
clean. But the PR also introduced 10 NEW `page.get_by_test_id(...)` calls constructed
**inline in the test file** instead of as page-object `LocatorDescriptor` class fields
— a *different* clause of the same overall locator policy
(`.agents/testing.md` § Locator policy: "locators live ONLY as page-object class
fields... never in spec files"). `get_by_test_id` wasn't in the alternation, so this
violation sailed through the implementer's own self-check and only got caught by a
fresh reviewer's independent review.

## Why it matters

A rework whose entire purpose is enforcing a locator-hygiene rule is exactly the
context where the self-check needs to be most complete — a partial gate gives false
confidence ("grep came back clean, must be compliant") while leaving a real gap. The
canonical reviewer-slot check in `.agents/role-overrides.md` § Reviewer slot IS the
complete alternation for the "no raw handle" half of the rule, but doesn't by itself
cover the "not inline in spec files" half — that's a structural check (where is the
locator constructed), not a lexical one (what function is called).

## Rule going forward

When dispatching a rework/fix task that exists specifically to enforce a locator
policy, the dispatch prompt's self-check instructions must cover **every clause**
of the policy being enforced, not just the specific violation pattern the task
started from:

1. **Lexical check** (which functions are banned as bare handles): the standard
   `get_by_role|get_by_label|get_by_text|get_by_placeholder|get_by_title|get_by_alt_text|page\.locator|\.locator\(`
   alternation — catches raw/chained non-testid locators.
2. **Structural check** (where locators may live): `grep -n 'get_by_test_id' <spec-file>`
   should be empty in spec/test files — even a compliant `get_by_test_id` call is a
   violation if it's constructed inline rather than as a class-level `LocatorDescriptor`
   field. This check is orthogonal to #1 and easy to forget precisely because the
   locator itself "looks compliant" (it uses the sanctioned testid mechanism).

Both checks belong in the dispatch prompt's verification section, and both belong in
the reviewer's re-verify checklist — don't rely on the implementer's self-check alone
to be complete; the reviewer's mechanical gate should independently include both
clauses too.
