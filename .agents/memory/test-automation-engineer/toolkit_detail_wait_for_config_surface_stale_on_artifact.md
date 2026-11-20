---
name: toolkit detail navigation quirks
description: ToolkitDetailPage.wait_for_config_surface times out on fresh artifact toolkits; navigate_to_toolkit works; set APP_PREFIX=/app when .env.test is absent
type: reference
---

- `ToolkitDetailPage.navigate_to_toolkit(id)` + `open_test_surface()` works for an API-created artifact toolkit; `wait_for_config_surface()` (indexes panel) timed out (15s) there, so ELITEA-4758 skips it and waits on `test_button` instead.
- Without `automation/.env.test` the app prefix defaults to empty -> 404 page; run with `APP_PREFIX=/app`.
