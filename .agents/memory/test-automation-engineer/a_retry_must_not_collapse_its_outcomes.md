---
name: A bounded retry must not collapse its outcomes into one traceback
description: Bare `raise` in every retry branch destroys the diagnosis the retry was added to protect — give each branch its own message naming which defect it is.
type: feedback
aliases: [retry diagnosability, bare raise, indistinguishable traceback, retry branch messages]
tags: [type/pattern, area/reliability]
created: 2026-09-04
updated: 2026-09-04
---

## The failure mode

A bounded retry usually ends up with several `except` branches — "this proves the
action happened, re-raise", "unexpected state, re-raise", "attempts exhausted,
re-raise". Writing each as a bare `raise` is the obvious thing to do and it is
wrong: **N semantically different outcomes then produce one byte-identical
traceback**, with no attempt number and none of the evidence the branch just
examined.

Caught at review on ELITEA-1886 / #1812 round 2, and the reviewer's framing is the
one to remember:

> *"Round 3 will land on DEV a week from now looking exactly like round 1's
> failure, and will again have to be reconstructed from allure screenshots —
> which is the precise cost that motivated this whole branch. The change that
> added the retry is the change that took the diagnosis away."*

That branch existed **only** because a previous failure was undiagnosable from
the pytest tail. Shipping a retry that re-created the condition would have paid
the same forensic cost twice.

## The rule

Every re-raise gets its own message, and each message states **which defect it is
or explicitly is not**:

```python
except SomeTimeout as err:
    if <proof the action happened>:
        raise AssertionError(f"... evidence ... on attempt {attempt}. NOT bug #N — "
                             "the action landed; investigate downstream.") from err
    if <unexpected third state>:
        raise AssertionError(f"... on attempt {attempt} — neither X nor Y. "
                             "Unexpected state, not #N.") from err
    if attempt == ATTEMPTS - 1:
        raise AssertionError(f"... no-opped on all {ATTEMPTS} attempts. Bug #N.") from err
```

- **`from err`, not `from None`** — the originating exception stays in the
  traceback while your message is what pytest's short summary prints. You lose
  nothing and gain the tail.
- **Name the ticket, in both directions.** "Product bug #N" and "NOT #N" are the
  two sentences a triager needs; a message that names neither sends them back to
  the screenshots.
- **Include the evidence the branch just read** — the captured URLs, the composer
  contents, the attempt index. It is already in a local variable; not printing it
  is the whole bug.

## Proving it

Force each branch deterministically and capture the actual failure line — the
green run cannot show you any of them. `--tb=line` prints one line per failure, so
the proof is three greppable messages, not a screenshot. Then revert the
instrumentation and `diff` against a `/tmp` copy saved before you started.

Related: [[chatbox_composer_clear_is_a_lagging_signal]], [[react_fresh_props_defeat_to_be_enabled]]
