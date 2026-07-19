---
name: Artifacts upload-flow duplicate dialogs and lastModified gap
description: ELITEA-1832 — the Upload-path and Resolve-duplicates modals share one generic testid-less MUI dialog shell; duplicate detection and Cancel are both client-side (zero network calls); no UI "Last update" timestamp exists anywhere, only via the S3 JSON listing endpoint's lastModified field
type: feedback
---

## What was found (ELITEA-1832 analyst pass, 2026-07-19)

Executed the Artifacts upload → duplicate-detection → "Resolve duplicates" →
Cancel flow live against `localhost:5173` (Private project, id 399), 2/2
identical runs.

### 1. Both upload-flow dialogs are one shared, fully testid-less MUI shell

The "Upload files to ..." dialog (opens after selecting files in the native
file-picker, shows the Path field) and the "Resolve duplicates" dialog (opens
after clicking Upload when a filename collision is detected) both render
through the exact same generic dialog component —
`aria-labelledby="variables-dialog-title"` /
`aria-describedby="alert-dialog-description"` on **both**, differing only in
title text/content. Confirmed via
`document.querySelectorAll('[role="dialog"] [data-testid]')` inside each —
**empty array for both**. Neither the Path input, neither dialog's Cancel
button, nor the Resolve-duplicates dialog's Skip/Replace/Keep-both buttons
have any testid. Any future case touching either of these two dialogs will
hit the same gap — check first before re-discovering it.

Because they share the same generic role/aria wrapper, a bare
`[role="dialog"]` locator cannot disambiguate which one is open — testids
(once added) must be scoped to the dialog's own dedicated testid, not the
shared shell.

### 2. Duplicate detection + Cancel are both 100% client-side

Clicking "Upload" in the Upload-path dialog when a duplicate filename is
selected does **not** fire any network request to detect the collision — the
frontend already holds the bucket's current listing in memory (from the
`GET /artifacts/s3/{bucket}?project_id=...&format=json` call made when the
bucket was opened) and diffs the selected filenames against it locally.
Clicking "Cancel" in the Resolve-duplicates dialog likewise fires **zero**
network requests — confirmed via `browser_network_requests` diffed
immediately before/after each click, 2/2 runs. Any assertion waiting on a
network response after either of these clicks will simply time out doing
nothing useful — wait on the dialog's visibility-state transition instead.

### 3. No "Last update"/timestamp field exists anywhere in the Artifacts UI

The file table only has Name/Type/Size/Actions columns; the per-file dot-menu
only offers Download/Delete (no Properties/Details view). A case requiring a
file-timestamp assertion (e.g. "verify original file unchanged with its
original Last update timestamp") is **only verifiable via the API**: the same
`GET /artifacts/s3/{bucket}?project_id=...&format=json` endpoint returns a
`lastModified` ISO-8601 field per file in its `contents[]` array — but
`ArtifactAPI.list_bucket_files()` (`automation/api/client.py:1226`) currently
**drops** everything except `key`. Any case needing a timestamp/metadata
assertion needs either a small enhancement to that method (return full
per-file dicts) or a new `get_file_metadata()`-style method — this is not a
blocker, just a recurring gap worth fixing once rather than working around
per-case.

### 4. Test-data gap: no bucket literally named the case's placeholder exists

Searched all 5 available projects (Private 73 buckets, UI Testing 0,
Elitea Testing Team 6, Elitea Development 16, Bugs & Features 140 — including
the in-app "Search buckets" feature) for a bucket matching ELITEA-1832's
precondition shape (`bucket-1`, containing `sample.txt` but not
`sample.png`). None exists anywhere — the case's bucket name is a case-text
placeholder, not a literal fixture to look up. This project's existing
`artifact_bucket` pytest fixture (`automation/fixtures/data_fixtures.py:455`,
function-scoped, API-created + auto-deleted) is the correct generate-per-test
strategy for any artifacts case with a specific-file-content precondition —
don't go hunting for a pre-seeded bucket matching a case's literal name.
