# Test Case: Upload Flow – Duplicate File Detected and Resolve Duplicates Modal Appears

## Metadata
- **TMS ID**: ELITEA-1828
- **Linked Story**: none
- **Priority**: l2 (medium — as authored in the source TMS case)
- **Environment Explored**: local (`http://localhost:5173`, EliteaUI `automation/testids`
  branch → DEV backend, project `Elitea Testing Team` / `${ELITEA_PROJECT_ID}`=471)
- **User set**: `${TEST_USER}` (on localhost, `auth_state` fixture skips login via
  `VITE_DEV_TOKEN`)
- **Analyst**: qa-engineer, analyst slot
- **Status**: **extend-existing** — case executed end-to-end live, 2/2 identical runs
  (fresh bucket, same-name re-upload), all 10 case steps pass, zero product defects. A
  genuinely small gap (2 unasserted observables: the modal's exact message text, and the
  presence of all four action buttons) against an already-merged spec — see § Overlap
  check for the dedup/extend boundary call, and § Gap assertions for the precise
  insertion point. 4 testid gaps found (message text + Skip/Replace/Keep-both buttons);
  no `already-covered` (partial-overlap, not full) and no fresh `ready-for-automation`
  (the gap is 2 assertions inserted at an existing observable point, not a new flow).

## Overlap check vs existing automation

`automation/tests/ui/artifacts/test_artifacts_upload_duplicate_cancel.py`
(`TestArtifactUploadDuplicateCancel::test_cancel_stops_entire_upload_including_non_duplicate`,
ELITEA-1832, **merged to `automation/base`** — commit `9dcb2805`, PR #635, confirmed via
`git merge-base --is-ancestor <sha> automation/base` this run) was read in full (295
lines) before this run, alongside its AFS
(`test-specs/artifacts/l3_upload-flow-duplicate-cancel-stops-entire-upload_ELITEA-1832.md`)
and `automation/pages/artifacts_page.py`'s existing `resolve_duplicates_*` locators/methods
(lines 289-309, 1844-1924).

**ELITEA-1832's covering test drives the IDENTICAL flow this case needs** — seed a
bucket with `sample.txt`, upload a file with the same name, land on the "Resolve
duplicates" modal — and its own Step 9 already asserts the dialog is visible and that
the duplicate filename (`sample.txt`) is listed. **What it never asserts, and this
case's own reason to exist:**
1. The modal's exact **message text** (case step 8: *"This file already exists in this
   bucket. Choose how to handle duplicates."*) — the covering test's Step 9 only checks
   `wait_for_resolve_duplicates_dialog()` (visibility) and the filename list; it never
   reads the message `<Typography>` at all.
2. **All four action buttons are present** (case step 10: Cancel, Skip, Replace, Keep
   both) — the covering test's own AFS explicitly documents Skip/Replace/Keep-both were
   deliberately left **without testids** because "this test never clicks Skip/Replace/
   Keep-both and never asserts on them" (its § Concrete Handles, "implementer scope
   call — NOT added" rows) — an honest, correct scope call at the time, but it leaves
   exactly the three elements this case's own step 10 needs to assert visible.

**Dedup verdict (Rule 6):** partial overlap, not full. The underlying mechanism (client-
side duplicate detection, the same dialog component, the same duplicate-filename
rendering) is already proven by 1832; this case's own two missing observables (message
text + button-presence) are a small, local addition at the SAME point in that same
test's flow (immediately after its own Step 9, before its Step 10's Cancel click) — not
a materially different scenario. This is exactly the "small number of missing
assertions on an existing test" shape `extend-existing` exists for (`.agents/memory/
qa-engineer/extend_existing_means_insert_into_same_test_not_sibling_method.md`): the
covering test is a single continuous flow (seed → upload duplicate → modal opens →
Cancel → verify abort), and this case's gap is exactly at the "what does the modal
show" observable point, not a distinct entry point or precondition.

## Preconditions
- User is logged in (on localhost, `auth_state` fixture skips login).
- A project is selected/accessible (`Elitea Testing Team`, id `471` in this exploration
  run; the covering test itself uses whatever project its own fixtures target — no
  change needed for the extension).
- A bucket contains a file named "sample.md" — confirmed live this run: the case's own
  `bucket-1` / `sample.md` names are **case-text placeholders**, not literal fixture
  names (same finding as every other AFS in this folder — the exploration bucket
  `autotest-elitea1828-dupmodal` was freshly created for this run and none of the
  project's other ~9 buckets are named `bucket-1`). The covering test's own
  `artifact_bucket` fixture + `DUPLICATE_FILE_NAME = "sample.txt"` seed already supplies
  an equivalent precondition (a bucket containing one pre-existing file) — no new
  bucket-creation step needed for the extension (see § Gap assertions).
- A local file with the same name as the existing file is available for upload —
  the covering test's own `duplicate_file_path` (`tmp_path / DUPLICATE_FILE_NAME`) already
  satisfies this; no new file needs generating.

## Test Data

### reuse-existing (from the covering test's own fixtures/constants)
- **Bucket**: the covering test's `artifact_bucket` fixture (`bucket_name` local var,
  line 127) — do **not** create a second bucket for this extension.
- **File**: the covering test's own `DUPLICATE_FILE_NAME` ("sample.txt") /
  `DUPLICATE_FILE_CONTENT` / `duplicate_file_path` (lines 68-70, 153) — same literal
  duplicate-seed file already written to `tmp_path`; no new file needs generating. (This
  case's own text uses the literal `sample.md` — confirmed live during exploration this
  is purely a case-text placeholder, exactly like `bucket-1`; the dialog's message/
  button-set behavior is identical regardless of which filename triggers it, confirmed
  by exploring with both `sample.md` in a fresh throwaway bucket AND cross-checking
  against the covering test's own `sample.txt` mechanism — same component, same props
  shape, `duplicateFilenames.length === 1` either way.)

No `generate-per-test` or `generate-shared-with-cleanup` applies — the extension runs
entirely within the covering test's own already-scoped, function-level bucket fixture
and existing file constants.

## Test Steps

*(Steps below are the case's own 10 steps, executed live this run twice — 2/2 identical
— against a fresh bucket built via the UI "New Bucket" form for exploration purposes,
`autotest-elitea1828-dupmodal`, `Elitea Testing Team` project. § Gap assertions maps
steps 8-10 onto the concrete insertion point in the covering test.)*

1. Navigate to the Artifacts section in the left sidebar (case step 1).
   - **Verify**: `artifacts-buckets-heading` visible; confirmed live.
2. Click on the bucket in the bucket list that already contains "sample.md" (case
   step 2).
   - **Verify**: bucket selected, right-panel header shows its name, file table shows
     `sample.md`; confirmed live.
3. Click the upload icon in the top-right corner of the main panel (case step 3) —
   confirmed live this is the **toolbar** entry point (`artifacts-upload-files-button`),
   the same entry point the covering test already uses.
   - **Verify**: native file explorer opens immediately (case step 4, folded — same
     observable, no separate action) — confirmed live via Playwright's file-chooser
     modal-state firing the instant the button is clicked.
4. (Folded into step 3's verify.)
5. Select a file named "sample.md" (same name as the existing file) and click "Open"
   (case step 5).
   - **Verify**: "Upload files to ..." modal opens (case step 6, folded below).
6. Verify the "Upload files to ..." modal opens with the Path field pre-filled with
   "bucket-1" (case step 6).
   - **Verify**: confirmed live — modal title "Upload files to ...", Path field shows
     the bucket name as a read-only prefix (`{bucket_name}/`) before an editable
     textbox — same rendering the covering test's own Step 7 already asserts.
7. Click "Upload" (case step 7).
   - **Verify**: triggers duplicate detection — confirmed live this run (again) it is
     purely client-side: `browser_network_requests` filtered on `artifacts` showed no
     new request between the click and the modal appearing (same mechanism the covering
     test's own Step 8/9 already proves and asserts via `capture_requests_matching`).
8. Verify the "Resolve duplicates" modal opens with the message: "This file already
   exists in this bucket. Choose how to handle duplicates." (case step 8) — **THE GAP**.
   - **Verify**: confirmed live, 2/2 runs — the dialog's message `<Typography>`
     (`DuplicateDialogContent.jsx` line 57-62) reads byte-identical to the case's exact
     text when exactly one duplicate is present. **Not yet asserted by the covering
     test** — its Step 9 only checks dialog visibility + filename list, never reads this
     message. **No testid on this element** — confirmed live via
     `document.querySelector('[data-testid="artifacts-resolve-duplicates-dialog"]')`
     then walking its children; the message `<Typography>` has no `data-testid`
     anywhere in its ancestor chain up to the dialog root. Needs `add-data-testid`
     (see § Concrete Handles).
   - **Automation-hint finding**: the label is **dynamic**, not a static string — the
     component computes `` `${countFiles === 1 ? 'This file' : `${countFiles} files`}
     already exist${countFiles === 1 ? 's' : ''} in this bucket. Choose how to handle
     duplicates.` `` (`DuplicateDialogContent.jsx` lines 31-35). The case's exact text
     is the **singular** (`countFiles === 1`) branch, which is what this case's own
     single-file-duplicate scenario always renders — confirmed live both runs. Not a
     defect; noted so the implementer doesn't assert a literal string against a
     multi-duplicate scenario by mistake.
9. Verify the duplicate file name "sample.md" is listed in the modal (case step 9).
   - **Verify**: confirmed live, 2/2 runs — rendered split across two spans (`sample` /
     `.md`), same technique the covering test's own Step 9
     (`get_resolve_duplicates_filenames()`) already exercises and asserts against
     `sample.txt`. **Already covered** by the existing `resolve_duplicates_filename`
     testid + page-object method — no gap here, this step needs no new assertion beyond
     what 1832 already proves (the mechanism is identical regardless of which literal
     filename triggers it).
10. Verify the modal contains four buttons: "Cancel", "Skip", "Replace", "Keep both"
    (case step 10) — **THE OTHER GAP**.
    - **Verify**: confirmed live, 2/2 runs — all four buttons render
      (`DuplicateResolutionDialog.jsx` lines 28-53): "Cancel" (already has testid,
      reused by the covering test to close the dialog), "Skip", "Replace", "Keep both"
      (all three currently have **no testid** — confirmed live via DOM query; the
      covering test's own AFS explicitly documents this as a deliberate, correct
      scope call AT THE TIME, since it never touched them). This case's own step 10
      asserts their **presence**, which per this project's locator policy
      (`.agents/testing.md` § Locator policy — "absence assertions count as references"
      /"referenced = called on the test's actual code path") means a **visibility
      assertion on these three buttons IS a reference this test makes** — testids must
      be added, not left out, now that a real case needs to assert them. Needs
      `add-data-testid` (see § Concrete Handles).

## Expected Results
- The "Resolve duplicates" modal is displayed with the correct message ("This file
  already exists in this bucket. Choose how to handle duplicates." — the singular-
  duplicate rendering of the component's dynamic label), the correct duplicate file
  name, and all four action buttons (Cancel, Skip, Replace, Keep both) — confirmed live,
  2/2 identical runs, when uploading a file that already exists in the bucket.
- No console errors attributable to this flow (confirmed: across both runs, console
  showed exactly the same 4 pre-existing, unrelated `403 Forbidden` errors on
  `GET /api/v2/secrets/secrets/default/471` — documented background noise in this local
  environment, present on every page load regardless of any action taken; see
  `test-specs/chat-interface/l2_conversation-deletion_ELITEA-2114.md` and sibling AFS
  files for the same finding. Zero NEW errors from either run of the upload/duplicate
  flow itself).
- Clicking "Cancel" (not itself a case step, but used to close the dialog cleanly during
  this exploration) closes the modal with zero network requests — consistent with
  ELITEA-1832's own already-proven Cancel semantics; not re-asserted here since it's
  out of this case's own scope.

## Coverage Map

### Axis 1 — Case element → Coverage
| Case element | Expected result | Covered by (AFS step) | Asserted where | Disposition |
|---|---|---|---|---|
| Precondition: bucket contains "sample.md" | Precondition state exists | Preconditions + Test Data | covering test's own `artifact_bucket` fixture + `DUPLICATE_FILE_NAME` seed, reused as-is — "bucket-1"/"sample.md" confirmed live (again) as case-text placeholders | asserted *(via extend — no new bucket/file)* |
| Step 1: Navigate to Artifacts | Artifacts page loads | Test Step 1 | `artifacts-buckets-heading` visible — covering test's own Step 1, unchanged | asserted *(already proven by covering test)* |
| Step 2: Click bucket-1 (has sample.md) | Bucket selected, sample.md visible | Test Step 2 | covering test's own Step 2 (`navigate_to_bucket` + `file_exists`), unchanged | asserted *(already proven by covering test)* |
| Step 3: Click upload icon | System file explorer opens | Test Step 3 | covering test's own Steps 4-6 (`upload_files()`), unchanged | asserted *(already proven by covering test)* |
| Step 4: Verify file explorer opens immediately | File explorer open | Test Step 3 (folded) | same observable | asserted *(decomposed — already proven by covering test)* |
| Step 5: Select sample.md, click Open | File selected | Test Step 5 | covering test's own Steps 4-6, unchanged | asserted *(already proven by covering test)* |
| Step 6: Verify "Upload files to ..." modal, Path pre-filled | Modal open, Path = bucket name | Test Step 6 | covering test's own Step 7 (`get_upload_path_prefix_text`), unchanged | asserted *(already proven by covering test)* |
| Step 7: Click Upload | Duplicate detection triggered, client-side only | Test Step 7 | covering test's own Step 8/9 (`capture_requests_matching` + assert empty), unchanged | asserted *(already proven by covering test)* |
| Step 8: Verify "Resolve duplicates" modal message text | Exact message shown | Gap Step A (new) | **NEW** — `get_resolve_duplicates_message_text()`, testid `artifacts-resolve-duplicates-message` (needs adding) | asserted *(THE GAP — new assertion)* |
| Step 9: Verify duplicate file name "sample.md" listed | Duplicate filename shown | Test Step 9 | covering test's own Step 9 (`get_resolve_duplicates_filenames`), unchanged — mechanism identical regardless of literal filename | asserted *(already proven by covering test)* |
| Step 10: Verify four buttons present (Cancel, Skip, Replace, Keep both) | All four buttons visible | Gap Step B (new) | **NEW** — Cancel via existing `resolve_duplicates_cancel_button`; Skip/Replace/Keep-both via 3 new testids (need adding) + 3 new `to_be_visible()` assertions | asserted *(THE GAP — new assertions)* |
| Expected Final State: modal shows correct message, filename, and all 4 buttons | Composite pass condition | Gap Steps A+B + existing Step 9 | combination of the above | asserted |
| Pass criterion: "All steps complete without errors" | No errors during flow | All steps | console-error check (4 pre-existing unrelated errors only, 2/2 runs) — extend the covering test's own existing final console-error step's scope to cover the appended assertions, no code change needed (it already collects from page load) | asserted |

### Axis 2 — Observables asserted beyond the case
- **2/2 identical live reproduction** (ran the full navigate → upload duplicate →
  Resolve-duplicates-modal flow twice in the same session, fresh bucket both times) —
  *added: establishes this isn't a timing-flaky observation before handing off as
  `extend-existing`.*
- **The dynamic (singular vs. plural) nature of the modal's message label** — *added:
  the case text only ever specifies the singular-duplicate wording; documented so the
  implementer doesn't hardcode an assertion that would break if a future case exercises
  a multi-duplicate upload (a real, different code path in `DuplicateDialogContent.jsx`,
  not asserted by this case).*
- **Console-message check across both runs** — *added: standard silent-error guard;
  confirmed zero errors attributable to this flow (only the pre-existing, already-
  documented, unrelated project-471 `secrets/secrets/default` `403` noise present on
  every page load in this environment).*
- **Network-idle confirmation that clicking "Upload" (this case's own step 7) fires
  zero requests** — *added: same technique the covering test already uses; re-confirmed
  live here since it's this case's own step 7, not merely inherited.*

## Gap assertions (what the implementer inserts into the covering test)

**Covering spec**: `automation/tests/ui/artifacts/test_artifacts_upload_duplicate_cancel.py::
TestArtifactUploadDuplicateCancel::test_cancel_stops_entire_upload_including_non_duplicate`
(method body: lines 116-295).

**Insertion point**: inside the EXISTING **Step 9** block (lines 210-225 — "Verify the
'Resolve duplicates' modal opens listing sample.txt..."), immediately after the existing
`duplicate_names` assertion and **before** Step 10's Cancel click (line 227). This is the
single point in the covering test's flow where the modal is open and fully rendered —
exactly where this case's own steps 8 and 10 belong; no new bucket state or navigation is
needed, and nothing about the existing Step 9/10 boundary needs to move.

**New assertions to insert** (extend the existing Step 9 block — do not renumber; widen
its own docstring text to mention the message/button assertions too):

```python
        with allure.step(
            "Step 9 — Verify the 'Resolve duplicates' modal opens listing "
            "sample.txt with the correct message and all four action buttons "
            "(ELITEA-1828), and that detection was purely client-side "
            "(zero network requests between Upload click and the modal)"
        ):
            artifacts_page.wait_for_resolve_duplicates_dialog(timeout=DIALOG_TIMEOUT)
            assert not requests_during_detection, (
                "Duplicate detection must be a purely client-side diff "
                f"against the already-fetched bucket listing — no network "
                f"request should fire, but observed: {requests_during_detection}"
            )
            duplicate_names = artifacts_page.get_resolve_duplicates_filenames()
            assert any(DUPLICATE_FILE_NAME in name for name in duplicate_names), (
                f"'Resolve duplicates' modal should list {DUPLICATE_FILE_NAME!r} "
                f"as the duplicate file, got: {duplicate_names}"
            )

            # --- ELITEA-1828 additions below ---
            message_text = artifacts_page.get_resolve_duplicates_message_text()
            assert message_text == (
                "This file already exists in this bucket. Choose how to handle "
                "duplicates."
            ), (
                f"'Resolve duplicates' modal should show the singular-duplicate "
                f"message for a single colliding file, got: {message_text!r}"
            )
            expect(artifacts_page.resolve_duplicates_cancel_button).to_be_visible()
            expect(artifacts_page.resolve_duplicates_skip_button).to_be_visible()
            expect(artifacts_page.resolve_duplicates_replace_button).to_be_visible()
            expect(artifacts_page.resolve_duplicates_keep_both_button).to_be_visible()
```

**New `ArtifactsPage` members needed** (add alongside the existing
`resolve_duplicates_*` locators, `artifacts_page.py` lines 289-309 / 1882-1905):

```python
    resolve_duplicates_message = LocatorDescriptor(
        testid="artifacts-resolve-duplicates-message",
        description="'Resolve duplicates' dialog — the message explaining why the "
        "dialog appeared and what the user should do (dynamic singular/plural "
        "wording depending on duplicate count; ELITEA-1828 only exercises the "
        "singular, one-duplicate case)",
    )

    resolve_duplicates_skip_button = LocatorDescriptor(
        testid="artifacts-resolve-duplicates-skip-button",
        description="'Skip' button inside the 'Resolve duplicates' dialog — skips "
        "the duplicate file, keeps uploading any non-duplicate files in the batch "
        "(ELITEA-1828 only asserts presence; no case yet exercises clicking it)",
    )

    resolve_duplicates_replace_button = LocatorDescriptor(
        testid="artifacts-resolve-duplicates-replace-button",
        description="'Replace' button inside the 'Resolve duplicates' dialog — "
        "overwrites the existing file (ELITEA-1828 only asserts presence; no case "
        "yet exercises clicking it)",
    )

    resolve_duplicates_keep_both_button = LocatorDescriptor(
        testid="artifacts-resolve-duplicates-keep-both-button",
        description="'Keep both' button inside the 'Resolve duplicates' dialog — "
        "uploads the file alongside the existing one under a modified name "
        "(ELITEA-1828 only asserts presence; no case yet exercises clicking it)",
    )

    def get_resolve_duplicates_message_text(self) -> str:
        """Return the 'Resolve duplicates' dialog's explanatory message text.

        Dynamic label — reads "This file already exist**s**..." for exactly one
        duplicate, "N file**s** already exist..." for more than one (see
        DuplicateDialogContent.jsx). ELITEA-1828 only exercises the singular case.
        """
        text = self.resolve_duplicates_message.text_content() or ""
        logger.info("'Resolve duplicates' dialog message: %s", text)
        return text.strip()
```

Then widen the class docstring / module docstring to mention ELITEA-1828 as a second
covered case, and add a second `@allure.issue` decorator alongside the existing
ELITEA-1832 one (lines 110-114), pointing at this case's own onetest markdown file, so
the shipped test's traceability reaches both TMS cases — per `.agents/memory/qa-engineer/
coverage_classification_needs_board_task_not_just_behavioral_match.md`'s point that a
behavioral match alone isn't the same as delivered traceability.

## Cleanup
1. No new bucket/fixture cleanup needed for the extension — it reuses the covering
   test's own `artifact_bucket` fixture teardown as-is.
2. No other entities are created by this extension (no Agent, no Toolkit, no
   Credential).
3. **This exploration run's artifacts** (not part of the automated test — a standalone
   bucket built via the UI form to verify the case live, since the automated extension
   runs inside the COVERING test's own fixture-managed bucket, not a new one): bucket
   `autotest-elitea1828-dupmodal` was created in the `Elitea Testing Team` project
   (id 471), containing `sample.md` (82 B) at bucket root at the end of this run. Left in
   place — matches this project's existing convention of un-deleted `autotest-*` test
   buckets from prior runs; safe to delete at any time via
   `ArtifactAPI.delete_bucket("autotest-elitea1828-dupmodal")`.
4. Local exploration screenshot (repo-root `.playwright-mcp/`, untracked, uploaded to
   the `evidence` prerelease store and embedded below): shows the live "Resolve
   duplicates" modal with the exact message text, the `sample`/`.md` filename split, and
   all four buttons (Cancel, Skip, Replace, Keep both) rendered together.

   ![Resolve duplicates modal — message, filename, and all four buttons](https://github.com/EliteaAI/elitea-testing-public/releases/download/evidence/ELITEA-1828-resolve-duplicates-modal.png)
5. Local temp upload source file (untracked, harmless to leave or delete):
   `.playwright-mcp/uploads/sample.md`.

## Concrete Handles (discovered during exploration)

**Locator policy note (overrides spec-format's generic ladder):** this project's
locator policy (`.agents/testing.md` § Locator policy, `.agents/role-overrides.md`) is
**testid-only, no fallback ladder** — `LocatorDescriptor(testid=...)` with no
`fallback=`/`locator=`. Every row below carries a **PROVENANCE** column verified this
run via `cd ../EliteaUI && git fetch origin` followed by `git grep` against both
`origin/main` and `origin/automation/testids`.

**4 testid gaps this run** — the message text and 3 of the 4 action buttons need
`add-data-testid` work; everything else this case touches already has a
policy-compliant testid.

| Element | testid | Provenance | Notes |
|---|---|---|---|
| Buckets heading | `artifacts-buckets-heading` | on-main ✓ | existing |
| Create bucket button | `artifacts-create-bucket-button` | on-main ✓ | existing (used only for this exploration's throwaway bucket, not part of the case's own steps) |
| Bucket name input (create-bucket form) | `artifacts-bucket-name-input` | on-main ✓ | existing (exploration only) |
| Bucket save button (create-bucket form) | `artifacts-bucket-save-button` | on-main ✓ | existing (exploration only) |
| Upload files button (toolbar, non-empty bucket) | `artifacts-upload-files-button` | on-main ✓ | existing — this case's own step 3 entry point |
| Upload files button (empty-bucket state) | `artifacts-upload-files-empty-state-button` | on-main ✓ | existing — confirmed live as a DISTINCT testid from the toolbar button above, used only for this exploration's precondition-seeding upload into a brand-new empty bucket, not part of the case's own steps (the case's own bucket already contains "sample.md") |
| "Upload files to ..." dialog | `artifacts-upload-path-dialog` | on-automation/testids only (awaiting promotion) | existing (ELITEA-1832) |
| Upload path input — read-only prefix wrapper | `artifacts-upload-path-input` | on-automation/testids only | existing (ELITEA-1832) |
| Upload path "Upload" button | `artifacts-upload-path-upload-button` | on-automation/testids only | existing (ELITEA-1832) |
| **"Resolve duplicates" modal — entire dialog** | `artifacts-resolve-duplicates-dialog` | on-automation/testids only | existing (ELITEA-1832), via `BaseModal`'s `data-testid` prop |
| "Resolve duplicates" modal — duplicate filename display | `artifacts-resolve-duplicates-filename` | on-automation/testids only | existing (ELITEA-1832) — repeated testid per row |
| "Resolve duplicates" modal — Cancel button | `artifacts-resolve-duplicates-cancel-button` | on-automation/testids only | existing (ELITEA-1832) — this case's step 10 reuses it for the visibility assertion, no click needed |
| **"Resolve duplicates" modal — message text** | `artifacts-resolve-duplicates-message` | **needs-adding** | `DuplicateDialogContent.jsx` line 57-62 (the `<Typography variant="labelMedium">` rendering the dynamic `label` string) — confirmed live via DOM query: no `data-testid` anywhere in its ancestor chain up to the dialog root |
| **"Resolve duplicates" modal — Skip button** | `artifacts-resolve-duplicates-skip-button` | **needs-adding** | `DuplicateResolutionDialog.jsx` line 36-41 (`Button.BaseBtn` calling `onSkip`) — confirmed live, no `data-testid` |
| **"Resolve duplicates" modal — Replace button** | `artifacts-resolve-duplicates-replace-button` | **needs-adding** | `DuplicateResolutionDialog.jsx` line 42-47 (`Button.BaseBtn` calling `onReplace`) — confirmed live, no `data-testid` |
| **"Resolve duplicates" modal — Keep both button** | `artifacts-resolve-duplicates-keep-both-button` | **needs-adding** | `DuplicateResolutionDialog.jsx` line 48-53 (`Button.BaseBtn` calling `onKeepBoth`) — confirmed live, no `data-testid` |

## Network Behavior
- Same mechanism ELITEA-1832 already documents and this run re-confirmed twice: opening
  a bucket fires `GET {ELITEA_URL}/artifacts/s3/{bucket}?project_id={id}&format=json`;
  the initial seed upload fires one `PUT {ELITEA_URL}/artifacts/s3/{bucket}/{file_key}
  ?project_id={id}` → `200 OK`; clicking "Upload" when a duplicate is present fires
  **zero** network requests (confirmed live via `browser_network_requests` filtered on
  `artifacts`, comparing the request list immediately before and after the click, both
  runs) — the "Resolve duplicates" modal is driven entirely by a client-side diff
  against the already-fetched bucket listing.
- Confirmed live this run: `PUT http://localhost:5173/artifacts/s3/autotest-elitea1828-dupmodal/sample.md?project_id=471`
  → `200 OK` for the precondition-seeding upload; no further requests until the modal
  was closed via Cancel.

## Known Defects Found During Exploration
**None found.** Live product behavior matches the case's expected behavior exactly
across 2/2 identical runs: the "Resolve duplicates" modal opens with the message "This
file already exists in this bucket. Choose how to handle duplicates.", lists the
duplicate file name, and renders all four action buttons (Cancel, Skip, Replace, Keep
both). Zero console errors attributable to the flow (only the pre-existing, already-
documented, unrelated project-471 `secrets/secrets/default` `403` noise, present on
every page load in this environment — see `test-specs/chat-interface/
l2_conversation-deletion_ELITEA-2114.md` and sibling AFS files for the same finding,
confirmed to recur identically here).

## Blocked Steps
None.

## Automation Hints
- Framework: Playwright + pytest (confirmed from `.agents/testing.md`).
- **Do not create a new test file or a new test method.** Insert the 5 new assertion
  lines directly into the covering test's existing Step 9 block, per this project's own
  `extend-existing` precedent (`.agents/memory/qa-engineer/
  extend_existing_means_insert_into_same_test_not_sibling_method.md`): the covering test
  is already at the exact observable point (the modal open, fully rendered) this case's
  remaining steps need — there is no separate flow or precondition to set up.
- **4 new `LocatorDescriptor` fields + 1 new page-object method needed** on
  `ArtifactsPage` (see § Gap assertions) — all four are dynamic-free, static testids
  (no templating needed, unlike e.g. `artifact-actions-{filename}-menu-button`
  elsewhere in this file).
- **Run `add-data-testid` for all 4 gaps before writing the page-object fields** — commit
  + push to `automation/testids` per the standard flow (`.agents/workflow.md` § Testid
  flow). All 4 are plain JSX attribute additions in
  `../EliteaUI/src/pages/Artifacts/component/DuplicateDialogContent.jsx` (1 line) and
  `.../DuplicateResolutionDialog.jsx` (3 lines) — confirmed live neither file has any
  other testid work pending, no merge-conflict risk expected.
- Wait strategy: no additional waits needed beyond the covering test's own existing
  `wait_for_resolve_duplicates_dialog()` — by the time that resolves, the message and
  all four buttons are already rendered synchronously (same DOM paint, confirmed live
  both runs: no separate loading state for any part of this dialog's content).
- **The `@allure.issue` decorator referencing this case's own TMS link is a follow-up
  for whoever lands the extension** — add a second `@allure.issue(".../ELITEA-1828_
  upload-flow-duplicate-file-detected-and-resolve-duplicates-modal-appears.md",
  "onetest-ai Test Case link")` alongside the existing ELITEA-1832 issue decorator
  (lines 110-114), so the shipped test's traceability reaches both TMS cases.
- **`automation_test_id` back-write**: this same test
  (`tests.ui.artifacts.test_artifacts_upload_duplicate_cancel.TestArtifactUploadDuplicateCancel.test_cancel_stops_entire_upload_including_non_duplicate`)
  now proves BOTH ELITEA-1832 and ELITEA-1828 — the onetest case file for ELITEA-1828
  gets this same dotted ref in its own `automation_test_id` list at merge time (per
  `.agents/test-automation.yaml` § `backwrite_on_done` — "one test may also cover
  several cases").
