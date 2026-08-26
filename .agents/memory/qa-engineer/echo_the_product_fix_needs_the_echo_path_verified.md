---
name: A "carry the product's value forward" fix is only honest if the echo path really reaches the product
description: Re-review test for a de-authored seed flag — verify the GET the fixture echoes actually returns the field, or the fallback re-authors it
type: feedback
aliases: [get and echo seed, de-authored flag re-review, carry forward the product flag, seed fallback re-authors]
tags: [area/fidelity, type/review-finding]
created: 2026-08-26
updated: 2026-08-26
---

## The pattern

Round 1 blocks a seed fixture for authoring a field the case reads as its own
observable (`PUT {content, enabled: True}` + `expect(toggle).to_be_checked()`).
The natural fix round ships **GET-and-echo**:

```python
def _current_enabled() -> bool:
    resp = api.get(path); resp.raise_for_status()
    current = resp.json().get("enabled")
    return True if current is None else bool(current)   # mirrors serverData?.enabled ?? true
```

It reads honest. It has a hole: the fixture DELETEs before it seeds, so the `GET`
runs against an **absent** resource. If that `GET` 404s, or returns the field as
`null`/absent, the `?? true` fallback is a **product rule copied into Python** —
the test authors the flag again, laundered through a helper, and the tautology is
back with a better story on top.

## The re-review test — two questions, not one

1. **Does the echo path reach the product?** Find the documented live behaviour of
   the read (surface digest § REST endpoints, or the analyst's live evidence) — not
   the code shape. Here `GET` is *always 200* and returns
   `{"id": null, "content": "", "enabled": true, ...}` when unset, so the echoed
   value is the **server's own default** and the Python fallback is dead code on
   that path. That fact is what makes the fix real; without it the fix is cosmetic.
2. **Is the read as fault-tolerant as the write?** `_delete_project_context`
   tolerates 404; `_current_enabled`'s `raise_for_status()` does not. Asymmetric
   tolerance is fine while the contract holds — say so, so a backend change that
   starts 404ing the `GET` fails loudly in setup instead of quietly.

## Why it is worth the extra lookup

Both a real fix and a cosmetic one produce the same diff shape (a `None` default,
a helper named `_current_enabled`, a pinning unit test). Only the endpoint's live
contract separates them, and it lives in a different file from everything you were
reading.

Related: [[a_seed_fixture_that_writes_two_fields_declares_only_one]]
