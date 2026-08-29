---
name: expect_response body pruned when a second navigation supersedes the document
description: response.json() raises "Network.getResponseBody: No resource with given identifier found" — re-capture, do not blame the app
type: feedback
aliases: [getResponseBody, No resource with given identifier found, pruned response body, expect_response race]
tags: [area/playwright, type/gotcha]
created: 2026-08-30
updated: 2026-08-30
---

## Symptom

`response.json()` on a response captured with `page.expect_response(...)` around a
navigation raises:

```
playwright._impl._errors.Error: Response.json: Protocol error
(Network.getResponseBody): No resource with given identifier found
```

Deterministic, not flaky (reproduced 2/2 on ELITEA-2406).

## Mechanism

`expect_response` attaches its listener BEFORE the navigation inside the `with` block.
A spec that lands on a page once (e.g. to switch project) and then navigates again to
capture will have requests from the **outgoing** document still in flight — one of them
can be the first match. Once the navigation commits, Chromium discards that document's
network entries, so the body is gone even though `.status` still reads fine.

Bites the LAST-issued requests hardest: earlier ones already arrived and are never
matched by a listener attached after them.

## Fix

Re-capture, bounded. `AIProvidersPage.navigate_and_capture_section_models_json()` is the
worked shape (3 attempts, returns `(response, body)`). Nothing about the assertions
changes — the body is still the product's own response.

Also check TEARDOWN helpers: the same raise inside a `try/except` that swallows made a
restore that had SUCCEEDED report `None`, and the caller then asserted a state loss that
had not happened.

Related: [[ai_providers_section_isolation]]
