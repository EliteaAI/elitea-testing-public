---
name: chat-folder-item-{id} testid needs folderId prop wiring, not just source presence
description: FolderAccordion.jsx's data-testid template only resolves if FolderItem.jsx passes folderId={folder.id} down — that prop was silently dropped by an unrelated merge/refactor on BOTH main and automation/testids, so the testid string existed in source but rendered on zero elements
type: feedback
---

## What happened (ELITEA-2458)

`FolderAccordion.jsx` has (and always had):
```js
data-testid={folderId != null ? `chat-folder-item-${folderId}` : undefined}
```
This looks like a normal, working, committed testid — `git log -S` shows it's
been present since ELITEA-2132 (commit `6fceb3e2`). But the `folderId` PROP
it reads was passed into `<FolderAccordion>` from `FolderItem.jsx` only in
that same original commit, and a later commit (`8147d5c1`, "promote
accumulated data-testids to main") that re-added it after some loss never
actually reached `origin/main` — it sits on an orphaned, never-merged branch
(`testids/promote-20260731`). `automation/testids` independently lacked the
prop too. Net effect: `chat-folder-item-{id}` rendered `data-testid={undefined}`
on every folder, invisibly — 0 of 22 live folders had it. `ChatPage.get_folder_item()`
and everything built on it (`is_folder_expanded`, `expand_folder`,
`delete_folder_via_menu`, `is_conversation_in_folder`, `get_folder_empty_state_text`)
was silently broken, including in the two already-merged tests that use it
(`test_folder_creation.py`, `test_move_conversation_to_folder.py`).

**The AFS's provenance table said "on-automation/testids ✓" for this exact
testid** — technically the DOM ATTRIBUTE TEMPLATE existed in source, but the
prop that populates it did not, so the claim was functionally false despite
being sourced from a real `git grep` hit on the testid string.

## The check that catches this

A `git grep` hit on `data-testid="x"` or a template string proves the JSX
LINE exists — it does NOT prove the attribute ever renders with a real
value. For any DYNAMIC (templated) testid, live-verify a COUNT, not just a
source grep:
```js
await page.locator('[data-testid^="chat-folder-item-"]').count()  // must be > 0
```
If the count is 0 despite matching rows visibly rendering in the UI, trace
the prop chain from the string template backwards to its caller — the bug is
almost always a dropped prop at a call site, not the template itself. Same
regression *class* as #1309 (a `key` dropped from a menuItems array) — this
project has now hit "testid plumbing silently lost across a merge" twice on
the SAME `FolderItem.jsx`/`FolderAccordion.jsx` pair. Treat any chat-folder
testid as worth a live COUNT check, not just a source grep, until this
component pair stabilizes.

Fix filed + landed: issue #1310, EliteaAI/EliteaUI@f5fd23da (one-line
additive `folderId={folder.id}` restore).

(from ELITEA-2458)
