---
name: Artifacts nested-folder auto-create is lazy-rendered in the tree + extend-existing boundary call (ELITEA-1827)
description: Typing a multi-segment non-existing path ("folder-a/folder-b") in the Upload dialog auto-creates all levels in ONE PUT (S3 key-prefix storage, no separate folder-create call), but the left-panel tree only renders each nesting level on expand — a depth-2 tree-item's DOM node does not exist until its parent is clicked, confirmed via a fresh-page-load re-check (the post-upload auto-navigated state alone can't distinguish lazy from eager rendering). Also documents why this was classified extend-existing against ELITEA-1824's already-merged single-level ("a1") test rather than a fresh spec.
type: feedback
---

## The nested-folder mechanism (confirmed live, ELITEA-1827)

`UploadPathDialog.jsx`'s own helper text says it outright: *"Use '/' to
create nested folder(s)."* Typing `folder-a/folder-b` (neither segment
existing yet) and clicking Upload fires exactly ONE
`PUT .../artifacts/s3/{bucket}/folder-a/folder-b/{file}?project_id=...` →
200 OK — no separate "create folder" request for either intermediate
segment. This is S3-style/key-prefix storage: "folders" are a pure
client-side rendering construct derived from `/`-splitting the object's
own key (`contents[].key` in the `GET .../s3/{bucket}?format=json`
response), not a server-side resource with its own lifecycle. That's
*why* multi-level nesting is safe to prove in one action — there's no
multi-step server operation that could partially fail (create folder-a,
then fail folder-b).

## The lazy-tree-rendering gotcha

Right after upload, the app auto-navigates into the newly-created
DEEPEST folder (URL becomes `?bucket={b}&folder=folder-a%2Ffolder-b`),
and in that state BOTH `artifacts-tree-item-folder-a/` AND
`artifacts-tree-item-folder-a/folder-b/` are already in the DOM —
reading the tree only in this auto-navigated state would make lazy and
eager rendering look identical. The distinguishing check requires a
**second, independent pass**: reload the bucket at its own ROOT
(`navigate_to_bucket(bucket_name)`, no `folder` param), then confirm
`folder-a/folder-b/`'s tree-item node is **absent** from the DOM
(`is_tree_item_visible(..., timeout=SHORT) == False`) until `folder-a`'s
own node is clicked — only then does `folder-b`'s node appear. This is
the single most load-bearing piece of new evidence in the AFS; a
depth-1-only case (like ELITEA-1824's own "a1") cannot structurally
distinguish lazy-vs-eager tree rendering because there's only one level
to render either way.

Also: `artifacts-tree-item-{key}` is keyed by the FULL relative path
(`folder-a/folder-b/`, not just `folder-b/`) — 1824's single-level case
never surfaced this because its one folder's key and leaf name
coincide (`a1/` either way).

## The extend-existing boundary call

ELITEA-1824's merged test already types a single-segment new subfolder
name ("a1") into the identical Path field and proves depth-1
auto-creation, tree visibility, and a 1-element
`get_breadcrumb_folder_names()` list. This case's whole point — a
NON-existing MULTI-segment path creating an arbitrary-depth chain in one
shot, the tree's lazy-per-level rendering, and
`get_breadcrumb_folder_names()`'s genuine 2-element return — is a real
but narrow gap: same underlying mechanism, proven at a depth 1824 never
reaches. Classified `extend-existing` (not `ready-for-automation`, not
`already-covered`) per the existing
`extend_existing_means_insert_into_same_test_not_sibling_method.md`
rule: append new steps to 1824's own state-machine test
(`test_upload_via_three_options_and_verify_selection`, right after its
existing Step 46, before its own final console-error check) rather than
write a parallel spec — same bucket fixture, same page-object methods,
zero new testids, zero new setup.

**Reusable pattern**: when a new case proves "the same feature the
existing test already proves, but at a DEEPER/WIDER instance of the same
parameter" (depth 1 → depth 2, one file → N files, one entry point →
another), check first whether the deeper instance could pass even if a
real bug existed that the shallow instance's assertions structurally
can't catch (here: an off-by-one truncating breadcrumb-crumb list, or a
tree component that only supports one level of lazy expansion). If yes,
that's a genuine (if narrow) gap → `extend-existing`, not
`already-covered`; if the deeper instance is truly just "more of the
identical assertion with bigger N," lean `already-covered` instead.
