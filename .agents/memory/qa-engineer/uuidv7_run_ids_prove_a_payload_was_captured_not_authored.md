---
name: UUIDv7 run-ids prove a payload was captured, not authored
description: Verify stored wire samples by checking UUIDv7 embedded ms against the frame's own timestamps
type: feedback
---

When a PR ships stored product payloads as "captured live" fixtures, the reviewer's
job is to prove capture vs authorship — and a docstring saying "captured" is not
evidence. On Elitea's Socket.IO frames there is a decisive, cheap check.

`agent_tool_end.response_metadata.tool_run_id` is a **UUIDv7**: its first 48 bits are
the creation time in milliseconds. It must agree with the frame's own
`timestamp_start`, which is an independently serialized field. An author writing a
plausible-looking payload will not reconstruct that.

```python
rid = frame["response_metadata"]["tool_run_id"].replace("-", "")
ms  = int(rid[:12], 16)                      # UUIDv7 ms since epoch
ver = int(rid[12], 16)                       # must be 7
uuid_t = datetime.fromtimestamp(ms/1000, timezone.utc)
# assert abs(uuid_t - fromisoformat(rm["timestamp_start"])) < 2 ms
```

Verified 2026-08-27 on ELITEA-1140/#1817: all six stored frames matched to
sub-millisecond (delta +0.000 to +0.001 s), across three separate capture sessions.

Two corroborating cross-checks on the same frames, worth running together:

- **`metadata.toolkit_name` embeds an epoch stamp** (`ConfluenceToolkit1787826883`,
  `Probejira TK1787824330646` — 10- or 13-digit). It must land ~20-40 s BEFORE
  `timestamp_start` — the fixture creating the toolkit, then driving the chat turn.
- **`metadata.display_name` must equal what the project's own fixture builds.**
  Here `managed_toolkit` yields `f"{cfg.display_name} Toolkit {_ts()}"`, and the
  stored frames carry `"Confluence Toolkit 1787826883"` while `toolkit_name` is the
  de-spaced `"ConfluenceToolkit1787826883"` — i.e. the samples came through this
  repo's real fixture path, not a hand-written dict.

Per-tool durations are a soft fourth signal (`timestamp_finish - timestamp_start`):
0.57 s for an empty list, 1.89 s populated, 3.75 s for the rejected call. Authored
payloads tend to carry round or identical durations.
