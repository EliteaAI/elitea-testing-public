---
name: Reproducing a failure across different signatures and an already-merged spec means environment, not code
description: When a new test's failures aren't identical run-to-run, sanity-check by re-running an ALREADY-merged, previously-passing spec touching the same mechanism — if it fails the same way, root-cause live via Playwright MCP before filing anything
type: feedback
---

## What happened (2026-08-19, wave-15, ELITEA-2217)

The batch's own gate + 3 independent standalone re-runs of a new test all
failed, but with TWO different-looking signatures (a "warning icon never
appeared" assertion once, a raw `Locator.wait_for` timeout on a messages
counter twice). This is NOT the deterministic-3/3-identical pattern the
sanctioned-RED exception requires, and it's also NOT obviously a flaky test
either — two distinct symptoms from the same flow is a signal to stop
guessing and get ground truth.

**Fast disambiguation step, before deep-diving the new test's own code:** find
an ALREADY-MERGED, previously-passing spec that exercises the SAME underlying
mechanism (here: `wait_for_context_budget_messages_count`, used by both the
new ELITEA-2217 test and the pre-existing, merged ELITEA-2218 test) and run
it standalone. It failed identically. A previously-passing, unrelated-to-this-diff
spec failing the same way rules out "the new wave's code is wrong" almost
completely — the shared cause has to be environmental or backend-state, not
something introduced this session.

**Then root-cause live, not via more pytest reruns.** Used Playwright MCP
directly against `localhost:5173`: navigated to chat, sent a real message,
confirmed via `browser_evaluate` that 2 real `<li>` messages rendered in the
DOM while the tracked testid still read `"0"` — even after a full page
reload (rules out a live-update lag). Then pulled the actual network response
via `browser_network_requests`/`browser_network_request` for the
`context_analytics` and `conversation` endpoints. The conversation endpoint's
own `message_groups[0].meta.error` contained the real root cause verbatim:
`elitea_sdk.runtime.exceptions.BudgetExceededError: ... budget_error_code:
"project_budget_exceeded"`. The chat UI still renders SOME reply (a
budget-exceeded stub message), so any test that only waits for "a response
event" passes through this silently — only tests inspecting real content or
token/context accumulation break.

## The technique, generalized

1. Two-plus DIFFERENT failure shapes on the same new flow (not 3/3 identical)
   → don't file a defect yet, don't classify sanctioned-RED, don't assume
   plain flakiness either.
2. Find and run an already-merged spec touching the same page-object
   method/mechanism. Same failure there = environmental, not this wave's
   regression.
3. Root-cause live via Playwright MCP: `browser_navigate` → drive the exact
   flow → `browser_evaluate` for DOM ground truth → `browser_network_requests`
   (filter by relevant path) → `browser_network_request` with
   `part: "response-body"` on the specific request to read the backend's own
   error/state. This is faster and more conclusive than N more pytest runs,
   and gives you the literal error class/message to quote in a filing.
4. If the root cause is infra/ops (a budget, a quota, a downed dependency) —
   not a code path — file it as a `question`, not a `bug`. It needs a human
   with admin access, not a code fix.
