---
name: Redundant assert after a wait on the SAME locator is not vacuous — but it downgrades the red
description: Wait-then-assert on one locator makes the assert unreachable-as-failure; coverage survives, diagnostics and pytest outcome do not.
type: feedback
---

## The shape

```python
page_obj.wait_for_items(popper, timeout=10_000)          # popper.locator(SEL).first.wait_for(state="visible")
assert page_obj.get_item_count(popper) > 0, "…message…"  # popper.locator(SEL).count()
```

Same locator, same subject. Once the wait returns, the assert **cannot** be
False. Reviewers reach for "vacuous" here. That is the wrong word, and getting
it wrong in either direction is expensive.

## Rule the two apart by asking WHAT VARIES, not whether the assert can fail

| | Subject of the assertion | Broken product → | Verdict |
|---|---|---|---|
| **Content-scoped locator** (`.MuiPopper-root:has([data-testid="x"])` then assert `x` is present) | **Defined by the thing asserted** — locator silently retargets to whatever else on the page carries `x` | can still go GREEN on the wrong element | **vacuous — blocks.** Coverage destroyed |
| **Wait-then-assert** (subject chosen independently; wait and assert both interrogate it) | fixed, independent | wait raises `TimeoutError` → **RED** | **redundant — does not block.** Coverage intact |

The question that separates them: *if the product breaks, does the test still
go red?* Redundancy keeps the red and moves it; vacuity removes it.

## What redundancy DOES cost — say it, don't wave it through

1. **The assertion message becomes dead code.** It can never print. The real
   failure is a bare `TimeoutError: Locator.wait_for … [data-testid="x"] >> nth=0`.
2. **pytest outcome flips `failed` → `broken`** (allure). This repo's whole
   noise-triage ledger in `.agents/testing.md` § Known issues turns on that
   distinction — `broken` reads as "environment flake, re-run", `failed` reads
   as "product/data problem". A real missing-fixture failure now arrives
   wearing the flake costume.

**Better shape when you get to choose:** one auto-waiting assertion instead of
two statements — `expect(loc).not_to_have_count(0, timeout=…)`. Keeps the
message, keeps `failed`, keeps the wait.

## Precedent is not authority here

PR #1921 shipped this shape first and PR for ELITEA-2037/#1891 mirrored it.
"The sibling already ships it" is not a disposition (`role-overrides.md`
§ precedent is not authority) — rule on it each time. Both times the ruling
came out non-blocking, and both times the cost above was worth stating.
