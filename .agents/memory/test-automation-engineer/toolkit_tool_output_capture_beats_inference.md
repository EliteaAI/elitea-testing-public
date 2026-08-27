---
name: Toolkit tool_output shapes must be captured per toolkit, never inferred
description: Each Elitea toolkit's success AND failure tool_output shape is unrelated to its siblings' — infer one from another and you ship a wrong oracle
type: feedback
---

ELITEA-1140 / #1817 proved this twice, on two different toolkits.

**Round 1** — the github success pattern `^Branches in \S+:` was inferred from the
CI *chat message*. Capture refuted it: the real `tool_output` is a JSON array
(`[{"name": …, "protected": …}]`); `Branches in …:` was LLM narration.

**Round 2 (R1)** — confluence's failure shape was reasonably assumed to be
`Failed to list pages: 401 …`, by analogy with github's
`Failed to list branches: 401 …`. Capture refuted that too: it is a prose block
beginning `Tool execution error!\n\nPossible root causes: …`.

Shapes captured live 2026-08-27 (all real calls, localhost:5173 → DEV):

| toolkit | success | failure |
|---|---|---|
| github `list_branches_in_repo` | `[{"name": …, "protected": false}, …]` | `Failed to list branches: 401 {...}` |
| jira `list_projects` | `Found <n> projects:\n[{...}]` | (not captured) |
| confluence `list_pages_with_label` | `[]` (no match) or `[{"id": …, "title": …}]` | `Tool execution error!\n\nPossible root causes: …` |

**How to capture one in ~40 s** (no new tooling): temporarily dump the frames from
inside the spec, run the one parameter, revert.

```python
# TEMP, inside the capture_socketio_frames block, before the Tier-1 assert
import json as _json, os as _os
if _os.environ.get("DUMP"):
    _json.dump(list(frames), open(_os.environ["DUMP"], "w"), indent=2)
```
```
cd automation && DUMP=/tmp/f.json HEADLESS=true ../.venv/bin/pytest \
  "tests/ui/toolkits/test_toolkit_parameterized.py::TestChatWithToolkit::test_chat_with_toolkit[<tk>]" -q
```

To capture a **failure** honestly, corrupt the *credential's* secret in
`toolkit_factories.py` for the run (`token + "-INVALID"`). The remote service
really rejects it, so the payload is real product output — observation, not
simulation. Revert the factory afterwards.
