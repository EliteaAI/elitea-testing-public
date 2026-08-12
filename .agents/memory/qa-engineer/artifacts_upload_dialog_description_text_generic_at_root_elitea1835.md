---
name: Artifacts upload-dialog description text is generic (bucket-name-free) at root, only names the bucket in a subfolder
description: ELITEA-1835 found the "Upload files to ..." dialog's separate description Typography (distinct DOM node from the Path field) reads a GENERIC string with no bucket name at all when currentPrefix is empty (bucket root) — it only interpolates the bucket name when a subfolder is active. No testid exists for this element. Also documents a narrower extend-existing shape than ELITEA-1827's precedent: inserting assertions into an EXISTING covering-test code block, not appending a new flow.
type: feedback
---

## The finding

`UploadPathDialog.jsx`'s `descriptionMessage` (`useMemo`, lines 32-42) has three
branches, keyed on `currentPrefix`:

- **empty** (bucket root): `"Files will be uploaded to the selected bucket.
  Optionally, enter a folder path to organize your files. Use "/" to create
  nested folder(s)."` — **no bucket name anywhere in this string.**
- **non-empty, not at max depth**: `Files will be uploaded to "${bucket}/
  ${currentPrefix}". Optionally, enter a subfolder path...`
- **non-empty, at max depth**: similar, with a depth-limit note.

This is a SEPARATE `<Typography>` from the Path `<TextField>` (which DOES
correctly show `"{bucket}/"` at root, confirmed by ELITEA-1824's own shipped
assertion). ELITEA-1835's own case step 11 ("verify the modal description
indicates files will be uploaded to bucket-1/") implicitly assumes the bucket
name interpolates into this description at root — it does not. Filed as
CLARIFICATION [#674](https://github.com/EliteaAI/elitea-testing-public/issues/674)
(reverse-masking guard: live product is deliberate/correct, case text is
stale) — recommend the case's own expected-result text be corrected to
describe the Path FIELD, not this separate description line.

**No testid exists on this element at all** (`UploadPathDialog.jsx` lines
65-73) — specced as `testid needed: artifacts-upload-path-description-text`,
not self-fixed (analyst-slot policy, `.agents/role-overrides.md`).

## Why this was missed by every prior sibling AFS

ELITEA-1808/1824/1826/1832/1827 all touch the SAME dialog extensively (Path
field, prefix, typed suffix, Upload button) but none of them ever asserted
the description line — it simply wasn't in scope for any of their own case
steps. ELITEA-1835 is the first case whose own literal text names the
description as an observable, which is what surfaced the gap.

## Reusable check

When a case's expected-result text names a UI element that's ADJACENT to
one already well-covered by a sibling AFS (here: "the Path field" vs "the
modal description" — visually close, easy to conflate), don't assume
coverage transfers. Read the actual component source for a SEPARATE render
branch/DOM node before concluding "this is basically the same thing the
sibling case already checked."

## Extend-existing shape: insertion into an existing block, not a new appended flow

ELITEA-1827's own extension (Steps 47-54) appended a genuinely NEW flow at
the end of ELITEA-1824's covering test, because 1824 never touched
multi-segment nested paths at all. ELITEA-1835 is different: 1824's own
EXISTING recovery block (the Escape-and-re-open-from-root sequence written
for the #649 workaround, lines 426-454 at analysis time) already reaches
and asserts almost the exact state 1835 needs — Path-field-at-root text,
root placement via the upload PUT's URL, negative-presence in the
subfolder (all already shipped). The correct `extend-existing` shape here
is **two small INSERTIONS into that existing block** (a bucket-selected/
breadcrumb-root assertion right after the existing `click_bucket_row()`
call, and the new description-text assertion alongside the existing
Path-prefix assertion) — not a third appended flow. Reusable heuristic:
before defaulting to "append new steps at the end" (1827's shape), check
whether the covering test's OWN existing code already walks through the
state the new case needs at some interior point — if so, insert there
instead of duplicating the walk.

## Live re-verification of a flagged dedup risk (not just trusting the covering AFS)

The dispatch explicitly asked whether 1824's "isolation check" (reached via
an Escape-and-recovery workaround AFTER first triggering #649 from inside a
subfolder) generalizes to 1835's own literal scenario (a bucket clicked at
root as a genuinely FIRST action, no prior in-session #649 trigger). Rather
than accept the source-reading argument alone (`currentPrefix` only cares
about its current value, not history), this run reproduced the exact
scenario from scratch in a brand-new, pristine bucket that never triggered
#649 in-session — confirmed identical correct behavior (Path field root-only,
PUT lands at root, file absent from subfolder). This is the kind of live,
pristine re-verification `test-case-analysis`'s dedup-proof requirement
exists for — a code-reading argument for behavioral equivalence should still
be checked against a real execution when the dispatch specifically flags it
as a risk.

See `test-specs/artifacts/lextend_upload-flow-file-uploaded-to-bucket-root_ELITEA-1835.md`
for the full AFS.
