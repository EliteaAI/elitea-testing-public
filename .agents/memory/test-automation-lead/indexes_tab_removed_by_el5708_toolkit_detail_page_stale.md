---
name: RESOLVED — Indexes tab restructure (EL-5947, not EL-5708); page object already reworked
description: HISTORICAL. toolkit_detail_page.py now uses indexes_accordion + wait_for_config_surface(); count_config_tabs() is gone. Landed in 583fa8f1. Nothing to do.
type: project
---

> ✅ **RESOLVED 2026-08-10 (scout) — no action required; de-indexed.**
> The body says the rework is "not yet fixed". It **is** fixed. Verified against
> `automation/pages/toolkit_detail_page.py`: it declares
> `indexes_accordion = LocatorDescriptor(testid="toolkit-indexes-accordion", …)`
> and `count_config_tabs()` has been replaced by `wait_for_config_surface()`,
> whose docstring records the reason. Landed as `583fa8f1
> test(adjust): toolkit-detail tabs restructure (EliteaUI EL-5947)`.
> **The entry also names the wrong ticket** — the code says **EL-5947**, not
> EL-5708. Kept on disk as the record of the drift and its repair.

During the 2026-07-21 run-30 unattended sync (issue #707), merging `origin/main`
into `EliteaUI`'s `automation/testids` produced a real conflict in
`src/pages/Toolkits/EditToolkit.jsx`: our branch still carried the standalone
"Indexes" tab (`data-testid: toolkit-detail-indexes-tab`, `data-tour:
TOOLKIT_TOUR_TARGET_IDS.indexesTab`) that `main`'s EL-5708 "Indexes redesign"
had already deleted — Indexes moved from a separate top-strip tab into an
accordion embedded inside the Configuration tab. Resolved per the
sync-base-branches skill's divergence rule: **main wins**. The UI team's own
EL-5708 commits already carry a replacement testid for the new pattern:
`toolkit-indexes-accordion` (plus 7 siblings: `toolkit-indexes-count`,
`toolkit-indexes-add-button`, `index-card-delete-btn`,
`index-card-open-new-tab-btn`, `index-card-reindex-btn`,
`run-index-accordions`, `create-index-configuration-accordion`).

**Consequence, not yet fixed:** `automation/pages/toolkit_detail_page.py`
(~line 63) still declares `indexes_tab = LocatorDescriptor(testid=
"toolkit-detail-indexes-tab", ...)`. Its only consumer,
`count_config_tabs()` (~line 90, `return
self.configuration_tab.count() + self.indexes_tab.count()`), is asserted
`>= 2` at Step 24 of
`automation/tests/ui/toolkits/test_toolkit_creation_create_bucket_verify_list_files.py:495`
("Expected at least the Configuration and Indexes tabs"). Since the testid no
longer renders, `indexes_tab.count()` → 0 and the method returns 1, so that
assertion will fail the next time this test actually runs. This was confirmed
statically (grep for the testid string + its single consumer) — the sync
routine deliberately did NOT run the full test live (it creates real
buckets/toolkits, long-running, disproportionate for a sync tick) and did NOT
edit the page object (sync-only scope, no test-code edits from that routine).

**Action for whoever next touches this area:** treat as its own small
automation case — update `toolkit_detail_page.py` to locate the new
`toolkit-indexes-accordion` element instead of a second tab, and rework Step
24's assertion to match the accordion-based UI (no longer "count of two tabs
>= 2"). Don't rediscover this by re-deriving it from a fresh failure — this
entry already has the file/line/testid mapping.
