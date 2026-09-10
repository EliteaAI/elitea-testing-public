---
name: DEV local runs die in page.goto(domcontentloaded) — the page loads, the waiter does not
description: Deterministic, not a cold start — goto(wait_until=commit) + explicit wait_for_load_state in a throwaway -p plugin unblocks the whole DEV gate
type: feedback
aliases: [dev goto timeout, domcontentloaded hang, cannot run tests against dev, dev.elitea.ai local run blocked, devenv plugin, navigation shim]
tags: [area/ci, area/environment, type/harness]
created: 2026-09-10
updated: 2026-09-10
---

## The symptom

Every local run retargeted at `https://dev.elitea.ai` dies in **session setup**, before
any test body, in the session-scoped `_browser_cookies` fixture:

```
fixtures/api_fixtures.py:104: in _browser_cookies
    pg.goto("/", wait_until="domcontentloaded")
E   playwright._impl._errors.TimeoutError: Page.goto: Timeout 15000ms exceeded.
```

Both tests ERROR at setup, `--reruns=2` burns every attempt, and the message names
navigation rather than the cause (the #2074/#2076 "wrong subsystem" family).

## It is NOT a cold start, and NOT DEV being down

[[gate_on_the_environment_the_repair_is_FOR]] records this same traceback as a
first-connection cold-start flake that `--reruns=2` absorbs. That reading is
**refuted for the deterministic variant** (2026-09-10, #2121): 6 of 6 attempts,
25 s / 45 s / **60 s** budgets all exhausted, `wait_until="load"` too, and
`/app/` direct (no 302) as well. A single occurrence may still be a cold start —
but if it repeats, stop re-running and read this note.

Measured directly: document responses arrive (`302 /` -> `200 /app/`),
`wait_until="commit"` resolves in **4-7 s**, and afterwards
`document.readyState` goes `interactive` @ t+4 s -> **`complete` @ t+8 s** with
**410 `[data-testid]` nodes** rendered. `page.on("domcontentloaded")` /
`page.on("load")` never fire in 20 s of listening. The app loads fine; the
lifecycle event never reaches Playwright's `goto` waiter. Third-party assets
(`fonts.googleapis`, `googletagmanager`) both 200 in <0.8 s — not the blocker.

## The unblock — transit only, nothing committed

A throwaway `-p` plugin (never a repo edit) that retargets the env AND changes only
**how the harness waits to arrive**:

```python
# /tmp/devenv.py   ->   PYTHONPATH=/tmp:. pytest -p devenv <node-id>
import config
config.settings.elitea_url = "https://dev.elitea.ai"   # .env.test beats shell env, so this is the only way
config.settings.app_prefix = "/app"
from playwright.sync_api import Page
_orig = Page.goto
def _goto(self, url, *, timeout=None, wait_until=None, referer=None):
    want, budget = wait_until or "load", timeout if timeout is not None else 30000
    resp = _orig(self, url, timeout=budget, wait_until="commit", referer=referer)
    if want != "commit":
        self.wait_for_load_state(want, timeout=budget)
    return resp
Page.goto = _goto
```

`PYTHONPATH=/tmp:.` — bare `/tmp` hides the repo's own `config` module. Prove the
target from the plugin banner + the `Authenticating via API against …` INFO line in
each run, never from intent. With it, ELITEA-2070's file ran **3/3 green on DEV**
(74.82 / 112.07 / 99.19 s, `reruns.json == {}`).

No assertion, locator or observable is touched — this is transit, not substitution.
Filed as **#2156**; candidate durable fix is #1847's medicine (wait on what the
caller needs), which is also #2089's scope.

Related: [[gate_on_the_environment_the_repair_is_FOR]] · [[a_duplicate_card_is_where_you_pay_the_originals_evidence_gap]]
