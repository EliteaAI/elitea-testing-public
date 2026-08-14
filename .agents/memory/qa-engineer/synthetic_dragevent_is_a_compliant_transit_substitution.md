---
name: Synthetic DragEvent drag-drop is a compliant transit substitution
description: page.evaluate() constructing a real File + DataTransfer + dragenter/dragover/drop DragEvents to simulate OS-level file drag is NOT a fidelity violation — it substitutes only the input mechanism Playwright cannot produce natively; the real onDrop handler/pipeline/render still run.
type: feedback
---

## Pattern seen (ELITEA-2091 review, PR #1508)

`ChatPage.drag_and_drop_file()` calls `self.composer_dropzone.evaluate(...)`
to build a real in-page `File` (from real bytes, base64-round-tripped), wrap
it in a `DataTransfer`, and dispatch `dragenter`→`dragover`→`drop`
`DragEvent`s at a real testid'd drop-zone element. This trips the mechanical
fidelity grep (`\.evaluate\(`) every time — don't reflexively treat that hit
as a violation.

## Why it's compliant (transit-only, not terminal)

Playwright has no API to drive a native OS-level file drag (Finder/Explorer)
— there's no browser surface for it. `.evaluate()` here only supplies the
INPUT EVENT the browser would otherwise synthesize from OS drag — it does
not fabricate a response, inject app state, or bypass the component under
test. The real `onDrop` handler, the real upload/attach pipeline, and the
real chip render all still execute exactly as they do for the file-picker
path. This matches `.agents/testing.md` § Fidelity policy's "timing
control is NOT substitution" spirit, extended to input-mechanism
substitution: the case's own observable (chip renders, counter decrements,
filename in the sent thread) is still produced by the system.

## What to check before waving it through

1. The element the event is dispatched on has a REAL testid-based
   `LocatorDescriptor` (not a page-level raw handle) — here
   `composer_dropzone = LocatorDescriptor(testid="chat-composer-dropzone")`.
2. The `File` content is real bytes from a real on-disk file, not a
   hand-authored payload standing in for a server response.
3. The docstring/AFS/PR body all declare the substitution explicitly
   (transit-only, names the real pipeline it still exercises) — an
   undeclared use of the same technique would NOT get this pass.
4. No response is mocked and no unrelated app state is written via the
   same `.evaluate()` call — only the synthetic input event itself.

If all four hold, this is the correct pattern for automating file-drag-drop
anywhere in this suite — cite this precedent rather than re-deriving the
reasoning each time.
