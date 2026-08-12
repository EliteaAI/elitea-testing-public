---
name: Console side-channel checks — the five ways one silently proves nothing
description: A "no console errors" assertion is only real if the listener is dual (console+pageerror), registered before step 1, its predicate matches the spec's exact wording, its known-defect filters match EVERY message shape the defect emits, and the filter has been proven to fire. Ship the canonical block; don't retrofit.
type: feedback
---

## Rule

A side-channel check that runs is not a side-channel check that works. Ship
this shape, in full, the first time — every deviation below has already
shipped and bounced at review.

```python
console_issues, page_errors = [], []

def _on_console(msg):
    if msg.type in ("error", "warning") and not _is_known_<ISSUE>(msg):
        console_issues.append(msg)

page.on("console", _on_console)                    # BEFORE step 1, not mid-flow
page.on("pageerror", lambda e: page_errors.append(str(e)))
...
with allure.step("Side-channel check — no console/JS errors"):
    assert not console_issues and not page_errors, (...)
```

Five things to get right, in order:

1. **Dual listener.** `page.on("console")` alone misses uncaught JS
   exceptions. `page.on("pageerror")` is a co-default, not an afterthought.
2. **Registration point.** Register before the FIRST step the assertion
   claims to cover — right before `try:`/Step 1. Comment *why* it's early so
   nobody moves it down "for tidiness." Moving it earlier can surface real
   pre-existing noise: extend the known-defect filter, never weaken the
   assert or revert the move.
3. **Predicate matches the wording.** Re-read the AFS's Expected Results
   literally. "errors" ⇒ `msg.type == "error"`. "errors **or warnings**" /
   "0 console issues" ⇒ `msg.type in ("error","warning")`. Name the list
   `console_issues` when it holds both, so the variable can't lie.
4. **One filter fn per known defect**, module-level, docstring citing the
   ticket, matching on BOTH `msg.text` AND `(msg.location or {}).get("url")`.
   One root cause routinely emits SEVERAL distinct message shapes — React's
   error-boundary companion message does **not** repeat the original error
   text. OR the conditions (original substring, plus `"above error occurred"`
   and `"<ComponentName>"`).
5. **Prove the filter fired.** Add a throwaway unfiltered-list + raw
   `msg.text`/`msg.location` print for ONE run, confirm the artifact really
   fires and is really filtered, then remove the debug code. For a
   probabilistic defect (~60–75%), green runs prove nothing — grep the
   defect's own recovery/log line across a `-s --log-cli-level=WARNING` run.

**Corollary:** first-ever listener on a long-live page will surface genuinely
new defects. That is the check working — file them, don't suppress them.

## Seen 5×

- ELITEA-1929 R1 / ELITEA-1881 — shipped `msg.type=="error"` against an AFS saying "errors or warnings"; a new MUI-Tabs warning surfaced only once a listener existed (#549).
- ELITEA-1902 / PR #606 — listener registered inside Step 2; Step 1's output never observed despite "full-flow" wording.
- ELITEA-2095 / PR #693 — AFS claimed a "console-error check" the shipped test never made; established the filter-fn + Side-channel-step idiom; verified the project-471 403 fired 4×/run.
- ELITEA-1962 / PR #617 R2 — #518 emits 3 console shapes; single-substring filter missed 2/3 and failed live. #554 confirmed leaking from a bare list `navigate()` too.
- ELITEA-2094/#688 then ELITEA-2095/#693 R2 — both shipped console-only, both retrofitted `pageerror` days apart. Dual listener is now the default.

See also: console_listener_error_only_predicate_gap.md ·
console_listener_registered_after_flow_start_gap.md ·
console_filter_idiom_and_seed_vs_document_ambient_data.md ·
known_518_two_shapes_plus_verify_filter_actually_fired.md ·
two_wait_idioms_coexist_and_dual_listener_now_established_twice.md
