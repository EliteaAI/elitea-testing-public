---
name: A pipeline run's state is readable on the Socket.IO wire — the panel is not the only source
description: agent_on_transitional_edge (next_step END) carries exactly what Run Details renders; use it as an independent oracle
type: reference
aliases: [pipeline run state oracle, agent_on_transitional_edge, run details state source]
tags: [area/pipelines, type/handle]
created: 2026-09-10
updated: 2026-09-10
---

## Where the value comes from

```
backend  agent_on_transitional_edge{response_metadata: {next_step, metadata.langgraph_node, state}}
   -> parseRunsByEvent.helpers.js:263-278   assigns `state` to the LAST timeline entry
   -> RunStateDialog.jsx:346-350            valueAfter = timeline[selectedStep].state[name]
                                            valueBefore = selectedStep ? timeline[selectedStep-1].state[name] : ''
   -> StateItemView.jsx:32,45               renders JSON.stringify(value)
```

So `[f for f in frames if f["type"]=="agent_on_transitional_edge"
and f["response_metadata"]["next_step"]=="END"][-1]["response_metadata"]["state"]`
is exactly what the panel shows for the default-selected (last) step.

Capture via `PipelineDetailPage.capture_websocket_frames()` — **entered before the first
navigation** (Playwright's `websocket` event fires at connection-open only).

## Why it's worth reaching for

- Independent oracle: settles "UI dropped the value" vs "the backend never had it"
  in one comparison (30/30 matched on ELITEA-2453 — the panel is faithful).
- Lets a spec decide retry-vs-proceed **without** opening the Run Details panel, which
  can only be opened once (the MUI Dialog then intercepts canvas clicks).
- Step 0's `Before` is a hardcoded `''` (renders as `""`) — see open defect `#1271`;
  don't read it as state.

Observation, never substitution — same class of evidence as reading a response body.
