---
name: A comment quoting a removed raw locator trips the reviewer's grep
description: Describe a deleted raw handle in prose — never paste the code fragment into the explanatory comment
type: feedback
---

When a repair REMOVES a raw locator and you explain why in a comment, do not paste
the removed fragment. The reviewer's mechanical locator-policy grep matches added
lines by pattern, not by syntax role, so a comment is indistinguishable from code:

```bash
git diff origin/main -- automation/ | grep -nE '^[+].*(get_by_role|…|page\.locator|\.locator\()'
```

Hit on 2026-08-27 (ELITEA-1866 / #1815). The Step 28b repair deleted a raw
`page.locator('text=/Model.*…/i')` and the comment justifying the deletion quoted
it verbatim — one hit, on the very line documenting compliance. A reviewer running
the same grep sees a violation and spends a round on it.

**Fix: describe the removed handle in prose.** "a raw page-level text-matching
handle on the pattern /Model.*Anthropic|…/i" carries the same information and greps
clean. Same applies to the fidelity grep (`page.route(`, `.evaluate(`, `monkeypatch`)
— never quote those in a comment either.

Run both self-check greps yourself and READ the hits before handoff; a hit you can
explain still costs a round if the reviewer finds it first.
