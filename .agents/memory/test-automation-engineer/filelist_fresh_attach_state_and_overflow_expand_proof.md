---
name: FileList.jsx fresh attach state + overflow expand proof
description: Reuse remove_attachment_chip(0) loop to zero chips instead of a new conversation for "fresh attach state"; icon outerHTML is a valid genericity proof; aria-expanded before/after click proves the +N control is real, not plumbing.
type: feedback
---

## "Fresh attach state" without a new conversation

ELITEA-2196/2197/2199/2467 all only get ONE `conversation_id` fixture per
test. When an AFS says "in a separate attach action (fresh chip set)" or
"in a fresh conversation/attach state" for a second attach sub-step within
the SAME test, the cheapest honest way to get there is NOT a new
conversation — it's looping the already-existing
`remove_attachment_chip(0)` (index 0 renumbers after each removal, same
idiom ELITEA-2198's sequential-removal test already established) down to
`wait_for_attachment_chip_count(0)`, then attaching again. Confirmed live
(ELITEA-2199/2467 implementation): this reliably zeroes the composer's
client-side attachment state and the subsequent attach action behaves
identically to a truly fresh composer (same overflow-split math, same
chip indices starting at 0). No navigation, no new fixture, no server
round-trip — attachments are entirely client-side pre-send anyway.

## Icon-genericity proof: compare `outerHTML`, not just presence

To prove a shared/generic icon renders identically regardless of input
data (e.g. `FileList.jsx`'s `<AttachedFileIcon/>` for every attachment
type — no per-type branching, confirmed via source read), read each
instance's `el.children[0].outerHTML` via a scoped `.evaluate()` (same
idiom as the existing `has_file_icon` structural check) and assert
`len(set(markups)) == 1` across N differently-triggered instances. This
only works safely when the icon source SVG has no per-instance dynamic
ids (checked `attached-file-icon.svg` source first — static path data,
no `useId()`/`clipPath` ids that would differ by mount position). If an
icon asset DOES use dynamic ids, this technique would false-fail — check
the source first.

## Proving a "+N" overflow control is a REAL click-to-expand, not inert

Existing tests (ELITEA-2196/2197's `get_overflow_attachment_names()`)
click the overflow button only as PLUMBING to read hidden names for a
count assertion — they never assert the interaction itself. To assert it
as its own observable (ELITEA-2467 AFS steps 4-5): read
`chat_attachment_overflow_button.get_attribute("aria-expanded")` BEFORE
the click (expect not `"true"`) and again immediately AFTER
(`FileList.jsx:117`, `aria-expanded={open ? 'true' : undefined}` — expect
exactly `"true"`), alongside the existing hidden-item-visibility wait.
This proves the control's own accessibility state machine actually
flips, not just that a `<ul>` happened to appear. New page-object method:
`ChatPage.open_attachment_overflow_menu_and_read()` — additive, doesn't
touch `get_overflow_attachment_names()`.
