---
name: An absence assertion is only evidence if its detector is proven to fire
description: When reviewing "nothing happened" assertions, verify the detection mechanism fires in the positive case — cite a merged spec that proves it.
type: feedback
aliases: [absence assertion, negative assertion, no download event, vacuous pass, detector validity]
tags: [area/review, type/heuristic]
created: 2026-08-22
updated: 2026-08-22
---

## The trap

A negative assertion (`assert downloads == []`, `to_have_count(0)`, "no toast appeared")
passes both when the product behaved correctly AND when the *detector* was never capable
of firing in the first place. The second case is a silent, permanently green hole — the
exact shape the masking hunt exists to catch, but it carries no skip marker and no
weakened `expect`, so the standard greps miss it.

## The check (one grep, do it every time)

Find a **merged** spec that uses the SAME mechanism in its positive form, and cite it.

Worked example — ELITEA-1842/1843 (`test_artifacts_download_cancel_zip_progress.py`),
which proves "no ZIP was saved" via `page.on("download", …)` + an empty list. The ZIP is
handed to the browser through a blob-URL anchor (`anchor.download = "{bucket}.zip";
anchor.click()`), and it is NOT self-evident that Playwright emits a `download` event for
that shape. It does — ELITEA-1840 `test_artifacts_download_multiple_files_zip.py:250,316`
captures the identical flow with `page.expect_download()` and asserts
`suggested_filename == f"{bucket_name}.zip"`. Detector validated, assertion is real evidence.

Had no such positive-case spec existed, the correct verdict is not CHANGES_REQUESTED on the
assertion itself but a demand for the detector's proof — e.g. a same-spec positive control,
or a cited live observation of the event firing.

Related: [[afs_axis2_claim_needs_grep_not_just_row_presence]]
