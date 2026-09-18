---
name: Captured wire-frame provenance check (reviewer)
description: How to prove a "captured" agent_tool_end JSON sample was observed, not authored — UUIDv7 vs timestamps, source line numbers, parser key order
type: feedback
---

When a PR ships a `tests/unit/data/*.json` "captured live" payload as an oracle, verify it was
observed rather than authored. Three cheap, independent checks (all passed on PR #2364, 2026-09-18):

1. **UUIDv7 vs the frame's own clocks.** `response_metadata.tool_run_id` on real tool frames is
   UUIDv7: first 48 hex bits = ms since epoch. Decode it (`int(hex[:12],16)`) and compare with
   `timestamp_start`, `timestamp_finish`, `created_at`. A genuine frame agrees to the millisecond
   (`tool_run_id` == `timestamp_start`; `created_at` a few hundred µs after `timestamp_finish`).
   Exception-path frames (`tool_name: "Agent Exception Stacktrace"`) carry a UUIDv4 and no
   `tool_meta`/`metadata` — that is the platform's shape, not a red flag; use check 2 for those.
2. **Traceback line numbers vs live source.** `gh api repos/EliteaAI/elitea-sdk/contents/<path>`
   (read-only, base64) and grep the cited lines — a captured traceback's `api_wrapper.py:47` /
   `:69` must land on the exact statements. Nobody authors matching line numbers.
3. **Payload structure vs the producer.** Read the SDK method that builds the payload
   (`_parse_projects` → `{"id","key","name","type","style"}` in that order, `style` always `""`)
   and confirm the sample's key order / constant fields match. Also cross-check ids against any
   independently pasted evidence (the CI log in the [FIX] card).

Also: toolkit display-name suffixes are epoch seconds (`JiraToolkit1789734344` → 12:25:44Z) and
should sit a few seconds before the tool call. Verify the named upstream commit exists and touches
the producer file (`gh api repos/<org>/<repo>/commits/<sha>`), don't take the changelog on faith.
