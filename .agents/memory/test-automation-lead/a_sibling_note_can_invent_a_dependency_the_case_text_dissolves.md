# A sibling's "read #N first, your fix falls out of it" can be a dependency the CASE TEXT dissolves

**Date:** 2026-09-09 · **Context:** #2112 / ELITEA-0679 (image creation), sibling note from #2083

## What happened

#2112's only prior comment, from the agent that worked sibling card #2083, said:

> "Suite-wide decision (`config.default_model_name` is a dead literal + 4 specs hardcode removed
> display names) is carded separately as **#2117**. Whoever picks this card up should read #2117
> first — the fix here likely falls out of that decision."

#2117 is an OPEN, UNANSWERED `question` card. Taken at face value, #2112 was parked-by-proxy:
blocked on a human decision about which model literal to use.

It wasn't. **The TMS case never named a model.** ELITEA-0679's precondition is *"At least one
shared image model is available as the default"*, its Step 3 says *"using the default image
model"*, and it has **no model-selection step at all**. `select_model("GPT-5.2")` was a
test-implementation artifact. The repair deleted the step; the card shipped the same session.

## The rule

**Before accepting that your card is gated on someone else's open question, read the upstream
contract — the TMS case — and ask whether the disputed thing is something YOUR case actually
requires.** A sibling's note records their reading of their own surface, honestly and usefully.
It is not a verdict on yours, and "this looks like the same root cause" is where an inherited
dependency gets invented.

Corollary, and the reason the distinction is sharp: **#2117 is about specs that ASSERT a model
display name, or that seed one via API. This spec did neither** — the model was pure *transit*.
Where a value is transit, the correct answer is very often **name nothing and let the product's
own default answer**, which can never rot. Where it is the observable, you genuinely need the
human. Same dead literal, two completely different dispositions.

## Generalisation

Same family as `sibling_fix_cards_do_not_share_a_root_cause.md` and
`my_dispatch_premise_can_be_false_let_ics_refuse_it.md`, one level up: there, a sibling's
*diagnosis* doesn't transfer; here, a sibling's *blocker* doesn't transfer either.

**Test to apply:** can I state, quoting the case text, what my case requires of the disputed
thing? If the quote says "the default", "any", or says nothing at all — there is no dependency,
and parking would have been a false block that cost a human round-trip.
