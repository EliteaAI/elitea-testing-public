---
name: The branded full-page 500 is a gateway outage, not the feature under test
description: Open the failure SCREENSHOT first — this class names the wrong subsystem in its assertion message every time
type: feedback
aliases: [500 Internal Server Error page, Something went wrong on our end, gateway outage, wrong subsystem]
tags: [area/triage, type/gotcha]
created: 2026-09-09
updated: 2026-09-09
---

Elitea's branded `500 / Internal Server Error / "Something went wrong on our end"` page with
`Go to Elitea` / `Go Back` buttons **does not exist in EliteaUI's source** — it is served by the
layer in front of the app. Seeing it means a platform outage, never an app-level error boundary.

Because page objects wait on an in-page element (`input#name`, a testid, …) rather than on the
navigation's HTTP status, the failure surfaces 15 s later naming a subsystem that was never
involved. Reading the assertion message first costs a session; opening the screenshot costs 10 s.

Confirmed again 2026-09-09 (ELITEA-2002 / `#2077`, nightly 34331579791): attempts 2 and 3 of one
test showed byte-identical gateway-500 screenshots while failing on a
`Page.wait_for_function: input#name has a value` timeout. Sibling cards `#2074` et al. from the
same run were the same outage. `#2089` tracks promoting the fail-fast navigation status guard to
`BasePage.navigate()` suite-wide; until it lands, every page object except `SkillsListPage`
fails this class slowly and misleadingly.

**Corollary:** a same-run sibling `[FIX]` card's root cause does NOT transfer by association.
Check the job's own pass/fail spread — 44 of 47 passing is not an outage shard.

Related: [[caplog_accumulates_across_pytest_reruns]]
