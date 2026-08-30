---
name: AI Providers reload-persistence gotchas
description: Reloading /settings/ai-providers — why BasePage.reload_and_wait() is a #1847 trap, and what must be asserted after the reload
type: feedback
aliases: [reload_and_wait, reload persistence, ai providers reload, networkidle reload]
tags: [area/settings-ai-providers, type/framework-gotcha]
created: 2026-08-30
updated: 2026-08-30
---

## BasePage.reload_and_wait() is a #1847 trap — never spec it

`pages/base_page.py:320` reloads with `wait_until="networkidle"` and THEN calls
`wait_for_network()` — two networkidle waits. Elitea holds a persistent
`/socket.io/` polling transport open on every page, so "500 ms of network
silence" is structurally racy (`.agents/testing.md` § #1847). On any
persist-after-reload case, spec a reload that waits on the product's own
response instead:

```python
with self.page.expect_response(_is_llm_models_response, timeout=NAVIGATION_TIMEOUT) as info:
    self.page.reload()
```

## What a reload must assert on this surface

- `aria-expanded="true"` on `ai-providers-section-llms` BEFORE counting cards —
  accordion content unmounts on collapse, so a collapsed section reads as
  "record missing". Observed live: the first load of a session can arrive with
  LLMs collapsed / TTS expanded from stale `expandSection` route state.
- Presence AND count AND group AND status — a bare presence check passes for a
  duplicate-on-persist or a persisted-but-broken record.
- For the Default tier: there is **no Save button**, so the cold re-read is the
  only thing that distinguishes "persisted" from "optimistically rendered".
  Also assert High-tier/Low-tier are unchanged — all three tiers share one POST
  discriminated only by a `section` field.

Related: [[priority_marker_drift_afs_vs_pytest_mark]]
