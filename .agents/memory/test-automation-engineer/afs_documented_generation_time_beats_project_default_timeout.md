---
name: AFS-documented generation time beats project default timeout
description: When an AFS's live analysis notes an actual observed generation duration, use that as the timeout floor instead of the project's blanket AI_RESPONSE_TIMEOUT default.
type: feedback
---

`test_context_management_disabled.py` (ELITEA-2216) first shipped with the
common project default `AI_RESPONSE_TIMEOUT = 45_000` (matches most
short-prompt chat tests) and failed 3/3 identically — `wait_for_ai_response()`
timed out with "Copy button never appeared", `_extract_message_body()`
stuck reading the transient "Thought for less than a second" placeholder the
whole time.

The AFS's own § Test Steps text had already recorded the real number from
live analysis: *"a complete multi-paragraph streamed response, ~90+ seconds
of real generation"* for this exact "long, detailed story" prompt shape. The
45s default was never going to be enough — the case's own live-analysis
evidence said so before a single line of test code was written.

**Rule of thumb:** when an AFS documents an actual observed
duration/latency/count for the SAME action the test will perform, treat that
number as the source of truth for the corresponding timeout/threshold, not
whatever the file's neighbouring tests happen to default to. A short/simple
prompt test's 30-45s default does not transfer to a "detailed, multi-
paragraph, non-trivial" prompt shape — bump it (this case used 120s, giving
headroom above the AFS's 90s+ observation) rather than debugging a green-
looking helper (`wait_for_ai_response` itself was working correctly; it was
correctly rejecting a still-transient placeholder).
