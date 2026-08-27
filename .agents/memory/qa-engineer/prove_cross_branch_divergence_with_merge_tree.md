---
name: Prove cross-branch divergence with git merge-tree
description: Read-only 3-way merge simulation — turns "this might conflict later" into evidence, no checkout, no worktree
type: feedback
---

Reviewing a branch that **ports code from one long-lived branch to another**
(this repo: `automation/base` ⇄ EliteaUI-style `main`) always raises the question
*"will this collide at the next promotion?"*. Do not speculate — simulate:

```bash
git merge-tree --write-tree HEAD origin/automation/base   # rc=1 ⇒ conflict
git show <tree>:<path> | grep -n '^<<<<<<<\|def <symbol>'
```

It performs a real 3-way merge **in memory**, writes the result to an object
tree, and returns rc=1 on conflict. Nothing is checked out, nothing moves — so
it is fully compatible with the no-worktrees ruling AND with the static-reviewer
contract (no execution of the suite).

Worked case (ELITEA-1140/#1817, 2026-08-27): a `ChatPage.capture_websocket_frames()`
delegator was ported from `automation/base` to a `main`-targeted branch,
**byte-identical body** but at a different anchor (EOF vs mid-class, because
base's neighbouring HITL code does not exist on main). Byte-identity looked like
"zero divergence"; the simulation produced 3 conflict regions in `chat_page.py`
and **two** `def capture_websocket_frames` in the merged blob. Identical CONTENT
at a different ANCHOR is still divergence — git merges by position.

Cheapest fix for that shape: don't add the delegator to the shared page object at
all — have the spec import the underlying util directly. An identically-added
whole FILE merges clean; an identically-added METHOD at two anchors does not.
