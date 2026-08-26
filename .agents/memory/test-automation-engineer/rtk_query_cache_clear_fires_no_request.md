---
name: RTK-Query cache makes "clear the filter" fire no request
description: Clearing a search/filter input in EliteaUI usually issues NO network request — the unfiltered query is still cached, so expect_response times out
type: feedback
aliases: [clear search no request, expect_response timeout on clear, RTK-Query cache refetch, search filter clear]
tags: [area/ui, type/gotcha]
created: 2026-08-26
updated: 2026-08-26
---

## The trap

An AFS that says "clear the field and wait for the resulting list GET" looks
obviously right and is usually wrong in this app. EliteaUI's lists are RTK-Query
backed: the UNFILTERED query was already fetched on page load, and while the test
is still inside `keepUnusedDataFor` (60 s default) clearing the filter re-selects
that cache entry instead of refetching. `page.expect_response(<unfiltered list
GET>)` then times out at 15 s and the test fails for a non-defect reason.

Confirmed live 2026-08-26 on Settings → Notifications (ELITEA-2264): typing a term
fires a real `search=` GET; clearing it fires nothing at all.

## What to assert instead

- Wait on the **rendered list** (`expect(row_locator).to_have_count(baseline)`),
  not on a response that may never come.
- Keep network evidence by asserting an **absence**: no `search=`-carrying request
  fires while clearing.

## Proving "no request fired" without a sleep

`page.expect_request(<predicate>, timeout=N)` wrapped in
`try/except PlaywrightTimeoutError` — the timeout IS the verdict, and it is a
framework wait, so it does not violate the no-sleeps rule. Bound it comfortably
past the product's debounce (600 ms search debounce → 4 s window). Same shape
works for "clicking this row does NOT mutate anything".

Implemented as `NotificationCenterPage.fill_search_expecting_no_request()` /
`click_row_expecting_no_mark_mutation()`.

Related: [[absence_of_request_assertion_must_wrap_its_trigger]] (the ordering rule these
probes must obey — the trigger goes INSIDE the `with`, which both helpers above do)
