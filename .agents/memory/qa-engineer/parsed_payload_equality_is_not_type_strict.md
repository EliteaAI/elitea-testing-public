---
name: Parsed-payload equality is not type-strict — "strictly stronger than a substring match" is an overclaim
description: Replacing a serialization substring pin with `parsed == {...}` loses int/bool/float discrimination; verify the claim, don't accept it
type: feedback
aliases: [structural equality assertion, json.loads assertion, repr pin replacement, ELITEA-1866, parse_tool_result_payload]
tags: [area/assertions, type/review-check]
created: 2026-09-09
updated: 2026-09-09
---

## The pattern under review

A merged test pinned a payload as a **substring of one serialization**
(`"{'total': 0, 'rows': []}" in result_text`). The product changed serialization,
the test went red on correct behaviour, and the repair replaced it with
**structural equality on the parsed payload** (`parse(...) == {"total": 0, "rows": []}`).
The repair is right, and the standard justification — *"structural equality on the
whole payload is strictly stronger than a substring match on one rendering of it"* —
is what a reviewer is asked to accept.

## Verify it; it is very nearly true, and not exactly true

Python dict equality compares **values**, not types:

```python
{"total": False, "rows": []} == {"total": 0, "rows": []}   # True
{"total": 0.0,   "rows": []} == {"total": 0, "rows": []}   # True
```

So the parsed form accepts `false` and `0.0` where the byte-for-byte substring pin
did not. Key reordering is also newly accepted — that one IS semantically free, the
type laxity is not. Everything else moves the right way (position becomes anchored,
extra/renamed keys still fail, a missing payload raises).

**Reviewer move:** run the two-line probe above against the *actual* expected
constant before repeating "strictly stronger" back. If the observable is a count or
a flag, `== EXPECTED` alone does not pin the type; `isinstance` on the discriminating
key closes it. Whether that is worth the line is a judgement — silently endorsing the
overclaim is not.

## The other edges worth probing on a regex payload extractor

`(\{.*\})\s*$` (greedy, end-anchored) after a marker split:

- prose braces **before** the marker → dropped ✓ (this is what the marker split buys)
- prose braces **after** the marker → one greedy blob → parse fails **loudly** ✓
- any trailing text after the payload → `$` fails → **loud** ✓
- the marker appearing **inside** the payload → truncates mid-payload → **loud** ✓
- **no marker at all** → whole text is searched; still parses if the payload ends it

Every failure edge is loud. That is the property that matters — a payload extractor
whose miss path returns a default or an empty dict would let the assertion pass on a
surface that stopped rendering.
