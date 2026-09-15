---
name: Entity folders panel — handles, dead testid, URL state
description: Entity (social) folders ≠ chat folders; open folder is ?folder=<id>; delete-folder-dialog testid is dead; name input testid sits on the TextField root
type: project
aliases: [social folders, entity folders, FolderSection, folder-item, move-to-folder]
tags: [area/social-folders, type/handles]
created: 2026-09-15
updated: 2026-09-15
---

## What to know before touching the FOLDERS panel on entity lists

- Implementation: `EliteaUI/src/[fsd]/entities/folder/` — mounted on 6 lists (skills/agents/
  pipelines/mcps via `RightInfoPanel`, toolkits/credentials directly). NOT chat folders
  (`chat-folder-*`, `chat_page.py`) — different tree, different API (`/social/folders/...`).
- **Open folder = URL search param `?folder=<id>`** (`useFolderView.hooks.js`). Close deletes it
  (14 ms); deleting the open folder deletes it too (~700 ms after the 204). Best observable.
- **`data-testid="delete-folder-dialog"` is DEAD** — `DeleteFolderDialog.jsx` passes it, but
  `Modal.DeleteEntityModal` hardcodes `delete-confirm-dialog` / `delete-confirm-button`. Bind the
  shared ids. Folder delete has no type-to-confirm.
- `create-folder-name-input` lands on the MUI TextField ROOT div; `fill()` there throws. Use a
  `'[data-testid="create-folder-name-input"] input'` class constant (precedent
  `oauth_auth_modal_page.py:91`).
- `folder-item-{id}` is keyed by id — read the id from the create POST **201 body**.
- Counts `(N)` arrive only on `GET /social/folders/...&include_counts=true`; empty folder list query
  uses the `ids=0` sentinel; "unfiltered" = list GET without `ids=`.
- Empty-state copy is `No items in this folder yet` (no period; 5 copies) — clarification #2302.
- No card-level delete on skill/credential cards; entity delete lives on the detail page, whose
  route already drops `?folder=`; skill delete then fires a stale GET → 404 (#2303, sibling #1666).
- Full digest: `test-specs/social-folders/_surface.md`.

Related: [[project_briefing]]
