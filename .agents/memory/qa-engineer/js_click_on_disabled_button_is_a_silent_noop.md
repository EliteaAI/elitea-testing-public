---
name: JS el.click() on a disabled button is a silent no-op
description: Why "the action never happened but nothing failed" reds are misdiagnosed two steps downstream, and the two greps that find them
type: feedback
aliases: [evaluate click, el.click(), disabled button, silent no-op, save did nothing, vacuous url guard]
tags: [area/ui-tests, type/anti-pattern]
created: 2026-08-28
updated: 2026-08-28
---

## The rule

`locator.evaluate("el => el.click()")` on a `disabled` HTML button dispatches
**nothing** — browsers do not fire click on disabled elements. No exception, no
network, no console error. Playwright's own `locator.click()` would have raised,
because it auto-waits for the element to be **enabled**.

So `evaluate("el => el.click()")` is not "a more reliable click". It is the one
form of click that **cannot fail**, and it converts a real fault into a red two or
more steps downstream, with the evidence gone.

Verified live 2026-08-28 on `dev.elitea.ai` (issue #1897): with one required field
left empty, the JS click produced — URL unchanged, zero POSTs, no toast, no error
element; the real `.click()` raised `TimeoutError` immediately.

## Its usual accomplice: the vacuous URL guard

`assert "/credentials" in page.url` is **True** on
`/credentials/create-credential/jira` — the page the browser never left. A
substring guard against a nested route is not a navigation check. Use
`page.wait_for_url(re.compile(r"/credentials/all(\?.*)?$"))`.

## When triaging any "the action didn't happen" red

Grep the spec before anything else:

```bash
grep -nE 'evaluate\("el ?=> ?el\.click' <spec>          # cannot-fail click
grep -nE 'assert ".*" in page\.url'   <spec>            # possibly-vacuous guard
```

A hit on both means the reported failure is almost certainly **not** where the
traceback points. Fix the diagnosis first, then re-run — do not chase the
downstream assertion.

⚠️ **Do not use step duration to tell a no-op from a success.** A successful save
and a no-op click both measured ~3.1 s, because the time was a fixed
`wait_for_timeout(3000)` and `networkidle` returned in 0–4 ms either way.

Related: [[retarget_suite_at_dev_without_editing_env_test]]
