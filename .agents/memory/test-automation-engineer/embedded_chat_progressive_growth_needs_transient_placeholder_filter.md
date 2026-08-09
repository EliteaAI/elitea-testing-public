---
name: Embedded-chat progressive-growth check needs a transient-placeholder filter
description: A naive "poll get_embedded_chat_last_message(), assert length grows" check can be fooled by a placeholder SWAP (shorter loading text -> longer loading text) before real content starts
type: feedback
---

## What happened (ELITEA-2017, implementer, 2026-08-09)

`PipelineDetailPage.get_embedded_chat_last_message()` returns whatever text
is currently in the DOM for the last message — including transient
loading/status placeholders ("Waking the agent…", "Packing its tools…",
"Thought for `<n>` secs"), which are non-empty and NOT the real streamed
response. A first implementation sampled `sample_1 = get_embedded_chat_last_
message()` right after sending, then polled for `len(sample_2) > len(sample_1)`
— and failed on a live run because `sample_1` was `"Waking the agent…"`
(18 chars) and `sample_2` was `"Packing its tools…"` (19 chars, a DIFFERENT
placeholder, not real content growth). The superset assertion
(`sample_1 in sample_2`) correctly caught this as a real bug in the check,
not a flake to retry past.

`ChatPage` already has exactly this filter (`TRANSIENT_MESSAGES` +
`_is_transient_message()`, used by `wait_for_message_content_stable()`) —
but `PipelineDetailPage`'s embedded-chat methods had no equivalent, because
no prior case had needed a progressive-growth check on this surface.

## Fix

Added `PipelineDetailPage._is_embedded_chat_transient_text()` (same known
vocabulary as `ChatPage._is_transient_message` — nbsp-normalizing lowercase
match against "waking the agent"/"thinking" + dynamic "thought for "/
"packing...tool" patterns) plus two new condition-wait methods that both
filter through it:
- `wait_for_embedded_chat_real_content(timeout)` — returns the FIRST
  non-transient, non-empty sample. Use this for the baseline, never a raw
  `get_embedded_chat_last_message()` call, on any surface that shows a
  loading placeholder before real content.
- `wait_for_embedded_chat_body_growth(previous_length, timeout)` — polls for
  growth PAST `previous_length` while also rejecting transient samples, so a
  placeholder swap mid-poll can't masquerade as content growth either.

Duplicated the vocabulary rather than refactoring `ChatPage`'s private
attribute into a shared `BasePage` helper — `ChatPage` has many merged
callers and this fix didn't need to touch it; if a THIRD page needs the same
filter, that's the trigger to promote it to `BasePage`.

## Rule of thumb

Any "poll a page's rendered response text, assert monotonic growth" check
on a NEW page/component needs its own transient-placeholder audit before
trusting length-only growth — don't assume the analyst's live manual
polling (which naturally samples past the placeholder phase without
noticing it) generalizes to an automated tight-interval poll, which WILL
land inside the placeholder window often enough to matter.
