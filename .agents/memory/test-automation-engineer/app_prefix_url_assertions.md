---
name: APP_PREFIX-unsafe URL assertions are green on localhost, red on every deployed env
description: Hardcoded absolute URL paths in tests pass locally and fail structurally in GHA — parameterise by settings.app_prefix
type: feedback
aliases: [app_prefix, APP_PREFIX, url path assertion, /app prefix, deployed env only failure]
tags: [area/ui-tests, type/pitfall]
created: 2026-08-28
updated: 2026-08-28
---

## The trap

`config.py` sets `app_prefix = ""` on localhost and `/app` on deployed envs (DEV/STAGE/NEXT,
where React Router uses `basename="/app"`). A test asserting a **hardcoded absolute** URL path
is therefore green locally and **structurally red on every deployed env** — it can never have
passed in GHA. The local run cannot reproduce the failure, so don't claim it did.

Seen: ELITEA-2020 / issue #1889 / PR #1918.

## The fix shape (keeps assertion strength)

```python
from config import settings

# exact-equality, both envs
assert url_path == f"{settings.app_prefix}/pipelines/create"

# anchored regex, both envs
re.match(rf"^{re.escape(settings.app_prefix)}/pipelines/all/(\d+)$", url_path)
```

Do **not** weaken to `.endswith(...)` / `in` to make it pass — that is masking. Precedent:
`pages/chat_page.py:1738`, `tests/ui/admin/test_notification_link_navigates_to_conversation.py:299`.

## Two things that cost time here

- **Anchors come in pairs.** Fixing only the first assertion just moves the failure to a later
  step. Grep the WHOLE test body for `"/`-prefixed path literals before declaring done.
- **`ruff --stdin-filename` is a false baseline.** Checking a pristine file via stdin reported
  "All checks passed" while the same content at its real path reported 18 pre-existing E501.
  For a lint before/after comparison, write the pristine file to the **real path**, or you will
  wrongly believe you introduced errors.

Related: [[project_briefing]]
