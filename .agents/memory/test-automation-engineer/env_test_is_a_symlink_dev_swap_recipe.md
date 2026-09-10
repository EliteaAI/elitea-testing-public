---
name: Swapping the test target to DEV (.env.test is a symlink)
description: Working shell recipe to point runs at dev.elitea.ai and always restore, incl. the settings.app_base_url proof
type: reference
aliases: [dev swap, env.test symlink, ELITEA_URL swap, run against DEV, APP_PREFIX /app]
tags: [area/automation, type/gotcha]
created: 2026-09-10
updated: 2026-09-10
---

## Why it needs a recipe

`automation/.env.test` is a **symlink** to the master `.env.test` in the parent
workspace. BSD `sed -i ''` refuses symlinks, exits non-zero and changes nothing —
so a swap step that uses it fails *silently by omission* and the run happily
targets localhost. And `.env.test` beats shell env (`config.py` orders dotenv
first), so `ELITEA_URL=… pytest` does nothing either.

## The recipe (proven 2026-09-10, ELITEA-1869 / #2145)

Wrap the whole thing in one script so the `trap` always restores — the master
file is shared by every sibling clone and must never be left pointing at DEV.

```bash
REAL=$(python3 -c "import os;print(os.path.realpath('automation/.env.test'))")
BAK=$(mktemp); cp "$REAL" "$BAK"
trap 'cp "$BAK" "$REAL"' EXIT INT TERM
python3 - "$REAL" <<'PY'
import sys, re
p = sys.argv[1]; s = open(p).read()
s = re.sub(r'(?m)^ELITEA_URL=.*$', 'ELITEA_URL=https://dev.elitea.ai', s)
s = re.sub(r'(?m)^APP_PREFIX=.*$',  'APP_PREFIX=/app', s)
open(p, 'w').write(s)
PY
cd automation
TARGET=$(../.venv/bin/python -c "from config import settings; print(settings.app_base_url)")
[ "$TARGET" = "https://dev.elitea.ai/app" ] || { echo "SWAP FAILED"; exit 2; }
```

**The `settings.app_base_url` echo is the non-optional part** — a swap is not
done until the framework's own resolver agrees. The cheap secondary tell is wall
clock: ~11 s/run against localhost vs 45-65 s against DEV.

`ELITEA_PROJECT_ID` is already 399 (the DEV project), so it needs no swap.

Related: [[dev_page_goto_flake_is_a_precondition]]
