---
name: generated-entity-chip canvas chrome has no dedicated page object per entity type yet
description: Agent/Pipeline/MCP each got their own *CanvasPage for in-chat chrome; newer entity types (Project Context, Skill, Toolkit) opened via the shared generated-entity-chip do not — add one, mirroring McpCanvasPage's shape (title + close_button, xpath-scoped off the entity's own existing content testid), don't bolt it onto the entity's non-chat form/page object.
type: feedback
---

## What happened (ELITEA-3368)

The AFS flagged this as an open declared-improvisation question: "no existing
precedent names which page object should own a NEW entity's in-chat canvas
chrome when that entity's 'form' page object already exists for a non-chat
host." For Project Context, `ProjectContextPage` already owns the Settings
page's own chrome (`project-context-save-button`, etc.) — but the IN-CHAT
canvas (`EditorHeader.jsx`/`BaseEditor.jsx`) is a structurally different
component tree with no testid on its title or close button for this
entity's chat-canvas call site.

## The pattern (now established, reuse it)

Add a **new, minimal page object** named `<Entity>ChatCanvasPage` (e.g.
`ProjectContextChatCanvasPage`) that owns ONLY the canvas chrome — mirrors
`McpCanvasPage`'s shape exactly: `title` + `close_button` fields,
`wait_for_open()`/`close()` methods. Compose it alongside the entity's own
existing page object (`ProjectContextPage(page)`) on the SAME `page`, same as
`AgentCanvasPage` + `AgentFormPage`. Do NOT add the canvas's close button as
a field on the entity's own non-chat page object — that page object's
testids are shared with a different host (the standalone Settings page),
and the canvas chrome belongs to a structurally distinct subtree
(`BaseEditor`/`EditorHeader`), not that page's own markup.

## Locating title/close_button when BOTH are testid-less

Confirmed live for Project Context: `EditorHeader.jsx`'s title Typography
and close IconButton get `data-testid` ONLY when the call site passes
`titleTestId`/`closeButtonTestId` — most existing in-chat canvases (Agent,
Pipeline, MCP) HAVE these wired; a newer one (Project Context, as of this
session) does not. When neither prop is wired, declare BOTH as `xpath=`
rungs scoped off the entity's own already-testid'd content element's `<form>`
ancestor (`BaseEditor`'s own Formik `<Form>` — one per open canvas):
- title: `.../ancestor::form//*[contains(@class,"MuiTypography")][normalize-space(text())="<Entity Name>"]`
- close_button: same title-text predicate, then `/parent::*/preceding-sibling::button`
  (EditorHeader.jsx's own structure: the close IconButton is a direct
  preceding sibling of the Box wrapping the title Typography, inside the
  same `titleSection` container) — this is a structural relationship, not a
  position/index pick, so it passes the no-positional-selector validator.

## Why this is worth remembering

The `generated-entity-chip` mechanism (ELITEA-3368) is shared across Agent/
Pipeline/Toolkit/Skill/Project-Context — the NEXT entity type whose chip gets
exercised (Skill or Toolkit) will very likely hit the same "no dedicated
canvas-chrome page object, no testid on title/close" situation. Reuse this
pattern directly instead of re-deriving it.
