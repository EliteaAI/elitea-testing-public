---
name: Chat attachment overflow bucket + Escape closes parent popper
description: FileList.jsx's visible/overflow chip split is container-width-dependent even with 3-4 attachments when the plus-menu popper is open; ChatPage.get_overflow_attachment_names()'s internal Escape press can close the WHOLE plus-menu popper, not just the overflow sub-menu.
type: feedback
---

## FileList.jsx overflow — never assert visible-chip-count alone

With the chat plus-menu popper open (narrows the composer), even 3-4
attachments can overflow into the "+N" bucket depending on viewport width —
confirmed live during ELITEA-2091 implementation (headless pytest context,
default viewport). Asserting `ChatPage.get_attachment_chip_count()` /
`get_visible_attachment_names()` (visible-only) after a real, successful
attach can stay FLAT (test looks red) purely because the new item landed in
overflow instead of a visible chip.

**Always use `get_total_attached_file_count()` / `get_all_attached_file_names()`**
(visible + overflow) for any attachment count/name assertion — this is
already documented in `get_total_attached_file_count()`'s own docstring
("never hardcode a 'N visible' split"), but the docstring doesn't warn that
this can bite even at LOW attachment counts (3-4), not just near the
10-file ceiling.

## Escape closes the PARENT popper, not just the sub-menu

`ChatPage.get_overflow_attachment_names()` opens the overflow Menu, reads
names, then closes it via `page.keyboard.press("Escape")`. When an overflow
bucket actually exists, this Escape press closes the WHOLE plus-menu
popper too (same class of quirk `ChatPage.close_plus_menu_popper()`'s
docstring already documents for ELITEA-2203: "closing (Escape) ... closes
the popper in a way that then blocks the next open"). A caller that reads
`chat.attach_files_button.text_content()` (the "N left" counter, only
visible inside the popper) AFTER calling
`get_all_attached_file_names()`/`get_overflow_attachment_names()` will hit
a `Locator.text_content()` timeout if overflow existed.

**Rule: read the "N left" counter text BEFORE calling
`get_all_attached_file_names()`**, not after — and use
`ChatPage.close_plus_menu_popper()` (click a neutral point, never Escape)
if you need the popper in a known-closed state afterward.
