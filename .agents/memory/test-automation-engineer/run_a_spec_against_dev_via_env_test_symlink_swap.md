---
name: Run a spec against DEV by swapping the .env.test symlink, never by exporting
description: .env.test beats shell env, so ELITEA_URL=... pytest silently still runs localhost; swap the symlink for a copy+override instead
type: reference
aliases: [run against dev, dev.elitea.ai locally, env.test override, APP_PREFIX /app, deployed env verification]
tags: [area/environment, type/technique]
created: 2026-09-09
updated: 2026-09-09
---

## The trap

`config.py` orders sources `init > .env.test > shell env` (its own docstring says
so, deliberately, to stop a stale exported token winning). So the obvious move for
a "verify on DEV" card —

```bash
ELITEA_URL=https://dev.elitea.ai APP_PREFIX=/app ../.venv/bin/pytest <node-id>
```

— **silently runs against localhost anyway**. No error, no warning. The run looks
legitimate and proves nothing about DEV.

`automation/.env.test` is a *symlink* to the master `../../.env.test`, so editing
it in place edits the shared master — the thing nobody should be mutating.

## The move

Swap the symlink for a private copy carrying the overrides, then put it back.
python-dotenv takes the LAST occurrence of a duplicate key, so appending wins.

```bash
cd automation
test -L .env.test && mv .env.test .env.test.symlink.bak   # moves the LINK, not the target
cat ../../.env.test > .env.test
printf '\nELITEA_URL=https://dev.elitea.ai\nAPP_PREFIX=/app\n' >> .env.test
chmod 600 .env.test
# ... run ...
rm -f .env.test && mv .env.test.symlink.bak .env.test      # restore
```

`**/.env*` is gitignored, so neither file can be committed by accident.

**Verify both ends, don't assume** — one line, and it prints nothing secret:

```bash
../.venv/bin/python -c "from config import settings; print(settings.app_base_url)"
# expect https://dev.elitea.ai/app  before the run, http://localhost:5173 after the restore
```

Auth needs nothing extra: `auth_state` branches on `"localhost" in ELITEA_URL`
(`fixtures/session_fixtures.py:107`), so a non-localhost URL routes it through the
real Keycloak login with `TEST_USER_EMAIL`/`TEST_USER_PASSWORD` automatically.

Related: [[react_dev_only_warnings_do_not_fire_on_deployed_builds]]
