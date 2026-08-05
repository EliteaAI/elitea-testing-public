---
name: ELITEA-2336 PR #1204 R3 — known-defect console matcher required BOTH text+stack, implementer's own reruns showed it flakes
description: _is_known_defect_1203() required "Maximum update depth exceeded" AND "SecretsContent.jsx" in the same ConsoleMessage.text; implementer's own 3x verification reruns hit a short-form message (no stack suffix) 1/3 times, causing a hard fail instead of the sanctioned pytest.fail() soft path — same class as elitea_1962_pr617_r2_known_518_console_flake.md
type: feedback
---

## What happened

Reviewing PR #1204 (ELITEA-2336, Secrets inline create) round 3 (re-review
after the AFS-amendment fix was confirmed done). The implementer's OWN
`.agents/memory/test-automation-engineer/daily/2026-08-05.md` (17:30 entry)
and `secrets_page_react_render_loop_on_mount.md` transparently documented an
unresolved finding from their own round-2 verification: rerunning the merged
spec 3x, 2/3 correctly hit the intended `pytest.fail()` soft path for the
known, filed, OPEN defect `elitea-testing-public#1203` — but 1/3 **hard-failed**
at the earlier `assert not unexpected_errors` line instead, because that
run's single captured `ConsoleMessage.text` was short-form (~250 chars, no
component-stack suffix) vs the normal long-form (~4600 chars, full stack
incl. `SecretsContent.jsx`). The matcher:

```python
def _is_known_defect_1203(text: str) -> bool:
    return "Maximum update depth exceeded" in text and "SecretsContent.jsx" in text
```

requires BOTH substrings, so the short-form occurrence fell into
`unexpected_errors` and hard-failed the test with a DIFFERENT failure
signature than the other 2 runs.

## Why this blocks

`.agents/testing.md` § Merge gate's sanctioned-RED exception requires
"(a) deterministic — identical failure 3/3" — and this PR's own body invokes
exactly that exception to justify shipping RED until `#1203` ships. Evidence
already exists (from the implementer's own verification, not hypothetical)
that the failure is NOT always identical: it flips between a `pytest.fail()`
soft-path message and a raw `assert not unexpected_errors` hard-fail
depending on whether Playwright's console-message capture includes the
stack-trace suffix for that particular occurrence. If the batch hardening
gate's independent N=3 hits the short-form branch even once, the 3 runs
won't show an identical signature, and the case can't legitimately be
classified sanctioned-RED that cycle.

## Durable lesson — generalizes the #518 pattern

Same root cause class as `elitea_1962_pr617_r2_known_518_console_flake.md`
(credentials #518): a known-defect console-filter matcher anchored on BOTH
the warning text AND a volatile suffix (component name / stack trace) is
fragile, because Playwright's console-message text capture can truncate or
omit the stack portion non-deterministically. **The fix is the same shape
both times: match on the STABLE prefix of the known warning's own text
alone**, dropping the volatile suffix requirement — for #1203 specifically,
`"Warning: Maximum update depth exceeded. This can happen when a component
calls setState inside useEffect"` is already unique enough (per the filed
issue's own reproduction notes) without requiring `"SecretsContent.jsx"`.

**When reviewing any `_is_known_<N>_warning`/`_is_known_defect_<N>`-style
matcher**, check whether it requires a stack/component-name substring in
addition to the core warning text — if the implementer's own verification
notes (Run Report, daily log, or a "not fixed, out of scope" memory entry)
mention ANY rerun landing on a different failure line/signature than the
others, that is not a minor flake to wave through — it directly undermines
the sanctioned-RED gate's own determinism requirement and should block until
narrowed to the stable prefix.

(from ELITEA-2336, PR #1204, round 3 — the same reviewing agent had
previously confirmed and closed this class of issue for #518 on PR #617)
