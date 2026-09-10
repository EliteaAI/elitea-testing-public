---
name: Prove a timing repair with a throwaway routing plugin over the REAL spec
description: A pytest -p plugin that delays or aborts one request runs the actual spec under the failure condition — far stronger than a script that mirrors the spec's logic
type: feedback
aliases: [control plugin, prove the repair, delay the response, abort the POST, reproduce a CI timing red]
tags: [area/gates, type/technique]
created: 2026-09-10
updated: 2026-09-10
---

## The technique

For a repair card whose red is a *timing* or *missing-request* failure, don't re-implement
the spec's steps in a probe script — the probe then proves the probe. Instead drop a
throwaway plugin on `PYTHONPATH` and load it with `-p`, so the **real spec code** runs
under a controlled request condition:

```python
# /tmp/<slug>/ctrl_plugin.py  — never committed
@pytest.fixture(autouse=True)
def _ctrl_route(page):
    def handler(route):
        r = route.request
        if r.method == "POST" and "<the endpoint>" in r.url:
            if BLOCK:
                route.abort(); return          # genuine non-save
            resp = route.fetch(); time.sleep(DELAY)
            route.fulfill(response=resp)       # REAL response, delivered late
            return
        route.continue_()
    page.route("<pattern>", handler)
    yield
```

```
CTRL_DELAY=8 PYTHONPATH=/tmp/<slug> pytest <node-id> -p ctrl_plugin --reruns=0
```

Run three controls and report them as a table — this is what makes a repair *provable*
rather than merely green:

| control | code | condition | expectation |
|---|---|---|---|
| A | **pre-repair** (`git stash push -- <code dir>`) | real response, delayed | reproduces the CI failure verbatim |
| B | repaired | same delay | PASSES |
| C | repaired | request **aborted** | FAILS, at the right step, naming what is missing |

C is the one people skip, and it is the one that proves the repair did not buy green by
going blind.

## Fidelity

Delaying a **real** response is timing control, not substitution
(`.agents/testing.md` § Fidelity policy) — every asserted value still comes from the
system. It stays in `/tmp`, never in the repo, so it cannot reach the committed diff or
the reviewer's substitution grep.

## Make the missing-request red name itself

`page.expect_response(...)`'s native timeout reads only
`Timeout 30000ms exceeded while waiting for event "response"` — it names neither the
request nor the step. Re-raise it:

```python
except PlaywrightTimeoutError as err:
    raise AssertionError(f"No create request (POST .../<path>...) was observed within "
                         f"{TIMEOUT} ms of clicking Save — ... URL: {page.url}") from err
```

Two deliberate side effects: the allure status becomes `failed` instead of `broken`
(nothing keys on it — `conftest.py` keys on `report.outcome`), and the failure leaves
`pytest.ini`'s `--only-rerun "TimeoutError"` bucket, which is right — a request that never
fires is deterministic, not a flake worth retrying.

Related: [[matched_control_run_before_blaming_a_diff]] · [[name_based_teardown_lookup_leaks_when_the_field_truncates]]
