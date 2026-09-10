---
name: Swap .env.test for a DEV gate inside ONE detached script with a restore trap
description: The file is a symlink to a MASTER shared by all four sibling clones — a session that dies mid-gate leaves the whole workspace pointed at DEV
type: insight
aliases: [env.test dev swap, symlink sed fails, dev gate setup, ELITEA_URL swap, restore trap]
tags: [area/gate, area/dev-env, type/procedure]
created: 2026-09-10
updated: 2026-09-10
---

## Why bare shell steps are wrong

`.agents/testing.md` already warns that `sed -i ''` cannot edit `automation/.env.test`
(it is a **symlink**; BSD sed refuses, exits non-zero, and the gate then runs against
localhost producing greens that certify nothing). It does not warn about the second
hazard: the symlink target is the **master env file shared by every sibling clone**, so an
agent session that dies between swap and restore leaves the entire workspace on DEV.

## The shape that works (used for #2149, 3/3 clean, verified restored)

Put the swap, **all N pytest invocations**, and the restore in ONE detached script whose
`trap` fires on EXIT/INT/TERM — then the restore survives a killed session or a failed run:

```bash
REAL=$(python3 -c "import os;print(os.path.realpath('.env.test'))")
cp "$REAL" "$BAK"; trap 'cp "$BAK" "$REAL"' EXIT INT TERM
# …python re.sub ELITEA_URL=https://dev.elitea.ai / APP_PREFIX=/app in "$REAL"…
TARGET=$(../.venv/bin/python -c "from config import settings; print(settings.app_base_url)")
[ "$TARGET" = "https://dev.elitea.ai/app" ] || exit 2      # REFUSE to run otherwise
```

- The **`exit 2` guard is the load-bearing half** — without it a failed swap yields
  localhost greens labelled as a DEV gate.
- Echo `settings.app_base_url` **again after the restore** — that is the only proof the
  workspace is back on `http://localhost:5173`. Do it before your final message.
- Launch with `nohup … &`, then wait in bounded `sleep`/`tail` slices (factory delta 5).
