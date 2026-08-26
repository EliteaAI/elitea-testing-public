---
name: Shared modal base class invites orphan testids
description: Subclassing a page-object base wires every placeholder locator — added testids for methods the spec never calls violate #511
type: feedback
aliases: [orphan testid, loading-indicator testid, GenerateEntityModalPageBase, 511 unreferenced]
tags: [area/locators, type/review-trap]
created: 2026-08-26
updated: 2026-08-26
---

## The trap

`GenerateEntityModalPageBase` declares ten locator placeholders
(`open_button`, `modal`, `close_button`, `prompt_input`, `error_alert`,
`loading_indicator`, `generate_button`, `cancel_button`, `back_button`,
`approve_button`). A new subclass naturally fills in "all of them", and the
matching testids get added to EliteaUI in one commit — but the spec only
*invokes* a subset of the base's methods.

Canon ruling #511 (`.agents/testing.md` § Locator policy) says a testid wired
into a page-object field is NOT referenced unless the test calls it **on the
executed path**, with no carve-out for reusable scaffolding. So every
placeholder filled "for completeness" is an orphan testid that inflates the
presence-based coverage metric.

Field case — ELITEA-2269 (PR #1798): `generate-project-context-loading-indicator`
was added to `GenerateProjectContextModal.jsx` and declared on
`GenerateProjectContextModalPage`, but no spec calls
`wait_for_loading_visible()` / `wait_for_loading_hidden()`. The AFS *and* the
EliteaUI commit message both claimed "every testid added by this case is
referenced on the executed path" — the claim was false, and the same AFS was
otherwise meticulous about #511 (it deliberately withheld testids from
`Back to prompt`, the close X and the error alert).

## Reviewer move

For any new subclass of a shared page-object base, grep each declared testid
across `automation/` and check the hit is a *spec* call, not just the
descriptor:

```bash
grep -rn "<testid>" automation/            # descriptor only ⇒ orphan
grep -rn "<accessor_name>\|<method_name>" automation/tests/
```

Do not trust the AFS's "all referenced" sentence — it is exactly the sentence
that goes stale when the base class supplies methods nobody calls.

Related: [[fidelity_declaration_never_asserted_clause_needs_a_grep]]
