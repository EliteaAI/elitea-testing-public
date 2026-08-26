---
name: A shared-state fixture's try/finally must open BEFORE the mutating write, not after its readback
description: Setup code between the mutating write and the try opens an unprotected window that leaks org-wide state — pytest runs no teardown for a fixture that raised in setup
type: feedback
aliases: [fixture teardown window, org-wide side effect leak, guardrails fixture, restore not in finally, readback assert]
tags: [area/fixtures, type/gotcha]
created: 2026-08-27
updated: 2026-08-27
---

## The pattern that looks safe and is not

```python
original = api.get_config()
api.set_config(mutated)          # <-- shared/org-wide state is now DIRTY

applied = api.get_config()       # <-- UNPROTECTED: a raise here leaks it
assert marker in applied, "..."  # <-- UNPROTECTED: this assert is *designed* to fail sometimes

try:
    yield
finally:
    api.set_config(original)     # never reached if the lines above raised
```

Every line between the mutating write and `try:` runs with the shared state dirty and
**no restore path** — pytest does not run the teardown half of a fixture that raised
during setup. The readback assertion is the worst offender: its whole reason to exist is
that it can fail, and when it does it leaves the environment corrupted for everyone.

Reviewers: "the restore is in a `finally`" is not the check. The check is
**"is the `finally` armed at the moment the write lands?"** Read where `try:` opens
relative to the write, not whether the word `finally` appears.

## The fix

Open `try:` immediately **before** the mutating call (or set an `applied = False` flag and
guard the restore on it). Verification, logging and any other setup work then live inside
the protected region.

## Where this bit

ELITEA-2211 rework (PR #1832), `automation/fixtures/data_fixtures.py:1901-1913` — an
org-wide guardrails `sensitive_tools` PUT against the shared DEV backend, with the
readback assert and a `logger.info` sitting in the gap. Blast radius of a leak: every
artifact-toolkit `delete_file` call org-wide starts hitting an unexpected HITL
authorization card, with no self-healing and a symptom that points nowhere near the cause.

Related: [[positive_existence_wait_cant_assert_negative_transition]]
