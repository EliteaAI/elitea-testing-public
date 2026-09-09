---
name: Prove a removed assertion is ENTAILED by what replaced it — the entailment test separates correction from masking
description: "Correcting removes a premise the case never had" is a judgment; entailment makes it a proof. If the old assertion cannot be false on any path reaching the new one, nothing was weakened.
type: feedback
aliases: [correction vs masking, entailment test, removed assertion, weakened assertion, is this masking, guard-dominated oracle, over-assertion on LLM content]
tags: [area/review, area/test-repair, type/instrument]
created: 2026-09-10
updated: 2026-09-10
---

## The problem the usual rule leaves open

The project's own distinguishing test — *masking removes evidence of a real
fault; correcting removes a premise the case never had* — is correct but
**judgmental**. Every repair author sincerely believes their removal is the
second kind. Quoting the TMS case establishes that the premise was absent; it
does **not** establish that the replacement is at least as strong.

## The instrument

Ask: **can the removed assertion be FALSE on any path that reaches the new
one?** If no, the old assertion is *logically entailed* by the new one, and the
removal cannot have weakened anything — that is a proof, not a reading.

Worked case, #2120 / ELITEA-2453 (2026-09-10). Removed: `custom_text != '""'`,
`len(parsed_list) > 0`, `len(parsed_json) > 0` — three assertions on content an
LLM chose, which the case never contracted. Replaced by a precondition guard
admitting only a non-empty `str` / non-empty `list` / non-empty `dict`, then
`json.loads(rendered) == backend_state[name]`. Since the guard **dominates**
every one of those steps, all three removed assertions are unfalsifiable there.
Strictly stronger, too: the new shape also catches a mangled value, a dropped
value, and a stale/other-run value — none of which the old shape could see.

## The companion check: is the vacuum actually closed?

An equality oracle has the opposite failure mode — `"" == ""` passes and proves
nothing. So entailment is only half the argument; the other half is that the
guard **dominates**, structurally:

- trace the control flow, don't trust the comment — every exit of the loop,
  every `continue`, every soft-assert;
- confirm **no step reads the oracle from inside** the retry/guard block;
- then ask the reverse: can the equality pass against the **wrong run's** state?

## The tell that you are looking at this class

A `[FIX]` card whose failing assertion constrains the **content produced by a
nondeterministic producer** (an LLM, a ranking service, a clock) rather than the
product's *behaviour*. `!= ""`, `len(x) > 0`, `is not None` on a generated value
are the signatures. The case text almost never contracts content — check.

## The trap on the other side

**Do not simply delete the content assertions.** `""` / `[]` / `{}` trivially
satisfy a surviving "renders as a JSON-quoted string / array / object" check, so
an entirely unpopulated run would go green. Deletion IS masking here; only
deletion **plus** a dominating guard is a correction.

Related: [[repair_of_a_transient_needs_a_negative_control]] ·
[[mixed_shard_spread_refutes_the_outage_and_means_a_missing_precondition]] ·
[[an_empty_string_on_both_sides_of_an_assert_means_absence]]
