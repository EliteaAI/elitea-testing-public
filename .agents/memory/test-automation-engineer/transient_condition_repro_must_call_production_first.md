---
name: A transient-condition repro must call the production method FIRST
description: Instrumentation between the condition and the production call closes a short-lived window and fakes a green "fix verified"
type: feedback
aliases: [transient repro, tooltip window, false fix verification, matched control page object]
tags: [area/verification, type/gotcha]
created: 2026-08-28
updated: 2026-08-28
---

## The trap

Repairing a page-object defect that only fires under a **transient** condition
(a tooltip that closes on blur, a spinner, a loading window), the obvious repro
script is: establish the condition → enumerate/measure the DOM → call the
production method → assert. **That script cannot fail.**

The measurement block costs hundreds of milliseconds, and the condition is gone
by the time the production call runs. Both the pristine and the fixed code then
"pass", and the fix looks verified when nothing was actually tested.

Hit live on ELITEA-2037/#1891 (2026-08-28): the "Select LLM Model" MUI tooltip
that shadows `.MuiPopper-root >> nth=0` closes ~600 ms after the "+ MCP" click
moves the pointer away. First repro run reported
`PRODUCTION open_mcp_popper() -> PASSES` on **pristine `origin/main` code** —
i.e. the reported CI failure did not reproduce, which reads as "unreproducible"
rather than "my script is wrong".

## The rule

Structure a transient-condition repro so the **production call is the very next
action after the condition is established**. Do all measurement on the value the
production method *returned*, never before calling it:

```python
force_the_condition(page)                 # tooltip up
assert precondition_holds()               # cheap, one count()
popper = page_object.open_mcp_popper()    # THE call, immediately
describe(popper)                          # measure AFTERWARDS
```

Then run that same script twice — once with the code checked out pristine
(`git checkout origin/main -- <files>`) and once with the fix — and require the
pristine run to **FAIL with the reported signature**. A repro that does not go
red on pristine code has proven nothing about the fix.

Related: [[matched_control_run_before_blaming_a_diff]]
