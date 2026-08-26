---
name: Project Context renders three views on two real routes (no ?view= param)
description: Where the toggle, the editor and Save actually live in Settings → Project Context, and why a case text describing one page is stale.
type: project
aliases: [project context, project-context, EnableToggleCard, project background, settings project params]
tags: [area/settings, type/surface-behavior]
created: 2026-08-26
updated: 2026-08-26
---

## The shape

`ProjectContextContent.jsx` switches on **route** + `content` non-empty. `?view=create`
is **retired**; `src/routes.js` has `/settings/project-context` and
`/settings/project-context/edit`.

| View | When | Holds |
|---|---|---|
| Empty state | content empty | Create + Build with AI. No toggle, no editor, no Save. |
| Saved view | content non-empty | Edit with AI / Edit / dot-menu, **the enable toggle card**, rendered markdown. No editor, no Save. |
| Editor | `/edit` | Save + Cancel(create)/Discard(edit) **in the header**, mode tab group, AI button, Import, Copy, line-numbered CodeMirror, char counter. No toggle. |

## The traps

- **The toggle only exists when content is non-empty.** Any toggle test must seed
  content first (API `PUT`). Saving empty content makes the toggle disappear.
- **The toggle has no Save button** — it auto-`PUT`s on change (200), and persists
  across a full reload.
- **Toggle OFF disables the Edit button** but does NOT guard the `/edit` route —
  direct-URL navigation still opens a working editor.
- **A re-created context inherits the previous `enabled`** (`enabled: serverData?.enabled ?? true`),
  so it can come back silently OFF.
- Project **399 "Private"** has edit rights; **"Bugs & Features"** renders
  *"You don't have permission to edit this setting."* — pick the project deliberately.

Related: [[stale_route_broke_merged_project_context_test]] ·
`test-specs/settings-project-params/_surface.md`
