---
name: capture_websocket_frames / utils.websocket_frames live on automation/base, NOT on main
description: A fix branch cut from main has no Socket.IO frame collector — port the FILE verbatim, never the page-object method
type: project
---

`automation/utils/websocket_frames.py` and `ChatPage.capture_websocket_frames()`
exist on **`automation/base`** only. A repair branch cut from **`main`** (the base
for fixes to already-promoted tests) does not have them, even though AFS files
written against the working tree assume they do.

**Port the FILE. Never port the METHOD.** Corrected 2026-08-27 by a reviewer on
`fix/ELITEA-1140-toolkit-chat-error-oracle` — the first pass ported both, and:

- an identically-added **file** merges clean (add/add, same content);
- an identically-added **method** does NOT. Git merges by position, and base
  places `capture_websocket_frames` mid-class after `_wait_for_sensitive_action_panel`
  (HITL code absent from `main`), so a main-cut branch appends it at EOF. Result:
  `CONFLICT (content) in automation/pages/chat_page.py`, and a human resolving by
  taking both sides ships **two** definitions (ruff `F811`, second wins silently).

So: `git show origin/automation/base:automation/utils/websocket_frames.py` verbatim,
and have the spec call `capture_socketio_frames(page)` **directly**. Bonus — the
branch then touches no shared page object at all, dropping blast radius to zero.

**Prove it, don't assume it.** Before handoff on any main-cut branch:

```bash
OUT=$(git merge-tree --write-tree HEAD origin/automation/base); echo "rc=$?"
echo "$OUT" | grep CONFLICT
git show "$(echo "$OUT" | head -1)":<path> | grep -c 'def <method>'   # must be 1
```

⚠️ Two traps that cost time here: in zsh use `"${TREE}:path"` — bare `$TREE:a…`
hits the `:a` parameter modifier; and a **stray trailing newline** is enough to
keep a "reverted" file conflicting (`git show origin/main:<path> > <path>` is the
reliable revert). Memory-file conflicts in that same output are the documented
add/add class, not your code.
