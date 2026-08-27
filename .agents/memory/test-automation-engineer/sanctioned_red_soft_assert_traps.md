---
name: Sanctioned-RED soft-assert traps
description: Two rules for implementing a known-defect assertion — never author a new raw locator to fit expect.soft()'s API shape (use the soft_failures/pytest.fail() list for plain value comparisons), and a defect gated on accumulated state/volume is NOT guaranteed to reproduce RED on any given run.
type: feedback
---

## Rule

**1. Pick the mechanism from the operand type, not from habit.**
`expect.soft()` applies only when the thing compared is natively a
Locator/Page/APIResponse. For a plain `str`/`int`/`list` comparison, use this
project's established shape:

```python
soft_failures = []
# Known defect: #N — <what the correct behavior would be>
if page_obj.get_message_count() != expected:
    soft_failures.append(f"#N — got {…}, expected {…}")
...
if soft_failures:
    pytest.fail("; ".join(soft_failures))
```

(precedent: `test_fork_agent_to_different_project.py` #570,
`test_skill_agent_interaction.py` #38)

**Never author a new raw locator to force-fit `expect.soft()`.** A dispatch
suggesting `expect.soft(page.get_by_text(...)).to_be_visible()` is still a
new non-testid handle — the reviewer's mechanical grep flags it regardless of
any pre-existing tech-debt or third-party-widget framing on the same file.
Reusing an *already-documented* handle is what the exception covers;
authoring a new one is not.

**2. RED is only guaranteed for stateless defects.** The merge gate's
sanctioned-RED bar ("3/3 identical failures IS its deterministic gate")
assumes a pure logic/UI-state bug. A defect gated on accumulated data volume
or shared-account history may sit GREEN on every run because its
precondition isn't currently met. Actually run it, look at the result, and
say so explicitly in the AFS amendment, PR body and Run Report. A
forward-looking regression net that isn't currently red is legitimate to
ship — but only when labelled as such, never reported as the dispatch's
anticipated outcome.

**3. Both operands must come from the SAME getter.** Page objects expose
counters that look interchangeable and aren't (`get_message_count()` = total
vs `get_assistant_message_count()` = assistant-only ⇒ ~2× apart). Run the
real observed repro numbers through the comparison before trusting it:
`100 < 48` is `False` — the check would never have fired on the confirmed
repro. Capture the baseline with the getter you will later compare against.

**4. The `if` condition must go TRUE on the CURRENT buggy symptom, not on a
deviation from it.** `soft_failures.append(...)` existing is necessary but
NOT sufficient — trace which branch actually fires TODAY, while the defect
is open. Compliant shape (`test_pipeline_hitl_node_runtime_behavior.py`
#1103): `if restarted_types: soft_failures.append(...)` — true exactly when
the symptom occurs, so the test is RED now and flips GREEN automatically
once fixed. The inverted shape (ELITEA-2445 R0, PR #1382) wrote
`if timeline_count != _EXPECTED_COUNT_WITH_BLOCKED_NODE: soft_failures.append(...)`
— true only if the defect got FIXED or something else changed — so the test
was GREEN for an open, confirmed, filed defect and would only go RED if the
defect were fixed. Mechanically identical shape, opposite meaning; the
reviewer's mechanical grep (and a skim for "does soft_failures exist") can't
catch it — you have to read which branch is live. Self-check before
shipping any known-defect soft-assert: plug in the CURRENT observed repro
values and confirm the condition evaluates TRUE right now.

## Seen 1× (three distinct traps, one case) + 1 related

- ELITEA-1799 / PR #608 — GH#607 sanctioned-RED assertion: dispatch-suggested `expect.soft(get_by_text(...))` was a new raw locator (Trap 1); the defect needs >~100 message groups but `start_new_chat()` guarantees a fresh small conversation, so it never went RED (Trap 2); `get_message_count()` vs `get_assistant_message_count()` cross-compared, caught in review (Trap 3).
- ELITEA-1800 / PR #626 — same defect family; delta-assertion safety verified live rather than inferred (see `verify_your_own_delivery_before_handoff.md` §6).

See also: sanctioned_red_new_locator_and_account_state_traps.md ·
gh607_delta_assertion_survives_truncation_mechanism.md ·
../qa-engineer/count_vs_assistant_count_getter_unit_mismatch.md
