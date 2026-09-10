---
name: DEV local runs die in page.goto(domcontentloaded) — the page loads, the waiter does not
description: BURSTY, not deterministic (5 clean DEV greens with no shim, 2026-09-10 #2137) and it fires in BasePage.navigate() too, not just session setup — try the plain DEV run FIRST, reach for the commit+wait_for_load_state shim only when it bursts
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

## Correction (2026-09-10, #2137): it is BURSTY — try the plain run first

The section below said "deterministic". **That is true of a burst, not of the class.**
Same day, three DEV invocations of `tests/ui/chat/test_image_creation.py` (2 params)
with **no shim at all**, just the env-file swap:

| Run | Result | Wall |
|---|---|---|
| 1 | 1 failed, 1 passed, 2 rerun — `minimal_prompt` hung **3 attempts in a row** | 251.66 s |
| 2 | **2 passed**, `reruns.json == {}` | 185.38 s |
| 3 | 2 passed, 1 rerun (hung once, retry passed) | 168.21 s |

**9 attempts: 5 clean end-to-end greens on DEV, 4 hangs.**

**Burst ceiling measured 2026-09-10 (#2140, ELITEA-2453): 7 of 9 attempts hung** — same day,
same hazard, nearly double the rate, on a single-test spec. So size a DEV verification at
2-4x nominal wall clock and never assume one invocation per result. Both greens still landed
(one with `reruns.json == {}`), and **0 of 9 attempts showed an assertion failure** — which is
the only reading that matters: `broken` != `failed`. Run 1's
`detailed_description` navigated fine seconds before `minimal_prompt` hung three
consecutive times on the same route. So the hazard arrives in bursts and a whole
invocation can pass clean.

**Operational rule, in cost order:** run DEV plainly first (env-file swap, ~3 min for
a 2-test file). If you get a clean run, you have your fact and the shim was never
needed. Build the `-p` plugin below only when the hangs actually burst and eat the
invocation — it is the cure for a blocked gate, not a prerequisite for touching DEV.
Corollary: **a clean DEV run does not disprove #2156**, and a hang mid-suite does not
mean the shim is now mandatory.

## It also fires INSIDE the test body — a second call site

The traceback below pins it to session setup (`_browser_cookies`, `/`, 15 000 ms).
Three of my four hangs were in **`ChatPage.navigate_to_chat` -> `BasePage.navigate()`**
at the 30 000 ms budget, on an already project-scoped deep link with no 302:

```
Page.goto: Timeout 30000ms exceeded — "https://dev.elitea.ai/app/chat/10118", waiting until "domcontentloaded"
Page.goto: Timeout 30000ms exceeded — "https://dev.elitea.ai/app/chat/10119", waiting until "domcontentloaded"
Page.goto: Timeout 30000ms exceeded — "https://dev.elitea.ai/app/chat/10120", waiting until "domcontentloaded"
Page.goto: Timeout 15000ms exceeded — "https://dev.elitea.ai/",              waiting until "domcontentloaded"   # the classic
```

Consequences: a fix scoped to the API fixture would have cured **1 of my 4**
occurrences — the durable fix belongs in `BasePage.navigate()` (which is also
#2124's and #2089's territory, so design the three together). And because these are
raw uncaught errors at a **precondition**, they are never a member of a
sanctioned-RED closed set: the response is re-run/re-gate, never accept 2-of-3.
Allure status is `broken` and the pytest tail shows NOTHING once a retry passes —
evidence lives only in `reports/allure-results/*-result.json`, grep by `fullName`.

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
