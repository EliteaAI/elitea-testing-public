# Surface digest — Social (entity) folders

_Exploration digest (handle cache, not truth). Created 2026-09-15 by qa-engineer
(analyst) during batch `social-folders-critical` (ELITEA-3208/3209/3210). Verify
every handle as you use it. Implementers may append attributed notes._

**Surface key:** `entity-folders-panel`

## What it is (and is NOT)

Entity folders = `EliteaUI/src/[fsd]/entities/folder/` — the "FOLDERS" panel on the
six private entity lists (agents, skills, pipelines, toolkits & indexes, MCPs,
credentials). It is a **separate implementation from chat folders**
(`features/chat/conversation-list/ui/folders/`, `chat-folder-*` testids,
`chat_page.py` helpers) — never reuse those (broken-testid history #1309/#1310/#1533).

Mount paths (verified 2026-09-15 by `grep -rln FolderSection src`):

| entity type (draw value) | route | folder `entity_type` (API) | list component | mount |
|---|---|---|---|---|
| `skills` | `/skills/all?viewMode=owner` | `skill` | `[fsd]/features/skill/ui/PrivateSkillsList.jsx` | via `components/RightInfoPanel.jsx` |
| `agents` | `/agents/all?viewMode=owner` | `agent` | `pages/Applications/PrivateAgentsList.jsx` | via RightInfoPanel |
| `pipelines` | `/pipelines/all?viewMode=owner` | `pipeline` | `pages/Pipelines/PrivatePipelinesList.jsx` | via RightInfoPanel |
| `mcps` | `/mcps/all?viewMode=owner` | `mcp` | `[fsd]/features/mcp/ui/list/AuthorMCPList.jsx` | via RightInfoPanel |
| `toolkits_and_indexes` | `/toolkits/all` | `toolkit` | `[fsd]/features/toolkits/ui/list/ToolkitsList.jsx` | direct `FolderSection` |
| `credentials` | `/credentials/all` | `configuration` | `pages/Credentials/CredentialsList.jsx` | direct `FolderSection` |

**Executed live:** `skills` (all three cases, every step) and `credentials`
(spot-check: panel, create dialog, folder item, open/empty-state/header, close).
Handles were byte-identical on both mount paths.

## Folder-view state lives in the URL — the strongest observable

`useFolderView.hooks.js`: the open folder is `?folder=<id>` (a search param, kept
alongside `viewMode=owner`). Open = param set; close = param deleted; **deleting
the open folder calls `closeFolder()`** (`onFolderDelete`) so the param is deleted
too. Clicking the already-open folder item toggles it closed.

Observed timings (localhost, DEV backend): close → param gone in **14 ms**; delete
open folder → param gone in **~700 ms** (after the DELETE 204).

## Backend traffic (all under `${ELITEA_API_BASE}` = `/api/v2`)

| Action | Request | Notes |
|---|---|---|
| panel load | `GET /social/folders/prompt_lib/{pid}?entity_type=<type>&include_counts=true` | `{total, folders:[{id,name,entity_type,meta,entities_count,...}]}`; counts come ONLY with `include_counts=true` — the MoveToFolder menu fires the same URL without it |
| create folder | `POST /social/folders/prompt_lib/{pid}` body `{name, entity_type, meta}` → **201** `{id, name, entity_type, ...}` | the id in the 201 body is the `folder-item-{id}` key — capture it from the response, never from DOM text |
| open folder | `GET /social/folder_items/prompt_lib/{pid}/{fid}?sort_by=name&sort_order=asc&limit=100&offset=0` → `{total, items:[{entity_id,...}]}` then the entity list `GET .../<entities>/prompt_lib/{pid}?...&ids=<csv>&limit=20` | **empty folder ⇒ `ids=0`** (sentinel, `useFolderEntities.hooks.js`) |
| close folder | entity list `GET` re-fired **without** `ids=` | this absence is the "complete unfiltered list" oracle |
| move to folder | `PUT /social/move_to_folder/prompt_lib/{pid}` body `{entity_type, entity_id, folder_id}` → 200 `{"message": "Skill moved to folder", ...}`; then `GET /social/folders/...include_counts=true` | count in the panel updates on that refetch (~600 ms) |
| remove from folder | same PUT with `folder_id: null` → 200 `{"message": "Skill removed from folder", "folder_id": null}` | |
| delete folder | `DELETE /social/folder/prompt_lib/{pid}/{fid}` → **204** | optimistic cache patch clears `folder_id` on cached entity rows |
| entity rows | every list row carries `folder_id` / `folder_name` (null when unfiled) | "unfiled" ground truth |

## Handles (all `on-main ✓` unless marked; verified `git fetch origin` 2026-09-15)

| Element | Handle | Provenance | Notes |
|---|---|---|---|
| Create-folder button (panel header) | `folders-panel-create-btn` | on-main ✓ | `FolderSection.jsx:165` |
| Create/Edit dialog | `create-folder-dialog` | on-main ✓ | `Modal.BaseModal` |
| Folder name input | `create-folder-name-input` — **lands on the MUI TextField ROOT `<div>`**, the `<input>` is a descendant | on-main ✓ | `fill()` on the root throws; bind a class constant `CREATE_FOLDER_NAME_INPUT_FIELD = '[data-testid="create-folder-name-input"] input'` (precedent `oauth_auth_modal_page.py:91`) |
| Save / Cancel | `create-folder-submit-btn` / `create-folder-cancel-btn` | on-main ✓ | Save disabled while name empty |
| Folder item (row in panel) | `folder-item-{id}` (dynamic, keyed by **id**) | on-main ✓ | text `"<name>\n(<count>)"`; **no `data-*` state attribute** for selected (style only) |
| Folder item count `(N)` | **`testid needed: folder-item-count-{id}`** | needs-adding | `FolderItem.jsx` — the `<Typography variant="labelSmall">({folder.entities_count})</Typography>`; rendered only when `entities_count != null` |
| Folder item "more" (⋮) button | **`testid needed: folder-item-menu-btn-{id}`** | needs-adding | `FolderItem.jsx` `Button.BaseBtn className="folder-more-btn"`; opacity 0 until the row is hovered — hover the row first |
| Folder actions menu | `folder-menu-pin` / `folder-menu-edit` / `folder-menu-delete` | on-main ✓ | `FolderActionsMenu.jsx` (NOT FolderMenuContent) |
| Delete-folder dialog | **`delete-confirm-dialog`** (+ `delete-confirm-button`, `delete-confirm-cancel-button`) | on-main ✓ | ⚠ `DeleteFolderDialog.jsx:53` passes `data-testid="delete-folder-dialog"` but `Modal.DeleteEntityModal` hardcodes its own — **`delete-folder-dialog` is DEAD at runtime**; bind the shared ids. Folder delete needs NO type-to-confirm |
| Folder view header (name + count + close) | close: `folder-view-close-btn` · name: **`testid needed: folder-view-header-name`** · count: **`testid needed: folder-view-header-count`** | close on-main ✓; others needs-adding | `FolderViewHeader.jsx`; header renders only while a folder is open |
| Folder empty state | **`testid needed: folder-empty-state`** — 5 copies, add in ALL: `PrivateSkillsList.jsx:164`, `ToolkitsList.jsx:292`, `PrivatePipelinesList.jsx:201`, `PrivateAgentsList.jsx:192`, `CredentialsList.jsx:250` | needs-adding | text is **`No items in this folder yet`** (no trailing period) — clarification #2302 |
| Card move-to-folder button | `move-to-folder-btn-{entityId}` | on-main ✓ | hover the card first (opacity 0); the `{entityId}` is the entity's id — a per-entity presence oracle too |
| Move-to-folder menu items | **`testid needed: move-to-folder-menu-create-item`**, **`move-to-folder-menu-folder-{id}`**, **`move-to-folder-menu-remove-item`** | needs-adding | `FolderMenuContent.jsx:35/59/105` — "Create Folder" / one row per folder / "Remove from folder" (last one renders only when the entity is filed) |
| Entity cards | `entity-card`, `entity-card-name` | on-main ✓ | list page size 20 (`limit=20`), default sort `created_at desc` ⇒ freshly created entities land on page 1 |
| Toasts | `toast-message`, `toast-alert` (+ `data-severity`) | on-main ✓ | copy: "Folder created successfully" / "Moved to \"<name>\"" / "Removed from folder" / "Folder deleted successfully" — **do not assert copy** (EliteaAI/elitea_issues#6480 open) |
| Skill delete (detail page) | `skill-controls-menu-button` → `skill-delete-menu-item` → `delete-confirm-name-input` (type name) → `delete-confirm-button` | on-main ✓ | lands on bare `/skills/all` (drops `viewMode` AND `folder` params); fires a stale `GET /elitea_core/skill/.../{id}` → 404 console error — #2303 (sibling of credentials #1666) |

## Quirks worth knowing

- `VISIBLE_FOLDER_COUNT = 6` (`FolderSection.jsx:22`): with >6 folders the panel
  collapses behind "Show more". Project 399 had **0 folders in every type** at
  analysis time; specs create one and delete it, so this never triggers — but a
  leaked folder from a crashed run accumulates. Teardown by API is mandatory.
- Card-level delete does not exist on the card grid for skills or credentials;
  the "normal entity delete action" is the detail page's overflow menu. Opening
  the detail page already drops `?folder=` from the URL, so after the delete
  redirect the folder view is closed and the count is read on the panel item.
- The panel's "No folders created yet" text has no testid (not needed by
  3208–3210; do not blanket-add).
- An API-created entity does not appear in an already-mounted list until the
  list refetches — navigate/reload the list page after seeding.

## Evidence (analysis run, skills type)

`test-results/screenshots/ELITEA-3208-step-02-empty-folder-open.png`,
`ELITEA-3208-step-03-folder-closed.png`, `ELITEA-3209-step-01-folder-count-2.png`,
`ELITEA-3209-step-02-folder-open-two-entities.png`,
`ELITEA-3209-step-03-after-delete-open-folder.png`,
`ELITEA-3210-step-01-folder-count-3.png`, `ELITEA-3210-step-02-after-entity-delete.png`,
`ELITEA-3210-step-03-reopen-count-2.png`, `ELITEA-3210-step-04-count-3.png`,
`ELITEA-3210-step-05-count-2.png`, `ELITEA-3208-credentials-empty-folder-open.png`.
