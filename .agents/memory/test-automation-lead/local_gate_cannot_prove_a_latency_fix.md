# A local gate cannot prove a CI-latency fix — say so instead of implying it

**Learned:** 2026-09-09, FIX #2078 (ELITEA-2354/2363).

localhost:5173 proxies the **same DEV backend**, so backend-latency reds seen in CI are usually
**not reproducible locally**. Measured: the Agent Hub bulk fetch takes ~9.0-10.6s locally against a
15s cap that expired in CI.

Consequence for the merge gate: 3x green locally proves **no regression**. It does **not** prove the
fix. Both the PR body and the closure record must say which, and name the human-triggered
`test-ui-dev.yml` run as the real confirmation. Claiming the local gate validated the fix would be a
false closure row of the #35/#36/#37 family.

Corollary worth reusing: when a fix is not locally provable, ship **diagnostics** alongside it so the
NEXT occurrence is self-classifying (here: on timeout, re-raise with the URLs actually observed —
`observed: ['none']` = outage/page never got there vs a listed 200 = the awaited call alone was slow).
