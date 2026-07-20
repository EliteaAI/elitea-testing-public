---
name: Artifacts bucket-delete reuses DeleteEntityModal + whole-container text-read pattern (ELITEA-1817)
description: Bucket dot-menu Delete reuses ELITEA-1847's DeleteEntityModal testids as-is (zero new testids for the modal); DotMenu.jsx's Menu container itself carries a templated `{id}-menu` testid usable for whole-container .text_content() reads (avoids needing per-item testids for visibility-only checks); UI's own bucket-delete call is query-param shaped, differing from ArtifactAPI.delete_bucket()'s path-segment shape (informs #636); TMS case's own "55 chars" test-data label was actually 56 chars (case-authoring miscount, filed as CLARIFICATION not a defect).
type: feedback
---

## Context

ELITEA-1817 (analyst pass, 2026-07-20): create a bucket with a 55/56-char name at the
`CreateBucket.jsx` yup `max(56)` boundary, delete it via the bucket-row dot-menu
"Delete" action, confirm removal. AFS: `test-specs/artifacts/l3_create-artifact-bucket-55-char-name-and-delete_ELITEA-1817.md`.

## Findings worth keeping

1. **Bucket delete and file/folder delete share the exact same confirmation modal.**
   `BucketItem.jsx`'s Delete menu-item config sets `entityName: name`, which
   `DotMenu.jsx`'s `activeDialog.props.entityName` check routes to
   `Modal.DeleteEntityModal` — the IDENTICAL component ELITEA-1847 already put
   `delete-confirm-dialog`/`delete-confirm-message`/`delete-confirm-button` testids
   on for the file/folder bulk-delete flow. Confirmed live: zero new testids needed
   for the modal itself when a new case reuses it from a different call site (only
   the entry-point trigger — the bucket dot-menu's Delete item — needed its own
   testid, since it had none: added `key: 'bucket-menu-delete'` to `BucketItem.jsx`'s
   menuItems array, same one-line mechanism as the sibling `bucket-menu-upload-files`
   fix from ELITEA-1808).

2. **`DotMenu.jsx`'s whole dropdown Menu carries its own testid** —
   `<Menu data-testid={id ? \`${id}-menu\` : undefined}>` (distinct from the
   `-menu-button` trigger testid). For a case that only needs to VERIFY multiple
   dropdown item labels are present (not click each one), reading the ENTIRE
   container's `.text_content()` (e.g. `"Upload filesRenamePin to topDelete"`) is a
   fully testid-compliant way to assert all-items-visible without adding a
   per-item testid to every menu entry — same "read the whole testid'd container,
   substring-check inside it" pattern this page object already established with
   `get_file_row_text()` for file-table columns. Saves testid churn for
   visibility-only requirements; only add per-item testids when a future case needs
   to CLICK that specific item.

3. **Bucket delete's live network call is query-param shaped, NOT path-segment
   shaped.** UI's own delete fires
   `DELETE /artifacts/buckets/default/{project_id}?name={bucket}` (confirmed live,
   200 OK) — completely different shape from `automation/api/client.py`'s
   `ArtifactAPI.delete_bucket()`, which builds
   `DELETE /artifacts/buckets/default/{project_id}/{bucket_name}` (path segment,
   with a `p--{project_id}.{bucket_name}` fallback also path-segment). This
   independently supports the hypothesis that issue #636 ("bucket cleanup fails
   silently — delete returns 404") is a wrong-URL-format bug in the Python API test
   client, not a real backend defect — a case whose delete goes through the real UI
   button is unaffected by #636 entirely. Flagged as a comment-worthy note on #636,
   not re-opened/re-investigated as part of this case.

4. **A TMS case's own test-data label can be wrong, independent of any live-product
   drift.** ELITEA-1817's Test Data table labelled its bucket name "(55 chars)" —
   the literal string is actually 56 characters (`len()` confirmed via a plain
   Python one-liner). This doesn't affect the case's pass/fail (56 ≤
   `CreateBucket.jsx`'s `max(56)` boundary still triggers no warning), but it means
   the case is exercising the exact max-length boundary, not "one below max" as its
   own framing implies. Filed as a 4th CLARIFICATION
   ([#667](https://github.com/EliteaAI/elitea-testing-public/issues/667)) alongside
   3 live-product-wording drifts
   ([#664](https://github.com/EliteaAI/elitea-testing-public/issues/664) confirm-dialog
   wording, [#665](https://github.com/EliteaAI/elitea-testing-public/issues/665) toast
   wording, [#666](https://github.com/EliteaAI/elitea-testing-public/issues/666)
   dot-menu label/order "Rename" vs "Edit") — a good reminder to always `len()`-check
   a case's own literal test-data strings against its stated character-count claims,
   not just trust the label.

5. **Operational note**: `gh release upload` to the shared `evidence` release hit
   repeated transient 502/503 errors from GitHub's uploads service during this run
   (persisted across ~4 retries with backoff). Filed the 3 wording CLARIFICATIONs
   with local screenshot filenames referenced but not yet embedded — flagged for a
   later `embed-evidence` sweep once the outage clears, rather than blocking the
   whole deliverable on an upload retry loop.
