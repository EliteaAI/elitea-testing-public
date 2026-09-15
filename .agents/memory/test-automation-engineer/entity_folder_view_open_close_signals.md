---
name: Entity-folder view — which signals are real on open, close, reopen
description: Social/entity folders (`?folder=<id>`) — match the filtered list GET by exact ids (transient ids=0), re-opens may fire no request, wait for the header to unmount before re-clicking
type: project
aliases: [social folders, entity folders, folder-item, FolderSection, ids=0]
tags: [area/social-folders, type/waits]
created: 2026-09-15
updated: 2026-09-15
---

## Verified 2026-09-15 (ELITEA-3208/3209/3210, all six entity types)

- **Opening a NON-empty folder fires TWO filtered list GETs**: `…&ids=0&…` first (while
  `folder_items` loads — `useFolderItems` returns `idsQueryParam='0'`), then `…&ids=<csv>`.
  Wait for the GET whose `ids` set == the expected set (`FolderSection.open_folder(expected_ids=…)`),
  never "the first GET with ids=".
- **Re-open / re-close inside one list mount can fire NOTHING** (RTK cache for `folder_items` and
  for identical list-query args). Take open/closed from the URL `folder` param + the header
  (`folder-view-header-count` renders only while selected) and read counts through auto-retrying
  `expect`.
- **Close → reopen race**: the row's onClick closes over the last-rendered `selectedFolderId`; a
  click after the param cleared but before React re-rendered TOGGLES it closed again. Wait for the
  header to be hidden before the next click (`close_folder` does).
- **Deleting the open folder clears the URL param BEFORE the DELETE 204 lands** (optimistic).
- **Zero-entity lists redirect to the create page** (ToolkitsList first-render effect; credentials
  too) — the FOLDERS panel never mounts. Project 399 holds 0 credentials / 0 toolkits, so a
  "needs no entities" case must still seed one. `/mcps/all` did the same redirect intermittently
  with 20 MCPs present (2 hits, second test in a session) — precondition hazard, re-run.
- **Post-delete landing is type-specific**: skills/agents/credentials → bare list (folder closed);
  pipelines/toolkits/mcps `navigate(-1)` → `…/all?folder=<id>` (still open).
  `McpFormPage.confirm_delete()`'s `**/mcps/all` glob never matches that URL.

Where: `automation/components/folder_section.py`, `automation/fixtures/social_folder_fixtures.py`,
`test-specs/social-folders/_surface.md` § Implementation notes.

Related: [[never_assume_a_transition_settled]] · [[playwright_count_never_auto_waits]] · [[positive_existence_wait_cant_assert_negative_transition]]
