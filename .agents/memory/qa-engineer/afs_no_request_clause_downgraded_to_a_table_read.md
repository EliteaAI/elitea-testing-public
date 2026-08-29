---
name: AFS "no request fired yet" clause downgraded to a table read
description: An AFS verify clause naming a REQUEST is satisfiable-looking by a UI read that cannot prove it — grep the spec for the listener.
type: feedback
aliases: [no delete yet, request listener assertion, non-destructive control assertion]
tags: [area/review, type/triangulation-trap]
created: 2026-08-29
updated: 2026-08-29
---

## The trap

An AFS step that says *"Verify: no DELETE has fired yet (the icon only opens a
dialog)"* is a claim about the **network**, not about the table. The cheap
implementation is `expect(row).to_have_count(1)` — the row is still there — and
it reads like coverage in review because an `expect()` is present at the right
step, in the right `allure.step`, with a comment repeating the AFS sentence.

It proves nothing. A row survives a delete that is still in flight (the RTK
refetch has not landed), which is exactly the distinction the clause exists to
make. The honest shape is the passive observer:

```python
delete_requests: list[str] = []
page.on("request", lambda r: delete_requests.append(r.url) if r.method == "DELETE" else None)
...
assert not delete_requests, f"...but the page sent: {delete_requests}"
```

Registered **before** the first click (see
[[absence_of_request_assertion_registration_window]]).

## The review move

When an AFS Verify clause or a Coverage-Map "Asserted where" cell names a
**request** (`no DELETE`, `no POST`, `one PUT`), grep the spec for
`page.on(` / `expect_response` / `expect_request`. If the only thing at that
step is a locator assertion, it is drift — even when a sibling spec in the SAME
PR does it correctly (ELITEA-2298 vs ELITEA-2299/2300, PR #1976). Same-PR
inconsistency is the loudest tell.

Related: [[absence_of_request_assertion_registration_window]] ·
[[afs_row_can_claim_an_assertion_no_handle_supports]] ·
[[network_wait_after_a_non_networking_action_passes_vacuously]]
