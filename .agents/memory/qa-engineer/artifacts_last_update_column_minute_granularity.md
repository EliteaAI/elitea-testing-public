---
name: Artifacts "Last update" column — exists, minute granularity, row-text read
description: The Artifacts file table DOES render a Last update column; asserting ui_after != ui_before on a fast flow is a latent flake
type: feedback
aliases: [last update column, artifacts timestamp, modified column, lastModified UI]
tags: [area/artifacts, type/flake-trap]
created: 2026-08-21
updated: 2026-08-21
---

## The fact

`EliteaUI/src/pages/Artifacts/component/ArtifactTable.jsx:58-66` renders a `modified`
column labelled **"Last update"**. Older artifacts specs' prose (ELITEA-1831/1832) claims
there is "no UI-visible timestamp column" — **that is stale**; it was read live off the row
on 2026-08-21: `'sample.txt\nText\n32 B\n21-08-2026, 08:40 PM'`.

## The trap

Format is `dd-MM-yyyy, hh:mm a` (`ArtifactTable.jsx:50`) — **minute** granularity, **local**
time (UTC `17:41:10Z` → `08:41 PM` at UTC+3). A flow that seeds and then mutates inside the
same minute renders an **identical string**. So `assert ui_after != ui_before` passes only
because the flow happens to take >1 minute — a latent flake.

Honest shape instead:
1. primary: API `lastModified` strictly newer (`artifact_api.get_file_metadata`);
2. UI carries it through: rendered cell == API value formatted `%d-%m-%Y, %I:%M %p`;
3. granularity-immune backup: file **size** / content changed.

## How to read it (testid-compliant, merged precedent)

No per-cell testid exists and adding `dataCellTestIdPrefix` to `ArtifactTable` would blanket-tag
all four data cells (single prefix prop) — against the scope rule. Use
`ArtifactsPage.get_file_row_text()` (`artifacts_page.py:1848`) + the regex helper in the merged
`automation/tests/ui/artifacts/test_artifacts_file_preview_edit_save.py:71-97`.

Column is width-gated (`hideBelow: 900`); merged specs set `set_viewport_size(1600x900)`.

Related: [[no_playwright_mcp_use_sync_playwright_script]]
