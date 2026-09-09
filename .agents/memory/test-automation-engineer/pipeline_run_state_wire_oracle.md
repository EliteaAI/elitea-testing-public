---
name: Pipeline run state — read the oracle off the wire, not out of the chat
description: The LLM1->END transitional edge carries the run's real state; the chat's JSON block is a DIFFERENT call and disagrees
type: reference
aliases: [run state oracle, agent_on_transitional_edge, structured output state, run details state]
tags: [area/pipelines, type/technique]
created: 2026-09-10
updated: 2026-09-10
---

## The oracle

For any assertion about what the Run Details panel SHOULD show, the run's own
backend state is available on the wire and is the correct oracle for a
nondeterministic (LLM) producer:

```python
edges = [f for f in frames
         if f.get("type") == "agent_on_transitional_edge"
         and (f.get("response_metadata") or {}).get("next_step") == "END"]
state = (edges[-1].get("response_metadata") or {}).get("state") or {}
```

Confirmed live on DEV 2026-09-10 (ELITEA-2453): this is exactly the object the
panel renders — `parseRunsByEvent.helpers.js:263-278` assigns it to the last
timeline entry and `StateItemView.jsx` does `JSON.stringify(state[name])`.
Capture with `PipelineDetailPage.capture_websocket_frames()`, entered BEFORE
any navigation. Passive observation, not substitution.

## The trap that makes this necessary

**The JSON block visible in the chat answer is NOT the state.** A
`structured_output: true` node makes (at least) TWO LLM calls — the answer call
and the structured-extraction call — and they routinely disagree. Observed in
one passing run: the chat showed
`custom_json: {"key1": "value1", "key2": "value2"}` while the state written was
`{"status": "active", "count": 5}`. Asserting the panel against the chat text
would have failed a perfectly correct run.

Worse, when the answer call replies in prose the extraction writes NOTHING and
the run still reports `Completed` with a success message in the chat
(`EliteaAI/elitea-testing-public#2153`, ~25% of runs, bursty). So the chat is
not even evidence that state exists.

Related: [[dev_env_run_harness_and_goto_flake]]
