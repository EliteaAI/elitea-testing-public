---
name: UI display-string constants need a source pointer
description: A page-object list of UI display strings silently rots on a product rename — cite the source file + commit so drift is one grep away
type: feedback
aliases: [internal tools enum, module titles, display string drift, EL-6540, internalTools.constants.js]
tags: [area/page-objects, type/maintenance]
created: 2026-09-09
updated: 2026-09-09
---

## The failure mode

`automation/pages/internal_tools.py` held the chat Modules panel's titles as bare
string constants with no pointer to where they came from. EliteaUI
EliteaAI/EliteaUI@79fd2a55 (EL-6540, merged 2026-09-08) renamed several of them and
added two modules; our list went stale in three ways at once — two wrong strings
("Image creation" -> "Image Creation", "Smart Tool Selection" -> "Smart Tools
Selection"), one wrong string plus a wrong enum member name ("Agents & Pipeline
Builder" -> "Agent & Pipeline Builder"), and two modules never added at all
(Skill Builder, Project Context Builder). Card #2111 / ELITEA-0501.

## The fix that generalises

When a page object mirrors a list the product owns, the docstring cites **the source
file and the commit** the values came from:

```
Titles are sourced from EliteaUI
``src/[fsd]/shared/lib/constants/internalTools.constants.js``; several were
renamed by EliteaAI/EliteaUI@79fd2a55 ("[EL-6540] ...", merged 2026-09-08).
```

Re-verification then costs one `grep -n "title" <that file>` instead of a live walk.
Also declare the render ORDER as the member order — that is free documentation and
makes an added module visible as a gap rather than an append.

## The trap this list still carries

A count assertion over such a list (`visible_count >= len(LIST)`) hard-requires every
member. `Image Creation` is gated per-project on the
`ImageGenServiceProvider_ImageGen` toolkit, so it can vanish while the other nine
render; `internal_mcp` / `skill_builder` / `project_context_builder` share one gate
(`useIsMcpVisible()`) and appear or vanish **as a group of three**. Adding a
conditionally-rendered module to a hard-required list is a latent env-dependent red —
check the gate before you add.

Related: [[chat_modules_panel_ask_user_toggle_added]]
