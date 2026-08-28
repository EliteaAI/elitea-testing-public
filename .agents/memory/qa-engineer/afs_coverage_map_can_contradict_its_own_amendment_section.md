---
name: AFS Coverage Map can contradict its own amendment section
description: Tick Coverage-Map rows against the SHIPPED assertion, never against the AFS's trailing "Implementation notes / AFS amendments" block — they routinely disagree.
type: feedback
aliases: [coverage map drift, AFS amendment section, implementation notes amendment]
tags: [area/review, type/triangulation]
created: 2026-08-28
updated: 2026-08-28
---

## The trap

This project's AFS files carry a trailing `## Implementation notes / AFS amendments`
section that the implementer appends. When an amendment changes *what is asserted*,
the **Coverage Map row above is often left stale** — so the same document says two
opposite things, and a reviewer who ticks the map alone signs off on an assertion
that does not exist.

Worked example (PR #1953, ELITEA-2322, `l2_tools-tab-chart-and-details-table_ELITEA-2322.md`):

- Coverage Map row 5 (line 85): *"header cell tuple + `text-transform: uppercase`
  … asserted both ways"*.
- Step 5 body (lines 51-55): asserts the title-case DOM text **plus** a computed
  `text-transform` read.
- Amendment (line ~193) + shipped code: a single `inner_text()` read of the
  CSS-rendered uppercase tuple. **No `text-transform` assertion exists.**

The sibling case (ELITEA-2324) had the identical drift, was blocked for it, and its
fix round doc-synced its Coverage Map **and** step body. 2322's was not touched —
one fix round can leave the same class undocumented in a sibling case.

## The check

For every `asserted` Coverage-Map row, find the assertion **in the diff** before
accepting the row. When the AFS's amendment block contradicts a row, the row is the
defect: ask for the doc-sync (map row + step body), not just the note.

Related: [[base_page_capture_console_errors_is_url_less]]
