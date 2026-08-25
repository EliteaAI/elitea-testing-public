---
name: UI/flow assumption gate
description: When test fails and you assume UI/flow changed, verify against the case text before proceeding
type: feedback
---

## The rule

When investigating a test failure, if you assume the UI or application flow has changed (e.g. "maybe the button moved", "perhaps the wizard now has an extra step", "the modal might close differently now"), **STOP and verify against the test case** before building that assumption into your analysis or fix.

## The check

1. Read the TMS case text (the source `.md` file in `onetest-ai-tm-Elitea`)
2. Does the case describe the flow/UI you're assuming exists?
   - **YES** → the case was updated to match the product change → proceed with that understanding
   - **NO** → the case still describes the old flow → your assumption is unconfirmed

## If unconfirmed

**Do not proceed on the assumption.** Surface it to the user:

> "The test fails as if [describe assumed change]. However, the case text (ELITEA-NNNN) still describes [old behavior]. Either:
> - The product changed and the case needs updating (case bug), OR  
> - My assumption is wrong and the failure has a different cause.
>
> Should I proceed assuming the product changed, or investigate other causes?"

Then **wait for explicit direction.**

## Why this exists

Multiple sessions (guardrails test fixing: b9b71e12, ebae2583, 76bb064f, 14e06b31, d884c08c) had thrash cycles where an agent assumed a UI change, built a fix around that assumption, then discovered the assumption was wrong when the human corrected it. The case text is ground truth for "what the product should do" — if it's out of sync with the product, that's a separate issue (case update needed), not licence to guess.

## Examples

**WRONG:**
```
Test fails clicking "Save" → assume button moved → 
search DOM for "Save" in different locations → 
update locator to new location → commit
```

**RIGHT:**
```
Test fails clicking "Save" → check case ELITEA-1234 → 
case still says "click Save button in top-right" → 
surface to user: "Case describes top-right, but test fails there. 
Did UI change and case needs update, or is this a real product bug?"
```

## Scope

Applies to **UI behavior changes only** — button locations, wizard steps, modal flow, navigation paths. Does NOT apply to:
- Backend API contract changes (those have OpenAPI as ground truth)
- Obvious product bugs (elements missing, errors thrown)
- Timing/sync issues (those are framework problems, not flow changes)
