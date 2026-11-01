---
name: Help Center tour links are backend config
description: Help Center tour/doc links come from admin config on DEV; empty list makes ELITEA-3754/2226/2228 time out
type: reference
---

Help Center resource links (incl. `help-center-tour-link-<slug>`) render from
`GET /api/v2/admin/plugin_config_values/prompt_lib/resources` (`resources_*_links`).
On 2026-10-31 DEV had `resources_interactive_tours_links: []` ("No links configured"),
so help_center tour tests fail at `open_resource_link_in_new_tab` — data gap, not drift
(#2808 → question #2830). Check this endpoint first for any help_center timeout.
Factory container has no `.env.test`: export `APP_PREFIX=/app` or navigation hits
`https://dev.elitea.ai/help-center` (404).
