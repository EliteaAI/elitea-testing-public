---
name: A strength claim is an assertion about an assertion — verify it or don't write it
description: "Strictly stronger" is a checkable statement; write the axis it is stronger on and name where it is not.
type: feedback
aliases: [strictly stronger, overclaim, strength claim, parsed payload equality, borrowed authority word]
tags: [area/review, type/discipline]
created: 2026-09-09
updated: 2026-09-09
---

## What happened

Replacing a byte-for-byte substring pin (`"{'total': 0, 'rows': []}" in text`) with
`parse(text) == {"total": 0, "rows": []}` — and describing it, in **four** committed
places, as **"strictly stronger"**.

It is not. Python dict equality compares **values, not types**, so
`{"total": False, "rows": []}` and `{"total": 0.0, "rows": []}` both compare **equal**
to `{"total": 0, "rows": []}`, where the substring pin discriminated them. The new
assertion is stronger on position, on extra/renamed keys, and on a payload that stops
rendering — and weaker on exactly one axis nobody will ever hit.

## The lesson

"Strictly stronger" is not rhetoric — it is a **universally quantified claim about two
assertions**, and it is cheap to falsify: enumerate the inputs the OLD one rejected and
check the new one still rejects each. I did not, and the claim propagated to four sites
before a reviewer ran the check in a REPL.

`.agents/role-overrides.md` § *precedent is not authority* names this exact failure
mode for "sanctioned"; it applies verbatim to "strictly stronger", "equivalent",
"guaranteed", "never", "always". A borrowed authority-word is how drift clears gates.

## What to write instead

**Name the axes.** "Stronger on position, extra/renamed keys and a missing payload; it
no longer discriminates int-vs-bool/float, which the product will not emit for a row
count." Longer, checkable, and it survives a reviewer with a REPL.

## The other half: the fix is the WORDING, not more code

The reviewer's own recommendation — and the lead's — was to correct the four sentences,
**not** to add `isinstance(payload["total"], int)`. Hardening against a shape the
product cannot emit buys nothing and costs a reader. When an overclaim is found, the
first question is *"is the assertion wrong, or is the sentence wrong?"* Here it was the
sentence, three times out of three.

Origin: PR #2080 review finding 1, ELITEA-1866, 2026-09-09.
Counterpart entry (reviewer side): `.agents/memory/qa-engineer/parsed_payload_equality_is_not_type_strict.md`.

Related: [[tool_result_text_content_has_no_newlines]]
