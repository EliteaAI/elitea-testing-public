---
name: A soft wait helper cannot fail — it moves the failure to the wrong assertion
description: wait_for_embedded_chat_response logs a WARNING and returns; the red then names the wrong subsystem
type: feedback
aliases: [soft wait, wait_for_embedded_chat_response, did not stabilise, element not found red]
tags: [area/pipelines, area/chat, type/triage]
created: 2026-09-09
updated: 2026-09-09
---

## The pattern

`PipelineDetailPage.wait_for_embedded_chat_response()`
(`automation/pages/pipeline_detail_page.py:7336-7396`) logs
`WARNING Embedded chat response did not stabilise within timeout` **and returns
normally**. Any spec built on it has no wait: the next assertion inherits the
race and reports the failure in its own vocabulary ("element not found"),
naming the wrong subsystem. ELITEA-2448 / `#2076` burned a CI run and a
session exactly this way.

Two ways it silently consumes its full budget:

1. Its `[aria-label="Delete"]` wait takes **all remaining budget** inside a bare
   `try/except: pass`. A pipeline that emits no chat answer never renders that
   action bar (verified 165 s post-send, hover included).
2. The pre-answer placeholder rotates **every 2.0 s** (`Waking the agent…` →
   `Packing its tools…` → `Wiring integrations…` → `Fetching keys & creds…` →
   …), so `stable_duration_ms=3000` can never be met while it shows.

## What to do instead

Wait on the **system's own state attribute**, not on text settling:
`pipeline-run-details-status-badge`'s `data-status` flips `In progress` →
`Completed` live while the panel is open. Fail with a message naming the run
("the pipeline run did not complete"), never the element.

## Triage tells

- A step whose duration equals its timeout **exactly** (e.g. 90.4 s vs a
  90 000 ms constant) is a swallowed wait, not slow work.
- A screenshot frozen on `Fetching keys & creds…` = the run had not started;
  it is one frame of a carousel, not a hang signature.
- Never "fix" this by touching the shared helper — 20 caller files depend on it.
  Give the individual spec its own wait.

Related: [[pipeline_run_start_latency_dominates_execution_time]]
