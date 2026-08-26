---
name: Project Context page layout vs ELITEA-226x case texts
description: Settings → Project Context has 3 views (empty/editor/saved); the "toggle + Project Background + bottom Save/Discard" layout in the case texts does not exist
type: project
aliases: [project context, project-context, EnableToggleCard, ELITEA-2266, ELITEA-2267, ELITEA-2276, Project Background]
tags: [area/settings, type/case-drift]
created: 2026-08-26
updated: 2026-08-26
---

## What the live product renders (EliteaUI automation/testids @ 62e04b3f, verified 2026-08-26)

`/settings/project-context` → `ProjectContextContent.jsx` picks ONE of three views
(no `?view=` param any more — the editor is its own route
`RouteDefinitions.ProjectContextEdit`):

| View | Component | When |
|---|---|---|
| Empty state | `ProjectContextEmptyState.jsx` | `serverData.content` empty → "Still no Project Context" + `Create` (`project-context-create-button`) + `Build with AI` buttons. **No toggle.** |
| Saved view | `ProjectContextSavedView.jsx` | content non-empty → header (Edit with AI / Edit / DotMenu Copy+Delete) → optional no-permission banner → `EnableToggleCard` (title + description + MUI Switch) → optional "Project Context is turned off…" banner → rendered Markdown. **No Save/Discard, no editor.** Toggle PUTs immediately on change (`handleToggle`), there is no Save step. |
| Editor | `ProjectContextEditor.jsx` (route `/edit`) | Save (`project-context-save-button`) + Cancel/Discard live in the **page header**, gated on `isDirty`. Toolbar = edit/preview TabGroupButton, Build-with-AI or Edit-with-AI, import-markdown icon, copy icon. CodeMirror `contentTestId="project-context-editor-content"`, `project-context-char-counter`. **No toggle card here.** |

`EnableToggleCard` has exactly two consumers: `ProjectContextSavedView` and
`project-general/MidturnInjection.jsx` (re-titled "Mid-turn Input (Beta)").

## Why it matters

TMS cases ELITEA-2266 / 2267 / 2276 describe a single page with a toggle card at the
top, a "Project Background" section (subtitle + Build with AI + upload + `</>` + eye
icons + line-numbered editor) and Save/Discard **at the bottom**. That layout exists
nowhere in the product — it predates EliteaAI/EliteaUI@92fc6f4e
("Feat/el 5888/project context new design", 2026-07-20). Any case in this module
written before that date needs re-analysis against the three-view shape above.

Also: the toggle only exists once content is saved, so any toggle case needs a
**seeded non-empty context** as a precondition, and the acting user needs
`projectContext.edit` permission (project 406 "Bugs & Features" does NOT have it —
banner "You don't have permission to edit this setting.", switch disabled).

Related: [[../../../test-specs/settings-project-params/_surface.md]]
