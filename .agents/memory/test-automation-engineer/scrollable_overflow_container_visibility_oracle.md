---
name: Scrollable overflow container — is_visible() is not a visibility oracle
description: In an overflow:auto list, a row scrolled far out of view is still is_visible()==True; compare bounding boxes instead.
type: feedback
aliases: [scroll visibility, overflow auto visible, bucket list scrolling, is_visible clipped]
tags: [area/artifacts, type/gotcha]
created: 2026-08-21
updated: 2026-08-21
---

## The trap

Playwright's `is_visible()` means "has a box and is not `visibility:hidden`" —
it says nothing about clipping by a scroll container. In the Artifacts BUCKETS
panel (`overflow-y: auto`, 768 non-virtualised rows, `scrollHeight` 30792 vs
`clientHeight` 755) the LAST bucket row reports `is_visible() == True` while
sitting 30 000 px below the fold.

## The oracle that works

Compare the row's `bounding_box()` with the scroll container's — implemented as
`ArtifactsPage.is_bucket_row_within_panel(name)` /
`bucket_row_offset_from_panel_top(name)` (ELITEA-1822). Both handles are
testids, so it stays locator-policy compliant, and it needs no `evaluate()`
(reading `scrollTop` would trip the fidelity grep and assert an implementation
value instead of the case's observable).

Corollary: "the first item is back at the TOP" needs the offset check too — with
a 755 px band, "somewhere in the panel" is true for any scroll position under
~715 px, so a visibility-only assertion passes on a list that never scrolled back.

## Scrolling mechanics (Chromium, live 2026-08-21)

- `mouse.wheel()` goes to whatever is under the cursor → `page.mouse.move()` onto
  the container first, and it returns BEFORE the scroll applies → settle with a
  polled condition wait, not a fixed sleep.
- **Arrow keys scroll a container with no `tabIndex` and no `onKeyDown`** after a
  plain click inside it (`document.activeElement` stays `BODY`), ~38.7 px/press.
  Never conclude "keyboard scrolling is unsupported" from the source alone.
- Click the container's PADDING GUTTER (`x + 6`), never a row — a row click
  selects/expands that item.

Related: [[../../../test-specs/artifacts/_surface]]
