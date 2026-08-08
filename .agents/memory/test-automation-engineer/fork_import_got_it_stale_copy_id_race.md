---
name: Fork/Import "Got it" stale copy-id race
description: ELITEA-2051 — after clicking "Got it" on the Fork/Import Complete dialog, the detail page's copy-id testid can briefly still show the PREVIOUS entity's id/text before the SPA refetch lands — wait for it to settle, don't trust it immediately
type: feedback
---

## The bug that cost a debug round

`AgentDetailPage.confirm_fork_complete()` / the new
`PipelineDetailPage.confirm_fork_complete()` click "Got it", wait for the URL
to change to `/{entity}/all/{new-id}`, then `wait_for_network()`. That is
NOT enough: "Got it" is a client-side SPA navigation (the detail page
component stays mounted, only its data/route param changes), so the
`copy-id` testid element can still show the PREVIOUSLY-viewed entity's text
for a beat after the URL has already updated. A test that reads
`get_pipeline_id()`/`get_agent_id()` immediately after `confirm_fork_complete()`
returns races this refetch and gets a stale/wrong value (observed live,
ELITEA-2051: URL correctly showed the new forked id `8244`, but
`get_pipeline_id()` returned `'161'` — a leftover value, not even the
source pipeline's own id).

## Fix — poll for the ID text to actually match, inside the page-object method

`PipelineDetailPage.confirm_fork_complete()` now does, after parsing the id
from the URL:

```python
from playwright.sync_api import expect

expect(self.copy_id_button).to_have_text(str(forked_pipeline_id), timeout=timeout)
```

(Round-1 review fix, ELITEA-2051: the FIRST version used a raw
`page.wait_for_function()` with a `document.querySelector('[data-testid="copy-id"]')`
JS string — same observable, but it duplicated the existing `copy_id_button`
`LocatorDescriptor` field via a method-body-constructed selector, and it
survived the self-check + round-1 review because the standard mechanical
grep only matches Python `.locator(`/`get_by_*` calls, not selectors embedded
in a JS string. See `mechanical_grep_misses_js_string_embedded_selectors.md`.
`expect().to_have_text()` is both the policy-compliant AND the simpler form —
prefer it over `wait_for_function` whenever the condition is a plain
Playwright assertion.)

This makes the method's own return value trustworthy — callers no longer
need to add their own settle-wait before reading ID/Version-ID fields.
`AgentDetailPage.confirm_fork_complete()` does NOT have this guard yet (its
ELITEA-1893 test never re-reads the agent id via a UI element after the
fork-complete navigation — it only compares the URL-parsed id against the
source id) — if a future case needs to read `get_agent_id()` right after
`confirm_fork_complete()`, port this same wait first.

## Where else this pattern likely applies

Any method that clicks something producing a client-side SPA route change
to another detail page of the SAME entity type (import-complete, version
switch, "Save As Version") and then immediately reads a testid'd field that
displays entity-identifying data should suspect this race if the value
looks stale/wrong rather than simply absent — the field IS in the DOM, it's
just not refetched yet.
