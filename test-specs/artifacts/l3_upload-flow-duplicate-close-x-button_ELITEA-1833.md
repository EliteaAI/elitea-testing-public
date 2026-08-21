# Test Case: Upload Flow – Duplicate Handling: Close X Button on Resolve Duplicates Modal

## Metadata
- **TMS ID**: ELITEA-1833
- **Linked Story**: none
- **Priority**: l3 (medium — as authored in the source TMS case)
- **Environment Explored**: local (`http://localhost:5173`, EliteaUI `automation/testids`
  branch → DEV backend, project `Private` / `${ELITEA_PROJECT_ID}`=399)
- **User set**: `${TEST_USER}` (on localhost, `auth_state` fixture skips login via
  `VITE_DEV_TOKEN`)
- **Analyst**: qa-engineer, analyst slot (cluster session with ELITEA-1830, 2026-08-21)
- **Status**: ready-for-automation — all 11 case steps executed end-to-end live, no
  defects found. Not already-covered, not extend-existing — see § Overlap check.

## Overlap check vs existing automation

Closest merged spec: `automation/tests/ui/artifacts/test_artifacts_upload_duplicate_cancel.py`
(ELITEA-1832, `test_cancel_stops_entire_upload_including_non_duplicate`). Read in full
before this run. Why it is **not** coverage for this case:

1. **Different control.** ELITEA-1832 clicks the dialog's **Cancel button**
   (`artifacts-resolve-duplicates-cancel-button`, `artifacts_page.py:2430`). This case's
   step 8 says *"Click the X (close) icon in the top-right corner"* — a different,
   currently **untested and untagged** element.
2. **Different scenario shape.** ELITEA-1832 selects **two** files (duplicate +
   non-duplicate) and its whole point is that the *non-duplicate* is aborted too. This case
   selects **one** file and asserts the original is untouched. Neither spec's assertions
   imply the other's.

**Honest note for the reviewer (source-level, verified):** in the current build the X and
Cancel are wired to the **same** handler — `DuplicateResolutionDialog.jsx` passes
`onCancel` to both `Modal.BaseModal`'s `onClose` (which the X and the backdrop/Escape call)
and to the Cancel button's `onClick`. So the two tests exercise one product path today.
That is an implementation fact, not a coverage fact: the case is written against the X
**control**, the wiring can change without either case changing, and the X is a real,
user-reachable affordance nothing currently asserts. Classified `ready-for-automation`
(fresh spec) rather than `already-covered` per the standing asymmetry — a redundant test is
visible and deletable, a missing one is invisible.

## Preconditions
- User is logged in (on localhost, `auth_state` skips login).
- A bucket exists containing `sample.txt`. **No stable `bucket-1` fixture exists** — the
  case's `bucket-1` is illustrative. Use the `artifact_bucket` fixture and seed
  `sample.txt` via `artifact_api.upload_file(...)`, exactly as ELITEA-1831/1832 do. The
  API seed is **transit only** (declared); every asserted observable is product-produced.
- A local `sample.txt` is available for upload — write it into pytest's `tmp_path`.

## Test Data

### generate-per-test (created in setup, removed by the `artifact_bucket` teardown)
| Field | Value | Notes |
|---|---|---|
| Bucket | `artifact_bucket` fixture (`autotest-*`) | fresh per test |
| Existing file | `sample.txt`, content `ORIGINAL …` (68 B) | seeded via `artifact_api.upload_file` |
| Uploaded file | `sample.txt` (SAME name), **different content and different byte length** | if the X wrongly uploaded, size AND content would both change — makes "unchanged" a strong claim, not a coincidence |

## Test Steps

Live-confirmed behaviour; step numbers map to the TMS case.

| # | Action | Expected (confirmed live) |
|---|---|---|
| 1 | Navigate to Artifacts | Artifacts page loads |
| 2 | Open the seeded bucket | Bucket selected; `sample.txt` visible (`file_exists` → `True`); baseline file count = 1 |
| 3–5 | Click the upload icon, select `sample.txt`, confirm (`upload_files([path])`) | Native chooser opens and resolves inside the one `expect_file_chooser` action; "Upload files to …" modal opens |
| 6 | Verify the modal, click **Upload** | Modal open with the bucket-name prefix; duplicate detection triggers **client-side** (0 network requests) |
| 7 | Verify the "Resolve duplicates" modal lists `sample.txt` | Dialog visible; `get_resolve_duplicates_filenames()` → `['sample.txt']` |
| 8 | Click the **X** icon top-right of the dialog | Dialog closes. Exactly **one** X exists inside the dialog root (`aria-label="Close"`, visible); it has **no testid today** — see § Concrete Handles |
| 9 | Verify the modal is closed | `wait_for_resolve_duplicates_dialog_closed()` succeeds. **Also confirmed:** the parent "Upload files to …" dialog does **not** re-appear (count 0) — the X dismisses the whole upload interaction, it does not fall back a step |
| 10 | Verify no file was uploaded and no success notification | Capture on `"artifacts"` across the click + close returned `[]` (**zero** requests — positive proof, not mere absence in the table); `success_toast_message` count 0 |
| 11 | Verify the original `sample.txt` is unchanged | File count still 1 (and still 1 after a page reload — the server, not a stale client listing, is the oracle); `lastModified` byte-identical to baseline (`2026-08-21T17:38:33.000Z` before and after); `size` 68 → 68; `artifact_api.get_file(...)` byte-equal to the ORIGINAL content, **not** the replacement bytes |

## Expected Results
- Dialog closes via X; nothing is uploaded; no toast.
- Zero network requests fire from the X click onward.
- The original file's content, size and `lastModified` are all unchanged, verified after a
  reload.
- Zero console errors across the whole flow (confirmed live).

## Coverage Map

### Axis 1 — Case element → Coverage
| Case element | Expected result | Covered by | Asserted where | Disposition |
|---|---|---|---|---|
| Precondition: bucket contains `sample.txt` | present | API seed + `file_exists` + baseline metadata | Setup / Step 2 | covered |
| Precondition: local `sample.txt` available | present | `tmp_path` write | Setup | covered |
| Step 1 navigate | Artifacts loads | `navigate_to_artifacts()` | Step 1 | covered |
| Step 2 select bucket | bucket selected | `navigate_to_bucket()` + `file_exists` | Step 2 | covered |
| Step 3 click upload icon | chooser opens | `upload_files()` (`expect_file_chooser`) | Steps 3–5 | covered (folded — no observable between click and chooser) |
| Step 4 chooser opens immediately | open | same action; failure raises a chooser timeout | Steps 3–5 | covered (folded) |
| Step 5 select + Open | upload modal opens | `wait_for_upload_path_dialog()` | Steps 3–5 | covered |
| Step 6 verify modal, click Upload | detection triggered | prefix assertion + `click_upload_path_upload_button()` | Step 6 | covered |
| Step 7 resolve modal lists `sample.txt` | visible, listed | dialog wait + `get_resolve_duplicates_filenames()` | Step 7 | covered |
| Step 8 click X | modal closes | `click_resolve_duplicates_close_button()` (**new PO method + new testid**) | Step 8 | covered |
| Step 9 modal closed | not visible | `wait_for_resolve_duplicates_dialog_closed()` | Step 9 | covered |
| Step 10 no upload, no notification | none | zero-request capture + toast count 0 | Step 10 | covered |
| Step 11 original unchanged | same metadata | count + `lastModified` + `size` + content, after reload | Step 11 | covered |
| Final state: modal closed via X, nothing uploaded, original unchanged | — | Steps 9–11 combined | Steps 9–11 | covered |

### Axis 2 — Observables asserted beyond the case
| Observable | Why (grounded) |
|---|---|
| **Zero** network requests from the X click onward | Turns "no file was uploaded" from an absence check into positive proof; catches an upload-then-rollback implementation that would leave the table looking correct |
| Parent "Upload files to …" dialog does not re-open | Confirmed live; a plausible alternative product behaviour (X = go back one step) that the case never pins down. Asserting it makes the observed contract explicit |
| Duplicate detection fires 0 requests | Family invariant already asserted by ELITEA-1829/1831/1832 — keeps the family consistent |
| Original file **content** byte-equal to the seed | The strongest "unchanged" claim; a same-size overwrite would defeat a metadata-only check |
| File count re-checked **after a page reload** | Makes the server the oracle rather than an un-refreshed client listing (the digest's own guidance) |
| No console errors | Project standard side-channel check |

## Cleanup
- `artifact_bucket` teardown deletes the bucket (known silent 404, issue `#636` — do not
  work around it here).
- Nothing else to clean: the case is non-mutating by design; the only write is the seed.

## Concrete Handles (discovered during exploration)

**PROVENANCE verified 2026-08-21 after `cd ../EliteaUI && git fetch origin`.**

| Element | Handle (testid-only) | Provenance | Notes |
|---|---|---|---|
| Nav / bucket / file list | existing `ArtifactsPage` methods | on-main ✓ | as ELITEA-1832 |
| Upload icon | `artifacts-upload-files-button` (via `upload_files()`) | on-main ✓ | |
| Upload-path dialog + Upload button | `artifacts-upload-path-dialog`, `artifacts-upload-path-upload-button` | on-main ✓ | |
| Resolve-duplicates dialog | `artifacts-resolve-duplicates-dialog` | on-`automation/testids` only (EliteaAI/EliteaUI@918b8b22) | human cherry-pick to `main` pending |
| Duplicate filename row | `artifacts-resolve-duplicates-filename` | on-`automation/testids` only (@918b8b22) | |
| **X (close) icon** | **testid needed**: `artifacts-resolve-duplicates-close-button` | needs-adding | Live enumeration of the dialog's buttons: `[('', None, 'Close'), ('Cancel', 'artifacts-resolve-duplicates-cancel-button', None), ('Skip', …), ('Replace', …), ('Keep both', …)]` — the X is the first, label-less button and carries **no** `data-testid`. `Modal.BaseModal` already accepts a caller-supplied **`closeButtonTestId`** prop (`src/[fsd]/shared/ui/modal/BaseModal.jsx:35`, applied at line 154 as `data-testid={closeButtonTestId}`); `DuplicateResolutionDialog.jsx` simply doesn't pass it. Add `closeButtonTestId="artifacts-resolve-duplicates-close-button"` to that `<Modal.BaseModal …>` call. Prop-only, zero functional impact (no new DOM node, no new hook, no removed line). Caller-supplied prop on a shared component = the compliant shape per `.agents/testing.md` § Locator policy |
| Success toast | `artifacts-success-toast-message` (`success_toast_message`) | on-main ✓ | asserted with `to_have_count(0)` on a short polled window (ELITEA-1832's `TOAST_ABSENCE_POLL_TIMEOUT` pattern) |
| Bucket listing / metadata / content | `artifact_api.list_bucket_files` / `get_file_metadata` / `get_file` | n/a (API) | server-side oracle |

**Page-object work:** add `resolve_duplicates_close_button` (`LocatorDescriptor(testid=…)`,
class field) and `click_resolve_duplicates_close_button()` to `ArtifactsPage`, mirroring
`click_resolve_duplicates_cancel_button()` (`artifacts_page.py:2430`).
**Do not** substitute `Escape` or a backdrop click — they reach the same `onClose` handler,
but the case's step 8 literally says "click the X icon", and the digest already records this
exact fidelity boundary for the sibling upload dialog (ELITEA-1825).

## Network Behavior
| Moment | Requests (confirmed live) |
|---|---|
| Upload click → duplicate modal | **none** (client-side diff) |
| X click → dialog closed → 2.5 s settle | **none** — `[]` |
| After a page reload | only the normal bucket/listing GETs; listing still 1 file |

## Known Defects
None. All 11 steps behaved exactly as the case describes.

## Blocked Steps
None.

## Automation Hints
- **Fidelity:** the only substitution is the API seed of the precondition file — transit
  only, declared. Every asserted observable (dialog state, request trace, toast absence,
  file metadata/content) is produced by the product. No `route.fulfill`, no
  `page.evaluate`, no injected state.
- Markers: `ui`, `regression`, `p2` (matching ELITEA-1831/1832).
- Suggested file: `automation/tests/ui/artifacts/test_artifacts_upload_duplicate_close_x.py`;
  class `TestArtifactUploadDuplicateCloseX`.
- Wrap each step in `with allure.step("Step N — …")` (project mandatory).
- Assert toast absence with the auto-retrying `expect(...).to_have_count(0, timeout=…)`,
  never a raw sleep — reuse ELITEA-1832's constant and its rationale.
- Timing baseline: the analyst's live run of this flow took **~50 s** headless.
