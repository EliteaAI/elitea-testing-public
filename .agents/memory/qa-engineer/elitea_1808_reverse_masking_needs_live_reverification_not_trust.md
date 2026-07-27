---
name: Reverse-masking claims need live re-verification, not a trust check
description: An AFS's "the UI has no column X / product diverges from case-text" claim is a factual assertion about the live system — the reviewer must independently re-verify it at a normal viewport, not just check whether the CLARIFICATION-vs-Bug classification is internally consistent with the AFS's own premise. A narrow exploration viewport is enough to hide a real table column and misfile a false CLARIFICATION.
type: feedback
---

## What happened (PR #643, ELITEA-1808 round-2 reviewer pass)

The AFS and the shipped test both claimed: *"confirmed live the file table has
exactly four columns (Name/Type/Size/Actions), no visible upload/last-modified
timestamp anywhere in this UI"* — and treated the TMS case's step-16
"...with correct file type, size, and timestamp" requirement as case-text
drift, filing CLARIFICATION [#642](https://github.com/EliteaAI/elitea-testing-public/issues/642)
instead of asserting it.

**This was false.** Navigating live at a normal desktop viewport (1600×900)
showed a real 5th column, "Last update", populated with a real timestamp.
DOM confirmation via `evaluate` on the `artifacts-file-row` element:
`cellTexts: ["", "test.txt", "Text", "60 B", "19-07-2026, 08:42 AM", ""]` — 6
real cells, not a tooltip or aria-only artifact.

Root cause: the analyst's own exploration screenshot
(`ELITEA-1808-step15-16-upload-complete-file-visible.png`) was taken at a
narrower viewport that visually clips the 5th column off-screen. Nobody
scrolled or resized to check. A real column was misread as absent.

The kicker: the shipped test's own `get_file_row_text()` — already called at
Step 16 to check Type/Size — returns the FULL row text including the
timestamp segment. Confirmed via my own live `--log-cli-level=INFO` run:
`'test.txtText60 B19-07-2026, 08:42 AM'`. The data was already in hand; the
code just never asserted the trailing segment.

## Why round 1 missed this

Round 1's review explicitly praised the handling: *"The known timestamp-column
absence is correctly handled as CLARIFICATION #642... no reverse-masking."*
That's a coherent-sounding check — it confirmed the AFS's own internal
classification (CLARIFICATION, not silently-dropped, not falsely-asserted)
was self-consistent. But it never independently re-verified the *underlying
factual claim* ("four columns, no timestamp") against the live UI. It trusted
the AFS's premise and only audited whether the premise was handled
correctly — not whether the premise was true.

## The generalizable check

The reverse-masking guard (`test-automation-workflow` skill) documents
weakening an assertion *toward* stale case-text when the product *correctly*
diverges. This is the mirror-image failure: treating the product as having
diverged when it actually hasn't — a false "case-text drift" call. Both
directions require the SAME fix: **the reviewer must independently observe
the live system**, not just check that the AFS's own classification logic is
internally consistent.

Concretely, whenever an AFS or test comment asserts a negative product claim
("no timestamp column," "the button doesn't exist," "this field is read-only
in this state") as the basis for skipping an assertion or filing a
CLARIFICATION instead of asserting: **re-drive the live surface yourself at a
normal viewport/state before accepting it.** A narrow viewport, a stale
screenshot, or an unscrolled panel is enough to manufacture a false negative
that then compounds — it degrades a real test assertion AND files a
misleading ticket that other cases (here, the sibling ELITEA-1832, per #642's
own text: "the same gap was independently observed during ELITEA-1832's
analysis") will cite as confirmed fact without re-checking either.

(from ELITEA-1808, PR #643 round 2 — https://github.com/EliteaAI/elitea-testing-public/pull/643#issuecomment-5014598007)
