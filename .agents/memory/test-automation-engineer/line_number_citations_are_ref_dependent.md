---
name: Line-number citations into EliteaUI are ref-dependent
description: Cite the symbol, not the line — main and automation/testids drift, so the same code sits on different lines
type: project
aliases: [line number citation, source citation, file:line, code pointer, cite EliteaUI source]
tags: [area/docs, type/convention]
created: 2026-08-27
updated: 2026-08-27
---

## The problem

A `file.js:NN` citation in a docstring, AFS or `_surface.md` names a line that is only
true **on the ref you happened to read**. `EliteaAI/EliteaUI` `main` and `automation/testids`
routinely differ by unrelated lines above the code you are citing, so the same symbol sits at
different line numbers on each.

Worked case (2026-08-27, ELITEA-1891): a reviewer reading `main` cited
`convertChatConversationMessages.js:26`; I had read `automation/testids` and cited `:25`.
Verified both — the branches differ by one import line near the top:

```
origin/main               -> convertTime declared at line 26
origin/automation/testids -> convertTime declared at line 25
```

**Neither citation was wrong.** Treating it as a correction and "fixing" 25 to 26 would have
made the doc wrong on the branch the dev server actually serves.

## The rule

**Cite the file and the SYMBOL, never the line.** `` `version.helpers.jsx`'s
`formatVersionMeta()` `` beats `` `version.helpers.jsx:6-13` ``. It survives ref drift, survives
any edit above it, and is what a reader greps for anyway.

## The wider lesson

When a review asks you to change a *fact*, verify the fact on both refs before complying — the
disagreement may be real divergence rather than an error. `git show "<ref>:<path>"` is the check.

⚠️ zsh eats `$ref:src/...` as a `:s` history modifier. Quote it: `spec="${ref}:${path}"; git show "$spec"`.
