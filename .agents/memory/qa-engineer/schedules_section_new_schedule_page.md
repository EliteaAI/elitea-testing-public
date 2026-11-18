---
name: schedules_section_new_schedule_page
description: Pipeline schedules moved to SCHEDULES section + New Schedule page (testids, risk block, interrupt not blocked #2984)
type: project
---

Since EL-7011/#7338 Schedule is gone from the entry-node Trigger dropdown (Webhook too, on DEV 2026-11-18). Create via `pipeline-schedules-section-add` -> `/schedules/create` page. Full handle map in `test-specs/pipelines/_surface.md` § SCHEDULES section.

Gotchas: mode toggle is role=button not tab; cron selects are single-select Autocompletes (no old multi-checkbox mechanics); summary has no quotes; Printer/HITL block (`schedule-risk-block-box`, Save disabled) but saved interrupt_before/after does NOT (#2984); "Open pipeline to change steps" opens a new tab; both platform banners intercept clicks; no Chrome for the Playwright MCP in this env - scripted sync_playwright probes with the storage state worked instead.
