---
name: /credentials/all never reliably reaches networkidle
description: Reload waits on the Credentials list must settle on the list GET response, not wait_for_load_state("networkidle")
type: feedback
aliases: [credentials list networkidle, reload_list, wait_for_network timeout credentials]
tags: [area/credentials, type/flake]
created: 2026-08-22
updated: 2026-08-22
---

## The fact

`BasePage.wait_for_network()` is `page.wait_for_load_state("networkidle", 15s)` and
it **raises**. On `/credentials/all` it times out non-deterministically even when the
page is fully rendered — background traffic keeps the network busy. Observed
2026-08-22 (ELITEA-1964): a `page.reload()` + `wait_for_network()` timed out on one of
two runs, costing a rerun; the page itself was correct both times.

## What to do instead

Settle on the list fetch, which is the real signal that the reloaded page has server
data:

```python
with self.page.expect_response(
    lambda r: (f"/configurations/configurations/{settings.elitea_project_id}" in r.url
               and "section=credentials" in r.url and r.request.method == "GET"),
    timeout=SEARCH_RESPONSE_TIMEOUT,
):
    self.page.reload(wait_until="domcontentloaded")
recover_from_credentials_list_crash(self.page)
```

Shipped as `CredentialsListPage.reload_list()`. `CredentialsListPage.navigate()` still
uses `wait_for_network()` + a first-card wait and has not shown the same failure — the
card wait absorbs it — so this is specifically about reload/absence paths where there
may be no card to wait for.

Related: [[cheapest_honest_credential_for_delete_cases]]
