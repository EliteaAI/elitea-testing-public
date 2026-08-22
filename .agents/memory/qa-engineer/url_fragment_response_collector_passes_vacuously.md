---
name: URL-fragment response collectors can pass vacuously
description: A page.on("response") collector filtered only by a URL substring is satisfied by unrelated GETs; assert method/scope too.
type: feedback
aliases: [response collector, page.on response, upload assertion, vacuous assertion]
tags: [area/review, type/assertion-strength]
created: 2026-08-22
updated: 2026-08-22
---

## The trap

A spec proving "the file really left the browser" often arms
`page.on("response", ... if "/attachments/" in response.url)` and later asserts
`assert upload_statuses` + `all(status < 300)`.

That filter matches **any** request whose URL carries the fragment — including
GETs the app fires while *restoring* a previous conversation that already has
attachments. On a suite that deliberately leaves its data behind (Support
Assistant, chat), runs 2..N can populate the collector without any upload
happening, so `assert upload_statuses` becomes vacuous and `all(status < 300)`
grades unrelated traffic.

## What to require at review

Scope the collector by **method** (`response.request.method == "POST"`) and,
where available, by the entity id in the path (conversation uuid). Then the
assertion can only be satisfied by the action under test.

Not automatically a blocker: judge whether an independent, non-vacuous
assertion carries the same claim (e.g. the outbound predict frame containing
the filename). If one exists, this is a strength finding, not a false green.

First seen: ELITEA-2421 / PR #1654 (support-assistant attachment send).

Related: [[expect_soft_failure_is_a_real_red]]
