---
name: Bucket-menu composite actions don't reopen the menu; DeleteEntityModal siblings key off the DELETE URL substring
description: Two durable patterns from ELITEA-1817 (create bucket at the 56-char boundary + delete via bucket-menu, PR #668) for artifacts_page.py — a menu-action method contract and a shared-modal sibling-method contract, both reusable for future entity types.
type: feedback
---

## Pattern 1 — composite bucket-menu action methods never re-open the menu; the caller opens once

`ArtifactsPage.open_bucket_menu(bucket_name)` hovers the row then clicks the
hover-gated dot-menu trigger. The established, CORRECT contract for any
composite "click an item in the open menu" method
(`click_bucket_menu_upload_files_item()`, ELITEA-1808) is:

- The method does **NOT** call `open_bucket_menu()` internally.
- Its docstring says "call `open_bucket_menu` first" — a **prerequisite the
  caller must satisfy**, not something the method does for you.
- The test calls `open_bucket_menu()` exactly once, then the composite
  method just clicks the already-visible item.

**Why this matters, concretely (ELITEA-1817):** the AFS's own Automation
Hints section described the analogous new method
(`click_bucket_menu_delete_item(bucket_name)`) as "call `open_bucket_menu`
(existing, already waits for the menu to open), then click the Delete
item" — i.e. it read as if the method should open the menu itself. But
this case's own Test Step 10 needs to read the dropdown's full text
(`get_bucket_menu_items_text()`) *while the menu opened in Step 9 is still
open* — inserted BETWEEN opening and clicking Delete. If
`click_bucket_menu_delete_item()` had re-invoked `open_bucket_menu()`
internally, the test would re-hover the row and re-click the
already-open trigger a second time — for a MUI menu whose `onClick` toggles
`anchorEl`, that's a real risk of closing an already-open menu instead of
clicking through it (untested territory; no sibling test had ever needed
the dropdown to stay open across two page-object calls before this case).

**The fix:** read the REAL code of the existing precedent
(`click_bucket_menu_upload_files_item()`), not just its docstring's loose
paraphrase, and match that shape — no internal `open_bucket_menu()` call,
caller-opens-once. Shipped `click_bucket_menu_delete_item(timeout=10000)`
with no `bucket_name` param at all (it doesn't need one — it just clicks
the already-open menu's Delete item + waits for the confirm dialog).

**Generalizes to:** any future case that needs to inspect/read an
already-open dropdown/menu/popper BEFORE clicking one of its items. Don't
trust an AFS's English description of a composite method's shape over the
actual code of its closest sibling — grep the real implementation.

## Pattern 2 — shared `DeleteEntityModal` sibling-methods key off the DELETE URL substring, not a bucket/file distinction

The `delete-confirm-dialog`/`delete-confirm-message`/`delete-confirm-button`
testids (ELITEA-1847) belong to ONE shared `DeleteEntityModal` component,
reused across at least two call sites now: the file/folder toolbar
bulk-delete (ELITEA-1847) and the bucket-row dot-menu's "Delete" (ELITEA-1817).
The existing `confirm_delete()` (ELITEA-1847) wraps
`page.expect_response(lambda r: "artifacts/artifacts" in r.url and
r.request.method == "DELETE")` — that's the file/folder endpoint. It is
**not reusable as-is** for a bucket delete, whose endpoint is
`DELETE .../artifacts/buckets/default/{project_id}?name={bucket}` (a
QUERY-PARAMETER shape, notably different from
`ArtifactAPI.delete_bucket()`'s own path-segment shape — this asymmetry is
also the likely root cause of #636, "bucket cleanup 404s", confirmed
independently useful evidence but out of THIS case's scope to fix).

**The established sibling pattern**: add a new method with the identical
`expect_response` idiom, only the URL substring differs
(`confirm_delete_bucket()` matches `"artifacts/buckets"` instead of
`"artifacts/artifacts"`) — reuse `delete_confirm_button` as-is, since the
CLICK target is the same shared component regardless of which entity type
is being deleted.

**Generalizes to:** any future case that drives `DeleteEntityModal` from a
THIRD call site (e.g. a future agent/toolkit/credential delete flow reusing
the same shared modal) — check the actual DELETE endpoint's URL substring
live before assuming `confirm_delete()` applies; if it's a different
endpoint, add a sibling `confirm_delete_<entity>()` method rather than
widening `confirm_delete()`'s own matcher (which would silently break its
existing file/folder-delete callers if the URL patterns ever overlapped
unexpectedly).

## Pattern 3 (minor, same PR) — `wait_for_bucket_removed_from_list()` added defensively, beyond the AFS's own hints

The AFS's Automation Hints said to reuse `count_bucket_rows(bucket_name) ==
0` bare (confirmed live 2/2 by the analyst). Implementer judgment call: since
`wait_for_bucket_in_list()`'s own docstring already documents a "list
mid-refetch" race for the bucket's *appearance* after Save, the symmetric
race for its *disappearance* after a delete-confirm click seemed plausible
too (same class of race `wait_for_file_count()` already guards for the
file-table, ELITEA-1847). Added `wait_for_bucket_removed_from_list()` using
the identical `expect(locator).to_have_count(0, timeout=...)` idiom, used it
ahead of the AFS's own bare count check in Test Step 15. Ran GREEN 2/2 either
way in this environment — the extra wait never demonstrated the race firing,
but it's a cheap, precedented, non-scope-creep addition (same assertion,
sturdier mechanism) worth keeping for whichever future run finally hits the
timing window.
